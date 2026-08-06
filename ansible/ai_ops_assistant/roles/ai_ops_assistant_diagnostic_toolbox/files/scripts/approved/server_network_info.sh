#!/usr/bin/env bash
# Project-reader-only network attachment context for one requested server.
set -u
set -o pipefail

readonly AIOPS_SERVER_NETWORK_TOOL_NAME="server_network_info"
readonly AIOPS_SERVER_NETWORK_RECORD_LIMIT=50
readonly AIOPS_SERVER_NETWORK_DOCUMENT_MAX_BYTES=1048576
readonly AIOPS_SERVER_NETWORK_REDACT='def redact: walk(if type == "object" then with_entries(if (.key | ascii_downcase | test("password|secret|token|credential|private[ _-]?key|authorization")) then .value = "***REDACTED***" else . end) else . end);'

script_path="${BASH_SOURCE[0]}"
script_dir="${script_path%/*}"
[[ "$script_dir" == "$script_path" ]] && script_dir="."
common_helper="${script_dir}/lib/aiops_common.sh"
[[ -r "$common_helper" ]] || { printf 'server_network_info: common helper is unavailable\n' >&2; exit 4; }
# shellcheck source=lib/aiops_common.sh
if ! declare -F aiops_emit_error >/dev/null; then source "$common_helper"; fi

aiops_server_network_classify_failure() {
  case "${1,,}" in
    *not\ found*|*no\ server\ found*|*http*404*) printf '%s\n' not_found ;;
    *more\ than\ one*|*multiple\ matches*|*ambiguous*) printf '%s\n' ambiguous ;;
    *forbidden*|*http*403*) printf '%s\n' policy_denied ;;
    *service\ unavailable*|*http*503*) printf '%s\n' service_unavailable ;;
    *service\ catalog*|*endpoint\ not\ found*) printf '%s\n' catalog_missing ;;
    *connection\ refused*|*timed\ out*|*could\ not\ resolve*|*unreachable*) printf '%s\n' connectivity_error ;;
    *authentication*|*unauthorized*|*invalid\ credential*|*token*) printf '%s\n' authentication_error ;;
    *) printf '%s\n' execution_error ;;
  esac
}

aiops_server_network_unavailable() {
  "$1" -cn --arg name "$2" --arg error_class "$3" \
    '{name:$name,status:"unavailable",data:[],error:{class:$error_class,message:"read unavailable"},truncated:false}'
}

aiops_server_network_error() {
  "$1" -cn --arg tool "$AIOPS_SERVER_NETWORK_TOOL_NAME" --arg error_class "$2" \
    '{schema_version:"1.0",tool:$tool,status:"error",sections:[],error:{class:$error_class,message:"read unavailable"}}'
}

aiops_server_network_read() {
  local section="$1" filter="$2"; shift 2
  local raw rc count data status truncated error_class
  raw="$("$aiops_server_network_openstack_bin" "$@" -f json 2>&1)"; rc=$?
  if [[ "$rc" -ne 0 ]]; then
    error_class="$(aiops_server_network_classify_failure "$raw")"
    aiops_server_network_section="$(aiops_server_network_unavailable "$aiops_server_network_jq_bin" "$section" "$error_class")"
    aiops_server_network_failure="$error_class"; return 0
  fi
  if ! count="$("$aiops_server_network_jq_bin" -er 'if type == "array" then length else error("expected array") end' <<<"$raw" 2>/dev/null)" ||
     ! data="$("$aiops_server_network_jq_bin" -ce "$AIOPS_SERVER_NETWORK_REDACT redact | $filter | .[0:$AIOPS_SERVER_NETWORK_RECORD_LIMIT]" <<<"$raw" 2>/dev/null)"; then
    aiops_server_network_section="$(aiops_server_network_unavailable "$aiops_server_network_jq_bin" "$section" execution_error)"
    aiops_server_network_failure=execution_error; return 0
  fi
  [[ "$count" -eq 0 ]] && status=empty || status=ok
  [[ "$count" -gt "$AIOPS_SERVER_NETWORK_RECORD_LIMIT" ]] && truncated=true || truncated=false
  aiops_server_network_section="$("$aiops_server_network_jq_bin" -cn --arg name "$section" --arg status "$status" --argjson data "$data" --argjson truncated "$truncated" '{name:$name,status:$status,data:$data,error:null,truncated:$truncated}')"
  aiops_server_network_failure=""
}

server_network_info_main() {
  local identifier raw rc server_data server_id ports_data document status top_error id lookup_section
  local -a sections network_ids subnet_ids
  if [[ "$#" -ne 1 ]] || ! aiops_require_safe_identifier "${1:-}" "server identifier"; then
    aiops_emit_error "$AIOPS_SERVER_NETWORK_TOOL_NAME" invalid_input "server_network_info requires one valid server identifier"; return 2
  fi
  identifier="$1"
  aiops_server_network_openstack_bin="$(aiops_openstack_bin)" || { aiops_emit_error "$AIOPS_SERVER_NETWORK_TOOL_NAME" configuration_error "OpenStack CLI is unavailable"; return 4; }
  aiops_server_network_jq_bin="$(aiops_jq_bin)" || { aiops_emit_error "$AIOPS_SERVER_NETWORK_TOOL_NAME" configuration_error "jq is unavailable"; return 4; }
  [[ -x "$aiops_server_network_openstack_bin" && -x "$aiops_server_network_jq_bin" ]] || { aiops_emit_error "$AIOPS_SERVER_NETWORK_TOOL_NAME" configuration_error "required executable is unavailable"; return 4; }
  aiops_use_project_reader_profile

  raw="$("$aiops_server_network_openstack_bin" server show "$identifier" -f json 2>&1)"; rc=$?
  if [[ "$rc" -ne 0 ]]; then
    aiops_server_network_error "$aiops_server_network_jq_bin" "$(aiops_server_network_classify_failure "$raw")"; return 4
  fi
  if ! server_data="$("$aiops_server_network_jq_bin" -ce "$AIOPS_SERVER_NETWORK_REDACT redact | if type == \"object\" then ({id,name,status}|with_entries(select(.value != null))) else error(\"expected object\") end" <<<"$raw" 2>/dev/null)" ||
     ! server_id="$("$aiops_server_network_jq_bin" -er '.id | strings' <<<"$raw" 2>/dev/null)" ||
     ! aiops_require_safe_identifier "$server_id" "derived server identifier"; then
    aiops_server_network_error "$aiops_server_network_jq_bin" execution_error; return 4
  fi
  sections+=("$("$aiops_server_network_jq_bin" -cn --argjson data "$server_data" '{name:"server",status:"ok",data:$data,error:null,truncated:false}')")

  aiops_server_network_read ports 'map({id,network_id,fixed_ips,mac_address,status})' port list --device "$server_id"
  sections+=("$aiops_server_network_section")
  [[ -n "$aiops_server_network_failure" ]] && status=partial
  if [[ -z "$aiops_server_network_failure" ]]; then
    ports_data="$("$aiops_server_network_jq_bin" -re '.data[].network_id? // empty' <<<"$aiops_server_network_section" 2>/dev/null || true)"
    while IFS= read -r id; do [[ -n "$id" ]] && network_ids+=("$id"); done <<<"$ports_data"
    ports_data="$("$aiops_server_network_jq_bin" -re '.data[].fixed_ips[]?.subnet_id? // empty' <<<"$aiops_server_network_section" 2>/dev/null || true)"
    while IFS= read -r id; do [[ -n "$id" ]] && subnet_ids+=("$id"); done <<<"$ports_data"
  fi

  for lookup_section in networks subnets; do
    local -a ids=()
    [[ "$lookup_section" == networks ]] && ids=("${network_ids[@]}") || ids=("${subnet_ids[@]}")
    local -a values=(); local failure=""
    for id in "${ids[@]}"; do
      if ! aiops_require_safe_identifier "$id" "derived ${lookup_section} identifier"; then failure=execution_error; break; fi
      raw="$("$aiops_server_network_openstack_bin" "${lookup_section%?}" show "$id" -f json 2>&1)"; rc=$?
      if [[ "$rc" -ne 0 ]]; then failure="$(aiops_server_network_classify_failure "$raw")"; break; fi
      if [[ "$lookup_section" == networks ]]; then
        lookup_section_data='if type == "object" then ({id,name,status}|with_entries(select(.value != null))) else error("expected object") end'
      else
        lookup_section_data='if type == "object" then ({id,name,cidr,ip_version}|with_entries(select(.value != null))) else error("expected object") end'
      fi
      if ! lookup_section_data="$("$aiops_server_network_jq_bin" -ce "$AIOPS_SERVER_NETWORK_REDACT redact | $lookup_section_data" <<<"$raw" 2>/dev/null)"; then failure=execution_error; break; fi
      values+=("$lookup_section_data")
    done
    if [[ -n "$failure" ]]; then
      sections+=("$(aiops_server_network_unavailable "$aiops_server_network_jq_bin" "$lookup_section" "$failure")"); status=partial
    else
      document="$(printf '%s\n' "${values[@]:-}" | "$aiops_server_network_jq_bin" -cs 'map(select(. != null))')"
      [[ "$document" == '[]' ]] && lookup_status=empty || lookup_status=ok
      sections+=("$("$aiops_server_network_jq_bin" -cn --arg name "$lookup_section" --arg status "$lookup_status" --argjson data "$document" '{name:$name,status:$status,data:$data,error:null,truncated:false}')")
    fi
  done
  [[ "${status:-}" == partial ]] || status=ok
  document="$(printf '%s\n' "${sections[@]}" | "$aiops_server_network_jq_bin" -cs --arg tool "$AIOPS_SERVER_NETWORK_TOOL_NAME" --arg status "$status" '{schema_version:"1.0",tool:$tool,status:$status,sections:.,error:null}')" || return 4
  [[ "${#document}" -le "$AIOPS_SERVER_NETWORK_DOCUMENT_MAX_BYTES" ]] || { aiops_emit_error "$AIOPS_SERVER_NETWORK_TOOL_NAME" execution_error "output exceeds the approved bound"; return 4; }
  printf '%s\n' "$document"; [[ "$status" == ok ]] && return 0 || return 3
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then server_network_info_main "$@"; fi
