#!/usr/bin/env python3
"""Closed synthetic host-observer transport boundary.

This connector validates only fixed diagnostic requests and owner-provided
projection descriptors. It never accepts a remote command, shell fragment,
transport option, or caller-selected source. Missing runtime projection or key
material remains unavailable before SSH contact.
"""

from __future__ import annotations

import grp
import ipaddress
import json
import os
import pwd
import re
import stat
import subprocess
import sys
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, TextIO

SCHEMA_VERSION = "1.0"
HOST_OBSERVER_AUTHORITY = "aiops-assistant-host-observer"
REQUEST_MAX_BYTES = 8192
MAX_PROJECTION_BYTES = 65_536
MAX_PROJECTION_LIFETIME = timedelta(hours=24)
CONNECTOR_TIMEOUT_SECONDS = 5
CONNECTOR_OUTPUT_MAX_BYTES = 16_384
SSH_BINARY = "/usr/bin/ssh"
OBSERVER_USER = "aiops-host-observer"
DESTINATION_PROJECTION_PATH = Path(
    "/opt/openstack-ai-ops-assistant/credentials/host-observer/destination-projection.json"
)
DESTINATION_PROJECTION_TYPE = "host_observer_destination"
COLLECTOR_PATH = "/usr/local/libexec/openstack-ai-ops-assistant/host-observer-collector"
ALLOWED_WINDOW_CLASSES = frozenset({"15m", "30m", "1h"})
ALLOWED_LINE_LIMIT_CLASSES = frozenset({"small", "medium", "large"})
HOST_LABEL_PATTERN = r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$"
PROJECTION_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)

TOOL_SOURCE_MAPPINGS: dict[str, dict[str, str]] = {
    "recent_metadata_errors": {
        "source_class": "metadata_error_events",
        "service_class": "metadata",
        "logical_selector": "metadata_service_errors",
        "inventory_roles": ("controller",),
    },
    "recent_neutron_errors": {
        "source_class": "neutron_error_events",
        "service_class": "neutron",
        "logical_selector": "neutron_service_errors",
        "inventory_roles": ("controller", "compute"),
    },
    "recent_nova_errors": {
        "source_class": "nova_error_events",
        "service_class": "nova",
        "logical_selector": "nova_service_errors",
        "inventory_roles": ("controller",),
    },
}
SOURCE_TOOL_MAPPINGS = {
    values["source_class"]: tool for tool, values in TOOL_SOURCE_MAPPINGS.items()
}

DESTINATION_PROJECTION_FIELDS = {
    "schema_version",
    "projection_type",
    "revision",
    "generated_at",
    "expires_at",
    "entries",
}
DESTINATION_PROJECTION_ENTRY_FIELDS = {
    "host_label",
    "inventory_role",
    "source_classes",
    "enabled",
    "destination",
}
DESTINATION_FIELDS = {"address", "port", "user"}


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("request contains duplicate fields")
        result[key] = value
    return result


def _parse_projection_timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or PROJECTION_TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise ValueError("observer projection timestamp is invalid")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("observer projection timestamp is invalid") from exc
    return parsed.astimezone(timezone.utc)


def _validate_projection_entry_host_label(value: Any) -> str:
    if (
        not isinstance(value, str)
        or len(value.encode("utf-8")) > 64
        or re.fullmatch(HOST_LABEL_PATTERN, value) is None
    ):
        raise ValueError("observer projection host label is invalid")
    return value


def _validate_projection_owner(metadata: os.stat_result, expected_uid: int, expected_gid: int) -> None:
    if metadata.st_uid != expected_uid or metadata.st_gid != expected_gid:
        raise ValueError("observer projection ownership is unsafe")


def validate_protected_projection_path(
    path: str | Path,
    *,
    expected_uid: int | None = None,
    expected_gid: int | None = None,
) -> Path:
    """Require the owner-controlled projection directory and regular file."""

    projection_path = Path(path)
    if not projection_path.is_absolute():
        raise ValueError("observer projection path must be absolute")
    if expected_uid is None or expected_gid is None:
        try:
            expected_uid = pwd.getpwnam("aiops_assistant").pw_uid
            expected_gid = grp.getgrnam("aiops_assistant").gr_gid
        except KeyError as exc:
            raise ValueError("observer projection owner is unavailable") from exc
    try:
        parent_metadata = os.lstat(projection_path.parent)
        file_metadata = os.lstat(projection_path)
    except OSError as exc:
        raise ValueError("observer projection is unavailable") from exc
    if (
        stat.S_ISLNK(parent_metadata.st_mode)
        or not stat.S_ISDIR(parent_metadata.st_mode)
        or stat.S_IMODE(parent_metadata.st_mode) != 0o700
    ):
        raise ValueError("observer projection directory is unsafe")
    _validate_projection_owner(parent_metadata, expected_uid, expected_gid)
    if (
        stat.S_ISLNK(file_metadata.st_mode)
        or not stat.S_ISREG(file_metadata.st_mode)
        or stat.S_IMODE(file_metadata.st_mode) != 0o600
    ):
        raise ValueError("observer projection file is unsafe")
    _validate_projection_owner(file_metadata, expected_uid, expected_gid)
    return projection_path


def validate_destination_projection(
    projection: Mapping[str, Any], now: datetime | None = None
) -> Mapping[str, Any]:
    """Validate the protected transport projection without exposing its values."""

    if not isinstance(projection, Mapping) or set(projection) != DESTINATION_PROJECTION_FIELDS:
        raise ValueError("observer destination projection fields are invalid")
    if projection["schema_version"] != SCHEMA_VERSION:
        raise ValueError("observer destination projection schema is unsupported")
    if projection["projection_type"] != DESTINATION_PROJECTION_TYPE:
        raise ValueError("observer destination projection type is invalid")
    revision = projection["revision"]
    if not isinstance(revision, str) or not revision or len(revision) > 128:
        raise ValueError("observer projection revision is invalid")
    generated_at = _parse_projection_timestamp(projection["generated_at"])
    expires_at = _parse_projection_timestamp(projection["expires_at"])
    current_time = datetime.now(timezone.utc) if now is None else now.astimezone(timezone.utc)
    if generated_at > current_time or expires_at <= generated_at:
        raise ValueError("observer projection is stale")
    if expires_at - generated_at > MAX_PROJECTION_LIFETIME or current_time > expires_at:
        raise ValueError("observer projection is stale")
    entries = projection["entries"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("observer destination projection entries are invalid")

    labels: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping) or set(entry) != DESTINATION_PROJECTION_ENTRY_FIELDS:
            raise ValueError("observer destination projection entry is invalid")
        label = _validate_projection_entry_host_label(entry["host_label"])
        if label in labels:
            raise ValueError("observer destination projection is ambiguous")
        labels.add(label)
        if entry["inventory_role"] not in {"controller", "compute"}:
            raise ValueError("observer destination projection role is invalid")
        source_classes = entry["source_classes"]
        if (
            not isinstance(source_classes, list)
            or not source_classes
            or not all(isinstance(source, str) for source in source_classes)
            or len(set(source_classes)) != len(source_classes)
            or not set(source_classes) <= {
                values["source_class"] for values in TOOL_SOURCE_MAPPINGS.values()
            }
        ):
            raise ValueError("observer destination projection sources are invalid")
        if not isinstance(entry["enabled"], bool):
            raise ValueError("observer destination projection enablement is invalid")
        _validate_destination(entry["destination"])
    return projection


def load_destination_projection(
    path: str | Path = DESTINATION_PROJECTION_PATH,
    *,
    now: datetime | None = None,
    expected_uid: int | None = None,
    expected_gid: int | None = None,
) -> Mapping[str, Any]:
    """Load only the owner-controlled, fresh destination projection."""

    projection_path = validate_protected_projection_path(
        path, expected_uid=expected_uid, expected_gid=expected_gid
    )
    try:
        with projection_path.open("rb") as stream:
            raw_projection = stream.read(MAX_PROJECTION_BYTES + 1)
        if len(raw_projection) > MAX_PROJECTION_BYTES:
            raise ValueError("observer projection is oversized")
        projection = json.loads(
            raw_projection.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("observer destination projection is unavailable") from exc
    return validate_destination_projection(projection, now=now)


def _unavailable_document(tool_name: str, error_class: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": tool_name,
        "status": "unavailable",
        "sections": [],
        "error": {
            "class": error_class,
            "message": {
                "invocation_denied": "Collector invocation is unavailable.",
                "validation_error": "Collector request is invalid.",
                "approved_optional_capability_absent": "Approved optional capability is unavailable.",
            }.get(error_class, "Approved host-observer capability is unavailable."),
        },
    }


def validate_host_observer_request(
    tool_name: str,
    host_label: str,
    window_class: str = "30m",
    line_limit_class: str = "medium",
) -> dict[str, str]:
    """Validate closed caller values and derive the fixed source class."""

    if tool_name not in TOOL_SOURCE_MAPPINGS:
        raise ValueError("diagnostic tool is not approved")
    if not isinstance(window_class, str) or not isinstance(line_limit_class, str):
        raise ValueError("observer bound classes are invalid")
    if (
        not isinstance(host_label, str)
        or len(host_label.encode("utf-8")) > 64
        or re.fullmatch(HOST_LABEL_PATTERN, host_label) is None
    ):
        raise ValueError("host label is invalid")
    if window_class not in ALLOWED_WINDOW_CLASSES:
        raise ValueError("window class is invalid")
    if line_limit_class not in ALLOWED_LINE_LIMIT_CLASSES:
        raise ValueError("line limit class is invalid")
    return {
        "schema_version": SCHEMA_VERSION,
        "host_label": host_label,
        "source_class": TOOL_SOURCE_MAPPINGS[tool_name]["source_class"],
        "window_class": window_class,
        "line_limit_class": line_limit_class,
    }


def serialize_observer_request(request: Mapping[str, str]) -> bytes:
    """Serialize one bounded request with no caller-controlled transport data."""

    expected_fields = {
        "schema_version",
        "host_label",
        "source_class",
        "window_class",
        "line_limit_class",
    }
    if set(request) != expected_fields:
        raise ValueError("observer request fields are invalid")
    tool_name = SOURCE_TOOL_MAPPINGS.get(request.get("source_class"))
    if tool_name is None:
        raise ValueError("observer source class is invalid")
    expected_request = validate_host_observer_request(
        tool_name,
        request.get("host_label"),
        request.get("window_class"),
        request.get("line_limit_class"),
    )
    if dict(request) != expected_request:
        raise ValueError("observer request values are invalid")
    payload = (
        json.dumps(
            dict(request), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")
    if len(payload) > REQUEST_MAX_BYTES:
        raise ValueError("observer request is oversized")
    return payload


def resolve_observer_destination(
    tool_name: str,
    host_label: str,
    projection: Mapping[str, Any] | None,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Resolve a private fixed destination from an owner-provided projection."""

    validated_request = validate_host_observer_request(tool_name, host_label)
    if projection is None:
        raise ValueError("observer projection is unavailable")
    projection = validate_destination_projection(projection, now=now)
    source_class = TOOL_SOURCE_MAPPINGS[tool_name]["source_class"]
    allowed_roles = TOOL_SOURCE_MAPPINGS[tool_name]["inventory_roles"]
    matches = [
        entry
        for entry in projection["entries"]
        if entry["host_label"] == validated_request["host_label"]
    ]
    if len(matches) != 1:
        raise ValueError("observer host projection is unavailable")
    entry = matches[0]
    if entry["inventory_role"] not in allowed_roles or entry["enabled"] is not True:
        raise ValueError("observer host projection is not permitted")
    if source_class not in entry["source_classes"]:
        raise ValueError("observer source is not permitted")
    return _validate_destination(entry["destination"])


def validate_credential_path(path: str | Path) -> Path:
    """Require one absolute regular private credential with restrictive mode."""

    credential_path = Path(path)
    if not credential_path.is_absolute():
        raise ValueError("observer credential path must be absolute")
    try:
        metadata = os.stat(credential_path)
    except OSError as exc:
        raise ValueError("observer credential is unavailable") from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077:
        raise ValueError("observer credential permissions are unsafe")
    return credential_path


def _validate_destination(destination: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(destination, Mapping) or set(destination) != DESTINATION_FIELDS:
        raise ValueError("observer destination fields are invalid")
    address = destination["address"]
    if not isinstance(address, str):
        raise ValueError("observer destination address is invalid")
    try:
        parsed_address = ipaddress.ip_address(address)
    except ValueError as exc:
        raise ValueError("observer destination address is invalid") from exc
    if str(parsed_address) != address:
        raise ValueError("observer destination address is not canonical")
    port = destination["port"]
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("observer destination port is invalid")
    if destination["user"] != OBSERVER_USER:
        raise ValueError("observer destination user is invalid")
    return {"address": address, "port": port, "user": OBSERVER_USER}


def build_fixed_ssh_argv(
    destination: Mapping[str, Any], key_path: str | Path, known_hosts_path: str | Path
) -> list[str]:
    """Build fixed SSH argv; the forced collector supplies the remote command."""

    destination = _validate_destination(destination)
    key = validate_credential_path(key_path)
    known_hosts = validate_credential_path(known_hosts_path)
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
        "-p",
        str(destination["port"]),
        f"{OBSERVER_USER}@{destination['address']}",
    ]


def run_connector(
    request_payload: bytes,
    destination: Mapping[str, Any],
    key_path: str | Path,
    known_hosts_path: str | Path,
    run_command: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
) -> subprocess.CompletedProcess[bytes]:
    """Send exactly one bounded request to the fixed forced collector."""

    if len(request_payload) > REQUEST_MAX_BYTES:
        raise ValueError("observer request is oversized")
    argv = build_fixed_ssh_argv(destination, key_path, known_hosts_path)
    completed = run_command(
        argv,
        input=request_payload,
        capture_output=True,
        timeout=CONNECTOR_TIMEOUT_SECONDS,
        shell=False,
        check=False,
    )
    if (
        len(completed.stdout or b"") + len(completed.stderr or b"")
        > CONNECTOR_OUTPUT_MAX_BYTES
    ):
        raise ValueError("observer output is oversized")
    return completed


def tool_for_request(request: Mapping[str, Any]) -> str:
    source_class = request.get("source_class")
    if source_class not in SOURCE_TOOL_MAPPINGS:
        raise ValueError("observer source class is invalid")
    return SOURCE_TOOL_MAPPINGS[source_class]


def main(
    argv: list[str] | None = None,
    *,
    stdin: Any = None,
    stdout: TextIO = sys.stdout,
) -> int:
    """Reject arguments and remain unavailable until protected projection is deployed."""

    arguments = sys.argv[1:] if argv is None else argv
    if arguments:
        stdout.write(
            json.dumps(
                _unavailable_document("host_observer_connector", "invocation_denied")
            )
            + "\n"
        )
        return 2
    stream = sys.stdin.buffer if stdin is None else stdin
    try:
        raw_request = stream.read(REQUEST_MAX_BYTES + 1)
        if len(raw_request) > REQUEST_MAX_BYTES:
            raise ValueError("observer request is oversized")
        request = json.loads(
            raw_request.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
        tool_name = tool_for_request(request)
        if set(request) != {
            "schema_version",
            "host_label",
            "source_class",
            "window_class",
            "line_limit_class",
        }:
            raise ValueError("observer request fields are invalid")
        expected_request = validate_host_observer_request(
            tool_name,
            request.get("host_label"),
            request.get("window_class"),
            request.get("line_limit_class"),
        )
        if request != expected_request:
            raise ValueError("observer request values are invalid")
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        stdout.write(
            json.dumps(
                _unavailable_document("host_observer_connector", "validation_error")
            )
            + "\n"
        )
        return 2
    stdout.write(
        json.dumps(
            _unavailable_document(tool_name, "approved_optional_capability_absent")
        )
        + "\n"
    )
    return 5


if __name__ == "__main__":
    raise SystemExit(main())
