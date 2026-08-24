#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_validate_mvp_runner.yml"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

[[ -f "$playbook" && ! -L "$playbook" ]] || fail "validation playbook is missing or symlinked"

grep -Fq 'hosts: ai_ops_assistant' "$playbook"
grep -Fq '    ansible_pipelining: true' "$playbook"
grep -Fq "inventory_hostname == 'assistant02'" "$playbook"
grep -Fq "ansible_limit | default('') == 'assistant02'" "$playbook"
grep -Fq 'ai_ops_assistant_mvp_validation_enabled: false' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_validation_implementation_ready: false' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_secure_identifier_transport: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_comparator_interface: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_pre_attestation_interface: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_post_attestation_interface: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_external_evidence_location: unconfirmed' "$playbook"
grep -Fq 'ansible.builtin.command:' "$playbook"
grep -Fq 'project_resource_summary' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_project_summary_raw' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_project_summary_result' "$playbook"
grep -Fq 'server_basic_info' "$playbook"
grep -Fq 'server_network_info' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_server_identifier' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_audit_metadata_after_calls' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_post_attestation_valid' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_post_attestation_unchanged' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_prior_runtime_isolation_confirmed' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_bounded_audit_inspection_implemented' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_outcome_report' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_producer_result' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_validation_output_directory: /run/openstack-ai-ops/phase05-validation' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_validation_output_path' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_source_revision: unconfirmed' "$playbook"
grep -Fq 'producer: mvp_acceptance_validation' "$playbook"
grep -Fq 'operation: mvp_three_tool_acceptance' "$playbook"
grep -Fq 'status: blocked' "$playbook"
grep -Fq 'to_nice_json' "$playbook"
grep -Fq 'ansible.builtin.copy:' "$playbook"
grep -Fq 'force: false' "$playbook"
grep -Fq 'mode: "0700"' "$playbook"
grep -Fq 'mode: "0600"' "$playbook"
grep -Fq 'audit_inspector.py' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_audit_start_offset' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_audit_inspection_raw' "$playbook"
grep -Fq 'Capture normalized bounded audit inspection failure class' "$playbook"
grep -Fq 'Require bounded audit inspector output before parsing' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_audit_inspection_failure_class' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_audit_inspection_raw.stdout | trim | length > 0' "$playbook"
grep -Fq 'ansible.builtin.stat:' "$playbook"
if grep -nE 'ansible\.builtin\.slurp:|ai_ops_assistant_mvp_audit_raw|b64decode|ai_ops_assistant_mvp_audit_events' "$playbook"; then
  fail "unbounded audit-file inspection found"
fi
grep -Fq 'ai_ops_assistant_mvp_runner_metadata' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_sensitive_metadata' "$playbook"
grep -Fq 'item.stat.isreg' "$playbook"
grep -Fq 'item.stat.islnk' "$playbook"
grep -Fq 'no_log: true' "$playbook"
grep -Fq '/opt/openstack-ai-ops-assistant/scripts/tool_runner/aiops_tool_runner.py' "$playbook"
grep -Fq '/opt/openstack-ai-ops-assistant/scripts/tool_runner/tool_registry.json' "$playbook"
grep -Fq '/opt/openstack-ai-ops-assistant/audit/tool-runner.jsonl' "$playbook"
grep -Fq 'server_basic_info' "$playbook"
grep -Fq 'server_network_info' "$playbook"
grep -Fq 'MVP runner validation is fail-closed' "$playbook"
grep -Fq 'Require bounded audit inspection gate after runner calls' "$playbook"
grep -Fq 'administrator post-state attestation' "$playbook"
grep -Fq 'result_process_agreement' "$playbook"
grep -Fq 'audit_pair_validated' "$playbook"
grep -Fq 'path_isolation_confirmed' "$playbook"
grep -Fq 'unchanged_state_confirmed' "$playbook"

for status in ok error denied validation_error timeout unavailable; do
  grep -Fq "  $status:" "$playbook" || fail "missing exit mapping for $status"
done
for fixture in success unavailable child_failure validation_failure audit_failure; do
  grep -Fq "name: $fixture" "$playbook" || fail "missing exit semantic fixture $fixture"
done
grep -Fq "ai_ops_assistant_mvp_project_summary_raw.rc ==" "$playbook"
grep -Fq "item.raw.rc == ai_ops_assistant_mvp_exit_codes[item.result.status]" "$playbook"

if grep -nE 'ansible\.builtin\.(shell|raw)|(^|[[:space:]/])openstack([[:space:]]|$)|vars_prompt|(^|[^[:alnum:]_])audit_path[[:space:]]*:|profile_override' "$playbook"; then
  fail "prohibited execution, identifier transport, or secret-path override found"
fi
if grep -nE '^    - name: Debug$|ansible\.builtin\.debug:' "$playbook"; then
  fail "temporary debug task found in validation playbook"
fi

printf 'MVP runner validation stub test passed\n'
