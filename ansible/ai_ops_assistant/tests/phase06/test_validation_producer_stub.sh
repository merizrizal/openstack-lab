#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_produce_restricted_diagnostics_validation.yml"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

[[ -f "$playbook" && ! -L "$playbook" ]] || fail "validation producer playbook is missing or symlinked"
for required in \
  'ai_ops_assistant_phase06_validation_enabled: false' \
  'ai_ops_assistant_phase06_validation_tool_outcomes: []' \
  'ai_ops_assistant_phase06_validation_negative_controls: []' \
  'ai_ops_assistant_phase06_validation_scope_outcomes: []' \
  'ai_ops_assistant_phase06_validation_audit_pairs: []' \
  'operation: seven_tool_acceptance_orchestration' \
  'seven-tool outcome collection' \
  'negative-control collection' \
  'ordered scope outcomes' \
  'Derive final acceptance from the closed outcome set' \
  'final_acceptance: false' \
  'no_log: true'; do
  grep -Fq "$required" "$playbook" || fail "missing producer contract: $required"
done

grep -Fq "| length == 7" "$playbook"
grep -Fq "| length == 18" "$playbook"
grep -Fq "| length == 11" "$playbook"
grep -Fq "'neutron_agent_health', 'project_resource_summary', 'recent_metadata_errors', 'recent_neutron_errors', 'recent_nova_errors', 'server_basic_info', 'server_network_info'" "$playbook"
grep -Fq "'agent_forwarding', 'alternate_sudo_arguments', 'arbitrary_command" "$playbook"
grep -Fq "'prerequisite_readiness', 'operator_reader_deployment', 'observer_deployment', 'host_source_contact'" "$playbook"
grep -Fq "post_attestation.unchanged" "$playbook"
grep -Fq "audit_pairs_acceptable" "$playbook"
grep -Fq "representative_workflow_pending" "$playbook"

if grep -nE 'ansible\.builtin\.(shell|command|raw|debug)|stdout|stderr|private\.key|password|token|credential|address|raw.log' "$playbook"; then
  fail "producer contains execution, raw disclosure, or protected-value handling"
fi

if grep -nE "phase05_acceptance_confirmed: true|final_acceptance: true|status: accepted|neutron_read_classified" "$playbook"; then
  fail "producer contains success-shaped defaults or obsolete Neutron-only fields"
fi

printf 'Phase 06 seven-tool validation producer static test passed\n'
