#!/usr/bin/env python3
"""Disabled fail-closed skeleton for the internal MCP network boundary."""

from __future__ import annotations

import argparse
import contextlib
import ipaddress
import json
import logging
import re
import ssl
import subprocess
import sys
import threading
import time
from collections import deque
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import uvicorn
from mcp import types
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.server.lowlevel import Server
from mcp.server.streamable_http import StreamableHTTPServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.routing import Route

CONFIG_PATH = Path("/etc/ai-ops-assistant/mcp/config.json")
SERVICE_NAME = "ai-ops-assistant-mcp"
SERVICE_VERSION = "0.1.0"
SERVICE_DISABLED_EXIT_CODE = 3
CONFIGURATION_ERROR_EXIT_CODE = 2
DEFAULT_ENABLED = False
DEFAULT_EXPLICIT_ACTIVATION = False

RUNNER_PYTHON = Path("/opt/openstack-ai-ops-assistant/mcp/venv/bin/python")
RUNNER_SCRIPT = Path(
    "/opt/openstack-ai-ops-assistant/scripts/tool_runner/aiops_tool_runner.py"
)
PROJECT_RESOURCE_SUMMARY = "project_resource_summary"
PROJECT_RESOURCE_SUMMARY_TIMEOUT_SECONDS = 45
SERVER_BASIC_INFO = "server_basic_info"
SERVER_NETWORK_INFO = "server_network_info"
INITIAL_TOOL_NAMES = (
    PROJECT_RESOURCE_SUMMARY,
    SERVER_BASIC_INFO,
    SERVER_NETWORK_INFO,
)
TOOL_TIMEOUT_SECONDS = {
    PROJECT_RESOURCE_SUMMARY: 45,
    SERVER_BASIC_INFO: 30,
    SERVER_NETWORK_INFO: 45,
}
SERVER_IDENTIFIER_PATTERN = r"^[A-Za-z0-9._:-]+$"
SERVER_IDENTIFIER_MAX_LENGTH = 255
SERVER_BASIC_INFO_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "server_identifier": {
            "type": "string",
            "description": "Server name or ID using the approved safe identifier character set.",
            "pattern": SERVER_IDENTIFIER_PATTERN,
            "maxLength": SERVER_IDENTIFIER_MAX_LENGTH,
        }
    },
    "required": ["server_identifier"],
    "additionalProperties": False,
}
SERVER_NETWORK_INFO_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "server_identifier": {
            "type": "string",
            "description": "Server name or ID using the approved safe identifier character set.",
            "pattern": SERVER_IDENTIFIER_PATTERN,
            "maxLength": SERVER_IDENTIFIER_MAX_LENGTH,
        }
    },
    "required": ["server_identifier"],
    "additionalProperties": False,
}
RESOURCE_CATALOG_PATH = Path(
    "/opt/openstack-ai-ops-assistant/mcp/mcp_resource_catalog.json"
)
RESOURCE_CATALOG_SCHEMA_VERSION = 1
RESOURCE_CATALOG_NAME = "ai-ops-assistant-mcp-resources-steps-01-04"
RESOURCE_MAX_CONTENT_BYTES = 65536
RESOURCE_MAX_CATALOG_BYTES = 262144
RESOURCE_MIME_TYPE = "text/markdown"
REVIEWED_RESOURCE_METADATA = {
    "aiops://policy/diagnostic-safety": {
        "name": "diagnostic-safety",
        "description": "Read-only diagnostic safety policy and runner boundary.",
    },
    "aiops://runbooks/metadata-troubleshooting": {
        "name": "metadata-troubleshooting",
        "description": "Safe evidence order for metadata troubleshooting.",
    },
    "aiops://architecture/lab-summary": {
        "name": "lab-architecture-summary",
        "description": "Sanitized OpenStack lab topology and service placement.",
    },
}
RUNNER_MAX_ENVELOPE_BYTES = 262144
RUNNER_STATUSES = frozenset(
    {"ok", "error", "denied", "validation_error", "timeout", "unavailable"}
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

PROJECT_RESOURCE_SUMMARY_INPUT_SCHEMA = {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": False,
}


TOOL_INPUT_SCHEMAS = {
    PROJECT_RESOURCE_SUMMARY: PROJECT_RESOURCE_SUMMARY_INPUT_SCHEMA,
    SERVER_BASIC_INFO: SERVER_BASIC_INFO_INPUT_SCHEMA,
    SERVER_NETWORK_INFO: SERVER_NETWORK_INFO_INPUT_SCHEMA,
}
EXPECTED_FIELDS = frozenset(
    {
        "schema_version",
        "transport",
        "bind_interface",
        "bind_address",
        "port",
        "endpoint_path",
        "allowed_source_cidrs",
        "tls_certificate_path",
        "tls_private_key_path",
        "tls_client_ca_path",
        "tls_client_crl_path",
        "authorized_principal_uri",
        "max_header_bytes",
        "max_request_body_bytes",
        "max_response_body_bytes",
        "max_concurrent_sessions",
        "max_concurrent_runner_children",
        "requests_per_minute",
        "request_burst",
        "session_idle_seconds",
        "request_deadline_seconds",
    }
)

EXPECTED_BIND_INTERFACE = "eth0"
EXPECTED_BIND_ADDRESS = "192.168.121.21"
EXPECTED_PORT = 8443
EXPECTED_ENDPOINT_PATH = "/mcp"
EXPECTED_SOURCE_NETWORK = ipaddress.ip_network("192.168.121.0/24")
EXPECTED_PRINCIPAL_URI = "spiffe://openstack-lab/mcp/mcp-internal-reader"
EXPECTED_TLS_CERTIFICATE_PATH = Path("/etc/ai-ops-assistant/mcp/tls/server.crt")
EXPECTED_TLS_PRIVATE_KEY_PATH = Path("/etc/ai-ops-assistant/mcp/tls/server.key")
EXPECTED_TLS_CLIENT_CA_PATH = Path("/etc/ai-ops-assistant/mcp/tls/client-ca.crt")
EXPECTED_TLS_CLIENT_CRL_PATH = Path("/etc/ai-ops-assistant/mcp/tls/client-ca.crl")
MAX_LOG_EVENTS_PER_MINUTE = 100
RATE_LIMIT_RETRY_AFTER_SECONDS = 60
RUNNER_CLEANUP_GRACE_SECONDS = 5
LIFECYCLE_EVENT_TYPES = frozenset(
    {"mcp_lifecycle", "mcp_authentication", "mcp_authorization"}
)
LIFECYCLE_OUTCOMES = frozenset({"started", "stopped", "accepted", "denied"})
LIFECYCLE_REASONS = frozenset(
    {
        "configuration_error",
        "service_disabled",
        "authentication_failed",
        "authorization_denied",
        "source_not_allowed",
        "request_limit",
        "runner_unavailable",
        "runner_protocol_error",
        "shutdown_timeout",
        "null",
    }
)
LOGGER = logging.getLogger(SERVICE_NAME)


class ConfigurationError(ValueError):
    """Raised when the closed network configuration is not acceptable."""


class NetworkMCPDisabledError(RuntimeError):
    """Raised whenever the not-yet-activated network service is requested."""


class AuthenticationError(ValueError):
    """Raised when the authenticated principal is not allowlisted."""


class RequestValidationError(ValueError):
    """Raised when the first-tool request does not match its fixed schema."""


class ResourceCatalogError(ValueError):
    """Raised when the embedded resource catalog is not closed and reviewed."""


class RunnerProtocolError(ValueError):
    """Raised when the fixed runner does not return a safe envelope."""


class RequestLimitError(RuntimeError):
    """Raised when a request exceeds one of the fixed admission bounds."""


class LifecycleError(RuntimeError):
    """Raised when a child cannot be terminated and reaped safely."""


class PrincipalRateLimiter:
    """Small token-bucket limiter with bounded per-principal state."""

    def __init__(
        self,
        requests_per_minute: int,
        burst: int,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if requests_per_minute <= 0 or burst <= 0:
            raise ValueError("rate limits must be positive")
        self._rate = requests_per_minute / 60.0
        self._capacity = float(burst)
        self._clock = clock
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def allow(self, principal: str) -> bool:
        """Consume one token, rejecting without queueing when empty."""
        now = self._clock()
        with self._lock:
            tokens, updated = self._buckets.get(principal, (self._capacity, now))
            tokens = min(self._capacity, tokens + max(0.0, now - updated) * self._rate)
            if tokens < 1.0:
                self._buckets[principal] = (tokens, now)
                return False
            self._buckets[principal] = (tokens - 1.0, now)
            return True


class NetworkMCPAdmission:
    """Enforce fixed rate, session, and runner-child limits without queueing."""

    def __init__(self, config: "NetworkMCPConfig") -> None:
        self.rate_limiter = PrincipalRateLimiter(
            config.requests_per_minute, config.request_burst
        )
        self.session_slots = threading.BoundedSemaphore(config.max_concurrent_sessions)
        self.runner_slots = threading.BoundedSemaphore(
            config.max_concurrent_runner_children
        )

    @contextlib.contextmanager
    def request(self, principal: str) -> Any:
        if not self.rate_limiter.allow(principal):
            raise RequestLimitError("request rate limit exceeded")
        if not self.session_slots.acquire(blocking=False):
            raise RequestLimitError("session limit exceeded")
        try:
            if not self.runner_slots.acquire(blocking=False):
                raise RequestLimitError("runner concurrency limit exceeded")
            try:
                yield
            finally:
                self.runner_slots.release()
        finally:
            self.session_slots.release()


def validate_request_bounds(
    config: "NetworkMCPConfig", *, header_bytes: int, body_bytes: int
) -> None:
    """Reject oversized HTTP metadata before MCP/session handling."""
    if (
        not isinstance(header_bytes, int)
        or isinstance(header_bytes, bool)
        or not isinstance(body_bytes, int)
        or isinstance(body_bytes, bool)
    ):
        raise RequestLimitError("request size is invalid")
    if header_bytes < 0 or body_bytes < 0:
        raise RequestLimitError("request size is invalid")
    if header_bytes > config.max_header_bytes:
        raise RequestLimitError("request headers exceed bound")
    if body_bytes > config.max_request_body_bytes:
        raise RequestLimitError("request body exceeds bound")


def validate_response_bounds(config: "NetworkMCPConfig", payload: bytes) -> None:
    """Keep retained response bytes within the fixed aggregate bound."""
    validate_response_bytes(payload, config.max_response_body_bytes)


def validate_response_bytes(payload: bytes, max_bytes: int) -> None:
    """Validate a serialized response against one fixed byte limit."""
    if (
        not isinstance(max_bytes, int)
        or isinstance(max_bytes, bool)
        or max_bytes < 0
        or not isinstance(payload, bytes)
        or len(payload) > max_bytes
    ):
        raise RunnerProtocolError("response exceeds its fixed bound")


def terminate_and_reap_child(
    process: Any, *, grace_seconds: float = RUNNER_CLEANUP_GRACE_SECONDS
) -> None:
    """Terminate, then kill if necessary, and always reap one child."""
    if grace_seconds < 0:
        raise ValueError("cleanup grace cannot be negative")
    try:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=grace_seconds)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=grace_seconds)
        else:
            process.wait(timeout=0)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LifecycleError("runner child was not reaped safely") from exc


class _LifecycleLogLimiter:
    """Bound lifecycle/auth log emission to a fixed rolling one-minute window."""

    def __init__(self, *, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._events: deque[float] = deque()
        self._lock = threading.Lock()

    def allow(self) -> bool:
        now = self._clock()
        with self._lock:
            while self._events and self._events[0] <= now - 60.0:
                self._events.popleft()
            if len(self._events) >= MAX_LOG_EVENTS_PER_MINUTE:
                return False
            self._events.append(now)
            return True


_LIFECYCLE_LOG_LIMITER = _LifecycleLogLimiter()


def emit_lifecycle_event(
    event_type: str,
    outcome: str,
    *,
    principal: str | None = None,
    source_allowed: bool = False,
    reason: str | None = None,
) -> None:
    """Emit only the closed, bounded lifecycle/auth event shape."""
    if event_type not in LIFECYCLE_EVENT_TYPES or outcome not in LIFECYCLE_OUTCOMES:
        raise ValueError("lifecycle event classification is not approved")
    if reason not in LIFECYCLE_REASONS - {"null"}:
        reason = None
    event = {
        "schema_version": "1.0",
        "event_type": event_type,
        "outcome": outcome,
        "principal": (
            "mcp-internal-reader" if principal == "mcp-internal-reader" else "unknown"
        ),
        "source_allowed": bool(source_allowed),
        "reason": reason,
    }
    if _LIFECYCLE_LOG_LIMITER.allow():
        LOGGER.info("mcp lifecycle event", extra={"mcp_event": event})


@dataclass(frozen=True)
class NetworkMCPConfig:
    """The exact non-secret configuration accepted by the network service."""

    schema_version: int
    transport: str
    bind_interface: str
    bind_address: str
    port: int
    endpoint_path: str
    allowed_source_cidrs: tuple[str, ...]
    tls_certificate_path: Path
    tls_private_key_path: Path
    tls_client_ca_path: Path
    tls_client_crl_path: Path
    authorized_principal_uri: str
    max_header_bytes: int
    max_request_body_bytes: int
    max_response_body_bytes: int
    max_concurrent_sessions: int
    max_concurrent_runner_children: int
    requests_per_minute: int
    request_burst: int
    session_idle_seconds: int
    request_deadline_seconds: int

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "NetworkMCPConfig":
        if set(value) != EXPECTED_FIELDS:
            raise ConfigurationError("configuration fields are not exact")

        cidrs = value["allowed_source_cidrs"]
        if (
            not isinstance(cidrs, list)
            or len(cidrs) != 1
            or not all(isinstance(item, str) for item in cidrs)
        ):
            raise ConfigurationError("allowed_source_cidrs is not exact")

        integer_fields = (
            "schema_version",
            "port",
            "max_header_bytes",
            "max_request_body_bytes",
            "max_response_body_bytes",
            "max_concurrent_sessions",
            "max_concurrent_runner_children",
            "requests_per_minute",
            "request_burst",
            "session_idle_seconds",
            "request_deadline_seconds",
        )
        for field in integer_fields:
            field_value = value[field]
            if not isinstance(field_value, int) or isinstance(field_value, bool):
                raise ConfigurationError(f"{field} must be an integer")

        string_fields = (
            "transport",
            "bind_interface",
            "bind_address",
            "endpoint_path",
            "tls_certificate_path",
            "tls_private_key_path",
            "tls_client_ca_path",
            "tls_client_crl_path",
            "authorized_principal_uri",
        )
        if any(not isinstance(value[field], str) for field in string_fields):
            raise ConfigurationError("configuration contains a non-string field")

        config = cls(
            schema_version=value["schema_version"],
            transport=value["transport"],
            bind_interface=value["bind_interface"],
            bind_address=value["bind_address"],
            port=value["port"],
            endpoint_path=value["endpoint_path"],
            allowed_source_cidrs=tuple(cidrs),
            tls_certificate_path=Path(value["tls_certificate_path"]),
            tls_private_key_path=Path(value["tls_private_key_path"]),
            tls_client_ca_path=Path(value["tls_client_ca_path"]),
            tls_client_crl_path=Path(value["tls_client_crl_path"]),
            authorized_principal_uri=value["authorized_principal_uri"],
            max_header_bytes=value["max_header_bytes"],
            max_request_body_bytes=value["max_request_body_bytes"],
            max_response_body_bytes=value["max_response_body_bytes"],
            max_concurrent_sessions=value["max_concurrent_sessions"],
            max_concurrent_runner_children=value["max_concurrent_runner_children"],
            requests_per_minute=value["requests_per_minute"],
            request_burst=value["request_burst"],
            session_idle_seconds=value["session_idle_seconds"],
            request_deadline_seconds=value["request_deadline_seconds"],
        )
        validate_fixed_configuration(config)
        return config


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in pairs:
        if key in result:
            raise ConfigurationError("duplicate configuration key")
        result[key] = item
    return result


def load_configuration(path: Path = CONFIG_PATH) -> NetworkMCPConfig:
    """Load the exact closed configuration without applying defaults."""
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        ConfigurationError,
    ) as exc:
        raise ConfigurationError("unable to load network MCP configuration") from exc
    if not isinstance(payload, dict):
        raise ConfigurationError("network MCP configuration must be an object")
    return NetworkMCPConfig.from_mapping(payload)


def validate_bind_scope(config: NetworkMCPConfig) -> None:
    """Reject every bind scope except the owner-approved fixed address."""
    if (
        config.bind_interface != EXPECTED_BIND_INTERFACE
        or config.bind_address != EXPECTED_BIND_ADDRESS
        or config.port != EXPECTED_PORT
        or config.endpoint_path != EXPECTED_ENDPOINT_PATH
    ):
        raise ConfigurationError("network bind scope is not approved")
    if config.bind_address in {"0.0.0.0", "127.0.0.1", "::", "0:0:0:0:0:0:0:0"}:
        raise ConfigurationError("wildcard or loopback bind is forbidden")
    try:
        address = ipaddress.ip_address(config.bind_address)
        networks = tuple(
            ipaddress.ip_network(cidr) for cidr in config.allowed_source_cidrs
        )
    except ValueError as exc:
        raise ConfigurationError(
            "network address or source network is invalid"
        ) from exc
    if address.is_loopback or address.is_unspecified or len(networks) != 1:
        raise ConfigurationError("network bind scope is invalid")
    if networks[0] != EXPECTED_SOURCE_NETWORK:
        raise ConfigurationError("source network is not approved")


def validate_tls_auth_configuration(
    config: NetworkMCPConfig, *, require_material: bool = False
) -> None:
    """Validate fixed TLS/auth references; optionally inspect material paths."""
    expected_paths = (
        (config.tls_certificate_path, EXPECTED_TLS_CERTIFICATE_PATH),
        (config.tls_private_key_path, EXPECTED_TLS_PRIVATE_KEY_PATH),
        (config.tls_client_ca_path, EXPECTED_TLS_CLIENT_CA_PATH),
        (config.tls_client_crl_path, EXPECTED_TLS_CLIENT_CRL_PATH),
    )
    if any(actual != expected for actual, expected in expected_paths):
        raise ConfigurationError("TLS material paths are not approved")
    if config.authorized_principal_uri != EXPECTED_PRINCIPAL_URI:
        raise ConfigurationError("authorized principal is not approved")
    if require_material:
        for path, _ in expected_paths:
            try:
                metadata = path.lstat()
            except OSError as exc:
                raise ConfigurationError("TLS material is unavailable") from exc
            if not path.is_file() or path.is_symlink() or not metadata:
                raise ConfigurationError(
                    "TLS material must be a regular non-symlink file"
                )


def validate_fixed_configuration(config: NetworkMCPConfig) -> None:
    """Validate all fixed values before any SDK or network object is started."""
    if config.schema_version != 1 or config.transport != "streamable-http":
        raise ConfigurationError("configuration schema or transport is not approved")
    validate_bind_scope(config)
    validate_tls_auth_configuration(config)
    expected_limits = {
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
    if any(
        getattr(config, name) != expected for name, expected in expected_limits.items()
    ):
        raise ConfigurationError("configuration limits are not approved")


def build_tls_context(config: NetworkMCPConfig) -> ssl.SSLContext:
    """Build the fixed TLS context without opening a socket."""
    validate_fixed_configuration(config)
    validate_tls_auth_configuration(config, require_material=True)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_cert_chain(
        certfile=str(config.tls_certificate_path),
        keyfile=str(config.tls_private_key_path),
    )
    context.load_verify_locations(cafile=str(config.tls_client_ca_path))
    context.verify_flags |= ssl.VERIFY_CRL_CHECK_LEAF
    return context


def authorize_principal(principal_uri: str) -> str:
    """Map exactly one certificate-derived URI to the fixed MCP principal."""
    if principal_uri != EXPECTED_PRINCIPAL_URI:
        raise AuthenticationError("authenticated principal is not authorized")
    return "mcp-internal-reader"


def validate_tool_request(
    tool_name: str, arguments: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Apply the fixed MCP defense-in-depth schema for an initial tool."""
    if tool_name not in INITIAL_TOOL_NAMES:
        raise RequestValidationError("tool is not exposed by the initial policy")
    if arguments is not None and not isinstance(arguments, Mapping):
        raise RequestValidationError("tool arguments must be an object")
    validated = {} if arguments is None else dict(arguments)
    if tool_name == PROJECT_RESOURCE_SUMMARY:
        if validated:
            raise RequestValidationError("project resource summary takes no arguments")
        return validated
    if set(validated) != {"server_identifier"}:
        raise RequestValidationError("server identifier is required and exclusive")
    server_identifier = validated["server_identifier"]
    if (
        not isinstance(server_identifier, str)
        or not server_identifier
        or len(server_identifier) > SERVER_IDENTIFIER_MAX_LENGTH
        or re.fullmatch(SERVER_IDENTIFIER_PATTERN, server_identifier) is None
    ):
        raise RequestValidationError("server identifier is not safe")
    return validated


def validate_project_resource_summary_request(
    tool_name: str, arguments: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Retain the first-tool compatibility seam over the initial policy."""
    if tool_name != PROJECT_RESOURCE_SUMMARY:
        raise RequestValidationError("tool is not exposed by the first-tool slice")
    return validate_tool_request(tool_name, arguments)


def fixed_runner_argv(tool_name: str, arguments: Mapping[str, Any]) -> list[str]:
    """Build only the fixed runner argv for an approved initial tool."""
    validated = validate_tool_request(tool_name, arguments)
    argv = [str(RUNNER_PYTHON), str(RUNNER_SCRIPT), tool_name]
    if tool_name != PROJECT_RESOURCE_SUMMARY:
        argv.extend(("--arg", f"server_identifier={validated['server_identifier']}"))
    return argv


def decode_runner_envelope(
    payload: bytes,
    *,
    expected_tool: str = PROJECT_RESOURCE_SUMMARY,
    expected_arguments: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Decode one bounded, complete, non-secret runner result envelope."""
    if expected_tool not in INITIAL_TOOL_NAMES:
        raise RunnerProtocolError("runner envelope tool is not approved")
    expected = (
        validate_tool_request(expected_tool, expected_arguments)
        if expected_arguments is not None
        else validate_tool_request(expected_tool, {})
    )
    if not isinstance(payload, bytes) or len(payload) > RUNNER_MAX_ENVELOPE_BYTES:
        raise RunnerProtocolError("runner envelope exceeds its bound")
    try:
        envelope = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RunnerProtocolError("runner envelope is not valid JSON") from exc
    if not isinstance(envelope, dict) or set(envelope) != RUNNER_ENVELOPE_FIELDS:
        raise RunnerProtocolError("runner envelope fields are not exact")
    if envelope["schema_version"] != "1.0":
        raise RunnerProtocolError("runner envelope schema is unsupported")
    if envelope["tool"] != expected_tool:
        raise RunnerProtocolError("runner envelope tool is unexpected")
    if envelope["status"] not in RUNNER_STATUSES:
        raise RunnerProtocolError("runner envelope status is unsupported")
    if envelope["arguments"] != expected:
        raise RunnerProtocolError("runner envelope arguments are unexpected")
    for field in ("exit_code", "duration_ms"):
        value = envelope[field]
        if not isinstance(value, int) or isinstance(value, bool):
            raise RunnerProtocolError("runner envelope numeric field is invalid")
    if envelope["stdout"] is not None or envelope["stderr"] is not None:
        raise RunnerProtocolError("runner envelope contains raw process output")
    if not isinstance(envelope["truncated"], bool):
        raise RunnerProtocolError("runner envelope truncation flag is invalid")
    if not isinstance(envelope["timestamp"], str) or not envelope["timestamp"]:
        raise RunnerProtocolError("runner envelope timestamp is invalid")
    if (
        not isinstance(envelope["correlation_id"], str)
        or not envelope["correlation_id"]
    ):
        raise RunnerProtocolError("runner envelope correlation is invalid")
    error = envelope["error"]
    if error is not None and (
        not isinstance(error, dict)
        or set(error) != {"class", "message"}
        or not all(isinstance(item, str) and item for item in error.values())
    ):
        raise RunnerProtocolError("runner envelope error is invalid")
    return envelope


def invoke_fixed_runner(
    tool_name: str,
    arguments: Mapping[str, Any] | None = None,
    *,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    """Invoke only the fixed runner command and decode its bounded envelope."""
    validated = validate_tool_request(tool_name, arguments)
    argv = fixed_runner_argv(tool_name, validated)
    try:
        completed = runner(
            argv,
            shell=False,
            check=False,
            capture_output=True,
            timeout=TOOL_TIMEOUT_SECONDS[tool_name],
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RunnerProtocolError("fixed runner did not complete safely") from exc
    stdout = getattr(completed, "stdout", None)
    if not isinstance(stdout, bytes):
        raise RunnerProtocolError("fixed runner output is not bounded bytes")
    return decode_runner_envelope(
        stdout, expected_tool=tool_name, expected_arguments=validated
    )


def runner_envelope_to_mcp_result(
    envelope: Mapping[str, Any],
    *,
    max_response_body_bytes: int = RUNNER_MAX_ENVELOPE_BYTES,
) -> types.CallToolResult:
    """Preserve the complete envelope and add one deterministic compact text item."""
    try:
        serialized = json.dumps(
            envelope,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise RunnerProtocolError("runner envelope is not JSON-safe") from exc
    tool_name = envelope.get("tool")
    arguments = envelope.get("arguments")
    if not isinstance(tool_name, str) or not isinstance(arguments, Mapping):
        raise RunnerProtocolError("runner envelope request identity is invalid")
    validated = decode_runner_envelope(
        serialized.encode("utf-8"),
        expected_tool=tool_name,
        expected_arguments=arguments,
    )
    text = json.dumps(
        validated,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    validate_response_bytes(text.encode("utf-8"), max_response_body_bytes)
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=text)],
        structuredContent=validated,
        isError=validated["status"] != "ok",
    )


def handle_authenticated_initial_tool(
    principal_uri: str,
    tool_name: str,
    arguments: Mapping[str, Any] | None = None,
    *,
    runner: Callable[..., Any] = subprocess.run,
    admission: NetworkMCPAdmission | None = None,
    max_response_body_bytes: int = RUNNER_MAX_ENVELOPE_BYTES,
) -> types.CallToolResult:
    """Authenticate and execute exactly one initial registry tool."""
    try:
        authorize_principal(principal_uri)
    except AuthenticationError:
        emit_lifecycle_event(
            "mcp_authentication",
            "denied",
            source_allowed=False,
            reason="authentication_failed",
        )
        raise
    emit_lifecycle_event(
        "mcp_authentication",
        "accepted",
        principal="mcp-internal-reader",
        source_allowed=True,
    )
    validated_arguments = validate_tool_request(tool_name, arguments)
    if admission is None:
        envelope = invoke_fixed_runner(tool_name, validated_arguments, runner=runner)
    else:
        with admission.request("mcp-internal-reader"):
            envelope = invoke_fixed_runner(
                tool_name, validated_arguments, runner=runner
            )
    emit_lifecycle_event(
        "mcp_authorization",
        "accepted",
        principal="mcp-internal-reader",
        source_allowed=True,
    )
    return runner_envelope_to_mcp_result(
        envelope, max_response_body_bytes=max_response_body_bytes
    )


def handle_authenticated_server_basic_info(
    principal_uri: str,
    arguments: Mapping[str, Any] | None = None,
    *,
    runner: Callable[..., Any] = subprocess.run,
) -> types.CallToolResult:
    """Authenticate and execute the fixed server basic information tool."""
    return handle_authenticated_initial_tool(
        principal_uri, SERVER_BASIC_INFO, arguments, runner=runner
    )


def handle_authenticated_server_network_info(
    principal_uri: str,
    arguments: Mapping[str, Any] | None = None,
    *,
    runner: Callable[..., Any] = subprocess.run,
) -> types.CallToolResult:
    """Authenticate and execute the fixed server network information tool."""
    return handle_authenticated_initial_tool(
        principal_uri, SERVER_NETWORK_INFO, arguments, runner=runner
    )


def handle_authenticated_project_resource_summary(
    principal_uri: str,
    arguments: Mapping[str, Any] | None = None,
    *,
    runner: Callable[..., Any] = subprocess.run,
) -> types.CallToolResult:
    """Authenticate, validate, execute, and map the one approved fixture tool."""
    authorize_principal(principal_uri)
    validated_arguments = validate_project_resource_summary_request(
        PROJECT_RESOURCE_SUMMARY, arguments
    )
    envelope = invoke_fixed_runner(
        PROJECT_RESOURCE_SUMMARY, validated_arguments, runner=runner
    )
    return runner_envelope_to_mcp_result(envelope)


def create_authenticated_first_tool_server(
    config: NetworkMCPConfig,
    principal_uri: str,
    *,
    catalog: Mapping[str, Any] | None = None,
    runner: Callable[..., Any] = subprocess.run,
) -> Server[Any, Any]:
    """Compatibility name for the complete authenticated initial surface."""
    return create_authenticated_tool_server(
        config, principal_uri, catalog=catalog, runner=runner
    )


def _reject_duplicate_resource_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in pairs:
        if key in result:
            raise ResourceCatalogError("duplicate resource catalog key")
        result[key] = item
    return result


def validate_resource_catalog(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the exact embedded catalog before exposing any resource."""
    if not isinstance(value, Mapping) or set(value) != {
        "schema_version",
        "catalog_name",
        "resources",
    }:
        raise ResourceCatalogError("resource catalog fields are not exact")
    if value["schema_version"] != RESOURCE_CATALOG_SCHEMA_VERSION:
        raise ResourceCatalogError("resource catalog schema is unsupported")
    if value["catalog_name"] != RESOURCE_CATALOG_NAME:
        raise ResourceCatalogError("resource catalog name is not approved")
    resources = value["resources"]
    if not isinstance(resources, list) or len(resources) != len(
        REVIEWED_RESOURCE_METADATA
    ):
        raise ResourceCatalogError("resource catalog entries are not exact")

    expected_uris = tuple(REVIEWED_RESOURCE_METADATA)
    canonical_resources: list[dict[str, Any]] = []
    seen_uris: set[str] = set()
    total_content_bytes = 0
    for resource, expected_uri in zip(resources, expected_uris, strict=True):
        if not isinstance(resource, Mapping) or set(resource) != {
            "uri",
            "name",
            "description",
            "mime_type",
            "content",
        }:
            raise ResourceCatalogError("resource entry fields are not exact")
        uri = resource["uri"]
        metadata = REVIEWED_RESOURCE_METADATA[expected_uri]
        if (
            uri != expected_uri
            or uri in seen_uris
            or resource["name"] != metadata["name"]
            or resource["description"] != metadata["description"]
            or resource["mime_type"] != RESOURCE_MIME_TYPE
        ):
            raise ResourceCatalogError("resource entry metadata is not approved")
        seen_uris.add(uri)
        content = resource["content"]
        if not isinstance(content, str) or not content:
            raise ResourceCatalogError("resource content is not non-empty text")
        content_bytes = len(content.encode("utf-8"))
        if content_bytes > RESOURCE_MAX_CONTENT_BYTES:
            raise ResourceCatalogError("resource content exceeds its bound")
        if re.search(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", content):
            raise ResourceCatalogError("resource contains private-key material")
        if re.search(r"(?i)\b(?:password|token|secret)\s*[:=]", content):
            raise ResourceCatalogError("resource contains secret assignment material")
        if re.search(r"(?i)\bbearer\s+[A-Za-z0-9._~-]+", content):
            raise ResourceCatalogError("resource contains bearer material")
        total_content_bytes += content_bytes
        canonical_resources.append(dict(resource))

    if seen_uris != set(REVIEWED_RESOURCE_METADATA):
        raise ResourceCatalogError("resource catalog URI allowlist is incomplete")
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
        raise ResourceCatalogError("resource catalog exceeds its bound")
    return canonical


def load_resource_catalog(path: Path = RESOURCE_CATALOG_PATH) -> dict[str, Any]:
    """Load only the fixed catalog artifact; resource reads never use this path."""
    try:
        raw = path.read_bytes()
        if len(raw) > RESOURCE_MAX_CATALOG_BYTES:
            raise ResourceCatalogError("resource catalog exceeds its bound")
        payload = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_resource_keys
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        ResourceCatalogError,
    ) as exc:
        raise ResourceCatalogError("unable to load resource catalog") from exc
    return validate_resource_catalog(payload)


def list_curated_resources(catalog: Mapping[str, Any]) -> list[types.Resource]:
    """Return descriptors from the validated static catalog in fixed order."""
    validated = validate_resource_catalog(catalog)
    return [
        types.Resource(
            uri=resource["uri"],
            name=resource["name"],
            description=resource["description"],
            mimeType=resource["mime_type"],
            size=len(resource["content"].encode("utf-8")),
        )
        for resource in validated["resources"]
    ]


def read_curated_resource(
    uri: Any, catalog: Mapping[str, Any]
) -> list[ReadResourceContents]:
    """Read only embedded content; never interpret a URI as a path or URL."""
    validated = validate_resource_catalog(catalog)
    requested_uri = str(uri)
    for resource in validated["resources"]:
        if resource["uri"] == requested_uri:
            return [ReadResourceContents(resource["content"], RESOURCE_MIME_TYPE)]
    raise ResourceCatalogError("unknown curated resource URI")


INITIAL_TOOL_DESCRIPTIONS = {
    PROJECT_RESOURCE_SUMMARY: "List project-visible OpenStack resources using the fixed read-only diagnostic.",
    SERVER_BASIC_INFO: "Show basic information for one project-visible server.",
    SERVER_NETWORK_INFO: "Show server ports and permitted related network information.",
}


def project_initial_tool_definitions() -> tuple[dict[str, Any], ...]:
    """Project only the approved initial registry subset into MCP metadata."""
    return tuple(
        {
            "name": tool_name,
            "description": INITIAL_TOOL_DESCRIPTIONS[tool_name],
            "inputSchema": TOOL_INPUT_SCHEMAS[tool_name],
        }
        for tool_name in INITIAL_TOOL_NAMES
    )


def create_authenticated_tool_server(
    config: NetworkMCPConfig,
    principal_uri: str,
    *,
    catalog: Mapping[str, Any] | None = None,
    runner: Callable[..., Any] = subprocess.run,
) -> Server[Any, Any]:
    """Create the authenticated three-tool server with an exact static catalog."""
    validate_fixed_configuration(config)
    authorize_principal(principal_uri)
    validated_catalog = (
        load_resource_catalog()
        if catalog is None
        else validate_resource_catalog(catalog)
    )
    server = create_mcp_server(config)
    admission = NetworkMCPAdmission(config)

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(**definition)
            for definition in project_initial_tool_definitions()
        ]

    @server.call_tool(validate_input=False)
    async def call_tool(name: str, arguments: dict[str, Any]) -> types.CallToolResult:
        return handle_authenticated_initial_tool(
            principal_uri,
            name,
            arguments,
            runner=runner,
            admission=admission,
            max_response_body_bytes=config.max_response_body_bytes,
        )

    @server.list_resources()
    async def list_resources() -> list[types.Resource]:
        return list_curated_resources(validated_catalog)

    @server.read_resource()
    async def read_resource(uri: Any) -> list[ReadResourceContents]:
        return read_curated_resource(uri, validated_catalog)

    return server


def create_authenticated_three_tool_server(
    config: NetworkMCPConfig,
    principal_uri: str,
    *,
    catalog: Mapping[str, Any] | None = None,
    runner: Callable[..., Any] = subprocess.run,
) -> Server[Any, Any]:
    """Named compatibility factory for the complete initial MCP surface."""
    return create_authenticated_tool_server(
        config, principal_uri, catalog=catalog, runner=runner
    )


def create_mcp_server(config: NetworkMCPConfig) -> Server[Any, Any]:
    """Create an empty low-level server; tools and resources are not registered."""
    validate_fixed_configuration(config)
    return Server(name=SERVICE_NAME, version=SERVICE_VERSION)


def create_streamable_http_transport() -> StreamableHTTPServerTransport:
    """Create the approved JSON-only transport without binding it."""
    return StreamableHTTPServerTransport(
        mcp_session_id=None,
        is_json_response_enabled=True,
        event_store=None,
    )


def create_session_manager(
    server: Server[Any, Any], config: NetworkMCPConfig
) -> StreamableHTTPSessionManager:
    """Create the bounded stateful manager without entering its run context."""
    validate_fixed_configuration(config)
    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[f"{EXPECTED_BIND_ADDRESS}:{EXPECTED_PORT}"],
        allowed_origins=[],
    )
    return StreamableHTTPSessionManager(
        app=server,
        event_store=None,
        json_response=True,
        stateless=False,
        security_settings=security,
        session_idle_timeout=config.session_idle_seconds,
    )


@dataclass(frozen=True)
class NetworkMCPApplication:
    """Future application components, retained as a non-starting seam."""

    application: Starlette
    session_manager: StreamableHTTPSessionManager
    tls_context: ssl.SSLContext


@contextlib.asynccontextmanager
async def _manager_lifespan(
    _: Starlette, manager: StreamableHTTPSessionManager
) -> AsyncIterator[None]:
    async with manager.run():
        yield


def create_application(
    config: NetworkMCPConfig,
    *,
    enabled: bool = DEFAULT_ENABLED,
    explicit_activation: bool = DEFAULT_EXPLICIT_ACTIVATION,
) -> NetworkMCPApplication:
    """Keep application creation disabled until authentication is implemented."""
    validate_fixed_configuration(config)
    if not enabled or not explicit_activation:
        raise NetworkMCPDisabledError("network MCP service is disabled")
    raise NetworkMCPDisabledError("network MCP authentication is not activated")


def build_uvicorn_config(
    application: Starlette, config: NetworkMCPConfig, tls_context: ssl.SSLContext
) -> uvicorn.Config:
    """Prepare explicit TLS server settings without constructing a server."""
    validate_fixed_configuration(config)
    return uvicorn.Config(
        application,
        host=config.bind_address,
        port=config.port,
        proxy_headers=False,
        forwarded_allow_ips=[],
        reload=False,
        workers=1,
        ssl_context_factory=lambda _config, _create_default: tls_context,
    )


def main(arguments: Sequence[str] | None = None) -> int:
    """Validate configuration and exit without activating a listener."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parsed = parser.parse_args(arguments)
    try:
        load_configuration(parsed.config)
    except ConfigurationError:
        print("network MCP configuration rejected", file=sys.stderr)
        return CONFIGURATION_ERROR_EXIT_CODE
    if not DEFAULT_ENABLED or not DEFAULT_EXPLICIT_ACTIVATION:
        return SERVICE_DISABLED_EXIT_CODE
    return CONFIGURATION_ERROR_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())
