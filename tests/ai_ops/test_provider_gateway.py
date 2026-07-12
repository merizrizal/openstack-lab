import ast
import contextlib
import http.client
import importlib.util
import io
import json
import socket
import sys
import threading
import time
import unittest
from pathlib import Path

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


class TestProviderGatewayStub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gateway = load_gateway_module()

    def policy(self, **overrides):
        value = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        value.update(overrides)
        return self.gateway.GatewayPolicy.from_mapping(value)

    def start_gateway(self, policy=None, fake_upstream_sink=None):
        server = self.gateway.GatewayServer(
            policy or self.policy(), port=0, fake_upstream_sink=fake_upstream_sink
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

    def test_accepts_only_exact_post_responses_route(self):
        _, port = self.start_gateway()

        status, _, _ = self.request(port, path="/v1/other")
        self.assertEqual(status, 404)
        status, headers, _ = self.request(port, method="GET")
        self.assertEqual(status, 405)
        self.assertEqual(headers["Allow"], "POST")
        status, _, body = self.request(port)
        self.assertEqual(status, 503)
        self.assertEqual(body, b'{"error":"ERR_GATEWAY_UNAVAILABLE"}')

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
        _, port = self.start_gateway(self.policy(max_request_bytes=8))

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

        self.assertEqual(status, 503)
        self.assertEqual(body, b'{"error":"ERR_GATEWAY_UNAVAILABLE"}')

    def test_gateway_source_has_no_outbound_client_or_forwarding_call(self):
        tree = ast.parse(GATEWAY_PATH.read_text(encoding="utf-8"))
        forbidden_modules = {"http.client", "httpx", "requests", "urllib", "urllib.request"}
        imported_modules = set()
        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)

        self.assertFalse(imported_modules & forbidden_modules)
        self.assertFalse(calls & {"connect", "create_connection", "request", "urlopen"})

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
