import importlib.util
import json
import subprocess
import sys
import tempfile
import time
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest import mock

RUNNER_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/aiops_tool_runner.py"
)
SPEC = importlib.util.spec_from_loader(
    "aiops_tool_runner_process_bounds",
    SourceFileLoader("aiops_tool_runner_process_bounds", str(RUNNER_PATH)),
)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class ProcessBoundsTest(unittest.TestCase):
    def capture_fixture(self, source, timeout_seconds=1, output_limit_bytes=128):
        process = subprocess.Popen(
            [sys.executable, "-c", source],
            start_new_session=True,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        return RUNNER.capture_bounded(process, timeout_seconds, output_limit_bytes)

    def test_noisy_dual_streams_are_drained_and_bounded(self):
        capture = self.capture_fixture(
            "import sys; sys.stdout.buffer.write(b'o' * 1024); sys.stderr.buffer.write(b'e' * 1024)"
        )

        self.assertEqual(capture.return_code, 0)
        self.assertFalse(capture.timed_out)
        self.assertTrue(capture.truncated)
        self.assertLessEqual(len(capture.stdout) + len(capture.stderr), 128)

    def test_timeout_terminates_parent_and_descendant(self):
        with tempfile.TemporaryDirectory() as directory:
            pid_path = Path(directory) / "descendant.pid"
            source = (
                "import subprocess, sys, time\n"
                "from pathlib import Path\n"
                "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
                f"Path({str(pid_path)!r}).write_text(str(child.pid), encoding='utf-8')\n"
                "time.sleep(30)\n"
            )
            capture = self.capture_fixture(source)
            descendant_pid = int(pid_path.read_text(encoding="utf-8"))

            self.assertTrue(capture.timed_out)
            deadline = time.monotonic() + 2
            while (
                Path(f"/proc/{descendant_pid}").exists() and time.monotonic() < deadline
            ):
                time.sleep(0.05)
            self.assertFalse(Path(f"/proc/{descendant_pid}").exists())

    def test_interruption_before_spawn_is_normalized_without_unbound_process(self):
        tool = RUNNER.load_registry()["tools"][0]
        with (
            mock.patch.object(
                RUNNER,
                "build_command_argv",
                return_value=["fixture"],
            ),
            mock.patch.object(
                RUNNER.subprocess,
                "Popen",
                side_effect=KeyboardInterrupt,
            ),
        ):
            outcome = RUNNER.execute_fixed_diagnostic(tool, {})

        self.assertEqual(outcome, ("error", "runner was interrupted", None))

    def test_invalid_utf8_and_malformed_json_fail_closed(self):
        tool = RUNNER.load_registry()["tools"][0]
        invalid_utf8 = self.capture_fixture(
            "import sys; sys.stdout.buffer.write(b'\\xff')"
        )
        malformed_json = self.capture_fixture("print('{not-json')")

        with self.assertRaises(ValueError):
            RUNNER.validate_diagnostic_payload(tool, invalid_utf8.stdout)
        with self.assertRaises(ValueError):
            RUNNER.validate_diagnostic_payload(tool, malformed_json.stdout)

    def test_approved_unavailable_error_class_maps_to_unavailable(self):
        tool = RUNNER.load_registry()["tools"][0]
        payload = json.dumps(
            {
                "schema_version": "1.0",
                "tool": "project_resource_summary",
                "status": "error",
                "sections": [],
                "error": {"class": "service_unavailable"},
            }
        ).encode("utf-8")

        self.assertEqual(
            RUNNER.validate_diagnostic_payload(tool, payload), "unavailable"
        )


if __name__ == "__main__":
    unittest.main()
