package toolcall

import (
	"context"
	_ "embed"
	"encoding/json"
	"fmt"
	"strings"

	"openstacklab/openstack-ai/internal/ai"
)

//go:embed decision.schema.json
var decisionSchema []byte

const selectorPrompt = `
You are the tool-selection component of an OpenStack
diagnostic application.

You do not have direct access to OpenStack.

AVAILABLE TOOL:

get_server
- Retrieves the current Nova server state.
- Input requires an exact server UUID or server name.
- Read-only.

RULES:

1. If the user asks for current or lab-specific information
   about a Nova server and provides its exact UUID or name,
   request get_server.

2. If the question can be answered using general OpenStack
   knowledge without inspecting the lab, answer directly.

3. Never invent a server UUID or server name.

4. If lab-specific information is requested but no exact
   server UUID or name is provided, answer that more information
   is required instead of calling the tool.

5. Request at most one tool.

6. Tool execution is performed by the Go application.
`

type Selector struct {
	client ai.StructuredClient
}

func NewSelector(client ai.StructuredClient) *Selector {
	return &Selector{client: client}
}

func (s *Selector) Decide(ctx context.Context, input string) (Decision, ai.Usage, error) {
	messages := []ai.Message{
		{
			Role:    "system",
			Content: selectorPrompt,
		},
		{
			Role:    "user",
			Content: input,
		},
	}

	response, err := s.client.ChatStructured(ctx, messages, decisionSchema)
	if err != nil {
		return Decision{}, ai.Usage{}, fmt.Errorf("select tool: %w", err)
	}

	var decision Decision

	decoder := json.NewDecoder(strings.NewReader(response.Text))
	decoder.DisallowUnknownFields()

	if err := decoder.Decode(&decision); err != nil {
		return Decision{}, ai.Usage{}, fmt.Errorf("decode tool decision: %w", err)
	}

	if err := decision.Validate(); err != nil {
		return Decision{}, ai.Usage{}, fmt.Errorf("invalid tool decision: %w", err)
	}

	return decision, response.Usage, nil
}
