"""Tests for the closed fake-only runtime entrypoint."""

from __future__ import annotations

from pathlib import Path

import pytest

from openstack_ai_ops_orchestrator import runtime_entrypoint
from openstack_ai_ops_orchestrator.runtime_entrypoint import (
    ExitCategory,
    InvocationProfile,
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
        "official_codex_adapter",
        "openai_codex",
        "mcp_client",
        "socket",
        "subprocess",
        "requests",
        "urllib",
        "argparse",
        "os.environ",
        "sys.argv",
    ):
        assert prohibited_reference not in source
