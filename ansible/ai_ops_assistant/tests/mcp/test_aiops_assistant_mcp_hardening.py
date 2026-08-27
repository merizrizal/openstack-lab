import importlib.util
import json
import sys
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest import mock

SERVER_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_mcp/files/mcp/aiops_assistant_mcp_server.py"
)
SPEC = importlib.util.spec_from_loader(
    "aiops_assistant_mcp_server_hardening",
    SourceFileLoader("aiops_assistant_mcp_server_hardening", str(SERVER_PATH)),
)
SERVER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SERVER
SPEC.loader.exec_module(SERVER)


class MCPHardeningTest(unittest.TestCase):
    def valid_configuration(self):
        return SERVER.NetworkMCPConfig.from_mapping(
            {
                "schema_version": 1,
                "transport": "streamable-http",
                "bind_interface": "eth0",
                "bind_address": "192.168.121.21",
                "port": 8443,
                "endpoint_path": "/mcp",
                "allowed_source_cidrs": ["192.168.121.0/24"],
                "tls_certificate_path": "/etc/ai-ops-assistant/mcp/tls/server.crt",
                "tls_private_key_path": "/etc/ai-ops-assistant/mcp/tls/server.key",
                "tls_client_ca_path": "/etc/ai-ops-assistant/mcp/tls/client-ca.crt",
                "tls_client_crl_path": "/etc/ai-ops-assistant/mcp/tls/client-ca.crl",
                "authorized_principal_uri": "spiffe://openstack-lab/mcp/mcp-internal-reader",
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
        )

    def test_rate_limiter_allows_fixed_burst_then_refills(self):
        now = [100.0]
        limiter = SERVER.PrincipalRateLimiter(10, 2, clock=lambda: now[0])
        self.assertTrue(limiter.allow("mcp-internal-reader"))
        self.assertTrue(limiter.allow("mcp-internal-reader"))
        self.assertFalse(limiter.allow("mcp-internal-reader"))
        now[0] += 6.0
        self.assertTrue(limiter.allow("mcp-internal-reader"))

    def test_admission_rejects_runner_concurrency_without_queueing(self):
        admission = SERVER.NetworkMCPAdmission(self.valid_configuration())
        with admission.request("mcp-internal-reader"):
            with self.assertRaises(SERVER.RequestLimitError):
                with admission.request("mcp-internal-reader"):
                    pass

    def test_request_and_response_bounds_fail_closed(self):
        config = self.valid_configuration()
        with self.assertRaises(SERVER.RequestLimitError):
            SERVER.validate_request_bounds(config, header_bytes=8193, body_bytes=1)
        with self.assertRaises(SERVER.RequestLimitError):
            SERVER.validate_request_bounds(config, header_bytes=1, body_bytes=65537)
        with self.assertRaises(SERVER.RunnerProtocolError):
            SERVER.validate_response_bounds(config, b"x" * 262145)

    def test_child_termination_is_bounded_and_reaped(self):
        process = mock.Mock()
        process.poll.side_effect = [None, 0]
        SERVER.terminate_and_reap_child(process, grace_seconds=0)
        process.terminate.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=0)

    def test_sanitized_lifecycle_event_has_closed_shape_and_no_payload(self):
        with mock.patch.object(SERVER.LOGGER, "info") as info:
            SERVER.emit_lifecycle_event(
                "mcp_authentication",
                "accepted",
                principal="untrusted-client-name",
                source_allowed=True,
                reason="authentication_failed",
            )
        event = info.call_args.kwargs["extra"]["mcp_event"]
        self.assertEqual(
            set(event),
            {
                "schema_version",
                "event_type",
                "outcome",
                "principal",
                "source_allowed",
                "reason",
            },
        )
        self.assertEqual(event["principal"], "unknown")
        self.assertNotIn("untrusted-client-name", json.dumps(event))

    def test_default_disabled_deployment_contract_is_static_and_hardened(self):
        root = Path(__file__).parents[2]
        defaults = (root / "roles/ai_ops_assistant_mcp/defaults/main.yml").read_text(
            encoding="utf-8"
        )
        service = (
            root
            / "roles/ai_ops_assistant_mcp/templates/ai-ops-assistant-mcp.service.j2"
        ).read_text(encoding="utf-8")
        tasks = (root / "roles/ai_ops_assistant_mcp/tasks/main.yml").read_text(
            encoding="utf-8"
        )
        playbook = (root / "playbook_deploy_mcp.yml").read_text(encoding="utf-8")
        self.assertIn("ai_ops_assistant_mcp_enabled: false", defaults)
        self.assertIn("ai_ops_assistant_mcp_explicit_activation: false", defaults)
        self.assertIn("enabled: false", tasks)
        self.assertIn("ProtectSystem=strict", service)
        self.assertIn("RestrictAddressFamilies=AF_INET", service)
        self.assertIn(
            "ExecStart={{ ai_ops_assistant_mcp_venv_path }}/bin/python {{ ai_ops_assistant_mcp_adapter_path }}",
            service,
        )
        self.assertIn("ai_ops_assistant_mcp_enabled: false", playbook)
        self.assertNotIn("ansible.posix.firewalld", playbook)
        self.assertNotIn("client", playbook.lower())

    def test_systemd_template_contains_no_proxy_or_provider_environment(self):
        template = (
            Path(__file__).parents[2]
            / "roles/ai_ops_assistant_mcp/templates/ai-ops-assistant-mcp.service.j2"
        ).read_text(encoding="utf-8")
        for forbidden in ("HTTP_PROXY", "HTTPS_PROXY", "OS_AUTH_URL", "OPENAI_API_KEY"):
            self.assertNotIn(forbidden, template)


if __name__ == "__main__":
    unittest.main()
