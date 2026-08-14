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
import sys
from typing import Any, Mapping

SCHEMA_VERSION = "1.0"
TOOL_NAME = "host_observer_collector"
REQUEST_MAX_BYTES = 8192

SOURCE_CLASSES = frozenset({"metadata", "neutron", "nova"})
WINDOW_CLASSES = frozenset({"default"})
LINE_LIMIT_CLASSES = frozenset({"default"})
PROJECTION_FRESHNESS_CLASSES = frozenset({"current", "stale", "unknown"})

REQUEST_FIELDS = {"schema_version", "host_label", "source_class", "window_class", "line_limit_class"}
PROJECTION_FIELDS = {"schema_version", "revision", "freshness_class", "entries"}
PROJECTION_ENTRY_FIELDS = {"host_label", "inventory_role", "source_classes", "enabled"}
POLICY_FIELDS = {
    "schema_version",
    "source_classes",
    "window_classes",
    "line_limit_classes",
    "metadata_status",
    "redaction_policy_status",
}

ERROR_MESSAGES = {
    "authorization_pending": "host observation is unavailable",
    "collector_stub": "host observation collector is unavailable",
    "invocation_denied": "collector invocation is unavailable",
    "validation_error": "collector request is invalid",
    "observer_integrity_error": "observer metadata is unavailable",
    "unsupported_deployment_state": "observer deployment is unavailable",
    "host_unavailable": "approved host is unavailable",
    "host_disabled": "approved host is disabled",
    "source_role_mismatch": "approved source is unavailable for this host",
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


def _require_mapping(value: Any, error_class: str = "validation_error") -> Mapping[str, Any]:
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
    if any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in label):
        raise CollectorValidationError("unsafe_host_label")
    return label


def parse_request(raw: bytes | str) -> dict[str, Any]:
    """Parse the closed collector request without reading any source."""

    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    if not isinstance(raw, bytes) or len(raw) > REQUEST_MAX_BYTES:
        raise CollectorValidationError("request_oversized")
    try:
        request = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, CollectorValidationError):
        raise CollectorValidationError("validation_error") from None

    request = _require_mapping(request)
    if set(request) != REQUEST_FIELDS:
        raise CollectorValidationError("unknown_or_missing_field")
    if request["schema_version"] != SCHEMA_VERSION:
        raise CollectorValidationError("unsupported_schema")
    normalized = {
        "schema_version": SCHEMA_VERSION,
        "host_label": _validate_host_label(request["host_label"]),
        "source_class": _require_closed_string(request["source_class"], SOURCE_CLASSES),
        "window_class": _require_closed_string(request["window_class"], WINDOW_CLASSES),
        "line_limit_class": _require_closed_string(
            request["line_limit_class"], LINE_LIMIT_CLASSES
        ),
    }
    return normalized


def validate_projection_metadata(projection: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate non-secret projection metadata supplied by a synthetic caller."""

    projection = _require_mapping(projection, "observer_integrity_error")
    if set(projection) != PROJECTION_FIELDS or projection["schema_version"] != SCHEMA_VERSION:
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
        if set(entry) != PROJECTION_ENTRY_FIELDS:
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


def unavailable_document(error_class: str = "collector_stub") -> dict[str, Any]:
    """Return the deterministic non-success document for the compile-safe stub."""

    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL_NAME,
        "status": "unavailable",
        "sections": [],
        "error": {
            "class": error_class,
            "message": ERROR_MESSAGES.get(error_class, "host observation is unavailable"),
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
