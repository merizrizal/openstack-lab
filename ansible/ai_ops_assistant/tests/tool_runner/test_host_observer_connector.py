import importlib.util
import io
import json
import os
import stat
import tempfile
import unittest
from datetime import datetime, timezone
from importlib.machinery import SourceFileLoader
from pathlib import Path

CONNECTOR_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/host_observer_connector.py"
)
SPEC = importlib.util.spec_from_loader(
    "host_observer_connector",
    SourceFileLoader("host_observer_connector", str(CONNECTOR_PATH)),
)
CONNECTOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(CONNECTOR)


PROJECTION_NOW = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
VALID_PROJECTION = {
    "schema_version": "1.0",
    "projection_type": "host_observer_destination",
    "revision": "synthetic-revision",
    "generated_at": "2026-08-01T00:00:00Z",
    "expires_at": "2026-08-01T23:59:59Z",
    "entries": [
        {
            "host_label": "controller-a",
            "inventory_role": "controller",
            "source_classes": [
                "metadata_error_events",
                "neutron_error_events",
                "nova_error_events",
            ],
            "enabled": True,
            "destination": {
                "address": "192.0.2.10",
                "port": 22,
                "user": "aiops-host-observer",
            },
        }
    ],
}


class HostObserverConnectorTest(unittest.TestCase):
    def test_fixed_tool_mapping_and_bounded_request(self):
        request = CONNECTOR.validate_host_observer_request(
            "recent_nova_errors", "controller-a", "1h", "large"
        )
        self.assertEqual(request["source_class"], "nova_error_events")
        payload = CONNECTOR.serialize_observer_request(request)
        self.assertLessEqual(len(payload), CONNECTOR.REQUEST_MAX_BYTES)
        self.assertNotIn(b"logical_selector", payload)
        self.assertNotIn(b"address", payload)
        self.assertEqual(json.loads(payload), request)

        for values in (
            ("recent_nova_errors", "controller.a", "30m", "medium"),
            ("recent_nova_errors", "controller-a", "default", "medium"),
            ("recent_nova_errors", "controller-a", "30m", "huge"),
            ("ssh", "controller-a", "30m", "medium"),
        ):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    CONNECTOR.validate_host_observer_request(*values)

    def test_projection_resolution_is_private_and_fail_closed(self):
        destination = CONNECTOR.resolve_observer_destination(
            "recent_nova_errors", "controller-a", VALID_PROJECTION, now=PROJECTION_NOW
        )
        self.assertEqual(destination, VALID_PROJECTION["entries"][0]["destination"])

        for projection in (
            None,
            {**VALID_PROJECTION, "freshness_class": "stale"},
            {**VALID_PROJECTION, "entries": []},
            {
                **VALID_PROJECTION,
                "entries": [
                    VALID_PROJECTION["entries"][0],
                    VALID_PROJECTION["entries"][0],
                ],
            },
        ):
            with self.subTest(projection=projection):
                with self.assertRaises(ValueError):
                    CONNECTOR.resolve_observer_destination(
                        "recent_nova_errors", "controller-a", projection, now=PROJECTION_NOW
                    )

        role_mismatch = {
            **VALID_PROJECTION,
            "entries": [
                {
                    **VALID_PROJECTION["entries"][0],
                    "inventory_role": "compute",
                }
            ],
        }
        with self.assertRaises(ValueError):
            CONNECTOR.resolve_observer_destination(
                "recent_nova_errors", "controller-a", role_mismatch, now=PROJECTION_NOW
            )

    def test_ssh_argv_is_fixed_and_has_no_remote_command(self):
        with tempfile.TemporaryDirectory() as directory:
            key_path = Path(directory) / "observer.key"
            known_hosts_path = Path(directory) / "known_hosts"
            for path in (key_path, known_hosts_path):
                path.write_text("synthetic", encoding="utf-8")
                os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)

            argv = CONNECTOR.build_fixed_ssh_argv(
                VALID_PROJECTION["entries"][0]["destination"],
                key_path,
                known_hosts_path,
            )

        self.assertEqual(argv[0], "/usr/bin/ssh")
        self.assertIn("-F", argv)
        self.assertIn("/dev/null", argv)
        self.assertIn("ForwardAgent=no", argv)
        self.assertIn("ClearAllForwardings=yes", argv)
        self.assertEqual(argv[-1], "aiops-host-observer@192.0.2.10")
        self.assertNotIn(CONNECTOR.COLLECTOR_PATH, argv)
        self.assertNotIn("bash", argv)
        self.assertNotIn("sh", argv)

    def test_run_connector_uses_bounded_stdin_and_fixed_execution_options(self):
        calls = []

        def fake_run(argv, **kwargs):
            calls.append((argv, kwargs))
            return __import__("subprocess").CompletedProcess(
                argv, 0, stdout=b"{}", stderr=b""
            )

        with tempfile.TemporaryDirectory() as directory:
            key_path = Path(directory) / "observer.key"
            known_hosts_path = Path(directory) / "known_hosts"
            for path in (key_path, known_hosts_path):
                path.write_text("synthetic", encoding="utf-8")
                os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
            request = CONNECTOR.validate_host_observer_request(
                "recent_metadata_errors", "controller-a"
            )
            result = CONNECTOR.run_connector(
                CONNECTOR.serialize_observer_request(request),
                VALID_PROJECTION["entries"][0]["destination"],
                key_path,
                known_hosts_path,
                fake_run,
            )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(calls), 1)
        argv, kwargs = calls[0]
        self.assertEqual(kwargs["input"], CONNECTOR.serialize_observer_request(request))
        self.assertEqual(kwargs["timeout"], CONNECTOR.CONNECTOR_TIMEOUT_SECONDS)
        self.assertFalse(kwargs["shell"])
        self.assertFalse(kwargs["check"])
        self.assertNotIn("--", argv)

    def test_valid_connector_request_remains_unavailable_without_projection(self):
        request = CONNECTOR.validate_host_observer_request(
            "recent_neutron_errors", "controller-a"
        )
        output = io.StringIO()
        exit_code = CONNECTOR.main(
            argv=[],
            stdin=io.BytesIO(CONNECTOR.serialize_observer_request(request)),
            stdout=output,
        )
        document = json.loads(output.getvalue())
        self.assertEqual(exit_code, 5)
        self.assertEqual(document["tool"], "recent_neutron_errors")
        self.assertEqual(document["status"], "unavailable")
        self.assertEqual(
            document["error"]["class"], "approved_optional_capability_absent"
        )


    def test_destination_projection_requires_owner_freshness_and_distinct_schema(self):
        invalid_projections = (
            {**VALID_PROJECTION, "projection_type": "host_observer_metadata"},
            {**VALID_PROJECTION, "generated_at": "2026-08-01T12:00:01Z"},
            {**VALID_PROJECTION, "expires_at": "2026-08-01T11:59:59Z"},
            {**VALID_PROJECTION, "expires_at": "2026-08-02T00:00:01Z"},
        )
        for projection in invalid_projections:
            with self.subTest(projection=projection):
                with self.assertRaises(ValueError):
                    CONNECTOR.resolve_observer_destination(
                        "recent_nova_errors",
                        "controller-a",
                        projection,
                        now=PROJECTION_NOW,
                    )

    def test_neutron_projection_allows_compute_role_but_not_metadata_or_nova(self):
        compute_projection = {
            **VALID_PROJECTION,
            "entries": [
                {
                    **VALID_PROJECTION["entries"][0],
                    "host_label": "compute-a",
                    "inventory_role": "compute",
                    "source_classes": ["neutron_error_events"],
                }
            ],
        }
        destination = CONNECTOR.resolve_observer_destination(
            "recent_neutron_errors",
            "compute-a",
            compute_projection,
            now=PROJECTION_NOW,
        )
        self.assertEqual(destination["user"], "aiops-host-observer")
        with self.assertRaises(ValueError):
            CONNECTOR.resolve_observer_destination(
                "recent_nova_errors",
                "compute-a",
                compute_projection,
                now=PROJECTION_NOW,
            )

    def test_protected_projection_loader_checks_owner_mode_and_regular_file(self):
        with tempfile.TemporaryDirectory() as directory:
            projection_directory = Path(directory) / "host-observer"
            projection_directory.mkdir()
            os.chmod(projection_directory, 0o700)
            projection_path = projection_directory / "destination-projection.json"
            projection_path.write_text(json.dumps(VALID_PROJECTION), encoding="utf-8")
            os.chmod(projection_path, 0o600)
            loaded = CONNECTOR.load_destination_projection(
                projection_path,
                now=PROJECTION_NOW,
                expected_uid=os.getuid(),
                expected_gid=os.getgid(),
            )
            self.assertEqual(loaded["projection_type"], "host_observer_destination")
            os.chmod(projection_path, 0o640)
            with self.assertRaises(ValueError):
                CONNECTOR.load_destination_projection(
                    projection_path,
                    now=PROJECTION_NOW,
                    expected_uid=os.getuid(),
                    expected_gid=os.getgid(),
                )

if __name__ == "__main__":
    unittest.main()
