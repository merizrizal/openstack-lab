package agent

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"openstacklab/openstack-ai/internal/ai"
)

const (
	StatusRunning   = "running"
	StatusPaused    = "paused"
	StatusCompleted = "completed"
)

type ToolArguments struct {
	ServerIdentifier string `json:"server_identifier,omitempty"`
	FlavorID         string `json:"flavor_id,omitempty"`
}

type Decision struct {
	Action      string        `json:"action"`
	ToolName    string        `json:"tool_name"`
	Arguments   ToolArguments `json:"arguments"`
	FinalAnswer string        `json:"final_answer"`
}

func (d *Decision) Normalize() {
	d.Action = strings.TrimSpace(d.Action)
	d.ToolName = strings.TrimSpace(d.ToolName)
	d.FinalAnswer = strings.TrimSpace(d.FinalAnswer)
	d.Arguments.ServerIdentifier = strings.TrimSpace(d.Arguments.ServerIdentifier)
	d.Arguments.FlavorID = strings.TrimSpace(d.Arguments.FlavorID)

	if d.Action == "finish" {
		d.Arguments = ToolArguments{}
	}
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
			if d.Arguments.ServerIdentifier == "" {
				return fmt.Errorf("get_server requires server_identifier")
			}
			if d.Arguments.FlavorID != "" {
				return fmt.Errorf("get_server must not contain flavor_id")
			}

		case "get_flavor":
			if d.Arguments.FlavorID == "" {
				return fmt.Errorf("get_flavor requires flavor_id")
			}
			if d.Arguments.ServerIdentifier != "" {
				return fmt.Errorf("get_flavor must not contain server_identifier")
			}

		default:
			return fmt.Errorf("unsupported tool %q", d.ToolName)
		}

	default:
		return fmt.Errorf("invalid action %q", d.Action)
	}

	return nil
}

type Observation struct {
	Step      int             `json:"step"`
	Tool      string          `json:"tool"`
	Arguments json.RawMessage `json:"arguments"`
	Result    json.RawMessage `json:"result,omitempty"`
	Error     string          `json:"error,omitempty"`
}

type State struct {
	ID              string        `json:"id"`
	Goal            string        `json:"goal"`
	Status          string        `json:"status"`
	Step            int           `json:"step"`
	Summary         string        `json:"summary,omitempty"`
	SummarizedCount int           `json:"summarized_count"`
	Observations    []Observation `json:"observations"`
	FinalAnswer     string        `json:"final_answer,omitempty"`
	CreatedAt       time.Time     `json:"created_at"`
	UpdatedAt       time.Time     `json:"updated_at"`
}

type MemoryRecord struct {
	ID              string    `json:"id"`
	InvestigationID string    `json:"investigation_id"`
	Subjects        []string  `json:"subjects"`
	Goal            string    `json:"goal"`
	Summary         string    `json:"summary"`
	CreatedAt       time.Time `json:"created_at"`
}

type Result struct {
	InvestigationID  string
	Status           string
	Answer           string
	Steps            int
	Observations     []Observation
	HistoricalMemory int
	Usage            ai.Usage
}
