import importlib.util
import io
import json
import subprocess
import unittest
from datetime import datetime, timedelta, timezone
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch

SCRIPT_PATH = (
    Path(__file__).parents[2]
    / "roles/ai_ops_assistant_host_observer_boundary/files/scripts/host_observer/host_observer_collector.py"
)
SPEC = importlib.util.spec_from_loader(
    "host_observer_collector",
    SourceFileLoader("host_observer_collector", str(SCRIPT_PATH)),
)
COLLECTOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(COLLECTOR)


VALID_REQUEST = {
    "schema_version": "1.0",
    "host_label": "controller-a",
    "source_class": "metadata_error_events",
    "window_class": "30m",
    "line_limit_class": "medium",
}
VALID_PROJECTION = {
    "schema_version": "1.0",
    "projection_type": "host_observer_metadata",
    "revision": "fixture-revision",
    "freshness_class": "current",
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
        }
    ],
}


def policy_reader(adapter_id):
    return {
        "adapter_id": adapter_id,
        "argv": list(COLLECTOR.ADAPTER_DEFINITIONS[adapter_id]["argv"]),
    }


POLICY_GENERATED_AT = datetime.now(timezone.utc) - timedelta(hours=1)
POLICY_EXPIRES_AT = POLICY_GENERATED_AT + timedelta(hours=2)

VALID_POLICY = {
    "schema_version": "1.0",
    "policy_type": "host_observer_policy",
    "revision": "fixture-revision",
    "generated_at": POLICY_GENERATED_AT.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    "expires_at": POLICY_EXPIRES_AT.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    "freshness_class": "current",
    "metadata_status": "accepted",
    "redaction_policy_status": "accepted",
    "source_classes": [
        "metadata_error_events",
        "neutron_error_events",
        "nova_error_events",
    ],
    "window_classes": ["15m", "30m", "1h"],
    "line_limit_classes": ["small", "medium", "large"],
    "local_host_label": "controller-a",
    "hosts": [
        {
            "host_label": "controller-a",
            "inventory_role": "controller",
            "source_classes": [
                "metadata_error_events",
                "neutron_error_events",
                "nova_error_events",
            ],
            "enabled": True,
        }
    ],
    "entries": [
        {
            "source_class": "metadata_error_events",
            "logical_selector": "metadata_service_errors",
            "inventory_role": "controller",
            "readers": [
                policy_reader("metadata_agent_errors"),
                policy_reader("metadata_apache_errors"),
            ],
        },
        {
            "source_class": "neutron_error_events",
            "logical_selector": "neutron_service_errors",
            "inventory_role": "controller",
            "readers": [
                policy_reader("neutron_server_errors"),
                policy_reader("neutron_ovs_agent_errors"),
            ],
        },
        {
            "source_class": "neutron_error_events",
            "logical_selector": "neutron_service_errors",
            "inventory_role": "compute",
            "readers": [policy_reader("neutron_ovs_agent_errors")],
        },
        {
            "source_class": "nova_error_events",
            "logical_selector": "nova_service_errors",
            "inventory_role": "controller",
            "readers": [
                policy_reader("nova_api_errors"),
                policy_reader("nova_conductor_errors"),
                policy_reader("nova_scheduler_errors"),
                policy_reader("nova_apache_errors"),
            ],
        },
    ],
}


COLLECTION_START = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
COLLECTION_START_TEXT = "2026-08-01T12:00:00.000000Z"


def metadata_record(
    sequence,
    observed_at,
    severity="error",
    event_class="request_error",
    summary="metadata failure",
):
    return {
        "source_sequence": sequence,
        "observed_at": observed_at,
        "severity": severity,
        "event_class": event_class,
        "summary": summary,
    }


class HostObserverCollectorTest(unittest.TestCase):
    def test_valid_request_dispatches_all_fixed_metadata_readers(self):
        now = datetime.now(timezone.utc).replace(microsecond=123456)

        def fake_execute(argv, _timeout):
            if "--unit" in argv:
                unit = argv[argv.index("--unit") + 1]
                payload = {
                    "_SYSTEMD_UNIT": unit,
                    "_SEQNUM": "1",
                    "__REALTIME_TIMESTAMP": str(int(now.timestamp() * 1_000_000)),
                    "PRIORITY": "3",
                    "MESSAGE": "metadata service failure",
                }
                return (
                    subprocess.CompletedProcess(
                        argv, 0, json.dumps(payload).encode() + b"\n", b""
                    ),
                    False,
                )
            apache_line = (
                now.strftime("[%a %b %d %H:%M:%S.%f %Y]")
                + " [proxy:error] metadata apache failure\n"
            )
            return (
                subprocess.CompletedProcess(argv, 0, apache_line.encode(), b""),
                False,
            )

        snapshot = COLLECTOR.PolicySnapshot(
            VALID_POLICY, "fixture-digest", (1, 2, 3, 4, 5), COLLECTOR.POLICY_PATH
        )
        with patch.object(
            COLLECTOR, "load_policy", return_value=snapshot
        ), patch.object(COLLECTOR, "verify_policy_snapshot"), patch.object(
            COLLECTOR, "execute_fixed_argv", side_effect=fake_execute
        ):
            exit_code, document = COLLECTOR.run(
                raw_request=json.dumps(VALID_REQUEST).encode()
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(document["tool"], "recent_metadata_errors")
        self.assertEqual(document["status"], "ok")
        self.assertEqual(len(document["sections"][0]["data"]), 2)

    def test_valid_request_dispatches_neutron_and_nova_tools(self):
        now = datetime.now(timezone.utc).replace(microsecond=123456)

        def fake_execute(argv, _timeout):
            if "--unit" in argv:
                unit = argv[argv.index("--unit") + 1]
                payload = {
                    "_SYSTEMD_UNIT": unit,
                    "_SEQNUM": "1",
                    "__REALTIME_TIMESTAMP": str(int(now.timestamp() * 1_000_000)),
                    "PRIORITY": "3",
                    "MESSAGE": "fixed service failure",
                }
                return (
                    subprocess.CompletedProcess(
                        argv, 0, json.dumps(payload).encode() + b"\n", b""
                    ),
                    False,
                )
            line = (
                now.strftime("[%a %b %d %H:%M:%S.%f %Y]")
                + " [proxy:error] fixed apache failure\n"
            )
            return (
                subprocess.CompletedProcess(argv, 0, line.encode(), b""),
                False,
            )

        for source_class, tool_name in (
            ("neutron_error_events", "recent_neutron_errors"),
            ("nova_error_events", "recent_nova_errors"),
        ):
            request = {**VALID_REQUEST, "source_class": source_class}
            snapshot = COLLECTOR.PolicySnapshot(
                VALID_POLICY,
                "fixture-digest",
                (1, 2, 3, 4, 5),
                COLLECTOR.POLICY_PATH,
            )
            with self.subTest(source_class=source_class), patch.object(
                COLLECTOR, "load_policy", return_value=snapshot
            ), patch.object(COLLECTOR, "verify_policy_snapshot"), patch.object(
                COLLECTOR, "execute_fixed_argv", side_effect=fake_execute
            ):
                exit_code, document = COLLECTOR.run(
                    raw_request=json.dumps(request).encode()
                )
            self.assertEqual(exit_code, 0)
            self.assertEqual(document["tool"], tool_name)
            self.assertEqual(document["status"], "ok")

    def test_invocation_arguments_and_original_command_are_rejected(self):
        for argv, environment in (
            (["unexpected"], {}),
            ([], {"SSH_ORIGINAL_COMMAND": "x"}),
        ):
            with self.subTest(argv=argv, environment=environment):
                exit_code, document = COLLECTOR.run(argv, environment, b"")
                self.assertEqual(exit_code, 2)
                self.assertEqual(document["error"]["class"], "invocation_denied")

    def test_request_rejects_duplicate_unknown_oversized_and_unsafe_values(self):
        cases = (
            b'{"schema_version":"1.0","schema_version":"1.0","host_label":"controller-a","source_class":"metadata_error_events","window_class":"default","line_limit_class":"default"}',
            json.dumps({**VALID_REQUEST, "extra": "no"}).encode(),
            b"{" + b"x" * (COLLECTOR.REQUEST_MAX_BYTES + 1) + b"}",
            json.dumps({**VALID_REQUEST, "host_label": "controller.a"}).encode(),
            json.dumps({**VALID_REQUEST, "source_class": "shell"}).encode(),
        )
        for raw in cases:
            with self.subTest(raw=raw[:40]):
                exit_code, document = COLLECTOR.run(raw_request=raw)
                self.assertEqual(exit_code, 2)
                self.assertEqual(document["status"], "error")
                self.assertEqual(document["error"]["class"], "validation_error")

    def test_projection_and_policy_metadata_accept_only_closed_synthetic_shapes(self):
        request = COLLECTOR.parse_request(json.dumps(VALID_REQUEST))
        self.assertEqual(
            COLLECTOR.resolve_projection(request, VALID_PROJECTION)["inventory_role"],
            "controller",
        )
        self.assertEqual(
            COLLECTOR.validate_boundary(request, VALID_PROJECTION, VALID_POLICY)[
                "host_label"
            ],
            "controller-a",
        )

        stale = {**VALID_PROJECTION, "freshness_class": "stale"}
        with self.assertRaises(COLLECTOR.CollectorUnavailableError):
            COLLECTOR.validate_projection_metadata(stale)

        duplicate = {
            **VALID_PROJECTION,
            "entries": VALID_PROJECTION["entries"] * 2,
        }
        with self.assertRaises(COLLECTOR.CollectorValidationError):
            COLLECTOR.validate_projection_metadata(duplicate)

        unsafe = {
            **VALID_PROJECTION,
            "entries": [{**VALID_PROJECTION["entries"][0], "address": "forbidden"}],
        }
        with self.assertRaises(COLLECTOR.CollectorValidationError):
            COLLECTOR.validate_projection_metadata(unsafe)

        unresolved_policy = {**VALID_POLICY, "metadata_status": "unresolved"}
        with self.assertRaises(COLLECTOR.CollectorUnavailableError):
            COLLECTOR.validate_policy_metadata(unresolved_policy)

    def test_unavailable_document_is_deterministic_and_contains_no_source_data(self):
        first = COLLECTOR.unavailable_document()
        second = COLLECTOR.unavailable_document()
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "unavailable")
        self.assertNotIn("data", first)
        self.assertNotIn("address", json.dumps(first))

    def test_metadata_success_uses_fixed_schema_window_and_deterministic_order(self):
        records = [
            metadata_record(
                3,
                "2026-08-01T11:45:00Z",
                "warning",
                "dependency_error",
                "dependency controller-a",
            ),
            metadata_record(
                2,
                "2026-08-01T11:45:00Z",
                "critical",
                "connection_error",
                "password=secret 10.0.0.1",
            ),
            metadata_record(
                1, "2026-08-01T11:45:00Z", "error", "request_error", "normal"
            ),
            metadata_record(
                4, "2026-08-01T09:00:00Z", "critical", "timeout", "outside window"
            ),
        ]
        document = COLLECTOR.collect_metadata_slice(
            records,
            False,
            "current",
            "controller-a",
            "controller",
            "30m",
            "medium",
            COLLECTION_START,
        )
        self.assertEqual(document["status"], "ok")
        self.assertIsNone(document["error"])
        section = document["sections"][0]
        self.assertEqual(section["name"], "metadata_errors")
        self.assertEqual(section["status"], "ok")
        self.assertEqual(
            [event["source_class"] for event in section["data"]],
            ["metadata_error_events"] * 3,
        )
        self.assertEqual(
            [event["severity"] for event in section["data"]],
            ["critical", "error", "warning"],
        )
        self.assertEqual(
            set(section["data"][0]),
            {
                "host_label",
                "inventory_role",
                "source_class",
                "service_class",
                "observed_at",
                "severity",
                "event_class",
                "redacted_summary",
            },
        )
        self.assertNotIn("password=secret", json.dumps(document))
        self.assertNotIn("10.0.0.1", json.dumps(document))

    def test_metadata_empty_and_source_truncated_are_explicit(self):
        document = COLLECTOR.collect_metadata_slice(
            [metadata_record(1, "2026-08-01T10:00:00Z")],
            True,
            "current",
            "controller-a",
            "controller",
            "15m",
            "small",
            COLLECTION_START_TEXT,
        )
        self.assertEqual(document["status"], "ok")
        self.assertEqual(document["sections"][0]["status"], "empty")
        self.assertEqual(document["sections"][0]["data"], [])
        self.assertTrue(document["sections"][0]["truncated"])

    def test_metadata_source_and_role_failures_have_no_sections(self):
        cases = (
            (None, "source_missing", "unavailable"),
            ("stale", "source_stale", "unavailable"),
            ("denied", "source_denied", "denied"),
            ("malformed", "malformed_source", "error"),
            ("timeout", "timeout", "timeout"),
        )
        for source_records, error_class, status in cases:
            with self.subTest(error_class=error_class):
                document = COLLECTOR.collect_metadata_slice(
                    source_records,
                    False,
                    "current",
                    "controller-a",
                    "controller",
                    "30m",
                    "medium",
                    COLLECTION_START,
                )
                self.assertEqual(document["status"], status)
                self.assertEqual(document["error"]["class"], error_class)
                self.assertEqual(document["sections"], [])

        role_mismatch = COLLECTOR.collect_metadata_slice(
            [metadata_record(1, "2026-08-01T11:45:00Z")],
            False,
            "current",
            "compute-a",
            "compute",
            "30m",
            "medium",
            COLLECTION_START,
        )
        self.assertEqual(role_mismatch["error"]["class"], "source_role_mismatch")
        self.assertEqual(role_mismatch["sections"], [])

        stale_before_malformed = COLLECTOR.collect_metadata_slice(
            [{"not": "a record"}],
            False,
            "stale",
            "controller-a",
            "controller",
            "30m",
            "medium",
            COLLECTION_START,
        )
        self.assertEqual(stale_before_malformed["error"]["class"], "source_stale")

    def test_malformed_record_fails_atomically(self):
        document = COLLECTOR.collect_metadata_slice(
            [metadata_record(1, "2026-08-01T11:45:00Z"), {"source_sequence": 2}],
            False,
            "current",
            "controller-a",
            "controller",
            "30m",
            "medium",
            COLLECTION_START,
        )
        self.assertEqual(document["status"], "error")
        self.assertEqual(document["error"]["class"], "malformed_source")
        self.assertEqual(document["sections"], [])

    def test_timestamp_validation_rejects_future_and_excess_precision(self):
        for timestamp in ("2026-08-01T12:00:01Z", "2026-08-01T11:00:00.1234567Z"):
            with self.subTest(timestamp=timestamp):
                document = COLLECTOR.collect_metadata_slice(
                    [metadata_record(1, timestamp)],
                    False,
                    "current",
                    "controller-a",
                    "controller",
                    "30m",
                    "medium",
                    COLLECTION_START,
                )
                self.assertEqual(document["error"]["class"], "malformed_source")
                self.assertEqual(document["sections"], [])

    def test_duplicates_are_retained_and_record_cap_is_deterministic(self):
        duplicate = metadata_record(1, "2026-08-01T11:45:00Z")
        document = COLLECTOR.collect_metadata_slice(
            [duplicate, duplicate.copy()],
            False,
            "current",
            "controller-a",
            "controller",
            "30m",
            "medium",
            COLLECTION_START,
        )
        self.assertEqual(len(document["sections"][0]["data"]), 2)

        records = [
            metadata_record(index, "2026-08-01T11:45:00Z") for index in range(25)
        ]
        capped = COLLECTOR.collect_metadata_slice(
            records,
            False,
            "current",
            "controller-a",
            "controller",
            "30m",
            "medium",
            COLLECTION_START,
        )
        self.assertEqual(len(capped["sections"][0]["data"]), 20)
        self.assertTrue(capped["sections"][0]["truncated"])
        self.assertEqual(
            [event["redacted_summary"] for event in capped["sections"][0]["data"]],
            ["metadata failure"] * 20,
        )

    def test_utf8_message_and_serialized_output_bounds_are_enforced(self):
        message = "é" * 600
        document = COLLECTOR.collect_metadata_slice(
            [metadata_record(1, "2026-08-01T11:45:00Z", summary=message)],
            False,
            "current",
            "h" * 64,
            "controller",
            "30m",
            "medium",
            COLLECTION_START,
        )
        event = document["sections"][0]["data"][0]
        self.assertLessEqual(len(event["redacted_summary"].encode("utf-8")), 512)

        original_output_limit = COLLECTOR.SERIALIZED_OUTPUT_MAX_BYTES
        COLLECTOR.SERIALIZED_OUTPUT_MAX_BYTES = 1_000
        try:
            large = COLLECTOR.collect_metadata_slice(
                [
                    metadata_record(index, "2026-08-01T11:45:00Z", summary="x" * 4096)
                    for index in range(20)
                ],
                False,
                "current",
                "h" * 64,
                "controller",
                "30m",
                "medium",
                COLLECTION_START,
            )
        finally:
            COLLECTOR.SERIALIZED_OUTPUT_MAX_BYTES = original_output_limit
        serialized = (
            json.dumps(large, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        self.assertLessEqual(len(serialized), 1_000)
        self.assertTrue(large["sections"][0]["truncated"])

    def test_redaction_canaries_are_removed(self):
        summary = (
            "password=secret token=abc authorization: Bearer xyz "
            "-----BEGIN PRIVATE KEY-----secret-----END PRIVATE KEY----- "
            "https://user:pass@example.invalid 192.0.2.10 2001:db8::1 "
            "aa:bb:cc:dd:ee:ff 123e4567-e89b-12d3-a456-426614174000 controller-a"
        )
        document = COLLECTOR.collect_metadata_slice(
            [metadata_record(1, "2026-08-01T11:45:00Z", summary=summary)],
            False,
            "current",
            "controller-a",
            "controller",
            "30m",
            "medium",
            COLLECTION_START,
        )
        redacted = document["sections"][0]["data"][0]["redacted_summary"]
        for canary in (
            "secret",
            "abc",
            "xyz",
            "PRIVATE KEY",
            "example.invalid",
            "192.0.2.10",
            "2001:db8",
            "aa:bb:cc:dd:ee:ff",
            "123e4567-e89b-12d3-a456-426614174000",
            "controller-a",
        ):
            self.assertNotIn(canary, redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_redaction_failure_discards_all_events(self):
        document = COLLECTOR.collect_metadata_slice(
            [
                metadata_record(1, "2026-08-01T11:45:00Z"),
                metadata_record(
                    2, "2026-08-01T11:45:00Z", summary="__REDACTION_FAILURE__"
                ),
            ],
            False,
            "current",
            "controller-a",
            "controller",
            "30m",
            "medium",
            COLLECTION_START,
        )
        self.assertEqual(document["status"], "error")
        self.assertEqual(document["error"]["class"], "redaction_failure")
        self.assertEqual(document["sections"], [])

    def test_raw_summary_and_unknown_enum_validation_are_closed(self):
        for summary in ("x" * (COLLECTOR.MAX_RAW_SUMMARY_BYTES + 1), "\ud800", ""):
            with self.subTest(summary=repr(summary)):
                document = COLLECTOR.collect_metadata_slice(
                    [metadata_record(1, "2026-08-01T11:45:00Z", summary=summary)],
                    False,
                    "current",
                    "controller-a",
                    "controller",
                    "30m",
                    "medium",
                    COLLECTION_START,
                )
                self.assertEqual(document["error"]["class"], "malformed_source")
                self.assertEqual(document["sections"], [])

        document = COLLECTOR.collect_metadata_slice(
            [
                metadata_record(
                    1, "2026-08-01T11:45:00Z", "not-a-severity", "not-an-event"
                )
            ],
            False,
            "current",
            "controller-a",
            "controller",
            "30m",
            "medium",
            COLLECTION_START,
        )
        event = document["sections"][0]["data"][0]
        self.assertEqual(event["severity"], "unknown")
        self.assertEqual(event["event_class"], "unknown")

    def test_neutron_slice_uses_fixed_identity_and_metadata_contract(self):
        document = COLLECTOR.collect_neutron_slice(
            [
                metadata_record(
                    1,
                    "2026-08-01T11:45:00Z",
                    "error",
                    "connection_error",
                    "token=secret 192.0.2.20",
                )
            ],
            False,
            "current",
            "controller-a",
            "controller",
            "30m",
            "medium",
            COLLECTION_START,
        )
        self.assertEqual(document["tool"], "recent_neutron_errors")
        self.assertEqual(document["status"], "ok")
        section = document["sections"][0]
        self.assertEqual(section["name"], "neutron_errors")
        self.assertEqual(section["status"], "ok")
        event = section["data"][0]
        self.assertEqual(event["source_class"], "neutron_error_events")
        self.assertEqual(event["service_class"], "neutron")
        self.assertNotIn("metadata_error_events", json.dumps(document))
        self.assertNotIn("metadata_service_errors", json.dumps(document))
        self.assertNotIn("secret", json.dumps(document))
        self.assertNotIn("192.0.2.20", json.dumps(document))

    def test_neutron_slice_preserves_unavailable_and_role_boundaries(self):
        missing = COLLECTOR.collect_neutron_slice(
            None,
            False,
            "current",
            "controller-a",
            "controller",
            "30m",
            "medium",
            COLLECTION_START,
        )
        self.assertEqual(missing["tool"], "recent_neutron_errors")
        self.assertEqual(missing["status"], "unavailable")
        self.assertEqual(missing["error"]["class"], "source_missing")
        self.assertEqual(missing["sections"], [])

        mismatch = COLLECTOR.collect_neutron_slice(
            [metadata_record(1, "2026-08-01T11:45:00Z")],
            False,
            "current",
            "compute-a",
            "compute",
            "30m",
            "medium",
            COLLECTION_START,
        )
        self.assertEqual(mismatch["tool"], "recent_neutron_errors")
        self.assertEqual(mismatch["error"]["class"], "source_role_mismatch")
        self.assertEqual(mismatch["sections"], [])

    def test_nova_constants_define_fixed_schema_identity(self):
        self.assertEqual(COLLECTOR.NOVA_TOOL_NAME, "recent_nova_errors")
        self.assertEqual(COLLECTOR.NOVA_SECTION_NAME, "nova_errors")
        self.assertEqual(COLLECTOR.NOVA_SOURCE_CLASS, "nova_error_events")
        self.assertEqual(COLLECTOR.NOVA_SERVICE_CLASS, "nova")
        self.assertEqual(COLLECTOR.NOVA_LOGICAL_SELECTOR, "nova_service_errors")
        self.assertEqual(COLLECTOR.NOVA_ROLE, "controller")

    def test_nova_slice_uses_fixed_identity_and_metadata_contract(self):
        document = COLLECTOR.collect_nova_slice(
            [metadata_record(1, "2026-08-01T11:45:00Z", "error", "timeout")],
            False,
            "current",
            "controller-a",
            "controller",
            "30m",
            "medium",
            COLLECTION_START,
        )
        self.assertEqual(document["schema_version"], "1.0")
        self.assertEqual(document["tool"], "recent_nova_errors")
        self.assertEqual(document["status"], "ok")
        section = document["sections"][0]
        self.assertEqual(section["name"], "nova_errors")
        self.assertEqual(section["status"], "ok")
        event = section["data"][0]
        self.assertEqual(event["source_class"], "nova_error_events")
        self.assertEqual(event["service_class"], "nova")
        self.assertEqual(event["inventory_role"], "controller")
        self.assertNotIn("metadata_error_events", json.dumps(document))
        self.assertNotIn("neutron_error_events", json.dumps(document))

    def test_nova_slice_returns_empty_and_unavailable_documents(self):
        empty = COLLECTOR.collect_nova_slice(
            [],
            False,
            "current",
            "controller-a",
            "controller",
            "30m",
            "medium",
            COLLECTION_START,
        )
        self.assertEqual(empty["tool"], "recent_nova_errors")
        self.assertEqual(empty["status"], "ok")
        self.assertEqual(empty["sections"][0]["name"], "nova_errors")
        self.assertEqual(empty["sections"][0]["status"], "empty")
        self.assertEqual(empty["sections"][0]["data"], [])

        missing = COLLECTOR.collect_nova_slice(
            None,
            False,
            "current",
            "controller-a",
            "controller",
            "30m",
            "medium",
            COLLECTION_START,
        )
        self.assertEqual(missing["tool"], "recent_nova_errors")
        self.assertEqual(missing["status"], "unavailable")
        self.assertEqual(missing["error"]["class"], "source_missing")
        self.assertEqual(missing["sections"], [])

    def test_nova_slice_rejects_non_controller_role(self):
        document = COLLECTOR.collect_nova_slice(
            [metadata_record(1, "2026-08-01T11:45:00Z")],
            False,
            "current",
            "compute-a",
            "compute",
            "30m",
            "medium",
            COLLECTION_START,
        )
        self.assertEqual(document["tool"], "recent_nova_errors")
        self.assertEqual(document["status"], "unavailable")
        self.assertEqual(document["error"]["class"], "source_role_mismatch")
        self.assertEqual(document["sections"], [])

    def test_nova_slice_reuses_redaction_and_record_truncation(self):
        records = [
            metadata_record(
                sequence,
                "2026-08-01T11:45:00Z",
                summary=(
                    "nova token=secret 192.0.2.44 "
                    if sequence == 0
                    else "nova compute failure"
                ),
            )
            for sequence in range(21)
        ]
        document = COLLECTOR.collect_nova_slice(
            records,
            False,
            "current",
            "controller-a",
            "controller",
            "30m",
            "medium",
            COLLECTION_START,
        )
        section = document["sections"][0]
        self.assertTrue(section["truncated"])
        self.assertEqual(len(section["data"]), 20)
        serialized = json.dumps(document)
        self.assertIn("[REDACTED]", serialized)
        self.assertNotIn("secret", serialized)
        self.assertNotIn("192.0.2.44", serialized)

    def test_policy_schema_rejects_unknown_and_tampered_reader_fields(self):
        unknown = json.loads(json.dumps(VALID_POLICY))
        unknown["unexpected"] = True
        with self.assertRaises(COLLECTOR.CollectorValidationError):
            COLLECTOR.validate_policy_metadata(unknown)

        tampered = json.loads(json.dumps(VALID_POLICY))
        tampered["entries"][0]["readers"][0]["argv"][0] = "/bin/sh"
        with self.assertRaises(COLLECTOR.CollectorValidationError):
            COLLECTOR.validate_policy_metadata(tampered)

        stale = json.loads(json.dumps(VALID_POLICY))
        stale["generated_at"] = "2000-01-01T00:00:00.000000Z"
        stale["expires_at"] = "2000-01-01T01:00:00.000000Z"
        with self.assertRaises(COLLECTOR.CollectorUnavailableError):
            COLLECTOR.validate_policy_metadata(stale)

    def test_fixed_reader_argv_adds_only_code_owned_bounds(self):
        reader = VALID_POLICY["entries"][0]["readers"][0]
        adapter_id, argv = COLLECTOR._build_reader_argv(
            reader,
            {"window_class": "30m", "line_limit_class": "medium"},
            COLLECTION_START,
        )
        self.assertEqual(adapter_id, "metadata_agent_errors")
        self.assertIn("--unit", argv)
        self.assertEqual(argv[argv.index("--lines") + 1], "101")
        self.assertNotIn("|", argv)
        self.assertNotIn(";", argv)

    def test_injected_journal_reader_normalizes_fixed_fields(self):
        reader = VALID_POLICY["entries"][0]["readers"][0]
        payload = {
            "_SYSTEMD_UNIT": "neutron-metadata-agent",
            "_SEQNUM": "4",
            "__REALTIME_TIMESTAMP": str(int(COLLECTION_START.timestamp() * 1_000_000)),
            "PRIORITY": "3",
            "MESSAGE": "metadata failure",
        }

        def fake_execute(argv, _timeout):
            return (
                subprocess.CompletedProcess(
                    argv, 0, json.dumps(payload).encode() + b"\n", b""
                ),
                False,
            )

        result = COLLECTOR.read_approved_source(
            reader,
            {"window_class": "30m", "line_limit_class": "medium"},
            COLLECTION_START,
            execute=fake_execute,
        )
        self.assertEqual(result.records[0]["source_sequence"], 4)
        self.assertEqual(result.records[0]["event_class"], "unknown")

    def test_injected_reader_failure_is_bounded_and_has_no_partial_document(self):
        snapshot = COLLECTOR.PolicySnapshot(
            VALID_POLICY, "fixture-digest", (1, 2, 3, 4, 5), COLLECTOR.POLICY_PATH
        )
        calls = 0

        def fake_execute(argv, _timeout):
            nonlocal calls
            calls += 1
            if calls == 1:
                unit = argv[argv.index("--unit") + 1]
                payload = {
                    "_SYSTEMD_UNIT": unit,
                    "_SEQNUM": "1",
                    "__REALTIME_TIMESTAMP": str(
                        int(datetime.now(timezone.utc).timestamp() * 1_000_000)
                    ),
                    "PRIORITY": "3",
                    "MESSAGE": "first reader",
                }
                return (
                    subprocess.CompletedProcess(
                        argv, 0, json.dumps(payload).encode() + b"\n", b""
                    ),
                    False,
                )
            return subprocess.CompletedProcess(argv, 1, b"", b"denied"), False

        with patch.object(
            COLLECTOR, "load_policy", return_value=snapshot
        ), patch.object(COLLECTOR, "verify_policy_snapshot"), patch.object(
            COLLECTOR, "execute_fixed_argv", side_effect=fake_execute
        ):
            exit_code, document = COLLECTOR.run(
                raw_request=json.dumps(VALID_REQUEST).encode()
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(document["status"], "denied")
        self.assertEqual(document["error"]["class"], "source_denied")
        self.assertEqual(document["sections"], [])

    def test_injected_timeout_does_not_fallback_to_another_reader(self):
        reader = VALID_POLICY["entries"][0]["readers"][0]

        def timeout(_argv, _timeout):
            raise COLLECTOR.SourceReaderError("timeout")

        with self.assertRaises(COLLECTOR.SourceReaderError) as context:
            COLLECTOR.read_approved_source(
                reader,
                {"window_class": "30m", "line_limit_class": "medium"},
                COLLECTION_START,
                execute=timeout,
            )
        self.assertEqual(context.exception.error_class, "timeout")

    def test_policy_loader_and_snapshot_verification_use_injected_bytes_only(self):
        payload = json.dumps(VALID_POLICY, separators=(",", ":")).encode()
        changed = json.dumps(
            {**VALID_POLICY, "revision": "changed"}, separators=(",", ":")
        ).encode()
        with patch.object(
            COLLECTOR,
            "_read_policy_bytes",
            side_effect=[(payload, (1, 2, 3, 4, 5)), (changed, (1, 2, 3, 4, 6))],
        ):
            snapshot = COLLECTOR.load_policy()
            self.assertEqual(snapshot.policy["revision"], "fixture-revision")
            with self.assertRaises(COLLECTOR.CollectorUnavailableError) as context:
                COLLECTOR.verify_policy_snapshot(snapshot)
        self.assertEqual(context.exception.error_class, "observer_integrity_error")


if __name__ == "__main__":
    unittest.main()
