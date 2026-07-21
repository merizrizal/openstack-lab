"""Closed repository contracts that do not import or invoke the Codex SDK."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class WorkflowState(StrEnum):
    """Monotonic workflow states owned by the repository."""

    RECEIVED = "received"
    VALIDATED = "validated"
    REDACTED = "redacted"
    ADAPTER_STARTED = "adapter_started"
    RUNNING = "running"
    OUTPUT_VALIDATING = "output_validating"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    AUTH_ACTION_REQUIRED = "auth_action_required"
    ADAPTER_FAILED = "adapter_failed"
    POLICY_FAILED = "policy_failed"
    EVIDENCE_FAILED = "evidence_failed"
    VENDOR_BLOCKED = "vendor_blocked"


TERMINAL_WORKFLOW_STATES = frozenset(
    {
        WorkflowState.COMPLETED,
        WorkflowState.REJECTED,
        WorkflowState.CANCELLED,
        WorkflowState.TIMED_OUT,
        WorkflowState.AUTH_ACTION_REQUIRED,
        WorkflowState.ADAPTER_FAILED,
        WorkflowState.POLICY_FAILED,
        WorkflowState.EVIDENCE_FAILED,
        WorkflowState.VENDOR_BLOCKED,
    }
)


class AdapterEventType(StrEnum):
    """The bounded lifecycle events accepted from an adapter."""

    THREAD_STARTED = "thread_started"
    TURN_STARTED = "turn_started"
    TOOL_STARTED = "tool_started"
    TOOL_COMPLETED = "tool_completed"
    TURN_COMPLETED = "turn_completed"
    TURN_FAILED = "turn_failed"
    CANCELLED = "cancelled"
    ADAPTER_FAILED = "adapter_failed"


class AdapterErrorCategory(StrEnum):
    """Sanitized terminal adapter categories."""

    REAL_ADAPTER_DISABLED = "real_adapter_disabled"
    INVALID_ADAPTER_EVENT = "invalid_adapter_event"
    SDK_START_FAILED = "sdk_start_failed"
    SDK_RUNTIME_FAILED = "sdk_runtime_failed"
    MCP_INTERCEPTION_UNSUPPORTED = "mcp_interception_unsupported"
    DEADLINE_EXCEEDED = "deadline_exceeded"
    CANCELLED = "cancelled"
    EVIDENCE_FAILED = "evidence_failed"


@dataclass(frozen=True, slots=True)
class DiagnosticTurnRequest:
    """A validated, already-redacted diagnostic request."""

    workflow: str
    correlation_id: str
    redacted_context: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> DiagnosticTurnRequest:
        expected_fields = {"workflow", "correlation_id", "redacted_context"}
        if set(value) != expected_fields:
            raise ValueError("diagnostic request fields must match the closed schema")

        workflow = value["workflow"]
        correlation_id = value["correlation_id"]
        redacted_context = value["redacted_context"]
        if not (
            isinstance(workflow, str)
            and workflow
            and isinstance(correlation_id, str)
            and correlation_id
            and isinstance(redacted_context, str)
            and redacted_context
        ):
            raise ValueError("diagnostic request fields must be non-empty strings")

        return cls(
            workflow=workflow,
            correlation_id=correlation_id,
            redacted_context=redacted_context,
        )


@dataclass(frozen=True, slots=True)
class RuntimePolicy:
    """Closed limits and fixed execution settings for one workflow."""

    deadline_seconds: int
    maximum_event_count: int
    maximum_output_bytes: int
    model_alias: str
    fixed_working_directory: str
    maximum_turn_count: int = 1


@dataclass(frozen=True, slots=True)
class AdapterEvent:
    """Sanitized adapter event metadata; never raw SDK payloads or tool output."""

    event_type: AdapterEventType
    tool_name: str | None = None
    status: str | None = None


@dataclass(frozen=True, slots=True)
class AdapterResult:
    """Terminal category and optional already-validated advisory text."""

    state: WorkflowState
    error_category: AdapterErrorCategory | None = None
    advisory_text: str | None = None


class CodexAdapter(Protocol):
    """Repository boundary that isolates all beta SDK interactions."""

    def run_turn(
        self,
        request: DiagnosticTurnRequest,
        policy: RuntimePolicy,
        cancellation: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        """Yield only repository events; terminal handling is adapter-owned."""
