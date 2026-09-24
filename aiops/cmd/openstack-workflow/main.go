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
	"openstacklab/openstack-ai/internal/workflow"
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
	knowledgeDir := getenv("OPENSTACK_AI_KNOWLEDGE_DIR", "knowledge")

	agentStore, err := agent.NewFileStore(dataDir)
	if err != nil {
		fail("initialize agent store: %v", err)
	}

	chunks, err := knowledge.LoadDir(knowledgeDir, 220, 40)
	if err != nil {
		fail("load knowledge: %v", err)
	}

	retriever := knowledge.NewBM25(chunks)

	agentRuntime := agent.NewRuntime(aiClient, registry, agentStore, 6, 2).
		WithKnowledge(retriever, 4)

	classifier := workflow.NewClassifier(aiClient)

	workflowStore, err := workflow.NewFileStore(filepath.Join(dataDir, "workflows"))
	if err != nil {
		fail("initialize workflow store: %v", err)
	}

	engine, err := workflow.NewEngine(
		workflowStore,
		20,
		workflow.ServerIncidentSteps(registry, classifier, agentRuntime)...,
	)
	if err != nil {
		fail("initialize workflow engine: %v", err)
	}

	fmt.Println("OpenStack AI Assistant - Workflow Mode")
	fmt.Printf("AI client: %s\n", aiClientName)
	fmt.Printf("AI model: %s\n", aiModel)
	if strings.EqualFold(getenv("AI_CLIENT", "codex"), "pi") {
		fmt.Println("Outbound context: instructions, goals, observations, summaries, memories, and retrieved knowledge")
	}
	fmt.Printf("Knowledge chunks: %d\n", len(chunks))
	fmt.Println()
	fmt.Println("Commands:")
	fmt.Println("  <goal>          start workflow")
	fmt.Println("  /resume <id>    resume workflow")
	fmt.Println("  /show <id>      show workflow state")
	fmt.Println("  /exit           quit")
	fmt.Println("Use one canonical server UUID or server_identifier=<exact name>.")
	fmt.Println("Quote server names containing spaces or punctuation.")
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
			runWorkflow(engine.Resume, id)

		case strings.HasPrefix(input, "/show "):
			id := strings.TrimSpace(strings.TrimPrefix(input, "/show "))
			ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			state, err := workflowStore.Load(ctx, id)
			cancel()

			if err != nil {
				fmt.Printf("\nError: %v\n\n", err)
				continue
			}

			printJSON(state)

		default:
			runWorkflow(engine.Start, input)
		}
	}

	if err := scanner.Err(); err != nil {
		fail("read stdin: %v", err)
	}
}

type cliAIClient interface {
	ai.Client
	ai.StructuredClient
}

func newAIClient() (cliAIClient, string, string, error) {
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

func runWorkflow(run func(context.Context, string) (workflow.State, error), value string) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	state, err := run(ctx, value)
	cancel()

	fmt.Printf("\nWorkflow: %s\n", state.ID)

	for _, transition := range state.History {
		fmt.Printf("%s -> %s", transition.From, transition.To)
		if transition.Error != "" {
			fmt.Printf(" error=%q", transition.Error)
		}
		fmt.Println()
	}

	if state.FinalReport != "" {
		fmt.Printf("\n%s\n", state.FinalReport)
	}

	fmt.Printf("\nstatus=%s current_step=%s\n", state.Status, state.CurrentStep)

	if err != nil {
		fmt.Printf("error=%v\n", err)
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
