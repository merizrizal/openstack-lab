import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml
from jinja2 import Environment, StrictUndefined

REPO_ROOT = Path(__file__).resolve().parents[2]
REMOTE_UNIT_PATH = (
    REPO_ROOT
    / "ansible/ai_ops_runtime/roles/orchestrator_runtime/templates/aiops-orchestrator-remote.service.j2"
)
PREFLIGHT_PATH = (
    REPO_ROOT / "ansible/ai_ops_runtime/playbook_validate_phase12_remote_preflight.yml"
)
OPERATION_PATH = (
    REPO_ROOT
    / "ansible/ai_ops_runtime/playbook_operate_orchestrator_remote_acceptance.yml"
)
EGRESS_DEFAULTS_PATH = (
    REPO_ROOT / "ansible/ai_ops_runtime/roles/orchestrator_egress/defaults/main.yml"
)
EGRESS_TASKS_PATH = (
    REPO_ROOT / "ansible/ai_ops_runtime/roles/orchestrator_egress/tasks/main.yml"
)
AUTH_EGRESS_WINDOW_PATH = (
    REPO_ROOT
    / "ansible/ai_ops_runtime/playbook_operate_orchestrator_auth_egress_window.yml"
)


def named_task(tasks, name):
    matches = [task for task in tasks if task.get("name") == name]
    if len(matches) != 1:
        raise AssertionError(f"expected one task {name!r}, found {len(matches)}")
    return matches[0]


def render_remote_unit():
    environment = Environment(undefined=StrictUndefined, keep_trailing_newline=True)
    template = environment.from_string(REMOTE_UNIT_PATH.read_text(encoding="utf-8"))
    return template.render(
        ai_ops_orchestrator={
            "user": "aiops-orchestrator",
            "group": "aiops-orchestrator",
            "work_root": "/var/lib/aiops-orchestrator/work",
            "codex_home": "/var/lib/aiops-orchestrator/codex-home",
            "evidence_root": "/var/lib/aiops-orchestrator/evidence",
            "root": "/opt/openstack-ai-ops/orchestrator",
            "venv": "/opt/openstack-ai-ops/orchestrator/venv",
        }
    )


class TestOrchestratorRemoteOperationsContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.remote_unit = render_remote_unit()
        cls.preflight = yaml.safe_load(PREFLIGHT_PATH.read_text(encoding="utf-8"))
        cls.operation = yaml.safe_load(OPERATION_PATH.read_text(encoding="utf-8"))[0]
        cls.egress_defaults = yaml.safe_load(
            EGRESS_DEFAULTS_PATH.read_text(encoding="utf-8")
        )
        cls.egress_tasks = yaml.safe_load(EGRESS_TASKS_PATH.read_text(encoding="utf-8"))
        cls.auth_egress_window = yaml.safe_load(
            AUTH_EGRESS_WINDOW_PATH.read_text(encoding="utf-8")
        )[0]

    def test_remote_unit_is_static_and_runs_as_the_orchestrator_identity(self):
        self.assertIn(
            "ConditionPathExists=/run/aiops-orchestrator/remote-approval",
            self.remote_unit,
        )
        self.assertIn("User=aiops-orchestrator", self.remote_unit)
        self.assertIn("Group=aiops-orchestrator", self.remote_unit)
        self.assertIn("Type=oneshot", self.remote_unit)
        self.assertIn("Restart=no", self.remote_unit)
        self.assertIn("TimeoutStartSec=45", self.remote_unit)
        self.assertIn("UMask=0077", self.remote_unit)
        self.assertIn("NoNewPrivileges=true", self.remote_unit)
        self.assertIn("CapabilityBoundingSet=", self.remote_unit)
        self.assertIn("AmbientCapabilities=", self.remote_unit)
        self.assertIn(
            "UnsetEnvironment=ALL_PROXY HTTP_PROXY HTTPS_PROXY NO_PROXY",
            self.remote_unit,
        )
        self.assertIn(
            "ExecStart=/opt/openstack-ai-ops/orchestrator/venv/bin/python",
            self.remote_unit,
        )
        self.assertNotIn("[Install]", self.remote_unit)
        self.assertNotIn("WantedBy=", self.remote_unit)
        self.assertNotIn("Restart=always", self.remote_unit)
        self.assertNotIn("Environment=HTTP", self.remote_unit)

    def test_preflight_requires_static_unit_absent_approval_and_disabled_egress(self):
        self.assertEqual(
            self.preflight[0]["name"], "Validate fake-only deployment precondition"
        )
        play = self.preflight[1]
        tasks = play["tasks"]
        contract = named_task(
            tasks, "Assert remote service and permanent deny contracts"
        )
        self.assertIn(
            "ai_ops_orchestrator_egress.mode == 'disabled'",
            contract["ansible.builtin.assert"]["that"],
        )
        self.assertTrue(contract["no_log"])
        approval = named_task(tasks, "Inspect remote approval artifact absence")
        self.assertTrue(approval["no_log"])
        enabled = named_task(tasks, "Read remote service enablement metadata")
        self.assertTrue(enabled["no_log"])
        static = named_task(tasks, "Assert remote service is installed but not enabled")
        self.assertIn("'static'", static["ansible.builtin.assert"]["that"][1])

    def test_operation_fails_closed_and_always_restores_static_baseline(self):
        self.assertFalse(self.operation["vars"]["ai_ops_remote_acceptance_apply"])
        operation = named_task(
            self.operation["tasks"],
            "Reject remote acceptance until a separately approved operation exists",
        )
        reject = named_task(operation["block"], "Reject remote operation request")
        self.assertIn(
            "not (ai_ops_remote_acceptance_apply | bool)",
            reject["ansible.builtin.assert"]["that"],
        )
        self.assertTrue(reject["no_log"])
        cleanup_names = [task["name"] for task in operation["always"]]
        self.assertEqual(
            cleanup_names,
            [
                "Stop and disable remote acceptance service",
                "Remove remote approval artifact",
            ],
        )
        stop = operation["always"][0]["ansible.builtin.systemd_service"]
        self.assertFalse(stop["enabled"])
        self.assertEqual(stop["state"], "stopped")
        self.assertTrue(operation["always"][0]["no_log"])
        self.assertTrue(operation["always"][1]["no_log"])
        source = OPERATION_PATH.read_text(encoding="utf-8")
        for prohibited in (
            "ansible.builtin.shell",
            "retries:",
            "until:",
            "enabled: true",
        ):
            self.assertNotIn(prohibited, source)

    def test_egress_contract_remains_permanently_disabled(self):
        self.assertTrue(self.egress_defaults["ai_ops_orchestrator_egress"]["enabled"])
        self.assertEqual(
            self.egress_defaults["ai_ops_orchestrator_egress"]["mode"], "disabled"
        )
        contract = named_task(
            self.egress_tasks, "Assert orchestrator disabled egress contract"
        )
        assertions = contract["ansible.builtin.assert"]["that"]
        self.assertIn("ai_ops_orchestrator_egress.mode == 'disabled'", assertions)
        self.assertIn("ai_ops_orchestrator_egress.approval.id == ''", assertions)
        self.assertIn(
            "ai_ops_orchestrator_egress.approval.expires_at_utc == ''", assertions
        )

    def test_authentication_egress_window_is_fail_closed_until_policy_exists(self):
        self.assertEqual(
            self.auth_egress_window["name"],
            "Operate approved temporary orchestrator authentication egress window",
        )
        window_vars = self.auth_egress_window["vars"]
        self.assertFalse(window_vars["ai_ops_orchestrator_auth_window_apply"])
        self.assertEqual(window_vars["ai_ops_orchestrator_auth_window_approval_id"], "")
        self.assertEqual(
            window_vars["ai_ops_orchestrator_auth_window_expires_at_utc"], ""
        )
        self.assertEqual(
            window_vars["ai_ops_orchestrator_auth_window_pause_seconds"], 0
        )
        self.assertEqual(
            window_vars["ai_ops_orchestrator_auth_window_policy"],
            "dedicated_identity_dns_and_https",
        )
        approval = named_task(
            self.auth_egress_window["tasks"],
            "Assert approved authentication window inputs",
        )
        self.assertTrue(approval["no_log"])
        approval_assertions = approval["ansible.builtin.assert"]["that"]
        self.assertIn(
            "ai_ops_orchestrator_auth_window_approval_id is match('^[A-Za-z0-9][A-Za-z0-9._-]{2,63}$')",
            approval_assertions,
        )
        self.assertIn(
            "ai_ops_orchestrator_auth_window_pause_seconds | int <= 600",
            approval_assertions,
        )
        expiry = named_task(
            self.auth_egress_window["tasks"],
            "Assert authentication window expiry is bounded and current",
        )
        self.assertTrue(expiry["no_log"])
        operation = named_task(
            self.auth_egress_window["tasks"],
            "Materialize and unconditionally remove temporary authentication egress",
        )
        self.assertEqual(
            operation["when"], "ai_ops_orchestrator_auth_window_apply | bool"
        )
        ipv4_allow = named_task(
            operation["block"], "Install temporary IPv4 authentication owner allows"
        )
        ipv6_allow = named_task(
            operation["block"], "Install temporary IPv6 authentication owner allows"
        )
        self.assertTrue(ipv4_allow["no_log"])
        self.assertTrue(ipv6_allow["no_log"])
        self.assertIn(
            "-p udp --dport 53 -j ACCEPT",
            ipv4_allow["ansible.builtin.blockinfile"]["block"],
        )
        self.assertIn(
            "-p tcp --dport 53 -j ACCEPT",
            ipv4_allow["ansible.builtin.blockinfile"]["block"],
        )
        self.assertIn(
            "-p tcp --dport 443 -j ACCEPT",
            ipv4_allow["ansible.builtin.blockinfile"]["block"],
        )
        self.assertIn(
            "ufw6-before-output", ipv6_allow["ansible.builtin.blockinfile"]["block"]
        )
        cleanup_names = [task["name"] for task in operation["always"]]
        self.assertIn(
            "Remove temporary IPv4 authentication owner allows", cleanup_names
        )
        self.assertIn(
            "Remove temporary IPv6 authentication owner allows", cleanup_names
        )
        self.assertIn(
            "Revalidate permanent disabled orchestrator policy", cleanup_names
        )
        self.assertIn(
            "Revalidate independent assistant egress preflight", cleanup_names
        )
        self.assertIn("Revalidate independent assistant egress policy", cleanup_names)
        source = AUTH_EGRESS_WINDOW_PATH.read_text(encoding="utf-8")
        for prohibited in ("ansible.builtin.shell", "login status", "codex-home"):
            self.assertNotIn(prohibited, source)

    @unittest.skipUnless(shutil.which("systemd-analyze"), "systemd-analyze unavailable")
    def test_rendered_remote_unit_verifies(self):
        rendered = self.remote_unit.replace(
            "/opt/openstack-ai-ops/orchestrator/venv/bin/python", "/bin/true", 1
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aiops-orchestrator-remote.service"
            path.write_text(rendered, encoding="utf-8")
            result = subprocess.run(
                ["systemd-analyze", "verify", str(path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
