import contextlib
import importlib.util
import io
import json
import os
import pwd
import grp
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

HELPER_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/audit_inspector.py"
)
SPEC = importlib.util.spec_from_loader(
    "aiops_audit_inspector",
    SourceFileLoader("aiops_audit_inspector", str(HELPER_PATH)),
)
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


class BoundedAuditInspectorTest(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp())
        self.directory.chmod(0o700)
        self.audit_path = self.directory / "tool-runner.jsonl"
        self.audit_path.touch(mode=0o600)
        self.audit_path.chmod(0o600)
        self.original = (
            HELPER.AUDIT_DIRECTORY,
            HELPER.AUDIT_PATH,
            HELPER.AUDIT_OWNER,
            HELPER.AUDIT_GROUP,
        )
        HELPER.AUDIT_DIRECTORY = self.directory
        HELPER.AUDIT_PATH = self.audit_path
        HELPER.AUDIT_OWNER = pwd.getpwuid(os.getuid()).pw_name
        HELPER.AUDIT_GROUP = grp.getgrgid(os.getgid()).gr_name

    def tearDown(self):
        (
            HELPER.AUDIT_DIRECTORY,
            HELPER.AUDIT_PATH,
            HELPER.AUDIT_OWNER,
            HELPER.AUDIT_GROUP,
        ) = self.original
        self.audit_path.unlink(missing_ok=True)
        self.directory.rmdir()

    def event(self, tool, correlation_id, exit_code=0):
        return {
            "schema_version": "1.0",
            "timestamp": "2030-01-02T03:04:05.678Z",
            "event_type": "tool_request_completed",
            "actor": "local_cli",
            "tool": tool,
            "arguments": (
                {"server_identifier_present": True}
                if tool != "project_resource_summary"
                else {}
            ),
            "status": "ok",
            "duration_ms": 42,
            "correlation_id": correlation_id,
            "reason": None,
            "exit_code": exit_code,
            "truncated": False,
        }

    def test_reads_only_matching_events_and_returns_normalized_fields(self):
        correlations = [
            "00000000-0000-4000-8000-000000000001",
            "00000000-0000-4000-8000-000000000002",
            "00000000-0000-4000-8000-000000000003",
        ]
        events = [
            self.event("project_resource_summary", correlations[0]),
            self.event("server_basic_info", correlations[1]),
            self.event("server_network_info", correlations[2]),
        ]
        self.audit_path.write_text(
            "\n".join(json.dumps(event) for event in events) + "\n"
        )
        result = HELPER.inspect(0, correlations)

        self.assertEqual(
            [event["correlation_id"] for event in result["events"]], correlations
        )
        self.assertNotIn("event_type", result["events"][0])
        self.assertNotIn("actor", result["events"][0])

    def test_main_emits_normalized_failure_without_raw_audit_data(self):
        output = io.StringIO()
        correlations = [
            "00000000-0000-4000-8000-000000000001",
            "00000000-0000-4000-8000-000000000002",
            "00000000-0000-4000-8000-000000000003",
        ]

        with contextlib.redirect_stdout(output):
            exit_code = HELPER.main(["--offset", "0", *correlations])

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["error"], {"class": "audit_events_incomplete"})
        self.assertEqual(payload["events"], [])
        self.assertNotIn("00000000-0000-4000-8000-000000000001", output.getvalue())

    def test_failure_classes_are_normalized_without_detail(self):
        cases = {
            "audit event fields are invalid": "audit_event_fields_invalid",
            "audit schema is invalid": "audit_schema_invalid",
            "audit identity is invalid": "audit_identity_invalid",
            "audit duration is invalid": "audit_duration_invalid",
            "audit event is not valid JSON": "audit_event_json_invalid",
        }

        for message, expected in cases.items():
            with self.subTest(message=message):
                self.assertEqual(HELPER.failure_class(message), expected)

    def test_rejects_unbounded_appended_region(self):
        self.audit_path.write_bytes(b"x" * (HELPER.MAX_SCAN_BYTES + 1))

        with self.assertRaises(ValueError):
            HELPER.inspect(
                0,
                [
                    "00000000-0000-4000-8000-000000000001",
                    "00000000-0000-4000-8000-000000000002",
                    "00000000-0000-4000-8000-000000000003",
                ],
            )

    def test_rejects_duplicate_matching_correlation(self):
        event = self.event(
            "project_resource_summary", "00000000-0000-4000-8000-000000000001"
        )
        self.audit_path.write_text(
            "\n".join(json.dumps(event) for _ in range(2)) + "\n"
        )

        with self.assertRaises(ValueError):
            HELPER.inspect(
                0,
                [
                    "00000000-0000-4000-8000-000000000001",
                    "00000000-0000-4000-8000-000000000002",
                    "00000000-0000-4000-8000-000000000003",
                ],
            )


if __name__ == "__main__":
    unittest.main()
