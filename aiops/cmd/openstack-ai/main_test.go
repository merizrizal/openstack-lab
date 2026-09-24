package main

import (
	"testing"

	"openstacklab/openstack-ai/internal/ai"
)

func TestNewAIClientDefaultsToCodex(t *testing.T) {
	t.Setenv("AI_CLIENT", "")
	t.Setenv("CODEX_BIN", "")
	t.Setenv("CODEX_MODEL", "")

	client, provider, model, err := newAIClient()
	if err != nil {
		t.Fatalf("newAIClient() error = %v", err)
	}
	if _, ok := client.(*ai.CodexClient); !ok {
		t.Fatalf("newAIClient() type = %T, want *ai.CodexClient", client)
	}
	if provider != "OpenAI Codex via Codex CLI" {
		t.Errorf("provider = %q, want Codex CLI provider", provider)
	}
	if model != "Codex account default" {
		t.Errorf("model = %q, want account default", model)
	}
}

func TestNewAIClientRequiresPiOutboundOptIn(t *testing.T) {
	t.Setenv("AI_CLIENT", "pi")
	t.Setenv("AI_PI_ALLOW_OUTBOUND", "false")

	if _, _, _, err := newAIClient(); err == nil {
		t.Fatal("newAIClient() error = nil, want outbound authorization error")
	}
}

func TestNewAIClientUsesPiWhenConfigured(t *testing.T) {
	t.Setenv("AI_CLIENT", "pi")
	t.Setenv("AI_PI_ALLOW_OUTBOUND", "true")
	t.Setenv("PI_BIN", "")
	t.Setenv("AI_MODEL_PROVIDER", "test-provider")
	t.Setenv("AI_MODEL", "test-model")
	t.Setenv("PI_CODING_AGENT_DIR", t.TempDir())
	t.Setenv("AI_PI_VERSION", "test-version")

	client, provider, model, err := newAIClient()
	if err != nil {
		t.Fatalf("newAIClient() error = %v", err)
	}
	if _, ok := client.(*ai.PiClient); !ok {
		t.Fatalf("newAIClient() type = %T, want *ai.PiClient", client)
	}
	if provider != "Pi CLI via test-provider" {
		t.Errorf("provider = %q, want Pi provider", provider)
	}
	if model != "test-model" {
		t.Errorf("model = %q, want test-model", model)
	}
}

func TestNewAIClientRejectsUnknownClient(t *testing.T) {
	t.Setenv("AI_CLIENT", "unknown")

	if _, _, _, err := newAIClient(); err == nil {
		t.Fatal("newAIClient() error = nil, want unsupported client error")
	}
}
