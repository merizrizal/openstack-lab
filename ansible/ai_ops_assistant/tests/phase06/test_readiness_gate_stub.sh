#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_validate_live_acceptance_readiness.yml"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

[[ -f "$playbook" && ! -L "$playbook" ]] || fail "readiness-gate playbook is missing or symlinked"

grep -Fq 'hosts: ai_ops_assistant' "$playbook"
grep -Fq "inventory_hostname == 'assistant02'" "$playbook"
grep -Fq "ansible_limit | default('') == 'assistant02'" "$playbook"
grep -Fq 'ai_ops_assistant_readiness_gate_enabled: false' "$playbook"
grep -Fq "ai_ops_assistant_readiness_gate_authorization_reference == 'phase06-live-acceptance-2026-0004'" "$playbook"
grep -Fq "ai_ops_assistant_readiness_gate_authorization_class == 'phase06-restricted-diagnostics-live-acceptance'" "$playbook"
grep -Fq "ai_ops_assistant_readiness_gate_run_id == '2026-0004'" "$playbook"
grep -Fq "/run/openstack-ai-ops/2026-0004/phase06-readiness.json" "$playbook"
grep -Fq '/opt/openstack-ai-ops-assistant/scripts/tool_runner/readiness_manifest.py' "$playbook"
grep -Fq 'status: blocked' "$playbook"
grep -Fq 'limitation_class: authorization_pending' "$playbook"
grep -Fq 'ready: false' "$playbook"
grep -Fq 'not (ai_ops_assistant_readiness_gate_enabled | bool)' "$playbook"
grep -Fq 'Run fixed readiness-manifest validator after explicit authorization' "$playbook"
grep -Fq 'ansible.builtin.command:' "$playbook"
grep -Fq 'argv:' "$playbook"
grep -Fq -- '- python3' "$playbook"
grep -Fq -- '- /opt/openstack-ai-ops-assistant/scripts/tool_runner/readiness_manifest.py' "$playbook"
grep -Fq 'register: ai_ops_assistant_readiness_gate_raw' "$playbook"
grep -Fq 'failed_when: false' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_gate_raw.rc in [0, 5]' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_gate_raw.stdout | length <= 256' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_gate_raw.stdout | trim | from_json' "$playbook"
grep -Fq 'Accept only a normalized ready readiness-gate outcome' "$playbook"
grep -Fq "['limitation_class', 'ready', 'schema_version', 'status']" "$playbook"
grep -Fq 'ai_ops_assistant_readiness_gate_raw.rc == 0' "$playbook"
grep -Fq "ai_ops_assistant_readiness_gate_output.status == 'ready'" "$playbook"
grep -Fq "ai_ops_assistant_readiness_gate_output.limitation_class == 'none'" "$playbook"
grep -Fq 'ai_ops_assistant_readiness_gate_output.ready is boolean' "$playbook"
grep -Fq 'ai_ops_assistant_readiness_gate_output.ready' "$playbook"
grep -Fq 'ansible.builtin.set_fact:' "$playbook"
grep -Fq 'no_log: true' "$playbook"

if grep -nE 'ansible\.builtin\.(shell|raw|script|slurp|stat|copy|debug)|private.key|password|token|credential|address|audit.line' "$playbook"; then
  fail "protected-input handling or unsafe command module found"
fi

if grep -Fq '{{ ai_ops_assistant_readiness_gate_validator_path }}' "$playbook"; then
  fail "readiness validator path is caller-controlled"
fi

if grep -nE 'status: ready|ready: true|enabled: true' "$playbook"; then
  fail "readiness gate contains an activation-shaped default"
fi

printf 'Readiness-gate stub test passed\n'
