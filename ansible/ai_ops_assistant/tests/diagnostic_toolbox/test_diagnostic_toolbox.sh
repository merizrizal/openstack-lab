#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../../.." && pwd)"
helper="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved/lib/aiops_common.sh"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

[[ -r "$helper" ]] || fail "helper is missing"
# shellcheck source=../../roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved/lib/aiops_common.sh
source "$helper"

for value in server-01 550e8400-e29b-41d4-a716-446655440000 server.name:1; do
  aiops_require_safe_identifier "$value" "server identifier" || fail "valid identifier rejected: $value"
done

long_identifier="$(printf 'a%.0s' {1..256})"
for value in '' 'bad value' '../server' 'server/name' 'server;id' "$long_identifier"; do
  if aiops_require_safe_identifier "$value" "server identifier"; then
    fail "unsafe identifier accepted"
  fi
done

OS_PASSWORD=ambient
OS_TOKEN=ambient
aiops_use_project_reader_profile
[[ "$OS_CLIENT_CONFIG_FILE" == "/opt/openstack-ai-ops-assistant/credentials/profiles/clouds.yaml" ]] || fail "wrong profile path"
[[ "$OS_CLOUD" == "aiops-assistant-project-reader" ]] || fail "wrong profile name"
[[ -z "${OS_PASSWORD+x}" && -z "${OS_TOKEN+x}" ]] || fail "ambient credentials were retained"

fixture_dir="$(mktemp -d)"
trap 'rm -rf "$fixture_dir"' EXIT
fake_openstack="$fixture_dir/openstack"
printf '#!/usr/bin/env bash\nexit 0\n' > "$fake_openstack"
chmod 0700 "$fake_openstack"

[[ "$(aiops_openstack_bin)" == "/usr/bin/openstack" ]] || fail "production CLI path is not fixed"
[[ "$(AIOPS_TEST_MODE=fixture AIOPS_TEST_OPENSTACK_BIN="$fake_openstack" aiops_openstack_bin)" == "$fake_openstack" ]] || fail "fixture CLI seam failed"

error_output="$(AIOPS_TEST_MODE=fixture AIOPS_TEST_JQ_BIN=/usr/bin/jq aiops_emit_error server_basic_info invalid_input 'bad input')"
printf '%s' "$error_output" | /usr/bin/jq -e \
  '.schema_version == "1.0" and .tool == "server_basic_info" and .status == "error" and .error.class == "invalid_input"' \
  >/dev/null || fail "error envelope is invalid"

set +e
stub_output="$(AIOPS_TEST_MODE=fixture AIOPS_TEST_JQ_BIN=/usr/bin/jq aiops_run_read_section server_basic_info server)"
stub_status=$?
set -e
[[ "$stub_status" -eq 4 ]] || fail "stub did not return explicit non-zero status"
printf '%s' "$stub_output" | /usr/bin/jq -e \
  '.status == "error" and .error.class == "execution_error" and .error.message == "not_implemented"' \
  >/dev/null || fail "stub envelope is invalid"

summary="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved/project_resource_summary.sh"
[[ -r "$summary" ]] || fail "project summary is missing"
# shellcheck source=../../roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved/project_resource_summary.sh
source "$summary"

summary_fake_openstack="$fixture_dir/project-summary-openstack"
summary_argv_log="$fixture_dir/project-summary-argv.log"
cat > "$summary_fake_openstack" <<'EOF_FAKE'
#!/usr/bin/env bash
set -u

printf '%s\n' "$*" >> "$AIOPS_TEST_ARGV_LOG"
[[ "${OS_CLIENT_CONFIG_FILE:-}" == "/opt/openstack-ai-ops-assistant/credentials/profiles/clouds.yaml" ]] || exit 93
[[ "${OS_CLOUD:-}" == "aiops-assistant-project-reader" ]] || exit 94

case "${AIOPS_TEST_SCENARIO:-success}:$*" in
  partial:network\ list\ -f\ json)
    printf 'Forbidden\n' >&2
    exit 1
    ;;
  auth:server\ list\ -f\ json)
    printf 'Unauthorized\n' >&2
    exit 1
    ;;
  malformed:port\ list\ -f\ json)
    printf '{not-json'
    exit 0
    ;;
  truncate:server\ list\ -f\ json)
    printf '['
    for ((index = 1; index <= 51; index++)); do
      [[ "$index" -gt 1 ]] && printf ','
      printf '{"id":"server-%s","name":"server-%s","status":"ACTIVE"}' "$index" "$index"
    done
    printf ']\n'
    exit 0
    ;;
  redact:network\ list\ -f\ json)
    printf '[{"id":"network-1","name":{"token":"fixture-token","display":"network-1"},"status":"ACTIVE"}]\n'
    exit 0
    ;;
  empty:*)
    printf '[]\n'
    exit 0
    ;;
  *:server\ list\ -f\ json)
    printf '[{"id":"server-1","name":"server-1","status":"ACTIVE"}]\n'
    ;;
  *:network\ list\ -f\ json)
    printf '[{"id":"network-1","name":"network-1","status":"ACTIVE"}]\n'
    ;;
  *:subnet\ list\ -f\ json)
    printf '[{"id":"subnet-1","name":"subnet-1","network_id":"network-1","cidr":"192.0.2.0/24","ip_version":4}]\n'
    ;;
  *:port\ list\ -f\ json)
    printf '[{"id":"port-1","device_id":"server-1","network_id":"network-1","status":"ACTIVE"}]\n'
    ;;
  *:volume\ list\ -f\ json)
    printf '[{"id":"volume-1","name":"volume-1","status":"available","size":1}]\n'
    ;;
  *:image\ list\ -f\ json)
    printf '[{"id":"image-1","name":"image-1","status":"active"}]\n'
    ;;
  *:security\ group\ list\ -f\ json)
    printf '[{"id":"security-group-1","name":"default","status":"active"}]\n'
    ;;
  *)
    printf 'unexpected argv: %s\n' "$*" >&2
    exit 95
    ;;
esac
EOF_FAKE
chmod 0700 "$summary_fake_openstack"

run_project_summary() {
  : > "$summary_argv_log"
  set +e
  project_summary_output="$(AIOPS_TEST_MODE=fixture AIOPS_TEST_OPENSTACK_BIN="$summary_fake_openstack" AIOPS_TEST_JQ_BIN=/usr/bin/jq AIOPS_TEST_ARGV_LOG="$summary_argv_log" AIOPS_TEST_SCENARIO="$1" project_resource_summary_main)"
  project_summary_status=$?
  set -e
}

run_project_summary success
[[ "$project_summary_status" -eq 0 ]] || fail "successful project summary failed"
printf '%s' "$project_summary_output" | /usr/bin/jq -e \
  '.tool == "project_resource_summary" and .status == "ok" and (.sections | length == 7) and ([.sections[].status] | all(. == "ok"))' \
  >/dev/null || fail "successful summary envelope is invalid"
[[ "$(wc -l < "$summary_argv_log")" -eq 7 ]] || fail "summary did not issue seven fixed reads"
grep -qx 'server list -f json' "$summary_argv_log" || fail "server argv changed"
grep -qx 'security group list -f json' "$summary_argv_log" || fail "security-group argv changed"

run_project_summary empty
[[ "$project_summary_status" -eq 0 ]] || fail "empty project summary failed"
printf '%s' "$project_summary_output" | /usr/bin/jq -e '[.sections[].status] | all(. == "empty")' >/dev/null || fail "empty sections are not explicit"

run_project_summary partial
[[ "$project_summary_status" -eq 3 ]] || fail "partial summary exit code is incorrect"
printf '%s' "$project_summary_output" | /usr/bin/jq -e \
  '.status == "partial" and (.sections[] | select(.name == "networks").error.class == "policy_denied")' \
  >/dev/null || fail "partial policy result is invalid"

run_project_summary auth
[[ "$project_summary_status" -eq 4 ]] || fail "authentication summary exit code is incorrect"
printf '%s' "$project_summary_output" | /usr/bin/jq -e \
  '.status == "error" and .error.class == "authentication_error" and (.sections | length == 1)' \
  >/dev/null || fail "authentication result is invalid"

run_project_summary malformed
[[ "$project_summary_status" -eq 3 ]] || fail "malformed JSON summary exit code is incorrect"
printf '%s' "$project_summary_output" | /usr/bin/jq -e \
  '.status == "partial" and (.sections[] | select(.name == "ports").error.class == "execution_error")' \
  >/dev/null || fail "malformed JSON result is invalid"

run_project_summary truncate
[[ "$project_summary_status" -eq 0 ]] || fail "truncation summary failed"
printf '%s' "$project_summary_output" | /usr/bin/jq -e \
  '(.sections[] | select(.name == "servers") | .truncated and (.data | length == 50))' \
  >/dev/null || fail "truncation contract is invalid"

run_project_summary redact
[[ "$project_summary_status" -eq 0 ]] || fail "redaction summary failed"
printf '%s' "$project_summary_output" | /usr/bin/jq -e \
  '(.sections[] | select(.name == "networks") | .data[0].name.token == "***REDACTED***")' \
  >/dev/null || fail "redaction contract is invalid"

: > "$summary_argv_log"
set +e
invalid_summary_output="$(AIOPS_TEST_MODE=fixture AIOPS_TEST_OPENSTACK_BIN="$summary_fake_openstack" AIOPS_TEST_JQ_BIN=/usr/bin/jq AIOPS_TEST_ARGV_LOG="$summary_argv_log" project_resource_summary_main unexpected)"
invalid_summary_status=$?
set -e
[[ "$invalid_summary_status" -eq 2 ]] || fail "unexpected summary argument was not rejected"
[[ ! -s "$summary_argv_log" ]] || fail "invalid summary argument reached the fake CLI"
printf '%s' "$invalid_summary_output" | /usr/bin/jq -e \
  '.status == "error" and .error.class == "invalid_input"' \
  >/dev/null || fail "invalid summary envelope is invalid"

printf 'diagnostic toolbox helper and project-summary tests passed\n'
