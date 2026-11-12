# Prior AI-OPS Source Capability Catalog

## Purpose and Scope

This catalog records the historical AI-OPS source tree as immutable, fixed-revision evidence for the revised diagnostic -> runner -> local stdio MCP product path. It is a classification record, not a copy plan, implementation approval, or activation mechanism.

The fail-closed selective-reuse manifest is intentionally deferred to Chunk 2. A `selected-for-phase` disposition below authorizes only later path-level content and dependency review by the named phase. It does not authorize copying, execution, provisioning, credential creation, or modification of either runtime tree.

## Fixed Provenance

| Field | Value |
| --- | --- |
| Accepted repository revision | `0fbc8a45d5a31e5728caafe90d3cda7da616c911` |
| Branch when cataloged | `ai-ops-assistant-phase01` |
| Prior source root | `ansible/ai_ops_runtime/` |
| Prior runtime tree identity | `3abc4bcf3fa4caf1c6d89f8d25865e2c0aef8e07` |
| Revised repository root | `ansible/ai_ops_assistant/` |
| Prior-source state at cataloging | No staged or unstaged diff under the prior source root. |

Historical tests, playbooks, documents, and evidence remain evidence for the prior baseline only; they are not revised acceptance evidence.

## Classification Rules

- Each tracked prior path is classified by the first matching selector in the coverage table below.
- `**` means all tracked descendants for catalog coverage only. It is not a reuse selection and must not be interpreted as a directory-level allowlist.
- Protected inventory, credentials, generated state, caches, logs, raw audit data, and unredacted evidence remain excluded regardless of tracking state. This catalog records protected paths by name only.
- Every later reuse decision must name the exact source path, current requirement, owning phase, full dependency closure, required isolation changes, and independent validation.
- Absence from the later selective-reuse manifest means excluded.

## Capability Catalog

| Coverage selector | Capability classification | Revised requirement / owner | Disposition | Direct dependency or coupling concern | Content review |
| --- | --- | --- | --- | --- | --- |
| `inventories/local/**` | Historical inventory and variables | No current source reuse requirement | `excluded` | May contain protected inventory values; values were not read | Not applicable |
| `files/orchestrator/**` | Orchestrator package, remote acceptance, and MCP bridge support | None in current product path | `excluded` | Defines `openstack_ai_ops_orchestrator`, imported by the historical assistant bridge | Not applicable |
| `roles/ai_client_runtime/**` | Provider gateway and AI-client runtime | None in current product path | `excluded` | Provider and runtime architecture is outside the diagnostic boundary | Not applicable |
| `roles/assistant_egress/**` | Assistant egress controls | None in current product path | `excluded` | Egress is outside the initial management-only route | Not applicable |
| `roles/assistant_egress_validation/**` | Assistant egress validation | None in current product path | `excluded` | Validates an excluded egress capability | Not applicable |
| `roles/assistant_device_auth_egress/**` | Device-auth egress | None in current product path | `excluded` | Device-auth operations are outside the current product path | Not applicable |
| `roles/orchestrator_runtime/**` | Orchestrator deployment and bridge services | None in current product path | `excluded` | Includes orchestrator and bridge runtime/service lifecycle | Not applicable |
| `roles/orchestrator_egress/**` | Orchestrator egress controls | None in current product path | `excluded` | Depends on excluded orchestrator architecture | Not applicable |
| `roles/orchestrator_wheelhouse_builder/**` | Offline wheelhouse build | None in current product path | `excluded` | Wheelhouse operations are outside the current product path | Not applicable |
| `roles/orchestrator_wheelhouse_transfer/**` | Offline wheelhouse transfer | None in current product path | `excluded` | Depends on excluded wheelhouse capability | Not applicable |
| `roles/assistant_runtime/defaults/main.yml`, `roles/assistant_runtime/tasks/workspace.yml`, `roles/assistant_runtime/tasks/tooling.yml`, `playbook_setup_assistant_runtime.yml` | Historical workspace/tooling setup behavior | Phase 01 Step 4 minimal foundation | `reference-only` | Historical `tasks/main.yml` unconditionally includes workspace, scripts, credentials, tooling, and MCP lifecycle; it is not a minimal foundation boundary | Deferred to Phase 01 Step 4 |
| `roles/assistant_runtime/files/scripts/approved/lib/aiops_common.sh`, `roles/assistant_runtime/files/scripts/approved/project_resource_summary.sh`, `roles/assistant_runtime/files/scripts/approved/server_basic_info.sh`, `roles/assistant_runtime/files/scripts/approved/server_network_info.sh`, `roles/assistant_runtime/files/scripts/approved/README.md` | Shared helper and three project-level diagnostics | FR-011, FR-012, FR-013 / Phase 03 | `selected-for-phase` | Each of the three scripts resolves and sources `lib/aiops_common.sh`; revised paths, profile, input validation, output, and safety contract require review | Deferred to Phase 03 |
| `roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py` | Named-tool runner | FR-022 through FR-031 / Phase 04 | `selected-for-phase` | Resolves an adjacent registry; historical behavior and paths require revised safety review | Deferred to Phase 04 |
| `roles/assistant_runtime/files/scripts/tool_runner/tool_registry.json` | Historical registry | FR-022 through FR-031 / Phase 04 | `reference-only` | Contains historical `/opt/openstack-ai-ops` targets and later Neutron/host tools; derive a minimal revised registry | Deferred to Phase 04 |
| `roles/assistant_runtime/files/scripts/approved/neutron_agent_health.sh`, `roles/assistant_runtime/files/scripts/host_diagnostics/**`, `roles/assistant_runtime/templates/host_diagnostics/**`, `roles/host_observer/**`, `playbook_setup_host_observer.yml`, `playbook_validate_phase06_restricted_host_diagnostics.yml` | Neutron-agent and restricted-host diagnostics | FR-014, FR-015 / Phase 06 | `candidate` | Requires separately approved operator-reader, restricted SSH/sudo, host policy, and output/redaction review | Deferred to Phase 06 |
| `roles/assistant_runtime/tasks/credentials.yml`, `playbook_validate_phase02_1_readonly_credential_boundary.yml`, `playbook_validate_phase02_2_profile_sync_and_mutation_denial.yml` | Historical credential lifecycle and validation | Phase 02 read-only identity boundary | `candidate` | Credential material must be created fresh; protected values must never be copied | Deferred to Phase 02 |
| `roles/assistant_runtime/files/mcp/aiops_mcp_server.py` | Local stdio MCP adapter | FR-036, FR-037 / Phase 07 | `selected-for-phase` | Imports `mcp.server.stdio.stdio_server` and invokes the historical runner/registry paths; must be adapted to the revised runner only | Deferred to Phase 07 |
| `roles/assistant_runtime/files/mcp/resources/**`, `roles/assistant_runtime/templates/mcp/mcp_policy.json.j2`, `roles/assistant_runtime/tasks/mcp_lifecycle.yml`, `playbook_manage_mcp_lifecycle.yml`, `playbook_validate_phase07_mcp_integration.yml` | MCP resources, policy, lifecycle, and validation behavior | FR-038, FR-039 / Phase 07 | `candidate` | Requires resource content/secret review, revised process identity, and local-stdio lifecycle review | Deferred to Phase 07 |
| `roles/assistant_runtime/files/mcp/aiops_assistant_bridge.py`, `playbook_validate_phase12_assistant_bridge_activation.yml` | Historical MCP assistant bridge | None in current product path | `excluded` | Imports `openstack_ai_ops_orchestrator.contracts` and `.mcp_bridge`; coupled to excluded orchestrator architecture | Not applicable |
| `roles/assistant_runtime/tasks/scripts.yml`, `roles/assistant_runtime/tasks/main.yml` | Historical aggregate assistant-runtime entrypoint | No direct reuse requirement | `reference-only` | Main task list includes workspace, scripts, credentials, tooling, and MCP lifecycle together; cannot provide Phase 01 isolation | Deferred only as behavior reference |
| `playbook_validate_phase01_runtime_evidence_summary.yml`, `playbook_validate_phase03_diagnostic_toolbox.yml`, `playbook_validate_phase04_tool_runner_safety_gateway.yml`, `playbook_validate_phase05_manual_aiops_workflows.yml` | Historical validation evidence | Corresponding revised phases | `reference-only` | Historical results do not prove revised acceptance | Deferred to owning phase |
| `playbook_build_orchestrator_wheelhouse.yml`, `playbook_copy_orchestrator_wheelhouse_seed_to_builder.yml`, `playbook_stage_orchestrator_wheelhouse_seed.yml`, `playbook_transfer_orchestrator_wheelhouse.yml` | Wheelhouse build and transfer playbooks | None in current product path | `excluded` | Wheelhouse family is excluded | Not applicable |
| `playbook_materialize_assistant_egress.yml`, `playbook_operate_device_auth_egress_window.yml`, `playbook_validate_device_auth_egress_contract.yml` | Assistant/device-auth egress playbooks | None in current product path | `excluded` | Egress and device authentication are excluded | Not applicable |
| `playbook_operate_orchestrator_auth_egress_window.yml`, `playbook_operate_orchestrator_egress_window.yml`, `playbook_operate_orchestrator_remote_acceptance.yml`, `playbook_setup_orchestrator_runtime.yml`, `playbook_validate_phase11_orchestrator_deployment.yml`, `playbook_validate_phase11_orchestrator_egress.yml`, `playbook_validate_phase12_remote_preflight.yml` | Orchestrator and remote-operation playbooks | None in current product path | `excluded` | Depends on excluded orchestrator, egress, or remote acceptance architecture | Not applicable |
| `playbook_retire_phase13_provider_gateway.yml`, `playbook_setup_ai_client_runtime.yml`, `playbook_validate_phase07_provider_gateway_deployment.yml`, `playbook_validate_phase07_provider_gateway_egress.yml`, `playbook_validate_phase13_provider_gateway_retirement.yml` | Provider gateway deployment, egress, and retirement playbooks | None in current product path | `excluded` | Provider operations and retirement are excluded | Not applicable |

## Coverage Reconciliation

The selectors above cover all Git-tracked paths under `ansible/ai_ops_runtime/` at the accepted revision. The catalog is deliberately broader than a future manifest: broad selectors classify historical evidence, but no directory or selector authorizes reuse.

The only future review candidates aligned to the approved product sequence are:

1. Phase 03: the common shell helper and three project-level diagnostic scripts.
2. Phase 04: the runner; the registry remains reference-only and must be derived anew.
3. Phase 06: Neutron-agent and restricted-host assets, deferred behind separate controls.
4. Phase 07: the local stdio MCP adapter, then separately reviewed resources, policy, and lifecycle behavior.

All provider, orchestrator, egress, device-auth, wheelhouse, remote-operation, bridge-activation, and provider-retirement capabilities remain outside the current product path. No implementation file has been copied into `ansible/ai_ops_assistant/`.

## Validation Record

Catalog evidence was established without reading protected inventory values and without executing Ansible, provisioning hosts, creating credentials, or making network changes. Path existence, source-tree identity, source-tree immutability, and destination-tree non-mutation must be rechecked before later catalog or manifest updates.
