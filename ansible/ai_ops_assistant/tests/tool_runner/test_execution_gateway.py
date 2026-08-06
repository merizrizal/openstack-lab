import contextlib
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
    "aiops_tool_runner_execution",
    SourceFileLoader("aiops_tool_runner_execution", str(RUNNER_PATH)),
)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class ExecutionGatewayTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.record_path = self.root / "fixture-record.json"
        self.fixture_path = self.root / "approved_fixture.py"
        self.fixture_path.write_text(
            "\n".join(
                (
                    f"#!{sys.executable}",
                    "import json",
                    "import os",
                    "import sys",
                    "from pathlib import Path",
                    f"Path({str(self.record_path)!r}).write_text(json.dumps({{'argv': sys.argv, 'cwd': str(Path.cwd()), 'environment': dict(os.environ)}}), encoding='utf-8')",
                    "tool = {'server-1': 'server_basic_info', 'server-2': 'server_network_info'}.get(sys.argv[-1], 'project_resource_summary')",
                    "print(json.dumps({'schema_version': '1.0', 'tool': tool, 'status': 'ok', 'sections': [], 'error': None}))",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        self.fixture_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        self.original_secret = os.environ.get("PARENT_SECRET_CANARY")
        os.environ["PARENT_SECRET_CANARY"] = "must-not-reach-child"
        RUNNER._TEST_EXECUTION_TARGET = self.fixture_path
        RUNNER._TEST_WORKING_DIRECTORY = self.root

    def tearDown(self):
        RUNNER._TEST_EXECUTION_TARGET = None
        RUNNER._TEST_WORKING_DIRECTORY = None
        if self.original_secret is None:
            os.environ.pop("PARENT_SECRET_CANARY", None)
        else:
            os.environ["PARENT_SECRET_CANARY"] = self.original_secret
        self.temporary.cleanup()

    def run_request(self, argv):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = RUNNER.main(argv)
        return exit_code, json.loads(output.getvalue())

    def test_all_tools_use_only_fixed_fixture_argvs_and_environment(self):
        cases = (
            (["project_resource_summary"], [str(self.fixture_path)]),
            (
                ["server_basic_info", "--arg", "server_identifier=server-1"],
                [str(self.fixture_path), "server-1"],
            ),
            (
                ["server_network_info", "--arg", "server_identifier=server-2"],
                [str(self.fixture_path), "server-2"],
            ),
        )
        for argv, expected_argv in cases:
            with self.subTest(argv=argv):
                self.record_path.unlink(missing_ok=True)
                exit_code, outcome = self.run_request(argv)
                record = json.loads(self.record_path.read_text(encoding="utf-8"))

                self.assertEqual(exit_code, 0)
                self.assertEqual(outcome["status"], "ok")
                self.assertEqual(outcome["tool"], argv[0])
                self.assertFalse(outcome["truncated"])
                self.assertIn("duration_ms", outcome)
                self.assertEqual(record["argv"], expected_argv)
                self.assertEqual(record["cwd"], str(self.root))
                self.assertEqual(record["environment"], RUNNER.CHILD_ENVIRONMENT)
                self.assertNotIn("PARENT_SECRET_CANARY", record["environment"])

    def test_executable_overrides_and_server_requests_do_not_reach_the_fixture(self):
        exit_code, outcome = self.run_request(
            ["project_resource_summary", "--arg", "executable=/bin/sh"]
        )
        self.assertEqual(exit_code, 3)
        self.assertEqual(outcome["status"], "validation_error")
        self.assertFalse(self.record_path.exists())

        exit_code, outcome = self.run_request(
            ["server_basic_info", "--arg", "server_identifier=server-1;/bin/sh"]
        )
        self.assertEqual(exit_code, 3)
        self.assertEqual(outcome["status"], "validation_error")
        self.assertFalse(self.record_path.exists())

    def test_missing_or_symlinked_fixture_is_not_executed(self):
        RUNNER._TEST_EXECUTION_TARGET = self.root / "missing_fixture"
        exit_code, outcome = self.run_request(["project_resource_summary"])
        self.assertEqual(exit_code, 5)
        self.assertEqual(outcome["status"], "unavailable")
        self.assertFalse(self.record_path.exists())

        target = self.root / "fixture-target"
        target.write_text("fixture", encoding="utf-8")
        symlink = self.root / "fixture-link"
        symlink.symlink_to(target)
        RUNNER._TEST_EXECUTION_TARGET = symlink
        exit_code, outcome = self.run_request(["project_resource_summary"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(outcome["status"], "error")
        self.assertFalse(self.record_path.exists())


if __name__ == "__main__":
    unittest.main()
