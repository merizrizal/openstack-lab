import dataclasses
import importlib.util
import json
import sys
import unittest
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REDACTION_PATH = (
    REPO_ROOT
    / "ansible/ai_ops_runtime/roles/ai_client_runtime/files/provider_gateway/redaction.py"
)


def load_redaction_module():
    spec = importlib.util.spec_from_file_location("provider_redaction", REDACTION_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestProviderRedaction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.redaction = load_redaction_module()

    def test_redacts_nested_identity_aliases_and_preserves_input(self):
        original = {
            "input": [
                {
                    "context": {
                        "user_name": "SYNTHETIC_USERNAME",
                        "group-name": "SYNTHETIC_GROUP",
                    }
                }
            ],
            "note": "SYNTHETIC_USERNAME SYNTHETIC_GROUP",
        }

        result = self.redaction.redact_remote_payload(original)

        self.assertEqual(
            result.payload["input"][0]["context"],
            {"user_name": "[REDACTED]", "group-name": "[REDACTED]"},
        )
        self.assertEqual(result.payload["note"], "[REDACTED] [REDACTED]")
        self.assertEqual(result.redaction_counts["identity"], 2)
        self.assertEqual(
            original["input"][0]["context"]["user_name"], "SYNTHETIC_USERNAME"
        )

    def test_redacts_arrays_and_exact_values_seen_later_in_the_payload(self):
        payload = {
            "note": "owner=SYNTHETIC_USER team=SYNTHETIC_GROUP",
            "input": [
                {"username": "SYNTHETIC_USER"},
                {"nested": [{"group": "SYNTHETIC_GROUP"}]},
            ],
        }

        result = self.redaction.redact_remote_payload(payload)

        self.assertEqual(result.payload["note"], "owner=[REDACTED] team=[REDACTED]")
        self.assertEqual(result.payload["input"][0]["username"], "[REDACTED]")
        self.assertEqual(result.payload["input"][1]["nested"][0]["group"], "[REDACTED]")
        self.assertEqual(result.redaction_counts["propagated_value"], 2)

    def test_redacts_null_numeric_boolean_and_collection_sensitive_values(self):
        payload = {
            "username": None,
            "group": 7,
            "user_name": True,
            "group-name": ["member"],
        }

        result = self.redaction.redact_remote_payload(payload)

        self.assertEqual(
            result.payload,
            {
                "username": "[REDACTED]",
                "group": "[REDACTED]",
                "user_name": "[REDACTED]",
                "group-name": "[REDACTED]",
            },
        )
        self.assertEqual(result.redaction_counts["identity"], 4)

    def test_redacts_secret_like_fields_and_propagates_values(self):
        payload = {
            "nested": {
                "password": "SYNTHETIC_PASSWORD",
                "api_key": "SYNTHETIC_API_KEY",
                "private-key": "SYNTHETIC_PRIVATE_KEY",
                "credential": "SYNTHETIC_CREDENTIAL",
            },
            "note": "SYNTHETIC_PASSWORD SYNTHETIC_API_KEY SYNTHETIC_PRIVATE_KEY SYNTHETIC_CREDENTIAL",
        }

        result = self.redaction.redact_remote_payload(payload)

        self.assertEqual(
            result.payload["nested"],
            {
                "password": "[REDACTED]",
                "api_key": "[REDACTED]",
                "private-key": "[REDACTED]",
                "credential": "[REDACTED]",
            },
        )
        self.assertEqual(
            result.payload["note"], "[REDACTED] [REDACTED] [REDACTED] [REDACTED]"
        )
        self.assertEqual(result.redaction_counts["secret"], 4)

    def test_redacts_canonical_labeled_text(self):
        result = self.redaction.redact_remote_payload(
            {
                "input": "username=SYNTHETIC_USER group: SYNTHETIC_GROUP token=SYNTHETIC_TOKEN"
            }
        )

        self.assertEqual(
            result.payload["input"],
            "username=[REDACTED] group: [REDACTED] token=[REDACTED]",
        )
        self.assertEqual(result.redaction_counts["canonical_text"], 3)

    def test_redacts_embedded_json_text(self):
        result = self.redaction.redact_remote_payload(
            {"input": '{"username":"SYNTHETIC_USER","safe":"SYNTHETIC_SAFE"}'}
        )

        self.assertEqual(
            json.loads(result.payload["input"]),
            {"safe": "SYNTHETIC_SAFE", "username": "[REDACTED]"},
        )
        self.assertEqual(result.redaction_counts["embedded_json"], 1)

    def test_rejects_duplicate_and_malformed_json(self):
        with self.assertRaises(self.redaction.DuplicateKeyError):
            self.redaction.strict_json_loads('{"username":"first","username":"second"}')
        with self.assertRaises(self.redaction.MalformedJsonError):
            self.redaction.strict_json_loads('{"username":')

    def test_rejects_ambiguous_sensitive_text_with_safe_metadata(self):
        cases = (
            ("the username is SYNTHETIC_USER", "plain_text_label", "identity"),
            ("token SYNTHETIC_TOKEN", "plain_text_label", "secret"),
            ('{"token":', "json_like_text", "secret"),
        )
        for text, reason, label_category in cases:
            with self.subTest(text=text):
                with self.assertRaises(
                    self.redaction.AmbiguousSensitiveLabelError
                ) as raised:
                    self.redaction.redact_remote_payload({"input": text})

                error = raised.exception
                self.assertEqual(error.reason, reason)
                self.assertEqual(error.label_category, label_category)
                self.assertEqual(error.args, ("ambiguous sensitive label",))
                self.assertNotIn("SYNTHETIC", repr(error.__dict__))

    def test_rejects_unsupported_provider_content(self):
        with self.assertRaises(self.redaction.UnsupportedContentError):
            self.redaction.redact_remote_payload(
                {"input": [{"type": "input_image", "image_url": "synthetic"}]}
            )
        with self.assertRaises(self.redaction.UnsupportedContentError):
            self.redaction.redact_remote_payload({"input": b"synthetic"})

    def test_leak_scan_rejects_reintroduced_protected_value(self):
        original = {"username": "SYNTHETIC_USERNAME", "note": "SYNTHETIC_USERNAME"}
        result = self.redaction.redact_remote_payload(original)

        scan = self.redaction.scan_redacted_payload(original, result)
        self.assertEqual(scan.correlation_id, result.correlation_id)
        leaked = dataclasses.replace(result, payload={"note": "SYNTHETIC_USERNAME"})
        with self.assertRaises(self.redaction.RedactionError):
            self.redaction.scan_redacted_payload(original, leaked)

    def test_preserves_non_sensitive_marker(self):
        result = self.redaction.redact_remote_payload(
            {"input": "SYNTHETIC_SAFE_MARKER"}
        )

        self.assertEqual(result.payload["input"], "SYNTHETIC_SAFE_MARKER")
        self.assertEqual(result.classification_status, "clear")
        self.assertEqual(result.redaction_counts, {})

    def test_result_metadata_contains_no_original_sensitive_values(self):
        username = "SYNTHETIC_USERNAME"
        secret = "SYNTHETIC_SECRET"
        result = self.redaction.redact_remote_payload(
            {"username": username, "token": secret, "note": f"{username}:{secret}"}
        )

        retained = json.dumps(dataclasses.asdict(result), sort_keys=True)
        self.assertNotIn(username, retained)
        self.assertNotIn(secret, retained)
        self.assertEqual(result.schema_version, 1)
        self.assertEqual(uuid.UUID(result.correlation_id).version, 4)


if __name__ == "__main__":
    unittest.main()
