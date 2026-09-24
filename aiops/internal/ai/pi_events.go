package ai

import (
	"bufio"
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
)

type piTokenUsage struct {
	Input      int64  `json:"input"`
	Output     int64  `json:"output"`
	CacheRead  int64  `json:"cacheRead"`
	CacheWrite int64  `json:"cacheWrite"`
	Reasoning  *int64 `json:"reasoning"`
}

type piContent struct {
	Type string `json:"type"`
	Text string `json:"text"`
}

type piMessage struct {
	Role          string        `json:"role"`
	Provider      string        `json:"provider"`
	Model         string        `json:"model"`
	ResponseModel string        `json:"responseModel"`
	StopReason    string        `json:"stopReason"`
	Content       []piContent   `json:"content"`
	Usage         *piTokenUsage `json:"usage"`
}

type piCompletion struct {
	Text, ResponseModel string
	Usage               piTokenUsage
}

// Accept one completed, text-only inference. Do not mistake exit status 0,
// streaming deltas, or a valid-looking partial JSON string for success.
func piParseEvents(data []byte, provider, model string) (piCompletion, error) {
	scanner := bufio.NewScanner(bytes.NewReader(data))
	scanner.Buffer(make([]byte, 64*1024), 16<<20)
	var completion piCompletion
	completedMessages, agentEnds := 0, 0
	assistantStarted := false

	for scanner.Scan() {
		if len(bytes.TrimSpace(scanner.Bytes())) == 0 {
			continue
		}
		var event struct {
			Type                  string            `json:"type"`
			Message               json.RawMessage   `json:"message"`
			Steering              []json.RawMessage `json:"steering"`
			FollowUp              []json.RawMessage `json:"followUp"`
			AssistantMessageEvent struct {
				Type string `json:"type"`
			} `json:"assistantMessageEvent"`
		}
		if err := json.Unmarshal(scanner.Bytes(), &event); err != nil {
			return piCompletion{}, errors.New("Pi emitted a malformed JSON event")
		}
		if strings.HasPrefix(event.Type, "tool_execution_") {
			return piCompletion{}, errors.New("Pi attempted tool execution; rejecting inference")
		}
		if strings.HasPrefix(event.AssistantMessageEvent.Type, "toolcall_") {
			return piCompletion{}, errors.New("Pi emitted a native tool call; rejecting inference")
		}
		if event.AssistantMessageEvent.Type == "error" {
			return piCompletion{}, errors.New("Pi reported an inference error")
		}

		switch event.Type {
		case "session", "agent_start", "turn_start", "turn_end", "agent_settled":
			// No output is accepted from snapshots or lifecycle metadata.
		case "queue_update":
			if len(event.Steering) != 0 || len(event.FollowUp) != 0 {
				return piCompletion{}, errors.New("Pi queued additional input; one-shot contract violated")
			}
		case "message_update":
			// Ignore text/thinking deltas. Only message_end is authoritative.
		case "message_start", "message_end":
			var header struct {
				Role         string            `json:"role"`
				ToolsAdded   []json.RawMessage `json:"toolsAdded"`
				ToolsRemoved []json.RawMessage `json:"toolsRemoved"`
			}
			if err := json.Unmarshal(event.Message, &header); err != nil {
				return piCompletion{}, errors.New("Pi message has an invalid header")
			}
			if agentEnds != 0 {
				return piCompletion{}, fmt.Errorf("unexpected Pi %s after agent_end (role=%q)", event.Type, header.Role)
			}
			switch header.Role {
			case "system", "user":
				if assistantStarted || completedMessages != 0 {
					return piCompletion{}, fmt.Errorf("Pi emitted %s with role %q after assistant output started", event.Type, header.Role)
				}
				if len(header.ToolsAdded) != 0 || len(header.ToolsRemoved) != 0 {
					return piCompletion{}, errors.New("Pi declared or changed native tools; rejecting inference")
				}
				// Pi can emit initial system/user messages. They are input,
				// not model output. Do not decode, return or log their content.
				continue
			case "assistant":
				if event.Type == "message_start" {
					if assistantStarted || completedMessages != 0 {
						return piCompletion{}, errors.New("Pi started multiple assistant messages; one-shot contract violated")
					}
					assistantStarted = true
					continue
				}
			default:
				return piCompletion{}, fmt.Errorf("unsupported Pi message role %q in %s", header.Role, event.Type)
			}
			var message piMessage
			if err := json.Unmarshal(event.Message, &message); err != nil {
				return piCompletion{}, errors.New("Pi assistant message has an invalid format")
			}
			if message.Provider != provider || message.Model != model {
				return piCompletion{}, errors.New("Pi selected a different provider/model; use an exact available model ID")
			}
			if message.StopReason != "stop" {
				return piCompletion{}, errors.New("Pi response was errored, aborted, truncated, deferred or tool-using")
			}
			if message.Usage == nil || !piUsageValid(*message.Usage) {
				return piCompletion{}, errors.New("Pi returned invalid or missing usage metadata")
			}
			var text strings.Builder
			for _, block := range message.Content {
				switch block.Type {
				case "text":
					text.WriteString(block.Text)
				case "thinking":
					// Never return, log, or persist reasoning content.
				default:
					return piCompletion{}, errors.New("Pi returned non-text/non-thinking content")
				}
			}
			completedMessages++
			if completedMessages != 1 {
				return piCompletion{}, errors.New("Pi produced multiple assistant messages; one-shot contract violated")
			}
			completion = piCompletion{Text: strings.TrimSpace(text.String()), ResponseModel: message.ResponseModel, Usage: *message.Usage}
		case "agent_end":
			agentEnds++
			if agentEnds != 1 || completedMessages != 1 {
				return piCompletion{}, errors.New("Pi ended without exactly one completed assistant message")
			}
		default:
			// Includes auto_retry/compaction/model-change events. Those may add
			// hidden model calls; this adapter deliberately does not accept them.
			return piCompletion{}, fmt.Errorf("unsupported Pi event type %q", event.Type)
		}
	}
	if err := scanner.Err(); err != nil {
		return piCompletion{}, errors.New("Pi event exceeds the event size budget")
	}
	if agentEnds != 1 || completedMessages != 1 || completion.Text == "" || len(completion.Text) > 1<<20 {
		return piCompletion{}, errors.New("Pi returned no complete bounded text response")
	}
	return completion, nil
}

func piUsageValid(u piTokenUsage) bool {
	for _, n := range []int64{u.Input, u.Output, u.CacheRead, u.CacheWrite} {
		if n < 0 || n > 1<<40 {
			return false
		}
	}
	return u.Reasoning == nil || (*u.Reasoning >= 0 && *u.Reasoning <= u.Output)
}
