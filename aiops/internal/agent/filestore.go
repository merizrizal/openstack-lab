package agent

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"sort"
	"strings"
)

var recordIDPattern = regexp.MustCompile(`^[A-Za-z0-9._-]+$`)

type FileStore struct {
	root string
}

func NewFileStore(root string) (*FileStore, error) {
	root = strings.TrimSpace(root)
	if root == "" {
		return nil, fmt.Errorf("store root cannot be empty")
	}

	store := &FileStore{root: root}
	if err := os.MkdirAll(store.investigationsDir(), 0700); err != nil {
		return nil, fmt.Errorf("create investigations directory: %w", err)
	}
	if err := os.MkdirAll(store.memoriesDir(), 0700); err != nil {
		return nil, fmt.Errorf("create memories directory: %w", err)
	}

	return store, nil
}

func (s *FileStore) SaveState(ctx context.Context, state State) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	if err := validateRecordID(state.ID); err != nil {
		return err
	}

	path := filepath.Join(s.investigationsDir(), state.ID+".json")
	if err := writeJSONAtomic(path, state); err != nil {
		return fmt.Errorf("save investigation %q: %w", state.ID, err)
	}

	return nil
}

func (s *FileStore) LoadState(ctx context.Context, id string) (State, error) {
	if err := ctx.Err(); err != nil {
		return State{}, err
	}

	id = strings.TrimSpace(id)
	if err := validateRecordID(id); err != nil {
		return State{}, err
	}

	data, err := os.ReadFile(filepath.Join(s.investigationsDir(), id+".json"))
	if err != nil {
		return State{}, fmt.Errorf("read investigation %q: %w", id, err)
	}

	var state State
	if err := json.Unmarshal(data, &state); err != nil {
		return State{}, fmt.Errorf("decode investigation %q: %w", id, err)
	}

	return state, nil
}

func (s *FileStore) SaveMemory(ctx context.Context, memory MemoryRecord) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	if err := validateRecordID(memory.ID); err != nil {
		return err
	}

	path := filepath.Join(s.memoriesDir(), memory.ID+".json")
	if err := writeJSONAtomic(path, memory); err != nil {
		return fmt.Errorf("save memory %q: %w", memory.ID, err)
	}

	return nil
}

func (s *FileStore) FindMemoriesBySubject(ctx context.Context, subject string, limit int) ([]MemoryRecord, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	subject = strings.TrimSpace(subject)
	if subject == "" {
		return nil, nil
	}

	entries, err := os.ReadDir(s.memoriesDir())
	if err != nil {
		return nil, fmt.Errorf("read memories directory: %w", err)
	}

	memories := make([]MemoryRecord, 0)

	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".json") {
			continue
		}

		data, err := os.ReadFile(filepath.Join(s.memoriesDir(), entry.Name()))
		if err != nil {
			return nil, fmt.Errorf("read memory %q: %w", entry.Name(), err)
		}

		var memory MemoryRecord
		if err := json.Unmarshal(data, &memory); err != nil {
			return nil, fmt.Errorf("decode memory %q: %w", entry.Name(), err)
		}

		if slices.Contains(memory.Subjects, subject) {
			memories = append(memories, memory)
		}
	}

	sort.Slice(memories, func(i, j int) bool {
		return memories[i].CreatedAt.After(memories[j].CreatedAt)
	})

	if limit > 0 && len(memories) > limit {
		memories = memories[:limit]
	}

	return memories, nil
}

func (s *FileStore) investigationsDir() string {
	return filepath.Join(s.root, "investigations")
}

func (s *FileStore) memoriesDir() string {
	return filepath.Join(s.root, "memories")
}

func validateRecordID(id string) error {
	if !recordIDPattern.MatchString(id) {
		return fmt.Errorf("invalid record ID %q", id)
	}
	return nil
}

func writeJSONAtomic(path string, value any) error {
	data, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return fmt.Errorf("encode JSON: %w", err)
	}
	data = append(data, '\n')

	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0700); err != nil {
		return fmt.Errorf("create directory: %w", err)
	}

	file, err := os.CreateTemp(dir, ".tmp-*")
	if err != nil {
		return fmt.Errorf("create temporary file: %w", err)
	}

	tempPath := file.Name()
	defer os.Remove(tempPath)

	if err := file.Chmod(0600); err != nil {
		file.Close()
		return fmt.Errorf("set temporary file permissions: %w", err)
	}
	if _, err := file.Write(data); err != nil {
		file.Close()
		return fmt.Errorf("write temporary file: %w", err)
	}
	if err := file.Sync(); err != nil {
		file.Close()
		return fmt.Errorf("sync temporary file: %w", err)
	}
	if err := file.Close(); err != nil {
		return fmt.Errorf("close temporary file: %w", err)
	}
	if err := os.Rename(tempPath, path); err != nil {
		return fmt.Errorf("replace file: %w", err)
	}

	return nil
}
