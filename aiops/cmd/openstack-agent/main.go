package main

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"strings"
	"time"

	"openstacklab/openstack-ai/internal/agent"
	"openstacklab/openstack-ai/internal/ai"
	"openstacklab/openstack-ai/internal/openstackclient"
	"openstacklab/openstack-ai/internal/tools"
)

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	computeClient, err := openstackclient.NewComputeClient(ctx)
	cancel()
	if err != nil {
		fail("initialize OpenStack: %v", err)
	}

	aiClient := ai.NewCodexClient(
		getenv("CODEX_BIN", "codex"),
		strings.TrimSpace(os.Getenv("CODEX_MODEL")),
	)

	registry, err := tools.NewRegistry(
		tools.NewGetServerTool(computeClient),
		tools.NewGetFlavorTool(computeClient),
	)
	if err != nil {
		fail("create tool registry: %v", err)
	}

	runtime := agent.NewRuntime(aiClient, registry, 6)

	fmt.Println("OpenStack AI Assistant - Stage 4")
	fmt.Println("Agent tools: get_server, get_flavor")
	fmt.Println("Read-only agent loop")
	fmt.Println()
	fmt.Println("Commands:")
	fmt.Println("  /exit   quit")
	fmt.Println()

	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 1024), 1024*1024)

	for {
		fmt.Print("> ")

		if !scanner.Scan() {
			break
		}

		input := strings.TrimSpace(scanner.Text())
		if input == "" {
			continue
		}
		if input == "/exit" {
			return
		}

		requestCtx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
		result, err := runtime.Run(requestCtx, input)
		cancel()

		printTrace(result.Observations)

		if err != nil {
			fmt.Printf("\nAgent error: %v\n\n", err)
			continue
		}

		fmt.Printf("\n%s\n\n", result.Answer)
		fmt.Printf(
			"[decisions=%d tool_calls=%d input=%d cached=%d output=%d reasoning=%d]\n\n",
			result.Steps,
			len(result.Observations),
			result.Usage.InputTokens,
			result.Usage.CachedInputTokens,
			result.Usage.OutputTokens,
			result.Usage.ReasoningOutputTokens,
		)
	}

	if err := scanner.Err(); err != nil {
		fail("read stdin: %v", err)
	}
}

func printTrace(observations []agent.Observation) {
	for _, observation := range observations {
		fmt.Printf(
			"\n[step %d] tool=%s args=%s\n",
			observation.Step,
			observation.Tool,
			string(observation.Arguments),
		)

		if observation.Error != "" {
			fmt.Printf("[step %d] error=%s\n", observation.Step, observation.Error)
			continue
		}

		fmt.Printf("[step %d] result=%s\n", observation.Step, string(observation.Result))
	}
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
