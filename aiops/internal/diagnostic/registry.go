package diagnostic

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"
	"time"
	"unicode/utf8"
)

const (
	serverBasicName    = "server-basic"
	serverBasicVersion = "v1"

	// The envelope cap bounds parsing while leaving room for a 2 KiB argument
	// object and JSON escaping. The decoded identifier cap is deliberately a
	// byte/resource limit, not a normalization or character-set rule.
	maxRequestJSONBytes    = 4096
	maxArgumentsJSONBytes  = 2048
	maxIdentifierUTF8Bytes = 1024
	maxToolNameBytes       = 64
	maxToolVersionBytes    = 16
)

var (
	errInvalidRequest        = errors.New("invalid diagnostic request")
	errRequestDenied         = errors.New("diagnostic request denied")
	errCapabilityUnavailable = errors.New("diagnostic capability unavailable")
)

type capabilityAvailability uint8

const (
	capabilityUnavailable capabilityAvailability = iota
)

type readerProfile uint8

const (
	profileProjectReader readerProfile = iota + 1
)

type riskClassification uint8

const (
	riskReadOnly riskClassification = iota + 1
)

type implementationID uint8

const (
	implementationServerBasic implementationID = iota + 1
)

type serverBasicOperationSet uint8

const (
	operationResolveServer serverBasicOperationSet = 1 << iota
	operationReadServer
	operationReadRelatedFlavor
	operationReadRelatedPorts
)

type trustedGrantSet uint8

const (
	grantServerBasic trustedGrantSet = 1 << iota
	grantResolveServer
	grantReadServer
	grantReadRelatedFlavor
	grantReadRelatedPorts
)

type prerequisiteSet uint8

const (
	prerequisiteAuthenticatedIngress prerequisiteSet = 1 << iota
	prerequisiteTrustedProjectReader
	prerequisiteReviewedReaderPolicy
	prerequisiteDurableAudit
	prerequisiteSanitization
)

type scopeRule uint8

const (
	scopeOneExplicitServerInTrustedProject scopeRule = iota + 1
)

type relationshipRule uint8

const (
	relatedReadsRequireVerifiedServerAndSeparateGrant relationshipRule = iota + 1
)

type argumentSchema struct {
	requiredIdentifier string
	maxIdentifierBytes int
}

type resourceLimits struct {
	maxRequestBytes       int
	maxArgumentsBytes     int
	maxIdentifierBytes    int
	maxElapsed            time.Duration
	maxAPICalls           int
	maxRetries            int
	maxLookupPages        int
	maxLookupRecords      int
	maxRelatedPortPages   int
	maxRelatedPortRecords int
	maxResponseBytes      int
	maxTotalResponseBytes int
	maxOutputBytes        int
}

type capabilityDefinition struct {
	name           string
	version        string
	intent         string
	schema         argumentSchema
	implementation implementationID
	operations     serverBasicOperationSet
	profile        readerProfile
	scope          scopeRule
	relationships  relationshipRule
	prerequisites  prerequisiteSet
	risk           riskClassification
	readOnly       bool
	availability   capabilityAvailability
	limits         resourceLimits
}

// serverBasicDefinition is the only definition in this chunk. Its fixed
// implementation ID is descriptive only: no executable implementation is
// attached, so the capability remains unavailable and cannot dispatch.
//
// Bounds are chosen for one explicit server action, not copied from legacy
// tools: a 15-second total budget, zero retries, up to two name-lookup pages
// (64 candidates) to establish bounded uniqueness, one server read, one
// optional flavor read, and up to two related-port pages (16 records) yield
// at most six API calls. If uniqueness is not established within those limits,
// a future implementation must refuse the request. Each response is capped at
// 256 KiB, all responses together at 512 KiB, and the eventual output at 16 KiB.
// These are reviewed maxima for future enforcement, not proof that collection
// or output is currently implemented.
func serverBasicDefinition() capabilityDefinition {
	return capabilityDefinition{
		name:           serverBasicName,
		version:        serverBasicVersion,
		intent:         "Inspect basic information for one explicitly selected OpenStack server.",
		schema:         argumentSchema{requiredIdentifier: "server_identifier", maxIdentifierBytes: maxIdentifierUTF8Bytes},
		implementation: implementationServerBasic,
		operations:     operationResolveServer | operationReadServer | operationReadRelatedFlavor | operationReadRelatedPorts,
		profile:        profileProjectReader,
		scope:          scopeOneExplicitServerInTrustedProject,
		relationships:  relatedReadsRequireVerifiedServerAndSeparateGrant,
		prerequisites:  prerequisiteAuthenticatedIngress | prerequisiteTrustedProjectReader | prerequisiteReviewedReaderPolicy | prerequisiteDurableAudit | prerequisiteSanitization,
		risk:           riskReadOnly,
		readOnly:       true,
		availability:   capabilityUnavailable,
		limits: resourceLimits{
			maxRequestBytes:       maxRequestJSONBytes,
			maxArgumentsBytes:     maxArgumentsJSONBytes,
			maxIdentifierBytes:    maxIdentifierUTF8Bytes,
			maxElapsed:            15 * time.Second,
			maxAPICalls:           6,
			maxRetries:            0,
			maxLookupPages:        2,
			maxLookupRecords:      64,
			maxRelatedPortPages:   2,
			maxRelatedPortRecords: 16,
			maxResponseBytes:      256 * 1024,
			maxTotalResponseBytes: 512 * 1024,
			maxOutputBytes:        16 * 1024,
		},
	}
}

func reviewedDefinitions() []capabilityDefinition {
	return []capabilityDefinition{serverBasicDefinition()}
}

func definitionFor(name, version string) (capabilityDefinition, error) {
	if name != serverBasicName {
		return capabilityDefinition{}, errRequestDenied
	}
	if version != serverBasicVersion {
		return capabilityDefinition{}, errCapabilityUnavailable
	}
	return serverBasicDefinition(), nil
}

type serverBasicArguments struct {
	serverIdentifier string
}

// validatedRequest records syntax and schema validation only. It contains no
// authorization context, implementation function, reader, or dispatch handle.
type validatedRequest struct {
	definition capabilityDefinition
	arguments  serverBasicArguments
}

// validateRequest validates the entire caller envelope. Correlation, project,
// profile, policy, budget, and authority are intentionally absent; those belong
// to trusted application context, never caller-controlled JSON.
func validateRequest(raw []byte) (validatedRequest, error) {
	fields, err := decodeJSONObject(raw, maxRequestJSONBytes)
	if err != nil || !hasExactKeys(fields, "name", "version", "arguments") {
		return validatedRequest{}, errInvalidRequest
	}

	name, ok := decodeJSONString(fields["name"], maxToolNameBytes)
	if !ok {
		return validatedRequest{}, errInvalidRequest
	}
	version, ok := decodeJSONString(fields["version"], maxToolVersionBytes)
	if !ok {
		return validatedRequest{}, errInvalidRequest
	}
	definition, err := definitionFor(name, version)
	if err != nil {
		return validatedRequest{}, err
	}

	if len(fields["arguments"]) > definition.limits.maxArgumentsBytes {
		return validatedRequest{}, errInvalidRequest
	}
	arguments, err := validateServerBasicArguments(fields["arguments"], definition.schema)
	if err != nil {
		return validatedRequest{}, errInvalidRequest
	}

	return validatedRequest{definition: definition, arguments: arguments}, nil
}

// validateServerBasicArguments is the tool-local schema check as well as the
// registry's argument check. Any later implementation must apply it before
// starting an operation; no implementation exists in this chunk.
func validateServerBasicArguments(raw []byte, schema argumentSchema) (serverBasicArguments, error) {
	fields, err := decodeJSONObject(raw, maxArgumentsJSONBytes)
	if err != nil || !hasExactKeys(fields, schema.requiredIdentifier) {
		return serverBasicArguments{}, errInvalidRequest
	}
	identifier, ok := decodeJSONString(fields[schema.requiredIdentifier], schema.maxIdentifierBytes)
	if !ok {
		return serverBasicArguments{}, errInvalidRequest
	}
	return serverBasicArguments{serverIdentifier: identifier}, nil
}

func decodeJSONString(raw json.RawMessage, maxBytes int) (string, bool) {
	if len(raw) == 0 {
		return "", false
	}
	var value string
	if err := json.Unmarshal(raw, &value); err != nil || value == "" || len(value) > maxBytes || !utf8.ValidString(value) || hasUnpairedSurrogateEscape(raw) {
		return "", false
	}
	return value, true
}

// encoding/json replaces unpaired UTF-16 surrogate escapes with U+FFFD. Reject
// them instead so validation never silently changes a caller's literal name.
func hasUnpairedSurrogateEscape(raw []byte) bool {
	for i := 0; i < len(raw); i++ {
		if raw[i] != '\\' {
			continue
		}
		i++
		if i >= len(raw) {
			return true
		}
		if raw[i] != 'u' {
			continue
		}
		if i+4 >= len(raw) {
			return true
		}
		unit, ok := parseHexCodeUnit(raw[i+1 : i+5])
		if !ok {
			return true
		}
		if unit >= 0xd800 && unit <= 0xdbff {
			if i+10 >= len(raw) || raw[i+5] != '\\' || raw[i+6] != 'u' {
				return true
			}
			low, ok := parseHexCodeUnit(raw[i+7 : i+11])
			if !ok || low < 0xdc00 || low > 0xdfff {
				return true
			}
			i += 10
			continue
		}
		if unit >= 0xdc00 && unit <= 0xdfff {
			return true
		}
		i += 4
	}
	return false
}

func parseHexCodeUnit(raw []byte) (uint16, bool) {
	if len(raw) != 4 {
		return 0, false
	}
	var value uint16
	for _, char := range raw {
		value <<= 4
		switch {
		case char >= '0' && char <= '9':
			value |= uint16(char - '0')
		case char >= 'a' && char <= 'f':
			value |= uint16(char-'a') + 10
		case char >= 'A' && char <= 'F':
			value |= uint16(char-'A') + 10
		default:
			return 0, false
		}
	}
	return value, true
}

func hasExactKeys(fields map[string]json.RawMessage, required ...string) bool {
	if len(fields) != len(required) {
		return false
	}
	for _, key := range required {
		if _, exists := fields[key]; !exists {
			return false
		}
	}
	return true
}

// decodeJSONObject accepts exactly one UTF-8 JSON object, detects duplicate
// decoded keys, and rejects trailing values. Input size is checked before any
// JSON work; parser errors are never returned to callers because they may quote
// attacker-controlled field names or values.
func decodeJSONObject(raw []byte, maxBytes int) (map[string]json.RawMessage, error) {
	if len(raw) == 0 || len(raw) > maxBytes || !utf8.Valid(raw) {
		return nil, errInvalidRequest
	}

	decoder := json.NewDecoder(bytes.NewReader(raw))
	token, err := decoder.Token()
	if err != nil || token != json.Delim('{') {
		return nil, errInvalidRequest
	}

	fields := make(map[string]json.RawMessage)
	for decoder.More() {
		token, err = decoder.Token()
		if err != nil {
			return nil, errInvalidRequest
		}
		key, ok := token.(string)
		if !ok {
			return nil, errInvalidRequest
		}
		if _, exists := fields[key]; exists {
			return nil, errInvalidRequest
		}
		var value json.RawMessage
		if err := decoder.Decode(&value); err != nil {
			return nil, errInvalidRequest
		}
		fields[key] = value
	}

	token, err = decoder.Token()
	if err != nil || token != json.Delim('}') {
		return nil, errInvalidRequest
	}
	var trailing json.RawMessage
	if err := decoder.Decode(&trailing); err != io.EOF {
		return nil, errInvalidRequest
	}
	return fields, nil
}

// These private contracts are boundaries for later chunks, not active
// dependencies. A trusted context can only be produced by application-owned
// authenticated ingress; its string identifiers alone are not proof of trust.
// The zero value grants nothing. No constructor, caller, or implementation is
// wired here.
type trustedCallerBinding struct {
	principalID    string
	securityDomain string
}

type trustedScope struct {
	cloudID        string
	projectID      string
	selectedServer string
}

type trustedPolicy struct {
	identity string
	version  string
}

type trustedContext struct {
	caller        trustedCallerBinding
	scope         trustedScope
	profile       readerProfile
	grants        trustedGrantSet
	policy        trustedPolicy
	limits        resourceLimits
	correlationID string
	expiresAt     time.Time
}

type requestAuthorizer interface {
	authorize(context.Context, trustedContext, validatedRequest) error
}

type requestAdmitter interface {
	admit(context.Context, trustedContext, validatedRequest) error
}

// requestAuditor is an interface contract only. Validated arguments remain
// untrusted and must be minimized/sanitized before an implementation records
// them; an intent must be durable before any read and an outcome before any
// result disclosure. No auditor implementation is wired in this chunk.
type requestAuditor interface {
	recordDenial(context.Context, trustedContext, validatedRequest, Status) error
	recordIntent(context.Context, trustedContext, validatedRequest) error
	recordOutcome(context.Context, trustedContext, validatedRequest, Result) error
}

// serverBasicReader returns untrusted API bytes to an internal owner only. It
// exposes narrow server-basic operations, never an SDK/client handle, endpoint,
// arbitrary operation name, or caller-selected implementation. No reader is
// implemented or invoked in this chunk; returned bytes require later
// sanitization before any sink.
type serverBasicReader interface {
	resolveServer(context.Context, trustedContext, string) (ResolvedTarget, error)
	readServer(context.Context, trustedContext, string) (json.RawMessage, error)
	readRelatedFlavor(context.Context, trustedContext, string) (json.RawMessage, error)
	readRelatedPorts(context.Context, trustedContext, string) (json.RawMessage, error)
}
