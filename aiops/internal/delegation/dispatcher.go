package delegation

import (
	"context"
	"encoding/json"
	"fmt"
	"slices"
	"strings"
	"time"

	"openstacklab/openstack-ai/internal/team"
)

type registered struct {
	agent Specialist
	tools map[string]bool
}

type Dispatcher struct {
	selector    Selector
	fallback    team.Investigator
	specialists map[string]registered
	timeout     time.Duration
}

func NewDispatcher(selector Selector, fallback team.Investigator, timeout time.Duration, entries ...Registration) (*Dispatcher, error) {
	if selector == nil || fallback == nil || timeout <= 0 {
		return nil, fmt.Errorf("selector, fallback, and a positive timeout are required")
	}

	d := &Dispatcher{selector: selector, fallback: fallback, specialists: make(map[string]registered), timeout: timeout}
	for _, entry := range entries {
		if entry.Agent == nil {
			return nil, fmt.Errorf("specialist cannot be nil")
		}
		name := entry.Agent.Name()
		if name != Compute && name != Network {
			return nil, fmt.Errorf("unsupported specialist %q", name)
		}
		if _, exists := d.specialists[name]; exists {
			return nil, fmt.Errorf("duplicate specialist %q", name)
		}
		if len(entry.AllowedEvidenceTools) == 0 {
			return nil, fmt.Errorf("specialist %q requires an evidence allowlist", name)
		}

		tools := make(map[string]bool, len(entry.AllowedEvidenceTools))
		for _, tool := range entry.AllowedEvidenceTools {
			if strings.TrimSpace(tool) == "" || tools[tool] {
				return nil, fmt.Errorf("invalid or duplicate evidence source %q for %q", tool, name)
			}
			tools[tool] = true
		}
		d.specialists[name] = registered{agent: entry.Agent, tools: tools}
	}
	return d, nil
}

func (d *Dispatcher) Run(ctx context.Context, work team.Work) (Result, error) {
	var result Result
	if err := checkWork(work); err != nil {
		return result, err
	}
	ctx, cancel := context.WithTimeout(ctx, d.timeout)
	defer cancel()
	if err := ctx.Err(); err != nil {
		return result, err
	}
	started := time.Now()

	selection, err := d.selector.Select(ctx, cloneWork(work))
	if err != nil {
		return result, fmt.Errorf("select specialist: %w", err)
	}
	if err := ctx.Err(); err != nil {
		return result, err
	}
	result.Selection = selection

	switch selection.Action {
	case Direct:
		if selection.Specialist != None || selection.Objective != "" || len(selection.EvidenceIDs) != 0 || strings.TrimSpace(selection.Reason) == "" {
			return result, fmt.Errorf("direct decision contains delegation fields or lacks reason")
		}
		report, err := d.fallback.Investigate(ctx, cloneWork(work))
		if err != nil {
			return result, fmt.Errorf("general investigator: %w", err)
		}
		if err := ctx.Err(); err != nil {
			return result, err
		}
		if err := checkReport(report, work.Input.Evidence); err != nil {
			return result, fmt.Errorf("invalid general report: %w", err)
		}
		result.Report = cloneReport(report)

	case Delegate:
		registration, exists := d.specialists[selection.Specialist]
		if !exists {
			return result, fmt.Errorf("specialist %q is not registered", selection.Specialist)
		}
		if strings.TrimSpace(selection.Objective) == "" || len(selection.Objective) > 1024 || strings.TrimSpace(selection.Reason) == "" || len(selection.Reason) > 1024 {
			return result, fmt.Errorf("delegation requires a bounded objective and reason")
		}
		selected, err := selectEvidence(work.Input, selection.EvidenceIDs, registration.tools)
		if err != nil {
			return result, fmt.Errorf("denied evidence selection: %w", err)
		}

		assignment := Assignment{
			Goal: work.Input.Goal, TargetID: work.Input.TargetID, Objective: selection.Objective,
			Evidence: selected, Revision: work.Revision, Previous: cloneReportPtr(work.Previous), Feedback: cloneReviewPtr(work.Feedback),
		}
		report, err := registration.agent.Analyze(ctx, assignment)
		if err != nil {
			return result, fmt.Errorf("specialist %q: %w", selection.Specialist, err)
		}
		if err := ctx.Err(); err != nil {
			return result, err
		}
		if err := checkReport(report, selected); err != nil {
			return result, fmt.Errorf("invalid specialist report: %w", err)
		}
		result.Report = cloneReport(report)
		result.Delegated = true
		result.EvidenceIDs = slices.Clone(selection.EvidenceIDs)

	default:
		return result, fmt.Errorf("unsupported selection action %q", selection.Action)
	}
	result.Elapsed = time.Since(started)
	return result, nil
}

type InvestigatorAdapter struct {
	dispatcher *Dispatcher
	onResult   func(context.Context, Result) error
}

func NewInvestigatorAdapter(dispatcher *Dispatcher, onResult func(context.Context, Result) error) (*InvestigatorAdapter, error) {
	if dispatcher == nil {
		return nil, fmt.Errorf("dispatcher is required")
	}
	return &InvestigatorAdapter{dispatcher: dispatcher, onResult: onResult}, nil
}

func (a *InvestigatorAdapter) Investigate(ctx context.Context, work team.Work) (team.Report, error) {
	result, err := a.dispatcher.Run(ctx, work)
	if err != nil {
		return team.Report{}, err
	}
	if a.onResult != nil {
		if err := a.onResult(ctx, result); err != nil {
			return team.Report{}, fmt.Errorf("record delegation: %w", err)
		}
	}
	return cloneReport(result.Report), nil
}

func selectEvidence(in team.Input, ids []string, allowed map[string]bool) ([]team.Evidence, error) {
	if len(ids) == 0 || len(ids) > 16 {
		return nil, fmt.Errorf("delegation requires 1..16 evidence IDs")
	}
	known := make(map[string]team.Evidence, len(in.Evidence))
	for _, e := range in.Evidence {
		known[e.ID] = e
	}
	seen := make(map[string]bool, len(ids))
	selected := make([]team.Evidence, 0, len(ids))
	for _, id := range ids {
		evidence, exists := known[id]
		if !exists || seen[id] {
			return nil, fmt.Errorf("unknown or duplicate evidence ID %q", id)
		}
		if !allowed[evidence.Tool] {
			return nil, fmt.Errorf("source %q is not available to specialist", evidence.Tool)
		}
		if evidence.TargetID != in.TargetID {
			return nil, fmt.Errorf("evidence %q is outside the target scope", id)
		}
		seen[id] = true
		copy := evidence
		copy.Data = slices.Clone(evidence.Data)
		selected = append(selected, copy)
	}
	return selected, nil
}

func checkWork(work team.Work) error {
	in := work.Input
	if work.Revision <= 0 || strings.TrimSpace(in.Goal) == "" || len(in.Goal) > 8192 || strings.TrimSpace(in.TargetID) == "" {
		return fmt.Errorf("work requires bounded goal, target, and positive revision")
	}
	if len(in.Evidence) == 0 || len(in.Evidence) > 32 {
		return fmt.Errorf("work requires 1..32 evidence records")
	}
	seen := make(map[string]bool)
	total := 0
	for _, e := range in.Evidence {
		if strings.TrimSpace(e.ID) == "" || seen[e.ID] || e.TargetID != in.TargetID || strings.TrimSpace(e.Tool) == "" || e.ObservedAt.IsZero() || !json.Valid(e.Data) || string(e.Data) == "null" {
			return fmt.Errorf("invalid, duplicated, or out-of-scope evidence %q", e.ID)
		}
		seen[e.ID] = true
		total += len(e.Data)
	}
	if total > 128*1024 {
		return fmt.Errorf("evidence exceeds 128 KiB")
	}
	return nil
}

func checkReport(report team.Report, evidence []team.Evidence) error {
	if len(report.Claims) == 0 || len(report.Claims) > 32 || report.MissingEvidence == nil || len(report.MissingEvidence) > 16 {
		return fmt.Errorf("report requires 1..32 claims and a bounded missing_evidence array")
	}
	known := make(map[string]bool, len(evidence))
	for _, e := range evidence {
		known[e.ID] = true
	}
	seenClaims := make(map[string]bool, len(report.Claims))
	for _, claim := range report.Claims {
		if strings.TrimSpace(claim.ID) == "" || seenClaims[claim.ID] || strings.TrimSpace(claim.Text) == "" || len(claim.Text) > 4096 || len(claim.EvidenceIDs) == 0 {
			return fmt.Errorf("invalid or duplicated claim %q", claim.ID)
		}
		seenClaims[claim.ID] = true
		switch claim.Kind {
		case "observation", "interpretation", "hypothesis":
		default:
			return fmt.Errorf("invalid claim kind %q", claim.Kind)
		}
		seenReferences := make(map[string]bool)
		for _, id := range claim.EvidenceIDs {
			if !known[id] || seenReferences[id] {
				return fmt.Errorf("claim %q cites unavailable or duplicate evidence %q", claim.ID, id)
			}
			seenReferences[id] = true
		}
	}
	for _, missing := range report.MissingEvidence {
		if strings.TrimSpace(missing) == "" || len(missing) > 2048 {
			return fmt.Errorf("invalid missing-evidence description")
		}
	}
	return nil
}

func cloneWork(work team.Work) team.Work {
	work.Input = cloneInput(work.Input)
	work.Previous = cloneReportPtr(work.Previous)
	work.Feedback = cloneReviewPtr(work.Feedback)
	return work
}

func cloneInput(in team.Input) team.Input {
	in.Evidence = slices.Clone(in.Evidence)
	for i := range in.Evidence {
		in.Evidence[i].Data = slices.Clone(in.Evidence[i].Data)
	}
	return in
}

func cloneReport(report team.Report) team.Report {
	report.Claims = slices.Clone(report.Claims)
	for i := range report.Claims {
		report.Claims[i].EvidenceIDs = slices.Clone(report.Claims[i].EvidenceIDs)
	}
	report.MissingEvidence = slices.Clone(report.MissingEvidence)
	return report
}

func cloneReportPtr(report *team.Report) *team.Report {
	if report == nil {
		return nil
	}
	copy := cloneReport(*report)
	return &copy
}

func cloneReviewPtr(review *team.Review) *team.Review {
	if review == nil {
		return nil
	}
	copy := *review
	copy.Issues = slices.Clone(copy.Issues)
	return &copy
}
