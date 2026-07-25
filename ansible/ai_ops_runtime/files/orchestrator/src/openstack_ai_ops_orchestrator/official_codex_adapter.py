"""Disabled boundary for future public Codex SDK integration."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import aclosing
from typing import TYPE_CHECKING, Protocol

from .contracts import (
    AdapterErrorCategory,
    AdapterEvent,
    AdapterEventType,
    AdapterResult,
    DiagnosticTurnRequest,
    RuntimePolicy,
    WorkflowState,
)

if TYPE_CHECKING:
    from openai_codex import AsyncCodex, CodexConfig

OFFICIAL_ADAPTER_ENABLED = False


class PublicTurnStatus(Protocol):
    """Minimal public status shape accepted without retaining SDK payloads."""

    @property
    def value(self) -> str:
        """Return the closed public status value."""


class PublicTurnResult(Protocol):
    """Minimal terminal-result shape accepted from the pinned public SDK."""

    @property
    def status(self) -> PublicTurnStatus:
        """Return the terminal public status without other SDK fields."""


class PublicSdkEvent(Protocol):
    """Minimal notification shape reduced before it leaves the adapter."""

    @property
    def method(self) -> str:
        """Return the public lifecycle method name only."""


class PublicSdkEventStream(AsyncIterator[PublicSdkEvent], Protocol):
    """Closable public event stream owned by one mocked turn."""

    async def aclose(self) -> None:
        """Close the exact mocked stream."""


class PublicAsyncTurn(Protocol):
    """Public turn-handle shape needed by the finite mocked lifecycle."""

    def stream(self) -> PublicSdkEventStream:
        """Return the public event stream."""

    async def interrupt(self) -> object:
        """Request the sole bounded cancellation interrupt."""


class PublicAsyncThread(Protocol):
    """Public thread shape needed by the finite mocked lifecycle."""

    async def turn(self, input: str) -> PublicAsyncTurn:
        """Start one mocked turn from already-redacted input."""


class MockedSdkClient(Protocol):
    """Public client shape used only through an injected mocked factory."""

    async def thread_start(self) -> PublicAsyncThread:
        """Start one mocked thread."""

    async def close(self) -> None:
        """Close the exact mocked client."""


class MockedSdkLifecycleFactory(Protocol):
    """Test-only factory for public-shape SDK mocks; never a production path."""

    def __call__(self) -> MockedSdkClient:
        """Return one injected mock client without constructing a real runtime."""


class OfficialSdkFactory(Protocol):
    """Future injected runtime seam; it must remain unreachable while disabled."""

    def __call__(self, config: CodexConfig) -> AsyncCodex:
        """Construct the pinned SDK client only after a future approval gate."""


class OfficialAdapterCompatibilityError(RuntimeError):
    """Raised when a public SDK contract cannot be mapped safely."""


class OfficialAdapterDisabledError(RuntimeError):
    """Raised before any Codex configuration or runtime can be entered."""


def build_curated_codex_config(policy: RuntimePolicy) -> CodexConfig:
    """Describe the sole future SDK configuration after an explicit approval gate."""
    if not OFFICIAL_ADAPTER_ENABLED:
        raise OfficialAdapterDisabledError("official adapter remains disabled")
    return CodexConfig(
        config_overrides=(),
        cwd=policy.fixed_working_directory,
        env={},
    )


def map_public_event_method(method: str) -> AdapterEvent:
    """Map only reviewed public lifecycle names to metadata-only events."""
    event_type = {
        "thread/started": AdapterEventType.THREAD_STARTED,
        "turn/started": AdapterEventType.TURN_STARTED,
        "turn/completed": AdapterEventType.TURN_COMPLETED,
    }.get(method)
    if event_type is None:
        raise OfficialAdapterCompatibilityError("unrecognized public event")
    return AdapterEvent(event_type=event_type)


def map_turn_result(result: PublicTurnResult) -> AdapterResult:
    """Map only terminal public statuses without retaining SDK result content."""
    match result.status.value:
        case "completed":
            return AdapterResult(state=WorkflowState.COMPLETED)
        case "interrupted":
            return AdapterResult(
                state=WorkflowState.CANCELLED,
                error_category=AdapterErrorCategory.CANCELLED,
            )
        case "failed":
            return AdapterResult(
                state=WorkflowState.ADAPTER_FAILED,
                error_category=AdapterErrorCategory.SDK_RUNTIME_FAILED,
            )
        case "inProgress":
            raise OfficialAdapterCompatibilityError("non-terminal public turn status")
        case _:
            raise OfficialAdapterCompatibilityError("unrecognized public turn status")


class OfficialCodexAdapter:
    """Explicitly disabled adapter; it never constructs ``AsyncCodex``."""

    def __init__(
        self, mocked_sdk_factory: MockedSdkLifecycleFactory | None = None
    ) -> None:
        self._mocked_sdk_factory = mocked_sdk_factory
        self.cleanup_completed = False
        self.interruption_attempted = False
        self.result: AdapterResult | None = None

    def run_turn(
        self,
        request: DiagnosticTurnRequest,
        policy: RuntimePolicy,
        cancellation: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        """Run only an injected mock; ordinary construction remains disabled."""
        if self._mocked_sdk_factory is None:
            del request, policy, cancellation
            return self._disabled_events()
        return self._mocked_events(request, policy, cancellation)

    async def _disabled_events(self) -> AsyncIterator[AdapterEvent]:
        self.result = AdapterResult(
            state=WorkflowState.VENDOR_BLOCKED,
            error_category=AdapterErrorCategory.REAL_ADAPTER_DISABLED,
        )
        if False:
            yield AdapterEvent(event_type=AdapterEventType.ADAPTER_FAILED)

    async def _mocked_events(
        self,
        request: DiagnosticTurnRequest,
        policy: RuntimePolicy,
        cancellation: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        """Run one finite injected mock lifecycle without retaining raw payloads."""
        self.cleanup_completed = False
        self.interruption_attempted = False
        self.result = None
        client: MockedSdkClient | None = None
        turn: PublicAsyncTurn | None = None
        try:
            if cancellation.is_set():
                self.result = AdapterResult(
                    state=WorkflowState.CANCELLED,
                    error_category=AdapterErrorCategory.CANCELLED,
                )
                yield AdapterEvent(event_type=AdapterEventType.CANCELLED)
                return
            async with asyncio.timeout(policy.deadline_seconds):
                factory = self._mocked_sdk_factory
                if factory is None:
                    raise OfficialAdapterDisabledError(
                        "mocked lifecycle factory is unavailable"
                    )
                client = factory()
                thread = await client.thread_start()
                turn = await thread.turn(request.redacted_context)
                if cancellation.is_set():
                    await self._interrupt_once(turn, policy)
                    self.result = AdapterResult(
                        state=WorkflowState.CANCELLED,
                        error_category=AdapterErrorCategory.CANCELLED,
                    )
                    yield AdapterEvent(event_type=AdapterEventType.CANCELLED)
                    return
                saw_terminal_event = False
                async with aclosing(turn.stream()) as stream:
                    async for raw_event in stream:
                        if cancellation.is_set():
                            await self._interrupt_once(turn, policy)
                            self.result = AdapterResult(
                                state=WorkflowState.CANCELLED,
                                error_category=AdapterErrorCategory.CANCELLED,
                            )
                            yield AdapterEvent(event_type=AdapterEventType.CANCELLED)
                            return
                        event = map_public_event_method(raw_event.method)
                        saw_terminal_event = (
                            saw_terminal_event
                            or event.event_type is AdapterEventType.TURN_COMPLETED
                        )
                        yield event
                if not saw_terminal_event:
                    raise OfficialAdapterCompatibilityError(
                        "mocked stream is incomplete"
                    )
                self.result = AdapterResult(state=WorkflowState.COMPLETED)
        except TimeoutError:
            await self._interrupt_once(turn, policy)
            self.result = AdapterResult(
                state=WorkflowState.TIMED_OUT,
                error_category=AdapterErrorCategory.DEADLINE_EXCEEDED,
            )
        except OfficialAdapterCompatibilityError:
            self.result = AdapterResult(
                state=WorkflowState.ADAPTER_FAILED,
                error_category=AdapterErrorCategory.INVALID_ADAPTER_EVENT,
            )
            yield AdapterEvent(event_type=AdapterEventType.ADAPTER_FAILED)
        except Exception:
            self.result = AdapterResult(
                state=WorkflowState.ADAPTER_FAILED,
                error_category=AdapterErrorCategory.SDK_RUNTIME_FAILED,
            )
            yield AdapterEvent(event_type=AdapterEventType.ADAPTER_FAILED)
        finally:
            if client is not None:
                try:
                    await asyncio.wait_for(
                        client.close(), policy.cleanup_timeout_seconds
                    )
                except Exception:
                    if (
                        self.result is None
                        or self.result.state is WorkflowState.COMPLETED
                    ):
                        self.result = AdapterResult(
                            state=WorkflowState.ADAPTER_FAILED,
                            error_category=AdapterErrorCategory.SDK_RUNTIME_FAILED,
                        )
            self.cleanup_completed = True

    async def _interrupt_once(
        self, turn: PublicAsyncTurn | None, policy: RuntimePolicy
    ) -> None:
        """Request at most one bounded interrupt from the injected mock turn."""
        if turn is None or self.interruption_attempted:
            return
        self.interruption_attempted = True
        try:
            await asyncio.wait_for(turn.interrupt(), policy.cleanup_timeout_seconds)
        except Exception:
            pass
