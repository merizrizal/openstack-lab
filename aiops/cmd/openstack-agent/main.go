package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"openstacklab/openstack-ai/internal/agent"
	"openstacklab/openstack-ai/internal/ai"
	"openstacklab/openstack-ai/internal/knowledge"
	"openstacklab/openstack-ai/internal/openstackclient"
	"openstacklab/openstack-ai/internal/tools"
)

func main() {
	aiClient, aiClientName, aiModel, err := newAIClient()
	if err != nil {
		fail("configure AI client: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	computeClient, err := openstackclient.NewComputeClient(ctx)
	cancel()

	if err != nil {
		fail("initialize OpenStack: %v", err)
	}

	registry, err := tools.NewRegistry(
		tools.NewGetServerTool(computeClient),
		tools.NewGetFlavorTool(computeClient),
	)
	if err != nil {
		fail("create tool registry: %v", err)
	}

	dataDir := getenv("OPENSTACK_AI_DATA_DIR", defaultDataDir())

	store, err := agent.NewFileStore(dataDir)
	if err != nil {
		fail("initialize state store: %v", err)
	}

	knowledgeDir := getenv("OPENSTACK_AI_KNOWLEDGE_DIR", "knowledge")

	chunks, err := knowledge.LoadDir(knowledgeDir, 220, 40)
	if err != nil {
		fail("load knowledge: %v", err)
	}

	retriever := knowledge.NewBM25(chunks)

	runtime := agent.NewRuntime(aiClient, registry, store, 6, 2).
		WithKnowledge(retriever, 4)

	fmt.Println("OpenStack AI Assistant - Agent Mode")
	fmt.Printf("AI client: %s\n", aiClientName)
	fmt.Printf("AI model: %s\n", aiModel)
	if strings.EqualFold(getenv("AI_CLIENT", "codex"), "pi") {
		fmt.Println("Outbound context: instructions, goals, observations, summaries, memories, and retrieved knowledge")
	}
	fmt.Printf("Data directory: %s\n", dataDir)
	fmt.Printf("Knowledge directory: %s\n", knowledgeDir)
	fmt.Printf("Knowledge chunks: %d\n", len(chunks))
	fmt.Println()
	fmt.Println("Commands:")
	fmt.Println("  <goal>               start a new investigation")
	fmt.Println("  /resume <id>         resume an investigation")
	fmt.Println("  /show <id>           show persisted state")
	fmt.Println("  /memory <server-id>  show historical memory")
	fmt.Println("  /exit                quit")
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

		switch {
		case input == "/exit":
			return

		case strings.HasPrefix(input, "/resume "):
			id := strings.TrimSpace(strings.TrimPrefix(input, "/resume "))
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
			result, err := runtime.Resume(ctx, id)
			cancel()
			printResult(result, err)

		case strings.HasPrefix(input, "/show "):
			id := strings.TrimSpace(strings.TrimPrefix(input, "/show "))
			ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			state, err := store.LoadState(ctx, id)
			cancel()

			if err != nil {
				fmt.Printf("\nError: %v\n\n", err)
				continue
			}

			printJSON(state)

		case strings.HasPrefix(input, "/memory "):
			subject := strings.ToLower(strings.TrimSpace(strings.TrimPrefix(input, "/memory ")))
			ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			memories, err := store.FindMemoriesBySubject(ctx, subject, 10)
			cancel()

			if err != nil {
				fmt.Printf("\nError: %v\n\n", err)
				continue
			}

			printJSON(memories)

		default:
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
			result, err := runtime.Start(ctx, input)
			cancel()
			printResult(result, err)
		}
	}

	if err := scanner.Err(); err != nil {
		fail("read stdin: %v", err)
	}
}

func printResult(result agent.Result, runErr error) {
	if result.InvestigationID != "" {
		fmt.Printf("\nInvestigation: %s\n", result.InvestigationID)
	}

	for _, observation := range result.Observations {
		fmt.Printf(
			"[step %d] tool=%s args=%s\n",
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

	if result.Answer != "" {
		fmt.Printf("\n%s\n", result.Answer)
	}

	fmt.Printf(
		"\n[status=%s steps=%d historical_memories=%d input=%d cached=%d output=%d reasoning=%d]\n",
		result.Status,
		result.Steps,
		result.HistoricalMemory,
		result.Usage.InputTokens,
		result.Usage.CachedInputTokens,
		result.Usage.OutputTokens,
		result.Usage.ReasoningOutputTokens,
	)

	if runErr != nil {
		fmt.Printf("\nAgent error: %v\n", runErr)
	}

	fmt.Println()
}

func printJSON(value any) {
	data, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		fmt.Printf("\nError: %v\n\n", err)
		return
	}

	fmt.Printf("\n%s\n\n", data)
}

func defaultDataDir() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return ".openstack-ai"
	}

	return filepath.Join(home, ".openstack-ai")
}

func newAIClient() (ai.StructuredClient, string, string, error) {
	clientType := strings.ToLower(getenv("AI_CLIENT", "codex"))
	switch clientType {
	case "codex":
		model := strings.TrimSpace(os.Getenv("CODEX_MODEL"))
		modelName := model
		if modelName == "" {
			modelName = "Codex account default"
		}
		client := ai.NewCodexClient(getenv("CODEX_BIN", "codex"), model)
		return client, "OpenAI Codex via Codex CLI", modelName, nil
	case "pi":
		if !strings.EqualFold(getenv("AI_PI_ALLOW_OUTBOUND", "false"), "true") {
			return nil, "", "", fmt.Errorf("Pi outbound is disabled; set AI_PI_ALLOW_OUTBOUND=true only after approving agent context transmission")
		}
		provider := strings.TrimSpace(os.Getenv("AI_MODEL_PROVIDER"))
		model := strings.TrimSpace(os.Getenv("AI_MODEL"))
		client, err := ai.NewPiClientFromEnv(piRequestAuthorizer(provider, model))
		if err != nil {
			return nil, "", "", fmt.Errorf("configure Pi client: %w", err)
		}
		return client, fmt.Sprintf("Pi CLI via %s", provider), model, nil
	default:
		return nil, "", "", fmt.Errorf("unsupported AI_CLIENT %q (supported: codex, pi)", clientType)
	}
}

func piRequestAuthorizer(provider, model string) func(context.Context, ai.PiOutbound) error {
	return func(ctx context.Context, request ai.PiOutbound) error {
		if err := ctx.Err(); err != nil {
			return err
		}
		if request.Provider != provider || request.Model != model {
			return fmt.Errorf("Pi outbound request does not match the configured provider and model")
		}
		return nil
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
