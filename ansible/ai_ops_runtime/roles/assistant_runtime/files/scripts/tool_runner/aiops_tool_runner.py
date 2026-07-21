#!/usr/bin/env python3
"""Fail-closed AI-OPS tool runner for reviewed diagnostic tools."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_EXIT_CODES = {
    "ok": 0,
    "error": 1,
    "denied": 2,
    "validation_error": 3,
    "timeout": 4,
    "unavailable": 5,
    "truncated": 6,
}

SAFE_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")
SECRET_LIKE_ARGUMENT_RE = re.compile(
    r"(?:^|[_-])(token|secret|password|passphrase|credential|private[_-]?key|api[_-]?key)(?:$|[_-])",
    re.IGNORECASE,
)
MCP_AUDIT_CLIENT_ID = "local-mcp-client"
MCP_AUDIT_TRANSPORT = "stdio"


def default_registry_path() -> Path:
    return Path(__file__).with_name("tool_registry.json")



def default_audit_path() -> Path:
    return Path("/opt/openstack-ai-ops/audit/tool-runner.jsonl")


def load_registry(path: str | Path) -> dict[str, Any]:
    registry_path = Path(path)
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("registry root must be a JSON object")

    tools = data.get("tools")
    if not isinstance(tools, list):
        raise ValueError("registry tools must be a JSON array")

    seen_names: set[str] = set()
    for tool in tools:
        if not isinstance(tool, dict):
            raise ValueError("registry tool entries must be JSON objects")
        name = tool.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("registry tool entry missing non-empty name")
        if name in seen_names:
            raise ValueError(f"duplicate tool name in registry: {name}")
        seen_names.add(name)

    return data


def build_result_envelope(
    tool_name: str,
    status: str,
    *,
    arguments: dict[str, str] | None = None,
    exit_code: int | None = None,
    stdout: str = "",
    stderr: str = "",
    duration_ms: int = 0,
    truncated: bool = False,
    request_id: str | None = None,
) -> dict[str, Any]:
    return {
        "tool": tool_name,
        "status": status,
        "arguments": sanitize_arguments(arguments),
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "duration_ms": duration_ms,
        "truncated": truncated,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "request_id": request_id or str(uuid.uuid4()),
    }


def sanitize_arguments(arguments: dict[str, str] | None) -> dict[str, Any]:
    if not arguments:
        return {}

    sanitized: dict[str, Any] = {}
    redacted_count = 0
    for name, value in arguments.items():
        if SECRET_LIKE_ARGUMENT_RE.search(name):
            redacted_count += 1
            continue
        sanitized[name] = value

    if redacted_count:
        sanitized["_redacted_argument_count"] = redacted_count

    return sanitized



def build_audit_event(
    envelope: dict[str, Any],
    *,
    client_id: str | None = None,
    transport: str | None = None,
) -> dict[str, Any]:
    if client_id not in (None, MCP_AUDIT_CLIENT_ID):
        raise ValueError("unsupported audit client identifier")
    if transport not in (None, MCP_AUDIT_TRANSPORT):
        raise ValueError("unsupported audit transport")

    event = {
        "timestamp": envelope["timestamp"],
        "tool": envelope["tool"],
        "status": envelope["status"],
        "arguments": sanitize_arguments(envelope.get("arguments")),
        "duration_ms": envelope["duration_ms"],
        "request_id": envelope["request_id"],
    }

    if client_id is not None:
        event["client_id"] = client_id
    if transport is not None:
        event["transport"] = transport
    if envelope.get("exit_code") is not None:
        event["exit_code"] = envelope["exit_code"]
    if envelope.get("truncated"):
        event["truncated"] = True
    if envelope.get("stderr"):
        event["reason"] = envelope["stderr"]

    return event



def write_audit_event(path: str | Path, event: dict[str, Any]) -> None:
    audit_path = Path(path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        json.dump(event, handle, sort_keys=True)
        handle.write("\n")


def parse_declared_args(raw_args: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_arg in raw_args:
        if "=" not in raw_arg:
            raise ValueError("declared arguments must use key=value format")
        key, value = raw_arg.split("=", 1)
        if not key:
            raise ValueError("declared argument key must not be empty")
        if key in parsed:
            raise ValueError(f"duplicate declared argument: {key}")
        parsed[key] = value
    return parsed


def get_supported_validation_types(registry: dict[str, Any]) -> set[str]:
    raw_types = registry.get("supported_argument_validation_types", [])
    if not isinstance(raw_types, list):
        raise ValueError("supported argument validation types must be a JSON array")

    supported_types: set[str] = set()
    for raw_type in raw_types:
        if not isinstance(raw_type, str) or not raw_type:
            raise ValueError(
                "supported argument validation types must be non-empty strings"
            )
        supported_types.add(raw_type)

    return supported_types


def validate_allowed_values(
    argument_definition: dict[str, Any],
    value: str,
) -> str:
    name = argument_definition["name"]
    raw_allowed_values = argument_definition.get("allowed_values")
    if (
        not isinstance(raw_allowed_values, list)
        or not raw_allowed_values
        or any(
            not isinstance(allowed_value, str) or not allowed_value
            for allowed_value in raw_allowed_values
        )
        or len(set(raw_allowed_values)) != len(raw_allowed_values)
    ):
        raise ValueError(
            f"registry argument {name} allowed_values must be a JSON array of unique non-empty strings"
        )
    if value not in raw_allowed_values:
        raise ValueError(f"{name} is not an allowed value")
    return value


def validate_allowed_host(
    argument_definition: dict[str, Any],
    value: str,
) -> str:
    return validate_allowed_values(argument_definition, value)


def validate_bounded_time_window(
    argument_definition: dict[str, Any],
    value: str,
) -> str:
    return validate_allowed_values(argument_definition, value)


def validate_fixed_arguments(requested_tool: dict[str, Any]) -> list[str]:
    tool_name = requested_tool.get("name", "unknown")
    raw_fixed_arguments = requested_tool.get("fixed_arguments")
    if raw_fixed_arguments is None:
        return []
    if (
        not isinstance(raw_fixed_arguments, list)
        or not raw_fixed_arguments
        or any(not isinstance(value, str) or not value for value in raw_fixed_arguments)
        or len(set(raw_fixed_arguments)) != len(raw_fixed_arguments)
    ):
        raise ValueError(
            f"registry tool {tool_name} fixed_arguments must be a JSON array of unique non-empty strings"
        )
    return raw_fixed_arguments


def validate_argument_value(
    argument_definition: dict[str, Any],
    value: str,
    supported_validation_types: set[str],
) -> str:
    name = argument_definition["name"]
    if value == "":
        raise ValueError(f"{name} must not be empty")

    max_length = argument_definition.get("max_length")
    if max_length is not None:
        if (
            not isinstance(max_length, int)
            or isinstance(max_length, bool)
            or max_length < 1
        ):
            raise ValueError(f"{name} max_length must be a positive integer")
        if len(value) > max_length:
            raise ValueError(f"{name} exceeds maximum length of {max_length}")

    validation_type = argument_definition.get("validation", "required_string")
    if not isinstance(validation_type, str) or not validation_type:
        raise ValueError(f"registry argument {name} is missing a validation type")
    if validation_type not in supported_validation_types:
        raise ValueError(
            f"registry argument {name} uses unsupported validation type: {validation_type}"
        )

    if validation_type == "required_string":
        return value

    if validation_type == "safe_identifier_pattern":
        pattern_text = argument_definition.get("pattern", SAFE_IDENTIFIER_PATTERN.pattern)
        if not isinstance(pattern_text, str) or not pattern_text:
            raise ValueError(f"registry argument {name} is missing a non-empty pattern")
        if re.fullmatch(pattern_text, value) is None:
            raise ValueError(f"{name} contains unsafe characters")
        return value

    if validation_type == "allowed_host_list":
        return validate_allowed_host(argument_definition, value)

    if validation_type == "bounded_time_window":
        return validate_bounded_time_window(argument_definition, value)

    raise ValueError(
        f"registry argument {name} uses unsupported validation type: {validation_type}"
    )


def validate_request(
    registry: dict[str, Any],
    tool_name: str,
    raw_args: dict[str, str],
) -> tuple[dict[str, Any], dict[str, str]]:
    tool_index = {tool["name"]: tool for tool in registry["tools"]}
    requested_tool = tool_index.get(tool_name)
    if requested_tool is None:
        raise ValueError("requested tool is not present in the reviewed allowlist")

    argument_definitions = requested_tool.get("arguments", [])
    if not isinstance(argument_definitions, list):
        raise ValueError(f"registry arguments for tool {tool_name} must be a JSON array")

    supported_validation_types = get_supported_validation_types(registry)
    allowed_names: set[str] = set()
    validated_args: dict[str, str] = {}

    for argument_definition in sorted(
        argument_definitions,
        key=lambda definition: definition.get("position", 0),
    ):
        if not isinstance(argument_definition, dict):
            raise ValueError(
                f"registry argument definitions for tool {tool_name} must be JSON objects"
            )

        name = argument_definition.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError(
                f"registry argument definition for tool {tool_name} is missing a non-empty name"
            )
        if name in allowed_names:
            raise ValueError(
                f"duplicate registry argument for tool {tool_name}: {name}"
            )
        allowed_names.add(name)

        required = argument_definition.get("required", False)
        if not isinstance(required, bool):
            raise ValueError(f"registry argument {name} required flag must be boolean")

        if name not in raw_args:
            if "default" in argument_definition:
                default_value = argument_definition["default"]
                if not isinstance(default_value, str):
                    raise ValueError(f"registry default for argument {name} must be a string")
                validated_args[name] = validate_argument_value(
                    argument_definition,
                    default_value,
                    supported_validation_types,
                )
            elif required:
                raise ValueError(f"missing required argument: {name}")
            continue

        validated_args[name] = validate_argument_value(
            argument_definition,
            raw_args[name],
            supported_validation_types,
        )

    unknown_args = sorted(set(raw_args) - allowed_names)
    if unknown_args:
        raise ValueError(
            f"unknown declared argument(s): {', '.join(unknown_args)}"
        )

    return requested_tool, validated_args


def get_positive_int_setting(
    registry: dict[str, Any],
    requested_tool: dict[str, Any],
    setting_name: str,
    fallback_value: int,
) -> int:
    if fallback_value < 1:
        raise ValueError(f"fallback {setting_name} must be positive")

    raw_defaults = registry.get("defaults", {})
    if not isinstance(raw_defaults, dict):
        raise ValueError("registry defaults must be a JSON object")

    value = requested_tool.get(setting_name, raw_defaults.get(setting_name, fallback_value))
    if not isinstance(value, int) or value < 1:
        tool_name = requested_tool.get("name", "unknown")
        raise ValueError(f"registry tool {tool_name} has invalid {setting_name}")

    return value



def build_command_argv(
    requested_tool: dict[str, Any],
    validated_args: dict[str, str],
) -> list[str]:
    tool_name = requested_tool.get("name", "unknown")
    script_target = requested_tool.get("script_target")
    if not isinstance(script_target, str) or not script_target:
        raise ValueError(f"registry tool {tool_name} is missing a non-empty script_target")

    argument_definitions = requested_tool.get("arguments", [])
    if not isinstance(argument_definitions, list):
        raise ValueError(f"registry arguments for tool {tool_name} must be a JSON array")

    argv = [script_target, *validate_fixed_arguments(requested_tool)]
    for argument_definition in sorted(
        argument_definitions,
        key=lambda definition: definition.get("position", 0),
    ):
        name = argument_definition.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError(
                f"registry argument definition for tool {tool_name} is missing a non-empty name"
            )
        if name in validated_args:
            argv.append(validated_args[name])

    return argv



def truncate_output(text: str, output_limit_bytes: int) -> tuple[str, bool]:
    if output_limit_bytes < 1:
        raise ValueError("output_limit_bytes must be positive")

    encoded = text.encode("utf-8")
    if len(encoded) <= output_limit_bytes:
        return text, False

    return encoded[:output_limit_bytes].decode("utf-8", errors="ignore"), True



def normalize_stream_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value



def run_tool(
    registry: dict[str, Any],
    requested_tool: dict[str, Any],
    validated_args: dict[str, str],
) -> dict[str, Any]:
    timeout_seconds = get_positive_int_setting(
        registry,
        requested_tool,
        "timeout_seconds",
        30,
    )
    output_limit_bytes = get_positive_int_setting(
        registry,
        requested_tool,
        "output_limit_bytes",
        65536,
    )
    argv = build_command_argv(requested_tool, validated_args)

    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout, stdout_truncated = truncate_output(
            normalize_stream_text(exc.stdout),
            output_limit_bytes,
        )
        timeout_message = f"tool execution exceeded timeout of {timeout_seconds} seconds"
        stderr_text = normalize_stream_text(exc.stderr)
        if stderr_text:
            stderr_text = f"{stderr_text.rstrip()}\n{timeout_message}"
        else:
            stderr_text = timeout_message
        stderr, stderr_truncated = truncate_output(stderr_text, output_limit_bytes)
        return {
            "status": "timeout",
            "exit_code": None,
            "stdout": stdout,
            "stderr": stderr,
            "truncated": stdout_truncated or stderr_truncated,
        }
    except OSError as exc:
        stderr, stderr_truncated = truncate_output(str(exc), output_limit_bytes)
        return {
            "status": "error",
            "exit_code": None,
            "stdout": "",
            "stderr": stderr,
            "truncated": stderr_truncated,
        }

    stdout, stdout_truncated = truncate_output(completed.stdout, output_limit_bytes)
    stderr, stderr_truncated = truncate_output(completed.stderr, output_limit_bytes)
    truncated = stdout_truncated or stderr_truncated

    status = "ok" if completed.returncode == 0 else "error"
    if truncated:
        status = "truncated"

    return {
        "status": status,
        "exit_code": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "truncated": truncated,
    }


def parse_cli_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail-closed AI-OPS tool runner for reviewed diagnostic tools."
    )
    parser.add_argument("tool_name", help="Requested reviewed diagnostic tool name")
    parser.add_argument(
        "--registry",
        default=str(default_registry_path()),
        help="Path to tool registry JSON file",
    )
    parser.add_argument(
        "--arg",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Declared tool argument in key=value form for reviewed registry tools.",
    )
    parser.add_argument(
        "--request-id",
        default=None,
        help="Optional caller-provided request or correlation identifier",
    )
    parser.add_argument(
        "--client-id",
        choices=[MCP_AUDIT_CLIENT_ID],
        default=None,
        help="Optional fixed audit client identifier for local MCP calls.",
    )
    parser.add_argument(
        "--transport",
        choices=[MCP_AUDIT_TRANSPORT],
        default=None,
        help="Optional fixed audit transport for local MCP calls.",
    )
    parser.add_argument(
        "--audit-path",
        default=str(default_audit_path()),
        help="Path to JSON Lines audit log file",
    )
    return parser.parse_args(argv)


def emit_envelope(envelope: dict[str, Any]) -> None:
    json.dump(envelope, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    args = parse_cli_args(argv)
    started = time.monotonic()

    try:
        registry = load_registry(args.registry)
    except Exception as exc:  # fail closed during startup
        envelope = build_result_envelope(
            args.tool_name,
            "error",
            arguments={},
            stderr=str(exc),
            duration_ms=int((time.monotonic() - started) * 1000),
            request_id=args.request_id,
        )
        try:
            write_audit_event(
                args.audit_path,
                build_audit_event(
                    envelope,
                    client_id=args.client_id,
                    transport=args.transport,
                ),
            )
        except Exception as audit_exc:
            envelope = build_result_envelope(
                args.tool_name,
                "error",
                arguments={},
                stderr=f"failed to write audit event: {audit_exc}",
                duration_ms=int((time.monotonic() - started) * 1000),
                request_id=args.request_id,
            )
        emit_envelope(envelope)
        return STATUS_EXIT_CODES.get(envelope["status"], 1)

    try:
        declared_args = parse_declared_args(args.arg)
    except ValueError as exc:
        envelope = build_result_envelope(
            args.tool_name,
            "validation_error",
            arguments={},
            stderr=str(exc),
            duration_ms=int((time.monotonic() - started) * 1000),
            request_id=args.request_id,
        )
        try:
            write_audit_event(
                args.audit_path,
                build_audit_event(
                    envelope,
                    client_id=args.client_id,
                    transport=args.transport,
                ),
            )
        except Exception as audit_exc:
            envelope = build_result_envelope(
                args.tool_name,
                "error",
                arguments={},
                stderr=f"failed to write audit event: {audit_exc}",
                duration_ms=int((time.monotonic() - started) * 1000),
                request_id=args.request_id,
            )
        emit_envelope(envelope)
        return STATUS_EXIT_CODES.get(envelope["status"], 1)

    tool_index = {tool["name"]: tool for tool in registry["tools"]}
    requested_tool = tool_index.get(args.tool_name)

    if requested_tool is None:
        envelope = build_result_envelope(
            args.tool_name,
            "denied",
            arguments=declared_args,
            stderr="requested tool is not present in the reviewed allowlist",
            duration_ms=int((time.monotonic() - started) * 1000),
            request_id=args.request_id,
        )
    elif not requested_tool.get("available", True):
        envelope = build_result_envelope(
            args.tool_name,
            "unavailable",
            arguments=declared_args,
            stderr=requested_tool.get(
                "unavailable_reason",
                "tool is intentionally unavailable",
            ),
            duration_ms=int((time.monotonic() - started) * 1000),
            request_id=args.request_id,
        )
    else:
        try:
            requested_tool, validated_args = validate_request(
                registry,
                args.tool_name,
                declared_args,
            )
            execution_result = run_tool(registry, requested_tool, validated_args)
        except ValueError as exc:
            envelope = build_result_envelope(
                args.tool_name,
                "validation_error",
                arguments={},
                stderr=str(exc),
                duration_ms=int((time.monotonic() - started) * 1000),
                request_id=args.request_id,
            )
        except Exception as exc:  # fail closed during execution
            envelope = build_result_envelope(
                args.tool_name,
                "error",
                arguments={},
                stderr=str(exc),
                duration_ms=int((time.monotonic() - started) * 1000),
                request_id=args.request_id,
            )
        else:
            envelope = build_result_envelope(
                args.tool_name,
                execution_result["status"],
                arguments=validated_args,
                exit_code=execution_result["exit_code"],
                stdout=execution_result["stdout"],
                stderr=execution_result["stderr"],
                duration_ms=int((time.monotonic() - started) * 1000),
                truncated=execution_result["truncated"],
                request_id=args.request_id,
            )

    try:
        write_audit_event(
            args.audit_path,
            build_audit_event(
                envelope,
                client_id=args.client_id,
                transport=args.transport,
            ),
        )
    except Exception as exc:
        envelope = build_result_envelope(
            args.tool_name,
            "error",
            arguments={},
            stderr=f"failed to write audit event: {exc}",
            duration_ms=int((time.monotonic() - started) * 1000),
            request_id=args.request_id,
        )

    emit_envelope(envelope)
    return STATUS_EXIT_CODES.get(envelope["status"], 1)


if __name__ == "__main__":
    raise SystemExit(main())
