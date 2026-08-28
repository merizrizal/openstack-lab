import ast
import asyncio
import contextlib
import importlib.util
import io
import json
import tempfile
import sys
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest import mock

SERVER_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_mcp_stdio/files/mcp_stdio/aiops_assistant_mcp_stdio_server.py"
)
REGISTRY_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/tool_registry.json"
)
CATALOG_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_mcp_stdio/files/mcp_stdio/mcp_resource_catalog.json"
)
SPEC = importlib.util.spec_from_loader(
    "aiops_assistant_mcp_stdio_server_test_target",
    SourceFileLoader("aiops_assistant_mcp_stdio_server_test_target", str(SERVER_PATH)),
)
SERVER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SERVER
SPEC.loader.exec_module(SERVER)


class StdioLifecycleTest(unittest.TestCase):
    def write_configuration(self, payload):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "config.json"
        path.write_text(payload, encoding="utf-8")
        self.addCleanup(temporary.cleanup)
        return path

    def valid_configuration(self):
        return {
            "schema_version": 1,
            "transport": "stdio",
            "runtime_root": "/opt/openstack-ai-ops-assistant/mcp-stdio",
            "adapter_path": "/opt/openstack-ai-ops-assistant/mcp-stdio/aiops_assistant_mcp_stdio_server.py",
            "resource_catalog_path": "/opt/openstack-ai-ops-assistant/mcp-stdio/mcp_resource_catalog.json",
            "max_concurrent_runner_children": 1,
            "cleanup_grace_seconds": 5,
        }

    def configuration(self):
        path = self.write_configuration(
            json.dumps(self.valid_configuration(), separators=(",", ":"))
        )
        return SERVER.load_configuration(path)

    def test_missing_and_malformed_configuration_fail_without_stdout(self):
        missing = Path(tempfile.gettempdir()) / "mcp-stdio-config-does-not-exist"
        malformed = self.write_configuration('{"schema_version": 1,')
        duplicate = self.write_configuration(
            '{"schema_version": 1, "schema_version": 1}'
        )

        for path in (missing, malformed, duplicate):
            with self.subTest(path=path), contextlib.redirect_stdout(
                io.StringIO()
            ) as stdout, contextlib.redirect_stderr(io.StringIO()) as stderr:
                exit_code = SERVER.main(path)
            self.assertEqual(exit_code, SERVER.CONFIGURATION_ERROR_EXIT_CODE)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(stderr.getvalue(), "adapter_configuration_error\n")

    def test_missing_sdk_fails_nonzero_without_protocol_output(self):
        path = self.write_configuration(
            json.dumps(self.valid_configuration(), separators=(",", ":"))
        )
        with mock.patch.object(SERVER, "Server", None), mock.patch.object(
            SERVER, "stdio_server", None
        ), contextlib.redirect_stdout(
            io.StringIO()
        ) as stdout, contextlib.redirect_stderr(
            io.StringIO()
        ) as stderr:
            exit_code = SERVER.main(path)

        self.assertEqual(exit_code, SERVER.DEPENDENCY_ERROR_EXIT_CODE)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "adapter_dependency_error\n")

    def test_server_registers_initial_tools_and_curated_resources_without_prompts(self):
        server = SERVER.create_server(
            self.configuration(),
            fixed_registry_path=REGISTRY_PATH,
            catalog=SERVER.load_resource_catalog(CATALOG_PATH),
        )
        from mcp import types

        self.assertIn(types.ListToolsRequest, server.request_handlers)
        self.assertIn(types.CallToolRequest, server.request_handlers)
        self.assertIn(types.ListResourcesRequest, server.request_handlers)
        self.assertIn(types.ReadResourceRequest, server.request_handlers)
        for request_type in (
            types.ListResourceTemplatesRequest,
            types.ListPromptsRequest,
            types.GetPromptRequest,
        ):
            with self.subTest(request_type=request_type):
                self.assertNotIn(request_type, server.request_handlers)

        listed = asyncio.run(server.request_handlers[types.ListToolsRequest](None))
        self.assertEqual(
            [tool.name for tool in listed.root.tools], list(SERVER.INITIAL_TOOL_NAMES)
        )
        self.assertEqual(
            [tool.inputSchema for tool in listed.root.tools],
            [
                SERVER.PROJECT_TOOL_SCHEMA,
                SERVER.SERVER_BASIC_INFO_SCHEMA,
                SERVER.SERVER_NETWORK_INFO_SCHEMA,
            ],
        )
        for optional_name in SERVER.PHASE06_TOOL_NAMES:
            self.assertNotIn(optional_name, [tool.name for tool in listed.root.tools])

        listed_resources = asyncio.run(
            server.request_handlers[types.ListResourcesRequest](None)
        )
        self.assertEqual(
            [str(resource.uri) for resource in listed_resources.root.resources],
            list(SERVER.REVIEWED_RESOURCE_METADATA),
        )

    def test_source_uses_only_low_level_stdio_and_no_network_or_historical_path(self):
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

        self.assertIn("asyncio", imported_modules)
        self.assertIn("json", imported_modules)
        self.assertNotIn("socket", imported_modules)
        self.assertNotIn("subprocess", imported_modules)
        for forbidden in (
            "uvicorn",
            "streamable_http",
            "http.server",
            "mcp.server.sse",
            "aiops_assistant_bridge",
            "/opt/openstack-ai-ops/",
        ):
            self.assertNotIn(forbidden, source)

    def test_stdio_run_cleanup_executes_on_cancellation(self):
        configuration = self.configuration()
        cleanup_called = False

        class FakeServer:
            def create_initialization_options(self):
                return object()

            async def run(self, read_stream, write_stream, initialization_options):
                raise asyncio.CancelledError

        class FakeStdioContext:
            async def __aenter__(self):
                return object(), object()

            async def __aexit__(self, exc_type, exc_value, traceback):
                return False

        class FakeLifecycle:
            async def cleanup(self):
                nonlocal cleanup_called
                cleanup_called = True

        with mock.patch.object(
            SERVER, "create_server", return_value=FakeServer()
        ), mock.patch.object(SERVER, "stdio_server", return_value=FakeStdioContext()):
            with self.assertRaises(asyncio.CancelledError):
                asyncio.run(SERVER.run_server(configuration, FakeLifecycle()))

        self.assertTrue(cleanup_called)

    def test_runner_stdout_and_stderr_bounds_fail_closed(self):
        class FakeProcess:
            returncode = 0

            def __init__(self, stdout, stderr):
                self.stdout = stdout
                self.stderr = stderr

            async def communicate(self):
                return self.stdout, self.stderr

        for stdout, stderr in (
            (b"x" * (SERVER.RUNNER_MAX_ENVELOPE_BYTES + 1), b""),
            (b"{}", b"e" * (SERVER.RUNNER_MAX_STDERR_BYTES + 1)),
        ):
            with self.subTest(stdout=len(stdout), stderr=len(stderr)):
                process = FakeProcess(stdout, stderr)
                registry = SERVER.ChildProcessRegistry()

                async def fake_spawn(*_args, **_kwargs):
                    return process

                with mock.patch.object(
                    SERVER.asyncio, "create_subprocess_exec", fake_spawn
                ), self.assertRaises(SERVER.RunnerProtocolError):
                    asyncio.run(
                        SERVER.invoke_revised_runner(
                            SERVER.PROJECT_RESOURCE_SUMMARY,
                            {},
                            child_registry=registry,
                        )
                    )
                self.assertEqual(registry.active_children, 0)

    def test_runner_timeout_terminates_and_reaps_child(self):
        class HangingProcess:
            returncode = None

            def __init__(self):
                self.terminated = False
                self.reaped = False

            async def communicate(self):
                await asyncio.sleep(3600)

            def terminate(self):
                self.terminated = True

            async def wait(self):
                self.reaped = True
                self.returncode = -15

        process = HangingProcess()
        registry = SERVER.ChildProcessRegistry()

        async def fake_spawn(*_args, **_kwargs):
            return process

        with mock.patch.object(
            SERVER.asyncio, "create_subprocess_exec", fake_spawn
        ), mock.patch.dict(
            SERVER.RUNNER_TIMEOUT_SECONDS_BY_TOOL,
            {SERVER.PROJECT_RESOURCE_SUMMARY: 0},
        ), self.assertRaises(
            SERVER.RunnerProtocolError
        ):
            asyncio.run(
                SERVER.invoke_revised_runner(
                    SERVER.PROJECT_RESOURCE_SUMMARY, {}, child_registry=registry
                )
            )

        self.assertTrue(process.terminated)
        self.assertTrue(process.reaped)
        self.assertEqual(registry.active_children, 0)

    def test_runner_cancellation_terminates_and_reaps_child(self):
        class HangingProcess:
            returncode = None

            def __init__(self, started):
                self.started = started
                self.terminated = False
                self.reaped = False

            async def communicate(self):
                self.started.set()
                await asyncio.sleep(3600)

            def terminate(self):
                self.terminated = True

            async def wait(self):
                self.reaped = True
                self.returncode = -15

        async def exercise():
            started = asyncio.Event()
            process = HangingProcess(started)
            registry = SERVER.ChildProcessRegistry()

            async def fake_spawn(*_args, **_kwargs):
                return process

            with mock.patch.object(
                SERVER.asyncio, "create_subprocess_exec", fake_spawn
            ):
                task = asyncio.create_task(
                    SERVER.invoke_revised_runner(
                        SERVER.PROJECT_RESOURCE_SUMMARY, {}, child_registry=registry
                    )
                )
                await started.wait()
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task

            return process, registry

        process, registry = asyncio.run(exercise())
        self.assertTrue(process.terminated)
        self.assertTrue(process.reaped)
        self.assertEqual(registry.active_children, 0)

    def test_child_cleanup_is_bounded_and_reaps_registered_handles(self):
        class FakeChild:
            def __init__(self):
                self.terminated = False
                self.reaped = False

            def terminate(self):
                self.terminated = True

            async def wait(self):
                self.reaped = True

        child = FakeChild()
        registry = SERVER.ChildProcessRegistry()
        registry.register(child)
        self.assertEqual(registry.active_children, 1)

        asyncio.run(registry.cleanup())

        self.assertTrue(child.terminated)
        self.assertTrue(child.reaped)
        self.assertEqual(registry.active_children, 0)

    def test_successful_lifecycle_emits_no_stdout_or_stderr(self):
        configuration = self.configuration()

        async def no_op_run(_configuration):
            return None

        with mock.patch.object(
            SERVER, "run_server", side_effect=no_op_run
        ), contextlib.redirect_stdout(
            io.StringIO()
        ) as stdout, contextlib.redirect_stderr(
            io.StringIO()
        ) as stderr:
            exit_code = SERVER.main(
                self.write_configuration(
                    json.dumps(self.valid_configuration(), separators=(",", ":"))
                )
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(configuration.transport, "stdio")


if __name__ == "__main__":
    unittest.main()
