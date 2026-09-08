#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
role_root="$repo_root/ansible/ai_ops_assistant/roles/mcp_wheelhouse_transfer"
defaults="$role_root/defaults/main.yml"
tasks="$role_root/tasks/main.yml"
transfer="$role_root/tasks/transfer.yml"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_transfer_mcp_wheelhouse.yml"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

for path in "$defaults" "$tasks" "$transfer" "$playbook"; do
  [[ -f "$path" && ! -L "$path" ]] || fail "required transfer artifact is missing or symlinked: $path"
done

grep -Fq 'ai_ops_mcp_wheelhouse_transfer:' "$defaults"
grep -Fq 'enabled: false' "$defaults"
grep -Fq 'host: builder01' "$defaults"
grep -Fq '/var/lib/openstack-ai-ops/wheelhouse-artifacts/mcp' "$defaults"
grep -Fq '/tmp/openstack-ai-ops-wheelhouse-transfer/mcp' "$defaults"
grep -Fq '/var/lib/openstack-ai-ops/wheelhouse/mcp' "$defaults"

grep -Fq "inventory_hostname == 'assistant02'" "$tasks"
grep -Fq "inventory_hostname == 'assistant02'" "$playbook"
grep -Fq "ai_ops_mcp_wheelhouse_transfer.enabled | type_debug == 'bool'" "$tasks"
grep -Fq 'include_tasks: transfer.yml' "$tasks"
grep -Fq 'builder.host == '\''builder01'\''' "$tasks"

grep -Fq -- 'manifest.json' "$transfer"
grep -Fq -- 'manifest.sha256' "$transfer"
grep -Fq -- 'requirements.lock' "$transfer"
grep -Fq -- 'wheels/[^/]+\\.whl' "$transfer"
grep -Fq -- 'sha256sum' "$transfer"
grep -Fq -- 'ansible.builtin.fetch' "$transfer"
grep -Fq -- '/usr/bin/mv' "$transfer"
grep -Fq -- 'not ai_ops_mcp_wheelhouse_transfer_source_stat.stat.islnk' "$transfer"
grep -Fq -- 'not item.stat.islnk' "$transfer"
grep -Fq -- 'no_log: true' "$transfer"

grep -Fq "hosts: ai_ops_assistant" "$playbook"
grep -Fq "ansible_play_hosts_all == ['assistant02']" "$playbook"
grep -Fq "ansible_limit | default('') == 'assistant02'" "$playbook"
grep -Fq 'role: mcp_wheelhouse_transfer' "$playbook"
grep -Fq 'enabled: false' "$playbook"

if grep -nE -- '--index-url|--extra-index-url|pypi\.org|https?://|state: started|enabled: true|systemd|firewall|listener|service|ansible\.builtin\.(pip|package|shell|raw)' \
  "$defaults" "$tasks" "$transfer" "$playbook"; then
  fail 'activation, package acquisition, public-index, or service behavior found in MCP transfer artifacts'
fi

printf 'MCP wheelhouse transfer static acceptance passed\n'
