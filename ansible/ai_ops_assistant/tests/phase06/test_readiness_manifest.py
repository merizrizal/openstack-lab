import copy
import importlib.util
import io
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from importlib.machinery import SourceFileLoader
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/readiness_manifest.py"
)
SPEC = importlib.util.spec_from_loader(
    "readiness_manifest", SourceFileLoader("readiness_manifest", str(SCRIPT_PATH))
)
MANIFEST = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MANIFEST)

NOW = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)


def reference(name):
    return f"2026-0004-{name}"


def valid_manifest():
    return {
        "schema_version": "1.0",
        "run_id": "2026-0004",
        "authorization_reference": "phase06-live-acceptance-2026-0004",
        "authorization_class": "phase06-restricted-diagnostics-live-acceptance",
        "source_revision": reference("source-r1"),
        "environment_label": "local",
        "evidence_owner": "OpenStack platform operations / lab administrator",
        "scope_approvals": [
            {
                "scope": scope,
                "status": "approved",
                "owner_label": "OpenStack platform operations / lab administrator",
                "authorization_reference": "phase06-live-acceptance-2026-0004",
                "outcome_evidence_reference": reference(f"evidence-{scope}"),
            }
            for scope in sorted(MANIFEST.REQUIRED_SCOPES)
        ],
        "protected_input_references": {
            name: reference(f"{name}-r1")
            for name in MANIFEST.PROTECTED_REFERENCE_FIELDS
        },
        "integrity_checks": {
            name: {
                "status": "passed",
                "outcome_evidence_reference": reference(f"integrity-{name}"),
            }
            for name in MANIFEST.INTEGRITY_CHECK_FIELDS
        },
        "status": "ready",
        "issued_at": "2026-08-01T00:00:00Z",
        "expires_at": "2026-08-01T23:59:59Z",
    }


class ReadinessManifestTest(unittest.TestCase):
    def test_ready_manifest_has_only_normalized_outcome(self):
        payload = json.dumps(valid_manifest())

        validated = MANIFEST.validate_manifest(
            MANIFEST.parse_manifest(payload), now=NOW
        )
        outcome = MANIFEST.evaluate_manifest(payload, now=NOW)

        self.assertEqual(validated["status"], "ready")
        self.assertEqual(
            outcome,
            {
                "schema_version": "1.0",
                "status": "ready",
                "limitation_class": "none",
                "ready": True,
            },
        )
        self.assertNotIn("address", json.dumps(outcome))
        self.assertNotIn("credential", json.dumps(outcome))

    def test_duplicate_unknown_and_unsafe_reference_are_blocked(self):
        duplicate = b'{"schema_version":"1.0","schema_version":"1.0"}'
        unknown = {**valid_manifest(), "unexpected": "value"}
        unsafe_reference = valid_manifest()
        unsafe_reference["protected_input_references"][
            "host_policy_revision"
        ] = "/opt/openstack-ai-ops-assistant/host-policy"

        with self.assertRaises(MANIFEST.ManifestValidationError):
            MANIFEST.parse_manifest(duplicate)
        for document in (unknown, unsafe_reference):
            with self.subTest(document=document is unsafe_reference):
                with self.assertRaises(MANIFEST.ManifestValidationError):
                    MANIFEST.validate_manifest(document, now=NOW)

    def test_stale_and_non_ready_states_fail_closed(self):
        stale = valid_manifest()
        stale["expires_at"] = "2026-08-01T11:59:59Z"
        invalid_ready = valid_manifest()
        invalid_ready["scope_approvals"][0]["status"] = "pending"
        blocked = copy.deepcopy(invalid_ready)
        blocked["status"] = "blocked"

        for document in (stale, invalid_ready):
            with self.subTest(document=document is invalid_ready):
                with self.assertRaises(MANIFEST.ManifestValidationError):
                    MANIFEST.validate_manifest(document, now=NOW)
        self.assertEqual(
            MANIFEST.evaluate_manifest(json.dumps(invalid_ready), now=NOW)["status"],
            "blocked",
        )
        self.assertEqual(
            MANIFEST.evaluate_manifest(json.dumps(blocked), now=NOW),
            {
                "schema_version": "1.0",
                "status": "blocked",
                "limitation_class": "readiness_not_ready",
                "ready": False,
            },
        )

    def test_fixed_path_loader_checks_mode_size_and_symlink(self):
        payload = json.dumps(valid_manifest()).encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            manifest_path = parent / "manifest.json"
            manifest_path.write_bytes(payload)
            os.chmod(parent, 0o700)
            os.chmod(manifest_path, 0o600)

            self.assertEqual(
                MANIFEST._read_manifest_payload(
                    manifest_path, expected_path=manifest_path
                ),
                payload,
            )
            with self.assertRaises(MANIFEST.ManifestValidationError):
                MANIFEST._read_manifest_payload(
                    manifest_path, expected_path=parent / "other.json"
                )

            os.chmod(manifest_path, 0o640)
            with self.assertRaises(MANIFEST.ManifestValidationError):
                MANIFEST._read_manifest_payload(
                    manifest_path, expected_path=manifest_path
                )

            manifest_path.write_bytes(b"x" * (MANIFEST.MAX_MANIFEST_BYTES + 1))
            os.chmod(manifest_path, 0o600)
            with self.assertRaises(MANIFEST.ManifestValidationError):
                MANIFEST._read_manifest_payload(
                    manifest_path, expected_path=manifest_path
                )

            source_path = parent / "source.json"
            source_path.write_bytes(payload)
            os.chmod(source_path, 0o600)
            manifest_path.unlink()
            manifest_path.symlink_to(source_path)
            with self.assertRaises(MANIFEST.ManifestValidationError):
                MANIFEST._read_manifest_payload(
                    manifest_path, expected_path=manifest_path
                )

    def test_cli_rejects_arguments_without_reading_the_fixed_path(self):
        output = io.StringIO()

        exit_code = MANIFEST.main(["unexpected"], stdout=output)

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            json.loads(output.getvalue()),
            {
                "schema_version": "1.0",
                "status": "blocked",
                "limitation_class": "readiness_manifest_invalid",
                "ready": False,
            },
        )

    def test_scope_integrity_and_run_binding_are_closed(self):
        duplicate_scope = valid_manifest()
        duplicate_scope["scope_approvals"][1]["scope"] = duplicate_scope[
            "scope_approvals"
        ][0]["scope"]
        incomplete_integrity = valid_manifest()
        incomplete_integrity["integrity_checks"].pop("host_policy")
        wrong_run_reference = valid_manifest()
        wrong_run_reference["source_revision"] = "other-run-source-r1"

        for document in (duplicate_scope, incomplete_integrity, wrong_run_reference):
            with self.subTest(document=document):
                with self.assertRaises(MANIFEST.ManifestValidationError):
                    MANIFEST.validate_manifest(document, now=NOW)


if __name__ == "__main__":
    unittest.main()
