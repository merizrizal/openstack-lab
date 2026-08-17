"""Closed, non-activating readiness-manifest validation.

This module validates only non-secret manifest content supplied as a fixture or
later by an explicitly wired local gate. It never reads a runtime path, invokes
commands, contacts hosts, or materializes protected inputs.
"""

from __future__ import annotations

import json
import os
import re
import stat
import sys
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, TextIO

SCHEMA_VERSION = "1.0"
REQUIRED_RUN_ID = "2026-0004"
REQUIRED_AUTHORIZATION_REFERENCE = "phase06-live-acceptance-2026-0004"
REQUIRED_AUTHORIZATION_CLASS = "phase06-restricted-diagnostics-live-acceptance"
MAX_MANIFEST_LIFETIME = timedelta(hours=24)
MAX_MANIFEST_BYTES = 16_384
READINESS_MANIFEST_PATH = Path("/run/openstack-ai-ops/2026-0004/phase06-readiness.json")

TOP_LEVEL_FIELDS = frozenset(
    {
        "schema_version",
        "run_id",
        "authorization_reference",
        "authorization_class",
        "source_revision",
        "environment_label",
        "evidence_owner",
        "scope_approvals",
        "protected_input_references",
        "integrity_checks",
        "status",
        "issued_at",
        "expires_at",
    }
)
SCOPE_APPROVAL_FIELDS = frozenset(
    {
        "scope",
        "status",
        "owner_label",
        "authorization_reference",
        "outcome_evidence_reference",
    }
)
REQUIRED_SCOPES = frozenset(
    {
        "prerequisite_readiness",
        "operator_reader_deployment",
        "observer_deployment",
        "host_source_contact",
        "positive_validation",
        "negative_boundary_validation",
        "outcome_evidence_recording",
        "protected_audit_inspection",
        "unchanged_state_comparison",
        "revocation_rollback",
        "representative_workflow",
    }
)
SCOPE_STATUSES = frozenset({"approved", "pending", "denied", "revoked", "expired"})
PROTECTED_REFERENCE_FIELDS = frozenset(
    {
        "manifest_revision",
        "destination_projection_revision",
        "operator_reader_revision",
        "observer_key_revision",
        "host_collector_revision",
        "host_policy_revision",
    }
)
INTEGRITY_CHECK_FIELDS = frozenset(
    {
        "destination_projection_directory",
        "destination_projection_file",
        "destination_projection_freshness",
        "operator_reader_source",
        "operator_reader_target",
        "observer_private_key",
        "host_collector",
        "host_policy",
    }
)
INTEGRITY_CHECK_ENTRY_FIELDS = frozenset({"status", "outcome_evidence_reference"})
INTEGRITY_STATUSES = frozenset({"passed", "blocked", "failed", "unavailable"})
MANIFEST_STATUSES = frozenset({"ready", "blocked", "failed", "unavailable"})
OPAQUE_REFERENCE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._@-]{0,127}$")
ENVIRONMENT_LABEL_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")


class ManifestValidationError(ValueError):
    """Raised when a readiness manifest cannot safely satisfy the contract."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ManifestValidationError("manifest contains duplicate fields")
        result[key] = value
    return result


def _require_exact_keys(
    value: Any, expected: frozenset[str], message: str
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ManifestValidationError(message)
    return value


def _parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise ManifestValidationError("manifest timestamp is invalid")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)
    except ValueError as exc:
        raise ManifestValidationError("manifest timestamp is invalid") from exc


def _validate_opaque_reference(value: Any, run_id: str) -> str:
    if (
        not isinstance(value, str)
        or OPAQUE_REFERENCE_PATTERN.fullmatch(value) is None
        or not value.startswith(f"{run_id}-")
    ):
        raise ManifestValidationError("manifest reference is invalid")
    return value


def _validate_owner_label(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 96
        or "\n" in value
        or "\r" in value
    ):
        raise ManifestValidationError("manifest owner label is invalid")
    return value


def parse_manifest(payload: str | bytes) -> Mapping[str, Any]:
    """Parse one JSON object while rejecting duplicate object keys."""

    try:
        parsed = json.loads(payload, object_pairs_hook=_reject_duplicate_keys)
    except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestValidationError("manifest JSON is invalid") from exc
    if not isinstance(parsed, Mapping):
        raise ManifestValidationError("manifest document is invalid")
    return parsed


def validate_manifest(
    manifest: Mapping[str, Any], *, now: datetime | None = None
) -> Mapping[str, Any]:
    """Validate the closed manifest contract without accessing protected inputs."""

    document = _require_exact_keys(
        manifest, TOP_LEVEL_FIELDS, "manifest top-level fields are invalid"
    )
    if document["schema_version"] != SCHEMA_VERSION:
        raise ManifestValidationError("manifest schema version is unsupported")
    if document["run_id"] != REQUIRED_RUN_ID:
        raise ManifestValidationError("manifest run identifier is invalid")
    if document["authorization_reference"] != REQUIRED_AUTHORIZATION_REFERENCE:
        raise ManifestValidationError("manifest authorization reference is invalid")
    if document["authorization_class"] != REQUIRED_AUTHORIZATION_CLASS:
        raise ManifestValidationError("manifest authorization class is invalid")
    if (
        not isinstance(document["environment_label"], str)
        or ENVIRONMENT_LABEL_PATTERN.fullmatch(document["environment_label"]) is None
    ):
        raise ManifestValidationError("manifest environment label is invalid")
    _validate_owner_label(document["evidence_owner"])

    current_time = (
        datetime.now(timezone.utc) if now is None else now.astimezone(timezone.utc)
    )
    issued_at = _parse_timestamp(document["issued_at"])
    expires_at = _parse_timestamp(document["expires_at"])
    if (
        issued_at > current_time
        or expires_at <= issued_at
        or expires_at - issued_at > MAX_MANIFEST_LIFETIME
        or current_time > expires_at
    ):
        raise ManifestValidationError("manifest is stale")

    run_id = document["run_id"]
    _validate_opaque_reference(document["source_revision"], run_id)
    _validate_scope_approvals(document["scope_approvals"], run_id)
    _validate_protected_input_references(document["protected_input_references"], run_id)
    _validate_integrity_checks(document["integrity_checks"], run_id)

    status = document["status"]
    if status not in MANIFEST_STATUSES:
        raise ManifestValidationError("manifest status is invalid")
    if status == "ready" and not _is_ready(document):
        raise ManifestValidationError("manifest ready state is invalid")
    return document


def _validate_scope_approvals(value: Any, run_id: str) -> None:
    if not isinstance(value, list) or len(value) != len(REQUIRED_SCOPES):
        raise ManifestValidationError("manifest scope approvals are invalid")
    scopes: set[str] = set()
    for entry in value:
        approval = _require_exact_keys(
            entry, SCOPE_APPROVAL_FIELDS, "manifest scope approval fields are invalid"
        )
        scope = approval["scope"]
        if (
            not isinstance(scope, str)
            or scope not in REQUIRED_SCOPES
            or scope in scopes
        ):
            raise ManifestValidationError("manifest scope approval is invalid")
        scopes.add(scope)
        if approval["status"] not in SCOPE_STATUSES:
            raise ManifestValidationError("manifest scope approval status is invalid")
        _validate_owner_label(approval["owner_label"])
        if approval["authorization_reference"] != REQUIRED_AUTHORIZATION_REFERENCE:
            raise ManifestValidationError("manifest scope authorization is invalid")
        _validate_opaque_reference(approval["outcome_evidence_reference"], run_id)
    if scopes != REQUIRED_SCOPES:
        raise ManifestValidationError("manifest scope approvals are incomplete")


def _validate_protected_input_references(value: Any, run_id: str) -> None:
    references = _require_exact_keys(
        value,
        PROTECTED_REFERENCE_FIELDS,
        "manifest protected input references are invalid",
    )
    for reference in references.values():
        _validate_opaque_reference(reference, run_id)


def _validate_integrity_checks(value: Any, run_id: str) -> None:
    checks = _require_exact_keys(
        value, INTEGRITY_CHECK_FIELDS, "manifest integrity checks are invalid"
    )
    for check in checks.values():
        result = _require_exact_keys(
            check,
            INTEGRITY_CHECK_ENTRY_FIELDS,
            "manifest integrity check fields are invalid",
        )
        if result["status"] not in INTEGRITY_STATUSES:
            raise ManifestValidationError("manifest integrity status is invalid")
        _validate_opaque_reference(result["outcome_evidence_reference"], run_id)


def _is_ready(manifest: Mapping[str, Any]) -> bool:
    return all(
        entry["status"] == "approved" for entry in manifest["scope_approvals"]
    ) and all(
        check["status"] == "passed" for check in manifest["integrity_checks"].values()
    )


def evaluate_manifest(
    payload: str | bytes, *, now: datetime | None = None
) -> dict[str, Any]:
    """Return a normalized, non-secret readiness outcome for one fixture payload."""

    try:
        manifest = validate_manifest(parse_manifest(payload), now=now)
    except ManifestValidationError:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "blocked",
            "limitation_class": "readiness_manifest_invalid",
            "ready": False,
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": manifest["status"],
        "limitation_class": (
            "none" if manifest["status"] == "ready" else "readiness_not_ready"
        ),
        "ready": manifest["status"] == "ready",
    }


def _validate_manifest_location(path: Path, expected_path: Path) -> Path:
    manifest_path = Path(path)
    if manifest_path != expected_path or not manifest_path.is_absolute():
        raise ManifestValidationError("manifest path is invalid")
    try:
        parent_metadata = os.lstat(manifest_path.parent)
    except OSError as exc:
        raise ManifestValidationError("manifest parent is unavailable") from exc
    if (
        stat.S_ISLNK(parent_metadata.st_mode)
        or not stat.S_ISDIR(parent_metadata.st_mode)
        or stat.S_IMODE(parent_metadata.st_mode) != 0o700
    ):
        raise ManifestValidationError("manifest parent is unsafe")
    return manifest_path


def _read_manifest_payload(path: Path, *, expected_path: Path) -> bytes:
    """Read one bounded regular manifest through an already-fixed path."""

    manifest_path = _validate_manifest_location(path, expected_path)
    try:
        descriptor = os.open(manifest_path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise ManifestValidationError("manifest is unavailable") from exc
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or metadata.st_size > MAX_MANIFEST_BYTES
        ):
            raise ManifestValidationError("manifest file is unsafe")
        payload = bytearray()
        while len(payload) <= MAX_MANIFEST_BYTES:
            chunk = os.read(
                descriptor, min(8192, MAX_MANIFEST_BYTES + 1 - len(payload))
            )
            if not chunk:
                break
            payload.extend(chunk)
        if len(payload) > MAX_MANIFEST_BYTES:
            raise ManifestValidationError("manifest is oversized")
        return bytes(payload)
    finally:
        os.close(descriptor)


def read_manifest_payload() -> bytes:
    """Read only the contract-fixed readiness manifest path."""

    return _read_manifest_payload(
        READINESS_MANIFEST_PATH, expected_path=READINESS_MANIFEST_PATH
    )


def load_manifest(*, now: datetime | None = None) -> Mapping[str, Any]:
    """Load and validate the fixed manifest without exposing its contents."""

    return validate_manifest(parse_manifest(read_manifest_payload()), now=now)


def _blocked_outcome() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "blocked",
        "limitation_class": "readiness_manifest_invalid",
        "ready": False,
    }


def main(argv: list[str] | None = None, stdout: TextIO | None = None) -> int:
    """Emit a normalized outcome; arguments cannot alter the manifest path."""

    arguments = sys.argv[1:] if argv is None else argv
    output = sys.stdout if stdout is None else stdout
    if arguments:
        outcome = _blocked_outcome()
        exit_code = 2
    else:
        try:
            outcome = evaluate_manifest(read_manifest_payload())
        except ManifestValidationError:
            outcome = _blocked_outcome()
        exit_code = 0 if outcome["ready"] else 5
    output.write(json.dumps(outcome, ensure_ascii=False, sort_keys=True) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
