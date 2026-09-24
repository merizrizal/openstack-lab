package ai

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

func piIsolationFlags() []string {
	return []string{
		"--no-session", "--no-tools", "--no-extensions", "--no-skills",
		"--no-prompt-templates", "--no-context-files", "--no-themes", "--no-approve",
	}
}

// Check runs version/help only. It does not submit an inference request.
func (c *PiClient) Check(ctx context.Context) error {
	if err := c.checkSettings(); err != nil {
		return err
	}
	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()
	workdir, err := os.MkdirTemp("", "openstack-ai-pi-check-*")
	if err != nil {
		return fmt.Errorf("create Pi check directory: %w", err)
	}
	defer os.RemoveAll(workdir)
	version, err := c.command(ctx, workdir, []string{"--version"}, "", 64*1024)
	if err != nil {
		return fmt.Errorf("check Pi version: %w", err)
	}
	if strings.TrimSpace(string(version)) != c.config.ExpectedVersion {
		return errors.New("installed Pi version differs from ExpectedVersion; review and re-test the adapter")
	}
	help, err := c.command(ctx, workdir, []string{"--help"}, "", 1<<20)
	if err != nil {
		return fmt.Errorf("check Pi flags: %w", err)
	}
	for _, flag := range append(piIsolationFlags(), "--mode", "--provider", "--model", "--system-prompt") {
		if !strings.Contains(string(help), flag) {
			return fmt.Errorf("installed Pi does not advertise required flag %s", flag)
		}
	}
	return nil
}

func (c *PiClient) runProcess(ctx context.Context, request PiOutbound) (piCompletion, error) {
	if err := c.Check(ctx); err != nil {
		return piCompletion{}, err
	}
	workdir, err := os.MkdirTemp("", "openstack-ai-pi-*")
	if err != nil {
		return piCompletion{}, fmt.Errorf("create Pi working directory: %w", err)
	}
	defer os.RemoveAll(workdir)

	// Use a 0600 prompt file so application instructions do not enter argv.
	// Pi itself reads this explicitly passed file; model filesystem tools stay off.
	promptPath := filepath.Join(workdir, "system.txt")
	if err := os.WriteFile(promptPath, []byte(request.SystemPrompt), 0600); err != nil {
		return piCompletion{}, fmt.Errorf("write Pi instructions: %w", err)
	}
	args := append(piIsolationFlags(), "--mode", "json", "--provider", request.Provider, "--model", request.Model, "--system-prompt", promptPath)
	output, err := c.command(ctx, workdir, args, request.Prompt, 32<<20)
	if err != nil {
		return piCompletion{}, err
	}
	return piParseEvents(output, request.Provider, request.Model)
}

func (c *PiClient) command(ctx context.Context, workdir string, args []string, input string, limit int) ([]byte, error) {
	binary, err := exec.LookPath(c.config.Binary)
	if err != nil {
		return nil, fmt.Errorf("locate Pi executable: %w", err)
	}
	binary, err = filepath.Abs(binary)
	if err != nil {
		return nil, fmt.Errorf("resolve Pi executable: %w", err)
	}
	childCtx, cancel := context.WithCancel(ctx)
	defer cancel()
	output := &piBoundedBuffer{limit: limit, cancel: cancel}
	cmd := exec.CommandContext(childCtx, binary, args...)
	cmd.Dir = workdir
	cmd.Env = c.environment()
	cmd.Stdin = strings.NewReader(input)
	cmd.Stdout = output
	// Do not leak provider errors, prompts, credentials or reasoning into logs.
	// Investigate failures separately with synthetic data, never raw lab payloads.
	cmd.Stderr = io.Discard
	cmd.WaitDelay = 2 * time.Second
	err = cmd.Run()
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	if output.exceeded {
		return nil, errors.New("Pi stdout exceeded byte budget")
	}
	if err != nil {
		return nil, fmt.Errorf("Pi process failed (stderr intentionally withheld): %w", err)
	}
	return output.buffer.Bytes(), nil
}

type piBoundedBuffer struct {
	buffer   bytes.Buffer
	limit    int
	cancel   context.CancelFunc
	exceeded bool
}

func (b *piBoundedBuffer) Write(data []byte) (int, error) {
	if len(data) > b.limit-b.buffer.Len() {
		b.exceeded = true
		b.cancel()
		return 0, errors.New("Pi output limit exceeded")
	}
	return b.buffer.Write(data)
}

// Deliberate allowlist, NOT os.Environ(): no OS_*, SSH_AUTH_SOCK, NODE_OPTIONS,
// arbitrary API keys, or application secrets are inherited implicitly.
func (c *PiClient) environment() []string {
	values := map[string]string{
		"PI_CODING_AGENT_DIR": c.config.AgentDir,
		"PI_OFFLINE":          "1", "PI_TELEMETRY": "0", "NO_COLOR": "1",
	}
	for _, name := range []string{"PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "TZ", "SYSTEMROOT", "WINDIR"} {
		if value, exists := os.LookupEnv(name); exists {
			values[name] = value
		}
	}
	for name, value := range c.config.ExtraEnv {
		values[name] = value
	}
	names := make([]string, 0, len(values))
	for name := range values {
		names = append(names, name)
	}
	sort.Strings(names)
	environment := make([]string, 0, len(names))
	for _, name := range names {
		environment = append(environment, name+"="+values[name])
	}
	return environment
}

func piAllowedExtraEnv(name string) bool {
	switch name {
	case "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY",
		"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "NODE_EXTRA_CA_CERTS", "SSL_CERT_FILE":
		return true
	default:
		return false
	}
}
