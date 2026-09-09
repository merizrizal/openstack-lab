package tools

import (
	"context"
	"encoding/json"
)

type Tool interface {
	Name() string
	Description() string
	Execute(ctx context.Context, arguments json.RawMessage) (json.RawMessage, error)
}
