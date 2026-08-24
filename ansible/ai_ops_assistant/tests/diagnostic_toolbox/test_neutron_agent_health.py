import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[2] / "roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved/neutron_agent_health.py"
SPEC = importlib.util.spec_from_loader(
    "neutron_agent_health",
    SourceFileLoader("neutron_agent_health", str(SCRIPT_PATH)),
)
DIAGNOSTIC = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(DIAGNOSTIC)


FAKE_OPENSTACK = r'''#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

Path(os.environ["AIOPS_TEST_ARGV_LOG"]).write_text(json.dumps(sys.argv[1:]))
Path(os.environ["AIOPS_TEST_ENV_LOG"]).write_text(json.dumps(sorted(os.environ)))
scenario = os.environ.get("AIOPS_FIXTURE_SCENARIO", "payload")
if scenario == "failure":
    sys.stderr.write("Forbidden\n")
    raise SystemExit(1)
if scenario == "invalid_utf8":
    sys.stdout.buffer.write(b"\xff\xfe")
    raise SystemExit(0)
sys.stdout.buffer.write(Path(os.environ["AIOPS_FIXTURE_PAYLOAD_FILE"]).read_bytes())
'''


class NeutronAgentHealthTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.fake_openstack = self.directory / "openstack"
        self.fake_openstack.write_text(FAKE_OPENSTACK)
        self.fake_openstack.chmod(0o700)
        self.payload_file = self.directory / "payload.json"
        self.argv_log = self.directory / "argv.json"
        self.env_log = self.directory / "env.json"

    def tearDown(self):
        self.temporary.cleanup()

    def run_diagnostic(self, payload=b"[]", *, scenario="payload", arguments=(), profile=True):
        self.payload_file.write_bytes(payload)
        self.argv_log.write_text("")
        self.env_log.write_text("")
        environment = os.environ.copy()
        environment.update(
            {
                "AIOPS_TEST_MODE": "fixture",
                "AIOPS_TEST_OPENSTACK_BIN": str(self.fake_openstack),
                "AIOPS_FIXTURE_SCENARIO": scenario,
                "AIOPS_FIXTURE_PAYLOAD_FILE": str(self.payload_file),
                "AIOPS_TEST_ARGV_LOG": str(self.argv_log),
                "AIOPS_TEST_ENV_LOG": str(self.env_log),
                "OS_CLOUD": DIAGNOSTIC.OPERATOR_READER_PROFILE,
                "OS_CLIENT_CONFIG_FILE": DIAGNOSTIC.OPERATOR_READER_CONFIG,
                "OS_PASSWORD": "fixture-secret-must-not-be-inherited",
                "OS_TOKEN": "fixture-token-must-not-be-inherited",
            }
        )
        if not profile:
            environment.pop("OS_CLOUD", None)
            environment.pop("OS_CLIENT_CONFIG_FILE", None)
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *arguments],
            check=False,
            capture_output=True,
            env=environment,
        )

    @staticmethod
    def document(result):
        return json.loads(result.stdout)

    def test_fixed_read_projects_minimized_fields_and_argv(self):
        payload = json.dumps(
            [
                {
                    "agent_type": "L3 agent",
                    "host": "compute-b.example",
                    "alive": False,
                    "admin_state_up": True,
                    "created_at": "2025-01-02T00:00:00Z",
                    "updated_at": "2025-01-02T01:00:00Z",
                    "heartbeat_timestamp": None,
                    "id": "agent-2",
                    "configuration": {"password": "fixture-secret"},
                },
                {
                    "agent_type": "DHCP agent",
                    "host": "compute-a.example",
                    "alive": True,
                    "admin_state_up": True,
                    "created_at": None,
                    "updated_at": None,
                    "heartbeat_timestamp": "2025-01-02T02:00:00Z",
                    "id": "agent-1",
                    "unexpected": "ignored-by-minimization",
                },
            ]
        ).encode()
        result = self.run_diagnostic(payload)

        self.assertEqual(result.returncode, 0)
        document = self.document(result)
        self.assertEqual(document["status"], "ok")
        agents = document["sections"][0]["data"]
        self.assertEqual([agent["agent_type"] for agent in agents], ["DHCP agent", "L3 agent"])
        self.assertEqual(agents[0]["host_label_or_redacted_host"], "***REDACTED***")
        self.assertEqual(
            set(agents[0]),
            {
                "agent_type",
                "host_label_or_redacted_host",
                "alive",
                "admin_state_up",
                "diagnostic_timestamps",
            },
        )
        self.assertEqual(json.loads(self.argv_log.read_text()), ["network", "agent", "list", "-f", "json"])
        child_environment = set(json.loads(self.env_log.read_text()))
        self.assertNotIn("OS_PASSWORD", child_environment)
        self.assertNotIn("OS_TOKEN", child_environment)
        self.assertIn("OS_CLOUD", child_environment)
        self.assertIn("OS_CLIENT_CONFIG_FILE", child_environment)

    def test_deterministic_record_limit_and_ordering(self):
        records = [
            {
                "agent_type": f"agent-{index:02d}",
                "host": f"compute-{index:02d}",
                "alive": True,
                "admin_state_up": True,
                "created_at": None,
                "updated_at": None,
                "heartbeat_timestamp": None,
            }
            for index in reversed(range(55))
        ]
        result = self.run_diagnostic(json.dumps(records).encode())

        self.assertEqual(result.returncode, 0)
        document = self.document(result)
        section = document["sections"][0]
        self.assertTrue(section["truncated"])
        self.assertEqual(len(section["data"]), DIAGNOSTIC.RECORD_LIMIT)
        self.assertEqual(section["data"][0]["agent_type"], "agent-00")
        self.assertEqual(section["data"][-1]["agent_type"], "agent-49")

    def test_byte_limit_is_enforced_by_deterministic_truncation(self):
        records = [
            {
                "agent_type": f"agent-{index:02d}-" + ("x" * 200),
                "host": f"compute-{index:02d}",
                "alive": True,
                "admin_state_up": True,
                "created_at": "2025-01-02T00:00:00Z" * 5,
                "updated_at": "2025-01-02T01:00:00Z" * 5,
                "heartbeat_timestamp": "2025-01-02T02:00:00Z" * 5,
            }
            for index in range(DIAGNOSTIC.RECORD_LIMIT)
        ]
        result = self.run_diagnostic(json.dumps(records).encode())

        self.assertEqual(result.returncode, 0)
        self.assertLessEqual(len(result.stdout.rstrip(b"\n")), DIAGNOSTIC.OUTPUT_MAX_BYTES)
        self.assertTrue(self.document(result)["sections"][0]["truncated"])

    def test_secret_like_host_and_agent_values_are_redacted(self):
        payload = json.dumps(
            [
                {
                    "agent_type": "agent-token-canary",
                    "host": "password-canary.example",
                    "alive": True,
                    "admin_state_up": True,
                    "created_at": None,
                    "updated_at": None,
                    "heartbeat_timestamp": None,
                }
            ]
        ).encode()
        result = self.run_diagnostic(payload)

        self.assertEqual(result.returncode, 0)
        serialized = result.stdout.decode()
        self.assertNotIn("password-canary", serialized)
        self.assertNotIn("agent-token-canary", serialized)
        self.assertEqual(
            self.document(result)["sections"][0]["data"][0]["agent_type"],
            "***REDACTED***",
        )

    def test_missing_profile_is_unavailable_without_read(self):
        result = self.run_diagnostic(profile=False)

        self.assertEqual(result.returncode, 4)
        document = self.document(result)
        self.assertEqual(document["status"], "unavailable")
        self.assertEqual(document["error"]["class"], "profile_missing_or_revoked")
        self.assertEqual(self.argv_log.read_text(), "")

    def test_policy_denial_is_normalized_unavailable(self):
        result = self.run_diagnostic(scenario="failure")

        self.assertEqual(result.returncode, 4)
        document = self.document(result)
        self.assertEqual(document["status"], "unavailable")
        self.assertEqual(document["error"]["class"], "policy_denied")

    def test_malformed_json_and_invalid_utf8_fail_closed(self):
        malformed = self.run_diagnostic(b"{not-json\n")
        invalid_utf8 = self.run_diagnostic(scenario="invalid_utf8")

        self.assertEqual(malformed.returncode, 4)
        self.assertEqual(self.document(malformed)["error"]["class"], "output_decode_error")
        self.assertEqual(invalid_utf8.returncode, 4)
        self.assertEqual(self.document(invalid_utf8)["error"]["class"], "invalid_utf8")

    def test_input_byte_limit_stops_process_output(self):
        result = self.run_diagnostic(b"x" * (DIAGNOSTIC.INPUT_MAX_BYTES + 1))

        self.assertEqual(result.returncode, 4)
        self.assertEqual(self.document(result)["error"]["class"], "output_limit_exceeded")

    def test_unexpected_output_fields_are_rejected(self):
        document = DIAGNOSTIC._success_document([], False)
        document["sections"][0]["data"].append(
            {
                "agent_type": "agent",
                "host_label_or_redacted_host": "***REDACTED***",
                "alive": True,
                "admin_state_up": True,
                "diagnostic_timestamps": {
                    "created_at": None,
                    "updated_at": None,
                    "heartbeat_timestamp": None,
                },
                "unexpected": "value",
            }
        )

        with self.assertRaises(DIAGNOSTIC.DiagnosticFailure) as failure:
            DIAGNOSTIC.validate_document(document)
        self.assertEqual(failure.exception.error_class, "unexpected_field")

    def test_arguments_are_not_public_parameters(self):
        result = self.run_diagnostic(arguments=("--host", "compute-1"))

        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.document(result)["error"]["class"], "invalid_input")
        self.assertEqual(self.argv_log.read_text(), "")

    def test_source_is_registered_and_read_only(self):
        source = SCRIPT_PATH.read_text()
        defaults = SCRIPT_PATH.parents[3] / "defaults/main.yml"
        registry = SCRIPT_PATH.parents[4] / "ai_ops_assistant_tool_runner/files/scripts/tool_runner/tool_registry.json"

        self.assertIn('FIXED_OPENSTACK_ARGV = ("network", "agent", "list", "-f", "json")', source)
        self.assertIn("shell=False", source)
        self.assertNotIn("shell=True", source)
        self.assertNotIn("os.system(", source)
        self.assertNotIn("security group create", source)
        self.assertNotIn("network agent set", source)
        self.assertIn("neutron_agent_health", defaults.read_text())
        self.assertIn("neutron_agent_health", registry.read_text())
        self.assertEqual(stat.S_IMODE(SCRIPT_PATH.stat().st_mode), 0o755)

    def test_unavailable_classes_are_declared(self):
        source = SCRIPT_PATH.read_text()
        for error_class in (
            "profile_missing_or_revoked",
            "approved_optional_capability_absent",
            "service_unavailable",
            "catalog_missing",
            "connectivity_error",
            "unsupported_deployment_state",
        ):
            self.assertIn(error_class, source)


if __name__ == "__main__":
    unittest.main()
