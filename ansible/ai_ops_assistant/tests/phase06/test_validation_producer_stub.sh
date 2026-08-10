#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_produce_phase06_restricted_diagnostics_validation.yml"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

[[ -f "$playbook" && ! -L "$playbook" ]] || fail "validation producer playbook is missing or symlinked"

grep -Fq 'hosts: ai_ops_assistant' "$playbook"
grep -Fq "inventory_hostname == 'assistant02'" "$playbook"
grep -Fq "ansible_limit | default('') == 'assistant02'" "$playbook"
grep -Fq 'ai_ops_assistant_phase06_validation_enabled: false' "$playbook"
grep -Fq 'ai_ops_assistant_phase06_validation_phase05_acceptance_gate: unconfirmed' "$playbook"
grep -Fq "ai_ops_assistant_phase06_validation_scope: project-reader-neutron-read-only" "$playbook"
grep -Fq "ai_ops_assistant_phase06_validation_profile_name: aiops-assistant-project-reader" "$playbook"
grep -Fq 'ai_ops_assistant_phase06_validation_public_parameters: []' "$playbook"
grep -Fq 'ai_ops_assistant_phase06_validation_operation_label: neutron_agent_list_project_reader' "$playbook"
grep -Fq 'schema_version: "1.0"' "$playbook"
grep -Fq 'status: blocked' "$playbook"
grep -Fq 'limitation_class: authorization_pending' "$playbook"
grep -Fq 'validation_producer_not_implemented' "$playbook"
grep -Fq 'no_log: true' "$playbook"
grep -Fq 'ansible.builtin.command:' "$playbook"
grep -Fq "'/usr/bin/env', '-i', 'HOME=/home/aiops_assistant'" "$playbook"
grep -Fq "'OS_CLIENT_CONFIG_FILE=/opt/openstack-ai-ops-assistant/credentials/profiles/clouds.yaml'" "$playbook"
grep -Fq "'OS_CLOUD=aiops-assistant-project-reader'" "$playbook"
grep -Fq 'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' "$playbook"
grep -Fq 'become_user: aiops_assistant' "$playbook"
grep -Fq 'failed_when: false' "$playbook"
grep -Fq 'ansible.builtin.copy:' "$playbook"
grep -Fq 'force: false' "$playbook"
grep -Fq 'mode: "0700"' "$playbook"
grep -Fq 'mode: "0600"' "$playbook"
grep -Fq 'follow: false' "$playbook"
grep -Fq 'json_shape_valid' "$playbook"
grep -Fq "'policy_denied'" "$playbook"
grep -Fq "'catalog_missing'" "$playbook"
grep -Fq "'connectivity_error'" "$playbook"
grep -Fq "'authentication_error'" "$playbook"
grep -Fq "'configuration_error'" "$playbook"
grep -Fq "administrator-authorized-phase06-validation" "$playbook"
grep -Fq "administrator-confirmed-external-evidence" "$playbook"
grep -Fq "administrator-approved-protected-validation-location" "$playbook"
grep -Fq "ai_ops_assistant_phase06_validation_source_revision != 'unconfirmed'" "$playbook"

if grep -nE 'ansible\.builtin\.(shell|raw|debug)|playbook_validate_phase06_restricted_host_diagnostics|ai_ops_runtime|(^|[[:space:]])stdout:|(^|[[:space:]])stderr:|content:.*(stdout|stderr)|private.key|password' "$playbook"; then
  fail "shell execution, historical reuse, raw output persistence, or sensitive handling found"
fi

if grep -nE 'phase05_acceptance_confirmed: true|neutron_read_classified: true|operator_reader_reviewed: true|observer_policy_reviewed: true|negative_test_plan_approved: true|output_schema_frozen: true|redaction_check_completed: true' "$playbook"; then
  fail "validation producer contains success-shaped gate defaults"
fi

printf 'Phase 06 validation producer stub test passed\n'
