package tools

import (
	"context"
	"encoding/json"
	"fmt"
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
using its exact server UUID.

This tool is read-only.
`
}

type getServerArguments struct {
	ServerID string `json:"server_id"`
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

	arguments.ServerID = strings.TrimSpace(arguments.ServerID)

	if arguments.ServerID == "" {
		return nil, fmt.Errorf("server_id is required")
	}

	server, err := servers.Get(ctx, t.compute, arguments.ServerID).Extract()

	if err != nil {
		return nil, fmt.Errorf("get Nova server %q: %w", arguments.ServerID, err)
	}

	observation := ServerObservation{
		ID:               server.ID,
		Name:             server.Name,
		Status:           server.Status,
		VMState:          server.VmState,
		TaskState:        server.TaskState,
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

func truncate(value string, max int) string {
	if len(value) <= max {
		return value
	}

	return value[:max] + "...[truncated]"
}

func formatTime(value time.Time) string {
	if value.IsZero() {
		return ""
	}

	return value.UTC().Format(time.RFC3339)
}
