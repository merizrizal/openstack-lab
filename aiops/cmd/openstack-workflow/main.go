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
	fmt.Printf("Knowledge chunks: %d\n", len(chunks))
	fmt.Println()
	fmt.Println("Commands:")
	fmt.Println("  <goal>          start workflow")
	fmt.Println("  /resume <id>    resume workflow")
	fmt.Println("  /show <id>      show workflow state")
	fmt.Println("  /exit           quit")
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
