#!/usr/bin/env python3
"""Fail-closed loopback Responses API gateway with no upstream transport."""

from __future__ import annotations

import argparse
import fcntl
import http.client
import json
import os
import re
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import parse_qsl, urlsplit

from redaction import (
    DuplicateKeyError,
    MalformedJsonError,
    RedactionError,
    RedactionResult,
    redact_remote_payload,
    scan_redacted_payload,
    strict_json_loads,
)

POLICY_SCHEMA_VERSION = 1
POLICY_KEYS = frozenset(
    {
        "schema_version",
        "bind_host",
        "bind_port",
        "service_identity",
        "route",
        "max_request_bytes",
        "upstream_host",
        "upstream_port",
        "upstream_route",
        "upstream_timeout_seconds",
        "max_response_bytes",
    }
)
LOOPBACK_HOSTS = frozenset({"127.0.0.1"})
MODELS_ROUTE = "/v1/models"
EXPECTED_MODELS_QUERY = (("client_version", "0.144.1"),)
FIXED_UPSTREAM_HOST = "chatgpt.com"
FIXED_UPSTREAM_PORT = 443
FIXED_UPSTREAM_ROUTE = "/backend-api/codex/responses"


class GatewayPolicyError(ValueError):
    """Raised when a gateway policy cannot safely define a local listener."""


@dataclass(frozen=True)
class GatewayPolicy:
    """Fixed local-listener contract; it intentionally has no upstream fields."""

    bind_host: str
    bind_port: int
    service_identity: str
    route: str
    max_request_bytes: int
    upstream_host: str
    upstream_port: int
    upstream_route: str
    upstream_timeout_seconds: int
    max_response_bytes: int

    @classmethod
    def from_mapping(cls, value: Any) -> "GatewayPolicy":
        if not isinstance(value, dict) or set(value) != POLICY_KEYS:
            raise GatewayPolicyError("gateway policy has unsupported fields")
        schema_version = value["schema_version"]
        if (
            isinstance(schema_version, bool)
            or not isinstance(schema_version, int)
            or schema_version != POLICY_SCHEMA_VERSION
        ):
            raise GatewayPolicyError("gateway policy schema version is unsupported")
        bind_host = value["bind_host"]
        if not isinstance(bind_host, str) or bind_host not in LOOPBACK_HOSTS:
            raise GatewayPolicyError("gateway listener must use a loopback address")
        bind_port = value["bind_port"]
        if (
            isinstance(bind_port, bool)
            or not isinstance(bind_port, int)
            or not 0 < bind_port < 65536
        ):
            raise GatewayPolicyError("gateway port is invalid")
        if value["service_identity"] != "aiops-provider":
            raise GatewayPolicyError("gateway service identity is not approved")
        if value["route"] != "/v1/responses":
            raise GatewayPolicyError("gateway route is not approved")
        max_request_bytes = value["max_request_bytes"]
        if (
            isinstance(max_request_bytes, bool)
            or not isinstance(max_request_bytes, int)
            or max_request_bytes <= 0
        ):
            raise GatewayPolicyError("gateway request bound is invalid")
        upstream_host = value["upstream_host"]
        if upstream_host != FIXED_UPSTREAM_HOST:
            raise GatewayPolicyError("gateway upstream host is not approved")
        upstream_port = value["upstream_port"]
        if upstream_port != FIXED_UPSTREAM_PORT:
            raise GatewayPolicyError("gateway upstream port is not approved")
        upstream_route = value["upstream_route"]
        if upstream_route != FIXED_UPSTREAM_ROUTE:
            raise GatewayPolicyError("gateway upstream route is not approved")
        upstream_timeout_seconds = value["upstream_timeout_seconds"]
        if (
            isinstance(upstream_timeout_seconds, bool)
            or not isinstance(upstream_timeout_seconds, int)
            or not 0 < upstream_timeout_seconds <= 30
        ):
            raise GatewayPolicyError("gateway upstream timeout is invalid")
        max_response_bytes = value["max_response_bytes"]
        if (
            isinstance(max_response_bytes, bool)
            or not isinstance(max_response_bytes, int)
            or not 0 < max_response_bytes <= max_request_bytes
        ):
            raise GatewayPolicyError("gateway response bound is invalid")
        return cls(
            bind_host=value["bind_host"],
            bind_port=value["bind_port"],
            service_identity=value["service_identity"],
            route=value["route"],
            max_request_bytes=value["max_request_bytes"],
            upstream_host=upstream_host,
            upstream_port=upstream_port,
            upstream_route=upstream_route,
            upstream_timeout_seconds=upstream_timeout_seconds,
            max_response_bytes=max_response_bytes,
        )


REVIEWED_MODEL = "gpt-5.6-terra"
FIXED_FAKE_UPSTREAM_PATH = "/v1/responses"
FIXED_FAKE_UPSTREAM_HEADERS = {
    "Accept": "text/event-stream",
    "Content-Type": "application/json",
}


class ProviderRequestError(ValueError):
    """Raised when a provider request falls outside the reviewed local contract."""


@dataclass(frozen=True)
class FakeUpstreamRequest:
    """Rebuilt redacted request sent only to the injected local test sink."""

    path: str
    headers: dict[str, str]
    body: bytes
    correlation_id: str


@dataclass(frozen=True)
class FakeUpstreamResponse:
    """Fixed fake response shape for local streaming acceptance tests."""

    status: int
    body_chunks: tuple[bytes, ...]


@dataclass(frozen=True)
class UpstreamRequest:
    """Rebuilt HTTPS request with a memory-only authorization header."""

    host: str
    port: int
    path: str
    timeout_seconds: int
    max_response_bytes: int
    headers: dict[str, str]
    body: bytes


HISTORICAL_GATEWAY_EVIDENCE_SCHEMA_VERSION = 1
GATEWAY_EVIDENCE_SCHEMA_VERSION = 2
HISTORICAL_GATEWAY_EVIDENCE_ROUTE = "/v1/responses"
GATEWAY_EVIDENCE_ROUTES = {
    HISTORICAL_GATEWAY_EVIDENCE_SCHEMA_VERSION: HISTORICAL_GATEWAY_EVIDENCE_ROUTE,
    GATEWAY_EVIDENCE_SCHEMA_VERSION: FIXED_UPSTREAM_ROUTE,
}
GATEWAY_EVIDENCE_FIELDS = frozenset(
    {
        "classification_status",
        "correlation_id",
        "model",
        "outcome",
        "redaction_counts",
        "route",
        "schema_version",
        "timestamp_utc",
        "tls_verified",
        "upstream_status_class",
    }
)
GATEWAY_EVIDENCE_COUNT_CATEGORIES = frozenset(
    {"canonical_text", "embedded_json", "identity", "propagated_value", "secret"}
)
GATEWAY_EVIDENCE_OUTCOMES = frozenset(
    {
        "forward_started",
        "upstream_connection_failed",
        "upstream_request_transport_failed",
        "upstream_response_transport_failed",
        "upstream_response_invalid",
        "upstream_response_status_invalid",
        "upstream_response_content_type_invalid",
        "upstream_response_stream_invalid",
        "upstream_non_success",
        "upstream_succeeded",
        "upstream_transport_failed",
    }
)
GATEWAY_EVIDENCE_STAGED_FAILURE_OUTCOMES = frozenset(
    {
        "upstream_connection_failed",
        "upstream_request_transport_failed",
        "upstream_response_transport_failed",
        "upstream_response_invalid",
        "upstream_response_status_invalid",
        "upstream_response_content_type_invalid",
        "upstream_response_stream_invalid",
    }
)
GATEWAY_EVIDENCE_STATUS_CLASSES = frozenset({"1xx", "2xx", "3xx", "4xx", "5xx"})
GATEWAY_EVIDENCE_TIMESTAMP_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)
GATEWAY_EVIDENCE_MAX_REDACTION_COUNT = 10000


class GatewayEvidenceError(ValueError):
    """Raised when a metadata-only gateway evidence event is invalid."""


@dataclass(frozen=True)
class GatewayEvidenceEvent:
    """Allowlisted metadata for one gateway request lifecycle state."""

    timestamp_utc: str
    correlation_id: str
    model: str
    route: str
    classification_status: str
    redaction_counts: tuple[tuple[str, int], ...]
    outcome: str
    upstream_status_class: str | None
    tls_verified: bool | None
    schema_version: int = GATEWAY_EVIDENCE_SCHEMA_VERSION


def serialize_gateway_evidence_event(event: GatewayEvidenceEvent) -> bytes:
    """Serialize one bounded, payload-free gateway evidence event."""
    if not isinstance(event, GatewayEvidenceEvent):
        raise GatewayEvidenceError("gateway evidence event is invalid")
    if (
        isinstance(event.schema_version, bool)
        or not isinstance(event.schema_version, int)
        or event.schema_version != GATEWAY_EVIDENCE_SCHEMA_VERSION
    ):
        raise GatewayEvidenceError("gateway evidence schema is unsupported")
    if not isinstance(event.timestamp_utc, str) or not GATEWAY_EVIDENCE_TIMESTAMP_RE.fullmatch(
        event.timestamp_utc
    ):
        raise GatewayEvidenceError("gateway evidence timestamp is invalid")
    try:
        correlation_uuid = uuid.UUID(event.correlation_id)
    except (AttributeError, ValueError):
        raise GatewayEvidenceError("gateway evidence correlation is invalid") from None
    if correlation_uuid.version != 4:
        raise GatewayEvidenceError("gateway evidence correlation is invalid")
    if event.model != REVIEWED_MODEL or event.route != FIXED_UPSTREAM_ROUTE:
        raise GatewayEvidenceError("gateway evidence route is invalid")
    if event.classification_status not in {"clear", "redacted"}:
        raise GatewayEvidenceError("gateway evidence classification is invalid")
    if event.outcome not in GATEWAY_EVIDENCE_OUTCOMES:
        raise GatewayEvidenceError("gateway evidence outcome is invalid")
    if not isinstance(event.redaction_counts, tuple) or not all(
        isinstance(item, tuple) and len(item) == 2 for item in event.redaction_counts
    ):
        raise GatewayEvidenceError("gateway evidence counts are invalid")
    if tuple(sorted(event.redaction_counts)) != event.redaction_counts:
        raise GatewayEvidenceError("gateway evidence counts are unordered")
    counts: dict[str, int] = {}
    for category, count in event.redaction_counts:
        if (
            category not in GATEWAY_EVIDENCE_COUNT_CATEGORIES
            or isinstance(count, bool)
            or not isinstance(count, int)
            or not 0 <= count <= GATEWAY_EVIDENCE_MAX_REDACTION_COUNT
        ):
            raise GatewayEvidenceError("gateway evidence counts are invalid")
        if category in counts:
            raise GatewayEvidenceError("gateway evidence counts are duplicated")
        counts[category] = count
    if event.outcome == "forward_started":
        if event.upstream_status_class is not None or event.tls_verified is not None:
            raise GatewayEvidenceError("gateway evidence start state is invalid")
    elif event.outcome == "upstream_transport_failed":
        if event.upstream_status_class is not None or event.tls_verified is not False:
            raise GatewayEvidenceError("gateway evidence transport state is invalid")
    elif event.outcome in GATEWAY_EVIDENCE_STAGED_FAILURE_OUTCOMES:
        if event.upstream_status_class is not None or event.tls_verified is not None:
            raise GatewayEvidenceError("gateway evidence transport state is invalid")
    elif (
        event.upstream_status_class not in GATEWAY_EVIDENCE_STATUS_CLASSES
        or event.tls_verified is not True
    ):
        raise GatewayEvidenceError("gateway evidence terminal state is invalid")
    return json.dumps(
        {
            "classification_status": event.classification_status,
            "correlation_id": event.correlation_id,
            "model": event.model,
            "outcome": event.outcome,
            "redaction_counts": counts,
            "route": event.route,
            "schema_version": event.schema_version,
            "timestamp_utc": event.timestamp_utc,
            "tls_verified": event.tls_verified,
            "upstream_status_class": event.upstream_status_class,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def parse_gateway_evidence_record(record: bytes | str) -> GatewayEvidenceEvent:
    """Parse one allowlisted historical or current evidence record."""
    if not isinstance(record, (bytes, str)):
        raise GatewayEvidenceError("gateway evidence record is invalid")

    def unique_mapping(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise GatewayEvidenceError("gateway evidence record is invalid")
            value[key] = item
        return value

    try:
        value = json.loads(record, object_pairs_hook=unique_mapping)
    except (TypeError, ValueError, UnicodeDecodeError):
        raise GatewayEvidenceError("gateway evidence record is invalid") from None
    if not isinstance(value, dict) or frozenset(value) != GATEWAY_EVIDENCE_FIELDS:
        raise GatewayEvidenceError("gateway evidence record is invalid")
    counts = value["redaction_counts"]
    if not isinstance(counts, dict):
        raise GatewayEvidenceError("gateway evidence counts are invalid")
    try:
        event = GatewayEvidenceEvent(
            timestamp_utc=value["timestamp_utc"],
            correlation_id=value["correlation_id"],
            model=value["model"],
            route=value["route"],
            classification_status=value["classification_status"],
            redaction_counts=tuple(sorted(counts.items())),
            outcome=value["outcome"],
            upstream_status_class=value["upstream_status_class"],
            tls_verified=value["tls_verified"],
            schema_version=value["schema_version"],
        )
    except TypeError:
        raise GatewayEvidenceError("gateway evidence record is invalid") from None
    if (
        isinstance(event.schema_version, bool)
        or not isinstance(event.schema_version, int)
        or event.schema_version not in GATEWAY_EVIDENCE_ROUTES
        or event.route != GATEWAY_EVIDENCE_ROUTES[event.schema_version]
    ):
        raise GatewayEvidenceError("gateway evidence schema is unsupported")
    if event.schema_version == GATEWAY_EVIDENCE_SCHEMA_VERSION:
        serialize_gateway_evidence_event(event)
    else:
        serialize_gateway_evidence_event(
            replace(
                event,
                schema_version=GATEWAY_EVIDENCE_SCHEMA_VERSION,
                route=FIXED_UPSTREAM_ROUTE,
            )
        )
    return event


GATEWAY_EVIDENCE_MAX_RECORD_BYTES = 4096
GATEWAY_EVIDENCE_MIN_LEDGER_BYTES = GATEWAY_EVIDENCE_MAX_RECORD_BYTES
GATEWAY_EVIDENCE_MAX_LEDGER_BYTES = 65536


class GatewayEvidenceWriter(Protocol):
    """Append validated metadata records without exposing a query interface."""

    def append(self, record: bytes) -> None:
        """Durably append one newline-terminated metadata record."""


@dataclass(frozen=True)
class LocalGatewayEvidenceWriter:
    """Append bounded metadata records to an operator-provisioned local ledger."""

    path: Path
    max_bytes: int = GATEWAY_EVIDENCE_MAX_LEDGER_BYTES

    def validate(self) -> None:
        """Create and validate the configured ledger without writing an event."""
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        descriptor = None
        try:
            descriptor = os.open(self.path, flags, 0o600)
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            metadata = os.fstat(descriptor)
            if metadata.st_size > self.max_bytes or metadata.st_mode & 0o777 != 0o600:
                raise GatewayEvidenceError("gateway evidence ledger is unsafe")
        except GatewayEvidenceError:
            raise
        except OSError:
            raise GatewayEvidenceError("gateway evidence write failed") from None
        finally:
            if descriptor is not None:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                    os.close(descriptor)
                except OSError:
                    raise GatewayEvidenceError("gateway evidence write failed") from None

    def append(self, record: bytes) -> None:
        if (
            not isinstance(record, bytes)
            or not record.endswith(b"\n")
            or not 0 < len(record) <= GATEWAY_EVIDENCE_MAX_RECORD_BYTES
        ):
            raise GatewayEvidenceError("gateway evidence record is invalid")
        if (
            isinstance(self.max_bytes, bool)
            or not isinstance(self.max_bytes, int)
            or not GATEWAY_EVIDENCE_MIN_LEDGER_BYTES
            <= self.max_bytes
            <= GATEWAY_EVIDENCE_MAX_LEDGER_BYTES
        ):
            raise GatewayEvidenceError("gateway evidence retention is invalid")
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        descriptor = None
        try:
            descriptor = os.open(self.path, flags, 0o600)
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            if os.fstat(descriptor).st_size + len(record) > self.max_bytes:
                raise GatewayEvidenceError("gateway evidence retention exceeded")
            if os.write(descriptor, record) != len(record):
                raise OSError("gateway evidence record was partially written")
            os.fsync(descriptor)
        except GatewayEvidenceError:
            raise
        except OSError:
            raise GatewayEvidenceError("gateway evidence write failed") from None
        finally:
            if descriptor is not None:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                    os.close(descriptor)
                except OSError:
                    raise GatewayEvidenceError("gateway evidence write failed") from None


def append_gateway_evidence_event(
    writer: GatewayEvidenceWriter, event: GatewayEvidenceEvent
) -> None:
    """Serialize then append one metadata event; any failure is fail-closed."""
    record = serialize_gateway_evidence_event(event) + b"\n"
    if len(record) > GATEWAY_EVIDENCE_MAX_RECORD_BYTES:
        raise GatewayEvidenceError("gateway evidence record is too large")
    try:
        writer.append(record)
    except GatewayEvidenceError:
        raise
    except (AttributeError, OSError, TypeError, ValueError):
        raise GatewayEvidenceError("gateway evidence write failed") from None


def build_gateway_evidence_event(
    result: RedactionResult,
    *,
    outcome: str,
    upstream_status_class: str | None,
    tls_verified: bool | None,
) -> GatewayEvidenceEvent:
    """Construct one strict metadata event from an already-redacted result."""
    if not isinstance(result, RedactionResult):
        raise GatewayEvidenceError("gateway evidence result is invalid")
    return GatewayEvidenceEvent(
        timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        correlation_id=result.correlation_id,
        model=REVIEWED_MODEL,
        route=FIXED_UPSTREAM_ROUTE,
        classification_status=result.classification_status,
        redaction_counts=tuple(sorted(result.redaction_counts.items())),
        outcome=outcome,
        upstream_status_class=upstream_status_class,
        tls_verified=tls_verified,
    )


def upstream_status_class(status: int) -> str:
    """Return the sanitized HTTP status class for a reviewed upstream response."""
    if isinstance(status, bool) or not isinstance(status, int) or not 100 <= status < 600:
        raise GatewayEvidenceError("gateway evidence upstream status is invalid")
    return f"{status // 100}xx"


def provider_error_category(status: int) -> str:
    """Classify one provider 4xx status without inspecting response content."""
    if isinstance(status, bool) or not isinstance(status, int) or not 400 <= status < 500:
        raise GatewayEvidenceError("provider error status is invalid")
    return {
        400: "bad_request",
        401: "authentication",
        403: "permission",
        404: "not_found",
        422: "unprocessable",
        429: "rate_or_quota",
    }.get(status, "other_4xx")


class FakeUpstreamSink(Protocol):
    """Test-only in-memory sink; it must not perform transport I/O."""

    def submit(self, request: FakeUpstreamRequest) -> FakeUpstreamResponse:
        """Capture one rebuilt request and return a synthetic streamed response."""


def load_policy(path: Path) -> GatewayPolicy:
    """Load the fixed policy with duplicate-key rejection."""
    try:
        parsed = strict_json_loads(path.read_bytes())
    except (OSError, DuplicateKeyError, MalformedJsonError) as exc:
        raise GatewayPolicyError("gateway policy is invalid") from exc
    return GatewayPolicy.from_mapping(parsed)


FORBIDDEN_CALLER_UPSTREAM_FIELDS = frozenset(
    {"base_url", "proxy", "transport", "upstream_url"}
)


def validate_provider_request_shape(payload: dict[str, Any]) -> dict[str, Any]:
    """Accept only the observed model/input shape without caller upstream control."""
    if payload.get("model") != REVIEWED_MODEL or "input" not in payload:
        raise ProviderRequestError("provider request shape is not reviewed")
    if any(field in payload for field in FORBIDDEN_CALLER_UPSTREAM_FIELDS):
        raise ProviderRequestError("caller-selected upstream is not allowed")
    return payload


def build_fake_upstream_request(result: RedactionResult) -> FakeUpstreamRequest:
    """Serialize only the redacted payload for the fixed in-memory test sink."""
    return FakeUpstreamRequest(
        path=FIXED_FAKE_UPSTREAM_PATH,
        headers=dict(FIXED_FAKE_UPSTREAM_HEADERS),
        body=json.dumps(
            result.payload, sort_keys=True, separators=(",", ":")
        ).encode("utf-8"),
        correlation_id=result.correlation_id,
    )


UPSTREAM_PROTOCOL_HEADERS = {
    "Accept": "text/event-stream",
    "Content-Type": "application/json",
}

CHATGPT_AUTHORIZATION_MAX_BYTES = 16384
CHATGPT_ACCOUNT_ID_MAX_BYTES = 256
CHATGPT_PROTECTED_SINGLETON_HEADERS = (
    "Authorization",
    "ChatGPT-Account-ID",
    "X-OpenAI-Fedramp",
    "Content-Type",
    "Content-Length",
    "Content-Encoding",
    "Transfer-Encoding",
    "Host",
)


@dataclass(frozen=True, repr=False)
class ChatGPTAuthHeaders:
    """Transient validated ChatGPT authentication-routing values."""

    authorization: str
    account_id: str


def _header_values(headers: Any, name: str) -> list[str]:
    """Return all values for one header or fail without exposing a value."""
    try:
        values = headers.get_all(name, [])
    except (AttributeError, TypeError):
        raise ProviderRequestError(
            "provider authentication headers are unavailable"
        ) from None
    if not isinstance(values, list) or not all(
        isinstance(value, str) for value in values
    ):
        raise ProviderRequestError("provider authentication headers are unavailable")
    return values


def _validate_transient_header_value(
    values: list[str], *, max_bytes: int, prefix: str | None = None
) -> str:
    """Validate one bounded opaque value without including it in an error."""
    if len(values) != 1:
        raise ProviderRequestError("provider authentication headers are unavailable")
    value = values[0]
    try:
        encoded = value.encode("latin-1")
    except UnicodeEncodeError:
        raise ProviderRequestError(
            "provider authentication headers are unavailable"
        ) from None
    if (
        not value
        or value != value.strip()
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or len(encoded) > max_bytes
    ):
        raise ProviderRequestError("provider authentication headers are unavailable")
    if prefix is not None:
        if not value.startswith(prefix):
            raise ProviderRequestError(
                "provider authentication headers are unavailable"
            )
        opaque_value = value[len(prefix) :]
        if not opaque_value or opaque_value != opaque_value.strip():
            raise ProviderRequestError(
                "provider authentication headers are unavailable"
            )
    return value


def validate_chatgpt_auth_headers(headers: Any) -> ChatGPTAuthHeaders:
    """Validate the fail-closed ChatGPT header contract without forwarding it."""
    values_by_name = {
        name: _header_values(headers, name)
        for name in CHATGPT_PROTECTED_SINGLETON_HEADERS
    }
    if any(len(values) > 1 for values in values_by_name.values()):
        raise ProviderRequestError("provider authentication headers are unavailable")
    if values_by_name["X-OpenAI-Fedramp"]:
        raise ProviderRequestError("provider authentication headers are unavailable")
    authorization = _validate_transient_header_value(
        values_by_name["Authorization"],
        max_bytes=CHATGPT_AUTHORIZATION_MAX_BYTES,
        prefix="Bearer ",
    )
    account_id = _validate_transient_header_value(
        values_by_name["ChatGPT-Account-ID"],
        max_bytes=CHATGPT_ACCOUNT_ID_MAX_BYTES,
    )
    return ChatGPTAuthHeaders(authorization=authorization, account_id=account_id)


def build_upstream_request(
    result: RedactionResult, policy: GatewayPolicy, auth_headers: ChatGPTAuthHeaders
) -> UpstreamRequest:
    """Build the fixed HTTPS request from redacted data and validated headers."""
    headers = dict(UPSTREAM_PROTOCOL_HEADERS)
    headers["Authorization"] = auth_headers.authorization
    headers["ChatGPT-Account-ID"] = auth_headers.account_id
    return UpstreamRequest(
        host=policy.upstream_host,
        port=policy.upstream_port,
        path=policy.upstream_route,
        timeout_seconds=policy.upstream_timeout_seconds,
        max_response_bytes=policy.max_response_bytes,
        headers=headers,
        body=json.dumps(result.payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        ),
    )


class UpstreamTransportError(RuntimeError):
    """Raised with a bounded failure stage and no transport details."""

    def __init__(self, outcome: str):
        if outcome not in GATEWAY_EVIDENCE_STAGED_FAILURE_OUTCOMES:
            raise ValueError("upstream transport outcome is invalid")
        self.outcome = outcome
        super().__init__("provider transport failed")


def forward_upstream_request(
    request: UpstreamRequest, connection_factory: Any = http.client.HTTPSConnection
) -> FakeUpstreamResponse:
    """Forward one rebuilt request over verified HTTPS and bound the response."""
    connection = None
    try:
        connection = connection_factory(
            request.host, port=request.port, timeout=request.timeout_seconds
        )
    except (OSError, http.client.HTTPException):
        raise UpstreamTransportError("upstream_connection_failed") from None
    try:
        try:
            connection.request("POST", request.path, body=request.body, headers=request.headers)
        except (OSError, http.client.HTTPException):
            raise UpstreamTransportError("upstream_request_transport_failed") from None
        try:
            response = connection.getresponse()
            status = response.status
            if isinstance(status, bool) or not isinstance(status, int) or not 100 <= status < 600:
                raise UpstreamTransportError("upstream_response_status_invalid")
            if not 200 <= status < 300:
                return FakeUpstreamResponse(status=status, body_chunks=())
            content_type = response.getheader("Content-Type", "")
            if content_type.split(";", 1)[0].strip().casefold() != "text/event-stream":
                raise UpstreamTransportError("upstream_response_content_type_invalid")
            chunks: list[bytes] = []
            remaining = request.max_response_bytes
            while True:
                chunk = response.read(min(65536, remaining + 1))
                if not chunk:
                    break
                if not isinstance(chunk, bytes) or len(chunk) > remaining:
                    raise UpstreamTransportError("upstream_response_stream_invalid")
                chunks.append(chunk)
                remaining -= len(chunk)
            return FakeUpstreamResponse(status=status, body_chunks=tuple(chunks))
        except UpstreamTransportError:
            raise
        except (OSError, http.client.HTTPException):
            raise UpstreamTransportError("upstream_response_transport_failed") from None
    finally:
        if connection is not None:
            connection.close()


class GatewayRequestHandler(BaseHTTPRequestHandler):
    """Accept reviewed requests and submit only rebuilt data to a local test sink."""

    server_version = "aiops-provider-gateway"
    sys_version = ""

    def log_message(self, format: str, *args: Any) -> None:
        """Disable access and error logging so request data cannot be retained."""

    def _append_gateway_evidence(
        self,
        result: RedactionResult,
        *,
        outcome: str,
        upstream_status_class: str | None,
        tls_verified: bool | None,
    ) -> bool:
        writer = self.server.evidence_writer
        if writer is None:
            return True
        try:
            append_gateway_evidence_event(
                writer,
                build_gateway_evidence_event(
                    result,
                    outcome=outcome,
                    upstream_status_class=upstream_status_class,
                    tls_verified=tls_verified,
                ),
            )
        except GatewayEvidenceError:
            self._send_error_json(502, "ERR_GATEWAY_EVIDENCE")
            return False
        return True

    def do_POST(self) -> None:
        if self.path != self.server.policy.route:
            self._send_error_json(404, "ERR_GATEWAY_ROUTE")
            return
        payload = self._read_json_body()
        if payload is None:
            return
        try:
            result = redact_remote_payload(validate_provider_request_shape(payload))
            scan_redacted_payload(payload, result)
        except ProviderRequestError:
            self._send_error_json(400, "ERR_GATEWAY_SCHEMA_DRIFT")
            return
        except RedactionError:
            self._send_error_json(400, "ERR_OPENAI_REDACTION_UNCLASSIFIED")
            return

        sink = self.server.fake_upstream_sink
        if sink is not None:
            try:
                response = sink.submit(build_fake_upstream_request(result))
            except Exception:
                self._send_error_json(502, "ERR_GATEWAY_FAKE_UPSTREAM")
                return
        else:
            try:
                auth_headers = validate_chatgpt_auth_headers(self.headers)
                request = build_upstream_request(result, self.server.policy, auth_headers)
            except ProviderRequestError:
                self._send_error_json(401, "ERR_OPENAI_AUTH_MANUAL")
                return
            try:
                if not self._append_gateway_evidence(
                    result,
                    outcome="forward_started",
                    upstream_status_class=None,
                    tls_verified=None,
                ):
                    return
                try:
                    response = forward_upstream_request(
                        request, self.server.upstream_connection_factory
                    )
                except UpstreamTransportError as exc:
                    if not self._append_gateway_evidence(
                        result,
                        outcome=exc.outcome,
                        upstream_status_class=None,
                        tls_verified=None,
                    ):
                        return
                    self._send_error_json(502, "ERR_OPENAI_RESPONSE")
                    return
                if not self._append_gateway_evidence(
                    result,
                    outcome=(
                        "upstream_succeeded"
                        if 200 <= response.status < 300
                        else "upstream_non_success"
                    ),
                    upstream_status_class=upstream_status_class(response.status),
                    tls_verified=True,
                ):
                    return
            finally:
                request.headers.clear()
                del request
                del auth_headers
        self._send_fake_response(response)

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        if (
            parsed.path == MODELS_ROUTE
            and tuple(parse_qsl(parsed.query, keep_blank_values=True))
            == EXPECTED_MODELS_QUERY
        ):
            self._send_models_response()
            return
        self._reject_method()

    def do_DELETE(self) -> None:
        self._reject_method()

    def do_HEAD(self) -> None:
        self._reject_method()

    def do_OPTIONS(self) -> None:
        self._reject_method()

    def do_PATCH(self) -> None:
        self._reject_method()

    def do_PUT(self) -> None:
        self._reject_method()

    def _send_models_response(self) -> None:
        body = json.dumps(
            {
                "object": "list",
                "data": [
                    {
                        "id": REVIEWED_MODEL,
                        "object": "model",
                        "created": 0,
                        "owned_by": "openai",
                    }
                ],
            },
            separators=(",", ":"),
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.close_connection = True
        self.end_headers()
        self.wfile.write(body)

    def _reject_method(self) -> None:
        if self.path == self.server.policy.route:
            self._send_error_json(405, "ERR_GATEWAY_ROUTE", allow="POST")
            return
        self._send_error_json(404, "ERR_GATEWAY_ROUTE")

    def _read_json_body(self) -> dict[str, Any] | None:
        """Return one bounded JSON object or emit a fail-closed local error."""
        content_types = self.headers.get_all("Content-Type", [])
        if len(content_types) != 1 or content_types[0].casefold() != "application/json":
            self._send_error_json(415, "ERR_GATEWAY_CONTENT_TYPE")
            return None

        content_encodings = self.headers.get_all("Content-Encoding", [])
        transfer_encodings = self.headers.get_all("Transfer-Encoding", [])
        if (
            transfer_encodings
            or len(content_encodings) > 1
            or (content_encodings and content_encodings[0].casefold() != "identity")
        ):
            self._send_error_json(415, "ERR_GATEWAY_UNSUPPORTED_CONTENT")
            return None

        content_lengths = self.headers.get_all("Content-Length", [])
        if len(content_lengths) != 1:
            self._send_error_json(411, "ERR_GATEWAY_REQUEST_SIZE")
            return None
        raw_length = content_lengths[0]
        if not raw_length.isascii() or not raw_length.isdecimal():
            self._send_error_json(400, "ERR_GATEWAY_REQUEST_SIZE")
            return None
        content_length = int(raw_length)
        if content_length > self.server.policy.max_request_bytes:
            self._send_error_json(413, "ERR_GATEWAY_REQUEST_SIZE")
            return None

        body = self.rfile.read(content_length)
        if len(body) != content_length:
            return None
        try:
            parsed = strict_json_loads(body)
        except (DuplicateKeyError, MalformedJsonError):
            self._send_error_json(400, "ERR_GATEWAY_JSON")
            return None
        if not isinstance(parsed, dict):
            self._send_error_json(400, "ERR_GATEWAY_SCHEMA_DRIFT")
            return None
        return parsed

    def _send_fake_response(self, response: FakeUpstreamResponse) -> None:
        """Stream only fixed fake-sink chunks back to the local client."""
        if (
            not isinstance(response, FakeUpstreamResponse)
            or isinstance(response.status, bool)
            or not isinstance(response.status, int)
            or not 200 <= response.status < 600
            or not isinstance(response.body_chunks, tuple)
            or not all(isinstance(chunk, bytes) for chunk in response.body_chunks)
        ):
            self._send_error_json(502, "ERR_GATEWAY_FAKE_UPSTREAM")
            return
        try:
            self.send_response(response.status)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.close_connection = True
            self.end_headers()
            for chunk in response.body_chunks:
                self.wfile.write(chunk)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            return

    def _send_error_json(self, status: int, code: str, *, allow: str | None = None) -> None:
        body = json.dumps({"error": code}, separators=(",", ":")).encode("utf-8")
        try:
            self.send_response(status)
            if allow is not None:
                self.send_header("Allow", allow)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.close_connection = True
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            return


class GatewayServer(ThreadingHTTPServer):
    """Local threaded server with suppressed handler error output."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        policy: GatewayPolicy,
        *,
        port: int | None = None,
        fake_upstream_sink: FakeUpstreamSink | None = None,
        upstream_connection_factory: Any = http.client.HTTPSConnection,
        evidence_writer: GatewayEvidenceWriter | None = None,
    ) -> None:
        self.policy = policy
        self.fake_upstream_sink = fake_upstream_sink
        self.upstream_connection_factory = upstream_connection_factory
        self.evidence_writer = evidence_writer
        super().__init__(
            (policy.bind_host, policy.bind_port if port is None else port),
            GatewayRequestHandler,
        )

    def handle_error(self, request: Any, client_address: Any) -> None:
        """Avoid emitting request-adjacent exception data."""


def serve(policy: GatewayPolicy, evidence_ledger: Path) -> None:
    """Run the loopback gateway with a validated local evidence ledger."""
    evidence_writer = LocalGatewayEvidenceWriter(evidence_ledger)
    evidence_writer.validate()
    server = GatewayServer(policy, evidence_writer=evidence_writer)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path(__file__).with_name("gateway_policy.json"),
    )
    parser.add_argument("--evidence-ledger", type=Path, required=True)
    args = parser.parse_args()
    try:
        serve(load_policy(args.policy), args.evidence_ledger)
    except (GatewayPolicyError, GatewayEvidenceError):
        return 2
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
