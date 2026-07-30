"""Tests for the closed fake-only runtime entrypoint."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from itertools import count
from pathlib import Path
from typing import cast

import pytest
from openai_codex.generated.v2_all import (
    Thread,
    ThreadItem,
    ThreadStartedNotification,
    Turn,
    TurnCompletedNotification,
    TurnItemsView,
    TurnStartedNotification,
    TurnStatus,
)
from openai_codex.models import Notification

from openstack_ai_ops_orchestrator import runtime_entrypoint
from openstack_ai_ops_orchestrator.contracts import (
    RuntimePolicy,
    SafeToolResult,
    ToolCallRequest,
)
from openstack_ai_ops_orchestrator.official_codex_adapter import (
    MockedSdkLifecycleFactory,
    OfficialSdkFactory,
)
from openstack_ai_ops_orchestrator.redaction import redact_tool_result
from openstack_ai_ops_orchestrator.remote_acceptance import (
    RemoteAcceptancePolicy,
    ValidatedOneShotApproval,
    validate_remote_acceptance_policy,
)
from openstack_ai_ops_orchestrator.runtime_entrypoint import (
    ExitCategory,
    InvocationProfile,
    _fixed_remote_policy,
    _fixed_remote_request,
    _run_disabled_remote_entrypoint,
    _run_fixed_remote_mocked,
    _run_fixed_remote_operation,
    _run_validate_local_fake,
    main,
)


def test_default_invocation_completes_the_fixed_fake_profile() -> None:
    assert main() is ExitCategory.SUCCESS


def test_remote_profile_is_disabled_before_any_adapter_selection() -> None:
    assert (
        main(("--profile", InvocationProfile.REMOTE.value))
        is ExitCategory.REMOTE_DISABLED
    )


@pytest.mark.parametrize(
    "arguments",
    (
        ("--prompt", "caller-content"),
        ("--path", "/caller/path"),
        ("--adapter", "official"),
        ("--model", "caller-model"),
        ("--url", "https://example.invalid"),
        ("--egress", "enabled"),
    ),
)
def test_arbitrary_runtime_input_is_rejected(arguments: tuple[str, str]) -> None:
    assert main(arguments) is ExitCategory.INVOCATION_REJECTED


def test_fixed_fake_workflow_writes_private_temporary_evidence(tmp_path: Path) -> None:
    result = _run_validate_local_fake(tmp_path)

    ledger_path = tmp_path / "validate-local-fake.jsonl"
    assert result is ExitCategory.SUCCESS
    assert tmp_path.stat().st_mode & 0o777 == 0o700
    assert ledger_path.stat().st_mode & 0o777 == 0o600
    assert len(ledger_path.read_text().splitlines()) == 2


def test_entrypoint_source_excludes_runtime_configuration_and_live_boundaries() -> None:
    source = Path(runtime_entrypoint.__file__).read_text()

    for prohibited_reference in (
        "subprocess",
        "requests",
        "urllib",
        "argparse",
        "os.environ",
        "sys.argv",
    ):
        assert prohibited_reference not in source


def mocked_notification_sequence() -> tuple[Notification, ...]:
    thread = Thread.model_construct(id="thread-1")
    started_turn = Turn.model_validate(
        {
            "id": "turn-1",
            "items": [],
            "items_view": TurnItemsView.full,
            "status": TurnStatus.in_progress,
        }
    )
    terminal_item = ThreadItem.model_validate(
        {"id": "item-1", "text": "safe advisory", "type": "agentMessage"}
    )
    completed_turn = Turn.model_validate(
        {
            "id": "turn-1",
            "items": [terminal_item],
            "items_view": TurnItemsView.full,
            "status": TurnStatus.completed,
        }
    )
    return (
        Notification(
            "thread/started", ThreadStartedNotification.model_construct(thread=thread)
        ),
        Notification(
            "turn/started",
            TurnStartedNotification.model_construct(
                thread_id="thread-1", turn=started_turn
            ),
        ),
        Notification(
            "turn/completed",
            TurnCompletedNotification.model_construct(
                thread_id="thread-1", turn=completed_turn
            ),
        ),
    )


class MockSdkStream:
    def __init__(self) -> None:
        self._events = iter(mocked_notification_sequence())
        self.closed = False

    def __aiter__(self) -> MockSdkStream:
        return self

    async def __anext__(self) -> Notification:
        try:
            return next(self._events)
        except StopIteration as error:
            raise StopAsyncIteration from error

    async def aclose(self) -> None:
        self.closed = True


class MockSdkTurn:
    def __init__(self, stream: MockSdkStream) -> None:
        self.id = "turn-1"
        self.stream_value = stream

    def stream(self) -> MockSdkStream:
        return self.stream_value

    async def interrupt(self) -> object:
        return object()


class MockSdkThread:
    def __init__(self, turn: MockSdkTurn) -> None:
        self.id = "thread-1"
        self.turn_value = turn
        self.input: str | None = None

    async def turn(self, input: str) -> MockSdkTurn:
        self.input = input
        return self.turn_value


class MockSdkClient:
    def __init__(self, thread: MockSdkThread) -> None:
        self.thread = thread
        self.closed = False

    async def thread_start(self) -> MockSdkThread:
        return self.thread

    async def close(self) -> None:
        self.closed = True


class MockReviewedProxy:
    def __init__(self) -> None:
        self.requests: list[tuple[ToolCallRequest, str]] = []
        self.closed = False

    async def forward(
        self, request: ToolCallRequest, correlation_id: str
    ) -> SafeToolResult:
        self.requests.append((request, correlation_id))
        return redact_tool_result(
            {
                "tool_name": request.tool_name,
                "category": "ok",
                "content": '{"project_count":1}',
                "truncated": False,
                "request_sequence_number": request.sequence_number,
            },
            maximum_raw_bytes=270464,
            maximum_content_bytes=131072,
            maximum_redactions=10000,
        )

    async def aclose(self) -> None:
        self.closed = True


_approval_ids = count()


def approved_remote_acceptance() -> ValidatedOneShotApproval:
    policy = RemoteAcceptancePolicy(
        approval_id=f"entrypoint-approval-{next(_approval_ids)}",
        expires_at=datetime.now(UTC) + timedelta(minutes=1),
    )
    return validate_remote_acceptance_policy(policy, datetime.now(UTC))


def test_fixed_remote_profile_has_no_caller_selected_values() -> None:
    request = _fixed_remote_request()
    policy = _fixed_remote_policy()

    assert request == {
        "workflow": RemoteAcceptancePolicy.workflow,
        "correlation_id": "remote-acceptance-1",
        "redacted_context": RemoteAcceptancePolicy.prompt_text,
    }
    assert policy.model_alias == RemoteAcceptancePolicy.model_alias
    assert (
        policy.fixed_working_directory == RemoteAcceptancePolicy.fixed_working_directory
    )
    assert policy.maximum_turn_count == policy.maximum_tool_call_count == 1


def test_mocked_remote_slice_consumes_approval_and_retains_metadata_only_evidence(
    tmp_path: Path,
) -> None:
    stream = MockSdkStream()
    client = MockSdkClient(MockSdkThread(MockSdkTurn(stream)))
    proxy = MockReviewedProxy()
    presented: list[str] = []

    result = _run_fixed_remote_mocked(
        approved_remote_acceptance(),
        tmp_path,
        cast(MockedSdkLifecycleFactory, lambda: client),
        lambda policy: proxy,
        presented.append,
    )

    ledger_path = tmp_path / "remote-acceptance.jsonl"
    assert result is ExitCategory.SUCCESS
    assert proxy.requests == [
        (ToolCallRequest(RemoteAcceptancePolicy.workflow, (), 1), "remote-acceptance-1")
    ]
    assert proxy.closed
    assert client.closed
    assert client.thread.input == RemoteAcceptancePolicy.prompt_text
    assert stream.closed
    assert presented == []
    assert tmp_path.stat().st_mode & 0o777 == 0o700
    assert ledger_path.stat().st_mode & 0o777 == 0o600
    assert len(ledger_path.read_text().splitlines()) == 2
    assert RemoteAcceptancePolicy.prompt_text not in ledger_path.read_text()


def test_remote_slice_rejects_missing_or_reused_approval_before_proxy_or_sdk(
    tmp_path: Path,
) -> None:
    factory_calls: list[RuntimePolicy] = []
    approval = approved_remote_acceptance()
    first_client = MockSdkClient(MockSdkThread(MockSdkTurn(MockSdkStream())))
    first_proxy = MockReviewedProxy()
    factory = cast(MockedSdkLifecycleFactory, lambda: first_client)

    assert (
        _run_fixed_remote_mocked(
            None,
            tmp_path,
            factory,
            lambda policy: first_proxy,
            lambda advisory: None,
        )
        is ExitCategory.REMOTE_PREREQUISITE_FAILED
    )
    assert not first_proxy.requests
    assert not first_client.closed

    assert (
        _run_fixed_remote_mocked(
            approval,
            tmp_path,
            factory,
            lambda policy: first_proxy,
            lambda advisory: None,
        )
        is ExitCategory.SUCCESS
    )

    def unexpected_proxy(policy: RuntimePolicy) -> MockReviewedProxy:
        factory_calls.append(policy)
        return first_proxy

    assert (
        _run_fixed_remote_mocked(
            approval,
            tmp_path / "reused",
            factory,
            unexpected_proxy,
            lambda advisory: None,
        )
        is ExitCategory.REMOTE_PREREQUISITE_FAILED
    )
    assert factory_calls == []


def test_disabled_remote_entrypoint_consumes_only_a_valid_artifact(
    tmp_path: Path,
) -> None:
    artifact_path = tmp_path / "approval.json"
    artifact_path.write_text(
        '{"approval_id":"entrypoint-artifact-1","expires_at_utc":"2026-03-09T12:01:00Z"}'
    )
    artifact_path.chmod(0o600)

    assert (
        _run_disabled_remote_entrypoint(
            artifact_path, datetime(2026, 3, 9, 12, tzinfo=UTC)
        )
        is ExitCategory.REMOTE_DISABLED
    )


def test_disabled_remote_entrypoint_rejects_invalid_artifact(tmp_path: Path) -> None:
    artifact_path = tmp_path / "approval.json"
    artifact_path.write_text("{}")
    artifact_path.chmod(0o600)

    assert (
        _run_disabled_remote_entrypoint(
            artifact_path, datetime(2026, 3, 9, 12, tzinfo=UTC)
        )
        is ExitCategory.REMOTE_PREREQUISITE_FAILED
    )


def test_fixed_remote_operation_consumes_artifact_before_injected_runtime(
    tmp_path: Path,
) -> None:
    artifact_path = tmp_path / "approval.json"
    artifact_path.write_text(
        '{"approval_id":"entrypoint-operation-1","expires_at_utc":"2026-03-09T12:01:00Z"}'
    )
    artifact_path.chmod(0o600)
    evidence_directory = tmp_path / "evidence"
    evidence_directory.mkdir(mode=0o700)
    stream = MockSdkStream()
    client = MockSdkClient(MockSdkThread(MockSdkTurn(stream)))
    proxy = MockReviewedProxy()
    factory_configs: list[object] = []
    presented: list[str] = []

    def official_factory(config: object) -> MockSdkClient:
        factory_configs.append(config)
        return client

    result = _run_fixed_remote_operation(
        artifact_path,
        datetime(2026, 3, 9, 12, tzinfo=UTC),
        evidence_directory,
        cast(OfficialSdkFactory, official_factory),
        lambda policy: proxy,
        presented.append,
    )

    assert result is ExitCategory.SUCCESS
    assert not artifact_path.exists()
    assert len(factory_configs) == 1
    assert proxy.closed
    assert client.closed
    assert stream.closed
    assert presented == []


def test_fixed_remote_operation_rejects_artifact_before_proxy_or_sdk(
    tmp_path: Path,
) -> None:
    artifact_path = tmp_path / "approval.json"
    evidence_directory = tmp_path / "evidence"
    evidence_directory.mkdir(mode=0o700)
    factory_calls: list[object] = []
    proxy_calls: list[RuntimePolicy] = []

    def official_factory(config: object) -> MockSdkClient:
        factory_calls.append(config)
        return MockSdkClient(MockSdkThread(MockSdkTurn(MockSdkStream())))

    def proxy_factory(policy: RuntimePolicy) -> MockReviewedProxy:
        proxy_calls.append(policy)
        return MockReviewedProxy()

    assert (
        _run_fixed_remote_operation(
            artifact_path,
            datetime(2026, 3, 9, 12, tzinfo=UTC),
            evidence_directory,
            cast(OfficialSdkFactory, official_factory),
            proxy_factory,
            lambda advisory: None,
        )
        is ExitCategory.REMOTE_PREREQUISITE_FAILED
    )
    assert factory_calls == []
    assert proxy_calls == []
