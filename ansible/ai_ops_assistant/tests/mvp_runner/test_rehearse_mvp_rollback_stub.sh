#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_rehearse_mvp_rollback.yml"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

[[ -f "$playbook" && ! -L "$playbook" ]] || fail "rollback rehearsal playbook is missing or symlinked"

grep -Fq 'hosts: ai_ops_assistant' "$playbook"
grep -Fq "inventory_hostname == 'assistant02'" "$playbook"
grep -Fq "ansible_limit | default('') == 'assistant02'" "$playbook"
grep -Fq 'ai_ops_assistant_mvp_rollback_rehearsal_enabled: false' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_rollback_recovery_ready: false' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_rollback_pre_attestation_valid: false' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_rollback_prior_baseline_attestation_interface: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_rollback_external_evidence_location: unconfirmed' "$playbook"
grep -Fq 'ansible.builtin.file:' "$playbook"
grep -Fq 'state: absent' "$playbook"
grep -Fq 'aiops_tool_runner.py' "$playbook"
grep -Fq 'audit_inspector.py' "$playbook"
grep -Fq 'tool_registry.json' "$playbook"
grep -Fq 'clouds.yaml' "$playbook"
grep -Fq 'secure.yaml' "$playbook"
grep -Fq 'ansible.builtin.pause:' "$playbook"
grep -Fq "user_input == 'REVOKED'" "$playbook"
grep -Fq "user_input == 'VERIFIED'" "$playbook"
grep -Fq 'no_log: true' "$playbook"
grep -Fq 'Rollback rehearsal is fail-closed' "$playbook"

if grep -nE 'ansible\.builtin\.(shell|command|raw)|(^|[[:space:]/])openstack([[:space:]]|$)|OS_APPLICATION_CREDENTIAL_SECRET|vars_prompt|ansible\.builtin\.debug:' "$playbook"; then
  fail "prohibited credential, command, provider, or debug behavior found"
fi

printf 'MVP rollback rehearsal stub test passed\n'
