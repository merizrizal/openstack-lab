import asyncio
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest import mock

from mcp import types

SERVER_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_mcp/files/mcp/aiops_assistant_mcp_server.py"
)
SPEC = importlib.util.spec_from_loader(
    "aiops_assistant_mcp_server",
    SourceFileLoader("aiops_assistant_mcp_server", str(SERVER_PATH)),
)
SERVER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SERVER
SPEC.loader.exec_module(SERVER)


class DisabledNetworkMCPServerTest(unittest.TestCase):
    def valid_configuration(self):
        return {
            "schema_version": 1,
            "transport": "streamable-http",
            "bind_interface": "eth0",
            "bind_address": "192.168.121.21",
            "port": 8443,
            "endpoint_path": "/mcp",
            "allowed_source_cidrs": ["192.168.121.0/24"],
            "tls_certificate_path": "/etc/ai-ops-assistant/mcp/tls/server.crt",
            "tls_private_key_path": "/etc/ai-ops-assistant/mcp/tls/server.key",
            "tls_client_ca_path": "/etc/ai-ops-assistant/mcp/tls/client-ca.crt",
            "tls_client_crl_path": "/etc/ai-ops-assistant/mcp/tls/client-ca.crl",
            "authorized_principal_uri": "spiffe://openstack-lab/mcp/mcp-internal-reader",
            "max_header_bytes": 8192,
            "max_request_body_bytes": 65536,
            "max_response_body_bytes": 262144,
            "max_concurrent_sessions": 4,
            "max_concurrent_runner_children": 1,
            "requests_per_minute": 10,
            "request_burst": 2,
            "session_idle_seconds": 300,
            "request_deadline_seconds": 305,
        }

    def write_configuration(self, payload):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "config.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        self.addCleanup(temporary.cleanup)
        return path

    def valid_runner_envelope(self, status="ok"):
        return {
            "schema_version": "1.0",
            "tool": "project_resource_summary",
            "status": status,
            "arguments": {},
            "exit_code": 0 if status == "ok" else 1,
            "data": {"sections": []} if status == "ok" else None,
            "stdout": None,
            "stderr": None,
            "error": (
                None
                if status == "ok"
                else {
                    "class": "execution_error",
                    "message": "Diagnostic result failed.",
                }
            ),
            "duration_ms": 12,
            "truncated": False,
            "timestamp": "2030-01-02T03:04:05.678Z",
            "correlation_id": "00000000-0000-4000-8000-000000000001",
        }

    def test_configuration_is_exact_and_default_startup_is_disabled(self):
        path = self.write_configuration(self.valid_configuration())

        with mock.patch.object(SERVER, "DEFAULT_ENABLED", False), mock.patch.object(
            SERVER, "DEFAULT_EXPLICIT_ACTIVATION", False
        ), mock.patch.object(SERVER.uvicorn.Server, "run") as run:
            self.assertEqual(SERVER.main(["--config", str(path)]), 3)

        run.assert_not_called()
        config = SERVER.load_configuration(path)
        self.assertEqual(config.bind_address, "192.168.121.21")
        self.assertEqual(config.allowed_source_cidrs, ("192.168.121.0/24",))

    def test_missing_or_duplicate_configuration_fails_without_activation(self):
        missing_path = Path(tempfile.gettempdir()) / "mcp-config-does-not-exist.json"
        self.assertEqual(SERVER.main(["--config", str(missing_path)]), 2)

        payload = json.dumps(self.valid_configuration())[:-1]
        duplicate_path = self.write_configuration(self.valid_configuration())
        duplicate_path.write_text(payload + ', "port": 8443}', encoding="utf-8")
        with self.assertRaises(SERVER.ConfigurationError):
            SERVER.load_configuration(duplicate_path)

    def test_bind_scope_rejects_wildcard_and_alternate_address(self):
        config = SERVER.NetworkMCPConfig.from_mapping(self.valid_configuration())
        for address in ("0.0.0.0", "127.0.0.1", "192.168.121.22"):
            with self.subTest(address=address):
                changed = self.valid_configuration()
                changed["bind_address"] = address
                with self.assertRaises(SERVER.ConfigurationError):
                    SERVER.NetworkMCPConfig.from_mapping(changed)

    def test_authentication_and_schema_denials_do_not_invoke_runner(self):
        calls = []

        def fake_runner(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("runner must not be called")

        with self.assertRaises(SERVER.AuthenticationError):
            SERVER.handle_authenticated_project_resource_summary(
                "spiffe://openstack-lab/mcp/unknown", runner=fake_runner
            )
        with self.assertRaises(SERVER.RequestValidationError):
            SERVER.handle_authenticated_project_resource_summary(
                SERVER.EXPECTED_PRINCIPAL_URI,
                {"unexpected": "value"},
                runner=fake_runner,
            )
        with self.assertRaises(SERVER.RequestValidationError):
            SERVER.invoke_fixed_runner("server_basic_info", {}, runner=fake_runner)
        self.assertEqual(calls, [])

    def test_authorized_first_tool_uses_exact_runner_argv_and_maps_success(self):
        calls = []
        envelope = self.valid_runner_envelope()

        def fake_runner(argv, **kwargs):
            calls.append((argv, kwargs))
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout=json.dumps(envelope).encode("utf-8"),
                stderr=b"raw-secret",
            )

        result = SERVER.handle_authenticated_project_resource_summary(
            SERVER.EXPECTED_PRINCIPAL_URI, runner=fake_runner
        )

        self.assertEqual(
            calls[0][0],
            [
                "/opt/openstack-ai-ops-assistant/mcp/venv/bin/python",
                "/opt/openstack-ai-ops-assistant/scripts/tool_runner/aiops_tool_runner.py",
                "project_resource_summary",
            ],
        )
        self.assertEqual(
            calls[0][1],
            {
                "shell": False,
                "check": False,
                "capture_output": True,
                "timeout": 45,
            },
        )
        self.assertEqual(result.structuredContent, envelope)
        self.assertFalse(result.isError)
        self.assertEqual(
            result.content[0].text,
            json.dumps(
                envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        )
        self.assertNotIn("raw-secret", result.content[0].text)

    def test_runner_error_envelope_maps_to_mcp_error_without_raw_output(self):
        envelope = self.valid_runner_envelope("error")

        def fake_runner(argv, **kwargs):
            return subprocess.CompletedProcess(
                argv,
                1,
                stdout=json.dumps(envelope).encode("utf-8"),
                stderr=b"raw-secret",
            )

        result = SERVER.handle_authenticated_project_resource_summary(
            SERVER.EXPECTED_PRINCIPAL_URI, runner=fake_runner
        )

        self.assertTrue(result.isError)
        self.assertEqual(result.structuredContent["status"], "error")
        self.assertNotIn("raw-secret", result.content[0].text)

    def test_malformed_or_oversized_runner_envelopes_fail_closed(self):
        with self.assertRaises(SERVER.RunnerProtocolError):
            SERVER.decode_runner_envelope(b"{}")
        with self.assertRaises(SERVER.RunnerProtocolError):
            SERVER.decode_runner_envelope(b"x" * (SERVER.RUNNER_MAX_ENVELOPE_BYTES + 1))

    def test_authenticated_server_registers_initial_tools_and_resources(self):
        config = SERVER.NetworkMCPConfig.from_mapping(self.valid_configuration())
        catalog_path = (
            Path(__file__).parents[2]
            / "roles/ai_ops_assistant_mcp/files/mcp/mcp_resource_catalog.json"
        )
        server = SERVER.create_authenticated_first_tool_server(
            config,
            SERVER.EXPECTED_PRINCIPAL_URI,
            catalog=SERVER.load_resource_catalog(catalog_path),
            runner=lambda *args, **kwargs: None,
        )
        self.assertIn(types.ListToolsRequest, server.request_handlers)
        self.assertIn(types.CallToolRequest, server.request_handlers)
        self.assertIn(types.ListResourcesRequest, server.request_handlers)
        self.assertNotIn(types.ListResourceTemplatesRequest, server.request_handlers)

        listed = asyncio.run(server.request_handlers[types.ListToolsRequest](None))
        self.assertEqual(
            [tool.name for tool in listed.root.tools], list(SERVER.INITIAL_TOOL_NAMES)
        )
        self.assertEqual(
            listed.root.tools[1].inputSchema, SERVER.SERVER_BASIC_INFO_INPUT_SCHEMA
        )
        self.assertEqual(
            listed.root.tools[2].inputSchema, SERVER.SERVER_NETWORK_INFO_INPUT_SCHEMA
        )

    def test_low_level_server_has_no_tools_or_resources(self):
        config = SERVER.NetworkMCPConfig.from_mapping(self.valid_configuration())
        server = SERVER.create_mcp_server(config)
        self.assertEqual(server._tool_cache, {})
        self.assertNotIn(types.ListToolsRequest, server.request_handlers)
        self.assertNotIn(types.ListResourcesRequest, server.request_handlers)

    def test_transport_and_manager_are_constructed_without_listener(self):
        config = SERVER.NetworkMCPConfig.from_mapping(self.valid_configuration())
        server = SERVER.create_mcp_server(config)
        transport = SERVER.create_streamable_http_transport()
        manager = SERVER.create_session_manager(server, config)
        self.assertTrue(transport.is_json_response_enabled)
        self.assertFalse(manager.stateless)
        self.assertIsNone(manager.event_store)
        self.assertEqual(manager.session_idle_timeout, 300)

    def test_application_activation_gate_remains_closed(self):
        config = SERVER.NetworkMCPConfig.from_mapping(self.valid_configuration())
        with self.assertRaisesRegex(
            SERVER.NetworkMCPDisabledError, "authentication is not activated"
        ):
            SERVER.create_application(config, enabled=True, explicit_activation=True)


if __name__ == "__main__":
    unittest.main()
