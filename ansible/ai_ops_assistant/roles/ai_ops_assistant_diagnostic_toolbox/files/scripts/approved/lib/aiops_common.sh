#!/usr/bin/env bash
# Shared contracts for revised AI-OPS manual diagnostics.
# This helper never invokes OpenStack or reads profile contents.

readonly AIOPS_OPENSTACK_BIN="/usr/bin/openstack"
readonly AIOPS_JQ_BIN="/usr/local/bin/jq"
readonly AIOPS_PROJECT_READER_PROFILE="aiops-assistant-project-reader"
readonly AIOPS_PROJECT_READER_CONFIG="/opt/openstack-ai-ops-assistant/credentials/profiles/clouds.yaml"
readonly AIOPS_IDENTIFIER_MAX_BYTES=255
readonly AIOPS_ERROR_MESSAGE_MAX_CHARS=512

aiops_fixture_mode_enabled() {
  local source_path

  [[ "${AIOPS_TEST_MODE:-}" == "fixture" ]] || return 1
  for source_path in "${BASH_SOURCE[@]:1}"; do
    [[ "$source_path" == */ansible/ai_ops_assistant/tests/diagnostic_toolbox/* || "$source_path" == ansible/ai_ops_assistant/tests/diagnostic_toolbox/* ]] && return 0
  done
  return 1
}

aiops_jq_bin() {
  if aiops_fixture_mode_enabled; then
    [[ -n "${AIOPS_TEST_JQ_BIN:-}" && -x "${AIOPS_TEST_JQ_BIN}" ]] || return 4
    printf '%s\n' "$AIOPS_TEST_JQ_BIN"
    return 0
  fi

  printf '%s\n' "$AIOPS_JQ_BIN"
}

aiops_openstack_bin() {
  if aiops_fixture_mode_enabled; then
    [[ -n "${AIOPS_TEST_OPENSTACK_BIN:-}" && -x "${AIOPS_TEST_OPENSTACK_BIN}" ]] || return 4
    printf '%s\n' "$AIOPS_TEST_OPENSTACK_BIN"
    return 0
  fi

  printf '%s\n' "$AIOPS_OPENSTACK_BIN"
}

aiops_use_project_reader_profile() {
  unset OS_AUTH_URL OS_AUTH_TYPE OS_USERNAME OS_PASSWORD OS_PROJECT_NAME OS_PROJECT_ID
  unset OS_USER_DOMAIN_NAME OS_PROJECT_DOMAIN_NAME OS_TOKEN
  unset OS_APPLICATION_CREDENTIAL_ID OS_APPLICATION_CREDENTIAL_SECRET
  export OS_CLIENT_CONFIG_FILE="$AIOPS_PROJECT_READER_CONFIG"
  export OS_CLOUD="$AIOPS_PROJECT_READER_PROFILE"
}

aiops_require_safe_identifier() {
  local value="${1:-}"

  [[ "$#" -eq 2 ]] || return 2
  [[ -n "$value" ]] || return 2
  [[ "${#value}" -le "$AIOPS_IDENTIFIER_MAX_BYTES" ]] || return 2
  [[ "$value" != *..* ]] || return 2
  [[ "$value" != */* ]] || return 2
  [[ "$value" =~ ^[A-Za-z0-9._:-]+$ ]] || return 2
}

aiops_bound_message() {
  local message="${1:-}"
  printf '%s' "${message:0:AIOPS_ERROR_MESSAGE_MAX_CHARS}"
}

aiops_emit_error() {
  local tool="${1:-}"
  local error_class="${2:-execution_error}"
  local message
  local jq_bin

  [[ "$#" -eq 3 && -n "$tool" ]] || return 4
  message="$(aiops_bound_message "$3")"
  jq_bin="$(aiops_jq_bin)" || return 4

  "$jq_bin" -cn \
    --arg tool "$tool" \
    --arg error_class "$error_class" \
    --arg message "$message" \
    '{schema_version:"1.0", tool:$tool, status:"error", sections:[], error:{class:$error_class, message:$message}}'
}

aiops_run_read_section() {
  local tool="${1:-}"
  local section="${2:-}"

  [[ "$#" -ge 2 && -n "$tool" && -n "$section" ]] || return 4
  aiops_emit_error "$tool" "execution_error" "not_implemented"
  return 4
}
