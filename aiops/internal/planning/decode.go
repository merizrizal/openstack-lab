package planning

import (
	"encoding/json"
	"fmt"
	"io"
	"strings"
	"unicode/utf8"
)

func DecodeDraft(text string) (Draft, error) {
	if len(text) == 0 || len(text) > MaxPlanBytes || !utf8.ValidString(text) {
		return Draft{}, fmt.Errorf("plan JSON must contain 1..%d valid UTF-8 bytes", MaxPlanBytes)
	}
	scan := json.NewDecoder(strings.NewReader(text))
	scan.UseNumber()
	if err := rejectDuplicateKeys(scan, 0); err != nil {
		return Draft{}, err
	}
	if _, err := scan.Token(); err != io.EOF {
		return Draft{}, fmt.Errorf("plan must contain exactly one JSON value")
	}

	var root map[string]json.RawMessage
	if err := json.Unmarshal([]byte(text), &root); err != nil {
		return Draft{}, fmt.Errorf("decode plan object: %w", err)
	}
	if err := exactKeys(root, "disposition", "explanation", "tasks"); err != nil {
		return Draft{}, err
	}
	var rawTasks []map[string]json.RawMessage
	if err := json.Unmarshal(root["tasks"], &rawTasks); err != nil {
		return Draft{}, fmt.Errorf("decode tasks: %w", err)
	}
	for _, task := range rawTasks {
		if err := exactKeys(task, "id", "type", "server_identifier", "focus", "depends_on"); err != nil {
			return Draft{}, err
		}
	}

	var draft Draft
	decoder := json.NewDecoder(strings.NewReader(text))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&draft); err != nil {
		return Draft{}, fmt.Errorf("decode plan: %w", err)
	}
	return draft, nil
}

func exactKeys(object map[string]json.RawMessage, keys ...string) error {
	if len(object) != len(keys) {
		return fmt.Errorf("JSON object has missing or unexpected fields")
	}
	for _, key := range keys {
		raw, exists := object[key]
		if !exists || strings.TrimSpace(string(raw)) == "null" {
			return fmt.Errorf("missing or null field %q", key)
		}
	}
	return nil
}

func rejectDuplicateKeys(decoder *json.Decoder, depth int) error {
	if depth > 16 {
		return fmt.Errorf("plan JSON nesting is too deep")
	}
	token, err := decoder.Token()
	if err != nil {
		return fmt.Errorf("read plan JSON: %w", err)
	}
	delimiter, container := token.(json.Delim)
	if !container {
		return nil
	}
	switch delimiter {
	case '{':
		seen := make(map[string]bool)
		for decoder.More() {
			key, err := decoder.Token()
			if err != nil {
				return err
			}
			name, ok := key.(string)
			if !ok || seen[name] {
				return fmt.Errorf("duplicate or invalid JSON object key")
			}
			seen[name] = true
			if err := rejectDuplicateKeys(decoder, depth+1); err != nil {
				return err
			}
		}
		end, err := decoder.Token()
		if err != nil || end != json.Delim('}') {
			return fmt.Errorf("invalid JSON object ending")
		}
	case '[':
		for decoder.More() {
			if err := rejectDuplicateKeys(decoder, depth+1); err != nil {
				return err
			}
		}
		end, err := decoder.Token()
		if err != nil || end != json.Delim(']') {
			return fmt.Errorf("invalid JSON array ending")
		}
	default:
		return fmt.Errorf("unexpected JSON delimiter")
	}
	return nil
}
