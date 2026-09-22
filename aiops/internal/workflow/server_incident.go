package workflow

import (
	"context"
	"fmt"
	"regexp"
	"strings"

	"openstacklab/openstack-ai/internal/agent"
	"openstacklab/openstack-ai/internal/tools"
)

var serverIDPattern = regexp.MustCompile(`[a-z0-9]+[_-].[a-z0-9]+`)

func ServerIncidentSteps(
	registry *tools.Registry,
	classifier *Classifier,
	agentRuntime *agent.Runtime,
) []Step {
	return []Step{
		&validateInputStep{},
		&collectBaselineStep{registry: registry},
		&classifyStep{classifier: classifier},
		&routeStep{},
		&investigateComputeStep{runtime: agentRuntime},
		&validateResultStep{},
		&renderReportStep{},
	}
}

type validateInputStep struct{}

func (s *validateInputStep) Name() StepName {
	return StepValidateInput
}

func (s *validateInputStep) Run(ctx context.Context, state *State) (StepName, error) {
	if err := ctx.Err(); err != nil {
		return "", err
	}

	matches := serverIDPattern.FindAllString(state.Goal, -1)

	if len(matches) == 0 {
		return "", fmt.Errorf("workflow requires an exact server ID")
	}
	if len(matches) > 1 {
		return "", fmt.Errorf("workflow accepts exactly one server ID")
	}

	state.ServerIdentifier = strings.ToLower(matches[0])
	return StepCollectBaseline, nil
}

type collectBaselineStep struct {
	registry *tools.Registry
}

func (s *collectBaselineStep) Name() StepName {
	return StepCollectBaseline
}

func (s *collectBaselineStep) Run(ctx context.Context, state *State) (StepName, error) {
	arguments, err := (agent.ToolArguments{ServerIdentifier: state.ServerIdentifier}).JSONForTool("get_server")
	if err != nil {
		return "", fmt.Errorf("encode baseline arguments: %w", err)
	}

	result, err := s.registry.Execute(ctx, "get_server", arguments)
	if err != nil {
		return "", fmt.Errorf("collect server baseline: %w", err)
	}

	state.BaselineArguments = arguments
	state.BaselineResult = result

	return StepClassify, nil
}

type classifyStep struct {
	classifier *Classifier
}

func (s *classifyStep) Name() StepName {
	return StepClassify
}

func (s *classifyStep) Run(ctx context.Context, state *State) (StepName, error) {
	classification, err := s.classifier.Classify(ctx, state.Goal, state.BaselineResult)
	if err != nil {
		return "", err
	}

	state.Domain = classification.Domain
	state.ClassificationReason = classification.Reason

	return StepRoute, nil
}

type routeStep struct{}

func (s *routeStep) Name() StepName {
	return StepRoute
}

func (s *routeStep) Run(ctx context.Context, state *State) (StepName, error) {
	if err := ctx.Err(); err != nil {
		return "", err
	}

	switch state.Domain {
	case "compute":
		return StepInvestigateCompute, nil

	case "network", "storage", "identity", "image", "load_balancing", "unknown":
		state.Outcome = fmt.Sprintf(
			"No workflow is registered for domain %q yet. Classification: %s",
			state.Domain,
			state.ClassificationReason,
		)
		return StepRenderReport, nil

	default:
		return "", fmt.Errorf("unsupported classification domain %q", state.Domain)
	}
}

type investigateComputeStep struct {
	runtime *agent.Runtime
}

func (s *investigateComputeStep) Name() StepName {
	return StepInvestigateCompute
}

func (s *investigateComputeStep) Run(ctx context.Context, state *State) (StepName, error) {
	var result agent.Result
	var err error

	if state.AgentInvestigationID == "" {
		baseline := agent.Observation{
			Step:      1,
			Tool:      "get_server",
			Arguments: state.BaselineArguments,
			Result:    state.BaselineResult,
		}

		result, err = s.runtime.StartWithObservations(ctx, state.Goal, []agent.Observation{baseline})
	} else {
		result, err = s.runtime.Resume(ctx, state.AgentInvestigationID)
	}

	state.AgentInvestigationID = result.InvestigationID
	state.AgentStatus = result.Status
	state.AgentAnswer = result.Answer

	if err != nil {
		return "", fmt.Errorf("compute investigation %q: %w", result.InvestigationID, err)
	}

	return StepValidateResult, nil
}

type validateResultStep struct{}

func (s *validateResultStep) Name() StepName {
	return StepValidateResult
}

func (s *validateResultStep) Run(ctx context.Context, state *State) (StepName, error) {
	if err := ctx.Err(); err != nil {
		return "", err
	}

	if state.AgentStatus != agent.StatusCompleted {
		return "", fmt.Errorf("agent investigation is not completed: %s", state.AgentStatus)
	}

	if strings.TrimSpace(state.AgentAnswer) == "" {
		return "", fmt.Errorf("agent investigation returned no answer")
	}

	return StepRenderReport, nil
}

type renderReportStep struct{}

func (s *renderReportStep) Name() StepName {
	return StepRenderReport
}

func (s *renderReportStep) Run(ctx context.Context, state *State) (StepName, error) {
	if err := ctx.Err(); err != nil {
		return "", err
	}

	findings := strings.TrimSpace(state.AgentAnswer)
	if findings == "" {
		findings = strings.TrimSpace(state.Outcome)
	}

	state.FinalReport = fmt.Sprintf(
		"Server: %s\nDomain: %s\nClassification: %s\nAgent investigation: %s\n\n%s",
		state.ServerIdentifier,
		state.Domain,
		state.ClassificationReason,
		state.AgentInvestigationID,
		findings,
	)

	return StepDone, nil
}
