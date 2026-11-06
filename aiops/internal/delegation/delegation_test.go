package delegation

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"testing"
	"time"

	"openstacklab/openstack-ai/internal/team"
)

const targetID = "11111111-1111-4111-8111-111111111111"

type selectorFunc func(context.Context, team.Work) (Selection, error)

func (f selectorFunc) Select(ctx context.Context, work team.Work) (Selection, error) {
	return f(ctx, work)
}

type specialistFunc struct {
	name string
	fn   func(context.Context, Assignment) (team.Report, error)
}

func (s specialistFunc) Name() string { return s.name }
func (s specialistFunc) Analyze(ctx context.Context, assignment Assignment) (team.Report, error) {
	return s.fn(ctx, assignment)
}

type investigatorFunc func(context.Context, team.Work) (team.Report, error)

func (f investigatorFunc) Investigate(ctx context.Context, work team.Work) (team.Report, error) {
	return f(ctx, work)
}

func evidenceSnapshot() team.Work {
	stamp := time.Date(2026, 9, 1, 10, 0, 0, 0, time.UTC)
	return team.Work{
		Revision: 1,
		Input: team.Input{
			Goal: "Investigate fictional server NoValidHost", TargetID: targetID,
			Evidence: []team.Evidence{
				{ID: "E1", TargetID: targetID, Tool: "get_server", ObservedAt: stamp, Data: json.RawMessage(`{"status":"ERROR","fault":"NoValidHost"}`)},
				{ID: "E2", TargetID: targetID, Tool: "get_flavor", ObservedAt: stamp, Data: json.RawMessage(`{"vcpus":2,"ram_mb":4096}`)},
				{ID: "E3", TargetID: targetID, Tool: "get_port", ObservedAt: stamp, Data: json.RawMessage(`{"status":"ACTIVE"}`)},
			},
		},
	}
}

func report(ids ...string) team.Report {
	return team.Report{Claims: []team.Claim{{ID: "C1", Kind: "interpretation", Text: "Scheduler failure reported, exact cause unknown", EvidenceIDs: ids}}, MissingEvidence: []string{"Scheduler rejection details"}}
}

func successfulSelector(_ context.Context, _ team.Work) (Selection, error) {
	return Selection{Action: Delegate, Specialist: Compute, Objective: "Explain the scheduling failure", EvidenceIDs: []string{"E1", "E2"}, Reason: "Compute symptoms"}, nil
}

func makeDispatcher(t *testing.T, selector Selector, specialist Specialist, fallback team.Investigator) *Dispatcher {
	t.Helper()
	if fallback == nil {
		fallback = investigatorFunc(func(context.Context, team.Work) (team.Report, error) { return report("E1"), nil })
	}
	registrations := []Registration{}
	if specialist != nil {
		registrations = append(registrations, Registration{Agent: specialist, AllowedEvidenceTools: []string{"get_server", "get_flavor"}})
	}
	d, err := NewDispatcher(selector, fallback, time.Second, registrations...)
	if err != nil {
		t.Fatal(err)
	}
	return d
}

func TestDelegationAllowsOnlySelectedEvidence(t *testing.T) {
	called := false
	specialist := specialistFunc{name: Compute, fn: func(_ context.Context, assignment Assignment) (team.Report, error) {
		called = true
		if assignment.TargetID != targetID || len(assignment.Evidence) != 2 || assignment.Evidence[0].ID != "E1" || assignment.Evidence[1].ID != "E2" {
			t.Fatalf("unexpected assignment: %+v", assignment)
		}
		assignment.Evidence[0].Data[0] = 'X'
		return report("E1", "E2"), nil
	}}
	work := evidenceSnapshot()
	d := makeDispatcher(t, selectorFunc(successfulSelector), specialist, nil)
	got, err := d.Run(context.Background(), work)
	if err != nil || !called || !got.Delegated || len(got.EvidenceIDs) != 2 {
		t.Fatalf("unexpected result=%+v err=%v", got, err)
	}
	if work.Input.Evidence[0].Data[0] != '{' {
		t.Fatal("specialist mutated authoritative evidence")
	}
}

func TestDeniedDelegationDoesNotCallSpecialist(t *testing.T) {
	cases := []struct {
		name      string
		selection Selection
	}{
		{"unregistered", Selection{Action: Delegate, Specialist: Network, Objective: "test", Reason: "test", EvidenceIDs: []string{"E1"}}},
		{"unknown evidence", Selection{Action: Delegate, Specialist: Compute, Objective: "test", Reason: "test", EvidenceIDs: []string{"E999"}}},
		{"duplicate evidence", Selection{Action: Delegate, Specialist: Compute, Objective: "test", Reason: "test", EvidenceIDs: []string{"E1", "E1"}}},
		{"source denied", Selection{Action: Delegate, Specialist: Compute, Objective: "test", Reason: "test", EvidenceIDs: []string{"E3"}}},
		{"missing focus", Selection{Action: Delegate, Specialist: Compute, Reason: "test", EvidenceIDs: []string{"E1"}}},
		{"no evidence", Selection{Action: Delegate, Specialist: Compute, Objective: "test", Reason: "test", EvidenceIDs: []string{}}},
		{"unknown action", Selection{Action: "execute", Specialist: Compute, Objective: "test", Reason: "test", EvidenceIDs: []string{"E1"}}},
		{"invalid direct", Selection{Action: Direct, Specialist: Compute, Reason: "test", EvidenceIDs: []string{}}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			called := false
			specialist := specialistFunc{name: Compute, fn: func(context.Context, Assignment) (team.Report, error) {
				called = true
				return report("E1"), nil
			}}
			d := makeDispatcher(t, selectorFunc(func(context.Context, team.Work) (Selection, error) { return tc.selection, nil }), specialist, nil)
			_, err := d.Run(context.Background(), evidenceSnapshot())
			if err == nil || called {
				t.Fatalf("expected denial before dispatch: err=%v called=%v", err, called)
			}
		})
	}
}

func TestSpecialistCannotCiteHiddenEvidence(t *testing.T) {
	specialist := specialistFunc{name: Compute, fn: func(context.Context, Assignment) (team.Report, error) { return report("E3"), nil }}
	d := makeDispatcher(t, selectorFunc(successfulSelector), specialist, nil)
	_, err := d.Run(context.Background(), evidenceSnapshot())
	if err == nil || !strings.Contains(err.Error(), "unavailable") {
		t.Fatalf("expected unavailable evidence rejection: %v", err)
	}
}

func TestDirectActionUsesFallback(t *testing.T) {
	called := 0
	fallback := investigatorFunc(func(_ context.Context, work team.Work) (team.Report, error) {
		called++
		if work.Input.TargetID != targetID {
			t.Fatal("changed target")
		}
		return report("E1"), nil
	})
	selector := selectorFunc(func(context.Context, team.Work) (Selection, error) {
		return Selection{Action: Direct, Specialist: None, EvidenceIDs: []string{}, Reason: "General answer is sufficient"}, nil
	})
	d := makeDispatcher(t, selector, nil, fallback)
	got, err := d.Run(context.Background(), evidenceSnapshot())
	if err != nil || got.Delegated || called != 1 {
		t.Fatalf("direct result=%+v err=%v calls=%d", got, err, called)
	}
}

func TestBadWorkIsRejectedBeforeModel(t *testing.T) {
	work := evidenceSnapshot()
	work.Input.Evidence[0].TargetID = "unapproved-target"
	called := false
	d := makeDispatcher(t, selectorFunc(func(context.Context, team.Work) (Selection, error) {
		called = true
		return successfulSelector(context.Background(), team.Work{})
	}), nil, nil)
	_, err := d.Run(context.Background(), work)
	if err == nil || called {
		t.Fatalf("expected pre-inference denial, err=%v called=%v", err, called)
	}
}

func TestCancelledContextStopsBeforeSelection(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	called := false
	d := makeDispatcher(t, selectorFunc(func(ctx context.Context, work team.Work) (Selection, error) {
		called = true
		return Selection{}, ctx.Err()
	}), nil, nil)
	_, err := d.Run(ctx, evidenceSnapshot())
	if !errors.Is(err, context.Canceled) || called {
		t.Fatalf("err=%v called=%v", err, called)
	}
}

func TestStage9AReviewerStillControlsAcceptance(t *testing.T) {
	calls := 0
	specialist := specialistFunc{name: Compute, fn: func(_ context.Context, assignment Assignment) (team.Report, error) {
		calls++
		text := "Host RAM was exhausted"
		if assignment.Revision > 1 {
			if assignment.Feedback == nil || len(assignment.Feedback.Issues) == 0 {
				t.Fatal("missing review feedback")
			}
			text = "NoValidHost is observed; exact scheduling constraint remains unknown"
		}
		return team.Report{Claims: []team.Claim{{ID: "C1", Kind: "interpretation", Text: text, EvidenceIDs: []string{"E1", "E2"}}}, MissingEvidence: []string{"Scheduler logs"}}, nil
	}}
	d := makeDispatcher(t, selectorFunc(successfulSelector), specialist, nil)
	adapter, err := NewInvestigatorAdapter(d, nil)
	if err != nil {
		t.Fatal(err)
	}
	reviewer := reviewerFunc(func(_ context.Context, input team.ReviewInput) (team.Review, error) {
		review := team.Review{Digest: input.Digest, Verdict: team.Accept, Issues: []team.Issue{}}
		if strings.Contains(input.Report.Claims[0].Text, "exhausted") {
			review.Verdict = team.Revise
			review.Issues = []team.Issue{{ClaimID: "C1", Reason: "Requested RAM is not available capacity"}}
		}
		return review, nil
	})
	coordinator, err := team.NewCoordinator(adapter, reviewer, 1, time.Second)
	if err != nil {
		t.Fatal(err)
	}
	result, err := coordinator.Run(context.Background(), evidenceSnapshot().Input)
	if err != nil || result.Outcome != team.Accepted || calls != 2 || len(result.Rounds) != 2 {
		t.Fatalf("review result=%+v err=%v calls=%d", result, err, calls)
	}
}

type reviewerFunc func(context.Context, team.ReviewInput) (team.Review, error)

func (f reviewerFunc) Review(ctx context.Context, input team.ReviewInput) (team.Review, error) {
	return f(ctx, input)
}

func TestModelAdaptersCallOnlyStructuredBoundary(t *testing.T) {
	call := 0
	generate := func(_ context.Context, instructions, input string, schema []byte) (string, error) {
		call++
		if len(schema) == 0 || strings.TrimSpace(instructions) == "" || !json.Valid([]byte(input)) {
			return "", fmt.Errorf("invalid model boundary")
		}
		if call == 1 {
			return `{"action":"delegate","specialist":"compute","objective":"Inspect scheduling evidence","evidence_ids":["E1","E2"],"reason":"Compute incident"}`, nil
		}
		return `{"claims":[{"id":"C1","kind":"observation","text":"NoValidHost was reported","evidence_ids":["E1"]}],"missing_evidence":["Scheduler constraint"]}`, nil
	}
	selector, err := NewModelSelector(generate)
	if err != nil {
		t.Fatal(err)
	}
	specialist, err := NewModelSpecialist(Compute, generate)
	if err != nil {
		t.Fatal(err)
	}
	d := makeDispatcher(t, selector, specialist, nil)
	got, err := d.Run(context.Background(), evidenceSnapshot())
	if err != nil || call != 2 || !got.Delegated {
		t.Fatalf("result=%+v err=%v calls=%d", got, err, call)
	}
}
