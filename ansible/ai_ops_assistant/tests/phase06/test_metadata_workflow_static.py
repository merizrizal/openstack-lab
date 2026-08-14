import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
RUNBOOK_PATH = REPOSITORY_ROOT / "docs/ai-ops-revised/runtime/manual-aiops-workflows.md"
EXPECTED_SEQUENCE = [
    "project_resource_summary",
    "server_basic_info",
    "server_network_info",
    "neutron_agent_health",
    "recent_metadata_errors",
    "recent_neutron_errors",
    "recent_nova_errors",
]
OPTIONAL_TOOLS = {
    "neutron_agent_health",
    "recent_metadata_errors",
    "recent_neutron_errors",
    "recent_nova_errors",
}


SYNTHETIC_RESULTS = [
    {"tool": "project_resource_summary", "status": "ok"},
    {"tool": "server_basic_info", "status": "ok", "server_identifier": "demo-node"},
    {"tool": "server_network_info", "status": "ok", "server_identifier": "demo-node"},
    {
        "tool": "neutron_agent_health",
        "status": "ok",
        "agents": [{"host_label": "ctrl-demo", "alive": False}],
    },
    {
        "tool": "recent_metadata_errors",
        "status": "ok",
        "events": [
            {
                "host_label": "ctrl-demo",
                "source_class": "metadata_error_events",
                "redacted_summary": "metadata request failed",
            }
        ],
    },
    {
        "tool": "recent_neutron_errors",
        "status": "unavailable",
        "error": {"class": "approved_optional_capability_absent"},
    },
    {
        "tool": "recent_nova_errors",
        "status": "unavailable",
        "error": {"class": "approved_optional_capability_absent"},
    },
]


def interpret_workflow(results):
    by_tool = {result["tool"]: result for result in results}
    gaps = [
        tool
        for tool in EXPECTED_SEQUENCE
        if by_tool.get(tool, {}).get("status") != "ok"
    ]
    inferences = []
    if by_tool.get("neutron_agent_health", {}).get("agents"):
        if any(
            not agent["alive"] for agent in by_tool["neutron_agent_health"]["agents"]
        ):
            inferences.append("neutron-agent/proxy issue is a hypothesis")
    if by_tool.get("recent_metadata_errors", {}).get("events"):
        inferences.append("metadata-service evidence is present")
    return {"gaps": gaps, "inferences": inferences}


def refusal_for(request):
    remediation_terms = ("restart", "ssh", "sudo", "edit", "raw log")
    if any(term in request.lower() for term in remediation_terms):
        return (
            "refuse: diagnostic-only workflow; manual operator follow-up is unexecuted"
        )
    return "interpret accepted evidence only"


class MetadataWorkflowStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

    def test_runbook_declares_closed_seven_tool_sequence(self):
        positions = [self.runbook.index(f"`{tool}`") for tool in EXPECTED_SEQUENCE]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("static and synthetic workflow contract only", self.runbook)
        self.assertIn("host_label", self.runbook)
        self.assertIn("window_class", self.runbook)
        self.assertIn("line_limit_class", self.runbook)

    def test_synthetic_workflow_separates_hypotheses_from_gaps(self):
        interpretation = interpret_workflow(SYNTHETIC_RESULTS)
        self.assertEqual(
            interpretation["gaps"],
            ["recent_neutron_errors", "recent_nova_errors"],
        )
        self.assertIn(
            "neutron-agent/proxy issue is a hypothesis", interpretation["inferences"]
        )
        self.assertIn(
            "metadata-service evidence is present", interpretation["inferences"]
        )

    def test_optional_tools_are_never_reinterpreted_as_success(self):
        for tool in OPTIONAL_TOOLS:
            result = {"tool": tool, "status": "unavailable"}
            interpretation = interpret_workflow(
                [
                    {"tool": name, "status": "ok"}
                    for name in EXPECTED_SEQUENCE
                    if name != tool
                ]
                + [result]
            )
            self.assertIn(tool, interpretation["gaps"])

    def test_remediation_requests_are_refused_without_commands(self):
        response = refusal_for("SSH into the host and restart the metadata service")
        self.assertIn("refuse", response)
        self.assertIn("unexecuted", response)
        self.assertNotIn("ssh ", response.lower())
        self.assertNotIn("sudo ", response.lower())


if __name__ == "__main__":
    unittest.main()
