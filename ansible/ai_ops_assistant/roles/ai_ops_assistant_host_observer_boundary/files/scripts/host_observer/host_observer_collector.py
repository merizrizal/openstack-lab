#!/usr/bin/env python3
"""Fail-closed host-observer collector boundary.

This boundary validates a closed request and one root-owned, host-specific
policy. It reads only policy-approved fixed sources through adapter-specific
argv and returns bounded, normalized, redacted evidence. It never accepts a
caller-selected command, path, unit, source, timeout, or output cap.
"""

from __future__ import annotations

import grp
import hashlib
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

SCHEMA_VERSION = "1.0"
TOOL_NAME = "host_observer_collector"
METADATA_TOOL_NAME = "recent_metadata_errors"
METADATA_SECTION_NAME = "metadata_errors"
REQUEST_MAX_BYTES = 8192
SERIALIZED_OUTPUT_MAX_BYTES = 16_384
MAX_RECORDS = 20
MAX_RAW_SUMMARY_BYTES = 4_096
MAX_NORMALIZED_SUMMARY_BYTES = 512

SOURCE_CLASSES = frozenset(
    {
        "metadata_error_events",
        "neutron_error_events",
        "nova_error_events",
    }
)
WINDOW_CLASSES = frozenset({"15m", "30m", "1h"})
LINE_LIMIT_CLASSES = frozenset({"small", "medium", "large"})
WINDOW_DURATIONS = {"15m": 900, "30m": 1_800, "1h": 3_600}
LINE_LIMITS = {"small": 50, "medium": 100, "large": 200}
PROJECTION_FRESHNESS_CLASSES = frozenset({"current", "stale", "unknown"})
COLLECTOR_METADATA_PROJECTION_TYPE = "host_observer_metadata"

REQUEST_REQUIRED_FIELDS = {"schema_version", "host_label"}
REQUEST_OPTIONAL_FIELDS = {"source_class", "window_class", "line_limit_class"}
REQUEST_FIELDS = REQUEST_REQUIRED_FIELDS | REQUEST_OPTIONAL_FIELDS
METADATA_SOURCE_CLASS = "metadata_error_events"
METADATA_SERVICE_CLASS = "metadata"
METADATA_LOGICAL_SELECTOR = "metadata_service_errors"
METADATA_ROLE = "controller"
NEUTRON_TOOL_NAME = "recent_neutron_errors"
NEUTRON_SECTION_NAME = "neutron_errors"
NEUTRON_SOURCE_CLASS = "neutron_error_events"
NEUTRON_SERVICE_CLASS = "neutron"
NEUTRON_LOGICAL_SELECTOR = "neutron_service_errors"
NEUTRON_ROLE = "controller"
NOVA_TOOL_NAME = "recent_nova_errors"
NOVA_SECTION_NAME = "nova_errors"
NOVA_SOURCE_CLASS = "nova_error_events"
NOVA_SERVICE_CLASS = "nova"
NOVA_LOGICAL_SELECTOR = "nova_service_errors"
NOVA_ROLE = "controller"

POLICY_PATH = Path("/etc/openstack-ai-ops-assistant/host-observer-policy.yml")
POLICY_MAX_BYTES = 65_536
POLICY_FILE_MODE = 0o640
POLICY_GROUP_NAME = "aiops-host-observer"
COLLECTOR_TIMEOUT_SECONDS = 5.0
SOURCE_OUTPUT_MAX_BYTES = 1_048_576
MINIMAL_SOURCE_ENVIRONMENT = {
    "PATH": "/usr/bin:/bin",
    "LANG": "C",
    "LC_ALL": "C",
    "SYSTEMD_PAGER": "cat",
    "SYSTEMD_COLORS": "0",
}

ADAPTER_DEFINITIONS = {
    "metadata_agent_errors": {
        "kind": "journal",
        "argv": [
            "/usr/bin/journalctl",
            "--no-pager",
            "--quiet",
            "--utc",
            "--output=json",
            "--priority=err..emerg",
            "--unit",
            "neutron-metadata-agent",
        ],
    },
    "metadata_apache_errors": {
        "kind": "apache_error_log",
        "argv": [
            "/usr/bin/tail",
            "--",
            "/var/log/apache2/nova_metadata_error.log",
        ],
    },
    "neutron_server_errors": {
        "kind": "journal",
        "argv": [
            "/usr/bin/journalctl",
            "--no-pager",
            "--quiet",
            "--utc",
            "--output=json",
            "--priority=err..emerg",
            "--unit",
            "neutron-server",
        ],
    },
    "neutron_ovs_agent_errors": {
        "kind": "journal",
        "argv": [
            "/usr/bin/journalctl",
            "--no-pager",
            "--quiet",
            "--utc",
            "--output=json",
            "--priority=err..emerg",
            "--unit",
            "neutron-openvswitch-agent",
        ],
    },
    "nova_api_errors": {
        "kind": "journal",
        "argv": [
            "/usr/bin/journalctl",
            "--no-pager",
            "--quiet",
            "--utc",
            "--output=json",
            "--priority=err..emerg",
            "--unit",
            "nova-api",
        ],
    },
    "nova_conductor_errors": {
        "kind": "journal",
        "argv": [
            "/usr/bin/journalctl",
            "--no-pager",
            "--quiet",
            "--utc",
            "--output=json",
            "--priority=err..emerg",
            "--unit",
            "nova-conductor",
        ],
    },
    "nova_scheduler_errors": {
        "kind": "journal",
        "argv": [
            "/usr/bin/journalctl",
            "--no-pager",
            "--quiet",
            "--utc",
            "--output=json",
            "--priority=err..emerg",
            "--unit",
            "nova-scheduler",
        ],
    },
    "nova_apache_errors": {
        "kind": "apache_error_log",
        "argv": [
            "/usr/bin/tail",
            "--",
            "/var/log/apache2/nova_metadata_error.log",
        ],
    },
}
SOURCE_RECORD_FIELDS = {
    "source_sequence",
    "observed_at",
    "severity",
    "event_class",
    "summary",
}
SEVERITY_PRIORITY = {"critical": 0, "error": 1, "warning": 2, "info": 3, "unknown": 4}
SEVERITIES = frozenset(SEVERITY_PRIORITY)
EVENT_CLASSES = frozenset(
    {
        "request_error",
        "connection_error",
        "timeout",
        "authentication_error",
        "dependency_error",
        "configuration_error",
        "unknown",
    }
)
COLLECTOR_METADATA_PROJECTION_FIELDS = {
    "schema_version",
    "projection_type",
    "revision",
    "freshness_class",
    "entries",
}
COLLECTOR_METADATA_PROJECTION_ENTRY_FIELDS = {
    "host_label",
    "inventory_role",
    "source_classes",
    "enabled",
}
POLICY_FIELDS = {
    "schema_version",
    "policy_type",
    "revision",
    "generated_at",
    "expires_at",
    "freshness_class",
    "metadata_status",
    "redaction_policy_status",
    "source_classes",
    "window_classes",
    "line_limit_classes",
    "local_host_label",
    "hosts",
    "entries",
}
POLICY_HOST_FIELDS = {
    "host_label",
    "inventory_role",
    "source_classes",
    "enabled",
}
POLICY_ENTRY_FIELDS = {
    "source_class",
    "logical_selector",
    "inventory_role",
    "readers",
}
POLICY_READER_FIELDS = {"adapter_id", "argv"}
POLICY_SOURCE_CLASSES = [
    METADATA_SOURCE_CLASS,
    NEUTRON_SOURCE_CLASS,
    NOVA_SOURCE_CLASS,
]
POLICY_WINDOW_CLASSES = ["15m", "30m", "1h"]
POLICY_LINE_LIMIT_CLASSES = ["small", "medium", "large"]
POLICY_SELECTOR_BY_SOURCE = {
    METADATA_SOURCE_CLASS: METADATA_LOGICAL_SELECTOR,
    NEUTRON_SOURCE_CLASS: NEUTRON_LOGICAL_SELECTOR,
    NOVA_SOURCE_CLASS: NOVA_LOGICAL_SELECTOR,
}
POLICY_ROLE_SOURCE_CLASSES = {
    "controller": frozenset(POLICY_SOURCE_CLASSES),
    "compute": frozenset({NEUTRON_SOURCE_CLASS}),
}
EXPECTED_POLICY_READERS = {
    (METADATA_SOURCE_CLASS, "controller"): (
        "metadata_agent_errors",
        "metadata_apache_errors",
    ),
    (NEUTRON_SOURCE_CLASS, "controller"): (
        "neutron_server_errors",
        "neutron_ovs_agent_errors",
    ),
    (NEUTRON_SOURCE_CLASS, "compute"): ("neutron_ovs_agent_errors",),
    (NOVA_SOURCE_CLASS, "controller"): (
        "nova_api_errors",
        "nova_conductor_errors",
        "nova_scheduler_errors",
        "nova_apache_errors",
    ),
}

ERROR_MESSAGES = {
    "authorization_pending": "Host observation is unavailable.",
    "collector_stub": "Host observation collector is unavailable.",
    "invocation_denied": "Collector invocation is unavailable.",
    "validation_error": "Collector request is invalid.",
    "observer_integrity_error": "Observer metadata is unavailable.",
    "unsupported_deployment_state": "Observer deployment is unavailable.",
    "host_unavailable": "Approved host is unavailable.",
    "host_disabled": "Approved host is disabled.",
    "source_role_mismatch": "Approved source is unavailable for this host role.",
    "source_missing": "Approved source is missing.",
    "source_stale": "Approved source is stale.",
    "source_denied": "Approved source access is denied.",
    "malformed_source": "Approved source data is malformed.",
    "timeout": "Diagnostic exceeded its time limit.",
    "redaction_failure": "Diagnostic output could not be safely redacted.",
    "approved_optional_capability_absent": "Approved optional capability is unavailable.",
}


class CollectorValidationError(ValueError):
    """A request or metadata validation failure with a safe error class."""

    def __init__(self, error_class: str):
        super().__init__(error_class)
        self.error_class = error_class


class CollectorUnavailableError(CollectorValidationError):
    """A validated but unavailable projection or policy state."""


class PolicySnapshot:
    def __init__(
        self,
        policy: Mapping[str, Any],
        digest: str,
        signature: tuple[int, int, int, int, int],
        path: Path,
    ):
        self.policy = policy
        self.digest = digest
        self.signature = signature
        self.path = path


class SourceReadResult:
    def __init__(
        self, records: list[Mapping[str, Any]], source_truncated: bool = False
    ):
        self.records = records
        self.source_truncated = source_truncated


class SourceReaderError(CollectorValidationError):
    """A fixed source reader failed without exposing source details."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CollectorValidationError("duplicate_field")
        result[key] = value
    return result


def _require_mapping(
    value: Any, error_class: str = "validation_error"
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CollectorValidationError(error_class)
    return value


def _require_string(value: Any, error_class: str = "validation_error") -> str:
    if not isinstance(value, str) or not value or len(value) > 128:
        raise CollectorValidationError(error_class)
    return value


def _require_closed_string(value: Any, allowed: frozenset[str]) -> str:
    text = _require_string(value)
    if text not in allowed:
        raise CollectorValidationError("unsupported_class")
    return text


def _validate_host_label(value: Any) -> str:
    label = _require_string(value)
    if len(label) > 64 or label[0] == "-" or label[-1] == "-":
        raise CollectorValidationError("unsafe_host_label")
    if any(
        character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in label
    ):
        raise CollectorValidationError("unsafe_host_label")
    return label


def _policy_signature(metadata: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _read_policy_bytes(path: Path) -> tuple[bytes, tuple[int, int, int, int, int]]:
    try:
        expected_gid = grp.getgrnam(POLICY_GROUP_NAME).gr_gid
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode):
                raise CollectorUnavailableError("observer_integrity_error")
            if metadata.st_uid != 0 or metadata.st_gid != expected_gid:
                raise CollectorUnavailableError("observer_integrity_error")
            if stat.S_IMODE(metadata.st_mode) != POLICY_FILE_MODE:
                raise CollectorUnavailableError("observer_integrity_error")
            payload = stream.read(POLICY_MAX_BYTES + 1)
    except CollectorUnavailableError:
        raise
    except (KeyError, OSError):
        raise CollectorUnavailableError("observer_integrity_error") from None
    if len(payload) > POLICY_MAX_BYTES:
        raise CollectorUnavailableError("observer_integrity_error")
    return payload, _policy_signature(metadata)


def load_policy(
    path: Path = POLICY_PATH,
    *,
    now: datetime | None = None,
) -> PolicySnapshot:
    """Load one validated root-owned policy snapshot."""

    if Path(path) != POLICY_PATH:
        raise CollectorUnavailableError("observer_integrity_error")
    payload, signature = _read_policy_bytes(POLICY_PATH)
    try:
        policy = json.loads(
            payload.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
        policy = validate_policy_metadata(policy, now=now)
    except CollectorValidationError as error:
        if error.error_class in {"source_stale", "unsupported_deployment_state"}:
            raise
        raise CollectorUnavailableError("observer_integrity_error") from None
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
        raise CollectorUnavailableError("observer_integrity_error") from None
    return PolicySnapshot(
        policy=policy,
        digest=hashlib.sha256(payload).hexdigest(),
        signature=signature,
        path=path,
    )


def verify_policy_snapshot(snapshot: PolicySnapshot) -> None:
    """Reject a policy replaced or modified during one collection."""

    payload, signature = _read_policy_bytes(snapshot.path)
    if (
        signature != snapshot.signature
        or hashlib.sha256(payload).hexdigest() != snapshot.digest
    ):
        raise CollectorUnavailableError("observer_integrity_error")


def parse_request(raw: bytes | str) -> dict[str, Any]:
    """Parse the closed collector request without reading any source."""

    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    if not isinstance(raw, bytes) or len(raw) > REQUEST_MAX_BYTES:
        raise CollectorValidationError("request_oversized")
    try:
        request = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except (UnicodeDecodeError, json.JSONDecodeError, CollectorValidationError):
        raise CollectorValidationError("validation_error") from None

    request = _require_mapping(request)
    if (
        not REQUEST_REQUIRED_FIELDS <= set(request)
        or not set(request) <= REQUEST_FIELDS
    ):
        raise CollectorValidationError("unknown_or_missing_field")
    if request["schema_version"] != SCHEMA_VERSION:
        raise CollectorValidationError("unsupported_schema")
    normalized = {
        "schema_version": SCHEMA_VERSION,
        "host_label": _validate_host_label(request["host_label"]),
        "source_class": (
            _require_closed_string(request["source_class"], SOURCE_CLASSES)
            if "source_class" in request
            else None
        ),
        "window_class": _require_closed_string(
            request.get("window_class", "30m"), WINDOW_CLASSES
        ),
        "line_limit_class": _require_closed_string(
            request.get("line_limit_class", "medium"), LINE_LIMIT_CLASSES
        ),
    }
    return normalized


def validate_projection_metadata(projection: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate non-secret projection metadata supplied by a synthetic caller."""

    projection = _require_mapping(projection, "observer_integrity_error")
    if (
        set(projection) != COLLECTOR_METADATA_PROJECTION_FIELDS
        or projection["schema_version"] != SCHEMA_VERSION
        or projection["projection_type"] != COLLECTOR_METADATA_PROJECTION_TYPE
    ):
        raise CollectorValidationError("observer_integrity_error")
    _require_string(projection["revision"], "observer_integrity_error")
    freshness = _require_closed_string(
        projection["freshness_class"], PROJECTION_FRESHNESS_CLASSES
    )
    if freshness != "current":
        raise CollectorUnavailableError("projection_stale")
    entries = projection["entries"]
    if not isinstance(entries, list) or not entries:
        raise CollectorUnavailableError("projection_unavailable")

    labels: set[str] = set()
    for entry in entries:
        entry = _require_mapping(entry, "observer_integrity_error")
        if set(entry) != COLLECTOR_METADATA_PROJECTION_ENTRY_FIELDS:
            raise CollectorValidationError("observer_integrity_error")
        label = _validate_host_label(entry["host_label"])
        if label in labels:
            raise CollectorValidationError("duplicate_projection_label")
        labels.add(label)
        _require_string(entry["inventory_role"], "observer_integrity_error")
        source_classes = entry["source_classes"]
        if (
            not isinstance(source_classes, list)
            or not source_classes
            or any(source not in SOURCE_CLASSES for source in source_classes)
            or len(set(source_classes)) != len(source_classes)
        ):
            raise CollectorValidationError("observer_integrity_error")
        if not isinstance(entry["enabled"], bool):
            raise CollectorValidationError("observer_integrity_error")
    return projection


def validate_policy_metadata(
    policy: Mapping[str, Any],
    *,
    now: datetime | None = None,
) -> Mapping[str, Any]:
    """Validate one complete non-transport host-observer policy."""

    policy = _require_mapping(policy, "observer_integrity_error")
    if set(policy) != POLICY_FIELDS or policy["schema_version"] != SCHEMA_VERSION:
        raise CollectorValidationError("observer_integrity_error")
    if policy["policy_type"] != "host_observer_policy":
        raise CollectorValidationError("observer_integrity_error")
    _require_string(policy["revision"], "observer_integrity_error")
    generated_at = _parse_utc_timestamp(policy["generated_at"])
    expires_at = _parse_utc_timestamp(policy["expires_at"])
    current_time = datetime.now(timezone.utc) if now is None else now
    if (
        generated_at > current_time
        or expires_at <= generated_at
        or expires_at < current_time
        or expires_at - generated_at > timedelta(hours=24)
    ):
        raise CollectorUnavailableError("source_stale")
    if policy["freshness_class"] != "current":
        raise CollectorUnavailableError("source_stale")
    if policy["metadata_status"] != "accepted":
        raise CollectorUnavailableError("unsupported_deployment_state")
    if policy["redaction_policy_status"] != "accepted":
        raise CollectorUnavailableError("unsupported_deployment_state")
    if policy["source_classes"] != POLICY_SOURCE_CLASSES:
        raise CollectorValidationError("observer_integrity_error")
    if policy["window_classes"] != POLICY_WINDOW_CLASSES:
        raise CollectorValidationError("observer_integrity_error")
    if policy["line_limit_classes"] != POLICY_LINE_LIMIT_CLASSES:
        raise CollectorValidationError("observer_integrity_error")

    local_host_label = _validate_host_label(policy["local_host_label"])
    hosts = policy["hosts"]
    if not isinstance(hosts, list) or len(hosts) != 1:
        raise CollectorValidationError("observer_integrity_error")
    host = _require_mapping(hosts[0], "observer_integrity_error")
    if set(host) != POLICY_HOST_FIELDS:
        raise CollectorValidationError("observer_integrity_error")
    if _validate_host_label(host["host_label"]) != local_host_label:
        raise CollectorValidationError("observer_integrity_error")
    role = host["inventory_role"]
    if not isinstance(role, str) or role not in POLICY_ROLE_SOURCE_CLASSES:
        raise CollectorValidationError("observer_integrity_error")
    if host["source_classes"] != sorted(POLICY_ROLE_SOURCE_CLASSES[role]):
        raise CollectorValidationError("observer_integrity_error")
    if not isinstance(host["enabled"], bool):
        raise CollectorValidationError("observer_integrity_error")

    entries = policy["entries"]
    if not isinstance(entries, list) or len(entries) != len(EXPECTED_POLICY_READERS):
        raise CollectorValidationError("observer_integrity_error")
    seen: set[tuple[str, str]] = set()
    for entry_value in entries:
        entry = _require_mapping(entry_value, "observer_integrity_error")
        if set(entry) != POLICY_ENTRY_FIELDS:
            raise CollectorValidationError("observer_integrity_error")
        source_class = _require_closed_string(entry["source_class"], SOURCE_CLASSES)
        inventory_role = entry["inventory_role"]
        if (
            not isinstance(inventory_role, str)
            or inventory_role not in POLICY_ROLE_SOURCE_CLASSES
        ):
            raise CollectorValidationError("observer_integrity_error")
        selector = entry["logical_selector"]
        if selector != POLICY_SELECTOR_BY_SOURCE[source_class]:
            raise CollectorValidationError("observer_integrity_error")
        key = (source_class, inventory_role)
        if key in seen or key not in EXPECTED_POLICY_READERS:
            raise CollectorValidationError("observer_integrity_error")
        seen.add(key)
        readers = entry["readers"]
        expected_adapters = EXPECTED_POLICY_READERS[key]
        if not isinstance(readers, list) or len(readers) != len(expected_adapters):
            raise CollectorValidationError("observer_integrity_error")
        for reader_value, expected_adapter_id in zip(readers, expected_adapters):
            reader = _require_mapping(reader_value, "observer_integrity_error")
            if set(reader) != POLICY_READER_FIELDS:
                raise CollectorValidationError("observer_integrity_error")
            if reader["adapter_id"] != expected_adapter_id:
                raise CollectorValidationError("observer_integrity_error")
            definition = ADAPTER_DEFINITIONS[expected_adapter_id]
            if reader["argv"] != definition["argv"]:
                raise CollectorValidationError("observer_integrity_error")
    if seen != set(EXPECTED_POLICY_READERS):
        raise CollectorValidationError("observer_integrity_error")
    return policy


def resolve_projection(
    request: Mapping[str, Any], projection: Mapping[str, Any]
) -> Mapping[str, str]:
    """Resolve only non-secret projection metadata; never return a destination."""

    request = parse_request(json.dumps(dict(request), sort_keys=True))
    projection = validate_projection_metadata(projection)
    for entry in projection["entries"]:
        if entry["host_label"] != request["host_label"]:
            continue
        if not entry["enabled"]:
            raise CollectorUnavailableError("host_disabled")
        if request["source_class"] not in entry["source_classes"]:
            raise CollectorUnavailableError("source_role_mismatch")
        return {
            "host_label": entry["host_label"],
            "inventory_role": entry["inventory_role"],
            "source_class": request["source_class"],
        }
    raise CollectorUnavailableError("host_unavailable")


def validate_boundary(
    request: Mapping[str, Any],
    projection: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> Mapping[str, str]:
    """Validate all closed metadata and return no transport or source details."""

    request = parse_request(json.dumps(dict(request), sort_keys=True))
    policy = validate_policy_metadata(policy)
    if request["source_class"] not in policy["source_classes"]:
        raise CollectorUnavailableError("source_role_mismatch")
    if request["window_class"] not in policy["window_classes"]:
        raise CollectorUnavailableError("unsupported_class")
    if request["line_limit_class"] not in policy["line_limit_classes"]:
        raise CollectorUnavailableError("unsupported_class")
    return resolve_projection(request, projection)


METADATA_SOURCE_OUTCOMES = {
    "missing": "source_missing",
    "stale": "source_stale",
    "denied": "source_denied",
    "malformed": "malformed_source",
    "timeout": "timeout",
}


def _metadata_error_status(error_class: str) -> str:
    if error_class == "source_denied":
        return "denied"
    if error_class == "timeout":
        return "timeout"
    if error_class in {"malformed_source", "redaction_failure", "validation_error"}:
        return "error"
    return "unavailable"


def _metadata_error_document(error_class: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": METADATA_TOOL_NAME,
        "status": _metadata_error_status(error_class),
        "sections": [],
        "error": {
            "class": error_class,
            "message": ERROR_MESSAGES[error_class],
        },
    }


def _metadata_success_document(
    events: list[dict[str, str]], truncated: bool
) -> dict[str, Any]:
    section_status = "ok" if events else "empty"
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": METADATA_TOOL_NAME,
        "status": "ok",
        "sections": [
            {
                "name": METADATA_SECTION_NAME,
                "status": section_status,
                "data": events,
                "error": None,
                "truncated": truncated,
            }
        ],
        "error": None,
    }


def _parse_utc_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        if not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z",
            value,
        ):
            raise CollectorValidationError("malformed_source")
        try:
            parsed = datetime.fromisoformat(value[:-1] + "+00:00")
        except ValueError:
            raise CollectorValidationError("malformed_source") from None
    else:
        raise CollectorValidationError("malformed_source")
    if parsed.tzinfo is None:
        raise CollectorValidationError("malformed_source")
    return parsed.astimezone(timezone.utc)


def _canonical_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _line_limit_from_bounds(bounds: Mapping[str, Any]) -> int:
    line_limit_class = bounds.get("line_limit_class")
    if line_limit_class not in LINE_LIMITS:
        raise SourceReaderError("observer_integrity_error")
    return LINE_LIMITS[line_limit_class]


def _build_reader_argv(
    reader: Mapping[str, Any],
    bounds: Mapping[str, Any],
    collection_started_at: datetime,
) -> tuple[str, list[str]]:
    if set(reader) != POLICY_READER_FIELDS:
        raise SourceReaderError("observer_integrity_error")
    adapter_id = reader.get("adapter_id")
    definition = ADAPTER_DEFINITIONS.get(adapter_id)
    if definition is None or reader.get("argv") != definition["argv"]:
        raise SourceReaderError("observer_integrity_error")
    line_limit = _line_limit_from_bounds(bounds) + 1
    argv = list(definition["argv"])
    if definition["kind"] == "journal":
        window_class = bounds.get("window_class")
        if window_class not in WINDOW_DURATIONS:
            raise SourceReaderError("observer_integrity_error")
        earliest = collection_started_at - timedelta(
            seconds=WINDOW_DURATIONS[window_class]
        )
        return adapter_id, argv + [
            "--since",
            earliest.strftime("%Y-%m-%d %H:%M:%S.%f UTC"),
            "--until",
            collection_started_at.strftime("%Y-%m-%d %H:%M:%S.%f UTC"),
            "--lines",
            str(line_limit),
        ]
    if definition["kind"] == "apache_error_log":
        return adapter_id, [argv[0], "--lines", str(line_limit), *argv[1:]]
    raise SourceReaderError("observer_integrity_error")


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    try:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=1.0)
    except (ProcessLookupError, OSError, subprocess.TimeoutExpired):
        pass


def execute_fixed_argv(
    argv: Sequence[str],
    timeout_seconds: float,
    *,
    output_limit: int = SOURCE_OUTPUT_MAX_BYTES,
) -> tuple[subprocess.CompletedProcess[bytes], bool]:
    """Execute one approved argv with bounded binary output and no shell."""

    try:
        process = subprocess.Popen(
            list(argv),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            cwd="/",
            env=dict(MINIMAL_SOURCE_ENVIRONMENT),
            start_new_session=True,
        )
    except FileNotFoundError:
        raise SourceReaderError("source_missing") from None
    except PermissionError:
        raise SourceReaderError("source_denied") from None
    except OSError:
        raise SourceReaderError("source_denied") from None

    assert process.stdout is not None
    assert process.stderr is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    stdout = bytearray()
    source_truncated = False
    started = time.monotonic()
    try:
        while selector.get_map():
            remaining = timeout_seconds - (time.monotonic() - started)
            if remaining <= 0:
                _terminate_process_group(process)
                raise SourceReaderError("timeout")
            events = selector.select(remaining)
            if not events:
                _terminate_process_group(process)
                raise SourceReaderError("timeout")
            for key, _ in events:
                chunk = os.read(key.fileobj.fileno(), 65_536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                if key.data != "stdout":
                    continue
                available = output_limit - len(stdout)
                if len(chunk) > available:
                    stdout.extend(chunk[:available])
                    source_truncated = True
                    _terminate_process_group(process)
                    selector.close()
                    process.wait(timeout=1.0)
                    return (
                        subprocess.CompletedProcess(
                            list(argv), process.returncode, bytes(stdout), b""
                        ),
                        True,
                    )
                stdout.extend(chunk)
    finally:
        selector.close()
        if process.poll() is None:
            _terminate_process_group(process)
    if process.returncode is None:
        try:
            process.wait(timeout=0.2)
        except subprocess.TimeoutExpired:
            _terminate_process_group(process)
    return (
        subprocess.CompletedProcess(list(argv), process.returncode, bytes(stdout), b""),
        source_truncated,
    )


def _parse_decimal_integer(value: Any) -> int:
    if isinstance(value, bool):
        raise SourceReaderError("malformed_source")
    if isinstance(value, int):
        result = value
    elif isinstance(value, str) and value.isdecimal():
        result = int(value)
    else:
        raise SourceReaderError("malformed_source")
    if result < 0:
        raise SourceReaderError("malformed_source")
    return result


def _journal_severity(value: Any) -> str:
    priority = _parse_decimal_integer(value)
    if priority <= 2:
        return "critical"
    if priority == 3:
        return "error"
    if priority == 4:
        return "warning"
    if priority in {5, 6}:
        return "info"
    if priority == 7:
        return "unknown"
    raise SourceReaderError("malformed_source")


def _journal_timestamp(value: Any) -> str:
    micros = _parse_decimal_integer(value)
    try:
        parsed = datetime.fromtimestamp(micros / 1_000_000, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        raise SourceReaderError("malformed_source") from None
    return _canonical_timestamp(parsed)


def _parse_journal_output(
    payload: bytes,
    adapter_id: str,
    source_truncated: bool,
) -> SourceReadResult:
    if payload and not payload.endswith(b"\n") and not source_truncated:
        raise SourceReaderError("malformed_source")
    lines = payload.splitlines()
    if source_truncated and lines and not payload.endswith(b"\n"):
        lines.pop()
    expected_unit = ADAPTER_DEFINITIONS[adapter_id]["argv"][-1]
    records: list[Mapping[str, Any]] = []
    for line in lines:
        try:
            record = json.loads(
                line.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys
            )
        except (UnicodeDecodeError, json.JSONDecodeError, CollectorValidationError):
            raise SourceReaderError("malformed_source") from None
        if not isinstance(record, Mapping):
            raise SourceReaderError("malformed_source")
        if record.get("_SYSTEMD_UNIT") != expected_unit:
            raise SourceReaderError("malformed_source")
        message = record.get("MESSAGE")
        if not isinstance(message, str):
            raise SourceReaderError("malformed_source")
        records.append(
            {
                "source_sequence": _parse_decimal_integer(record.get("_SEQNUM")),
                "observed_at": _journal_timestamp(record.get("__REALTIME_TIMESTAMP")),
                "severity": _journal_severity(record.get("PRIORITY")),
                "event_class": "unknown",
                "summary": message,
            }
        )
    return SourceReadResult(records, source_truncated)


_APACHE_ERROR_LINE = re.compile(
    r"^\[(?P<timestamp>[A-Za-z]{3} [A-Za-z]{3} \d{1,2} "
    r"\d{2}:\d{2}:\d{2}\.\d{1,6} \d{4})\]"
    r"(?: \[[^\]]+\])+ (?P<message>.+)$"
)


def _parse_apache_output(payload: bytes, source_truncated: bool) -> SourceReadResult:
    if payload and not payload.endswith(b"\n") and not source_truncated:
        raise SourceReaderError("malformed_source")
    lines = payload.splitlines()
    if source_truncated and lines and not payload.endswith(b"\n"):
        lines.pop()
    records: list[Mapping[str, Any]] = []
    for sequence, line in enumerate(lines):
        try:
            text = line.decode("utf-8")
        except UnicodeDecodeError:
            raise SourceReaderError("malformed_source") from None
        match = _APACHE_ERROR_LINE.fullmatch(text)
        if match is None:
            raise SourceReaderError("malformed_source")
        try:
            parsed = datetime.strptime(
                match.group("timestamp"), "%a %b %d %H:%M:%S.%f %Y"
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            raise SourceReaderError("malformed_source") from None
        records.append(
            {
                "source_sequence": sequence,
                "observed_at": _canonical_timestamp(parsed),
                "severity": "error",
                "event_class": "unknown",
                "summary": match.group("message"),
            }
        )
    return SourceReadResult(records, source_truncated)


def read_approved_source(
    policy_reader: Mapping[str, Any],
    bounds: Mapping[str, Any],
    collection_started_at: datetime,
    *,
    execute: Callable[
        ..., tuple[subprocess.CompletedProcess[bytes], bool]
    ] = execute_fixed_argv,
    deadline: float | None = None,
) -> SourceReadResult:
    """Read one policy-approved source through its fixed adapter."""

    adapter_id, argv = _build_reader_argv(policy_reader, bounds, collection_started_at)
    if deadline is None:
        deadline = time.monotonic() + COLLECTOR_TIMEOUT_SECONDS
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise SourceReaderError("timeout")
    completed, source_truncated = execute(argv, remaining)
    if completed.returncode != 0 and not source_truncated:
        raise SourceReaderError("source_denied")
    kind = ADAPTER_DEFINITIONS[adapter_id]["kind"]
    if kind == "journal":
        return _parse_journal_output(
            completed.stdout or b"", adapter_id, source_truncated
        )
    if kind == "apache_error_log":
        return _parse_apache_output(completed.stdout or b"", source_truncated)
    raise SourceReaderError("observer_integrity_error")


def _normalize_summary(value: Any) -> str:
    if not isinstance(value, str):
        raise CollectorValidationError("malformed_source")
    try:
        if len(value.encode("utf-8")) > MAX_RAW_SUMMARY_BYTES:
            raise CollectorValidationError("malformed_source")
    except UnicodeEncodeError:
        raise CollectorValidationError("malformed_source") from None
    value = unicodedata.normalize("NFC", value)
    value = "".join(
        " " if ord(character) < 32 or ord(character) == 127 else character
        for character in value
    )
    value = " ".join(value.split())
    if not value:
        raise CollectorValidationError("malformed_source")
    return value


def _redact_assignment(match: re.Match[str]) -> str:
    return re.sub(r"([:=]).*", r"\1[REDACTED]", match.group(0), count=1)


_REDACTION_PATTERNS = (
    (
        re.compile(
            r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
            re.IGNORECASE | re.DOTALL,
        ),
        "[REDACTED]",
    ),
    (
        re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^@\s]+@[^/\s]+", re.IGNORECASE),
        "[REDACTED]",
    ),
    (re.compile(r"\bBearer\s+[^\s,;]+", re.IGNORECASE), "Bearer [REDACTED]"),
    (
        re.compile(
            r"\b(?:authorization|proxy-authorization)\s*[:=]\s*(?:bearer\s+)?[^\s,;]+",
            re.IGNORECASE,
        ),
        _redact_assignment,
    ),
    (
        re.compile(
            r"\b(?:password|passwd|passphrase|pwd|token|api[_-]?key|secret)\s*[:=]\s*[^\s,;]+",
            re.IGNORECASE,
        ),
        _redact_assignment,
    ),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[REDACTED]"),
    (
        re.compile(r"(?<![\w:])[0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{0,4}){2,7}(?![\w:])"),
        "[REDACTED]",
    ),
    (re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b"), "[REDACTED]"),
    (
        re.compile(
            r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[1-5][0-9A-Fa-f]{3}-[89ABab][0-9A-Fa-f]{3}-[0-9A-Fa-f]{12}\b"
        ),
        "[REDACTED]",
    ),
    (re.compile(r"\b[a-z0-9]+(?:[-.][a-z0-9]+)+\b", re.IGNORECASE), "[REDACTED]"),
)
_REDACTION_CANARY_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^@\s]+@[^/\s]+", re.IGNORECASE),
    re.compile(r"\bBearer\s+(?!\[REDACTED\])[^\s,;]+", re.IGNORECASE),
    re.compile(
        r"\b(?:authorization|proxy-authorization)\s*[:=]\s*(?!\[REDACTED\])[^\s,;]+",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:password|passwd|passphrase|pwd|token|api[_-]?key|secret)\s*[:=]\s*(?!\[REDACTED\])[^\s,;]+",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    re.compile(r"(?<![\w:])[0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{0,4}){2,7}(?![\w:])"),
    re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b"),
    re.compile(
        r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[1-5][0-9A-Fa-f]{3}-[89ABab][0-9A-Fa-f]{3}-[0-9A-Fa-f]{12}\b"
    ),
    re.compile(r"\b[a-z0-9]+(?:[-.][a-z0-9]+)+\b", re.IGNORECASE),
)


def redact_summary(summary: str) -> str:
    """Redact fixed secret, address, identifier, and host-like canaries."""

    if summary == "__REDACTION_FAILURE__":
        raise CollectorValidationError("redaction_failure")
    redacted = summary
    for pattern, replacement in _REDACTION_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    if any(pattern.search(redacted) for pattern in _REDACTION_CANARY_PATTERNS):
        raise CollectorValidationError("redaction_failure")
    return redacted


def _truncate_utf8(value: str, maximum_bytes: int) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= maximum_bytes:
        return value
    return encoded[:maximum_bytes].decode("utf-8", errors="ignore")


def _source_outcome(source_records: Any) -> str | None:
    if source_records is None:
        return "source_missing"
    if isinstance(source_records, str):
        return METADATA_SOURCE_OUTCOMES.get(source_records)
    if isinstance(source_records, Mapping) and set(source_records) in (
        {"outcome"},
        {"status"},
    ):
        outcome = source_records.get("outcome", source_records.get("status"))
        if isinstance(outcome, str):
            return METADATA_SOURCE_OUTCOMES.get(outcome)
    return None


def collect_metadata_slice(
    source_records: Sequence[Mapping[str, Any]] | Mapping[str, Any] | str | None,
    source_truncated: bool,
    freshness_class: str,
    host_label: str,
    inventory_role: str,
    window_class: str,
    line_limit_class: str,
    collection_started_at: datetime | str,
) -> dict[str, Any]:
    """Collect one bounded, synthetic metadata evidence slice."""

    if freshness_class != "current":
        return _metadata_error_document("source_stale")
    if inventory_role != METADATA_ROLE:
        return _metadata_error_document("source_role_mismatch")

    try:
        host_label = _validate_host_label(host_label)
        window_class = _require_closed_string(window_class, WINDOW_CLASSES)
        line_limit_class = _require_closed_string(line_limit_class, LINE_LIMIT_CLASSES)
        if not isinstance(source_truncated, bool):
            raise CollectorValidationError("malformed_source")
        collection_start = _parse_utc_timestamp(collection_started_at)
        source_error = _source_outcome(source_records)
        if source_error is not None:
            return _metadata_error_document(source_error)
        if not isinstance(source_records, (list, tuple)):
            raise CollectorValidationError("malformed_source")

        line_limit = LINE_LIMITS[line_limit_class]
        bounded_records = source_records[:line_limit]
        truncated = source_truncated or len(source_records) > line_limit
        earliest_allowed = collection_start - timedelta(
            seconds=WINDOW_DURATIONS[window_class]
        )
        prepared_records: list[dict[str, Any]] = []
        for record in bounded_records:
            if not isinstance(record, Mapping) or set(record) != SOURCE_RECORD_FIELDS:
                raise CollectorValidationError("malformed_source")
            sequence = record["source_sequence"]
            if (
                isinstance(sequence, bool)
                or not isinstance(sequence, int)
                or sequence < 0
            ):
                raise CollectorValidationError("malformed_source")
            if not isinstance(record["observed_at"], str):
                raise CollectorValidationError("malformed_source")
            observed_at = _parse_utc_timestamp(record["observed_at"])
            if observed_at > collection_start:
                raise CollectorValidationError("malformed_source")
            summary = _normalize_summary(record["summary"])
            severity = record["severity"]
            event_class = record["event_class"]
            if not isinstance(severity, str) or not isinstance(event_class, str):
                raise CollectorValidationError("malformed_source")
            prepared_records.append(
                {
                    "source_sequence": sequence,
                    "observed_at": observed_at,
                    "severity": severity if severity in SEVERITIES else "unknown",
                    "event_class": (
                        event_class if event_class in EVENT_CLASSES else "unknown"
                    ),
                    "summary": summary,
                }
            )

        prepared_records = [
            record
            for record in prepared_records
            if earliest_allowed <= record["observed_at"] <= collection_start
        ]
        prepared_records.sort(
            key=lambda record: (
                -record["observed_at"].timestamp(),
                SEVERITY_PRIORITY[record["severity"]],
                record["event_class"],
                record["source_sequence"],
            )
        )
        if len(prepared_records) > MAX_RECORDS:
            prepared_records = prepared_records[:MAX_RECORDS]
            truncated = True

        events: list[dict[str, str]] = []
        try:
            for record in prepared_records:
                redacted_summary = redact_summary(record["summary"])
                redacted_summary = _truncate_utf8(
                    redacted_summary, MAX_NORMALIZED_SUMMARY_BYTES
                )
                events.append(
                    {
                        "host_label": host_label,
                        "inventory_role": METADATA_ROLE,
                        "source_class": METADATA_SOURCE_CLASS,
                        "service_class": METADATA_SERVICE_CLASS,
                        "observed_at": _canonical_timestamp(record["observed_at"]),
                        "severity": record["severity"],
                        "event_class": record["event_class"],
                        "redacted_summary": redacted_summary,
                    }
                )
        except Exception as error:
            if (
                isinstance(error, CollectorValidationError)
                and error.error_class != "redaction_failure"
            ):
                raise
            raise CollectorValidationError("redaction_failure") from None

        document = _metadata_success_document(events, truncated)
        while (
            len(
                (
                    json.dumps(
                        document,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    + "\n"
                ).encode("utf-8")
            )
            > SERIALIZED_OUTPUT_MAX_BYTES
            and document["sections"][0]["data"]
        ):
            document["sections"][0]["data"].pop()
            document["sections"][0]["truncated"] = True
        return document
    except CollectorValidationError as error:
        error_class = error.error_class
        if error_class not in ERROR_MESSAGES:
            error_class = "malformed_source"
        return _metadata_error_document(error_class)


def _with_diagnostic_identity(
    document: dict[str, Any],
    tool_name: str,
    section_name: str,
    source_class: str,
    service_class: str,
) -> dict[str, Any]:
    """Apply one fixed diagnostic identity without exposing a selector."""

    document["tool"] = tool_name
    if document["sections"]:
        section = document["sections"][0]
        section["name"] = section_name
        for event in section["data"]:
            event["source_class"] = source_class
            event["service_class"] = service_class
    return document


def collect_neutron_slice(
    source_records: Sequence[Mapping[str, Any]] | Mapping[str, Any] | str | None,
    source_truncated: bool,
    freshness_class: str,
    host_label: str,
    inventory_role: str,
    window_class: str,
    line_limit_class: str,
    collection_started_at: datetime | str,
) -> dict[str, Any]:
    """Collect one bounded, synthetic Neutron evidence slice."""

    document = collect_metadata_slice(
        source_records,
        source_truncated,
        freshness_class,
        host_label,
        inventory_role,
        window_class,
        line_limit_class,
        collection_started_at,
    )
    return _with_diagnostic_identity(
        document,
        NEUTRON_TOOL_NAME,
        NEUTRON_SECTION_NAME,
        NEUTRON_SOURCE_CLASS,
        NEUTRON_SERVICE_CLASS,
    )


def collect_nova_slice(
    source_records: Sequence[Mapping[str, Any]] | Mapping[str, Any] | str | None,
    source_truncated: bool,
    freshness_class: str,
    host_label: str,
    inventory_role: str,
    window_class: str,
    line_limit_class: str,
    collection_started_at: datetime | str,
) -> dict[str, Any]:
    """Collect one bounded, synthetic Nova evidence slice."""

    document = collect_metadata_slice(
        source_records,
        source_truncated,
        freshness_class,
        host_label,
        inventory_role,
        window_class,
        line_limit_class,
        collection_started_at,
    )
    return _with_diagnostic_identity(
        document,
        NOVA_TOOL_NAME,
        NOVA_SECTION_NAME,
        NOVA_SOURCE_CLASS,
        NOVA_SERVICE_CLASS,
    )


def _diagnostic_tool_for_source(source_class: str | None) -> str:
    return {
        METADATA_SOURCE_CLASS: METADATA_TOOL_NAME,
        NEUTRON_SOURCE_CLASS: NEUTRON_TOOL_NAME,
        NOVA_SOURCE_CLASS: NOVA_TOOL_NAME,
    }.get(source_class, TOOL_NAME)


def _diagnostic_error_document(tool_name: str, error_class: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": tool_name,
        "status": _metadata_error_status(error_class),
        "sections": [],
        "error": {
            "class": error_class,
            "message": ERROR_MESSAGES.get(
                error_class, "Approved host-observer capability is unavailable."
            ),
        },
    }


def _document_exit_code(document: Mapping[str, Any]) -> int:
    return {
        "ok": 0,
        "error": 1,
        "denied": 2,
        "timeout": 4,
        "unavailable": 5,
    }.get(document.get("status"), 1)


def _resolve_runtime_host(
    request: Mapping[str, Any], policy: Mapping[str, Any]
) -> Mapping[str, Any]:
    if request["host_label"] != policy["local_host_label"]:
        raise CollectorUnavailableError("host_unavailable")
    host = policy["hosts"][0]
    if not host["enabled"]:
        raise CollectorUnavailableError("host_disabled")
    if request["source_class"] not in host["source_classes"]:
        raise CollectorUnavailableError("source_role_mismatch")
    return host


def _resolve_runtime_entry(
    request: Mapping[str, Any], host: Mapping[str, Any], policy: Mapping[str, Any]
) -> Mapping[str, Any]:
    expected_selector = POLICY_SELECTOR_BY_SOURCE[request["source_class"]]
    matches = [
        entry
        for entry in policy["entries"]
        if entry["source_class"] == request["source_class"]
        and entry["logical_selector"] == expected_selector
        and entry["inventory_role"] == host["inventory_role"]
    ]
    if len(matches) != 1:
        raise CollectorUnavailableError("observer_integrity_error")
    return matches[0]


def _collect_runtime_document(
    request: Mapping[str, Any],
    host: Mapping[str, Any],
    source_records: Sequence[Mapping[str, Any]],
    source_truncated: bool,
    collection_started_at: datetime,
) -> dict[str, Any]:
    arguments = (
        source_records,
        source_truncated,
        "current",
        request["host_label"],
        host["inventory_role"],
        request["window_class"],
        request["line_limit_class"],
        collection_started_at,
    )
    if request["source_class"] == METADATA_SOURCE_CLASS:
        return collect_metadata_slice(*arguments)
    if request["source_class"] == NEUTRON_SOURCE_CLASS:
        return collect_neutron_slice(*arguments)
    if request["source_class"] == NOVA_SOURCE_CLASS:
        return collect_nova_slice(*arguments)
    raise CollectorUnavailableError("source_role_mismatch")


def _run_runtime_request(
    request: Mapping[str, Any],
    snapshot: PolicySnapshot,
) -> tuple[int, dict[str, Any]]:
    policy = snapshot.policy
    host = _resolve_runtime_host(request, policy)
    entry = _resolve_runtime_entry(request, host, policy)
    collection_started_at = datetime.now(timezone.utc)
    deadline = time.monotonic() + COLLECTOR_TIMEOUT_SECONDS
    bounds = {
        "window_class": request["window_class"],
        "line_limit_class": request["line_limit_class"],
    }
    source_records: list[Mapping[str, Any]] = []
    source_truncated = False
    for reader in entry["readers"]:
        result = read_approved_source(
            reader,
            bounds,
            collection_started_at,
            execute=execute_fixed_argv,
            deadline=deadline,
        )
        source_records.extend(result.records)
        source_truncated = source_truncated or result.source_truncated
    document = _collect_runtime_document(
        request,
        host,
        source_records,
        source_truncated,
        collection_started_at,
    )
    verify_policy_snapshot(snapshot)
    return _document_exit_code(document), document


def unavailable_document(error_class: str = "collector_stub") -> dict[str, Any]:
    """Return a deterministic non-success document without source data."""

    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL_NAME,
        "status": "unavailable",
        "sections": [],
        "error": {
            "class": error_class,
            "message": ERROR_MESSAGES.get(
                error_class, "host observation is unavailable"
            ),
        },
    }


def error_document(error_class: str) -> dict[str, Any]:
    return {
        **unavailable_document(error_class),
        "status": "error",
    }


def run(
    argv: list[str] | tuple[str, ...] = (),
    environment: Mapping[str, str] | None = None,
    raw_request: bytes = b"",
) -> tuple[int, dict[str, Any]]:
    """Run one fixed policy-gated diagnostic request."""

    environment = {} if environment is None else environment
    if argv or environment.get("SSH_ORIGINAL_COMMAND", ""):
        return 2, error_document("invocation_denied")
    try:
        request = parse_request(raw_request)
        if request["source_class"] is None:
            raise CollectorValidationError("validation_error")
    except CollectorValidationError:
        return 2, error_document("validation_error")

    tool_name = _diagnostic_tool_for_source(request["source_class"])
    try:
        snapshot = load_policy()
        return _run_runtime_request(request, snapshot)
    except CollectorValidationError as error:
        document = _diagnostic_error_document(tool_name, error.error_class)
        return _document_exit_code(document), document


def main() -> int:
    raw_request = sys.stdin.buffer.read(REQUEST_MAX_BYTES + 1)
    exit_code, document = run(tuple(sys.argv[1:]), os.environ, raw_request)
    sys.stdout.write(json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
