#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_record_restricted_diagnostics_evidence.yml"

afail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

[[ -f "$playbook" && ! -L "$playbook" ]] || afail "evidence recorder playbook is missing or symlinked"

grep -Fq 'hosts: ai_ops_assistant' "$playbook"
grep -Fq "inventory_hostname == 'assistant02'" "$playbook"
grep -Fq "ansible_limit | default('') == 'assistant02'" "$playbook"
grep -Fq 'ai_ops_assistant_restricted_evidence_recording_enabled: false' "$playbook"
grep -Fq 'ai_ops_assistant_restricted_evidence_authorization: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_restricted_evidence_location_approval: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_restricted_evidence_owner_name: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_restricted_evidence_parent_directory: /opt/openstack-ai-ops-assistant/evidence' "$playbook"
grep -Fq 'ai_ops_assistant_restricted_evidence_directory: /opt/openstack-ai-ops-assistant/evidence/phase06' "$playbook"
grep -Fq 'ai_ops_assistant_restricted_evidence_validation_result_directory: /run/openstack-ai-ops/phase06-validation' "$playbook"
grep -Fq 'ai_ops_assistant_restricted_evidence_validation_result_allowed_producers:' "$playbook"
grep -Fq 'phase06_restricted_diagnostics_validation' "$playbook"
grep -Fq 'ansible.builtin.slurp:' "$playbook"
grep -Fq 'b64decode | from_json' "$playbook"
grep -Fq 'item not in vars' "$playbook"
grep -Fq 'run_id == ai_ops_assistant_restricted_evidence_run_id' "$playbook"
grep -Fq 'source_revision == ai_ops_assistant_restricted_evidence_source_revision' "$playbook"
grep -Fq 'mode: "0700"' "$playbook"
grep -Fq 'mode: "0600"' "$playbook"
grep -Fq 'follow: false' "$playbook"
grep -Fq 'force: false' "$playbook"
grep -Fq 'ansible.builtin.copy:' "$playbook"
grep -Fq 'no_log: true' "$playbook"
grep -Fq 'Source revision:' "$playbook"
grep -Fq 'Overall status:' "$playbook"
grep -Fq 'Unresolved gate labels:' "$playbook"
grep -Fq 'Redaction check completed:' "$playbook"
grep -Fq 'Map normalized producer result to recorder fields' "$playbook"
grep -Fq 'neutron_read_classified' "$playbook"
grep -Fq 'Reject manual producer-derived validation fields' "$playbook"

if grep -nE 'ansible\.builtin\.(command|shell|raw)|ansible\.builtin\.debug:|stdout|stderr|private.key|password|token|credential|raw.log|resource.identifier|comparator.data' "$playbook"; then
  afail "raw execution, sensitive fields, or unbounded output found"
fi

printf 'Restricted evidence recorder stub test passed\n'
