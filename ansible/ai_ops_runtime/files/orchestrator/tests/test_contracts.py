"""Tests for closed, SDK-free repository contracts."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest

from openstack_ai_ops_orchestrator.contracts import (
    TERMINAL_WORKFLOW_STATES,
    AdapterEvent,
    AdapterEventType,
    CodexAdapter,
    DiagnosticTurnRequest,
    RuntimePolicy,
    WorkflowState,
)


def test_request_accepts_exact_closed_schema() -> None:
    request = DiagnosticTurnRequest.from_mapping(
        {
            "workflow": "project_resource_summary",
            "correlation_id": "local-correlation-1",
            "redacted_context": "safe context",
        }
    )

    assert request.workflow == "project_resource_summary"


@pytest.mark.parametrize(
    "value",
    [
        {"workflow": "project_resource_summary"},
        {
            "workflow": "project_resource_summary",
            "correlation_id": "local-correlation-1",
            "redacted_context": "safe context",
            "unexpected": "value",
        },
        {
            "workflow": "project_resource_summary",
            "correlation_id": "",
            "redacted_context": "safe context",
        },
    ],
)
def test_request_rejects_invalid_schema(value: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="closed schema|non-empty strings"):
        DiagnosticTurnRequest.from_mapping(value)


def test_terminal_states_are_closed() -> None:
    assert WorkflowState.COMPLETED in TERMINAL_WORKFLOW_STATES
    assert WorkflowState.RUNNING not in TERMINAL_WORKFLOW_STATES


class ContractOnlyAdapter:
    def run_turn(
        self,
        request: DiagnosticTurnRequest,
        policy: RuntimePolicy,
        cancellation: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        async def events() -> AsyncIterator[AdapterEvent]:
            yield AdapterEvent(event_type=AdapterEventType.TURN_STARTED)

        return events()


def test_protocol_has_no_sdk_runtime_requirement() -> None:
    adapter: CodexAdapter = ContractOnlyAdapter()
    assert adapter.run_turn(
        DiagnosticTurnRequest("project_resource_summary", "correlation-1", "safe"),
        RuntimePolicy(30, 4, 1024, "reviewed-model", "/fixed/workdir"),
        asyncio.Event(),
    )
