package team

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"testing"
	"time"
)

type investigatorFunc func(context.Context, Work) (Report, error)

func (f investigatorFunc) Investigate(ctx context.Context, work Work) (Report, error) {
	return f(ctx, work)
}

type reviewerFunc func(context.Context, ReviewInput) (Review, error)

func (f reviewerFunc) Review(ctx context.Context, in ReviewInput) (Review, error) { return f(ctx, in) }

func fixture() Input {
	return Input{
		Goal:     "Explain the reported build failure without inventing a root cause.",
		TargetID: "11111111-1111-4111-8111-111111111111",
		Evidence: []Evidence{{
			ID: "E1", TargetID: "11111111-1111-4111-8111-111111111111",
			Tool: "get_server", ObservedAt: time.Date(2026, 9, 1, 10, 0, 0, 0, time.UTC),
			Data: json.RawMessage(`{"status":"ERROR","fault":"NoValidHost"}`),
		}},
	}
}

func goodReport() Report {
	return Report{
		Claims:          []Claim{{ID: "C1", Kind: "observation", Text: "The snapshot reports ERROR and NoValidHost.", EvidenceIDs: []string{"E1"}}},
		MissingEvidence: []string{"The specific scheduler constraint is not established."},
	}
}

func acceptReviewer(_ context.Context, in ReviewInput) (Review, error) {
	return Review{Digest: in.Digest, Verdict: Accept, Issues: []Issue{}}, nil
}

func runFixture(t *testing.T, investigator Investigator, reviewer Reviewer) (Result, error) {
	t.Helper()
	c, err := NewCoordinator(investigator, reviewer, 1, time.Second)
	if err != nil {
		t.Fatal(err)
	}
	return c.Run(context.Background(), fixture())
}

func TestAcceptFirstDraft(t *testing.T) {
	result, err := runFixture(t, investigatorFunc(func(context.Context, Work) (Report, error) { return goodReport(), nil }), reviewerFunc(acceptReviewer))
	if err != nil || result.Outcome != Accepted || result.Invocations != 2 || len(result.Rounds) != 1 {
		t.Fatalf("result=%+v err=%v", result, err)
	}
}

func TestOneRevision(t *testing.T) {
	writer := investigatorFunc(func(_ context.Context, work Work) (Report, error) {
		if work.Revision == 2 && (work.Feedback == nil || work.Previous == nil) {
			t.Fatal("revision lost its feedback")
		}
		return goodReport(), nil
	})
	reviewer := reviewerFunc(func(_ context.Context, in ReviewInput) (Review, error) {
		if in.Revision == 1 {
			return Review{Digest: in.Digest, Verdict: Revise, Issues: []Issue{{ClaimID: "C1", Reason: "Clarify the observation timestamp."}}}, nil
		}
		return acceptReviewer(context.Background(), in)
	})
	result, err := runFixture(t, writer, reviewer)
	if err != nil || result.Outcome != Accepted || result.Invocations != 4 || len(result.Rounds) != 2 {
		t.Fatalf("result=%+v err=%v", result, err)
	}
	if result.Rounds[0].Digest == result.Rounds[1].Digest {
		t.Fatal("revision must change digest")
	}
}

func TestRevisionBudgetAndEscalation(t *testing.T) {
	for _, verdict := range []string{Revise, Escalate} {
		t.Run(verdict, func(t *testing.T) {
			writer := investigatorFunc(func(context.Context, Work) (Report, error) { return goodReport(), nil })
			reviewer := reviewerFunc(func(_ context.Context, in ReviewInput) (Review, error) {
				return Review{Digest: in.Digest, Verdict: verdict, Issues: []Issue{{Reason: "Evidence conflict remains."}}}, nil
			})
			result, err := runFixture(t, writer, reviewer)
			if err != nil || result.Outcome != NeedsHuman {
				t.Fatalf("result=%+v err=%v", result, err)
			}
			want := 4
			if verdict == Escalate {
				want = 2
			}
			if result.Invocations != want {
				t.Fatalf("got %d calls, want %d", result.Invocations, want)
			}
		})
	}
}

func TestInvalidReportStopsBeforeReviewer(t *testing.T) {
	cases := map[string]func(*Report){
		"unknown_reference":   func(r *Report) { r.Claims[0].EvidenceIDs = []string{"E999"} },
		"missing_references":  func(r *Report) { r.Claims[0].EvidenceIDs = nil },
		"duplicate_reference": func(r *Report) { r.Claims[0].EvidenceIDs = []string{"E1", "E1"} },
		"duplicate_claim":     func(r *Report) { r.Claims = append(r.Claims, r.Claims[0]) },
		"unknown_kind":        func(r *Report) { r.Claims[0].Kind = "confirmed_by_magic" },
		"empty_text":          func(r *Report) { r.Claims[0].Text = " " },
		"missing_gap_array":   func(r *Report) { r.MissingEvidence = nil },
	}
	for name, mutate := range cases {
		t.Run(name, func(t *testing.T) {
			writer := investigatorFunc(func(context.Context, Work) (Report, error) { r := goodReport(); mutate(&r); return r, nil })
			reviewer := reviewerFunc(func(context.Context, ReviewInput) (Review, error) {
				t.Fatal("reviewer must not run")
				return Review{}, nil
			})
			result, err := runFixture(t, writer, reviewer)
			if err == nil || result.Outcome != Failed || result.Invocations != 1 {
				t.Fatalf("result=%+v err=%v", result, err)
			}
		})
	}
}

func TestInvalidReviewCannotPublish(t *testing.T) {
	cases := map[string]func(*Review){
		"stale_digest":          func(r *Review) { r.Digest = "old" },
		"accept_with_issues":    func(r *Review) { r.Issues = []Issue{{ClaimID: "C1", Reason: "Unsupported."}} },
		"unknown_verdict":       func(r *Review) { r.Verdict = "run_shell" },
		"missing_issues":        func(r *Review) { r.Issues = nil },
		"revise_without_reason": func(r *Review) { r.Verdict = Revise },
		"unknown_claim":         func(r *Review) { r.Verdict = Revise; r.Issues = []Issue{{ClaimID: "C999", Reason: "Unsupported."}} },
	}
	for name, mutate := range cases {
		t.Run(name, func(t *testing.T) {
			writer := investigatorFunc(func(context.Context, Work) (Report, error) { return goodReport(), nil })
			reviewer := reviewerFunc(func(ctx context.Context, in ReviewInput) (Review, error) {
				r, _ := acceptReviewer(ctx, in)
				mutate(&r)
				return r, nil
			})
			result, err := runFixture(t, writer, reviewer)
			if err == nil || result.Outcome != Failed {
				t.Fatalf("result=%+v err=%v", result, err)
			}
		})
	}
}

func TestInputScopeAndEvidence(t *testing.T) {
	cases := map[string]func(*Input){
		"wrong_scope":  func(in *Input) { in.Evidence[0].TargetID = "other" },
		"no_evidence":  func(in *Input) { in.Evidence = nil },
		"bad_json":     func(in *Input) { in.Evidence[0].Data = json.RawMessage(`{`) },
		"duplicate_id": func(in *Input) { in.Evidence = append(in.Evidence, in.Evidence[0]) },
		"no_timestamp": func(in *Input) { in.Evidence[0].ObservedAt = time.Time{} },
		"no_goal":      func(in *Input) { in.Goal = "" },
	}
	for name, mutate := range cases {
		t.Run(name, func(t *testing.T) {
			in := fixture()
			mutate(&in)
			if validateInput(in) == nil {
				t.Fatal("input accepted")
			}
		})
	}
}

func TestSnapshotIsolation(t *testing.T) {
	input := fixture()
	before := string(input.Evidence[0].Data)
	writer := investigatorFunc(func(_ context.Context, work Work) (Report, error) {
		work.Input.Evidence[0].Data[0] = 'X'
		return goodReport(), nil
	})
	reviewer := reviewerFunc(func(ctx context.Context, in ReviewInput) (Review, error) {
		if string(in.Input.Evidence[0].Data) != before {
			t.Fatal("writer mutated authoritative evidence")
		}
		in.Report.Claims[0].Text = "changed in reviewer"
		return acceptReviewer(ctx, in)
	})
	c, _ := NewCoordinator(writer, reviewer, 1, time.Second)
	result, err := c.Run(context.Background(), input)
	if err != nil {
		t.Fatal(err)
	}
	if result.Rounds[0].Report.Claims[0].Text == "changed in reviewer" {
		t.Fatal("reviewer mutated report")
	}
	if string(input.Evidence[0].Data) != before {
		t.Fatal("input changed")
	}
}

func TestReviewerFailureAndCancellation(t *testing.T) {
	writer := investigatorFunc(func(context.Context, Work) (Report, error) { return goodReport(), nil })
	result, err := runFixture(t, writer, reviewerFunc(func(context.Context, ReviewInput) (Review, error) {
		return Review{}, errors.New("provider unavailable")
	}))
	if err == nil || result.Outcome != Failed || len(result.Rounds) != 1 {
		t.Fatalf("result=%+v err=%v", result, err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	c, _ := NewCoordinator(writer, reviewerFunc(acceptReviewer), 1, time.Second)
	result, err = c.Run(ctx, fixture())
	if !errors.Is(err, context.Canceled) || result.Invocations != 0 {
		t.Fatalf("result=%+v err=%v", result, err)
	}
}

func TestModelAdaptersUseSeparateInstructionsAndOriginalEvidence(t *testing.T) {
	var prompts []string
	generate := func(_ context.Context, instructions, input string, schema []byte) (string, error) {
		prompts = append(prompts, instructions)
		if !json.Valid(schema) || !strings.Contains(input, "NoValidHost") {
			t.Fatal("missing schema or evidence")
		}
		if len(prompts) == 1 {
			data, _ := json.Marshal(goodReport())
			return string(data), nil
		}
		var view ReviewInput
		if err := json.Unmarshal([]byte(input), &view); err != nil {
			return "", err
		}
		data, _ := json.Marshal(Review{Digest: view.Digest, Verdict: Accept, Issues: []Issue{}})
		return string(data), nil
	}
	writer, _ := NewModelInvestigator(generate)
	reviewer, _ := NewModelReviewer(generate)
	result, err := runFixture(t, writer, reviewer)
	if err != nil || result.Outcome != Accepted {
		t.Fatalf("result=%+v err=%v", result, err)
	}
	if len(prompts) != 2 || prompts[0] == prompts[1] {
		t.Fatal("roles share instructions")
	}
}

func TestModelOutputProtocol(t *testing.T) {
	for _, output := range []string{"not json", `{} {}`, `{"unknown":true}`, `null`, `{"claims":[],"missing_evidence":[]}`} {
		t.Run(output, func(t *testing.T) {
			writer, _ := NewModelInvestigator(func(context.Context, string, string, []byte) (string, error) { return output, nil })
			result, err := runFixture(t, writer, reviewerFunc(acceptReviewer))
			if err == nil || result.Outcome != Failed {
				t.Fatalf("result=%+v err=%v", result, err)
			}
		})
	}
}
