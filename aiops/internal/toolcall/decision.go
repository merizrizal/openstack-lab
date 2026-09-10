package toolcall

import (
	"fmt"
	"strings"
)

type ToolArguments struct {
	ServerIdentifier string `json:"server_identifier"`
}

type Decision struct {
	Action    string        `json:"action"`
	ToolName  string        `json:"tool_name"`
	Arguments ToolArguments `json:"arguments"`
	Answer    string        `json:"answer"`
}

func (d Decision) Validate() error {
	switch d.Action {
	case "answer":
		if d.ToolName != "none" {
			return fmt.Errorf("answer action must use tool_name=none")
		}

		if strings.TrimSpace(d.Answer) == "" {
			return fmt.Errorf("answer action requires answer")
		}

	case "tool":
		if d.ToolName != "get_server" {
			return fmt.Errorf("unsupported tool %q", d.ToolName)
		}

		if strings.TrimSpace(d.Arguments.ServerIdentifier) == "" {
			return fmt.Errorf("get_server requires server_identifier")
		}

		if strings.TrimSpace(d.Answer) != "" {
			return fmt.Errorf("tool action must not contain final answer")
		}

	default:
		return fmt.Errorf("invalid action %q", d.Action)
	}

	return nil
}
