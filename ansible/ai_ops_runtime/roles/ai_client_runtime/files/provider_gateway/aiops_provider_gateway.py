#!/usr/bin/env python3
"""Fail-closed loopback Responses API gateway with no upstream transport."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Protocol

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
    }
)
LOOPBACK_HOSTS = frozenset({"127.0.0.1"})


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
        return cls(
            bind_host=value["bind_host"],
            bind_port=value["bind_port"],
            service_identity=value["service_identity"],
            route=value["route"],
            max_request_bytes=value["max_request_bytes"],
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


class GatewayRequestHandler(BaseHTTPRequestHandler):
    """Accept reviewed requests and submit only rebuilt data to a local test sink."""

    server_version = "aiops-provider-gateway"
    sys_version = ""

    def log_message(self, format: str, *args: Any) -> None:
        """Disable access and error logging so request data cannot be retained."""

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
            fake_request = build_fake_upstream_request(result)
        except ProviderRequestError:
            self._send_error_json(400, "ERR_GATEWAY_SCHEMA_DRIFT")
            return
        except RedactionError:
            self._send_error_json(400, "ERR_OPENAI_REDACTION_UNCLASSIFIED")
            return

        sink = self.server.fake_upstream_sink
        if sink is None:
            self._send_error_json(503, "ERR_GATEWAY_UNAVAILABLE")
            return
        try:
            response = sink.submit(fake_request)
        except Exception:
            self._send_error_json(502, "ERR_GATEWAY_FAKE_UPSTREAM")
            return
        self._send_fake_response(response)

    def do_GET(self) -> None:
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
    ) -> None:
        self.policy = policy
        self.fake_upstream_sink = fake_upstream_sink
        super().__init__(
            (policy.bind_host, policy.bind_port if port is None else port),
            GatewayRequestHandler,
        )

    def handle_error(self, request: Any, client_address: Any) -> None:
        """Avoid emitting request-adjacent exception data."""


def serve(policy: GatewayPolicy) -> None:
    """Run only the local stub; no outbound client is constructed."""
    server = GatewayServer(policy)
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
    args = parser.parse_args()
    try:
        serve(load_policy(args.policy))
    except GatewayPolicyError:
        return 2
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
