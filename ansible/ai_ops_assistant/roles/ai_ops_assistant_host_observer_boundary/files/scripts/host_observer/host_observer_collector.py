#!/usr/bin/env python3
"""Fail-closed host-observer collector boundary.

This boundary validates only closed request and synthetic policy/projection
metadata. It does not read host sources, policy files, projection files, or
invoke a transport. Valid requests intentionally return ``unavailable`` until
later chunks provide reviewed source adapters and an authorized connector.
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "1.0"
TOOL_NAME = "host_observer_collector"
METADATA_TOOL_NAME = "recent_metadata_errors"
METADATA_SECTION_NAME = "metadata_errors"
REQUEST_MAX_BYTES = 8192
SERIALIZED_OUTPUT_MAX_BYTES = 16_384
MAX_RECORDS = 20
MAX_RAW_SUMMARY_BYTES = 4_096
MAX_NORMALIZED_SUMMARY_BYTES = 512

SOURCE_CLASSES = frozenset(
    {
        "metadata",
        "neutron",
        "nova",
        "metadata_error_events",
        "neutron_error_events",
        "nova_error_events",
    }
)
WINDOW_CLASSES = frozenset({"15m", "30m", "1h"})
LINE_LIMIT_CLASSES = frozenset({"small", "medium", "large"})
WINDOW_DURATIONS = {"15m": 900, "30m": 1_800, "1h": 3_600}
LINE_LIMITS = {"small": 50, "medium": 100, "large": 200}
PROJECTION_FRESHNESS_CLASSES = frozenset({"current", "stale", "unknown"})
COLLECTOR_METADATA_PROJECTION_TYPE = "host_observer_metadata"

REQUEST_REQUIRED_FIELDS = {"schema_version", "host_label"}
REQUEST_OPTIONAL_FIELDS = {"source_class", "window_class", "line_limit_class"}
REQUEST_FIELDS = REQUEST_REQUIRED_FIELDS | REQUEST_OPTIONAL_FIELDS
METADATA_SOURCE_CLASS = "metadata_error_events"
METADATA_SERVICE_CLASS = "metadata"
METADATA_LOGICAL_SELECTOR = "metadata_service_errors"
METADATA_ROLE = "controller"
NEUTRON_TOOL_NAME = "recent_neutron_errors"
NEUTRON_SECTION_NAME = "neutron_errors"
NEUTRON_SOURCE_CLASS = "neutron_error_events"
NEUTRON_SERVICE_CLASS = "neutron"
NEUTRON_LOGICAL_SELECTOR = "neutron_service_errors"
NEUTRON_ROLE = "controller"
NOVA_TOOL_NAME = "recent_nova_errors"
NOVA_SECTION_NAME = "nova_errors"
NOVA_SOURCE_CLASS = "nova_error_events"
NOVA_SERVICE_CLASS = "nova"
NOVA_LOGICAL_SELECTOR = "nova_service_errors"
NOVA_ROLE = "controller"
SOURCE_RECORD_FIELDS = {
    "source_sequence",
    "observed_at",
    "severity",
    "event_class",
    "summary",
}
SEVERITY_PRIORITY = {"critical": 0, "error": 1, "warning": 2, "info": 3, "unknown": 4}
SEVERITIES = frozenset(SEVERITY_PRIORITY)
EVENT_CLASSES = frozenset(
    {
        "request_error",
        "connection_error",
        "timeout",
        "authentication_error",
        "dependency_error",
        "configuration_error",
        "unknown",
    }
)
COLLECTOR_METADATA_PROJECTION_FIELDS = {
    "schema_version",
    "projection_type",
    "revision",
    "freshness_class",
    "entries",
}
COLLECTOR_METADATA_PROJECTION_ENTRY_FIELDS = {
    "host_label",
    "inventory_role",
    "source_classes",
    "enabled",
}
POLICY_FIELDS = {
    "schema_version",
    "source_classes",
    "window_classes",
    "line_limit_classes",
    "metadata_status",
    "redaction_policy_status",
}

ERROR_MESSAGES = {
    "authorization_pending": "Host observation is unavailable.",
    "collector_stub": "Host observation collector is unavailable.",
    "invocation_denied": "Collector invocation is unavailable.",
    "validation_error": "Collector request is invalid.",
    "observer_integrity_error": "Observer metadata is unavailable.",
    "unsupported_deployment_state": "Observer deployment is unavailable.",
    "host_unavailable": "Approved host is unavailable.",
    "host_disabled": "Approved host is disabled.",
    "source_role_mismatch": "Approved source is unavailable for this host role.",
    "source_missing": "Approved source is missing.",
    "source_stale": "Approved source is stale.",
    "source_denied": "Approved source access is denied.",
    "malformed_source": "Approved source data is malformed.",
    "timeout": "Diagnostic exceeded its time limit.",
    "redaction_failure": "Diagnostic output could not be safely redacted.",
    "approved_optional_capability_absent": "Approved optional capability is unavailable.",
}


class CollectorValidationError(ValueError):
    """A request or metadata validation failure with a safe error class."""

    def __init__(self, error_class: str):
        super().__init__(error_class)
        self.error_class = error_class


class CollectorUnavailableError(CollectorValidationError):
    """A validated but unavailable projection or policy state."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CollectorValidationError("duplicate_field")
        result[key] = value
    return result


def _require_mapping(
    value: Any, error_class: str = "validation_error"
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CollectorValidationError(error_class)
    return value


def _require_string(value: Any, error_class: str = "validation_error") -> str:
    if not isinstance(value, str) or not value or len(value) > 128:
        raise CollectorValidationError(error_class)
    return value


def _require_closed_string(value: Any, allowed: frozenset[str]) -> str:
    text = _require_string(value)
    if text not in allowed:
        raise CollectorValidationError("unsupported_class")
    return text


def _validate_host_label(value: Any) -> str:
    label = _require_string(value)
    if len(label) > 64 or label[0] == "-" or label[-1] == "-":
        raise CollectorValidationError("unsafe_host_label")
    if any(
        character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in label
    ):
        raise CollectorValidationError("unsafe_host_label")
    return label


def parse_request(raw: bytes | str) -> dict[str, Any]:
    """Parse the closed collector request without reading any source."""

    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    if not isinstance(raw, bytes) or len(raw) > REQUEST_MAX_BYTES:
        raise CollectorValidationError("request_oversized")
    try:
        request = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except (UnicodeDecodeError, json.JSONDecodeError, CollectorValidationError):
        raise CollectorValidationError("validation_error") from None

    request = _require_mapping(request)
    if (
        not REQUEST_REQUIRED_FIELDS <= set(request)
        or not set(request) <= REQUEST_FIELDS
    ):
        raise CollectorValidationError("unknown_or_missing_field")
    if request["schema_version"] != SCHEMA_VERSION:
        raise CollectorValidationError("unsupported_schema")
    normalized = {
        "schema_version": SCHEMA_VERSION,
        "host_label": _validate_host_label(request["host_label"]),
        "source_class": (
            _require_closed_string(request["source_class"], SOURCE_CLASSES)
            if "source_class" in request
            else None
        ),
        "window_class": _require_closed_string(
            request.get("window_class", "30m"), WINDOW_CLASSES
        ),
        "line_limit_class": _require_closed_string(
            request.get("line_limit_class", "medium"), LINE_LIMIT_CLASSES
        ),
    }
    return normalized


def validate_projection_metadata(projection: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate non-secret projection metadata supplied by a synthetic caller."""

    projection = _require_mapping(projection, "observer_integrity_error")
    if (
        set(projection) != COLLECTOR_METADATA_PROJECTION_FIELDS
        or projection["schema_version"] != SCHEMA_VERSION
        or projection["projection_type"] != COLLECTOR_METADATA_PROJECTION_TYPE
    ):
        raise CollectorValidationError("observer_integrity_error")
    _require_string(projection["revision"], "observer_integrity_error")
    freshness = _require_closed_string(
        projection["freshness_class"], PROJECTION_FRESHNESS_CLASSES
    )
    if freshness != "current":
        raise CollectorUnavailableError("projection_stale")
    entries = projection["entries"]
    if not isinstance(entries, list) or not entries:
        raise CollectorUnavailableError("projection_unavailable")

    labels: set[str] = set()
    for entry in entries:
        entry = _require_mapping(entry, "observer_integrity_error")
        if set(entry) != COLLECTOR_METADATA_PROJECTION_ENTRY_FIELDS:
            raise CollectorValidationError("observer_integrity_error")
        label = _validate_host_label(entry["host_label"])
        if label in labels:
            raise CollectorValidationError("duplicate_projection_label")
        labels.add(label)
        _require_string(entry["inventory_role"], "observer_integrity_error")
        source_classes = entry["source_classes"]
        if (
            not isinstance(source_classes, list)
            or not source_classes
            or any(source not in SOURCE_CLASSES for source in source_classes)
            or len(set(source_classes)) != len(source_classes)
        ):
            raise CollectorValidationError("observer_integrity_error")
        if not isinstance(entry["enabled"], bool):
            raise CollectorValidationError("observer_integrity_error")
    return projection


def validate_policy_metadata(policy: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate synthetic policy metadata without reading a policy file."""

    policy = _require_mapping(policy, "observer_integrity_error")
    if set(policy) != POLICY_FIELDS or policy["schema_version"] != SCHEMA_VERSION:
        raise CollectorValidationError("observer_integrity_error")
    for field, allowed in (
        ("source_classes", SOURCE_CLASSES),
        ("window_classes", WINDOW_CLASSES),
        ("line_limit_classes", LINE_LIMIT_CLASSES),
    ):
        values = policy[field]
        if not isinstance(values, list) or not values or not set(values) <= allowed:
            raise CollectorValidationError("observer_integrity_error")
    if policy["metadata_status"] != "accepted":
        raise CollectorUnavailableError("unsupported_deployment_state")
    if policy["redaction_policy_status"] != "accepted":
        raise CollectorUnavailableError("unsupported_deployment_state")
    return policy


def resolve_projection(
    request: Mapping[str, Any], projection: Mapping[str, Any]
) -> Mapping[str, str]:
    """Resolve only non-secret projection metadata; never return a destination."""

    request = parse_request(json.dumps(dict(request), sort_keys=True))
    projection = validate_projection_metadata(projection)
    for entry in projection["entries"]:
        if entry["host_label"] != request["host_label"]:
            continue
        if not entry["enabled"]:
            raise CollectorUnavailableError("host_disabled")
        if request["source_class"] not in entry["source_classes"]:
            raise CollectorUnavailableError("source_role_mismatch")
        return {
            "host_label": entry["host_label"],
            "inventory_role": entry["inventory_role"],
            "source_class": request["source_class"],
        }
    raise CollectorUnavailableError("host_unavailable")


def validate_boundary(
    request: Mapping[str, Any],
    projection: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> Mapping[str, str]:
    """Validate all closed metadata and return no transport or source details."""

    request = parse_request(json.dumps(dict(request), sort_keys=True))
    policy = validate_policy_metadata(policy)
    if request["source_class"] not in policy["source_classes"]:
        raise CollectorUnavailableError("source_role_mismatch")
    if request["window_class"] not in policy["window_classes"]:
        raise CollectorUnavailableError("unsupported_class")
    if request["line_limit_class"] not in policy["line_limit_classes"]:
        raise CollectorUnavailableError("unsupported_class")
    return resolve_projection(request, projection)


METADATA_SOURCE_OUTCOMES = {
    "missing": "source_missing",
    "stale": "source_stale",
    "denied": "source_denied",
    "malformed": "malformed_source",
    "timeout": "timeout",
}


def _metadata_error_status(error_class: str) -> str:
    if error_class == "source_denied":
        return "denied"
    if error_class == "timeout":
        return "timeout"
    if error_class in {"malformed_source", "redaction_failure", "validation_error"}:
        return "error"
    return "unavailable"


def _metadata_error_document(error_class: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": METADATA_TOOL_NAME,
        "status": _metadata_error_status(error_class),
        "sections": [],
        "error": {
            "class": error_class,
            "message": ERROR_MESSAGES[error_class],
        },
    }


def _metadata_success_document(
    events: list[dict[str, str]], truncated: bool
) -> dict[str, Any]:
    section_status = "ok" if events else "empty"
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": METADATA_TOOL_NAME,
        "status": "ok",
        "sections": [
            {
                "name": METADATA_SECTION_NAME,
                "status": section_status,
                "data": events,
                "error": None,
                "truncated": truncated,
            }
        ],
        "error": None,
    }


def _parse_utc_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        if not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z",
            value,
        ):
            raise CollectorValidationError("malformed_source")
        try:
            parsed = datetime.fromisoformat(value[:-1] + "+00:00")
        except ValueError:
            raise CollectorValidationError("malformed_source") from None
    else:
        raise CollectorValidationError("malformed_source")
    if parsed.tzinfo is None:
        raise CollectorValidationError("malformed_source")
    return parsed.astimezone(timezone.utc)


def _canonical_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _normalize_summary(value: Any) -> str:
    if not isinstance(value, str):
        raise CollectorValidationError("malformed_source")
    try:
        if len(value.encode("utf-8")) > MAX_RAW_SUMMARY_BYTES:
            raise CollectorValidationError("malformed_source")
    except UnicodeEncodeError:
        raise CollectorValidationError("malformed_source") from None
    value = unicodedata.normalize("NFC", value)
    value = "".join(
        " " if ord(character) < 32 or ord(character) == 127 else character
        for character in value
    )
    value = " ".join(value.split())
    if not value:
        raise CollectorValidationError("malformed_source")
    return value


def _redact_assignment(match: re.Match[str]) -> str:
    return re.sub(r"([:=]).*", r"\1[REDACTED]", match.group(0), count=1)


_REDACTION_PATTERNS = (
    (
        re.compile(
            r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
            re.IGNORECASE | re.DOTALL,
        ),
        "[REDACTED]",
    ),
    (
        re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^@\s]+@[^/\s]+", re.IGNORECASE),
        "[REDACTED]",
    ),
    (re.compile(r"\bBearer\s+[^\s,;]+", re.IGNORECASE), "Bearer [REDACTED]"),
    (
        re.compile(
            r"\b(?:authorization|proxy-authorization)\s*[:=]\s*(?:bearer\s+)?[^\s,;]+",
            re.IGNORECASE,
        ),
        _redact_assignment,
    ),
    (
        re.compile(
            r"\b(?:password|passwd|passphrase|pwd|token|api[_-]?key|secret)\s*[:=]\s*[^\s,;]+",
            re.IGNORECASE,
        ),
        _redact_assignment,
    ),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[REDACTED]"),
    (
        re.compile(r"(?<![\w:])[0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{0,4}){2,7}(?![\w:])"),
        "[REDACTED]",
    ),
    (re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b"), "[REDACTED]"),
    (
        re.compile(
            r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[1-5][0-9A-Fa-f]{3}-[89ABab][0-9A-Fa-f]{3}-[0-9A-Fa-f]{12}\b"
        ),
        "[REDACTED]",
    ),
    (re.compile(r"\b[a-z0-9]+(?:[-.][a-z0-9]+)+\b", re.IGNORECASE), "[REDACTED]"),
)
_REDACTION_CANARY_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^@\s]+@[^/\s]+", re.IGNORECASE),
    re.compile(r"\bBearer\s+(?!\[REDACTED\])[^\s,;]+", re.IGNORECASE),
    re.compile(
        r"\b(?:authorization|proxy-authorization)\s*[:=]\s*(?!\[REDACTED\])[^\s,;]+",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:password|passwd|passphrase|pwd|token|api[_-]?key|secret)\s*[:=]\s*(?!\[REDACTED\])[^\s,;]+",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    re.compile(r"(?<![\w:])[0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{0,4}){2,7}(?![\w:])"),
    re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b"),
    re.compile(
        r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[1-5][0-9A-Fa-f]{3}-[89ABab][0-9A-Fa-f]{3}-[0-9A-Fa-f]{12}\b"
    ),
    re.compile(r"\b[a-z0-9]+(?:[-.][a-z0-9]+)+\b", re.IGNORECASE),
)


def redact_summary(summary: str) -> str:
    """Redact fixed secret, address, identifier, and host-like canaries."""

    if summary == "__REDACTION_FAILURE__":
        raise CollectorValidationError("redaction_failure")
    redacted = summary
    for pattern, replacement in _REDACTION_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    if any(pattern.search(redacted) for pattern in _REDACTION_CANARY_PATTERNS):
        raise CollectorValidationError("redaction_failure")
    return redacted


def _truncate_utf8(value: str, maximum_bytes: int) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= maximum_bytes:
        return value
    return encoded[:maximum_bytes].decode("utf-8", errors="ignore")


def _source_outcome(source_records: Any) -> str | None:
    if source_records is None:
        return "source_missing"
    if isinstance(source_records, str):
        return METADATA_SOURCE_OUTCOMES.get(source_records)
    if isinstance(source_records, Mapping) and set(source_records) in (
        {"outcome"},
        {"status"},
    ):
        outcome = source_records.get("outcome", source_records.get("status"))
        if isinstance(outcome, str):
            return METADATA_SOURCE_OUTCOMES.get(outcome)
    return None


def collect_metadata_slice(
    source_records: Sequence[Mapping[str, Any]] | Mapping[str, Any] | str | None,
    source_truncated: bool,
    freshness_class: str,
    host_label: str,
    inventory_role: str,
    window_class: str,
    line_limit_class: str,
    collection_started_at: datetime | str,
) -> dict[str, Any]:
    """Collect one bounded, synthetic metadata evidence slice."""

    if freshness_class != "current":
        return _metadata_error_document("source_stale")
    if inventory_role != METADATA_ROLE:
        return _metadata_error_document("source_role_mismatch")

    try:
        host_label = _validate_host_label(host_label)
        window_class = _require_closed_string(window_class, WINDOW_CLASSES)
        line_limit_class = _require_closed_string(line_limit_class, LINE_LIMIT_CLASSES)
        if not isinstance(source_truncated, bool):
            raise CollectorValidationError("malformed_source")
        collection_start = _parse_utc_timestamp(collection_started_at)
        source_error = _source_outcome(source_records)
        if source_error is not None:
            return _metadata_error_document(source_error)
        if not isinstance(source_records, (list, tuple)):
            raise CollectorValidationError("malformed_source")

        line_limit = LINE_LIMITS[line_limit_class]
        bounded_records = source_records[:line_limit]
        truncated = source_truncated or len(source_records) > line_limit
        earliest_allowed = collection_start - timedelta(
            seconds=WINDOW_DURATIONS[window_class]
        )
        prepared_records: list[dict[str, Any]] = []
        for record in bounded_records:
            if not isinstance(record, Mapping) or set(record) != SOURCE_RECORD_FIELDS:
                raise CollectorValidationError("malformed_source")
            sequence = record["source_sequence"]
            if (
                isinstance(sequence, bool)
                or not isinstance(sequence, int)
                or sequence < 0
            ):
                raise CollectorValidationError("malformed_source")
            if not isinstance(record["observed_at"], str):
                raise CollectorValidationError("malformed_source")
            observed_at = _parse_utc_timestamp(record["observed_at"])
            if observed_at > collection_start:
                raise CollectorValidationError("malformed_source")
            summary = _normalize_summary(record["summary"])
            severity = record["severity"]
            event_class = record["event_class"]
            if not isinstance(severity, str) or not isinstance(event_class, str):
                raise CollectorValidationError("malformed_source")
            prepared_records.append(
                {
                    "source_sequence": sequence,
                    "observed_at": observed_at,
                    "severity": severity if severity in SEVERITIES else "unknown",
                    "event_class": (
                        event_class if event_class in EVENT_CLASSES else "unknown"
                    ),
                    "summary": summary,
                }
            )

        prepared_records = [
            record
            for record in prepared_records
            if earliest_allowed <= record["observed_at"] <= collection_start
        ]
        prepared_records.sort(
            key=lambda record: (
                -record["observed_at"].timestamp(),
                SEVERITY_PRIORITY[record["severity"]],
                record["event_class"],
                record["source_sequence"],
            )
        )
        if len(prepared_records) > MAX_RECORDS:
            prepared_records = prepared_records[:MAX_RECORDS]
            truncated = True

        events: list[dict[str, str]] = []
        try:
            for record in prepared_records:
                redacted_summary = redact_summary(record["summary"])
                redacted_summary = _truncate_utf8(
                    redacted_summary, MAX_NORMALIZED_SUMMARY_BYTES
                )
                events.append(
                    {
                        "host_label": host_label,
                        "inventory_role": METADATA_ROLE,
                        "source_class": METADATA_SOURCE_CLASS,
                        "service_class": METADATA_SERVICE_CLASS,
                        "observed_at": _canonical_timestamp(record["observed_at"]),
                        "severity": record["severity"],
                        "event_class": record["event_class"],
                        "redacted_summary": redacted_summary,
                    }
                )
        except Exception as error:
            if (
                isinstance(error, CollectorValidationError)
                and error.error_class != "redaction_failure"
            ):
                raise
            raise CollectorValidationError("redaction_failure") from None

        document = _metadata_success_document(events, truncated)
        while (
            len(
                (
                    json.dumps(
                        document,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    + "\n"
                ).encode("utf-8")
            )
            > SERIALIZED_OUTPUT_MAX_BYTES
            and document["sections"][0]["data"]
        ):
            document["sections"][0]["data"].pop()
            document["sections"][0]["truncated"] = True
        return document
    except CollectorValidationError as error:
        error_class = error.error_class
        if error_class not in ERROR_MESSAGES:
            error_class = "malformed_source"
        return _metadata_error_document(error_class)


def _with_diagnostic_identity(
    document: dict[str, Any],
    tool_name: str,
    section_name: str,
    source_class: str,
    service_class: str,
) -> dict[str, Any]:
    """Apply one fixed diagnostic identity without exposing a selector."""

    document["tool"] = tool_name
    if document["sections"]:
        section = document["sections"][0]
        section["name"] = section_name
        for event in section["data"]:
            event["source_class"] = source_class
            event["service_class"] = service_class
    return document


def collect_neutron_slice(
    source_records: Sequence[Mapping[str, Any]] | Mapping[str, Any] | str | None,
    source_truncated: bool,
    freshness_class: str,
    host_label: str,
    inventory_role: str,
    window_class: str,
    line_limit_class: str,
    collection_started_at: datetime | str,
) -> dict[str, Any]:
    """Collect one bounded, synthetic Neutron evidence slice."""

    document = collect_metadata_slice(
        source_records,
        source_truncated,
        freshness_class,
        host_label,
        inventory_role,
        window_class,
        line_limit_class,
        collection_started_at,
    )
    return _with_diagnostic_identity(
        document,
        NEUTRON_TOOL_NAME,
        NEUTRON_SECTION_NAME,
        NEUTRON_SOURCE_CLASS,
        NEUTRON_SERVICE_CLASS,
    )


def collect_nova_slice(
    source_records: Sequence[Mapping[str, Any]] | Mapping[str, Any] | str | None,
    source_truncated: bool,
    freshness_class: str,
    host_label: str,
    inventory_role: str,
    window_class: str,
    line_limit_class: str,
    collection_started_at: datetime | str,
) -> dict[str, Any]:
    """Collect one bounded, synthetic Nova evidence slice."""

    document = collect_metadata_slice(
        source_records,
        source_truncated,
        freshness_class,
        host_label,
        inventory_role,
        window_class,
        line_limit_class,
        collection_started_at,
    )
    return _with_diagnostic_identity(
        document,
        NOVA_TOOL_NAME,
        NOVA_SECTION_NAME,
        NOVA_SOURCE_CLASS,
        NOVA_SERVICE_CLASS,
    )


def unavailable_document(error_class: str = "collector_stub") -> dict[str, Any]:
    """Return the deterministic non-success document for the compile-safe stub."""

    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL_NAME,
        "status": "unavailable",
        "sections": [],
        "error": {
            "class": error_class,
            "message": ERROR_MESSAGES.get(
                error_class, "host observation is unavailable"
            ),
        },
    }


def error_document(error_class: str) -> dict[str, Any]:
    return {
        **unavailable_document(error_class),
        "status": "error",
    }


def run(
    argv: list[str] | tuple[str, ...] = (),
    environment: Mapping[str, str] | None = None,
    raw_request: bytes = b"",
) -> tuple[int, dict[str, Any]]:
    """Run the boundary without opening files, sockets, or child processes."""

    environment = {} if environment is None else environment
    if argv or environment.get("SSH_ORIGINAL_COMMAND", ""):
        return 2, error_document("invocation_denied")
    try:
        parse_request(raw_request)
    except CollectorValidationError as error:
        return 2, error_document("validation_error")
    return 5, unavailable_document("authorization_pending")


def main() -> int:
    raw_request = sys.stdin.buffer.read(REQUEST_MAX_BYTES + 1)
    exit_code, document = run(tuple(sys.argv[1:]), os.environ, raw_request)
    sys.stdout.write(json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
