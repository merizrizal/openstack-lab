package workflow

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"testing"
	"time"

	"openstacklab/openstack-ai/internal/agent"
	"openstacklab/openstack-ai/internal/ai"
	"openstacklab/openstack-ai/internal/team"
)

type reviewSnapshotClient struct {
	t     *testing.T
	calls int
}

func (c *reviewSnapshotClient) ChatStructured(_ context.Context, messages []ai.Message, schema []byte) (ai.Response, error) {
	c.t.Helper()
	c.calls++
	if len(messages) != 2 || messages[0].Role != "system" || messages[1].Role != "user" || !json.Valid(schema) {
		c.t.Fatalf("unexpected structured request: messages=%+v schema=%s", messages, schema)
	}

	switch c.calls {
	case 1:
		var work team.Work
		if err := json.Unmarshal([]byte(messages[1].Content), &work); err != nil {
			c.t.Fatal(err)
		}
		if len(work.Input.Evidence) != 1 || !strings.Contains(string(work.Input.Evidence[0].Data), "NoValidHost") {
			c.t.Fatalf("investigator did not receive the scoped snapshot: %+v", work.Input)
		}
		report := team.Report{
			Claims: []team.Claim{{
				ID: "C1", Kind: "observation", Text: "The snapshot reports NoValidHost.", EvidenceIDs: []string{work.Input.Evidence[0].ID},
			}},
			MissingEvidence: []string{},
		}
		return jsonResponse(c.t, report), nil
	case 2:
		var input team.ReviewInput
		if err := json.Unmarshal([]byte(messages[1].Content), &input); err != nil {
			c.t.Fatal(err)
		}
		return jsonResponse(c.t, team.Review{Digest: input.Digest, Verdict: team.Accept, Issues: []team.Issue{}}), nil
	default:
		c.t.Fatalf("unexpected structured call %d", c.calls)
		return ai.Response{}, nil
	}
}

func jsonResponse(t *testing.T, value any) ai.Response {
	t.Helper()
	data, err := json.Marshal(value)
	if err != nil {
		t.Fatal(err)
	}
	return ai.Response{Text: string(data)}
}

type reviewAgentStore struct {
	state agent.State
}

func (s *reviewAgentStore) SaveState(context.Context, agent.State) error { return nil }

func (s *reviewAgentStore) LoadState(_ context.Context, id string) (agent.State, error) {
	if id != s.state.ID {
		return agent.State{}, errors.New("unknown investigation")
	}
	return s.state, nil
}

func (s *reviewAgentStore) SaveMemory(context.Context, agent.MemoryRecord) error { return nil }

func (s *reviewAgentStore) FindMemoriesBySubject(context.Context, string, int) ([]agent.MemoryRecord, error) {
	return nil, nil
}

func TestValidateResultRoutesToEvidenceReview(t *testing.T) {
	state := &State{AgentStatus: agent.StatusCompleted, AgentAnswer: "snapshot ready"}
	next, err := (&validateResultStep{}).Run(context.Background(), state)
	if err != nil {
		t.Fatalf("validateResultStep.Run() error = %v", err)
	}
	if next != StepReviewSnapshot {
		t.Fatalf("next step = %q, want %q", next, StepReviewSnapshot)
	}
}

func TestReviewSnapshotStepPublishesReviewedReport(t *testing.T) {
	observedAt := time.Date(2026, 9, 1, 10, 0, 0, 0, time.UTC)
	store := &reviewAgentStore{state: agent.State{
		ID:          "inv-test",
		Goal:        "Explain the server failure.",
		Status:      agent.StatusCompleted,
		FinalAnswer: "The server is in ERROR.",
		Observations: []agent.Observation{{
			Step:       1,
			Tool:       "get_server",
			ObservedAt: observedAt,
			Arguments:  json.RawMessage(`{"server_identifier":"server-01"}`),
			Result:     json.RawMessage(`{"id":"server-01","status":"ERROR","fault":{"message":"NoValidHost"}}`),
		}},
	}}
	client := &reviewSnapshotClient{t: t}
	runtime := agent.NewRuntime(client, nil, store, 1, 1)
	state := &State{
		Goal:                 "Explain the server failure.",
		ServerIdentifier:     "server-01",
		AgentInvestigationID: "inv-test",
	}

	next, err := (&reviewSnapshotStep{runtime: runtime, client: client}).Run(context.Background(), state)
	if err != nil {
		t.Fatalf("reviewSnapshotStep.Run() error = %v", err)
	}
	if next != StepRenderReport {
		t.Fatalf("next step = %q, want %q", next, StepRenderReport)
	}
	if client.calls != 2 || state.EvidenceReview == nil || state.EvidenceReview.Outcome != team.Accepted {
		t.Fatalf("calls=%d evidence review=%+v", client.calls, state.EvidenceReview)
	}
	if got := state.EvidenceReview.Rounds[0].Report.Claims[0].EvidenceIDs; len(got) != 1 || got[0] != "E1" {
		t.Fatalf("claim evidence IDs = %v, want [E1]", got)
	}

	if _, err := (&renderReportStep{}).Run(context.Background(), state); err != nil {
		t.Fatalf("renderReportStep.Run() error = %v", err)
	}
	for _, want := range []string{"Evidence review: accepted", "NoValidHost", "evidence: E1"} {
		if !strings.Contains(state.FinalReport, want) {
			t.Errorf("final report %q does not contain %q", state.FinalReport, want)
		}
	}
}

func TestReviewInputPreservesTimeAndRejectsOutOfScopeEvidence(t *testing.T) {
	observedAt := time.Date(2026, 9, 1, 10, 0, 0, 0, time.UTC)
	snapshot := agent.Result{Observations: []agent.Observation{{
		Step:       1,
		Tool:       "get_server",
		ObservedAt: observedAt,
		Arguments:  json.RawMessage(`{"server_identifier":"server-01"}`),
		Result:     json.RawMessage(`{"id":"server-01","status":"ACTIVE"}`),
	}}}
	input, err := reviewInput("Investigate server-01", "server-01", snapshot)
	if err != nil {
		t.Fatalf("reviewInput() error = %v", err)
	}
	if len(input.Evidence) != 1 || !input.Evidence[0].ObservedAt.Equal(observedAt) {
		t.Fatalf("evidence did not preserve observation timestamp: %+v", input.Evidence)
	}

	snapshot.Observations[0].Arguments = json.RawMessage(`{"server_identifier":"server-02"}`)
	if _, err := reviewInput("Investigate server-01", "server-01", snapshot); err == nil {
		t.Fatal("out-of-scope server observation was accepted")
	}
}

func TestReviewInputRestrictsFlavorEvidenceToTargetServer(t *testing.T) {
	observedAt := time.Date(2026, 9, 1, 10, 0, 0, 0, time.UTC)
	snapshot := agent.Result{Observations: []agent.Observation{
		{
			Step: 1, Tool: "get_server", ObservedAt: observedAt,
			Arguments: json.RawMessage(`{"server_identifier":"server-01"}`),
			Result:    json.RawMessage(`{"id":"server-01","flavor_id":"flavor-01"}`),
		},
		{
			Step: 2, Tool: "get_flavor", ObservedAt: observedAt,
			Arguments: json.RawMessage(`{"flavor_id":"flavor-01"}`),
			Result:    json.RawMessage(`{"id":"flavor-01","ram_mb":2048}`),
		},
	}}
	if _, err := reviewInput("Investigate server-01", "server-01", snapshot); err != nil {
		t.Fatalf("reviewInput() rejected target flavor evidence: %v", err)
	}

	snapshot.Observations[1].Arguments = json.RawMessage(`{"flavor_id":"flavor-02"}`)
	if _, err := reviewInput("Investigate server-01", "server-01", snapshot); err == nil {
		t.Fatal("out-of-scope flavor observation was accepted")
	}
}

func TestFormatReviewedSnapshotSurfacesHumanEscalation(t *testing.T) {
	result := &team.Result{
		Outcome: team.NeedsHuman,
		Rounds: []team.Round{{
			Report: team.Report{Claims: []team.Claim{{ID: "C1", Kind: "hypothesis", Text: "Cause remains uncertain.", EvidenceIDs: []string{"E1"}}}},
			Review: &team.Review{Verdict: team.Escalate, Issues: []team.Issue{{ClaimID: "C1", Reason: "Available evidence cannot resolve the cause."}}},
		}},
	}
	formatted, err := formatReviewedSnapshot(result)
	if err != nil {
		t.Fatalf("formatReviewedSnapshot() error = %v", err)
	}
	for _, want := range []string{"Evidence review: needs_human", "Review concerns:", "Available evidence cannot resolve the cause."} {
		if !strings.Contains(formatted, want) {
			t.Errorf("formatted report %q does not contain %q", formatted, want)
		}
	}
}

func TestReviewInputRequiresObservationTimestamp(t *testing.T) {
	snapshot := agent.Result{Observations: []agent.Observation{{
		Step:      1,
		Tool:      "get_server",
		Arguments: json.RawMessage(`{"server_identifier":"server-01"}`),
		Result:    json.RawMessage(`{"id":"server-01","status":"ACTIVE"}`),
	}}}
	if _, err := reviewInput("Investigate server-01", "server-01", snapshot); err == nil {
		t.Fatal("observation without timestamp was accepted")
	}
}
