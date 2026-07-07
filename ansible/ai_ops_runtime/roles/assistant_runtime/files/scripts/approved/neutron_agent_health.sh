#!/usr/bin/env bash
# Neutron agent health availability gate for AI-OPS diagnostics.
#
# This diagnostic requires a separate validated non-default operator-reader
# profile. Until that profile exists, this placeholder fails closed and does
# not select project-reader or invoke OpenStack.

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

if [[ "$#" -ne 0 ]]; then
  aiops_error 64 "neutron_agent_health accepts no arguments while unavailable"
fi

aiops_print_section "neutron_agent_health"
printf '{"status":"unavailable","reason":"operator-reader profile deferred","detail":"no validated non-default operator-reader profile is available for this diagnostic"}\n'
exit 69
