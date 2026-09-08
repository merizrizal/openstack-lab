#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
mcp_role="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp"
stdio_role="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio"
mcp_defaults="$mcp_role/defaults/main.yml"
stdio_defaults="$stdio_role/defaults/main.yml"
mcp_tasks="$mcp_role/tasks/main.yml"
stdio_tasks="$stdio_role/tasks/main.yml"
mcp_playbook="$repo_root/ansible/ai_ops_assistant/playbook_deploy_mcp.yml"
stdio_playbook="$repo_root/ansible/ai_ops_assistant/playbook_deploy_mcp_stdio.yml"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

assert_file() {
  [[ -f "$1" && ! -L "$1" ]] || fail "required contract file is missing or symlinked: $1"
}

assert_missing() {
  [[ ! -e "$1" ]] || fail "unapproved dependency input is present: $1"
}

for path in "$mcp_defaults" "$stdio_defaults" "$mcp_tasks" "$stdio_tasks" \
  "$mcp_playbook" "$stdio_playbook" \
  "$mcp_role/files/mcp/requirements.in" \
  "$stdio_role/files/mcp_stdio/requirements.in"; do
  assert_file "$path"
done

# The lock and wheel closure is owner-supplied and is intentionally absent.
# This fixture passes only while both enabled paths remain fail-closed.
assert_missing "$mcp_role/files/mcp/requirements.lock"
assert_missing "$stdio_role/files/mcp_stdio/requirements.lock"
assert_missing "$mcp_role/files/mcp/wheels"
assert_missing "$stdio_role/files/mcp_stdio/wheels"

grep -Fq 'ai_ops_assistant_mcp_enabled: false' "$mcp_defaults"
grep -Fq 'ai_ops_assistant_mcp_explicit_activation: false' "$mcp_defaults"
grep -Fq 'ai_ops_assistant_mcp_stdio_enabled: false' "$stdio_defaults"
grep -Fq 'ai_ops_assistant_mcp_stdio_explicit_activation: false' "$stdio_defaults"
grep -Fq 'ai_ops_assistant_mcp_enabled: false' "$mcp_playbook"
grep -Fq 'ai_ops_assistant_mcp_explicit_activation: false' "$mcp_playbook"
grep -Fq 'ai_ops_assistant_mcp_stdio_enabled: false' "$stdio_playbook"
grep -Fq 'ai_ops_assistant_mcp_stdio_explicit_activation: false' "$stdio_playbook"

grep -Fxq 'mcp==1.28.1' "$mcp_role/files/mcp/requirements.in"
grep -Fxq 'mcp==1.28.1' "$stdio_role/files/mcp_stdio/requirements.in"

# Dependency resolution and public-index access are forbidden in this boundary.
if grep -nE 'ansible\.builtin\.(pip|package)|pip[[:space:]]+install|pip-compile|--index-url|pypi\.org|https?://[^ ]+' \
  "$mcp_defaults" "$mcp_tasks" "$stdio_defaults" "$stdio_tasks" \
  "$mcp_playbook" "$stdio_playbook"; then
  fail "dependency acquisition or public-index access found in MCP deployment artifacts"
fi

# No enabled deployment path may claim a closed dependency environment while the
# owner-supplied lock and wheel inputs are absent.
if grep -nE 'requirements\.lock.*(exists|present|accepted)|wheelhouse.*(exists|present|accepted)' \
  "$mcp_tasks" "$stdio_tasks"; then
  fail "deployment artifact claims an unavailable dependency closure"
fi

printf 'Dependency closure inputs absent; enabled MCP deployment remains fail-closed\n'
printf 'MCP dependency closure rejection fixture passed\n'
