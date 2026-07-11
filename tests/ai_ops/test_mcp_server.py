import asyncio
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mcp import types


REPO_ROOT = Path(__file__).resolve().parents[2]
MCP_SERVER_PATH = (
    REPO_ROOT
    / "ansible/ai_ops_runtime/roles/assistant_runtime/files/mcp/aiops_mcp_server.py"
)


def load_mcp_server_module():
    spec = importlib.util.spec_from_file_location("aiops_mcp_server", MCP_SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestMCPServerStub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server_module = load_mcp_server_module()

    def low_risk_policy(self):
        return {
            "tool_allowlist": [self.server_module.INITIAL_MCP_TOOL_NAME],
            "enabled_risk_levels": [self.server_module.LOW_READONLY_PROJECT_RISK],
        }

    def project_summary_tool(self):
        return {
            "name": self.server_module.INITIAL_MCP_TOOL_NAME,
            "description": "List project-visible diagnostic resources.",
            "credential_profile": "aiops-project-reader",
            "risk_level": self.server_module.LOW_READONLY_PROJECT_RISK,
            "available": True,
            "arguments": [],
        }

    def low_risk_registry(self):
        return {
            "policy": {"forbidden_capabilities": ["generic_shell"]},
            "tools": [self.project_summary_tool()],
        }

    def make_paths(self, policy=None, registry=None):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        policy_path = Path(tempdir.name) / "mcp_policy.json"
        registry_path = Path(tempdir.name) / "tool_registry.json"
        policy = self.low_risk_policy() if policy is None else policy
        registry = self.low_risk_registry() if registry is None else registry
        policy_path.write_text(json.dumps(policy), encoding="utf-8")
        registry_path.write_text(json.dumps(registry), encoding="utf-8")
        return self.server_module.AdapterPaths(policy_path, registry_path)

    def test_default_adapter_paths_are_fixed_runtime_paths(self):
        paths = self.server_module.default_adapter_paths()

        self.assertEqual(
            paths.policy_path,
            Path("/opt/openstack-ai-ops/mcp/mcp_policy.json"),
        )
        self.assertEqual(
            paths.registry_path,
            Path("/opt/openstack-ai-ops/scripts/tool_runner/tool_registry.json"),
        )

    def test_loaders_require_json_objects(self):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        invalid_path = Path(tempdir.name) / "invalid.json"
        invalid_path.write_text("[]", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "MCP policy.*JSON object"):
            self.server_module.load_mcp_policy(invalid_path)
        with self.assertRaisesRegex(ValueError, "runner registry.*JSON object"):
            self.server_module.load_runner_registry(invalid_path)
        with self.assertRaisesRegex(ValueError, "unable to load MCP policy"):
            self.server_module.load_mcp_policy(Path(tempdir.name) / "missing.json")

    def test_create_server_discovers_one_registry_derived_tool(self):
        server = self.server_module.create_server(self.make_paths())
        result = asyncio.run(
            server.request_handlers[types.ListToolsRequest](types.ListToolsRequest())
        )

        self.assertIn(types.CallToolRequest, server.request_handlers)
        self.assertEqual([tool.name for tool in result.root.tools], ["project_resource_summary"])
        self.assertEqual(result.root.tools[0].inputSchema, {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        })
        self.assertIn("read-only", result.root.tools[0].description.lower())

    def test_schema_derives_public_arguments_without_fixed_arguments(self):
        tool = self.project_summary_tool()
        tool["fixed_arguments"] = ["summary"]
        tool["arguments"] = [
            {
                "name": "server_identifier",
                "position": 1,
                "required": True,
                "validation": "safe_identifier_pattern",
                "pattern": "^[A-Za-z0-9._:-]+$",
                "description": "Reviewed server name or ID.",
            }
        ]

        schema = self.server_module.build_mcp_tool_schema(tool)

        self.assertEqual(schema["inputSchema"]["required"], ["server_identifier"])
        self.assertEqual(
            schema["inputSchema"]["properties"]["server_identifier"]["pattern"],
            "^[A-Za-z0-9._:-]+$",
        )
        self.assertFalse(schema["inputSchema"]["additionalProperties"])
        self.assertNotIn("fixed_arguments", schema["inputSchema"]["properties"])

    def test_exposure_rejects_unknown_unavailable_and_disabled_risk_tools(self):
        with self.assertRaisesRegex(ValueError, "unknown tool"):
            self.server_module.list_exposed_tools(
                self.low_risk_registry(),
                {
                    "tool_allowlist": ["unknown_tool"],
                    "enabled_risk_levels": [
                        self.server_module.LOW_READONLY_PROJECT_RISK
                    ],
                },
            )

        unavailable_registry = self.low_risk_registry()
        unavailable_registry["tools"][0]["available"] = False
        with self.assertRaisesRegex(ValueError, "unavailable tool"):
            self.server_module.list_exposed_tools(
                unavailable_registry,
                self.low_risk_policy(),
            )

        with self.assertRaisesRegex(ValueError, "does not enable tool risk"):
            self.server_module.list_exposed_tools(
                self.low_risk_registry(),
                {
                    "tool_allowlist": [self.server_module.INITIAL_MCP_TOOL_NAME],
                    "enabled_risk_levels": ["high_readonly_restricted_host_scope"],
                },
            )

    def test_registry_rejects_duplicate_and_forbidden_capabilities(self):
        duplicate_registry = self.low_risk_registry()
        duplicate_registry["tools"].append(self.project_summary_tool())
        with self.assertRaisesRegex(ValueError, "duplicate tool"):
            self.server_module.validate_runner_registry(duplicate_registry)

        forbidden_registry = self.low_risk_registry()
        forbidden_registry["tools"][0]["capabilities"] = ["generic_shell"]
        with self.assertRaisesRegex(ValueError, "forbidden capability"):
            self.server_module.validate_runner_registry(forbidden_registry)

    def test_unavailable_tool_call_fails_closed_without_echoing_arguments(self):
        result = asyncio.run(
            self.server_module.unavailable_tool_call(
                "project_resource_summary",
                {"api_token": "sensitive-value"},
            )
        )

        self.assertTrue(result.isError)
        self.assertEqual(len(result.content), 1)
        self.assertEqual(
            result.content[0].text,
            self.server_module.ADAPTER_UNAVAILABLE_MESSAGE,
        )
        self.assertNotIn("sensitive-value", result.content[0].text)

    def test_run_server_uses_stdio_lifecycle_only(self):
        class FakeStdio:
            async def __aenter__(self):
                return "read-stream", "write-stream"

            async def __aexit__(self, exc_type, exc_value, traceback):
                return False

        class FakeServer:
            def __init__(self):
                self.run_args = None

            def create_initialization_options(self):
                return "initialization-options"

            async def run(self, read_stream, write_stream, initialization_options):
                self.run_args = (read_stream, write_stream, initialization_options)

        fake_server = FakeServer()
        with (
            mock.patch.object(
                self.server_module,
                "create_server",
                return_value=fake_server,
            ),
            mock.patch.object(
                self.server_module,
                "stdio_server",
                return_value=FakeStdio(),
            ),
        ):
            asyncio.run(self.server_module.run_server(self.make_paths()))

        self.assertEqual(
            fake_server.run_args,
            ("read-stream", "write-stream", "initialization-options"),
        )

    def test_source_does_not_add_network_transport_or_runner_execution(self):
        source = MCP_SERVER_PATH.read_text(encoding="utf-8")

        self.assertIn("from mcp.server.lowlevel import Server", source)
        self.assertIn("from mcp.server.stdio import stdio_server", source)
        self.assertNotIn("subprocess", source)
        self.assertNotIn("uvicorn", source)
        self.assertNotIn("streamable", source)
        self.assertNotIn("from mcp.server.sse", source)


if __name__ == "__main__":
    unittest.main()
