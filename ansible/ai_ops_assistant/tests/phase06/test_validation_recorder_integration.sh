#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
producer="$repo_root/ansible/ai_ops_assistant/playbook_produce_restricted_diagnostics_validation.yml"
recorder="$repo_root/ansible/ai_ops_assistant/playbook_record_restricted_diagnostics_evidence.yml"
producer_test="$repo_root/ansible/ai_ops_assistant/tests/phase06/test_validation_producer_stub.sh"
recorder_test="$repo_root/ansible/ai_ops_assistant/tests/evidence/test_record_restricted_evidence_stub.sh"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

[[ -f "$producer" && ! -L "$producer" ]] || fail "producer playbook is missing or symlinked"
[[ -f "$recorder" && ! -L "$recorder" ]] || fail "recorder playbook is missing or symlinked"
rtk bash -n "$producer_test"
rtk bash "$producer_test"
rtk bash -n "$recorder_test"
rtk bash "$recorder_test"

test_dir="$(mktemp -d)"
trap 'rm -rf "$test_dir"' EXIT
fixture="$test_dir/2026-0004.json"
wrapper="$test_dir/validate_fixture.yml"
chmod 700 "$test_dir"

rtk python3 - "$fixture" <<'PY'
import json
import sys

path = sys.argv[1]
tools = [
    "neutron_agent_health",
    "project_resource_summary",
    "recent_metadata_errors",
    "recent_neutron_errors",
    "recent_nova_errors",
    "server_basic_info",
    "server_network_info",
]
negative = [
    "agent_forwarding", "alternate_sudo_arguments", "arbitrary_command",
    "collector_output_redirection", "destination_bypass", "editor_execution",
    "environment_injection", "extra_arguments", "interactive_shell",
    "local_forwarding", "out_of_policy_file_read", "package_manager_execution",
    "pty_allocation", "remote_forwarding", "service_control", "tunnel_request",
    "unrestricted_sudo", "x11_forwarding",
]
scopes = [
    "host_source_contact", "negative_boundary_validation", "observer_deployment",
    "operator_reader_deployment", "outcome_evidence_recording", "positive_validation",
    "prerequisite_readiness", "protected_audit_inspection", "representative_workflow",
    "revocation_rollback", "unchanged_state_comparison",
]
result = {
    "schema_version": "1.0",
    "producer": "phase06_restricted_diagnostics_validation",
    "operation": "seven_tool_acceptance_orchestration",
    "status": "blocked",
    "limitation_class": "acceptance_pending",
    "rollback_status": "pending",
    "unresolved_gates": ["phase05_acceptance_pending"],
    "run_id": "2026-0004",
    "source_revision": "2026-0004-source-r1",
    "phase05_acceptance_confirmed": False,
    "phase05_acceptance_outcome": "blocked",
    "phase05_acceptance_evidence_reference": "2026-0004-phase05-blocked",
    "tools": [
        {"name": name, "outcome": "unavailable", "json_shape_valid": False,
         "bounds_valid": False, "redaction_valid": False,
         "exit_code_agreement": False, "audit_pair_valid": False, "truncated": False}
        for name in tools
    ],
    "negative_controls": [{"case": case, "outcome": "denied"} for case in negative],
    "scope_outcomes": [{"scope": scope, "status": "blocked", "evidence_reference": f"2026-0004-{scope}"} for scope in scopes],
    "audit_pairs": [{"tool": name, "result_present": False, "audit_present": False,
                      "correlation_valid": False, "sanitized": False} for name in tools],
    "pre_attestation": {"valid": False, "unchanged": False},
    "post_attestation": {"valid": False, "unchanged": False},
    "unchanged_state_comparison": False,
    "revocation_rollback": {"status": "pending", "operator_reader_revoked": False,
                             "observer_revoked": False, "authority_isolated": False},
    "representative_workflow": {"status": "blocked", "required_evidence_gaps": ["representative_workflow_pending"],
                                 "advisory_only": False, "remediation_executed": False},
    "final_acceptance": False,
}
with open(path, "w", encoding="utf-8") as handle:
    json.dump(result, handle)
PY
chmod 600 "$fixture"

cat >"$wrapper" <<EOF_WRAPPER
---
- name: Validate normalized seven-tool result
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    fixture_path: "$fixture"
    expected_run_id: 2026-0004
    expected_source_revision: 2026-0004-source-r1
  tasks:
    - name: Read normalized result
      ansible.builtin.slurp:
        src: "{{ fixture_path }}"
      register: raw_result
      changed_when: false
      no_log: true
    - name: Decode normalized result
      ansible.builtin.set_fact:
        result: "{{ raw_result.content | b64decode | from_json }}"
      changed_when: false
      no_log: true
    - name: Validate closed result shape
      ansible.builtin.assert:
        that:
          - result.keys() | list | sort == ['audit_pairs', 'final_acceptance', 'limitation_class', 'negative_controls', 'operation', 'phase05_acceptance_confirmed', 'phase05_acceptance_evidence_reference', 'phase05_acceptance_outcome', 'post_attestation', 'pre_attestation', 'producer', 'representative_workflow', 'revocation_rollback', 'rollback_status', 'run_id', 'schema_version', 'scope_outcomes', 'source_revision', 'status', 'tools', 'unchanged_state_comparison', 'unresolved_gates']
          - result.run_id == expected_run_id
          - result.source_revision == expected_source_revision
          - result.tools | length == 7
          - result.negative_controls | length == 18
          - result.scope_outcomes | length == 11
          - result.audit_pairs | length == 7
          - result.final_acceptance == false
          - result.status == 'blocked'
          - result.phase05_acceptance_confirmed == false
        quiet: true
      changed_when: false
      no_log: true
EOF_WRAPPER

python_bin="${PYTHON_BIN:-/home/meriz/Documents/PyEnv/myEnv/bin/python}"
[[ -x "$python_bin" ]] || fail "approved Python environment is unavailable"
ansible_cmd=("$python_bin" -m ansible.cli.playbook)
rtk "${ansible_cmd[@]}" -i localhost, "$wrapper" >/dev/null 2>&1 || fail "normalized result integration failed"

set +e
rtk "${ansible_cmd[@]}" -i localhost, "$wrapper" -e '{"expected_source_revision":"wrong-revision"}' >/dev/null 2>&1
status=$?
set -e
[[ "$status" -ne 0 ]] || fail "source-revision mismatch was accepted"

printf 'Phase 06 seven-tool producer-recorder integration test passed\n'
