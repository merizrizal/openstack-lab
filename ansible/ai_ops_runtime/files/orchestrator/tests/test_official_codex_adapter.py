"""Static and behavior tests for the disabled official SDK boundary."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from openstack_ai_ops_orchestrator.contracts import (
    AdapterErrorCategory,
    AdapterEvent,
    DiagnosticTurnRequest,
    RuntimePolicy,
    WorkflowState,
)
from openstack_ai_ops_orchestrator.official_codex_adapter import (
    OFFICIAL_ADAPTER_ENABLED,
    OfficialAdapterDisabledError,
    OfficialCodexAdapter,
    build_curated_codex_config,
)


def request() -> DiagnosticTurnRequest:
    return DiagnosticTurnRequest(
        workflow="project_resource_summary",
        correlation_id="local-correlation-1",
        redacted_context="safe context",
    )


def policy() -> RuntimePolicy:
    return RuntimePolicy(30, 4, 1024, "reviewed-model", "/fixed/workdir")


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
        ".turn(",
        ".interrupt(",
        ".steer(",
        "retry_on_overload(",
    ):
        assert prohibited_call not in source
