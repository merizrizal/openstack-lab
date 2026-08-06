#!/usr/bin/env python3
"""Fail-closed registry loader and compile-safe runner stub."""

from __future__ import annotations

import json
import os
import re
import selectors
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUNTIME_ROOT = Path("/opt/openstack-ai-ops-assistant")
APPROVED_SCRIPT_ROOT = RUNTIME_ROOT / "scripts" / "approved"
PROJECT_READER_PROFILE = "aiops-assistant-project-reader"
REGISTRY_NAME = "ai-ops-assistant-tool-runner-steps-01-04"
REGISTRY_SCHEMA_VERSION = 1
TOOL_NAMES = {
    "project_resource_summary",
    "server_basic_info",
    "server_network_info",
}
TOOL_TARGETS = {
    "project_resource_summary": APPROVED_SCRIPT_ROOT / "project_resource_summary.sh",
    "server_basic_info": APPROVED_SCRIPT_ROOT / "server_basic_info.sh",
    "server_network_info": APPROVED_SCRIPT_ROOT / "server_network_info.sh",
}
CHILD_ENVIRONMENT = {
    "PATH": "/usr/bin:/bin",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "HOME": "/nonexistent",
    "PYTHONNOUSERSITE": "1",
    "OS_CLIENT_CONFIG_FILE": str(
        RUNTIME_ROOT / "credentials" / "profiles" / "clouds.yaml"
    ),
    "OS_CLOUD": PROJECT_READER_PROFILE,
}
_TEST_EXECUTION_TARGET: Path | None = None
_TEST_WORKING_DIRECTORY: Path | None = None
ROOT_FIELDS = {"schema_version", "registry_name", "defaults", "tools"}
DEFAULT_FIELDS = {
    "credential_profile",
    "risk_class",
    "timeout_seconds",
    "output_limit_bytes",
    "mutation_guarantee",
}
TOOL_FIELDS = {
    "name",
    "description",
    "implementation_target",
    "credential_profile",
    "risk_class",
    "timeout_seconds",
    "output_limit_bytes",
    "mutation_guarantee",
    "parameters",
}
PARAMETER_FIELDS = {
    "name",
    "position",
    "required",
    "type",
    "validation",
    "pattern",
    "max_length",
    "allowed_values",
    "default",
    "description",
}
SUPPORTED_VALIDATIONS = {"safe_identifier_pattern"}
MAX_TIMEOUT_SECONDS = 300
MAX_OUTPUT_BYTES = 1024 * 1024
SAFE_IDENTIFIER_PATTERN = r"^[A-Za-z0-9._:-]+$"

STATUS_EXIT_CODES = {
    "ok": 0,
    "error": 1,
    "denied": 2,
    "validation_error": 3,
    "timeout": 4,
    "unavailable": 5,
}
RESULT_FIELDS = {
    "schema_version",
    "tool",
    "status",
    "arguments",
    "exit_code",
    "data",
    "stdout",
    "stderr",
    "error",
    "duration_ms",
    "truncated",
    "timestamp",
    "correlation_id",
}
RESULT_SCHEMA_VERSION = "1.0"
AUDIT_SCHEMA_VERSION = "1.0"
AUDIT_EVENT_TYPE = "tool_request_completed"
AUDIT_ACTOR = "local_cli"
MAX_AUDIT_EVENT_BYTES = 16 * 1024
AUDIT_FIELDS = {
    "schema_version",
    "timestamp",
    "event_type",
    "actor",
    "tool",
    "arguments",
    "status",
    "duration_ms",
    "correlation_id",
    "reason",
    "exit_code",
    "truncated",
}
UNKNOWN_TOOL_LABEL = "unknown"
_TEST_CLOCK = None
_TEST_UUID_FACTORY = None


class RegistryError(ValueError):
    """Raised when the complete trusted registry is invalid."""


class RequestDeniedError(ValueError):
    """Raised when a request names an unapproved capability."""


class RequestValidationError(ValueError):
    """Raised when declared request input is malformed or unsafe."""


class TargetUnavailableError(ValueError):
    """Raised when the approved implementation cannot be used."""


class TargetIntegrityError(ValueError):
    """Raised when an implementation violates the fixed runtime boundary."""


class RedactionError(ValueError):
    """Raised when redaction cannot safely produce a complete sanitized value."""


class RedactionResult:
    """A complete sanitized value and its bounded-work metadata."""

    __slots__ = ("replaced", "truncated", "value")

    def __init__(
        self, value: Any, replaced: bool = False, truncated: bool = False
    ) -> None:
        self.value = value
        self.replaced = replaced
        self.truncated = truncated


class RedactionPolicy:
    """Limits and marker used by the standalone redaction boundary."""

    __slots__ = ("marker", "maximum_depth", "maximum_text_bytes", "maximum_values")

    def __init__(
        self,
        marker: str = "[REDACTED]",
        maximum_depth: int = 32,
        maximum_values: int = 100_000,
        maximum_text_bytes: int | None = None,
    ) -> None:
        self.marker = marker
        self.maximum_depth = maximum_depth
        self.maximum_values = maximum_values
        self.maximum_text_bytes = maximum_text_bytes


DEFAULT_REDACTION_POLICY = RedactionPolicy()
MAX_PUBLIC_MESSAGE_BYTES = 512
_SECRET_KEY_PARTS = (
    "password",
    "passphrase",
    "secret",
    "token",
    "credential",
    "privatekey",
    "apikey",
    "authorization",
)
_ASSIGNMENT_SECRET_PATTERN = re.compile(
    r"(?i)(\b(?:password|passphrase|secret|token|credential|private[ _-]*key|api[ _-]*key|authorization)\b"
    r"\s*[:=]\s*)(\"[^\"]*\"|'[^']*'|[^\s,;\]}]+)"
)
_BEARER_PATTERN = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN [^-\r\n]*PRIVATE KEY-----.*?-----END [^-\r\n]*PRIVATE KEY-----",
    re.DOTALL,
)


def _normalized_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _is_secret_key(value: str) -> bool:
    normalized = _normalized_key(value)
    return any(part in normalized for part in _SECRET_KEY_PARTS)


def _bounded_utf8_text(text: str, maximum_bytes: int) -> tuple[str, bool]:
    encoded = text.encode("utf-8")
    if len(encoded) <= maximum_bytes:
        return text, False
    retained = encoded[:maximum_bytes]
    while retained:
        try:
            return retained.decode("utf-8"), True
        except UnicodeDecodeError:
            retained = retained[:-1]
    return "", True


def sanitize_text(
    text: str,
    maximum_bytes: int = MAX_PUBLIC_MESSAGE_BYTES,
    policy: RedactionPolicy | None = None,
) -> RedactionResult:
    """Redact reviewed text forms and enforce a UTF-8 byte bound."""

    if not isinstance(text, str):
        raise RedactionError("text must be a string")
    if not isinstance(maximum_bytes, int) or isinstance(maximum_bytes, bool):
        raise RedactionError("text bound must be an integer")
    if maximum_bytes < 0:
        raise RedactionError("text bound must not be negative")
    active_policy = policy or DEFAULT_REDACTION_POLICY
    sanitized = _PRIVATE_KEY_PATTERN.sub(active_policy.marker, text)
    sanitized = _BEARER_PATTERN.sub(f"Bearer {active_policy.marker}", sanitized)
    sanitized = _ASSIGNMENT_SECRET_PATTERN.sub(
        rf"\1{re.escape(active_policy.marker)}", sanitized
    )
    sanitized, truncated = _bounded_utf8_text(sanitized, maximum_bytes)
    return RedactionResult(
        sanitized,
        replaced=sanitized != text or active_policy.marker in sanitized,
        truncated=truncated,
    )


def redact_value(
    value: Any,
    policy: RedactionPolicy | None = None,
) -> RedactionResult:
    """Recursively redact a JSON-like value, failing without partial output."""

    active_policy = policy or DEFAULT_REDACTION_POLICY
    if not isinstance(active_policy, RedactionPolicy):
        raise RedactionError("invalid redaction policy")
    state = {"values": 0}

    def visit(current: Any, depth: int) -> RedactionResult:
        state["values"] += 1
        if state["values"] > active_policy.maximum_values:
            raise RedactionError("redaction work limit exceeded")
        if depth > active_policy.maximum_depth:
            raise RedactionError("redaction nesting limit exceeded")
        if current is None or isinstance(current, (bool, int, float)):
            return RedactionResult(current)
        if isinstance(current, str):
            if active_policy.maximum_text_bytes is None:
                result = sanitize_text(
                    current, len(current.encode("utf-8")), active_policy
                )
            else:
                result = sanitize_text(
                    current, active_policy.maximum_text_bytes, active_policy
                )
            return result
        if isinstance(current, list):
            items = [visit(item, depth + 1) for item in current]
            return RedactionResult(
                [item.value for item in items],
                replaced=any(item.replaced for item in items),
                truncated=any(item.truncated for item in items),
            )
        if isinstance(current, dict):
            sanitized: dict[str, Any] = {}
            replaced = False
            truncated = False
            for key, item in current.items():
                if not isinstance(key, str):
                    raise RedactionError("object keys must be strings")
                if _is_secret_key(key):
                    sanitized[key] = active_policy.marker
                    replaced = True
                    state["values"] += 1
                    if state["values"] > active_policy.maximum_values:
                        raise RedactionError("redaction work limit exceeded")
                    continue
                result = visit(item, depth + 1)
                sanitized[key] = result.value
                replaced = replaced or result.replaced
                truncated = truncated or result.truncated
            return RedactionResult(sanitized, replaced, truncated)
        raise RedactionError("unsupported value for redaction")

    return visit(value, 0)


def sanitize_arguments(
    tool: str,
    validated_arguments: dict[str, Any],
    audience: str = "result",
) -> dict[str, Any]:
    """Return a redacted result argument object or minimal audit summary."""

    if not isinstance(tool, str) or not isinstance(validated_arguments, dict):
        raise RedactionError("invalid argument container")
    if audience == "audit":
        return {"server_identifier_present": "server_identifier" in validated_arguments}
    if audience != "result":
        raise RedactionError("invalid redaction audience")
    result = redact_value(validated_arguments)
    if not isinstance(result.value, dict):
        raise RedactionError("sanitized arguments are not an object")
    return result.value


def _request_timestamp() -> str:
    clock = _TEST_CLOCK or (lambda: datetime.now(timezone.utc))
    value = clock()
    if not isinstance(value, datetime):
        raise TypeError("request clock returned an invalid value")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _request_correlation_id() -> str:
    factory = _TEST_UUID_FACTORY or uuid.uuid4
    value = factory()
    if not isinstance(value, uuid.UUID) or value.version != 4:
        raise ValueError("request identifier factory returned an invalid value")
    return str(value)


def _public_tool_label(tool_name: str) -> str:
    return tool_name if tool_name in TOOL_NAMES else UNKNOWN_TOOL_LABEL


_ERROR_MESSAGES = {
    "registry_error": "Runner registry is invalid.",
    "validation_error": "Request arguments are invalid.",
    "target_unavailable": "Approved diagnostic is unavailable.",
    "target_integrity_error": "Approved diagnostic failed integrity checks.",
    "execution_error": "Approved diagnostic failed.",
    "timeout": "Diagnostic exceeded its time limit.",
    "interrupted": "Diagnostic was interrupted.",
    "output_decode_error": "Diagnostic output could not be accepted.",
    "redaction_error": "Diagnostic result could not be safely redacted.",
    "serialization_error": "Diagnostic result could not be serialized.",
    "request_context_error": "Request context could not be created.",
}


def _error_class(status: str, reason: str | None) -> str:
    if reason == "requested tool is not approved":
        return "validation_error"
    if reason == "runner registry is invalid":
        return "registry_error"
    if reason == "request parameters are invalid":
        return "validation_error"
    if reason == "approved implementation is unavailable":
        return "target_unavailable"
    if reason == "approved implementation is unsafe":
        return "target_integrity_error"
    if reason == "approved implementation timed out":
        return "timeout"
    if reason == "runner was interrupted":
        return "interrupted"
    if reason == "diagnostic output is invalid":
        return "output_decode_error"
    if reason == "result redaction failed":
        return "redaction_error"
    if status == "denied":
        return "validation_error"
    if status == "validation_error":
        return "validation_error"
    if status == "timeout":
        return "timeout"
    if status == "unavailable":
        return "target_unavailable"
    return "execution_error"


def _diagnostic_data(
    tool: dict[str, Any], capture: CaptureResult | None
) -> dict[str, Any] | None:
    if capture is None:
        return None
    try:
        payload = json.loads(capture.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RedactionError("diagnostic output is invalid") from exc
    if not isinstance(payload, dict):
        raise RedactionError("diagnostic output is invalid")
    if payload.get("schema_version") != "1.0" or payload.get("tool") != tool["name"]:
        raise RedactionError("diagnostic output is invalid")
    if payload.get("status") not in {"ok", "partial", "error"}:
        raise RedactionError("diagnostic output is invalid")
    redacted = redact_value(payload)
    if not isinstance(redacted.value, dict):
        raise RedactionError("diagnostic output is invalid")
    return redacted.value


def build_result_envelope(
    tool_name: str,
    status: str,
    arguments: dict[str, Any] | None = None,
    reason: str | None = None,
    capture: CaptureResult | None = None,
    timestamp: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Build one closed, redacted, deterministic result object."""

    if status not in STATUS_EXIT_CODES:
        raise ValueError("unknown result status")
    if timestamp is None:
        timestamp = _request_timestamp()
    if correlation_id is None:
        correlation_id = _request_correlation_id()
    safe_arguments = sanitize_arguments(
        _public_tool_label(tool_name), arguments or {}, "result"
    )
    should_include_data = capture is not None and (
        status in {"ok", "unavailable"}
        or reason in {None, "approved implementation failed"}
    )
    data = (
        _diagnostic_data({"name": _public_tool_label(tool_name)}, capture)
        if should_include_data and _public_tool_label(tool_name) != UNKNOWN_TOOL_LABEL
        else None
    )
    error = None
    if status != "ok":
        error_class = _error_class(status, reason)
        error = {
            "class": error_class,
            "message": _ERROR_MESSAGES.get(error_class, "Runner request failed."),
        }
        error = {
            "class": error["class"],
            "message": sanitize_text(error["message"]).value,
        }
    payload = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "tool": _public_tool_label(tool_name),
        "status": status,
        "arguments": safe_arguments,
        "exit_code": capture.return_code
        if capture is not None
        else STATUS_EXIT_CODES[status],
        "data": data,
        "stdout": None,
        "stderr": None,
        "error": error,
        "duration_ms": capture.duration_ms if capture is not None else 0,
        "truncated": capture.truncated if capture is not None else False,
        "timestamp": timestamp,
        "correlation_id": correlation_id,
    }
    if set(payload) != RESULT_FIELDS:
        raise ValueError("result envelope field set is invalid")
    return payload


def serialize_result_envelope(payload: dict[str, Any]) -> str:
    """Serialize one complete result object as compact deterministic JSON."""

    if not isinstance(payload, dict) or set(payload) != RESULT_FIELDS:
        raise ValueError("result envelope field set is invalid")
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )


def build_audit_event(
    result: dict[str, Any], actor: str = AUDIT_ACTOR
) -> dict[str, Any]:
    """Derive one closed, minimum-disclosure event from a safe result."""

    if not isinstance(result, dict) or set(result) != RESULT_FIELDS:
        raise ValueError("result envelope field set is invalid")
    if actor != AUDIT_ACTOR:
        raise ValueError("actor classification is not approved")
    arguments = result["arguments"]
    if not isinstance(arguments, dict):
        raise TypeError("result arguments are invalid")
    safe_arguments = sanitize_arguments("audit", arguments, "audit")
    error = result["error"]
    if error is not None and (
        not isinstance(error, dict) or set(error) != {"class", "message"}
    ):
        raise ValueError("result error object is invalid")
    event = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "timestamp": result["timestamp"],
        "event_type": AUDIT_EVENT_TYPE,
        "actor": AUDIT_ACTOR,
        "tool": result["tool"],
        "arguments": safe_arguments,
        "status": result["status"],
        "duration_ms": result["duration_ms"],
        "correlation_id": result["correlation_id"],
        "reason": error["class"] if error is not None else None,
        "exit_code": result["exit_code"],
        "truncated": result["truncated"],
    }
    if set(event) != AUDIT_FIELDS:
        raise ValueError("audit event field set is invalid")
    return event


def serialize_audit_event(event: dict[str, Any]) -> str:
    """Serialize one complete audit event without opening an audit sink."""

    if not isinstance(event, dict) or set(event) != AUDIT_FIELDS:
        raise ValueError("audit event field set is invalid")
    serialized = json.dumps(
        event,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    if len(serialized.encode("utf-8")) + 1 > MAX_AUDIT_EVENT_BYTES:
        raise ValueError("audit event exceeds its size bound")
    return serialized + "\n"


class CaptureResult:
    """Bounded byte capture and process completion state."""

    def __init__(
        self,
        stdout: bytes,
        stderr: bytes,
        truncated: bool,
        timed_out: bool,
        return_code: int,
        duration_ms: int,
    ) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.truncated = truncated
        self.timed_out = timed_out
        self.return_code = return_code
        self.duration_ms = duration_ms


def parse_declared_args(argv: list[str]) -> tuple[str, dict[str, str]]:
    """Parse the fixed tool-name and repeated ``--arg KEY=VALUE`` interface."""

    if not argv:
        raise RequestValidationError("tool name is required")
    tool_name = argv[0]
    declarations: dict[str, str] = {}
    index = 1
    while index < len(argv):
        if argv[index] != "--arg" or index + 1 >= len(argv):
            raise RequestValidationError("arguments must use --arg KEY=VALUE")
        declaration = argv[index + 1]
        key, separator, value = declaration.partition("=")
        if not separator or not key:
            raise RequestValidationError("arguments must use --arg KEY=VALUE")
        if key in declarations:
            raise RequestValidationError("parameter declarations must be unique")
        declarations[key] = value
        index += 2
    return tool_name, declarations


def default_registry_path() -> Path:
    """Return the only registry path the runner is allowed to load."""

    return Path(__file__).with_name("tool_registry.json")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RegistryError("registry contains duplicate object keys")
        result[key] = value
    return result


def _require_exact_fields(value: Any, expected: set[str], label: str) -> None:
    if not isinstance(value, dict):
        raise RegistryError(f"{label} must be an object")
    actual = set(value)
    if actual != expected:
        raise RegistryError(f"{label} has an invalid field set")


def _require_string(value: Any, label: str, expected: str | None = None) -> str:
    if not isinstance(value, str) or not value:
        raise RegistryError(f"{label} must be a non-empty string")
    if expected is not None and value != expected:
        raise RegistryError(f"{label} has an invalid value")
    return value


def _require_bounded_integer(value: Any, label: str, lower: int, upper: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RegistryError(f"{label} must be an integer")
    if not lower <= value <= upper:
        raise RegistryError(f"{label} is outside its permitted range")
    return value


def _validate_parameter(parameter: Any, tool_name: str) -> None:
    label = f"parameter for {tool_name}"
    required_fields = {
        "name",
        "position",
        "required",
        "type",
        "validation",
        "description",
    }
    optional_fields = {"pattern", "max_length", "allowed_values", "default"}
    if not isinstance(parameter, dict):
        raise RegistryError(f"{label} must be an object")
    actual_fields = set(parameter)
    if (
        not required_fields <= actual_fields
        or not actual_fields <= required_fields | optional_fields
    ):
        raise RegistryError(f"{label} has an invalid field set")
    _require_string(parameter["name"], f"{label} name")
    _require_bounded_integer(parameter["position"], f"{label} position", 1, 32)
    if not isinstance(parameter["required"], bool):
        raise RegistryError(f"{label} required must be boolean")
    _require_string(parameter["type"], f"{label} type", "string")
    validation = _require_string(parameter["validation"], f"{label} validation")
    if validation not in SUPPORTED_VALIDATIONS:
        raise RegistryError(f"{label} uses an unsupported validator")
    _require_string(
        parameter.get("pattern"), f"{label} pattern", SAFE_IDENTIFIER_PATTERN
    )
    _require_bounded_integer(parameter.get("max_length"), f"{label} max_length", 1, 255)
    if parameter["name"] != "server_identifier" or not parameter["required"]:
        raise RegistryError(f"{label} is not an approved initial parameter")
    if "allowed_values" in parameter or "default" in parameter:
        raise RegistryError(f"{label} has unsupported optional constraints")
    _require_string(parameter["description"], f"{label} description")


def _validate_tool(tool: Any, defaults: dict[str, Any], seen_names: set[str]) -> None:
    if not isinstance(tool, dict):
        raise RegistryError("registry tool entries must be objects")
    _require_exact_fields(tool, TOOL_FIELDS, "registry tool")
    name = _require_string(tool["name"], "registry tool name")
    if name not in TOOL_NAMES or name in seen_names:
        raise RegistryError("registry tool name is not unique and approved")
    seen_names.add(name)

    _require_string(tool["description"], f"{name} description")
    target = _require_string(
        tool["implementation_target"], f"{name} implementation_target"
    )
    if Path(target) != TOOL_TARGETS[name]:
        raise RegistryError(f"{name} implementation target is not approved")
    _require_string(
        tool["credential_profile"], f"{name} credential_profile", PROJECT_READER_PROFILE
    )
    _require_string(tool["risk_class"], f"{name} risk_class", defaults["risk_class"])
    timeout = _require_bounded_integer(
        tool["timeout_seconds"], f"{name} timeout_seconds", 1, MAX_TIMEOUT_SECONDS
    )
    if timeout > defaults["timeout_seconds"]:
        raise RegistryError(f"{name} timeout exceeds the registry default ceiling")
    output_limit = _require_bounded_integer(
        tool["output_limit_bytes"], f"{name} output_limit_bytes", 1, MAX_OUTPUT_BYTES
    )
    if output_limit > defaults["output_limit_bytes"]:
        raise RegistryError(f"{name} output limit exceeds the registry default ceiling")
    _require_string(
        tool["mutation_guarantee"],
        f"{name} mutation_guarantee",
        defaults["mutation_guarantee"],
    )
    parameters = tool["parameters"]
    if not isinstance(parameters, list):
        raise RegistryError(f"{name} parameters must be an array")
    seen_parameters: set[str] = set()
    seen_positions: set[int] = set()
    for parameter in parameters:
        _validate_parameter(parameter, name)
        parameter_name = parameter["name"]
        position = parameter["position"]
        if parameter_name in seen_parameters or position in seen_positions:
            raise RegistryError(f"{name} parameter names and positions must be unique")
        seen_parameters.add(parameter_name)
        seen_positions.add(position)

    expected_parameter_names = (
        {"server_identifier"} if name != "project_resource_summary" else set()
    )
    if seen_parameters != expected_parameter_names:
        raise RegistryError(f"{name} has an invalid parameter set")


def load_registry(path: str | Path | None = None) -> dict[str, Any]:
    """Load and fully validate the trusted registry before any request work."""

    registry_path = default_registry_path() if path is None else Path(path)
    try:
        raw = registry_path.read_text(encoding="utf-8")
        data = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
    except (OSError, UnicodeError, json.JSONDecodeError, RegistryError) as exc:
        if isinstance(exc, RegistryError):
            raise
        raise RegistryError("registry could not be read or parsed") from exc

    _require_exact_fields(data, ROOT_FIELDS, "registry root")
    if data["schema_version"] != REGISTRY_SCHEMA_VERSION:
        raise RegistryError("registry schema version is unsupported")
    _require_string(data["registry_name"], "registry_name", REGISTRY_NAME)

    defaults = data["defaults"]
    _require_exact_fields(defaults, DEFAULT_FIELDS, "registry defaults")
    _require_string(
        defaults["credential_profile"],
        "default credential_profile",
        PROJECT_READER_PROFILE,
    )
    _require_string(
        defaults["risk_class"], "default risk_class", "low_readonly_project_scope"
    )
    _require_bounded_integer(
        defaults["timeout_seconds"], "default timeout_seconds", 1, MAX_TIMEOUT_SECONDS
    )
    _require_bounded_integer(
        defaults["output_limit_bytes"],
        "default output_limit_bytes",
        1,
        MAX_OUTPUT_BYTES,
    )
    _require_string(
        defaults["mutation_guarantee"],
        "default mutation_guarantee",
        "read_only_fixed_diagnostic_script",
    )

    tools = data["tools"]
    if not isinstance(tools, list) or len(tools) != len(TOOL_NAMES):
        raise RegistryError("registry must contain exactly the approved tools")
    seen_names: set[str] = set()
    for tool in tools:
        _validate_tool(tool, defaults, seen_names)
    if seen_names != TOOL_NAMES:
        raise RegistryError("registry tool set is incomplete")
    return data


def validate_parameter_value(parameter: dict[str, Any], value: Any) -> str:
    """Return one validated value or fail before any target can be inspected."""

    if parameter["type"] != "string" or not isinstance(value, str):
        raise RequestValidationError("parameter has an invalid type")
    try:
        value_length = len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise RequestValidationError("parameter has an invalid value") from exc
    if value_length > parameter["max_length"]:
        raise RequestValidationError("parameter exceeds its maximum length")
    if (
        "/" in value
        or ".." in value
        or re.fullmatch(parameter["pattern"], value) is None
    ):
        raise RequestValidationError("parameter has an unsafe value")
    return value


def validate_request(
    registry: dict[str, Any], tool_name: str, declarations: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, str]]:
    """Resolve one registered request and validate only its declared parameters."""

    tool = next((item for item in registry["tools"] if item["name"] == tool_name), None)
    if tool is None:
        raise RequestDeniedError("requested tool is not approved")
    parameters = {parameter["name"]: parameter for parameter in tool["parameters"]}
    if any(name not in parameters for name in declarations):
        raise RequestValidationError("request contains an undeclared parameter")

    values: dict[str, str] = {}
    for name, parameter in parameters.items():
        if name not in declarations:
            if parameter["required"]:
                raise RequestValidationError("request is missing a required parameter")
            if "default" in parameter:
                values[name] = validate_parameter_value(parameter, parameter["default"])
            continue
        values[name] = validate_parameter_value(parameter, declarations[name])
    return tool, values


def build_child_environment() -> dict[str, str]:
    """Build the complete fixed child environment without inheriting parent state."""

    return dict(CHILD_ENVIRONMENT)


def validate_runtime_target(tool: dict[str, Any]) -> Path:
    """Return a regular executable only from the fixed approved target mapping."""

    name = tool["name"]
    expected_target = TOOL_TARGETS.get(name)
    if (
        expected_target is None
        or Path(tool["implementation_target"]) != expected_target
    ):
        raise TargetIntegrityError("approved target does not match its tool")
    target = (
        _TEST_EXECUTION_TARGET
        if _TEST_EXECUTION_TARGET is not None
        else expected_target
    )
    if not target.exists():
        raise TargetUnavailableError("approved implementation is unavailable")
    if target.is_symlink() or not target.is_file() or not os.access(target, os.X_OK):
        raise TargetIntegrityError("approved implementation is unsafe")
    return target


def build_command_argv(tool: dict[str, Any], values: dict[str, str]) -> list[str]:
    """Build fixed argv from the trusted target and ordered validated values only."""

    ordered_parameters = sorted(
        tool["parameters"], key=lambda parameter: parameter["position"]
    )
    expected_names = {parameter["name"] for parameter in ordered_parameters}
    if set(values) != expected_names:
        raise TargetIntegrityError(
            "validated parameters do not match the approved tool"
        )
    return [str(validate_runtime_target(tool))] + [
        values[parameter["name"]] for parameter in ordered_parameters
    ]


def terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    """Terminate, then forcibly reap, the child process group."""

    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=1)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    process.wait()


def capture_bounded(
    process: subprocess.Popen[bytes], timeout_seconds: int, output_limit_bytes: int
) -> CaptureResult:
    """Concurrently drain pipes under the fixed timeout and retained-byte budget."""

    started = time.monotonic()
    deadline = started + timeout_seconds
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    closed = {"stdout": False, "stderr": False}
    truncated = False
    timed_out = False
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0 and not timed_out:
                terminate_process_group(process)
                timed_out = True
                remaining = 0
            for key, _ in selector.select(min(0.05, max(remaining, 0.0))):
                stream_name = key.data
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    closed[stream_name] = True
                    continue
                other_stream = "stderr" if stream_name == "stdout" else "stdout"
                retained_total = len(buffers["stdout"]) + len(buffers["stderr"])
                stream_ceiling = (
                    output_limit_bytes
                    if closed[other_stream]
                    else output_limit_bytes // 2
                )
                retained = min(
                    len(chunk),
                    output_limit_bytes - retained_total,
                    max(0, stream_ceiling - len(buffers[stream_name])),
                )
                buffers[stream_name].extend(chunk[:retained])
                if retained != len(chunk):
                    truncated = True
            if process.poll() is not None and not selector.get_map():
                break
    return_code = process.wait()
    process.stdout.close()
    process.stderr.close()
    return CaptureResult(
        stdout=bytes(buffers["stdout"]),
        stderr=bytes(buffers["stderr"]),
        truncated=truncated,
        timed_out=timed_out,
        return_code=return_code,
        duration_ms=int((time.monotonic() - started) * 1000),
    )


def validate_diagnostic_payload(tool: dict[str, Any], stdout: bytes) -> str:
    """Validate strict diagnostic JSON and map only approved unavailable classes."""

    try:
        payload = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("diagnostic output is invalid") from exc
    if not isinstance(payload, dict):
        raise TypeError("diagnostic output is invalid")
    if payload.get("schema_version") != "1.0" or payload.get("tool") != tool["name"]:
        raise ValueError("diagnostic output is invalid")
    status = payload.get("status")
    if status not in {"ok", "partial", "error"}:
        raise ValueError("diagnostic output is invalid")
    error = payload.get("error")
    error_class = error.get("class") if isinstance(error, dict) else None
    if error_class in {"service_unavailable", "catalog_missing", "connectivity_error"}:
        return "unavailable"
    if status == "error":
        return "error"
    return "ok"


def execute_fixed_diagnostic(
    tool: dict[str, Any], values: dict[str, str]
) -> tuple[str, str | None, CaptureResult | None]:
    """Run one fixed diagnostic with bounded capture and process-group cleanup."""

    try:
        process = subprocess.Popen(
            build_command_argv(tool, values),
            close_fds=True,
            cwd=_TEST_WORKING_DIRECTORY or RUNTIME_ROOT,
            env=build_child_environment(),
            shell=False,
            start_new_session=True,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
        )
        capture = capture_bounded(
            process, tool["timeout_seconds"], tool["output_limit_bytes"]
        )
    except TargetUnavailableError:
        return "unavailable", "approved implementation is unavailable", None
    except TargetIntegrityError:
        return "error", "approved implementation is unsafe", None
    except KeyboardInterrupt:
        terminate_process_group(process)
        return "error", "runner was interrupted", None
    except OSError:
        return "error", "approved implementation could not start", None

    if capture.timed_out:
        return "timeout", "approved implementation timed out", capture
    try:
        capture.stderr.decode("utf-8")
        diagnostic_status = validate_diagnostic_payload(tool, capture.stdout)
    except ValueError:
        return "error", "diagnostic output is invalid", capture
    if capture.return_code != 0 and diagnostic_status != "unavailable":
        return "error", "approved implementation failed", capture
    if diagnostic_status == "unavailable":
        return "unavailable", "approved service is unavailable", capture
    return diagnostic_status, None, capture


def emit_result_outcome(
    tool_name: str,
    status: str,
    reason: str | None,
    arguments: dict[str, Any] | None,
    capture: CaptureResult | None = None,
    timestamp: str | None = None,
    correlation_id: str | None = None,
) -> None:
    """Emit exactly one final result envelope; audit persistence remains deferred."""

    try:
        payload = build_result_envelope(
            tool_name,
            status,
            arguments,
            reason,
            capture,
            timestamp,
            correlation_id,
        )
    except RedactionError:
        payload = build_result_envelope(
            tool_name,
            "error",
            {},
            "result redaction failed",
            None,
            timestamp,
            correlation_id,
        )
    sys.stdout.write(serialize_result_envelope(payload))


def main(argv: list[str] | None = None) -> int:
    """Validate input, execute the fixed diagnostic, and emit one final envelope."""

    requested = list(sys.argv[1:] if argv is None else argv)
    tool_name = requested[0] if requested else "unknown"
    timestamp = _request_timestamp()
    correlation_id = _request_correlation_id()
    try:
        registry = load_registry()
    except RegistryError:
        emit_result_outcome(
            tool_name,
            "error",
            "runner registry is invalid",
            {},
            timestamp=timestamp,
            correlation_id=correlation_id,
        )
        return STATUS_EXIT_CODES["error"]

    try:
        tool_name, declarations = parse_declared_args(requested)
        tool, values = validate_request(registry, tool_name, declarations)
    except RequestDeniedError:
        emit_result_outcome(
            tool_name,
            "denied",
            "requested tool is not approved",
            {},
            timestamp=timestamp,
            correlation_id=correlation_id,
        )
        return STATUS_EXIT_CODES["denied"]
    except RequestValidationError:
        emit_result_outcome(
            tool_name,
            "validation_error",
            "request parameters are invalid",
            {},
            timestamp=timestamp,
            correlation_id=correlation_id,
        )
        return STATUS_EXIT_CODES["validation_error"]

    status, reason, capture = execute_fixed_diagnostic(tool, values)
    emit_result_outcome(
        tool_name,
        status,
        reason,
        values,
        capture,
        timestamp,
        correlation_id,
    )
    return STATUS_EXIT_CODES[status]


if __name__ == "__main__":
    raise SystemExit(main())
