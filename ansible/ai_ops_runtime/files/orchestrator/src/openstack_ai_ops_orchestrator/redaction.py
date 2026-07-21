"""Pure fail-closed redaction at the orchestrator's pre-model boundary."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from .contracts import SafeToolResult, ToolResultCategory

REDACTION_MARKER: Final = "[REDACTED]"


class RedactionCategory(StrEnum):
    """Non-sensitive classifications produced by this boundary."""

    CLEAR = "clear"
    REDACTED = "redacted"


class RedactionError(ValueError):
    """Fixed-category error that never includes rejected content."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)


class _DuplicateKeyError(RedactionError):
    def __init__(self) -> None:
        super().__init__("duplicate_json_key")


type JsonValue = (
    None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
)


@dataclass(frozen=True, slots=True)
class RedactedContent:
    """Bounded, leak-scanned content and aggregate redaction metadata."""

    content: str
    classification: RedactionCategory
    redaction_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise ValueError("redacted content must be text")
        if not isinstance(self.classification, RedactionCategory):
            raise ValueError("redaction classification is invalid")
        if isinstance(self.redaction_count, bool) or self.redaction_count < 0:
            raise ValueError("redaction count is invalid")


_IDENTITY_FIELDS: Final = frozenset({"user", "username", "group", "groupname"})
_SECRET_FIELDS: Final = frozenset(
    {"password", "passwd", "secret", "token", "apikey", "privatekey", "credential"}
)
_UNSUPPORTED_FIELDS: Final = frozenset(
    {"audio", "binary", "compressed", "compression", "contentencoding", "file", "image"}
)
_LABEL = (
    r"username|user[_-]?name|group|group[_-]?name|password|passwd|secret|"
    r"token|api[_-]?key|private[_-]?key|credential"
)
_SENSITIVE_LABEL_RE = re.compile(rf"\b(?:{_LABEL})\b", re.IGNORECASE)
_CANONICAL_TEXT_RE = re.compile(
    rf"(?P<label>{_LABEL})(?P<before>\s*)(?P<separator>[=:])(?P<after>\s*)"
    r"(?P<value>[^\s,;]+)",
    re.IGNORECASE,
)


def redact_operator_context(
    context: str, maximum_bytes: int, maximum_redactions: int
) -> RedactedContent:
    """Validate, redact, and leak-scan operator-provided text."""
    _validate_text_bounds(context, maximum_bytes)
    redacted, count = _redact_text(context, set())
    _validate_result(redacted, count, maximum_bytes, maximum_redactions, set())
    return RedactedContent(
        content=redacted,
        classification=RedactionCategory.REDACTED if count else RedactionCategory.CLEAR,
        redaction_count=count,
    )


def redact_tool_result(
    raw_result: Mapping[str, object],
    *,
    maximum_raw_bytes: int,
    maximum_content_bytes: int,
    maximum_redactions: int,
) -> SafeToolResult:
    """Convert an exact, tainted internal envelope into a safe tool result."""
    expected = {
        "tool_name",
        "category",
        "content",
        "truncated",
        "request_sequence_number",
    }
    if not isinstance(raw_result, Mapping) or set(raw_result) != expected:
        raise RedactionError("invalid_tool_result")
    tool_name = raw_result["tool_name"]
    category_value = raw_result["category"]
    content = raw_result["content"]
    truncated = raw_result["truncated"]
    sequence = raw_result["request_sequence_number"]
    if (
        not isinstance(tool_name, str)
        or not tool_name
        or not isinstance(category_value, str)
        or not isinstance(content, str)
        or not isinstance(truncated, bool)
        or isinstance(sequence, bool)
        or not isinstance(sequence, int)
        or sequence < 1
    ):
        raise RedactionError("invalid_tool_result")
    try:
        category = ToolResultCategory(category_value)
    except ValueError as error:
        raise RedactionError("invalid_tool_result") from error
    _validate_text_bounds(content, maximum_raw_bytes)
    if not content.lstrip().startswith(("{", "[")):
        raise RedactionError("unsupported_content")
    redacted, count = _redact_text(content, set())
    _validate_result(redacted, count, maximum_content_bytes, maximum_redactions, set())
    return SafeToolResult._from_validated(
        tool_name=tool_name,
        category=category,
        redacted_content=redacted,
        truncated=truncated,
        content_bytes=len(redacted.encode("utf-8")),
        redaction_count=count,
        request_sequence_number=sequence,
    )


def strict_json_loads(raw: str) -> JsonValue:
    """Parse JSON without duplicate keys or non-finite numeric constants."""
    if not isinstance(raw, str):
        raise RedactionError("malformed_json")

    def reject_duplicates(pairs: list[tuple[str, JsonValue]]) -> dict[str, JsonValue]:
        parsed: dict[str, JsonValue] = {}
        for key, value in pairs:
            if key in parsed:
                raise _DuplicateKeyError()
            parsed[key] = value
        return parsed

    def reject_constant(_value: str) -> JsonValue:
        raise RedactionError("non_finite_json_number")

    try:
        value = json.loads(
            raw, object_pairs_hook=reject_duplicates, parse_constant=reject_constant
        )
    except RedactionError:
        raise
    except (TypeError, json.JSONDecodeError) as error:
        raise RedactionError("malformed_json") from error
    _validate_json_value(value)
    return value


def leak_scan(content: str, protected_values: set[str]) -> None:
    """Reject a rebuilt value retaining a protected value or sensitive label."""
    if not isinstance(content, str):
        raise RedactionError("invalid_redacted_content")
    if any(value and value in content for value in protected_values):
        raise RedactionError("redaction_leak")
    for match in _CANONICAL_TEXT_RE.finditer(content):
        if match.group("value") != REDACTION_MARKER:
            raise RedactionError("redaction_leak")


def _validate_text_bounds(value: str, maximum_bytes: int) -> None:
    if (
        not isinstance(value, str)
        or isinstance(maximum_bytes, bool)
        or maximum_bytes < 1
    ):
        raise RedactionError("invalid_content")
    if len(value.encode("utf-8")) > maximum_bytes:
        raise RedactionError("content_too_large")


def _validate_result(
    redacted: str,
    count: int,
    maximum_bytes: int,
    maximum_redactions: int,
    protected_values: set[str],
) -> None:
    _validate_text_bounds(redacted, maximum_bytes)
    if isinstance(maximum_redactions, bool) or maximum_redactions < 1:
        raise RedactionError("invalid_redaction_limit")
    if count > maximum_redactions:
        raise RedactionError("redaction_limit_exceeded")
    leak_scan(redacted, protected_values)


def _normalize(name: str) -> str:
    if not isinstance(name, str):
        raise RedactionError("unsupported_content")
    return re.sub(r"[^a-z0-9]", "", name.casefold())


def _field_category(name: str) -> str | None:
    normalized = _normalize(name)
    if normalized in _IDENTITY_FIELDS:
        return "identity"
    if normalized in _SECRET_FIELDS:
        return "secret"
    return None


def _validate_json_value(value: JsonValue) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise RedactionError("non_finite_json_number")
    if isinstance(value, list):
        for item in value:
            _validate_json_value(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if _normalize(key) in _UNSUPPORTED_FIELDS:
                raise RedactionError("unsupported_content")
            _validate_json_value(item)


def _redact_text(text: str, protected_values: set[str]) -> tuple[str, int]:
    stripped = text.strip()
    if stripped.startswith(("{", "[")):
        parsed = strict_json_loads(stripped)
        if not isinstance(parsed, dict | list):
            raise RedactionError("unsupported_content")
        redacted, count = _redact_json(parsed)
        return json.dumps(redacted, sort_keys=True, separators=(",", ":")), count + 1
    redacted = text
    count = 0
    for value in sorted(protected_values, key=len, reverse=True):
        occurrences = redacted.count(value)
        redacted = redacted.replace(value, REDACTION_MARKER)
        count += occurrences
    matches = list(_CANONICAL_TEXT_RE.finditer(redacted))
    ranges = [match.span() for match in matches]
    if any(
        not any(start <= label.start() and label.end() <= end for start, end in ranges)
        for label in _SENSITIVE_LABEL_RE.finditer(redacted)
    ):
        raise RedactionError("ambiguous_sensitive_label")
    pieces: list[str] = []
    cursor = 0
    for match in matches:
        pieces.extend(
            (
                redacted[cursor : match.start()],
                f"{match.group('label')}{match.group('before')}"
                f"{match.group('separator')}{match.group('after')}{REDACTION_MARKER}",
            )
        )
        cursor = match.end()
    return "".join(pieces) + redacted[cursor:], count + len(matches)


def _redact_json(
    value: JsonValue, inherited_protected_values: set[str] | None = None
) -> tuple[JsonValue, int]:
    protected = (inherited_protected_values or set()) | _collect_protected_values(value)
    if isinstance(value, list):
        items = [_redact_json(item, protected) for item in value]
        return [item for item, _ in items], sum(count for _, count in items)
    if isinstance(value, dict):
        redacted: dict[str, JsonValue] = {}
        count = 0
        for key, nested in value.items():
            if _field_category(key) is not None:
                redacted[key] = REDACTION_MARKER
                count += 1
            elif isinstance(nested, str):
                redacted[key], nested_count = _redact_text(nested, protected)
                count += nested_count
            else:
                redacted[key], nested_count = _redact_json(nested, protected)
                count += nested_count
        return redacted, count
    return value, 0


def _collect_protected_values(value: JsonValue) -> set[str]:
    collected: set[str] = set()
    if isinstance(value, list):
        for item in value:
            collected.update(_collect_protected_values(item))
    elif isinstance(value, dict):
        for key, nested in value.items():
            if _field_category(key) is not None:
                collected.update(_string_leaves(nested))
            collected.update(_collect_protected_values(nested))
    return collected


def _string_leaves(value: JsonValue) -> set[str]:
    if isinstance(value, str) and value:
        return {value}
    if isinstance(value, list):
        return set().union(*(_string_leaves(item) for item in value))
    if isinstance(value, dict):
        return set().union(*(_string_leaves(item) for item in value.values()))
    return set()
