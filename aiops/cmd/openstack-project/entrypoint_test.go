package main

import (
	"bytes"
	"context"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync/atomic"
	"syscall"
	"testing"
	"time"
)

const invokeProjectMainForTest = "AIOPS_TEST_INVOKE_PROJECT_MAIN"

func TestLegacyMainRefusesBeforeSideEffects(t *testing.T) {
	if os.Getenv(invokeProjectMainForTest) == "1" {
		main()
		return
	}

	root := t.TempDir()
	dataDir := filepath.Join(root, "legacy-data")
	if err := os.Mkdir(dataDir, 0700); err != nil {
		t.Fatal(err)
	}
	sentinel := filepath.Join(dataDir, "legacy-record.json")
	if err := os.WriteFile(sentinel, []byte("synthetic legacy record"), 0600); err != nil {
		t.Fatal(err)
	}
	knowledgeDir := filepath.Join(root, "knowledge")
	if err := os.Mkdir(knowledgeDir, 0700); err != nil {
		t.Fatal(err)
	}
	if err := syscall.Mkfifo(filepath.Join(knowledgeDir, "trap.md"), 0600); err != nil {
		t.Fatal(err)
	}

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
		{name: "project goal", text: "investigate synthetic project for 550e8400-e29b-41d4-a716-446655440000\n"},
		{name: "resume", text: "/resume synthetic-id\n"},
		{name: "show", text: "/show synthetic-id\n"},
		{name: "exit", text: "/exit\n"},
	}

	for _, input := range inputs {
		t.Run(input.name, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
			defer cancel()
			cmd := exec.CommandContext(ctx, executable, "-test.run=^TestLegacyMainRefusesBeforeSideEffects$")
			cmd.Env = []string{
				invokeProjectMainForTest + "=1",
				"PATH=/usr/bin:/bin",
				"HOME=" + root,
				"TMPDIR=" + root,
				"AI_CLIENT=codex",
				"CODEX_BIN=" + fakeCodex,
				"AIOPS_TEST_MODEL_MARKER=" + modelMarker,
				"OPENSTACK_AI_DATA_DIR=" + dataDir,
				"OPENSTACK_AI_KNOWLEDGE_DIR=" + knowledgeDir,
				"OS_AUTH_URL=" + authServer.URL,
				"OS_USERNAME=synthetic-user",
				"OS_PASSWORD=inert-test-value",
				"OS_PROJECT_NAME=synthetic-project",
				"OS_USER_DOMAIN_NAME=Default",
				"OS_PROJECT_DOMAIN_NAME=Default",
				"OS_REGION_NAME=RegionOne",
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
			if !strings.Contains(string(output), "openstack-project is disabled; use aiops") {
				t.Fatalf("main() did not positively report refusal: %s", output)
			}
			if got := authRequests.Load(); got != 0 {
				t.Fatalf("refused command made %d cloud/auth requests", got)
			}
			if _, err := os.Stat(modelMarker); !os.IsNotExist(err) {
				t.Fatalf("model trap was reached: stat error=%v", err)
			}
			for _, name := range []string{"investigations", "memories", "workflows", "projects"} {
				if _, err := os.Stat(filepath.Join(dataDir, name)); !os.IsNotExist(err) {
					t.Fatalf("legacy store path %q was initialized: stat error=%v", name, err)
				}
			}
			if got, err := os.ReadFile(sentinel); err != nil || !bytes.Equal(got, []byte("synthetic legacy record")) {
				t.Fatalf("synthetic legacy record changed: data=%q err=%v", got, err)
			}
		})
	}
}
