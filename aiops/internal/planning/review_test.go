package planning

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"strings"
	"testing"

	"openstacklab/openstack-ai/internal/ai"
)

func TestInteractiveReview(t *testing.T) {
	req, draft := fixture()
	prepared, err := Prepare(req, draft)
	if err != nil {
		t.Fatal(err)
	}
	payload, _ := json.Marshal(draft)
	tests := []struct {
		name, input string
		calls       int
	}{
		{"exact approval", "approve " + prepared.Digest() + "\n", 1},
		{"generic yes", "yes\n", 0},
		{"wrong digest", "approve wrong\n", 0},
		{"empty stdin", "", 0},
		{"cancel", "cancel\n", 0},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			client := &fakeClient{response: ai.Response{Text: string(payload)}}
			engine := &recordingStarter{}
			out := &bytes.Buffer{}
			_, err := NewPlanner(client).ReviewAndStart(context.Background(), engine, req, bufio.NewScanner(strings.NewReader(test.input)), out)
			if engine.calls != test.calls {
				t.Fatalf("executed %d times", engine.calls)
			}
			if test.calls == 1 && err != nil {
				t.Fatal(err)
			}
			if test.calls == 0 && !errors.Is(err, ErrNotApproved) {
				t.Fatalf("expected ErrNotApproved, got %v", err)
			}
			if !strings.Contains(out.String(), "runtime_tasks") {
				t.Fatal("actual tasks were not previewed")
			}
		})
	}
}

func TestDeclinedPlanNeverStarts(t *testing.T) {
	req, _ := fixture()
	client := &fakeClient{response: ai.Response{Text: `{"disposition":"unsupported","explanation":"No repair executor is available.","tasks":[]}`}}
	engine := &recordingStarter{}
	_, err := NewPlanner(client).ReviewAndStart(context.Background(), engine, req, bufio.NewScanner(strings.NewReader("approve\n")), &bytes.Buffer{})
	if !errors.Is(err, ErrNotReady) || engine.calls != 0 {
		t.Fatal("declined plan reached execution")
	}
}
