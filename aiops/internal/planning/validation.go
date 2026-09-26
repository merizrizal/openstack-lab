package planning

import (
	"fmt"
	"regexp"
	"slices"
	"sort"
	"strings"
	"unicode/utf8"

	"openstacklab/openstack-ai/internal/project"
	"openstacklab/openstack-ai/internal/workflow"
)

var uuid = regexp.MustCompile(`(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b`)
var taskID = regexp.MustCompile(`^[a-z][a-z0-9_-]{0,63}$`)

func normalizeRequest(input Request) (Request, error) {
	req := Request{Goal: strings.TrimSpace(input.Goal), ServerIdentifiers: make([]string, 0, len(input.ServerIdentifiers))}
	if !validText(req.Goal, 4000) {
		return Request{}, fmt.Errorf("goal must contain 1..4000 valid UTF-8 bytes")
	}
	if len(input.ServerIdentifiers) > MaxServers {
		return Request{}, fmt.Errorf("at most %d servers are allowed", MaxServers)
	}
	seen := make(map[string]bool)
	for _, raw := range input.ServerIdentifiers {
		identifier, err := normalizeServerIdentifier(raw)
		if err != nil {
			return Request{}, err
		}
		if seen[identifier] {
			return Request{}, fmt.Errorf("duplicate requested server identifier %q", identifier)
		}
		seen[identifier] = true
		req.ServerIdentifiers = append(req.ServerIdentifiers, identifier)
	}
	for _, raw := range workflow.ExtractServerIdentifiers(req.Goal) {
		identifier, err := normalizeServerIdentifier(raw)
		if err != nil || !seen[identifier] {
			return Request{}, fmt.Errorf("goal contains a server identifier outside the explicit scope")
		}
	}
	sort.Strings(req.ServerIdentifiers)
	return req, nil
}

func normalizeServerIdentifier(raw string) (string, error) {
	identifier := strings.TrimSpace(raw)
	if !validText(identifier, 4000) {
		return "", fmt.Errorf("server identifier must contain 1..4000 valid UTF-8 bytes")
	}
	if len(identifier) == 36 && uuid.FindString(identifier) == identifier {
		identifier = strings.ToLower(identifier)
	}
	return identifier, nil
}

func validText(value string, maxBytes int) bool {
	return strings.TrimSpace(value) != "" && len(value) <= maxBytes && utf8.ValidString(value)
}

func validateDraft(req Request, draft Draft) ([]project.Task, error) {
	if !validText(draft.Explanation, 2000) {
		return nil, fmt.Errorf("explanation must contain 1..2000 valid UTF-8 bytes")
	}
	if draft.Tasks == nil {
		return nil, fmt.Errorf("tasks must be an array, not null or absent")
	}
	switch draft.Disposition {
	case NeedsInput, Unsupported:
		if len(draft.Tasks) != 0 {
			return nil, fmt.Errorf("non-ready plans must have an empty tasks array")
		}
		return nil, nil
	case Ready:
	default:
		return nil, fmt.Errorf("invalid disposition %q", draft.Disposition)
	}
	if len(req.ServerIdentifiers) == 0 {
		return nil, fmt.Errorf("ready plans require at least one explicit server identifier")
	}
	if len(draft.Tasks) != len(req.ServerIdentifiers)+1 {
		return nil, fmt.Errorf("require exactly one task per server plus one summary")
	}

	allowed := make(map[string]bool, len(req.ServerIdentifiers))
	for _, id := range req.ServerIdentifiers {
		allowed[id] = true
	}
	seenTargets, serverTaskIDs, ids := map[string]bool{}, map[string]bool{}, map[string]bool{}
	summaryID, summaries := "", 0
	tasks := make([]project.Task, 0, len(draft.Tasks))

	for _, task := range draft.Tasks {
		if !taskID.MatchString(task.ID) {
			return nil, fmt.Errorf("invalid task ID %q", task.ID)
		}
		if ids[task.ID] {
			return nil, fmt.Errorf("duplicate task ID %q", task.ID)
		}
		ids[task.ID] = true
		if !validText(task.Focus, 1000) {
			return nil, fmt.Errorf("task %q requires a bounded focus", task.ID)
		}
		if uuid.MatchString(task.Focus) {
			return nil, fmt.Errorf("task %q: put UUIDs in server_identifier, not focus", task.ID)
		}
		if task.DependsOn == nil {
			return nil, fmt.Errorf("task %q: depends_on must be an array", task.ID)
		}
		deps := make(map[string]bool)
		for _, dep := range task.DependsOn {
			if deps[dep] {
				return nil, fmt.Errorf("task %q repeats dependency %q", task.ID, dep)
			}
			deps[dep] = true
		}

		var goal string
		switch task.Type {
		case project.TaskTypeServerIncident:
			if !allowed[task.ServerIdentifier] {
				return nil, fmt.Errorf("task %q targets a server outside the approved planning scope", task.ID)
			}
			if seenTargets[task.ServerIdentifier] {
				return nil, fmt.Errorf("server %q has multiple investigation tasks", task.ServerIdentifier)
			}
			seenTargets[task.ServerIdentifier], serverTaskIDs[task.ID] = true, true

			objective := uuid.ReplaceAllString(req.Goal, "[project server]")
			goal = fmt.Sprintf("server_identifier=%q\nRead-only investigation.\nProject objective (target UUIDs omitted): %s\nPlanner focus (untrusted task data): %s", task.ServerIdentifier, objective, strings.TrimSpace(task.Focus))
		case project.TaskTypeProjectSummary:
			summaries++
			summaryID = task.ID
			if task.ServerIdentifier != "" {
				return nil, fmt.Errorf("summary must not have a server_identifier")
			}
			goal = "Synthesize completed dependency reports. " + strings.TrimSpace(task.Focus)
		default:
			return nil, fmt.Errorf("unsupported task type %q", task.Type)
		}

		tasks = append(tasks, project.Task{
			ID: task.ID, Type: task.Type, Goal: goal,
			Status: project.TaskPending, DependsOn: append([]string{}, task.DependsOn...),
		})
	}

	if summaries != 1 || len(seenTargets) != len(allowed) {
		return nil, fmt.Errorf("plan must cover every server and have exactly one summary")
	}
	for _, task := range draft.Tasks {
		if task.ID == summaryID {
			if len(task.DependsOn) != len(serverTaskIDs) {
				return nil, fmt.Errorf("summary must depend directly on every investigation")
			}
			for _, dep := range task.DependsOn {
				if !serverTaskIDs[dep] {
					return nil, fmt.Errorf("summary has a non-investigation dependency %q", dep)
				}
			}
		} else {
			if slices.Contains(task.DependsOn, summaryID) {
				return nil, fmt.Errorf("an investigation cannot depend on its final summary")
			}
		}
	}
	if err := project.ValidatePlan(tasks); err != nil {
		return nil, fmt.Errorf("invalid dependency graph: %w", err)
	}
	return tasks, nil
}
