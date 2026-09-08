package ai

import "context"

// Message represents one logical conversation message
// owned by our application.
type Message struct {
	Role    string
	Content string
}

// Usage contains token usage reported by Codex for
// the complete Codex turn.
type Usage struct {
	InputTokens           int64
	CachedInputTokens     int64
	OutputTokens          int64
	ReasoningOutputTokens int64
}

// Response is the provider-independent response our
// application cares about.
type Response struct {
	Text  string
	Usage Usage
}

// Client is our application's inference boundary.
//
// Session doesn't know whether inference happens through
// Codex, OpenAI API, another provider, or something else.
type Client interface {
	Chat(
		ctx context.Context,
		messages []Message,
	) (Response, error)
}
