package planning

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"sync"
	"testing"

	"openstacklab/openstack-ai/internal/ai"
	"openstacklab/openstack-ai/internal/project"
	"openstacklab/openstack-ai/internal/workflow"
)

const serverA = "11111111-1111-4111-8111-111111111111"
const serverB = "22222222-2222-4222-8222-222222222222"
const serverC = "33333333-3333-4333-8333-333333333333"

func fixture() (Request, Draft) {
	req := Request{Goal: "Investigate the reported build failures and compare the evidence.", ServerIdentifiers: []string{serverA, serverB}}
	draft := Draft{Disposition: Ready, Explanation: "Investigate each target, then synthesize the reports.", Tasks: []ProposedTask{
		{ID: "investigate-a", Type: project.TaskTypeServerIncident, ServerIdentifier: serverA, Focus: "Inspect the build failure without assuming a cause.", DependsOn: []string{}},
		{ID: "investigate-b", Type: project.TaskTypeServerIncident, ServerIdentifier: serverB, Focus: "Inspect the build failure independently.", DependsOn: []string{}},
		{ID: "summary", Type: project.TaskTypeProjectSummary, Focus: "Compare findings, uncertainties and missing evidence.", DependsOn: []string{"investigate-a", "investigate-b"}},
	}}
	return req, draft
}

func TestPrepareRejectsInvalidPlans(t *testing.T) {
	tests := []struct {
		name   string
		mutate func(*Request, *Draft)
	}{
		{"no targets", func(r *Request, _ *Draft) { r.ServerIdentifiers = nil }},
		{"empty identifier", func(r *Request, _ *Draft) { r.ServerIdentifiers[0] = "" }},
		{"duplicate scope", func(r *Request, _ *Draft) { r.ServerIdentifiers[1] = serverA }},
		{"scope in goal", func(r *Request, _ *Draft) { r.Goal += " " + serverC }},
		{"unapproved marked name in goal", func(r *Request, _ *Draft) { r.Goal += ` server_identifier="unapproved server"` }},
		{"too many servers", func(r *Request, _ *Draft) { r.ServerIdentifiers = make([]string, MaxServers+1) }},
		{"empty goal", func(r *Request, _ *Draft) { r.Goal = " " }},
		{"long goal", func(r *Request, _ *Draft) { r.Goal = strings.Repeat("x", 4001) }},
		{"unknown disposition", func(_ *Request, d *Draft) { d.Disposition = "execute_now" }},
		{"empty rationale", func(_ *Request, d *Draft) { d.Explanation = "" }},
		{"nil tasks", func(_ *Request, d *Draft) { d.Tasks = nil }},
		{"unsupported task", func(_ *Request, d *Draft) { d.Tasks[0].Type = "reboot_server" }},
		{"scope expansion", func(_ *Request, d *Draft) { d.Tasks[0].ServerIdentifier = serverC }},
		{"duplicate target", func(_ *Request, d *Draft) { d.Tasks[1].ServerIdentifier = serverA }},
		{"missing target", func(_ *Request, d *Draft) { d.Tasks = d.Tasks[1:] }},
		{"duplicate task ID", func(_ *Request, d *Draft) { d.Tasks[1].ID = d.Tasks[0].ID }},
		{"invalid task ID", func(_ *Request, d *Draft) { d.Tasks[0].ID = "../a" }},
		{"empty focus", func(_ *Request, d *Draft) { d.Tasks[0].Focus = " " }},
		{"long focus", func(_ *Request, d *Draft) { d.Tasks[0].Focus = strings.Repeat("a", 1001) }},
		{"UUID in focus", func(_ *Request, d *Draft) { d.Tasks[0].Focus += serverB }},
		{"nil dependency array", func(_ *Request, d *Draft) { d.Tasks[0].DependsOn = nil }},
		{"unknown dependency", func(_ *Request, d *Draft) { d.Tasks[0].DependsOn = []string{"absent"} }},
		{"self dependency", func(_ *Request, d *Draft) { d.Tasks[0].DependsOn = []string{"investigate-a"} }},
		{"dependency cycle", func(_ *Request, d *Draft) {
			d.Tasks[0].DependsOn = []string{"investigate-b"}
			d.Tasks[1].DependsOn = []string{"investigate-a"}
		}},
		{"duplicate dependency", func(_ *Request, d *Draft) { d.Tasks[1].DependsOn = []string{"investigate-a", "investigate-a"} }},
		{"depends on summary", func(_ *Request, d *Draft) { d.Tasks[0].DependsOn = []string{"summary"} }},
		{"summary skips dependency", func(_ *Request, d *Draft) { d.Tasks[2].DependsOn = []string{"investigate-a"} }},
		{"summary targets server", func(_ *Request, d *Draft) { d.Tasks[2].ServerIdentifier = serverA }},
		{"summary depends on itself", func(_ *Request, d *Draft) { d.Tasks[2].DependsOn[1] = "summary" }},
		{"not ready with tasks", func(_ *Request, d *Draft) { d.Disposition = NeedsInput }},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			req, draft := fixture()
			test.mutate(&req, &draft)
			if _, err := Prepare(req, draft); err == nil {
				t.Fatal("invalid plan was accepted")
			}
		})
	}
}

func TestPreparePreservesGoalAndOneUUIDPerWorkflow(t *testing.T) {
	req, draft := fixture()
	req.Goal = "Compare failures of " + serverA + " and " + serverB + "; do not assume they share a cause."
	prepared, err := Prepare(req, draft)
	if err != nil {
		t.Fatal(err)
	}
	engine := &recordingStarter{}
	if _, err := prepared.Start(context.Background(), engine, prepared.Digest()); err != nil {
		t.Fatal(err)
	}
	if engine.goal != req.Goal {
		t.Fatal("project objective changed")
	}
	for _, task := range engine.tasks[:2] {
		if len(uuid.FindAllString(task.Goal, -1)) != 1 {
			t.Fatalf("workflow target is ambiguous: %s", task.Goal)
		}
		if !strings.Contains(task.Goal, "do not assume they share a cause") {
			t.Fatal("user objective was lost")
		}
		if task.Status != project.TaskPending || task.WorkflowID != "" || task.Result != "" {
			t.Fatal("runtime fields were injected")
		}
	}
}

func TestPrepareSupportsExactServerName(t *testing.T) {
	const name = `Web "API" / 01`
	req := Request{
		Goal:              `Investigate server_identifier="Web \"API\" / 01" for API failures.`,
		ServerIdentifiers: []string{name},
	}
	draft := Draft{Disposition: Ready, Explanation: "Inspect the explicitly selected server.", Tasks: []ProposedTask{
		{ID: "investigate", Type: project.TaskTypeServerIncident, ServerIdentifier: name, Focus: "Inspect the API failures.", DependsOn: []string{}},
		{ID: "summary", Type: project.TaskTypeProjectSummary, Focus: "Summarize the findings.", DependsOn: []string{"investigate"}},
	}}
	prepared, err := Prepare(req, draft)
	if err != nil {
		t.Fatal(err)
	}
	engine := &recordingStarter{}
	if _, err := prepared.Start(context.Background(), engine, prepared.Digest()); err != nil {
		t.Fatal(err)
	}
	identifier, ok := workflow.LeadingServerIdentifier(engine.tasks[0].Goal)
	if !ok || identifier != name {
		t.Fatalf("workflow target = %q, %v; want exact name %q", identifier, ok, name)
	}
}

func TestOrderingDependencyAllowed(t *testing.T) {
	req, draft := fixture()
	draft.Tasks[1].DependsOn = []string{"investigate-a"}
	if _, err := Prepare(req, draft); err != nil {
		t.Fatal(err)
	}
}

func TestNonReadyNotExecutable(t *testing.T) {
	for _, disposition := range []string{NeedsInput, Unsupported} {
		req, _ := fixture()
		_, err := Prepare(req, Draft{Disposition: disposition, Explanation: "More input or capabilities are required.", Tasks: []ProposedTask{}})
		if !errors.Is(err, ErrNotReady) {
			t.Fatalf("expected ErrNotReady, got %v", err)
		}
	}
}

type recordingStarter struct {
	mu    sync.Mutex
	calls int
	goal  string
	tasks []project.Task
	err   error
}

func (s *recordingStarter) Start(_ context.Context, goal string, tasks []project.Task) (project.State, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.calls++
	s.goal, s.tasks = goal, tasks
	return project.State{ID: "prj-test", Goal: goal, Tasks: tasks}, s.err
}

func TestApprovalAndSnapshot(t *testing.T) {
	req, draft := fixture()
	prepared, err := Prepare(req, draft)
	if err != nil {
		t.Fatal(err)
	}
	digest := prepared.Digest()
	req.ServerIdentifiers[0], draft.Tasks[0].ServerIdentifier = serverC, serverC
	draft.Tasks[2].DependsOn[0] = "evil"
	preview := prepared.Preview()
	preview[0] = 'x'
	engine := &recordingStarter{}
	if _, err := prepared.Start(context.Background(), engine, "wrong"); err == nil {
		t.Fatal("incorrect approval accepted")
	}
	if engine.calls != 0 {
		t.Fatal("started without approval")
	}
	if _, err := prepared.Start(context.Background(), engine, digest); err != nil {
		t.Fatal(err)
	}
	if strings.Contains(engine.tasks[0].Goal, serverC) || engine.tasks[2].DependsOn[0] != "investigate-a" {
		t.Fatal("reviewed snapshot mutated")
	}
	if _, err := prepared.Start(context.Background(), engine, digest); err == nil || engine.calls != 1 {
		t.Fatal("same in-memory plan started twice")
	}
}

func TestApprovalIsBoundToChangedPlan(t *testing.T) {
	req, draft := fixture()
	first, _ := Prepare(req, draft)
	draft.Tasks[0].Focus = "A different task focus."
	second, _ := Prepare(req, draft)
	engine := &recordingStarter{}
	if _, err := second.Start(context.Background(), engine, first.Digest()); err == nil {
		t.Fatal("stale approval accepted")
	}
}

func TestConcurrentApprovalStartsOnce(t *testing.T) {
	req, draft := fixture()
	prepared, _ := Prepare(req, draft)
	engine := &recordingStarter{}
	var group sync.WaitGroup
	for i := 0; i < 8; i++ {
		group.Add(1)
		go func() { defer group.Done(); _, _ = prepared.Start(context.Background(), engine, prepared.Digest()) }()
	}
	group.Wait()
	if engine.calls != 1 {
		t.Fatalf("started %d times", engine.calls)
	}
}

func TestExecutionErrorPreservesProjectID(t *testing.T) {
	req, draft := fixture()
	prepared, _ := Prepare(req, draft)
	engine := &recordingStarter{err: errors.New("paused child workflow")}
	state, err := prepared.Start(context.Background(), engine, prepared.Digest())
	if err == nil || state.ID != "prj-test" {
		t.Fatal("lost resumable project ID")
	}
}

func TestDecodeRejectsInvalidJSON(t *testing.T) {
	_, draft := fixture()
	raw, _ := json.Marshal(draft)
	good := string(raw)
	tests := map[string]string{
		"prose":          "Here is the plan: " + good,
		"fence":          "```json\n" + good + "\n```",
		"extra value":    good + `{}`,
		"extra text":     good + " trailing",
		"duplicate key":  strings.Replace(good, `"disposition":"ready"`, `"disposition":"ready","disposition":"ready"`, 1),
		"runtime field":  strings.Replace(good, `"id":"investigate-a"`, `"id":"investigate-a","status":"completed"`, 1),
		"missing field":  strings.Replace(good, `"server_identifier":"",`, ``, 1),
		"null field":     strings.Replace(good, `"server_identifier":""`, `"server_identifier":null`, 1),
		"case variation": strings.Replace(good, `"disposition"`, `"Disposition"`, 1),
		"oversized":      strings.Repeat(" ", MaxPlanBytes+1),
		"invalid UTF8":   string([]byte{0xff}),
		"deep nesting":   strings.Repeat("[", 30) + "0" + strings.Repeat("]", 30),
	}
	for name, text := range tests {
		t.Run(name, func(t *testing.T) {
			if _, err := DecodeDraft(text); err == nil {
				t.Fatal("invalid JSON accepted")
			}
		})
	}
	if _, err := DecodeDraft(good); err != nil {
		t.Fatal(err)
	}
}

type fakeClient struct {
	response ai.Response
	err      error
	calls    int
}

func (c *fakeClient) ChatStructured(_ context.Context, _ []ai.Message, schema []byte) (ai.Response, error) {
	c.calls++
	if !json.Valid(schema) {
		return ai.Response{}, errors.New("invalid schema")
	}
	return c.response, c.err
}

func TestPlannerUsesStructuredClient(t *testing.T) {
	req, draft := fixture()
	raw, _ := json.Marshal(draft)
	client := &fakeClient{response: ai.Response{Text: string(raw), Usage: ai.Usage{InputTokens: 123}}}
	result, usage, err := NewPlanner(client).Propose(context.Background(), req)
	if err != nil || result.Disposition != Ready || usage.InputTokens != 123 || client.calls != 1 {
		t.Fatalf("unexpected proposal: %v %v %v", result, usage, err)
	}
}

func TestMissingScopeNeedsNoModel(t *testing.T) {
	result, _, err := NewPlanner(nil).Propose(context.Background(), Request{Goal: "Investigate my servers."})
	if err != nil || result.Disposition != NeedsInput {
		t.Fatal(result, err)
	}
}

func TestBadRequestNeedsNoModel(t *testing.T) {
	client := &fakeClient{}
	if _, _, err := NewPlanner(client).Propose(context.Background(), Request{Goal: "Investigate", ServerIdentifiers: []string{""}}); err == nil || client.calls != 0 {
		t.Fatal("invalid scope reached model")
	}
}

func TestPlannerRejectsModelScopeExpansion(t *testing.T) {
	req, draft := fixture()
	draft.Tasks[0].ServerIdentifier = serverC
	raw, _ := json.Marshal(draft)
	client := &fakeClient{response: ai.Response{Text: string(raw), Usage: ai.Usage{InputTokens: 7}}}
	_, usage, err := NewPlanner(client).Propose(context.Background(), req)
	if err == nil || usage.InputTokens != 7 {
		t.Fatal("invalid plan or usage handling")
	}
}

func TestCancellationAndClientFailure(t *testing.T) {
	req, draft := fixture()
	client := &fakeClient{err: context.DeadlineExceeded, response: ai.Response{Usage: ai.Usage{InputTokens: 3}}}
	_, usage, err := NewPlanner(client).Propose(context.Background(), req)
	if !errors.Is(err, context.DeadlineExceeded) || usage.InputTokens != 3 {
		t.Fatal("error or usage lost")
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if _, _, err := NewPlanner(client).Propose(ctx, req); !errors.Is(err, context.Canceled) || client.calls != 1 {
		t.Fatal("cancellation ignored")
	}
	prepared, _ := Prepare(req, draft)
	engine := &recordingStarter{}
	if _, err := prepared.Start(ctx, engine, prepared.Digest()); !errors.Is(err, context.Canceled) || engine.calls != 0 {
		t.Fatal("cancelled start executed")
	}
}
