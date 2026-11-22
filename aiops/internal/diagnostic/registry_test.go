package diagnostic

import (
	"bytes"
	"encoding/json"
	"errors"
	"reflect"
	"strings"
	"testing"
)

func TestOnlyReviewedServerBasicDefinitionIsAvailableForValidation(t *testing.T) {
	definitions := reviewedDefinitions()
	if len(definitions) != 1 {
		t.Fatalf("definition count = %d, want exactly one", len(definitions))
	}
	definition := definitions[0]
	if definition.name != serverBasicName || definition.version != serverBasicVersion {
		t.Fatalf("definition identity = %q/%q", definition.name, definition.version)
	}
	if definition.intent == "" || definition.schema.requiredIdentifier != "server_identifier" {
		t.Fatalf("definition lacks diagnostic intent or strict identifier schema: %#v", definition)
	}
	if definition.schema.maxIdentifierBytes != maxIdentifierUTF8Bytes {
		t.Fatalf("definition does not enforce the fixed argument schema: %#v", definition.schema)
	}
	if definition.profile != profileProjectReader || definition.scope != scopeOneExplicitServerInTrustedProject {
		t.Fatalf("definition has unexpected profile/scope: %#v", definition)
	}
	if definition.relationships != relatedReadsRequireVerifiedServerAndSeparateGrant {
		t.Fatalf("definition has unexpected relationship rule: %v", definition.relationships)
	}
	if definition.prerequisites != prerequisiteAuthenticatedIngress|prerequisiteTrustedProjectReader|prerequisiteReviewedReaderPolicy|prerequisiteDurableAudit|prerequisiteSanitization {
		t.Fatalf("definition prerequisites = %05b", definition.prerequisites)
	}
	if definition.risk != riskReadOnly || !definition.readOnly {
		t.Fatalf("definition is not explicitly read-only: %#v", definition)
	}
	if definition.implementation != implementationServerBasic || definition.availability != capabilityUnavailable {
		t.Fatalf("definition must have one fixed mapping but remain unavailable: %#v", definition)
	}
	if definition.operations != operationResolveServer|operationReadServer|operationReadRelatedFlavor|operationReadRelatedPorts {
		t.Fatalf("unexpected private operation set: %04b", definition.operations)
	}

	limits := definition.limits
	if limits.maxRequestBytes != 4096 || limits.maxArgumentsBytes != 2048 || limits.maxIdentifierBytes != 1024 {
		t.Fatalf("unexpected request limits: %#v", limits)
	}
	if limits.maxElapsed <= 0 || limits.maxAPICalls != 6 || limits.maxRetries != 0 {
		t.Fatalf("unbounded or retry-enabled operation limits: %#v", limits)
	}
	if limits.maxLookupPages != 2 || limits.maxLookupRecords != 64 || limits.maxRelatedPortPages != 2 || limits.maxRelatedPortRecords != 16 {
		t.Fatalf("unexpected page/record bounds: %#v", limits)
	}
	if limits.maxResponseBytes != 256*1024 || limits.maxTotalResponseBytes != 512*1024 || limits.maxOutputBytes != 16*1024 {
		t.Fatalf("unexpected response/output bounds: %#v", limits)
	}
}

func TestDefinitionLookupDeniesUnknownNamesWithoutFallback(t *testing.T) {
	for _, name := range []string{"get_server", "get_flavor", "get_ports", "shell", "server-delete", ""} {
		t.Run(name, func(t *testing.T) {
			if _, err := definitionFor(name, serverBasicVersion); !errors.Is(err, errRequestDenied) {
				t.Fatalf("definitionFor(%q) error = %v, want fixed denial", name, err)
			}
		})
	}
	if _, err := definitionFor(serverBasicName, "v2"); !errors.Is(err, errCapabilityUnavailable) {
		t.Fatalf("unsupported version error = %v, want unavailable", err)
	}
}

func TestValidateRequestPreservesLiteralWhitespaceAndUnicode(t *testing.T) {
	identifier := "\t compute-节点  \n"
	request, err := validateRequest(validServerBasicRequest(identifier))
	if err != nil {
		t.Fatalf("validateRequest() error = %v", err)
	}
	if request.arguments.serverIdentifier != identifier {
		t.Fatalf("identifier = %q, want exact original %q", request.arguments.serverIdentifier, identifier)
	}
	if request.definition.availability != capabilityUnavailable {
		t.Fatalf("validation made capability available: %v", request.definition.availability)
	}
	if request.definition.name != serverBasicName || request.definition.version != serverBasicVersion {
		t.Fatalf("validated request changed fixed mapping: %#v", request.definition)
	}
}

func TestServerBasicToolLocalValidatorPreservesValidSurrogatePairAndRejectsUnpaired(t *testing.T) {
	arguments, err := validateServerBasicArguments([]byte(`{"server_identifier":"\ud83d\ude80"}`), serverBasicDefinition().schema)
	if err != nil {
		t.Fatalf("valid surrogate pair rejected: %v", err)
	}
	if arguments.serverIdentifier != "🚀" {
		t.Fatalf("decoded identifier = %q, want rocket", arguments.serverIdentifier)
	}

	for _, escaped := range []string{`"\ud800"`, `"\udc00"`, `"\ud800\u0041"`} {
		raw := []byte(`{"server_identifier":` + escaped + `}`)
		if _, err := validateServerBasicArguments(raw, serverBasicDefinition().schema); !errors.Is(err, errInvalidRequest) {
			t.Errorf("unpaired surrogate %s error = %v, want invalid request", escaped, err)
		}
	}
}

func TestValidateRequestAcceptsWhitespaceAroundSingleJSONValue(t *testing.T) {
	raw := append([]byte(" \n\t"), validServerBasicRequest("server-1")...)
	raw = append(raw, []byte("\n ")...)
	if _, err := validateRequest(raw); err != nil {
		t.Fatalf("valid request with surrounding whitespace rejected: %v", err)
	}
}

func TestServerBasicToolLocalValidatorAcceptsIdentifierAtLimit(t *testing.T) {
	identifier := strings.Repeat("x", maxIdentifierUTF8Bytes)
	arguments, err := validateServerBasicArguments(serverBasicArgumentsJSON(identifier), serverBasicDefinition().schema)
	if err != nil {
		t.Fatalf("tool-local validation at limit failed: %v", err)
	}
	if arguments.serverIdentifier != identifier {
		t.Fatal("tool-local validation changed the identifier")
	}
}

func TestValidateRequestRejectsInvalidEnvelopeWithoutEchoingInput(t *testing.T) {
	valid := validServerBasicRequest("server-1")
	oversized := append(append([]byte(nil), valid...), bytes.Repeat([]byte(" "), maxRequestJSONBytes)...)
	invalidUTF8 := append(append([]byte(nil), valid...), 0xff)
	trailingObject := append(append([]byte(nil), valid...), []byte(` {}`)...)
	trailingValue := append(append([]byte(nil), valid...), []byte(` true`)...)

	tests := []struct {
		name string
		raw  []byte
		want error
	}{
		{name: "empty", raw: nil, want: errInvalidRequest},
		{name: "malformed json", raw: []byte(`{"name":`), want: errInvalidRequest},
		{name: "array root", raw: []byte(`[]`), want: errInvalidRequest},
		{name: "null root", raw: []byte(`null`), want: errInvalidRequest},
		{name: "missing name", raw: []byte(`{"version":"v1","arguments":{"server_identifier":"x"}}`), want: errInvalidRequest},
		{name: "missing version", raw: []byte(`{"name":"server-basic","arguments":{"server_identifier":"x"}}`), want: errInvalidRequest},
		{name: "missing arguments", raw: []byte(`{"name":"server-basic","version":"v1"}`), want: errInvalidRequest},
		{name: "wrong name type", raw: []byte(`{"name":1,"version":"v1","arguments":{"server_identifier":"x"}}`), want: errInvalidRequest},
		{name: "wrong version type", raw: []byte(`{"name":"server-basic","version":true,"arguments":{"server_identifier":"x"}}`), want: errInvalidRequest},
		{name: "wrong arguments type", raw: []byte(`{"name":"server-basic","version":"v1","arguments":[]}`), want: errInvalidRequest},
		{name: "duplicate name", raw: []byte(`{"name":"server-basic","name":"server-basic","version":"v1","arguments":{"server_identifier":"x"}}`), want: errInvalidRequest},
		{name: "escaped duplicate name", raw: []byte(`{"name":"server-basic","\u006eame":"server-basic","version":"v1","arguments":{"server_identifier":"x"}}`), want: errInvalidRequest},
		{name: "duplicate arguments", raw: []byte(`{"name":"server-basic","version":"v1","arguments":{"server_identifier":"x"},"arguments":{"server_identifier":"y"}}`), want: errInvalidRequest},
		{name: "trailing object", raw: trailingObject, want: errInvalidRequest},
		{name: "trailing value", raw: trailingValue, want: errInvalidRequest},
		{name: "invalid utf-8", raw: invalidUTF8, want: errInvalidRequest},
		{name: "request over byte limit", raw: oversized, want: errInvalidRequest},
		{name: "unknown tool", raw: requestWithName("get_server", serverBasicVersion, `{"server_identifier":"x"}`), want: errRequestDenied},
		{name: "generic tool", raw: requestWithName("shell", serverBasicVersion, `{"server_identifier":"x"}`), want: errRequestDenied},
		{name: "mutation tool", raw: requestWithName("server-delete", serverBasicVersion, `{"server_identifier":"x"}`), want: errRequestDenied},
		{name: "unsupported version", raw: requestWithName(serverBasicName, "v2", `{"server_identifier":"x"}`), want: errCapabilityUnavailable},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			_, err := validateRequest(test.raw)
			if !errors.Is(err, test.want) {
				t.Fatalf("validateRequest() error = %v, want %v", err, test.want)
			}
			if err == nil || len(err.Error()) > MaxPublicErrorMessageBytes || strings.Contains(err.Error(), "secret-canary") {
				t.Fatalf("error is not fixed and bounded: %v", err)
			}
		})
	}
}

func TestValidateRequestRejectsCallerAuthorityAndImplementationOverrides(t *testing.T) {
	overrides := []string{"implementation", "endpoint", "path", "host", "profile", "policy", "budget", "correlation_id"}
	for _, field := range overrides {
		t.Run("envelope/"+field, func(t *testing.T) {
			raw := []byte(`{"name":"server-basic","version":"v1","arguments":{"server_identifier":"server-1"},"` + field + `":"secret-canary"}`)
			if _, err := validateRequest(raw); !errors.Is(err, errInvalidRequest) {
				t.Fatalf("override %q error = %v, want invalid request", field, err)
			} else if strings.Contains(err.Error(), "secret-canary") || len(err.Error()) > MaxPublicErrorMessageBytes {
				t.Fatalf("override %q error echoed or exceeded bounds: %v", field, err)
			}
		})
		t.Run("arguments/"+field, func(t *testing.T) {
			arguments := `{"server_identifier":"server-1","` + field + `":"secret-canary"}`
			if _, err := validateRequest(validServerBasicRequestWithArguments(arguments)); !errors.Is(err, errInvalidRequest) {
				t.Fatalf("argument override %q error = %v, want invalid request", field, err)
			} else if strings.Contains(err.Error(), "secret-canary") || len(err.Error()) > MaxPublicErrorMessageBytes {
				t.Fatalf("argument override %q error echoed or exceeded bounds: %v", field, err)
			}
		})
	}
}

func TestServerBasicToolLocalValidatorRejectsMalformedAndExtraArguments(t *testing.T) {
	tooLong := serverBasicArgumentsJSON(strings.Repeat("x", maxIdentifierUTF8Bytes+1))
	tooManyArgumentBytes := []byte(`{"server_identifier":"` + strings.Repeat("x", maxArgumentsJSONBytes) + `"}`)
	invalidUTF8 := []byte{'{', '"', 's', 'e', 'r', 'v', 'e', 'r', '_', 'i', 'd', 'e', 'n', 't', 'i', 'f', 'i', 'e', 'r', '"', ':', '"', 0xff, '"', '}'}

	tests := []struct {
		name string
		raw  []byte
	}{
		{name: "empty object", raw: []byte(`{}`)},
		{name: "empty identifier", raw: []byte(`{"server_identifier":""}`)},
		{name: "null identifier", raw: []byte(`{"server_identifier":null}`)},
		{name: "number identifier", raw: []byte(`{"server_identifier":17}`)},
		{name: "boolean identifier", raw: []byte(`{"server_identifier":false}`)},
		{name: "array identifier", raw: []byte(`{"server_identifier":[]}`)},
		{name: "object identifier", raw: []byte(`{"server_identifier":{}}`)},
		{name: "extra field", raw: []byte(`{"server_identifier":"server-1","profile":"secret-canary"}`)},
		{name: "duplicate field", raw: []byte(`{"server_identifier":"server-1","server_identifier":"server-2"}`)},
		{name: "escaped duplicate field", raw: []byte(`{"server_identifier":"server-1","server_\u0069dentifier":"server-2"}`)},
		{name: "trailing object", raw: []byte(`{"server_identifier":"server-1"}{}`)},
		{name: "malformed json", raw: []byte(`{"server_identifier":`)},
		{name: "invalid utf-8", raw: invalidUTF8},
		{name: "identifier over limit", raw: tooLong},
		{name: "argument object over limit", raw: tooManyArgumentBytes},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			_, err := validateServerBasicArguments(test.raw, serverBasicDefinition().schema)
			if !errors.Is(err, errInvalidRequest) {
				t.Fatalf("tool-local validation error = %v, want invalid request", err)
			}
			if strings.Contains(err.Error(), "secret-canary") || len(err.Error()) > MaxPublicErrorMessageBytes {
				t.Fatalf("tool-local error echoed or exceeded bounds: %v", err)
			}
		})
	}
}

func TestValidationDoesNotGrantAuthorityOrCreateDispatchCapability(t *testing.T) {
	request, err := validateRequest(validServerBasicRequest(" server-1 "))
	if err != nil {
		t.Fatalf("validateRequest() error = %v", err)
	}
	if request.definition.availability != capabilityUnavailable {
		t.Fatalf("valid input changed capability availability: %v", request.definition.availability)
	}
	if reflect.TypeOf(request.definition.operations) == reflect.TypeOf(trustedGrantSet(0)) {
		t.Fatal("definition operation metadata is interchangeable with trusted grants")
	}

	// The validation entry point accepts only raw bytes and returns a data-only
	// value. It has no context, authorization, admission, audit, reader, or
	// implementation dependency to call or grant through.
	validatorType := reflect.TypeOf(validateRequest)
	if validatorType.NumIn() != 1 || validatorType.In(0) != reflect.TypeOf([]byte(nil)) {
		t.Fatalf("validator has non-input dependencies: %v", validatorType)
	}
	requestType := reflect.TypeOf(request)
	for i := 0; i < requestType.NumField(); i++ {
		field := requestType.Field(i)
		kind := field.Type.Kind()
		if kind == reflect.Func || kind == reflect.Interface || kind == reflect.Pointer {
			t.Fatalf("validated request carries executable or reference authority in %q: %v", field.Name, field.Type)
		}
	}
	if requestType.NumMethod() != 0 {
		t.Fatalf("validated request unexpectedly exposes methods: %v", requestType)
	}
}

func validServerBasicRequest(identifier string) []byte {
	return validServerBasicRequestWithArguments(string(serverBasicArgumentsJSON(identifier)))
}

func validServerBasicRequestWithArguments(arguments string) []byte {
	return requestWithName(serverBasicName, serverBasicVersion, arguments)
}

func requestWithName(name, version, arguments string) []byte {
	encodedName, _ := json.Marshal(name)
	encodedVersion, _ := json.Marshal(version)
	return []byte(`{"name":` + string(encodedName) + `,"version":` + string(encodedVersion) + `,"arguments":` + arguments + `}`)
}

func serverBasicArgumentsJSON(identifier string) []byte {
	encodedIdentifier, _ := json.Marshal(identifier)
	return []byte(`{"server_identifier":` + string(encodedIdentifier) + `}`)
}
