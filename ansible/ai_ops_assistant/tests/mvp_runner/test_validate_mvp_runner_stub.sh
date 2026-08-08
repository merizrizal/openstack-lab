#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_validate_mvp_runner.yml"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

[[ -f "$playbook" && ! -L "$playbook" ]] || fail "validation playbook is missing or symlinked"

rtk grep -Fq 'hosts: ai_ops_assistant' "$playbook"
rtk grep -Fq '    ansible_pipelining: true' "$playbook"
rtk grep -Fq "inventory_hostname == 'assistant02'" "$playbook"
rtk grep -Fq "ansible_limit | default('') == 'assistant02'" "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_validation_enabled: false' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_validation_implementation_ready: false' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_secure_identifier_transport: unconfirmed' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_comparator_interface: unconfirmed' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_pre_attestation_interface: unconfirmed' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_post_attestation_interface: unconfirmed' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_external_evidence_location: unconfirmed' "$playbook"
rtk grep -Fq 'ansible.builtin.command:' "$playbook"
rtk grep -Fq 'project_resource_summary' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_project_summary_raw' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_project_summary_result' "$playbook"
rtk grep -Fq 'server_basic_info' "$playbook"
rtk grep -Fq 'server_network_info' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_server_identifier' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_audit_metadata_after_calls' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_post_attestation_valid' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_post_attestation_unchanged' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_prior_runtime_isolation_confirmed' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_bounded_audit_inspection_implemented' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_outcome_report' "$playbook"
rtk grep -Fq 'audit_inspector.py' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_audit_start_offset' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_audit_inspection_raw' "$playbook"
rtk grep -Fq 'Capture normalized bounded audit inspection failure class' "$playbook"
rtk grep -Fq 'Require bounded audit inspector output before parsing' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_audit_inspection_failure_class' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_audit_inspection_raw.stdout | trim | length > 0' "$playbook"
rtk grep -Fq 'ansible.builtin.stat:' "$playbook"
if rtk grep -nE 'ansible\.builtin\.slurp:|ai_ops_assistant_mvp_audit_raw|b64decode|ai_ops_assistant_mvp_audit_events' "$playbook"; then
  fail "unbounded audit-file inspection found"
fi
rtk grep -Fq 'ai_ops_assistant_mvp_runner_metadata' "$playbook"
rtk grep -Fq 'ai_ops_assistant_mvp_sensitive_metadata' "$playbook"
rtk grep -Fq 'item.stat.isreg' "$playbook"
rtk grep -Fq 'item.stat.islnk' "$playbook"
rtk grep -Fq 'no_log: true' "$playbook"
rtk grep -Fq '/opt/openstack-ai-ops-assistant/scripts/tool_runner/aiops_tool_runner.py' "$playbook"
rtk grep -Fq '/opt/openstack-ai-ops-assistant/scripts/tool_runner/tool_registry.json' "$playbook"
rtk grep -Fq '/opt/openstack-ai-ops-assistant/audit/tool-runner.jsonl' "$playbook"
rtk grep -Fq 'server_basic_info' "$playbook"
rtk grep -Fq 'server_network_info' "$playbook"
rtk grep -Fq 'MVP runner validation is fail-closed' "$playbook"
rtk grep -Fq 'Require bounded audit inspection gate after runner calls' "$playbook"
rtk grep -Fq 'administrator post-state attestation' "$playbook"
rtk grep -Fq 'result_process_agreement' "$playbook"
rtk grep -Fq 'audit_pair_validated' "$playbook"
rtk grep -Fq 'path_isolation_confirmed' "$playbook"
rtk grep -Fq 'unchanged_state_confirmed' "$playbook"

for status in ok error denied validation_error timeout unavailable; do
  rtk grep -Fq "  $status:" "$playbook" || fail "missing exit mapping for $status"
done
for fixture in success unavailable child_failure validation_failure audit_failure; do
  rtk grep -Fq "name: $fixture" "$playbook" || fail "missing exit semantic fixture $fixture"
done
rtk grep -Fq "ai_ops_assistant_mvp_project_summary_raw.rc ==" "$playbook"
rtk grep -Fq "item.raw.rc == ai_ops_assistant_mvp_exit_codes[item.result.status]" "$playbook"

if rtk grep -nE 'ansible\.builtin\.(shell|raw)|(^|[[:space:]/])openstack([[:space:]]|$)|vars_prompt|(^|[^[:alnum:]_])audit_path[[:space:]]*:|profile_override' "$playbook"; then
  fail "prohibited execution, identifier transport, or secret-path override found"
fi
if rtk grep -nE '^    - name: Debug$|ansible\.builtin\.debug:' "$playbook"; then
  fail "temporary debug task found in validation playbook"
fi

printf 'MVP runner validation stub test passed\n'
