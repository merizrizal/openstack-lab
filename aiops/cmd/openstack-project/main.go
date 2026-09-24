package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"openstacklab/openstack-ai/internal/agent"
	"openstacklab/openstack-ai/internal/ai"
	"openstacklab/openstack-ai/internal/knowledge"
	"openstacklab/openstack-ai/internal/openstackclient"
	"openstacklab/openstack-ai/internal/project"
	"openstacklab/openstack-ai/internal/tools"
	"openstacklab/openstack-ai/internal/workflow"
)

var serverIdPattern = regexp.MustCompile(`[a-z0-9]+[_-].[a-z0-9]+`)

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

	workflowEngine, err := workflow.NewEngine(
		workflowStore,
		20,
		workflow.ServerIncidentSteps(registry, classifier, agentRuntime)...,
	)
	if err != nil {
		fail("initialize workflow engine: %v", err)
	}

	projectStore, err := project.NewFileStore(filepath.Join(dataDir, "projects"))
	if err != nil {
		fail("initialize project store: %v", err)
	}

	projectEngine, err := project.NewEngine(
		projectStore,
		20,
		project.NewWorkflowExecutor(workflowEngine),
		project.NewSummaryExecutor(aiClient),
	)
	if err != nil {
		fail("initialize project engine: %v", err)
	}

	runCLI(projectEngine, projectStore)
}

func runCLI(engine *project.Engine, store *project.FileStore) {
	fmt.Println("OpenStack AI Assistant - Project Mode")
	fmt.Println()
	fmt.Println("Enter a project goal containing one or more server UUIDs.")
	fmt.Println()
	fmt.Println("Commands:")
	fmt.Println("  /resume <id>   resume project")
	fmt.Println("  /show <id>     show project state")
	fmt.Println("  /exit          quit")
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
			runProject(engine.Resume, id)

		case strings.HasPrefix(input, "/show "):
			id := strings.TrimSpace(strings.TrimPrefix(input, "/show "))
			ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			state, err := store.Load(ctx, id)
			cancel()

			if err != nil {
				fmt.Printf("\nError: %v\n\n", err)
				continue
			}

			printJSON(state)

		default:
			tasks, err := buildTasks(input)
			if err != nil {
				fmt.Printf("\nError: %v\n\n", err)
				continue
			}

			ctx, cancel := context.WithTimeout(context.Background(), 30*time.Minute)
			state, err := engine.Start(ctx, input, tasks)
			cancel()
			printProject(state, err)
		}
	}

	if err := scanner.Err(); err != nil {
		fail("read stdin: %v", err)
	}
}

func buildTasks(goal string) ([]project.Task, error) {
	serverIDs := serverIdPattern.FindAllString(goal, -1)
	if len(serverIDs) == 0 {
		return nil, fmt.Errorf("project goal must contain at least one server UUID")
	}

	tasks := make([]project.Task, 0, len(serverIDs)+1)
	dependencies := make([]string, 0, len(serverIDs))

	for i, serverID := range serverIDs {
		taskID := fmt.Sprintf("investigate-server-%d", i+1)

		tasks = append(tasks, project.Task{
			ID:        taskID,
			Type:      project.TaskTypeServerIncident,
			Goal:      fmt.Sprintf("Investigate the current problem for server %s.", strings.ToLower(serverID)),
			DependsOn: []string{},
		})

		dependencies = append(dependencies, taskID)
	}

	tasks = append(tasks, project.Task{
		ID:        "project-summary",
		Type:      project.TaskTypeProjectSummary,
		Goal:      "Produce the final project assessment.",
		DependsOn: dependencies,
	})

	return tasks, nil
}

func runProject(run func(context.Context, string) (project.State, error), value string) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Minute)
	state, err := run(ctx, value)
	cancel()

	printProject(state, err)
}

func printProject(state project.State, runErr error) {
	fmt.Printf("\nProject: %s\n", state.ID)

	for _, task := range state.Tasks {
		fmt.Printf(
			"%s type=%s status=%s workflow=%s\n",
			task.ID,
			task.Type,
			task.Status,
			task.WorkflowID,
		)
	}

	fmt.Printf("\nstatus=%s\n", state.Status)

	if runErr != nil {
		fmt.Printf("error=%v\n", runErr)
	}

	if len(state.Tasks) > 0 {
		for _, task := range state.Tasks {
			if task.Type == project.TaskTypeProjectSummary && task.Result != "" {
				fmt.Printf("\nPROJECT SUMMARY\n\n%s\n", task.Result)
			}
		}
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
