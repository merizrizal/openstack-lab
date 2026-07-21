import asyncio
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from jinja2 import Environment, StrictUndefined
from mcp import types


REPO_ROOT = Path(__file__).resolve().parents[2]
MCP_SERVER_PATH = (
    REPO_ROOT
    / "ansible/ai_ops_runtime/roles/assistant_runtime/files/mcp/aiops_mcp_server.py"
)
RUNNER_REGISTRY_PATH = (
    REPO_ROOT
    / "ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/tool_registry.json"
)
TOOL_RUNNER_PATH = (
    REPO_ROOT
    / "ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py"
)
MCP_RESOURCE_SOURCE_PATH = MCP_SERVER_PATH.parent / "resources"
MCP_POLICY_TEMPLATE_PATH = (
    REPO_ROOT
    / "ansible/ai_ops_runtime/roles/assistant_runtime/templates/mcp/mcp_policy.json.j2"
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

    def render_policy_template(
        self,
        restricted_host_enabled=False,
        low_risk_tools=None,
        restricted_host_tools=None,
    ):
        environment = Environment(undefined=StrictUndefined)
        environment.filters["to_json"] = json.dumps
        template = environment.from_string(
            MCP_POLICY_TEMPLATE_PATH.read_text(encoding="utf-8")
        )
        rendered = template.render(
            ai_ops_runtime_mcp_low_risk_tool_allowlist=(
                list(self.server_module.INITIAL_MCP_TOOL_NAMES)
                if low_risk_tools is None
                else low_risk_tools
            ),
            ai_ops_runtime_mcp_restricted_host_tool_allowlist=(
                list(self.server_module.RESTRICTED_HOST_MCP_TOOL_NAMES)
                if restricted_host_tools is None
                else restricted_host_tools
            ),
            ai_ops_runtime_mcp_restricted_host_exposure_enabled=(
                restricted_host_enabled
            ),
        )
        return json.loads(rendered)

    def low_risk_policy(self):
        return {
            "tool_allowlist": list(self.server_module.INITIAL_MCP_TOOL_NAMES),
            "enabled_risk_levels": [self.server_module.LOW_READONLY_PROJECT_RISK],
        }

    def project_summary_tool(self):
        return {
            "name": self.server_module.INITIAL_MCP_TOOL_NAMES[0],
            "description": "List project-visible diagnostic resources.",
            "credential_profile": "aiops-project-reader",
            "risk_level": self.server_module.LOW_READONLY_PROJECT_RISK,
            "available": True,
            "arguments": [],
        }

    def server_tool(self, name):
        descriptions = {
            "server_basic_info": "Show basic OpenStack details for one server.",
            "server_network_info": "Return network context for one server.",
        }
        return {
            "name": name,
            "description": descriptions[name],
            "credential_profile": "aiops-project-reader",
            "risk_level": self.server_module.LOW_READONLY_PROJECT_RISK,
            "available": True,
            "timeout_seconds": 30,
            "arguments": [
                {
                    "name": "server_identifier",
                    "position": 1,
                    "required": True,
                    "validation": "safe_identifier_pattern",
                    "pattern": "^[A-Za-z0-9._:-]+$",
                    "max_length": self.server_module.MCP_MAX_SERVER_IDENTIFIER_LENGTH,
                    "description": "Reviewed server name or ID.",
                }
            ],
        }

    def low_risk_registry(self):
        return {
            "policy": {"forbidden_capabilities": ["generic_shell"]},
            "supported_argument_validation_types": ["safe_identifier_pattern"],
            "tools": [
                self.project_summary_tool(),
                *(self.server_tool(name) for name in self.server_module.INITIAL_MCP_TOOL_NAMES[1:]),
            ],
        }

    def fake_runner_source(self, payload=None, raw_stdout=None):
        if raw_stdout is not None:
            return f"import sys\nsys.stdout.write({raw_stdout!r})\n"

        payload = {
            "tool": self.server_module.INITIAL_MCP_TOOL_NAMES[0],
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
            "payload['tool'] = sys.argv[1]\n"
            "payload['arguments'] = {}\n"
            "for index, value in enumerate(sys.argv):\n"
            "    if value == '--arg':\n"
            "        name, argument_value = sys.argv[index + 1].split('=', 1)\n"
            "        payload['arguments'][name] = argument_value\n"
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
            MCP_RESOURCE_SOURCE_PATH,
        )

    def call_tool(self, paths, arguments=None, tool_name=None):
        server = self.server_module.create_server(paths)
        request = types.CallToolRequest(
            params=types.CallToolRequestParams(
                name=tool_name or self.server_module.INITIAL_MCP_TOOL_NAMES[0],
                arguments=arguments,
            )
        )
        result = asyncio.run(server.request_handlers[types.CallToolRequest](request))
        return result.root

    def read_resource(self, paths, uri):
        server = self.server_module.create_server(paths)
        request = types.ReadResourceRequest(
            params=types.ReadResourceRequestParams(uri=uri)
        )
        result = asyncio.run(
            server.request_handlers[types.ReadResourceRequest](request)
        )
        return result.root

    def get_prompt(self, paths, name, arguments=None):
        server = self.server_module.create_server(paths)
        request = types.GetPromptRequest(
            params=types.GetPromptRequestParams(name=name, arguments=arguments)
        )
        result = asyncio.run(
            server.request_handlers[types.GetPromptRequest](request)
        )
        return result.root

    def make_real_runner_paths(self, policy=None, registry=None):
        paths = self.make_paths(policy, registry)
        return self.server_module.AdapterPaths(
            paths.policy_path,
            paths.registry_path,
            Path(sys.executable),
            TOOL_RUNNER_PATH,
            paths.audit_path,
        )

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
        self.assertEqual(
            paths.resource_directory,
            Path("/opt/openstack-ai-ops/mcp/resources"),
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

    def test_create_server_discovers_exactly_three_registry_derived_tools(self):
        server = self.server_module.create_server(self.make_paths())
        result = asyncio.run(
            server.request_handlers[types.ListToolsRequest](types.ListToolsRequest())
        )

        tools = {tool.name: tool for tool in result.root.tools}
        self.assertIn(types.CallToolRequest, server.request_handlers)
        self.assertEqual(list(tools), list(self.server_module.INITIAL_MCP_TOOL_NAMES))
        self.assertEqual(tools["project_resource_summary"].inputSchema, {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        })
        for tool_name in self.server_module.INITIAL_MCP_TOOL_NAMES[1:]:
            with self.subTest(tool_name=tool_name):
                self.assertEqual(
                    tools[tool_name].inputSchema["properties"]["server_identifier"],
                    {
                        "type": "string",
                        "description": "Reviewed server name or ID.",
                        "pattern": "^[A-Za-z0-9._:-]+$",
                        "maxLength": self.server_module.MCP_MAX_SERVER_IDENTIFIER_LENGTH,
                    },
                )
        self.assertIn("read-only", tools["project_resource_summary"].description.lower())

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
                "max_length": self.server_module.MCP_MAX_SERVER_IDENTIFIER_LENGTH,
                "description": "Reviewed server name or ID.",
            }
        ]

        schema = self.server_module.build_mcp_tool_schema(tool)

        self.assertEqual(schema["inputSchema"]["required"], ["server_identifier"])
        self.assertEqual(
            schema["inputSchema"]["properties"]["server_identifier"]["pattern"],
            "^[A-Za-z0-9._:-]+$",
        )
        self.assertEqual(
            schema["inputSchema"]["properties"]["server_identifier"]["maxLength"],
            self.server_module.MCP_MAX_SERVER_IDENTIFIER_LENGTH,
        )
        self.assertFalse(schema["inputSchema"]["additionalProperties"])
        self.assertNotIn("fixed_arguments", schema["inputSchema"]["properties"])

    def test_low_risk_server_identifier_lengths_match_envelope_contract(self):
        registry = json.loads(RUNNER_REGISTRY_PATH.read_text(encoding="utf-8"))
        tools = {tool["name"]: tool for tool in registry["tools"]}

        for tool_name in ("server_basic_info", "server_network_info"):
            with self.subTest(tool_name=tool_name):
                argument = tools[tool_name]["arguments"][0]
                self.assertEqual(
                    argument["max_length"],
                    self.server_module.MCP_MAX_SERVER_IDENTIFIER_LENGTH,
                )

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
                    "tool_allowlist": [self.server_module.INITIAL_MCP_TOOL_NAMES[0]],
                    "enabled_risk_levels": ["high_readonly_restricted_host_scope"],
                },
            )

    def test_policy_template_disables_restricted_host_tools_by_default(self):
        policy = self.render_policy_template()
        registry = json.loads(RUNNER_REGISTRY_PATH.read_text(encoding="utf-8"))

        self.assertEqual(
            policy,
            {
                "tool_allowlist": list(self.server_module.INITIAL_MCP_TOOL_NAMES),
                "enabled_risk_levels": [
                    self.server_module.LOW_READONLY_PROJECT_RISK
                ],
            },
        )
        exposed = self.server_module.list_exposed_tools(registry, policy)
        self.assertEqual(
            [tool["name"] for tool in exposed],
            list(self.server_module.INITIAL_MCP_TOOL_NAMES),
        )

    def test_explicit_restricted_host_opt_in_preserves_registry_contracts(self):
        policy = self.render_policy_template(restricted_host_enabled=True)
        registry = json.loads(RUNNER_REGISTRY_PATH.read_text(encoding="utf-8"))
        registry_tools = {tool["name"]: tool for tool in registry["tools"]}
        server = self.server_module.create_server(self.make_paths(policy, registry))
        result = asyncio.run(
            server.request_handlers[types.ListToolsRequest](types.ListToolsRequest())
        )
        tools = {tool.name: tool for tool in result.root.tools}

        self.assertEqual(
            list(tools),
            list(self.server_module.REVIEWED_MCP_TOOL_NAMES),
        )
        self.assertEqual(
            policy["enabled_risk_levels"],
            [
                self.server_module.LOW_READONLY_PROJECT_RISK,
                self.server_module.HIGH_READONLY_RESTRICTED_HOST_RISK,
            ],
        )
        metadata_prompt = self.get_prompt(
            self.make_paths(policy, registry),
            "metadata_diagnosis",
            {"server_identifier": "server-01"},
        )
        self.assertIn(
            "recent_metadata_errors",
            metadata_prompt.messages[0].content.text,
        )

        expected_contracts = {
            "recent_metadata_errors": (
                ["metadata"],
                ["controller01"],
            ),
            "recent_nova_errors": (
                ["nova"],
                ["controller01", "compute01", "compute02"],
            ),
            "recent_neutron_errors": (
                ["neutron"],
                ["controller01", "compute01", "compute02"],
            ),
        }
        for tool_name, (fixed_arguments, hosts) in expected_contracts.items():
            with self.subTest(tool_name=tool_name):
                registry_tool = registry_tools[tool_name]
                schema = tools[tool_name].inputSchema
                self.assertEqual(
                    registry_tool["risk_level"],
                    self.server_module.HIGH_READONLY_RESTRICTED_HOST_RISK,
                )
                self.assertEqual(registry_tool["fixed_arguments"], fixed_arguments)
                self.assertNotIn("fixed_arguments", schema["properties"])
                self.assertNotIn("kind", schema["properties"])
                self.assertEqual(schema["properties"]["host"]["enum"], hosts)
                self.assertEqual(
                    schema["properties"]["time_window"],
                    {
                        "type": "string",
                        "description": "Exact approved recent-evidence window.",
                        "enum": ["15m", "30m", "1h"],
                        "default": "15m",
                    },
                )
                self.assertFalse(schema["additionalProperties"])

    def test_restricted_host_policy_rejects_implicit_unknown_and_unreviewed_scope(self):
        registry = json.loads(RUNNER_REGISTRY_PATH.read_text(encoding="utf-8"))

        implicit_policy = self.render_policy_template(
            low_risk_tools=[
                *self.server_module.INITIAL_MCP_TOOL_NAMES,
                "recent_metadata_errors",
            ]
        )
        with self.assertRaisesRegex(ValueError, "does not enable tool risk"):
            self.server_module.list_exposed_tools(registry, implicit_policy)

        unknown_tool_policy = self.render_policy_template(
            restricted_host_enabled=True,
            restricted_host_tools=["unknown_host_tool"],
        )
        with self.assertRaisesRegex(ValueError, "unknown tool"):
            self.server_module.list_exposed_tools(registry, unknown_tool_policy)

        with self.assertRaisesRegex(ValueError, "unknown risk class"):
            self.server_module.validate_mcp_policy(
                {
                    "tool_allowlist": ["project_resource_summary"],
                    "enabled_risk_levels": [
                        self.server_module.LOW_READONLY_PROJECT_RISK,
                        "unreviewed_risk_scope",
                    ],
                }
            )

    def test_explicit_restricted_host_calls_delegate_to_runner_without_kind_override(self):
        policy = self.render_policy_template(restricted_host_enabled=True)
        registry = json.loads(RUNNER_REGISTRY_PATH.read_text(encoding="utf-8"))
        cases = {
            "recent_metadata_errors": "controller01",
            "recent_nova_errors": "compute01",
            "recent_neutron_errors": "compute02",
        }

        for tool_name, host in cases.items():
            with self.subTest(tool_name=tool_name):
                result = self.call_tool(
                    self.make_paths(policy, registry),
                    {"host": host, "time_window": "30m"},
                    tool_name,
                )
                self.assertFalse(result.isError)
                self.assertEqual(result.structuredContent["tool"], tool_name)
                self.assertEqual(
                    result.structuredContent["arguments"],
                    {"host": host, "time_window": "30m"},
                )
                self.assertNotIn("kind", result.structuredContent["arguments"])

    def test_restricted_host_invalid_alias_window_and_kind_are_runner_audited(self):
        policy = self.render_policy_template(restricted_host_enabled=True)
        registry = json.loads(RUNNER_REGISTRY_PATH.read_text(encoding="utf-8"))
        cases = (
            (
                "recent_metadata_errors",
                {"host": "compute01", "time_window": "15m"},
                "host is not an allowed value",
            ),
            (
                "recent_nova_errors",
                {"host": "controller01", "time_window": "2h"},
                "time_window is not an allowed value",
            ),
            (
                "recent_neutron_errors",
                {
                    "host": "controller01",
                    "time_window": "15m",
                    "kind": "metadata",
                },
                "unknown declared argument",
            ),
        )

        for tool_name, arguments, reason in cases:
            with self.subTest(tool_name=tool_name, reason=reason):
                paths = self.make_real_runner_paths(policy, registry)
                result = self.call_tool(paths, arguments, tool_name)
                events = [
                    json.loads(line)
                    for line in paths.audit_path.read_text(encoding="utf-8").splitlines()
                ]

                self.assertTrue(result.isError)
                self.assertEqual(result.structuredContent["status"], "validation_error")
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0]["tool"], tool_name)
                self.assertEqual(
                    events[0]["request_id"],
                    result.structuredContent["request_id"],
                )
                self.assertIn(reason, events[0]["reason"])

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

    def test_curated_resources_are_exactly_discoverable_and_readable(self):
        paths = self.make_paths()
        server = self.server_module.create_server(paths)
        result = asyncio.run(
            server.request_handlers[types.ListResourcesRequest](
                types.ListResourcesRequest()
            )
        )

        self.assertEqual(
            [str(resource.uri) for resource in result.root.resources],
            list(self.server_module.CURATED_RESOURCES),
        )
        self.assertIn(types.ReadResourceRequest, server.request_handlers)
        expected_headings = {
            "aiops://policy/diagnostic-safety": "# Diagnostic Safety Policy",
            "aiops://runbooks/metadata-troubleshooting": (
                "# Metadata Troubleshooting Context"
            ),
            "aiops://architecture/lab-summary": (
                "# OpenStack Lab Architecture Summary"
            ),
        }
        for uri, heading in expected_headings.items():
            with self.subTest(uri=uri):
                resource = self.read_resource(paths, uri).contents[0]
                self.assertEqual(str(resource.uri), uri)
                self.assertEqual(resource.mimeType, "text/markdown")
                self.assertTrue(resource.text.startswith(heading))

    def test_curated_resource_rejects_unknown_and_traversal_uris(self):
        for uri in (
            "aiops://policy/unknown",
            "aiops://policy/../architecture/lab-summary",
            "file:///etc/passwd",
        ):
            with self.subTest(uri=uri):
                with self.assertRaisesRegex(
                    ValueError,
                    "unknown curated resource URI",
                ):
                    self.server_module.read_curated_resource(
                        uri,
                        MCP_RESOURCE_SOURCE_PATH,
                    )

    def test_curated_resource_rejects_file_and_directory_symlinks(self):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = Path(tempdir.name)
        resource_directory = root / "resources"
        resource_directory.mkdir()
        outside = root / "outside.md"
        outside.write_text("outside", encoding="utf-8")
        (resource_directory / "diagnostic-safety.md").symlink_to(outside)

        with self.assertRaisesRegex(ValueError, "symlinks are not allowed"):
            self.server_module.read_curated_resource(
                "aiops://policy/diagnostic-safety",
                resource_directory,
            )

        resource_alias = root / "resource-alias"
        resource_alias.symlink_to(
            MCP_RESOURCE_SOURCE_PATH,
            target_is_directory=True,
        )
        with self.assertRaisesRegex(ValueError, "symlinks are not allowed"):
            self.server_module.read_curated_resource(
                "aiops://policy/diagnostic-safety",
                resource_alias,
            )

    def test_diagnostic_prompts_are_exactly_discoverable_and_non_remediating(self):
        paths = self.make_paths()
        server = self.server_module.create_server(paths)
        result = asyncio.run(
            server.request_handlers[types.ListPromptsRequest](
                types.ListPromptsRequest()
            )
        )

        prompts = {prompt.name: prompt for prompt in result.root.prompts}
        self.assertEqual(list(prompts), list(self.server_module.DIAGNOSTIC_PROMPTS))
        self.assertEqual(
            [argument.name for argument in prompts["metadata_diagnosis"].arguments],
            ["server_identifier"],
        )
        self.assertEqual(
            [argument.name for argument in prompts["server_inspection"].arguments],
            ["server_identifier"],
        )
        self.assertEqual(prompts["project_summary"].arguments, [])

        cases = {
            "metadata_diagnosis": (
                {"server_identifier": "server-01"},
                self.server_module.INITIAL_MCP_TOOL_NAMES,
            ),
            "server_inspection": (
                {"server_identifier": "server-01"},
                ("server_basic_info", "server_network_info"),
            ),
            "project_summary": (None, ("project_resource_summary",)),
        }
        for prompt_name, (arguments, expected_tools) in cases.items():
            with self.subTest(prompt_name=prompt_name):
                prompt = self.get_prompt(paths, prompt_name, arguments)
                text = prompt.messages[0].content.text
                self.assertIn("diagnostic-only", text)
                self.assertIn("Do not remediate", text)
                self.assertIn("Preserve every request ID", text)
                self.assertIn("manual next steps", text)
                for tool_name in expected_tools:
                    self.assertIn(tool_name, text)
                for forbidden_name in (
                    "neutron_agent_health",
                    "recent_metadata_errors",
                    "recent_nova_errors",
                    "recent_neutron_errors",
                ):
                    self.assertNotIn(forbidden_name, text)

    def test_diagnostic_prompt_arguments_follow_fixed_identifier_contract(self):
        invalid_cases = (
            ("unknown_prompt", None, "unknown diagnostic prompt"),
            (
                "metadata_diagnosis",
                None,
                "arguments do not match the fixed schema",
            ),
            (
                "server_inspection",
                {"server_identifier": "server;01"},
                "outside the reviewed identifier rules",
            ),
            (
                "metadata_diagnosis",
                {
                    "server_identifier": "a"
                    * (self.server_module.MCP_MAX_SERVER_IDENTIFIER_LENGTH + 1)
                },
                "outside the reviewed identifier rules",
            ),
            (
                "project_summary",
                {"unexpected": "value"},
                "arguments do not match the fixed schema",
            ),
        )

        for prompt_name, arguments, message in invalid_cases:
            with self.subTest(prompt_name=prompt_name, message=message):
                with self.assertRaisesRegex(ValueError, message):
                    self.server_module.render_diagnostic_prompt(
                        prompt_name,
                        arguments,
                    )

        with self.assertRaisesRegex(ValueError, "must be strings"):
            self.server_module.render_diagnostic_prompt(
                "server_inspection",
                {"server_identifier": 1},
            )

    def test_curated_content_and_prompts_contain_no_secret_material_or_examples(self):
        content = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(MCP_RESOURCE_SOURCE_PATH.glob("*.md"))
        )
        for prompt_name in self.server_module.DIAGNOSTIC_PROMPTS:
            arguments = (
                {"server_identifier": "server-01"}
                if prompt_name != "project_summary"
                else None
            )
            content += "\n" + self.server_module.render_diagnostic_prompt(
                prompt_name,
                arguments,
            ).messages[0].content.text

        for forbidden_text in (
            "-----BEGIN PRIVATE KEY-----",
            "platformpass",
            "password=",
            "password =",
            "token=",
            "token =",
            "secret=",
            "secret =",
            "```",
        ):
            with self.subTest(forbidden_text=forbidden_text):
                self.assertNotIn(forbidden_text, content)

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

    def test_server_tools_execute_fake_runner_with_valid_identifiers(self):
        for tool_name in self.server_module.INITIAL_MCP_TOOL_NAMES[1:]:
            with self.subTest(tool_name=tool_name):
                result = self.call_tool(
                    self.make_paths(),
                    {"server_identifier": "server-01"},
                    tool_name,
                )

                self.assertFalse(result.isError)
                self.assertEqual(result.structuredContent["tool"], tool_name)
                self.assertEqual(
                    result.structuredContent["arguments"],
                    {"server_identifier": "server-01"},
                )

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

    def test_maximum_identifier_envelope_fits_reviewed_bound(self):
        envelope = {
            "tool": "server_network_info",
            "status": "ok",
            "arguments": {
                "server_identifier": "a"
                * self.server_module.MCP_MAX_SERVER_IDENTIFIER_LENGTH
            },
            "exit_code": 0,
            "stdout": "a" * self.server_module.MCP_MAX_RUNNER_STREAM_BYTES,
            "stderr": "b" * self.server_module.MCP_MAX_RUNNER_STREAM_BYTES,
            "duration_ms": 1,
            "truncated": False,
            "timestamp": "2026-07-11T00:00:00Z",
            "request_id": "mcp-stdio-envelope-bound-test",
        }

        serialized = json.dumps(envelope, sort_keys=True).encode("utf-8") + b"\n"

        self.assertLessEqual(
            len(serialized), self.server_module.MCP_MAX_RUNNER_ENVELOPE_BYTES
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

    def test_invalid_string_arguments_are_runner_audited_with_correlation(self):
        cases = (
            ("server_basic_info", {}, "missing required argument"),
            (
                "server_network_info",
                {"server_identifier": "server;01"},
                "unsafe characters",
            ),
            (
                "server_basic_info",
                {"server_identifier": "server-01", "unknown": "server-01"},
                "unknown declared argument",
            ),
            (
                "server_network_info",
                {
                    "server_identifier": "a"
                    * (self.server_module.MCP_MAX_SERVER_IDENTIFIER_LENGTH + 1)
                },
                "exceeds maximum length",
            ),
        )

        for tool_name, arguments, reason in cases:
            with self.subTest(tool_name=tool_name, reason=reason):
                paths = self.make_real_runner_paths()
                result = self.call_tool(paths, arguments, tool_name)
                events = [
                    json.loads(line)
                    for line in paths.audit_path.read_text(encoding="utf-8").splitlines()
                ]

                self.assertTrue(result.isError)
                self.assertEqual(result.structuredContent["status"], "validation_error")
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0]["tool"], tool_name)
                self.assertEqual(events[0]["status"], "validation_error")
                self.assertEqual(
                    events[0]["request_id"],
                    result.structuredContent["request_id"],
                )
                self.assertEqual(
                    events[0]["client_id"], self.server_module.MCP_AUDIT_CLIENT_ID
                )
                self.assertEqual(
                    events[0]["transport"], self.server_module.MCP_AUDIT_TRANSPORT
                )
                self.assertIn(reason, events[0]["reason"])

    def test_adapter_rejects_non_string_argument_without_runner_execution(self):
        paths = self.make_paths()
        result = self.call_tool(
            paths,
            {"server_identifier": 1},
            "server_basic_info",
        )

        self.assertTrue(result.isError)
        self.assertEqual(
            json.loads(result.content[0].text)["error"],
            "MCP tool arguments must be strings",
        )
        self.assertFalse(paths.audit_path.exists())

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
