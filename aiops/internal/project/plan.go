package project

import (
	"fmt"
	"strings"
)

func ValidatePlan(tasks []Task) error {
	if len(tasks) == 0 {
		return fmt.Errorf("project must contain at least one task")
	}

	byID := make(map[string]Task, len(tasks))

	for _, task := range tasks {
		if strings.TrimSpace(task.ID) == "" {
			return fmt.Errorf("task ID cannot be empty")
		}
		if strings.TrimSpace(task.Type) == "" {
			return fmt.Errorf("task %q has no type", task.ID)
		}
		if _, exists := byID[task.ID]; exists {
			return fmt.Errorf("duplicate task ID %q", task.ID)
		}

		byID[task.ID] = task
	}

	for _, task := range tasks {
		for _, dependency := range task.DependsOn {
			if dependency == task.ID {
				return fmt.Errorf("task %q depends on itself", task.ID)
			}
			if _, exists := byID[dependency]; !exists {
				return fmt.Errorf("task %q depends on unknown task %q", task.ID, dependency)
			}
		}
	}

	visiting := make(map[string]bool)
	visited := make(map[string]bool)

	var visit func(string) error

	visit = func(id string) error {
		if visiting[id] {
			return fmt.Errorf("dependency cycle detected at task %q", id)
		}
		if visited[id] {
			return nil
		}

		visiting[id] = true

		for _, dependency := range byID[id].DependsOn {
			if err := visit(dependency); err != nil {
				return err
			}
		}

		visiting[id] = false
		visited[id] = true
		return nil
	}

	for id := range byID {
		if err := visit(id); err != nil {
			return err
		}
	}

	return nil
}
