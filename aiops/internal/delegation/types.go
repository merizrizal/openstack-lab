// Package delegation demonstrates bounded specialist delegation inside the
// existing Stage 9A investigator/reviewer workflow.
package delegation

import (
	"context"
	"time"

	"openstacklab/openstack-ai/internal/team"
)

const (
	Delegate = "delegate"
	Direct   = "direct"
	None     = "none"
	Compute  = "compute"
	Network  = "network"
)

type Selection struct {
	Action      string   `json:"action"`
	Specialist  string   `json:"specialist"`
	Objective   string   `json:"objective"`
	EvidenceIDs []string `json:"evidence_ids"`
	Reason      string   `json:"reason"`
}

type Assignment struct {
	Goal      string          `json:"goal"`
	TargetID  string          `json:"target_id"`
	Objective string          `json:"objective"`
	Evidence  []team.Evidence `json:"evidence"`
	Revision  int             `json:"revision"`
	Previous  *team.Report    `json:"previous,omitempty"`
	Feedback  *team.Review    `json:"feedback,omitempty"`
}

type Selector interface {
	Select(context.Context, team.Work) (Selection, error)
}

type Specialist interface {
	Name() string
	Analyze(context.Context, Assignment) (team.Report, error)
}

type Registration struct {
	Agent                Specialist
	AllowedEvidenceTools []string
}

type Result struct {
	Selection   Selection     `json:"selection"`
	Report      team.Report   `json:"report"`
	Delegated   bool          `json:"delegated"`
	EvidenceIDs []string      `json:"evidence_ids"`
	Elapsed     time.Duration `json:"-"`
}
