import contextlib
import copy
import importlib.util
import io
import json
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

RUNNER_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/aiops_tool_runner.py"
)
SPEC = importlib.util.spec_from_loader(
    "aiops_tool_runner_integration_gate",
    SourceFileLoader("aiops_tool_runner_integration_gate", str(RUNNER_PATH)),
)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)
REGISTRY_PATH = RUNNER_PATH.with_name("tool_registry.json")


class StepsOneToFourIntegrationGateTest(unittest.TestCase):
    def write_registry(self, directory, content):
        path = Path(directory) / "tool_registry.json"
        path.write_text(content, encoding="utf-8")
        return path

    def test_registry_corruption_fails_closed_before_request_processing(self):
        valid = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        corruptions = {
            "duplicate_root_key": REGISTRY_PATH.read_text(encoding="utf-8").replace(
                '"schema_version": 1,',
                '"schema_version": 1, "schema_version": 1,',
                1,
            ),
            "unknown_root_field": json.dumps({**valid, "unexpected": True}),
            "historical_target": json.dumps(
                {
                    **valid,
                    "tools": [
                        {
                            **valid["tools"][0],
                            "implementation_target": "/opt/openstack-ai-ops/scripts/approved/project_resource_summary.sh",
                        },
                        *valid["tools"][1:],
                    ],
                }
            ),
            "historical_profile": json.dumps(
                {
                    **valid,
                    "defaults": {
                        **valid["defaults"],
                        "credential_profile": "operator-reader",
                    },
                }
            ),
            "extra_capability": json.dumps(
                {
                    **valid,
                    "tools": [*valid["tools"], copy.deepcopy(valid["tools"][0])],
                }
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            for name, content in corruptions.items():
                with self.subTest(name=name):
                    path = self.write_registry(directory, content)
                    with self.assertRaises(RUNNER.RegistryError):
                        RUNNER.load_registry(path)

    def test_invalid_default_registry_returns_nonzero_before_request_validation(self):
        original_default_registry_path = RUNNER.default_registry_path
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = self.write_registry(
                    directory,
                    '{"schema_version": 1, "schema_version": 1}',
                )
                RUNNER.default_registry_path = lambda: path
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    exit_code = RUNNER.main(["shell"])
        finally:
            RUNNER.default_registry_path = original_default_registry_path

        self.assertEqual(exit_code, RUNNER.STATUS_EXIT_CODES["error"])
        envelope = json.loads(output.getvalue())
        self.assertEqual(set(envelope), RUNNER.RESULT_FIELDS)
        self.assertEqual(envelope["status"], "error")
        self.assertEqual(envelope["tool"], "unknown")
        self.assertEqual(envelope["error"]["class"], "registry_error")
        self.assertIsNone(envelope["data"])


if __name__ == "__main__":
    unittest.main()
