#!/usr/bin/env python3
"""Run fixed, policy-authorized host diagnostics over restricted SSH."""

from __future__ import annotations

import ipaddress
import json
import os
import stat
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, TextIO

POLICY_PATH = Path(
    "/opt/openstack-ai-ops/scripts/host_diagnostics/host_diagnostic_policy.json"
)
SSH_KEY_PATH = Path("/opt/openstack-ai-ops/credentials/ssh/observer_ed25519")
SSH_KNOWN_HOSTS_PATH = Path("/opt/openstack-ai-ops/credentials/ssh/known_hosts")
SSH_BINARY = "/usr/bin/ssh"
OBSERVER_USER = "aiops-observer"
CONNECTOR_TIMEOUT_SECONDS = 20
ALLOWED_KINDS = frozenset({"metadata", "nova", "neutron"})
ALLOWED_TIME_WINDOWS = frozenset({"15m", "30m", "1h"})


def load_host_policy(path: str | Path) -> dict[str, Any]:
    """Load one root-owned policy that cannot be group/world writable."""
    policy_path = Path(path)
    if not policy_path.is_absolute():
        raise ValueError("host policy path must be absolute")

    for managed_path in (policy_path, *policy_path.parents):
        try:
            metadata = os.stat(managed_path)
        except OSError as exc:
            raise ValueError(f"cannot inspect host policy: {exc}") from exc
        if metadata.st_uid != 0:
            raise ValueError("host policy path must be owned by root")
        if metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise ValueError("host policy path must not be group/world writable")

    if not stat.S_ISREG(os.stat(policy_path).st_mode):
        raise ValueError("host policy must be a regular file")

    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load host policy: {exc}") from exc

    if not isinstance(policy, dict) or set(policy) != {"aliases"}:
        raise ValueError("host policy must contain only an aliases mapping")
    if not isinstance(policy["aliases"], dict) or not policy["aliases"]:
        raise ValueError("host policy aliases must be a non-empty mapping")

    return policy


def validate_connector_request(
    kind: str,
    host_alias: str,
    time_window: str,
    policy: Mapping[str, Any],
) -> str:
    """Revalidate exact request values and return a policy-owned IP target."""
    if kind not in ALLOWED_KINDS:
        raise ValueError("unsupported diagnostic kind")
    if time_window not in ALLOWED_TIME_WINDOWS:
        raise ValueError("unsupported diagnostic time window")

    aliases = policy.get("aliases")
    if not isinstance(aliases, Mapping):
        raise ValueError("host policy aliases must be a mapping")
    target = aliases.get(host_alias)
    if not isinstance(target, Mapping):
        raise ValueError("host alias is not approved")

    address = target.get("address")
    if not isinstance(address, str):
        raise ValueError("host policy address must be a string")
    try:
        parsed_address = ipaddress.ip_address(address)
    except ValueError as exc:
        raise ValueError("host policy address must be an IP literal") from exc
    if parsed_address.version != 4 or str(parsed_address) != address:
        raise ValueError("host policy address must be a canonical IPv4 literal")

    for field, value, allowed_values in (
        ("kinds", kind, ALLOWED_KINDS),
        ("time_windows", time_window, ALLOWED_TIME_WINDOWS),
    ):
        configured_values = target.get(field)
        if (
            not isinstance(configured_values, list)
            or not configured_values
            or not all(isinstance(item, str) for item in configured_values)
            or not set(configured_values).issubset(allowed_values)
        ):
            raise ValueError(f"host policy {field} are invalid")
        if value not in configured_values:
            raise ValueError(f"host alias is not approved for {field}")

    return address


def build_ssh_argv(
    resolved_target: str,
    kind: str,
    time_window: str,
    key_path: str | Path,
    known_hosts_path: str | Path,
) -> list[str]:
    """Build SSH argv without a caller-controlled configuration or command."""
    if kind not in ALLOWED_KINDS or time_window not in ALLOWED_TIME_WINDOWS:
        raise ValueError("diagnostic kind and time window must be approved")
    try:
        parsed_target = ipaddress.ip_address(resolved_target)
    except ValueError as exc:
        raise ValueError("resolved target must be an IP literal") from exc
    if parsed_target.version != 4 or str(parsed_target) != resolved_target:
        raise ValueError("resolved target must be a canonical IPv4 literal")

    key = Path(key_path)
    known_hosts = Path(known_hosts_path)
    if not key.is_absolute() or not known_hosts.is_absolute():
        raise ValueError("SSH credential paths must be absolute")

    return [
        SSH_BINARY,
        "-F",
        "/dev/null",
        "-i",
        str(key),
        "-o",
        "BatchMode=yes",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "IdentityAgent=none",
        "-o",
        "PasswordAuthentication=no",
        "-o",
        "KbdInteractiveAuthentication=no",
        "-o",
        "NumberOfPasswordPrompts=0",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={known_hosts}",
        "-o",
        "GlobalKnownHostsFile=/dev/null",
        "-o",
        "UpdateHostKeys=no",
        "-o",
        "ForwardAgent=no",
        "-o",
        "ClearAllForwardings=yes",
        "-o",
        "RequestTTY=no",
        "-o",
        "PermitLocalCommand=no",
        "-l",
        OBSERVER_USER,
        resolved_target,
        "aiops-host-diagnostic",
        kind,
        time_window,
    ]


def validate_runtime_paths() -> None:
    """Fail before SSH when the dedicated key material is unavailable or broad."""
    for label, path in (
        ("private key", SSH_KEY_PATH),
        ("known hosts", SSH_KNOWN_HOSTS_PATH),
    ):
        try:
            metadata = os.stat(path)
        except OSError as exc:
            raise ValueError(f"connector {label} is unavailable: {exc}") from exc
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError(f"connector {label} must be a regular file")
        if metadata.st_mode & 0o077:
            raise ValueError(f"connector {label} has unsafe permissions")


def run_connector(
    argv: list[str],
    timeout_seconds: int,
    run_command: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> subprocess.CompletedProcess[str]:
    """Execute fixed SSH argv and deliberately propagate timeout/system errors."""
    if timeout_seconds < 1:
        raise ValueError("connector timeout must be positive")
    return run_command(
        argv,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        shell=False,
        check=False,
    )


def main(
    argv: list[str] | None = None,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
    run_command: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> int:
    """Accept only kind, policy alias, and window; no remote command input exists."""
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 3:
        stderr.write(
            "usage: aiops-host-diagnostic-connector KIND HOST_ALIAS TIME_WINDOW\n"
        )
        return 2

    kind, host_alias, time_window = arguments
    try:
        policy = load_host_policy(POLICY_PATH)
        validate_runtime_paths()
        resolved_target = validate_connector_request(
            kind, host_alias, time_window, policy
        )
        ssh_argv = build_ssh_argv(
            resolved_target,
            kind,
            time_window,
            SSH_KEY_PATH,
            SSH_KNOWN_HOSTS_PATH,
        )
        completed = run_connector(ssh_argv, CONNECTOR_TIMEOUT_SECONDS, run_command)
    except subprocess.TimeoutExpired:
        stderr.write("host diagnostic connector timed out\n")
        return 124
    except (OSError, ValueError) as exc:
        stderr.write(f"host diagnostic connector failed: {exc}\n")
        return 1

    stdout.write(completed.stdout or "")
    stderr.write(completed.stderr or "")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
