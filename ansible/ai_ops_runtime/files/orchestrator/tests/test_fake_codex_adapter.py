"""Tests for deterministic, SDK-free fake adapter behavior."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from openstack_ai_ops_orchestrator.contracts import (
    AdapterErrorCategory,
    AdapterEvent,
    AdapterEventType,
    DiagnosticTurnRequest,
    RuntimePolicy,
    SafeToolResult,
    ToolCallRequest,
    ToolResultCategory,
    WorkflowState,
)
from openstack_ai_ops_orchestrator.fake_codex_adapter import (
    FakeCodexAdapter,
    FakeCodexScenario,
    FakeToolRequestStep,
)


def collect_events(events: AsyncIterator[AdapterEvent]) -> list[AdapterEvent]:
    async def collect() -> list[AdapterEvent]:
        return [event async for event in events]

    return asyncio.run(collect())


def request() -> DiagnosticTurnRequest:
    return DiagnosticTurnRequest(
        workflow="project_resource_summary",
        correlation_id="local-correlation-1",
        redacted_context="safe context",
    )


def policy(deadline_seconds: int) -> RuntimePolicy:
    return RuntimePolicy(
        deadline_seconds=deadline_seconds,
        maximum_event_count=4,
        maximum_output_bytes=1024,
        model_alias="reviewed-model",
        fixed_working_directory="/fixed/workdir",
    )


def test_fake_adapter_emits_deterministic_success_events() -> None:
    adapter = FakeCodexAdapter(FakeCodexScenario.successful())

    events = collect_events(adapter.run_turn(request(), policy(1), asyncio.Event()))

    assert [event.event_type for event in events] == [
        AdapterEventType.THREAD_STARTED,
        AdapterEventType.TURN_STARTED,
        AdapterEventType.TURN_COMPLETED,
    ]
    assert adapter.result is not None
    assert adapter.result.state is WorkflowState.COMPLETED
    assert adapter.cleanup_completed


def test_fake_adapter_cancellation_emits_terminal_event_and_cleans_up() -> None:
    adapter = FakeCodexAdapter(FakeCodexScenario.successful())
    cancellation = asyncio.Event()
    cancellation.set()

    events = collect_events(adapter.run_turn(request(), policy(1), cancellation))

    assert [event.event_type for event in events] == [AdapterEventType.CANCELLED]
    assert adapter.result is not None
    assert adapter.result.state is WorkflowState.CANCELLED
    assert adapter.result.error_category is AdapterErrorCategory.CANCELLED
    assert adapter.cleanup_completed


def test_fake_adapter_deadline_sets_terminal_result_and_cleans_up() -> None:
    adapter = FakeCodexAdapter(FakeCodexScenario.successful())

    events = collect_events(adapter.run_turn(request(), policy(0), asyncio.Event()))

    assert events == []
    assert adapter.result is not None
    assert adapter.result.state is WorkflowState.TIMED_OUT
    assert adapter.result.error_category is AdapterErrorCategory.DEADLINE_EXCEEDED
    assert adapter.cleanup_completed


def test_fake_adapter_source_excludes_runtime_and_network_imports() -> None:
    source = Path(
        "ansible/ai_ops_runtime/files/orchestrator/src/"
        "openstack_ai_ops_orchestrator/fake_codex_adapter.py"
    ).read_text()

    for prohibited_reference in (
        "openai_codex",
        "mcp_client",
        "LocalMcpClient",
        "socket",
        "requests",
        "http.client",
        "subprocess",
        "os.environ",
        "Path(",
        "open(",
    ):
        assert prohibited_reference not in source


def safe_result(sequence_number: int = 1) -> SafeToolResult:
    return SafeToolResult._from_validated(
        tool_name="project_resource_summary",
        category=ToolResultCategory.OK,
        redacted_content='[{"project":"[REDACTED]"}]',
        truncated=False,
        content_bytes=26,
        redaction_count=1,
        request_sequence_number=sequence_number,
    )


def test_fake_adapter_requires_one_matching_safe_result_before_resuming() -> None:
    adapter = FakeCodexAdapter(FakeCodexScenario.successful_with_tool_request())

    async def run_handshake() -> list[AdapterEvent]:
        events = adapter.run_turn(request(), policy(1), asyncio.Event())
        observed = [await anext(events), await anext(events)]
        step = adapter.pending_tool_request_step()
        assert isinstance(step, FakeToolRequestStep)
        assert step.request == ToolCallRequest("project_resource_summary", (), 1)
        with pytest.raises(ValueError, match="does not match"):
            adapter.submit_tool_result(safe_result(2))
        adapter.submit_tool_result(safe_result())
        observed.append(await anext(events))
        with pytest.raises(StopAsyncIteration):
            await anext(events)
        return observed

    observed = asyncio.run(run_handshake())

    assert [event.event_type for event in observed] == [
        AdapterEventType.THREAD_STARTED,
        AdapterEventType.TURN_STARTED,
        AdapterEventType.TURN_COMPLETED,
    ]
    assert adapter.observed_tool_results == (safe_result(),)
    assert "phase10-secret" not in repr(adapter.observed_tool_results)
    assert adapter.result is not None
    assert adapter.result.state is WorkflowState.COMPLETED
    assert adapter.cleanup_completed
    with pytest.raises(ValueError, match="currently expected"):
        adapter.submit_tool_result(safe_result())


def test_fake_adapter_fails_closed_when_safe_result_is_not_submitted() -> None:
    adapter = FakeCodexAdapter(FakeCodexScenario.successful_with_tool_request())

    async def run_without_result() -> list[AdapterEvent]:
        events = adapter.run_turn(request(), policy(1), asyncio.Event())
        observed = [await anext(events), await anext(events)]
        assert isinstance(adapter.pending_tool_request_step(), FakeToolRequestStep)
        observed.append(await anext(events))
        return observed

    observed = asyncio.run(run_without_result())

    assert observed[2] == AdapterEvent(event_type=AdapterEventType.ADAPTER_FAILED)
    assert adapter.result is not None
    assert adapter.result.state is WorkflowState.ADAPTER_FAILED
    assert adapter.result.error_category is AdapterErrorCategory.INVALID_ADAPTER_EVENT
    assert adapter.cleanup_completed
