package diagnostic

import (
	"encoding/json"
	"reflect"
	"strings"
	"testing"
	"time"
)

func TestStatusesHaveExactVersionedWireValues(t *testing.T) {
	tests := []struct {
		status Status
		wire   string
	}{
		{StatusOK, `"ok"`},
		{StatusPartial, `"partial"`},
		{StatusError, `"error"`},
		{StatusDenied, `"denied"`},
		{StatusValidationError, `"validation_error"`},
		{StatusTimeout, `"timeout"`},
		{StatusCancelled, `"cancelled"`},
		{StatusUnavailable, `"unavailable"`},
	}

	for _, test := range tests {
		t.Run(string(test.status), func(t *testing.T) {
			encoded, err := json.Marshal(test.status)
			if err != nil {
				t.Fatalf("json.Marshal() error = %v", err)
			}
			if string(encoded) != test.wire {
				t.Fatalf("wire status = %s, want %s", encoded, test.wire)
			}
			if got := test.status.String(); got != string(test.status) {
				t.Fatalf("String() = %q, want %q", got, test.status)
			}

			var decoded Status
			if err := json.Unmarshal(encoded, &decoded); err != nil {
				t.Fatalf("json.Unmarshal() error = %v", err)
			}
			if decoded != test.status {
				t.Fatalf("decoded status = %q, want %q", decoded, test.status)
			}
		})
	}
}

func TestMetadataFlagsAreIndependentOfEveryStatus(t *testing.T) {
	statuses := []Status{
		StatusOK, StatusPartial, StatusError, StatusDenied,
		StatusValidationError, StatusTimeout, StatusCancelled, StatusUnavailable,
	}

	for _, status := range statuses {
		for flags := 0; flags < 8; flags++ {
			want := ResultMetadata{
				Truncated: flags&1 != 0,
				Redacted:  flags&2 != 0,
				Withheld:  flags&4 != 0,
			}
			name := string(status) + "/" + metadataName(want)
			t.Run(name, func(t *testing.T) {
				result := Result{
					SchemaVersion: ResultSchemaVersion,
					Status:        status,
					Provenance: Provenance{
						Timing: CollectionTiming{State: TimingNotApplicable},
					},
					Metadata: want,
				}
				encoded, err := json.Marshal(result)
				if err != nil {
					t.Fatalf("json.Marshal() error = %v", err)
				}

				var decoded Result
				if err := json.Unmarshal(encoded, &decoded); err != nil {
					t.Fatalf("json.Unmarshal() error = %v", err)
				}
				if decoded.SchemaVersion != ResultSchemaVersion {
					t.Fatalf("schema version = %q, want %q", decoded.SchemaVersion, ResultSchemaVersion)
				}
				if decoded.Status != status {
					t.Fatalf("status = %q, want %q", decoded.Status, status)
				}
				if decoded.Metadata != want {
					t.Fatalf("metadata = %#v, want %#v", decoded.Metadata, want)
				}
			})
		}
	}
}

func TestFieldStatesHaveDistinctWireValues(t *testing.T) {
	tests := []struct {
		state FieldState
		wire  string
	}{
		{FieldAvailable, `"available"`},
		{FieldDenied, `"denied"`},
		{FieldUnavailable, `"unavailable"`},
		{FieldNotApplicable, `"not-applicable"`},
	}

	for _, test := range tests {
		t.Run(string(test.state), func(t *testing.T) {
			encoded, err := json.Marshal(test.state)
			if err != nil {
				t.Fatalf("json.Marshal() error = %v", err)
			}
			if string(encoded) != test.wire {
				t.Fatalf("wire state = %s, want %s", encoded, test.wire)
			}
			var decoded FieldState
			if err := json.Unmarshal(encoded, &decoded); err != nil {
				t.Fatalf("json.Unmarshal() error = %v", err)
			}
			if decoded != test.state {
				t.Fatalf("decoded state = %q, want %q", decoded, test.state)
			}
		})
	}

	if _, err := json.Marshal(FieldState("secret-canary")); err == nil || strings.Contains(err.Error(), "secret-canary") {
		t.Fatalf("invalid field state must fail without exposing its value: %v", err)
	}
}

func TestNotApplicableTimingIsExplicitAndHasNoFabricatedDuration(t *testing.T) {
	result := Result{
		SchemaVersion: ResultSchemaVersion,
		Status:        StatusDenied,
		Provenance: Provenance{
			Timing: CollectionTiming{State: TimingNotApplicable},
		},
	}

	encoded, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("json.Marshal() error = %v", err)
	}
	var wire struct {
		Provenance struct {
			Timing map[string]json.RawMessage `json:"timing"`
		} `json:"provenance"`
	}
	if err := json.Unmarshal(encoded, &wire); err != nil {
		t.Fatalf("decode timing JSON: %v", err)
	}
	var state string
	if err := json.Unmarshal(wire.Provenance.Timing["state"], &state); err != nil {
		t.Fatalf("decode timing state: %v", err)
	}
	if state != string(TimingNotApplicable) {
		t.Fatalf("timing state = %q, want %q", state, TimingNotApplicable)
	}
	for _, key := range []string{"started_at", "ended_at", "duration_ns"} {
		if _, exists := wire.Provenance.Timing[key]; exists {
			t.Errorf("not-applicable timing unexpectedly contains %q", key)
		}
	}
}

func TestMeasuredTimingAndProvenanceRoundTripWithoutIdentityLoss(t *testing.T) {
	startedAt := time.Date(2026, time.January, 2, 3, 4, 5, 0, time.UTC)
	endedAt := startedAt
	zeroDuration := int64(0)
	result := Result{
		SchemaVersion: ResultSchemaVersion,
		Status:        StatusPartial,
		Provenance: Provenance{
			RequestID:     "request-17",
			ToolName:      "server-basic",
			ToolVersion:   "v1",
			CorrelationID: "correlation-23",
			Target: &TargetIdentity{
				Original: "  exact Server name  ",
				Resolved: &ResolvedTarget{ID: "server-id-9", Name: "exact Server name"},
			},
			Timing: CollectionTiming{
				State:      TimingMeasured,
				StartedAt:  &startedAt,
				EndedAt:    &endedAt,
				DurationNS: &zeroDuration,
			},
			Evidence: []EvidenceReference{{ID: "evidence-31"}, {ID: "evidence-32"}},
		},
		Fields: []FieldOutcome{
			{Name: "status", State: FieldAvailable},
			{Name: "fault", State: FieldDenied, Error: &PublicError{Category: ErrorCategoryAuthorization}},
			{Name: "image", State: FieldUnavailable, Error: &PublicError{Category: ErrorCategoryUnavailable}},
			{Name: "host", State: FieldNotApplicable},
		},
		Metadata: ResultMetadata{Truncated: true, Redacted: true, Withheld: true},
	}

	encoded, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("json.Marshal() error = %v", err)
	}
	if strings.Contains(string(encoded), "exit_code") {
		t.Fatalf("result contract must not invent a subprocess exit code: %s", encoded)
	}

	var decoded Result
	if err := json.Unmarshal(encoded, &decoded); err != nil {
		t.Fatalf("json.Unmarshal() error = %v", err)
	}
	if !reflect.DeepEqual(decoded, result) {
		t.Fatalf("round-trip result mismatch:\n got: %#v\nwant: %#v", decoded, result)
	}
}

func TestPublicErrorsAreFixedBoundedAndRejectUnknownCategories(t *testing.T) {
	categories := []ErrorCategory{
		ErrorCategoryValidation, ErrorCategoryAuthorization, ErrorCategoryUnavailable,
		ErrorCategoryTimeout, ErrorCategoryCancelled, ErrorCategoryCollection,
		ErrorCategoryIntegrity, ErrorCategoryInternal,
	}

	for _, category := range categories {
		t.Run(string(category), func(t *testing.T) {
			publicError := PublicError{Category: category}
			message := publicError.Message()
			if len(message) == 0 || len(message) > MaxPublicErrorMessageBytes {
				t.Fatalf("public message length = %d, want 1..%d", len(message), MaxPublicErrorMessageBytes)
			}

			encoded, err := json.Marshal(publicError)
			if err != nil {
				t.Fatalf("json.Marshal() error = %v", err)
			}
			var decoded PublicError
			if err := json.Unmarshal(encoded, &decoded); err != nil {
				t.Fatalf("json.Unmarshal() error = %v", err)
			}
			if decoded.Category != category {
				t.Fatalf("decoded category = %q, want %q", decoded.Category, category)
			}
			var fields map[string]json.RawMessage
			if err := json.Unmarshal(encoded, &fields); err != nil {
				t.Fatalf("decode public error JSON: %v", err)
			}
			if _, exists := fields["message"]; exists {
				t.Fatalf("public error JSON must not contain free-form message: %s", encoded)
			}
		})
	}

	invalid := PublicError{Category: ErrorCategory("secret-canary")}
	if got := invalid.Message(); strings.Contains(got, "secret-canary") {
		t.Fatalf("unknown category exposed input: %q", got)
	}
	if _, err := json.Marshal(invalid); err == nil || strings.Contains(err.Error(), "secret-canary") {
		t.Fatalf("unknown category must fail serialization without exposing input: %v", err)
	}
}

func TestInvalidStatusAndTimingEnumsDoNotSerializeRawValues(t *testing.T) {
	if got := Status("secret-canary").String(); got != "unknown" {
		t.Fatalf("unknown status String() = %q, want %q", got, "unknown")
	}
	for name, value := range map[string]any{
		"status": Status("secret-canary"),
		"timing": TimingState("secret-canary"),
	} {
		t.Run(name, func(t *testing.T) {
			if _, err := json.Marshal(value); err == nil || strings.Contains(err.Error(), "secret-canary") {
				t.Fatalf("invalid %s must fail serialization without exposing input: %v", name, err)
			}
		})
	}
}

func metadataName(metadata ResultMetadata) string {
	return "truncated=" + boolName(metadata.Truncated) +
		",redacted=" + boolName(metadata.Redacted) +
		",withheld=" + boolName(metadata.Withheld)
}

func boolName(value bool) string {
	if value {
		return "true"
	}
	return "false"
}
