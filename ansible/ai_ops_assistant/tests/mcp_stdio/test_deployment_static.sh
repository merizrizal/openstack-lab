#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
role_root="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio"
role_defaults="$role_root/defaults/main.yml"
role_tasks="$role_root/tasks/main.yml"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_deploy_mcp_stdio.yml"
artifact_root="$role_root/files/mcp_stdio"
config="$artifact_root/config.json"
requirements_in="$artifact_root/requirements.in"
lock_source="$artifact_root/requirements.lock"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

for path in "$role_defaults" "$role_tasks" "$playbook" \
  "$artifact_root/aiops_assistant_mcp_stdio_server.py" \
  "$artifact_root/mcp_resource_catalog.json" "$config" "$requirements_in"; do
  [[ -f "$path" && ! -L "$path" ]] || fail "required local-stdio artifact is missing or symlinked: $path"
done

# The lock is an approved prerequisite, not a fabricated repository artifact.
# Its absence must keep an enabled deployment fail-closed.
if [[ -L "$lock_source" ]]; then
  fail "dependency lock input must not be symlinked: $lock_source"
fi

grep -Fq 'ai_ops_assistant_mcp_stdio_enabled: false' "$role_defaults"
grep -Fq 'ai_ops_assistant_mcp_stdio_explicit_activation: false' "$role_defaults"
grep -Fq 'ai_ops_assistant_mcp_stdio_lifecycle_action: present' "$role_defaults"
grep -Fq 'ai_ops_assistant_mcp_stdio_removal_requested: false' "$role_defaults"
grep -Fq 'ai_ops_assistant_mcp_stdio_removal_authorization: unconfirmed' "$role_defaults"
grep -Fq '/opt/openstack-ai-ops-assistant/mcp-stdio' "$role_defaults"
grep -Fq '/etc/ai-ops-assistant/mcp-stdio' "$role_defaults"
grep -Fq 'ai_ops_assistant_mcp_stdio_dependency_requirement:' "$role_defaults"
grep -Fq '  mcp==1.28.1' "$role_defaults"
grep -Fq 'external-approved-offline-artifact' "$role_defaults"
grep -Fq 'mcp_stdio/requirements.lock' "$role_defaults"

grep -Fq 'hosts: ai_ops_assistant' "$playbook"
grep -Fq "inventory_hostname == 'assistant02'" "$playbook"
grep -Fq "'ai_ops_assistant' in group_names" "$playbook"
grep -Fq "ansible_play_hosts_all == ['assistant02']" "$playbook"
grep -Fq "ansible_limit | default('') == 'assistant02'" "$playbook"
grep -Fq 'role: ai_ops_assistant_mcp_stdio' "$playbook"
grep -Fq 'ai_ops_assistant_mcp_stdio_enabled: false' "$playbook"
grep -Fq 'ai_ops_assistant_mcp_stdio_explicit_activation: false' "$playbook"
[[ "$(grep -Ec '^[[:space:]]+- role:' "$playbook")" -eq 1 ]] || \
  fail "local-stdio playbook must include exactly one role"

if grep -nE 'ai_ops_assistant_mcp_stdio_(enabled|explicit_activation): true' "$playbook"; then
  fail "local-stdio playbook enables activation"
fi

grep -Fq 'follow: false' "$role_tasks"
grep -Fq 'item.stat.isreg' "$role_tasks"
grep -Fq 'not item.stat.islnk' "$role_tasks"
grep -Fq 'ai_ops_assistant_mcp_stdio_dependency_metadata' "$role_tasks"
grep -Fq 'ai_ops_assistant_mcp_stdio_enabled | bool' "$role_tasks"
grep -Fq 'state: directory' "$role_tasks"
grep -Fq 'mode: "0750"' "$role_tasks"
grep -Fq 'mode: "{{ item.mode }}"' "$role_tasks"
grep -Fq "item.stat.pw_name == 'root'" "$role_tasks"
grep -Fq 'item.stat.gr_name == ai_ops_assistant_mcp_stdio_runtime_group' "$role_tasks"
grep -Fq 'item.stat.mode == item.item.mode' "$role_tasks"

if grep -nE 'ansible\.builtin\.(shell|command|raw|expect|package|pip)|systemd|service|listener|socket|firewall|route|client|(^|[[:space:]])(runner|audit|rollback)([[:space:]:]|$)|state: (started|absent)|enabled: true|hosts: all|/opt/openstack-ai-ops/' \
  "$playbook" "$role_defaults" "$role_tasks" "$config" "$requirements_in"; then
  fail "activation, network, package-install, removal, or historical-runtime behavior found"
fi

"${PYTHON_BIN:-/usr/bin/python3}" - "$config" "$requirements_in" <<'PY'
import json
import sys
from pathlib import Path

def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


config = json.loads(
    Path(sys.argv[1]).read_text(encoding="utf-8"),
    object_pairs_hook=reject_duplicate_keys,
)
assert set(config) == {
    "schema_version",
    "transport",
    "runtime_root",
    "adapter_path",
    "resource_catalog_path",
    "max_concurrent_runner_children",
    "cleanup_grace_seconds",
}
assert config == {
    "schema_version": 1,
    "transport": "stdio",
    "runtime_root": "/opt/openstack-ai-ops-assistant/mcp-stdio",
    "adapter_path": "/opt/openstack-ai-ops-assistant/mcp-stdio/aiops_assistant_mcp_stdio_server.py",
    "resource_catalog_path": "/opt/openstack-ai-ops-assistant/mcp-stdio/mcp_resource_catalog.json",
    "max_concurrent_runner_children": 1,
    "cleanup_grace_seconds": 5,
}
assert Path(sys.argv[2]).read_text(encoding="utf-8") == "mcp==1.28.1\n"
PY

"${PYTHON_BIN:-/usr/bin/python3}" -m py_compile \
  "$artifact_root/aiops_assistant_mcp_stdio_server.py"

if [[ -e "$lock_source" ]]; then
  printf 'Dependency lock input present; separate hash/closure approval remains required\n'
else
  printf 'Dependency lock input absent; enabled deployment remains fail-closed\n'
fi
printf 'Local-stdio deployment static acceptance passed\n'
