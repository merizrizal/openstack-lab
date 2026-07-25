"""Static and behavior tests for the disabled official SDK boundary."""

from __future__ import annotations

import asyncio
import socket
import subprocess
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from openstack_ai_ops_orchestrator.contracts import (
    AdapterErrorCategory,
    AdapterEvent,
    AdapterEventType,
    AdapterResult,
    DiagnosticTurnRequest,
    RuntimePolicy,
    WorkflowState,
)
from openstack_ai_ops_orchestrator.official_codex_adapter import (
    OFFICIAL_ADAPTER_ENABLED,
    OfficialAdapterCompatibilityError,
    OfficialAdapterDisabledError,
    OfficialCodexAdapter,
    build_curated_codex_config,
    map_public_event_method,
    map_turn_result,
)


def request() -> DiagnosticTurnRequest:
    return DiagnosticTurnRequest(
        workflow="project_resource_summary",
        correlation_id="local-correlation-1",
        redacted_context="safe context",
    )


def policy(deadline_seconds: int = 30) -> RuntimePolicy:
    return RuntimePolicy(deadline_seconds, 4, 1024, "reviewed-model", "/fixed/workdir")


def collect_events(events: AsyncIterator[AdapterEvent]) -> list[AdapterEvent]:
    async def collect() -> list[AdapterEvent]:
        return [event async for event in events]

    return asyncio.run(collect())


def test_official_adapter_is_disabled_before_any_sdk_runtime_entry() -> None:
    adapter = OfficialCodexAdapter()

    events = collect_events(adapter.run_turn(request(), policy(), asyncio.Event()))

    assert not OFFICIAL_ADAPTER_ENABLED
    assert events == []
    assert adapter.result is not None
    assert adapter.result.state is WorkflowState.VENDOR_BLOCKED
    assert adapter.result.error_category is AdapterErrorCategory.REAL_ADAPTER_DISABLED


def test_curated_config_cannot_be_constructed_while_disabled() -> None:
    with pytest.raises(OfficialAdapterDisabledError, match="remains disabled"):
        build_curated_codex_config(policy())


def test_official_adapter_source_excludes_runtime_and_auth_calls() -> None:
    source = Path(
        "ansible/ai_ops_runtime/files/orchestrator/src/"
        "openstack_ai_ops_orchestrator/official_codex_adapter.py"
    ).read_text()

    for prohibited_call in (
        "AsyncCodex(",
        "login_api_key(",
        "login_chatgpt(",
        "login_chatgpt_device_code(",
        ".account(",
        ".steer(",
        "retry_on_overload(",
    ):
        assert prohibited_call not in source


@dataclass(frozen=True, slots=True)
class MockPublicTurnStatus:
    value: str


@dataclass(frozen=True, slots=True)
class MockPublicTurnResult:
    status: MockPublicTurnStatus


@pytest.mark.parametrize(
    ("status", "expected_state", "expected_error"),
    (
        ("completed", WorkflowState.COMPLETED, None),
        (
            "interrupted",
            WorkflowState.CANCELLED,
            AdapterErrorCategory.CANCELLED,
        ),
        (
            "failed",
            WorkflowState.ADAPTER_FAILED,
            AdapterErrorCategory.SDK_RUNTIME_FAILED,
        ),
    ),
)
def test_public_terminal_statuses_map_to_closed_results(
    status: str,
    expected_state: WorkflowState,
    expected_error: AdapterErrorCategory | None,
) -> None:
    result = map_turn_result(MockPublicTurnResult(MockPublicTurnStatus(status)))

    assert result.state is expected_state
    assert result.error_category is expected_error


@pytest.mark.parametrize("status", ("inProgress", "unknown"))
def test_non_terminal_or_unknown_public_status_fails_closed(status: str) -> None:
    with pytest.raises(OfficialAdapterCompatibilityError):
        map_turn_result(MockPublicTurnResult(MockPublicTurnStatus(status)))


@pytest.mark.parametrize(
    ("method", "event_type"),
    (
        ("thread/started", AdapterEventType.THREAD_STARTED),
        ("turn/started", AdapterEventType.TURN_STARTED),
        ("turn/completed", AdapterEventType.TURN_COMPLETED),
    ),
)
def test_reviewed_public_events_map_to_metadata_only_events(
    method: str, event_type: AdapterEventType
) -> None:
    assert map_public_event_method(method) == AdapterEvent(event_type=event_type)


def test_unknown_public_event_fails_closed() -> None:
    with pytest.raises(OfficialAdapterCompatibilityError):
        map_public_event_method("item/completed")


def test_disabled_adapter_never_enters_runtime_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("disabled adapter entered a runtime boundary")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)

    adapter = OfficialCodexAdapter()

    assert collect_events(adapter.run_turn(request(), policy(), asyncio.Event())) == []
    assert adapter.result is not None
    assert adapter.result.error_category is AdapterErrorCategory.REAL_ADAPTER_DISABLED


@dataclass(frozen=True, slots=True)
class MockPublicSdkEvent:
    method: str
    ignored_content: str = "raw SDK content must not escape"


class MockPublicSdkStream:
    def __init__(
        self,
        events: tuple[MockPublicSdkEvent, ...],
        cancellation: asyncio.Event | None = None,
        block: bool = False,
    ) -> None:
        self._events = events
        self._cancellation = cancellation
        self._block = block
        self._index = 0
        self.closed = False

    def __aiter__(self) -> MockPublicSdkStream:
        return self

    async def __anext__(self) -> MockPublicSdkEvent:
        if self._block:
            await asyncio.sleep(0)
        if self._index >= len(self._events):
            raise StopAsyncIteration
        event = self._events[self._index]
        self._index += 1
        if self._cancellation is not None:
            self._cancellation.set()
        return event

    async def aclose(self) -> None:
        self.closed = True


class MockPublicAsyncTurn:
    def __init__(self, stream: MockPublicSdkStream) -> None:
        self._stream = stream
        self.interrupt_calls = 0

    def stream(self) -> MockPublicSdkStream:
        return self._stream

    async def interrupt(self) -> object:
        self.interrupt_calls += 1
        return object()


class MockPublicAsyncThread:
    def __init__(self, turn: MockPublicAsyncTurn) -> None:
        self._turn = turn
        self.input: str | None = None

    async def turn(self, input: str) -> MockPublicAsyncTurn:
        self.input = input
        return self._turn


class MockPublicAsyncCodex:
    def __init__(self, thread: MockPublicAsyncThread) -> None:
        self._thread = thread
        self.closed = False

    async def thread_start(self) -> MockPublicAsyncThread:
        return self._thread

    async def close(self) -> None:
        self.closed = True


def test_injected_mocked_lifecycle_emits_metadata_only_events_and_cleans_up() -> None:
    stream = MockPublicSdkStream(
        (
            MockPublicSdkEvent("thread/started"),
            MockPublicSdkEvent("turn/started"),
            MockPublicSdkEvent("turn/completed"),
        )
    )
    turn = MockPublicAsyncTurn(stream)
    thread = MockPublicAsyncThread(turn)
    client = MockPublicAsyncCodex(thread)
    adapter = OfficialCodexAdapter(lambda: client)

    events = collect_events(adapter.run_turn(request(), policy(), asyncio.Event()))

    assert [event.event_type for event in events] == [
        AdapterEventType.THREAD_STARTED,
        AdapterEventType.TURN_STARTED,
        AdapterEventType.TURN_COMPLETED,
    ]
    assert all(event.status is None and event.tool_name is None for event in events)
    assert adapter.result == AdapterResult(state=WorkflowState.COMPLETED)
    assert adapter.cleanup_completed
    assert stream.closed
    assert client.closed
    assert turn.interrupt_calls == 0


def test_injected_mocked_unknown_event_fails_closed_and_cleans_up() -> None:
    stream = MockPublicSdkStream((MockPublicSdkEvent("item/completed"),))
    turn = MockPublicAsyncTurn(stream)
    client = MockPublicAsyncCodex(MockPublicAsyncThread(turn))
    adapter = OfficialCodexAdapter(lambda: client)

    events = collect_events(adapter.run_turn(request(), policy(), asyncio.Event()))

    assert events == [AdapterEvent(event_type=AdapterEventType.ADAPTER_FAILED)]
    assert adapter.result == AdapterResult(
        state=WorkflowState.ADAPTER_FAILED,
        error_category=AdapterErrorCategory.INVALID_ADAPTER_EVENT,
    )
    assert adapter.cleanup_completed
    assert stream.closed
    assert client.closed


def test_mocked_factory_failure_is_sanitized_and_does_not_start_a_client() -> None:
    def fail_factory() -> MockPublicAsyncCodex:
        raise RuntimeError("raw SDK failure")

    adapter = OfficialCodexAdapter(fail_factory)

    events = collect_events(adapter.run_turn(request(), policy(), asyncio.Event()))

    assert events == [AdapterEvent(event_type=AdapterEventType.ADAPTER_FAILED)]
    assert adapter.result == AdapterResult(
        state=WorkflowState.ADAPTER_FAILED,
        error_category=AdapterErrorCategory.SDK_RUNTIME_FAILED,
    )
    assert adapter.cleanup_completed


def test_mocked_cancellation_interrupts_once_and_cleans_up() -> None:
    cancellation = asyncio.Event()
    stream = MockPublicSdkStream(
        (MockPublicSdkEvent("thread/started"),), cancellation=cancellation
    )
    turn = MockPublicAsyncTurn(stream)
    client = MockPublicAsyncCodex(MockPublicAsyncThread(turn))
    adapter = OfficialCodexAdapter(lambda: client)

    events = collect_events(adapter.run_turn(request(), policy(), cancellation))

    assert events == [AdapterEvent(event_type=AdapterEventType.CANCELLED)]
    assert adapter.result == AdapterResult(
        state=WorkflowState.CANCELLED,
        error_category=AdapterErrorCategory.CANCELLED,
    )
    assert adapter.interruption_attempted
    assert turn.interrupt_calls == 1
    assert adapter.cleanup_completed
    assert stream.closed
    assert client.closed


def test_mocked_deadline_interrupts_once_and_cleans_up() -> None:
    stream = MockPublicSdkStream((), block=True)
    turn = MockPublicAsyncTurn(stream)
    client = MockPublicAsyncCodex(MockPublicAsyncThread(turn))
    adapter = OfficialCodexAdapter(lambda: client)

    events = collect_events(adapter.run_turn(request(), policy(0), asyncio.Event()))

    assert events == []
    assert adapter.result == AdapterResult(
        state=WorkflowState.TIMED_OUT,
        error_category=AdapterErrorCategory.DEADLINE_EXCEEDED,
    )
    assert adapter.interruption_attempted
    assert turn.interrupt_calls == 1
    assert adapter.cleanup_completed
    assert stream.closed
    assert client.closed
