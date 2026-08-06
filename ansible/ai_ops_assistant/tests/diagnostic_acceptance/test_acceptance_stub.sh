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
rtk grep -Fq 'that: false' "$playbook"

if rtk grep -nE 'ansible\.builtin\.(command|shell)|openstack|server_identifier|vars_prompt|pause' "$playbook"; then
  printf 'acceptance stub test: prohibited execution or identifier transport found\n' >&2
  exit 1
fi

printf 'acceptance stub test passed\n'
