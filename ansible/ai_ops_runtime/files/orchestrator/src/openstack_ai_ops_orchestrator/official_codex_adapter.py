"""Disabled boundary for future public Codex SDK integration."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import aclosing
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, cast

from openai_codex.generated.v2_all import (
    AgentMessageThreadItem,
    Thread,
    ThreadItem,
    ThreadStartedNotification,
    Turn,
    TurnCompletedNotification,
    TurnStartedNotification,
    TurnStatus,
)
from openai_codex.models import Notification

from .contracts import (
    AdapterErrorCategory,
    AdapterEvent,
    AdapterEventType,
    AdapterResult,
    DiagnosticTurnRequest,
    RuntimePolicy,
    WorkflowState,
)
from .redaction import RedactionError, redact_operator_context
from .remote_acceptance import ConsumedApproval

if TYPE_CHECKING:
    from openai_codex import AsyncCodex, CodexConfig

OFFICIAL_ADAPTER_ENABLED = False
_used_approval_ids: set[str] = set()


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


class PublicSdkNotification(Protocol):
    """Tainted pinned-SDK notification shape available only to the reducer."""

    @property
    def method(self) -> str:
        """Return the public notification method name."""

    @property
    def payload(self) -> object:
        """Return the opaque tainted payload for immediate local reduction."""


class PublicSdkEventStream(Protocol):
    """Closable public event stream owned by one injected turn."""

    def __aiter__(self) -> AsyncIterator[PublicSdkNotification]:
        """Return the exact owned asynchronous iterator."""

    async def __anext__(self) -> PublicSdkNotification:
        """Return the next tainted public notification."""

    async def aclose(self) -> None:
        """Close the exact injected stream."""


class PublicAsyncTurn(Protocol):
    """Public turn-handle shape needed by the finite injected lifecycle."""

    @property
    def id(self) -> str:
        """Return the public turn identity."""

    def stream(self) -> PublicSdkEventStream:
        """Return the public event stream."""

    async def interrupt(self) -> object:
        """Request the sole bounded cancellation interrupt."""


class PublicAsyncThread(Protocol):
    """Public thread shape needed by the finite injected lifecycle."""

    @property
    def id(self) -> str:
        """Return the public thread identity."""

    async def turn(self, input: str) -> PublicAsyncTurn:
        """Start one injected turn from already-redacted input."""


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


@dataclass(frozen=True, slots=True)
class TaintedNotificationReduction:
    """Repository-owned reducer output with no raw SDK values."""

    event: AdapterEvent
    advisory_text: str | None = None


class TaintedNotificationReducer:
    """Reduce one bounded, ordered pinned-SDK notification sequence in memory."""

    _EXPECTED_EVENTS = (
        ("thread/started", ThreadStartedNotification, AdapterEventType.THREAD_STARTED),
        ("turn/started", TurnStartedNotification, AdapterEventType.TURN_STARTED),
        ("turn/completed", TurnCompletedNotification, AdapterEventType.TURN_COMPLETED),
    )

    def __init__(
        self,
        *,
        expected_thread_id: str,
        expected_turn_id: str,
        maximum_payload_bytes: int,
        maximum_advisory_bytes: int,
        maximum_redactions: int,
    ) -> None:
        if (
            not isinstance(expected_thread_id, str)
            or not expected_thread_id
            or not isinstance(expected_turn_id, str)
            or not expected_turn_id
            or any(
                isinstance(limit, bool) or not isinstance(limit, int) or limit < 1
                for limit in (
                    maximum_payload_bytes,
                    maximum_advisory_bytes,
                    maximum_redactions,
                )
            )
        ):
            raise OfficialAdapterCompatibilityError(
                "invalid tainted reducer configuration"
            )
        self._expected_thread_id = expected_thread_id
        self._expected_turn_id = expected_turn_id
        self._maximum_payload_bytes = maximum_payload_bytes
        self._maximum_advisory_bytes = maximum_advisory_bytes
        self._maximum_redactions = maximum_redactions
        self._next_event_index = 0

    def reduce(
        self, notification: PublicSdkNotification
    ) -> TaintedNotificationReduction:
        """Validate and discard one tainted notification after safe reduction."""
        if type(notification) is not Notification:
            raise OfficialAdapterCompatibilityError("invalid tainted notification")
        if self._next_event_index >= len(self._EXPECTED_EVENTS):
            raise OfficialAdapterCompatibilityError("invalid tainted notification")

        method, payload_type, event_type = self._EXPECTED_EVENTS[self._next_event_index]
        payload = notification.payload
        if notification.method != method or type(payload) is not payload_type:
            raise OfficialAdapterCompatibilityError("invalid tainted notification")
        self._validate_payload_size(
            cast(
                ThreadStartedNotification
                | TurnStartedNotification
                | TurnCompletedNotification,
                payload,
            )
        )

        if type(payload) is ThreadStartedNotification:
            self._validate_thread_started(payload)
            advisory_text = None
        elif type(payload) is TurnStartedNotification:
            self._validate_turn(payload)
            advisory_text = None
        elif type(payload) is TurnCompletedNotification:
            self._validate_turn(payload)
            advisory_text = self._reduce_terminal_advisory(payload.turn)
        else:
            raise OfficialAdapterCompatibilityError("invalid tainted notification")

        self._next_event_index += 1
        return TaintedNotificationReduction(
            event=AdapterEvent(event_type=event_type), advisory_text=advisory_text
        )

    def _validate_payload_size(
        self,
        payload: ThreadStartedNotification
        | TurnStartedNotification
        | TurnCompletedNotification,
    ) -> None:
        try:
            serialized_payload = payload.model_dump_json().encode("utf-8")
        except Exception:
            raise OfficialAdapterCompatibilityError(
                "invalid tainted notification"
            ) from None
        if len(serialized_payload) > self._maximum_payload_bytes:
            raise OfficialAdapterCompatibilityError("invalid tainted notification")
        del serialized_payload

    def _validate_thread_started(self, payload: ThreadStartedNotification) -> None:
        if (
            type(payload.thread) is not Thread
            or payload.thread.id != self._expected_thread_id
        ):
            raise OfficialAdapterCompatibilityError("invalid tainted notification")

    def _validate_turn(
        self, payload: TurnStartedNotification | TurnCompletedNotification
    ) -> None:
        if (
            payload.thread_id != self._expected_thread_id
            or type(payload.turn) is not Turn
            or payload.turn.id != self._expected_turn_id
        ):
            raise OfficialAdapterCompatibilityError("invalid tainted notification")

    def _reduce_terminal_advisory(self, turn: Turn) -> str:
        if (
            turn.status is not TurnStatus.completed
            or type(turn.items) is not list
            or not turn.items
        ):
            raise OfficialAdapterCompatibilityError("invalid tainted notification")
        final_item = turn.items[-1]
        if (
            type(final_item) is not ThreadItem
            or type(final_item.root) is not AgentMessageThreadItem
            or not isinstance(final_item.root.text, str)
            or not final_item.root.text
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in final_item.root.text
            )
        ):
            raise OfficialAdapterCompatibilityError("invalid tainted notification")
        try:
            return redact_operator_context(
                final_item.root.text,
                self._maximum_advisory_bytes,
                self._maximum_redactions,
            ).content
        except RedactionError:
            raise OfficialAdapterCompatibilityError(
                "invalid tainted notification"
            ) from None


def build_curated_codex_config(
    policy: RuntimePolicy, consumed_approval: ConsumedApproval | None = None
) -> CodexConfig:
    """Describe the sole future SDK configuration after an explicit approval gate."""
    if not OFFICIAL_ADAPTER_ENABLED or not isinstance(
        consumed_approval, ConsumedApproval
    ):
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


def contains_public_event_content(event: PublicSdkEvent) -> bool:
    """Reject event shapes that expose unreviewed SDK payload fields."""
    return any(
        hasattr(event, attribute)
        for attribute in (
            "content",
            "item",
            "message",
            "payload",
            "response",
            "result",
            "text",
            "usage",
        )
    )


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
        self,
        consumed_approval: ConsumedApproval | None = None,
        mocked_sdk_factory: MockedSdkLifecycleFactory | None = None,
    ) -> None:
        self._consumed_approval = consumed_approval
        self._mocked_sdk_factory = mocked_sdk_factory
        self._approval_used = False
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
        approval = self._consumed_approval
        if (
            not isinstance(approval, ConsumedApproval)
            or self._mocked_sdk_factory is None
            or self._approval_used
            or approval.approval_id in _used_approval_ids
        ):
            del request, policy, cancellation
            return self._disabled_events()
        _used_approval_ids.add(approval.approval_id)
        self._approval_used = True
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
                reducer = TaintedNotificationReducer(
                    expected_thread_id=thread.id,
                    expected_turn_id=turn.id,
                    maximum_payload_bytes=policy.maximum_mcp_result_bytes,
                    maximum_advisory_bytes=policy.maximum_output_bytes,
                    maximum_redactions=policy.maximum_redaction_count,
                )
                saw_terminal_event = False
                event_count = 0
                async with aclosing(turn.stream()) as stream:
                    async for raw_notification in stream:
                        if cancellation.is_set():
                            await self._interrupt_once(turn, policy)
                            self.result = AdapterResult(
                                state=WorkflowState.CANCELLED,
                                error_category=AdapterErrorCategory.CANCELLED,
                            )
                            yield AdapterEvent(event_type=AdapterEventType.CANCELLED)
                            return
                        event_count += 1
                        if event_count > policy.maximum_event_count:
                            raise OfficialAdapterCompatibilityError(
                                "too many public notifications"
                            )
                        reduction = reducer.reduce(raw_notification)
                        event = reduction.event
                        saw_terminal_event = (
                            event.event_type is AdapterEventType.TURN_COMPLETED
                        )
                        del raw_notification, reduction
                        yield event
                if not saw_terminal_event:
                    raise OfficialAdapterCompatibilityError(
                        "incomplete public notification stream"
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
