#!/usr/bin/env bash
# Local static contract gate for the revised Phase 03 diagnostic toolbox.
set -u
set -o pipefail

if [[ "$#" -ne 0 ]]; then
  printf 'usage: %s\n' "$0" >&2
  exit 64
fi
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
approved_dir="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved"
readonly -a expected=(
  'lib/aiops_common.sh'
  'project_resource_summary.sh'
  'server_basic_info.sh'
  'server_network_info.sh'
)
[[ -d "$approved_dir" ]] || { printf 'revised diagnostic gate: approved directory is missing\n' >&2; exit 66; }
for expected_file in "${expected[@]}"; do
  [[ ! -L "$approved_dir/$expected_file" ]] || { printf 'revised diagnostic gate: symlinks are not permitted\n' >&2; exit 1; }
done
mapfile -t actual < <(find "$approved_dir" -type f -name '*.sh' -printf '%P\n' | sort)
[[ "${actual[*]}" == "${expected[*]}" ]] || { printf 'revised diagnostic gate: approved file allowlist mismatch\n' >&2; exit 1; }
bash "$repo_root/scripts/check_ai_ops_diagnostic_safety.sh" "$approved_dir"
historical_identifier_pattern='/opt/openstack-ai-ops/|aiops-project-reader|assistant01|neutron_agent_health\.sh|operator\.reader'
if grep -RniI -E "$historical_identifier_pattern" "$approved_dir"; then
  printf 'revised diagnostic gate: historical path/profile identifier found\n' >&2; exit 1
fi
if grep -RniI -E '(cat|grep|sed|awk|sha256sum|md5sum)[^\n]*(clouds\.yaml|credentials/profiles)' "$approved_dir"; then
  printf 'revised diagnostic gate: credential-content read found\n' >&2; exit 1
fi
printf 'revised diagnostic contract gate passed\n'
