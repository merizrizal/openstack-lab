package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"
	"time"

	"openstacklab/openstack-ai/internal/ai"
	"openstacklab/openstack-ai/internal/diagnosis"
)

func main() {
	codexBinary := getenv("CODEX_BIN", "codex")
	codexModel := strings.TrimSpace(os.Getenv("CODEX_MODEL"))
	client := ai.NewCodexClient(codexBinary, codexModel)
	analyzer := diagnosis.NewAnalyzer(client)

	evidence, err := io.ReadAll(os.Stdin)
	if err != nil {
		fail("read evidence: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	result, usage, err := analyzer.Analyze(ctx, string(evidence))
	if err != nil {
		fail("analyze incident: %v", err)
	}

	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")

	if err := encoder.Encode(result); err != nil {
		fail("encode result: %v", err)
	}

	fmt.Fprintf(
		os.Stderr,
		"\n[input=%d cached=%d output=%d reasoning=%d]\n",
		usage.InputTokens,
		usage.CachedInputTokens,
		usage.OutputTokens,
		usage.ReasoningOutputTokens,
	)
}

func getenv(key, fallback string) string {
	value := strings.TrimSpace(os.Getenv(key))

	if value == "" {
		return fallback
	}

	return value
}

func fail(format string, args ...any) {
	fmt.Fprintf(os.Stderr, format+"\n", args...)
	os.Exit(1)
}
