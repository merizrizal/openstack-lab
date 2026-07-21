"""Disabled boundary for future public Codex SDK integration."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

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
    from openai_codex import CodexConfig, TurnResult

OFFICIAL_ADAPTER_ENABLED = False


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


def map_turn_result(result: TurnResult) -> AdapterResult:
    """Map public SDK result status without retaining SDK result content."""
    if result.status.value == "completed":
        return AdapterResult(state=WorkflowState.COMPLETED)
    return AdapterResult(
        state=WorkflowState.ADAPTER_FAILED,
        error_category=AdapterErrorCategory.SDK_RUNTIME_FAILED,
    )


class OfficialCodexAdapter:
    """Explicitly disabled adapter; it never constructs ``AsyncCodex``."""

    def __init__(self) -> None:
        self.result: AdapterResult | None = None

    def run_turn(
        self,
        request: DiagnosticTurnRequest,
        policy: RuntimePolicy,
        cancellation: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        """Return a disabled stream before SDK configuration or runtime entry."""
        del request, policy, cancellation
        return self._disabled_events()

    async def _disabled_events(self) -> AsyncIterator[AdapterEvent]:
        self.result = AdapterResult(
            state=WorkflowState.VENDOR_BLOCKED,
            error_category=AdapterErrorCategory.REAL_ADAPTER_DISABLED,
        )
        if False:
            yield AdapterEvent(event_type=AdapterEventType.ADAPTER_FAILED)
