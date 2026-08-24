#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_record_mvp_acceptance_evidence.yml"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

[[ -f "$playbook" && ! -L "$playbook" ]] || fail "MVP evidence recorder playbook is missing or symlinked"

grep -Fq 'hosts: ai_ops_assistant' "$playbook"
grep -Fq "inventory_hostname == 'assistant02'" "$playbook"
grep -Fq "ansible_limit | default('') == 'assistant02'" "$playbook"
grep -Fq 'ai_ops_assistant_mvp_evidence_recording_enabled: false' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_evidence_authorization: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_evidence_location_approval: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_evidence_owner_name: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_evidence_parent_directory: /opt/openstack-ai-ops-assistant/evidence' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_evidence_directory: /opt/openstack-ai-ops-assistant/evidence/phase05' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_evidence_validation_result_directory: /run/openstack-ai-ops/phase05-validation' "$playbook"
grep -Fq 'mvp_acceptance_validation' "$playbook"
grep -Fq 'mvp_three_tool_acceptance' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_evidence_manual_validation_fields' "$playbook"
grep -Fq 'ansible.builtin.slurp:' "$playbook"
grep -Fq 'b64decode | from_json' "$playbook"
grep -Fq 'item not in vars' "$playbook"
grep -Fq 'owner_reviewed' "$playbook"
grep -Fq 'pre_attestation_valid' "$playbook"
grep -Fq 'post_attestation_unchanged' "$playbook"
grep -Fq 'ai_explanation_reviewed' "$playbook"
grep -Fq 'ai_refusal_reviewed' "$playbook"
grep -Fq 'ai_disclosure_reviewed' "$playbook"
grep -Fq 'rollback_reviewed' "$playbook"
grep -Fq 'project_resource_summary' "$playbook"
grep -Fq 'server_basic_info' "$playbook"
grep -Fq 'server_network_info' "$playbook"
grep -Fq 'mode: "0700"' "$playbook"
grep -Fq 'mode: "0600"' "$playbook"
grep -Fq 'follow: false' "$playbook"
grep -Fq 'force: false' "$playbook"
grep -Fq 'ansible.builtin.copy:' "$playbook"
grep -Fq 'no_log: true' "$playbook"
grep -Fq 'Known gap labels:' "$playbook"
grep -Fq 'Owner review completed:' "$playbook"

if grep -nE 'ansible\.builtin\.(command|shell|raw)|ansible\.builtin\.debug:|stdout|stderr|private.key|password|token|credential|raw.log|resource.identifier|comparator.data|server_identifier' "$playbook"; then
  fail "raw execution, sensitive fields, identifiers, or unbounded output found"
fi

if grep -nE 'ai_ops_assistant_mvp_evidence_(status|owner_reviewed|pre_attestation_valid|post_attestation_valid|post_attestation_unchanged|result_process_agreement|audit_pair_validated|path_isolation_confirmed|redaction_check_completed|ai_explanation_reviewed|ai_refusal_reviewed|ai_disclosure_reviewed|rollback_reviewed): true' "$playbook"; then
  fail "MVP evidence recorder contains success-shaped gate defaults"
fi

if grep -nE 'playbook_record_restricted_diagnostics_evidence|phase06|ai_ops_runtime' "$playbook"; then
  fail "MVP evidence recorder imports a different phase or historical runtime"
fi

printf 'MVP acceptance evidence recorder stub test passed\n'
