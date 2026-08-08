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
    printf '[{"ID":"server-1","Name":"server-1","Status":"ACTIVE"}]\n'
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
  '.tool == "project_resource_summary" and .status == "ok" and (.sections | length == 7) and ([.sections[].status] | all(. == "ok")) and (.sections[] | select(.name == "servers") | .data[0].id == "server-1" and .data[0].name == "server-1" and .data[0].status == "ACTIVE")' \
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

server_basic="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved/server_basic_info.sh"
[[ -r "$server_basic" ]] || fail "server basic info is missing"
# shellcheck source=../../roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved/server_basic_info.sh
source "$server_basic"

server_basic_fake_openstack="$fixture_dir/server-basic-openstack"
server_basic_argv_log="$fixture_dir/server-basic-argv.log"
cat > "$server_basic_fake_openstack" <<'EOF_FAKE'
#!/usr/bin/env bash
set -u

printf '%s\n' "$*" >> "$AIOPS_TEST_ARGV_LOG"
[[ "${OS_CLIENT_CONFIG_FILE:-}" == "/opt/openstack-ai-ops-assistant/credentials/profiles/clouds.yaml" ]] || exit 93
[[ "${OS_CLOUD:-}" == "aiops-assistant-project-reader" ]] || exit 94

case "${AIOPS_TEST_SCENARIO:-success}:$*" in
  not_found:server\ show\ *\ -f\ json)
    printf 'No Server found\n' >&2
    exit 1
    ;;
  ambiguous:server\ show\ *\ -f\ json)
    printf 'Multiple matches found\n' >&2
    exit 1
    ;;
  policy:server\ show\ *\ -f\ json)
    printf 'Forbidden\n' >&2
    exit 1
    ;;
  auth:server\ show\ *\ -f\ json)
    printf 'Unauthorized\n' >&2
    exit 1
    ;;
  malformed:server\ show\ *\ -f\ json)
    printf '{not-json\n'
    ;;
  empty:server\ show\ *\ -f\ json)
    printf '{}\n'
    ;;
  redact:server\ show\ *\ -f\ json)
    printf '{"id":"server-1","name":"server-1","status":"ACTIVE","image":{"token":"fixture-token","name":"image-1"},"flavor":"small","addresses":{"net":["192.0.2.10"]},"availability_zone":"nova","config_drive":false,"created":"2025-01-01T00:00:00Z"}\n'
    ;;
  success:server\ show\ *\ -f\ json)
    printf '{"id":"server-1","name":"server-1","status":"ACTIVE","image":"image-1","flavor":"small","addresses":{"net":["192.0.2.10"]},"availability_zone":"nova","config_drive":false,"created":"2025-01-01T00:00:00Z","ignored":"value"}\n'
    ;;
  *)
    printf 'unexpected argv: %s\n' "$*" >&2
    exit 95
    ;;
esac
EOF_FAKE
chmod 0700 "$server_basic_fake_openstack"

run_server_basic() {
  : > "$server_basic_argv_log"
  set +e
  server_basic_output="$(AIOPS_TEST_MODE=fixture AIOPS_TEST_OPENSTACK_BIN="$server_basic_fake_openstack" AIOPS_TEST_JQ_BIN=/usr/bin/jq AIOPS_TEST_ARGV_LOG="$server_basic_argv_log" AIOPS_TEST_SCENARIO="$1" server_basic_info_main "$2")"
  server_basic_status=$?
  set -e
}

run_server_basic success server-1
[[ "$server_basic_status" -eq 0 ]] || fail "successful server read failed"
printf '%s' "$server_basic_output" | /usr/bin/jq -e \
  '.tool == "server_basic_info" and .status == "ok" and .sections[0].name == "server" and .sections[0].status == "ok" and (.sections[0].data | keys == ["addresses", "availability_zone", "config_drive", "created", "flavor", "id", "image", "name", "status"])' \
  >/dev/null || fail "successful server envelope is invalid"
grep -qx 'server show server-1 -f json' "$server_basic_argv_log" || fail "server show argv changed"

run_server_basic empty server-1
[[ "$server_basic_status" -eq 0 ]] || fail "empty server read failed"
printf '%s' "$server_basic_output" | /usr/bin/jq -e '.status == "ok" and .sections[0].status == "empty"' >/dev/null || fail "empty server result is invalid"

for scenario in not_found ambiguous policy auth malformed; do
  run_server_basic "$scenario" server-1
  [[ "$server_basic_status" -eq 4 ]] || fail "server $scenario exit code is incorrect"
  expected_class="$scenario"
  [[ "$scenario" == "policy" ]] && expected_class="policy_denied"
  [[ "$scenario" == "auth" ]] && expected_class="authentication_error"
  [[ "$scenario" == "malformed" ]] && expected_class="execution_error"
  printf '%s' "$server_basic_output" | /usr/bin/jq -e --arg expected_class "$expected_class" \
    '.status == "error" and .error.class == $expected_class and .sections[0].status == "unavailable"' \
    >/dev/null || fail "server $scenario result is invalid"
done

run_server_basic redact server-1
[[ "$server_basic_status" -eq 0 ]] || fail "redacted server read failed"
printf '%s' "$server_basic_output" | /usr/bin/jq -e \
  '.sections[0].data.image.token == "***REDACTED***"' \
  >/dev/null || fail "server secret-like key was not redacted"

for value in '' 'server;id' '../server' 'server/name' "$long_identifier" $'server\n01'; do
  run_server_basic success "$value"
  [[ "$server_basic_status" -eq 2 ]] || fail "invalid server identifier was not rejected"
  [[ ! -s "$server_basic_argv_log" ]] || fail "invalid server identifier reached the fake CLI"
done

: > "$server_basic_argv_log"
set +e
extra_server_output="$(AIOPS_TEST_MODE=fixture AIOPS_TEST_OPENSTACK_BIN="$server_basic_fake_openstack" AIOPS_TEST_JQ_BIN=/usr/bin/jq AIOPS_TEST_ARGV_LOG="$server_basic_argv_log" server_basic_info_main server-1 extra)"
extra_server_status=$?
set -e
[[ "$extra_server_status" -eq 2 ]] || fail "extra server argument was not rejected"
[[ ! -s "$server_basic_argv_log" ]] || fail "extra server argument reached the fake CLI"
printf '%s' "$extra_server_output" | /usr/bin/jq -e '.error.class == "invalid_input"' >/dev/null || fail "extra argument envelope is invalid"

network="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved/server_network_info.sh"
[[ -r "$network" ]] || fail "server network info is missing"
# shellcheck source=../../roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved/server_network_info.sh
source "$network"
network_fake_openstack="$fixture_dir/server-network-openstack"
network_argv_log="$fixture_dir/server-network-argv.log"
cat > "$network_fake_openstack" <<'EOF_FAKE'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$AIOPS_TEST_ARGV_LOG"
case "${AIOPS_TEST_SCENARIO:-success}:$*" in
  not_found:server\ show\ *) printf 'No Server found\n' >&2; exit 1 ;;
  malformed:port\ list\ *) printf '{bad-json\n' ;;
  unavailable_network:network\ show\ *) printf 'Forbidden\n' >&2; exit 1 ;;
  unsafe_derived:port\ list\ *) printf '[{"id":"port-1","network_id":"../bad","fixed_ips":[],"mac_address":"00:00:00:00:00:01","status":"ACTIVE"}]\n' ;;
  no_port:server\ show\ *) printf '{"id":"server-1","name":"server-1","status":"ACTIVE"}\n' ;;
  no_port:port\ list\ *) printf '[]\n' ;;
  *:server\ show\ *) printf '{"id":"server-1","name":"server-1","status":"ACTIVE"}\n' ;;
  *:port\ list\ *) printf '[{"id":"port-1","network_id":"network-1","fixed_ips":[{"subnet_id":"subnet-1","ip_address":"192.0.2.10"}],"mac_address":"00:00:00:00:00:01","status":"ACTIVE"},{"id":"port-2","network_id":"network-2","fixed_ips":[{"subnet_id":"subnet-2","token":"fixture-token"}],"mac_address":"00:00:00:00:00:02","status":"DOWN"}]\n' ;;
  *:network\ show\ network-1\ *) printf '{"id":"network-1","name":"network-1","status":"ACTIVE"}\n' ;;
  *:network\ show\ network-2\ *) printf '{"id":"network-2","name":"network-2","status":"ACTIVE"}\n' ;;
  *:subnet\ show\ subnet-1\ *) printf '{"id":"subnet-1","name":"subnet-1","cidr":"192.0.2.0/24","ip_version":4}\n' ;;
  *:subnet\ show\ subnet-2\ *) printf '{"id":"subnet-2","name":"subnet-2","cidr":"192.0.3.0/24","ip_version":4}\n' ;;
  *) printf 'unexpected argv: %s\n' "$*" >&2; exit 95 ;;
esac
EOF_FAKE
chmod 0700 "$network_fake_openstack"
run_server_network() {
  : > "$network_argv_log"; set +e
  network_output="$(AIOPS_TEST_MODE=fixture AIOPS_TEST_OPENSTACK_BIN="$network_fake_openstack" AIOPS_TEST_JQ_BIN=/usr/bin/jq AIOPS_TEST_ARGV_LOG="$network_argv_log" AIOPS_TEST_SCENARIO="$1" server_network_info_main "$2")"
  network_status=$?; set -e
}
run_server_network success server-1
[[ "$network_status" -eq 0 ]] || fail "successful network read failed"
printf '%s' "$network_output" | /usr/bin/jq -e '.tool == "server_network_info" and .status == "ok" and (.sections | map(.name) == ["server","ports","networks","subnets"]) and (.sections[] | select(.name == "ports").data | length == 2) and (.sections[] | select(.name == "ports").data[1].fixed_ips[0].token == "***REDACTED***")' >/dev/null || fail "network success or redaction result is invalid"
grep -qx 'server show server-1 -f json' "$network_argv_log" || fail "network server argv changed"
grep -qx 'port list --device server-1 -f json' "$network_argv_log" || fail "network port argv changed"
grep -qx 'network show network-1 -f json' "$network_argv_log" || fail "network relationship argv changed"
grep -qx 'subnet show subnet-1 -f json' "$network_argv_log" || fail "subnet relationship argv changed"
for scenario in not_found malformed unsafe_derived unavailable_network; do
  run_server_network "$scenario" server-1
  expected=3; [[ "$scenario" == not_found ]] && expected=4
  [[ "$network_status" -eq "$expected" ]] || fail "network $scenario exit code is incorrect"
done
run_server_network no_port server-1
[[ "$network_status" -eq 0 ]] || fail "no-port network read failed"
printf '%s' "$network_output" | /usr/bin/jq -e '(.sections[] | select(.name == "ports").status == "empty") and ([.sections[] | select(.name == "networks" or .name == "subnets").status] | all(. == "empty"))' >/dev/null || fail "no-port sections are not empty"
: > "$network_argv_log"; set +e
invalid_network_output="$(AIOPS_TEST_MODE=fixture AIOPS_TEST_OPENSTACK_BIN="$network_fake_openstack" AIOPS_TEST_JQ_BIN=/usr/bin/jq AIOPS_TEST_ARGV_LOG="$network_argv_log" server_network_info_main 'server;id')"; invalid_network_status=$?
set -e
[[ "$invalid_network_status" -eq 2 && ! -s "$network_argv_log" ]] || fail "invalid network identifier reached fake CLI"
printf 'diagnostic toolbox helper, project-summary, server-basic, and server-network tests passed\n'
