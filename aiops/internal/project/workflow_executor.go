package project

import (
	"context"
	"fmt"
	"strings"

	"openstacklab/openstack-ai/internal/workflow"
)

type WorkflowExecutor struct {
	engine *workflow.Engine
}

func NewWorkflowExecutor(engine *workflow.Engine) *WorkflowExecutor {
	return &WorkflowExecutor{engine: engine}
}

func (e *WorkflowExecutor) Type() string {
	return TaskTypeServerIncident
}

func (e *WorkflowExecutor) Execute(ctx context.Context, project State, task Task) (ExecutionResult, error) {
	var state workflow.State
	var err error

	if strings.TrimSpace(task.WorkflowID) == "" {
		state, err = e.engine.Start(ctx, task.Goal)
	} else {
		state, err = e.engine.Resume(ctx, task.WorkflowID)
	}

	result := ExecutionResult{
		Output:     state.FinalReport,
		WorkflowID: state.ID,
		Paused:     state.Status == workflow.StatusPaused,
	}

	if err != nil {
		return result, err
	}
	if state.Status != workflow.StatusCompleted {
		return result, fmt.Errorf("workflow %q finished with status %q", state.ID, state.Status)
	}

	return result, nil
}
