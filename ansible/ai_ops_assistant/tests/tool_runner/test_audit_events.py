import importlib.util
import json
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

RUNNER_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/aiops_tool_runner.py"
)
SPEC = importlib.util.spec_from_loader(
    "aiops_tool_runner_audit_events",
    SourceFileLoader("aiops_tool_runner_audit_events", str(RUNNER_PATH)),
)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class AuditEventTest(unittest.TestCase):
    def setUp(self):
        self.base = {
            "schema_version": "1.0",
            "tool": "server_basic_info",
            "status": "ok",
            "arguments": {"server_identifier": "demo-server"},
            "exit_code": 0,
            "data": {"password": "fixture-secret", "safe": "value"},
            "stdout": None,
            "stderr": None,
            "error": None,
            "duration_ms": 42,
            "truncated": False,
            "timestamp": "2030-01-02T03:04:05.678Z",
            "correlation_id": "00000000-0000-4000-8000-000000000001",
        }

    def test_closed_event_uses_fixed_actor_and_minimum_arguments(self):
        event = RUNNER.build_audit_event(self.base)

        self.assertEqual(set(event), RUNNER.AUDIT_FIELDS)
        self.assertEqual(event["schema_version"], "1.0")
        self.assertEqual(event["event_type"], "tool_request_completed")
        self.assertEqual(event["actor"], "local_cli")
        self.assertEqual(event["arguments"], {"server_identifier_present": True})
        self.assertEqual(event["reason"], None)
        self.assertNotIn("data", event)
        self.assertNotIn("password", RUNNER.serialize_audit_event(event))
        self.assertNotIn("fixture-secret", RUNNER.serialize_audit_event(event))

    def test_project_summary_event_omits_arguments(self):
        result = dict(self.base)
        result["tool"] = "project_resource_summary"
        result["arguments"] = {}

        event = RUNNER.build_audit_event(result)

        self.assertEqual(event["arguments"], {})

    def test_event_carries_status_context_and_truncation_for_each_status(self):
        for status, exit_code in RUNNER.STATUS_EXIT_CODES.items():
            with self.subTest(status=status):
                result = dict(self.base)
                result["status"] = status
                result["exit_code"] = exit_code
                result["truncated"] = status == "error"
                result["error"] = (
                    {"class": "execution_error", "message": "safe message"}
                    if status != "ok"
                    else None
                )
                event = RUNNER.build_audit_event(result)
                self.assertEqual(event["status"], status)
                self.assertEqual(event["exit_code"], exit_code)
                self.assertEqual(event["truncated"], status == "error")
                self.assertEqual(
                    event["reason"], None if status == "ok" else "execution_error"
                )

    def test_event_shares_result_timestamp_correlation_and_status(self):
        result = dict(self.base)
        result["status"] = "timeout"
        result["exit_code"] = 4
        result["error"] = {"class": "timeout", "message": "bounded message"}

        event = RUNNER.build_audit_event(result)

        self.assertEqual(event["timestamp"], result["timestamp"])
        self.assertEqual(event["correlation_id"], result["correlation_id"])
        self.assertEqual(event["status"], result["status"])

    def test_arbitrary_actor_and_invalid_result_are_rejected(self):
        with self.assertRaises(ValueError):
            RUNNER.build_audit_event(self.base, actor="operator-text")
        with self.assertRaises(ValueError):
            RUNNER.build_audit_event({"status": "ok"})

    def test_serialization_is_compact_single_line_and_bounded(self):
        event = RUNNER.build_audit_event(self.base)

        serialized = RUNNER.serialize_audit_event(event)

        self.assertEqual(serialized.count("\n"), 1)
        self.assertNotIn(": ", serialized)
        self.assertEqual(json.loads(serialized), event)
        self.assertLessEqual(
            len(serialized.encode("utf-8")), RUNNER.MAX_AUDIT_EVENT_BYTES
        )

    def test_oversized_event_is_rejected_before_persistence(self):
        event = RUNNER.build_audit_event(self.base)
        event["tool"] = "x" * RUNNER.MAX_AUDIT_EVENT_BYTES

        with self.assertRaises(ValueError):
            RUNNER.serialize_audit_event(event)


if __name__ == "__main__":
    unittest.main()
