package agent

import "context"

type Store interface {
	SaveState(ctx context.Context, state State) error
	LoadState(ctx context.Context, id string) (State, error)
	SaveMemory(ctx context.Context, memory MemoryRecord) error
	FindMemoriesBySubject(ctx context.Context, subject string, limit int) ([]MemoryRecord, error)
}
