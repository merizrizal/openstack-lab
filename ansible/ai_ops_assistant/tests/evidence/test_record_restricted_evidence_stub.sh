#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_record_restricted_diagnostics_evidence.yml"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

[[ -f "$playbook" && ! -L "$playbook" ]] || fail "evidence recorder playbook is missing or symlinked"
for required in \
  'ai_ops_assistant_restricted_evidence_recording_enabled: false' \
  'ai_ops_assistant_restricted_evidence_validation_result_directory: /run/openstack-ai-ops/phase06-validation' \
  'ai_ops_assistant_restricted_evidence_validation_result_raw' \
  'b64decode | from_json' \
  'item not in vars' \
  'tools | length == 7' \
  'negative_controls | length == 18' \
  'scope_outcomes | length == 11' \
  'audit_pairs | length == 7' \
  'final_acceptance' \
  'Unchanged-state comparison:' \
  'Revocation/rollback:' \
  'mode: "0700"' \
  'mode: "0600"' \
  'no_log: true'; do
  grep -Fq "$required" "$playbook" || fail "missing recorder contract: $required"
done

grep -Fq 'phase06_restricted_diagnostics_validation' "$playbook"
grep -Fq 'seven_tool_acceptance_orchestration' "$playbook"
grep -Fq 'run_id == ai_ops_assistant_restricted_evidence_run_id' "$playbook"
grep -Fq 'source_revision == ai_ops_assistant_restricted_evidence_source_revision' "$playbook"
grep -Fq 'force: false' "$playbook"
grep -Fq 'follow: false' "$playbook"

if grep -nE 'ansible\.builtin\.(command|shell|raw)|ansible\.builtin\.debug:|stdout|stderr|private\.key|password|token|credential|address|raw.log|comparator.data' "$playbook"; then
  fail "recorder contains raw execution or sensitive disclosure"
fi

printf 'Restricted evidence recorder static test passed\n'
