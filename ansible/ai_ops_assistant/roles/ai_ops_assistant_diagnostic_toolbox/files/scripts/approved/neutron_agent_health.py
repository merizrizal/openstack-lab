#!/usr/bin/env python3
"""Fixed, read-only Neutron agent health diagnostic."""

from __future__ import annotations

import json
import os
import re
import selectors
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping

TOOL_NAME = "neutron_agent_health"
SCHEMA_VERSION = "1.0"
OPERATOR_READER_PROFILE = "aiops-assistant-operator-reader"
OPERATOR_READER_CONFIG = "/opt/openstack-ai-ops-assistant/credentials/operator-reader/clouds.yaml"
OPENSTACK_BINARY = "/usr/bin/openstack"
FIXED_OPENSTACK_ARGV = ("network", "agent", "list", "-f", "json")
COMMAND_TIMEOUT_SECONDS = 10
INPUT_MAX_BYTES = 262144
OUTPUT_MAX_BYTES = 16384
RECORD_LIMIT = 50
TIMESTAMP_FIELDS = ("created_at", "updated_at", "heartbeat_timestamp")
AGENT_FIELDS = {
    "agent_type",
    "host_label_or_redacted_host",
    "alive",
    "admin_state_up",
    "diagnostic_timestamps",
}
TOP_LEVEL_FIELDS = {"schema_version", "tool", "status", "sections", "error"}
SECTION_FIELDS = {"name", "status", "data", "error", "truncated"}
SECRET_LIKE = re.compile(
    r"password|secret|token|credential|private[ _-]*key|authorization",
    re.IGNORECASE,
)


class DiagnosticFailure(Exception):
    """A normalized fail-closed diagnostic failure."""

    def __init__(self, error_class: str):
        super().__init__(error_class)
        self.error_class = error_class


def _error(error_class: str) -> dict[str, Any]:
    return {"class": error_class, "message": "read unavailable"}


def _error_document(error_class: str, status: str = "error") -> dict[str, Any]:
    failure = _error(error_class)
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL_NAME,
        "status": status,
        "sections": [
            {
                "name": "agents",
                "status": "unavailable" if status == "unavailable" else "error",
                "data": [],
                "error": failure,
                "truncated": False,
            }
        ],
        "error": failure,
    }


def _success_document(agents: list[dict[str, Any]], truncated: bool) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL_NAME,
        "status": "ok",
        "sections": [
            {
                "name": "agents",
                "status": "ok" if agents else "empty",
                "data": agents,
                "error": None,
                "truncated": truncated,
            }
        ],
        "error": None,
    }


def _encode(document: Mapping[str, Any]) -> bytes:
    return json.dumps(
        document,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _fixture_mode() -> bool:
    return os.environ.get("AIOPS_TEST_MODE") == "fixture"


def _profile_environment() -> dict[str, str]:
    cloud = os.environ.get("OS_CLOUD", "")
    config = os.environ.get("OS_CLIENT_CONFIG_FILE", "")
    if not cloud or not config:
        raise DiagnosticFailure("profile_missing_or_revoked")
    if cloud != OPERATOR_READER_PROFILE or config != OPERATOR_READER_CONFIG:
        raise DiagnosticFailure("profile_integrity_error")

    child_environment = {
        "PATH": "/usr/bin:/bin",
        "HOME": "/",
        "LANG": "C",
        "OS_CLOUD": cloud,
        "OS_CLIENT_CONFIG_FILE": config,
    }
    if _fixture_mode():
        for name in (
            "AIOPS_FIXTURE_SCENARIO",
            "AIOPS_FIXTURE_PAYLOAD_FILE",
            "AIOPS_TEST_ARGV_LOG",
            "AIOPS_TEST_ENV_LOG",
        ):
            if name in os.environ:
                child_environment[name] = os.environ[name]
    return child_environment


def _openstack_binary() -> str:
    binary = os.environ.get("AIOPS_TEST_OPENSTACK_BIN", "") if _fixture_mode() else OPENSTACK_BINARY
    if not binary or not Path(binary).is_file() or not os.access(binary, os.X_OK):
        raise DiagnosticFailure("configuration_error")
    return binary


def _classify_command_failure(message: str) -> str:
    lowered = message.lower()
    if "forbidden" in lowered or "http" in lowered and "403" in lowered:
        return "policy_denied"
    if "service unavailable" in lowered or "http" in lowered and "503" in lowered:
        return "service_unavailable"
    if "service catalog" in lowered or "endpoint not found" in lowered:
        return "catalog_missing"
    if any(
        marker in lowered
        for marker in (
            "connection refused",
            "timed out",
            "could not resolve",
            "name or service not known",
            "unreachable",
        )
    ):
        return "connectivity_error"
    if any(marker in lowered for marker in ("authentication", "unauthorized", "invalid credential")):
        return "authentication_error"
    if "unsupported" in lowered or "not supported" in lowered:
        return "unsupported_deployment_state"
    if "not found" in lowered or "no such service" in lowered:
        return "approved_optional_capability_absent"
    return "execution_error"


def _run_bounded_read(binary: str, child_environment: dict[str, str]) -> tuple[int, bytes, bytes]:
    try:
        process = subprocess.Popen(
            [binary, *FIXED_OPENSTACK_ARGV],
            env=child_environment,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise DiagnosticFailure("configuration_error") from exc

    assert process.stdout is not None
    assert process.stderr is not None
    selector = selectors.DefaultSelector()
    streams = {process.stdout: bytearray(), process.stderr: bytearray()}
    selector.register(process.stdout, selectors.EVENT_READ)
    selector.register(process.stderr, selectors.EVENT_READ)
    total_bytes = 0
    deadline = time.monotonic() + COMMAND_TIMEOUT_SECONDS
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise DiagnosticFailure("timeout")
            events = selector.select(remaining)
            if not events:
                raise DiagnosticFailure("timeout")
            for key, _ in events:
                chunk = os.read(key.fd, 8192)
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                total_bytes += len(chunk)
                if total_bytes > INPUT_MAX_BYTES:
                    raise DiagnosticFailure("output_limit_exceeded")
                streams[key.fileobj].extend(chunk)
        returncode = process.wait()
        return returncode, bytes(streams[process.stdout]), bytes(streams[process.stderr])
    except DiagnosticFailure:
        if process.poll() is None:
            process.kill()
        process.wait()
        raise
    except OSError as exc:
        if process.poll() is None:
            process.kill()
        process.wait()
        raise DiagnosticFailure("configuration_error") from exc
    finally:
        selector.close()
        if process.stdout is not None and not process.stdout.closed:
            process.stdout.close()
        if process.stderr is not None and not process.stderr.closed:
            process.stderr.close()


def _read_agent_payload() -> bytes:
    child_environment = _profile_environment()
    binary = _openstack_binary()
    returncode, stdout, stderr = _run_bounded_read(binary, child_environment)
    if returncode != 0:
        message = (stderr + stdout).decode("utf-8", errors="replace")
        raise DiagnosticFailure(_classify_command_failure(message))
    return stdout


def _safe_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        raise DiagnosticFailure("output_validation_error")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise DiagnosticFailure("output_validation_error")
    if SECRET_LIKE.search(value):
        return "***REDACTED***"
    return value


def _normalize_agent(record: Mapping[str, Any]) -> tuple[tuple[str, ...], dict[str, Any]]:
    required = ("agent_type", "host", "alive", "admin_state_up")
    if any(field not in record for field in required):
        raise DiagnosticFailure("unexpected_field")
    if type(record["alive"]) is not bool or type(record["admin_state_up"]) is not bool:
        raise DiagnosticFailure("output_validation_error")

    agent_type = _safe_string(record["agent_type"], "agent_type")
    _safe_string(record["host"], "host")
    timestamps: dict[str, str | None] = {}
    for field in TIMESTAMP_FIELDS:
        value = record.get(field)
        if value is not None:
            value = _safe_string(value, field)
        timestamps[field] = value

    normalized = {
        "agent_type": agent_type,
        "host_label_or_redacted_host": "***REDACTED***",
        "alive": record["alive"],
        "admin_state_up": record["admin_state_up"],
        "diagnostic_timestamps": timestamps,
    }
    sort_key = tuple(
        json.dumps(record.get(field, ""), ensure_ascii=True, sort_keys=True)
        for field in ("agent_type", "host", "binary", "id")
    )
    return sort_key, normalized


def _build_success(records: Any) -> dict[str, Any]:
    if not isinstance(records, list):
        raise DiagnosticFailure("output_decode_error")

    normalized = []
    for record in records:
        if not isinstance(record, dict):
            raise DiagnosticFailure("unexpected_field")
        normalized.append(_normalize_agent(record))
    normalized.sort(key=lambda item: item[0])

    selected = [item[1] for item in normalized[:RECORD_LIMIT]]
    truncated = len(normalized) > RECORD_LIMIT
    while True:
        document = _success_document(selected, truncated)
        if len(_encode(document)) <= OUTPUT_MAX_BYTES:
            return document
        if not selected:
            raise DiagnosticFailure("output_limit_exceeded")
        selected.pop()
        truncated = True


def validate_document(document: Mapping[str, Any]) -> None:
    if set(document) != TOP_LEVEL_FIELDS:
        raise DiagnosticFailure("unexpected_field")
    if document["schema_version"] != SCHEMA_VERSION or document["tool"] != TOOL_NAME:
        raise DiagnosticFailure("output_validation_error")
    if document["status"] not in {"ok", "unavailable", "error"}:
        raise DiagnosticFailure("output_validation_error")
    sections = document["sections"]
    if not isinstance(sections, list) or len(sections) != 1:
        raise DiagnosticFailure("output_validation_error")
    section = sections[0]
    if not isinstance(section, dict) or set(section) != SECTION_FIELDS or section["name"] != "agents":
        raise DiagnosticFailure("unexpected_field")
    if not isinstance(section["data"], list) or type(section["truncated"]) is not bool:
        raise DiagnosticFailure("output_validation_error")

    expected_section_status = {
        "ok": {"ok", "empty"},
        "unavailable": {"unavailable"},
        "error": {"error"},
    }
    if section["status"] not in expected_section_status[document["status"]]:
        raise DiagnosticFailure("output_validation_error")
    if document["status"] == "ok" and section["error"] is not None:
        raise DiagnosticFailure("output_validation_error")
    if document["status"] != "ok":
        if not isinstance(section["error"], dict) or set(section["error"]) != {"class", "message"}:
            raise DiagnosticFailure("output_validation_error")
        if document["error"] != section["error"]:
            raise DiagnosticFailure("output_validation_error")
    elif document["error"] is not None:
        raise DiagnosticFailure("output_validation_error")

    for agent in section["data"]:
        if not isinstance(agent, dict) or set(agent) != AGENT_FIELDS:
            raise DiagnosticFailure("unexpected_field")
        if not isinstance(agent["agent_type"], str) or not isinstance(
            agent["host_label_or_redacted_host"], str
        ):
            raise DiagnosticFailure("output_validation_error")
        if type(agent["alive"]) is not bool or type(agent["admin_state_up"]) is not bool:
            raise DiagnosticFailure("output_validation_error")
        timestamps = agent["diagnostic_timestamps"]
        if not isinstance(timestamps, dict) or set(timestamps) != set(TIMESTAMP_FIELDS):
            raise DiagnosticFailure("unexpected_field")
        if any(value is not None and not isinstance(value, str) for value in timestamps.values()):
            raise DiagnosticFailure("output_validation_error")


def _emit(document: Mapping[str, Any]) -> None:
    encoded = _encode(document)
    if len(encoded) > OUTPUT_MAX_BYTES:
        document = _error_document("output_limit_exceeded")
        encoded = _encode(document)
    sys.stdout.buffer.write(encoded + b"\n")


def main(arguments: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if arguments is None else arguments
    if arguments:
        document = _error_document("invalid_input")
        _emit(document)
        return 2

    try:
        raw = _read_agent_payload()
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DiagnosticFailure("invalid_utf8") from exc
        try:
            records = json.loads(decoded)
        except json.JSONDecodeError as exc:
            raise DiagnosticFailure("output_decode_error") from exc
        document = _build_success(records)
        validate_document(document)
    except DiagnosticFailure as exc:
        status = "unavailable" if exc.error_class in {
            "profile_missing_or_revoked",
            "profile_integrity_error",
            "policy_denied",
            "service_unavailable",
            "catalog_missing",
            "connectivity_error",
            "authentication_error",
            "approved_optional_capability_absent",
            "unsupported_deployment_state",
            "timeout",
        } else "error"
        document = _error_document(exc.error_class, status)
        validate_document(document)
        _emit(document)
        return 4

    _emit(document)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
