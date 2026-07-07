#!/usr/bin/env bash
# Single-server OpenStack basic info for AI-OPS diagnostics.
#
# This script uses one fixed read-only OpenStack server show operation with the
# default aiops-project-reader profile. It accepts only one validated server
# name or ID and does not expose arbitrary OpenStack subcommands.

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

if [[ "$#" -ne 1 ]]; then
  aiops_error 64 "server_basic_info requires exactly one server name or ID"
fi

server_identifier="$1"
aiops_require_safe_identifier "$server_identifier" "server identifier"
aiops_use_project_reader_profile

if [[ ! -x "$AIOPS_OPENSTACK_BIN" ]]; then
  aiops_error 69 "OpenStack CLI not found or not executable: $AIOPS_OPENSTACK_BIN"
fi

"$AIOPS_OPENSTACK_BIN" server show "$server_identifier" -f json
exit "$?"
