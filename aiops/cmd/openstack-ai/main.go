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
	client, providerName, modelName, err := newAIClient()
	if err != nil {
		fmt.Fprintf(os.Stderr, "configure AI client: %v\n", err)
		os.Exit(1)
	}
	session := chat.NewSession(client, systemPrompt)

	fmt.Println("OpenStack AI Assistant - Conversational Mode")
	fmt.Println()
	fmt.Printf("Provider: %s\n", providerName)
	fmt.Printf("Model: %s\n", modelName)

	fmt.Println()
	fmt.Println("Commands:")
	fmt.Println("  /reset  clear conversation history")
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

		switch input {
		case "/exit":
			fmt.Println("Bye.")
			return
		case "/reset":
			session.Reset()
			fmt.Println("Conversation history cleared.")
			fmt.Println()
			continue
		}

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
		response, err := session.Ask(ctx, input)
		cancel()

		if err != nil {
			fmt.Printf("\nError: %v\n\n", err)

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
		fmt.Fprintf(os.Stderr, "read stdin: %v\n", err)
	}
}

func newAIClient() (ai.Client, string, string, error) {
	clientType := strings.ToLower(getenv("AI_CLIENT", "codex"))
	switch clientType {
	case "codex":
		codexModel := strings.TrimSpace(os.Getenv("CODEX_MODEL"))
		modelName := codexModel
		if modelName == "" {
			modelName = "Codex account default"
		}
		return ai.NewCodexClient(getenv("CODEX_BIN", "codex"), codexModel), "OpenAI Codex via Codex CLI", modelName, nil
	case "pi":
		if !strings.EqualFold(getenv("AI_PI_ALLOW_OUTBOUND", "false"), "true") {
			return nil, "", "", fmt.Errorf("Pi outbound requests are disabled; set AI_PI_ALLOW_OUTBOUND=true only after approving transmission of the full chat context to the configured provider")
		}
		provider := strings.TrimSpace(os.Getenv("AI_MODEL_PROVIDER"))
		model := strings.TrimSpace(os.Getenv("AI_MODEL"))
		client, err := ai.NewPiClientFromEnv(func(ctx context.Context, request ai.PiOutbound) error {
			if err := ctx.Err(); err != nil {
				return err
			}
			if request.Provider != provider || request.Model != model {
				return fmt.Errorf("Pi outbound request does not match the configured provider and model")
			}
			return nil
		})
		if err != nil {
			return nil, "", "", fmt.Errorf("configure Pi client: %w", err)
		}
		return client, fmt.Sprintf("Pi CLI via %s", provider), model, nil
	default:
		return nil, "", "", fmt.Errorf("unsupported AI_CLIENT %q (supported: codex, pi)", clientType)
	}
}

func getenv(key, fallback string) string {
	value := strings.TrimSpace(os.Getenv(key))

	if value == "" {
		return fallback
	}

	return value
}
