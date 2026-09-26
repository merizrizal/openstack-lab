package planning

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"sync"

	"openstacklab/openstack-ai/internal/project"
)

type Prepared struct {
	goal    string
	tasks   []project.Task
	preview []byte
	digest  string
	mu      sync.Mutex
	started bool
}

func Prepare(input Request, draft Draft) (*Prepared, error) {
	req, err := normalizeRequest(input)
	if err != nil {
		return nil, err
	}
	tasks, err := validateDraft(req, draft)
	if err != nil {
		return nil, err
	}
	if draft.Disposition != Ready {
		return nil, fmt.Errorf("%w: %s", ErrNotReady, draft.Explanation)
	}

	preview, err := json.MarshalIndent(struct {
		Version      int            `json:"version"`
		Request      Request        `json:"request"`
		Proposal     Draft          `json:"proposal"`
		RuntimeTasks []project.Task `json:"runtime_tasks"`
	}{
		Version:      1,
		Request:      req,
		Proposal:     draft,
		RuntimeTasks: tasks,
	}, "", "  ")
	if err != nil {
		return nil, err
	}
	digest := sha256.Sum256(preview)
	return &Prepared{
		goal:    req.Goal,
		tasks:   tasks,
		preview: preview,
		digest:  hex.EncodeToString(digest[:]),
	}, nil
}

func (p *Prepared) Digest() string {
	return p.digest
}

func (p *Prepared) Preview() []byte {
	return append([]byte(nil), p.preview...)
}

func (p *Prepared) Start(ctx context.Context, engine ProjectStarter, approvedDigest string) (project.State, error) {
	if err := ctx.Err(); err != nil {
		return project.State{}, err
	}
	if engine == nil {
		return project.State{}, fmt.Errorf("project engine is required")
	}
	if approvedDigest != p.digest {
		return project.State{}, fmt.Errorf("approval does not match the reviewed plan")
	}
	p.mu.Lock()
	if p.started {
		p.mu.Unlock()
		return project.State{}, fmt.Errorf("this prepared plan was already started; resume its project instead")
	}
	p.started = true
	tasks := make([]project.Task, len(p.tasks))
	for i, task := range p.tasks {
		task.DependsOn = append([]string{}, task.DependsOn...)
		tasks[i] = task
	}
	p.mu.Unlock()
	return engine.Start(ctx, p.goal, tasks)
}
