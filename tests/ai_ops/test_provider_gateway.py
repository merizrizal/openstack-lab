import ast
import contextlib
import http.client
import importlib.util
import io
import json
import socket
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
GATEWAY_PATH = (
    REPO_ROOT
    / "ansible/ai_ops_runtime/roles/ai_client_runtime/files/provider_gateway/aiops_provider_gateway.py"
)
POLICY_PATH = GATEWAY_PATH.with_name("gateway_policy.json")


def load_gateway_module():
    sys.path.insert(0, str(GATEWAY_PATH.parent))
    spec = importlib.util.spec_from_file_location("provider_gateway", GATEWAY_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RecordingFakeUpstream:
    def __init__(self, gateway):
        self.gateway = gateway
        self.submissions = []

    def submit(self, request):
        self.submissions.append(request)
        return self.gateway.FakeUpstreamResponse(
            status=200,
            body_chunks=(b"data: synthetic-one\n\n", b"data: [DONE]\n\n"),
        )


class SyntheticHeaders:
    def __init__(self, values):
        self.values = {
            name.casefold(): list(header_values)
            for name, header_values in values.items()
        }

    def get_all(self, name, default=None):
        return self.values.get(name.casefold(), default)


class TestProviderGatewayStub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gateway = load_gateway_module()

    def policy(self, **overrides):
        value = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        value.update(overrides)
        return self.gateway.GatewayPolicy.from_mapping(value)

    def start_gateway(
        self,
        policy=None,
        fake_upstream_sink=None,
        upstream_connection_factory=http.client.HTTPSConnection,
        evidence_writer=None,
    ):
        server = self.gateway.GatewayServer(
            policy or self.policy(),
            port=0,
            fake_upstream_sink=fake_upstream_sink,
            upstream_connection_factory=upstream_connection_factory,
            evidence_writer=evidence_writer,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 2)
        self.addCleanup(server.shutdown)
        return server, server.server_address[1]

    def request(self, port, method="POST", path="/v1/responses", body=None, headers=None):
        body = (
            b'{"model":"gpt-5.6-terra","input":"SYNTHETIC_SAFE_MARKER"}'
            if body is None
            else body
        )
        headers = {"Content-Type": "application/json", **(headers or {})}
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_policy_rejects_non_loopback_bind_scope(self):
        with self.assertRaises(self.gateway.GatewayPolicyError):
            self.policy(bind_host="0.0.0.0")
        with self.assertRaises(self.gateway.GatewayPolicyError):
            self.policy(bind_host="localhost")
        with self.assertRaises(self.gateway.GatewayPolicyError):
            self.policy(bind_port=True)

    def test_policy_accepts_only_fixed_bounded_upstream(self):
        policy = self.policy()

        self.assertEqual(policy.upstream_host, "chatgpt.com")
        self.assertEqual(policy.upstream_port, 443)
        self.assertEqual(policy.upstream_route, "/backend-api/codex/responses")
        self.assertEqual(policy.upstream_timeout_seconds, 30)
        self.assertEqual(policy.max_response_bytes, policy.max_request_bytes)
        for overrides in (
            {"upstream_host": "example.invalid"},
            {"upstream_port": 8443},
            {"upstream_route": "/v1/chat/completions"},
            {"upstream_timeout_seconds": 31},
            {"max_response_bytes": policy.max_request_bytes + 1},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(self.gateway.GatewayPolicyError):
                    self.policy(**overrides)

    def chatgpt_headers(self, **overrides):
        values = {
            "Authorization": ["Bearer SYNTHETIC_AUTHORIZATION"],
            "ChatGPT-Account-ID": ["SYNTHETIC_ACCOUNT_ID"],
            "Content-Type": ["application/json"],
            "Content-Length": ["64"],
            "Host": ["127.0.0.1:8765"],
        }
        values.update(overrides)
        return SyntheticHeaders(values)

    def test_validates_transient_chatgpt_auth_headers_without_repr_values(self):
        validated = self.gateway.validate_chatgpt_auth_headers(self.chatgpt_headers())

        self.assertEqual(validated.authorization, "Bearer SYNTHETIC_AUTHORIZATION")
        self.assertEqual(validated.account_id, "SYNTHETIC_ACCOUNT_ID")
        self.assertNotIn("SYNTHETIC_AUTHORIZATION", repr(validated))
        self.assertNotIn("SYNTHETIC_ACCOUNT_ID", repr(validated))

    def test_rejects_invalid_chatgpt_auth_headers_without_value_disclosure(self):
        invalid_cases = (
            ("missing authorization", {"Authorization": []}),
            (
                "duplicate authorization",
                {"Authorization": ["Bearer SYNTHETIC_ONE", "Bearer SYNTHETIC_TWO"]},
            ),
            ("non bearer authorization", {"Authorization": ["Basic SYNTHETIC"]}),
            ("empty bearer authorization", {"Authorization": ["Bearer "]}),
            (
                "authorization leading whitespace",
                {"Authorization": [" Bearer SYNTHETIC_AUTHORIZATION"]},
            ),
            (
                "authorization trailing whitespace",
                {"Authorization": ["Bearer SYNTHETIC_AUTHORIZATION "]},
            ),
            (
                "authorization control character",
                {"Authorization": ["Bearer SYNTHETIC_AUTHORIZATION\x7f"]},
            ),
            (
                "authorization over bound",
                {
                    "Authorization": [
                        "Bearer " + "A" * self.gateway.CHATGPT_AUTHORIZATION_MAX_BYTES
                    ]
                },
            ),
            ("missing account", {"ChatGPT-Account-ID": []}),
            (
                "duplicate account",
                {"ChatGPT-Account-ID": ["SYNTHETIC_ONE", "SYNTHETIC_TWO"]},
            ),
            ("empty account", {"ChatGPT-Account-ID": [""]}),
            (
                "account leading whitespace",
                {"ChatGPT-Account-ID": [" SYNTHETIC_ACCOUNT_ID"]},
            ),
            (
                "account trailing whitespace",
                {"ChatGPT-Account-ID": ["SYNTHETIC_ACCOUNT_ID "]},
            ),
            (
                "account control character",
                {"ChatGPT-Account-ID": ["SYNTHETIC_ACCOUNT_ID\x00"]},
            ),
            (
                "account over bound",
                {
                    "ChatGPT-Account-ID": [
                        "A" * (self.gateway.CHATGPT_ACCOUNT_ID_MAX_BYTES + 1)
                    ]
                },
            ),
            ("fedramp present", {"X-OpenAI-Fedramp": ["synthetic"]}),
        )

        for label, overrides in invalid_cases:
            with self.subTest(label=label):
                with self.assertRaises(self.gateway.ProviderRequestError) as raised:
                    self.gateway.validate_chatgpt_auth_headers(
                        self.chatgpt_headers(**overrides)
                    )
                self.assertEqual(
                    str(raised.exception),
                    "provider authentication headers are unavailable",
                )
                self.assertNotIn("SYNTHETIC_AUTHORIZATION", str(raised.exception))
                self.assertNotIn("SYNTHETIC_ACCOUNT_ID", str(raised.exception))

    def test_rejects_duplicate_protected_singleton_headers(self):
        for name in (
            "Content-Type",
            "Content-Length",
            "Content-Encoding",
            "Transfer-Encoding",
            "Host",
        ):
            with self.subTest(name=name):
                with self.assertRaises(self.gateway.ProviderRequestError):
                    self.gateway.validate_chatgpt_auth_headers(
                        self.chatgpt_headers(**{name: ["synthetic-one", "synthetic-two"]})
                    )

    def test_rebuilds_fixed_upstream_request_with_allowlisted_headers(self):
        result = self.gateway.redact_remote_payload(
            {"username": "SYNTHETIC_USERNAME", "input": "SYNTHETIC_USERNAME"}
        )

        request = self.gateway.build_upstream_request(
            result,
            self.policy(),
            self.gateway.validate_chatgpt_auth_headers(self.chatgpt_headers()),
        )

        self.assertEqual(request.host, "chatgpt.com")
        self.assertEqual(request.port, 443)
        self.assertEqual(request.path, "/backend-api/codex/responses")
        self.assertEqual(request.timeout_seconds, 30)
        self.assertEqual(request.max_response_bytes, 1048576)
        self.assertEqual(
            request.headers,
            {
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
                "Authorization": "Bearer SYNTHETIC_AUTHORIZATION",
                "ChatGPT-Account-ID": "SYNTHETIC_ACCOUNT_ID",
            },
        )
        self.assertNotIn("SYNTHETIC_USERNAME", request.body.decode("utf-8"))

    def test_accepts_only_exact_post_responses_route(self):
        _, port = self.start_gateway()

        status, _, _ = self.request(port, path="/v1/other")
        self.assertEqual(status, 404)
        status, headers, _ = self.request(port, method="GET")
        self.assertEqual(status, 405)
        self.assertEqual(headers["Allow"], "POST")
        status, _, body = self.request(port)
        self.assertEqual(status, 401)
        self.assertEqual(body, b'{"error":"ERR_OPENAI_AUTH_MANUAL"}')

    def test_rejects_missing_chatgpt_account_without_transport(self):
        connection_calls = []
        _, port = self.start_gateway(
            upstream_connection_factory=lambda *args, **kwargs: connection_calls.append(args),
        )

        status, _, body = self.request(
            port, headers={"Authorization": "Bearer SYNTHETIC_INBOUND_TOKEN"}
        )

        self.assertEqual(status, 401)
        self.assertEqual(body, b'{"error":"ERR_OPENAI_AUTH_MANUAL"}')
        self.assertEqual(connection_calls, [])

    def test_serves_only_reviewed_model_discovery_route(self):
        _, port = self.start_gateway()

        status, headers, body = self.request(
            port,
            method="GET",
            path="/v1/models?client_version=0.144.1",
        )

        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(
            json.loads(body),
            {
                "object": "list",
                "data": [
                    {
                        "id": self.gateway.REVIEWED_MODEL,
                        "object": "model",
                        "created": 0,
                        "owned_by": "openai",
                    }
                ],
            },
        )
        status, _, _ = self.request(port, method="GET", path="/v1/models")
        self.assertEqual(status, 404)
        status, _, _ = self.request(
            port,
            method="GET",
            path="/v1/models?client_version=unexpected",
        )
        self.assertEqual(status, 404)

    def test_redacts_and_streams_only_to_fixed_fake_upstream(self):
        sink = RecordingFakeUpstream(self.gateway)
        _, port = self.start_gateway(fake_upstream_sink=sink)
        payload = {
            "model": self.gateway.REVIEWED_MODEL,
            "input": [
                {
                    "context": {
                        "username": "SYNTHETIC_USERNAME",
                        "group": "SYNTHETIC_GROUP",
                        "token": "SYNTHETIC_TOKEN",
                    }
                },
                {"content": "username=SYNTHETIC_USERNAME token=SYNTHETIC_TOKEN"},
            ],
            "note": "SYNTHETIC_USERNAME SYNTHETIC_GROUP SYNTHETIC_TOKEN SYNTHETIC_SAFE_MARKER",
        }

        status, headers, body = self.request(
            port,
            body=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": "Bearer SYNTHETIC_INBOUND_TOKEN"},
        )

        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "text/event-stream")
        self.assertEqual(body, b"data: synthetic-one\n\ndata: [DONE]\n\n")
        self.assertEqual(len(sink.submissions), 1)
        submitted = sink.submissions[0]
        self.assertEqual(submitted.path, self.gateway.FIXED_FAKE_UPSTREAM_PATH)
        self.assertEqual(submitted.headers, self.gateway.FIXED_FAKE_UPSTREAM_HEADERS)
        rebuilt = json.loads(submitted.body)
        serialized = json.dumps(rebuilt, sort_keys=True)
        for marker in (
            "SYNTHETIC_USERNAME",
            "SYNTHETIC_GROUP",
            "SYNTHETIC_TOKEN",
            "SYNTHETIC_INBOUND_TOKEN",
        ):
            self.assertNotIn(marker, serialized)
        self.assertIn("SYNTHETIC_SAFE_MARKER", serialized)
        self.assertEqual(rebuilt["input"][0]["context"]["username"], "[REDACTED]")
        self.assertEqual(rebuilt["input"][0]["context"]["group"], "[REDACTED]")
        self.assertEqual(rebuilt["input"][0]["context"]["token"], "[REDACTED]")

    def test_rejects_caller_selected_upstream_without_submission(self):
        sink = RecordingFakeUpstream(self.gateway)
        _, port = self.start_gateway(fake_upstream_sink=sink)
        payload = {
            "model": self.gateway.REVIEWED_MODEL,
            "input": "SYNTHETIC_SAFE_MARKER",
            "upstream_url": "https://example.invalid/v1/responses",
        }

        status, _, body = self.request(port, body=json.dumps(payload).encode("utf-8"))

        self.assertEqual(status, 400)
        self.assertEqual(body, b'{"error":"ERR_GATEWAY_SCHEMA_DRIFT"}')
        self.assertEqual(sink.submissions, [])

    def test_enforces_request_size_bound(self):
        _, port = self.start_gateway(
            self.policy(max_request_bytes=8, max_response_bytes=8)
        )

        status, _, body = self.request(port, body=b'{"input":"too large"}')

        self.assertEqual(status, 413)
        self.assertEqual(body, b'{"error":"ERR_GATEWAY_REQUEST_SIZE"}')

    def test_rejects_unreviewed_content_type_and_encoding(self):
        _, port = self.start_gateway()

        status, _, _ = self.request(
            port, headers={"Content-Type": "application/json; charset=utf-8"}
        )
        self.assertEqual(status, 415)
        status, _, _ = self.request(port, headers={"Content-Encoding": "gzip"})
        self.assertEqual(status, 415)

    def test_rejects_malformed_duplicate_and_non_object_json(self):
        _, port = self.start_gateway()

        for body, expected in (
            (b'{"input":', b'{"error":"ERR_GATEWAY_JSON"}'),
            (b'{"input":1,"input":2}', b'{"error":"ERR_GATEWAY_JSON"}'),
            (b'[]', b'{"error":"ERR_GATEWAY_SCHEMA_DRIFT"}'),
        ):
            with self.subTest(body=body):
                status, _, response_body = self.request(port, body=body)
                self.assertEqual(status, 400)
                self.assertEqual(response_body, expected)

    def test_client_cancellation_does_not_interrupt_later_requests(self):
        _, port = self.start_gateway()
        request = (
            b"POST /v1/responses HTTP/1.1\r\n"
            b"Host: 127.0.0.1\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: 2\r\n\r\n{}"
        )
        client = socket.create_connection(("127.0.0.1", port), timeout=2)
        client.sendall(request)
        client.shutdown(socket.SHUT_RDWR)
        client.close()
        time.sleep(0.05)

        status, _, body = self.request(port)

        self.assertEqual(status, 401)
        self.assertEqual(body, b'{"error":"ERR_OPENAI_AUTH_MANUAL"}')

    def test_forwards_only_rebuilt_request_through_injected_https_connection(self):
        class Response:
            status = 200

            def getheader(self, name, default=None):
                return "text/event-stream" if name == "Content-Type" else default

            def read(self, size):
                if not hasattr(self, "sent"):
                    self.sent = True
                    return b"data: synthetic\n\n"
                return b""

        class Connection:
            def __init__(self):
                self.closed = False
                self.request_args = None

            def request(self, *args, **kwargs):
                self.request_args = (args, kwargs)

            def getresponse(self):
                return Response()

            def close(self):
                self.closed = True

        connection = Connection()
        result = self.gateway.redact_remote_payload({"input": "SYNTHETIC_SAFE_MARKER"})
        request = self.gateway.build_upstream_request(
            result,
            self.policy(),
            self.gateway.validate_chatgpt_auth_headers(self.chatgpt_headers()),
        )
        response = self.gateway.forward_upstream_request(
            request, lambda *args, **kwargs: connection
        )

        self.assertEqual(
            connection.request_args[0], ("POST", "/backend-api/codex/responses")
        )
        self.assertEqual(connection.request_args[1]["headers"], request.headers)
        self.assertEqual(response.body_chunks, (b"data: synthetic\n\n",))
        self.assertTrue(connection.closed)

    def test_classifies_provider_4xx_without_response_content(self):
        cases = {
            400: "bad_request",
            401: "authentication",
            403: "permission",
            404: "not_found",
            409: "other_4xx",
            422: "unprocessable",
            429: "rate_or_quota",
            451: "other_4xx",
        }
        for status, category in cases.items():
            with self.subTest(status=status):
                self.assertEqual(
                    self.gateway.provider_error_category(status), category
                )

        for status in (True, 399, 500):
            with self.subTest(invalid_status=status):
                with self.assertRaises(self.gateway.GatewayEvidenceError):
                    self.gateway.provider_error_category(status)

    def test_serializes_only_allowlisted_gateway_evidence_metadata(self):
        event = self.gateway.GatewayEvidenceEvent(
            timestamp_utc="2026-07-14T12:00:00Z",
            correlation_id="550e8400-e29b-41d4-a716-446655440000",
            model=self.gateway.REVIEWED_MODEL,
            route=self.gateway.FIXED_UPSTREAM_ROUTE,
            classification_status="redacted",
            redaction_counts=(("identity", 2), ("secret", 1)),
            outcome="upstream_succeeded",
            upstream_status_class="2xx",
            tls_verified=True,
        )

        serialized = self.gateway.serialize_gateway_evidence_event(event)
        value = json.loads(serialized)

        self.assertEqual(
            set(value),
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
            },
        )
        self.assertEqual(value["schema_version"], 2)
        self.assertEqual(value["redaction_counts"], {"identity": 2, "secret": 1})
        self.assertNotIn("SYNTHETIC_RAW_PROMPT", serialized.decode("utf-8"))

    def test_parses_mixed_schema_gateway_evidence_records(self):
        current = {
            "classification_status": "clear",
            "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
            "model": self.gateway.REVIEWED_MODEL,
            "outcome": "forward_started",
            "redaction_counts": {"identity": 1},
            "route": self.gateway.FIXED_UPSTREAM_ROUTE,
            "schema_version": self.gateway.GATEWAY_EVIDENCE_SCHEMA_VERSION,
            "timestamp_utc": "2026-07-14T12:00:00Z",
            "tls_verified": None,
            "upstream_status_class": None,
        }
        historical = current | {
            "route": self.gateway.HISTORICAL_GATEWAY_EVIDENCE_ROUTE,
            "schema_version": self.gateway.HISTORICAL_GATEWAY_EVIDENCE_SCHEMA_VERSION,
        }

        parsed = [
            self.gateway.parse_gateway_evidence_record(json.dumps(record))
            for record in (historical, current)
        ]

        self.assertEqual(
            [(event.schema_version, event.route) for event in parsed],
            [
                (1, "/v1/responses"),
                (2, "/backend-api/codex/responses"),
            ],
        )
        historical_event = self.gateway.GatewayEvidenceEvent(
            timestamp_utc=historical["timestamp_utc"],
            correlation_id=historical["correlation_id"],
            model=historical["model"],
            route=historical["route"],
            classification_status=historical["classification_status"],
            redaction_counts=(("identity", 1),),
            outcome=historical["outcome"],
            upstream_status_class=None,
            tls_verified=None,
            schema_version=1,
        )
        with self.assertRaises(self.gateway.GatewayEvidenceError):
            self.gateway.serialize_gateway_evidence_event(historical_event)

        for override in (
            {"schema_version": 3},
            {"schema_version": 1},
            {"route": "/v1/responses"},
            {"route": "/unexpected"},
        ):
            with self.subTest(override=override):
                with self.assertRaises(self.gateway.GatewayEvidenceError):
                    self.gateway.parse_gateway_evidence_record(
                        json.dumps(current | override)
                    )

    def test_rejects_invalid_or_unsafe_gateway_evidence_metadata(self):
        base = {
            "timestamp_utc": "2026-07-14T12:00:00Z",
            "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
            "model": self.gateway.REVIEWED_MODEL,
            "route": self.gateway.FIXED_UPSTREAM_ROUTE,
            "classification_status": "clear",
            "redaction_counts": (),
            "outcome": "forward_started",
            "upstream_status_class": None,
            "tls_verified": None,
        }
        invalid_values = (
            {"correlation_id": "not-a-uuid"},
            {"classification_status": "payload-retained"},
            {"redaction_counts": None},
            {"redaction_counts": (("identity", 1, 2),)},
            {"redaction_counts": (("payload", 1),)},
            {"redaction_counts": (("identity", True),)},
            {"outcome": "forward_started", "tls_verified": True},
            {
                "outcome": "upstream_succeeded",
                "upstream_status_class": "2xx",
                "tls_verified": False,
            },
        )
        for override in invalid_values:
            with self.subTest(override=override):
                event = self.gateway.GatewayEvidenceEvent(**(base | override))
                with self.assertRaises(self.gateway.GatewayEvidenceError):
                    self.gateway.serialize_gateway_evidence_event(event)

    def test_appends_valid_metadata_event_to_local_ledger(self):
        event = self.gateway.GatewayEvidenceEvent(
            timestamp_utc="2026-07-14T12:00:00Z",
            correlation_id="550e8400-e29b-41d4-a716-446655440000",
            model=self.gateway.REVIEWED_MODEL,
            route=self.gateway.FIXED_UPSTREAM_ROUTE,
            classification_status="clear",
            redaction_counts=(),
            outcome="forward_started",
            upstream_status_class=None,
            tls_verified=None,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gateway-evidence.jsonl"
            writer = self.gateway.LocalGatewayEvidenceWriter(path)

            self.gateway.append_gateway_evidence_event(writer, event)

            record = path.read_bytes()
            self.assertTrue(record.endswith(b"\n"))
            self.assertEqual(json.loads(record), json.loads(self.gateway.serialize_gateway_evidence_event(event)))
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_rejects_invalid_event_before_writer_and_propagates_writer_failure(self):
        class RecordingWriter:
            def __init__(self):
                self.records = []

            def append(self, record):
                self.records.append(record)

        class FailingWriter:
            def append(self, record):
                raise OSError("synthetic ledger failure")

        invalid_event = self.gateway.GatewayEvidenceEvent(
            timestamp_utc="invalid",
            correlation_id="550e8400-e29b-41d4-a716-446655440000",
            model=self.gateway.REVIEWED_MODEL,
            route=self.gateway.FIXED_UPSTREAM_ROUTE,
            classification_status="clear",
            redaction_counts=(),
            outcome="forward_started",
            upstream_status_class=None,
            tls_verified=None,
        )
        valid_event = self.gateway.GatewayEvidenceEvent(
            timestamp_utc="2026-07-14T12:00:00Z",
            correlation_id="550e8400-e29b-41d4-a716-446655440000",
            model=self.gateway.REVIEWED_MODEL,
            route=self.gateway.FIXED_UPSTREAM_ROUTE,
            classification_status="clear",
            redaction_counts=(),
            outcome="forward_started",
            upstream_status_class=None,
            tls_verified=None,
        )
        recording_writer = RecordingWriter()

        with self.assertRaises(self.gateway.GatewayEvidenceError):
            self.gateway.append_gateway_evidence_event(recording_writer, invalid_event)
        self.assertEqual(recording_writer.records, [])
        with self.assertRaises(self.gateway.GatewayEvidenceError):
            self.gateway.append_gateway_evidence_event(FailingWriter(), valid_event)

    def test_rejects_overflow_and_symlinked_ledgers_without_modification(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gateway-evidence.jsonl"
            path.write_bytes(b"x" * 4094)
            writer = self.gateway.LocalGatewayEvidenceWriter(path, max_bytes=4096)

            with self.assertRaises(self.gateway.GatewayEvidenceError):
                writer.append(b"{}\n")
            self.assertEqual(path.read_bytes(), b"x" * 4094)

            target = Path(directory) / "target.jsonl"
            target.write_bytes(b"preserved")
            link = Path(directory) / "ledger-link.jsonl"
            link.symlink_to(target)
            with self.assertRaises(self.gateway.GatewayEvidenceError):
                self.gateway.LocalGatewayEvidenceWriter(link, max_bytes=4096).append(b"{}\n")
            self.assertEqual(target.read_bytes(), b"preserved")

    def test_serializes_concurrent_appends_under_the_ledger_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gateway-evidence.jsonl"
            path.write_bytes(b"x" * 4091)
            writer = self.gateway.LocalGatewayEvidenceWriter(path, max_bytes=4096)
            barrier = threading.Barrier(2)
            errors = []

            def append_record():
                barrier.wait()
                try:
                    writer.append(b"{}\n")
                except self.gateway.GatewayEvidenceError as exc:
                    errors.append(exc)

            first = threading.Thread(target=append_record)
            second = threading.Thread(target=append_record)
            first.start()
            second.start()
            first.join()
            second.join()

            self.assertEqual(len(errors), 1)
            self.assertEqual(path.stat().st_size, 4094)

    def test_serve_requires_a_usable_explicit_evidence_ledger(self):
        class RecordingServer:
            instances = []

            def __init__(self, policy, *, evidence_writer):
                self.policy = policy
                self.evidence_writer = evidence_writer
                self.served = False
                self.closed = False
                self.instances.append(self)

            def serve_forever(self):
                self.served = True

            def server_close(self):
                self.closed = True

        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "gateway-evidence.jsonl"
            with mock.patch.object(self.gateway, "GatewayServer", RecordingServer):
                self.gateway.serve(self.policy(), ledger)

            server = RecordingServer.instances[-1]
            self.assertTrue(server.served)
            self.assertTrue(server.closed)
            self.assertEqual(server.evidence_writer.path, ledger)
            self.assertEqual(ledger.stat().st_mode & 0o777, 0o600)

            with self.assertRaises(self.gateway.GatewayEvidenceError):
                self.gateway.serve(self.policy(), Path(directory) / "missing" / "ledger.jsonl")

    def test_forwards_validated_chatgpt_headers_through_injected_https_connection(self):
        class Response:
            status = 200

            def getheader(self, name, default=None):
                return "text/event-stream" if name == "Content-Type" else default

            def read(self, size):
                if not hasattr(self, "sent"):
                    self.sent = True
                    return b"data: synthetic\n\n"
                return b""

        class Connection:
            def __init__(self):
                self.request_args = None
                self.closed = False

            def request(self, method, path, body, headers):
                self.request_args = (method, path, body, dict(headers))

            def getresponse(self):
                return Response()

            def close(self):
                self.closed = True

        connection = Connection()
        _, port = self.start_gateway(
            upstream_connection_factory=lambda *args, **kwargs: connection,
        )
        status, _, body = self.request(
            port,
            headers={
                "Authorization": "Bearer SYNTHETIC_INBOUND_TOKEN",
                "ChatGPT-Account-ID": "SYNTHETIC_ACCOUNT_ID",
                "X-Unreviewed": "SYNTHETIC_UNREVIEWED_HEADER",
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(body, b"data: synthetic\n\n")
        self.assertEqual(connection.request_args[:2], ("POST", "/backend-api/codex/responses"))
        self.assertEqual(
            connection.request_args[3],
            {
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
                "Authorization": "Bearer SYNTHETIC_INBOUND_TOKEN",
                "ChatGPT-Account-ID": "SYNTHETIC_ACCOUNT_ID",
            },
        )
        self.assertTrue(connection.closed)

    def test_redaction_failure_writes_no_evidence(self):
        class RecordingWriter:
            def __init__(self):
                self.records = []

            def append(self, record):
                self.records.append(record)

        writer = RecordingWriter()
        _, port = self.start_gateway(evidence_writer=writer)
        status, _, body = self.request(port, body=b'{"input":"unterminated')
        self.assertEqual(status, 400)
        self.assertEqual(body, b'{"error":"ERR_GATEWAY_JSON"}')
        self.assertEqual(writer.records, [])

    def test_gateway_source_uses_only_the_reviewed_https_transport(self):
        tree = ast.parse(GATEWAY_PATH.read_text(encoding="utf-8"))
        prohibited_modules = {"httpx", "requests", "urllib", "urllib.request"}
        imported_modules = set()
        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)

        self.assertIn("http.client", imported_modules)
        self.assertFalse(imported_modules & prohibited_modules)
        self.assertIn("request", calls)
        self.assertFalse(calls & {"connect", "create_connection", "urlopen"})

    def test_rejected_request_is_not_written_to_stderr(self):
        _, port = self.start_gateway()
        marker = "SYNTHETIC_RAW_REQUEST_MUST_NOT_LOG"
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            status, _, body = self.request(port, body=("{\"input\":\"" + marker).encode())

        self.assertEqual(status, 400)
        self.assertEqual(body, b'{"error":"ERR_GATEWAY_JSON"}')
        self.assertNotIn(marker, stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
