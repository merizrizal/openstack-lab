import importlib.util
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

RUNNER_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/aiops_tool_runner.py"
)
SPEC = importlib.util.spec_from_loader(
    "aiops_tool_runner_redaction",
    SourceFileLoader("aiops_tool_runner_redaction", str(RUNNER_PATH)),
)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class ResultRedactionTest(unittest.TestCase):
    def test_nested_secret_keys_are_replaced_and_safe_values_preserved(self):
        result = RUNNER.redact_value(
            {
                "name": "safe",
                "nested": [
                    {"Password": "secret-value"},
                    {"api_key": "another-secret"},
                    {"status": "ACTIVE"},
                ],
            }
        )

        self.assertTrue(result.replaced)
        self.assertEqual(result.value["name"], "safe")
        self.assertEqual(result.value["nested"][0]["Password"], "[REDACTED]")
        self.assertEqual(result.value["nested"][1]["api_key"], "[REDACTED]")
        self.assertEqual(result.value["nested"][2]["status"], "ACTIVE")

    def test_text_forms_redact_assignments_bearer_tokens_and_private_keys(self):
        text = (
            "password=secret Authorization: Bearer abc.def token: 'value' "
            "-----BEGIN PRIVATE KEY-----secret-----END PRIVATE KEY-----"
        )

        result = RUNNER.sanitize_text(text)

        self.assertTrue(result.replaced)
        self.assertNotIn("secret", result.value)
        self.assertNotIn("abc.def", result.value)
        self.assertNotIn("BEGIN PRIVATE KEY", result.value)
        self.assertGreaterEqual(result.value.count("[REDACTED]"), 2)

    def test_public_text_is_bounded_by_utf8_bytes(self):
        result = RUNNER.sanitize_text("é" * 20, maximum_bytes=7)

        self.assertTrue(result.truncated)
        self.assertLessEqual(len(result.value.encode("utf-8")), 7)
        result.value.encode("utf-8").decode("utf-8")

    def test_depth_and_work_limits_fail_closed(self):
        nested = "leaf"
        for _ in range(33):
            nested = {"next": nested}

        with self.assertRaises(RUNNER.RedactionError):
            RUNNER.redact_value(nested)
        with self.assertRaises(RUNNER.RedactionError):
            RUNNER.redact_value(
                ["one", "two", "three"],
                RUNNER.RedactionPolicy(maximum_values=2),
            )

    def test_unsupported_values_fail_closed(self):
        with self.assertRaises(RUNNER.RedactionError):
            RUNNER.redact_value({"payload": b"not-json"})

    def test_argument_audiences_apply_minimum_disclosure(self):
        arguments = {"server_identifier": "fake-server", "safe": "value"}

        result = RUNNER.sanitize_arguments("server_basic_info", arguments)
        audit = RUNNER.sanitize_arguments("server_basic_info", arguments, "audit")

        self.assertEqual(result, arguments)
        self.assertEqual(audit, {"server_identifier_present": True})

    def test_invalid_argument_audience_fails_closed(self):
        with self.assertRaises(RUNNER.RedactionError):
            RUNNER.sanitize_arguments("server_basic_info", {}, "unknown")


if __name__ == "__main__":
    unittest.main()
