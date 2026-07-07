#!/usr/bin/env bash
# Single-server OpenStack network evidence for AI-OPS diagnostics.
#
# This script uses fixed read-only OpenStack show/list operations with the
# default aiops-project-reader profile. It accepts only one validated server
# name or ID and does not expose arbitrary OpenStack subcommands.
#
# First version note: per-port network/subnet show expansion by parsed IDs is
# intentionally deferred until runtime output shape is validated. The script
# emits raw JSON sections for server summary, server ports, and project-visible
# network/subnet context so operators can correlate IDs without brittle parsing.

set -u
set -o pipefail

script_path="${BASH_SOURCE[0]}"
script_dir="${script_path%/*}"
if [[ "$script_dir" == "$script_path" ]]; then
  script_dir="."
fi

common_helper="${script_dir}/lib/aiops_common.sh"
if [[ ! -r "$common_helper" ]]; then
  printf 'aiops error: common helper not found: %s\n' "$common_helper" >&2
  exit 70
fi

# shellcheck source=lib/aiops_common.sh
source "$common_helper"

readonly AIOPS_OPENSTACK_BIN="/opt/openstack-ai-ops/.venv/bin/openstack"

run_optional_read_section() {
  local section_name="$1"
  shift

  aiops_print_section "$section_name"
  "$AIOPS_OPENSTACK_BIN" "$@" -f json
  local exit_code="$?"
  if [[ "$exit_code" -eq 0 ]]; then
    return 0
  fi

  printf '{"status":"unavailable","section":"%s","exit_code":%d}\n' "$section_name" "$exit_code"
  return 1
}

if [[ "$#" -ne 1 ]]; then
  aiops_error 64 "server_network_info requires exactly one server name or ID"
fi

server_identifier="$1"
aiops_require_safe_identifier "$server_identifier" "server identifier"
aiops_use_project_reader_profile

if [[ ! -x "$AIOPS_OPENSTACK_BIN" ]]; then
  aiops_error 69 "OpenStack CLI not found or not executable: $AIOPS_OPENSTACK_BIN"
fi

aiops_print_section "server_summary"
"$AIOPS_OPENSTACK_BIN" server show "$server_identifier" -f json
server_show_status="$?"
if [[ "$server_show_status" -ne 0 ]]; then
  exit "$server_show_status"
fi

section_failures=0

run_optional_read_section "server_ports" port list --server "$server_identifier" || section_failures=1
run_optional_read_section "project_visible_networks_for_correlation" network list || section_failures=1
run_optional_read_section "project_visible_subnets_for_correlation" subnet list || section_failures=1

exit "$section_failures"
