package workflow

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"strings"
	"time"
)

type Engine struct {
	steps          map[StepName]Step
	store          Store
	maxTransitions int
}

func NewEngine(store Store, maxTransitions int, steps ...Step) (*Engine, error) {
	if maxTransitions <= 0 {
		maxTransitions = 20
	}

	engine := &Engine{
		steps:          make(map[StepName]Step, len(steps)),
		store:          store,
		maxTransitions: maxTransitions,
	}

	for _, step := range steps {
		if _, exists := engine.steps[step.Name()]; exists {
			return nil, fmt.Errorf("duplicate workflow step %q", step.Name())
		}

		engine.steps[step.Name()] = step
	}

	return engine, nil
}

func (e *Engine) Start(ctx context.Context, goal string) (State, error) {
	goal = strings.TrimSpace(goal)
	if goal == "" {
		return State{}, fmt.Errorf("goal cannot be empty")
	}

	id, err := newWorkflowID()
	if err != nil {
		return State{}, fmt.Errorf("create workflow ID: %w", err)
	}

	now := time.Now().UTC()

	state := State{
		ID:          id,
		Goal:        goal,
		Status:      StatusRunning,
		CurrentStep: StepValidateInput,
		History:     []Transition{},
		CreatedAt:   now,
		UpdatedAt:   now,
	}

	if err := e.store.Save(ctx, state); err != nil {
		return State{}, fmt.Errorf("save initial workflow: %w", err)
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

	state.Status = StatusRunning
	state.Error = ""
	state.UpdatedAt = time.Now().UTC()

	if err := e.store.Save(ctx, state); err != nil {
		return State{}, fmt.Errorf("save resumed workflow: %w", err)
	}

	return e.run(ctx, &state)
}

func (e *Engine) run(ctx context.Context, state *State) (State, error) {
	for i := 0; i < e.maxTransitions; i++ {
		if state.CurrentStep == StepDone {
			state.Status = StatusCompleted
			state.UpdatedAt = time.Now().UTC()
			return *state, e.store.Save(ctx, *state)
		}

		step, exists := e.steps[state.CurrentStep]
		if !exists {
			return e.pause(ctx, state, fmt.Errorf("workflow step %q is not registered", state.CurrentStep))
		}

		current := state.CurrentStep
		started := time.Now().UTC()

		next, err := step.Run(ctx, state)

		transition := Transition{
			From:        current,
			To:          next,
			StartedAt:   started,
			CompletedAt: time.Now().UTC(),
		}

		if err != nil {
			transition.Error = err.Error()
			state.History = append(state.History, transition)
			return e.pause(ctx, state, fmt.Errorf("workflow step %q: %w", current, err))
		}

		state.History = append(state.History, transition)
		state.CurrentStep = next
		state.UpdatedAt = time.Now().UTC()

		if next == StepDone {
			state.Status = StatusCompleted
		}

		if err := e.store.Save(ctx, *state); err != nil {
			return *state, fmt.Errorf("checkpoint workflow after %q: %w", current, err)
		}

		if state.Status == StatusCompleted {
			return *state, nil
		}
	}

	return e.pause(ctx, state, fmt.Errorf("workflow exceeded %d transitions", e.maxTransitions))
}

func (e *Engine) pause(ctx context.Context, state *State, cause error) (State, error) {
	state.Status = StatusPaused
	state.Error = cause.Error()
	state.UpdatedAt = time.Now().UTC()
	_ = e.store.Save(ctx, *state)
	return *state, cause
}

func newWorkflowID() (string, error) {
	random := make([]byte, 4)
	if _, err := rand.Read(random); err != nil {
		return "", err
	}

	return fmt.Sprintf(
		"wf-%s-%s",
		time.Now().UTC().Format("20060102T150405Z"),
		hex.EncodeToString(random),
	), nil
}
