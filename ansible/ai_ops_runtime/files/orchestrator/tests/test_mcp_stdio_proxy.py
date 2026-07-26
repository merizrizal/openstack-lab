from __future__ import annotations

import asyncio
import os
from pathlib import Path
from unittest.mock import patch

import anyio
import pytest
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from mcp import ClientSession
from mcp.shared.message import SessionMessage

from openstack_ai_ops_orchestrator.contracts import (
    RuntimePolicy,
    SafeToolResult,
    ToolCallRequest,
)
from openstack_ai_ops_orchestrator.mcp_bridge import (
    AssistantBridgeExecutor,
    BridgeRequest,
    BridgeResponse,
    UnixSocketBridge,
)
from openstack_ai_ops_orchestrator.mcp_stdio_proxy import (
    McpStdioProxy,
    McpStdioProxyError,
    ModelFacingMcpServer,
)
from openstack_ai_ops_orchestrator.redaction import redact_tool_result


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


class FixtureBridgeProxy:
    def __init__(self) -> None:
        self.calls: list[tuple[ToolCallRequest, str]] = []
        self.closed = False

    async def forward(
        self, value: ToolCallRequest, correlation_id: str
    ) -> SafeToolResult:
        self.calls.append((value, correlation_id))
        return redact_tool_result(
            raw_result(),
            maximum_raw_bytes=policy().maximum_mcp_result_bytes,
            maximum_content_bytes=policy().maximum_tool_content_bytes,
            maximum_redactions=policy().maximum_redaction_count,
        )

    async def aclose(self) -> None:
        self.closed = True


def test_model_facing_server_exposes_one_fixed_redacted_tool_result() -> None:
    proxy = FixtureBridgeProxy()
    server = ModelFacingMcpServer(proxy)

    async def run() -> None:
        assert server.create_server() is not None
        response = await server.call_tool("project_resource_summary", {})
        assert response.isError is False
        assert response.structuredContent == {
            "tool_name": "project_resource_summary",
            "category": "ok",
            "content": '{"project_count":1,"username":"[REDACTED]"}',
            "truncated": False,
            "request_sequence_number": 1,
        }
        assert "fixture-user" not in str(response)
        rejected = await server.call_tool("project_resource_summary", {})
        assert rejected.isError is True
        await server.aclose()

    asyncio.run(run())
    assert proxy.calls == [
        (ToolCallRequest("project_resource_summary", (), 1), "model-facing-mcp-1")
    ]
    assert proxy.closed


def test_model_facing_server_consumes_invalid_tool_attempt_without_forwarding() -> None:
    proxy = FixtureBridgeProxy()
    server = ModelFacingMcpServer(proxy)

    async def run() -> None:
        denied = await server.call_tool("server_basic_info", {})
        assert denied.isError is True
        second = await server.call_tool("project_resource_summary", {})
        assert second.isError is True
        await server.aclose()

    asyncio.run(run())
    assert proxy.calls == []
    assert proxy.closed


def test_model_facing_mcp_protocol_reaches_unix_bridge_with_redaction(
    tmp_path: Path,
) -> None:
    calls: list[ToolCallRequest] = []

    async def runner(value: ToolCallRequest) -> dict[str, object]:
        calls.append(value)
        return raw_result()

    async def run() -> None:
        path = str(tmp_path / "bridge.sock")
        bridge = UnixSocketBridge(
            approved_peer_uid=os.getuid(),
            executor=AssistantBridgeExecutor(policy=policy(), runner=runner),
            timeout_seconds=1,
        )
        socket_server = await asyncio.start_unix_server(bridge.serve, path=path)
        try:
            with patch(
                "openstack_ai_ops_orchestrator.mcp_stdio_proxy.ASSISTANT_MCP_BRIDGE_SOCKET",
                path,
            ):
                facade = ModelFacingMcpServer(McpStdioProxy(policy=policy()))
                mcp_server = facade.create_server()
                client_write: MemoryObjectSendStream[SessionMessage]
                server_read: MemoryObjectReceiveStream[SessionMessage | Exception]
                server_write: MemoryObjectSendStream[SessionMessage]
                client_read: MemoryObjectReceiveStream[SessionMessage | Exception]
                client_write, server_read = anyio.create_memory_object_stream(0)
                server_write, client_read = anyio.create_memory_object_stream(0)
                try:
                    async with anyio.create_task_group() as task_group:
                        task_group.start_soon(
                            mcp_server.run,
                            server_read,
                            server_write,
                            mcp_server.create_initialization_options(),
                        )
                        async with ClientSession(client_read, client_write) as client:
                            await client.initialize()
                            discovered = await client.list_tools()
                            assert [tool.name for tool in discovered.tools] == [
                                "project_resource_summary"
                            ]
                            result = await client.call_tool(
                                "project_resource_summary", {}
                            )
                            assert result.isError is False
                            assert "fixture-user" not in str(result)
                            assert "[REDACTED]" in str(result)
                        task_group.cancel_scope.cancel()
                finally:
                    await facade.aclose()
        finally:
            socket_server.close()
            await socket_server.wait_closed()

    asyncio.run(run())
    assert calls == [ToolCallRequest("project_resource_summary", (), 1)]
