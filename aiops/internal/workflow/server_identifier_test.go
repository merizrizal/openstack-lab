package workflow

import (
	"context"
	"reflect"
	"testing"
)

func TestExtractServerIdentifiersFindsUUIDsAndMarkedNames(t *testing.T) {
	goal := `Investigate 550e8400-e29b-41d4-a716-446655440000 and A8AC160F-12E5-461A-ACD7-B79834DC548D; server_identifier=web-01. server_identifier="Web Application 01".`

	got := ExtractServerIdentifiers(goal)
	want := []string{
		"550e8400-e29b-41d4-a716-446655440000",
		"a8ac160f-12e5-461a-acd7-b79834dc548d",
		"web-01",
		"Web Application 01",
	}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("ExtractServerIdentifiers() = %#v, want %#v", got, want)
	}
}

func TestExtractServerIdentifiersAcceptsSentencePunctuationAroundUUID(t *testing.T) {
	goal := "Investigate 550e8400-e29b-41d4-a716-446655440000."

	got := ExtractServerIdentifiers(goal)
	want := []string{"550e8400-e29b-41d4-a716-446655440000"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("ExtractServerIdentifiers() = %#v, want %#v", got, want)
	}
}

func TestExtractServerIdentifiersRejectsFragmentsAndUnmarkedNames(t *testing.T) {
	goal := "Investigate 550e8400-e29b-41d4-a716 and web-01; reject server_identifier=web-01/other"

	if got := ExtractServerIdentifiers(goal); len(got) != 0 {
		t.Fatalf("ExtractServerIdentifiers() = %#v, want no identifiers", got)
	}
}

func TestLeadingServerIdentifierWinsOverIdentifiersInGoalContext(t *testing.T) {
	goal := "server_identifier=\"Web Application 01\"\nInvestigation goal includes 550e8400-e29b-41d4-a716-446655440000 and server_identifier=other-server"

	got, ok := LeadingServerIdentifier(goal)
	if !ok {
		t.Fatal("LeadingServerIdentifier() found no target")
	}
	if got != "Web Application 01" {
		t.Fatalf("LeadingServerIdentifier() = %q, want exact server name", got)
	}
}

func TestValidateInputUsesMarkedNameInsteadOfGoalContextUUID(t *testing.T) {
	state := &State{
		Goal: "Investigate API failures for server_identifier=web-01 and context UUID 550e8400-e29b-41d4-a716-446655440000",
	}

	if _, err := (&validateInputStep{}).Run(context.Background(), state); err != nil {
		t.Fatalf("validateInputStep.Run() error = %v", err)
	}
	if state.ServerIdentifier != "web-01" {
		t.Errorf("server identifier = %q, want marked name", state.ServerIdentifier)
	}
}

func TestValidateInputUsesLeadingServerIdentifier(t *testing.T) {
	state := &State{
		Goal: "server_identifier=\"Web Application 01\"\nInvestigation goal includes 550e8400-e29b-41d4-a716-446655440000",
	}

	next, err := (&validateInputStep{}).Run(context.Background(), state)
	if err != nil {
		t.Fatalf("validateInputStep.Run() error = %v", err)
	}
	if next != StepCollectBaseline {
		t.Errorf("next step = %q, want %q", next, StepCollectBaseline)
	}
	if state.ServerIdentifier != "Web Application 01" {
		t.Errorf("server identifier = %q, want exact name", state.ServerIdentifier)
	}
}
