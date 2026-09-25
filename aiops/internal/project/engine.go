package project

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"strings"
	"time"
)

type Engine struct {
	executors     map[string]Executor
	store         Store
	maxExecutions int
}

func NewEngine(store Store, maxExecutions int, executors ...Executor) (*Engine, error) {
	if maxExecutions <= 0 {
		maxExecutions = 20
	}

	engine := &Engine{
		executors:     make(map[string]Executor, len(executors)),
		store:         store,
		maxExecutions: maxExecutions,
	}

	for _, executor := range executors {
		if _, exists := engine.executors[executor.Type()]; exists {
			return nil, fmt.Errorf("duplicate executor for task type %q", executor.Type())
		}

		engine.executors[executor.Type()] = executor
	}

	return engine, nil
}

func (e *Engine) Start(ctx context.Context, goal string, tasks []Task) (State, error) {
	goal = strings.TrimSpace(goal)
	if goal == "" {
		return State{}, fmt.Errorf("project goal cannot be empty")
	}
	if err := ValidatePlan(tasks); err != nil {
		return State{}, fmt.Errorf("invalid project plan: %w", err)
	}

	id, err := newProjectID()
	if err != nil {
		return State{}, fmt.Errorf("create project ID: %w", err)
	}

	now := time.Now().UTC()
	copied := append([]Task(nil), tasks...)

	for i := range copied {
		copied[i].Status = TaskPending
	}

	state := State{
		ID:        id,
		Goal:      goal,
		Status:    StatusRunning,
		Tasks:     copied,
		Events:    []Event{},
		CreatedAt: now,
		UpdatedAt: now,
	}

	refreshTaskStatuses(&state)

	if err := e.store.Save(ctx, state); err != nil {
		return State{}, fmt.Errorf("save initial project: %w", err)
	}

	return e.run(ctx, &state)
}

func (e *Engine) Resume(ctx context.Context, id string) (State, error) {
	state, err := e.store.Load(ctx, strings.TrimSpace(id))
	if err != nil {
		return State{}, err
	}

	if state.Status == StatusCompleted {
		return state, nil
	}

	for i := range state.Tasks {
		if state.Tasks[i].Status == TaskPaused || state.Tasks[i].Status == TaskRunning {
			state.Tasks[i].Status = TaskPending
		}
	}

	state.Status = StatusRunning
	state.Error = ""
	state.UpdatedAt = time.Now().UTC()

	refreshTaskStatuses(&state)

	if err := e.store.Save(ctx, state); err != nil {
		return State{}, fmt.Errorf("save resumed project: %w", err)
	}

	return e.run(ctx, &state)
}

func (e *Engine) run(ctx context.Context, state *State) (State, error) {
	for execution := 0; execution < e.maxExecutions; execution++ {
		refreshTaskStatuses(state)

		if allTasksCompleted(*state) {
			state.Status = StatusCompleted
			state.UpdatedAt = time.Now().UTC()
			state.Events = append(state.Events, Event{
				Time:    state.UpdatedAt,
				Message: "project completed",
			})

			return *state, e.store.Save(ctx, *state)
		}

		task := firstReadyTask(state)

		if task == nil {
			if hasFailedOrBlocked(*state) {
				state.Status = StatusFailed
				state.Error = "project cannot continue because one or more tasks failed or are blocked"
				state.UpdatedAt = time.Now().UTC()
				_ = e.store.Save(ctx, *state)
				return *state, fmt.Errorf("%s", state.Error)
			}

			return e.pause(ctx, state, fmt.Errorf("no ready task available"))
		}

		executor, exists := e.executors[task.Type]
		if !exists {
			task.Status = TaskFailed
			task.Error = fmt.Sprintf("no executor registered for task type %q", task.Type)
			refreshTaskStatuses(state)
			state.Status = StatusFailed
			state.UpdatedAt = time.Now().UTC()
			_ = e.store.Save(ctx, *state)
			return *state, fmt.Errorf("task %q: %s", task.ID, task.Error)
		}

		now := time.Now().UTC()
		task.Status = TaskRunning
		task.StartedAt = &now
		task.Error = ""

		state.Events = append(state.Events, Event{
			Time:    now,
			TaskID:  task.ID,
			Message: "task started",
		})
		state.UpdatedAt = now

		if err := e.store.Save(ctx, *state); err != nil {
			return *state, fmt.Errorf("checkpoint task %q start: %w", task.ID, err)
		}

		result, err := executor.Execute(ctx, *state, *task)
		task.WorkflowID = result.WorkflowID

		if err != nil {
			if result.Paused {
				task.Status = TaskPaused
				task.Error = err.Error()
				return e.pause(ctx, state, fmt.Errorf("task %q paused: %w", task.ID, err))
			}

			finished := time.Now().UTC()
			task.Status = TaskFailed
			task.Error = err.Error()
			task.CompletedAt = &finished

			state.Events = append(state.Events, Event{
				Time:    finished,
				TaskID:  task.ID,
				Message: "task failed: " + err.Error(),
			})

			refreshTaskStatuses(state)
			state.Status = StatusFailed
			state.Error = fmt.Sprintf("task %q failed", task.ID)
			state.UpdatedAt = finished
			_ = e.store.Save(ctx, *state)

			return *state, fmt.Errorf("task %q: %w", task.ID, err)
		}

		finished := time.Now().UTC()
		task.Status = TaskCompleted
		task.Result = strings.TrimSpace(result.Output)
		task.Error = ""
		task.CompletedAt = &finished

		state.Events = append(state.Events, Event{
			Time:    finished,
			TaskID:  task.ID,
			Message: "task completed",
		})

		state.UpdatedAt = finished

		if err := e.store.Save(ctx, *state); err != nil {
			return *state, fmt.Errorf("checkpoint task %q completion: %w", task.ID, err)
		}
	}

	return e.pause(ctx, state, fmt.Errorf("project paused after %d task executions", e.maxExecutions))
}

func (e *Engine) pause(ctx context.Context, state *State, cause error) (State, error) {
	state.Status = StatusPaused
	state.Error = cause.Error()
	state.UpdatedAt = time.Now().UTC()
	_ = e.store.Save(ctx, *state)

	return *state, cause
}

func newProjectID() (string, error) {
	random := make([]byte, 4)
	if _, err := rand.Read(random); err != nil {
		return "", err
	}

	return fmt.Sprintf(
		"prj-%s-%s",
		time.Now().UTC().Format("20060102T150405Z"),
		hex.EncodeToString(random),
	), nil
}

func refreshTaskStatuses(state *State) {
	byID := make(map[string]*Task, len(state.Tasks))

	for i := range state.Tasks {
		byID[state.Tasks[i].ID] = &state.Tasks[i]
	}

	for i := range state.Tasks {
		task := &state.Tasks[i]

		switch task.Status {
		case TaskCompleted, TaskFailed, TaskRunning, TaskPaused, TaskBlocked:
			continue
		}

		allCompleted := true
		blocked := false

		for _, dependency := range task.DependsOn {
			dep := byID[dependency]

			switch dep.Status {
			case TaskFailed, TaskBlocked:
				blocked = true

			case TaskCompleted:
				// Satisfied.

			default:
				allCompleted = false
			}
		}

		switch {
		case blocked:
			task.Status = TaskBlocked
		case allCompleted:
			task.Status = TaskReady
		default:
			task.Status = TaskPending
		}
	}
}

func firstReadyTask(state *State) *Task {
	for i := range state.Tasks {
		if state.Tasks[i].Status == TaskReady {
			return &state.Tasks[i]
		}
	}

	return nil
}

func allTasksCompleted(state State) bool {
	for _, task := range state.Tasks {
		if task.Status != TaskCompleted {
			return false
		}
	}

	return true
}

func hasFailedOrBlocked(state State) bool {
	for _, task := range state.Tasks {
		if task.Status == TaskFailed || task.Status == TaskBlocked {
			return true
		}
	}

	return false
}
