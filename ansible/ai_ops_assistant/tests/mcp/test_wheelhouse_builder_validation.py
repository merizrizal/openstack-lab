import importlib.util
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).parents[2]
    / "roles/mcp_wheelhouse_builder/files/validate_wheelhouse_inputs.py"
)
SPEC = importlib.util.spec_from_loader(
    "validate_wheelhouse_inputs",
    SourceFileLoader("validate_wheelhouse_inputs", str(SCRIPT_PATH)),
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)


class WheelhouseBuilderValidationTest(unittest.TestCase):
    def test_attestation_capture_time_requires_past_utc_iso8601(self):
        VALIDATOR.require_utc_timestamp("2000-01-01T00:00:00Z", "capture time")

        for value in ("not-a-timestamp", "2999-01-01T00:00:00Z", 1):
            with (
                self.subTest(value=value),
                self.assertRaises(VALIDATOR.ValidationError),
            ):
                VALIDATOR.require_utc_timestamp(value, "capture time")

    def test_attestation_fingerprint_requires_sha256_digest(self):
        VALIDATOR.require_sha256_digest("a" * 64, "environment fingerprint")

        for value in ("a" * 63, "A" * 64, 1):
            with (
                self.subTest(value=value),
                self.assertRaises(VALIDATOR.ValidationError),
            ):
                VALIDATOR.require_sha256_digest(value, "environment fingerprint")


if __name__ == "__main__":
    unittest.main()
