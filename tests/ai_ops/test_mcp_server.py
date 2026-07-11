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

    def fake_runner_source(self, payload=None, raw_stdout=None):
        if raw_stdout is not None:
            return f"import sys\nsys.stdout.write({raw_stdout!r})\n"

        payload = {
            "tool": self.server_module.INITIAL_MCP_TOOL_NAME,
            "status": "ok",
            "arguments": {},
            "exit_code": 0,
            "stdout": "reviewed summary",
            "stderr": "",
            "duration_ms": 12,
            "truncated": False,
            "timestamp": "2026-07-11T00:00:00Z",
            **(payload or {}),
        }
        return (
            "import json\n"
            "import sys\n"
            f"payload = {payload!r}\n"
            "payload['request_id'] = sys.argv[sys.argv.index('--request-id') + 1]\n"
            "sys.stdout.write(json.dumps(payload, sort_keys=True) + '\\n')\n"
        )

    def make_paths(self, policy=None, registry=None, payload=None, raw_stdout=None):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        policy_path = Path(tempdir.name) / "mcp_policy.json"
        registry_path = Path(tempdir.name) / "tool_registry.json"
        runner_path = Path(tempdir.name) / "reviewed_runner.py"
        audit_path = Path(tempdir.name) / "tool-runner.jsonl"
        policy = self.low_risk_policy() if policy is None else policy
        registry = self.low_risk_registry() if registry is None else registry
        policy_path.write_text(json.dumps(policy), encoding="utf-8")
        registry_path.write_text(json.dumps(registry), encoding="utf-8")
        runner_path.write_text(
            self.fake_runner_source(payload, raw_stdout),
            encoding="utf-8",
        )
        return self.server_module.AdapterPaths(
            policy_path,
            registry_path,
            Path(sys.executable),
            runner_path,
            audit_path,
        )

    def call_tool(self, paths, arguments=None):
        server = self.server_module.create_server(paths)
        request = types.CallToolRequest(
            params=types.CallToolRequestParams(
                name=self.server_module.INITIAL_MCP_TOOL_NAME,
                arguments=arguments,
            )
        )
        result = asyncio.run(server.request_handlers[types.CallToolRequest](request))
        return result.root

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
        self.assertEqual(
            paths.python_path,
            Path("/opt/openstack-ai-ops/.venv/bin/python"),
        )
        self.assertEqual(
            paths.runner_path,
            Path("/opt/openstack-ai-ops/scripts/tool_runner/aiops_tool_runner.py"),
        )
        self.assertEqual(
            paths.audit_path,
            Path("/opt/openstack-ai-ops/audit/tool-runner.jsonl"),
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

    def test_project_summary_call_executes_fake_runner_and_preserves_envelope(self):
        result = self.call_tool(self.make_paths())

        self.assertFalse(result.isError)
        self.assertEqual(result.structuredContent["tool"], "project_resource_summary")
        self.assertEqual(result.structuredContent["status"], "ok")
        self.assertEqual(result.structuredContent["stdout"], "reviewed summary")
        self.assertTrue(
            result.structuredContent["request_id"].startswith(
                self.server_module.MCP_REQUEST_ID_PREFIX
            )
        )
        self.assertEqual(json.loads(result.content[0].text), result.structuredContent)

    def test_runner_timeout_envelope_is_returned_as_an_mcp_error(self):
        result = self.call_tool(
            self.make_paths(
                payload={
                    "status": "timeout",
                    "exit_code": None,
                    "stderr": "tool execution exceeded timeout",
                }
            )
        )

        self.assertTrue(result.isError)
        self.assertEqual(result.structuredContent["status"], "timeout")

    def test_runner_error_envelope_is_returned_as_an_mcp_error(self):
        result = self.call_tool(
            self.make_paths(
                payload={
                    "status": "error",
                    "exit_code": 1,
                    "stderr": "failed to write audit event: fixture failure",
                }
            )
        )

        self.assertTrue(result.isError)
        self.assertEqual(result.structuredContent["status"], "error")
        self.assertEqual(
            result.structuredContent["stderr"],
            "failed to write audit event: fixture failure",
        )

    def test_runner_call_uses_fixed_argv_and_origin_metadata(self):
        request_id = "mcp-stdio-fixed-request"
        envelope = {
            "tool": "project_resource_summary",
            "status": "ok",
            "arguments": {},
            "exit_code": 0,
            "stdout": "summary",
            "stderr": "",
            "duration_ms": 1,
            "truncated": False,
            "timestamp": "2026-07-11T00:00:00Z",
            "request_id": request_id,
        }

        class FakeProcess:
            returncode = 99

            async def communicate(self):
                return json.dumps(envelope).encode("utf-8") + b"\n", b""

        paths = self.make_paths()
        with (
            mock.patch.object(
                self.server_module,
                "new_request_id",
                return_value=request_id,
            ),
            mock.patch.object(
                self.server_module.asyncio,
                "create_subprocess_exec",
                new=mock.AsyncMock(return_value=FakeProcess()),
            ) as create_subprocess,
        ):
            result = self.call_tool(paths)

        self.assertFalse(result.isError)
        self.assertEqual(
            create_subprocess.await_args.args,
            (
                str(paths.python_path),
                str(paths.runner_path),
                "project_resource_summary",
                "--registry",
                str(paths.registry_path),
                "--audit-path",
                str(paths.audit_path),
                "--request-id",
                request_id,
                "--client-id",
                self.server_module.MCP_AUDIT_CLIENT_ID,
                "--transport",
                self.server_module.MCP_AUDIT_TRANSPORT,
            ),
        )
        self.assertEqual(
            create_subprocess.await_args.kwargs,
            {
                "stdout": self.server_module.subprocess.PIPE,
                "stderr": self.server_module.subprocess.PIPE,
            },
        )

    def test_runner_protocol_rejects_malformed_multiple_and_mismatched_envelopes(self):
        request_id = "mcp-stdio-protocol-test"
        envelope = {
            "tool": "project_resource_summary",
            "status": "ok",
            "arguments": {},
            "exit_code": 0,
            "stdout": "summary",
            "stderr": "",
            "duration_ms": 1,
            "truncated": False,
            "timestamp": "2026-07-11T00:00:00Z",
            "request_id": request_id,
        }
        cases = [
            "not-json\n",
            f"{json.dumps(envelope)}\n{{}}\n",
            f"{json.dumps({**envelope, 'request_id': 'wrong-request'})}\n",
        ]

        for raw_stdout in cases:
            with self.subTest(raw_stdout=raw_stdout):
                with self.assertRaisesRegex(
                    self.server_module.RunnerProtocolError,
                    "runner",
                ):
                    asyncio.run(
                        self.server_module.invoke_runner(
                            "project_resource_summary",
                            {},
                            request_id,
                            self.make_paths(raw_stdout=raw_stdout),
                            1,
                        )
                    )

    def test_cancellation_terminates_the_adapter_owned_runner(self):
        class BlockingProcess:
            def __init__(self):
                self.returncode = None
                self.terminated = False

            async def communicate(self):
                await asyncio.Event().wait()

            def terminate(self):
                self.terminated = True
                self.returncode = -15

            async def wait(self):
                return self.returncode

        async def cancel_call():
            process = BlockingProcess()
            with mock.patch.object(
                self.server_module.asyncio,
                "create_subprocess_exec",
                new=mock.AsyncMock(return_value=process),
            ):
                task = asyncio.create_task(
                    self.server_module.invoke_runner(
                        "project_resource_summary",
                        {},
                        "mcp-stdio-cancel-test",
                        self.make_paths(),
                        1,
                    )
                )
                await asyncio.sleep(0)
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
            self.assertTrue(process.terminated)

        asyncio.run(cancel_call())

    def test_argument_bearing_call_remains_unavailable_without_runner_execution(self):
        result = self.call_tool(
            self.make_paths(),
            {"server_identifier": "server-01"},
        )

        self.assertTrue(result.isError)
        self.assertEqual(
            result.content[0].text,
            self.server_module.ADAPTER_UNAVAILABLE_MESSAGE,
        )

    def test_source_uses_fixed_subprocess_execution_without_network_transport(self):
        source = MCP_SERVER_PATH.read_text(encoding="utf-8")

        self.assertIn("from mcp.server.lowlevel import Server", source)
        self.assertIn("from mcp.server.stdio import stdio_server", source)
        self.assertIn("asyncio.create_subprocess_exec", source)
        self.assertNotIn("subprocess.run", source)
        self.assertNotIn("shell=True", source)
        self.assertNotIn("uvicorn", source)
        self.assertNotIn("streamable", source)
        self.assertNotIn("from mcp.server.sse", source)


if __name__ == "__main__":
    unittest.main()
