package planning

import (
	"context"
	"errors"

	"openstacklab/openstack-ai/internal/project"
)

const (
	Ready        = "ready"
	NeedsInput   = "needs_input"
	Unsupported  = "unsupported"
	MaxServers   = 8
	MaxPlanBytes = 64 * 1024
)

var ErrNotReady = errors.New("plan is not ready for execution")

type Request struct {
	Goal              string   `json:"goal"`
	ServerIdentifiers []string `json:"server_identifiers"`
}

type ProposedTask struct {
	ID               string   `json:"id"`
	Type             string   `json:"type"`
	ServerIdentifier string   `json:"server_identifier"`
	Focus            string   `json:"focus"`
	DependsOn        []string `json:"depends_on"`
}

type Draft struct {
	Disposition string         `json:"disposition"`
	Explanation string         `json:"explanation"`
	Tasks       []ProposedTask `json:"tasks"`
}

type ProjectStarter interface {
	Start(ctx context.Context, goal string, tasks []project.Task) (project.State, error)
}
