#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_deploy_operator_identity_profile.yml"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

[[ -f "$playbook" && ! -L "$playbook" ]] || fail "operator profile playbook is missing or symlinked"

grep -Fq 'hosts: ai_ops_assistant' "$playbook"
grep -Fq "inventory_hostname == 'assistant02'" "$playbook"
grep -Fq "ansible_limit | default('') == 'assistant02'" "$playbook"
grep -Fq 'ai_ops_assistant_operator_identity_boundary_enabled: false' "$playbook"
grep -Fq "ai_ops_assistant_operator_identity_boundary_deployment_authorization: unconfirmed" "$playbook"
grep -Fq "ai_ops_assistant_operator_identity_boundary_phase05_acceptance_outcome: unconfirmed" "$playbook"
grep -Fq "ai_ops_assistant_operator_identity_boundary_project_reader_need_proof: unconfirmed" "$playbook"
grep -Fq "ai_ops_assistant_operator_identity_boundary_need_proof_operation: neutron_agent_list_project_reader" "$playbook"
grep -Fq "ai_ops_assistant_operator_identity_boundary_profile_name: aiops-assistant-operator-reader" "$playbook"
grep -Fq "ai_ops_assistant_operator_identity_boundary_profile_directory: /opt/openstack-ai-ops-assistant/credentials/operator-reader" "$playbook"
grep -Fq "ai_ops_assistant_operator_identity_boundary_profile_selection: neutron_agent_health" "$playbook"
grep -Fq "ai_ops_assistant_operator_identity_boundary_rotation_validation_outcome: unconfirmed" "$playbook"
grep -Fq "ai_ops_assistant_operator_identity_boundary_revocation_validation_outcome: unconfirmed" "$playbook"
grep -Fq 'operation: create' "$playbook"
grep -Fq 'operation: update' "$playbook"
grep -Fq 'operation: delete' "$playbook"
grep -Fq 'result: unconfirmed' "$playbook"
grep -Fq "lookup('ansible.builtin.env', item" "$playbook"
grep -Fq 'when: ai_ops_assistant_operator_identity_boundary_enabled | bool' "$playbook"
grep -Fq 'Require operator-owned profile inputs before profile tasks' "$playbook"
grep -Fq 'Require all operator-owned gates before profile tasks' "$playbook"
grep -Fq "ai_ops_assistant_operator_identity_boundary_source_classification == 'controller-local'" "$playbook"
grep -Fq 'ai_ops_assistant_operator_identity_boundary_identity_owner | length > 0' "$playbook"
grep -Fq 'ai_ops_assistant_operator_identity_boundary_approved_role_scope | length > 0' "$playbook"
grep -Fq 'ai_ops_assistant_operator_identity_boundary_rotation_owner | length > 0' "$playbook"
grep -Fq 'ai_ops_assistant_operator_identity_boundary_revocation_owner | length > 0' "$playbook"
grep -Fq 'ai_ops_assistant_operator_identity_boundary_mutation_denial_reference | length > 0' "$playbook"
grep -Fq "ai_ops_assistant_operator_identity_boundary_project_reader_need_proof == 'policy_denied'" "$playbook"
grep -Fq "ai_ops_assistant_operator_identity_boundary_phase05_acceptance_outcome == 'accepted'" "$playbook"
grep -Fq "schema_version: \"1.0\"" "$playbook"
grep -Fq 'status: blocked' "$playbook"
grep -Fq 'limitation_class: authorization_pending' "$playbook"
grep -Fq 'no_log: true' "$playbook"
grep -Fq 'ai_ops_assistant_operator_identity_boundary' "$playbook"

if grep -nE 'ansible\.builtin\.(shell|command|raw)|(^|[[:space:]])debug:|ansible\.builtin\.(copy|template|slurp)|hosts: all|ai_ops_runtime|(^|[[:space:]])stdout:|(^|[[:space:]])stderr:|cleanup|private\.key' "$playbook"; then
  fail "live command execution, profile-content handling, broad scope, historical reuse, or raw output handling found"
fi

if grep -nE '^    ai_ops_assistant_operator_identity_boundary_enabled: true|^    ai_ops_assistant_operator_identity_boundary_project_reader_need_proof: (pass|empty)|^    ai_ops_assistant_operator_identity_boundary_phase05_acceptance_outcome: accepted|^    ai_ops_assistant_operator_identity_boundary_rotation_validation_outcome: accepted|^    ai_ops_assistant_operator_identity_boundary_revocation_validation_outcome: accepted' "$playbook"; then
  fail "operator profile harness contains success-shaped gate defaults"
fi

printf 'Operator identity profile deployment/static harness test passed\n'
