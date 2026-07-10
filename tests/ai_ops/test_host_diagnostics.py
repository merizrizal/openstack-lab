import importlib.util
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COLLECTOR_PATH = (
    REPO_ROOT
    / "ansible/ai_ops_runtime/roles/host_observer/files/aiops_host_diagnostic.py"
)


def load_collector_module():
    spec = importlib.util.spec_from_file_location(
        "aiops_host_diagnostic", COLLECTOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestHostDiagnosticCollector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.collector = load_collector_module()

    def test_forced_command_accepts_only_approved_grammar(self):
        self.assertEqual(
            self.collector.parse_forced_command("aiops-host-diagnostic metadata 15m"),
            ("metadata", "15m"),
        )

        for command in (
            "",
            "metadata 15m",
            "aiops-host-diagnostic metadata 5m",
            "aiops-host-diagnostic shell 15m",
            "aiops-host-diagnostic metadata 15m extra",
            "aiops-host-diagnostic metadata 15m; id",
        ):
            with self.subTest(command=command):
                with self.assertRaises(ValueError):
                    self.collector.parse_forced_command(command)

    def test_build_fixed_journal_argv_rejects_unreviewed_values(self):
        self.assertEqual(
            self.collector.build_fixed_journal_argv(
                "neutron-metadata-agent", "30m", 200
            ),
            [
                "journalctl",
                "--no-pager",
                "--output=short-iso",
                "--since",
                "30 minutes ago",
                "--unit",
                "neutron-metadata-agent",
                "--lines",
                "200",
            ],
        )

        for unit, time_window, line_limit in (
            ("ssh", "15m", 200),
            ("apache2", "5m", 200),
            ("apache2", "15m", 201),
        ):
            with self.subTest(
                unit=unit, time_window=time_window, line_limit=line_limit
            ):
                with self.assertRaises(ValueError):
                    self.collector.build_fixed_journal_argv(
                        unit, time_window, line_limit
                    )

    def test_fixed_log_tail_bounds_and_redacts(self):
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "diagnostic.log"
            path.write_text(
                "\n".join(
                    [f"metadata timeout {index}" for index in range(1, 205)]
                    + ["metadata token=exposed"]
                )
                + "\n",
                encoding="utf-8",
            )

            section = self.collector.collect_fixed_log_tail(path, 200)

        self.assertEqual(section["status"], "partial")
        self.assertTrue(section["truncated"])
        self.assertEqual(len(section["lines"]), 200)
        self.assertNotIn("exposed", "\n".join(section["lines"]))

    def test_missing_log_source_is_unavailable(self):
        with tempfile.TemporaryDirectory() as tempdir:
            section = self.collector.collect_fixed_log_tail(
                Path(tempdir) / "missing.log", 200
            )

        self.assertEqual(section["status"], "unavailable")
        self.assertEqual(section["lines"], [])

    def test_bound_payload_truncates_to_byte_limit(self):
        payload = {
            "kind": "metadata",
            "time_window": "15m",
            "sections": [
                {
                    "source": "journal:apache2",
                    "status": "ok",
                    "lines": ["x" * 500, "y" * 500],
                }
            ],
        }

        bounded = self.collector.bound_payload(payload, 200)

        self.assertLessEqual(self.collector.serialized_payload_size(bounded), 200)
        self.assertTrue(bounded["truncated"])

    def test_collector_uses_fixed_argv_without_shell(self):
        calls = []

        def fake_run(argv, **kwargs):
            calls.append((argv, kwargs))
            return subprocess.CompletedProcess(
                argv,
                0,
                "metadata timeout token=exposed\n",
                "",
            )

        payload = self.collector.collect_diagnostic("metadata", "15m", fake_run)

        self.assertEqual(payload["kind"], "metadata")
        self.assertTrue(calls)
        self.assertTrue(all(isinstance(argv, list) for argv, _ in calls))
        self.assertTrue(all(kwargs["shell"] is False for _, kwargs in calls))
        self.assertNotIn("exposed", str(payload))
        self.assertIn(
            [
                "journalctl",
                "--no-pager",
                "--output=short-iso",
                "--since",
                "15 minutes ago",
                "--unit",
                "neutron-metadata-agent",
                "--lines",
                "200",
            ],
            [argv for argv, _ in calls],
        )
        self.assertIn(
            ["ss", "-ltn", "sport", "=", ":8775"],
            [argv for argv, _ in calls],
        )

    def test_dispatcher_passes_only_validated_request_to_collection_mode(self):
        calls = []
        stdout = io.StringIO()
        stderr = io.StringIO()

        def fake_run(argv, **kwargs):
            calls.append((argv, kwargs))
            return subprocess.CompletedProcess(argv, 0, "{}\n", "")

        exit_code = self.collector.main(
            argv=[],
            environ={"SSH_ORIGINAL_COMMAND": "aiops-host-diagnostic metadata 15m"},
            stdout=stdout,
            stderr=stderr,
            run_command=fake_run,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "{}\n")
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            calls[0][0],
            ["sudo", "-n", str(COLLECTOR_PATH.resolve()), "--collect"],
        )
        self.assertEqual(calls[0][1]["input"], "metadata 15m\n")
        self.assertFalse(calls[0][1]["shell"])


if __name__ == "__main__":
    unittest.main()
