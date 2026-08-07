import contextlib
import importlib.util
import io
import json
import os
import stat
import tempfile
import threading
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest import mock

RUNNER_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/aiops_tool_runner.py"
)
SPEC = importlib.util.spec_from_loader(
    "aiops_tool_runner_audit_persistence",
    SourceFileLoader("aiops_tool_runner_audit_persistence", str(RUNNER_PATH)),
)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class AuditPersistenceTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        os.chmod(self.directory, RUNNER.AUDIT_DIRECTORY_MODE)
        owner = os.stat(self.directory)
        RUNNER._TEST_AUDIT_DIRECTORY = self.directory
        RUNNER._TEST_AUDIT_OWNER = (owner.st_uid, owner.st_gid)
        self.event = {
            "schema_version": "1.0",
            "timestamp": "2030-01-02T03:04:05.678Z",
            "event_type": "tool_request_completed",
            "actor": "local_cli",
            "tool": "server_basic_info",
            "arguments": {"server_identifier_present": True},
            "status": "ok",
            "duration_ms": 42,
            "correlation_id": "00000000-0000-4000-8000-000000000001",
            "reason": None,
            "exit_code": 0,
            "truncated": False,
        }

    def tearDown(self):
        RUNNER._TEST_AUDIT_DIRECTORY = None
        RUNNER._TEST_AUDIT_OWNER = None
        self.temporary.cleanup()

    def test_safe_append_creates_restrictive_files_and_json_line(self):
        RUNNER.append_audit_event(self.event)

        active = self.directory / "tool-runner.jsonl"
        lock = self.directory / ".tool-runner.lock"
        self.assertEqual(json.loads(active.read_text()), self.event)
        self.assertEqual(stat.S_IMODE(active.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(lock.stat().st_mode), 0o600)

    def test_symlink_and_wrong_mode_are_rejected_without_fallback(self):
        active = self.directory / "tool-runner.jsonl"
        active.symlink_to(self.directory / "outside")
        with self.assertRaises(RUNNER.AuditPersistenceError):
            RUNNER.append_audit_event(self.event)
        active.unlink()
        active.touch()
        os.chmod(active, 0o644)
        with self.assertRaises(RUNNER.AuditPersistenceError):
            RUNNER.append_audit_event(self.event)

    def test_event_bound_is_enforced_before_filesystem_access(self):
        oversized = dict(self.event, tool="x" * RUNNER.MAX_AUDIT_EVENT_BYTES)
        with self.assertRaises(ValueError):
            RUNNER.append_audit_event(oversized)
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_rotation_retains_three_archives(self):
        active = self.directory / "tool-runner.jsonl"
        active.write_bytes(b"a" * RUNNER.AUDIT_ROTATION_BYTES)
        os.chmod(active, 0o600)
        for index in (1, 2, 3):
            archive = self.directory / f"tool-runner.jsonl.{index}"
            archive.write_text(str(index))
            os.chmod(archive, 0o600)

        RUNNER.append_audit_event(self.event)

        self.assertEqual((self.directory / "tool-runner.jsonl.3").read_text(), "2")
        self.assertEqual((self.directory / "tool-runner.jsonl.2").read_text(), "1")
        self.assertTrue(
            (self.directory / "tool-runner.jsonl.1").read_bytes().startswith(b"a")
        )
        self.assertEqual(len(list(self.directory.glob("tool-runner.jsonl.*"))), 3)

    def test_fsync_failure_is_fail_closed(self):
        with (
            mock.patch.object(RUNNER.os, "fsync", side_effect=OSError("fsync")),
            self.assertRaises(RUNNER.AuditPersistenceError),
        ):
            RUNNER.append_audit_event(self.event)
        self.assertTrue((self.directory / "tool-runner.jsonl").read_text())

    def test_concurrent_appends_remain_complete_json_lines(self):
        failures = []

        def append():
            try:
                RUNNER.append_audit_event(self.event)
            except (OSError, ValueError) as error:  # pragma: no cover
                failures.append(error)

        threads = [threading.Thread(target=append) for _ in range(12)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(failures, [])
        lines = (self.directory / "tool-runner.jsonl").read_text().splitlines()
        self.assertEqual(len(lines), 12)
        for line in lines:
            self.assertEqual(json.loads(line), self.event)

    def test_audit_failure_returns_generic_result_without_data(self):
        output = io.StringIO()
        with (
            contextlib.redirect_stdout(output),
            mock.patch.object(RUNNER.os, "fsync", side_effect=OSError("fsync")),
        ):
            result = RUNNER.emit_result_outcome(
                "server_basic_info",
                "ok",
                None,
                {"server_identifier": "fixture"},
                timestamp=self.event["timestamp"],
                correlation_id=self.event["correlation_id"],
            )
        self.assertEqual(result, 1)
        envelope = json.loads(output.getvalue())
        self.assertEqual(envelope["status"], "error")
        self.assertIsNone(envelope["data"])
        self.assertEqual(envelope["error"]["class"], "audit_write_error")


if __name__ == "__main__":
    unittest.main()
