import contextlib
import copy
import importlib.util
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

RUNNER_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/aiops_tool_runner.py"
)
SPEC = importlib.util.spec_from_loader(
    "aiops_tool_runner_host_observer",
    SourceFileLoader("aiops_tool_runner_host_observer", str(RUNNER_PATH)),
)
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RUNNER)


class HostObserverRunnerTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.audit_directory = self.root / "audit"
        self.audit_directory.mkdir()
        os.chmod(self.audit_directory, RUNNER.AUDIT_DIRECTORY_MODE)
        owner = self.audit_directory.stat()
        RUNNER._TEST_AUDIT_DIRECTORY = self.audit_directory
        RUNNER._TEST_AUDIT_OWNER = (owner.st_uid, owner.st_gid)
        self.record_path = self.root / "record.json"
        self.fixture = self.root / "host_observer_fixture.py"
        payload = {
            "schema_version": "1.0",
            "tool": "recent_nova_errors",
            "status": "unavailable",
            "sections": [],
            "error": {
                "class": "approved_optional_capability_absent",
                "message": "Approved optional capability is unavailable.",
            },
        }
        self.fixture.write_text(
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            "from pathlib import Path\n"
            f"Path({str(self.record_path)!r}).write_text(json.dumps({{'argv': sys.argv, 'stdin': sys.stdin.buffer.read().decode('utf-8'), 'environment': dict(os.environ)}}), encoding='utf-8')\n"
            f"print({json.dumps(payload)!r})\n",
            encoding="utf-8",
        )
        self.fixture.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        RUNNER._TEST_EXECUTION_TARGET = self.fixture
        RUNNER._TEST_WORKING_DIRECTORY = self.root

    def tearDown(self):
        RUNNER._TEST_EXECUTION_TARGET = None
        RUNNER._TEST_WORKING_DIRECTORY = None
        RUNNER._TEST_AUDIT_DIRECTORY = None
        RUNNER._TEST_AUDIT_OWNER = None
        self.temporary.cleanup()

    def test_registry_has_exact_seven_tools_and_separate_host_authority(self):
        registry = RUNNER.load_registry()
        self.assertEqual(len(registry["tools"]), 7)
        self.assertEqual(
            {tool["name"] for tool in registry["tools"]}, RUNNER.TOOL_NAMES
        )
        for tool in registry["tools"]:
            self.assertEqual(
                tool["authority_class"], RUNNER.TOOL_AUTHORITY_CLASSES[tool["name"]]
            )
        for tool_name in RUNNER.HOST_TOOL_NAMES:
            tool = next(tool for tool in registry["tools"] if tool["name"] == tool_name)
            self.assertIsNone(tool["credential_profile"])
            self.assertEqual(
                tool["implementation_target"], str(RUNNER.HOST_OBSERVER_TARGET)
            )
            self.assertEqual(tool["parameters"][0]["name"], "host_label")

    def test_host_authority_environment_has_no_openstack_or_parent_state(self):
        registry = RUNNER.load_registry()
        tool = next(
            tool for tool in registry["tools"] if tool["name"] == "recent_nova_errors"
        )
        os.environ["OS_PASSWORD_CANARY"] = "must-not-reach-host-observer"
        try:
            environment = RUNNER.build_child_environment(tool)
        finally:
            os.environ.pop("OS_PASSWORD_CANARY", None)
        self.assertEqual(environment, RUNNER.HOST_OBSERVER_ENVIRONMENT)
        self.assertFalse(any(key.startswith("OS_") for key in environment))
        self.assertNotIn("OS_PASSWORD_CANARY", environment)
        with self.assertRaises(RUNNER.TargetIntegrityError):
            RUNNER.resolve_tool_profile(tool)

    def test_host_request_is_closed_and_uses_stdin_not_argv(self):
        registry = RUNNER.load_registry()
        tool = next(
            tool for tool in registry["tools"] if tool["name"] == "recent_nova_errors"
        )
        validated_tool, values = RUNNER.validate_request(
            registry,
            "recent_nova_errors",
            {"host_label": "controller-a"},
        )
        self.assertIs(validated_tool, tool)
        self.assertEqual(
            values,
            {
                "host_label": "controller-a",
                "window_class": "30m",
                "line_limit_class": "medium",
            },
        )
        self.assertEqual(RUNNER.build_command_argv(tool, values), [str(self.fixture)])
        request = json.loads(RUNNER.build_host_observer_request(tool, values))
        self.assertEqual(request["source_class"], "nova_error_events")
        self.assertNotIn("logical_selector", request)

        for declarations in (
            {"host_label": "controller.a"},
            {"host_label": "controller-a", "window_class": "default"},
            {"host_label": "controller-a", "line_limit_class": "huge"},
            {"host_label": "controller-a", "source_class": "nova_error_events"},
        ):
            with self.subTest(declarations=declarations):
                with self.assertRaises(RUNNER.RequestValidationError):
                    RUNNER.validate_request(
                        registry, "recent_nova_errors", declarations
                    )

    def test_host_execution_receives_only_bounded_stdin_and_unavailable_result(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = RUNNER.main(
                ["recent_nova_errors", "--arg", "host_label=controller-a"]
            )
        result = json.loads(output.getvalue())
        record = json.loads(self.record_path.read_text(encoding="utf-8"))
        request = json.loads(record["stdin"])
        self.assertEqual(exit_code, RUNNER.STATUS_EXIT_CODES["unavailable"])
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(request["host_label"], "controller-a")
        self.assertEqual(request["source_class"], "nova_error_events")
        self.assertEqual(record["argv"], [str(self.fixture)])
        self.assertFalse(any(key.startswith("OS_") for key in record["environment"]))
        self.assertEqual(
            result["arguments"],
            {
                "host_label": "controller-a",
                "window_class": "30m",
                "line_limit_class": "medium",
            },
        )

    def test_cross_authority_tampering_fails_before_target_validation(self):
        registry = RUNNER.load_registry()
        tool = next(
            tool for tool in registry["tools"] if tool["name"] == "recent_nova_errors"
        )
        tampered = copy.deepcopy(tool)
        tampered["authority_class"] = "openstack-project-reader"
        with self.assertRaises(RUNNER.TargetIntegrityError):
            RUNNER.build_child_environment(tampered)
        tampered = copy.deepcopy(tool)
        tampered["credential_profile"] = RUNNER.PROJECT_READER_PROFILE
        with self.assertRaises(RUNNER.TargetIntegrityError):
            RUNNER.build_child_environment(tampered)


if __name__ == "__main__":
    unittest.main()
