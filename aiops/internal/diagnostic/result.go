package diagnostic

import (
	"encoding/json"
	"errors"
	"time"
)

const (
	// ResultSchemaVersion identifies the JSON contract defined by this package.
	ResultSchemaVersion = "1"

	// MaxPublicErrorMessageBytes bounds the fixed human-readable error messages.
	MaxPublicErrorMessageBytes = 64
)

var (
	errInvalidStatus        = errors.New("invalid diagnostic status")
	errInvalidFieldState    = errors.New("invalid diagnostic field state")
	errInvalidErrorCategory = errors.New("invalid diagnostic error category")
	errInvalidTimingState   = errors.New("invalid diagnostic timing state")
)

// Status describes the outcome of collecting evidence, not resource health or
// investigation lifecycle. Its JSON representation is one of the eight values
// defined below.
type Status string

const (
	StatusOK              Status = "ok"
	StatusPartial         Status = "partial"
	StatusError           Status = "error"
	StatusDenied          Status = "denied"
	StatusValidationError Status = "validation_error"
	StatusTimeout         Status = "timeout"
	StatusCancelled       Status = "cancelled"
	StatusUnavailable     Status = "unavailable"
)

func (status Status) String() string {
	if !validStatus(string(status)) {
		return "unknown"
	}
	return string(status)
}

func (status Status) MarshalJSON() ([]byte, error) {
	return marshalEnum(string(status), validStatus(string(status)), errInvalidStatus)
}

func (status *Status) UnmarshalJSON(data []byte) error {
	value, err := unmarshalEnum(data, validStatus, errInvalidStatus)
	if err != nil {
		return err
	}
	*status = Status(value)
	return nil
}

func validStatus(value string) bool {
	switch Status(value) {
	case StatusOK, StatusPartial, StatusError, StatusDenied,
		StatusValidationError, StatusTimeout, StatusCancelled, StatusUnavailable:
		return true
	default:
		return false
	}
}

// FieldState reports whether one logical result field was available. It is
// separate from the overall Status; unavailable or denied fields are never
// represented as empty, successful values.
type FieldState string

const (
	FieldAvailable     FieldState = "available"
	FieldDenied        FieldState = "denied"
	FieldUnavailable   FieldState = "unavailable"
	FieldNotApplicable FieldState = "not-applicable"
)

func (state FieldState) MarshalJSON() ([]byte, error) {
	return marshalEnum(string(state), validFieldState(string(state)), errInvalidFieldState)
}

func (state *FieldState) UnmarshalJSON(data []byte) error {
	value, err := unmarshalEnum(data, validFieldState, errInvalidFieldState)
	if err != nil {
		return err
	}
	*state = FieldState(value)
	return nil
}

func validFieldState(value string) bool {
	switch FieldState(value) {
	case FieldAvailable, FieldDenied, FieldUnavailable, FieldNotApplicable:
		return true
	default:
		return false
	}
}

// ErrorCategory selects a fixed public message. It cannot carry raw SDK, HTTP,
// filesystem, or debug error text.
type ErrorCategory string

const (
	ErrorCategoryValidation    ErrorCategory = "validation"
	ErrorCategoryAuthorization ErrorCategory = "authorization"
	ErrorCategoryUnavailable   ErrorCategory = "unavailable"
	ErrorCategoryTimeout       ErrorCategory = "timeout"
	ErrorCategoryCancelled     ErrorCategory = "cancelled"
	ErrorCategoryCollection    ErrorCategory = "collection"
	ErrorCategoryIntegrity     ErrorCategory = "integrity"
	ErrorCategoryInternal      ErrorCategory = "internal"
)

func (category ErrorCategory) MarshalJSON() ([]byte, error) {
	return marshalEnum(string(category), validErrorCategory(string(category)), errInvalidErrorCategory)
}

func (category *ErrorCategory) UnmarshalJSON(data []byte) error {
	value, err := unmarshalEnum(data, validErrorCategory, errInvalidErrorCategory)
	if err != nil {
		return err
	}
	*category = ErrorCategory(value)
	return nil
}

func validErrorCategory(value string) bool {
	switch ErrorCategory(value) {
	case ErrorCategoryValidation, ErrorCategoryAuthorization, ErrorCategoryUnavailable,
		ErrorCategoryTimeout, ErrorCategoryCancelled, ErrorCategoryCollection,
		ErrorCategoryIntegrity, ErrorCategoryInternal:
		return true
	default:
		return false
	}
}

// PublicError is deliberately limited to a safe category; it has no free-form
// message or underlying error field. Message returns a fixed bounded summary for
// human presentation.
type PublicError struct {
	Category ErrorCategory `json:"category"`
}

func (publicError PublicError) Message() string {
	switch publicError.Category {
	case ErrorCategoryValidation:
		return "The diagnostic request is invalid."
	case ErrorCategoryAuthorization:
		return "The diagnostic request is not authorized."
	case ErrorCategoryUnavailable:
		return "The diagnostic capability is unavailable."
	case ErrorCategoryTimeout:
		return "The diagnostic timed out."
	case ErrorCategoryCancelled:
		return "The diagnostic was cancelled."
	case ErrorCategoryCollection:
		return "The diagnostic collection failed."
	case ErrorCategoryIntegrity:
		return "The result could not be safely reported."
	default:
		return "The diagnostic failed."
	}
}

// TargetIdentity preserves the operator's original identifier and, when
// resolution occurred, the resolved resource identity.
type TargetIdentity struct {
	Original string          `json:"original"`
	Resolved *ResolvedTarget `json:"resolved,omitempty"`
}

// ResolvedTarget identifies the resource selected by a bounded authorized
// resolution. Either identifier may be absent when the source does not expose it.
type ResolvedTarget struct {
	ID   string `json:"id,omitempty"`
	Name string `json:"name,omitempty"`
}

// EvidenceReference links the result to an evidence record without embedding
// that record's content.
type EvidenceReference struct {
	ID string `json:"id"`
}

// TimingState distinguishes measured collection timing from a request for which
// collection duration does not apply. Not-applicable timing is never encoded as
// a fabricated zero duration.
type TimingState string

const (
	TimingMeasured      TimingState = "measured"
	TimingNotApplicable TimingState = "not-applicable"
)

func (state TimingState) MarshalJSON() ([]byte, error) {
	return marshalEnum(string(state), validTimingState(string(state)), errInvalidTimingState)
}

func (state *TimingState) UnmarshalJSON(data []byte) error {
	value, err := unmarshalEnum(data, validTimingState, errInvalidTimingState)
	if err != nil {
		return err
	}
	*state = TimingState(value)
	return nil
}

func validTimingState(value string) bool {
	switch TimingState(value) {
	case TimingMeasured, TimingNotApplicable:
		return true
	default:
		return false
	}
}

// CollectionTiming records collection timestamps and duration when measured,
// or an explicit not-applicable state when no collection duration exists.
type CollectionTiming struct {
	State      TimingState `json:"state"`
	StartedAt  *time.Time  `json:"started_at,omitempty"`
	EndedAt    *time.Time  `json:"ended_at,omitempty"`
	DurationNS *int64      `json:"duration_ns,omitempty"`
}

// FieldOutcome describes availability only. Payload values are intentionally
// absent until the separately reviewed sanitization contract is implemented.
type FieldOutcome struct {
	Name  string       `json:"name"`
	State FieldState   `json:"state"`
	Error *PublicError `json:"error,omitempty"`
}

// ResultMetadata keeps transformation and disclosure facts independent from
// Status. In particular, truncation, redaction, and withholding are not encoded
// as substitutes for a collection outcome.
type ResultMetadata struct {
	Truncated bool `json:"truncated"`
	Redacted  bool `json:"redacted"`
	Withheld  bool `json:"withheld"`
}

// Provenance binds a result to its request, tool/version, correlation, target,
// collection timing, and any related evidence records.
type Provenance struct {
	RequestID     string              `json:"request_id"`
	ToolName      string              `json:"tool_name"`
	ToolVersion   string              `json:"tool_version"`
	CorrelationID string              `json:"correlation_id"`
	Target        *TargetIdentity     `json:"target,omitempty"`
	Timing        CollectionTiming    `json:"timing"`
	Evidence      []EvidenceReference `json:"evidence,omitempty"`
}

// Result is the versioned logical result envelope. Status denotes collection
// outcome only; it does not claim health, root cause, or investigation state.
// JSON fields provide the machine-readable contract. Human output uses the
// status spelling and fixed PublicError.Message values, with gaps and metadata
// kept explicit. This package adds no output sink or payload serializer.
type Result struct {
	SchemaVersion string         `json:"schema_version"`
	Status        Status         `json:"status"`
	Provenance    Provenance     `json:"provenance"`
	Fields        []FieldOutcome `json:"fields,omitempty"`
	Error         *PublicError   `json:"error,omitempty"`
	Metadata      ResultMetadata `json:"metadata"`
}

func marshalEnum(value string, valid bool, invalid error) ([]byte, error) {
	if !valid {
		return nil, invalid
	}
	return json.Marshal(value)
}

func unmarshalEnum(data []byte, valid func(string) bool, invalid error) (string, error) {
	var value string
	if err := json.Unmarshal(data, &value); err != nil || !valid(value) {
		return "", invalid
	}
	return value, nil
}
