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
    consume_one_shot_approval,
    run_disabled_remote_acceptance,
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
    with pytest.raises(ValueError, match="approval identifier"):
        RemoteAcceptancePolicy(approval_id="", expires_at=NOW + timedelta(minutes=1))


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
