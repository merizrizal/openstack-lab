"""Closed repository contracts that do not import or invoke the Codex SDK."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from dataclasses import InitVar, dataclass
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


FIXED_MCP_COMMAND = "/opt/openstack-ai-ops/.venv/bin/python"
FIXED_MCP_ARGUMENTS = ("/opt/openstack-ai-ops/mcp/aiops_mcp_server.py",)
MCP_CLIENT_NOT_READY_MESSAGE = "MCP client is not ready"


class ToolResultCategory(StrEnum):
    """Closed runner/MCP result categories retained after redaction."""

    OK = "ok"
    ERROR = "error"
    DENIED = "denied"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    TRUNCATED = "truncated"


@dataclass(frozen=True, slots=True)
class McpCapabilityContract:
    """Exact immutable MCP discovery surface accepted by the orchestrator."""

    tools: tuple[str, ...]
    resources: tuple[str, ...]
    prompts: tuple[str, ...]

    def __post_init__(self) -> None:
        for names in (self.tools, self.resources, self.prompts):
            if (
                not names
                or any(not isinstance(name, str) or not name for name in names)
                or len(set(names)) != len(names)
                or tuple(sorted(names)) != names
            ):
                raise ValueError("MCP capability names must be unique sorted strings")


REVIEWED_MCP_CAPABILITIES = McpCapabilityContract(
    tools=(
        "project_resource_summary",
        "server_basic_info",
        "server_network_info",
    ),
    resources=(
        "aiops://architecture/lab-summary",
        "aiops://policy/diagnostic-safety",
        "aiops://runbooks/metadata-troubleshooting",
    ),
    prompts=(
        "metadata_diagnosis",
        "project_summary",
        "server_inspection",
    ),
)


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
class ToolCallRequest:
    """One immutable, closed tool request emitted by an adapter turn."""

    tool_name: str
    arguments: tuple[tuple[str, str], ...]
    sequence_number: int

    def __post_init__(self) -> None:
        argument_names = tuple(name for name, _ in self.arguments)
        if not isinstance(self.tool_name, str) or not self.tool_name:
            raise ValueError("tool request name must be a non-empty string")
        if (
            any(
                not isinstance(name, str) or not name or not isinstance(value, str)
                for name, value in self.arguments
            )
            or len(set(argument_names)) != len(argument_names)
            or tuple(sorted(self.arguments)) != self.arguments
        ):
            raise ValueError("tool request arguments must be unique sorted strings")
        if (
            isinstance(self.sequence_number, bool)
            or not isinstance(self.sequence_number, int)
            or self.sequence_number < 1
        ):
            raise ValueError("tool request sequence number must be positive")

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> ToolCallRequest:
        expected_fields = {"tool_name", "arguments", "sequence_number"}
        if set(value) != expected_fields:
            raise ValueError("tool request fields must match the closed schema")

        tool_name = value["tool_name"]
        arguments = value["arguments"]
        sequence_number = value["sequence_number"]
        if (
            not isinstance(tool_name, str)
            or not isinstance(arguments, Mapping)
            or isinstance(sequence_number, bool)
            or not isinstance(sequence_number, int)
        ):
            raise ValueError("tool request fields have invalid types")
        if any(
            not isinstance(name, str) or not isinstance(argument, str)
            for name, argument in arguments.items()
        ):
            raise ValueError("tool request arguments must be strings")
        return cls(
            tool_name=tool_name,
            arguments=tuple(sorted(arguments.items())),
            sequence_number=sequence_number,
        )


_SAFE_TOOL_RESULT_VALIDATION_TOKEN = object()


@dataclass(frozen=True, slots=True)
class SafeToolResult:
    """Validated and redacted tool content permitted to reach an adapter."""

    tool_name: str
    category: ToolResultCategory
    redacted_content: str
    truncated: bool
    content_bytes: int
    redaction_count: int
    request_sequence_number: int
    _validation_token: InitVar[object] = None

    def __post_init__(self, _validation_token: object) -> None:
        if _validation_token is not _SAFE_TOOL_RESULT_VALIDATION_TOKEN:
            raise ValueError(
                "safe tool results require the validated redaction boundary"
            )
        if not isinstance(self.tool_name, str) or not self.tool_name:
            raise ValueError("safe tool result name must be a non-empty string")
        if not isinstance(self.category, ToolResultCategory):
            raise ValueError("safe tool result category is invalid")
        if not isinstance(self.redacted_content, str):
            raise ValueError("safe tool result content must be text")
        if not isinstance(self.truncated, bool):
            raise ValueError("safe tool result truncation flag is invalid")
        if (
            isinstance(self.content_bytes, bool)
            or not isinstance(self.content_bytes, int)
            or self.content_bytes != len(self.redacted_content.encode("utf-8"))
        ):
            raise ValueError("safe tool result content byte count is invalid")
        if (
            isinstance(self.redaction_count, bool)
            or not isinstance(self.redaction_count, int)
            or self.redaction_count < 0
        ):
            raise ValueError("safe tool result redaction count is invalid")
        if (
            isinstance(self.request_sequence_number, bool)
            or not isinstance(self.request_sequence_number, int)
            or self.request_sequence_number < 1
        ):
            raise ValueError("safe tool result sequence number is invalid")

    @classmethod
    def _from_validated(
        cls,
        *,
        tool_name: str,
        category: ToolResultCategory,
        redacted_content: str,
        truncated: bool,
        content_bytes: int,
        redaction_count: int,
        request_sequence_number: int,
    ) -> SafeToolResult:
        return cls(
            tool_name=tool_name,
            category=category,
            redacted_content=redacted_content,
            truncated=truncated,
            content_bytes=content_bytes,
            redaction_count=redaction_count,
            request_sequence_number=request_sequence_number,
            _validation_token=_SAFE_TOOL_RESULT_VALIDATION_TOKEN,
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
    maximum_tool_call_count: int = 1
    maximum_concurrent_tool_calls: int = 1
    per_tool_call_timeout_seconds: int = 55
    maximum_mcp_result_bytes: int = 270464
    maximum_tool_content_bytes: int = 131072
    cleanup_timeout_seconds: int = 5
    maximum_context_bytes: int = 8192
    maximum_evidence_record_bytes: int = 4096
    maximum_evidence_ledger_bytes: int = 65536
    maximum_redaction_count: int = 10000

    def __post_init__(self) -> None:
        fixed_single_limits = (
            self.maximum_tool_call_count,
            self.maximum_concurrent_tool_calls,
        )
        if any(
            isinstance(limit, bool) or not isinstance(limit, int)
            for limit in fixed_single_limits
        ):
            raise ValueError("tool and evidence limits must be positive integers")
        if fixed_single_limits != (1, 1):
            raise ValueError("initial tool call and concurrency limits must remain one")
        positive_limits = (
            self.per_tool_call_timeout_seconds,
            self.maximum_mcp_result_bytes,
            self.maximum_tool_content_bytes,
            self.cleanup_timeout_seconds,
            self.maximum_context_bytes,
            self.maximum_evidence_record_bytes,
            self.maximum_evidence_ledger_bytes,
            self.maximum_redaction_count,
        )
        if any(
            isinstance(limit, bool) or not isinstance(limit, int) or limit < 1
            for limit in positive_limits
        ):
            raise ValueError("tool and evidence limits must be positive integers")
        if self.maximum_tool_content_bytes > self.maximum_mcp_result_bytes:
            raise ValueError("safe tool content cannot exceed the raw MCP result bound")
        if self.maximum_evidence_record_bytes > self.maximum_evidence_ledger_bytes:
            raise ValueError("evidence record bound cannot exceed the ledger bound")


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


class McpClientNotReadyError(RuntimeError):
    """Raised before any MCP dependency, process, or session can be entered."""


class LocalMcpClientProtocol(Protocol):
    """Typed local-only MCP lifecycle owned by one orchestrator workflow."""

    async def __aenter__(self) -> LocalMcpClientProtocol:
        """Open one fixed stdio session and validate discovery."""

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object,
    ) -> None:
        """Close the exact owned session and process."""

    async def call_tool(self, request: ToolCallRequest) -> object:
        """Return one internal tainted result for independent validation."""


class LocalMcpClientStub:
    """Compile-safe fail-closed placeholder until the fixed client slice exists."""

    async def __aenter__(self) -> LocalMcpClientStub:
        raise McpClientNotReadyError(MCP_CLIENT_NOT_READY_MESSAGE)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object,
    ) -> None:
        del exc_type, exc, traceback

    async def call_tool(self, request: ToolCallRequest) -> object:
        del request
        raise McpClientNotReadyError(MCP_CLIENT_NOT_READY_MESSAGE)


class CodexAdapter(Protocol):
    """Repository boundary that isolates all beta SDK interactions."""

    def run_turn(
        self,
        request: DiagnosticTurnRequest,
        policy: RuntimePolicy,
        cancellation: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        """Yield only repository events; terminal handling is adapter-owned."""
