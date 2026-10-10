package workflow

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"openstacklab/openstack-ai/internal/agent"
	"openstacklab/openstack-ai/internal/ai"
	"openstacklab/openstack-ai/internal/team"
)

func reviewSnapshot(ctx context.Context, client ai.StructuredClient, input team.Input) (team.Result, error) {
	if client == nil {
		return team.Result{}, fmt.Errorf("structured AI client is required")
	}

	generate := func(ctx context.Context, instructions, payload string, schema []byte) (string, error) {
		response, err := client.ChatStructured(ctx, []ai.Message{
			{Role: "system", Content: instructions},
			{Role: "user", Content: payload},
		}, schema)
		if err != nil {
			return "", err
		}
		return response.Text, nil
	}

	investigator, err := team.NewModelInvestigator(generate)
	if err != nil {
		return team.Result{}, err
	}
	reviewer, err := team.NewModelReviewer(generate)
	if err != nil {
		return team.Result{}, err
	}
	coordinator, err := team.NewCoordinator(investigator, reviewer, 1, 5*time.Minute)
	if err != nil {
		return team.Result{}, err
	}
	return coordinator.Run(ctx, input)
}

type reviewSnapshotStep struct {
	runtime *agent.Runtime
	client  ai.StructuredClient
}

func (s *reviewSnapshotStep) Name() StepName {
	return StepReviewSnapshot
}

func (s *reviewSnapshotStep) Run(ctx context.Context, state *State) (StepName, error) {
	if err := ctx.Err(); err != nil {
		return "", err
	}
	if strings.TrimSpace(state.AgentInvestigationID) == "" {
		return "", fmt.Errorf("agent investigation ID is required for evidence review")
	}

	snapshot, err := s.runtime.Resume(ctx, state.AgentInvestigationID)
	if err != nil {
		return "", fmt.Errorf("load agent snapshot for evidence review: %w", err)
	}
	if snapshot.Status != agent.StatusCompleted {
		return "", fmt.Errorf("agent snapshot is not completed: %s", snapshot.Status)
	}

	input, err := reviewInput(state.Goal, state.ServerIdentifier, snapshot)
	if err != nil {
		return "", fmt.Errorf("prepare evidence review: %w", err)
	}

	result, err := reviewSnapshot(ctx, s.client, input)
	state.EvidenceReview = &result
	if err != nil {
		return "", fmt.Errorf("review evidence snapshot: %w", err)
	}
	if result.Outcome != team.Accepted && result.Outcome != team.NeedsHuman {
		return "", fmt.Errorf("evidence review returned unsupported outcome %q", result.Outcome)
	}

	return StepRenderReport, nil
}

func reviewInput(goal, targetID string, snapshot agent.Result) (team.Input, error) {
	if len(snapshot.Observations) == 0 {
		return team.Input{}, fmt.Errorf("agent snapshot contains no observations")
	}

	baselineFlavorID := ""
	for _, observation := range snapshot.Observations {
		if observation.Tool != "get_server" || len(observation.Result) == 0 {
			continue
		}
		var server struct {
			FlavorID string `json:"flavor_id"`
		}
		if err := json.Unmarshal(observation.Result, &server); err != nil {
			return team.Input{}, fmt.Errorf("decode server observation at step %d: %w", observation.Step, err)
		}
		if baselineFlavorID == "" {
			baselineFlavorID = strings.TrimSpace(server.FlavorID)
		}
	}

	evidence := make([]team.Evidence, 0, len(snapshot.Observations))
	for index, observation := range snapshot.Observations {
		if observation.ObservedAt.IsZero() {
			return team.Input{}, fmt.Errorf("observation at step %d has no observation timestamp", observation.Step)
		}
		if len(observation.Result) == 0 && strings.TrimSpace(observation.Error) == "" {
			return team.Input{}, fmt.Errorf("observation at step %d contains neither result nor error", observation.Step)
		}

		switch observation.Tool {
		case "get_server":
			var arguments struct {
				ServerIdentifier string `json:"server_identifier"`
			}
			if err := json.Unmarshal(observation.Arguments, &arguments); err != nil {
				return team.Input{}, fmt.Errorf("decode get_server arguments at step %d: %w", observation.Step, err)
			}
			if strings.TrimSpace(arguments.ServerIdentifier) != targetID {
				return team.Input{}, fmt.Errorf("get_server observation at step %d is outside target scope", observation.Step)
			}
		case "get_flavor":
			var arguments struct {
				FlavorID string `json:"flavor_id"`
			}
			if err := json.Unmarshal(observation.Arguments, &arguments); err != nil {
				return team.Input{}, fmt.Errorf("decode get_flavor arguments at step %d: %w", observation.Step, err)
			}
			if baselineFlavorID == "" || strings.TrimSpace(arguments.FlavorID) != baselineFlavorID {
				return team.Input{}, fmt.Errorf("get_flavor observation at step %d is outside target scope", observation.Step)
			}
		default:
			return team.Input{}, fmt.Errorf("unsupported observation tool %q", observation.Tool)
		}

		data, err := json.Marshal(struct {
			Step      int             `json:"step"`
			Arguments json.RawMessage `json:"arguments,omitempty"`
			Result    json.RawMessage `json:"result,omitempty"`
			Error     string          `json:"error,omitempty"`
		}{
			Step:      observation.Step,
			Arguments: observation.Arguments,
			Result:    observation.Result,
			Error:     observation.Error,
		})
		if err != nil {
			return team.Input{}, fmt.Errorf("encode observation at step %d: %w", observation.Step, err)
		}

		evidence = append(evidence, team.Evidence{
			ID:         fmt.Sprintf("E%d", index+1),
			TargetID:   targetID,
			Tool:       observation.Tool,
			ObservedAt: observation.ObservedAt,
			Data:       data,
		})
	}

	return team.Input{Goal: goal, TargetID: targetID, Evidence: evidence}, nil
}

func formatReviewedSnapshot(result *team.Result) (string, error) {
	if result == nil || len(result.Rounds) == 0 {
		return "", fmt.Errorf("evidence review contains no report rounds")
	}
	if result.Outcome != team.Accepted && result.Outcome != team.NeedsHuman {
		return "", fmt.Errorf("evidence review is not publishable: %s", result.Outcome)
	}

	round := result.Rounds[len(result.Rounds)-1]
	var output strings.Builder
	fmt.Fprintf(&output, "Evidence review: %s\n", result.Outcome)
	fmt.Fprintln(&output, "Claims:")
	for _, claim := range round.Report.Claims {
		fmt.Fprintf(&output, "- [%s] %s (evidence: %s)\n", claim.Kind, claim.Text, strings.Join(claim.EvidenceIDs, ", "))
	}
	if len(round.Report.MissingEvidence) > 0 {
		fmt.Fprintln(&output, "Missing evidence:")
		for _, gap := range round.Report.MissingEvidence {
			fmt.Fprintf(&output, "- %s\n", gap)
		}
	}
	if round.Review != nil && len(round.Review.Issues) > 0 {
		fmt.Fprintln(&output, "Review concerns:")
		for _, issue := range round.Review.Issues {
			if issue.ClaimID != "" {
				fmt.Fprintf(&output, "- %s: %s\n", issue.ClaimID, issue.Reason)
			} else {
				fmt.Fprintf(&output, "- %s\n", issue.Reason)
			}
		}
	}
	return strings.TrimSpace(output.String()), nil
}
