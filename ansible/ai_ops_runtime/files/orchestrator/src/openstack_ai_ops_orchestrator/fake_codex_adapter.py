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
    WorkflowState,
)


@dataclass(frozen=True, slots=True)
class FakeCodexScenario:
    """A finite repository-event sequence for deterministic local tests."""

    events: tuple[AdapterEvent, ...]

    @classmethod
    def successful(cls) -> FakeCodexScenario:
        """Return the sole fake success sequence."""
        return cls(
            events=(
                AdapterEvent(event_type=AdapterEventType.THREAD_STARTED),
                AdapterEvent(event_type=AdapterEventType.TURN_STARTED),
                AdapterEvent(event_type=AdapterEventType.TURN_COMPLETED),
            )
        )


class FakeCodexAdapter:
    """Emit finite repository events without entering a Codex runtime boundary."""

    def __init__(self, scenario: FakeCodexScenario) -> None:
        self._scenario = scenario
        self.cleanup_completed = False
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

    async def _events(
        self,
        policy: RuntimePolicy,
        cancellation: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        self.cleanup_completed = False
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
                    yield event
                self.result = AdapterResult(state=WorkflowState.COMPLETED)
        except TimeoutError:
            self.result = AdapterResult(
                state=WorkflowState.TIMED_OUT,
                error_category=AdapterErrorCategory.DEADLINE_EXCEEDED,
            )
        finally:
            self.cleanup_completed = True
