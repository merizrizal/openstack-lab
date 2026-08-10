#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_validate_host_observer_scope.yml"
role_defaults="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_host_observer_boundary/defaults/main.yml"
role_tasks="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_host_observer_boundary/tasks/main.yml"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

for path in "$playbook" "$role_defaults" "$role_tasks"; do
  [[ -f "$path" && ! -L "$path" ]] || fail "observer policy artifact is missing or symlinked: $path"
done

grep -Fq 'hosts: ai_ops_host_observers' "$playbook"
grep -Fq 'connection: local' "$playbook"
grep -Fq 'serial: 1' "$playbook"
grep -Fq 'ai_ops_assistant_host_observer_boundary_enabled: false' "$playbook"
grep -Fq 'ai_ops_assistant_host_observer_boundary_validation_mode: true' "$playbook"
grep -Fq 'ai_ops_assistant_host_observer_boundary_deployment_authorization: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_host_observer_boundary_required_inventory_group: ai_ops_host_observers' "$playbook"
grep -Fq 'ai_ops_assistant_host_observer_boundary_required_limit: ai_ops_host_observers' "$playbook"
grep -Fq "ansible_limit | default('') == ai_ops_assistant_host_observer_boundary_required_limit" "$playbook"
grep -Fq "'ai_ops_host_observers' in group_names" "$playbook"
grep -Fq 'ai_ops_assistant_host_observer_boundary_live_validation_authorization: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_host_observer_boundary_negative_test_plan_authorization: unconfirmed' "$playbook"
grep -Fq 'ai_ops_assistant_host_observer_boundary_host_destination_override: ""' "$playbook"
grep -Fq 'ai_ops_assistant_host_observer_boundary_per_host_disablement_outcomes: {}' "$playbook"
grep -Fq 'case: approved_fixed_collector' "$playbook"
grep -Fq 'collector_path: /usr/local/libexec/openstack-ai-ops-assistant/host-observer-collector' "$playbook"
grep -Fq 'output_contract: bounded-redacted-structured' "$playbook"
grep -Fq 'result: unconfirmed' "$playbook"
grep -Fq 'ansible_play_hosts_all | difference(ai_ops_assistant_host_observer_boundary_allowed_host_labels)' "$playbook"
grep -Fq 'ai_ops_assistant_host_observer_boundary_per_host_enablement[inventory_hostname]' "$playbook"
grep -Fq 'per_host_disablement_outcomes[inventory_hostname].owner' "$playbook"
grep -Fq 'per_host_disablement_outcomes[inventory_hostname].procedure' "$playbook"
grep -Fq 'when: ai_ops_assistant_host_observer_boundary_enabled | bool' "$playbook"
grep -Fq 'ansible.builtin.set_fact:' "$playbook"
grep -Fq 'status: blocked' "$playbook"
grep -Fq 'limitation_class: authorization_pending' "$playbook"
grep -Fq 'no_log: true' "$playbook"
grep -Fq 'role: ai_ops_assistant_host_observer_boundary' "$playbook"

grep -Fq 'no-agent-forwarding' "$role_defaults"
grep -Fq 'no-X11-forwarding' "$role_defaults"
grep -Fq 'no-port-forwarding' "$role_defaults"
grep -Fq 'no-pty' "$role_defaults"
grep -Fq 'Require approved observer policy before any provisioning task' "$role_tasks"
grep -Fq 'Keep host-observer provisioning unavailable' "$role_tasks"

for case in \
  interactive_shell \
  pty_allocation \
  agent_forwarding \
  x11_forwarding \
  local_forwarding \
  remote_forwarding \
  tunnel_request \
  arbitrary_command \
  extra_arguments \
  environment_injection \
  destination_bypass \
  out_of_policy_file_read \
  editor_execution \
  package_manager_execution \
  service_control \
  unrestricted_sudo \
  alternate_sudo_arguments \
  collector_output_redirection; do
  grep -Fq "case: $case" "$playbook" || fail "negative observer case is missing: $case"
done

if grep -nE '(^|[[:space:]])hosts: all|ansible\.builtin\.(shell|command|raw|expect|user|authorized_key|copy|template|file|service|package)|(^|[[:space:]])(ssh|scp|sftp|sudo)([[:space:]]|$)|ansible\.builtin\.debug|ai_ops_runtime|private\.key' "$playbook"; then
  fail "generic host access, mutation, raw output, historical reuse, or sensitive handling found"
fi

if grep -nE '^    ai_ops_assistant_host_observer_boundary_enabled: true|^    ai_ops_assistant_host_observer_boundary_.*authorization: approved|^    ai_ops_assistant_host_observer_boundary_inventory_projection_status: accepted|^        result: (passed|accepted)' "$playbook"; then
  fail "observer entrypoint contains success-shaped gate defaults"
fi

printf 'Host-observer policy/scoped-entrypoint static harness test passed\n'
