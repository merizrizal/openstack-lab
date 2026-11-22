package diagnostic

import (
	"encoding/base64"
	"encoding/json"
	"errors"
	"regexp"
	"strings"
	"unicode/utf8"
)

const (
	maxSanitizationInputBytes  = 64 * 1024
	maxSanitizationOutputBytes = 16 * 1024
	maxSanitizationFragments   = 256
)

var (
	errSanitizationWithheld   = errors.New("diagnostic content withheld")
	pemBlockPattern           = regexp.MustCompile(`(?s)-----BEGIN [A-Z0-9 ]+-----.*?-----END [A-Z0-9 ]+-----`)
	pemBoundaryPattern        = regexp.MustCompile(`(?i)-----\s*(?:BEGIN|END)\b`)
	authorizationPattern      = regexp.MustCompile(`(?i)((?:authorization|proxy-authorization|x-auth-token|x-api-key)\s*[:=]\s*)[^\r\n,;]+`)
	bearerPattern             = regexp.MustCompile(`(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+`)
	assignmentSecretPattern   = regexp.MustCompile(`(?i)([A-Za-z0-9_.-]*(?:password|passwd|token|secret|api[_-]?key|client[_-]?secret|private[_-]?key|credential|access[_-]?key)[A-Za-z0-9_.-]*\s*[:=]\s*)(?:"[^"]*"|'[^']*'|[^\s,;&]+)`)
	quotedSensitiveKeyPattern = regexp.MustCompile(`(?i)"[A-Za-z0-9_.-]*(?:password|passwd|token|secret|api[_-]?key|client[_-]?secret|private[_-]?key|credential|access[_-]?key)[A-Za-z0-9_.-]*"\s*:`)
	querySecretPattern        = regexp.MustCompile(`(?i)([?&](?:password|passwd|token|access[_-]?token|refresh[_-]?token|secret|api[_-]?key|client[_-]?secret|private[_-]?key|access[_-]?key)=)[^&#\s]+`)
	base64TokenPattern        = regexp.MustCompile(`[A-Za-z0-9+/_-]{16,}={0,2}`)
)

// SanitizationMetadata records transformations without implying that an
// observation is complete, current, healthy, or authoritative.
type SanitizationMetadata struct {
	Redacted  bool `json:"redacted"`
	Truncated bool `json:"truncated"`
	Withheld  bool `json:"withheld"`
}

// SanitizedValue is an opaque, data-only transformed value. It cannot carry an
// implementation, policy, or authority. Only the fixed argument projection can
// currently produce content; unclassified free-form text is withheld. Pattern
// screening is not proof that any arbitrary source contains no secrets, and
// retained local identifiers remain sensitive untrusted data.
type SanitizedValue struct {
	jsonValue json.RawMessage
	textValue *string
	metadata  SanitizationMetadata
}

// Metadata returns transformation facts without exposing the original input.
func (value SanitizedValue) Metadata() SanitizationMetadata {
	return value.metadata
}

// Text returns text only when a reviewed source-specific transform produced it.
func (value SanitizedValue) Text() (string, bool) {
	if value.metadata.Withheld || value.textValue == nil {
		return "", false
	}
	return *value.textValue, true
}

// JSONValue returns a copy of the sanitized JSON value only when available.
func (value SanitizedValue) JSONValue() ([]byte, bool) {
	if value.metadata.Withheld || len(value.jsonValue) == 0 {
		return nil, false
	}
	return append([]byte(nil), value.jsonValue...), true
}

// MarshalJSON preserves an explicit data-only classification and omits content
// entirely when transformation failed or was withheld.
func (value SanitizedValue) MarshalJSON() ([]byte, error) {
	if value.metadata.Withheld {
		return json.Marshal(sanitizedValueEnvelope{
			Classification: "untrusted_data",
			Metadata:       value.metadata,
		})
	}
	if value.textValue == nil && len(value.jsonValue) == 0 {
		return nil, errSanitizationWithheld
	}

	envelope := sanitizedValueEnvelope{
		Classification: "untrusted_data",
		Metadata:       value.metadata,
	}
	if value.textValue != nil {
		encoded, err := json.Marshal(*value.textValue)
		if err != nil {
			return nil, errSanitizationWithheld
		}
		envelope.Value = encoded
	} else {
		envelope.Value = append(json.RawMessage(nil), value.jsonValue...)
	}
	return json.Marshal(envelope)
}

type sanitizedValueEnvelope struct {
	Classification string               `json:"classification"`
	Value          json.RawMessage      `json:"value,omitempty"`
	Metadata       SanitizationMetadata `json:"metadata"`
}

// sanitizeText refuses unclassified free-form content. Pattern screening can
// redact known forms but cannot establish that arbitrary text is secret-free;
// text remains withheld until a reviewed source-specific contract exists.
func sanitizeText(fragments []string) (SanitizedValue, error) {
	joined, err := joinSanitizationFragments(fragments)
	if err != nil || !utf8.ValidString(joined) {
		return withheldSanitizedValue(), errSanitizationWithheld
	}
	return withheldSanitizedValueWithMetadata(SanitizationMetadata{
		Truncated: len(joined) > maxSanitizationOutputBytes,
	}), errSanitizationWithheld
}

// sanitizeArguments applies the registry's single reviewed request projection.
// No caller supplies paths: only the exact server_identifier leaf is eligible.
// Other request fields are rejected, while malformed/unsupported input is
// withheld. The retained identifier remains sensitive local data.
func sanitizeArguments(raw []byte) (SanitizedValue, error) {
	arguments, err := validateServerBasicArguments(raw, serverBasicDefinition().schema)
	if err != nil {
		return withheldSanitizedValue(), errSanitizationWithheld
	}
	identifier, redacted, err := redactText(arguments.serverIdentifier)
	if err != nil {
		return withheldSanitizedValue(), errSanitizationWithheld
	}
	identifier, truncated := truncateUTF8(identifier, maxSanitizationOutputBytes)
	metadata := SanitizationMetadata{Redacted: redacted, Truncated: truncated}
	encoded, err := json.Marshal(map[string]string{"server_identifier": identifier})
	if err != nil || len(encoded) == 0 || len(encoded) > maxSanitizationOutputBytes {
		return withheldSanitizedValueWithMetadata(metadata), errSanitizationWithheld
	}
	return SanitizedValue{jsonValue: encoded, metadata: metadata}, nil
}

// sanitizeError deliberately ignores the raw error text and returns only a
// fixed public category. Raw SDK, transport, filesystem, and debug errors are
// never copied into a sink value.
func sanitizeError(_ error, category ErrorCategory) SanitizedValue {
	if !validErrorCategory(string(category)) {
		category = ErrorCategoryInternal
	}
	encoded, err := json.Marshal(PublicError{Category: category})
	if err != nil {
		return withheldSanitizedValue()
	}
	return SanitizedValue{jsonValue: encoded}
}

func withheldSanitizedValue() SanitizedValue {
	return withheldSanitizedValueWithMetadata(SanitizationMetadata{})
}

func withheldSanitizedValueWithMetadata(metadata SanitizationMetadata) SanitizedValue {
	metadata.Withheld = true
	return SanitizedValue{metadata: metadata}
}

func joinSanitizationFragments(fragments []string) (string, error) {
	if len(fragments) == 0 || len(fragments) > maxSanitizationFragments {
		return "", errSanitizationWithheld
	}
	var builder strings.Builder
	for _, fragment := range fragments {
		if builder.Len() > maxSanitizationInputBytes-len(fragment) {
			return "", errSanitizationWithheld
		}
		builder.WriteString(fragment)
	}
	return builder.String(), nil
}

func redactText(value string) (string, bool, error) {
	if containsEncodedSensitiveText(value) {
		return "", false, errSanitizationWithheld
	}
	return redactKnownText(value)
}

func containsEncodedSensitiveText(value string) bool {
	if containsBase64SensitivePattern(value) {
		return true
	}
	if !strings.Contains(value, "%") {
		return false
	}

	decoded := value
	for pass := 0; pass < 2; pass++ {
		unescaped, changed := decodePercentEscapes(decoded)
		if !changed {
			return false
		}
		if _, redacted, err := redactKnownText(unescaped); err != nil || redacted {
			return true
		}
		decoded = unescaped
	}

	// Refuse deeper encodings rather than return text whose meaning has not
	// been examined within the fixed decoding work bound.
	_, changed := decodePercentEscapes(decoded)
	return changed
}

func containsBase64SensitivePattern(value string) bool {
	encodings := []*base64.Encoding{
		base64.StdEncoding,
		base64.RawStdEncoding,
		base64.URLEncoding,
		base64.RawURLEncoding,
	}
	for _, token := range base64TokenPattern.FindAllString(value, -1) {
		for _, encoding := range encodings {
			decoded, err := encoding.DecodeString(token)
			if err != nil || !utf8.Valid(decoded) {
				continue
			}
			if _, redacted, err := redactKnownText(string(decoded)); err != nil || redacted {
				return true
			}
		}
	}
	return false
}

func decodePercentEscapes(value string) (string, bool) {
	var builder strings.Builder
	builder.Grow(len(value))
	changed := false
	for i := 0; i < len(value); i++ {
		if value[i] == '%' && i+2 < len(value) {
			high, highOK := hexNibble(value[i+1])
			low, lowOK := hexNibble(value[i+2])
			if highOK && lowOK {
				builder.WriteByte(high<<4 | low)
				i += 2
				changed = true
				continue
			}
		}
		builder.WriteByte(value[i])
	}
	return builder.String(), changed
}

func hexNibble(value byte) (byte, bool) {
	switch {
	case value >= '0' && value <= '9':
		return value - '0', true
	case value >= 'a' && value <= 'f':
		return value - 'a' + 10, true
	case value >= 'A' && value <= 'F':
		return value - 'A' + 10, true
	default:
		return 0, false
	}
}

func redactKnownText(value string) (string, bool, error) {
	if quotedSensitiveKeyPattern.MatchString(value) {
		return "", false, errSanitizationWithheld
	}
	redacted := pemBlockPattern.ReplaceAllString(value, "[REDACTED PEM]")
	if pemBoundaryPattern.MatchString(redacted) {
		return "", false, errSanitizationWithheld
	}
	redacted = authorizationPattern.ReplaceAllString(redacted, "${1}[REDACTED]")
	redacted = assignmentSecretPattern.ReplaceAllString(redacted, "${1}[REDACTED]")
	redacted = querySecretPattern.ReplaceAllString(redacted, "${1}[REDACTED]")
	redacted = bearerPattern.ReplaceAllString(redacted, "Bearer [REDACTED]")
	return redacted, redacted != value, nil
}

func truncateUTF8(value string, maxBytes int) (string, bool) {
	if len(value) <= maxBytes {
		return value, false
	}
	const marker = "…[truncated]"
	if maxBytes <= len(marker) {
		prefix := utf8SafePrefix(value, maxBytes)
		return prefix, true
	}
	prefix := utf8SafePrefix(value, maxBytes-len(marker))
	return prefix + marker, true
}

func utf8SafePrefix(value string, maxBytes int) string {
	if maxBytes <= 0 {
		return ""
	}
	if len(value) <= maxBytes {
		return value
	}
	end := maxBytes
	for end > 0 && !utf8.RuneStart(value[end]) {
		end--
	}
	return value[:end]
}
