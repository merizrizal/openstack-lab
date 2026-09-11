package ai

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
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

func (c *CodexClient) run(ctx context.Context, messages []Message, schema []byte) (Response, error) {
	workDir, err := os.MkdirTemp("", "openstack-ai-*")
	if err != nil {
		return Response{}, fmt.Errorf("create temporary Codex directory: %w", err)
	}
	defer os.RemoveAll(workDir)

	prompt := buildPrompt(messages)

	args := []string{
		"exec",
		"--json",
		"--ephemeral",
		"--ignore-user-config",
		"--ignore-rules",
		"--skip-git-repo-check",
		"--sandbox",
		"read-only",
		"--color",
		"never",
		"--cd",
		workDir,
	}

	if c.model != "" {
		args = append(args, "--model", c.model)
	}

	if len(schema) > 0 {
		schemaPath := filepath.Join(workDir, "output.schema.json")

		if err := os.WriteFile(schemaPath, schema, 0600); err != nil {
			return Response{}, fmt.Errorf("write Codex output schema: %w", err)
		}

		args = append(args, "--output-schema", schemaPath)
	}

	args = append(args, "-")

	cmd := exec.CommandContext(ctx, c.binary, args...)
	cmd.Env = filteredCodexEnvironment()
	cmd.Stdin = strings.NewReader(prompt)

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return Response{}, fmt.Errorf("capture Codex stdout: %w", err)
	}

	var stderr bytes.Buffer
	cmd.Stderr = &stderr

	if err := cmd.Start(); err != nil {
		return Response{}, fmt.Errorf("start Codex: %w", err)
	}

	var (
		finalText string
		usage     Usage
		turnError string
	)

	scanner := bufio.NewScanner(stdout)
	scanner.Buffer(make([]byte, 64*1024), 10*1024*1024)

	for scanner.Scan() {
		line := scanner.Bytes()

		var event codexEvent

		if err := json.Unmarshal(line, &event); err != nil {
			_ = cmd.Process.Kill()
			_ = cmd.Wait()

			return Response{}, fmt.Errorf("decode Codex JSONL event: %w\nline: %s", err, string(line))
		}

		switch event.Type {
		case "item.completed":
			if event.Item != nil && event.Item.Type == "agent_message" {
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

		return Response{}, fmt.Errorf("read Codex JSONL stream: %w", err)
	}

	if err := cmd.Wait(); err != nil {
		return Response{}, fmt.Errorf(
			"Codex execution failed: %w\nstderr: %s",
			err,
			strings.TrimSpace(stderr.String()),
		)
	}

	if turnError != "" {
		return Response{}, fmt.Errorf("Codex turn failed: %s", turnError)
	}

	finalText = strings.TrimSpace(finalText)

	if finalText == "" {
		return Response{}, fmt.Errorf("Codex returned no final assistant message")
	}

	return Response{
		Text:  finalText,
		Usage: usage,
	}, nil
}

func (c *CodexClient) Chat(ctx context.Context, messages []Message) (Response, error) {
	return c.run(ctx, messages, nil)
}

func (c *CodexClient) ChatStructured(ctx context.Context, messages []Message, schema []byte) (Response, error) {
	if len(schema) == 0 {
		return Response{}, fmt.Errorf("structured chat requires JSON schema")
	}

	return c.run(ctx, messages, schema)
}

func buildPrompt(messages []Message) string {
	var builder strings.Builder

	builder.WriteString(`
You are being used as the text inference backend for
AI-engineering learning application.

IMPORTANT MODE CONSTRAINTS:

- Treat this as a text-only question-and-answer task.
- Do not inspect files.
- Do not execute shell commands.
- Do not modify anything.
- Do not search the web.
- Do not attempt to access OpenStack.
- Do not access OpenStack or external systems yourself.
- Do not execute shell commands to retrieve infrastructure data.
- If the application asks for a tool decision, request only one of the explicitly supplied tools.
- Tool execution happens outside Codex.
- Use only the supplied conversation below.
- Respond only to the final USER message.

The application supplies logical SYSTEM, USER, and ASSISTANT
messages below.
`)

	for _, message := range messages {
		role := strings.ToUpper(strings.TrimSpace(message.Role))

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

func filteredCodexEnvironment() []string {
	current := os.Environ()
	filtered := make([]string, 0, len(current))

	for _, entry := range current {
		key, _, ok := strings.Cut(entry, "=")

		if !ok {
			continue
		}

		if strings.HasPrefix(key, "OS_") {
			continue
		}

		filtered = append(filtered, entry)
	}

	return filtered
}
