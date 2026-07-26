from __future__ import annotations

import asyncio
import inspect
import os
import socket

import pytest

import openstack_ai_ops_orchestrator.mcp_bridge as mcp_bridge
from openstack_ai_ops_orchestrator.contracts import RuntimePolicy, ToolCallRequest
from openstack_ai_ops_orchestrator.mcp_bridge import (
    AssistantBridgeExecutor,
    AssistantRunnerBridgeAdapter,
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


def runner_envelope(
    *,
    status: str = "ok",
    stdout: str = '{"project_count":1}',
    stderr: str = "",
    truncated: bool = False,
) -> dict[str, object]:
    return {
        "tool": "project_resource_summary",
        "status": status,
        "arguments": {},
        "exit_code": 0,
        "stdout": stdout,
        "stderr": stderr,
        "duration_ms": 1,
        "truncated": truncated,
        "timestamp": "2026-01-01T00:00:00Z",
        "request_id": "bridge-runner-1",
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


def test_assistant_executor_redacts_runner_result_before_bridge_response() -> None:
    calls: list[ToolCallRequest] = []

    async def runner(value: ToolCallRequest) -> dict[str, object]:
        calls.append(value)
        result = raw_result()
        result["content"] = '{"username":"fixture-user","project_count":1}'
        return result

    response = asyncio.run(
        AssistantBridgeExecutor(
            policy=RuntimePolicy(60, 5, 8192, "model", "/fixed"), runner=runner
        )(request())
    )

    assert calls == [request().tool_request]
    assert response.correlation_id == request().correlation_id
    assert response.request_sequence_number == 1
    assert "fixture-user" not in str(response.raw_result)
    assert "[REDACTED]" in str(response.raw_result)


def test_assistant_executor_rejects_invalid_or_mismatched_runner_results() -> None:
    async def invalid_runner(_value: ToolCallRequest) -> dict[str, object]:
        result = raw_result()
        result["content"] = "not-json fixture-secret"
        return result

    async def mismatched_runner(_value: ToolCallRequest) -> dict[str, object]:
        result = raw_result()
        result["request_sequence_number"] = 2
        return result

    policy = RuntimePolicy(60, 5, 8192, "model", "/fixed")
    for runner in (invalid_runner, mismatched_runner):
        with pytest.raises(McpBridgeError, match="^bridge_result_rejected$") as error:
            asyncio.run(
                AssistantBridgeExecutor(policy=policy, runner=runner)(request())
            )
        assert "fixture-secret" not in repr(error.value)


def test_assistant_runner_adapter_reuses_injected_runner_and_redacts_ok_result() -> (
    None
):
    calls: list[tuple[ToolCallRequest, str]] = []

    async def runner(value: ToolCallRequest, request_id: str) -> dict[str, object]:
        calls.append((value, request_id))
        envelope = runner_envelope(
            stdout='{"username":"fixture-user","project_count":1}'
        )
        envelope["request_id"] = request_id
        return envelope

    adapter = AssistantRunnerBridgeAdapter(
        runner=runner, request_id_factory=lambda: "bridge-runner-1"
    )
    response = asyncio.run(
        AssistantBridgeExecutor(
            policy=RuntimePolicy(60, 5, 8192, "model", "/fixed"), runner=adapter
        )(request())
    )

    assert calls == [(request().tool_request, "bridge-runner-1")]
    assert "fixture-user" not in str(response.raw_result)
    assert "[REDACTED]" in str(response.raw_result)


@pytest.mark.parametrize(
    ("status", "truncated"),
    [
        ("error", False),
        ("denied", False),
        ("validation_error", False),
        ("timeout", False),
        ("unavailable", False),
        ("truncated", True),
    ],
)
def test_assistant_runner_adapter_withholds_non_ok_runner_content(
    status: str, truncated: bool
) -> None:
    async def runner(value: ToolCallRequest, request_id: str) -> dict[str, object]:
        envelope = runner_envelope(
            status=status,
            stdout='{"secret":"fixture-secret"}',
            stderr="fixture-stderr",
            truncated=truncated,
        )
        envelope["request_id"] = request_id
        return envelope

    result = asyncio.run(
        AssistantRunnerBridgeAdapter(
            runner=runner, request_id_factory=lambda: "bridge-runner-1"
        )(request().tool_request)
    )

    assert result == {
        "tool_name": "project_resource_summary",
        "category": status,
        "content": f'{{"bridge_result":"{status}"}}',
        "truncated": truncated,
        "request_sequence_number": 1,
    }
    assert "fixture-secret" not in str(result)
    assert "fixture-stderr" not in str(result)


def test_assistant_runner_adapter_rejects_invalid_envelope_before_executor() -> None:
    async def runner(value: ToolCallRequest, request_id: str) -> dict[str, object]:
        envelope = runner_envelope()
        envelope["request_id"] = request_id
        envelope.pop("stderr")
        return envelope

    adapter = AssistantRunnerBridgeAdapter(
        runner=runner, request_id_factory=lambda: "bridge-runner-1"
    )
    with pytest.raises(ValueError, match="^bridge runner envelope is invalid$"):
        asyncio.run(adapter(request().tool_request))
