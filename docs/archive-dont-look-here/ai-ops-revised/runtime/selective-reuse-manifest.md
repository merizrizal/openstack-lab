# Fail-Closed Selective-Reuse Manifest

## Authority and Default

This manifest is the only approval record for considering prior AI-OPS implementation paths in the revised product. It applies to the fixed source revision recorded below.

- Any prior path absent from this manifest is `excluded`.
- A `selected-for-phase` path is approved only for the named phase's content and dependency review. It is not approved for copying, execution, provisioning, credential creation, or activation.
- A selected path must retain or replace its complete import, include, template, resource, and runtime-path dependency closure before it can enter the revised namespace.
- Directory selection and wildcard selection are prohibited. Exact paths are required for every selected entry.
- Protected inventory values, credentials, keys, generated state, caches, logs, raw audit data, and unredacted evidence are always excluded.

## Fixed Provenance

| Field | Value |
| --- | --- |
| Accepted repository revision | `0fbc8a45d5a31e5728caafe90d3cda7da616c911` |
| Prior runtime tree identity | `3abc4bcf3fa4caf1c6d89f8d25865e2c0aef8e07` |
| Prior source root | `ansible/ai_ops_runtime/` |
| Source catalog | `docs/ai-ops-revised/runtime/source-capability-catalog.md` |

A source-revision or tree-identity change invalidates this manifest until it is reviewed and regenerated.

## Disposition Vocabulary

| Disposition | Meaning |
| --- | --- |
| `selected-for-phase` | Exact path may be reviewed only by its named owning phase; activation remains blocked. |
| `reference-only` | Historical behavior may inform a new implementation but source content must not be copied as implementation. |
| `candidate` | Potentially relevant but not selected for review or activation. |
| `excluded` | Outside the approved product path; a plan and manifest amendment are required before reconsideration. |

## Selected Exact Paths

| `source_path` | `requirement` | `phase_owner` | `disposition` | `dependency_closure` | `required_modifications` | `validation_owner` |
| --- | --- | --- | --- | --- | --- | --- |
| `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved/lib/aiops_common.sh` | FR-011 through FR-013 | Phase 03 | `selected-for-phase` | The three selected diagnostics source this helper. | Revised root, credential profile, validation, and output contracts. | Phase 03 static forbidden-operation, syntax, input, output-contract, and deployed read-only validation. |
| `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved/project_resource_summary.sh` | FR-011 | Phase 03 | `selected-for-phase` | Selected common helper. | Remove historical runtime/profile paths. | Phase 03 safety and manual acceptance checks. |
| `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved/server_basic_info.sh` | FR-012 | Phase 03 | `selected-for-phase` | Selected common helper. | Enforce revised single-server parameter contract. | Phase 03 safety, malformed-input, and manual acceptance checks. |
| `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved/server_network_info.sh` | FR-013 | Phase 03 | `selected-for-phase` | Selected common helper. | Enforce revised single-server parameter contract. | Phase 03 safety, malformed-input, and manual acceptance checks. |
| `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py` | FR-022 through FR-031 | Phase 04 | `selected-for-phase` | Exact replacement: a newly derived revised registry. | Resolve only revised implementation, profile, audit, and runtime paths. | Phase 04 registry parsing, argument-vector, limits, result, audit, and negative-case validation. |
| `ansible/ai_ops_runtime/roles/assistant_runtime/files/mcp/aiops_mcp_server.py` | FR-036, FR-037 | Phase 07 | `selected-for-phase` | Exact replacement: accepted revised Phase 04 runner and registry. | Do not import or invoke the bridge or orchestrator package. | Phase 07 stdio, runner-equivalence, redaction, audit, and negative-capability validation. |

No other path is selected. In particular, the historical `README.md`, registry, MCP resources, policy, lifecycle task, and all playbooks are not selected by this manifest.

## Reference-Only Paths

| Prior source path | Owner | Reason |
| --- | --- | --- |
| `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml` | Phase 01 Step 4 | May inform isolated workspace/tooling behavior only. |
| `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/workspace.yml` | Phase 01 Step 4 | Historical workspace behavior is not a copy authority. |
| `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/tooling.yml` | Phase 01 Step 4 | Historical tooling behavior is not a copy authority. |
| `ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml` | Phase 01 Step 4 | Historical entrypoint is not a minimal revised foundation. |
| `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/tool_registry.json` | Phase 04 | Contains historical runtime paths and Phase 06 tools; a minimal revised registry must be derived. |
| `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/main.yml` | Phase 01 Step 4 | Unconditionally aggregates scripts, credentials, tooling, and MCP lifecycle. |
| `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/scripts.yml` | Phase 01 Step 4 | Historical aggregate installation behavior is not a minimal foundation. |
| `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/credentials.yml` | Phase 02 | May inform fresh profile-materialization controls only; credential values, source paths, variables, and implementation content must not be copied. |
| `ansible/ai_ops_runtime/playbook_validate_phase02_1_readonly_credential_boundary.yml` | Phase 02 | Raw stdout/stderr evidence and historical targeting violate the revised minimum-disclosure boundary; do not copy implementation content. |
| `ansible/ai_ops_runtime/playbook_validate_phase02_2_profile_sync_and_mutation_denial.yml` | Phase 02 | Generated-profile dependence, profile-content reads, named targets, and reader-credential cleanup violate the revised contract; do not copy implementation content. |

## Deferred Candidates

| Capability | Prior source paths | Owner | Required decision before selection |
| --- | --- | --- | --- |
| Neutron-agent and restricted-host diagnostics | `roles/assistant_runtime/files/scripts/approved/neutron_agent_health.sh`; `roles/assistant_runtime/files/scripts/host_diagnostics/aiops_host_diagnostic_connector.py`; `roles/assistant_runtime/templates/host_diagnostics/host_diagnostic_policy.json.j2`; `roles/host_observer/**` | Phase 06 | Approve separate operator-reader, restricted SSH/sudo, host-policy, and redaction controls. |
| MCP resources, policy, and lifecycle | `roles/assistant_runtime/files/mcp/resources/**`; `roles/assistant_runtime/templates/mcp/mcp_policy.json.j2`; `roles/assistant_runtime/tasks/mcp_lifecycle.yml` | Phase 07 | Review every resource for secrets and define revised local-stdio lifecycle and identity. |

The `**` expressions above identify deferred catalog families only. They are not selections.

## Explicit Exclusions

The following capability families and their tracked descendants are excluded from the current product path:

- `ansible/ai_ops_runtime/inventories/local/` and every protected inventory value.
- `ansible/ai_ops_runtime/files/orchestrator/`.
- `ansible/ai_ops_runtime/roles/ai_client_runtime/` and provider gateway behavior.
- `ansible/ai_ops_runtime/roles/assistant_egress/`.
- `ansible/ai_ops_runtime/roles/assistant_egress_validation/`.
- `ansible/ai_ops_runtime/roles/assistant_device_auth_egress/`.
- `ansible/ai_ops_runtime/roles/orchestrator_runtime/`.
- `ansible/ai_ops_runtime/roles/orchestrator_egress/`.
- `ansible/ai_ops_runtime/roles/orchestrator_wheelhouse_builder/`.
- `ansible/ai_ops_runtime/roles/orchestrator_wheelhouse_transfer/`.
- `ansible/ai_ops_runtime/roles/assistant_runtime/files/mcp/aiops_assistant_bridge.py`; it imports the excluded `openstack_ai_ops_orchestrator` package.
- Provider, orchestrator, egress, device-auth, wheelhouse, remote-acceptance, bridge-activation, and provider-retirement playbooks.

These exclusions include no exception for destination-path parity. A new approved requirement, plan amendment, and manifest revision are mandatory before any excluded capability is reconsidered.

## Manifest Consistency Requirements

Before a later phase uses a selected path, verify that:

1. The accepted revision and prior tree identity match this manifest.
2. The selected source path exists at that revision.
3. The path has a current requirement, named phase owner, complete dependency closure or documented replacement, required isolation changes, and independent validation gate.
4. No selected entry is a directory, wildcard, protected path, historical runtime path, bridge, provider, orchestrator, egress, wheelhouse, device-auth, remote-operation, or retirement path.
5. Phase 03 remains limited to the common helper plus the three named project-level diagnostics.
6. Phase 04 derives a minimal revised registry; it must not copy `tool_registry.json` or register later restricted-host tools.
7. Phase 07 delegates only to the revised Phase 04 runner and does not invoke the historical bridge or orchestrator package.
8. `ansible/ai_ops_runtime/`, `ansible/ai_ops_assistant/`, and `inventories/local/nodes.yml` have no unexpected implementation or inventory diff.

## Static Consistency Gate Contract

### Purpose and Inputs

A later non-mutating validator must verify this manifest before any selected path is reviewed, copied, or adapted. It receives only:

1. the manifest and source catalog paths;
2. the current Git `HEAD`, prior-source tree identity, and tracked path names; and
3. an explicit per-selected-path dependency declaration or replacement declaration.

It must not read protected inventory values, source credentials, generated state, logs, or raw audit evidence. It must not execute Ansible, provision a host, make network calls, or write repository files.

### Required Manifest Fields

Each selected entry must provide these non-empty fields:

| Field | Rule |
| --- | --- |
| `source_path` | Exact tracked path under `ansible/ai_ops_runtime/`; no directory, trailing slash, wildcard, or glob. |
| `requirement` | Current FR/NFR identifier or an explicitly approved current requirement. |
| `phase_owner` | One named implementation phase that owns content review and validation. |
| `disposition` | Exactly `selected-for-phase`. |
| `dependency_closure` | Exact selected dependencies or exact replacement declarations, including import, include, template, resource, and runtime-path concerns. |
| `required_modifications` | Revised isolation changes required before destination use. |
| `validation_owner` | Named phase validation and activation gate. |

Unknown fields, duplicate `source_path` values, missing fields, unsupported dispositions, or undeclared/ambiguous dependency declarations must fail validation.

### Accepted Provenance and Selected-Path Allowlist

The gate must require both accepted values before evaluating a path:

| Provenance field | Required value |
| --- | --- |
| Repository revision | `0fbc8a45d5a31e5728caafe90d3cda7da616c911` |
| Prior runtime tree identity | `3abc4bcf3fa4caf1c6d89f8d25865e2c0aef8e07` |

The selected-path allowlist is exact and contains only:

1. `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved/lib/aiops_common.sh`
2. `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved/project_resource_summary.sh`
3. `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved/server_basic_info.sh`
4. `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved/server_network_info.sh`
5. `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py`
6. `ansible/ai_ops_runtime/roles/assistant_runtime/files/mcp/aiops_mcp_server.py`

### Excluded-Prefix List

The gate must reject any selected path at or below these excluded prefixes:

- `ansible/ai_ops_runtime/inventories/local/`
- `ansible/ai_ops_runtime/files/orchestrator/`
- `ansible/ai_ops_runtime/roles/ai_client_runtime/`
- `ansible/ai_ops_runtime/roles/assistant_egress/`
- `ansible/ai_ops_runtime/roles/assistant_egress_validation/`
- `ansible/ai_ops_runtime/roles/assistant_device_auth_egress/`
- `ansible/ai_ops_runtime/roles/orchestrator_runtime/`
- `ansible/ai_ops_runtime/roles/orchestrator_egress/`
- `ansible/ai_ops_runtime/roles/orchestrator_wheelhouse_builder/`
- `ansible/ai_ops_runtime/roles/orchestrator_wheelhouse_transfer/`

It must also reject `ansible/ai_ops_runtime/roles/assistant_runtime/files/mcp/aiops_assistant_bridge.py`, every provider, orchestrator, egress, device-auth, wheelhouse, remote-operation, bridge-activation, and provider-retirement playbook, and any path not in the exact selected-path allowlist.

### Fail-Closed Algorithm and Output

For each selected entry, the validator must:

1. reject revision or tree-identity mismatch;
2. reject a missing required field, duplicate path, unknown path, broad directory, wildcard, protected path, or excluded path;
3. confirm the exact `source_path` is tracked at the accepted revision;
4. confirm every declared dependency is either another exact allowlisted path or an exact documented replacement in the revised namespace;
5. reject a dependency that resolves to an excluded path or has no replacement declaration; and
6. confirm Phase 03 has only its helper plus three diagnostics, Phase 04 replaces rather than copies the registry, and Phase 07 delegates only to the revised runner without the historical bridge or orchestrator package.

The validator prints only one line per result in `STATUS path reason` form. It prints no source contents or protected values. Any rejection produces a non-zero result and prevents later use of the affected path.

### Design Test Vectors

| Input | Expected result | Reason |
| --- | --- | --- |
| `project_resource_summary.sh` with helper dependency, Phase 03 owner, and revised-root replacement notes | accept | Exact allowlisted path with an owned requirement and declared closure. |
| `tool_registry.json` as a selected path | reject | Reference-only historical registry; it is not in the allowlist. |
| `aiops_assistant_bridge.py` as a selected path | reject | Explicitly excluded bridge imports the orchestrator package. |
| `roles/assistant_runtime/files/scripts/approved/` as a selected path | reject | Directory selection is prohibited. |
| `roles/assistant_runtime/files/scripts/approved/*.sh` as a selected path | reject | Wildcard selection is prohibited. |
| A nonexistent prior path | reject | Unknown or untracked path fails closed. |
| `aiops_mcp_server.py` with a historical runner path and no revised replacement | reject | Runtime-path dependency closure is incomplete. |

## Non-Activation Record

This manifest does not create destination implementation, runtime configuration, host state, credentials, network routes, diagnostic execution, runner execution, or MCP execution. It does not alter the historical runtime.
