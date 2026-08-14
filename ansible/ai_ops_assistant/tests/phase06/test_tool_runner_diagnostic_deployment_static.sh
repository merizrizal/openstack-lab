#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
runner_defaults="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/defaults/main.yml"
runner_tasks="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/tasks/main.yml"
runner_source="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/aiops_tool_runner.py"
registry="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/tool_registry.json"
diagnostic_defaults="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox/defaults/main.yml"
diagnostic_tasks="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox/tasks/main.yml"
diagnostic_source="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved/neutron_agent_health.py"
validation_playbook="$repo_root/ansible/ai_ops_assistant/playbook_produce_restricted_diagnostics_validation.yml"
connector_source="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/host_observer_connector.py"
observer_defaults="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_host_observer_boundary/defaults/main.yml"
observer_tasks="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_host_observer_boundary/tasks/main.yml"
observer_collector="$repo_root/ansible/ai_ops_assistant/roles/ai_ops_assistant_host_observer_boundary/files/scripts/host_observer/host_observer_collector.py"
workflow_test="$repo_root/ansible/ai_ops_assistant/tests/phase06/test_metadata_workflow_static.py"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

for path in \
  "$runner_defaults" \
  "$runner_tasks" \
  "$runner_source" \
  "$registry" \
  "$diagnostic_defaults" \
  "$diagnostic_tasks" \
  "$diagnostic_source" \
  "$validation_playbook" \
  "$connector_source" \
  "$observer_defaults" \
  "$observer_tasks" \
  "$observer_collector" \
  "$workflow_test"; do
  [[ -f "$path" && ! -L "$path" ]] || fail "required static artifact is missing or symlinked: $path"
done

grep -Fq 'ai_ops_assistant_tool_runner_enabled: false' "$runner_defaults"
grep -Fq 'ai_ops_assistant_tool_runner_explicit_deployment' "$runner_tasks"
grep -Fq '/opt/openstack-ai-ops-assistant/scripts/approved/neutron_agent_health.py' "$runner_defaults"
grep -Fq "'/neutron_agent_health.py'" "$runner_tasks"
grep -Fq "'aiops_tool_runner.py', 'audit_inspector.py', 'host_observer_connector.py'" "$runner_tasks"
grep -Fq 'host_observer_connector.py' "$runner_defaults"
grep -Fq "item.stat.pw_name == 'root'" "$runner_tasks"
grep -Fq 'item.stat.mode == item.item.mode' "$runner_tasks"
grep -Fq 'follow: false' "$runner_tasks"

grep -Fq 'ai_ops_assistant_diagnostic_toolbox_enabled: false' "$diagnostic_defaults"
grep -Fq 'neutron_agent_health.py' "$diagnostic_defaults"
grep -Fq "'neutron_agent_health.py'" "$diagnostic_tasks"
grep -Fq "'0640', '0750', '0750', '0750', '0750', '0750'" "$diagnostic_tasks"
grep -Fq "item.stat.pw_name == 'root'" "$diagnostic_tasks"
grep -Fq 'item.stat.mode == item.item.mode' "$diagnostic_tasks"
grep -Fq 'follow: false' "$diagnostic_tasks"

grep -Fq 'ai_ops_assistant_host_observer_boundary_enabled: false' "$observer_defaults"
grep -Fq 'host_observer/host_observer_collector.py' "$observer_defaults"
grep -Fq 'destination: host-observer-collector' "$observer_defaults"
grep -Fq 'collector_policy_path: /etc/openstack-ai-ops-assistant/host-observer-policy.yml' "$observer_defaults"
grep -Fq 'collector_policy_mode: "0600"' "$observer_defaults"
grep -Fq 'ai_ops_assistant_host_observer_boundary_deployment_authorization: unconfirmed' "$observer_defaults"
grep -Fq 'inventory_projection_status: unresolved' "$observer_defaults"
grep -Fq 'collector_metadata_status: unresolved' "$observer_defaults"
grep -Fq 'collector_policy_metadata_status: unresolved' "$observer_defaults"
grep -Fq 'redaction_policy_status: unresolved' "$observer_defaults"
grep -Fq 'ai_ops_assistant_host_observer_boundary_collector_files' "$observer_tasks"
grep -Fq 'Inspect host-observer collector source' "$observer_tasks"
grep -Fq 'Materialize exact host-observer collector' "$observer_tasks"
grep -Fq 'collector_destination_metadata.stat.pw_name == ai_ops_assistant_host_observer_boundary_collector_owner' "$observer_tasks"
grep -Fq 'not ansible_check_mode' "$observer_tasks"
grep -Fq 'Keep host-observer provisioning unavailable by default' "$observer_tasks"
grep -Fq 'Phase 06 restricted metadata evidence extension' "$repo_root/docs/ai-ops-revised/runtime/manual-aiops-workflows.md"
grep -Fq 'recent_nova_errors' "$repo_root/docs/ai-ops-revised/runtime/manual-aiops-workflows.md"

grep -Fq 'OPERATOR_READER_PROFILE' "$runner_source"
grep -Fq 'TOOL_PROFILES' "$runner_source"
grep -Fq 'def resolve_tool_profile' "$runner_source"
grep -Fq 'def build_child_environment(tool:' "$runner_source"
grep -Fq 'UNAVAILABLE_DIAGNOSTIC_ERROR_CLASSES' "$runner_source"

if grep -nE 'build_child_environment\(\)|shell=True|os\.system\(|ansible\.builtin\.(shell|command|raw|expect)|(^|[[:space:]])hosts: all|(^|[[:space:]])(ssh|sudo)([[:space:]]|$)|--(profile|credential|registry)|/opt/openstack-ai-ops([^/-]|$)' \
  "$runner_source" "$runner_tasks" "$connector_source" "$diagnostic_source" "$diagnostic_tasks"; then
  fail "generic execution, profile override, historical path, or broad host capability found"
fi

"${PYTHON_BIN:-python3}" - "$registry" "$runner_source" <<'PY'
import importlib.util
import json
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

registry_path = Path(sys.argv[1])
runner_path = Path(sys.argv[2])
registry = json.loads(registry_path.read_text(encoding="utf-8"))
expected_names = {
    "project_resource_summary",
    "server_basic_info",
    "server_network_info",
    "neutron_agent_health",
    "recent_metadata_errors",
    "recent_neutron_errors",
    "recent_nova_errors",
}
assert len(registry["tools"]) == 7
assert {tool["name"] for tool in registry["tools"]} == expected_names
neutron = next(tool for tool in registry["tools"] if tool["name"] == "neutron_agent_health")
assert neutron["implementation_target"] == "/opt/openstack-ai-ops-assistant/scripts/approved/neutron_agent_health.py"
assert neutron["credential_profile"] == "aiops-assistant-operator-reader"
assert neutron["risk_class"] == "higher_visibility_operator_scope"
assert neutron["parameters"] == []
host = next(tool for tool in registry["tools"] if tool["name"] == "recent_nova_errors")
assert host["authority_class"] == "aiops-assistant-host-observer"
assert host["credential_profile"] is None
assert host["parameters"][0]["name"] == "host_label"

spec = importlib.util.spec_from_loader(
    "static_runner_acceptance",
    SourceFileLoader("static_runner_acceptance", str(runner_path)),
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
loaded = runner.load_registry()
openstack_tools = {
    tool["name"]: runner.resolve_tool_profile(tool)
    for tool in loaded["tools"]
    if tool["name"] not in runner.HOST_TOOL_NAMES
}
assert openstack_tools == {
    "project_resource_summary": runner.PROJECT_READER_PROFILE,
    "server_basic_info": runner.PROJECT_READER_PROFILE,
    "server_network_info": runner.PROJECT_READER_PROFILE,
    "neutron_agent_health": runner.OPERATOR_READER_PROFILE,
}
assert not any(
    key.startswith("OS_")
    for key in runner.build_child_environment(host)
)
assert runner.build_child_environment(neutron)["OS_CLOUD"] == runner.OPERATOR_READER_PROFILE
PY

grep -Fq 'ai_ops_assistant_phase06_validation_enabled: false' "$validation_playbook"
grep -Fq 'status: blocked' "$validation_playbook"
grep -Fq 'limitation_class: authorization_pending' "$validation_playbook"
grep -Fq 'phase05_acceptance_confirmed: false' "$validation_playbook"
grep -Fq 'neutron_read_classified: false' "$validation_playbook"
grep -Fq 'operator_reader_reviewed: false' "$validation_playbook"
grep -Fq 'observer_policy_reviewed: false' "$validation_playbook"
grep -Fq 'output_schema_frozen: false' "$validation_playbook"
grep -Fq 'redaction_check_completed: false' "$validation_playbook"

printf 'Tool-runner/diagnostic deployment static acceptance test passed\n'
