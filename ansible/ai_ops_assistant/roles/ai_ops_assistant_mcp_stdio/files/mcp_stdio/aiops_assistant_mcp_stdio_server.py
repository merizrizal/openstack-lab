#!/usr/bin/env python3
"""Non-activating local-stdio MCP server skeleton."""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import re
import signal
import sys
import uuid
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from mcp import types
    from mcp.server.lowlevel import Server
    from mcp.server.lowlevel.helper_types import ReadResourceContents
    from mcp.server.stdio import stdio_server
except ImportError:  # pragma: no cover - exercised by the dependency-failure test.
    Server = None  # type: ignore[assignment,misc]
    types = None  # type: ignore[assignment]
    stdio_server = None  # type: ignore[assignment]
    ReadResourceContents = None  # type: ignore[assignment]

CONFIG_PATH = Path("/etc/ai-ops-assistant/mcp-stdio/config.json")
RUNTIME_ROOT = Path("/opt/openstack-ai-ops-assistant/mcp-stdio")
ADAPTER_PATH = RUNTIME_ROOT / "aiops_assistant_mcp_stdio_server.py"
RESOURCE_CATALOG_PATH = RUNTIME_ROOT / "mcp_resource_catalog.json"
REGISTRY_PATH = Path(
    "/opt/openstack-ai-ops-assistant/scripts/tool_runner/tool_registry.json"
)
RUNNER_PYTHON = Path("/opt/openstack-ai-ops-assistant/mcp-stdio/venv/bin/python")
RUNNER_SCRIPT = Path(
    "/opt/openstack-ai-ops-assistant/scripts/tool_runner/aiops_tool_runner.py"
)
PROJECT_RESOURCE_SUMMARY = "project_resource_summary"
SERVER_BASIC_INFO = "server_basic_info"
SERVER_NETWORK_INFO = "server_network_info"
INITIAL_TOOL_NAMES = (
    PROJECT_RESOURCE_SUMMARY,
    SERVER_BASIC_INFO,
    SERVER_NETWORK_INFO,
)
PHASE06_TOOL_NAMES = frozenset(
    {
        "neutron_agent_health",
        "recent_metadata_errors",
        "recent_neutron_errors",
        "recent_nova_errors",
    }
)
KNOWN_REGISTRY_TOOL_NAMES = frozenset(INITIAL_TOOL_NAMES) | PHASE06_TOOL_NAMES
SAFE_IDENTIFIER_PATTERN = r"^[A-Za-z0-9._:-]+$"
SERVER_IDENTIFIER_MAX_LENGTH = 255
RUNNER_TIMEOUT_SECONDS = 50
RUNNER_TIMEOUT_SECONDS_BY_TOOL = {
    PROJECT_RESOURCE_SUMMARY: 50,
    SERVER_BASIC_INFO: 35,
    SERVER_NETWORK_INFO: 50,
}
RUNNER_MAX_ENVELOPE_BYTES = 256 * 1024
RUNNER_MAX_STDERR_BYTES = 8 * 1024
RUNNER_TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
RUNNER_ERROR_FIELDS = frozenset({"class", "message"})
ADAPTER_ERROR_CLASSES = frozenset(
    {
        "adapter_configuration_error",
        "tool_exposure_error",
        "schema_equivalence_error",
        "runner_unavailable",
        "runner_protocol_error",
        "adapter_redaction_error",
        "request_validation_error",
        "adapter_unavailable",
    }
)
RUNNER_ENVELOPE_FIELDS = frozenset(
    {
        "schema_version",
        "tool",
        "status",
        "arguments",
        "exit_code",
        "data",
        "stdout",
        "stderr",
        "error",
        "duration_ms",
        "truncated",
        "timestamp",
        "correlation_id",
    }
)
RUNNER_STATUSES = frozenset(
    {"ok", "error", "denied", "validation_error", "timeout", "unavailable"}
)
RUNNER_STATUS_EXIT_CODES = {
    "ok": 0,
    "error": 1,
    "denied": 2,
    "validation_error": 3,
    "timeout": 4,
    "unavailable": 5,
}
PROJECT_TOOL_SCHEMA = {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": False,
}
SERVER_IDENTIFIER_SCHEMA = {
    "type": "string",
    "description": "Server name or ID using the approved safe identifier character set.",
    "pattern": SAFE_IDENTIFIER_PATTERN,
    "maxLength": SERVER_IDENTIFIER_MAX_LENGTH,
}
SERVER_BASIC_INFO_SCHEMA = {
    "type": "object",
    "properties": {"server_identifier": SERVER_IDENTIFIER_SCHEMA},
    "required": ["server_identifier"],
    "additionalProperties": False,
}
SERVER_NETWORK_INFO_SCHEMA = {
    "type": "object",
    "properties": {"server_identifier": SERVER_IDENTIFIER_SCHEMA},
    "required": ["server_identifier"],
    "additionalProperties": False,
}
INITIAL_TOOL_SCHEMAS = {
    PROJECT_RESOURCE_SUMMARY: PROJECT_TOOL_SCHEMA,
    SERVER_BASIC_INFO: SERVER_BASIC_INFO_SCHEMA,
    SERVER_NETWORK_INFO: SERVER_NETWORK_INFO_SCHEMA,
}
PROJECT_SUMMARY_PROMPT = "project_summary"
PROJECT_SUMMARY_DESCRIPTION = (
    "Summarize project-visible diagnostic resources using approved read-only evidence."
)
SERVER_INSPECTION_PROMPT = "server_inspection"
SERVER_INSPECTION_DESCRIPTION = (
    "Inspect one project-visible server using basic and network evidence."
)
METADATA_DIAGNOSIS_PROMPT = "metadata_diagnosis"
METADATA_DIAGNOSIS_DESCRIPTION = (
    "Diagnose metadata symptoms using bounded project and server evidence."
)
PROMPT_SERVER_IDENTIFIER_ARGUMENT = "server_identifier"
PROMPT_MAX_MESSAGE_BYTES = 16 * 1024
PROMPT_REQUIRED_HEADINGS = (
    "Observed evidence",
    "Healthy signals",
    "Failing signals",
    "Inferences and likely failure domain",
    "Missing or unavailable evidence",
    "Manual next actions — not executed",
)
REGISTRY_MAX_BYTES = 256 * 1024
REGISTRY_ROOT_FIELDS = frozenset(
    {"schema_version", "registry_name", "defaults", "tools"}
)
REGISTRY_DEFAULT_FIELDS = frozenset(
    {
        "credential_profile",
        "risk_class",
        "timeout_seconds",
        "output_limit_bytes",
        "mutation_guarantee",
    }
)
REGISTRY_TOOL_REQUIRED_FIELDS = frozenset({"name", "description", "parameters"})
REGISTRY_TOOL_ALLOWED_FIELDS = frozenset(
    {
        "name",
        "authority_class",
        "description",
        "implementation_target",
        "credential_profile",
        "risk_class",
        "timeout_seconds",
        "output_limit_bytes",
        "mutation_guarantee",
        "parameters",
    }
)
REGISTRY_PARAMETER_REQUIRED_FIELDS = frozenset(
    {"name", "position", "required", "type", "validation", "description"}
)
REGISTRY_PARAMETER_OPTIONAL_FIELDS = frozenset(
    {"pattern", "max_length", "allowed_values", "default"}
)
PUBLIC_DESCRIPTION_SUFFIX = (
    " Read-only diagnostic; no mutation, credential, or arbitrary execution capability."
)
SERVICE_NAME = "openstack-ai-ops-assistant-mcp-stdio"
SERVICE_VERSION = "0.1.0"
CONFIGURATION_ERROR_EXIT_CODE = 2
DEPENDENCY_ERROR_EXIT_CODE = 3
CLEANUP_GRACE_SECONDS = 5
MAX_CONFIGURATION_BYTES = 16 * 1024
EXPECTED_CONFIGURATION_FIELDS = frozenset(
    {
        "schema_version",
        "transport",
        "runtime_root",
        "adapter_path",
        "resource_catalog_path",
        "max_concurrent_runner_children",
        "cleanup_grace_seconds",
    }
)


RESOURCE_CATALOG_SCHEMA_VERSION = 1
RESOURCE_CATALOG_NAME = "ai-ops-assistant-mcp-resources-steps-01-04"
RESOURCE_MAX_CONTENT_BYTES = 64 * 1024
RESOURCE_MAX_CATALOG_BYTES = 256 * 1024
RESOURCE_MIME_TYPE = "text/markdown"
RESOURCE_CATALOG_ROOT_FIELDS = frozenset(
    {"schema_version", "catalog_name", "resources"}
)
RESOURCE_ENTRY_FIELDS = frozenset(
    {"uri", "name", "description", "mime_type", "content"}
)
REVIEWED_RESOURCE_METADATA = {
    "aiops://architecture/lab-summary": {
        "name": "lab-architecture-summary",
        "description": "Sanitized OpenStack lab architecture and service relationships.",
    },
    "aiops://policy/diagnostic-safety": {
        "name": "diagnostic-safety",
        "description": "Read-only diagnostic safety policy and runner boundary.",
    },
    "aiops://policy/credential-profile": {
        "name": "credential-profile-policy",
        "description": "Conceptual credential-profile separation and unavailable behavior.",
    },
    "aiops://policy/tool-registry": {
        "name": "tool-registry-policy",
        "description": "Reviewed diagnostic tool names, schemas, and authority boundary.",
    },
    "aiops://policy/audit": {
        "name": "audit-policy",
        "description": "Minimum-disclosure audit purpose and correlation policy.",
    },
    "aiops://runbooks/metadata-troubleshooting": {
        "name": "metadata-troubleshooting",
        "description": "Safe evidence order for metadata troubleshooting.",
    },
}
RESOURCE_CONTENT_FORBIDDEN_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(?:password|passwd|token|secret|api[_ -]?key)[ ]*[:=]"),
    re.compile(r"(?i)bearer[ ]+[A-Za-z0-9._~-]+"),
    re.compile(r"(?:^|[^0-9])(?:[0-9]{1,3}[.]){3}[0-9]{1,3}(?:$|[^0-9])"),
    re.compile(r"(?:^|[ (])/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+"),
)


class AdapterConfigurationError(ValueError):
    """Raised when fixed local-stdio configuration is unavailable or invalid."""


class ResourceCatalogError(ValueError):
    """Raised when the reviewed static resource catalog is invalid."""


class AdapterDependencyError(RuntimeError):
    """Raised when the approved MCP SDK API cannot be imported."""


class RegistryProjectionError(ValueError):
    """Raised when the trusted registry cannot produce the reviewed schema."""


class RunnerUnavailableError(RuntimeError):
    """Raised when the fixed runner process cannot be started."""


class RunnerProtocolError(RuntimeError):
    """Raised when the fixed runner does not emit one valid result envelope."""


class RunnerRequestValidationError(RunnerProtocolError):
    """Raised when a public MCP request fails adapter-side validation."""


class PromptContractError(ValueError):
    """Raised when a prompt request or rendered contract is invalid."""


@dataclass(frozen=True)
class PromptDefinition:
    """Closed metadata for one locally implemented diagnostic prompt."""

    name: str
    description: str
    required_tools: tuple[str, ...]
    argument_name: str | None = None


_PROMPT_DEFINITIONS = (
    PromptDefinition(
        name=PROJECT_SUMMARY_PROMPT,
        description=PROJECT_SUMMARY_DESCRIPTION,
        required_tools=(PROJECT_RESOURCE_SUMMARY,),
    ),
    PromptDefinition(
        name=SERVER_INSPECTION_PROMPT,
        description=SERVER_INSPECTION_DESCRIPTION,
        required_tools=(SERVER_BASIC_INFO, SERVER_NETWORK_INFO),
        argument_name=PROMPT_SERVER_IDENTIFIER_ARGUMENT,
    ),
    PromptDefinition(
        name=METADATA_DIAGNOSIS_PROMPT,
        description=METADATA_DIAGNOSIS_DESCRIPTION,
        required_tools=(
            PROJECT_RESOURCE_SUMMARY,
            SERVER_BASIC_INFO,
            SERVER_NETWORK_INFO,
        ),
        argument_name=PROMPT_SERVER_IDENTIFIER_ARGUMENT,
    ),
)


@dataclass(frozen=True)
class AdapterConfiguration:
    """Validated fixed values needed to construct the empty server skeleton."""

    schema_version: int
    transport: str
    runtime_root: Path
    adapter_path: Path
    resource_catalog_path: Path
    max_concurrent_runner_children: int
    cleanup_grace_seconds: int


class ChildProcessRegistry:
    """Bounded cleanup seam; this chunk never registers or starts a child."""

    def __init__(self, cleanup_grace_seconds: int = CLEANUP_GRACE_SECONDS) -> None:
        if not 1 <= cleanup_grace_seconds <= CLEANUP_GRACE_SECONDS:
            raise ValueError("cleanup grace is outside the fixed bound")
        self._cleanup_grace_seconds = cleanup_grace_seconds
        self._children: dict[int, Any] = {}

    @property
    def active_children(self) -> int:
        """Return the number of child handles awaiting cleanup."""

        return len(self._children)

    def register(self, child: Any) -> None:
        """Register a future runner child for bounded shutdown cleanup."""

        self._children[id(child)] = child

    def unregister(self, child: Any) -> None:
        """Remove a child handle after its owner has reaped it."""

        self._children.pop(id(child), None)

    async def cleanup(self) -> None:
        """Terminate and reap registered children within the fixed grace period."""

        children = tuple(self._children.values())
        self._children.clear()
        if not children:
            return

        for child in children:
            terminate = getattr(child, "terminate", None)
            if callable(terminate):
                terminate()

        waiters = [self._wait_for_child(child) for child in children]
        try:
            await asyncio.wait_for(
                asyncio.gather(*waiters), timeout=self._cleanup_grace_seconds
            )
        except asyncio.TimeoutError:
            for child in children:
                kill = getattr(child, "kill", None)
                if callable(kill):
                    kill()
            forced_waiters = [self._wait_for_child(child) for child in children]
            try:
                await asyncio.wait_for(
                    asyncio.gather(*forced_waiters),
                    timeout=self._cleanup_grace_seconds,
                )
            except asyncio.TimeoutError as exc:
                raise RuntimeError("child cleanup exceeded fixed grace") from exc

    @staticmethod
    async def _wait_for_child(child: Any) -> None:
        wait = getattr(child, "wait", None)
        if not callable(wait):
            return
        result = wait()
        if inspect.isawaitable(result):
            await result


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AdapterConfigurationError("configuration contains duplicate keys")
        result[key] = value
    return result


def _load_configuration_object(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise AdapterConfigurationError("configuration is unavailable")
    try:
        if path.stat().st_size > MAX_CONFIGURATION_BYTES:
            raise AdapterConfigurationError("configuration exceeds the fixed bound")
        return json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except AdapterConfigurationError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterConfigurationError("configuration cannot be decoded") from exc


def load_configuration(path: Path = CONFIG_PATH) -> AdapterConfiguration:
    """Load and validate only the fixed local-stdio configuration shape."""

    value = _load_configuration_object(path)
    if not isinstance(value, Mapping):
        raise AdapterConfigurationError("configuration must be an object")
    if set(value) != EXPECTED_CONFIGURATION_FIELDS:
        raise AdapterConfigurationError("configuration fields are not closed")

    expected = {
        "schema_version": 1,
        "transport": "stdio",
        "runtime_root": str(RUNTIME_ROOT),
        "adapter_path": str(ADAPTER_PATH),
        "resource_catalog_path": str(RESOURCE_CATALOG_PATH),
        "max_concurrent_runner_children": 1,
        "cleanup_grace_seconds": CLEANUP_GRACE_SECONDS,
    }
    if value != expected:
        raise AdapterConfigurationError("configuration contains an unexpected value")
    if type(value["schema_version"]) is not int:
        raise AdapterConfigurationError("schema version must be an integer")
    if type(value["max_concurrent_runner_children"]) is not int:
        raise AdapterConfigurationError("runner concurrency must be an integer")
    if type(value["cleanup_grace_seconds"]) is not int:
        raise AdapterConfigurationError("cleanup grace must be an integer")

    return AdapterConfiguration(
        schema_version=value["schema_version"],
        transport=value["transport"],
        runtime_root=Path(value["runtime_root"]),
        adapter_path=Path(value["adapter_path"]),
        resource_catalog_path=Path(value["resource_catalog_path"]),
        max_concurrent_runner_children=value["max_concurrent_runner_children"],
        cleanup_grace_seconds=value["cleanup_grace_seconds"],
    )


def _reject_duplicate_registry_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RegistryProjectionError("registry contains duplicate keys")
        result[key] = value
    return result


def _load_registry_object(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise RegistryProjectionError("registry is unavailable")
    try:
        if path.stat().st_size > REGISTRY_MAX_BYTES:
            raise RegistryProjectionError("registry exceeds the fixed bound")
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_registry_keys,
        )
    except RegistryProjectionError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RegistryProjectionError("registry cannot be decoded") from exc
    if not isinstance(value, Mapping):
        raise RegistryProjectionError("registry must be an object")
    return dict(value)


def _validate_registry_tool_shape(tool: Any) -> tuple[str, list[Any]]:
    if not isinstance(tool, Mapping):
        raise RegistryProjectionError("registry tool must be an object")
    actual_fields = set(tool)
    if not REGISTRY_TOOL_REQUIRED_FIELDS <= actual_fields:
        raise RegistryProjectionError("registry tool is missing public fields")
    if not actual_fields <= REGISTRY_TOOL_ALLOWED_FIELDS:
        raise RegistryProjectionError("registry tool fields are unsupported")
    name = tool["name"]
    description = tool["description"]
    parameters = tool["parameters"]
    if (
        not isinstance(name, str)
        or not name
        or len(name) > 128
        or not isinstance(description, str)
        or not description
        or len(description.encode("utf-8")) > 4096
        or not isinstance(parameters, list)
    ):
        raise RegistryProjectionError("registry tool has invalid public fields")
    return name, parameters


def _project_registry_parameter(
    parameter: Any, tool_name: str
) -> tuple[int, str, dict[str, Any]]:
    if not isinstance(parameter, Mapping):
        raise RegistryProjectionError("registry parameter must be an object")
    actual_fields = set(parameter)
    if not REGISTRY_PARAMETER_REQUIRED_FIELDS <= actual_fields:
        raise RegistryProjectionError("registry parameter is missing public fields")
    if not actual_fields <= (
        REGISTRY_PARAMETER_REQUIRED_FIELDS | REGISTRY_PARAMETER_OPTIONAL_FIELDS
    ):
        raise RegistryProjectionError("registry parameter fields are unsupported")

    name = parameter["name"]
    position = parameter["position"]
    required = parameter["required"]
    parameter_type = parameter["type"]
    validation = parameter["validation"]
    description = parameter["description"]
    if (
        not isinstance(name, str)
        or not name
        or len(name) > 128
        or isinstance(position, bool)
        or not isinstance(position, int)
        or not 1 <= position <= 32
        or not isinstance(required, bool)
        or parameter_type != "string"
        or not isinstance(validation, str)
        or not isinstance(description, str)
        or not description
        or len(description.encode("utf-8")) > 4096
    ):
        raise RegistryProjectionError("registry parameter has invalid public fields")

    schema: dict[str, Any] = {"type": "string", "description": description}
    if validation == "safe_identifier_pattern":
        expected_fields = REGISTRY_PARAMETER_REQUIRED_FIELDS | {
            "pattern",
            "max_length",
        }
        if (
            tool_name not in {SERVER_BASIC_INFO, SERVER_NETWORK_INFO}
            or name != "server_identifier"
            or not required
            or actual_fields != expected_fields
            or parameter["pattern"] != SAFE_IDENTIFIER_PATTERN
            or isinstance(parameter["max_length"], bool)
            or parameter["max_length"] != SERVER_IDENTIFIER_MAX_LENGTH
        ):
            raise RegistryProjectionError(
                "registry identifier parameter is unsupported"
            )
        schema["pattern"] = parameter["pattern"]
        schema["maxLength"] = parameter["max_length"]
    elif validation == "safe_host_label_pattern":
        expected_fields = REGISTRY_PARAMETER_REQUIRED_FIELDS | {
            "pattern",
            "max_length",
        }
        if (
            tool_name not in PHASE06_TOOL_NAMES - {"neutron_agent_health"}
            or name != "host_label"
            or not required
            or actual_fields != expected_fields
            or parameter["pattern"] != r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$"
            or isinstance(parameter["max_length"], bool)
            or parameter["max_length"] != 64
        ):
            raise RegistryProjectionError("registry host parameter is unsupported")
        schema["pattern"] = parameter["pattern"]
        schema["maxLength"] = parameter["max_length"]
    elif validation == "closed_value":
        expected_fields = REGISTRY_PARAMETER_REQUIRED_FIELDS | {
            "max_length",
            "allowed_values",
            "default",
        }
        expected_values = {
            "window_class": ["15m", "30m", "1h"],
            "line_limit_class": ["small", "medium", "large"],
        }.get(name)
        values = parameter.get("allowed_values")
        if (
            tool_name not in PHASE06_TOOL_NAMES - {"neutron_agent_health"}
            or name not in {"window_class", "line_limit_class"}
            or required
            or actual_fields != expected_fields
            or values != expected_values
            or isinstance(parameter["max_length"], bool)
            or not isinstance(parameter["max_length"], int)
            or parameter["max_length"] not in {3, 6}
            or not isinstance(parameter["default"], str)
            or parameter["default"] not in values
        ):
            raise RegistryProjectionError(
                "registry closed-value parameter is unsupported"
            )
        schema["maxLength"] = parameter["max_length"]
        schema["enum"] = list(values)
        schema["default"] = parameter["default"]
    else:
        raise RegistryProjectionError("registry parameter validator is unsupported")
    return position, name, schema


def _project_registry_tool_schema(
    tool_name: str, parameters: list[Any]
) -> dict[str, Any]:
    projected: list[tuple[int, str, dict[str, Any]]] = [
        _project_registry_parameter(parameter, tool_name) for parameter in parameters
    ]
    positions = [item[0] for item in projected]
    names = [item[1] for item in projected]
    if len(set(positions)) != len(positions) or len(set(names)) != len(names):
        raise RegistryProjectionError("registry parameters are not unique")
    projected.sort(key=lambda item: item[0])
    if [item[0] for item in projected] != list(range(1, len(projected) + 1)):
        raise RegistryProjectionError("registry parameter positions are unsupported")
    if tool_name in {SERVER_BASIC_INFO, SERVER_NETWORK_INFO} and [
        item[1] for item in projected
    ] != ["server_identifier"]:
        raise RegistryProjectionError(
            "initial parameter order diverges from the contract"
        )
    properties = {name: schema for _, name, schema in projected}
    required = [
        name
        for _, name, schema in projected
        if next(
            parameter["name"] == name and parameter["required"]
            for parameter in parameters
        )
    ]
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def load_exposed_tool_schemas(
    fixed_registry_path: Path = REGISTRY_PATH,
) -> list[dict[str, Any]]:
    """Project the exact initial allowlist from the accepted registry."""

    registry = _load_registry_object(fixed_registry_path)
    if set(registry) != REGISTRY_ROOT_FIELDS:
        raise RegistryProjectionError("registry root fields are not closed")
    if (
        registry.get("schema_version") != 1
        or registry.get("registry_name") != "ai-ops-assistant-tool-runner-steps-01-07"
    ):
        raise RegistryProjectionError("registry identity is unsupported")
    defaults = registry.get("defaults")
    if not isinstance(defaults, Mapping) or set(defaults) != REGISTRY_DEFAULT_FIELDS:
        raise RegistryProjectionError("registry defaults are unsupported")
    tools = registry.get("tools")
    if not isinstance(tools, list):
        raise RegistryProjectionError("registry tools must be an array")

    selected_tools: dict[str, Mapping[str, Any]] = {}
    projected_schemas: dict[str, dict[str, Any]] = {}
    seen_names: set[str] = set()
    for raw_tool in tools:
        name, parameters = _validate_registry_tool_shape(raw_tool)
        if name not in KNOWN_REGISTRY_TOOL_NAMES:
            raise RegistryProjectionError("registry tool is not in the exposure policy")
        if name in seen_names:
            raise RegistryProjectionError("registry tool names are not unique")
        seen_names.add(name)
        projected_schema = _project_registry_tool_schema(name, parameters)
        selected_tools[name] = raw_tool
        projected_schemas[name] = projected_schema

    if not set(INITIAL_TOOL_NAMES) <= set(selected_tools):
        raise RegistryProjectionError("initial registry tool set is incomplete")
    for name in INITIAL_TOOL_NAMES:
        if projected_schemas[name] != INITIAL_TOOL_SCHEMAS[name]:
            raise RegistryProjectionError(
                "initial tool schema diverges from the contract"
            )

    return [
        {
            "name": name,
            "description": selected_tools[name]["description"]
            + PUBLIC_DESCRIPTION_SUFFIX,
            "inputSchema": projected_schemas[name],
        }
        for name in INITIAL_TOOL_NAMES
    ]


def _reject_duplicate_resource_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ResourceCatalogError("resource catalog contains duplicate keys")
        result[key] = value
    return result


def _validate_resource_content(content: Any) -> int:
    if not isinstance(content, str) or not content:
        raise ResourceCatalogError("resource content is not non-empty text")
    try:
        content_bytes = len(content.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise ResourceCatalogError("resource content is not valid UTF-8") from exc
    if content_bytes > RESOURCE_MAX_CONTENT_BYTES:
        raise ResourceCatalogError("resource content exceeds its fixed bound")
    if any(pattern.search(content) for pattern in RESOURCE_CONTENT_FORBIDDEN_PATTERNS):
        raise ResourceCatalogError("resource content contains prohibited material")
    return content_bytes


def validate_resource_catalog(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the complete reviewed catalog before exposing any resource."""

    if not isinstance(value, Mapping) or set(value) != RESOURCE_CATALOG_ROOT_FIELDS:
        raise ResourceCatalogError("resource catalog fields are not closed")
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] != RESOURCE_CATALOG_SCHEMA_VERSION
        or value["catalog_name"] != RESOURCE_CATALOG_NAME
    ):
        raise ResourceCatalogError("resource catalog identity is unsupported")

    resources = value["resources"]
    expected_uris = tuple(REVIEWED_RESOURCE_METADATA)
    if not isinstance(resources, list) or len(resources) != len(expected_uris):
        raise ResourceCatalogError("resource catalog entries are not exact")

    canonical_resources: list[dict[str, Any]] = []
    seen_uris: set[str] = set()
    seen_names: set[str] = set()
    total_content_bytes = 0
    for resource, expected_uri in zip(resources, expected_uris, strict=True):
        if not isinstance(resource, Mapping) or set(resource) != RESOURCE_ENTRY_FIELDS:
            raise ResourceCatalogError("resource entry fields are not closed")
        metadata = REVIEWED_RESOURCE_METADATA[expected_uri]
        uri = resource["uri"]
        name = resource["name"]
        description = resource["description"]
        mime_type = resource["mime_type"]
        if (
            not isinstance(uri, str)
            or uri != expected_uri
            or uri in seen_uris
            or not isinstance(name, str)
            or name != metadata["name"]
            or name in seen_names
            or description != metadata["description"]
            or mime_type != RESOURCE_MIME_TYPE
        ):
            raise ResourceCatalogError("resource metadata is not approved")
        seen_uris.add(uri)
        seen_names.add(name)
        total_content_bytes += _validate_resource_content(resource["content"])
        canonical_resources.append(dict(resource))

    if seen_uris != set(expected_uris) or seen_names != {
        item["name"] for item in REVIEWED_RESOURCE_METADATA.values()
    }:
        raise ResourceCatalogError("resource catalog allowlist is incomplete")
    canonical = {
        "schema_version": RESOURCE_CATALOG_SCHEMA_VERSION,
        "catalog_name": RESOURCE_CATALOG_NAME,
        "resources": canonical_resources,
    }
    try:
        catalog_bytes = len(
            json.dumps(canonical, ensure_ascii=False, allow_nan=False).encode("utf-8")
        )
    except (TypeError, ValueError) as exc:
        raise ResourceCatalogError("resource catalog is not JSON-safe") from exc
    if (
        total_content_bytes > RESOURCE_MAX_CATALOG_BYTES
        or catalog_bytes > RESOURCE_MAX_CATALOG_BYTES
    ):
        raise ResourceCatalogError("resource catalog exceeds its fixed bound")
    return canonical


def load_resource_catalog(path: Path = RESOURCE_CATALOG_PATH) -> dict[str, Any]:
    """Load the fixed catalog artifact; resource reads never use this path."""

    if path.is_symlink() or not path.is_file():
        raise ResourceCatalogError("resource catalog is unavailable")
    try:
        raw = path.read_bytes()
        if len(raw) > RESOURCE_MAX_CATALOG_BYTES:
            raise ResourceCatalogError("resource catalog exceeds its fixed bound")
        payload = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_resource_keys
        )
    except ResourceCatalogError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResourceCatalogError("resource catalog cannot be decoded") from exc
    return validate_resource_catalog(payload)


def list_curated_resources(validated_catalog: Mapping[str, Any]) -> list[Any]:
    """Return deterministic MCP descriptors from the validated catalog."""

    _require_sdk()
    catalog = validate_resource_catalog(validated_catalog)
    return [
        types.Resource(
            uri=resource["uri"],
            name=resource["name"],
            description=resource["description"],
            mimeType=resource["mime_type"],
            size=len(resource["content"].encode("utf-8")),
        )
        for resource in catalog["resources"]
    ]


def read_curated_resource(
    uri: Any, validated_catalog: Mapping[str, Any]
) -> list[ReadResourceContents]:
    """Read only embedded content selected by the reviewed URI allowlist."""

    catalog = validate_resource_catalog(validated_catalog)
    requested_uri = str(uri)
    for resource in catalog["resources"]:
        if resource["uri"] == requested_uri:
            return [
                ReadResourceContents(
                    content=resource["content"], mime_type=resource["mime_type"]
                )
            ]
    raise ResourceCatalogError("resource URI is not approved")


def _reject_duplicate_envelope_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RunnerProtocolError("runner envelope contains duplicate keys")
        result[key] = value
    return result


def _reject_nonfinite_json_constant(value: str) -> None:
    raise RunnerProtocolError(f"runner envelope contains non-finite JSON: {value}")


def decode_runner_envelope(
    raw: bytes,
    *,
    expected_tool: str | None = None,
    expected_arguments: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Decode exactly one bounded, closed runner result line."""

    if not isinstance(raw, bytes) or len(raw) > RUNNER_MAX_ENVELOPE_BYTES:
        raise RunnerProtocolError("runner envelope exceeds the fixed bound")
    payload = raw[:-1] if raw.endswith(b"\n") else raw
    if not payload or b"\n" in payload or b"\r" in payload:
        raise RunnerProtocolError("runner output is not one complete result line")
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_envelope_keys,
            parse_constant=_reject_nonfinite_json_constant,
        )
    except RunnerProtocolError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RunnerProtocolError("runner output is not valid JSON") from exc
    if not isinstance(value, Mapping) or set(value) != RUNNER_ENVELOPE_FIELDS:
        raise RunnerProtocolError("runner envelope fields are not closed")
    envelope = dict(value)
    if envelope["schema_version"] != "1.0":
        raise RunnerProtocolError("runner envelope schema is unsupported")
    if envelope["status"] not in RUNNER_STATUSES:
        raise RunnerProtocolError("runner envelope status is unsupported")
    if not isinstance(envelope["tool"], str) or not envelope["tool"]:
        raise RunnerProtocolError("runner envelope tool is invalid")
    if not isinstance(envelope["arguments"], Mapping):
        raise RunnerProtocolError("runner envelope arguments are invalid")
    if envelope["data"] is not None and not isinstance(envelope["data"], Mapping):
        raise RunnerProtocolError("runner envelope data is invalid")
    error = envelope["error"]
    if error is not None:
        if (
            not isinstance(error, Mapping)
            or set(error) != RUNNER_ERROR_FIELDS
            or not isinstance(error["class"], str)
            or not error["class"]
            or not isinstance(error["message"], str)
            or not error["message"]
        ):
            raise RunnerProtocolError("runner envelope error is invalid")
    if (envelope["status"] == "ok") != (error is None):
        raise RunnerProtocolError("runner envelope status and error are inconsistent")
    if (
        isinstance(envelope["exit_code"], bool)
        or not isinstance(envelope["exit_code"], int)
        or envelope["exit_code"] != RUNNER_STATUS_EXIT_CODES[envelope["status"]]
    ):
        raise RunnerProtocolError("runner envelope exit status is inconsistent")
    if (
        isinstance(envelope["duration_ms"], bool)
        or not isinstance(envelope["duration_ms"], int)
        or envelope["duration_ms"] < 0
    ):
        raise RunnerProtocolError("runner envelope duration is invalid")
    if not isinstance(envelope["truncated"], bool):
        raise RunnerProtocolError("runner envelope truncation flag is invalid")
    if (
        not isinstance(envelope["timestamp"], str)
        or RUNNER_TIMESTAMP_PATTERN.fullmatch(envelope["timestamp"]) is None
    ):
        raise RunnerProtocolError("runner envelope timestamp is invalid")
    if not isinstance(envelope["correlation_id"], str):
        raise RunnerProtocolError("runner envelope correlation ID is invalid")
    try:
        correlation_id = uuid.UUID(envelope["correlation_id"])
    except (ValueError, AttributeError) as exc:
        raise RunnerProtocolError("runner envelope correlation ID is invalid") from exc
    if correlation_id.version != 4:
        raise RunnerProtocolError("runner envelope correlation ID is invalid")
    if envelope["stdout"] is not None or envelope["stderr"] is not None:
        raise RunnerProtocolError("runner envelope contains raw output")
    if expected_tool is not None and envelope["tool"] != expected_tool:
        raise RunnerProtocolError("runner envelope tool does not match request")
    if expected_arguments is not None and dict(envelope["arguments"]) != dict(
        expected_arguments
    ):
        raise RunnerProtocolError("runner envelope arguments do not match request")
    return envelope


def map_runner_envelope_to_mcp(envelope: Mapping[str, Any]) -> Any:
    """Return the accepted runner envelope as structured and deterministic text."""

    _require_sdk()
    structured = dict(envelope)
    text = json.dumps(
        structured,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=text)],
        structuredContent=structured,
        isError=structured["status"] != "ok",
    )


def adapter_error_result(error_class: str) -> Any:
    """Return only a fixed adapter error, never raw process or exception text."""

    _require_sdk()
    if error_class not in ADAPTER_ERROR_CLASSES:
        error_class = "adapter_redaction_error"
    structured = {"error": {"class": error_class}}
    return types.CallToolResult(
        content=[
            types.TextContent(
                type="text",
                text=json.dumps(structured, separators=(",", ":")),
            )
        ],
        structuredContent=structured,
        isError=True,
    )


def _validate_runner_arguments(
    tool_name: str, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    if tool_name not in INITIAL_TOOL_NAMES:
        raise RunnerProtocolError("requested tool is not enabled in this slice")
    if not isinstance(arguments, Mapping):
        raise RunnerRequestValidationError("request arguments are invalid")

    schema = INITIAL_TOOL_SCHEMAS[tool_name]
    if set(arguments) != set(schema["properties"]):
        raise RunnerRequestValidationError("request arguments are invalid")
    validated = dict(arguments)
    if tool_name == PROJECT_RESOURCE_SUMMARY:
        return validated

    value = validated["server_identifier"]
    if not isinstance(value, str):
        raise RunnerRequestValidationError("request arguments are invalid")
    try:
        value_length = len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise RunnerRequestValidationError("request arguments are invalid") from exc
    if (
        not value_length <= SERVER_IDENTIFIER_MAX_LENGTH
        or "/" in value
        or ".." in value
        or re.fullmatch(SAFE_IDENTIFIER_PATTERN, value) is None
    ):
        raise RunnerRequestValidationError("request arguments are invalid")
    return validated


def _runner_argv(tool_name: str, arguments: Mapping[str, Any]) -> list[str]:
    argv = [str(RUNNER_PYTHON), str(RUNNER_SCRIPT), tool_name]
    for parameter_name in INITIAL_TOOL_SCHEMAS[tool_name]["required"]:
        argv.extend(["--arg", f"{parameter_name}={arguments[parameter_name]}"])
    return argv


def _signal_process_group(process: Any, force: bool) -> None:
    """Signal a runner child session, falling back to its child handle."""

    pid = getattr(process, "pid", None)
    if isinstance(pid, int) and pid > 0:
        try:
            os.killpg(pid, signal.SIGKILL if force else signal.SIGTERM)
            return
        except ProcessLookupError:
            return
        except OSError:
            pass
    method = getattr(process, "kill" if force else "terminate", None)
    if callable(method):
        try:
            method()
        except OSError:
            pass


async def _terminate_and_reap(process: Any, grace_seconds: int) -> None:
    """Terminate one runner process group and reap it within fixed grace."""

    _signal_process_group(process, force=False)
    try:
        await asyncio.wait_for(
            ChildProcessRegistry._wait_for_child(process), timeout=grace_seconds
        )
        return
    except asyncio.TimeoutError:
        _signal_process_group(process, force=True)
    try:
        await asyncio.wait_for(
            ChildProcessRegistry._wait_for_child(process), timeout=grace_seconds
        )
    except asyncio.TimeoutError as exc:
        raise RunnerProtocolError("runner cleanup exceeded the fixed grace") from exc


async def _communicate_bounded(process: Any) -> tuple[bytes, bytes]:
    """Read runner streams without retaining more than each fixed bound plus one."""

    stdout_stream = getattr(process, "stdout", None)
    stderr_stream = getattr(process, "stderr", None)
    if not callable(getattr(stdout_stream, "read", None)) or not callable(
        getattr(stderr_stream, "read", None)
    ):
        communicate = getattr(process, "communicate", None)
        if not callable(communicate):
            raise RunnerProtocolError("runner streams are unavailable")
        return await communicate()

    streams = (
        (stdout_stream, RUNNER_MAX_ENVELOPE_BYTES),
        (stderr_stream, RUNNER_MAX_STDERR_BYTES),
    )

    async def read_stream(stream: Any, limit: int) -> bytes:
        retained = bytearray()
        while len(retained) <= limit:
            chunk = await stream.read(limit + 1 - len(retained))
            if not isinstance(chunk, bytes):
                raise RunnerProtocolError("runner stream is not byte data")
            if not chunk:
                return bytes(retained)
            retained.extend(chunk)
        return bytes(retained)

    tasks = [
        asyncio.create_task(read_stream(stream, limit)) for stream, limit in streams
    ]
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        results: list[bytes | None] = [None, None]
        for index, (task, (_, limit)) in enumerate(zip(tasks, streams)):
            if task in done:
                value = task.result()
                if len(value) > limit:
                    raise RunnerProtocolError("runner output exceeds the fixed bound")
                results[index] = value
        pending_tasks = [task for task in tasks if task not in done]
        values = await asyncio.gather(*pending_tasks)
        pending_indices = [
            index for index, task in enumerate(tasks) if task not in done
        ]
        for index, value in zip(pending_indices, values):
            results[index] = value
        if results[0] is None or results[1] is None:
            raise RunnerProtocolError("runner streams are incomplete")
        if len(results[0]) > RUNNER_MAX_ENVELOPE_BYTES:
            raise RunnerProtocolError("runner envelope exceeds the fixed bound")
        if len(results[1]) > RUNNER_MAX_STDERR_BYTES:
            raise RunnerProtocolError("runner stderr exceeds the fixed bound")
        await ChildProcessRegistry._wait_for_child(process)
        return results[0], results[1]
    finally:
        pending_tasks = [task for task in tasks if not task.done()]
        for task in pending_tasks:
            task.cancel()
        if pending_tasks:
            await asyncio.gather(*pending_tasks, return_exceptions=True)


async def invoke_revised_runner(
    tool_name: str,
    arguments: Mapping[str, Any],
    *,
    child_registry: ChildProcessRegistry | None = None,
) -> dict[str, Any]:
    """Invoke exactly the fixed runner argv for one exposed project tool."""

    validated_arguments = _validate_runner_arguments(tool_name, arguments)
    argv = _runner_argv(tool_name, validated_arguments)
    registry = child_registry or ChildProcessRegistry()
    try:
        process = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
    except (OSError, ValueError) as exc:
        raise RunnerUnavailableError("fixed runner is unavailable") from exc

    registry.register(process)
    reaped = False
    try:
        try:
            stdout, stderr = await asyncio.wait_for(
                _communicate_bounded(process),
                timeout=RUNNER_TIMEOUT_SECONDS_BY_TOOL[tool_name],
            )
            reaped = True
        except asyncio.TimeoutError as exc:
            await _terminate_and_reap(process, registry._cleanup_grace_seconds)
            reaped = True
            raise RunnerProtocolError("runner exceeded the fixed deadline") from exc
        except asyncio.CancelledError:
            try:
                await _terminate_and_reap(process, registry._cleanup_grace_seconds)
                reaped = True
            finally:
                raise
        except Exception as exc:
            await _terminate_and_reap(process, registry._cleanup_grace_seconds)
            reaped = True
            raise RunnerProtocolError("runner communication failed") from exc
        if not isinstance(stdout, bytes) or not isinstance(stderr, bytes):
            raise RunnerProtocolError("runner output is not byte data")
        if len(stdout) > RUNNER_MAX_ENVELOPE_BYTES:
            raise RunnerProtocolError("runner envelope exceeds the fixed bound")
        if len(stderr) > RUNNER_MAX_STDERR_BYTES:
            raise RunnerProtocolError("runner stderr exceeds the fixed bound")
        envelope = decode_runner_envelope(
            stdout,
            expected_tool=tool_name,
            expected_arguments=validated_arguments,
        )
        if process.returncode != envelope["exit_code"]:
            raise RunnerProtocolError("runner exit status does not match envelope")
        return envelope
    finally:
        if reaped:
            registry.unregister(process)


def _require_sdk() -> None:
    if Server is None or stdio_server is None:
        raise AdapterDependencyError("approved MCP stdio SDK is unavailable")


def _prompt_definition(prompt_name: str) -> PromptDefinition:
    for definition in _PROMPT_DEFINITIONS:
        if definition.name == prompt_name:
            return definition
    raise PromptContractError("prompt request is not approved")


def list_diagnostic_prompts(
    exposed_tool_names: Collection[str] | None = None,
) -> list[Any]:
    """Return only complete, deterministic prompt descriptors."""

    _require_sdk()
    available_tools = set(
        INITIAL_TOOL_NAMES if exposed_tool_names is None else exposed_tool_names
    )
    return [
        types.Prompt(
            name=definition.name,
            description=definition.description,
            arguments=(
                []
                if definition.argument_name is None
                else [
                    types.PromptArgument(
                        name=definition.argument_name,
                        description="Safe project-visible server name or ID.",
                        required=True,
                    )
                ]
            ),
        )
        for definition in _PROMPT_DEFINITIONS
        if set(definition.required_tools) <= available_tools
    ]


def validate_prompt_arguments(
    prompt_name: str,
    arguments: Mapping[str, Any] | None,
) -> dict[str, str]:
    """Validate the closed prompt argument map without performing I/O."""

    definition = _prompt_definition(prompt_name)
    if definition.argument_name is None:
        if arguments is None:
            return {}
        if not isinstance(arguments, Mapping) or arguments:
            raise PromptContractError("prompt arguments are invalid")
        return {}

    if not isinstance(arguments, Mapping) or set(arguments) != {
        definition.argument_name
    }:
        raise PromptContractError("prompt arguments are invalid")
    value = arguments[definition.argument_name]
    if not isinstance(value, str):
        raise PromptContractError("prompt arguments are invalid")
    try:
        value_length = len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise PromptContractError("prompt arguments are invalid") from exc
    if (
        not value_length <= SERVER_IDENTIFIER_MAX_LENGTH
        or "/" in value
        or ".." in value
        or re.fullmatch(SAFE_IDENTIFIER_PATTERN, value) is None
    ):
        raise PromptContractError("prompt arguments are invalid")
    return {definition.argument_name: value}


def _prompt_sections() -> str:
    return "\n\n".join(f"## {heading}\n" for heading in PROMPT_REQUIRED_HEADINGS)


def _prompt_workflow_instructions(
    prompt_name: str, server_identifier: str | None
) -> str:
    if prompt_name == PROJECT_SUMMARY_PROMPT:
        return (
            f"Use only the exact approved tool name present in discovery: "
            f"`{PROJECT_RESOURCE_SUMMARY}`. Do not request or use any other tool.\n\n"
            "This workflow is limited to project-visible diagnostic resources. "
            "It does not request or establish cloud-wide, server, guest, network, "
            "volume, host, or service-health evidence."
        )
    if server_identifier is None:
        raise PromptContractError("prompt identifier is unavailable")
    if prompt_name == SERVER_INSPECTION_PROMPT:
        return (
            "Use only this exact ordered sequence when the named tools are present "
            "in discovery:\n"
            f"1. `{SERVER_BASIC_INFO}` with "
            f"`{PROMPT_SERVER_IDENTIFIER_ARGUMENT}={server_identifier}`.\n"
            f"2. `{SERVER_NETWORK_INFO}` with the same exact "
            f"`{PROMPT_SERVER_IDENTIFIER_ARGUMENT}={server_identifier}`.\n\n"
            "Keep server, network, port, fixed-IP, volume, and config-drive "
            "evidence separate. Do not infer guest or application health."
        )
    if prompt_name == METADATA_DIAGNOSIS_PROMPT:
        return (
            "Use only this exact ordered sequence when the named tools are present "
            "in discovery:\n"
            f"1. `{PROJECT_RESOURCE_SUMMARY}` to establish project-visible context.\n"
            f"2. `{SERVER_BASIC_INFO}` with the exact "
            f"`{PROMPT_SERVER_IDENTIFIER_ARGUMENT}={server_identifier}`.\n"
            f"3. `{SERVER_NETWORK_INFO}` with the same exact "
            f"`{PROMPT_SERVER_IDENTIFIER_ARGUMENT}={server_identifier}`.\n\n"
            "Treat any operator-reported metadata or cloud-init symptom as a report, "
            "not as tool-observed evidence. Label guest behavior, routes and packet "
            "delivery, Neutron proxy/agent state, Nova metadata, listeners "
            "including port 8775, host state, and logs as unavailable unless a "
            "separate approved contract exposes them."
        )
    raise PromptContractError("prompt request is not approved")


def _prompt_common_instructions() -> str:
    return (
        "Preserve each tool result's status, correlation ID, duration, timestamp, "
        "and truncation semantics. Treat unavailable, timeout, denied, "
        "validation_error, error, empty sections, and truncation as evidence gaps, "
        "not as healthy signals. Keep operator-reported symptoms separate from "
        "tool-observed evidence.\n\n"
        "If an earlier result or section is unavailable, denied, failed, timed out, "
        "validation-invalid, mismatched, or truncated, stop further narrowing. Do "
        "not guess, retry, or substitute a second identifier.\n\n"
        "Never invent a tool, result, identifier, credential, observation, command, "
        "or root cause. Refuse create, update, delete, restart, stop, install, "
        "edit, SSH, sudo, shell, raw OpenStack, file, database, package, "
        "service-control, mutation, or remediation requests.\n\n"
        "The final section may contain only high-level follow-up. All recommendations "
        "are manual, advisory, and unexecuted, and must not include commands or "
        "remediation instructions."
    )


def _render_prompt_text(
    definition: PromptDefinition, server_identifier: str | None
) -> str:
    return "\n\n".join(
        (
            _prompt_workflow_instructions(definition.name, server_identifier),
            _prompt_common_instructions(),
            _prompt_sections(),
            "Summarize only evidence returned by the approved tools in the exact "
            "sequence above.",
        )
    )


def render_diagnostic_prompt(
    prompt_name: str,
    arguments: Mapping[str, Any] | None,
    exposed_tool_names: Collection[str],
) -> Any:
    """Render one bounded, non-executable diagnostic prompt result."""

    _require_sdk()
    definition = _prompt_definition(prompt_name)
    validated_arguments = validate_prompt_arguments(prompt_name, arguments)
    available_tools = set(exposed_tool_names)
    if not set(definition.required_tools) <= available_tools:
        raise PromptContractError("prompt dependencies are unavailable")
    server_identifier = validated_arguments.get(PROMPT_SERVER_IDENTIFIER_ARGUMENT)
    text = _render_prompt_text(definition, server_identifier)
    if len(text.encode("utf-8")) > PROMPT_MAX_MESSAGE_BYTES:
        raise PromptContractError("prompt message exceeds the fixed bound")
    return types.GetPromptResult(
        description=definition.description,
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(type="text", text=text),
            )
        ],
    )


def create_server(
    configuration: AdapterConfiguration,
    *,
    fixed_registry_path: Path = REGISTRY_PATH,
    lifecycle: ChildProcessRegistry | None = None,
    catalog: Mapping[str, Any] | None = None,
) -> Any:
    """Construct the server with the approved tools and static resources."""

    _require_sdk()
    if configuration.transport != "stdio":
        raise AdapterConfigurationError("local transport is not stdio")
    exposed_tools = load_exposed_tool_schemas(fixed_registry_path)
    exposed_tool_names = frozenset(tool["name"] for tool in exposed_tools)
    validated_catalog = (
        load_resource_catalog(configuration.resource_catalog_path)
        if catalog is None
        else validate_resource_catalog(catalog)
    )
    resource_descriptors = list_curated_resources(validated_catalog)
    child_registry = lifecycle or ChildProcessRegistry(
        configuration.cleanup_grace_seconds
    )
    runner_semaphore = asyncio.Semaphore(1)
    server = Server(SERVICE_NAME, version=SERVICE_VERSION)

    @server.list_tools()
    async def handle_list_tools() -> list[Any]:
        return [types.Tool(**tool) for tool in exposed_tools]

    @server.list_resources()
    async def handle_list_resources() -> list[Any]:
        return resource_descriptors

    @server.read_resource()
    async def handle_read_resource(uri: Any) -> list[ReadResourceContents]:
        return read_curated_resource(uri, validated_catalog)

    @server.list_prompts()
    async def handle_list_prompts() -> list[Any]:
        return list_diagnostic_prompts(exposed_tool_names)

    @server.get_prompt()
    async def handle_get_prompt(
        prompt_name: str, arguments: dict[str, str] | None = None
    ) -> Any:
        validated_arguments = validate_prompt_arguments(prompt_name, arguments)
        return render_diagnostic_prompt(
            prompt_name, validated_arguments, exposed_tool_names
        )

    @server.call_tool(validate_input=False)
    async def handle_call_tool(tool_name: str, arguments: dict[str, Any]) -> Any:
        if tool_name not in INITIAL_TOOL_NAMES:
            return adapter_error_result("adapter_unavailable")
        try:
            validated_arguments = _validate_runner_arguments(tool_name, arguments)
        except RunnerRequestValidationError:
            return adapter_error_result("request_validation_error")
        try:
            async with runner_semaphore:
                envelope = await invoke_revised_runner(
                    tool_name,
                    validated_arguments,
                    child_registry=child_registry,
                )
        except RunnerRequestValidationError:
            return adapter_error_result("request_validation_error")
        except asyncio.CancelledError:
            return adapter_error_result("runner_protocol_error")
        except RunnerUnavailableError:
            return adapter_error_result("runner_unavailable")
        except RunnerProtocolError:
            return adapter_error_result("runner_protocol_error")
        return map_runner_envelope_to_mcp(envelope)

    return server


async def run_server(
    configuration: AdapterConfiguration,
    lifecycle: ChildProcessRegistry | None = None,
    *,
    fixed_registry_path: Path = REGISTRY_PATH,
) -> None:
    """Serve the registry-derived server over stdio and always clean up children."""

    _require_sdk()
    child_registry = lifecycle or ChildProcessRegistry(
        configuration.cleanup_grace_seconds
    )
    server = create_server(
        configuration,
        fixed_registry_path=fixed_registry_path,
        lifecycle=child_registry,
    )
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    finally:
        await child_registry.cleanup()


def _write_error(error_class: str) -> None:
    sys.stderr.write(f"{error_class}\n")
    sys.stderr.flush()


def main(configuration_path: Path = CONFIG_PATH) -> int:
    """Run the fixed local process, returning non-zero on unresolved state."""

    try:
        configuration = load_configuration(configuration_path)
        _require_sdk()
        asyncio.run(run_server(configuration))
    except AdapterConfigurationError:
        _write_error("adapter_configuration_error")
        return CONFIGURATION_ERROR_EXIT_CODE
    except ResourceCatalogError:
        _write_error("resource_catalog_error")
        return CONFIGURATION_ERROR_EXIT_CODE
    except RegistryProjectionError:
        _write_error("schema_equivalence_error")
        return CONFIGURATION_ERROR_EXIT_CODE
    except AdapterDependencyError:
        _write_error("adapter_dependency_error")
        return DEPENDENCY_ERROR_EXIT_CODE
    except KeyboardInterrupt:
        return 130
    except Exception:
        _write_error("adapter_lifecycle_error")
        return CONFIGURATION_ERROR_EXIT_CODE
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
