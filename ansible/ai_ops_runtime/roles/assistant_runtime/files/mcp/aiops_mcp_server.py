#!/usr/bin/env python3
"""Fail-closed stdio MCP adapter for the initial reviewed runner tool."""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

MCP_SERVER_NAME = "openstack-ai-ops"
MCP_SERVER_VERSION = "0.1.0"
ADAPTER_UNAVAILABLE_MESSAGE = "adapter unavailable: requested MCP tool is not enabled"
INITIAL_MCP_TOOL_NAME = "project_resource_summary"
LOW_READONLY_PROJECT_RISK = "low_readonly_project_scope"
TOOL_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
MCP_REQUEST_ID_PREFIX = "mcp-stdio-"
MCP_AUDIT_CLIENT_ID = "local-mcp-client"
MCP_AUDIT_TRANSPORT = "stdio"
MCP_OUTER_TIMEOUT_GRACE_SECONDS = 5
MCP_MAX_RUNNER_STREAM_BYTES = 131072
MCP_MAX_SERVER_IDENTIFIER_LENGTH = 128
MCP_MAX_RUNNER_ENVELOPE_FIXED_OVERHEAD_BYTES = 8192
MCP_MAX_RUNNER_ENVELOPE_BYTES = (
    (2 * MCP_MAX_RUNNER_STREAM_BYTES)
    + MCP_MAX_SERVER_IDENTIFIER_LENGTH
    + MCP_MAX_RUNNER_ENVELOPE_FIXED_OVERHEAD_BYTES
)
MCP_ERROR_STATUSES = {
    "error",
    "denied",
    "validation_error",
    "timeout",
    "unavailable",
}
RUNNER_ENVELOPE_STATUSES = MCP_ERROR_STATUSES | {"ok", "truncated"}
RUNNER_ENVELOPE_FIELDS = {
    "tool",
    "status",
    "arguments",
    "exit_code",
    "stdout",
    "stderr",
    "duration_ms",
    "truncated",
    "timestamp",
    "request_id",
}


@dataclass(frozen=True)
class AdapterPaths:
    """Fixed runtime paths used by the stdio adapter and runner subprocess."""

    policy_path: Path
    registry_path: Path
    python_path: Path
    runner_path: Path
    audit_path: Path


def default_adapter_paths() -> AdapterPaths:
    return AdapterPaths(
        policy_path=Path("/opt/openstack-ai-ops/mcp/mcp_policy.json"),
        registry_path=Path(
            "/opt/openstack-ai-ops/scripts/tool_runner/tool_registry.json"
        ),
        python_path=Path("/opt/openstack-ai-ops/.venv/bin/python"),
        runner_path=Path(
            "/opt/openstack-ai-ops/scripts/tool_runner/aiops_tool_runner.py"
        ),
        audit_path=Path("/opt/openstack-ai-ops/audit/tool-runner.jsonl"),
    )


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to load {label}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return data


def _require_unique_string_list(
    mapping: dict[str, Any],
    key: str,
    label: str,
) -> list[str]:
    values = mapping.get(key)
    if (
        not isinstance(values, list)
        or not values
        or any(not isinstance(value, str) or not value for value in values)
        or len(set(values)) != len(values)
    ):
        raise ValueError(f"{label} must be a non-empty JSON array of unique strings")
    return values


def _validate_argument_definition(
    argument: dict[str, Any],
    tool_name: str,
    seen_names: set[str],
    seen_positions: set[int],
) -> None:
    name = argument.get("name")
    if not isinstance(name, str) or not TOOL_NAME_RE.fullmatch(name):
        raise ValueError(f"registry tool {tool_name} has an invalid argument name")
    if name in seen_names:
        raise ValueError(f"registry tool {tool_name} has duplicate argument {name}")
    seen_names.add(name)

    position = argument.get("position")
    if not isinstance(position, int) or isinstance(position, bool) or position < 1:
        raise ValueError(f"registry argument {name} has an invalid position")
    if position in seen_positions:
        raise ValueError(f"registry tool {tool_name} has duplicate argument position")
    seen_positions.add(position)

    if not isinstance(argument.get("required"), bool):
        raise ValueError(f"registry argument {name} must declare required as a boolean")
    if not isinstance(argument.get("validation"), str) or not argument["validation"]:
        raise ValueError(f"registry argument {name} has an invalid validation type")
    if not isinstance(argument.get("description"), str) or not argument["description"]:
        raise ValueError(f"registry argument {name} has an invalid description")

    max_length = argument.get("max_length")
    if max_length is not None and (
        not isinstance(max_length, int)
        or isinstance(max_length, bool)
        or max_length < 1
    ):
        raise ValueError(f"registry argument {name} has an invalid max_length")

    pattern = argument.get("pattern")
    if pattern is not None:
        if not isinstance(pattern, str):
            raise ValueError(f"registry argument {name} has an invalid pattern")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise ValueError(f"registry argument {name} has an invalid pattern") from exc

    allowed_values = argument.get("allowed_values")
    if allowed_values is not None:
        allowed_values = _require_unique_string_list(
            argument,
            "allowed_values",
            f"registry argument {name} allowed_values",
        )

    default = argument.get("default")
    if default is not None:
        if not isinstance(default, str):
            raise ValueError(f"registry argument {name} has an invalid default")
        if allowed_values is not None and default not in allowed_values:
            raise ValueError(f"registry argument {name} default is not allowed")


def _validate_registry_tool(tool: dict[str, Any]) -> None:
    name = tool.get("name")
    if not isinstance(name, str) or not TOOL_NAME_RE.fullmatch(name):
        raise ValueError("registry tool has an invalid name")
    for key in ("description", "credential_profile", "risk_level"):
        if not isinstance(tool.get(key), str) or not tool[key]:
            raise ValueError(f"registry tool {name} has an invalid {key}")
    if not isinstance(tool.get("available"), bool):
        raise ValueError(f"registry tool {name} must declare availability")

    capabilities = tool.get("capabilities", [])
    if not isinstance(capabilities, list) or any(
        not isinstance(capability, str) or not capability
        for capability in capabilities
    ):
        raise ValueError(f"registry tool {name} has invalid capabilities")

    fixed_arguments = tool.get("fixed_arguments")
    if fixed_arguments is not None:
        _require_unique_string_list(
            tool,
            "fixed_arguments",
            f"registry tool {name} fixed_arguments",
        )

    arguments = tool.get("arguments")
    if not isinstance(arguments, list):
        raise ValueError(f"registry tool {name} arguments must be a JSON array")
    seen_names: set[str] = set()
    seen_positions: set[int] = set()
    for argument in arguments:
        if not isinstance(argument, dict):
            raise ValueError(f"registry tool {name} has an invalid argument")
        _validate_argument_definition(argument, name, seen_names, seen_positions)


def validate_mcp_policy(policy: dict[str, Any]) -> dict[str, Any]:
    expected_keys = {"tool_allowlist", "enabled_risk_levels"}
    if set(policy) != expected_keys:
        raise ValueError("MCP policy must contain only reviewed exposure settings")
    _require_unique_string_list(policy, "tool_allowlist", "MCP policy tool_allowlist")
    _require_unique_string_list(
        policy,
        "enabled_risk_levels",
        "MCP policy enabled_risk_levels",
    )
    return policy


def validate_runner_registry(registry: dict[str, Any]) -> dict[str, Any]:
    policy = registry.get("policy")
    if not isinstance(policy, dict):
        raise ValueError("runner registry policy must be a JSON object")
    forbidden_capabilities = _require_unique_string_list(
        policy,
        "forbidden_capabilities",
        "runner registry forbidden_capabilities",
    )

    tools = registry.get("tools")
    if not isinstance(tools, list):
        raise ValueError("runner registry tools must be a JSON array")
    seen_names: set[str] = set()
    forbidden_capability_set = set(forbidden_capabilities)
    for tool in tools:
        if not isinstance(tool, dict):
            raise ValueError("runner registry tool entries must be JSON objects")
        _validate_registry_tool(tool)
        tool_name = tool["name"]
        if tool_name in seen_names:
            raise ValueError(f"runner registry has duplicate tool {tool_name}")
        seen_names.add(tool_name)
        capabilities = set(tool.get("capabilities", []))
        if tool_name in forbidden_capability_set or capabilities.intersection(
            forbidden_capability_set
        ):
            raise ValueError(f"runner registry tool {tool_name} has forbidden capability")
    return registry


def load_mcp_policy(path: Path) -> dict[str, Any]:
    return validate_mcp_policy(_load_json_object(path, "MCP policy"))


def load_runner_registry(path: Path) -> dict[str, Any]:
    return validate_runner_registry(_load_json_object(path, "runner registry"))


def build_mcp_tool_schema(registry_tool: dict[str, Any]) -> dict[str, Any]:
    """Derive an MCP tool definition without exposing fixed runner arguments."""

    _validate_registry_tool(registry_tool)
    properties: dict[str, dict[str, Any]] = {}
    required: list[str] = []
    for argument in sorted(registry_tool["arguments"], key=lambda item: item["position"]):
        property_schema: dict[str, Any] = {
            "type": "string",
            "description": argument["description"],
        }
        for key in ("pattern", "allowed_values", "default", "max_length"):
            if key not in argument:
                continue
            schema_key = {
                "allowed_values": "enum",
                "max_length": "maxLength",
            }.get(key, key)
            property_schema[schema_key] = argument[key]
        properties[argument["name"]] = property_schema
        if argument["required"]:
            required.append(argument["name"])

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        input_schema["required"] = required

    return {
        "name": registry_tool["name"],
        "description": (
            f"{registry_tool['description']} Read-only diagnostic. "
            f"Credential class: {registry_tool['credential_profile']}. "
            f"Risk class: {registry_tool['risk_level']}. "
            "Evidence may be unavailable or truncated."
        ),
        "inputSchema": input_schema,
    }


def list_exposed_tools(
    registry: dict[str, Any],
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    validate_runner_registry(registry)
    validate_mcp_policy(policy)
    tools_by_name = {tool["name"]: tool for tool in registry["tools"]}
    exposed_tools: list[dict[str, Any]] = []
    for tool_name in policy["tool_allowlist"]:
        tool = tools_by_name.get(tool_name)
        if tool is None:
            raise ValueError(f"MCP policy names unknown tool {tool_name}")
        if not tool["available"]:
            raise ValueError(f"MCP policy names unavailable tool {tool_name}")
        if tool["risk_level"] not in policy["enabled_risk_levels"]:
            raise ValueError(f"MCP policy does not enable tool risk {tool_name}")
        exposed_tools.append(build_mcp_tool_schema(tool))
    return exposed_tools


class RunnerProtocolError(ValueError):
    """Raised when the adapter cannot trust a runner subprocess response."""


def runner_timeout_seconds(registry_tool: dict[str, Any]) -> int:
    timeout = registry_tool.get("timeout_seconds", 30)
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
        raise ValueError("exposed runner tool has an invalid timeout_seconds value")
    return timeout


def new_request_id() -> str:
    return f"{MCP_REQUEST_ID_PREFIX}{uuid.uuid4()}"


def _validate_envelope_field_types(envelope: dict[str, Any]) -> None:
    if not isinstance(envelope["arguments"], dict):
        raise RunnerProtocolError("runner envelope arguments must be an object")
    if envelope["exit_code"] is not None and (
        not isinstance(envelope["exit_code"], int)
        or isinstance(envelope["exit_code"], bool)
    ):
        raise RunnerProtocolError("runner envelope exit_code must be an integer or null")
    for field in ("stdout", "stderr", "timestamp"):
        if not isinstance(envelope[field], str):
            raise RunnerProtocolError(f"runner envelope {field} must be a string")
    if not isinstance(envelope["duration_ms"], int) or isinstance(
        envelope["duration_ms"], bool
    ) or envelope["duration_ms"] < 0:
        raise RunnerProtocolError("runner envelope duration_ms must be non-negative")
    if not isinstance(envelope["truncated"], bool):
        raise RunnerProtocolError("runner envelope truncated must be a boolean")


def validate_runner_envelope(
    envelope: dict[str, Any],
    expected_tool: str,
    request_id: str,
) -> dict[str, Any]:
    if not RUNNER_ENVELOPE_FIELDS.issubset(envelope):
        raise RunnerProtocolError("runner envelope is missing required fields")
    if envelope["tool"] != expected_tool or not isinstance(envelope["tool"], str):
        raise RunnerProtocolError("runner envelope tool does not match request")
    if envelope["request_id"] != request_id or not isinstance(
        envelope["request_id"], str
    ):
        raise RunnerProtocolError("runner envelope request_id does not match request")
    if not isinstance(envelope["status"], str) or (
        envelope["status"] not in RUNNER_ENVELOPE_STATUSES
    ):
        raise RunnerProtocolError("runner envelope has an invalid status")
    _validate_envelope_field_types(envelope)
    for field in ("stdout", "stderr"):
        if len(envelope[field].encode("utf-8")) > MCP_MAX_RUNNER_STREAM_BYTES:
            raise RunnerProtocolError("runner envelope stream exceeds reviewed bound")
    return envelope


async def _terminate_runner(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    process.terminate()
    try:
        await asyncio.wait_for(process.wait(), timeout=1)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()


async def invoke_runner(
    tool_name: str,
    arguments: dict[str, Any],
    request_id: str,
    paths: AdapterPaths,
    timeout_seconds: int,
) -> dict[str, Any]:
    if tool_name != INITIAL_MCP_TOOL_NAME or arguments:
        raise RunnerProtocolError("runner invocation is not approved for this MCP tool")
    argv = [
        str(paths.python_path),
        str(paths.runner_path),
        tool_name,
        "--registry",
        str(paths.registry_path),
        "--audit-path",
        str(paths.audit_path),
        "--request-id",
        request_id,
        "--client-id",
        MCP_AUDIT_CLIENT_ID,
        "--transport",
        MCP_AUDIT_TRANSPORT,
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise RunnerProtocolError("runner subprocess could not be started") from exc

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout_seconds + MCP_OUTER_TIMEOUT_GRACE_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        await _terminate_runner(process)
        raise RunnerProtocolError("runner subprocess exceeded the adapter timeout") from exc
    except asyncio.CancelledError:
        await _terminate_runner(process)
        raise

    if stderr:
        raise RunnerProtocolError("runner wrote unexpected stderr output")
    if len(stdout) > MCP_MAX_RUNNER_ENVELOPE_BYTES:
        raise RunnerProtocolError("runner envelope exceeds reviewed bound")
    try:
        lines = stdout.decode("utf-8").splitlines()
        if len(lines) != 1 or not lines[0]:
            raise RunnerProtocolError("runner returned invalid JSON Lines output")
        envelope = json.loads(lines[0])
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RunnerProtocolError("runner returned malformed JSON output") from exc
    if not isinstance(envelope, dict):
        raise RunnerProtocolError("runner envelope must be a JSON object")
    return validate_runner_envelope(envelope, tool_name, request_id)


def map_envelope_to_mcp_result(envelope: dict[str, Any]) -> types.CallToolResult:
    return types.CallToolResult(
        content=[
            types.TextContent(
                type="text",
                text=json.dumps(envelope, sort_keys=True),
            )
        ],
        structuredContent=envelope,
        isError=envelope["status"] in MCP_ERROR_STATUSES,
    )


def adapter_error_result(request_id: str, message: str) -> types.CallToolResult:
    return types.CallToolResult(
        content=[
            types.TextContent(
                type="text",
                text=json.dumps({"request_id": request_id, "error": message}),
            )
        ],
        isError=True,
    )


async def unavailable_tool_call(
    tool_name: str,
    arguments: dict[str, Any],
) -> types.CallToolResult:
    """Fail closed without invoking the runner or any diagnostic script."""

    del tool_name, arguments
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=ADAPTER_UNAVAILABLE_MESSAGE)],
        isError=True,
    )


def create_server(paths: AdapterPaths | None = None) -> Server:
    """Build a stdio-only server after validating its fixed JSON inputs."""

    resolved_paths = paths or default_adapter_paths()
    policy = load_mcp_policy(resolved_paths.policy_path)
    registry = load_runner_registry(resolved_paths.registry_path)
    exposed_tools = list_exposed_tools(registry, policy)
    exposed_tool_names = {tool["name"] for tool in exposed_tools}
    registry_tools_by_name = {tool["name"]: tool for tool in registry["tools"]}
    runner_timeout = runner_timeout_seconds(
        registry_tools_by_name[INITIAL_MCP_TOOL_NAME]
    )
    runner_semaphore = asyncio.Semaphore(1)

    server = Server(MCP_SERVER_NAME, version=MCP_SERVER_VERSION)

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [types.Tool(**tool) for tool in exposed_tools]

    @server.call_tool(validate_input=False)
    async def handle_call_tool(
        tool_name: str,
        arguments: dict[str, Any],
    ) -> types.CallToolResult:
        if tool_name not in exposed_tool_names or tool_name != INITIAL_MCP_TOOL_NAME:
            return await unavailable_tool_call(tool_name, arguments)
        if arguments:
            return await unavailable_tool_call(tool_name, arguments)

        request_id = new_request_id()
        try:
            async with runner_semaphore:
                envelope = await invoke_runner(
                    tool_name,
                    arguments,
                    request_id,
                    resolved_paths,
                    runner_timeout,
                )
        except RunnerProtocolError as exc:
            return adapter_error_result(request_id, str(exc))
        return map_envelope_to_mcp_result(envelope)

    return server


async def run_server(paths: AdapterPaths | None = None) -> None:
    """Serve the fail-closed contract over the SDK's local stdio transport."""

    server = create_server(paths)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> int:
    asyncio.run(run_server())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
