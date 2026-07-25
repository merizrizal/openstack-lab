from __future__ import annotations

import asyncio
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from openstack_ai_ops_orchestrator.contracts import RuntimePolicy, ToolCallRequest
from openstack_ai_ops_orchestrator.mcp_bridge import (
    BridgeRequest,
    BridgeResponse,
    UnixSocketBridge,
)
from openstack_ai_ops_orchestrator.mcp_stdio_proxy import (
    McpStdioProxy,
    McpStdioProxyError,
)


def policy() -> RuntimePolicy:
    return RuntimePolicy(60, 5, 8192, "model", "/fixed")


def request() -> ToolCallRequest:
    return ToolCallRequest("project_resource_summary", (), 1)


def raw_result(
    content: str = '{"username":"fixture-user","project_count":1}',
) -> dict[str, object]:
    return {
        "tool_name": "project_resource_summary",
        "category": "ok",
        "content": content,
        "truncated": False,
        "request_sequence_number": 1,
    }


def test_proxy_uses_fixed_unix_socket_and_redacts_before_returning(
    tmp_path: Path,
) -> None:
    calls: list[BridgeRequest] = []

    async def execute(value: BridgeRequest) -> BridgeResponse:
        calls.append(value)
        return BridgeResponse(value.correlation_id, 1, raw_result())

    async def run() -> None:
        path = str(tmp_path / "bridge.sock")
        bridge = UnixSocketBridge(
            approved_peer_uid=os.getuid(), executor=execute, timeout_seconds=1
        )
        server = await asyncio.start_unix_server(bridge.serve, path=path)
        try:
            with patch(
                "openstack_ai_ops_orchestrator.mcp_stdio_proxy.ASSISTANT_MCP_BRIDGE_SOCKET",
                path,
            ):
                proxy = McpStdioProxy(policy=policy())
                result = await proxy.forward(request(), "correlation-1")
                assert "fixture-user" not in result.redacted_content
                await proxy.aclose()
                with pytest.raises(McpStdioProxyError, match="^proxy_closed$"):
                    await proxy.forward(request(), "correlation-2")
        finally:
            server.close()
            await server.wait_closed()

    asyncio.run(run())
    assert calls == [BridgeRequest("correlation-1", request())]


def test_proxy_rejects_closed_or_malformed_bridge_reply(tmp_path: Path) -> None:
    async def execute(value: BridgeRequest) -> BridgeResponse:
        return BridgeResponse(
            value.correlation_id, 1, raw_result("not-json fixture-secret")
        )

    async def run() -> None:
        path = str(tmp_path / "bridge.sock")
        bridge = UnixSocketBridge(
            approved_peer_uid=os.getuid(), executor=execute, timeout_seconds=1
        )
        server = await asyncio.start_unix_server(bridge.serve, path=path)
        try:
            with patch(
                "openstack_ai_ops_orchestrator.mcp_stdio_proxy.ASSISTANT_MCP_BRIDGE_SOCKET",
                path,
            ):
                with pytest.raises(
                    McpStdioProxyError, match="^mcp_bridge_denied$"
                ) as error:
                    await McpStdioProxy(policy=policy()).forward(
                        request(), "correlation-1"
                    )
                assert "fixture-secret" not in repr(error.value)
        finally:
            server.close()
            await server.wait_closed()

    asyncio.run(run())
