"""Credential-free stdio proxy over the fixed assistant Unix socket."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from typing import Any, Protocol

from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from .contracts import (
    RuntimePolicy,
    SafeToolResult,
    ToolCallRequest,
    ToolResultCategory,
)
from .redaction import RedactionError, redact_tool_result

ASSISTANT_MCP_BRIDGE_SOCKET = "/run/openstack-ai-ops/assistant-mcp-bridge.sock"
_MAXIMUM_MESSAGE_BYTES = 270464


class McpStdioProxyError(RuntimeError):
    """Fixed proxy failure category that never includes tool content."""


_MODEL_FACING_TOOL_NAME = "project_resource_summary"
_MODEL_FACING_CORRELATION_ID = "model-facing-mcp-1"
_MODEL_FACING_POLICY = RuntimePolicy(
    deadline_seconds=30,
    maximum_event_count=3,
    maximum_output_bytes=1024,
    model_alias="remote-acceptance",
    fixed_working_directory="/var/lib/aiops-orchestrator/work",
)


class _BridgeProxy(Protocol):
    async def forward(
        self, request: ToolCallRequest, correlation_id: str
    ) -> SafeToolResult:
        """Return one bridge-validated, redacted result."""

    async def aclose(self) -> None:
        """Close the exact proxy-owned socket resources."""


class ModelFacingMcpServer:
    """One-call credential-free stdio MCP surface for the reviewed tool only."""

    def __init__(self, proxy: _BridgeProxy) -> None:
        self._proxy = proxy
        self._consumed = False

    async def call_tool(
        self, tool_name: str, arguments: Mapping[str, object] | None
    ) -> types.CallToolResult:
        if self._consumed:
            return self._error_result()
        self._consumed = True
        if tool_name != _MODEL_FACING_TOOL_NAME or arguments is None or bool(arguments):
            return self._error_result()
        try:
            result = await self._proxy.forward(
                ToolCallRequest(_MODEL_FACING_TOOL_NAME, (), 1),
                _MODEL_FACING_CORRELATION_ID,
            )
        except McpStdioProxyError:
            return self._error_result()
        payload = self._result_mapping(result)
        return types.CallToolResult(
            content=[
                types.TextContent(type="text", text=json.dumps(payload, sort_keys=True))
            ],
            structuredContent=payload,
            isError=result.category is not ToolResultCategory.OK,
        )

    def create_server(self) -> Server:
        server = Server("openstack-ai-ops-model-proxy", version="0.1.0")

        @server.list_tools()  # type: ignore[no-untyped-call, misc]
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name=_MODEL_FACING_TOOL_NAME,
                    description="Read-only project resource summary.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                )
            ]

        @server.call_tool(validate_input=False)  # type: ignore[misc]
        async def handle_call_tool(
            tool_name: str, arguments: dict[str, Any]
        ) -> types.CallToolResult:
            return await self.call_tool(tool_name, arguments)

        return server

    async def aclose(self) -> None:
        await self._proxy.aclose()

    @staticmethod
    def _error_result() -> types.CallToolResult:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="MCP tool unavailable")],
            isError=True,
        )

    @staticmethod
    def _result_mapping(result: SafeToolResult) -> dict[str, object]:
        return {
            "tool_name": result.tool_name,
            "category": result.category.value,
            "content": result.redacted_content,
            "truncated": result.truncated,
            "request_sequence_number": result.request_sequence_number,
        }


def create_model_facing_server(
    proxy: _BridgeProxy | None = None,
) -> ModelFacingMcpServer:
    """Build the launchable fixed stdio surface without caller configuration."""
    return ModelFacingMcpServer(proxy or McpStdioProxy(policy=_MODEL_FACING_POLICY))


async def run_model_facing_server() -> None:
    """Serve the credential-free MCP surface over process stdio only."""
    facade = create_model_facing_server()
    try:
        server = facade.create_server()
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    finally:
        await facade.aclose()


def main() -> int:
    asyncio.run(run_model_facing_server())
    return 0


class McpStdioProxy:
    """Forward one reviewed request and redact the bridge reply before return."""

    def __init__(self, *, policy: RuntimePolicy) -> None:
        self._policy = policy
        self._closed = False

    async def forward(
        self, request: ToolCallRequest, correlation_id: str
    ) -> SafeToolResult:
        if self._closed:
            raise McpStdioProxyError("proxy_closed")
        try:
            reader, writer = await asyncio.open_unix_connection(
                ASSISTANT_MCP_BRIDGE_SOCKET
            )
            try:
                await self._write_message(
                    writer,
                    {
                        "correlation_id": correlation_id,
                        "tool": {
                            "tool_name": request.tool_name,
                            "arguments": dict(request.arguments),
                            "sequence_number": request.sequence_number,
                        },
                    },
                )
                response = self._decode_response(await self._read_message(reader))
            finally:
                writer.close()
                await writer.wait_closed()
            result = redact_tool_result(
                response["raw_result"],
                maximum_raw_bytes=self._policy.maximum_mcp_result_bytes,
                maximum_content_bytes=self._policy.maximum_tool_content_bytes,
                maximum_redactions=self._policy.maximum_redaction_count,
            )
        except (OSError, asyncio.IncompleteReadError, RedactionError, ValueError):
            raise McpStdioProxyError("mcp_bridge_denied") from None
        if (
            result.tool_name != request.tool_name
            or result.request_sequence_number != request.sequence_number
        ):
            raise McpStdioProxyError("mcp_result_rejected")
        return result

    async def aclose(self) -> None:
        self._closed = True

    @staticmethod
    async def _read_message(reader: asyncio.StreamReader) -> bytes:
        message = await reader.readuntil(b"\n")
        if not message or len(message) > _MAXIMUM_MESSAGE_BYTES:
            raise ValueError("proxy response is invalid")
        return message[:-1]

    @staticmethod
    async def _write_message(
        writer: asyncio.StreamWriter, value: Mapping[str, object]
    ) -> None:
        encoded = json.dumps(value, separators=(",", ":")).encode("utf-8")
        if len(encoded) > _MAXIMUM_MESSAGE_BYTES:
            raise ValueError("proxy request is invalid")
        writer.write(encoded + b"\n")
        await writer.drain()

    @staticmethod
    def _decode_response(message: bytes) -> Mapping[str, Mapping[str, object]]:
        value = json.loads(message)
        expected = {"correlation_id", "request_sequence_number", "raw_result"}
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ValueError("proxy response is invalid")
        raw_result = value["raw_result"]
        if not isinstance(raw_result, Mapping):
            raise ValueError("proxy response is invalid")
        return {"raw_result": raw_result}


if __name__ == "__main__":
    raise SystemExit(main())
