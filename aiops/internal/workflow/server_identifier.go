package workflow

import (
	"regexp"
	"sort"
	"strconv"
	"strings"
)

const serverUUIDPatternText = `[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`

var (
	serverUUIDPattern          = regexp.MustCompile(`(?i)` + serverUUIDPatternText)
	canonicalServerUUIDPattern = regexp.MustCompile(`(?i)^` + serverUUIDPatternText + `$`)
	serverIdentifierAssignment = regexp.MustCompile(`(?i)\bserver_identifier\s*=`)
)

type locatedServerIdentifier struct {
	index int
	value string
}

func ExtractServerIdentifiers(text string) []string {
	located := make([]locatedServerIdentifier, 0)

	for _, bounds := range serverUUIDPattern.FindAllStringIndex(text, -1) {
		start, end := bounds[0], bounds[1]
		if (start > 0 && isUUIDAdjacentCharacter(text[start-1])) ||
			(end < len(text) && isUUIDAdjacentCharacter(text[end])) {
			continue
		}
		located = append(located, locatedServerIdentifier{
			index: start,
			value: strings.ToLower(text[start:end]),
		})
	}

	located = append(located, serverIdentifierAssignments(text)...)
	return uniqueServerIdentifiers(located)
}

func markedServerIdentifiers(text string) []string {
	return uniqueServerIdentifiers(serverIdentifierAssignments(text))
}

func serverIdentifierAssignments(text string) []locatedServerIdentifier {
	assignments := make([]locatedServerIdentifier, 0)
	for _, assignment := range serverIdentifierAssignment.FindAllStringIndex(text, -1) {
		value, _, ok := parseServerIdentifierValue(text, assignment[1])
		if !ok {
			continue
		}
		assignments = append(assignments, locatedServerIdentifier{
			index: assignment[0],
			value: normalizeServerIdentifier(value),
		})
	}
	return assignments
}

func uniqueServerIdentifiers(located []locatedServerIdentifier) []string {
	sort.SliceStable(located, func(i, j int) bool {
		return located[i].index < located[j].index
	})

	identifiers := make([]string, 0, len(located))
	seen := make(map[string]struct{}, len(located))
	for _, match := range located {
		if _, ok := seen[match.value]; ok {
			continue
		}
		seen[match.value] = struct{}{}
		identifiers = append(identifiers, match.value)
	}

	return identifiers
}

func LeadingServerIdentifier(text string) (string, bool) {
	assignment := serverIdentifierAssignment.FindStringIndex(text)
	if assignment == nil || strings.TrimSpace(text[:assignment[0]]) != "" {
		return "", false
	}

	value, _, ok := parseServerIdentifierValue(text, assignment[1])
	if !ok {
		return "", false
	}

	return normalizeServerIdentifier(value), true
}

func parseServerIdentifierValue(text string, offset int) (string, int, bool) {
	for offset < len(text) && (text[offset] == ' ' || text[offset] == '\t') {
		offset++
	}
	if offset >= len(text) {
		return "", offset, false
	}

	if text[offset] == '"' {
		start := offset
		for i := offset + 1; i < len(text); i++ {
			switch text[i] {
			case '\\':
				i++
			case '"':
				value, err := strconv.Unquote(text[start : i+1])
				if err != nil || value == "" {
					return "", i + 1, false
				}
				return value, i + 1, true
			case '\n', '\r':
				return "", i, false
			}
		}
		return "", len(text), false
	}

	start := offset
	for offset < len(text) && isServerIdentifierCharacter(text[offset]) {
		if text[offset] == '.' && (offset+1 == len(text) || isServerIdentifierDelimiter(text[offset+1])) {
			break
		}
		offset++
	}
	if start == offset || (offset < len(text) && !isServerIdentifierDelimiter(text[offset])) {
		return "", offset, false
	}

	return text[start:offset], offset, true
}

func normalizeServerIdentifier(identifier string) string {
	if canonicalServerUUIDPattern.MatchString(identifier) {
		return strings.ToLower(identifier)
	}
	return identifier
}

func isUUIDAdjacentCharacter(value byte) bool {
	return value >= 'a' && value <= 'z' ||
		value >= 'A' && value <= 'Z' ||
		value >= '0' && value <= '9' ||
		value == '_'
}

func isServerIdentifierCharacter(value byte) bool {
	return value >= 'a' && value <= 'z' ||
		value >= 'A' && value <= 'Z' ||
		value >= '0' && value <= '9' ||
		value == '.' || value == '_' || value == ':' || value == '-'
}

func isServerIdentifierDelimiter(value byte) bool {
	switch value {
	case ' ', '\t', '\n', '\r', ',', ';', '.', '!', '?', ')', ']', '}':
		return true
	default:
		return false
	}
}
