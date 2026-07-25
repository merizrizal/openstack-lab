"""Closed one-shot approval contracts with a permanently disabled operation."""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import ClassVar

MAXIMUM_APPROVAL_LIFETIME = timedelta(minutes=5)
_VALIDATION_TOKEN = object()
_CONSUMPTION_TOKEN = object()


class RemoteAcceptanceErrorCategory(StrEnum):
    """Closed categories for the disabled remote-acceptance boundary."""

    REMOTE_APPROVAL_INVALID = "remote_approval_invalid"
    REMOTE_ACCEPTANCE_DISABLED = "remote_acceptance_disabled"


class RemoteAcceptanceError(RuntimeError):
    """Sanitized failure that exposes only a closed category."""

    def __init__(self, category: RemoteAcceptanceErrorCategory) -> None:
        super().__init__(category.value)
        self.category = category


@dataclass(frozen=True, slots=True)
class RemoteAcceptancePolicy:
    """Exact reviewed profile; only approval identity and expiry are variable."""

    approval_id: str
    expires_at: datetime

    request_allowance: ClassVar[int] = 1
    automatic_retry_allowance: ClassVar[int] = 0
    workflow: ClassVar[str] = "project_resource_summary"
    prompt_identifier: ClassVar[str] = "project_resource_summary_v1"
    prompt_text: ClassVar[str] = "Summarize reviewed project resources."
    model_alias: ClassVar[str] = "reviewed-model"
    maximum_turn_count: ClassVar[int] = 1
    maximum_tool_call_count: ClassVar[int] = 1
    fixed_working_directory: ClassVar[str] = "/run/openstack-ai-ops/remote-work"
    fixed_codex_home: ClassVar[str] = "/run/openstack-ai-ops/codex-home"
    fixed_evidence_directory: ClassVar[str] = "/run/openstack-ai-ops/evidence"
    fixed_mcp_proxy_socket: ClassVar[str] = (
        "/run/openstack-ai-ops/assistant-mcp-bridge.sock"
    )

    def __post_init__(self) -> None:
        if not isinstance(self.approval_id, str) or not self.approval_id:
            raise ValueError("approval identifier must be a non-empty string")
        if not isinstance(self.expires_at, datetime):
            raise ValueError("approval expiry must be a datetime")


@dataclass(slots=True)
class ValidatedOneShotApproval:
    """An approval capability issued only by the closed policy validator."""

    policy: RemoteAcceptancePolicy
    _validation_token: InitVar[object | None] = None
    _consumed: bool = field(default=False, init=False, repr=False)

    def __post_init__(self, _validation_token: object | None) -> None:
        if _validation_token is not _VALIDATION_TOKEN:
            raise ValueError("one-shot approvals require policy validation")


@dataclass(frozen=True, slots=True)
class ConsumedApproval:
    """A consumed marker that cannot authorize the disabled operation."""

    approval_id: str
    _consumption_token: InitVar[object | None] = None

    def __post_init__(self, _consumption_token: object | None) -> None:
        if _consumption_token is not _CONSUMPTION_TOKEN:
            raise ValueError("consumed approvals require one-shot consumption")


def validate_remote_acceptance_policy(
    policy: RemoteAcceptancePolicy, current_utc: datetime
) -> ValidatedOneShotApproval:
    """Validate a bounded UTC approval without touching any runtime boundary."""
    if (
        not isinstance(current_utc, datetime)
        or current_utc.tzinfo is not UTC
        or policy.expires_at.tzinfo is not UTC
        or policy.expires_at <= current_utc
        or policy.expires_at - current_utc > MAXIMUM_APPROVAL_LIFETIME
    ):
        raise RemoteAcceptanceError(
            RemoteAcceptanceErrorCategory.REMOTE_APPROVAL_INVALID
        )
    return ValidatedOneShotApproval(policy, _VALIDATION_TOKEN)


def consume_one_shot_approval(approval: ValidatedOneShotApproval) -> ConsumedApproval:
    """Consume a validated approval exactly once before any future runtime use."""
    if not isinstance(approval, ValidatedOneShotApproval) or approval._consumed:
        raise RemoteAcceptanceError(
            RemoteAcceptanceErrorCategory.REMOTE_APPROVAL_INVALID
        )
    approval._consumed = True
    return ConsumedApproval(approval.policy.approval_id, _CONSUMPTION_TOKEN)


def run_disabled_remote_acceptance(approval: ConsumedApproval) -> None:
    """Fail closed before SDK, MCP, process, network, or egress construction."""
    del approval
    raise RemoteAcceptanceError(
        RemoteAcceptanceErrorCategory.REMOTE_ACCEPTANCE_DISABLED
    )
