package planning

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"io"
	"strings"
	"time"

	"openstacklab/openstack-ai/internal/project"
)

var ErrNotApproved = errors.New("plan was not approved; no project was started")

func (p *Planner) ReviewAndStart(ctx context.Context, engine ProjectStarter, req Request, scanner *bufio.Scanner, out io.Writer) (project.State, error) {
	if scanner == nil || out == nil {
		return project.State{}, fmt.Errorf("review input and output are required")
	}
	planCtx, cancel := context.WithTimeout(ctx, 2*time.Minute)
	draft, usage, err := p.Propose(planCtx, req)
	cancel()
	if err != nil {
		return project.State{}, err
	}
	if draft.Disposition != Ready {
		return project.State{}, fmt.Errorf("%w: %s: %q", ErrNotReady, draft.Disposition, draft.Explanation)
	}
	prepared, err := Prepare(req, draft)
	if err != nil {
		return project.State{}, err
	}
	approval := "approve " + prepared.Digest()
	if _, err := fmt.Fprintf(out, "\nREVIEW ONLY; no project started.\n%s\n\nPlanning tokens: input=%d output=%d\n\nTo execute this exact plan, type:\n%s\nAnything else cancels.\n> ", prepared.Preview(), usage.InputTokens, usage.OutputTokens, approval); err != nil {
		return project.State{}, fmt.Errorf("show plan: %w", err)
	}
	if !scanner.Scan() {
		if err := scanner.Err(); err != nil {
			return project.State{}, err
		}
		return project.State{}, ErrNotApproved
	}
	if strings.TrimSpace(scanner.Text()) != approval {
		return project.State{}, ErrNotApproved
	}
	return prepared.Start(ctx, engine, prepared.Digest())
}
