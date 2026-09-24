package project

import (
	"context"
	"time"
)

const (
	StatusRunning   = "running"
	StatusPaused    = "paused"
	StatusCompleted = "completed"
	StatusFailed    = "failed"
)

const (
	TaskPending   = "pending"
	TaskReady     = "ready"
	TaskRunning   = "running"
	TaskPaused    = "paused"
	TaskCompleted = "completed"
	TaskFailed    = "failed"
	TaskBlocked   = "blocked"
)

const (
	TaskTypeServerIncident = "server_incident"
	TaskTypeProjectSummary = "project_summary"
)

type Task struct {
	ID          string     `json:"id"`
	Type        string     `json:"type"`
	Goal        string     `json:"goal"`
	Status      string     `json:"status"`
	DependsOn   []string   `json:"depends_on"`
	WorkflowID  string     `json:"workflow_id,omitempty"`
	Result      string     `json:"result,omitempty"`
	Error       string     `json:"error,omitempty"`
	StartedAt   *time.Time `json:"started_at,omitempty"`
	CompletedAt *time.Time `json:"completed_at,omitempty"`
}

type Event struct {
	Time    time.Time `json:"time"`
	TaskID  string    `json:"task_id,omitempty"`
	Message string    `json:"message"`
}

type State struct {
	ID        string    `json:"id"`
	Goal      string    `json:"goal"`
	Status    string    `json:"status"`
	Tasks     []Task    `json:"tasks"`
	Events    []Event   `json:"events"`
	Error     string    `json:"error,omitempty"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type ExecutionResult struct {
	Output     string
	WorkflowID string
	Paused     bool
}

type Executor interface {
	Type() string
	Execute(ctx context.Context, project State, task Task) (ExecutionResult, error)
}
