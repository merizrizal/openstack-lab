"""Tests for closed, disabled one-shot remote-acceptance contracts."""

from __future__ import annotations

import socket
import subprocess
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from openstack_ai_ops_orchestrator.remote_acceptance import (
    MAXIMUM_APPROVAL_LIFETIME,
    ConsumedApproval,
    RemoteAcceptanceError,
    RemoteAcceptanceErrorCategory,
    RemoteAcceptancePolicy,
    RemoteOperationCapability,
    consume_one_shot_approval,
    consume_remote_acceptance_artifact,
    load_remote_acceptance_artifact,
    run_disabled_remote_acceptance,
    run_remote_operation_cleanup_stub,
    validate_remote_acceptance_policy,
)

NOW = datetime(2026, 3, 9, 12, 0, tzinfo=UTC)


def policy(expires_at: datetime | None = None) -> RemoteAcceptancePolicy:
    return RemoteAcceptancePolicy(
        approval_id="approval-20260309-0001",
        expires_at=expires_at or NOW + timedelta(minutes=1),
    )


def test_policy_has_only_fixed_reviewed_profile_values() -> None:
    acceptance_policy = policy()

    assert acceptance_policy.request_allowance == 1
    assert acceptance_policy.automatic_retry_allowance == 0
    assert acceptance_policy.workflow == "project_resource_summary"
    assert acceptance_policy.prompt_identifier == "project_resource_summary_v1"
    assert acceptance_policy.model_alias == "reviewed-model"
    assert acceptance_policy.maximum_turn_count == 1
    assert acceptance_policy.maximum_tool_call_count == 1
    with pytest.raises(TypeError, match="request_allowance"):
        RemoteAcceptancePolicy(
            approval_id="approval-20260309-0002",
            expires_at=NOW + timedelta(minutes=1),
            request_allowance=2,  # type: ignore[call-arg]
        )


def test_policy_rejects_missing_or_invalid_approval_identifier() -> None:
    for approval_id in ("", "approval id"):
        with pytest.raises(ValueError, match="approval identifier"):
            RemoteAcceptancePolicy(
                approval_id=approval_id, expires_at=NOW + timedelta(minutes=1)
            )


def test_validator_rejects_expired_or_overlong_approval() -> None:
    with pytest.raises(RemoteAcceptanceError) as expired:
        validate_remote_acceptance_policy(policy(NOW), NOW)
    assert (
        expired.value.category is RemoteAcceptanceErrorCategory.REMOTE_APPROVAL_INVALID
    )

    with pytest.raises(RemoteAcceptanceError) as overlong:
        validate_remote_acceptance_policy(
            policy(NOW + MAXIMUM_APPROVAL_LIFETIME + timedelta(seconds=1)), NOW
        )
    assert (
        overlong.value.category is RemoteAcceptanceErrorCategory.REMOTE_APPROVAL_INVALID
    )


def test_validator_rejects_non_utc_expiry() -> None:
    non_utc = datetime(2026, 3, 9, 13, 0, tzinfo=timezone(timedelta(hours=1)))

    with pytest.raises(RemoteAcceptanceError) as rejected:
        validate_remote_acceptance_policy(policy(non_utc), NOW)

    assert (
        rejected.value.category is RemoteAcceptanceErrorCategory.REMOTE_APPROVAL_INVALID
    )


def test_consumption_is_deterministic_and_reuse_is_rejected() -> None:
    approval = validate_remote_acceptance_policy(policy(), NOW)

    consumed = consume_one_shot_approval(approval)

    assert isinstance(consumed, ConsumedApproval)
    assert consumed.approval_id == "approval-20260309-0001"
    with pytest.raises(RemoteAcceptanceError) as reused:
        consume_one_shot_approval(approval)
    assert (
        reused.value.category is RemoteAcceptanceErrorCategory.REMOTE_APPROVAL_INVALID
    )


def test_disabled_operation_never_enters_runtime_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("disabled operation entered a runtime boundary")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    consumed = consume_one_shot_approval(
        validate_remote_acceptance_policy(policy(), NOW)
    )

    with pytest.raises(RemoteAcceptanceError) as disabled:
        run_disabled_remote_acceptance(consumed)

    assert (
        disabled.value.category
        is RemoteAcceptanceErrorCategory.REMOTE_ACCEPTANCE_DISABLED
    )


def test_operation_cleanup_stub_consumes_approval_and_fails_closed() -> None:
    approval = validate_remote_acceptance_policy(policy(), NOW)
    cleanup_calls: list[str] = []

    with pytest.raises(ValueError, match="capability is unavailable"):
        RemoteOperationCapability("approval-20260309-0001")

    with pytest.raises(RemoteAcceptanceError) as disabled:
        run_remote_operation_cleanup_stub(
            approval, None, lambda: cleanup_calls.append("cleanup")
        )

    assert (
        disabled.value.category
        is RemoteAcceptanceErrorCategory.REMOTE_ACCEPTANCE_DISABLED
    )
    assert cleanup_calls == ["cleanup"]
    with pytest.raises(RemoteAcceptanceError) as reused:
        consume_one_shot_approval(approval)
    assert (
        reused.value.category is RemoteAcceptanceErrorCategory.REMOTE_APPROVAL_INVALID
    )


def test_loader_accepts_only_bounded_private_approval_artifact(tmp_path: Path) -> None:
    artifact_path = tmp_path / "approval.json"
    artifact_path.write_text(
        '{"approval_id":"approval-20260309-0001","expires_at_utc":"2026-03-09T12:01:00Z"}'
    )
    artifact_path.chmod(0o600)

    approval = load_remote_acceptance_artifact(artifact_path, NOW)

    assert approval.policy.approval_id == "approval-20260309-0001"
    assert approval.policy.expires_at == NOW + timedelta(minutes=1)


@pytest.mark.parametrize("mode", (0o640, 0o604))
def test_loader_rejects_permissive_or_invalid_approval_artifact(
    tmp_path: Path, mode: int
) -> None:
    artifact_path = tmp_path / "approval.json"
    artifact_path.write_text('{"approval_id":"approval-20260309-0001"}')
    artifact_path.chmod(mode)

    with pytest.raises(RemoteAcceptanceError) as rejected:
        load_remote_acceptance_artifact(artifact_path, NOW)

    assert (
        rejected.value.category is RemoteAcceptanceErrorCategory.REMOTE_APPROVAL_INVALID
    )


def test_loader_rejects_symlinked_approval_artifact(tmp_path: Path) -> None:
    target_path = tmp_path / "target.json"
    target_path.write_text(
        '{"approval_id":"approval-20260309-0001","expires_at_utc":"2026-03-09T12:01:00Z"}'
    )
    target_path.chmod(0o600)
    artifact_path = tmp_path / "approval.json"
    artifact_path.symlink_to(target_path)

    with pytest.raises(RemoteAcceptanceError) as rejected:
        load_remote_acceptance_artifact(artifact_path, NOW)

    assert (
        rejected.value.category is RemoteAcceptanceErrorCategory.REMOTE_APPROVAL_INVALID
    )


def test_consumer_durably_exhausts_artifact_before_issuing_capability(
    tmp_path: Path,
) -> None:
    artifact_path = tmp_path / "approval.json"
    artifact_path.write_text(
        '{"approval_id":"approval-20260309-0001","expires_at_utc":"2026-03-09T12:01:00Z"}'
    )
    artifact_path.chmod(0o600)

    consumed, capability = consume_remote_acceptance_artifact(artifact_path, NOW)

    assert consumed.approval_id == "approval-20260309-0001"
    assert capability.approval_id == consumed.approval_id
    assert not artifact_path.exists()
    with pytest.raises(RemoteAcceptanceError) as replayed:
        consume_remote_acceptance_artifact(artifact_path, NOW)
    assert (
        replayed.value.category is RemoteAcceptanceErrorCategory.REMOTE_APPROVAL_INVALID
    )


def test_consumer_rejects_symlinked_artifact_without_issuing_capability(
    tmp_path: Path,
) -> None:
    target_path = tmp_path / "target.json"
    target_path.write_text(
        '{"approval_id":"approval-20260309-0001","expires_at_utc":"2026-03-09T12:01:00Z"}'
    )
    target_path.chmod(0o600)
    artifact_path = tmp_path / "approval.json"
    artifact_path.symlink_to(target_path)

    with pytest.raises(RemoteAcceptanceError) as rejected:
        consume_remote_acceptance_artifact(artifact_path, NOW)

    assert (
        rejected.value.category is RemoteAcceptanceErrorCategory.REMOTE_APPROVAL_INVALID
    )
    assert artifact_path.is_symlink()


@pytest.mark.parametrize("failing_operation", ("unlink", "fsync"))
def test_consumer_never_issues_capability_when_exhaustion_is_not_durable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failing_operation: str
) -> None:
    artifact_path = tmp_path / "approval.json"
    artifact_path.write_text(
        '{"approval_id":"approval-20260309-0001","expires_at_utc":"2026-03-09T12:01:00Z"}'
    )
    artifact_path.chmod(0o600)

    def fail(*args: object) -> None:
        del args
        raise OSError("forced artifact exhaustion failure")

    monkeypatch.setattr(
        f"openstack_ai_ops_orchestrator.remote_acceptance.os.{failing_operation}",
        fail,
    )

    with pytest.raises(RemoteAcceptanceError) as rejected:
        consume_remote_acceptance_artifact(artifact_path, NOW)

    assert (
        rejected.value.category is RemoteAcceptanceErrorCategory.REMOTE_APPROVAL_INVALID
    )
    if failing_operation == "unlink":
        assert artifact_path.exists()
    else:
        assert not artifact_path.exists()


def test_consumer_rejects_permissive_artifact_without_exhausting_it(
    tmp_path: Path,
) -> None:
    artifact_path = tmp_path / "approval.json"
    artifact_path.write_text(
        '{"approval_id":"approval-20260309-0001","expires_at_utc":"2026-03-09T12:01:00Z"}'
    )
    artifact_path.chmod(0o640)

    with pytest.raises(RemoteAcceptanceError) as rejected:
        consume_remote_acceptance_artifact(artifact_path, NOW)

    assert (
        rejected.value.category is RemoteAcceptanceErrorCategory.REMOTE_APPROVAL_INVALID
    )
    assert artifact_path.exists()
