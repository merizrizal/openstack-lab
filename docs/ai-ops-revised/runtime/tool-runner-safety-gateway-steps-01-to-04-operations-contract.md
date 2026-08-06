# Revised AI-OPS Tool Runner Safety Gateway Operations Contract — Steps 1–4

## Status and Authority

This is the approved Steps 1–4 operations contract for Phase 04. It is subordinate to:

- `docs/ai-ops-revised/implementation-plan/04-tool-runner-safety-gateway.md`
- `docs/ai-ops-revised/implementation-plan/ads/04-00-tool-runner-safety-gateway-steps-01-to-04-ads.md`
- `docs/ai-ops-revised/runtime/manual-diagnostic-toolbox-operations-contract.md`
- `docs/ai-ops-revised/runtime/identity-policy-operations-contract.md`
- `docs/ai-ops-revised/runtime/selective-reuse-manifest.md`

It defines the contract for later implementation of registry validation, named-request denial, fixed shell-free execution, and time/process/output bounds. It does not authorize live execution, profile access, OpenStack calls, host diagnostics, MCP, audit completion, final result-envelope completion, or Phase 04 completion.

Steps 5–7 remain authoritative for the final result envelope, complete audit events, and the complete safety regression suite.

## Non-Activation Boundary

This document introduces no executable files, deployment role, validation playbook, host connection, Ansible execution, credential operation, profile read, OpenStack call, cloud-state authority, or audit record.

Implementation must remain fixture-driven until the later deployment and activation gate. The existing historical runner and registry are reference material only. They must not be copied, installed, imported, or executed.

## Approved Capability Boundary

The gateway is local-only and deny-by-default:

```text
named request
  -> fixed registry validation
  -> tool and parameter validation
  -> fixed argv construction
  -> fresh minimal child environment
  -> process-group execution
  -> timeout and bounded capture
  -> interim structured outcome
```

The initial public tool set contains exactly:

| Tool name | Revised implementation target | Parameters | Credential profile | Risk class |
| --- | --- | --- | --- | --- |
| `project_resource_summary` | `/opt/openstack-ai-ops-assistant/scripts/approved/project_resource_summary.sh` | none | `aiops-assistant-project-reader` | `low_readonly_project_scope` |
| `server_basic_info` | `/opt/openstack-ai-ops-assistant/scripts/approved/server_basic_info.sh` | required `server_identifier` | `aiops-assistant-project-reader` | `low_readonly_project_scope` |
| `server_network_info` | `/opt/openstack-ai-ops-assistant/scripts/approved/server_network_info.sh` | required `server_identifier` | `aiops-assistant-project-reader` | `low_readonly_project_scope` |

The registry must reject every other capability, including generic shell, SSH, sudo, OpenStack CLI passthrough, file read/write, database query, message-bus access, service restart, package mutation, remediation, and Phase 06 host diagnostics.

## Revised Source and Deployment Boundary

The revised implementation is owned by a dedicated role so Phase 03's exact diagnostic file allowlist remains unchanged:

| Concern | Approved value |
| --- | --- |
| Source role | `ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/` |
| Source runner | `ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/aiops_tool_runner.py` |
| Source registry | `ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/tool_registry.json` |
| Runtime root | `/opt/openstack-ai-ops-assistant` |
| Runtime runner directory | `/opt/openstack-ai-ops-assistant/scripts/tool_runner` |
| Runtime approved-script directory | `/opt/openstack-ai-ops-assistant/scripts/approved` |
| Runtime user/group | `aiops_assistant:aiops_assistant` |
| Runner owner/mode | `root:aiops_assistant`, `0750` |
| Registry owner/mode | `root:aiops_assistant`, `0640` |
| Controlled working directory | `/opt/openstack-ai-ops-assistant` |
| Enable default | disabled until a later authorized deployment gate |

The source role and paths are newly derived revised paths. They must not import from or copy the historical `ansible/ai_ops_runtime/roles/assistant_runtime/` implementation.

## Registry Schema Contract

The registry is a UTF-8 JSON object with duplicate-key rejection and exact schema version `1`. Unknown fields are invalid at every object level.

### Root fields

The root object contains exactly:

| Field | Type | Constraint |
| --- | --- | --- |
| `schema_version` | integer | exactly `1` |
| `registry_name` | string | exactly `ai-ops-assistant-tool-runner-steps-01-04` |
| `defaults` | object | exact fields below |
| `tools` | array | exactly three entries, unique names |

`defaults` contains exactly:

| Field | Type | Required value/range |
| --- | --- | --- |
| `credential_profile` | string | exactly `aiops-assistant-project-reader` |
| `risk_class` | string | exactly `low_readonly_project_scope` |
| `timeout_seconds` | integer | `1..300` |
| `output_limit_bytes` | integer | `1..1048576` |
| `mutation_guarantee` | string | exactly `read_only_fixed_diagnostic_script` |

### Tool fields

Each tool object contains exactly:

- `name`: one of the three approved names, unique;
- `description`: non-empty bounded public description;
- `implementation_target`: one exact path from the approved capability table;
- `credential_profile`: exactly `aiops-assistant-project-reader`;
- `risk_class`: exactly `low_readonly_project_scope`;
- `timeout_seconds`: integer `1..300`, not greater than the global default ceiling;
- `output_limit_bytes`: integer `1..1048576`, not greater than the global default ceiling;
- `mutation_guarantee`: exactly `read_only_fixed_diagnostic_script`;
- `parameters`: an ordered array of declared parameter objects.

No `available`, `unavailable_reason`, `source_script`, audit path, registry path, profile override, executable override, working-directory override, shell setting, or historical compatibility field is permitted.

The target-to-tool mapping is one-to-one and exact. A target outside `/opt/openstack-ai-ops-assistant/scripts/approved/`, a target mismatch, a symlink, a non-regular file, or an unavailable approved target fails closed. No `PATH` search or alternate root is allowed.

### Parameter fields

Each parameter object contains exactly:

- `name`: unique non-empty identifier;
- `position`: unique positive integer defining argv order;
- `required`: boolean;
- `type`: exactly `string` for the initial tools;
- `validation`: one supported validator;
- `pattern`, `max_length`, or `allowed_values` only when required by that validator;
- `default` only for an optional parameter;
- `description`: bounded public description.

The initial three tools use only:

- `safe_identifier_pattern` for `server_identifier`;
- `required: true`;
- `type: string`;
- ASCII pattern `^[A-Za-z0-9._:-]+$`;
- maximum length 255 bytes;
- no slash or `..` traversal sequence.

The registry loader rejects unsupported validators, duplicate names/positions, missing required fields, invalid defaults, unknown constraint fields, booleans used as integers, empty values, and inconsistent required/default combinations.

## Request Interface and Denial Contract

The initial local interface is a fixed CLI:

```text
aiops_tool_runner.py TOOL_NAME [--arg KEY=VALUE ...]
```

The public caller may provide only the registered tool name and declared parameter values. The caller cannot provide registry, target, profile, audit, environment, working-directory, shell, timeout, output, or executable overrides.

Validation order is fixed:

1. Load and fully validate the adjacent registry.
2. Parse CLI syntax and reject malformed or duplicate declarations.
3. Resolve the requested tool.
4. Reject unknown and generic capability names with `denied`.
5. Reject unknown parameters, missing required parameters, wrong types, invalid patterns, invalid ranges, and invalid allowlists with `validation_error`.
6. Resolve defaults and validate them using the same rules.
7. Only then inspect the fixed target and construct an argv.

No child process may be created for a denied or validation-error request. Public failure text must not disclose internal paths, registry fields, profile content, environment values, credentials, stack traces, raw stderr, or raw command data.

## Status and Exit-Code Contract

The stable runner statuses for Steps 1–4 are:

| Status | Meaning |
| --- | --- |
| `ok` | The fixed diagnostic completed successfully; an empty diagnostic result is still successful. |
| `error` | The fixed diagnostic or runner failed, including malformed output, authentication failure, policy denial, not-found, ambiguous result, or cleanup failure. |
| `denied` | The requested capability is not in the reviewed allowlist or is a forbidden generic capability. |
| `timeout` | The deadline was reached and process-group cleanup was attempted. |
| `validation_error` | Request or registry-declared input failed validation before execution. |
| `unavailable` | The approved implementation/profile is unavailable, or the diagnostic reports `service_unavailable`, `catalog_missing`, or `connectivity_error`. |

Output truncation does not create a separate status. It is represented by `truncated: true` in the interim structured outcome. The final public envelope remains a Step 5 responsibility.

The process exit-code mapping is:

| Exit code | Status |
| ---: | --- |
| `0` | `ok` |
| `1` | `error` |
| `2` | `denied` |
| `3` | `validation_error` |
| `4` | `timeout` |
| `5` | `unavailable` |

Every non-`ok` status returns non-zero. Unknown internal failures fail closed as `error`. A diagnostic's `not_found`, `ambiguous`, `authentication_error`, `policy_denied`, `configuration_error`, malformed JSON, or unrecognized error maps to `error`; only the explicitly approved unavailable classes map to `unavailable`.

## Fixed Argument-Vector Contract

The runner creates argv exclusively from trusted registry metadata and validated parameter values:

| Tool | Resulting argv shape |
| --- | --- |
| `project_resource_summary` | `[approved_project_summary_target]` |
| `server_basic_info` | `[approved_server_basic_target, validated_server_identifier]` |
| `server_network_info` | `[approved_server_network_target, validated_server_identifier]` |

The implementation must use `shell=False`. It must not construct shell strings, invoke `eval`, concatenate user input into commands, accept caller flags/subcommands, or allow user-selected executable/path/profile/output values.

The target must be revalidated immediately before spawn as an existing regular, executable, non-symlinked file under the exact revised approved-script directory. A missing target is `unavailable`; an integrity mismatch is `error`. There is no fallback.

## Minimal Child Environment Contract

The runner constructs a new environment; it never copies the parent environment and removes selected keys.

The only permitted child environment keys are:

| Key | Fixed value |
| --- | --- |
| `PATH` | `/usr/bin:/bin` |
| `LANG` | `C.UTF-8` |
| `LC_ALL` | `C.UTF-8` |
| `HOME` | `/nonexistent` |
| `PYTHONNOUSERSITE` | `1` |
| `OS_CLIENT_CONFIG_FILE` | `/opt/openstack-ai-ops-assistant/credentials/profiles/clouds.yaml` |
| `OS_CLOUD` | `aiops-assistant-project-reader` |

No inherited `OS_*` authentication values, token, password, application-credential values, SSH-agent variables, provider values, proxy values, or unrelated process state may reach the child. The runner does not read or print profile contents.

The child starts with working directory `/opt/openstack-ai-ops-assistant`, a new process session/process group, closed unrelated file descriptors, and no shell.

## Timeout, Process Cleanup, and Output Contract

### Timeout and cleanup

- Each tool uses its registry-defined positive timeout, bounded by 300 seconds.
- The deadline uses a monotonic clock.
- The child starts in a new session/process group.
- At timeout or runner interruption, send termination to the complete process group.
- Wait up to one second for graceful exit.
- Escalate to process-group kill if the group remains alive.
- Reap the direct child and close all pipes before returning.
- Failure to establish cleanup is `error`; execution is never retried automatically.

### Output budget

`output_limit_bytes` is a combined retained-byte budget for stdout and stderr, with a per-stream soft ceiling of half the configured limit. The capture loop drains both streams concurrently:

1. Retain bytes from each stream up to its half-budget.
2. If one stream remains below its half-budget, unused budget may be assigned to the other stream.
3. Never retain more than the combined configured limit.
4. Continue draining and discard excess bytes so a noisy child cannot deadlock.
5. Set `truncated: true` whenever any bytes are discarded.
6. Decode retained bytes strictly as UTF-8 after capture; invalid UTF-8 is `error`.

The configured maximum is 1 MiB. The runner must not use unbounded `capture_output=True` buffering. A complete diagnostic payload remains subject to the Phase 03 diagnostic's own 1 MiB JSON bound.

### Interim outcome

Until Step 5, the runner emits exactly one deterministic JSON object containing only:

- tool name;
- stable status;
- sanitized public reason when applicable;
- exit code when applicable;
- bounded stdout/stderr or validated diagnostic data;
- duration in milliseconds;
- `truncated` boolean.

It must not claim the final schema version, correlation ID, complete redaction contract, or audit event contract. Raw profile data, credentials, tokens, command paths, raw exceptions, raw catalog data, and unnecessary full output are prohibited.

## Security and Integrity Contract

- Registry parsing is closed-schema and duplicate-key rejecting.
- The exact three-tool allowlist is enforced at startup.
- Historical runtime paths, historical profile names, Phase 06 tools, and generic capabilities are rejected.
- The caller cannot override registry, executable, profile, environment, working directory, timeout, output, or audit paths.
- The child environment is constructed from an explicit allowlist.
- Process groups are cleaned on timeout and interruption.
- Output is bounded before decoding and no pipe may remain undrained.
- Diagnostics are read-only by their Phase 03 contract; the runner adds no mutation capability.
- No secrets are read, emitted, or retained by this contract.
- MCP must later delegate to this runner rather than reimplementing execution.

## Validation Contract

The implementation must use a user-provided/custom Python virtual environment. Its path must be confirmed before Python validation, and its Python executable must be used; no system Python fallback is permitted.

Before executable implementation, validate with the narrowest applicable commands:

```bash
rtk <venv-python> -m py_compile <changed-python-files>
rtk <venv-python> -m json.tool <registry-file>
rtk <venv-python> -m unittest discover -s ansible/ai_ops_assistant/tests/tool_runner -p 'test_*.py'
rtk git diff --check
```

The implementation must also provide tests proving malformed registries, historical paths/profiles, unknown tools, invalid parameters, shell-free argv, minimal environment, timeout cleanup, noisy dual-stream output, truncation metadata, invalid UTF-8, and malformed diagnostic JSON fail safely. No live OpenStack deployment is required for Steps 1–4.

## Deployment and Rollback Contract

Deployment is a later authorized step and must remain disabled by default. It may add only the dedicated runner role and its exact two files under the revised source/runtime paths. It must not change the Phase 03 diagnostic toolbox allowlist or copy any historical runtime file.

Rollback is limited to reverting the dedicated runner contract and later dedicated implementation/deployment files. It must not alter Phase 03 diagnostics, identity material, protected inventory, profiles, OpenStack resources, or external evidence.

## Explicit Deferrals

The following are not completed by this contract:

- final result-envelope schema and reviewed examples;
- complete secret redaction behavior for result/audit payloads;
- complete audit event fields, permissions, rotation, retention, and integrity review;
- full safety regression suite;
- live deployment or live diagnostic execution;
- MCP integration;
- host diagnostics or operator-reader profiles;
- Phase 04 checklist completion or Phase 04 definition of done.
