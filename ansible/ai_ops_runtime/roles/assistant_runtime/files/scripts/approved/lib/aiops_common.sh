#!/usr/bin/env bash
# Common helpers for AI-OPS approved diagnostic scripts.
#
# This file is intended to be sourced by reviewed read-only diagnostic scripts.
# It must not perform OpenStack operations or read credential file contents.

aiops_error() {
  local exit_code="${1:-1}"
  local message="${2:-AI-OPS diagnostic helper error}"

  printf 'aiops error: %s\n' "$message" >&2
  exit "$exit_code"
}

aiops_use_project_reader_profile() {
  export OS_CLIENT_CONFIG_FILE="/opt/openstack-ai-ops/credentials/profiles/clouds.yaml"
  export OS_CLOUD="aiops-project-reader"
}

aiops_require_safe_identifier() {
  local value="${1:-}"
  local field_name="${2:-identifier}"

  if [[ -z "$value" ]]; then
    aiops_error 64 "$field_name is required"
  fi

  # Fail closed: allow only a conservative OpenStack name/ID character set.
  # This rejects whitespace, quotes, shell metacharacters, glob characters,
  # path separators, command substitution, and expansion syntax before any
  # diagnostic script can pass the value to the OpenStack CLI.
  case "$value" in
    *[!A-Za-z0-9._:-]*)
      aiops_error 64 "$field_name contains unsafe characters"
      ;;
  esac
}

aiops_print_section() {
  local section_name="${1:-section}"

  printf '\n== %s ==\n' "$section_name"
}
