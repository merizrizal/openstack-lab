"""Tests for deterministic, SDK-free fake adapter behavior."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

from openstack_ai_ops_orchestrator.contracts import (
    AdapterErrorCategory,
    AdapterEvent,
    AdapterEventType,
    DiagnosticTurnRequest,
    RuntimePolicy,
    WorkflowState,
)
from openstack_ai_ops_orchestrator.fake_codex_adapter import (
    FakeCodexAdapter,
    FakeCodexScenario,
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
        "socket",
        "requests",
        "http.client",
        "subprocess",
        "os.environ",
        "Path(",
        "open(",
    ):
        assert prohibited_reference not in source
