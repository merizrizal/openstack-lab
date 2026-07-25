"""Credential-free stdio proxy over the fixed assistant Unix socket."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping

from .contracts import RuntimePolicy, SafeToolResult, ToolCallRequest
from .redaction import RedactionError, redact_tool_result

ASSISTANT_MCP_BRIDGE_SOCKET = "/run/openstack-ai-ops/assistant-mcp-bridge.sock"
_MAXIMUM_MESSAGE_BYTES = 270464


class McpStdioProxyError(RuntimeError):
    """Fixed proxy failure category that never includes tool content."""


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
