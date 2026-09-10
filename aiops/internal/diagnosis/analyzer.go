package diagnosis

import (
	"context"
	_ "embed"
	"encoding/json"
	"fmt"
	"strings"

	"openstacklab/openstack-ai/internal/ai"
)

//go:embed analysis.schema.json
var analysisSchema []byte

const systemPrompt = `
You are an OpenStack diagnostic analysis component.

Analyze only the evidence supplied by the application.

Important rules:

1. Never invent lab-specific facts.
2. observed_facts must contain only facts explicitly supported
   by the supplied evidence.
3. hypotheses must be clearly distinguished from observed facts.
4. Use "insufficient_evidence" when the supplied evidence does
   not support a meaningful hypothesis.
5. Use "hypothesis_available" when one or more plausible causes
   can be identified but are not proven.
6. Use "root_cause_confirmed" only when the supplied evidence
   directly establishes the cause.
7. Missing evidence should describe information that would help
   confirm or reject hypotheses.
8. Do not claim to have queried or inspected OpenStack.
`

type Analyzer struct {
	client ai.StructuredClient
}

func NewAnalyzer(client ai.StructuredClient) *Analyzer {
	return &Analyzer{
		client: client,
	}
}

func (a *Analyzer) Analyze(ctx context.Context, evidence string) (IncidentAnalysis, ai.Usage, error) {
	evidence = strings.TrimSpace(evidence)

	if evidence == "" {
		return IncidentAnalysis{}, ai.Usage{}, fmt.Errorf("evidence cannot be empty")
	}

	messages := []ai.Message{
		{
			Role:    "system",
			Content: systemPrompt,
		},
		{
			Role: "user",
			Content: `
Analyze the following OpenStack incident evidence.

Do not assume any information that is not present.

EVIDENCE:

` + evidence,
		},
	}

	response, err := a.client.ChatStructured(ctx, messages, analysisSchema)
	if err != nil {
		return IncidentAnalysis{}, ai.Usage{}, fmt.Errorf("structured inference failed: %w", err)
	}

	var result IncidentAnalysis

	decoder := json.NewDecoder(strings.NewReader(response.Text))
	decoder.DisallowUnknownFields()

	if err := decoder.Decode(&result); err != nil {
		return IncidentAnalysis{}, ai.Usage{}, fmt.Errorf("decode structured AI response: %w", err)
	}

	if err := result.Validate(); err != nil {
		return IncidentAnalysis{}, ai.Usage{}, fmt.Errorf("validate structured AI response: %w", err)
	}

	return result, response.Usage, nil
}
