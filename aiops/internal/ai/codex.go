package ai

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
)

type CodexClient struct {
	binary string
	model  string
}

func NewCodexClient(binary, model string) *CodexClient {
	if strings.TrimSpace(binary) == "" {
		binary = "codex"
	}

	return &CodexClient{
		binary: binary,
		model:  strings.TrimSpace(model),
	}
}

// codexEvent represents the subset of Codex exec JSONL
// events that Stage 1 cares about.
type codexEvent struct {
	Type string `json:"type"`

	Item *struct {
		Type string `json:"type"`
		Text string `json:"text"`
	} `json:"item,omitempty"`

	Usage *struct {
		InputTokens           int64 `json:"input_tokens"`
		CachedInputTokens     int64 `json:"cached_input_tokens"`
		OutputTokens          int64 `json:"output_tokens"`
		ReasoningOutputTokens int64 `json:"reasoning_output_tokens"`
	} `json:"usage,omitempty"`

	Error *struct {
		Message string `json:"message"`
	} `json:"error,omitempty"`

	Message string `json:"message,omitempty"`
}

func (c *CodexClient) Chat(
	ctx context.Context,
	messages []Message,
) (Response, error) {

	// Give every inference request a clean working directory.
	//
	// Stage 1 should not depend on repository contents,
	// AGENTS.md files, OpenStack credentials, etc.
	workDir, err := os.MkdirTemp(
		"",
		"openstack-ai-stage1-*",
	)
	if err != nil {
		return Response{}, fmt.Errorf(
			"create temporary Codex directory: %w",
			err,
		)
	}
	defer os.RemoveAll(workDir)

	prompt := buildPrompt(messages)

	args := []string{
		"exec",

		// Produce machine-readable JSONL events.
		"--json",

		// Do not persist the Codex thread/session.
		"--ephemeral",

		// Don't allow local ~/.codex configuration to modify
		// our learning experiment. Authentication is still used.
		"--ignore-user-config",

		// Ignore project/user execution rules.
		"--ignore-rules",

		// Our temporary directory is intentionally not a Git repo.
		"--skip-git-repo-check",

		// Stage 1 must not write files.
		"--sandbox",
		"read-only",

		"--color",
		"never",

		// Run Codex from our empty temporary directory.
		"--cd",
		workDir,
	}

	// Model selection is optional.
	//
	// If CODEX_MODEL is not configured, we let the user's
	// Codex account/configuration choose its available default.
	if c.model != "" {
		args = append(
			args,
			"--model",
			c.model,
		)
	}

	// "-" means read the prompt from stdin.
	args = append(args, "-")

	cmd := exec.CommandContext(
		ctx,
		c.binary,
		args...,
	)

	cmd.Stdin = strings.NewReader(prompt)

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return Response{}, fmt.Errorf(
			"capture Codex stdout: %w",
			err,
		)
	}

	var stderr bytes.Buffer
	cmd.Stderr = &stderr

	if err := cmd.Start(); err != nil {
		return Response{}, fmt.Errorf(
			"start Codex: %w",
			err,
		)
	}

	var (
		finalText string
		usage     Usage
		turnError string
	)

	scanner := bufio.NewScanner(stdout)

	// Codex responses/events can be larger than Scanner's
	// small default token size.
	scanner.Buffer(
		make([]byte, 64*1024),
		10*1024*1024,
	)

	for scanner.Scan() {
		line := scanner.Bytes()

		var event codexEvent

		if err := json.Unmarshal(line, &event); err != nil {
			_ = cmd.Process.Kill()
			_ = cmd.Wait()

			return Response{}, fmt.Errorf(
				"decode Codex JSONL event: %w\nline: %s",
				err,
				string(line),
			)
		}

		switch event.Type {

		case "item.completed":
			if event.Item != nil &&
				event.Item.Type == "agent_message" {

				// Keep the latest completed assistant message.
				finalText = event.Item.Text
			}

		case "turn.completed":
			if event.Usage != nil {
				usage = Usage{
					InputTokens:           event.Usage.InputTokens,
					CachedInputTokens:     event.Usage.CachedInputTokens,
					OutputTokens:          event.Usage.OutputTokens,
					ReasoningOutputTokens: event.Usage.ReasoningOutputTokens,
				}
			}

		case "turn.failed":
			if event.Error != nil {
				turnError = event.Error.Message
			}

		case "error":
			if event.Message != "" {
				turnError = event.Message
			}
		}
	}

	if err := scanner.Err(); err != nil {
		_ = cmd.Process.Kill()
		_ = cmd.Wait()

		return Response{}, fmt.Errorf(
			"read Codex JSONL stream: %w",
			err,
		)
	}

	if err := cmd.Wait(); err != nil {
		return Response{}, fmt.Errorf(
			"Codex execution failed: %w\nstderr: %s",
			err,
			strings.TrimSpace(stderr.String()),
		)
	}

	if turnError != "" {
		return Response{}, fmt.Errorf(
			"Codex turn failed: %s",
			turnError,
		)
	}

	finalText = strings.TrimSpace(finalText)

	if finalText == "" {
		return Response{}, fmt.Errorf(
			"Codex returned no final assistant message",
		)
	}

	return Response{
		Text:  finalText,
		Usage: usage,
	}, nil
}

// buildPrompt converts our application's role-based conversation
// into one prompt for Codex.
//
// This is important:
//
// Codex exec accepts an initial prompt. Our application therefore
// owns the logical message model and serializes it into that prompt.
func buildPrompt(messages []Message) string {
	var builder strings.Builder

	builder.WriteString(`
You are being used as the text inference backend for a Stage 1
AI-engineering learning application.

IMPORTANT MODE CONSTRAINTS:

- Treat this as a text-only question-and-answer task.
- Do not inspect files.
- Do not execute shell commands.
- Do not modify anything.
- Do not search the web.
- Do not attempt to access OpenStack.
- Use only the supplied conversation below.
- Respond only to the final USER message.

The application supplies logical SYSTEM, USER, and ASSISTANT
messages below.
`)

	for _, message := range messages {
		role := strings.ToUpper(
			strings.TrimSpace(message.Role),
		)

		builder.WriteString("\n\n===== ")
		builder.WriteString(role)
		builder.WriteString(" =====\n")

		builder.WriteString(message.Content)
	}

	builder.WriteString(`

===== END OF CONVERSATION =====

Respond to the final USER message.
`)

	return builder.String()
}
