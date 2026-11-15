package main

import (
	"context"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

const invokeChatMainForTest = "AIOPS_TEST_INVOKE_CHAT_MAIN"

func TestLegacyMainRefusesBeforeInference(t *testing.T) {
	if os.Getenv(invokeChatMainForTest) == "1" {
		main()
		return
	}

	root := t.TempDir()
	modelMarker := filepath.Join(root, "model-invoked")
	fakeCodex := filepath.Join(root, "fake-codex")
	script := "#!/bin/sh\nprintf invoked > \"$AIOPS_TEST_MODEL_MARKER\"\nexit 0\n"
	if err := os.WriteFile(fakeCodex, []byte(script), 0700); err != nil {
		t.Fatal(err)
	}

	var authRequests atomic.Int32
	authServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		authRequests.Add(1)
		http.Error(w, "inert test auth endpoint", http.StatusUnauthorized)
	}))
	defer authServer.Close()

	executable, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	inputs := []struct {
		name string
		text string
	}{
		{name: "model prompt", text: "explain this synthetic issue\n"},
		{name: "reset", text: "/reset\n"},
		{name: "exit", text: "/exit\n"},
	}

	for _, input := range inputs {
		t.Run(input.name, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
			defer cancel()
			cmd := exec.CommandContext(ctx, executable, "-test.run=^TestLegacyMainRefusesBeforeInference$")
			cmd.Env = []string{
				invokeChatMainForTest + "=1",
				"PATH=/usr/bin:/bin",
				"HOME=" + root,
				"TMPDIR=" + root,
				"AI_CLIENT=codex",
				"CODEX_BIN=" + fakeCodex,
				"AIOPS_TEST_MODEL_MARKER=" + modelMarker,
				"OS_AUTH_URL=" + authServer.URL,
				"OS_USERNAME=synthetic-user",
				"OS_PASSWORD=inert-test-value",
				"OS_PROJECT_NAME=synthetic-project",
				"OS_USER_DOMAIN_NAME=Default",
				"OS_PROJECT_DOMAIN_NAME=Default",
			}
			cmd.Stdin = strings.NewReader(input.text)
			output, runErr := cmd.CombinedOutput()
			if ctx.Err() != nil {
				t.Fatalf("entry point did not refuse promptly: %v; output: %s", ctx.Err(), output)
			}
			exitErr, ok := runErr.(*exec.ExitError)
			if !ok || exitErr.ExitCode() != 2 {
				t.Fatalf("main() exit = %v, output: %s", runErr, output)
			}
			if !strings.Contains(string(output), "openstack-ai is disabled; use aiops") {
				t.Fatalf("main() did not positively report refusal: %s", output)
			}
			if got := authRequests.Load(); got != 0 {
				t.Fatalf("chat command made %d cloud/auth requests", got)
			}
			if _, err := os.Stat(modelMarker); !os.IsNotExist(err) {
				t.Fatalf("model trap was reached: stat error=%v", err)
			}
		})
	}
}
