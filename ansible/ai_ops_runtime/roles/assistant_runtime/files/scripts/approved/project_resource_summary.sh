#!/usr/bin/env bash
# Project-visible OpenStack resource summary for AI-OPS diagnostics.
#
# This script uses fixed read-only OpenStack list operations with the default
# aiops-project-reader profile. It accepts no user-selected subcommands.

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

run_read_section() {
  local section_name="$1"
  shift

  aiops_print_section "$section_name"
  if "$AIOPS_OPENSTACK_BIN" "$@" -f json; then
    return 0
  fi

  local exit_code="$?"
  printf '{"status":"unavailable","section":"%s","exit_code":%d}\n' "$section_name" "$exit_code"
  return 1
}

if [[ "$#" -ne 0 ]]; then
  aiops_error 64 "project_resource_summary accepts no arguments"
fi

aiops_use_project_reader_profile

if [[ ! -x "$AIOPS_OPENSTACK_BIN" ]]; then
  aiops_error 69 "OpenStack CLI not found or not executable: $AIOPS_OPENSTACK_BIN"
fi

section_failures=0

run_read_section "servers" server list || section_failures=1
run_read_section "networks" network list || section_failures=1
run_read_section "subnets" subnet list || section_failures=1
run_read_section "ports" port list || section_failures=1
run_read_section "volumes" volume list || section_failures=1
run_read_section "images" image list || section_failures=1
run_read_section "security_groups" security group list || section_failures=1

exit "$section_failures"
