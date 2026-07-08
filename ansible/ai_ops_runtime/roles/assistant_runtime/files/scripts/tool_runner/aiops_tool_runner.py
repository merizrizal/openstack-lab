#!/usr/bin/env python3
"""Fail-closed AI-OPS tool runner stub for Phase 04 Chunk 2."""

from __future__ import annotations

import argparse
import json
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


def default_registry_path() -> Path:
    return Path(__file__).with_name("tool_registry.json")


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
        "arguments": arguments or {},
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "duration_ms": duration_ms,
        "truncated": truncated,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "request_id": request_id or str(uuid.uuid4()),
    }


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


def parse_cli_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail-closed AI-OPS tool runner stub for reviewed diagnostic tools."
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
        help="Declared tool argument. Chunk 2 stores arguments only; it does not validate them yet.",
    )
    parser.add_argument(
        "--request-id",
        default=None,
        help="Optional caller-provided request or correlation identifier",
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
        declared_args = parse_declared_args(args.arg)
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
            envelope = build_result_envelope(
                args.tool_name,
                "error",
                arguments=declared_args,
                stderr="tool execution not implemented in Chunk 2 stub",
                duration_ms=int((time.monotonic() - started) * 1000),
                request_id=args.request_id,
            )
    except Exception as exc:  # fail closed during stub phase
        envelope = build_result_envelope(
            args.tool_name if "args" in locals() else "unknown",
            "error",
            arguments={},
            stderr=str(exc),
            duration_ms=int((time.monotonic() - started) * 1000),
            request_id=getattr(args, "request_id", None) if "args" in locals() else None,
        )

    emit_envelope(envelope)
    return STATUS_EXIT_CODES.get(envelope["status"], 1)


if __name__ == "__main__":
    raise SystemExit(main())
