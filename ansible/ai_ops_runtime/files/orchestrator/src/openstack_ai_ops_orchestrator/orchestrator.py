"""Bounded, fake-first orchestration for one diagnostic workflow."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Mapping
from contextlib import aclosing
from dataclasses import dataclass
from typing import Protocol, cast

from .contracts import (
    TERMINAL_WORKFLOW_STATES,
    AdapterErrorCategory,
    AdapterEvent,
    AdapterEventType,
    AdapterResult,
    DiagnosticTurnRequest,
    RuntimePolicy,
    WorkflowState,
)

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


@dataclass(frozen=True, slots=True)
class WorkflowMetadata:
    """Allowlisted lifecycle metadata with no adapter payload content."""

    correlation_id: str
    state: WorkflowState
    error_category: AdapterErrorCategory | None
    event_count: int
    turn_count: int
    output_bytes: int


@dataclass(frozen=True, slots=True)
class WorkflowExecution:
    """Sanitized terminal result, state history, and optional metadata."""

    states: tuple[WorkflowState, ...]
    result: AdapterResult
    metadata: WorkflowMetadata | None = None


def validate_advisory_output(
    advisory_text: str | None, maximum_output_bytes: int
) -> str | None:
    """Accept only bounded advisory text; it remains inert data."""
    if advisory_text is None:
        return None
    if len(advisory_text.encode()) > maximum_output_bytes:
        raise ValueError("advisory output exceeds the configured byte limit")
    return advisory_text


def validate_metadata(metadata: WorkflowMetadata) -> None:
    """Reject metadata that is not limited to terminal lifecycle counters."""
    if not metadata.correlation_id.replace("-", "").replace("_", "").isalnum():
        raise ValueError("metadata correlation identifier is invalid")
    if metadata.state not in TERMINAL_WORKFLOW_STATES:
        raise ValueError("metadata state must be terminal")
    if min(metadata.event_count, metadata.turn_count, metadata.output_bytes) < 0:
        raise ValueError("metadata counters must be non-negative")
    if (
        metadata.state is WorkflowState.COMPLETED
        and metadata.error_category is not None
    ):
        raise ValueError("completed metadata cannot contain an error category")


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
        record_metadata: Callable[[WorkflowMetadata], None] | None = None,
    ) -> None:
        self._adapter = adapter
        self._redact_context = redact_context
        self._record_metadata = record_metadata

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
        request = DiagnosticTurnRequest(
            workflow=request.workflow,
            correlation_id=request.correlation_id,
            redacted_context=self._redact_context(request.redacted_context),
        )
        self._transition(states, WorkflowState.REDACTED)
        self._transition(states, WorkflowState.ADAPTER_STARTED)
        self._transition(states, WorkflowState.RUNNING)

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

    def _finalize(
        self,
        states: list[WorkflowState],
        correlation_id: str,
        result: AdapterResult,
        event_count: int,
        turn_count: int,
        output_bytes: int = 0,
    ) -> WorkflowExecution:
        metadata = WorkflowMetadata(
            correlation_id=correlation_id,
            state=result.state,
            error_category=result.error_category,
            event_count=event_count,
            turn_count=turn_count,
            output_bytes=output_bytes,
        )
        try:
            validate_metadata(metadata)
            if self._record_metadata is not None:
                self._record_metadata(metadata)
        except Exception:
            return self._terminal(
                states,
                WorkflowState.EVIDENCE_FAILED,
                AdapterErrorCategory.EVIDENCE_FAILED,
            )
        execution = self._terminal(
            states,
            result.state,
            result.error_category,
            result.advisory_text,
        )
        return WorkflowExecution(execution.states, execution.result, metadata)

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
