package agent

import (
	"encoding/json"
	"fmt"
	"strings"

	"openstacklab/openstack-ai/internal/ai"
)

type ToolArguments struct {
	ServerID string `json:"server_id,omitempty"`
	FlavorID string `json:"flavor_id,omitempty"`
}

type Decision struct {
	Action      string        `json:"action"`
	ToolName    string        `json:"tool_name"`
	Arguments   ToolArguments `json:"arguments"`
	FinalAnswer string        `json:"final_answer"`
}

func (d Decision) Validate() error {
	switch d.Action {
	case "finish":
		if d.ToolName != "none" {
			return fmt.Errorf("finish action must use tool_name=none")
		}
		if d.FinalAnswer == "" {
			return fmt.Errorf("finish action requires final_answer")
		}

	case "tool":
		if d.FinalAnswer != "" {
			return fmt.Errorf("tool action must not contain final_answer")
		}

		switch d.ToolName {
		case "get_server":
			if d.Arguments.ServerID == "" {
				return fmt.Errorf("get_server requires server_id")
			}
			if d.Arguments.FlavorID != "" {
				return fmt.Errorf("get_server must not contain flavor_id")
			}

		case "get_flavor":
			if d.Arguments.FlavorID == "" {
				return fmt.Errorf("get_flavor requires flavor_id")
			}
			if d.Arguments.ServerID != "" {
				return fmt.Errorf("get_flavor must not contain server_id")
			}

		default:
			return fmt.Errorf("unsupported tool %q", d.ToolName)
		}

	default:
		return fmt.Errorf("invalid action %q", d.Action)
	}

	return nil
}

func (d *Decision) Normalize() {
	d.Action = strings.TrimSpace(d.Action)
	d.ToolName = strings.TrimSpace(d.ToolName)
	d.FinalAnswer = strings.TrimSpace(d.FinalAnswer)
	d.Arguments.ServerID = strings.TrimSpace(d.Arguments.ServerID)
	d.Arguments.FlavorID = strings.TrimSpace(d.Arguments.FlavorID)

	if d.Action == "finish" {
		d.Arguments = ToolArguments{}
	}
}

type Observation struct {
	Step      int             `json:"step"`
	Tool      string          `json:"tool"`
	Arguments json.RawMessage `json:"arguments"`
	Result    json.RawMessage `json:"result,omitempty"`
	Error     string          `json:"error,omitempty"`
}

type State struct {
	Goal         string        `json:"goal"`
	Observations []Observation `json:"observations"`
}

type Result struct {
	Answer       string
	Steps        int
	Observations []Observation
	Usage        ai.Usage
}
