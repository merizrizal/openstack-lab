package chat

import (
	"context"
	"fmt"

	"openstacklab/openstack-ai/internal/ai"
)

type Session struct {
	client       ai.Client
	systemPrompt string
	history      []ai.Message
}

func NewSession(client ai.Client, systemPrompt string) *Session {
	return &Session{
		client:       client,
		systemPrompt: systemPrompt,
		history:      make([]ai.Message, 0),
	}
}

func (s *Session) Ask(ctx context.Context, input string) (ai.Response, error) {
	userMessage := ai.Message{
		Role:    "user",
		Content: input,
	}

	messages := make([]ai.Message, 0, len(s.history)+2)

	messages = append(messages, ai.Message{
		Role:    "system",
		Content: s.systemPrompt,
	})

	messages = append(messages, s.history...)

	messages = append(messages, userMessage)

	response, err := s.client.Chat(ctx, messages)
	if err != nil {
		return ai.Response{}, fmt.Errorf("generate assistant response: %w", err)
	}

	s.history = append(s.history, userMessage, ai.Message{
		Role:    "assistant",
		Content: response.Text,
	})

	return response, nil
}

func (s *Session) Reset() {
	s.history = nil
}

func (s *Session) HistoryLength() int {
	return len(s.history)
}
