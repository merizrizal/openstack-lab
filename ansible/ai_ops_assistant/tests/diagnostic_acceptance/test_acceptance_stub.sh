#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_accept_diagnostic_toolbox.yml"

[[ -f "$playbook" && ! -L "$playbook" ]] || {
  printf 'acceptance stub test: playbook is missing or symlinked\n' >&2
  exit 1
}

rtk grep -Fq 'hosts: ai_ops_assistant' "$playbook"
rtk grep -Fq "inventory_hostname == 'assistant02'" "$playbook"
rtk grep -Fq "ansible_limit | default('') == 'assistant02'" "$playbook"
rtk grep -Fq "ai_ops_assistant_acceptance_run_id is match('^[a-z0-9][a-z0-9-]{0,47}$')" "$playbook"
rtk grep -Fq "ai_ops_assistant_acceptance_transport == 'sdk-tty-one-shot'" "$playbook"
rtk grep -Fq "ai_ops_assistant_acceptance_comparator == 'administrator-owned-boolean-only'" "$playbook"
rtk grep -Fq "ai_ops_assistant_acceptance_pre_attestation_interface == 'administrator-owned-boolean-only'" "$playbook"
rtk grep -Fq "ai_ops_assistant_acceptance_post_attestation_interface == 'administrator-owned-boolean-only'" "$playbook"
rtk grep -Fq 'ansible.builtin.stat:' "$playbook"
rtk grep -Fq 'ansible.builtin.slurp:' "$playbook"
rtk grep -Fq 'follow: false' "$playbook"
rtk grep -Fq "ai_ops_assistant_acceptance_record_metadata.stat.mode == '0600'" "$playbook"
rtk grep -Fq "ai_ops_assistant_acceptance_record_directory_metadata.stat.mode == '0700'" "$playbook"
rtk grep -Fq 'ai_ops_assistant_acceptance_record_raw.content | b64decode | from_json' "$playbook"
rtk grep -Fq "ai_ops_assistant_acceptance_record.schema_version == '1.0'" "$playbook"
rtk grep -Fq "ai_ops_assistant_acceptance_record.unresolved_gate == 'administrator-post-state-attestation'" "$playbook"
rtk grep -Fq "['server_basic_info', 'server_network_info']" "$playbook"
rtk grep -Fq "['ok', 'not_found', 'policy_denied', 'authentication_error', 'connectivity_error', 'execution_error']" "$playbook"
! rtk grep -Fq 'that: false' "$playbook"

if rtk grep -nE 'ansible\.builtin\.(command|shell)|(^|[[:space:]/])openstack([[:space:]]|$)|server_identifier|vars_prompt|pause' "$playbook"; then
  printf 'acceptance stub test: prohibited execution or identifier transport found\n' >&2
  exit 1
fi

printf 'acceptance stub test passed\n'
