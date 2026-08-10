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
validation_playbook="$repo_root/ansible/ai_ops_assistant/playbook_produce_phase06_restricted_diagnostics_validation.yml"

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
  "$validation_playbook"; do
  [[ -f "$path" && ! -L "$path" ]] || fail "required static artifact is missing or symlinked: $path"
done

grep -Fq 'ai_ops_assistant_tool_runner_enabled: false' "$runner_defaults"
grep -Fq 'ai_ops_assistant_tool_runner_explicit_deployment' "$runner_tasks"
grep -Fq '/opt/openstack-ai-ops-assistant/scripts/approved/neutron_agent_health.py' "$runner_defaults"
grep -Fq "'/neutron_agent_health.py'" "$runner_tasks"
grep -Fq "'aiops_tool_runner.py', 'audit_inspector.py', 'tool_registry.json'" "$runner_tasks"
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

grep -Fq 'OPERATOR_READER_PROFILE' "$runner_source"
grep -Fq 'TOOL_PROFILES' "$runner_source"
grep -Fq 'def resolve_tool_profile' "$runner_source"
grep -Fq 'def build_child_environment(tool:' "$runner_source"
grep -Fq 'UNAVAILABLE_DIAGNOSTIC_ERROR_CLASSES' "$runner_source"

if grep -nE 'build_child_environment\(\)|shell=True|os\.system\(|ansible\.builtin\.(shell|command|raw|expect)|(^|[[:space:]])hosts: all|(^|[[:space:]])(ssh|sudo)([[:space:]]|$)|--(profile|credential|registry)|/opt/openstack-ai-ops([^/-]|$)' \
  "$runner_source" "$runner_tasks" "$diagnostic_source" "$diagnostic_tasks"; then
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
}
assert len(registry["tools"]) == 4
assert {tool["name"] for tool in registry["tools"]} == expected_names
neutron = next(tool for tool in registry["tools"] if tool["name"] == "neutron_agent_health")
assert neutron["implementation_target"] == "/opt/openstack-ai-ops-assistant/scripts/approved/neutron_agent_health.py"
assert neutron["credential_profile"] == "aiops-assistant-operator-reader"
assert neutron["risk_class"] == "higher_visibility_operator_scope"
assert neutron["parameters"] == []

spec = importlib.util.spec_from_loader(
    "static_runner_acceptance",
    SourceFileLoader("static_runner_acceptance", str(runner_path)),
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
loaded = runner.load_registry()
assert {tool["name"]: runner.resolve_tool_profile(tool) for tool in loaded["tools"]} == {
    "project_resource_summary": runner.PROJECT_READER_PROFILE,
    "server_basic_info": runner.PROJECT_READER_PROFILE,
    "server_network_info": runner.PROJECT_READER_PROFILE,
    "neutron_agent_health": runner.OPERATOR_READER_PROFILE,
}
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
