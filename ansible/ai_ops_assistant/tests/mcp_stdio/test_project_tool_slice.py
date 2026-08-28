import asyncio
import contextlib
import copy
import importlib.util
import io
import json
import sys
import tempfile
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
    "aiops_assistant_mcp_stdio_server_project_slice",
    SourceFileLoader(
        "aiops_assistant_mcp_stdio_server_project_slice", str(SERVER_PATH)
    ),
)
SERVER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SERVER
SPEC.loader.exec_module(SERVER)


class ProjectToolSliceTest(unittest.TestCase):
    def write_registry(self, payload):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "tool_registry.json"
        path.write_text(payload, encoding="utf-8")
        self.addCleanup(temporary.cleanup)
        return path

    def valid_registry(self):
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    def write_valid_registry(self):
        return self.write_registry(
            json.dumps(self.valid_registry(), separators=(",", ":"))
        )

    def configuration(self):
        config = {
            "schema_version": 1,
            "transport": "stdio",
            "runtime_root": "/opt/openstack-ai-ops-assistant/mcp-stdio",
            "adapter_path": "/opt/openstack-ai-ops-assistant/mcp-stdio/aiops_assistant_mcp_stdio_server.py",
            "resource_catalog_path": "/opt/openstack-ai-ops-assistant/mcp-stdio/mcp_resource_catalog.json",
            "max_concurrent_runner_children": 1,
            "cleanup_grace_seconds": 5,
        }
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        self.addCleanup(temporary.cleanup)
        return SERVER.load_configuration(path)

    def runner_envelope(
        self, status="ok", tool=SERVER.PROJECT_RESOURCE_SUMMARY, arguments=None
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
            "truncated": False,
            "timestamp": "2030-01-02T03:04:05.678Z",
            "correlation_id": "00000000-0000-4000-8000-000000000001",
        }

    def test_projection_matches_three_initial_registry_schemas(self):
        projected = SERVER.load_exposed_tool_schemas(REGISTRY_PATH)

        self.assertEqual(
            [tool["name"] for tool in projected], list(SERVER.INITIAL_TOOL_NAMES)
        )
        self.assertEqual(
            [
                tool["name"]
                for tool in projected
                if tool["name"] in SERVER.PHASE06_TOOL_NAMES
            ],
            [],
        )
        self.assertEqual(projected[0]["inputSchema"], SERVER.PROJECT_TOOL_SCHEMA)
        self.assertEqual(projected[1]["inputSchema"], SERVER.SERVER_BASIC_INFO_SCHEMA)
        self.assertEqual(projected[2]["inputSchema"], SERVER.SERVER_NETWORK_INFO_SCHEMA)
        for tool in projected[1:]:
            self.assertEqual(
                tool["inputSchema"]["properties"]["server_identifier"]["pattern"],
                SERVER.SAFE_IDENTIFIER_PATTERN,
            )
            self.assertEqual(
                tool["inputSchema"]["properties"]["server_identifier"]["maxLength"],
                SERVER.SERVER_IDENTIFIER_MAX_LENGTH,
            )
            self.assertEqual(tool["inputSchema"]["additionalProperties"], False)

    def test_registry_corruption_fails_closed_before_server_creation(self):
        valid = self.valid_registry()
        corruptions = {
            "duplicate_root_key": REGISTRY_PATH.read_text(encoding="utf-8").replace(
                '"schema_version": 1,', '"schema_version": 1, "schema_version": 1,', 1
            ),
            "unknown_root_field": json.dumps({**valid, "unexpected": True}),
            "missing_project_tool": json.dumps({**valid, "tools": valid["tools"][1:]}),
        }
        changed_project = copy.deepcopy(valid)
        changed_project["tools"][0]["parameters"] = [
            {"name": "unexpected", "required": False}
        ]
        corruptions["project_parameters"] = json.dumps(changed_project)
        unknown_tool = copy.deepcopy(valid)
        unknown_tool["tools"][0]["name"] = "unknown_tool"
        corruptions["unknown_tool"] = json.dumps(unknown_tool)
        unknown_parameter = copy.deepcopy(valid)
        unknown_parameter["tools"][1]["parameters"][0]["unexpected"] = True
        corruptions["unknown_parameter_field"] = json.dumps(unknown_parameter)

        for name, content in corruptions.items():
            with self.subTest(name=name):
                path = self.write_registry(content)
                with self.assertRaises(SERVER.RegistryProjectionError):
                    SERVER.load_exposed_tool_schemas(path)

    def test_initial_calls_use_fixed_argv_deadlines_and_preserve_envelopes(self):
        calls = []

        class FakeProcess:
            def __init__(self, envelope):
                self.returncode = 0
                self.envelope = envelope

            async def communicate(self):
                return (
                    json.dumps(self.envelope, separators=(",", ":")).encode() + b"\n",
                    b"raw-secret",
                )

        async def fake_spawn(*args, **kwargs):
            calls.append((args, kwargs))
            tool = args[2]
            arguments = (
                {"server_identifier": args[4].split("=", 1)[1]} if len(args) > 3 else {}
            )
            return FakeProcess(self.runner_envelope(tool=tool, arguments=arguments))

        with mock.patch.object(SERVER.asyncio, "create_subprocess_exec", fake_spawn):
            for tool, arguments in (
                (SERVER.PROJECT_RESOURCE_SUMMARY, {}),
                (SERVER.SERVER_BASIC_INFO, {"server_identifier": "server-01"}),
                (SERVER.SERVER_NETWORK_INFO, {"server_identifier": "server-01"}),
            ):
                with self.subTest(tool=tool):
                    result = asyncio.run(SERVER.invoke_revised_runner(tool, arguments))
                    self.assertEqual(result["tool"], tool)
                    self.assertEqual(result["arguments"], arguments)

        self.assertEqual(
            [call[0] for call in calls],
            [
                (
                    str(SERVER.RUNNER_PYTHON),
                    str(SERVER.RUNNER_SCRIPT),
                    SERVER.PROJECT_RESOURCE_SUMMARY,
                ),
                (
                    str(SERVER.RUNNER_PYTHON),
                    str(SERVER.RUNNER_SCRIPT),
                    SERVER.SERVER_BASIC_INFO,
                    "--arg",
                    "server_identifier=server-01",
                ),
                (
                    str(SERVER.RUNNER_PYTHON),
                    str(SERVER.RUNNER_SCRIPT),
                    SERVER.SERVER_NETWORK_INFO,
                    "--arg",
                    "server_identifier=server-01",
                ),
            ],
        )
        self.assertEqual(
            [
                SERVER.RUNNER_TIMEOUT_SECONDS_BY_TOOL[tool]
                for tool in SERVER.INITIAL_TOOL_NAMES
            ],
            [50, 35, 50],
        )
        self.assertTrue(all("shell" not in call[1] for call in calls))

    def test_unknown_tool_and_arguments_are_rejected_before_spawn(self):
        with mock.patch.object(
            SERVER.asyncio,
            "create_subprocess_exec",
            new_callable=mock.AsyncMock,
        ) as spawn:
            with self.assertRaises(SERVER.RunnerProtocolError):
                asyncio.run(SERVER.invoke_revised_runner("server_basic_info", {}))
            with self.assertRaises(SERVER.RunnerProtocolError):
                asyncio.run(
                    SERVER.invoke_revised_runner(
                        SERVER.PROJECT_RESOURCE_SUMMARY,
                        {"unexpected": "value"},
                    )
                )
        spawn.assert_not_awaited()

    def test_server_arguments_and_phase06_tools_are_rejected_without_spawn(self):
        cases = (
            (SERVER.SERVER_BASIC_INFO, {}),
            (SERVER.SERVER_BASIC_INFO, {"server_identifier": 1}),
            (SERVER.SERVER_NETWORK_INFO, {"server_identifier": "../etc/passwd"}),
            (SERVER.SERVER_NETWORK_INFO, {"server_identifier": "x" * 256}),
            (
                SERVER.SERVER_BASIC_INFO,
                {"server_identifier": "server-01", "extra": "value"},
            ),
            ("neutron_agent_health", {}),
            ("recent_metadata_errors", {}),
            ("recent_neutron_errors", {}),
            ("recent_nova_errors", {}),
        )
        with mock.patch.object(
            SERVER.asyncio,
            "create_subprocess_exec",
            new_callable=mock.AsyncMock,
        ) as spawn:
            for tool_name, arguments in cases:
                with self.subTest(tool_name=tool_name, arguments=arguments):
                    with self.assertRaises(SERVER.RunnerProtocolError):
                        asyncio.run(SERVER.invoke_revised_runner(tool_name, arguments))
        spawn.assert_not_awaited()

    def test_decoder_rejects_extra_lines_extra_fields_and_bad_exit_status(self):
        envelope = self.runner_envelope()
        raw = json.dumps(envelope, separators=(",", ":")).encode()
        with self.assertRaises(SERVER.RunnerProtocolError):
            SERVER.decode_runner_envelope(raw + b"\n\n")

        extra = {**envelope, "unexpected": True}
        with self.assertRaises(SERVER.RunnerProtocolError):
            SERVER.decode_runner_envelope(json.dumps(extra).encode())

        bad_exit = {**envelope, "exit_code": 1}
        with self.assertRaises(SERVER.RunnerProtocolError):
            SERVER.decode_runner_envelope(json.dumps(bad_exit).encode())

    def test_decoder_preserves_all_statuses_and_truncation_mapping(self):
        from mcp import types

        for status in SERVER.RUNNER_STATUSES:
            with self.subTest(status=status):
                envelope = self.runner_envelope(status=status)
                envelope["truncated"] = status == "error"
                decoded = SERVER.decode_runner_envelope(
                    json.dumps(envelope, separators=(",", ":")).encode()
                )
                result = SERVER.map_runner_envelope_to_mcp(decoded)
                self.assertEqual(result.structuredContent, envelope)
                self.assertEqual(result.isError, status != "ok")
                self.assertEqual(len(result.content), 1)
                self.assertEqual(json.loads(result.content[0].text), envelope)
                self.assertIsInstance(result.content[0], types.TextContent)

    def test_decoder_rejects_malformed_or_disclosing_envelopes(self):
        envelope = self.runner_envelope()
        malformed = [
            b"\xff",
            b"{not-json",
            json.dumps(
                {key: value for key, value in envelope.items() if key != "data"}
            ).encode(),
            json.dumps({**envelope, "data": []}).encode(),
            json.dumps(
                {
                    **envelope,
                    "error": {"class": "execution_error"},
                    "status": "error",
                    "exit_code": 1,
                }
            ).encode(),
            json.dumps({**envelope, "stderr": "fixture-secret"}).encode(),
            json.dumps({**envelope, "timestamp": "not-a-timestamp"}).encode(),
            json.dumps(
                {
                    **envelope,
                    "correlation_id": "00000000-0000-4000-0000-000000000001",
                }
            ).encode(),
            json.dumps({**envelope, "duration_ms": float("nan")}).encode(),
        ]
        for raw in malformed:
            with self.subTest(raw=raw):
                with self.assertRaises(SERVER.RunnerProtocolError):
                    SERVER.decode_runner_envelope(raw)

    def test_mapping_keeps_runner_redaction_and_writes_no_adapter_audit(self):
        envelope = self.runner_envelope()
        envelope["data"] = {
            "sections": [{"password": "[REDACTED]", "status": "ACTIVE"}]
        }
        result = SERVER.map_runner_envelope_to_mcp(envelope)
        serialized = result.content[0].text
        self.assertNotIn("fixture-secret", serialized)
        self.assertEqual(result.structuredContent, envelope)

        fallback = SERVER.adapter_error_result("fixture-secret")
        self.assertEqual(
            fallback.structuredContent["error"]["class"],
            "adapter_redaction_error",
        )
        self.assertNotIn("fixture-secret", fallback.content[0].text)

        source = SERVER_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "append_audit_event",
            "build_audit_event",
            "serialize_audit_event",
            "AUDIT_ACTIVE_FILE",
        ):
            self.assertNotIn(forbidden, source)

    def test_mcp_call_maps_runner_envelope_and_rejects_invalid_request_without_spawn(
        self,
    ):
        from mcp import types

        server = SERVER.create_server(
            self.configuration(),
            fixed_registry_path=REGISTRY_PATH,
            catalog=SERVER.load_resource_catalog(CATALOG_PATH),
        )
        envelope = self.runner_envelope()
        request = types.CallToolRequest(
            params=types.CallToolRequestParams(
                name=SERVER.PROJECT_RESOURCE_SUMMARY,
                arguments={},
            )
        )
        with mock.patch.object(
            SERVER, "invoke_revised_runner", new=mock.AsyncMock(return_value=envelope)
        ) as invoke:
            response = asyncio.run(
                server.request_handlers[types.CallToolRequest](request)
            )
        result = response.root
        self.assertFalse(result.isError)
        self.assertEqual(result.structuredContent, envelope)
        invoke.assert_awaited_once()

        invalid_request = types.CallToolRequest(
            params=types.CallToolRequestParams(
                name=SERVER.PROJECT_RESOURCE_SUMMARY,
                arguments={"unexpected": "value"},
            )
        )
        with mock.patch.object(
            SERVER, "invoke_revised_runner", new=mock.AsyncMock()
        ) as invoke:
            response = asyncio.run(
                server.request_handlers[types.CallToolRequest](invalid_request)
            )
        result = response.root
        self.assertTrue(result.isError)
        self.assertEqual(
            result.structuredContent["error"]["class"], "request_validation_error"
        )
        invoke.assert_not_awaited()

    def test_mcp_cancellation_returns_fixed_sanitized_error(self):
        from mcp import types

        server = SERVER.create_server(
            self.configuration(),
            fixed_registry_path=REGISTRY_PATH,
            catalog=SERVER.load_resource_catalog(CATALOG_PATH),
        )
        request = types.CallToolRequest(
            params=types.CallToolRequestParams(
                name=SERVER.PROJECT_RESOURCE_SUMMARY,
                arguments={},
            )
        )
        with mock.patch.object(
            SERVER,
            "invoke_revised_runner",
            new=mock.AsyncMock(side_effect=asyncio.CancelledError),
        ):
            response = asyncio.run(
                server.request_handlers[types.CallToolRequest](request)
            )

        result = response.root
        self.assertTrue(result.isError)
        self.assertEqual(
            result.structuredContent["error"]["class"], "runner_protocol_error"
        )
        self.assertNotIn("CancelledError", result.content[0].text)

    def test_startup_registry_failure_is_nonzero_and_stdout_clean(self):
        configuration = self.configuration()
        with mock.patch.object(
            SERVER, "load_configuration", return_value=configuration
        ), mock.patch.object(
            SERVER,
            "run_server",
            side_effect=SERVER.RegistryProjectionError("invalid registry"),
        ), contextlib.redirect_stdout(
            io.StringIO()
        ) as stdout, contextlib.redirect_stderr(
            io.StringIO()
        ) as stderr:
            exit_code = SERVER.main(Path("/fixed/configuration.json"))

        self.assertEqual(exit_code, SERVER.CONFIGURATION_ERROR_EXIT_CODE)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "schema_equivalence_error\n")
        self.assertEqual(configuration.transport, "stdio")


if __name__ == "__main__":
    unittest.main()
