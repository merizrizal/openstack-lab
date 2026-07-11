#!/usr/bin/env python3
"""Fail-closed stdio MCP adapter contract with no executable tools."""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

MCP_SERVER_NAME = "openstack-ai-ops"
MCP_SERVER_VERSION = "0.1.0"
ADAPTER_UNAVAILABLE_MESSAGE = "adapter unavailable: executable MCP tools are not enabled"
INITIAL_MCP_TOOL_NAME = "project_resource_summary"
LOW_READONLY_PROJECT_RISK = "low_readonly_project_scope"
TOOL_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class AdapterPaths:
    """Fixed runtime paths needed before the adapter can serve stdio requests."""

    policy_path: Path
    registry_path: Path


def default_adapter_paths() -> AdapterPaths:
    return AdapterPaths(
        policy_path=Path("/opt/openstack-ai-ops/mcp/mcp_policy.json"),
        registry_path=Path(
            "/opt/openstack-ai-ops/scripts/tool_runner/tool_registry.json"
        ),
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
        for key in ("pattern", "allowed_values", "default"):
            if key not in argument:
                continue
            schema_key = "enum" if key == "allowed_values" else key
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

    server = Server(MCP_SERVER_NAME, version=MCP_SERVER_VERSION)

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [types.Tool(**tool) for tool in exposed_tools]

    @server.call_tool(validate_input=False)
    async def handle_call_tool(
        tool_name: str,
        arguments: dict[str, Any],
    ) -> types.CallToolResult:
        return await unavailable_tool_call(tool_name, arguments)

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
