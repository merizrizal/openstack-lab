"""Fixed fake and approval-gated remote entrypoint with no caller configuration."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol

from openai_codex import AsyncCodex, CodexConfig

from .contracts import RuntimePolicy, SafeToolResult, ToolCallRequest, WorkflowState
from .evidence import BoundedJsonlEvidenceWriter
from .fake_codex_adapter import FakeCodexAdapter, FakeCodexScenario
from .mcp_stdio_proxy import McpStdioProxy
from .official_codex_adapter import (
    MockedSdkLifecycleFactory,
    OfficialCodexAdapter,
    OfficialSdkFactory,
)
from .orchestrator import REVIEWED_WORKFLOW, LocalOrchestrator
from .remote_acceptance import (
    RemoteAcceptanceError,
    RemoteAcceptanceErrorCategory,
    RemoteAcceptancePolicy,
    ValidatedOneShotApproval,
    consume_one_shot_approval,
    consume_remote_acceptance_artifact,
    load_remote_acceptance_artifact,
    run_remote_operation_cleanup_stub,
)


class InvocationProfile(StrEnum):
    """Closed profile names known to the temporary deployment entrypoint."""

    VALIDATE_LOCAL_FAKE = "validate-local-fake"
    REMOTE = "remote"


class ExitCategory(IntEnum):
    """Stable process categories that retain no workflow content."""

    SUCCESS = 0
    INVOCATION_REJECTED = 2
    REMOTE_DISABLED = 3
    WORKFLOW_FAILED = 4
    REMOTE_PREREQUISITE_FAILED = 5
    REMOTE_WORKFLOW_FAILED = 6


class ReviewedMcpProxy(Protocol):
    """Credential-free reviewed proxy seam used only by the mocked remote slice."""

    async def forward(
        self, request: ToolCallRequest, correlation_id: str
    ) -> SafeToolResult:
        """Return one already-redacted result for the fixed tool request."""

    async def aclose(self) -> None:
        """Close the exact injected proxy."""


_FIXED_REQUEST = {
    "workflow": REVIEWED_WORKFLOW,
    "correlation_id": "validate-local-fake-1",
    "redacted_context": "fixed-local-fake-context",
}
_FIXED_POLICY = RuntimePolicy(
    deadline_seconds=30,
    maximum_event_count=4,
    maximum_output_bytes=1024,
    model_alias="validate-local-fake",
    fixed_working_directory="/var/lib/aiops-orchestrator/work",
)


def _fixed_remote_request() -> dict[str, str]:
    """Build the sole repository-owned remote request without caller input."""
    return {
        "workflow": RemoteAcceptancePolicy.workflow,
        "correlation_id": "remote-acceptance-1",
        "redacted_context": RemoteAcceptancePolicy.prompt_text,
    }


def _fixed_remote_policy() -> RuntimePolicy:
    """Build the immutable runtime limits for the reviewed remote profile."""
    return RuntimePolicy(
        deadline_seconds=30,
        maximum_event_count=3,
        maximum_output_bytes=1024,
        model_alias=RemoteAcceptancePolicy.model_alias,
        fixed_working_directory=RemoteAcceptancePolicy.fixed_working_directory,
        maximum_turn_count=RemoteAcceptancePolicy.maximum_turn_count,
        maximum_tool_call_count=RemoteAcceptancePolicy.maximum_tool_call_count,
    )


_REMOTE_APPROVAL_ARTIFACT = Path("/run/aiops-orchestrator/remote-approval")
_REMOTE_EVIDENCE_DIRECTORY = Path(RemoteAcceptancePolicy.fixed_evidence_directory)


def _fixed_official_sdk_factory(config: CodexConfig) -> AsyncCodex:
    """Construct the pinned client only from the capability-gated configuration."""
    return AsyncCodex(config)


def _fixed_mcp_proxy_factory(policy: RuntimePolicy) -> ReviewedMcpProxy:
    """Construct the reviewed Unix-socket proxy from fixed runtime policy."""
    return McpStdioProxy(policy=policy)


def _suppress_remote_advisory(advisory: str) -> None:
    """Avoid persisting provider-derived advisory text from a one-shot unit."""
    del advisory


def _selected_profile(arguments: Sequence[str]) -> InvocationProfile | None:
    """Recognize only the explicit disabled remote request; reject all other input."""
    if not arguments:
        return InvocationProfile.VALIDATE_LOCAL_FAKE
    if tuple(arguments) == ("--profile", InvocationProfile.REMOTE.value):
        return InvocationProfile.REMOTE
    return None


def _run_validate_local_fake(evidence_directory: Path) -> ExitCategory:
    """Execute the sole deterministic fake-backed workflow in a private directory."""
    evidence_directory.chmod(0o700)
    ledger_path = evidence_directory / "validate-local-fake.jsonl"
    ledger_path.touch(mode=0o600, exist_ok=False)
    writer = BoundedJsonlEvidenceWriter(
        ledger_path,
        _FIXED_POLICY.maximum_evidence_record_bytes,
        _FIXED_POLICY.maximum_evidence_ledger_bytes,
    )
    orchestrator = LocalOrchestrator(
        FakeCodexAdapter(FakeCodexScenario.successful()),
        lambda context: context,
        evidence_writer=writer,
    )
    execution = asyncio.run(
        orchestrator.run(_FIXED_REQUEST, _FIXED_POLICY, asyncio.Event())
    )
    ledger_path.chmod(0o600)
    if execution.result.state is WorkflowState.COMPLETED:
        return ExitCategory.SUCCESS
    return ExitCategory.WORKFLOW_FAILED


def _run_fixed_remote_mocked(
    approval: ValidatedOneShotApproval | None,
    evidence_directory: Path,
    mocked_sdk_factory: MockedSdkLifecycleFactory,
    mcp_proxy_factory: Callable[[RuntimePolicy], ReviewedMcpProxy],
    present_advisory: Callable[[str], None],
) -> ExitCategory:
    """Exercise only the injected, approval-gated remote acceptance slice."""
    if not isinstance(approval, ValidatedOneShotApproval):
        return ExitCategory.REMOTE_PREREQUISITE_FAILED
    try:
        consumed_approval = consume_one_shot_approval(approval)
    except RemoteAcceptanceError:
        return ExitCategory.REMOTE_PREREQUISITE_FAILED

    policy = _fixed_remote_policy()
    request_value = _fixed_remote_request()
    evidence_directory.chmod(0o700)
    ledger_path = evidence_directory / "remote-acceptance.jsonl"
    ledger_path.touch(mode=0o600, exist_ok=False)
    writer = BoundedJsonlEvidenceWriter(
        ledger_path,
        policy.maximum_evidence_record_bytes,
        policy.maximum_evidence_ledger_bytes,
    )

    async def run() -> ExitCategory:
        proxy = mcp_proxy_factory(policy)
        try:
            tool_request = ToolCallRequest(REVIEWED_WORKFLOW, (), 1)
            tool_result = await proxy.forward(
                tool_request, request_value["correlation_id"]
            )
            if (
                tool_result.tool_name != tool_request.tool_name
                or tool_result.request_sequence_number != tool_request.sequence_number
            ):
                return ExitCategory.REMOTE_WORKFLOW_FAILED
            adapter = OfficialCodexAdapter(consumed_approval, mocked_sdk_factory)
            execution = await LocalOrchestrator(
                adapter, lambda context: context, evidence_writer=writer
            ).run(request_value, policy, asyncio.Event())
            if execution.result.state is not WorkflowState.COMPLETED:
                return ExitCategory.REMOTE_WORKFLOW_FAILED
            if execution.result.advisory_text is not None:
                present_advisory(execution.result.advisory_text)
            return ExitCategory.SUCCESS
        finally:
            await proxy.aclose()

    try:
        result = asyncio.run(run())
    except Exception:
        return ExitCategory.REMOTE_WORKFLOW_FAILED
    ledger_path.chmod(0o600)
    return result


def _run_fixed_remote_operation(
    approval_artifact: Path,
    current_utc: datetime,
    evidence_directory: Path,
    official_sdk_factory: OfficialSdkFactory,
    mcp_proxy_factory: Callable[[RuntimePolicy], ReviewedMcpProxy],
    present_advisory: Callable[[str], None],
) -> ExitCategory:
    """Run one fixed remote operation after durable approval consumption."""
    try:
        consumed_approval, operation_capability = consume_remote_acceptance_artifact(
            approval_artifact, current_utc
        )
    except RemoteAcceptanceError:
        return ExitCategory.REMOTE_PREREQUISITE_FAILED

    policy = _fixed_remote_policy()
    request_value = _fixed_remote_request()
    try:
        evidence_directory.chmod(0o700)
        ledger_path = evidence_directory / "remote-acceptance.jsonl"
        ledger_path.touch(mode=0o600, exist_ok=False)
        writer = BoundedJsonlEvidenceWriter(
            ledger_path,
            policy.maximum_evidence_record_bytes,
            policy.maximum_evidence_ledger_bytes,
        )
    except OSError:
        return ExitCategory.REMOTE_WORKFLOW_FAILED

    async def run() -> ExitCategory:
        proxy = mcp_proxy_factory(policy)
        try:
            tool_request = ToolCallRequest(REVIEWED_WORKFLOW, (), 1)
            tool_result = await proxy.forward(
                tool_request, request_value["correlation_id"]
            )
            if (
                tool_result.tool_name != tool_request.tool_name
                or tool_result.request_sequence_number != tool_request.sequence_number
            ):
                return ExitCategory.REMOTE_WORKFLOW_FAILED
            adapter = OfficialCodexAdapter(
                consumed_approval,
                operation_capability=operation_capability,
                official_sdk_factory=official_sdk_factory,
            )
            execution = await LocalOrchestrator(
                adapter, lambda context: context, evidence_writer=writer
            ).run(request_value, policy, asyncio.Event())
            if execution.result.state is not WorkflowState.COMPLETED:
                return ExitCategory.REMOTE_WORKFLOW_FAILED
            if execution.result.advisory_text is not None:
                present_advisory(execution.result.advisory_text)
            return ExitCategory.SUCCESS
        finally:
            await proxy.aclose()

    try:
        result = asyncio.run(run())
    except Exception:
        return ExitCategory.REMOTE_WORKFLOW_FAILED
    ledger_path.chmod(0o600)
    return result


def _run_disabled_remote_entrypoint(
    approval_artifact: Path, current_utc: datetime
) -> ExitCategory:
    """Exercise artifact validation without making the remote path reachable."""
    try:
        approval = load_remote_acceptance_artifact(approval_artifact, current_utc)
        run_remote_operation_cleanup_stub(approval, None, lambda: None)
    except RemoteAcceptanceError as error:
        if error.category is RemoteAcceptanceErrorCategory.REMOTE_ACCEPTANCE_DISABLED:
            return ExitCategory.REMOTE_DISABLED
        return ExitCategory.REMOTE_PREREQUISITE_FAILED
    return ExitCategory.REMOTE_WORKFLOW_FAILED


def main(arguments: Sequence[str] = ()) -> ExitCategory:
    """Run the fixed fake or approval-gated remote profile."""
    profile = _selected_profile(arguments)
    if profile is InvocationProfile.REMOTE:
        if not _REMOTE_APPROVAL_ARTIFACT.is_file():
            return ExitCategory.REMOTE_DISABLED
        return _run_fixed_remote_operation(
            _REMOTE_APPROVAL_ARTIFACT,
            datetime.now(UTC),
            _REMOTE_EVIDENCE_DIRECTORY,
            _fixed_official_sdk_factory,
            _fixed_mcp_proxy_factory,
            _suppress_remote_advisory,
        )
    if profile is None:
        return ExitCategory.INVOCATION_REJECTED
    with TemporaryDirectory(prefix="aiops-validate-local-fake-") as temporary_directory:
        return _run_validate_local_fake(Path(temporary_directory))


if __name__ == "__main__":
    raise SystemExit(main())
