package ai

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math/big"
	"reflect"
	"strconv"
	"strings"
	"unicode/utf8"
)

type piSchema struct {
	kind       string
	properties map[string]*piSchema
	required   []string
	additional bool
	items      *piSchema
	enum       []any
}

func piCompileSchema(data []byte) (*piSchema, error) {
	if len(data) == 0 || len(data) > 64*1024 {
		return nil, errors.New("schema must be nonempty and at most 64 KiB")
	}
	value, err := piDecodeJSON(data)
	if err != nil {
		return nil, errors.New("schema is not strict JSON")
	}
	return piSchemaNode(value)
}

func piSchemaNode(value any) (*piSchema, error) {
	object, ok := value.(map[string]any)
	if !ok {
		return nil, errors.New("this schema subset requires object-form schemas")
	}
	for key := range object {
		switch key {
		case "$schema", "title", "description", "type", "properties", "required", "additionalProperties", "items", "enum":
		default:
			return nil, fmt.Errorf("unsupported schema keyword %q; use a reviewed full validator to extend the subset", key)
		}
	}
	for _, key := range []string{"$schema", "title", "description"} {
		if value, exists := object[key]; exists {
			text, ok := value.(string)
			if !ok {
				return nil, fmt.Errorf("schema annotation %q must be a string", key)
			}
			if key == "$schema" && text != "https://json-schema.org/draft/2020-12/schema" {
				return nil, errors.New("only the draft 2020-12 identifier is supported")
			}
		}
	}
	kind, ok := object["type"].(string)
	if !ok {
		return nil, errors.New("every schema node must declare one string type")
	}
	node := &piSchema{kind: kind, additional: true, properties: make(map[string]*piSchema)}
	switch kind {
	case "object", "array", "string", "integer", "number", "boolean", "null":
	default:
		return nil, fmt.Errorf("unsupported schema type %q", kind)
	}
	if value, exists := object["properties"]; exists {
		properties, ok := value.(map[string]any)
		if !ok || kind != "object" {
			return nil, errors.New("properties requires an object schema and object value")
		}
		for name, value := range properties {
			child, err := piSchemaNode(value)
			if err != nil {
				return nil, fmt.Errorf("property %q: %w", name, err)
			}
			node.properties[name] = child
		}
	}
	if value, exists := object["required"]; exists {
		required, ok := value.([]any)
		if !ok || kind != "object" {
			return nil, errors.New("required must be an array in an object schema")
		}
		seen := make(map[string]bool)
		for _, value := range required {
			name, ok := value.(string)
			if !ok || seen[name] || node.properties[name] == nil {
				return nil, errors.New("required names must be unique, strings, and declared in properties")
			}
			seen[name] = true
			node.required = append(node.required, name)
		}
	}
	if value, exists := object["additionalProperties"]; exists {
		additional, ok := value.(bool)
		if !ok || kind != "object" {
			return nil, errors.New("additionalProperties must be a bool in an object schema")
		}
		node.additional = additional
	}
	if value, exists := object["items"]; exists {
		if kind != "array" {
			return nil, errors.New("items requires an array schema")
		}
		child, err := piSchemaNode(value)
		if err != nil {
			return nil, fmt.Errorf("items: %w", err)
		}
		node.items = child
	}
	if value, exists := object["enum"]; exists {
		values, ok := value.([]any)
		if !ok || len(values) == 0 {
			return nil, errors.New("enum must be a nonempty array")
		}
		node.enum = values
	}
	return node, nil
}

func (s *piSchema) validate(value any) error {
	if len(s.enum) > 0 {
		matched := false
		for _, choice := range s.enum {
			matched = matched || piJSONEqual(value, choice)
		}
		if !matched {
			return errors.New("enum mismatch")
		}
	}
	switch s.kind {
	case "object":
		object, ok := value.(map[string]any)
		if !ok {
			return errors.New("expected object")
		}
		for _, key := range s.required {
			if _, exists := object[key]; !exists {
				return errors.New("missing required property")
			}
		}
		for key, value := range object {
			child, exists := s.properties[key]
			if !exists && !s.additional {
				return errors.New("unknown property")
			}
			if exists {
				if err := child.validate(value); err != nil {
					return err
				}
			}
		}
	case "array":
		array, ok := value.([]any)
		if !ok {
			return errors.New("expected array")
		}
		if s.items != nil {
			for _, item := range array {
				if err := s.items.validate(item); err != nil {
					return err
				}
			}
		}
	case "string":
		if _, ok := value.(string); !ok {
			return errors.New("expected string")
		}
	case "boolean":
		if _, ok := value.(bool); !ok {
			return errors.New("expected boolean")
		}
	case "null":
		if value != nil {
			return errors.New("expected null")
		}
	case "number", "integer":
		number, ok := value.(json.Number)
		if !ok {
			return errors.New("expected number")
		}
		rat, ok := new(big.Rat).SetString(string(number))
		if !ok || (s.kind == "integer" && !rat.IsInt()) {
			return errors.New("invalid numeric type")
		}
	}
	return nil
}

func piJSONEqual(a, b any) bool {
	if an, ok := a.(json.Number); ok {
		bn, ok := b.(json.Number)
		if !ok {
			return false
		}
		ar, aok := new(big.Rat).SetString(string(an))
		br, bok := new(big.Rat).SetString(string(bn))
		return aok && bok && ar.Cmp(br) == 0
	}

	switch av := a.(type) {
	case []any:
		bv, ok := b.([]any)
		if !ok || len(av) != len(bv) {
			return false
		}
		for i := range av {
			if !piJSONEqual(av[i], bv[i]) {
				return false
			}
		}
		return true
	case map[string]any:
		bv, ok := b.(map[string]any)
		if !ok || len(av) != len(bv) {
			return false
		}
		for key, item := range av {
			other, exists := bv[key]
			if !exists || !piJSONEqual(item, other) {
				return false
			}
		}
		return true
	default:
		return reflect.DeepEqual(a, b)
	}
}

func piDecodeJSON(data []byte) (any, error) {
	if len(data) > 1<<20 || !utf8.Valid(data) {
		return nil, errors.New("JSON exceeds byte budget or is not UTF-8")
	}
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.UseNumber()
	value, err := piJSONValue(decoder, 0)
	if err != nil {
		return nil, err
	}
	if _, err := decoder.Token(); err != io.EOF {
		return nil, errors.New("trailing content after JSON")
	}
	return value, nil
}

func piJSONValue(decoder *json.Decoder, depth int) (any, error) {
	if depth > 64 {
		return nil, errors.New("JSON nesting exceeds limit")
	}
	token, err := decoder.Token()
	if err != nil {
		return nil, err
	}
	delimiter, isDelimiter := token.(json.Delim)
	if !isDelimiter {
		if number, ok := token.(json.Number); ok {
			if len(number) > 64 {
				return nil, errors.New("JSON number exceeds length limit")
			}
			if position := strings.IndexAny(string(number), "eE"); position >= 0 {
				exponent, err := strconv.Atoi(string(number)[position+1:])
				if err != nil || exponent < -1000 || exponent > 1000 {
					return nil, errors.New("JSON exponent exceeds numeric budget")
				}
			}
		}
		return token, nil
	}
	switch delimiter {
	case '{':
		object := make(map[string]any)
		for decoder.More() {
			keyToken, err := decoder.Token()
			if err != nil {
				return nil, err
			}
			key, ok := keyToken.(string)
			if !ok {
				return nil, errors.New("object key is not a string")
			}
			if _, exists := object[key]; exists {
				return nil, errors.New("duplicate JSON property")
			}
			value, err := piJSONValue(decoder, depth+1)
			if err != nil {
				return nil, err
			}
			object[key] = value
		}
		if end, err := decoder.Token(); err != nil || end != json.Delim('}') {
			return nil, errors.New("unterminated object")
		}
		return object, nil
	case '[':
		array := []any{}
		for decoder.More() {
			value, err := piJSONValue(decoder, depth+1)
			if err != nil {
				return nil, err
			}
			array = append(array, value)
		}
		if end, err := decoder.Token(); err != nil || end != json.Delim(']') {
			return nil, errors.New("unterminated array")
		}
		return array, nil
	default:
		return nil, errors.New("unexpected JSON delimiter")
	}
}
