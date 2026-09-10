package agent

import (
	"encoding/json"
	"testing"
)

func TestDecisionUsesServerIdentifier(t *testing.T) {
	decision := Decision{
		Action:   "tool",
		ToolName: "get_server",
		Arguments: ToolArguments{
			ServerIdentifier: "web-01",
		},
	}

	if err := decision.Validate(); err != nil {
		t.Fatalf("Validate() error = %v", err)
	}

	arguments, err := json.Marshal(decision.Arguments)
	if err != nil {
		t.Fatalf("Marshal() error = %v", err)
	}
	if got := string(arguments); got != `{"server_identifier":"web-01"}` {
		t.Fatalf("arguments JSON = %s", got)
	}
}
