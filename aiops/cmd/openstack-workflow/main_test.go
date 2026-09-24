package main

import (
	"context"
	"errors"
	"testing"

	"openstacklab/openstack-ai/internal/ai"
)

func TestNewAIClientDefaultsToCodex(t *testing.T) {
	t.Setenv("AI_CLIENT", "")
	t.Setenv("CODEX_BIN", "")
	t.Setenv("CODEX_MODEL", "")

	client, name, model, err := newAIClient()
	if err != nil {
		t.Fatalf("newAIClient() error = %v", err)
	}
	if _, ok := client.(*ai.CodexClient); !ok {
		t.Fatalf("newAIClient() type = %T, want *ai.CodexClient", client)
	}
	if name != "OpenAI Codex via Codex CLI" {
		t.Errorf("client name = %q, want Codex CLI", name)
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

	client, name, model, err := newAIClient()
	if err != nil {
		t.Fatalf("newAIClient() error = %v", err)
	}
	if _, ok := client.(*ai.PiClient); !ok {
		t.Fatalf("newAIClient() type = %T, want *ai.PiClient", client)
	}
	if name != "Pi CLI via test-provider" {
		t.Errorf("client name = %q, want Pi provider", name)
	}
	if model != "test-model" {
		t.Errorf("model = %q, want test-model", model)
	}
}

func TestPiRequestAuthorizerRestrictsConfiguredTarget(t *testing.T) {
	authorize := piRequestAuthorizer("test-provider", "test-model")
	request := ai.PiOutbound{Provider: "test-provider", Model: "test-model"}

	if err := authorize(context.Background(), request); err != nil {
		t.Fatalf("authorize configured target: %v", err)
	}

	request.Model = "other-model"
	if err := authorize(context.Background(), request); err == nil {
		t.Fatal("authorize mismatched model: error = nil, want rejection")
	}

	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if err := authorize(ctx, ai.PiOutbound{Provider: "test-provider", Model: "test-model"}); !errors.Is(err, context.Canceled) {
		t.Fatalf("authorize canceled request error = %v, want context.Canceled", err)
	}
}

func TestNewAIClientRejectsUnknownClient(t *testing.T) {
	t.Setenv("AI_CLIENT", "unknown")

	if _, _, _, err := newAIClient(); err == nil {
		t.Fatal("newAIClient() error = nil, want unsupported client error")
	}
}
