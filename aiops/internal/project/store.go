package project

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

var projectIDPattern = regexp.MustCompile(`^[A-Za-z0-9._-]+$`)

type Store interface {
	Save(ctx context.Context, state State) error
	Load(ctx context.Context, id string) (State, error)
}

type FileStore struct {
	root string
}

func NewFileStore(root string) (*FileStore, error) {
	root = strings.TrimSpace(root)
	if root == "" {
		return nil, fmt.Errorf("project store root cannot be empty")
	}

	if err := os.MkdirAll(root, 0700); err != nil {
		return nil, fmt.Errorf("create project directory: %w", err)
	}

	return &FileStore{root: root}, nil
}

func (s *FileStore) Save(ctx context.Context, state State) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	if !projectIDPattern.MatchString(state.ID) {
		return fmt.Errorf("invalid project ID %q", state.ID)
	}

	return writeJSONAtomic(filepath.Join(s.root, state.ID+".json"), state)
}

func (s *FileStore) Load(ctx context.Context, id string) (State, error) {
	if err := ctx.Err(); err != nil {
		return State{}, err
	}

	id = strings.TrimSpace(id)
	if !projectIDPattern.MatchString(id) {
		return State{}, fmt.Errorf("invalid project ID %q", id)
	}

	data, err := os.ReadFile(filepath.Join(s.root, id+".json"))
	if err != nil {
		return State{}, fmt.Errorf("read project %q: %w", id, err)
	}

	var state State
	if err := json.Unmarshal(data, &state); err != nil {
		return State{}, fmt.Errorf("decode project %q: %w", id, err)
	}

	return state, nil
}

func writeJSONAtomic(path string, value any) error {
	data, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return fmt.Errorf("encode project: %w", err)
	}

	data = append(data, '\n')

	file, err := os.CreateTemp(filepath.Dir(path), ".tmp-*")
	if err != nil {
		return fmt.Errorf("create temporary project file: %w", err)
	}

	tempPath := file.Name()
	defer os.Remove(tempPath)

	if err := file.Chmod(0600); err != nil {
		file.Close()
		return fmt.Errorf("set project file permissions: %w", err)
	}
	if _, err := file.Write(data); err != nil {
		file.Close()
		return fmt.Errorf("write project file: %w", err)
	}
	if err := file.Sync(); err != nil {
		file.Close()
		return fmt.Errorf("sync project file: %w", err)
	}
	if err := file.Close(); err != nil {
		return fmt.Errorf("close project file: %w", err)
	}
	if err := os.Rename(tempPath, path); err != nil {
		return fmt.Errorf("replace project file: %w", err)
	}

	return nil
}
