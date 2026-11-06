package scopedtools

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"regexp"
	"strings"
	"sync"
	"time"

	"openstacklab/openstack-ai/internal/team"
)

const (
	Compute = "compute"
	Network = "network"
)

var (
	ErrDenied = errors.New("specialist tool request denied")
	ErrBudget = errors.New("shared tool-call budget exhausted")
	uuidRE    = regexp.MustCompile(`(?i)^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`)
)

type Assignment struct {
	Role      string
	ProjectID string
	TargetID  string
	FlavorID  string
}

type Call struct {
	Name      string            `json:"name"`
	Arguments map[string]string `json:"arguments"`
}

type ServerSnapshot struct {
	ID        string `json:"id"`
	ProjectID string `json:"project_id"`
	FlavorID  string `json:"flavor_id"`
	Status    string `json:"status"`
	Fault     string `json:"fault,omitempty"`
}

type FlavorSnapshot struct {
	ID     string `json:"id"`
	VCPUs  int    `json:"vcpus"`
	RAMMiB int    `json:"ram_mib"`
}

type PortSnapshot struct {
	ID        string `json:"id"`
	ProjectID string `json:"project_id"`
	DeviceID  string `json:"device_id"`
	Status    string `json:"status"`
}

type ReaderFuncs struct {
	GetServer func(context.Context, string) (ServerSnapshot, error)
	GetFlavor func(context.Context, string) (FlavorSnapshot, error)
	GetPorts  func(ctx context.Context, projectID, deviceID string) ([]PortSnapshot, error)
}

type Result struct {
	Evidence team.Evidence
	Role     string
	Project  string
	Sequence int
}

type Broker struct {
	readers ReaderFuncs
	max     int
	mu      sync.Mutex
	used    int
}

func NewBroker(readers ReaderFuncs, maxCalls int) (*Broker, error) {
	if readers.GetServer == nil || readers.GetFlavor == nil || readers.GetPorts == nil {
		return nil, fmt.Errorf("all three read adapters are required")
	}
	if maxCalls <= 0 {
		return nil, fmt.Errorf("maxCalls must be positive")
	}
	return &Broker{readers: readers, max: maxCalls}, nil
}

func AllowedTools(role string) []string {
	switch role {
	case Compute:
		return []string{"get_server", "get_flavor"}
	case Network:
		return []string{"get_server", "get_ports"}
	default:
		return nil
	}
}

func validateAssignment(a Assignment) error {
	if a.Role != Compute && a.Role != Network {
		return fmt.Errorf("%w: unsupported role", ErrDenied)
	}
	if strings.TrimSpace(a.ProjectID) == "" || !uuidRE.MatchString(a.TargetID) {
		return fmt.Errorf("%w: invalid project or target scope", ErrDenied)
	}
	if a.FlavorID != "" && strings.TrimSpace(a.FlavorID) != a.FlavorID {
		return fmt.Errorf("%w: invalid flavor scope", ErrDenied)
	}
	return nil
}

func verifyCall(a Assignment, call Call) error {
	if len(call.Arguments) != 1 {
		return fmt.Errorf("%w: expected exactly one argument", ErrDenied)
	}
	var key, want string
	switch call.Name {
	case "get_server":
		key, want = "server_id", a.TargetID
	case "get_flavor":
		if a.Role != Compute || a.FlavorID == "" {
			return fmt.Errorf("%w: get_flavor not granted", ErrDenied)
		}
		key, want = "flavor_id", a.FlavorID
	case "get_ports":
		if a.Role != Network {
			return fmt.Errorf("%w: get_ports not granted", ErrDenied)
		}
		key, want = "device_id", a.TargetID
	default:
		return fmt.Errorf("%w: tool %q unavailable", ErrDenied, call.Name)
	}
	got, ok := call.Arguments[key]
	if !ok || got != want {
		return fmt.Errorf("%w: %s outside assigned scope", ErrDenied, key)
	}
	return nil
}

func (b *Broker) spend() (int, error) {
	b.mu.Lock()
	defer b.mu.Unlock()
	if b.used >= b.max {
		return 0, ErrBudget
	}
	b.used++
	return b.used, nil
}

func (b *Broker) CallsUsed() int {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.used
}

func (b *Broker) Execute(ctx context.Context, a Assignment, call Call) (Result, error) {
	if err := ctx.Err(); err != nil {
		return Result{}, err
	}
	if err := validateAssignment(a); err != nil {
		return Result{}, err
	}
	if err := verifyCall(a, call); err != nil {
		return Result{}, err
	}
	seq, err := b.spend()
	if err != nil {
		return Result{}, err
	}

	var snapshot any
	switch call.Name {
	case "get_server":
		server, err := b.readers.GetServer(ctx, a.TargetID)
		if err != nil {
			return Result{}, fmt.Errorf("get_server: %w", err)
		}
		if server.ID != a.TargetID || server.ProjectID != a.ProjectID {
			return Result{}, fmt.Errorf("%w: server response outside scope", ErrDenied)
		}
		if a.FlavorID != "" && server.FlavorID != a.FlavorID {
			return Result{}, fmt.Errorf("%w: server flavor differs from verified baseline", ErrDenied)
		}
		snapshot = server
	case "get_flavor":
		flavor, err := b.readers.GetFlavor(ctx, a.FlavorID)
		if err != nil {
			return Result{}, fmt.Errorf("get_flavor: %w", err)
		}
		if flavor.ID != a.FlavorID {
			return Result{}, fmt.Errorf("%w: flavor response outside scope", ErrDenied)
		}
		snapshot = flavor
	case "get_ports":
		ports, err := b.readers.GetPorts(ctx, a.ProjectID, a.TargetID)
		if err != nil {
			return Result{}, fmt.Errorf("get_ports: %w", err)
		}
		if len(ports) > 64 {
			return Result{}, fmt.Errorf("%w: too many ports", ErrDenied)
		}
		for _, port := range ports {
			if port.DeviceID != a.TargetID || port.ProjectID != a.ProjectID {
				return Result{}, fmt.Errorf("%w: port response outside scope", ErrDenied)
			}
		}
		snapshot = ports
	}
	if err := ctx.Err(); err != nil {
		return Result{}, err
	}
	data, err := json.Marshal(snapshot)
	if err != nil {
		return Result{}, fmt.Errorf("encode evidence: %w", err)
	}
	if len(data) > 16*1024 {
		return Result{}, fmt.Errorf("%w: evidence size limit", ErrDenied)
	}
	id, err := randomEvidenceID()
	if err != nil {
		return Result{}, err
	}
	return Result{
		Evidence: team.Evidence{ID: id, TargetID: a.TargetID, Tool: call.Name, ObservedAt: time.Now().UTC(), Data: data},
		Role:     a.Role, Project: a.ProjectID, Sequence: seq,
	}, nil
}

func randomEvidenceID() (string, error) {
	bytes := make([]byte, 16)
	if _, err := rand.Read(bytes); err != nil {
		return "", fmt.Errorf("create evidence ID: %w", err)
	}
	return "E-" + hex.EncodeToString(bytes), nil
}
