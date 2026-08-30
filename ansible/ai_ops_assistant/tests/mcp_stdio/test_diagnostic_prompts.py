import asyncio
import importlib.util
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
    "aiops_assistant_mcp_stdio_diagnostic_prompts",
    SourceFileLoader("aiops_assistant_mcp_stdio_diagnostic_prompts", str(SERVER_PATH)),
)
SERVER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SERVER
SPEC.loader.exec_module(SERVER)


class DiagnosticPromptsTest(unittest.TestCase):
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

    def server(self):
        return SERVER.create_server(
            self.configuration(),
            fixed_registry_path=REGISTRY_PATH,
            catalog=SERVER.load_resource_catalog(CATALOG_PATH),
        )

    def test_all_complete_prompts_are_discovered_in_contract_order(self):
        prompts = SERVER.list_diagnostic_prompts(SERVER.INITIAL_TOOL_NAMES)

        self.assertEqual(
            [prompt.name for prompt in prompts],
            ["project_summary", "server_inspection", "metadata_diagnosis"],
        )
        self.assertEqual(
            [prompt.description for prompt in prompts],
            [
                SERVER.PROJECT_SUMMARY_DESCRIPTION,
                SERVER.SERVER_INSPECTION_DESCRIPTION,
                SERVER.METADATA_DIAGNOSIS_DESCRIPTION,
            ],
        )
        self.assertEqual(prompts[0].arguments, [])
        for prompt in prompts:
            self.assertEqual(
                set(prompt.model_dump(exclude_none=True)),
                {"name", "description", "arguments"},
            )
        self.assertEqual(
            prompts[1].arguments[0].name, SERVER.PROMPT_SERVER_IDENTIFIER_ARGUMENT
        )
        self.assertTrue(prompts[1].arguments[0].required)
        self.assertEqual(SERVER.list_diagnostic_prompts(()), [])

    def test_project_summary_renders_required_bounded_advisory_message(self):
        result = SERVER.render_diagnostic_prompt(
            "project_summary", None, SERVER.INITIAL_TOOL_NAMES
        )
        self.assertEqual(result.description, SERVER.PROJECT_SUMMARY_DESCRIPTION)
        self.assertEqual(len(result.messages), 1)
        self.assertEqual(result.messages[0].role, "user")
        self.assertEqual(result.messages[0].content.type, "text")
        text = result.messages[0].content.text
        self.assertLessEqual(len(text.encode("utf-8")), SERVER.PROMPT_MAX_MESSAGE_BYTES)
        positions = [
            text.index(f"## {heading}") for heading in SERVER.PROMPT_REQUIRED_HEADINGS
        ]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("project_resource_summary", text)
        self.assertIn("status", text)
        self.assertIn("correlation ID", text)
        self.assertIn("manual, advisory, and unexecuted", text)
        for forbidden in (
            "server_basic_info",
            "server_network_info",
            "network_diagnosis",
            "volume_diagnosis",
            "fix_it",
        ):
            self.assertNotIn(forbidden, text)

    def test_prompt_arguments_validate_exact_safe_server_identifier(self):
        self.assertEqual(SERVER.validate_prompt_arguments("project_summary", None), {})
        self.assertEqual(SERVER.validate_prompt_arguments("project_summary", {}), {})
        for prompt_name in ("server_inspection", "metadata_diagnosis"):
            self.assertEqual(
                SERVER.validate_prompt_arguments(
                    prompt_name, {"server_identifier": "demo.server:1"}
                ),
                {"server_identifier": "demo.server:1"},
            )
            for arguments in (
                None,
                {},
                {"unexpected": "value"},
                {"server_identifier": 1},
                {"server_identifier": ""},
                {"server_identifier": "server/1"},
                {"server_identifier": "server name"},
                {"server_identifier": ".."},
                {"server_identifier": "a" * 256},
                {"server_identifier": "é" * 128},
            ):
                with (
                    self.subTest(prompt_name=prompt_name, arguments=arguments),
                    self.assertRaises(SERVER.PromptContractError),
                ):
                    SERVER.validate_prompt_arguments(prompt_name, arguments)
        for prompt_name in ("unknown", "network_diagnosis", "volume_diagnosis"):
            with self.assertRaises(SERVER.PromptContractError):
                SERVER.validate_prompt_arguments(prompt_name, {})

    def test_server_and_metadata_prompts_render_exact_sequences_and_boundaries(self):
        cases = (
            (
                "server_inspection",
                ("server_basic_info", "server_network_info"),
                (
                    "same exact `server_identifier=demo-server`",
                    "Keep server, network, port, fixed-IP, volume, and config-drive",
                ),
            ),
            (
                "metadata_diagnosis",
                (
                    "project_resource_summary",
                    "server_basic_info",
                    "server_network_info",
                ),
                (
                    "guest behavior",
                    "routes and packet delivery",
                    "Neutron proxy/agent state",
                    "Nova metadata",
                    "listeners including port 8775",
                    "host state",
                    "logs",
                ),
            ),
        )
        for prompt_name, sequence, required_text in cases:
            with self.subTest(prompt_name=prompt_name):
                result = SERVER.render_diagnostic_prompt(
                    prompt_name,
                    {"server_identifier": "demo-server"},
                    SERVER.INITIAL_TOOL_NAMES,
                )
                text = result.messages[0].content.text
                positions = [text.index(f"`{tool}`") for tool in sequence]
                self.assertEqual(positions, sorted(positions))
                self.assertTrue(
                    all(item in text for item in required_text),
                    text,
                )
                self.assertIn(
                    "Do not guess, retry, or substitute a second identifier.", text
                )
                self.assertEqual(len(result.messages), 1)
                self.assertLessEqual(
                    len(text.encode("utf-8")), SERVER.PROMPT_MAX_MESSAGE_BYTES
                )
                for heading in SERVER.PROMPT_REQUIRED_HEADINGS:
                    self.assertIn(f"## {heading}", text)
                for forbidden in (
                    "network_diagnosis",
                    "volume_diagnosis",
                    "fix_it",
                    "neutron_agent_health",
                    "recent_metadata_errors",
                ):
                    self.assertNotIn(forbidden, text)

    def test_prompt_handlers_are_registered_and_non_executable(self):
        server = self.server()
        list_request = types.ListPromptsRequest(params={})
        get_request = types.GetPromptRequest(
            params=types.GetPromptRequestParams(
                name="project_summary",
                arguments={},
            )
        )
        with (
            mock.patch.object(
                SERVER, "invoke_revised_runner", new=mock.AsyncMock()
            ) as invoke,
            mock.patch.object(
                SERVER.asyncio, "create_subprocess_exec", new=mock.AsyncMock()
            ) as spawn,
        ):
            listed = asyncio.run(
                server.request_handlers[types.ListPromptsRequest](list_request)
            )
            rendered = asyncio.run(
                server.request_handlers[types.GetPromptRequest](get_request)
            )

        self.assertEqual(
            [prompt.name for prompt in listed.root.prompts],
            ["project_summary", "server_inspection", "metadata_diagnosis"],
        )
        self.assertEqual(rendered.root.description, SERVER.PROJECT_SUMMARY_DESCRIPTION)
        invoke.assert_not_awaited()
        spawn.assert_not_awaited()

    def test_invalid_prompt_request_performs_no_execution(self):
        server = self.server()
        request = types.GetPromptRequest(
            params=types.GetPromptRequestParams(
                name="project_summary",
                arguments={"unexpected": "value"},
            )
        )
        with (
            mock.patch.object(
                SERVER, "invoke_revised_runner", new=mock.AsyncMock()
            ) as invoke,
            self.assertRaises(SERVER.PromptContractError),
        ):
            asyncio.run(server.request_handlers[types.GetPromptRequest](request))
        invoke.assert_not_awaited()

    def test_missing_dependency_and_oversized_render_fail_closed(self):
        self.assertEqual(SERVER.list_diagnostic_prompts(()), [])
        with self.assertRaises(SERVER.PromptContractError):
            SERVER.render_diagnostic_prompt("project_summary", {}, ())

        with (
            mock.patch.object(
                SERVER,
                "_render_prompt_text",
                return_value="x" * (16 * 1024 + 1),
            ),
            self.assertRaises(SERVER.PromptContractError),
        ):
            SERVER.render_diagnostic_prompt(
                "project_summary", {}, SERVER.INITIAL_TOOL_NAMES
            )


if __name__ == "__main__":
    unittest.main()
