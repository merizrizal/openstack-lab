import importlib.util
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
COLLECTOR_PATH = (
    REPO_ROOT
    / "ansible/ai_ops_runtime/roles/host_observer/files/aiops_host_diagnostic.py"
)
CONNECTOR_PATH = (
    REPO_ROOT
    / "ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/host_diagnostics"
    / "aiops_host_diagnostic_connector.py"
)
TOOL_RUNNER_PATH = (
    REPO_ROOT
    / "ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner"
    / "aiops_tool_runner.py"
)
TOOL_REGISTRY_PATH = TOOL_RUNNER_PATH.with_name("tool_registry.json")


def load_collector_module():
    spec = importlib.util.spec_from_file_location(
        "aiops_host_diagnostic", COLLECTOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_connector_module():
    spec = importlib.util.spec_from_file_location(
        "aiops_host_diagnostic_connector", CONNECTOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_tool_runner_module():
    spec = importlib.util.spec_from_file_location("aiops_tool_runner", TOOL_RUNNER_PATH)
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


class TestHostDiagnosticConnector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.connector = load_connector_module()

    def write_policy(self, directory: str) -> Path:
        path = Path(directory) / "host_diagnostic_policy.json"
        path.write_text(
            '{"aliases":{"controller01":{"address":"192.168.121.5",'
            '"kinds":["metadata","nova","neutron"],'
            '"time_windows":["15m","30m","1h"]},'
            '"compute01":{"address":"192.168.121.6",'
            '"kinds":["nova","neutron"],'
            '"time_windows":["15m","30m","1h"]}}}',
            encoding="utf-8",
        )
        return path

    def test_policy_requires_root_owned_non_writable_alias_mapping(self):
        with tempfile.TemporaryDirectory() as tempdir:
            policy_path = self.write_policy(tempdir)
            safe_metadata = SimpleNamespace(st_uid=0, st_mode=0o100644)
            with patch.object(self.connector.os, "stat", return_value=safe_metadata):
                policy = self.connector.load_host_policy(policy_path)

            self.assertIn("controller01", policy["aliases"])
            for unsafe_metadata in (
                SimpleNamespace(st_uid=1000, st_mode=0o100644),
                SimpleNamespace(st_uid=0, st_mode=0o100664),
            ):
                with patch.object(
                    self.connector.os, "stat", return_value=unsafe_metadata
                ):
                    with self.assertRaises(ValueError):
                        self.connector.load_host_policy(policy_path)

    def test_request_revalidates_alias_kind_and_time_window(self):
        policy = {
            "aliases": {
                "controller01": {
                    "address": "192.168.121.5",
                    "kinds": ["metadata", "nova", "neutron"],
                    "time_windows": ["15m", "30m", "1h"],
                },
                "compute01": {
                    "address": "192.168.121.6",
                    "kinds": ["nova", "neutron"],
                    "time_windows": ["15m", "30m", "1h"],
                },
            }
        }
        self.assertEqual(
            self.connector.validate_connector_request(
                "metadata", "controller01", "15m", policy
            ),
            "192.168.121.5",
        )

        for kind, alias, window in (
            ("shell", "controller01", "15m"),
            ("metadata", "storage01", "15m"),
            ("metadata", "compute01", "15m"),
            ("metadata", "controller01", "5m"),
            ("metadata", "controller01;id", "15m"),
        ):
            with self.subTest(kind=kind, alias=alias, window=window):
                with self.assertRaises(ValueError):
                    self.connector.validate_connector_request(
                        kind, alias, window, policy
                    )

    def test_build_ssh_argv_uses_only_fixed_pinned_options_and_command(self):
        argv = self.connector.build_ssh_argv(
            "192.168.121.5",
            "metadata",
            "15m",
            "/opt/openstack-ai-ops/credentials/ssh/observer_ed25519",
            "/opt/openstack-ai-ops/credentials/ssh/known_hosts",
        )

        self.assertEqual(
            argv,
            [
                "/usr/bin/ssh",
                "-F",
                "/dev/null",
                "-i",
                "/opt/openstack-ai-ops/credentials/ssh/observer_ed25519",
                "-o",
                "BatchMode=yes",
                "-o",
                "IdentitiesOnly=yes",
                "-o",
                "IdentityAgent=none",
                "-o",
                "PasswordAuthentication=no",
                "-o",
                "KbdInteractiveAuthentication=no",
                "-o",
                "NumberOfPasswordPrompts=0",
                "-o",
                "StrictHostKeyChecking=yes",
                "-o",
                "UserKnownHostsFile=/opt/openstack-ai-ops/credentials/ssh/known_hosts",
                "-o",
                "GlobalKnownHostsFile=/dev/null",
                "-o",
                "UpdateHostKeys=no",
                "-o",
                "ForwardAgent=no",
                "-o",
                "ClearAllForwardings=yes",
                "-o",
                "RequestTTY=no",
                "-o",
                "PermitLocalCommand=no",
                "-l",
                "aiops-observer",
                "192.168.121.5",
                "aiops-host-diagnostic",
                "metadata",
                "15m",
            ],
        )

    def test_connector_uses_no_shell_and_propagates_timeout_and_os_error(self):
        calls = []

        def fake_run(argv, **kwargs):
            calls.append((argv, kwargs))
            return subprocess.CompletedProcess(argv, 0, "{}\n", "")

        completed = self.connector.run_connector(["ssh"], 20, fake_run)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(calls[0][1]["shell"], False)
        self.assertEqual(calls[0][1]["timeout"], 20)

        def timeout_run(argv, **kwargs):
            raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

        def error_run(argv, **kwargs):
            raise OSError("ssh unavailable")

        with self.assertRaises(subprocess.TimeoutExpired):
            self.connector.run_connector(["ssh"], 20, timeout_run)
        with self.assertRaises(OSError):
            self.connector.run_connector(["ssh"], 20, error_run)

    def test_main_does_not_accept_a_caller_selected_remote_command(self):
        calls = []

        def fake_run(argv, **kwargs):
            calls.append((argv, kwargs))
            return subprocess.CompletedProcess(argv, 0, "", "")

        stderr = io.StringIO()
        exit_code = self.connector.main(
            ["metadata", "controller01", "15m", "id"],
            stderr=stderr,
            run_command=fake_run,
        )

        self.assertEqual(exit_code, 2)
        self.assertIn("usage:", stderr.getvalue())
        self.assertEqual(calls, [])


class TestHostDiagnosticToolMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_tool_runner_module()
        cls.registry = cls.runner.load_registry(TOOL_REGISTRY_PATH)
        cls.tools = {tool["name"]: tool for tool in cls.registry["tools"]}

    def test_host_tool_matrix_builds_only_reviewed_connector_argv(self):
        expected_tools = {
            "recent_metadata_errors": ("metadata", ["controller01"]),
            "recent_nova_errors": (
                "nova",
                ["controller01", "compute01", "compute02"],
            ),
            "recent_neutron_errors": (
                "neutron",
                ["controller01", "compute01", "compute02"],
            ),
        }
        approved_windows = ["15m", "30m", "1h"]
        connector_path = (
            "/opt/openstack-ai-ops/scripts/host_diagnostics/"
            "aiops_host_diagnostic_connector.py"
        )

        for tool_name, (kind, allowed_hosts) in expected_tools.items():
            with self.subTest(tool=tool_name):
                tool = self.tools[tool_name]
                self.assertTrue(tool["available"])
                self.assertEqual(tool["credential_profile"], "restricted-ssh-observer")
                self.assertEqual(
                    tool["risk_level"], "high_readonly_restricted_host_scope"
                )
                self.assertEqual(
                    tool["mutation_guarantee"],
                    "forced_command_restricted_sudo_readonly_bounded",
                )
                self.assertEqual(tool["fixed_arguments"], [kind])
                self.assertEqual(tool["arguments"][0]["allowed_values"], allowed_hosts)
                self.assertEqual(
                    tool["arguments"][1]["allowed_values"], approved_windows
                )

                for host in allowed_hosts:
                    for time_window in approved_windows:
                        _, validated_args = self.runner.validate_request(
                            self.registry,
                            tool_name,
                            {"host": host, "time_window": time_window},
                        )
                        self.assertEqual(
                            self.runner.build_command_argv(tool, validated_args),
                            [connector_path, kind, host, time_window],
                        )

    def test_host_tool_matrix_rejects_cross_role_and_unsafe_requests(self):
        for tool_name, host in (
            ("recent_metadata_errors", "compute01"),
            ("recent_nova_errors", "storage01"),
            ("recent_neutron_errors", "ceph01"),
        ):
            with self.subTest(tool=tool_name, host=host):
                with self.assertRaisesRegex(ValueError, "host is not an allowed value"):
                    self.runner.validate_request(
                        self.registry,
                        tool_name,
                        {"host": host, "time_window": "15m"},
                    )

        for tool_name in (
            "recent_metadata_errors",
            "recent_nova_errors",
            "recent_neutron_errors",
        ):
            with self.subTest(tool=tool_name, request="unsafe window"):
                with self.assertRaisesRegex(
                    ValueError, "time_window is not an allowed value"
                ):
                    self.runner.validate_request(
                        self.registry,
                        tool_name,
                        {"host": "controller01", "time_window": "15m;id"},
                    )

        with self.assertRaisesRegex(
            ValueError, "unknown declared argument.*diagnostic_kind"
        ):
            self.runner.validate_request(
                self.registry,
                "recent_nova_errors",
                {
                    "host": "controller01",
                    "time_window": "15m",
                    "diagnostic_kind": "neutron",
                },
            )


if __name__ == "__main__":
    unittest.main()
