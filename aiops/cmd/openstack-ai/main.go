package main

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"strings"
	"time"

	"openstacklab/openstack-ai/internal/ai"
	"openstacklab/openstack-ai/internal/chat"
)

const systemPrompt = `
You are an OpenStack infrastructure learning and diagnostic assistant.

Your purpose is to help explain and analyze OpenStack infrastructure
problems involving services such as Nova, Neutron, Keystone, Glance,
Cinder, Placement, Octavia, and Ceph integration.

When analyzing a problem:

1. Clearly separate observed facts from hypotheses.
2. Never claim that you inspected the user's OpenStack environment.
3. Never invent lab-specific facts.
4. If evidence is insufficient, explicitly say so.
5. Explain what additional evidence would be required.
6. Prefer evidence-based technical reasoning.
7. Do not assume a hypothesis is the confirmed root cause.

At Stage 1 you have no OpenStack tools and no access to the user's
actual OpenStack environment.
`

func main() {
	codexBinary := getenv(
		"CODEX_BIN",
		"codex",
	)

	// Optional.
	//
	// Leave empty to use whatever model your current Codex
	// account/session makes available by default.
	codexModel := strings.TrimSpace(
		os.Getenv("CODEX_MODEL"),
	)

	client := ai.NewCodexClient(
		codexBinary,
		codexModel,
	)

	session := chat.NewSession(
		client,
		systemPrompt,
	)

	fmt.Println("OpenStack AI Assistant - Stage 1")
	fmt.Println()
	fmt.Println("Provider: OpenAI Codex via Codex CLI")

	if codexModel == "" {
		fmt.Println("Model: Codex account default")
	} else {
		fmt.Printf(
			"Model: %s\n",
			codexModel,
		)
	}

	fmt.Println()
	fmt.Println("Commands:")
	fmt.Println("  /reset  clear conversation history")
	fmt.Println("  /exit   quit")
	fmt.Println()

	scanner := bufio.NewScanner(os.Stdin)

	scanner.Buffer(
		make([]byte, 1024),
		1024*1024,
	)

	for {
		fmt.Print("> ")

		if !scanner.Scan() {
			break
		}

		input := strings.TrimSpace(
			scanner.Text(),
		)

		if input == "" {
			continue
		}

		switch input {

		case "/exit":
			fmt.Println("Bye.")
			return

		case "/reset":
			session.Reset()

			fmt.Println(
				"Conversation history cleared.",
			)
			fmt.Println()

			continue
		}

		ctx, cancel := context.WithTimeout(
			context.Background(),
			5*time.Minute,
		)

		response, err := session.Ask(
			ctx,
			input,
		)

		cancel()

		if err != nil {
			fmt.Printf(
				"\nError: %v\n\n",
				err,
			)

			continue
		}

		fmt.Println()
		fmt.Println(response.Text)
		fmt.Println()

		fmt.Printf(
			"[input=%d cached=%d output=%d reasoning=%d history=%d]\n\n",
			response.Usage.InputTokens,
			response.Usage.CachedInputTokens,
			response.Usage.OutputTokens,
			response.Usage.ReasoningOutputTokens,
			session.HistoryLength(),
		)
	}

	if err := scanner.Err(); err != nil {
		fmt.Fprintf(
			os.Stderr,
			"read stdin: %v\n",
			err,
		)
	}
}

func getenv(
	key string,
	fallback string,
) string {

	value := strings.TrimSpace(
		os.Getenv(key),
	)

	if value == "" {
		return fallback
	}

	return value
}
