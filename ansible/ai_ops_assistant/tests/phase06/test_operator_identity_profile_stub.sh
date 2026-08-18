#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_deploy_operator_identity_profile.yml"
role_defaults="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_operator_identity_boundary/defaults/main.yml"
role_tasks="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_operator_identity_boundary/tasks/main.yml"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

for path in "$playbook" "$role_defaults" "$role_tasks"; do
  [[ -f "$path" && ! -L "$path" ]] || fail "required operator-reader artifact is missing or symlinked: $path"
done

grep -Fq 'hosts: ai_ops_assistant' "$playbook"
grep -Fq "inventory_hostname == 'assistant02'" "$playbook"
grep -Fq "ansible_limit | default('') == 'assistant02'" "$playbook"
grep -Fq 'ai_ops_assistant_operator_identity_boundary_enabled: false' "$playbook"
grep -Fq 'ai_ops_assistant_operator_identity_boundary_source_run_id: "2026-0004"' "$playbook"
grep -Fq 'ai_ops_assistant_operator_identity_boundary_source_directory: /run/openstack-ai-ops/2026-0004/operator-reader' "$playbook"
grep -Fq 'ai_ops_assistant_operator_identity_boundary_source_revision: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_operator_identity_boundary_source_freshness_status: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_operator_identity_boundary_expiry_policy: maximum-24-hours' "$playbook"
grep -Fq 'ai_ops_assistant_operator_identity_boundary_rotation_requested: false' "$playbook"
grep -Fq 'ai_ops_assistant_operator_identity_boundary_revocation_requested: false' "$playbook"
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
grep -Fq 'no_log: true' "$playbook"
grep -Fq 'ansible.builtin.find:' "$role_tasks"
grep -Fq 'ansible.builtin.copy:' "$role_tasks"
grep -Fq 'Remove transient operator-reader source after target verification' "$role_tasks"
grep -Fq 'Revoke operator-reader profile files independently' "$role_tasks"
grep -Fq 'state: absent' "$role_tasks"
grep -Fq "source_freshness_status ==" "$role_tasks"
grep -Fq "source_revision | length > 0" "$role_tasks"
grep -Fq "revocation_authorization == 'approved'" "$role_tasks"
grep -Fq 'maximum-24-hours' "$role_defaults"
grep -Fq 'rotation_requested: false' "$role_defaults"
grep -Fq 'revocation_requested: false' "$role_defaults"

if grep -nE 'ansible\.builtin\.(shell|command|raw|slurp)|(^|[[:space:]])debug:|hosts: all|ai_ops_runtime|(^|[[:space:]])stdout:|(^|[[:space:]])stderr:|private\.key|intentionally unavailable' "$playbook" "$role_defaults" "$role_tasks"; then
  fail "live command execution, broad scope, protected-content handling, or intentional stub found"
fi

if grep -nE '^    ai_ops_assistant_operator_identity_boundary_enabled: true|^    ai_ops_assistant_operator_identity_boundary_source_freshness_status: fresh|^    ai_ops_assistant_operator_identity_boundary_rotation_authorization: approved|^    ai_ops_assistant_operator_identity_boundary_revocation_authorization: approved' "$playbook"; then
  fail "operator profile harness contains success-shaped gate defaults"
fi

printf 'Operator identity profile deployment/lifecycle harness test passed\n'
