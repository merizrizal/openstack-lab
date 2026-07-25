from __future__ import annotations

import asyncio
import inspect
import os
import socket

import pytest

import openstack_ai_ops_orchestrator.mcp_bridge as mcp_bridge
from openstack_ai_ops_orchestrator.contracts import ToolCallRequest
from openstack_ai_ops_orchestrator.mcp_bridge import (
    BridgeRequest,
    BridgeResponse,
    McpBridgeError,
    UnixSocketBridge,
)


def request() -> BridgeRequest:
    return BridgeRequest(
        "correlation-1", ToolCallRequest("project_resource_summary", (), 1)
    )


def raw_result() -> dict[str, object]:
    return {
        "tool_name": "project_resource_summary",
        "category": "ok",
        "content": '{"project_count":1}',
        "truncated": False,
        "request_sequence_number": 1,
    }


def test_bridge_derives_unix_peer_uid_and_rejects_other_uid() -> None:
    async def execute(value: BridgeRequest) -> BridgeResponse:
        return BridgeResponse(value.correlation_id, 1, raw_result())

    async def run() -> None:
        left, right = socket.socketpair(socket.AF_UNIX)
        try:
            bridge = UnixSocketBridge(
                approved_peer_uid=os.getuid(), executor=execute, timeout_seconds=1
            )
            assert await bridge.call(left, request()) == BridgeResponse(
                "correlation-1", 1, raw_result()
            )
            denied = UnixSocketBridge(
                approved_peer_uid=os.getuid() + 1, executor=execute, timeout_seconds=1
            )
            with pytest.raises(McpBridgeError, match="^bridge_peer_denied$"):
                await denied.call(right, request())
        finally:
            left.close()
            right.close()

    asyncio.run(run())


def test_bridge_rejects_unreviewed_request_and_mismatched_response() -> None:
    with pytest.raises(ValueError, match="^bridge tool request is not reviewed$"):
        BridgeRequest("correlation-1", ToolCallRequest("server_basic_info", (), 1))


def test_bridge_module_has_no_tcp_listener_or_runner_command() -> None:
    source = inspect.getsource(mcp_bridge)
    assert "start_server" not in source
    assert "create_server" not in source
    assert "subprocess" not in source
