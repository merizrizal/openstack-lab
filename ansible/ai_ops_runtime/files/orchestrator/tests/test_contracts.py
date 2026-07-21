"""Tests for closed, SDK-free repository contracts."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest

from openstack_ai_ops_orchestrator.contracts import (
    FIXED_MCP_ARGUMENTS,
    FIXED_MCP_COMMAND,
    MCP_CLIENT_NOT_READY_MESSAGE,
    REVIEWED_MCP_CAPABILITIES,
    TERMINAL_WORKFLOW_STATES,
    AdapterEvent,
    AdapterEventType,
    CodexAdapter,
    DiagnosticTurnRequest,
    LocalMcpClientProtocol,
    LocalMcpClientStub,
    McpCapabilityContract,
    RuntimePolicy,
    SafeToolResult,
    ToolCallRequest,
    ToolResultCategory,
    WorkflowState,
)


def test_request_accepts_exact_closed_schema() -> None:
    request = DiagnosticTurnRequest.from_mapping(
        {
            "workflow": "project_resource_summary",
            "correlation_id": "local-correlation-1",
            "redacted_context": "safe context",
        }
    )

    assert request.workflow == "project_resource_summary"


@pytest.mark.parametrize(
    "value",
    [
        {"workflow": "project_resource_summary"},
        {
            "workflow": "project_resource_summary",
            "correlation_id": "local-correlation-1",
            "redacted_context": "safe context",
            "unexpected": "value",
        },
        {
            "workflow": "project_resource_summary",
            "correlation_id": "",
            "redacted_context": "safe context",
        },
    ],
)
def test_request_rejects_invalid_schema(value: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="closed schema|non-empty strings"):
        DiagnosticTurnRequest.from_mapping(value)


def test_terminal_states_are_closed() -> None:
    assert WorkflowState.COMPLETED in TERMINAL_WORKFLOW_STATES
    assert WorkflowState.RUNNING not in TERMINAL_WORKFLOW_STATES


class ContractOnlyAdapter:
    def run_turn(
        self,
        request: DiagnosticTurnRequest,
        policy: RuntimePolicy,
        cancellation: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        async def events() -> AsyncIterator[AdapterEvent]:
            yield AdapterEvent(event_type=AdapterEventType.TURN_STARTED)

        return events()


def test_protocol_has_no_sdk_runtime_requirement() -> None:
    adapter: CodexAdapter = ContractOnlyAdapter()
    assert adapter.run_turn(
        DiagnosticTurnRequest("project_resource_summary", "correlation-1", "safe"),
        RuntimePolicy(30, 4, 1024, "reviewed-model", "/fixed/workdir"),
        asyncio.Event(),
    )


def test_tool_request_is_closed_and_immutable() -> None:
    request = ToolCallRequest.from_mapping(
        {
            "tool_name": "project_resource_summary",
            "arguments": {},
            "sequence_number": 1,
        }
    )

    assert request.arguments == ()
    assert request.sequence_number == 1


@pytest.mark.parametrize(
    "value",
    [
        {
            "tool_name": "project_resource_summary",
            "arguments": {},
            "sequence_number": 1,
            "unexpected": "value",
        },
        {
            "tool_name": "project_resource_summary",
            "arguments": {"unsafe": object()},
            "sequence_number": 1,
        },
        {
            "tool_name": "project_resource_summary",
            "arguments": {},
            "sequence_number": 0,
        },
    ],
)
def test_tool_request_rejects_invalid_schema(value: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="tool request"):
        ToolCallRequest.from_mapping(value)


def test_safe_tool_result_requires_validated_factory() -> None:
    with pytest.raises(ValueError, match="validated redaction boundary"):
        SafeToolResult(
            tool_name="project_resource_summary",
            category=ToolResultCategory.OK,
            redacted_content="safe",
            truncated=False,
            content_bytes=4,
            redaction_count=0,
            request_sequence_number=1,
        )

    result = SafeToolResult._from_validated(
        tool_name="project_resource_summary",
        category=ToolResultCategory.OK,
        redacted_content="safe",
        truncated=False,
        content_bytes=4,
        redaction_count=0,
        request_sequence_number=1,
    )
    assert result.redacted_content == "safe"


def test_runtime_policy_contains_confirmed_tool_bounds() -> None:
    runtime_policy = RuntimePolicy(60, 5, 8192, "reviewed-model", "/fixed/workdir")

    assert runtime_policy.maximum_tool_call_count == 1
    assert runtime_policy.maximum_concurrent_tool_calls == 1
    assert runtime_policy.per_tool_call_timeout_seconds == 55
    assert runtime_policy.maximum_mcp_result_bytes == 270464
    assert runtime_policy.maximum_tool_content_bytes == 131072
    assert runtime_policy.cleanup_timeout_seconds == 5
    assert runtime_policy.maximum_context_bytes == 8192
    assert runtime_policy.maximum_evidence_record_bytes == 4096
    assert runtime_policy.maximum_evidence_ledger_bytes == 65536
    assert runtime_policy.maximum_redaction_count == 10000


def test_reviewed_mcp_contract_is_fixed() -> None:
    assert FIXED_MCP_COMMAND == "/opt/openstack-ai-ops/.venv/bin/python"
    assert FIXED_MCP_ARGUMENTS == ("/opt/openstack-ai-ops/mcp/aiops_mcp_server.py",)
    assert REVIEWED_MCP_CAPABILITIES.tools == (
        "project_resource_summary",
        "server_basic_info",
        "server_network_info",
    )
    assert len(REVIEWED_MCP_CAPABILITIES.resources) == 3
    assert len(REVIEWED_MCP_CAPABILITIES.prompts) == 3


def test_local_mcp_stub_fails_without_runtime_entry() -> None:
    client: LocalMcpClientProtocol = LocalMcpClientStub()
    request = ToolCallRequest("project_resource_summary", (), 1)

    with pytest.raises(RuntimeError, match=MCP_CLIENT_NOT_READY_MESSAGE):
        asyncio.run(client.call_tool(request))


def test_capability_contract_rejects_duplicate_or_unsorted_names() -> None:
    with pytest.raises(ValueError, match="unique sorted strings"):
        McpCapabilityContract(
            tools=("server_basic_info", "project_resource_summary"),
            resources=("aiops://policy/diagnostic-safety",),
            prompts=("project_summary",),
        )


def test_runtime_policy_rejects_open_or_inconsistent_tool_bounds() -> None:
    with pytest.raises(ValueError, match="must remain one"):
        RuntimePolicy(
            60,
            5,
            8192,
            "reviewed-model",
            "/fixed/workdir",
            maximum_tool_call_count=2,
        )
    with pytest.raises(ValueError, match="positive integers"):
        RuntimePolicy(
            60,
            5,
            8192,
            "reviewed-model",
            "/fixed/workdir",
            maximum_concurrent_tool_calls=True,
        )
    with pytest.raises(ValueError, match="raw MCP result bound"):
        RuntimePolicy(
            60,
            5,
            8192,
            "reviewed-model",
            "/fixed/workdir",
            maximum_mcp_result_bytes=1024,
            maximum_tool_content_bytes=2048,
        )
