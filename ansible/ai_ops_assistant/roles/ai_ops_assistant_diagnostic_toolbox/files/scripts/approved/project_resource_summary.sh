#!/usr/bin/env bash
# Project-reader-only summary of approved project-visible resources.

set -u
set -o pipefail

readonly AIOPS_TOOL_NAME="project_resource_summary"
readonly AIOPS_SECTION_RECORD_LIMIT=50
readonly AIOPS_DOCUMENT_MAX_BYTES=1048576

script_path="${BASH_SOURCE[0]}"
script_dir="${script_path%/*}"
if [[ "$script_dir" == "$script_path" ]]; then
  script_dir="."
fi

common_helper="${script_dir}/lib/aiops_common.sh"
if [[ ! -r "$common_helper" ]]; then
  printf 'project_resource_summary: common helper is unavailable\n' >&2
  exit 4
fi
# shellcheck source=lib/aiops_common.sh
if ! declare -F aiops_emit_error >/dev/null; then
  source "$common_helper"
fi

readonly AIOPS_JQ_REDACT='def redact: walk(if type == "object" then with_entries(if (.key | ascii_downcase | test("password|secret|token|credential|private[ _-]?key|authorization")) then .value = "***REDACTED***" else . end) else . end);'

aiops_classify_read_failure() {
  local message="${1,,}"

  case "$message" in
    *forbidden*|*http*403*) printf '%s\n' "policy_denied" ;;
    *service\ unavailable*|*http*503*) printf '%s\n' "service_unavailable" ;;
    *service\ catalog*|*endpoint\ not\ found*) printf '%s\n' "catalog_missing" ;;
    *connection\ refused*|*timed\ out*|*could\ not\ resolve*|*name\ or\ service\ not\ known*|*unreachable*) printf '%s\n' "connectivity_error" ;;
    *authentication*|*unauthorized*|*invalid\ credential*|*token*) printf '%s\n' "authentication_error" ;;
    *) printf '%s\n' "execution_error" ;;
  esac
}

aiops_unavailable_section() {
  local section_name="$1"
  local error_class="$2"
  local jq_bin="$3"

  "$jq_bin" -cn \
    --arg name "$section_name" \
    --arg error_class "$error_class" \
    '{name:$name, status:"unavailable", data:{}, error:{class:$error_class, message:"read unavailable"}, truncated:false}'
}

aiops_project_summary_section=""
aiops_project_summary_failure_class=""
aiops_project_summary_fatal=0

aiops_read_project_summary_section() {
  local section_name="$1"
  local filter="$2"
  shift 2
  local raw rc error_class record_count data section_status truncated

  raw="$("$aiops_project_summary_openstack_bin" "$@" -f json 2>&1)"
  rc=$?
  if [[ "$rc" -eq 0 ]]; then
    if ! record_count="$("$aiops_project_summary_jq_bin" -er 'if type == "array" then length else error("expected array") end' <<<"$raw" 2>/dev/null)"; then
      aiops_project_summary_section="$(aiops_unavailable_section "$section_name" "execution_error" "$aiops_project_summary_jq_bin")" || return 4
      aiops_project_summary_failure_class="execution_error"
      return 0
    fi

    if ! data="$("$aiops_project_summary_jq_bin" -ce "$AIOPS_JQ_REDACT redact | $filter | .[0:$AIOPS_SECTION_RECORD_LIMIT]" <<<"$raw" 2>/dev/null)"; then
      aiops_project_summary_section="$(aiops_unavailable_section "$section_name" "execution_error" "$aiops_project_summary_jq_bin")" || return 4
      aiops_project_summary_failure_class="execution_error"
      return 0
    fi

    if [[ "$record_count" -eq 0 ]]; then
      section_status="empty"
    else
      section_status="ok"
    fi
    if [[ "$record_count" -gt "$AIOPS_SECTION_RECORD_LIMIT" ]]; then
      truncated=true
    else
      truncated=false
    fi

    aiops_project_summary_section="$("$aiops_project_summary_jq_bin" -cn \
      --arg name "$section_name" \
      --arg status "$section_status" \
      --argjson data "$data" \
      --argjson truncated "$truncated" \
      '{name:$name, status:$status, data:$data, error:null, truncated:$truncated}')" || return 4
    aiops_project_summary_failure_class=""
    return 0
  fi

  error_class="$(aiops_classify_read_failure "$raw")"
  aiops_project_summary_section="$(aiops_unavailable_section "$section_name" "$error_class" "$aiops_project_summary_jq_bin")" || return 4
  aiops_project_summary_failure_class="$error_class"
  [[ "$rc" -ne 0 ]] || return 4
  if [[ "$error_class" == "authentication_error" || "$error_class" == "configuration_error" ]]; then
    aiops_project_summary_fatal=1
  fi
}

project_resource_summary_main() {
  local aiops_project_summary_openstack_bin aiops_project_summary_jq_bin
  local section_name filter status top_error document
  local -a sections
  local -a section_specs=(
    'servers|map({id:(.id // .ID), name:(.name // .Name), status:(.status // .Status)})|server|list'
    'networks|map({id, name, status})|network|list'
    'subnets|map({id, name, network_id, cidr, ip_version})|subnet|list'
    'ports|map({id, device_id, network_id, status})|port|list'
    'volumes|map({id, name, status, size})|volume|list'
    'images|map({id, name, status})|image|list'
    'security_groups|map({id, name, status})|security|group|list'
  )
  local -a spec_parts

  if [[ "$#" -ne 0 ]]; then
    aiops_emit_error "$AIOPS_TOOL_NAME" "invalid_input" "project_resource_summary accepts no arguments"
    return 2
  fi

  aiops_project_summary_openstack_bin="$(aiops_openstack_bin)" || {
    aiops_emit_error "$AIOPS_TOOL_NAME" "configuration_error" "OpenStack CLI is unavailable"
    return 4
  }
  aiops_project_summary_jq_bin="$(aiops_jq_bin)" || {
    aiops_emit_error "$AIOPS_TOOL_NAME" "configuration_error" "jq is unavailable"
    return 4
  }
  if [[ ! -x "$aiops_project_summary_openstack_bin" || ! -x "$aiops_project_summary_jq_bin" ]]; then
    aiops_emit_error "$AIOPS_TOOL_NAME" "configuration_error" "required executable is unavailable"
    return 4
  fi

  aiops_use_project_reader_profile
  for section_name in "${section_specs[@]}"; do
    IFS='|' read -r -a spec_parts <<<"$section_name"
    aiops_read_project_summary_section "${spec_parts[0]}" "${spec_parts[1]}" "${spec_parts[@]:2}" || {
      aiops_emit_error "$AIOPS_TOOL_NAME" "execution_error" "section construction failed"
      return 4
    }
    sections+=("$aiops_project_summary_section")
    if [[ -n "$aiops_project_summary_failure_class" ]]; then
      if [[ "$aiops_project_summary_fatal" -eq 1 ]]; then
        break
      fi
      status="partial"
    fi
  done

  if [[ "${status:-}" != "partial" ]]; then
    status="ok"
  fi
  top_error='null'
  if [[ "$aiops_project_summary_fatal" -eq 1 ]]; then
    status="error"
    top_error="$("$aiops_project_summary_jq_bin" -cn --arg error_class "$aiops_project_summary_failure_class" '{class:$error_class, message:"read unavailable"}')"
  fi

  document="$(printf '%s\n' "${sections[@]}" | "$aiops_project_summary_jq_bin" -cs \
    --arg tool "$AIOPS_TOOL_NAME" \
    --arg status "$status" \
    --argjson error "$top_error" \
    '{schema_version:"1.0", tool:$tool, status:$status, sections:., error:$error}')" || {
    aiops_emit_error "$AIOPS_TOOL_NAME" "execution_error" "envelope construction failed"
    return 4
  }
  if [[ "${#document}" -gt "$AIOPS_DOCUMENT_MAX_BYTES" ]]; then
    aiops_emit_error "$AIOPS_TOOL_NAME" "execution_error" "output exceeds the approved bound"
    return 4
  fi

  printf '%s\n' "$document"
  [[ "$status" == "ok" ]] && return 0
  [[ "$status" == "partial" ]] && return 3
  return 4
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  project_resource_summary_main "$@"
fi
