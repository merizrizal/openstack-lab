"""Bounded, fake-first orchestration for one diagnostic workflow."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Mapping
from contextlib import aclosing
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, cast

from .contracts import (
    TERMINAL_WORKFLOW_STATES,
    AdapterErrorCategory,
    AdapterEvent,
    AdapterEventType,
    AdapterResult,
    DiagnosticTurnRequest,
    LocalMcpClientProtocol,
    RuntimePolicy,
    SafeToolResult,
    ToolCallRequest,
    WorkflowState,
)
from .evidence import (
    CleanupOutcome,
    EvidenceEventCategory,
    EvidenceWriter,
    OrchestratorEvidenceRecord,
    TruncationOutcome,
)
from .fake_codex_adapter import FakeCodexAdapter
from .redaction import RedactionCategory, redact_tool_result

REVIEWED_WORKFLOW = "project_resource_summary"

_ALLOWED_TRANSITIONS: dict[WorkflowState, frozenset[WorkflowState]] = {
    WorkflowState.RECEIVED: frozenset(
        {WorkflowState.VALIDATED, WorkflowState.REJECTED}
    ),
    WorkflowState.VALIDATED: frozenset({WorkflowState.REDACTED}),
    WorkflowState.REDACTED: frozenset({WorkflowState.ADAPTER_STARTED}),
    WorkflowState.ADAPTER_STARTED: frozenset({WorkflowState.RUNNING}),
    WorkflowState.RUNNING: frozenset(
        {
            WorkflowState.OUTPUT_VALIDATING,
            WorkflowState.CANCELLED,
            WorkflowState.TIMED_OUT,
            WorkflowState.ADAPTER_FAILED,
            WorkflowState.EVIDENCE_FAILED,
        }
    ),
    WorkflowState.OUTPUT_VALIDATING: frozenset(
        {
            WorkflowState.COMPLETED,
            WorkflowState.POLICY_FAILED,
            WorkflowState.EVIDENCE_FAILED,
        }
    ),
}


class TerminalResultAdapter(Protocol):
    """Injected adapter seam with a sanitized terminal result."""

    result: AdapterResult | None

    def run_turn(
        self,
        request: DiagnosticTurnRequest,
        policy: RuntimePolicy,
        cancellation: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        """Yield repository events only."""


@dataclass(slots=True)
class _EvidenceProgress:
    """Counters retained only as closed evidence metadata."""

    correlation_id: str
    input_classification: RedactionCategory
    event_count: int = 1
    tool_call_count: int = 0
    redaction_count: int = 0
    content_bytes: int = 0


@dataclass(frozen=True, slots=True)
class WorkflowExecution:
    """Sanitized terminal result and workflow state history."""

    states: tuple[WorkflowState, ...]
    result: AdapterResult


def validate_advisory_output(
    advisory_text: str | None, maximum_output_bytes: int
) -> str | None:
    """Accept only bounded advisory text; it remains inert data."""
    if advisory_text is None:
        return None
    if len(advisory_text.encode()) > maximum_output_bytes:
        raise ValueError("advisory output exceeds the configured byte limit")
    return advisory_text


def classify_failure(error: BaseException) -> AdapterResult:
    """Discard free-form failures in favor of fixed repository categories."""
    if isinstance(error, asyncio.CancelledError):
        return AdapterResult(WorkflowState.CANCELLED, AdapterErrorCategory.CANCELLED)
    if isinstance(error, TimeoutError):
        return AdapterResult(
            WorkflowState.TIMED_OUT, AdapterErrorCategory.DEADLINE_EXCEEDED
        )
    return AdapterResult(
        WorkflowState.ADAPTER_FAILED, AdapterErrorCategory.SDK_RUNTIME_FAILED
    )


def validate_lifecycle_event(
    event: object,
    event_types: list[AdapterEventType],
    turn_count: int,
    maximum_turn_count: int,
) -> int:
    """Accept the closed fake lifecycle and reject unreviewed event metadata."""
    if not isinstance(event, AdapterEvent) or not isinstance(
        event.event_type, AdapterEventType
    ):
        raise ValueError("invalid adapter event")
    if event.tool_name is not None or event.status is not None:
        raise ValueError("unreviewed adapter event metadata")
    event_type = event.event_type
    if event_type not in {
        AdapterEventType.THREAD_STARTED,
        AdapterEventType.TURN_STARTED,
        AdapterEventType.TURN_COMPLETED,
        AdapterEventType.TURN_FAILED,
        AdapterEventType.CANCELLED,
        AdapterEventType.ADAPTER_FAILED,
    }:
        raise ValueError("unreviewed adapter event type")
    if event_types and event_types[-1] in {
        AdapterEventType.TURN_COMPLETED,
        AdapterEventType.TURN_FAILED,
        AdapterEventType.CANCELLED,
        AdapterEventType.ADAPTER_FAILED,
    }:
        raise ValueError("event follows terminal adapter event")
    if event_type is AdapterEventType.THREAD_STARTED:
        if event_types:
            raise ValueError("thread start must be first")
    elif event_type is AdapterEventType.TURN_STARTED:
        if not event_types or event_types[0] is not AdapterEventType.THREAD_STARTED:
            raise ValueError("turn start requires thread start")
        turn_count += 1
        if turn_count > maximum_turn_count:
            raise ValueError("turn count exceeds policy")
    elif (
        event_type
        in {
            AdapterEventType.TURN_COMPLETED,
            AdapterEventType.TURN_FAILED,
        }
        and turn_count == 0
    ):
        raise ValueError("turn terminal event requires a started turn")
    event_types.append(event_type)
    return turn_count


class LocalOrchestrator:
    """Run the sole reviewed diagnostic workflow through an injected adapter."""

    def __init__(
        self,
        adapter: TerminalResultAdapter,
        redact_context: Callable[[str], str],
        evidence_writer: EvidenceWriter | None = None,
        mcp_client_factory: Callable[[RuntimePolicy], LocalMcpClientProtocol]
        | None = None,
    ) -> None:
        self._adapter = adapter
        self._redact_context = redact_context
        self._evidence_writer = evidence_writer
        self._evidence_progress: _EvidenceProgress | None = None
        self._mcp_client_factory = mcp_client_factory

    async def run(
        self,
        request_value: Mapping[str, object],
        policy: RuntimePolicy,
        cancellation: asyncio.Event,
    ) -> WorkflowExecution:
        states = [WorkflowState.RECEIVED]
        try:
            request = DiagnosticTurnRequest.from_mapping(request_value)
        except ValueError:
            return self._terminal(states, WorkflowState.REJECTED)
        if request.workflow != REVIEWED_WORKFLOW:
            return self._terminal(states, WorkflowState.REJECTED)

        self._transition(states, WorkflowState.VALIDATED)
        original_context = request.redacted_context
        redacted_context = self._redact_context(original_context)
        request = DiagnosticTurnRequest(
            workflow=request.workflow,
            correlation_id=request.correlation_id,
            redacted_context=redacted_context,
        )
        input_classification = (
            RedactionCategory.REDACTED
            if redacted_context != original_context
            else RedactionCategory.CLEAR
        )
        self._transition(states, WorkflowState.REDACTED)
        self._transition(states, WorkflowState.ADAPTER_STARTED)
        self._transition(states, WorkflowState.RUNNING)
        try:
            self._begin_evidence(request.correlation_id, input_classification)
        except Exception:
            return self._terminal(
                states,
                WorkflowState.EVIDENCE_FAILED,
                AdapterErrorCategory.EVIDENCE_FAILED,
            )

        event_count = 0
        turn_count = 0
        event_types: list[AdapterEventType] = []
        try:
            async with aclosing(
                cast(
                    AsyncGenerator[AdapterEvent, None],
                    self._adapter.run_turn(request, policy, cancellation),
                )
            ) as events:
                async for event in events:
                    event_count += 1
                    if event_count > policy.maximum_event_count:
                        raise ValueError("event count exceeds policy")
                    turn_count = validate_lifecycle_event(
                        event,
                        event_types,
                        turn_count,
                        policy.maximum_turn_count,
                    )
                    await self._complete_fake_tool(policy, cancellation)
        except asyncio.CancelledError as error:
            classified_result = classify_failure(error)
            return self._finalize(
                states,
                request.correlation_id,
                classified_result,
                event_count,
                turn_count,
            )
        except ValueError:
            return self._finalize(
                states,
                request.correlation_id,
                AdapterResult(
                    WorkflowState.ADAPTER_FAILED,
                    AdapterErrorCategory.INVALID_ADAPTER_EVENT,
                ),
                event_count,
                turn_count,
            )
        except Exception as error:
            return self._finalize(
                states,
                request.correlation_id,
                classify_failure(error),
                event_count,
                turn_count,
            )

        result = self._adapter.result
        if result is None or result.state not in TERMINAL_WORKFLOW_STATES:
            return self._finalize(
                states,
                request.correlation_id,
                AdapterResult(
                    WorkflowState.ADAPTER_FAILED,
                    AdapterErrorCategory.INVALID_ADAPTER_EVENT,
                ),
                event_count,
                turn_count,
            )
        if result.state is not WorkflowState.COMPLETED:
            return self._finalize(
                states, request.correlation_id, result, event_count, turn_count
            )

        self._transition(states, WorkflowState.OUTPUT_VALIDATING)
        try:
            advisory_text = validate_advisory_output(
                result.advisory_text, policy.maximum_output_bytes
            )
        except ValueError:
            return self._finalize(
                states,
                request.correlation_id,
                AdapterResult(WorkflowState.POLICY_FAILED),
                event_count,
                turn_count,
            )
        return self._finalize(
            states,
            request.correlation_id,
            AdapterResult(WorkflowState.COMPLETED, advisory_text=advisory_text),
            event_count,
            turn_count,
            len(advisory_text.encode()) if advisory_text is not None else 0,
        )

    async def _complete_fake_tool(
        self, policy: RuntimePolicy, cancellation: asyncio.Event
    ) -> None:
        if not isinstance(self._adapter, FakeCodexAdapter):
            return
        step = self._adapter.pending_tool_request_step()
        if step is None:
            return
        request = step.request
        if (
            self._mcp_client_factory is None
            or request != ToolCallRequest(REVIEWED_WORKFLOW, (), 1)
            or cancellation.is_set()
        ):
            raise ValueError("invalid tool request")
        async with self._mcp_client_factory(policy) as client:
            raw_result = await asyncio.wait_for(
                client.call_tool(request), timeout=policy.per_tool_call_timeout_seconds
            )
        if not isinstance(raw_result, Mapping):
            raise ValueError("invalid tool result")
        safe_result = redact_tool_result(
            raw_result,
            maximum_raw_bytes=policy.maximum_mcp_result_bytes,
            maximum_content_bytes=policy.maximum_tool_content_bytes,
            maximum_redactions=policy.maximum_redaction_count,
        )
        if (
            safe_result.tool_name != request.tool_name
            or safe_result.request_sequence_number != request.sequence_number
        ):
            raise ValueError("invalid tool result")
        self._adapter.submit_tool_result(safe_result)
        self._record_tool_evidence(safe_result)

    def _finalize(
        self,
        states: list[WorkflowState],
        correlation_id: str,
        result: AdapterResult,
        event_count: int,
        turn_count: int,
        output_bytes: int = 0,
    ) -> WorkflowExecution:
        del correlation_id, event_count, output_bytes
        progress = self._evidence_progress
        try:
            if progress is not None and self._evidence_writer is not None:
                progress.event_count += 1
                self._evidence_writer.append(
                    OrchestratorEvidenceRecord(
                        schema_version=1,
                        timestamp=self._timestamp(),
                        correlation_id=progress.correlation_id,
                        workflow=REVIEWED_WORKFLOW,
                        event_category=EvidenceEventCategory.WORKFLOW_TERMINAL,
                        workflow_state=result.state,
                        error_category=result.error_category,
                        input_classification=progress.input_classification,
                        tool_name=None,
                        result_category=None,
                        event_count=progress.event_count,
                        turn_count=turn_count,
                        tool_call_count=progress.tool_call_count,
                        redaction_count=progress.redaction_count,
                        content_bytes=progress.content_bytes,
                        truncation_outcome=TruncationOutcome.NOT_APPLICABLE,
                        cleanup_outcome=CleanupOutcome.CLEAN,
                    )
                )
        except Exception:
            return self._terminal(
                states,
                WorkflowState.EVIDENCE_FAILED,
                AdapterErrorCategory.EVIDENCE_FAILED,
            )
        finally:
            self._evidence_progress = None
        return self._terminal(
            states,
            result.state,
            result.error_category,
            result.advisory_text,
        )

    def _begin_evidence(
        self, correlation_id: str, input_classification: RedactionCategory
    ) -> None:
        if self._evidence_writer is None:
            return
        progress = _EvidenceProgress(correlation_id, input_classification)
        self._evidence_writer.append(
            OrchestratorEvidenceRecord(
                schema_version=1,
                timestamp=self._timestamp(),
                correlation_id=correlation_id,
                workflow=REVIEWED_WORKFLOW,
                event_category=EvidenceEventCategory.WORKFLOW_STARTED,
                workflow_state=WorkflowState.RUNNING,
                error_category=None,
                input_classification=input_classification,
                tool_name=None,
                result_category=None,
                event_count=progress.event_count,
                turn_count=0,
                tool_call_count=0,
                redaction_count=0,
                content_bytes=0,
                truncation_outcome=TruncationOutcome.NOT_APPLICABLE,
                cleanup_outcome=CleanupOutcome.NOT_APPLICABLE,
            )
        )
        self._evidence_progress = progress

    def _record_tool_evidence(self, result: SafeToolResult) -> None:
        progress = self._evidence_progress
        if progress is None or self._evidence_writer is None:
            return
        progress.event_count += 1
        progress.tool_call_count += 1
        progress.redaction_count += result.redaction_count
        progress.content_bytes += result.content_bytes
        self._evidence_writer.append(
            OrchestratorEvidenceRecord(
                schema_version=1,
                timestamp=self._timestamp(),
                correlation_id=progress.correlation_id,
                workflow=REVIEWED_WORKFLOW,
                event_category=EvidenceEventCategory.TOOL_COMPLETED,
                workflow_state=WorkflowState.RUNNING,
                error_category=None,
                input_classification=progress.input_classification,
                tool_name=result.tool_name,
                result_category=result.category,
                event_count=progress.event_count,
                turn_count=1,
                tool_call_count=progress.tool_call_count,
                redaction_count=progress.redaction_count,
                content_bytes=progress.content_bytes,
                truncation_outcome=(
                    TruncationOutcome.TRUNCATED
                    if result.truncated
                    else TruncationOutcome.NOT_TRUNCATED
                ),
                cleanup_outcome=CleanupOutcome.NOT_APPLICABLE,
            )
        )

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def _transition(states: list[WorkflowState], next_state: WorkflowState) -> None:
        if next_state not in _ALLOWED_TRANSITIONS.get(states[-1], frozenset()):
            raise ValueError("invalid workflow state transition")
        states.append(next_state)

    @staticmethod
    def _terminal(
        states: list[WorkflowState],
        state: WorkflowState,
        error_category: AdapterErrorCategory | None = None,
        advisory_text: str | None = None,
    ) -> WorkflowExecution:
        if state not in TERMINAL_WORKFLOW_STATES:
            raise ValueError("workflow result must be terminal")
        if states[-1] is not state:
            LocalOrchestrator._transition(states, state)
        return WorkflowExecution(
            states=tuple(states),
            result=AdapterResult(state, error_category, advisory_text),
        )
