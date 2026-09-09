package tools

import (
	"context"
	"encoding/json"
	"fmt"
)

type Registry struct {
	tools map[string]Tool
}

func NewRegistry(registered ...Tool) (*Registry, error) {
	registry := &Registry{
		tools: make(map[string]Tool, len(registered)),
	}

	for _, tool := range registered {
		name := tool.Name()

		if name == "" {
			return nil, fmt.Errorf("tool has empty name")
		}

		if _, exists := registry.tools[name]; exists {
			return nil, fmt.Errorf("duplicate tool %q", name)
		}

		registry.tools[name] = tool
	}

	return registry, nil
}

func (r *Registry) Execute(ctx context.Context, name string, arguments json.RawMessage) (json.RawMessage, error) {
	tool, exists := r.tools[name]

	if !exists {
		return nil, fmt.Errorf("tool %q is not registered", name)
	}

	return tool.Execute(ctx, arguments)
}
