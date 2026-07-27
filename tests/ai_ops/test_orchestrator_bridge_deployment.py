import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml
from jinja2 import Environment, StrictUndefined

REPO_ROOT = Path(__file__).resolve().parents[2]
ROLE_ROOT = REPO_ROOT / "ansible/ai_ops_runtime/roles/orchestrator_runtime"
TASKS_PATH = ROLE_ROOT / "tasks/main.yml"
SOCKET_TEMPLATE_PATH = ROLE_ROOT / "templates/aiops-assistant-mcp-bridge.socket.j2"
SERVICE_TEMPLATE_PATH = ROLE_ROOT / "templates/aiops-assistant-mcp-bridge.service.j2"
ACTIVATION_PLAYBOOK_PATH = (
    REPO_ROOT
    / "ansible/ai_ops_runtime/playbook_validate_phase12_assistant_bridge_activation.yml"
)
SOCKET_NAME = "aiops-assistant-mcp-bridge.socket"
SERVICE_NAME = "aiops-assistant-mcp-bridge.service"
SOCKET_PATH = "/run/openstack-ai-ops/assistant-mcp-bridge.sock"
APPROVED_PEER_UID = "12345"


def render_unit(path):
    environment = Environment(undefined=StrictUndefined, keep_trailing_newline=True)
    template = environment.from_string(path.read_text(encoding="utf-8"))
    return template.render(
        ai_ops_orchestrator={
            "bridge_service_name": "aiops-assistant-mcp-bridge",
            "bridge_socket_name": "aiops-assistant-mcp-bridge",
            "group": "aiops-orchestrator",
            "root": "/opt/openstack-ai-ops/orchestrator",
        },
        ai_ops_orchestrator_bridge_peer_uid={"stdout": APPROVED_PEER_UID},
    )


def parse_unit(rendered):
    sections = {}
    current_section = None
    for raw_line in rendered.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1]
            sections[current_section] = []
            continue
        if current_section is None or "=" not in line:
            raise AssertionError(f"invalid unit line: {raw_line!r}")
        key, value = line.split("=", 1)
        sections[current_section].append((key, value))
    return sections


def unit_value(sections, section, key):
    values = [value for item_key, value in sections[section] if item_key == key]
    if len(values) != 1:
        raise AssertionError(f"expected one {section}.{key}, found {values!r}")
    return values[0]


def named_task(tasks, name):
    matches = [task for task in tasks if task.get("name") == name]
    if len(matches) != 1:
        raise AssertionError(f"expected one task {name!r}, found {len(matches)}")
    return matches[0]


class TestOrchestratorBridgeDeploymentContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.socket_unit = render_unit(SOCKET_TEMPLATE_PATH)
        cls.service_unit = render_unit(SERVICE_TEMPLATE_PATH)
        cls.tasks = yaml.safe_load(TASKS_PATH.read_text(encoding="utf-8"))
        cls.activation_play = yaml.safe_load(
            ACTIVATION_PLAYBOOK_PATH.read_text(encoding="utf-8")
        )[0]

    def test_socket_unit_is_fixed_static_unix_transport(self):
        sections = parse_unit(self.socket_unit)

        self.assertEqual(set(sections), {"Unit", "Socket"})
        self.assertEqual(unit_value(sections, "Socket", "ListenStream"), SOCKET_PATH)
        self.assertEqual(unit_value(sections, "Socket", "SocketUser"), "assistant")
        self.assertEqual(
            unit_value(sections, "Socket", "SocketGroup"), "aiops-orchestrator"
        )
        self.assertEqual(unit_value(sections, "Socket", "SocketMode"), "0660")
        self.assertEqual(unit_value(sections, "Socket", "DirectoryMode"), "0755")
        self.assertEqual(unit_value(sections, "Socket", "Accept"), "no")
        self.assertEqual(unit_value(sections, "Socket", "RemoveOnStop"), "true")
        self.assertEqual(unit_value(sections, "Socket", "Service"), SERVICE_NAME)

        for prohibited in (
            "[Install]",
            "WantedBy=",
            "OnCalendar=",
            "ListenDatagram=",
            "ListenFIFO=",
            "Accept=yes",
            "0.0.0.0",
            "::",
        ):
            self.assertNotIn(prohibited, self.socket_unit)

    def test_service_unit_has_fixed_identity_uid_and_hardening(self):
        sections = parse_unit(self.service_unit)

        self.assertEqual(set(sections), {"Unit", "Service"})
        self.assertEqual(unit_value(sections, "Service", "User"), "assistant")
        self.assertEqual(unit_value(sections, "Service", "Group"), "assistant")
        self.assertEqual(unit_value(sections, "Service", "Restart"), "no")
        self.assertEqual(unit_value(sections, "Service", "NoNewPrivileges"), "true")
        self.assertEqual(unit_value(sections, "Service", "CapabilityBoundingSet"), "")
        self.assertEqual(unit_value(sections, "Service", "AmbientCapabilities"), "")
        self.assertEqual(unit_value(sections, "Service", "UMask"), "0077")
        self.assertEqual(
            unit_value(sections, "Service", "ExecStart"),
            "/opt/openstack-ai-ops/.venv/bin/python "
            "/opt/openstack-ai-ops/mcp/aiops_assistant_bridge.py "
            f"--approved-peer-uid={APPROVED_PEER_UID}",
        )

        for prohibited in (
            "[Install]",
            "WantedBy=",
            "OnCalendar=",
            "Restart=always",
            "Restart=on-",
            "ExecStartPre=",
            "sudo",
            "0.0.0.0",
            "ListenStream=",
            "ListenDatagram=",
        ):
            self.assertNotIn(prohibited, self.service_unit)

    def test_role_stages_validates_and_installs_canonical_pair(self):
        stage = named_task(
            self.tasks, "Create temporary assistant bridge unit validation directory"
        )
        self.assertEqual(stage["ansible.builtin.tempfile"]["state"], "directory")

        lifecycle = named_task(
            self.tasks, "Validate and install the paired assistant bridge units"
        )
        render = named_task(
            lifecycle["block"],
            "Render assistant bridge units with canonical names for validation",
        )
        validate = named_task(
            lifecycle["block"], "Validate the paired assistant bridge units"
        )
        install = named_task(
            lifecycle["block"],
            "Install validated assistant bridge units without enabling them",
        )

        expected_loop = [
            "{{ ai_ops_orchestrator.bridge_socket_name }}.socket",
            "{{ ai_ops_orchestrator.bridge_service_name }}.service",
        ]
        self.assertEqual(render["loop"], expected_loop)
        self.assertEqual(render["ansible.builtin.template"]["src"], "{{ item }}.j2")
        self.assertEqual(render["ansible.builtin.template"]["mode"], "0644")

        argv = validate["ansible.builtin.command"]["argv"]
        self.assertEqual(argv[:2], ["/usr/bin/systemd-analyze", "verify"])
        self.assertEqual(
            argv[2:],
            [
                (
                    "{{ ai_ops_orchestrator_bridge_unit_stage.path }}/"
                    "{{ ai_ops_orchestrator.bridge_socket_name }}.socket"
                ),
                (
                    "{{ ai_ops_orchestrator_bridge_unit_stage.path }}/"
                    "{{ ai_ops_orchestrator.bridge_service_name }}.service"
                ),
            ],
        )

        copy = install["ansible.builtin.copy"]
        self.assertEqual(install["loop"], expected_loop)
        self.assertTrue(copy["remote_src"])
        self.assertEqual(copy["dest"], "/etc/systemd/system/{{ item }}")
        self.assertEqual(
            (copy["owner"], copy["group"], copy["mode"]),
            ("root", "root", "0644"),
        )

        cleanup = named_task(
            lifecycle["always"],
            "Remove temporary assistant bridge unit validation directory",
        )
        self.assertEqual(cleanup["ansible.builtin.file"]["state"], "absent")

    def test_role_deploys_credential_free_proxy_and_client_sources(self):
        source_task = named_task(
            self.tasks, "Install fixed fake-only orchestrator sources"
        )
        deployed_sources = source_task["loop"]
        self.assertIn("mcp_client.py", deployed_sources)
        self.assertIn("mcp_stdio_proxy.py", deployed_sources)
        copy = source_task["ansible.builtin.copy"]
        self.assertEqual(
            (copy["owner"], copy["group"], copy["mode"]), ("root", "root", "0644")
        )

    def test_role_materializes_uid_and_keeps_bridge_stopped(self):
        runtime_directory = named_task(
            self.tasks, "Create root-owned assistant bridge runtime directory"
        )["ansible.builtin.file"]
        self.assertEqual(runtime_directory["path"], "/run/openstack-ai-ops")
        self.assertEqual(
            (
                runtime_directory["owner"],
                runtime_directory["group"],
                runtime_directory["mode"],
            ),
            ("root", "root", "0755"),
        )

        resolve_uid = named_task(
            self.tasks,
            "Resolve orchestrator numeric UID for assistant bridge peer validation",
        )
        self.assertEqual(
            resolve_uid["ansible.builtin.command"]["argv"],
            ["/usr/bin/id", "-u", "{{ ai_ops_orchestrator.user }}"],
        )
        self.assertTrue(resolve_uid["no_log"])

        assert_uid = named_task(
            self.tasks, "Assert orchestrator bridge peer UID is numeric"
        )
        self.assertEqual(
            assert_uid["ansible.builtin.assert"]["that"],
            ["ai_ops_orchestrator_bridge_peer_uid.stdout | trim is match('^[0-9]+$')"],
        )
        self.assertTrue(assert_uid["no_log"])

        socket_stop = named_task(
            self.tasks, "Keep assistant bridge socket disabled and stopped"
        )["ansible.builtin.systemd_service"]
        service_stop = named_task(
            self.tasks, "Keep assistant bridge service disabled and stopped"
        )["ansible.builtin.systemd_service"]
        for state in (socket_stop, service_stop):
            self.assertFalse(state["enabled"])
            self.assertEqual(state["state"], "stopped")
        self.assertLess(
            self.tasks.index(
                named_task(
                    self.tasks, "Keep assistant bridge socket disabled and stopped"
                )
            ),
            self.tasks.index(
                named_task(
                    self.tasks, "Keep assistant bridge service disabled and stopped"
                )
            ),
        )

    def test_activation_playbook_is_gated_fake_only_and_cleanup_ordered(self):
        variables = self.activation_play["vars"]
        tasks = self.activation_play["tasks"]
        self.assertFalse(variables["ai_ops_bridge_activation_apply"])

        gate = named_task(tasks, "Assert bridge activation approval and target scope")
        self.assertIn(
            "ai_ops_bridge_activation_apply | bool",
            gate["ansible.builtin.assert"]["that"],
        )
        operation = named_task(
            tasks, "Exercise fake-only bridge activation with unconditional cleanup"
        )
        operation_tasks = operation["block"]
        dropin = named_task(
            operation_tasks, "Install temporary fake-runner service drop-in"
        )["ansible.builtin.copy"]["content"]
        self.assertIn("ExecStart=\n", dropin)
        self.assertIn("validation_entrypoint.py", dropin)
        self.assertIn("--approved-peer-uid=", dropin)

        entrypoint = named_task(
            operation_tasks, "Install temporary fake bridge validation entrypoint"
        )["ansible.builtin.copy"]["content"]
        self.assertIn("run_activated_bridge", entrypoint)
        self.assertIn("AdapterPaths", entrypoint)
        self.assertIn("fake_reviewed_runner.py", entrypoint)

        start = named_task(operation_tasks, "Start exact assistant bridge socket")
        self.assertFalse(start["ansible.builtin.systemd_service"]["enabled"])
        self.assertEqual(start["ansible.builtin.systemd_service"]["state"], "started")

        cleanup_names = [task["name"] for task in operation["always"]]
        self.assertLess(
            cleanup_names.index("Stop assistant bridge socket before service"),
            cleanup_names.index("Stop assistant bridge service after socket"),
        )
        self.assertLess(
            cleanup_names.index("Remove temporary fake-runner service drop-in"),
            cleanup_names.index("Reload systemd after fake-runner drop-in removal"),
        )
        self.assertIn(
            "Assert bridge cleanup restored the static baseline", cleanup_names
        )

        playbook_source = ACTIVATION_PLAYBOOK_PATH.read_text(encoding="utf-8")
        for prohibited in (
            "ansible.builtin.shell",
            "ansible.builtin.uri",
            "ansible.builtin.get_url",
            "enabled: true",
            "retries:",
            "until:",
        ):
            self.assertNotIn(prohibited, playbook_source)

    @unittest.skipUnless(shutil.which("systemd-analyze"), "systemd-analyze unavailable")
    def test_rendered_units_verify_together_with_canonical_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            socket_path = root / SOCKET_NAME
            service_path = root / SERVICE_NAME
            socket_path.write_text(self.socket_unit, encoding="utf-8")
            service_path.write_text(
                self.service_unit.replace(
                    "/opt/openstack-ai-ops/.venv/bin/python", "/bin/true", 1
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                ["systemd-analyze", "verify", str(socket_path), str(service_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
