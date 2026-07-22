"""Deterministic, SDK-free adapter for local orchestrator tests."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass

from .contracts import (
    AdapterErrorCategory,
    AdapterEvent,
    AdapterEventType,
    AdapterResult,
    DiagnosticTurnRequest,
    RuntimePolicy,
    SafeToolResult,
    ToolCallRequest,
    WorkflowState,
)


@dataclass(frozen=True, slots=True)
class FakeToolRequestStep:
    """One typed fake tool request that pauses the deterministic turn."""

    request: ToolCallRequest


@dataclass(frozen=True, slots=True)
class FakeCodexScenario:
    """A finite repository-event sequence for deterministic local tests."""

    events: tuple[AdapterEvent, ...]
    tool_request: ToolCallRequest | None = None

    @classmethod
    def successful(cls) -> FakeCodexScenario:
        """Return the no-tool fake success sequence."""
        return cls(
            events=(
                AdapterEvent(event_type=AdapterEventType.THREAD_STARTED),
                AdapterEvent(event_type=AdapterEventType.TURN_STARTED),
                AdapterEvent(event_type=AdapterEventType.TURN_COMPLETED),
            )
        )

    @classmethod
    def successful_with_tool_request(cls) -> FakeCodexScenario:
        """Return the sole fake success sequence containing one safe tool."""
        return cls(
            events=cls.successful().events,
            tool_request=ToolCallRequest("project_resource_summary", (), 1),
        )


class FakeCodexAdapter:
    """Emit finite repository events without entering a Codex runtime boundary."""

    def __init__(self, scenario: FakeCodexScenario) -> None:
        self._scenario = scenario
        self._pending_tool_request: ToolCallRequest | None = None
        self.cleanup_completed = False
        self.observed_tool_results: tuple[SafeToolResult, ...] = ()
        self.result: AdapterResult | None = None

    def run_turn(
        self,
        request: DiagnosticTurnRequest,
        policy: RuntimePolicy,
        cancellation: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        """Return a bounded event stream and retain its sanitized terminal result."""
        del request
        return self._events(policy, cancellation)

    def pending_tool_request_step(self) -> FakeToolRequestStep | None:
        """Return the sole typed tool step while the fake turn is paused."""
        if self._pending_tool_request is None:
            return None
        return FakeToolRequestStep(self._pending_tool_request)

    def submit_tool_result(self, result: SafeToolResult) -> None:
        """Accept one matching redacted result for the pending fake request."""
        pending = self._pending_tool_request
        if pending is None:
            raise ValueError("no fake tool result is currently expected")
        if (
            result.tool_name != pending.tool_name
            or result.request_sequence_number != pending.sequence_number
        ):
            raise ValueError("safe tool result does not match the pending request")
        self.observed_tool_results += (result,)
        self._pending_tool_request = None

    async def _events(
        self,
        policy: RuntimePolicy,
        cancellation: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        self.cleanup_completed = False
        self.observed_tool_results = ()
        self._pending_tool_request = None
        self.result = None
        try:
            async with asyncio.timeout(policy.deadline_seconds):
                for event in self._scenario.events:
                    if cancellation.is_set():
                        self.result = AdapterResult(
                            state=WorkflowState.CANCELLED,
                            error_category=AdapterErrorCategory.CANCELLED,
                        )
                        yield AdapterEvent(event_type=AdapterEventType.CANCELLED)
                        return
                    await asyncio.sleep(0)
                    if cancellation.is_set():
                        self.result = AdapterResult(
                            state=WorkflowState.CANCELLED,
                            error_category=AdapterErrorCategory.CANCELLED,
                        )
                        yield AdapterEvent(event_type=AdapterEventType.CANCELLED)
                        return
                    if (
                        isinstance(event, AdapterEvent)
                        and event.event_type is AdapterEventType.TURN_STARTED
                        and self._scenario.tool_request is not None
                    ):
                        self._pending_tool_request = self._scenario.tool_request
                    yield event
                    if (
                        isinstance(event, AdapterEvent)
                        and event.event_type is AdapterEventType.TURN_STARTED
                    ):
                        if cancellation.is_set():
                            self.result = AdapterResult(
                                state=WorkflowState.CANCELLED,
                                error_category=AdapterErrorCategory.CANCELLED,
                            )
                            yield AdapterEvent(event_type=AdapterEventType.CANCELLED)
                            return
                        if self._pending_tool_request is not None:
                            self.result = AdapterResult(
                                state=WorkflowState.ADAPTER_FAILED,
                                error_category=AdapterErrorCategory.INVALID_ADAPTER_EVENT,
                            )
                            yield AdapterEvent(
                                event_type=AdapterEventType.ADAPTER_FAILED
                            )
                            return
                self.result = AdapterResult(state=WorkflowState.COMPLETED)
        except TimeoutError:
            self.result = AdapterResult(
                state=WorkflowState.TIMED_OUT,
                error_category=AdapterErrorCategory.DEADLINE_EXCEEDED,
            )
        finally:
            self.cleanup_completed = True
