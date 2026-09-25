package project

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"openstacklab/openstack-ai/internal/ai"
)

const summaryPrompt = `
You summarize the results of an OpenStack investigation project.

Use only the supplied completed task results.

Rules:

- Do not invent infrastructure facts.
- Clearly identify which task supports each important conclusion.
- Distinguish confirmed findings from unresolved issues.
- Do not claim that you personally inspected OpenStack.
- Do not request tools.
`

type SummaryExecutor struct {
	client ai.Client
}

func NewSummaryExecutor(client ai.Client) *SummaryExecutor {
	return &SummaryExecutor{client: client}
}

func (e *SummaryExecutor) Type() string {
	return TaskTypeProjectSummary
}

func (e *SummaryExecutor) Execute(ctx context.Context, project State, task Task) (ExecutionResult, error) {
	type taskResult struct {
		TaskID string `json:"task_id"`
		Goal   string `json:"goal"`
		Result string `json:"result"`
	}

	results := make([]taskResult, 0, len(task.DependsOn))

	for _, dependency := range task.DependsOn {
		dep := findTask(project, dependency)
		if dep == nil {
			return ExecutionResult{}, fmt.Errorf("summary dependency %q not found", dependency)
		}
		if dep.Status != TaskCompleted {
			return ExecutionResult{}, fmt.Errorf("summary dependency %q is not completed", dependency)
		}

		results = append(results, taskResult{
			TaskID: dep.ID,
			Goal:   dep.Goal,
			Result: dep.Result,
		})
	}

	payload, err := json.Marshal(struct {
		ProjectGoal string       `json:"project_goal"`
		TaskResults []taskResult `json:"task_results"`
	}{
		ProjectGoal: project.Goal,
		TaskResults: results,
	})
	if err != nil {
		return ExecutionResult{}, fmt.Errorf("encode project summary input: %w", err)
	}

	response, err := e.client.Chat(ctx, []ai.Message{
		{Role: "system", Content: summaryPrompt},
		{Role: "user", Content: string(payload)},
	})
	if err != nil {
		return ExecutionResult{}, fmt.Errorf("generate project summary: %w", err)
	}

	output := strings.TrimSpace(response.Text)
	if output == "" {
		return ExecutionResult{}, fmt.Errorf("project summary is empty")
	}

	return ExecutionResult{Output: output}, nil
}

func findTask(project State, id string) *Task {
	for i := range project.Tasks {
		if project.Tasks[i].ID == id {
			return &project.Tasks[i]
		}
	}

	return nil
}
