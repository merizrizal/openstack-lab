import importlib.util
import io
import json
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


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
    "source_class": "metadata",
    "window_class": "default",
    "line_limit_class": "default",
}
VALID_PROJECTION = {
    "schema_version": "1.0",
    "revision": "fixture-revision",
    "freshness_class": "current",
    "entries": [
        {
            "host_label": "controller-a",
            "inventory_role": "controller",
            "source_classes": ["metadata", "neutron", "nova"],
            "enabled": True,
        }
    ],
}
VALID_POLICY = {
    "schema_version": "1.0",
    "source_classes": ["metadata", "neutron", "nova"],
    "window_classes": ["default"],
    "line_limit_classes": ["default"],
    "metadata_status": "accepted",
    "redaction_policy_status": "accepted",
}


class HostObserverCollectorTest(unittest.TestCase):
    def test_valid_request_is_explicitly_unavailable_without_source_access(self):
        exit_code, document = COLLECTOR.run(raw_request=json.dumps(VALID_REQUEST).encode())
        self.assertEqual(exit_code, 5)
        self.assertEqual(document["status"], "unavailable")
        self.assertEqual(document["error"]["class"], "authorization_pending")
        self.assertEqual(document["sections"], [])

    def test_invocation_arguments_and_original_command_are_rejected(self):
        for argv, environment in ((["unexpected"], {}), ([], {"SSH_ORIGINAL_COMMAND": "x"})):
            with self.subTest(argv=argv, environment=environment):
                exit_code, document = COLLECTOR.run(argv, environment, b"")
                self.assertEqual(exit_code, 2)
                self.assertEqual(document["error"]["class"], "invocation_denied")

    def test_request_rejects_duplicate_unknown_oversized_and_unsafe_values(self):
        cases = (
            b'{"schema_version":"1.0","schema_version":"1.0","host_label":"controller-a","source_class":"metadata","window_class":"default","line_limit_class":"default"}',
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
        self.assertEqual(COLLECTOR.validate_boundary(request, VALID_PROJECTION, VALID_POLICY)["host_label"], "controller-a")

        stale = {**VALID_PROJECTION, "freshness_class": "stale"}
        with self.assertRaises(COLLECTOR.CollectorUnavailableError):
            COLLECTOR.validate_projection_metadata(stale)

        duplicate = {
            **VALID_PROJECTION,
            "entries": VALID_PROJECTION["entries"] * 2,
        }
        with self.assertRaises(COLLECTOR.CollectorValidationError):
            COLLECTOR.validate_projection_metadata(duplicate)

        unsafe = {**VALID_PROJECTION, "entries": [{**VALID_PROJECTION["entries"][0], "address": "forbidden"}]}
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


if __name__ == "__main__":
    unittest.main()
