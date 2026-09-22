package workflow

import (
	"context"
	"encoding/json"
	"time"
)

type StepName string

const (
	StepValidateInput      StepName = "validate_input"
	StepCollectBaseline    StepName = "collect_baseline"
	StepClassify           StepName = "classify"
	StepRoute              StepName = "route"
	StepInvestigateCompute StepName = "investigate_compute"
	StepValidateResult     StepName = "validate_result"
	StepRenderReport       StepName = "render_report"
	StepDone               StepName = "done"
)

const (
	StatusRunning   = "running"
	StatusPaused    = "paused"
	StatusCompleted = "completed"
)

type Transition struct {
	From        StepName  `json:"from"`
	To          StepName  `json:"to,omitempty"`
	StartedAt   time.Time `json:"started_at"`
	CompletedAt time.Time `json:"completed_at"`
	Error       string    `json:"error,omitempty"`
}

type State struct {
	ID                   string          `json:"id"`
	Goal                 string          `json:"goal"`
	Status               string          `json:"status"`
	CurrentStep          StepName        `json:"current_step"`
	ServerIdentifier     string          `json:"server_identifier,omitempty"`
	BaselineArguments    json.RawMessage `json:"baseline_arguments,omitempty"`
	BaselineResult       json.RawMessage `json:"baseline_result,omitempty"`
	Domain               string          `json:"domain,omitempty"`
	ClassificationReason string          `json:"classification_reason,omitempty"`
	AgentInvestigationID string          `json:"agent_investigation_id,omitempty"`
	AgentStatus          string          `json:"agent_status,omitempty"`
	AgentAnswer          string          `json:"agent_answer,omitempty"`
	Outcome              string          `json:"outcome,omitempty"`
	FinalReport          string          `json:"final_report,omitempty"`
	Error                string          `json:"error,omitempty"`
	History              []Transition    `json:"history"`
	CreatedAt            time.Time       `json:"created_at"`
	UpdatedAt            time.Time       `json:"updated_at"`
}

type Step interface {
	Name() StepName
	Run(ctx context.Context, state *State) (StepName, error)
}
