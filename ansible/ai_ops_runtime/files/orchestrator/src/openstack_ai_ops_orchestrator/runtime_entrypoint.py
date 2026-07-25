"""Fixed fake-only validation entrypoint with no caller runtime configuration."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from enum import IntEnum, StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory

from .contracts import RuntimePolicy, WorkflowState
from .evidence import BoundedJsonlEvidenceWriter
from .fake_codex_adapter import FakeCodexAdapter, FakeCodexScenario
from .orchestrator import REVIEWED_WORKFLOW, LocalOrchestrator


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


def main(arguments: Sequence[str] = ()) -> ExitCategory:
    """Run the fixed fake profile, rejecting remote or arbitrary invocation input."""
    profile = _selected_profile(arguments)
    if profile is InvocationProfile.REMOTE:
        return ExitCategory.REMOTE_DISABLED
    if profile is None:
        return ExitCategory.INVOCATION_REJECTED
    with TemporaryDirectory(prefix="aiops-validate-local-fake-") as temporary_directory:
        return _run_validate_local_fake(Path(temporary_directory))


if __name__ == "__main__":
    raise SystemExit(main())
