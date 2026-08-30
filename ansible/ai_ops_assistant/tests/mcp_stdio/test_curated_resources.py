import asyncio
import ast
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest import mock

from mcp import types

SERVER_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_mcp_stdio/files/mcp_stdio/aiops_assistant_mcp_stdio_server.py"
)
CATALOG_PATH = SERVER_PATH.with_name("mcp_resource_catalog.json")
REGISTRY_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/tool_registry.json"
)
SPEC = importlib.util.spec_from_loader(
    "aiops_assistant_mcp_stdio_curated_resources",
    SourceFileLoader("aiops_assistant_mcp_stdio_curated_resources", str(SERVER_PATH)),
)
SERVER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SERVER
SPEC.loader.exec_module(SERVER)


class CuratedResourcesTest(unittest.TestCase):
    def setUp(self):
        self.catalog = SERVER.load_resource_catalog(CATALOG_PATH)

    def test_catalog_and_descriptors_match_reviewed_allowlist(self):
        expected_uris = list(SERVER.REVIEWED_RESOURCE_METADATA)
        self.assertEqual(
            [resource["uri"] for resource in self.catalog["resources"]], expected_uris
        )
        descriptors = SERVER.list_curated_resources(self.catalog)
        self.assertEqual([str(resource.uri) for resource in descriptors], expected_uris)
        self.assertEqual(
            [resource.name for resource in descriptors],
            [
                metadata["name"]
                for metadata in SERVER.REVIEWED_RESOURCE_METADATA.values()
            ],
        )
        self.assertTrue(
            all(resource.mimeType == "text/markdown" for resource in descriptors)
        )
        self.assertTrue(all(resource.size for resource in descriptors))

    def test_read_is_static_allowlisted_content_without_filesystem_access(self):
        with mock.patch.object(
            Path,
            "read_bytes",
            side_effect=AssertionError("resource read used filesystem"),
        ):
            contents = SERVER.read_curated_resource(
                "aiops://policy/diagnostic-safety", self.catalog
            )
        self.assertEqual(contents[0].mime_type, "text/markdown")
        self.assertIn("Diagnostic Safety Policy", contents[0].content)

        with self.assertRaises(SERVER.ResourceCatalogError):
            SERVER.read_curated_resource("file:///etc/passwd", self.catalog)

    def test_catalog_validation_rejects_duplicates_unknown_fields_bounds_and_canaries(
        self,
    ):
        unknown_field = copy.deepcopy(self.catalog)
        unknown_field["unexpected"] = True
        with self.assertRaises(SERVER.ResourceCatalogError):
            SERVER.validate_resource_catalog(unknown_field)

        oversized = copy.deepcopy(self.catalog)
        oversized["resources"][0]["content"] = "x" * (
            SERVER.RESOURCE_MAX_CONTENT_BYTES + 1
        )
        with self.assertRaises(SERVER.ResourceCatalogError):
            SERVER.validate_resource_catalog(oversized)

        for canary in (
            "token: do-not-ship",
            "-----BEGIN RSA PRIVATE KEY-----",
            "Bearer abc.def",
            "192.168.1.10",
            "/etc/private-config",
        ):
            canary_catalog = copy.deepcopy(self.catalog)
            canary_catalog["resources"][0]["content"] = canary
            with self.subTest(canary=canary), self.assertRaises(
                SERVER.ResourceCatalogError
            ):
                SERVER.validate_resource_catalog(canary_catalog)

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

    def test_server_registers_resources_without_templates_or_prompts(self):
        configuration = SERVER.AdapterConfiguration(
            schema_version=1,
            transport="stdio",
            runtime_root=SERVER.RUNTIME_ROOT,
            adapter_path=SERVER.ADAPTER_PATH,
            resource_catalog_path=CATALOG_PATH,
            max_concurrent_runner_children=1,
            cleanup_grace_seconds=5,
        )
        server = SERVER.create_server(
            configuration,
            fixed_registry_path=REGISTRY_PATH,
            catalog=self.catalog,
        )
        self.assertIn(types.ListResourcesRequest, server.request_handlers)
        self.assertIn(types.ReadResourceRequest, server.request_handlers)
        self.assertNotIn(types.ListResourceTemplatesRequest, server.request_handlers)
        self.assertIn(types.ListPromptsRequest, server.request_handlers)
        self.assertIn(types.GetPromptRequest, server.request_handlers)

        listed = asyncio.run(server.request_handlers[types.ListResourcesRequest](None))
        self.assertEqual(
            [str(resource.uri) for resource in listed.root.resources],
            list(SERVER.REVIEWED_RESOURCE_METADATA),
        )
        request = types.ReadResourceRequest(params={"uri": "aiops://policy/audit"})
        read_result = asyncio.run(
            server.request_handlers[types.ReadResourceRequest](request)
        )
        self.assertEqual(read_result.root.contents[0].mimeType, "text/markdown")
        self.assertIn("Audit Policy", read_result.root.contents[0].text)

    def test_source_has_no_dynamic_resource_access_or_network_imports(self):
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
        self.assertNotIn("glob", imported_modules)
        self.assertNotIn("open(", source)
        self.assertNotIn("urlopen", source)
        self.assertIn("read_bytes", source)


if __name__ == "__main__":
    unittest.main()
