import ast
import asyncio
import contextlib
import importlib.util
import io
import json
import sys
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest import mock

from mcp import types

SERVER_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_mcp_stdio/files/mcp_stdio/aiops_assistant_mcp_stdio_server.py"
)
REGISTRY_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/tool_registry.json"
)
CATALOG_PATH = SERVER_PATH.with_name("mcp_resource_catalog.json")
SPEC = importlib.util.spec_from_loader(
    "aiops_assistant_mcp_stdio_safety_integration",
    SourceFileLoader("aiops_assistant_mcp_stdio_safety_integration", str(SERVER_PATH)),
)
SERVER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SERVER
SPEC.loader.exec_module(SERVER)


class SafetyIntegrationTest(unittest.TestCase):
    def configuration(self):
        return SERVER.AdapterConfiguration(
            schema_version=1,
            transport="stdio",
            runtime_root=SERVER.RUNTIME_ROOT,
            adapter_path=SERVER.ADAPTER_PATH,
            resource_catalog_path=CATALOG_PATH,
            max_concurrent_runner_children=1,
            cleanup_grace_seconds=5,
        )

    def server(self, lifecycle=None):
        return SERVER.create_server(
            self.configuration(),
            fixed_registry_path=REGISTRY_PATH,
            lifecycle=lifecycle,
            catalog=SERVER.load_resource_catalog(CATALOG_PATH),
        )

    def runner_envelope(
        self,
        status="ok",
        tool=SERVER.PROJECT_RESOURCE_SUMMARY,
        arguments=None,
        correlation_id="00000000-0000-4000-8000-000000000001",
    ):
        arguments = {} if arguments is None else arguments
        return {
            "schema_version": "1.0",
            "tool": tool,
            "status": status,
            "arguments": arguments,
            "exit_code": SERVER.RUNNER_STATUS_EXIT_CODES[status],
            "data": {"sections": []} if status == "ok" else None,
            "stdout": None,
            "stderr": None,
            "error": (
                None
                if status == "ok"
                else {"class": "execution_error", "message": "safe message"}
            ),
            "duration_ms": 12,
            "truncated": status == "error",
            "timestamp": "2030-01-02T03:04:05.678Z",
            "correlation_id": correlation_id,
        }

    def test_closed_discovery_contains_only_approved_capabilities(self):
        server = self.server()
        tools = asyncio.run(
            server.request_handlers[types.ListToolsRequest](types.ListToolsRequest())
        ).root.tools
        resources = asyncio.run(
            server.request_handlers[types.ListResourcesRequest](
                types.ListResourcesRequest()
            )
        ).root.resources
        prompts = asyncio.run(
            server.request_handlers[types.ListPromptsRequest](
                types.ListPromptsRequest()
            )
        ).root.prompts

        self.assertEqual(
            [tool.name for tool in tools],
            [
                SERVER.PROJECT_RESOURCE_SUMMARY,
                SERVER.SERVER_BASIC_INFO,
                SERVER.SERVER_NETWORK_INFO,
            ],
        )
        self.assertEqual(
            [str(resource.uri) for resource in resources],
            list(SERVER.REVIEWED_RESOURCE_METADATA),
        )
        self.assertEqual(
            [prompt.name for prompt in prompts],
            [
                SERVER.PROJECT_SUMMARY_PROMPT,
                SERVER.SERVER_INSPECTION_PROMPT,
                SERVER.METADATA_DIAGNOSIS_PROMPT,
            ],
        )
        forbidden_capabilities = (
            "network_diagnosis",
            "volume_diagnosis",
            "neutron_agent_health",
            "recent_metadata_errors",
            "recent_neutron_errors",
            "recent_nova_errors",
            "fix_it",
            "shell",
            "ssh",
            "sudo",
            "remediation",
        )
        discovered_names = {
            item
            for item in [tool.name for tool in tools]
            + [prompt.name for prompt in prompts]
            + [str(resource.uri) for resource in resources]
        }
        for forbidden in forbidden_capabilities:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, discovered_names)

    def test_static_adapter_has_no_network_or_historical_runtime_imports(self):
        source = SERVER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_modules.update(
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
            if node.module
        )
        self.assertNotIn("socket", imported_modules)
        self.assertNotIn("urllib", imported_modules)
        self.assertNotIn("requests", imported_modules)
        self.assertNotIn("subprocess", imported_modules)
        for historical_path in (
            "aiops_assistant_bridge",
            "/opt/ai-ops-assistant/",
            "streamable_http",
            "mcp.server.sse",
        ):
            self.assertNotIn(historical_path, source)

    def test_resources_are_static_allowlisted_and_reject_sensitive_canaries(self):
        catalog = SERVER.load_resource_catalog(CATALOG_PATH)
        contents = [
            SERVER.read_curated_resource(uri, catalog)[0].content
            for uri in SERVER.REVIEWED_RESOURCE_METADATA
        ]
        self.assertEqual(len(contents), 6)
        for canary in (
            "fixture-token-should-not-ship",
            "fixture-password-should-not-ship",
            "fixture-private-key-should-not-ship",
            "fixture-address-should-not-ship",
            "fixture-protected-path-should-not-ship",
            "fixture-topology-should-not-ship",
        ):
            self.assertNotIn(canary, "\n".join(contents))
        for uri in (
            "file:///etc/passwd",
            "aiops://secret/fixture-token-should-not-ship",
            "aiops://topology/private",
        ):
            with self.subTest(uri=uri), self.assertRaises(SERVER.ResourceCatalogError):
                SERVER.read_curated_resource(uri, catalog)

    def test_prompt_list_and_get_are_deterministic_and_non_executable(self):
        server = self.server()
        list_handler = server.request_handlers[types.ListPromptsRequest]
        get_handler = server.request_handlers[types.GetPromptRequest]
        requests = (
            (SERVER.PROJECT_SUMMARY_PROMPT, {}),
            (SERVER.SERVER_INSPECTION_PROMPT, {"server_identifier": "demo-server"}),
            (SERVER.METADATA_DIAGNOSIS_PROMPT, {"server_identifier": "demo-server"}),
        )
        with (
            mock.patch.object(
                SERVER, "invoke_revised_runner", new=mock.AsyncMock()
            ) as invoke,
            mock.patch.object(
                SERVER.asyncio, "create_subprocess_exec", new=mock.AsyncMock()
            ) as spawn,
            mock.patch.object(
                SERVER, "read_curated_resource", side_effect=AssertionError
            ),
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            listed = asyncio.run(list_handler(types.ListPromptsRequest()))
            first_results = []
            second_results = []
            for prompt_name, arguments in requests:
                request = types.GetPromptRequest(
                    params=types.GetPromptRequestParams(
                        name=prompt_name, arguments=arguments
                    )
                )
                first_results.append(asyncio.run(get_handler(request)))
                second_results.append(asyncio.run(get_handler(request)))

        listed_again = asyncio.run(list_handler(types.ListPromptsRequest()))
        self.assertEqual(
            [prompt.model_dump() for prompt in listed.root.prompts],
            [prompt.model_dump() for prompt in listed_again.root.prompts],
        )
        for first, second in zip(first_results, second_results):
            self.assertEqual(first.model_dump(), second.model_dump())
            text = first.root.messages[0].content.text
            self.assertLessEqual(
                len(text.encode("utf-8")), SERVER.PROMPT_MAX_MESSAGE_BYTES
            )
            for heading in SERVER.PROMPT_REQUIRED_HEADINGS:
                self.assertIn(f"## {heading}", text)
            for canary in (
                "fixture-token-should-not-ship",
                "fixture-password-should-not-ship",
                "fixture-private-key-should-not-ship",
                "fixture-address-should-not-ship",
                "fixture-protected-path-should-not-ship",
                "fixture-command-should-not-ship",
                "fixture-raw-output-should-not-ship",
                "fixture-topology-should-not-ship",
            ):
                self.assertNotIn(canary, text)
        invoke.assert_not_awaited()
        spawn.assert_not_awaited()

    def test_prompt_invalid_arguments_fail_without_execution(self):
        server = self.server()
        get_handler = server.request_handlers[types.GetPromptRequest]
        invalid_requests = (
            (SERVER.PROJECT_SUMMARY_PROMPT, {"unexpected": "value"}),
            (SERVER.SERVER_INSPECTION_PROMPT, {}),
            (SERVER.SERVER_INSPECTION_PROMPT, {"server_identifier": "../etc/passwd"}),
            (SERVER.METADATA_DIAGNOSIS_PROMPT, {"server_identifier": "x" * 256}),
            ("network_diagnosis", {}),
        )
        with mock.patch.object(
            SERVER, "invoke_revised_runner", new=mock.AsyncMock()
        ) as invoke:
            for prompt_name, arguments in invalid_requests:
                request = types.GetPromptRequest(
                    params=types.GetPromptRequestParams(
                        name=prompt_name, arguments=arguments
                    )
                )
                with (
                    self.subTest(prompt_name=prompt_name, arguments=arguments),
                    self.assertRaises(SERVER.PromptContractError),
                ):
                    asyncio.run(get_handler(request))
        invoke.assert_not_awaited()

    def test_all_runner_statuses_preserve_envelope_metadata_and_error_mapping(self):
        server = self.server()
        call_handler = server.request_handlers[types.CallToolRequest]
        request = types.CallToolRequest(
            params=types.CallToolRequestParams(
                name=SERVER.PROJECT_RESOURCE_SUMMARY, arguments={}
            )
        )
        self.assertEqual(
            set(SERVER.RUNNER_STATUSES),
            {"ok", "error", "denied", "validation_error", "timeout", "unavailable"},
        )
        for status in SERVER.RUNNER_STATUSES:
            envelope = self.runner_envelope(status=status)
            with (
                self.subTest(status=status),
                mock.patch.object(
                    SERVER,
                    "invoke_revised_runner",
                    new=mock.AsyncMock(return_value=envelope),
                ) as invoke,
            ):
                response = asyncio.run(call_handler(request))
            result = response.root
            self.assertEqual(result.structuredContent, envelope)
            self.assertEqual(result.isError, status != "ok")
            self.assertEqual(json.loads(result.content[0].text), envelope)
            self.assertEqual(
                result.structuredContent["correlation_id"], envelope["correlation_id"]
            )
            self.assertEqual(result.structuredContent["duration_ms"], 12)
            self.assertEqual(
                result.structuredContent["timestamp"], envelope["timestamp"]
            )
            self.assertEqual(result.structuredContent["truncated"], status == "error")
            invoke.assert_awaited_once_with(
                SERVER.PROJECT_RESOURCE_SUMMARY,
                {},
                child_registry=mock.ANY,
            )

    def test_valid_and_invalid_tool_requests_preserve_runner_boundary(self):
        server = self.server()
        call_handler = server.request_handlers[types.CallToolRequest]
        valid_request = types.CallToolRequest(
            params=types.CallToolRequestParams(
                name=SERVER.SERVER_BASIC_INFO,
                arguments={"server_identifier": "demo-server"},
            )
        )
        envelope = self.runner_envelope(
            tool=SERVER.SERVER_BASIC_INFO,
            arguments={"server_identifier": "demo-server"},
        )
        with mock.patch.object(
            SERVER, "invoke_revised_runner", new=mock.AsyncMock(return_value=envelope)
        ) as invoke:
            result = asyncio.run(call_handler(valid_request)).root
        self.assertFalse(result.isError)
        self.assertEqual(result.structuredContent, envelope)
        invoke.assert_awaited_once_with(
            SERVER.SERVER_BASIC_INFO,
            {"server_identifier": "demo-server"},
            child_registry=mock.ANY,
        )

        for name, arguments in (
            ("shell", {}),
            (SERVER.SERVER_BASIC_INFO, {}),
            (SERVER.SERVER_NETWORK_INFO, {"server_identifier": "server/1"}),
            (SERVER.PROJECT_RESOURCE_SUMMARY, {"unexpected": "value"}),
        ):
            request = types.CallToolRequest(
                params=types.CallToolRequestParams(name=name, arguments=arguments)
            )
            with mock.patch.object(
                SERVER, "invoke_revised_runner", new=mock.AsyncMock()
            ) as rejected_invoke:
                result = asyncio.run(call_handler(request)).root
            self.assertTrue(result.isError)
            self.assertIn("error", result.structuredContent)
            self.assertNotIn("fixture-secret", result.content[0].text)
            rejected_invoke.assert_not_awaited()

    def test_timeout_cancellation_and_eof_shutdown_leave_no_children(self):
        class HangingProcess:
            returncode = None

            def __init__(self, started=None):
                self.started = started
                self.terminated = False
                self.reaped = False

            async def communicate(self):
                if self.started is not None:
                    self.started.set()
                await asyncio.sleep(3600)

            def terminate(self):
                self.terminated = True

            async def wait(self):
                self.reaped = True
                self.returncode = -15

        timeout_process = HangingProcess()
        timeout_registry = SERVER.ChildProcessRegistry()

        async def timeout_spawn(*_args, **_kwargs):
            return timeout_process

        with (
            mock.patch.object(SERVER.asyncio, "create_subprocess_exec", timeout_spawn),
            mock.patch.dict(
                SERVER.RUNNER_TIMEOUT_SECONDS_BY_TOOL,
                {SERVER.PROJECT_RESOURCE_SUMMARY: 0},
            ),
            self.assertRaises(SERVER.RunnerProtocolError),
        ):
            asyncio.run(
                SERVER.invoke_revised_runner(
                    SERVER.PROJECT_RESOURCE_SUMMARY,
                    {},
                    child_registry=timeout_registry,
                )
            )
        self.assertTrue(timeout_process.terminated)
        self.assertTrue(timeout_process.reaped)
        self.assertEqual(timeout_registry.active_children, 0)

        async def cancellation_exercise():
            started = asyncio.Event()
            cancellation_process = HangingProcess(started)
            cancellation_registry = SERVER.ChildProcessRegistry()

            async def cancellation_spawn(*_args, **_kwargs):
                return cancellation_process

            with mock.patch.object(
                SERVER.asyncio, "create_subprocess_exec", cancellation_spawn
            ):
                task = asyncio.create_task(
                    SERVER.invoke_revised_runner(
                        SERVER.PROJECT_RESOURCE_SUMMARY,
                        {},
                        child_registry=cancellation_registry,
                    )
                )
                await started.wait()
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
            return cancellation_process, cancellation_registry

        cancellation_process, cancellation_registry = asyncio.run(
            cancellation_exercise()
        )
        self.assertTrue(cancellation_process.terminated)
        self.assertTrue(cancellation_process.reaped)
        self.assertEqual(cancellation_registry.active_children, 0)

        cleanup_called = False

        class FakeServer:
            def create_initialization_options(self):
                return object()

            async def run(self, _read_stream, _write_stream, _initialization_options):
                raise EOFError("fixture EOF")

        class FakeStdioContext:
            async def __aenter__(self):
                return object(), object()

            async def __aexit__(self, _exc_type, _exc_value, _traceback):
                return False

        class FakeLifecycle:
            async def cleanup(self):
                nonlocal cleanup_called
                cleanup_called = True

        with (
            mock.patch.object(SERVER, "create_server", return_value=FakeServer()),
            mock.patch.object(SERVER, "stdio_server", return_value=FakeStdioContext()),
            self.assertRaises(EOFError),
        ):
            asyncio.run(SERVER.run_server(self.configuration(), FakeLifecycle()))
        self.assertTrue(cleanup_called)

    def test_adapter_keeps_runner_as_the_only_audit_authority(self):
        source = SERVER_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "append_audit_event",
            "build_audit_event",
            "serialize_audit_event",
            "AUDIT_ACTIVE_FILE",
            "AUDIT_ARCHIVE_FILE",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
