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

    def write_registry(self, tools, supported_validation_types=None):
        if supported_validation_types is None:
            supported_validation_types = [
                "required_string",
                "safe_identifier_pattern",
            ]
        tempdir = tempfile.TemporaryDirectory()
        registry_path = Path(tempdir.name) / "tool_registry.json"
        registry_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "registry_name": "test-registry",
                    "supported_argument_validation_types": supported_validation_types,
                    "defaults": {
                        "timeout_seconds": 30,
                        "output_limit_bytes": 65536,
                    },
                    "tools": tools,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        self.addCleanup(tempdir.cleanup)
        return registry_path

    def write_executable_script(self, source: str, filename: str = "fixture_tool.py"):
        tempdir = tempfile.TemporaryDirectory()
        script_path = Path(tempdir.name) / filename
        script_path.write_text(source, encoding="utf-8")
        script_path.chmod(0o755)
        self.addCleanup(tempdir.cleanup)
        return script_path

    def make_audit_path(self):
        tempdir = tempfile.TemporaryDirectory()
        audit_path = Path(tempdir.name) / "tool-runner.jsonl"
        self.addCleanup(tempdir.cleanup)
        return audit_path

    def read_audit_events(self, audit_path: Path):
        if not audit_path.exists():
            return []
        return [
            json.loads(line)
            for line in audit_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def invoke_main_with_audit(self, argv):
        audit_path = self.make_audit_path()
        exit_code, payload = self.invoke_main(
            [*argv, "--audit-path", str(audit_path)]
        )
        return exit_code, payload, self.read_audit_events(audit_path)

    def invoke_main(self, argv):
        effective_argv = list(argv)
        if "--audit-path" not in effective_argv:
            audit_path = self.make_audit_path()
            effective_argv.extend(["--audit-path", str(audit_path)])

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = self.runner.main(effective_argv)
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

    def test_main_rejects_unknown_declared_argument(self):
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

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["validation_error"])
        self.assertEqual(payload["status"], "validation_error")
        self.assertEqual(payload["arguments"], {})
        self.assertIn("unknown declared argument", payload["stderr"])

    def test_main_rejects_missing_required_argument(self):
        registry_path = self.write_registry(
            [
                {
                    "name": "server_basic_info",
                    "available": True,
                    "arguments": [
                        {
                            "name": "server_identifier",
                            "position": 1,
                            "required": True,
                            "validation": "safe_identifier_pattern",
                            "pattern": "^[A-Za-z0-9._:-]+$",
                        }
                    ],
                }
            ]
        )

        exit_code, payload = self.invoke_main(
            ["server_basic_info", "--registry", str(registry_path)]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["validation_error"])
        self.assertEqual(payload["status"], "validation_error")
        self.assertEqual(payload["arguments"], {})
        self.assertIn("missing required argument: server_identifier", payload["stderr"])

    def test_main_rejects_unsafe_identifier_argument(self):
        registry_path = self.write_registry(
            [
                {
                    "name": "server_basic_info",
                    "available": True,
                    "arguments": [
                        {
                            "name": "server_identifier",
                            "position": 1,
                            "required": True,
                            "validation": "safe_identifier_pattern",
                            "pattern": "^[A-Za-z0-9._:-]+$",
                        }
                    ],
                }
            ]
        )

        exit_code, payload = self.invoke_main(
            [
                "server_basic_info",
                "--registry",
                str(registry_path),
                "--arg",
                "server_identifier=vm 01",
            ]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["validation_error"])
        self.assertEqual(payload["status"], "validation_error")
        self.assertEqual(payload["arguments"], {})
        self.assertIn("server_identifier contains unsafe characters", payload["stderr"])

    def test_host_and_window_validations_accept_only_declared_values(self):
        supported_validation_types = {
            "allowed_host_list",
            "bounded_time_window",
        }
        host_definition = {
            "name": "host",
            "validation": "allowed_host_list",
            "allowed_values": ["controller01", "compute01"],
        }
        window_definition = {
            "name": "time_window",
            "validation": "bounded_time_window",
            "allowed_values": ["15m", "30m", "1h"],
        }

        for argument_definition, value in (
            (host_definition, "controller01"),
            (window_definition, "15m"),
            (window_definition, "30m"),
            (window_definition, "1h"),
        ):
            with self.subTest(value=value):
                self.assertEqual(
                    self.runner.validate_argument_value(
                        argument_definition,
                        value,
                        supported_validation_types,
                    ),
                    value,
                )

        for argument_definition, value in (
            (host_definition, "compute02"),
            (host_definition, "controller01;id"),
            (window_definition, "5m"),
            (window_definition, "15m;id"),
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "is not an allowed value"):
                    self.runner.validate_argument_value(
                        argument_definition,
                        value,
                        supported_validation_types,
                    )

    def test_host_and_window_validations_reject_malformed_allowed_values(self):
        supported_validation_types = {
            "allowed_host_list",
            "bounded_time_window",
        }

        for validation_type, allowed_values in (
            ("allowed_host_list", []),
            ("allowed_host_list", "controller01"),
            ("allowed_host_list", ["controller01", "controller01"]),
            ("bounded_time_window", ["15m", ""]),
            ("bounded_time_window", ["15m", 30]),
        ):
            with self.subTest(allowed_values=allowed_values):
                with self.assertRaisesRegex(ValueError, "allowed_values"):
                    self.runner.validate_argument_value(
                        {
                            "name": validation_type,
                            "validation": validation_type,
                            "allowed_values": allowed_values,
                        },
                        "controller01",
                        supported_validation_types,
                    )

    def test_bounded_time_window_default_is_validated(self):
        tool = {
            "name": "recent_metadata_errors",
            "available": False,
            "arguments": [
                {
                    "name": "host",
                    "position": 1,
                    "required": True,
                    "validation": "allowed_host_list",
                    "allowed_values": ["controller01"],
                },
                {
                    "name": "time_window",
                    "position": 2,
                    "required": False,
                    "validation": "bounded_time_window",
                    "allowed_values": ["15m", "30m", "1h"],
                    "default": "15m",
                },
            ],
        }
        registry = self.runner.load_registry(
            self.write_registry(
                [tool],
                ["allowed_host_list", "bounded_time_window"],
            )
        )

        _, validated_args = self.runner.validate_request(
            registry,
            "recent_metadata_errors",
            {"host": "controller01"},
        )
        self.assertEqual(validated_args["time_window"], "15m")

        registry["tools"][0]["arguments"][1]["default"] = "5m"
        with self.assertRaisesRegex(ValueError, "is not an allowed value"):
            self.runner.validate_request(
                registry,
                "recent_metadata_errors",
                {"host": "controller01"},
            )

    def test_fixed_arguments_prefix_argv_and_reject_caller_overrides(self):
        requested_tool = {
            "name": "recent_metadata_errors",
            "script_target": "/opt/openstack-ai-ops/scripts/host_diagnostics.py",
            "fixed_arguments": ["metadata"],
            "arguments": [
                {
                    "name": "host",
                    "position": 1,
                    "required": True,
                    "validation": "allowed_host_list",
                    "allowed_values": ["controller01"],
                },
                {
                    "name": "time_window",
                    "position": 2,
                    "required": False,
                    "validation": "bounded_time_window",
                    "allowed_values": ["15m", "30m", "1h"],
                    "default": "15m",
                },
            ],
        }

        self.assertEqual(
            self.runner.build_command_argv(
                requested_tool,
                {"host": "controller01", "time_window": "30m"},
            ),
            [
                "/opt/openstack-ai-ops/scripts/host_diagnostics.py",
                "metadata",
                "controller01",
                "30m",
            ],
        )

        registry = {
            "tools": [requested_tool],
            "supported_argument_validation_types": [
                "allowed_host_list",
                "bounded_time_window",
            ],
        }
        with self.assertRaisesRegex(
            ValueError, "unknown declared argument.*diagnostic_kind"
        ):
            self.runner.validate_request(
                registry,
                "recent_metadata_errors",
                {
                    "host": "controller01",
                    "time_window": "30m",
                    "diagnostic_kind": "nova",
                },
            )

    def test_fixed_arguments_reject_malformed_registry_values(self):
        requested_tool = {
            "name": "recent_metadata_errors",
            "script_target": "/opt/openstack-ai-ops/scripts/host_diagnostics.py",
            "arguments": [],
        }

        for fixed_arguments in (
            "metadata",
            [],
            ["metadata", "metadata"],
            ["metadata", ""],
        ):
            with self.subTest(fixed_arguments=fixed_arguments):
                with self.assertRaisesRegex(ValueError, "fixed_arguments"):
                    self.runner.build_command_argv(
                        {**requested_tool, "fixed_arguments": fixed_arguments},
                        {},
                    )

    def test_main_executes_allowlisted_no_argument_tool_by_argv(self):
        script_path = self.write_executable_script(
            "#!/usr/bin/env python3\nprint(\"project summary ok\")\n",
            filename="project_resource_summary.py",
        )
        registry_path = self.write_registry(
            [
                {
                    "name": "project_resource_summary",
                    "available": True,
                    "script_target": str(script_path),
                    "timeout_seconds": 5,
                    "output_limit_bytes": 1024,
                    "arguments": [],
                }
            ]
        )

        exit_code, payload = self.invoke_main(
            ["project_resource_summary", "--registry", str(registry_path)]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["ok"])
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["arguments"], {})
        self.assertEqual(payload["exit_code"], 0)
        self.assertEqual(payload["stdout"], "project summary ok\n")
        self.assertEqual(payload["stderr"], "")
        self.assertFalse(payload["truncated"])

    def test_main_executes_allowlisted_single_argument_tool_by_argv(self):
        script_path = self.write_executable_script(
            "#!/usr/bin/env python3\nimport json\nimport sys\nprint(json.dumps(sys.argv[1:]))\n",
            filename="server_basic_info.py",
        )
        registry_path = self.write_registry(
            [
                {
                    "name": "server_basic_info",
                    "available": True,
                    "script_target": str(script_path),
                    "timeout_seconds": 5,
                    "output_limit_bytes": 1024,
                    "arguments": [
                        {
                            "name": "server_identifier",
                            "position": 1,
                            "required": True,
                            "validation": "safe_identifier_pattern",
                            "pattern": "^[A-Za-z0-9._:-]+$",
                        }
                    ],
                }
            ]
        )

        exit_code, payload = self.invoke_main(
            [
                "server_basic_info",
                "--registry",
                str(registry_path),
                "--arg",
                "server_identifier=vm01:prod",
            ]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["ok"])
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["arguments"], {"server_identifier": "vm01:prod"})
        self.assertEqual(payload["exit_code"], 0)
        self.assertEqual(payload["stdout"], '["vm01:prod"]\n')
        self.assertEqual(payload["stderr"], "")
        self.assertFalse(payload["truncated"])

    def test_main_reports_timeout_for_slow_tool(self):
        script_path = self.write_executable_script(
            "#!/usr/bin/env python3\nimport time\ntime.sleep(2)\nprint(\"finished\")\n",
            filename="slow_tool.py",
        )
        registry_path = self.write_registry(
            [
                {
                    "name": "project_resource_summary",
                    "available": True,
                    "script_target": str(script_path),
                    "timeout_seconds": 1,
                    "output_limit_bytes": 1024,
                    "arguments": [],
                }
            ]
        )

        exit_code, payload = self.invoke_main(
            ["project_resource_summary", "--registry", str(registry_path)]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["timeout"])
        self.assertEqual(payload["status"], "timeout")
        self.assertIsNone(payload["exit_code"])
        self.assertIn("exceeded timeout of 1 seconds", payload["stderr"])

    def test_main_marks_truncated_output_when_limit_is_exceeded(self):
        script_path = self.write_executable_script(
            "#!/usr/bin/env python3\nprint(\"ABCDEFGHIJKLMNOPQRSTUVWXYZ\")\n",
            filename="noisy_tool.py",
        )
        registry_path = self.write_registry(
            [
                {
                    "name": "project_resource_summary",
                    "available": True,
                    "script_target": str(script_path),
                    "timeout_seconds": 5,
                    "output_limit_bytes": 8,
                    "arguments": [],
                }
            ]
        )

        exit_code, payload = self.invoke_main(
            ["project_resource_summary", "--registry", str(registry_path)]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["truncated"])
        self.assertEqual(payload["status"], "truncated")
        self.assertEqual(payload["exit_code"], 0)
        self.assertEqual(payload["stdout"], "ABCDEFGH")
        self.assertEqual(payload["stderr"], "")
        self.assertTrue(payload["truncated"])


    def test_main_writes_audit_event_for_denied_request(self):
        registry_path = self.write_registry(
            [
                {
                    "name": "project_resource_summary",
                    "available": True,
                    "arguments": [],
                }
            ]
        )

        exit_code, payload, events = self.invoke_main_with_audit(
            ["not_registered", "--registry", str(registry_path)]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["denied"])
        self.assertEqual(payload["status"], "denied")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["tool"], "not_registered")
        self.assertEqual(events[0]["status"], "denied")
        self.assertEqual(events[0]["arguments"], {})
        self.assertNotIn("client_id", events[0])
        self.assertNotIn("transport", events[0])
        self.assertIn("allowlist", events[0]["reason"])

    def test_main_writes_fixed_mcp_origin_metadata_only_to_audit_event(self):
        registry_path = self.write_registry(
            [
                {
                    "name": "project_resource_summary",
                    "available": True,
                    "arguments": [],
                }
            ]
        )

        exit_code, payload, events = self.invoke_main_with_audit(
            [
                "not_registered",
                "--registry",
                str(registry_path),
                "--client-id",
                self.runner.MCP_AUDIT_CLIENT_ID,
                "--transport",
                self.runner.MCP_AUDIT_TRANSPORT,
            ]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["denied"])
        self.assertEqual(payload["status"], "denied")
        self.assertNotIn("client_id", payload)
        self.assertNotIn("transport", payload)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["client_id"], self.runner.MCP_AUDIT_CLIENT_ID)
        self.assertEqual(events[0]["transport"], self.runner.MCP_AUDIT_TRANSPORT)

    def test_audit_origin_rejects_unreviewed_values(self):
        envelope = self.runner.build_result_envelope(
            "project_resource_summary",
            "denied",
            request_id="req-123",
        )

        with self.assertRaisesRegex(ValueError, "client identifier"):
            self.runner.build_audit_event(
                envelope,
                client_id="untrusted-client",
            )
        with self.assertRaisesRegex(ValueError, "transport"):
            self.runner.build_audit_event(
                envelope,
                transport="https",
            )
        with self.assertRaises(SystemExit):
            self.runner.parse_cli_args(
                ["project_resource_summary", "--client-id", "untrusted-client"]
            )
        with self.assertRaises(SystemExit):
            self.runner.parse_cli_args(
                ["project_resource_summary", "--transport", "https"]
            )

    def test_main_writes_audit_event_for_validation_error(self):
        registry_path = self.write_registry(
            [
                {
                    "name": "project_resource_summary",
                    "available": True,
                    "arguments": [],
                }
            ]
        )

        exit_code, payload, events = self.invoke_main_with_audit(
            [
                "project_resource_summary",
                "--registry",
                str(registry_path),
                "--arg",
                "scope=project",
            ]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["validation_error"])
        self.assertEqual(payload["status"], "validation_error")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["status"], "validation_error")
        self.assertIn("unknown declared argument", events[0]["reason"])

    def test_main_writes_audit_event_for_unavailable_request(self):
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

        exit_code, payload, events = self.invoke_main_with_audit(
            ["neutron_agent_health", "--registry", str(registry_path)]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["unavailable"])
        self.assertEqual(payload["status"], "unavailable")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["status"], "unavailable")
        self.assertEqual(events[0]["reason"], "operator-reader profile deferred")

    def test_main_writes_audit_event_for_successful_execution(self):
        script_path = self.write_executable_script(
            "#!/usr/bin/env python3\nprint(\"project summary ok\")\n",
            filename="project_resource_summary.py",
        )
        registry_path = self.write_registry(
            [
                {
                    "name": "project_resource_summary",
                    "available": True,
                    "script_target": str(script_path),
                    "timeout_seconds": 5,
                    "output_limit_bytes": 1024,
                    "arguments": [],
                }
            ]
        )

        exit_code, payload, events = self.invoke_main_with_audit(
            ["project_resource_summary", "--registry", str(registry_path)]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["ok"])
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["status"], "ok")
        self.assertEqual(events[0]["exit_code"], 0)
        self.assertNotIn("reason", events[0])

    def test_main_writes_audit_event_for_timeout(self):
        script_path = self.write_executable_script(
            "#!/usr/bin/env python3\nimport time\ntime.sleep(2)\n",
            filename="slow_tool.py",
        )
        registry_path = self.write_registry(
            [
                {
                    "name": "project_resource_summary",
                    "available": True,
                    "script_target": str(script_path),
                    "timeout_seconds": 1,
                    "output_limit_bytes": 1024,
                    "arguments": [],
                }
            ]
        )

        exit_code, payload, events = self.invoke_main_with_audit(
            ["project_resource_summary", "--registry", str(registry_path)]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["timeout"])
        self.assertEqual(payload["status"], "timeout")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["status"], "timeout")
        self.assertIn("exceeded timeout", events[0]["reason"])

    def test_main_writes_audit_event_for_truncated_output(self):
        script_path = self.write_executable_script(
            "#!/usr/bin/env python3\nprint(\"ABCDEFGHIJKLMNOPQRSTUVWXYZ\")\n",
            filename="noisy_tool.py",
        )
        registry_path = self.write_registry(
            [
                {
                    "name": "project_resource_summary",
                    "available": True,
                    "script_target": str(script_path),
                    "timeout_seconds": 5,
                    "output_limit_bytes": 8,
                    "arguments": [],
                }
            ]
        )

        exit_code, payload, events = self.invoke_main_with_audit(
            ["project_resource_summary", "--registry", str(registry_path)]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["truncated"])
        self.assertEqual(payload["status"], "truncated")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["status"], "truncated")
        self.assertTrue(events[0]["truncated"])

    def test_main_writes_audit_event_for_execution_error(self):
        script_path = self.write_executable_script(
            "#!/usr/bin/env python3\nimport sys\nprint(\"boom\", file=sys.stderr)\nsys.exit(7)\n",
            filename="failing_tool.py",
        )
        registry_path = self.write_registry(
            [
                {
                    "name": "project_resource_summary",
                    "available": True,
                    "script_target": str(script_path),
                    "timeout_seconds": 5,
                    "output_limit_bytes": 1024,
                    "arguments": [],
                }
            ]
        )

        exit_code, payload, events = self.invoke_main_with_audit(
            ["project_resource_summary", "--registry", str(registry_path)]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["error"])
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["exit_code"], 7)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["status"], "error")
        self.assertEqual(events[0]["exit_code"], 7)
        self.assertIn("boom", events[0]["reason"])

    def test_main_sanitizes_secret_like_arguments_in_result_and_audit(self):
        script_path = self.write_executable_script(
            "#!/usr/bin/env python3\nprint(\"ok\")\n",
            filename="secret_arg_tool.py",
        )
        registry_path = self.write_registry(
            [
                {
                    "name": "project_resource_summary",
                    "available": True,
                    "script_target": str(script_path),
                    "timeout_seconds": 5,
                    "output_limit_bytes": 1024,
                    "arguments": [
                        {
                            "name": "api_token",
                            "position": 1,
                            "required": True,
                            "validation": "required_string",
                        }
                    ],
                }
            ]
        )

        exit_code, payload, events = self.invoke_main_with_audit(
            [
                "project_resource_summary",
                "--registry",
                str(registry_path),
                "--arg",
                "api_token=super-secret-token",
            ]
        )

        self.assertEqual(exit_code, self.runner.STATUS_EXIT_CODES["ok"])
        self.assertEqual(payload["arguments"], {"_redacted_argument_count": 1})
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["arguments"], {"_redacted_argument_count": 1})
        self.assertNotIn("super-secret-token", json.dumps(events[0], sort_keys=True))

if __name__ == "__main__":
    unittest.main()
