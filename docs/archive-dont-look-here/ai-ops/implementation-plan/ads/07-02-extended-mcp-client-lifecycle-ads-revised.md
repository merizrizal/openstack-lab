## Architectural Design Specification: Phase 07 Extended — MCP Deployment Lifecycle Control

**Status:** Revised coordinated follow-on after Codex runtime-home and local MCP acceptance.

**Dependency order:** Phase 07 MCP integration -> `07-01-codex-runtime-home-ads-revised.md` Chunks 0-5 -> this ADS Chunks 0-4 -> `07-03-openai-remote-provider-boundary-ads-revised.md` Revised Chunks 0-7 -> Phase 99.

**Supersedes:** `07-extended-mcp-client-lifecycle-ads.md` where that document duplicates real-client acceptance and model-backend/provider decisions now owned by the runtime-home and remote-provider ADSs.

**Source:** Remaining Phase 07 lifecycle closure work from `docs/ai-ops/implementation-plan/07-mcp-integration.md`, live MCP evidence, the accepted Codex runtime-home/local-MCP boundary, and the boundary of `docs/ai-ops/implementation-plan/99-hardening-validation-and-rollout.md`.

**Goal:** Add a narrow, fail-closed, repository-managed way to install, remove, and restore only the deployed MCP adapter artifacts while preserving Codex runtime-home state, the manual runner, credentials, audit history, host diagnostics, and OpenStack Lab state.

---

### I. Overview and Contract

This ADS starts only after the Codex runtime-home ADS has proven:

- the reviewed Codex version is installed;
- Codex runs as `assistant` with the fixed assistant-owned runtime home;
- `/home/assistant` remains absent and the account remains non-interactive;
- the fixed local stdio MCP entry discovers the exact reviewed surface;
- the entry can be disabled and the adapter exits;
- remote model mode remains disabled.

Those client-acceptance responsibilities are not repeated here. This ADS owns only MCP deployment lifecycle control.

Expected flow:

```text
accepted Codex runtime-home and local MCP evidence
  -> disable the runtime-local Codex MCP entry
  -> prove no MCP adapter process remains
  -> dedicated lifecycle playbook validates `present`
  -> guarded `absent` removes only reviewed MCP artifacts
  -> manual runner, registry, credentials, diagnostics, and audit remain intact
  -> repeated `absent` is idempotent
  -> dedicated `present` restores the exact reviewed MCP surface
  -> repeated `present` is idempotent
  -> Phase 07 MCP validation passes again
  -> local Codex MCP entry may be re-enabled for a bounded smoke and disabled again
  -> hand off to the separate remote-provider gateway ADS
```

#### Scope boundary

Included:

- explicit MCP lifecycle state contract;
- one dedicated MCP-only Ansible playbook;
- extraction of existing MCP installation tasks into one lifecycle task owner;
- guarded removal of the adapter, policy, curated resources, and empty MCP directories;
- optional, separately confirmed removal of the pinned MCP SDK;
- preservation checks for the runner, registry, scripts, credentials, diagnostics, and audit path;
- idempotent reinstall and Phase 07 MCP regression validation;
- sanitized lifecycle evidence and accurate Phase 07 checklist updates.

Excluded and owned by `07-01-codex-runtime-home-ads-revised.md`:

- Codex installation or upgrade;
- Codex runtime-home creation or removal;
- client profile selection;
- real-client configuration, discovery, low-risk calls, and normal client disablement acceptance;
- changes to the `assistant` account or login shell.

Excluded and owned by `07-03-openai-remote-provider-boundary-ads-revised.md`:

- model/provider selection and activation;
- custom-provider configuration;
- loopback redaction gateway;
- provider credentials or manual login;
- egress, TLS, retention, training, telemetry, or remote acceptance;
- any provider-facing listener or service.

Also excluded:

- enabling restricted-host MCP tools;
- remote MCP transport, MCP listener, HTTP/SSE/WebSocket MCP, or an MCP service unit;
- deleting or inspecting Codex runtime-home contents;
- deleting audit history;
- changing or revoking the read-only OpenStack profile;
- comprehensive cross-phase status/secret regression owned by Phase 99;
- the unrelated shared-role Chrony idempotency defect.

#### Local Client Preconditions

The accepted local client command remains:

```text
/opt/openstack-ai-ops/.venv/bin/python /opt/openstack-ai-ops/mcp/aiops_mcp_server.py
```

Before `absent` may run:

- the Codex MCP entry must be disabled through the accepted runtime-local client operation;
- the exact adapter process must be absent;
- no lifecycle task may edit, delete, enumerate, copy, or back up `/opt/openstack-ai-ops/codex-home`;
- no provider or model session may be active.

The lifecycle playbook does not configure or invoke Codex. A bounded post-reinstall client smoke may use the already accepted runtime-home procedure, but client configuration remains runtime-local and uncommitted.

#### Lifecycle State Contract

Proposed variables:

```text
ai_ops_runtime_mcp_state: present
ai_ops_runtime_mcp_removal_confirmed: false
ai_ops_runtime_mcp_remove_sdk: false
```

Contract:

- `ai_ops_runtime_mcp_state` accepts only `present` or `absent` and defaults to `present`.
- `absent` requires `ai_ops_runtime_mcp_removal_confirmed=true`.
- `absent` must fail if the exact adapter process is active.
- `absent` must fail if the MCP root contains an entry outside the reviewed managed set.
- `absent` must reject symlinks, sockets, devices, FIFOs, or unexpected file types under the managed root.
- `ai_ops_runtime_mcp_remove_sdk=true` is valid only with `state=absent` and explicit removal confirmation.
- SDK removal must fail closed when reverse dependencies or environment ownership are uncertain.
- `present` must preserve current paths, modes, ownership, package pin, low-risk allowlist, and restricted-host default.

#### Managed Artifact Contract

The initial managed runtime set is exact:

```text
/opt/openstack-ai-ops/mcp/
/opt/openstack-ai-ops/mcp/aiops_mcp_server.py
/opt/openstack-ai-ops/mcp/mcp_policy.json
/opt/openstack-ai-ops/mcp/resources/
/opt/openstack-ai-ops/mcp/resources/diagnostic-safety.md
/opt/openstack-ai-ops/mcp/resources/metadata-troubleshooting.md
/opt/openstack-ai-ops/mcp/resources/lab-architecture.md
```

The pinned package is:

```text
mcp==1.28.1
```

The exact set must be derived from reviewed role defaults/templates and confirmed against deployed metadata in Chunk 0. Removal must name each managed file explicitly. Recursive deletion of the MCP root is prohibited.

Not managed by this ADS:

```text
/opt/openstack-ai-ops/codex-home/**
/opt/openstack-ai-ops/scripts/tool_runner/**
/opt/openstack-ai-ops/scripts/diagnostics/**
/opt/openstack-ai-ops/credentials/**
/opt/openstack-ai-ops/audit/**
```

#### Ansible Ownership Contract

A single task entrypoint owns MCP lifecycle:

```text
ansible/ai_ops_runtime/roles/assistant_runtime/tasks/mcp_lifecycle.yml
```

Existing MCP-specific directory, adapter, policy, resource, and SDK installation tasks move from broad task files into this entrypoint without changing present-state behavior.

A dedicated playbook:

```text
ansible/ai_ops_runtime/playbook_manage_mcp_lifecycle.yml
```

must:

- target only the approved `assistant01` host in the `assistant` group;
- invoke only the MCP lifecycle path;
- avoid the `common` role, account provisioning, client-runtime role, credentials, host diagnostics, provider gateway, and broad assistant setup;
- reject an ambiguous or multi-host target.

**Function Signature Contract:** not applicable. Existing Python MCP adapter and runner interfaces remain unchanged.

### II. Observed Evidence and Assumptions

#### Observed evidence

- Phase 07 has a deployed, live-validated local stdio MCP adapter with exact low-risk discovery, fixed runner delegation, audit correlation, bounded output, and no MCP listener.
- The existing evidence records that no repository-managed removal toggle exists.
- The current assistant-runtime role creates MCP directories and installs MCP artifacts from broad `workspace.yml`, `scripts.yml`, and `tooling.yml` paths.
- The shared virtual environment contains `mcp==1.28.1`; prior inspection found no installed reverse dependency, but this must be reconfirmed immediately before optional removal.
- The accepted Codex runtime-home ADS owns real-client acceptance and normal MCP-entry disablement.
- Phase 99 owns consolidated status propagation, broad secret/audit review, and cross-phase rollout checks, but not repository-managed MCP artifact removal.

#### Assumptions

- The Codex runtime-home ADS Chunks 0-5 are accepted before this ADS begins.
- The runtime-local MCP entry can be disabled without deleting Codex runtime-home state.
- The deployed MCP root still matches the reviewed managed set when Chunk 0 runs.
- The manual runner and MCP adapter share a Python virtual environment; SDK removal therefore remains optional and conservative.
- Reinstallation can use the dedicated lifecycle path without invoking broad host or credential setup.
- Remote-provider work has not begun and remains disabled throughout this ADS.

#### Open confirmations for Chunk 0

- Is the runtime-home/local-MCP handoff evidence complete and accepted?
- What exact process pattern uniquely identifies the adapter without matching unrelated Python processes?
- What exact entries and file types exist under the deployed MCP root?
- Which existing tasks currently own each MCP directory, file, template, and SDK installation?
- Does any installed package currently require `mcp`, and is SDK removal necessary at all?
- Does `ai_ops_runtime_directories` need to stop owning the MCP directories to prevent absent-state recreation?
- What preservation metadata can be recorded for runner, registry, credential, diagnostic, audit, and Codex runtime-home paths without reading sensitive contents?
- Does the dedicated playbook need check-mode exceptions for process and package-dependency inspection?

### III. Required Technical Dependencies and Imports

#### Existing repository dependencies

- `docs/ai-ops/implementation-plan/ads/07-01-codex-runtime-home-ads-revised.md`
- `docs/ai-ops/runtime/mcp-integration.md`
- `docs/ai-ops/runtime/phase07-mcp-integration-evidence-2026-07-12.md`
- the dated Codex runtime-home/local-MCP acceptance evidence
- `ansible/ai_ops_runtime/inventories/local/local.yml`
- `ansible/ai_ops_runtime/inventories/local/group_vars/all/common_vars.yml`
- `inventories/local/nodes.yml`
- `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml`
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/main.yml`
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/workspace.yml`
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/scripts.yml`
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/tooling.yml`
- `ansible/ai_ops_runtime/playbook_validate_phase07_mcp_integration.yml`
- `tests/ai_ops/test_mcp_server.py`
- `tests/ai_ops/test_tool_runner.py`

#### Proposed repository additions

- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/mcp_lifecycle.yml`
- `ansible/ai_ops_runtime/playbook_manage_mcp_lifecycle.yml`
- a dated sanitized MCP lifecycle evidence note under `docs/ai-ops/runtime/`

#### Ansible modules

Prefer built-in modules:

- `ansible.builtin.assert`
- `ansible.builtin.stat`
- `ansible.builtin.find`
- `ansible.builtin.file`
- `ansible.builtin.copy`
- `ansible.builtin.template`
- `ansible.builtin.pip`
- `ansible.builtin.command`
- `ansible.builtin.include_tasks`

`ansible.builtin.command` is permitted only for fixed-argv process inspection, Python package dependency inspection, exact `rmdir` behavior where needed, and accepted validation commands. Do not use `shell`.

#### Runtime dependencies

- existing `/opt/openstack-ai-ops/.venv/bin/python`;
- existing `mcp==1.28.1` in the present state;
- fixed filesystem paths and `assistant` identity;
- standard `pgrep`, `ss`, and filesystem metadata tools, checked before use.

No Codex package installation, model runtime, provider credential, public egress, remote MCP transport, or provider gateway dependency belongs in this ADS.

### IV. Step-by-Step Procedure / Execution Flow

#### A. Prerequisite and baseline

1. Verify the accepted runtime-home/local-MCP handoff evidence.
2. Confirm remote mode and provider work are disabled.
3. Disable the runtime-local Codex MCP entry using the accepted procedure.
4. Confirm the exact adapter process is absent and no MCP listener exists.
5. Run the existing Phase 07 MCP validation playbook as the baseline present-state proof.
6. Record metadata-only snapshots for managed MCP artifacts and preserved paths.

#### B. Lifecycle task extraction

1. Add lifecycle variables with current-compatible defaults.
2. Add a compile-safe lifecycle entrypoint that validates state and target scope.
3. Move existing MCP directory, adapter, policy, resource, and SDK present-state tasks into the lifecycle entrypoint.
4. Remove duplicate MCP ownership from `workspace.yml`, `scripts.yml`, and `tooling.yml`.
5. Include the lifecycle entrypoint from the broad role so default setup remains compatible.
6. Add the dedicated MCP-only lifecycle playbook.
7. Prove the dedicated `present` path is syntax-valid, lint-clean, and idempotent.

#### C. Guarded absent state

1. Require explicit removal confirmation.
2. Use a fixed process inspection contract and fail if the adapter is active.
3. Inspect the MCP root without following symlinks.
4. Compare observed relative paths and types to the exact managed set.
5. Fail on any unexpected entry or type before deleting anything.
6. Remove known resource files, policy, and adapter individually.
7. Remove `resources/` and the MCP root only after they are empty.
8. Optionally remove the SDK only when explicitly requested and dependency inspection proves safety.
9. Assert preserved runtime paths still exist with expected high-level types/ownership where non-sensitive.
10. Run a manual runner smoke after removal.
11. Run `absent` again and require no changes.

#### D. Restore and prove

1. Run the dedicated lifecycle playbook with `state=present`.
2. Run it again and require no MCP changes.
3. Run the Phase 07 MCP integration validation playbook.
4. Optionally re-enable the accepted local Codex MCP entry for one bounded discovery smoke.
5. Disable the entry again and confirm no adapter process remains.
6. Record only metadata, statuses, counts, and pass/fail assertions.
7. Update only Phase 07 lifecycle checklist items proven by the run.

#### E. Handoff

After lifecycle evidence is accepted, hand off to `07-03-openai-remote-provider-boundary-ads-revised.md`. That ADS may rely on the stable local MCP deployment and accepted client runtime but must not modify the lifecycle contract without a separate review.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
|---|---|---|---|
| Prerequisite | Runtime-home/local-MCP acceptance is incomplete | Stop before lifecycle edits or live removal | `ERR_MCP_LIFECYCLE_PREREQUISITE` |
| Client disable | Runtime-local MCP entry cannot be disabled cleanly | Stop; return to the runtime-home procedure | `ERR_MCP_CLIENT_DISABLE` |
| Active process | Exact adapter process exists during removal | Fail before filesystem/package changes | `ERR_MCP_PROCESS_ACTIVE` |
| State validation | State is not `present` or `absent` | Fail before any action | `ERR_MCP_STATE` |
| Removal approval | `absent` lacks explicit confirmation | Fail closed with no changes | `ERR_MCP_REMOVAL_CONFIRMATION` |
| Target scope | Dedicated playbook resolves zero, multiple, or wrong hosts | Fail before role invocation | `ERR_MCP_LIFECYCLE_TARGET` |
| Ownership migration | Duplicate MCP install ownership remains in broad task files | Fail validation; do not run live lifecycle | `ERR_MCP_TASK_OWNERSHIP` |
| Filesystem inspection | Unexpected entry, symlink, socket, device, FIFO, or type exists | Fail before deleting any artifact | `ERR_MCP_UNMANAGED_ARTIFACT` |
| Known-file removal | A managed file cannot be removed | Stop before directory cleanup | `ERR_MCP_ARTIFACT_REMOVAL` |
| Directory cleanup | Directory remains nonempty after known-file removal | Preserve directory and report remaining names only | `ERR_MCP_DIRECTORY_NOT_EMPTY` |
| SDK removal | Reverse dependency or ownership is uncertain | Preserve SDK and continue only if artifact removal remains valid | `ERR_MCP_SDK_DEPENDENCY` |
| Preservation | Runner, registry, credentials, diagnostics, audit, or runtime home changed/missing | Stop and treat as boundary violation | `ERR_MCP_ROLLBACK_BOUNDARY` |
| Runner smoke | Manual runner fails after removal | Stop; do not delete further state or claim success | `ERR_MCP_RUNNER_REGRESSION` |
| Reinstall | Present path cannot restore the exact reviewed surface | Keep client disabled and report failure | `ERR_MCP_REINSTALL` |
| Discovery | Post-restore surface differs from the reviewed set | Disable client and fail acceptance | `ERR_MCP_RESTORE_DISCOVERY` |
| Remote boundary | Provider, model, gateway, credential, or public egress work is introduced | Reject the change and defer to the provider ADS | `ERR_MODEL_REMOTE_EGRESS` |
| Evidence | Raw prompt, response, tool output, audit line, credential, or client config is retained | Delete unsafe draft and recreate metadata-only evidence | `ERR_MCP_EVIDENCE_SANITIZATION` |

### VI. Security, Integrity, Idempotency, and Cleanup

#### Security

- Keep MCP stdio-only and process-per-client-session.
- Never add an MCP listener, URL-mode MCP, service unit, firewall rule, or remote MCP transport.
- Run lifecycle automation only against the approved `assistant01` target.
- Never run the adapter or lifecycle operation as an interactive `assistant` login.
- Do not inspect, copy, template, delete, or commit Codex runtime-home contents.
- Do not enable restricted-host MCP tools.
- Do not add provider configuration, credentials, login, gateway, model request, or public egress.
- Require explicit confirmation for `absent`.
- Reject unknown filesystem entries instead of recursively deleting them.

#### Integrity

- Preserve existing owner/group/mode contracts in `present`.
- Validate lifecycle state before branching.
- Maintain one task owner for every MCP artifact and SDK action.
- Use exact managed paths and explicit file removal.
- Do not follow symlinks.
- Preserve runner, registry, diagnostic scripts, credentials, audit history, Codex runtime home, and OpenStack state.
- Tie checklist changes to sanitized observed evidence only.

#### Idempotency

- Default `present` reproduces current setup behavior.
- A second dedicated `present` run reports no MCP changes.
- A second confirmed `absent` run reports no changes.
- Missing known files are acceptable in `absent`; unknown files are not.
- Normal client disablement leaves no adapter process.
- Reinstall restores the same discovery surface and package pin.

#### Cleanup and rollback

- Normal operational rollback is client-entry disablement; artifact removal is a separately confirmed secondary action.
- Temporary inspection/evidence helpers are removed after validation.
- SDK removal remains optional; preserving the SDK is the safer default.
- A failed removal must not trigger recursive cleanup or deletion of non-MCP state.
- A failed restore leaves the client disabled until the exact surface is recovered.

### VII. Validation Strategy

Use the repository-approved temporary Python/Ansible environment. If the previously used environment no longer exists or is stale, create a new `/tmp` virtual environment from repository requirements.

#### Static validation

```bash
rtk /tmp/openstack-lab-phase07-lifecycle-venv/bin/ansible-playbook \
  -i ansible/ai_ops_runtime/inventories/local/local.yml \
  -e root_dir="$PWD" -e target_env=local \
  ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml \
  --syntax-check

rtk /tmp/openstack-lab-phase07-lifecycle-venv/bin/ansible-playbook \
  -i ansible/ai_ops_runtime/inventories/local/local.yml \
  -e root_dir="$PWD" -e target_env=local \
  ansible/ai_ops_runtime/playbook_manage_mcp_lifecycle.yml \
  --syntax-check

rtk /tmp/openstack-lab-phase07-lifecycle-venv/bin/ansible-lint \
  ansible/ai_ops_runtime/playbook_manage_mcp_lifecycle.yml \
  ansible/ai_ops_runtime/roles/assistant_runtime/tasks/mcp_lifecycle.yml
```

#### Contract and ownership checks

```bash
rtk grep -Rni "ai_ops_runtime_mcp_state\|ai_ops_runtime_mcp_removal_confirmed\|ai_ops_runtime_mcp_remove_sdk" \
  ansible/ai_ops_runtime

rtk grep -Rni "mcp_lifecycle.yml" ansible/ai_ops_runtime

rtk grep -RniE "mcp_python_package|aiops_mcp_server.py|mcp_policy.json|mcp_resources_path" \
  ansible/ai_ops_runtime/roles/assistant_runtime/tasks
```

The final result must show one lifecycle owner and no duplicate MCP installation tasks.

#### Existing Python regression

```bash
rtk /tmp/openstack-lab-phase07-lifecycle-venv/bin/python -m unittest \
  tests.ai_ops.test_tool_runner \
  tests.ai_ops.test_mcp_server
```

#### Live lifecycle validation

1. Confirm the Codex MCP entry is disabled.
2. Confirm no exact adapter process remains.
3. Run dedicated `absent` with explicit confirmation.
4. Run `absent` again; require no changes.
5. Run the manual-runner safety validation.
6. Verify preserved path metadata without reading sensitive contents.
7. Run dedicated `present`.
8. Run `present` again; require no changes.
9. Run the Phase 07 MCP validation playbook.
10. Optionally perform one accepted local-client discovery smoke, then disable the entry again.
11. Confirm no adapter process and no MCP listener remain.

#### Security and diff review

```bash
rtk git diff --check

rtk git diff -- \
  ansible/ai_ops_runtime/roles/assistant_runtime \
  ansible/ai_ops_runtime/playbook_manage_mcp_lifecycle.yml \
  docs/ai-ops/runtime/mcp-integration.md \
  docs/ai-ops/implementation-plan/07-mcp-integration.md

rtk grep -RniE "ansible\.builtin\.shell|rm -rf|recurse: true|0\.0\.0\.0|WebSocket|SSE|state: restarted" \
  ansible/ai_ops_runtime/roles/assistant_runtime/tasks/mcp_lifecycle.yml \
  ansible/ai_ops_runtime/playbook_manage_mcp_lifecycle.yml 2>/dev/null || true
```

Investigate every match. Documentation may mention prohibited mechanisms only as explicit exclusions.

### VIII. Thin Vertical Slice Chunk Design

Execute exactly one chunk at a time. Every chunk ends with targeted validation, scoped diff review, risk assessment, and an explicit stop.

#### Chunk 0: Lifecycle Integration Confirmation

- **Goal:** Confirm accepted prerequisites, exact MCP ownership/artifact contracts, adapter process matching, and SDK dependency state without editing.
- **Files to read:** this ADS; the accepted runtime-home ADS/evidence; assistant-runtime defaults/tasks; deployed MCP metadata; Phase 07 MCP runtime documentation/evidence.
- **Actions:** inspect Git state; confirm client entry disabled; inspect task ownership; collect sanitized `stat`/`find` metadata; inspect package dependencies; confirm the preserved-path metadata plan.
- **Do not:** configure Codex, invoke a model, contact a provider, remove files, or edit the repository.
- **Stop condition:** Produce a handoff containing exact managed paths/types, task migration plan, process pattern, SDK decision, and any blocker.

#### Chunk 1: Lifecycle State Contract and Compile-Safe Entry Point

- **Goal:** Add validated lifecycle variables and an inert lifecycle task entrypoint.
- **Files to change:** `roles/assistant_runtime/defaults/main.yml`; new `roles/assistant_runtime/tasks/mcp_lifecycle.yml`.
- **Implementation:** Validate `present|absent`, confirmation flag type, SDK flag relationship, and target assumptions. Do not move, install, or remove artifacts yet.
- **Validation:** YAML parse, targeted lint, setup playbook syntax, scoped diff.
- **Stop condition:** Contract exists but runtime behavior is unchanged.

#### Chunk 2: Present-State Migration and Dedicated Playbook

- **Goal:** Move all existing MCP installation ownership into the lifecycle entrypoint and add the narrow playbook.
- **Files to change:** lifecycle task; `workspace.yml`; `scripts.yml`; `tooling.yml`; `main.yml`; new `playbook_manage_mcp_lifecycle.yml`.
- **Implementation:** Preserve exact present-state paths, modes, owners, templates, package pin, allowlist, and restricted-host default. Remove duplicate ownership. Dedicated playbook invokes only lifecycle tasks.
- **Validation:** both playbook syntax checks, targeted lint, ownership grep, Python regressions, and—after explicit approval—two live `present` runs with zero changes on the second.
- **Stop condition:** Present behavior is uniquely owned and idempotent; no absent logic exists yet.

#### Chunk 3: Guarded Absent State

- **Goal:** Implement reviewable fail-closed artifact removal without executing live removal.
- **Files to change:** lifecycle task and `docs/ai-ops/runtime/mcp-integration.md`.
- **Implementation:** confirmation gate, exact process check, no-follow managed-entry inspection, explicit file removal, empty-directory removal, optional SDK logic, preservation assertions, and normal-disable versus artifact-removal documentation.
- **Validation:** syntax/lint, check-mode analysis, unsafe-pattern scan, Python regressions, scoped diff. Do not perform live removal.
- **Stop condition:** Absent logic is reviewable and fail-closed but unexecuted.

#### Chunk 4: Live Remove, Preserve, Restore, and Evidence

- **Goal:** Prove the complete lifecycle on `assistant01` and close the Phase 07 lifecycle gap.
- **Files to change:** dated sanitized lifecycle evidence; Phase 07 plan/checklist only for observed results.
- **Execution:** disable client; run confirmed `absent` twice; validate manual runner and preserved metadata; run `present` twice; rerun Phase 07 MCP validation; optionally perform and then disable one local-client discovery smoke.
- **Validation:** all live assertions, secret-pattern scan, final scoped diff, security/rollback review.
- **Stop condition:** Lifecycle control is evidence-backed, client is disabled, local MCP deployment is restored, remote mode remains disabled, and Phase 99 has not begun.

#### Handoff Gate: Remote Provider Gateway ADS

- **Prerequisites:** runtime-home ADS accepted; this lifecycle ADS Chunk 4 accepted; MCP deployment restored; client entry disabled; manual runner and Phase 07 MCP validation green; no provider configuration or remote traffic introduced.
- **Next document:** `docs/ai-ops/implementation-plan/ads/07-03-openai-remote-provider-boundary-ads-revised.md`.
- **Stop condition:** Begin only Revised Chunk 0 of that ADS. Do not fold provider work into this document.

### IX. Handoff to `chunked-implementation`

Start with:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.
Activate rtk-command-prefix for shell commands.

Task:
Implement Phase 07 Extended — MCP Deployment Lifecycle Control from the revised ADS.

Mode:
Execute Chunk 0 only. Do not edit files. Treat the accepted Codex runtime-home and local MCP evidence as prerequisites. Confirm the exact managed MCP artifact set and types, unique adapter process match, current task ownership, SDK reverse-dependency/removal decision, and preserved-path metadata plan. Confirm the runtime-local client entry is disabled. Do not configure Codex, invoke a model, contact a provider, remove artifacts, or begin Phase 99. Record the handoff and stop.
```

After Chunk 0:

```text
Resume from the accepted lifecycle handoff.
Execute exactly the next approved chunk only.
Do not configure a provider, change Codex runtime-home state, enable restricted-host tools, add remote MCP transport, use recursive deletion, or run broad host/credential setup.
Run chunk-specific validation, review the scoped diff, assess security and rollback risk, write the next handoff, and stop.
```

For live Chunk 4:

```text
Execute Chunk 4 only after explicit approval for live MCP artifact removal and restoration on assistant01.
Disable the accepted runtime-local client entry first. Stop on an active adapter, unexpected artifact/type, preservation failure, runner regression, reinstall failure, listener creation, credential concern, or any destructive ambiguity. Keep the client disabled and remote mode off after validation. Update evidence and checkboxes only for successful sanitized observations. Do not begin the remote-provider ADS or Phase 99 in the same run.
```

After the lifecycle handoff gate:

```text
Continue Phase 07 with `07-03-openai-remote-provider-boundary-ads-revised.md`.
Execute Revised Chunk 0 only. Treat both the accepted runtime-home/local-MCP evidence and the accepted MCP lifecycle evidence as prerequisites. Use only a temporary loopback fake Responses API provider and synthetic data. Do not contact OpenAI, log in, use a real credential, or enable permanent remote mode. Record the compatibility result and stop.
```

### X. Conclusion and Next Steps

The original extended ADS combined three different concerns: client-runtime acceptance, MCP artifact lifecycle, and model-provider selection. After the runtime-home and provider ADS revisions, only MCP artifact lifecycle belongs here.

This revised ADS therefore begins after Codex runtime-home/local-MCP acceptance and ends after guarded remove/restore behavior is proven. It never installs or configures Codex, selects a model backend, handles provider credentials, or introduces a remote data path.

The next action is Chunk 0 only: confirm the exact lifecycle integration contracts without editing or removing anything. After Chunks 0-4 are accepted and MCP is restored, the implementation may proceed to Revised Chunk 0 of the remote-provider gateway ADS.
