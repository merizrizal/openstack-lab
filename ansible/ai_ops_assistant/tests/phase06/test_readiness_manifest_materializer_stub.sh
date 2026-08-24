#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_materialize_live_acceptance_readiness_manifest.yml"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

[[ -f "$playbook" && ! -L "$playbook" ]] || fail "readiness-manifest materializer playbook is missing or symlinked"

grep -Fq 'hosts: ai_ops_assistant' "$playbook"
grep -Fq "inventory_hostname == 'assistant02'" "$playbook"
grep -Fq "ansible_limit | default('') == 'assistant02'" "$playbook"
grep -Fq 'ai_ops_assistant_readiness_manifest_materializer_enabled: false' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_manifest_materializer_mode: runtime' "$playbook"
grep -Fq "ai_ops_assistant_readiness_manifest_materializer_mode in ['campaign', 'runtime']" "$playbook"
grep -Fq 'schema_version: "1.0"' "$playbook"
grep -Fq 'status: blocked' "$playbook"
grep -Fq 'limitation_class: authorization_pending' "$playbook"
grep -Fq 'materialized: false' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_manifest_materializer_run_id: "2026-0004"' "$playbook"
grep -Fq 'phase06-live-acceptance-2026-0004' "$playbook"
grep -Fq 'phase06-restricted-diagnostics-live-acceptance' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_manifest_materializer_source_revision: 2026-0004-source-r1' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_manifest_materializer_environment_label: local-lab' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_manifest_materializer_evidence_owner: openstack lab admin' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_manifest_materializer_scope_approvals: []' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_manifest_materializer_protected_input_references: {}' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_manifest_materializer_integrity_checks: {}' "$playbook"
grep -Fq 'Assert owner-provided readiness-manifest identity inputs' "$playbook"
grep -Fq 'Assert closed readiness-manifest scope-approval collection' "$playbook"
grep -Fq 'Assert each readiness-manifest scope approval' "$playbook"
grep -Fq 'Assert closed readiness-manifest protected-input references' "$playbook"
grep -Fq 'Assert each readiness-manifest protected-input reference' "$playbook"
grep -Fq 'Assert closed readiness-manifest integrity-check collection' "$playbook"
grep -Fq 'Assert each readiness-manifest integrity check' "$playbook"
grep -Fq "item.status in ['approved', 'pending', 'denied', 'revoked', 'expired']" "$playbook"
grep -Fq "item.value.status in ['passed', 'blocked', 'failed', 'unavailable']" "$playbook"
grep -Fq 'run_id' "$playbook"
grep -Fq 'no_log: true' "$playbook"
grep -Fq 'ansible.builtin.set_fact:' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_manifest_materializer_issued_at: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_manifest_materializer_expires_at: unconfirmed' "$playbook"
grep -Fq '/run/openstack-ai-ops/2026-0004/phase06-readiness.json' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_manifest_materializer_directory_owner: aiops_assistant' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_manifest_materializer_directory_mode: "0700"' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_manifest_materializer_file_mode: "0600"' "$playbook"
grep -Fq 'Require every readiness-manifest scope approval' "$playbook"
grep -Fq 'Require every readiness-manifest integrity check' "$playbook"
grep -Fq "ai_ops_assistant_readiness_manifest_materializer_mode == 'runtime'" "$playbook"
grep -Fq 'Publish campaign authorization outcome without materialization' "$playbook"
grep -Fq 'mode: campaign' "$playbook"
grep -Fq 'Build normalized ready readiness manifest in protected task state' "$playbook"
grep -Fq 'Assert serialized readiness-manifest bound' "$playbook"
grep -Fq 'Atomically write fixed readiness manifest' "$playbook"
grep -Fq 'ansible.builtin.file:' "$playbook"
grep -Fq 'ansible.builtin.copy:' "$playbook"
grep -Fq 'follow: false' "$playbook"
grep -Fq 'force: false' "$playbook"
grep -Fq 'unsafe_writes: false' "$playbook"
grep -Fq 'Refuse an existing readiness manifest' "$playbook"
grep -Fq 'Assert fixed readiness-manifest metadata' "$playbook"

if grep -nE 'ansible\.builtin\.(command|shell|raw|script|template|slurp|debug)|stdout|stderr|password|token|credential|address|audit.line' "$playbook"; then
  fail "materializer accesses content or exposes protected output"
fi

if grep -nE 'enabled: true' "$playbook"; then
  fail "materializer contains an activation-shaped default"
fi

printf 'Readiness-manifest materializer stub test passed\n'
