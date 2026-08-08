#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_recover_mvp_rollback.yml"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

[[ -f "$playbook" && ! -L "$playbook" ]] || fail "rollback recovery playbook is missing or symlinked"

grep -Fq 'hosts: ai_ops_assistant' "$playbook"
grep -Fq "inventory_hostname == 'assistant02'" "$playbook"
grep -Fq "ansible_limit | default('') == 'assistant02'" "$playbook"
grep -Fq 'ai_ops_assistant_mvp_recovery_enabled: false' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_recovery_ready: false' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_recovery_post_attestation_unchanged: false' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_recovery_recorded_revision_confirmed: false' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_recovery_external_evidence_location: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_mvp_recovery_credential_confirmation.user_input ==' "$playbook"
grep -Fq "'RESTORED'" "$playbook"
grep -Fq 'ai_ops_assistant_mvp_recovery_artifact_confirmation.user_input ==' "$playbook"
grep -Fq "'VERIFIED'" "$playbook"
grep -Fq 'role: ai_ops_assistant_identity_boundary' "$playbook"
grep -Fq 'role: ai_ops_assistant_tool_runner' "$playbook"
grep -Fq 'ai_ops_assistant_identity_boundary_enabled: true' "$playbook"
grep -Fq 'ai_ops_assistant_tool_runner_enabled: true' "$playbook"
grep -Fq 'ai_ops_assistant_tool_runner_explicit_deployment: true' "$playbook"
grep -Fq 'Do not run diagnostics.' "$playbook"
grep -Fq 'no_log: true' "$playbook"
grep -Fq 'Recovery is fail-closed' "$playbook"

if grep -nE 'ansible\.builtin\.(shell|command|raw)|(^|[[:space:]/])openstack([[:space:]]|$)|vars_prompt|ansible\.builtin\.debug:' "$playbook"; then
  fail "prohibited command, provider, credential-prompt, or debug behavior found"
fi

printf 'MVP rollback recovery stub test passed\n'
