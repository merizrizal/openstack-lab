import contextlib
import importlib.util
import io
import json
import os
import stat
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

RUNNER_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/aiops_tool_runner.py"
)
SPEC = importlib.util.spec_from_loader(
    "aiops_tool_runner",
    SourceFileLoader("aiops_tool_runner", str(RUNNER_PATH)),
)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class RequestGatewayTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.audit_directory = Path(self.temporary.name) / "audit"
        self.audit_directory.mkdir()
        os.chmod(self.audit_directory, RUNNER.AUDIT_DIRECTORY_MODE)
        owner = self.audit_directory.stat()
        RUNNER._TEST_AUDIT_DIRECTORY = self.audit_directory
        RUNNER._TEST_AUDIT_OWNER = (owner.st_uid, owner.st_gid)
        self.marker = Path(self.temporary.name) / "child-started"
        self.fixture = Path(self.temporary.name) / "marker_fixture.py"
        self.fixture.write_text(
            f"from pathlib import Path\nPath({str(self.marker)!r}).touch()\n",
            encoding="utf-8",
        )
        self.fixture.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

    def tearDown(self):
        RUNNER._TEST_AUDIT_DIRECTORY = None
        RUNNER._TEST_AUDIT_OWNER = None
        self.temporary.cleanup()

    def run_request(self, argv):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = RUNNER.main(argv)
        return exit_code, json.loads(output.getvalue())

    def assert_no_spawn(self, argv, expected_status, expected_exit_code):
        exit_code, outcome = self.run_request(argv)
        self.assertEqual(exit_code, expected_exit_code)
        self.assertEqual(outcome["status"], expected_status)
        self.assertFalse(self.marker.exists())

    def test_unknown_and_generic_tools_are_denied_without_spawn(self):
        for tool_name in ("unknown_tool", "shell", "ssh", "openstack_cli"):
            with self.subTest(tool_name=tool_name):
                self.assert_no_spawn([tool_name], "denied", 2)

    def test_malformed_and_duplicate_declarations_are_validation_errors_without_spawn(
        self,
    ):
        cases = (
            ["server_basic_info", "--arg"],
            ["server_basic_info", "--arg", "server_identifier"],
            ["server_basic_info", "--arg", "=server-1"],
            [
                "server_basic_info",
                "--arg",
                "server_identifier=one",
                "--arg",
                "server_identifier=two",
            ],
            ["server_basic_info", "--parameter", "server_identifier=server-1"],
        )
        for argv in cases:
            with self.subTest(argv=argv):
                self.assert_no_spawn(argv, "validation_error", 3)

    def test_missing_undeclared_and_unsafe_parameters_are_validation_errors_without_spawn(
        self,
    ):
        cases = (
            ["server_basic_info"],
            ["project_resource_summary", "--arg", "server_identifier=server-1"],
            ["server_network_info", "--arg", "server_identifier=../server"],
            ["server_network_info", "--arg", "server_identifier=server/name"],
            ["server_network_info", "--arg", "server_identifier=server;id"],
            ["server_network_info", "--arg", f"server_identifier={'a' * 256}"],
        )
        for argv in cases:
            with self.subTest(argv=argv):
                self.assert_no_spawn(argv, "validation_error", 3)

    def test_wrong_type_parameter_is_rejected_without_spawn(self):
        registry = RUNNER.load_registry()
        parameter = registry["tools"][1]["parameters"][0]

        with self.assertRaises(RUNNER.RequestValidationError):
            RUNNER.validate_parameter_value(parameter, 1)

        self.assertFalse(self.marker.exists())

    def test_valid_requests_remain_unavailable_without_spawn(self):
        for argv in (
            ["project_resource_summary"],
            ["server_basic_info", "--arg", "server_identifier=server-1"],
        ):
            with self.subTest(argv=argv):
                self.assert_no_spawn(argv, "unavailable", 5)


if __name__ == "__main__":
    unittest.main()
