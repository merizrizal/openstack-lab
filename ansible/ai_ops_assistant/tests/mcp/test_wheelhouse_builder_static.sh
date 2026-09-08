#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
role_root="$repo_root/ansible/ai_ops_assistant/roles/mcp_wheelhouse_builder"
defaults="$role_root/defaults/main.yml"
tasks="$role_root/tasks/main.yml"
publish="$role_root/tasks/publish.yml"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_build_mcp_wheelhouse.yml"
validator="$role_root/files/validate_wheelhouse_inputs.py"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

for path in "$defaults" "$tasks" "$publish" "$playbook" "$validator"; do
  [[ -f "$path" && ! -L "$path" ]] || fail "required builder artifact is missing or symlinked: $path"
done

grep -Fq 'ai_ops_mcp_wheelhouse_build:' "$defaults"
grep -Fq 'enabled: false' "$defaults"
grep -Fq '/tmp/openstack-ai-ops-wheelhouse-seed-inbox/mcp' "$defaults"
grep -Fq '/var/lib/openstack-ai-ops/wheelhouse-artifacts/mcp' "$defaults"
grep -Fq 'dependency_lock_source: mcp/requirements.lock' "$defaults"
grep -Fq 'provenance_manifest_source: mcp/manifest.json' "$defaults"
grep -Fq 'environment_attestation_source: ""' "$defaults"
grep -Fq 'abi: cp312' "$defaults"
grep -Fq 'platform: ""' "$defaults"
grep -Fq 'compatibility_tags: []' "$defaults"

grep -Fq "inventory_hostname == 'builder01'" "$tasks"
grep -Fq "ai_ops_mcp_wheelhouse_build.enabled | type_debug == 'bool'" "$tasks"
grep -Fq 'ERR_MCP_WHEELHOUSE_DEPENDENCY_INPUTS' "$tasks"
grep -Fq 'not item.stat.islnk' "$tasks"
grep -Fq 'ERR_MCP_WHEELHOUSE_SEED_CONTENTS' "$tasks"
grep -Fq 'include_tasks: publish.yml' "$tasks"
grep -Fq 'environment_attestation_source | length > 0' "$tasks"
grep -Fq 'validate_wheelhouse_inputs.py' "$publish"
grep -Fq -- '--attestation' "$publish"
grep -Fq -- '--expected-tags-json' "$publish"

grep -Fq -- '--no-index' "$publish"
grep -Fq -- '--require-hashes' "$publish"
grep -Fq -- '--platform' "$publish"
grep -Fq -- '--python-version' "$publish"
grep -Fq -- '--implementation' "$publish"
grep -Fq -- '--abi' "$publish"
grep -Fq 'manifest.json' "$publish"
grep -Fq 'manifest.sha256' "$publish"
grep -Fq 'no_log: true' "$publish"
grep -Fq '/usr/bin/mv' "$publish"

if grep -nE -- '--index-url|--extra-index-url|pypi\.org|https?://' "$defaults" "$tasks" "$publish" "$playbook"; then
  fail 'public package-index access found in MCP builder artifacts'
fi
if grep -nE 'enabled: true|state: started|enabled: yes|systemd|firewall|listener|service|role: common|ansible\.builtin\.(package|pip|apt)' \
  "$defaults" "$tasks" "$publish" "$playbook"; then
  fail 'activation or host-service behavior found in MCP builder artifacts'
fi

printf 'MCP wheelhouse builder static acceptance passed\n'
