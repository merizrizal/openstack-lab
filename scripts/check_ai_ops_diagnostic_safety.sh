#!/usr/bin/env bash
# Static guardrail for AI-OPS approved diagnostic scripts.
#
# This check scans reviewed shell scripts for obvious unsafe command patterns.
# It is intentionally conservative and does not prove safety; human review is
# still required for false positives and for changes that evade simple patterns.

set -u
set -o pipefail

readonly DEFAULT_APPROVED_DIR="ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved"

if [[ "$#" -gt 1 ]]; then
  printf 'usage: %s [approved-script-directory]\n' "$0" >&2
  exit 64
fi

approved_dir="${1:-$DEFAULT_APPROVED_DIR}"

if [[ ! -d "$approved_dir" ]]; then
  printf 'aiops safety check error: approved script directory not found: %s\n' "$approved_dir" >&2
  exit 66
fi

mapfile -d '' script_files < <(find "$approved_dir" -type f -name '*.sh' -print0)

if [[ "${#script_files[@]}" -eq 0 ]]; then
  printf 'aiops safety check error: no shell scripts found under: %s\n' "$approved_dir" >&2
  exit 66
fi

rule_names=(
  "OpenStack mutation through approved CLI variable"
  "OpenStack mutation through literal openstack command"
  "shell eval"
  "backtick command substitution"
  "unrestricted sudo"
  "raw ssh forwarding"
  "service control"
  "package manager mutation"
  "pip package installation"
  "file mutation commands"
  "in-place sed mutation"
  "tee file write helper"
  "database or RabbitMQ access"
  "generic shell command string"
  "pipe remote download into shell"
)

rule_patterns=(
  'AIOPS_OPENSTACK_BIN.*[[:space:]](add|create|delete|remove|set|unset|update|reboot|rebuild|evacuate|migrate|resize|shelve|unshelve|pause|unpause|suspend|resume|lock|unlock|rescue|unrescue|start|stop|restart)([[:space:]]|$)'
  '(^|[[:space:]])openstack[[:space:]].*[[:space:]](add|create|delete|remove|set|unset|update|reboot|rebuild|evacuate|migrate|resize|shelve|unshelve|pause|unpause|suspend|resume|lock|unlock|rescue|unrescue|start|stop|restart)([[:space:]]|$)'
  '(^|[[:space:];|&])eval([[:space:]]|$)'
  '`[^`]+`'
  '(^|[[:space:];|&])sudo([[:space:]]|$)'
  '(^|[[:space:];|&])ssh([[:space:]]|$)'
  '(^|[[:space:];|&])(systemctl|service)[[:space:]].*(restart|reload|enable|disable|start|stop)'
  '(^|[[:space:];|&])(apt|apt-get|dnf|yum|apk|snap)[[:space:]].*(install|upgrade|remove)'
  '(^|[[:space:];|&])pip[0-9.]*[[:space:]]+install'
  '(^|[[:space:];|&])(rm|mv|cp|touch|chmod|chown|mkdir)([[:space:]]|$)'
  '(^|[[:space:];|&])sed[[:space:]].*-i'
  '(^|[[:space:];|&])tee([[:space:]]|$)'
  '(^|[[:space:];|&])(mysql|psql|rabbitmqctl)([[:space:]]|$)'
  '(^|[[:space:];|&])(bash|sh)[[:space:]]+-c[[:space:]]'
  '(^|[[:space:];|&])curl[[:space:]].*\|[[:space:]]*(bash|sh)'
)

violations=0

for script_file in "${script_files[@]}"; do
  if ! bash -n "$script_file"; then
    printf 'aiops safety check violation: shell syntax failed: %s\n' "$script_file" >&2
    violations=1
  fi

  for i in "${!rule_patterns[@]}"; do
    matches="$(grep -nE "${rule_patterns[$i]}" "$script_file" | grep -vE '^[^:]+:[[:space:]]*#' || true)"
    if [[ -n "$matches" ]]; then
      printf 'aiops safety check violation: %s in %s\n' "${rule_names[$i]}" "$script_file" >&2
      printf '%s\n' "$matches" >&2
      violations=1
    fi
  done
done

if [[ "$violations" -ne 0 ]]; then
  printf 'aiops safety check failed. Review matches manually before trusting scripts.\n' >&2
  exit 1
fi

printf 'aiops safety check passed: %d shell script(s) scanned under %s\n' "${#script_files[@]}" "$approved_dir"
