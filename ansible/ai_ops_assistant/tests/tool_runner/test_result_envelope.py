import contextlib
import importlib.util
import io
import json
import unittest
import uuid
from datetime import datetime, timezone
from importlib.machinery import SourceFileLoader
from pathlib import Path

RUNNER_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/aiops_tool_runner.py"
)
SPEC = importlib.util.spec_from_loader(
    "aiops_tool_runner_result_envelope",
    SourceFileLoader("aiops_tool_runner_result_envelope", str(RUNNER_PATH)),
)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class ResultEnvelopeTest(unittest.TestCase):
    def setUp(self):
        RUNNER._TEST_CLOCK = lambda: datetime(
            2030, 1, 2, 3, 4, 5, 678901, tzinfo=timezone.utc
        )
        RUNNER._TEST_UUID_FACTORY = lambda: uuid.UUID(
            "00000000-0000-4000-8000-000000000001"
        )

    def tearDown(self):
        RUNNER._TEST_CLOCK = None
        RUNNER._TEST_UUID_FACTORY = None

    def test_closed_envelope_has_all_fields_and_stable_context(self):
        envelope = RUNNER.build_result_envelope(
            "server_basic_info", "validation_error", {"unsafe": "value"}
        )

        self.assertEqual(set(envelope), RUNNER.RESULT_FIELDS)
        self.assertEqual(envelope["schema_version"], "1.0")
        self.assertEqual(envelope["timestamp"], "2030-01-02T03:04:05.678Z")
        self.assertEqual(
            envelope["correlation_id"], "00000000-0000-4000-8000-000000000001"
        )
        self.assertEqual(envelope["exit_code"], 3)
        self.assertEqual(envelope["stdout"], None)
        self.assertEqual(envelope["stderr"], None)
        self.assertEqual(envelope["error"]["class"], "validation_error")

    def test_each_status_uses_the_existing_exit_code(self):
        for status, exit_code in RUNNER.STATUS_EXIT_CODES.items():
            with self.subTest(status=status):
                envelope = RUNNER.build_result_envelope("unknown_tool", status)
                self.assertEqual(envelope["status"], status)
                self.assertEqual(envelope["exit_code"], exit_code)
                self.assertEqual(envelope["tool"], "unknown")
                self.assertEqual(envelope["data"], None)

    def test_valid_diagnostic_data_is_redacted_and_empty_shape_is_preserved(self):
        payload = {
            "schema_version": "1.0",
            "tool": "server_basic_info",
            "status": "ok",
            "sections": [
                {
                    "name": "server",
                    "status": "empty",
                    "data": {"password": "fixture-secret", "status": "ACTIVE"},
                    "error": None,
                    "truncated": False,
                }
            ],
            "error": None,
        }
        capture = RUNNER.CaptureResult(
            json.dumps(payload).encode("utf-8"), b"ignored-secret", False, False, 0, 12
        )

        envelope = RUNNER.build_result_envelope(
            "server_basic_info",
            "ok",
            {"server_identifier": "demo-server"},
            capture=capture,
        )

        section = envelope["data"]["sections"][0]
        self.assertEqual(section["status"], "empty")
        self.assertEqual(section["data"]["password"], "[REDACTED]")
        self.assertEqual(section["data"]["status"], "ACTIVE")
        self.assertIsNone(envelope["stdout"])
        self.assertIsNone(envelope["stderr"])

    def test_invalid_output_and_truncation_are_safe(self):
        capture = RUNNER.CaptureResult(b"{not-json", b"raw-secret", True, False, 1, 8)

        envelope = RUNNER.build_result_envelope(
            "server_basic_info",
            "error",
            {"server_identifier": "demo-server"},
            "diagnostic output is invalid",
            capture,
        )

        self.assertEqual(envelope["error"]["class"], "output_decode_error")
        self.assertIsNone(envelope["data"])
        self.assertTrue(envelope["truncated"])
        self.assertNotIn("raw-secret", RUNNER.serialize_result_envelope(envelope))

    def test_serialization_is_compact_sorted_and_single_line(self):
        envelope = RUNNER.build_result_envelope("project_resource_summary", "ok")

        serialized = RUNNER.serialize_result_envelope(envelope)

        self.assertEqual(serialized, RUNNER.serialize_result_envelope(envelope))
        self.assertTrue(serialized.endswith("\n"))
        self.assertEqual(serialized.count("\n"), 1)
        self.assertNotIn(": ", serialized)
        self.assertEqual(json.loads(serialized), envelope)

    def test_main_uses_the_final_envelope_for_denial(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = RUNNER.main(["shell"])

        envelope = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(set(envelope), RUNNER.RESULT_FIELDS)
        self.assertEqual(envelope["status"], "denied")
        self.assertEqual(envelope["tool"], "unknown")
        self.assertIsNone(envelope["data"])


if __name__ == "__main__":
    unittest.main()
