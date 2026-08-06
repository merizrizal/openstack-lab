import importlib.util
from importlib.machinery import SourceFileLoader
import json
import stat
import tempfile
import unittest
from pathlib import Path


CONSUMER_PATH = Path(__file__).parents[2] / "roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved/secure_diagnostic_acceptance_consumer"
SPEC = importlib.util.spec_from_loader(
    "secure_diagnostic_acceptance_consumer",
    SourceFileLoader("secure_diagnostic_acceptance_consumer", str(CONSUMER_PATH)),
)
CONSUMER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONSUMER)


class FakeReader:
    def __init__(self, server):
        self.server = server
        self.identifiers = []

    def find_server(self, identifier):
        self.identifiers.append(identifier)
        return self.server

    def list_ports(self, server_id):
        return [{"network_id": "network-1", "fixed_ips": [{"subnet_id": "subnet-1"}]}]

    def get_network(self, network_id):
        return {"id": network_id, "name": "network"}

    def get_subnet(self, subnet_id):
        return {"id": subnet_id, "cidr": "192.0.2.0/24"}


class SecureDiagnosticAcceptanceConsumerTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.record_directory = Path(self.temporary.name) / "records"
        self.record_directory.mkdir(mode=0o700)
        self.record_directory.chmod(0o700)

    def tearDown(self):
        self.temporary.cleanup()

    def test_writes_outcome_only_record(self):
        reader = FakeReader({"id": "server-1", "name": "server-1", "status": "ACTIVE"})

        record_path = CONSUMER.run_acceptance(
            "20026-0001",
            reader,
            lambda: "server-1",
            self.record_directory,
        )

        serialized = record_path.read_text()
        record = json.loads(serialized)
        self.assertEqual(reader.identifiers, ["server-1"])
        self.assertEqual(stat.S_IMODE(record_path.stat().st_mode), 0o600)
        self.assertEqual(record["run_id"], "20026-0001")
        self.assertEqual([tool["name"] for tool in record["tools"]], ["server_basic_info", "server_network_info"])
        self.assertNotIn("server-1", serialized)
        self.assertNotIn("192.0.2.0", serialized)

    def test_rejects_secret_like_response_without_retaining_it(self):
        reader = FakeReader({"id": "server-1", "token": "fixture-token"})

        with self.assertRaises(CONSUMER.ConsumerError):
            CONSUMER.run_acceptance(
                "20026-0002",
                reader,
                lambda: "server-1",
                self.record_directory,
            )

        self.assertEqual(list(self.record_directory.iterdir()), [])

    def test_rejects_invalid_identifier_without_sdk_read_or_record(self):
        reader = FakeReader({"id": "server-1"})

        with self.assertRaises(CONSUMER.ConsumerError):
            CONSUMER.run_acceptance(
                "20026-0003",
                reader,
                lambda: "../server",
                self.record_directory,
            )

        self.assertEqual(reader.identifiers, [])
        self.assertEqual(list(self.record_directory.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
