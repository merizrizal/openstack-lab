#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
playbook="$repo_root/ansible/ai_ops_assistant/playbook_deploy_host_observer.yml"
inventory="$repo_root/ansible/ai_ops_assistant/inventories/local/local.yml"
role_defaults="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_host_observer_boundary/defaults/main.yml"
role_tasks="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_host_observer_boundary/tasks/main.yml"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

for path in "$playbook" "$inventory" "$role_defaults" "$role_tasks"; do
  [[ -f "$path" && ! -L "$path" ]] || fail "observer provisioning artifact is missing or symlinked: $path"
done

grep -Fq 'hosts: ai_ops_host_observers' "$playbook"
grep -Fq 'serial: 1' "$playbook"
grep -Fq 'ansible_play_batch | length == 1' "$playbook"
grep -Fq 'ai_ops_assistant_host_observer_boundary_enabled: false' "$playbook"
grep -Fq 'ai_ops_assistant_host_observer_boundary_lifecycle_action: present' "$playbook"
grep -Fq 'deployment_authorization: unconfirmed' "$playbook"
grep -Fq 'disablement_authorization: unconfirmed' "$playbook"
grep -Fq 'removal_authorization: unconfirmed' "$playbook"
grep -Fq "lifecycle_action != 'present'" "$playbook"
grep -Fq 'ai_ops_host_observers:' "$inventory"
grep -Fq 'controller01:' "$inventory"
grep -Fq 'compute01:' "$inventory"
grep -Fq 'compute02:' "$inventory"

grep -Fq 'ai_ops_assistant_host_observer_boundary_lifecycle_action in [' "$role_tasks"
grep -Fq 'Ensure observer account group is present' "$role_tasks"
grep -Fq 'Ensure observer account is present with a non-interactive shell' "$role_tasks"
grep -Fq 'ansible.posix.authorized_key:' "$role_tasks"
grep -Fq 'exclusive: true' "$role_tasks"
grep -Fq "ssh-ed25519 [A-Za-z0-9" "$role_tasks"
grep -Fq 'Assert fixed observer policy directory metadata' "$role_tasks"
grep -Fq 'no-agent-forwarding' "$role_defaults"
grep -Fq 'no-X11-forwarding' "$role_defaults"
grep -Fq 'no-port-forwarding' "$role_defaults"
grep -Fq 'no-pty' "$role_defaults"
grep -Fq 'from="{{ ai_ops_assistant_host_observer_boundary_ssh_source_restriction }}"' "$role_tasks"
grep -Fq 'command="{{ ai_ops_assistant_host_observer_boundary_forced_command }}"' "$role_tasks"
grep -Fq "is match('^((25[0-5]" "$role_tasks"
grep -Fq 'collector_policy_source.startswith' "$role_tasks"
grep -Fq 'Materialize owner-supplied host-observer policy' "$role_tasks"
grep -Fq 'Materialize owner-supplied observer inventory projection' "$role_tasks"
grep -Fq 'remote_src: true' "$role_tasks"
grep -Fq 'Require independently authorized host-observer disablement' "$role_tasks"
grep -Fq 'Require independently authorized host-observer removal' "$role_tasks"
grep -Fq 'Remove observer account and dedicated group' "$role_tasks"
grep -Fq 'no_log: true' "$role_tasks"
grep -Fq 'sudo_required: false' "$role_defaults"

if grep -nE 'ansible\.builtin\.(shell|command|raw|expect|slurp|debug)|(^|[[:space:]])(ssh|scp|sftp)([[:space:]]|$)|private[._ -]?key|secret' "$playbook" "$role_tasks"; then
  fail "unsafe execution or protected-content handling found in observer provisioning"
fi

if grep -nE '^    ai_ops_assistant_host_observer_boundary_.*authorization: approved|^    ai_ops_assistant_host_observer_boundary_enabled: true|^    ai_ops_assistant_host_observer_boundary_inventory_projection_status: accepted' "$playbook"; then
  fail "observer deployment entrypoint contains success-shaped defaults"
fi

printf 'Host-observer provisioning static test passed\n'
