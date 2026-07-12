#!/usr/bin/env python3
"""Pure fail-closed redaction for reviewed Responses API request payloads."""

from __future__ import annotations

import json
import math
import re
import uuid
from collections import Counter
from dataclasses import dataclass
from typing import Any

REDACTION_MARKER = "[REDACTED]"
SCHEMA_VERSION = 1

IDENTITY_FIELD_NAMES = frozenset({"user", "username", "group", "groupname"})
SECRET_FIELD_NAMES = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "token",
        "apikey",
        "privatekey",
        "credential",
    }
)
UNSUPPORTED_FIELD_NAMES = frozenset(
    {
        "audio",
        "binary",
        "compressed",
        "compression",
        "contentencoding",
        "file",
        "fileupload",
        "image",
        "multipart",
    }
)
UNSUPPORTED_INPUT_TYPES = frozenset(
    {"inputaudio", "inputfile", "inputimage", "audio", "file", "image"}
)

_LABEL_PATTERN = (
    r"(?:username|user[_-]?name|group|group[_-]?name|password|passwd|secret|"
    r"token|api[_-]?key|private[_-]?key|credential)"
)
SENSITIVE_LABEL_RE = re.compile(rf"\b{_LABEL_PATTERN}\b", re.IGNORECASE)
CANONICAL_TEXT_RE = re.compile(
    rf"(?P<label>{_LABEL_PATTERN})(?P<space_before>\s*)(?P<separator>[=:])"
    r"(?P<space_after>\s*)(?P<value>[^\s,;]+)",
    re.IGNORECASE,
)


class RedactionError(ValueError):
    """Base error for a request that cannot be redacted safely."""


class DuplicateKeyError(RedactionError):
    """Raised when JSON duplicate keys make field policy ambiguous."""


class MalformedJsonError(RedactionError):
    """Raised when a JSON value cannot be parsed deterministically."""


class AmbiguousSensitiveLabelError(RedactionError):
    """Raised with fixed metadata when a sensitive text label is ambiguous."""

    def __init__(self, reason: str, label_category: str) -> None:
        if reason not in {"json_like_text", "plain_text_label"}:
            raise ValueError("unsupported ambiguity reason")
        if label_category not in {"identity", "secret"}:
            raise ValueError("unsupported ambiguity label category")
        self.reason = reason
        self.label_category = label_category
        super().__init__("ambiguous sensitive label")


class UnsupportedContentError(RedactionError):
    """Raised for binary or unreviewed provider content."""


@dataclass(frozen=True)
class RedactionResult:
    """A redacted payload and non-sensitive processing metadata only."""

    payload: dict[str, Any]
    redaction_counts: dict[str, int]
    classification_status: str
    schema_version: int
    correlation_id: str


@dataclass(frozen=True)
class LeakScanResult:
    """Non-sensitive proof that a rebuilt payload passed the local leak scan."""

    redaction_counts: dict[str, int]
    classification_status: str
    schema_version: int
    correlation_id: str


def normalize_field_name(name: str) -> str:
    """Normalize reviewed JSON field-name aliases without accepting arbitrary labels."""
    if not isinstance(name, str):
        raise UnsupportedContentError("JSON object keys must be strings")
    return re.sub(r"[^a-z0-9]", "", name.casefold())


def strict_json_loads(raw: str | bytes | bytearray) -> Any:
    """Parse JSON while rejecting duplicate keys instead of silently overwriting them."""

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise DuplicateKeyError("duplicate JSON key")
            result[key] = value
        return result

    try:
        return json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except DuplicateKeyError:
        raise
    except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MalformedJsonError("malformed JSON") from exc


def redact_remote_payload(
    payload: dict[str, Any], *, schema_version: int = SCHEMA_VERSION
) -> RedactionResult:
    """Return a new redacted payload or fail before any caller can transmit it."""
    if not isinstance(payload, dict):
        raise UnsupportedContentError("provider payload must be a JSON object")
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        raise RedactionError("schema version must be an integer")

    _assert_supported_content(payload)
    sensitive_values = _collect_sensitive_values(payload)
    counts: Counter[str] = Counter()
    redacted = _redact_value(payload, sensitive_values, counts)
    if not isinstance(redacted, dict):
        raise UnsupportedContentError("provider payload must remain a JSON object")

    return RedactionResult(
        payload=redacted,
        redaction_counts=dict(sorted(counts.items())),
        classification_status="redacted" if counts else "clear",
        schema_version=schema_version,
        correlation_id=str(uuid.uuid4()),
    )


def scan_redacted_payload(
    original_payload: dict[str, Any], result: RedactionResult
) -> LeakScanResult:
    """Reject rebuilt payloads that retain protected fields or discovered values."""
    if not isinstance(original_payload, dict) or not isinstance(result.payload, dict):
        raise RedactionError("redaction leak scan requires JSON objects")

    sensitive_values = _collect_sensitive_values(original_payload)
    for value in _iter_string_values(result.payload):
        if any(sensitive in value for sensitive in sensitive_values):
            raise RedactionError("redacted payload retains a protected value")
    _assert_protected_fields_redacted(result.payload)

    return LeakScanResult(
        redaction_counts=result.redaction_counts,
        classification_status=result.classification_status,
        schema_version=result.schema_version,
        correlation_id=result.correlation_id,
    )


def _iter_string_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _iter_string_values(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_string_values(item)


def _assert_protected_fields_redacted(value: Any) -> None:
    if isinstance(value, list):
        for item in value:
            _assert_protected_fields_redacted(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if _field_category(key) is not None and item != REDACTION_MARKER:
                raise RedactionError("redacted payload retains a protected field")
            _assert_protected_fields_redacted(item)


def _assert_supported_content(value: Any) -> None:
    if isinstance(value, (bytes, bytearray, memoryview, tuple, set)):
        raise UnsupportedContentError("binary or non-JSON content is not supported")
    if isinstance(value, float) and not math.isfinite(value):
        raise UnsupportedContentError("non-finite JSON numbers are not supported")
    if isinstance(value, list):
        for item in value:
            _assert_supported_content(item)
        return
    if not isinstance(value, dict):
        return

    for key, child in value.items():
        normalized_key = normalize_field_name(key)
        if normalized_key in UNSUPPORTED_FIELD_NAMES:
            raise UnsupportedContentError("unsupported provider content field")
        if normalized_key == "type" and isinstance(child, str):
            if normalize_field_name(child) in UNSUPPORTED_INPUT_TYPES:
                raise UnsupportedContentError("unsupported provider input type")
        _assert_supported_content(child)


def _collect_sensitive_values(value: Any) -> set[str]:
    collected: set[str] = set()

    def collect_string_leaves(candidate: Any) -> None:
        if isinstance(candidate, str) and candidate:
            collected.add(candidate)
        elif isinstance(candidate, list):
            for item in candidate:
                collect_string_leaves(item)
        elif isinstance(candidate, dict):
            for nested in candidate.values():
                collect_string_leaves(nested)

    def visit(candidate: Any) -> None:
        if isinstance(candidate, list):
            for item in candidate:
                visit(item)
        elif isinstance(candidate, dict):
            for key, nested in candidate.items():
                if (
                    normalize_field_name(key)
                    in IDENTITY_FIELD_NAMES | SECRET_FIELD_NAMES
                ):
                    collect_string_leaves(nested)
                visit(nested)

    visit(value)
    return collected


def _field_category(key: str) -> str | None:
    normalized_key = normalize_field_name(key)
    if normalized_key in IDENTITY_FIELD_NAMES:
        return "identity"
    if normalized_key in SECRET_FIELD_NAMES:
        return "secret"
    return None


def _ambiguous_label_error(reason: str, text: str) -> AmbiguousSensitiveLabelError:
    match = SENSITIVE_LABEL_RE.search(text)
    if match is None:
        raise RedactionError("sensitive label classification is absent")
    label_category = _field_category(match.group(0))
    if label_category is None:
        raise RedactionError("sensitive label category is unreviewed")
    return AmbiguousSensitiveLabelError(reason, label_category)


def _redact_value(value: Any, sensitive_values: set[str], counts: Counter[str]) -> Any:
    if isinstance(value, list):
        return [_redact_value(item, sensitive_values, counts) for item in value]
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, nested in value.items():
            category = _field_category(key)
            if category is not None:
                counts[category] += 1
                redacted[key] = REDACTION_MARKER
            else:
                redacted[key] = _redact_value(nested, sensitive_values, counts)
        return redacted
    if isinstance(value, str):
        return _redact_text(value, sensitive_values, counts)
    return value


def _redact_text(text: str, sensitive_values: set[str], counts: Counter[str]) -> str:
    stripped = text.strip()
    if stripped.startswith(("{", "[")):
        try:
            embedded = strict_json_loads(stripped)
        except MalformedJsonError:
            if SENSITIVE_LABEL_RE.search(text):
                raise _ambiguous_label_error("json_like_text", text)
        else:
            if not isinstance(embedded, (dict, list)):
                raise UnsupportedContentError(
                    "embedded JSON must be an object or array"
                )
            counts["embedded_json"] += 1
            return json.dumps(
                _redact_value(embedded, sensitive_values, counts),
                sort_keys=True,
                separators=(",", ":"),
            )

    matches = list(CANONICAL_TEXT_RE.finditer(text))
    canonical_label_ranges = [match.span("label") for match in matches]
    for label_match in SENSITIVE_LABEL_RE.finditer(text):
        if not any(
            start <= label_match.start() and label_match.end() <= end
            for start, end in canonical_label_ranges
        ):
            raise _ambiguous_label_error("plain_text_label", label_match.group(0))

    pieces: list[str] = []
    cursor = 0
    for match in matches:
        pieces.append(text[cursor : match.start()])
        pieces.append(
            "".join(
                (
                    match.group("label"),
                    match.group("space_before"),
                    match.group("separator"),
                    match.group("space_after"),
                    REDACTION_MARKER,
                )
            )
        )
        cursor = match.end()
        counts["canonical_text"] += 1
    redacted = "".join(pieces) + text[cursor:]

    for sensitive_value in sorted(sensitive_values, key=len, reverse=True):
        occurrences = redacted.count(sensitive_value)
        if occurrences:
            redacted = redacted.replace(sensitive_value, REDACTION_MARKER)
            counts["propagated_value"] += occurrences
    return redacted
