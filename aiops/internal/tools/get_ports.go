package tools

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"regexp"
	"strings"

	"github.com/gophercloud/gophercloud/v2"
	"github.com/gophercloud/gophercloud/v2/openstack/networking/v2/ports"
	"github.com/gophercloud/gophercloud/v2/pagination"
)

const (
	maxPortRecords = 32
	maxPortPages   = 4
)

var projectIDPattern = regexp.MustCompile(`(?i)^(?:[0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$`)

type GetPortsTool struct {
	network   *gophercloud.ServiceClient
	projectID string
}

func NewGetPortsTool(network *gophercloud.ServiceClient, approvedProjectID string) *GetPortsTool {
	return &GetPortsTool{network: network, projectID: approvedProjectID}
}

func (t *GetPortsTool) Name() string {
	return "get_ports"
}

func (t *GetPortsTool) Description() string {
	return "List up to 32 Neutron ports for one exact server UUID in the configured project. This tool is read-only."
}

type getPortsArguments struct {
	ServerID string `json:"server_id"`
}

type PortObservation struct {
	ID           string `json:"id"`
	NetworkID    string `json:"network_id"`
	DeviceID     string `json:"device_id"`
	Status       string `json:"status"`
	AdminStateUp bool   `json:"admin_state_up"`
}

type PortsObservation struct {
	ServerID  string            `json:"server_id"`
	ProjectID string            `json:"project_id"`
	Ports     []PortObservation `json:"ports"`
}

func (t *GetPortsTool) Execute(ctx context.Context, rawArguments json.RawMessage) (json.RawMessage, error) {
	if len(rawArguments) > 2048 {
		return nil, fmt.Errorf("get_ports arguments are too large")
	}

	var arguments getPortsArguments
	decoder := json.NewDecoder(bytes.NewReader(rawArguments))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&arguments); err != nil {
		return nil, fmt.Errorf("decode get_ports arguments: %w", err)
	}
	if err := decoder.Decode(new(any)); err != io.EOF {
		return nil, fmt.Errorf("get_ports arguments must contain exactly one JSON object")
	}

	arguments.ServerID = strings.TrimSpace(arguments.ServerID)
	if !serverUUIDPattern.MatchString(arguments.ServerID) {
		return nil, fmt.Errorf("server_id must be an exact UUID")
	}

	observation := PortsObservation{
		ServerID:  arguments.ServerID,
		ProjectID: t.projectID,
		Ports:     make([]PortObservation, 0),
	}

	opts := ports.ListOpts{
		DeviceID:  arguments.ServerID,
		ProjectID: t.projectID,
		Limit:     maxPortRecords + 1,
	}

	pages := 0
	err := ports.List(t.network, opts).EachPage(ctx, func(_ context.Context, page pagination.Page) (bool, error) {
		pages++
		if pages > maxPortPages {
			return false, fmt.Errorf("get_ports exceeded %d pages", maxPortPages)
		}

		items, err := ports.ExtractPorts(page)
		if err != nil {
			return false, fmt.Errorf("extract Neutron ports: %w", err)
		}
		if len(items) > maxPortRecords-len(observation.Ports) {
			return false, fmt.Errorf("get_ports exceeded %d port records", maxPortRecords)
		}

		for _, port := range items {
			if port.ID == "" || !sameOpenStackID(port.DeviceID, arguments.ServerID) {
				return false, fmt.Errorf("Neutron returned a port with an unexpected device")
			}

			ownerID := port.ProjectID
			if ownerID == "" {
				ownerID = port.TenantID
			}
			if !sameOpenStackID(ownerID, t.projectID) || (port.ProjectID != "" && port.TenantID != "" && !sameOpenStackID(port.ProjectID, port.TenantID)) {
				return false, fmt.Errorf("Neutron returned a port with an unexpected project")
			}

			observation.Ports = append(observation.Ports, PortObservation{
				ID:           port.ID,
				NetworkID:    port.NetworkID,
				DeviceID:     port.DeviceID,
				Status:       port.Status,
				AdminStateUp: port.AdminStateUp,
			})
		}

		return true, nil
	})
	if err != nil {
		return nil, fmt.Errorf("list Neutron ports for server %q: %w", arguments.ServerID, err)
	}

	result, err := json.Marshal(observation)
	if err != nil {
		return nil, fmt.Errorf("encode ports observation: %w", err)
	}

	return result, nil
}

func sameOpenStackID(a, b string) bool {
	canonical := func(value string) string {
		return strings.ReplaceAll(strings.ToLower(strings.TrimSpace(value)), "-", "")
	}
	return canonical(a) == canonical(b)
}
