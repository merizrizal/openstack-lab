package chat

import (
	"context"
	"fmt"

	"openstacklab/openstack-ai/internal/ai"
)

type Session struct {
	client ai.Client

	systemPrompt string

	// Conversation history belongs to OUR APPLICATION.
	//
	// Every Codex invocation is ephemeral, so Codex itself
	// is not being relied upon to remember previous turns.
	history []ai.Message
}

func NewSession(
	client ai.Client,
	systemPrompt string,
) *Session {

	return &Session{
		client:       client,
		systemPrompt: systemPrompt,
		history:      make([]ai.Message, 0),
	}
}

func (s *Session) Ask(
	ctx context.Context,
	input string,
) (ai.Response, error) {

	userMessage := ai.Message{
		Role:    "user",
		Content: input,
	}

	// Construct the complete logical context for THIS inference.
	messages := make(
		[]ai.Message,
		0,
		len(s.history)+2,
	)

	// Application-level behavior/instructions.
	messages = append(
		messages,
		ai.Message{
			Role:    "system",
			Content: s.systemPrompt,
		},
	)

	// Previous conversation.
	messages = append(
		messages,
		s.history...,
	)

	// Current user input.
	messages = append(
		messages,
		userMessage,
	)

	response, err := s.client.Chat(
		ctx,
		messages,
	)
	if err != nil {
		// Never commit failed model interactions to state.
		return ai.Response{}, fmt.Errorf(
			"generate assistant response: %w",
			err,
		)
	}

	// Commit conversation state only after inference succeeded.
	s.history = append(
		s.history,
		userMessage,
		ai.Message{
			Role:    "assistant",
			Content: response.Text,
		},
	)

	return response, nil
}

func (s *Session) Reset() {
	s.history = nil
}

func (s *Session) HistoryLength() int {
	return len(s.history)
}
