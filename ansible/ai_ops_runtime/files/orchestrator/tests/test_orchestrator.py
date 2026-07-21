"""End-to-end tests for the bounded fake-backed workflow."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import cast

from openstack_ai_ops_orchestrator.contracts import (
    AdapterErrorCategory,
    AdapterEvent,
    AdapterEventType,
    AdapterResult,
    DiagnosticTurnRequest,
    RuntimePolicy,
    WorkflowState,
)
from openstack_ai_ops_orchestrator.evidence import (
    EvidenceEventCategory,
    OrchestratorEvidenceRecord,
)
from openstack_ai_ops_orchestrator.fake_codex_adapter import (
    FakeCodexAdapter,
    FakeCodexScenario,
)
from openstack_ai_ops_orchestrator.orchestrator import (
    REVIEWED_WORKFLOW,
    LocalOrchestrator,
    TerminalResultAdapter,
    WorkflowExecution,
)


def request_value(context: str = "safe context") -> dict[str, str]:
    return {
        "workflow": REVIEWED_WORKFLOW,
        "correlation_id": "local-correlation-1",
        "redacted_context": context,
    }


def policy(maximum_event_count: int = 4, deadline_seconds: int = 1) -> RuntimePolicy:
    return RuntimePolicy(
        deadline_seconds=deadline_seconds,
        maximum_event_count=maximum_event_count,
        maximum_output_bytes=1024,
        model_alias="reviewed-model",
        fixed_working_directory="/fixed/workdir",
    )


def run_workflow(
    adapter: TerminalResultAdapter,
    value: dict[str, str],
    runtime_policy: RuntimePolicy,
) -> tuple[WorkflowExecution, list[str]]:
    redacted_contexts: list[str] = []

    def redact_context(context: str) -> str:
        redacted_contexts.append(context)
        return "[redacted]"

    orchestrator = LocalOrchestrator(adapter, redact_context)

    async def run() -> WorkflowExecution:
        return await orchestrator.run(value, runtime_policy, asyncio.Event())

    return asyncio.run(run()), redacted_contexts


def test_fake_backed_workflow_completes_with_redaction_seam() -> None:
    execution, redacted_contexts = run_workflow(
        FakeCodexAdapter(FakeCodexScenario.successful()),
        request_value("never-store-this"),
        policy(),
    )

    assert execution.result.state is WorkflowState.COMPLETED
    assert execution.result.advisory_text is None
    assert execution.states == (
        WorkflowState.RECEIVED,
        WorkflowState.VALIDATED,
        WorkflowState.REDACTED,
        WorkflowState.ADAPTER_STARTED,
        WorkflowState.RUNNING,
        WorkflowState.OUTPUT_VALIDATING,
        WorkflowState.COMPLETED,
    )
    assert redacted_contexts == ["never-store-this"]
    assert "never-store-this" not in repr(execution)


def test_invalid_request_stops_before_fake_adapter_invocation() -> None:
    adapter = FakeCodexAdapter(FakeCodexScenario.successful())
    execution, redacted_contexts = run_workflow(
        adapter,
        {"workflow": REVIEWED_WORKFLOW},
        policy(),
    )

    assert execution.result.state is WorkflowState.REJECTED
    assert execution.states == (WorkflowState.RECEIVED, WorkflowState.REJECTED)
    assert redacted_contexts == []
    assert not adapter.cleanup_completed


def test_excessive_events_fail_closed_after_fake_cleanup() -> None:
    adapter = FakeCodexAdapter(FakeCodexScenario.successful())
    execution, _ = run_workflow(adapter, request_value(), policy(maximum_event_count=2))

    assert execution.result.state is WorkflowState.ADAPTER_FAILED
    assert execution.result.error_category is AdapterErrorCategory.INVALID_ADAPTER_EVENT
    assert adapter.cleanup_completed


class AdvisoryFakeAdapter:
    """A local fake used to exercise advisory-output validation."""

    def __init__(self, advisory_text: str) -> None:
        self._advisory_text = advisory_text
        self.result: AdapterResult | None = None

    def run_turn(
        self,
        request: DiagnosticTurnRequest,
        runtime_policy: RuntimePolicy,
        cancellation: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        del request, runtime_policy, cancellation

        async def events() -> AsyncIterator[AdapterEvent]:
            yield AdapterEvent(event_type=AdapterEventType.THREAD_STARTED)
            yield AdapterEvent(event_type=AdapterEventType.TURN_STARTED)
            yield AdapterEvent(event_type=AdapterEventType.TURN_COMPLETED)
            self.result = AdapterResult(
                state=WorkflowState.COMPLETED,
                advisory_text=self._advisory_text,
            )

        return events()


def test_fake_cancellation_reaches_sanitized_terminal_state() -> None:
    adapter = FakeCodexAdapter(FakeCodexScenario.successful())
    orchestrator = LocalOrchestrator(adapter, lambda context: context)
    cancellation = asyncio.Event()
    cancellation.set()

    async def run() -> WorkflowExecution:
        return await orchestrator.run(request_value(), policy(), cancellation)

    execution = asyncio.run(run())

    assert execution.result.state is WorkflowState.CANCELLED
    assert execution.result.error_category is AdapterErrorCategory.CANCELLED
    assert execution.states[-1] is WorkflowState.CANCELLED


def test_fake_deadline_reaches_sanitized_terminal_state() -> None:
    execution, _ = run_workflow(
        FakeCodexAdapter(FakeCodexScenario.successful()),
        request_value(),
        policy(deadline_seconds=0),
    )

    assert execution.result.state is WorkflowState.TIMED_OUT
    assert execution.result.error_category is AdapterErrorCategory.DEADLINE_EXCEEDED
    assert execution.states[-1] is WorkflowState.TIMED_OUT


def test_oversized_advisory_output_is_rejected_without_retaining_text() -> None:
    execution, _ = run_workflow(
        AdvisoryFakeAdapter("x" * 1025),
        request_value(),
        policy(),
    )

    assert execution.result.state is WorkflowState.POLICY_FAILED
    assert execution.result.advisory_text is None


class RaisingFakeAdapter:
    """A fake stream whose exception must not cross the orchestration boundary."""

    def __init__(self) -> None:
        self.cleanup_completed = False
        self.result: AdapterResult | None = None

    def run_turn(
        self,
        request: DiagnosticTurnRequest,
        runtime_policy: RuntimePolicy,
        cancellation: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        del request, runtime_policy, cancellation

        async def events() -> AsyncIterator[AdapterEvent]:
            try:
                raise RuntimeError("RAW_EXCEPTION_MARKER")
                yield cast(AdapterEvent, None)
            finally:
                self.cleanup_completed = True

        return events()


def test_malformed_event_fails_closed_and_closes_fake_stream() -> None:
    adapter = FakeCodexAdapter(
        FakeCodexScenario(
            events=(
                AdapterEvent(event_type=AdapterEventType.THREAD_STARTED),
                cast(AdapterEvent, object()),
            )
        )
    )

    execution, _ = run_workflow(adapter, request_value(), policy())

    assert execution.result.state is WorkflowState.ADAPTER_FAILED
    assert execution.result.error_category is AdapterErrorCategory.INVALID_ADAPTER_EVENT
    assert adapter.cleanup_completed


def test_turn_count_limit_fails_closed_and_closes_fake_stream() -> None:
    adapter = FakeCodexAdapter(
        FakeCodexScenario(
            events=(
                AdapterEvent(event_type=AdapterEventType.THREAD_STARTED),
                AdapterEvent(event_type=AdapterEventType.TURN_STARTED),
                AdapterEvent(event_type=AdapterEventType.TURN_STARTED),
            )
        )
    )

    execution, _ = run_workflow(adapter, request_value(), policy())

    assert execution.result.state is WorkflowState.ADAPTER_FAILED
    assert execution.result.error_category is AdapterErrorCategory.INVALID_ADAPTER_EVENT
    assert adapter.cleanup_completed


def test_raw_adapter_exception_is_sanitized_and_cleanup_runs() -> None:
    adapter = RaisingFakeAdapter()

    execution, _ = run_workflow(adapter, request_value(), policy())

    assert execution.result.state is WorkflowState.ADAPTER_FAILED
    assert execution.result.error_category is AdapterErrorCategory.SDK_RUNTIME_FAILED
    assert adapter.cleanup_completed
    assert "RAW_EXCEPTION_MARKER" not in repr(execution)


def test_evidence_failure_overrides_completed_result_without_raw_marker() -> None:
    raw_marker = "RAW_EVIDENCE_MARKER"

    class RejectingEvidenceWriter:
        def __init__(self) -> None:
            self.append_count = 0

        def append(self, _: object) -> None:
            self.append_count += 1
            if self.append_count > 1:
                raise RuntimeError(raw_marker)

    adapter = FakeCodexAdapter(FakeCodexScenario.successful())
    orchestrator = LocalOrchestrator(
        adapter,
        lambda context: context,
        evidence_writer=RejectingEvidenceWriter(),
    )

    async def run() -> WorkflowExecution:
        return await orchestrator.run(request_value(), policy(), asyncio.Event())

    execution = asyncio.run(run())

    assert execution.result.state is WorkflowState.EVIDENCE_FAILED
    assert execution.result.error_category is AdapterErrorCategory.EVIDENCE_FAILED
    assert adapter.cleanup_completed
    assert raw_marker not in repr(execution)


class ToolClient:
    def __init__(self, result: object | None = None) -> None:
        self.closed = False
        self.requests: list[object] = []
        self._result = result

    async def __aenter__(self) -> ToolClient:
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        del exc_type, exc, traceback
        self.closed = True

    async def call_tool(self, request: object) -> object:
        self.requests.append(request)
        if self._result is not None:
            return self._result
        return {
            "tool_name": REVIEWED_WORKFLOW,
            "category": "ok",
            "content": '{"username":"phase10-user"}',
            "truncated": False,
            "request_sequence_number": 1,
        }


def test_fake_tool_loop_redacts_result_and_closes_client() -> None:
    adapter = FakeCodexAdapter(FakeCodexScenario.successful_with_tool_request())
    client = ToolClient()
    orchestrator = LocalOrchestrator(
        adapter,
        lambda context: context,
        mcp_client_factory=lambda _: client,
    )

    async def run() -> WorkflowExecution:
        return await orchestrator.run(request_value(), policy(), asyncio.Event())

    execution = asyncio.run(run())

    assert execution.result.state is WorkflowState.COMPLETED
    assert client.closed
    assert len(client.requests) == 1
    assert len(adapter.observed_tool_results) == 1
    assert "phase10-user" not in repr(adapter.observed_tool_results)


def test_fake_tool_loop_writes_only_versioned_metadata_evidence() -> None:
    class CapturingEvidenceWriter:
        def __init__(self) -> None:
            self.records: list[OrchestratorEvidenceRecord] = []

        def append(self, record: OrchestratorEvidenceRecord) -> None:
            self.records.append(record)

    adapter = FakeCodexAdapter(FakeCodexScenario.successful_with_tool_request())
    client = ToolClient()
    writer = CapturingEvidenceWriter()
    orchestrator = LocalOrchestrator(
        adapter,
        lambda context: context,
        evidence_writer=writer,
        mcp_client_factory=lambda _: client,
    )

    async def run() -> WorkflowExecution:
        return await orchestrator.run(request_value(), policy(), asyncio.Event())

    execution = asyncio.run(run())

    assert execution.result.state is WorkflowState.COMPLETED
    assert [record.event_category for record in writer.records] == [
        EvidenceEventCategory.WORKFLOW_STARTED,
        EvidenceEventCategory.TOOL_COMPLETED,
        EvidenceEventCategory.WORKFLOW_TERMINAL,
    ]
    assert writer.records[1].tool_name == REVIEWED_WORKFLOW
    assert writer.records[1].content_bytes > 0
    assert all("phase10-user" not in repr(record) for record in writer.records)


def test_fake_tool_loop_fails_closed_without_client_injection() -> None:
    adapter = FakeCodexAdapter(FakeCodexScenario.successful_with_tool_request())
    orchestrator = LocalOrchestrator(adapter, lambda context: context)

    async def run() -> WorkflowExecution:
        return await orchestrator.run(request_value(), policy(), asyncio.Event())

    execution = asyncio.run(run())

    assert execution.result.state is WorkflowState.ADAPTER_FAILED
    assert execution.result.error_category is AdapterErrorCategory.INVALID_ADAPTER_EVENT
    assert adapter.cleanup_completed


def test_fake_tool_loop_rejects_malformed_result_and_closes_client() -> None:
    adapter = FakeCodexAdapter(FakeCodexScenario.successful_with_tool_request())
    client = ToolClient({"unexpected": "phase10-secret"})
    orchestrator = LocalOrchestrator(
        adapter,
        lambda context: context,
        mcp_client_factory=lambda _: client,
    )

    async def run() -> WorkflowExecution:
        return await orchestrator.run(request_value(), policy(), asyncio.Event())

    execution = asyncio.run(run())

    assert execution.result.state is WorkflowState.ADAPTER_FAILED
    assert execution.result.error_category is AdapterErrorCategory.INVALID_ADAPTER_EVENT
    assert client.closed
    assert "phase10-secret" not in repr(execution)
