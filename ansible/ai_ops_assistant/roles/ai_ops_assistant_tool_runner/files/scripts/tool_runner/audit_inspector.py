#!/usr/bin/env python3
"""Bounded, fixed-path audit correlation helper for protected validation use."""

from __future__ import annotations

import argparse
import grp
import json
import os
import pwd
import stat
import sys
import uuid
from pathlib import Path
from typing import Any, NoReturn

AUDIT_PATH = Path("/opt/openstack-ai-ops-assistant/audit/tool-runner.jsonl")
AUDIT_DIRECTORY = AUDIT_PATH.parent
AUDIT_OWNER = "aiops_assistant"
AUDIT_GROUP = "aiops_assistant"
AUDIT_MODE = 0o600
AUDIT_DIRECTORY_MODE = 0o700
MAX_SCAN_BYTES = 64 * 1024
EXPECTED_TOOLS = {
    "project_resource_summary",
    "server_basic_info",
    "server_network_info",
}
EXPECTED_FIELDS = {
    "schema_version",
    "timestamp",
    "event_type",
    "actor",
    "tool",
    "arguments",
    "status",
    "duration_ms",
    "correlation_id",
    "reason",
    "exit_code",
    "truncated",
}
EXPECTED_STATUSES = {
    "ok",
    "error",
    "denied",
    "validation_error",
    "timeout",
    "unavailable",
}


class AuditInspectionError(ValueError):
    """Raised with a safe, normalized audit-inspection failure class."""

    def __init__(self, error_class: str) -> None:
        super().__init__(error_class)
        self.error_class = error_class


def failure_class(message: str) -> str:
    """Map internal validation failures to non-sensitive public classes."""

    if any(
        marker in message
        for marker in (
            "metadata",
            "path type",
            "ownership",
            "mode",
            "open failed",
        )
    ):
        return "audit_metadata_failed"
    if "request" in message:
        return "audit_request_invalid"
    if "correlation format" in message or "correlation is invalid" in message:
        return "audit_correlation_invalid"
    if "duplicate" in message:
        return "audit_duplicate_correlation"
    if "incomplete" in message:
        return "audit_events_incomplete"
    if "bound" in message:
        return "audit_bound_exceeded"
    if "read failed" in message:
        return "audit_read_failed"
    if "event fields" in message:
        return "audit_event_fields_invalid"
    if "schema" in message:
        return "audit_schema_invalid"
    if "identity" in message:
        return "audit_identity_invalid"
    if "outcome" in message:
        return "audit_outcome_invalid"
    if "timestamp" in message:
        return "audit_timestamp_invalid"
    if "duration" in message:
        return "audit_duration_invalid"
    if "exit code" in message:
        return "audit_exit_code_invalid"
    if "truncation" in message:
        return "audit_truncation_invalid"
    if "arguments" in message:
        return "audit_arguments_invalid"
    if "reason" in message:
        return "audit_reason_invalid"
    if "not valid JSON" in message:
        return "audit_event_json_invalid"
    if "not an object" in message:
        return "audit_event_object_invalid"
    return "audit_inspection_failed"


def fail(message: str) -> "NoReturn":
    raise AuditInspectionError(failure_class(message))


def metadata_identity(owner: str, group: str) -> tuple[int, int]:
    try:
        return pwd.getpwnam(owner).pw_uid, grp.getgrnam(group).gr_gid
    except (KeyError, OSError):
        fail("audit metadata unavailable")


def assert_stat_metadata(
    metadata: os.stat_result,
    expected_mode: int,
    owner_uid: int,
    group_gid: int,
    directory: bool = False,
) -> None:
    if stat.S_ISLNK(metadata.st_mode) or (
        stat.S_ISDIR(metadata.st_mode) != directory
    ):
        fail("audit path type is unsafe")
    if metadata.st_uid != owner_uid or metadata.st_gid != group_gid:
        fail("audit ownership is unsafe")
    if stat.S_IMODE(metadata.st_mode) != expected_mode:
        fail("audit mode is unsafe")


def assert_metadata(
    path: Path, expected_mode: int, owner: str, group: str, directory: bool = False
) -> None:
    try:
        metadata = path.lstat()
    except OSError:
        fail("audit metadata unavailable")
    owner_uid, group_gid = metadata_identity(owner, group)
    assert_stat_metadata(metadata, expected_mode, owner_uid, group_gid, directory)


def open_fixed_audit_file() -> Any:
    owner_uid, group_gid = metadata_identity(AUDIT_OWNER, AUDIT_GROUP)
    directory_fd = -1
    audit_fd = -1
    try:
        directory_fd = os.open(
            str(AUDIT_DIRECTORY), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        )
        assert_stat_metadata(
            os.fstat(directory_fd),
            AUDIT_DIRECTORY_MODE,
            owner_uid,
            group_gid,
            directory=True,
        )
        audit_fd = os.open(
            AUDIT_PATH.name,
            os.O_RDONLY | os.O_NOFOLLOW,
            dir_fd=directory_fd,
        )
        assert_stat_metadata(
            os.fstat(audit_fd), AUDIT_MODE, owner_uid, group_gid
        )
        return os.fdopen(audit_fd, "rb")
    except (OSError, ValueError):
        if audit_fd >= 0:
            os.close(audit_fd)
        fail("audit metadata or open failed")
    finally:
        if directory_fd >= 0:
            os.close(directory_fd)


def normalized_event(event: dict[str, Any], correlation_id: str) -> dict[str, Any]:
    if set(event) != EXPECTED_FIELDS:
        fail("audit event fields are invalid")
    if event["schema_version"] != "1.0":
        fail("audit schema is invalid")
    if event["event_type"] != "tool_request_completed" or event["actor"] != "local_cli":
        fail("audit identity is invalid")
    if event["correlation_id"] != correlation_id:
        fail("audit correlation is invalid")
    if event["tool"] not in EXPECTED_TOOLS or event["status"] not in EXPECTED_STATUSES:
        fail("audit outcome is invalid")
    if not isinstance(event["timestamp"], str) or not event["timestamp"]:
        fail("audit timestamp is invalid")
    if not isinstance(event["duration_ms"], int) or event["duration_ms"] < 0:
        fail("audit duration is invalid")
    if event["exit_code"] is not None and (
        not isinstance(event["exit_code"], int) or isinstance(event["exit_code"], bool)
    ):
        fail("audit exit code is invalid")
    if not isinstance(event["truncated"], bool):
        fail("audit truncation is invalid")
    expected_arguments = (
        {"server_identifier_present": True}
        if event["tool"] != "project_resource_summary"
        else {}
    )
    if event["arguments"] != expected_arguments:
        fail("audit arguments are not minimum disclosure")
    if event["reason"] is not None and not isinstance(event["reason"], str):
        fail("audit reason is invalid")
    return {
        "schema_version": event["schema_version"],
        "timestamp": event["timestamp"],
        "tool": event["tool"],
        "status": event["status"],
        "duration_ms": event["duration_ms"],
        "correlation_id": event["correlation_id"],
        "reason": event["reason"],
        "exit_code": event["exit_code"],
        "truncated": event["truncated"],
        "arguments": event["arguments"],
    }


def inspect(offset: int, correlation_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    if offset < 0 or len(correlation_ids) != 3 or len(set(correlation_ids)) != 3:
        fail("audit inspection request is invalid")
    for correlation_id in correlation_ids:
        try:
            if str(uuid.UUID(correlation_id)) != correlation_id:
                fail("audit correlation format is invalid")
        except (ValueError, AttributeError):
            fail("audit correlation format is invalid")
    try:
        with open_fixed_audit_file() as audit_file:
            audit_file.seek(offset)
            content = audit_file.read(MAX_SCAN_BYTES + 1)
    except OSError:
        fail("audit read failed")
    if len(content) > MAX_SCAN_BYTES or (content and not content.endswith(b"\n")):
        fail("audit inspection exceeded its bound")

    found: dict[str, dict[str, Any]] = {}
    for line in content.splitlines():
        try:
            event = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
            fail("audit event is not valid JSON")
        if not isinstance(event, dict):
            fail("audit event is not an object")
        correlation_id = event.get("correlation_id")
        if correlation_id in correlation_ids:
            if correlation_id in found:
                fail("duplicate audit correlation")
            found[correlation_id] = normalized_event(event, correlation_id)
    if set(found) != set(correlation_ids):
        fail("matching audit events are incomplete")
    return {"events": [found[correlation_id] for correlation_id in correlation_ids]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--offset", type=int, required=True)
    parser.add_argument("correlation_ids", nargs=3)
    args = parser.parse_args(argv)
    try:
        result = inspect(args.offset, args.correlation_ids)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    except AuditInspectionError as error:
        print(
            json.dumps(
                {"error": {"class": error.error_class}, "events": []},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 1
    except (ValueError, KeyError, TypeError, OSError):
        print(
            json.dumps(
                {"error": {"class": "audit_inspection_failed"}, "events": []},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
