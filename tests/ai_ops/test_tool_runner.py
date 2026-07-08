import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = (
    REPO_ROOT
    / "ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py"
)


def load_runner_module():
    spec = importlib.util.spec_from_file_location("aiops_tool_runner", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestToolRunnerStub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_runner_module()

    def write_registry(self, tools):
        tempdir = tempfile.TemporaryDirectory()
        registry_path = Path(tempdir.name) / "tool_registry.json"
        registry_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "registry_name": "test-registry",
                    "tools": tools,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        self.addCleanup(tempdir.cleanup)
        return registry_path

    def invoke_main(self, argv):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = self.runner.main(argv)
        payload = json.loads(stdout.getvalue())
        return exit_code, payload

    def test_build_result_envelope_has_required_fields(self):
        envelope = self.runner.build_result_envelope(
            "server_basic_info",
            "denied",
            arguments={"server_identifier": "vm01"},
            stderr="requested tool is not present in the reviewed allowlist",
            request_id="req-123",
        )

        self.assertEqual(envelope["tool"], "server_basic_info")
        self.assertEqual(envelope["status"], "denied")
        self.assertEqual(envelope["arguments"], {"server_identifier": "vm01"})
        self.assertIsNone(envelope["exit_code"])
        self.assertEqual(envelope["stdout"], "")
        self.assertEqual(
            envelope["stderr"],
            "requested tool is not present in the reviewed allowlist",
        )
        self.assertIn("duration_ms", envelope)
        self.assertIn("timestamp", envelope)
        self.assertEqual(envelope["request_id"], "req-123")
        self.assertFalse(envelope["truncated"])

    def test_main_denies_unknown_tool(self):
        registry_path = self.write_registry(
            [
                {
                    "name": "project_resource_summary",
                    "available": True,
                    "arguments": [],
                }
            ]
        )

        exit_code, payload = self.invoke_main(
            ["not_registered", "--registry", str(registry_path)]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["denied"])
        self.assertEqual(payload["tool"], "not_registered")
        self.assertEqual(payload["status"], "denied")
        self.assertEqual(payload["arguments"], {})
        self.assertIn("allowlist", payload["stderr"])

    def test_main_reports_unavailable_tool(self):
        registry_path = self.write_registry(
            [
                {
                    "name": "neutron_agent_health",
                    "available": False,
                    "unavailable_reason": "operator-reader profile deferred",
                    "arguments": [],
                }
            ]
        )

        exit_code, payload = self.invoke_main(
            ["neutron_agent_health", "--registry", str(registry_path)]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["unavailable"])
        self.assertEqual(payload["status"], "unavailable")
        self.assertEqual(payload["stderr"], "operator-reader profile deferred")

    def test_main_returns_explicit_stub_error_for_available_tool(self):
        registry_path = self.write_registry(
            [
                {
                    "name": "project_resource_summary",
                    "available": True,
                    "arguments": [],
                }
            ]
        )

        exit_code, payload = self.invoke_main(
            [
                "project_resource_summary",
                "--registry",
                str(registry_path),
                "--arg",
                "scope=project",
            ]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["error"])
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["arguments"], {"scope": "project"})
        self.assertIn("not implemented", payload["stderr"])


if __name__ == "__main__":
    unittest.main()
