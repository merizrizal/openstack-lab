package knowledge

import "context"

type Chunk struct {
	ID      string `json:"id"`
	Source  string `json:"source"`
	Section string `json:"section"`
	Text    string `json:"text"`
}

type Result struct {
	ID      string  `json:"id"`
	Source  string  `json:"source"`
	Section string  `json:"section"`
	Text    string  `json:"text"`
	Score   float64 `json:"score"`
}

type Retriever interface {
	Search(ctx context.Context, query string, limit int) ([]Result, error)
}
