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
from unittest import mock

RUNNER_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/aiops_tool_runner.py"
)
SPEC = importlib.util.spec_from_loader(
    "aiops_tool_runner_profile_isolation",
    SourceFileLoader("aiops_tool_runner_profile_isolation", str(RUNNER_PATH)),
)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class ProfileIsolationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.audit_directory = self.root / "audit"
        self.audit_directory.mkdir()
        os.chmod(self.audit_directory, RUNNER.AUDIT_DIRECTORY_MODE)
        owner = self.audit_directory.stat()
        RUNNER._TEST_AUDIT_DIRECTORY = self.audit_directory
        RUNNER._TEST_AUDIT_OWNER = (owner.st_uid, owner.st_gid)
        self.environment_log = self.root / "environment.json"
        self.fixture = self.root / "operator_fixture.py"
        payload = {
            "schema_version": "1.0",
            "tool": "neutron_agent_health",
            "status": "unavailable",
            "sections": [],
            "error": {
                "class": "profile_missing_or_revoked",
                "message": "read unavailable",
            },
        }
        self.fixture.write_text(
            f"#!{sys.executable}\n"
            "import json, os\n"
            f"from pathlib import Path\nPath({str(self.environment_log)!r}).write_text("
            "json.dumps(dict(os.environ)), encoding='utf-8')\n"
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

    def run_request(self, argv):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = RUNNER.main(argv)
        return exit_code, json.loads(output.getvalue())

    def test_registry_has_exact_four_tools_and_closed_profile_mapping(self):
        registry = RUNNER.load_registry()
        self.assertEqual(
            {tool["name"] for tool in registry["tools"]}, RUNNER.TOOL_NAMES
        )
        self.assertEqual(
            {tool["name"]: tool["credential_profile"] for tool in registry["tools"]},
            RUNNER.TOOL_PROFILES,
        )
        neutron = next(
            tool for tool in registry["tools"] if tool["name"] == "neutron_agent_health"
        )
        self.assertEqual(neutron["parameters"], [])
        self.assertEqual(
            neutron["implementation_target"],
            str(RUNNER.TOOL_TARGETS[neutron["name"]]),
        )
        self.assertEqual(neutron["risk_class"], "higher_visibility_operator_scope")

    def test_profiles_have_distinct_fixed_environments_without_fallback(self):
        registry = RUNNER.load_registry()
        project = next(
            tool for tool in registry["tools"] if tool["name"] == "project_resource_summary"
        )
        neutron = next(
            tool for tool in registry["tools"] if tool["name"] == "neutron_agent_health"
        )
        project_environment = RUNNER.build_child_environment(project)
        operator_environment = RUNNER.build_child_environment(neutron)

        self.assertEqual(project_environment["OS_CLOUD"], RUNNER.PROJECT_READER_PROFILE)
        self.assertEqual(operator_environment["OS_CLOUD"], RUNNER.OPERATOR_READER_PROFILE)
        self.assertNotEqual(
            project_environment["OS_CLIENT_CONFIG_FILE"],
            operator_environment["OS_CLIENT_CONFIG_FILE"],
        )
        self.assertNotIn("OS_PASSWORD", operator_environment)
        self.assertNotIn("OPENSTACK_PASSWORD", operator_environment)

        tampered = copy.deepcopy(neutron)
        tampered["credential_profile"] = RUNNER.PROJECT_READER_PROFILE
        with self.assertRaises(RUNNER.TargetIntegrityError):
            RUNNER.resolve_tool_profile(tampered)
        with mock.patch.object(RUNNER, "validate_runtime_target") as target:
            outcome = RUNNER.execute_fixed_diagnostic(tampered, {})
        target.assert_not_called()
        self.assertEqual(outcome, ("error", "approved implementation is unsafe", None))

    def test_operator_tool_maps_unavailable_profile_to_result_and_audit(self):
        exit_code, outcome = self.run_request(["neutron_agent_health"])
        environment = json.loads(self.environment_log.read_text(encoding="utf-8"))
        audit_lines = self.audit_directory.joinpath("tool-runner.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()

        self.assertEqual(exit_code, RUNNER.STATUS_EXIT_CODES["unavailable"])
        self.assertEqual(outcome["tool"], "neutron_agent_health")
        self.assertEqual(outcome["status"], "unavailable")
        self.assertEqual(environment["OS_CLOUD"], RUNNER.OPERATOR_READER_PROFILE)
        self.assertEqual(
            environment["OS_CLIENT_CONFIG_FILE"], str(RUNNER.OPERATOR_READER_CONFIG)
        )
        self.assertEqual(len(audit_lines), 1)
        audit = json.loads(audit_lines[0])
        self.assertEqual(audit["tool"], "neutron_agent_health")
        self.assertEqual(audit["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
