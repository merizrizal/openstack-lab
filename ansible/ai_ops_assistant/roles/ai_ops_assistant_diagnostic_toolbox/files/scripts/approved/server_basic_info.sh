#!/usr/bin/env bash
# Project-reader-only basic information for one requested server.

set -u
set -o pipefail

readonly AIOPS_SERVER_BASIC_TOOL_NAME="server_basic_info"
readonly AIOPS_SERVER_BASIC_DOCUMENT_MAX_BYTES=1048576

script_path="${BASH_SOURCE[0]}"
script_dir="${script_path%/*}"
if [[ "$script_dir" == "$script_path" ]]; then
  script_dir="."
fi

common_helper="${script_dir}/lib/aiops_common.sh"
if [[ ! -r "$common_helper" ]]; then
  printf 'server_basic_info: common helper is unavailable\n' >&2
  exit 4
fi
# shellcheck source=lib/aiops_common.sh
if ! declare -F aiops_emit_error >/dev/null; then
  source "$common_helper"
fi

readonly AIOPS_SERVER_BASIC_JQ_REDACT='def redact: walk(if type == "object" then with_entries(if (.key | ascii_downcase | test("password|secret|token|credential|private[ _-]?key|authorization")) then .value = "***REDACTED***" else . end) else . end);'

aiops_server_basic_classify_failure() {
  local message="${1,,}"

  case "$message" in
    *not\ found*|*no\ server\ found*|*http*404*) printf '%s\n' "not_found" ;;
    *more\ than\ one*|*multiple\ matches*|*ambiguous*) printf '%s\n' "ambiguous" ;;
    *forbidden*|*http*403*) printf '%s\n' "policy_denied" ;;
    *service\ unavailable*|*http*503*) printf '%s\n' "service_unavailable" ;;
    *service\ catalog*|*endpoint\ not\ found*) printf '%s\n' "catalog_missing" ;;
    *connection\ refused*|*timed\ out*|*could\ not\ resolve*|*name\ or\ service\ not\ known*|*unreachable*) printf '%s\n' "connectivity_error" ;;
    *authentication*|*unauthorized*|*invalid\ credential*|*token*) printf '%s\n' "authentication_error" ;;
    *) printf '%s\n' "execution_error" ;;
  esac
}

aiops_server_basic_error_document() {
  local jq_bin="$1"
  local error_class="$2"

  "$jq_bin" -cn \
    --arg tool "$AIOPS_SERVER_BASIC_TOOL_NAME" \
    --arg error_class "$error_class" \
    '{schema_version:"1.0", tool:$tool, status:"error", sections:[{name:"server", status:"unavailable", data:{}, error:{class:$error_class, message:"read unavailable"}, truncated:false}], error:{class:$error_class, message:"read unavailable"}}'
}

server_basic_info_main() {
  local identifier aiops_server_basic_openstack_bin aiops_server_basic_jq_bin
  local raw rc error_class data section_status document

  if [[ "$#" -ne 1 ]] || ! aiops_require_safe_identifier "${1:-}" "server identifier"; then
    aiops_emit_error "$AIOPS_SERVER_BASIC_TOOL_NAME" "invalid_input" "server_basic_info requires one valid server identifier"
    return 2
  fi
  identifier="$1"

  aiops_server_basic_openstack_bin="$(aiops_openstack_bin)" || {
    aiops_emit_error "$AIOPS_SERVER_BASIC_TOOL_NAME" "configuration_error" "OpenStack CLI is unavailable"
    return 4
  }
  aiops_server_basic_jq_bin="$(aiops_jq_bin)" || {
    aiops_emit_error "$AIOPS_SERVER_BASIC_TOOL_NAME" "configuration_error" "jq is unavailable"
    return 4
  }
  if [[ ! -x "$aiops_server_basic_openstack_bin" || ! -x "$aiops_server_basic_jq_bin" ]]; then
    aiops_emit_error "$AIOPS_SERVER_BASIC_TOOL_NAME" "configuration_error" "required executable is unavailable"
    return 4
  fi

  aiops_use_project_reader_profile
  raw="$("$aiops_server_basic_openstack_bin" server show "$identifier" -f json 2>&1)"
  rc=$?
  if [[ "$rc" -ne 0 ]]; then
    error_class="$(aiops_server_basic_classify_failure "$raw")"
    document="$(aiops_server_basic_error_document "$aiops_server_basic_jq_bin" "$error_class")" || return 4
    printf '%s\n' "$document"
    return 4
  fi

  if ! data="$("$aiops_server_basic_jq_bin" -ce "$AIOPS_SERVER_BASIC_JQ_REDACT redact | if type == \"object\" then ({id, name, status, image, flavor, addresses, availability_zone, config_drive, created} | with_entries(select(.value != null))) else error(\"expected object\") end" <<<"$raw" 2>/dev/null)"; then
    document="$(aiops_server_basic_error_document "$aiops_server_basic_jq_bin" "execution_error")" || return 4
    printf '%s\n' "$document"
    return 4
  fi

  if [[ "$data" == "{}" ]]; then
    section_status="empty"
  else
    section_status="ok"
  fi
  document="$("$aiops_server_basic_jq_bin" -cn \
    --arg tool "$AIOPS_SERVER_BASIC_TOOL_NAME" \
    --arg status "$section_status" \
    --argjson data "$data" \
    '{schema_version:"1.0", tool:$tool, status:"ok", sections:[{name:"server", status:$status, data:$data, error:null, truncated:false}], error:null}')" || {
    aiops_emit_error "$AIOPS_SERVER_BASIC_TOOL_NAME" "execution_error" "envelope construction failed"
    return 4
  }
  if [[ "${#document}" -gt "$AIOPS_SERVER_BASIC_DOCUMENT_MAX_BYTES" ]]; then
    aiops_emit_error "$AIOPS_SERVER_BASIC_TOOL_NAME" "execution_error" "output exceeds the approved bound"
    return 4
  fi

  printf '%s\n' "$document"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  server_basic_info_main "$@"
fi
