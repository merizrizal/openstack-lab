package main

import (
	"bytes"
	"strings"
	"testing"
)

func TestLocalCommandsAndUnavailableDiagnostics(t *testing.T) {
	tests := []struct {
		name       string
		args       []string
		wantCode   int
		wantOutput string
		wantError  bool
	}{
		{name: "help", args: []string{"help"}, wantCode: 0, wantOutput: "local-only"},
		{name: "readiness", args: []string{"readiness"}, wantCode: 1, wantOutput: "status=unavailable"},
		{name: "catalog", args: []string{"catalog"}, wantCode: 0, wantOutput: "diagnostics=unavailable"},
		{name: "diagnostic request", args: []string{"diagnose", "server"}, wantCode: 2, wantOutput: "diagnostic unavailable", wantError: true},
		{name: "unknown diagnostic", args: []string{"server-basic"}, wantCode: 2, wantOutput: "diagnostic unavailable", wantError: true},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			var stdout, stderr bytes.Buffer
			code := run(test.args, &stdout, &stderr)
			if code != test.wantCode {
				t.Fatalf("run() code = %d, want %d", code, test.wantCode)
			}

			actual := stdout.String()
			if test.wantError {
				actual = stderr.String()
			}
			if !strings.Contains(actual, test.wantOutput) {
				t.Fatalf("output %q does not contain %q", actual, test.wantOutput)
			}
			if strings.Contains(stdout.String(), "status=ready") {
				t.Fatalf("readiness must not claim success: %q", stdout.String())
			}
		})
	}
}
