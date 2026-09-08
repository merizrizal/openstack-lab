package ai

import "context"

type Message struct {
	Role    string
	Content string
}

type Usage struct {
	InputTokens           int64
	CachedInputTokens     int64
	OutputTokens          int64
	ReasoningOutputTokens int64
}

type Response struct {
	Text  string
	Usage Usage
}

type Client interface {
	Chat(
		ctx context.Context,
		messages []Message,
	) (Response, error)
}

type StructuredClient interface {
	ChatStructured(
		ctx context.Context,
		messages []Message,
		schema []byte,
	) (Response, error)
}
