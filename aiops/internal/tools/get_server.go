package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"regexp"
	"strings"
	"time"

	"github.com/gophercloud/gophercloud/v2"
	"github.com/gophercloud/gophercloud/v2/openstack/compute/v2/servers"
)

type GetServerTool struct {
	compute *gophercloud.ServiceClient
}

func NewGetServerTool(compute *gophercloud.ServiceClient) *GetServerTool {
	return &GetServerTool{compute: compute}
}

func (t *GetServerTool) Name() string {
	return "get_server"
}

func (t *GetServerTool) Description() string {
	return `
Retrieve current information about one OpenStack Nova server
using its exact server UUID or server name.

This tool is read-only.
`
}

type getServerArguments struct {
	ServerIdentifier string `json:"server_identifier"`
}

type ServerFaultObservation struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
	Details string `json:"details,omitempty"`
}

type ServerObservation struct {
	ID               string                  `json:"id"`
	Name             string                  `json:"name"`
	Status           string                  `json:"status"`
	VMState          string                  `json:"vm_state,omitempty"`
	TaskState        string                  `json:"task_state,omitempty"`
	FlavorID         string                  `json:"flavor_id,omitempty"`
	AvailabilityZone string                  `json:"availability_zone,omitempty"`
	Host             string                  `json:"host,omitempty"`
	Created          string                  `json:"created,omitempty"`
	Updated          string                  `json:"updated,omitempty"`
	Fault            *ServerFaultObservation `json:"fault,omitempty"`
}

func (t *GetServerTool) Execute(ctx context.Context, rawArguments json.RawMessage) (json.RawMessage, error) {
	var arguments getServerArguments

	decoder := json.NewDecoder(strings.NewReader(string(rawArguments)))

	decoder.DisallowUnknownFields()

	if err := decoder.Decode(&arguments); err != nil {
		return nil, fmt.Errorf("decode get_server arguments: %w", err)
	}

	arguments.ServerIdentifier = strings.TrimSpace(arguments.ServerIdentifier)

	if arguments.ServerIdentifier == "" {
		return nil, fmt.Errorf("server_identifier is required")
	}

	server, err := t.resolveServer(ctx, arguments.ServerIdentifier)
	if err != nil {
		return nil, fmt.Errorf("get Nova server %q: %w", arguments.ServerIdentifier, err)
	}

	observation := ServerObservation{
		ID:               server.ID,
		Name:             server.Name,
		Status:           server.Status,
		VMState:          server.VmState,
		TaskState:        server.TaskState,
		FlavorID:         mapString(server.Flavor, "id"),
		AvailabilityZone: server.AvailabilityZone,
		Host:             server.Host,
		Created:          formatTime(server.Created),
		Updated:          formatTime(server.Updated),
	}

	if server.Fault.Code != 0 ||
		server.Fault.Message != "" ||
		server.Fault.Details != "" {
		observation.Fault = &ServerFaultObservation{
			Code:    server.Fault.Code,
			Message: truncate(server.Fault.Message, 2000),
			Details: truncate(server.Fault.Details, 4000),
		}
	}

	result, err := json.Marshal(observation)
	if err != nil {
		return nil, fmt.Errorf("encode server observation: %w", err)
	}

	return result, nil
}

var serverUUIDPattern = regexp.MustCompile(`(?i)^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`)

func (t *GetServerTool) resolveServer(ctx context.Context, identifier string) (*servers.Server, error) {
	if serverUUIDPattern.MatchString(identifier) {
		return servers.Get(ctx, t.compute, identifier).Extract()
	}

	allPages, err := servers.List(t.compute, servers.ListOpts{Name: identifier}).AllPages(ctx)
	if err != nil {
		return nil, fmt.Errorf("list Nova servers by name: %w", err)
	}

	candidates, err := servers.ExtractServers(allPages)
	if err != nil {
		return nil, fmt.Errorf("decode Nova servers by name: %w", err)
	}

	matches := make([]servers.Server, 0, len(candidates))
	for _, candidate := range candidates {
		if candidate.Name == identifier {
			matches = append(matches, candidate)
		}
	}

	switch len(matches) {
	case 0:
		return nil, gophercloud.ErrResourceNotFound{
			Name:         identifier,
			ResourceType: "server",
		}
	case 1:
		return servers.Get(ctx, t.compute, matches[0].ID).Extract()
	default:
		return nil, gophercloud.ErrMultipleResourcesFound{
			Name:         identifier,
			Count:        len(matches),
			ResourceType: "server",
		}
	}
}

func truncate(value string, max int) string {
	if len(value) <= max {
		return value
	}

	return value[:max] + "...[truncated]"
}

func mapString(values map[string]any, key string) string {
	value, _ := values[key].(string)
	return strings.TrimSpace(value)
}

func formatTime(value time.Time) string {
	if value.IsZero() {
		return ""
	}

	return value.UTC().Format(time.RFC3339)
}
