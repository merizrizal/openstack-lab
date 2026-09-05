#!/usr/bin/env python3
"""Validate the approved MCP wheelhouse closure without network or installation."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import sys
import sysconfig
from datetime import datetime, timezone
from pathlib import Path
from email.parser import Parser
from zipfile import BadZipFile, ZipFile

from packaging.tags import sys_tags
from packaging.utils import canonicalize_name, parse_wheel_filename


class ValidationError(Exception):
    """Raised when an approved wheelhouse input is invalid."""


def fail(message: str) -> None:
    raise ValidationError(message)


def require_keys(value: object, expected: set[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != expected:
        fail(f"{label} schema mismatch")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_lock(path: Path) -> dict[str, tuple[str, set[str]]]:
    entries: dict[str, tuple[str, set[str]]] = {}
    current: tuple[str, str] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9_.-]*)==([^\\\s]+)", line)
        if match:
            name = canonicalize_name(match.group(1))
            if name in entries:
                fail(f"duplicate lock entry: {name}")
            current = (name, match.group(2))
            entries[name] = (match.group(2), set())
            continue
        hash_match = re.search(r"--hash=sha256:([a-f0-9]{64})", line)
        if hash_match and current:
            entries[current[0]][1].add(hash_match.group(1))
    if not entries:
        fail("lock contains no pinned requirements")
    if any(not hashes for _, hashes in entries.values()):
        fail("lock entry is missing sha256 hashes")
    return entries


def runtime_record(python_executable: Path) -> dict[str, str]:
    if Path(sys.executable).resolve() != python_executable.resolve():
        fail("validator interpreter does not match approved Python executable")
    implementation = platform.python_implementation()
    cache_tag = sys.implementation.cache_tag or ""
    if not cache_tag.startswith("cpython-"):
        fail("runtime is not CPython")
    runtime_abi = "cp" + cache_tag.split("-", 1)[1]
    try:
        pip_version = importlib.metadata.version("pip")
        pip_tools_version = importlib.metadata.version("pip-tools")
    except importlib.metadata.PackageNotFoundError as exc:
        fail(f"required build tool is missing: {exc.name}")
    return {
        "python_executable": str(python_executable.resolve()),
        "python_version": platform.python_version(),
        "implementation": implementation,
        "abi": runtime_abi,
        "architecture": platform.machine(),
        "sysconfig_platform": sysconfig.get_platform(),
        "glibc": platform.libc_ver()[1],
        "pip_version": pip_version,
        "pip_tools_version": pip_tools_version,
    }


def load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {label}: {exc}")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def validate(args: argparse.Namespace) -> None:
    manifest = load_json(Path(args.manifest), "manifest")
    attestation = load_json(Path(args.attestation), "builder attestation")

    require_keys(
        manifest,
        {"schema_version", "approval", "target", "generator", "artifacts"},
        "manifest",
    )
    if manifest["schema_version"] != 1:
        fail("unsupported manifest schema version")

    approval = require_keys(manifest["approval"], {"id", "expires_at_utc"}, "approval")
    if approval["id"] != args.approval_id or approval["expires_at_utc"] != args.approval_expires_at_utc:
        fail("manifest approval does not match the current run")
    try:
        expiry = datetime.strptime(approval["expires_at_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        fail("manifest approval expiry is not UTC ISO-8601")
    if expiry <= datetime.now(timezone.utc):
        fail("manifest approval is expired")

    target = require_keys(
        manifest["target"],
        {"python_version", "abi", "platform", "implementation", "architecture", "compatibility_tags"},
        "target",
    )
    expected_tags = json.loads(args.expected_tags_json)
    if not isinstance(expected_tags, list) or not expected_tags or any(not isinstance(tag, str) for tag in expected_tags):
        fail("approved compatibility tags are invalid")
    if not isinstance(target["compatibility_tags"], list) or not target["compatibility_tags"] or any(
        not isinstance(tag, str) for tag in target["compatibility_tags"]
    ):
        fail("manifest compatibility tags are invalid")
    expected_target = {
        "python_version": args.expected_python_version,
        "abi": args.expected_abi,
        "platform": args.expected_platform,
        "implementation": args.expected_implementation,
        "architecture": args.expected_architecture,
    }
    if any(target[key] != value for key, value in expected_target.items()):
        fail("manifest target does not match approved target")
    if sorted(target["compatibility_tags"]) != sorted(expected_tags):
        fail("manifest compatibility tags do not match approved tags")

    generator = require_keys(
        manifest["generator"],
        {
            "host",
            "image_identity",
            "environment_digest",
            "environment_fingerprint_sha256",
            "python_executable",
            "python_version",
            "implementation",
            "abi",
            "architecture",
            "sysconfig_platform",
            "glibc",
            "pip_version",
            "pip_tools_version",
        },
        "generator",
    )
    attestation = require_keys(
        attestation,
        {"host", "image_identity", "server_uuid", "environment_fingerprint_sha256", "captured_at_utc", "approval_id", "immutable"},
        "builder attestation",
    )
    required_attestation_strings = ("host", "image_identity", "server_uuid", "environment_fingerprint_sha256", "captured_at_utc", "approval_id")
    if any(not isinstance(attestation[key], str) or not attestation[key] for key in required_attestation_strings):
        fail("builder attestation contains an empty identity field")
    if attestation["immutable"] is not True or attestation["host"] != args.expected_host:
        fail("builder attestation is not immutable or is for the wrong host")
    if attestation["approval_id"] != args.approval_id:
        fail("builder attestation approval does not match the current run")
    if not isinstance(generator["image_identity"], str) or not generator["image_identity"]:
        fail("manifest generator image identity is missing")
    if generator["host"] != args.expected_host or generator["image_identity"] != attestation["image_identity"]:
        fail("manifest generator identity does not match builder attestation")
    if generator["environment_fingerprint_sha256"] != attestation["environment_fingerprint_sha256"]:
        fail("manifest environment fingerprint does not match builder attestation")

    runtime = runtime_record(Path(args.python_executable))
    for key, value in runtime.items():
        if generator[key] != value:
            fail(f"manifest generator field does not match builder runtime: {key}")
    environment_digest = hashlib.sha256(
        json.dumps(runtime, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if generator["environment_digest"] != f"sha256:{environment_digest}":
        fail("manifest environment digest does not match builder runtime")

    lock_entries = parse_lock(Path(args.lock))
    wheel_paths = sorted(Path(args.wheel_dir).glob("*.whl"))
    if not wheel_paths:
        fail("wheel directory is empty")

    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        fail("manifest artifacts must be a non-empty list")
    artifact_by_filename: dict[str, dict] = {}
    artifact_by_package: dict[str, dict] = {}
    for artifact in artifacts:
        item = require_keys(
            artifact,
            {"package", "version", "filename", "sha256", "compatibility_tags", "license_identifiers", "provenance_reference"},
            "artifact",
        )
        package = canonicalize_name(str(item["package"]))
        if item["filename"] in artifact_by_filename or package in artifact_by_package:
            fail("manifest contains duplicate artifact entries")
        if not isinstance(item["package"], str) or not isinstance(item["version"], str) or not isinstance(item["filename"], str):
            fail("manifest artifact identity fields are invalid")
        if not re.fullmatch(r"[a-f0-9]{64}", str(item["sha256"])):
            fail("manifest artifact hash is invalid")
        if not isinstance(item["compatibility_tags"], list) or not item["compatibility_tags"] or any(
            not isinstance(tag, str) for tag in item["compatibility_tags"]
        ):
            fail("manifest artifact compatibility tags are invalid")
        if not isinstance(item["license_identifiers"], list) or not item["license_identifiers"]:
            fail("manifest artifact license identifiers are missing")
        if not isinstance(item["provenance_reference"], str) or not item["provenance_reference"]:
            fail("manifest artifact provenance is missing")
        artifact_by_filename[item["filename"]] = item
        artifact_by_package[package] = item

    wheel_names = {path.name for path in wheel_paths}
    if set(artifact_by_filename) != wheel_names:
        fail("manifest wheel inventory does not match selected wheels")
    if set(artifact_by_package) != set(lock_entries):
        fail("manifest package inventory does not match lock")

    runtime_tags = {str(tag) for tag in sys_tags()}
    for wheel_path in wheel_paths:
        item = artifact_by_filename[wheel_path.name]
        try:
            wheel_name, wheel_version, _, wheel_tags = parse_wheel_filename(wheel_path.name)
            with ZipFile(wheel_path) as archive:
                metadata_members = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
                if len(metadata_members) != 1:
                    fail(f"wheel must contain exactly one METADATA file: {wheel_path.name}")
                metadata = Parser().parsestr(archive.read(metadata_members[0]).decode("utf-8"))
        except (ValueError, BadZipFile, KeyError, UnicodeDecodeError) as exc:
            fail(f"invalid wheel metadata: {wheel_path.name}: {exc}")
        package = canonicalize_name(str(wheel_name))
        if package != canonicalize_name(str(item["package"])) or str(wheel_version) != str(item["version"]):
            fail(f"wheel filename does not match manifest: {wheel_path.name}")
        metadata_name = metadata.get("Name")
        metadata_version = metadata.get("Version")
        if not isinstance(metadata_name, str) or not isinstance(metadata_version, str):
            fail(f"wheel METADATA identity is incomplete: {wheel_path.name}")
        if canonicalize_name(metadata_name) != package or metadata_version != str(wheel_version):
            fail(f"wheel METADATA does not match filename: {wheel_path.name}")
        if package not in lock_entries or lock_entries[package][0] != str(wheel_version):
            fail(f"wheel version does not match lock: {wheel_path.name}")
        actual_tags = {str(tag) for tag in wheel_tags}
        manifest_tags = set(item["compatibility_tags"])
        if actual_tags != manifest_tags:
            fail(f"wheel compatibility tags do not match manifest: {wheel_path.name}")
        if actual_tags - set(target["compatibility_tags"]):
            fail(f"wheel has unapproved compatibility tags: {wheel_path.name}")
        if not actual_tags <= runtime_tags:
            fail(f"wheel tags are unsupported by builder runtime: {wheel_path.name}")
        digest = sha256_file(wheel_path)
        if digest != item["sha256"] or digest not in lock_entries[package][1]:
            fail(f"wheel hash is not approved: {wheel_path.name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--wheel-dir", required=True)
    parser.add_argument("--attestation", required=True)
    parser.add_argument("--approval-id", required=True)
    parser.add_argument("--approval-expires-at-utc", required=True)
    parser.add_argument("--python-executable", required=True)
    parser.add_argument("--expected-host", required=True)
    parser.add_argument("--expected-python-version", required=True)
    parser.add_argument("--expected-abi", required=True)
    parser.add_argument("--expected-platform", required=True)
    parser.add_argument("--expected-implementation", required=True)
    parser.add_argument("--expected-architecture", required=True)
    parser.add_argument("--expected-tags-json", required=True)
    args = parser.parse_args()
    try:
        validate(args)
    except (OSError, ValidationError, json.JSONDecodeError) as exc:
        print(f"ERR_MCP_WHEELHOUSE_VALIDATION: {exc}", file=sys.stderr)
        return 1
    print("MCP wheelhouse input validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
