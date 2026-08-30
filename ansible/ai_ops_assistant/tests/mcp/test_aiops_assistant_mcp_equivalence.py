import asyncio
import copy
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
CATALOG_PATH = SERVER_PATH.with_name("mcp_resource_catalog.json")
SPEC = importlib.util.spec_from_loader(
    "aiops_assistant_mcp_server_equivalence",
    SourceFileLoader("aiops_assistant_mcp_server_equivalence", str(SERVER_PATH)),
)
SERVER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SERVER
SPEC.loader.exec_module(SERVER)


class ThreeToolAndResourceEquivalenceTest(unittest.TestCase):
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

    def runner_envelope(self, tool, arguments):
        return {
            "schema_version": "1.0",
            "tool": tool,
            "status": "ok",
            "arguments": arguments,
            "exit_code": 0,
            "data": {"tool": tool},
            "stdout": None,
            "stderr": None,
            "error": None,
            "duration_ms": 12,
            "truncated": False,
            "timestamp": "2030-01-02T03:04:05.678Z",
            "correlation_id": "00000000-0000-4000-8000-000000000001",
        }

    def test_projected_initial_tools_match_approved_registry_subset(self):
        registry_path = (
            Path(__file__).parents[2]
            / "roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/tool_registry.json"
        )
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry_tools = {
            tool["name"]: tool
            for tool in registry["tools"]
            if tool["name"] in SERVER.INITIAL_TOOL_NAMES
        }
        projected = SERVER.project_initial_tool_definitions()

        self.assertEqual(
            [tool["name"] for tool in projected], list(SERVER.INITIAL_TOOL_NAMES)
        )
        for tool in projected:
            source = registry_tools[tool["name"]]
            self.assertEqual(tool["description"], source["description"])
        self.assertEqual(
            projected[1]["inputSchema"], SERVER.SERVER_BASIC_INFO_INPUT_SCHEMA
        )
        self.assertEqual(
            projected[2]["inputSchema"], SERVER.SERVER_NETWORK_INFO_INPUT_SCHEMA
        )

    def test_both_server_tools_use_exact_argv_timeout_and_envelope(self):
        calls = []

        def fake_runner(argv, **kwargs):
            calls.append((argv, kwargs))
            tool = argv[2]
            arguments = {"server_identifier": argv[4].split("=", 1)[1]}
            envelope = self.runner_envelope(tool, arguments)
            return subprocess.CompletedProcess(
                argv, 0, stdout=json.dumps(envelope).encode("utf-8"), stderr=b""
            )

        for tool, handler in (
            (SERVER.SERVER_BASIC_INFO, SERVER.handle_authenticated_server_basic_info),
            (
                SERVER.SERVER_NETWORK_INFO,
                SERVER.handle_authenticated_server_network_info,
            ),
        ):
            with self.subTest(tool=tool):
                result = handler(
                    SERVER.EXPECTED_PRINCIPAL_URI,
                    {"server_identifier": "server-01"},
                    runner=fake_runner,
                )
                self.assertFalse(result.isError)
                self.assertEqual(result.structuredContent["tool"], tool)

        self.assertEqual(
            [call[0] for call in calls],
            [
                [
                    str(SERVER.RUNNER_PYTHON),
                    str(SERVER.RUNNER_SCRIPT),
                    SERVER.SERVER_BASIC_INFO,
                    "--arg",
                    "server_identifier=server-01",
                ],
                [
                    str(SERVER.RUNNER_PYTHON),
                    str(SERVER.RUNNER_SCRIPT),
                    SERVER.SERVER_NETWORK_INFO,
                    "--arg",
                    "server_identifier=server-01",
                ],
            ],
        )
        self.assertEqual([call[1]["timeout"] for call in calls], [30, 45])
        self.assertTrue(all(call[1]["shell"] is False for call in calls))

    def test_authenticated_fixture_runs_project_then_same_identifier_server_workflow(
        self,
    ):
        calls = []

        def fake_runner(argv, **kwargs):
            calls.append((argv, kwargs))
            tool = argv[2]
            arguments = (
                {}
                if tool == SERVER.PROJECT_RESOURCE_SUMMARY
                else {"server_identifier": argv[4].split("=", 1)[1]}
            )
            envelope = self.runner_envelope(tool, arguments)
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout=json.dumps(envelope).encode("utf-8"),
                stderr=b"fixture-secret",
            )

        principal = SERVER.EXPECTED_PRINCIPAL_URI
        project_result = SERVER.handle_authenticated_project_resource_summary(
            principal, {}, runner=fake_runner
        )
        basic_result = SERVER.handle_authenticated_server_basic_info(
            principal, {"server_identifier": "server-01"}, runner=fake_runner
        )
        network_result = SERVER.handle_authenticated_server_network_info(
            principal, {"server_identifier": "server-01"}, runner=fake_runner
        )

        for result in (project_result, basic_result, network_result):
            self.assertFalse(result.isError)
            self.assertNotIn("fixture-secret", result.content[0].text)
        self.assertEqual(
            [call[0][2] for call in calls],
            [
                SERVER.PROJECT_RESOURCE_SUMMARY,
                SERVER.SERVER_BASIC_INFO,
                SERVER.SERVER_NETWORK_INFO,
            ],
        )
        self.assertEqual(
            calls[1][0][4],
            "server_identifier=server-01",
        )
        self.assertEqual(
            calls[2][0][4],
            "server_identifier=server-01",
        )
        self.assertEqual([call[1]["timeout"] for call in calls], [45, 30, 45])
        self.assertTrue(all(call[1]["shell"] is False for call in calls))
        self.assertEqual(
            [
                result.structuredContent["arguments"]
                for result in (
                    project_result,
                    basic_result,
                    network_result,
                )
            ],
            [
                {},
                {"server_identifier": "server-01"},
                {"server_identifier": "server-01"},
            ],
        )

    def test_authenticated_fixture_exposes_no_prompt_or_remediation_surface(self):
        config = SERVER.NetworkMCPConfig.from_mapping(self.valid_configuration())
        server = SERVER.create_authenticated_three_tool_server(
            config,
            SERVER.EXPECTED_PRINCIPAL_URI,
            catalog=SERVER.load_resource_catalog(CATALOG_PATH),
            runner=lambda *args, **kwargs: None,
        )
        listed = asyncio.run(server.request_handlers[types.ListToolsRequest](None))
        self.assertEqual(
            [tool.name for tool in listed.root.tools], list(SERVER.INITIAL_TOOL_NAMES)
        )
        for request_type in (types.ListPromptsRequest, types.GetPromptRequest):
            self.assertNotIn(request_type, server.request_handlers)
        for forbidden in (
            "network_diagnosis",
            "volume_diagnosis",
            "fix_it",
            "shell",
            "ssh",
            "sudo",
            "remediation",
        ):
            self.assertNotIn(forbidden, [tool.name for tool in listed.root.tools])

    def test_invalid_initial_requests_and_phase06_tools_never_spawn(self):
        calls = []

        def fake_runner(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("runner must not be called")

        invalid_requests = [
            (SERVER.SERVER_BASIC_INFO, {}),
            (SERVER.SERVER_NETWORK_INFO, {"server_identifier": "../etc/passwd"}),
            (SERVER.SERVER_BASIC_INFO, {"server_identifier": "x", "extra": "y"}),
            (SERVER.SERVER_NETWORK_INFO, {"server_identifier": "x" * 256}),
            ("neutron_agent_health", {}),
        ]
        for tool, arguments in invalid_requests:
            with (
                self.subTest(tool=tool, arguments=arguments),
                self.assertRaises(SERVER.RequestValidationError),
            ):
                SERVER.invoke_fixed_runner(tool, arguments, runner=fake_runner)
        self.assertEqual(calls, [])

    def test_authenticated_full_server_exposes_only_three_tools_and_catalog(self):
        config = SERVER.NetworkMCPConfig.from_mapping(self.valid_configuration())
        catalog = SERVER.load_resource_catalog(CATALOG_PATH)
        server = SERVER.create_authenticated_three_tool_server(
            config,
            SERVER.EXPECTED_PRINCIPAL_URI,
            catalog=catalog,
            runner=lambda *args, **kwargs: None,
        )

        listed_tools = asyncio.run(
            server.request_handlers[types.ListToolsRequest](None)
        )
        self.assertEqual(
            [tool.name for tool in listed_tools.root.tools],
            list(SERVER.INITIAL_TOOL_NAMES),
        )
        self.assertNotIn(
            "neutron_agent_health", [tool.name for tool in listed_tools.root.tools]
        )
        self.assertNotIn(types.ListResourceTemplatesRequest, server.request_handlers)
        self.assertNotIn(types.GetPromptRequest, server.request_handlers)

        listed_resources = asyncio.run(
            server.request_handlers[types.ListResourcesRequest](None)
        )
        self.assertEqual(
            [str(resource.uri) for resource in listed_resources.root.resources],
            list(SERVER.REVIEWED_RESOURCE_METADATA),
        )

        uri = next(iter(SERVER.REVIEWED_RESOURCE_METADATA))
        request = types.ReadResourceRequest(params={"uri": uri})
        read_result = asyncio.run(
            server.request_handlers[types.ReadResourceRequest](request)
        )
        self.assertEqual(read_result.root.contents[0].mimeType, "text/markdown")
        self.assertIn("Diagnostic Safety Policy", read_result.root.contents[0].text)

    def test_resource_reads_are_pure_allowlisted_lookups(self):
        catalog = SERVER.load_resource_catalog(CATALOG_PATH)
        with mock.patch.object(
            Path, "read_bytes", side_effect=AssertionError("filesystem read")
        ):
            with self.assertRaises(SERVER.ResourceCatalogError):
                SERVER.read_curated_resource("file:///etc/passwd", catalog)
            contents = SERVER.read_curated_resource(
                "aiops://policy/diagnostic-safety", catalog
            )
        self.assertIn("diagnostic-only", contents[0].content)

    def test_catalog_rejects_duplicate_fields_unknown_fields_and_secret_canaries(self):
        catalog = SERVER.load_resource_catalog(CATALOG_PATH)

        unknown_field = copy.deepcopy(catalog)
        unknown_field["unexpected"] = True
        with self.assertRaises(SERVER.ResourceCatalogError):
            SERVER.validate_resource_catalog(unknown_field)

        secret_catalog = copy.deepcopy(catalog)
        secret_catalog["resources"][0]["content"] = "token: do-not-ship"
        with self.assertRaises(SERVER.ResourceCatalogError):
            SERVER.validate_resource_catalog(secret_catalog)

        duplicate_json = (
            '{"schema_version":1,"schema_version":1,'
            '"catalog_name":"ai-ops-assistant-mcp-resources-steps-01-04",'
            '"resources":[]}'
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text(duplicate_json, encoding="utf-8")
            with self.assertRaises(SERVER.ResourceCatalogError):
                SERVER.load_resource_catalog(path)


if __name__ == "__main__":
    unittest.main()
