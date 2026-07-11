## Architectural Design Specification: Phase 07 Extended — Local AI Client Acceptance and MCP Lifecycle Control

**Source:** Remaining Phase 07 closure work from `docs/ai-ops/implementation-plan/07-mcp-integration.md`, the live evidence in `docs/ai-ops/runtime/phase07-mcp-integration-evidence-2026-07-12.md`, and the boundary of `docs/ai-ops/implementation-plan/99-hardening-validation-and-rollout.md`.

**Goal:** Close the MCP-specific operational gaps that Phase 99 does not explicitly own by proving one approved local AI client can use and disable the stdio adapter on `assistant01`, and by adding a narrow, fail-closed, repository-managed way to install or remove MCP deployment artifacts without changing the manual runner, credentials, audit history, host diagnostics, or OpenStack Lab state.

---

### I. Overview and Contract

Phase 07 already has a deployed and live-validated local stdio MCP adapter. The extension does not redesign the adapter or broaden its authority. It adds two operational slices:

1. **Real-client acceptance:** select one approved local AI client, configure it locally on `assistant01` to launch the fixed adapter command as `assistant`, prove discovery and low-risk calls through that client, disable the entry, and prove the adapter exits.
2. **Repository-managed lifecycle control:** extract MCP deployment into a narrowly callable Ansible task path supporting explicit `present` and `absent` states, with guarded removal and a dedicated playbook that does not run the broad common, credential, host-diagnostic, or general runtime setup paths.

Expected flow:

```text
existing MCP runtime validation passes
  -> operator selects one local AI client
  -> client configuration uses fixed command and argv over stdio
  -> client discovers exact reviewed surface
  -> client performs reviewed low-risk calls
  -> client entry is disabled and session closes
  -> adapter process and listener absence are confirmed
  -> dedicated lifecycle playbook can remove only reviewed MCP artifacts
  -> manual runner, credentials, audit history, and OpenStack state remain intact
  -> dedicated lifecycle playbook can reinstall MCP idempotently
  -> Phase 07 evidence/checklists are updated only for observed outcomes
```

#### Scope boundary

Included:

- one approved local AI-client acceptance path on `assistant01`;
- client enable, discovery, low-risk call, disconnect, and disable proof;
- sanitized acceptance evidence without client history or diagnostic payloads;
- an explicit MCP lifecycle state contract;
- a dedicated MCP-only lifecycle playbook;
- guarded removal of the adapter, policy, curated resources, and empty MCP directories;
- optional explicit removal of the pinned MCP SDK from the shared virtual environment;
- reinstall and manual-runner regression validation.

Excluded because Phase 99 already owns them:

- comprehensive MCP propagation tests for `timeout`, `truncated`, `unavailable`, `denied`, and other runner statuses;
- repository-wide secret scanning and review of sample result/audit output;
- cross-phase rollout order, general operational support notes, and consolidated safety regression commands.

Also excluded:

- enabling restricted-host MCP tools;
- remote MCP transport, listener, service, HTTP, SSE, or WebSocket support;
- committing client-specific credentials, local client configuration, prompts, history, or payloads;
- changing or revoking the read-only OpenStack profile;
- deleting audit history;
- fixing the shared `common` role Chrony restart, which is a separate idempotency defect.

#### Local Client Launch Contract (Concrete)

The deployed fixed launch command is:

```text
/opt/openstack-ai-ops/.venv/bin/python /opt/openstack-ai-ops/mcp/aiops_mcp_server.py
```

- The client must execute the command directly with a command-and-arguments configuration, not through a shell string or wrapper.
- The client and adapter must run as `assistant`.
- Transport must remain local stdio.
- No caller-controlled executable, adapter path, credential path, registry path, audit path, client ID, or transport value is allowed.
- The accepted surface remains exactly three low-risk project tools, three curated resources, and three diagnostic prompts.
- The client configuration itself remains runtime-local and uncommitted.

**Client Configuration Contract (Conceptual):** The selected client's configuration key, file path, CLI syntax, and disable operation must be confirmed in Chunk 0 from that client's installed version and official/local help. No product-specific path or command is approved by this ADS in advance.

#### Lifecycle State Contract (Conceptual)

Proposed Ansible variables:

```text
ai_ops_runtime_mcp_state: present
ai_ops_runtime_mcp_removal_confirmed: false
ai_ops_runtime_mcp_remove_sdk: false
```

- `ai_ops_runtime_mcp_state` accepts only `present` or `absent` and defaults to `present` to preserve current setup behavior.
- `absent` requires `ai_ops_runtime_mcp_removal_confirmed=true`; omission must fail before changing files.
- Removal must fail while the exact adapter command is running.
- Removal must fail if the MCP directory contains entries outside the reviewed managed set.
- SDK removal must require both `state=absent` and `ai_ops_runtime_mcp_remove_sdk=true`.
- The dedicated lifecycle playbook must target only the sole `assistant01` host.

**Ansible Task Contract (Conceptual):** A proposed `tasks/mcp_lifecycle.yml` owns MCP directories, adapter, policy, resources, and pinned SDK state. Existing MCP install tasks in `scripts.yml` and `tooling.yml` move into this file without changing their present-state behavior.

**Playbook Contract (Conceptual):** A proposed `playbook_manage_mcp_lifecycle.yml` loads the existing inventory/node variables, asserts target scope, and invokes only the MCP lifecycle task entrypoint. It must not include the broad `common` role or credential management.

**Function Signature Contract:** not applicable. The extension is Ansible lifecycle automation, client operation, documentation, and evidence work. Existing Python MCP and runner interfaces remain unchanged.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops/runtime/phase07-mcp-integration-evidence-2026-07-12.md` records a successful deployment and local SDK-client validation on `assistant01`: exact discovery, valid and invalid calls, fixed audit origin, no listener, and process exit all passed.
- The same evidence states that no real AI-client configuration was introduced and that the role has no dedicated MCP artifact-removal toggle.
- `docs/ai-ops/implementation-plan/07-mcp-integration.md` still leaves the initial real-client connection and Step 7 client setup/rollback outcomes unchecked.
- `docs/ai-ops/runtime/mcp-integration.md` already defines the fixed command, runtime identity, local stdio boundary, normal client-disable rollback, and desired repository-managed removal boundary.
- `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml` defines fixed MCP paths, `mcp==1.28.1`, the low-risk allowlist, and disabled restricted-host exposure.
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/scripts.yml` currently creates MCP directories and installs the adapter, policy, and three resources alongside non-MCP scripts.
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/tooling.yml` currently installs the pinned MCP SDK alongside baseline and OpenStack Python tooling.
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/main.yml` invokes workspace, scripts, optional credentials, and tooling as one broad role path.
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/workspace.yml` creates directories from `ai_ops_runtime_directories`; that list currently includes `mcp`.
- No dedicated tests for Ansible role structure were found under `tests/ai_ops`; repository validation currently relies on Ansible syntax/lint, Python tests, and live playbook runs.
- Existing `tests/ai_ops/test_mcp_server.py` already covers stdio lifecycle, fixed runner argv/audit origin, timeout mapping, envelope bounds, cancellation, and default restricted-host exclusion.
- Phase 99 explicitly owns consolidated status regressions, secret/audit review, and general MCP disablement documentation, but does not require a real AI-client acceptance run or a dedicated MCP artifact-removal implementation.

#### Assumptions

- The operator will choose and approve one AI client that is installed or installable locally on `assistant01` and supports MCP stdio command-and-arguments configuration.
- The selected client can be run under the existing `assistant` account without granting a login shell or broader credentials; if this is false, Chunk 0 must stop and request a revised operating method.
- Client acceptance can be demonstrated without committing the runtime-local client configuration.
- The shared Python virtual environment may contain packages that depend on `mcp`; therefore SDK removal is opt-in and must be checked before execution.
- Removal is expected to act only on the exact repository-managed MCP paths. Unexpected files are operator-owned or suspicious and must block recursive deletion.
- Reinstallation should use the dedicated lifecycle path, not the broad setup playbook, once that path exists.

#### Open confirmations for Chunk 0

- Which AI client and exact installed version are approved?
- What official configuration path or CLI operation adds and disables a local stdio MCP command for that version?
- Can the selected client run as `assistant` despite the account's `/usr/sbin/nologin` shell, or is a controlled `runuser` invocation required?
- Does the client emit or retain raw payloads/history by default, and how can evidence collection avoid those stores?
- What exact process tree and exit behavior does the real client produce after disable/disconnect?
- Does any installed package in `/opt/openstack-ai-ops/.venv` require `mcp`, and should SDK removal be approved?
- What exact managed-entry allowlist exists under `/opt/openstack-ai-ops/mcp` after deployment?

### III. Required Technical Dependencies and Imports

#### Existing repository dependencies

- `ansible/ai_ops_runtime/inventories/local/local.yml`
- `inventories/local/nodes.yml`
- `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml`
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/main.yml`
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/workspace.yml`
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/scripts.yml`
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/tooling.yml`
- `ansible/ai_ops_runtime/playbook_validate_phase07_mcp_integration.yml`
- `docs/ai-ops/runtime/mcp-integration.md`
- `docs/ai-ops/runtime/phase07-mcp-integration-evidence-2026-07-12.md`
- `docs/ai-ops/implementation-plan/07-mcp-integration.md`
- `tests/ai_ops/test_mcp_server.py`
- `tests/ai_ops/test_tool_runner.py`

#### Proposed repository additions

- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/mcp_lifecycle.yml`
- `ansible/ai_ops_runtime/playbook_manage_mcp_lifecycle.yml`
- a dated sanitized client-acceptance/lifecycle evidence note under `docs/ai-ops/runtime/`, or an extension to the existing Phase 07 evidence after review

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
- `ansible.builtin.include_role` or `ansible.builtin.include_tasks`

`ansible.builtin.command` is acceptable for exact `pgrep`, `rmdir`, package dependency inspection, and client/version inspection where no safer module provides the needed contract. Do not use `shell`.

#### Runtime dependencies

- existing `/opt/openstack-ai-ops/.venv/bin/python`;
- existing `mcp==1.28.1` for the present state;
- selected approved AI client and its verified local stdio support;
- `pgrep`, `ss`, and standard filesystem tools already available on `assistant01` or explicitly checked before use.

No new network service, listener, daemon, or remote transport dependency is permitted.

### IV. Step-by-Step Procedure / Execution Flow

#### A. Real-client acceptance

1. Confirm the selected AI client, version, execution identity, configuration mechanism, and local data-retention behavior.
2. Run the existing Phase 07 validation playbook as a precondition.
3. Configure the client runtime-locally with the fixed executable and adapter argument. Do not use a shell wrapper or commit the configuration.
4. Start the client as `assistant` and establish one local stdio MCP session.
5. Verify exact discovery of the reviewed three tools, three resources, and three prompts.
6. Invoke the three low-risk project tools using the reviewed project-visible server identifier.
7. Record only sanitized names, statuses, request IDs or correlation counts, process identity, transport, and pass/fail assertions.
8. Disable or remove the client entry and close the session.
9. Confirm the exact adapter process no longer exists and no new listener exists.
10. Confirm the manual runner still works.
11. Update only client-acceptance and documented enable/disable checklist items supported by evidence.

#### B. Lifecycle task extraction

1. Add and validate the explicit lifecycle variables with current-compatible defaults.
2. Add a compile-safe lifecycle task entrypoint that initially asserts state and target scope.
3. Move existing MCP directory, adapter, policy, resource, and SDK present-state tasks into the lifecycle entrypoint without changing paths, ownership, modes, package pin, or default restricted-host policy.
4. Include the lifecycle entrypoint from the existing broad role so default setup behavior remains unchanged.
5. Add the dedicated lifecycle playbook that invokes only this task entrypoint.
6. Prove the dedicated `present` path is syntax-valid and idempotent.

#### C. Guarded absent state

1. Require explicit removal confirmation.
2. Inspect the exact adapter process pattern and fail if any adapter is active.
3. Inspect MCP directory contents without following symlinks.
4. Compare observed entries to the exact managed allowlist and fail on any unexpected path, symlink, socket, or non-regular managed-file type.
5. Remove only the known resource files, policy, and adapter.
6. Remove resource and MCP directories only after they are empty; do not use recursive directory deletion as a shortcut.
7. Optionally remove `mcp==1.28.1` only when SDK removal is explicitly requested and dependency inspection permits it.
8. Assert runner, registry, approved scripts, credential profile, diagnostics, and audit path still exist and were not modified.
9. Run a manual runner smoke after removal.
10. Re-run `absent` to prove idempotency.

#### D. Reinstall and evidence

1. Run the dedicated lifecycle playbook with `state=present`.
2. Re-run it to prove MCP-specific idempotency.
3. Run the existing Phase 07 MCP integration validation playbook.
4. Confirm the real client can be re-enabled only after the artifacts are restored.
5. Disable the client again and verify process/listener absence.
6. Record sanitized lifecycle results and update only proven Phase 07 checklist items.
7. Stop before Phase 99 implementation.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
|---|---|---|---|
| Client selection | No approved client/version or no stdio support | Stop before configuration; record the missing decision | `ERR_MCP_CLIENT_UNSELECTED` (proposed) |
| Client identity | Client cannot run as `assistant` without broadening account access | Stop; do not change shell or grant extra privileges | `ERR_MCP_CLIENT_IDENTITY` (proposed) |
| Client configuration | Client requires shell-string execution, remote URL, or caller-controlled paths | Reject configuration and keep client disabled | `ERR_MCP_CLIENT_BOUNDARY` (proposed) |
| Client discovery | Surface differs from the exact reviewed tools/resources/prompts | Disable entry, close session, retain sanitized mismatch only | `ERR_MCP_CLIENT_DISCOVERY` (proposed) |
| Client call | Low-risk call lacks structured status or audit correlation | Disable entry and stop acceptance | `ERR_MCP_CLIENT_AUDIT` (proposed) |
| Client shutdown | Adapter survives disconnect or a listener appears | Terminate only the adapter-owned process; treat as security failure | `ERR_MCP_CLIENT_LIFECYCLE` (proposed) |
| State validation | Lifecycle state is not `present` or `absent` | Fail before any filesystem/package action | `ERR_MCP_STATE` (proposed) |
| Removal approval | `absent` requested without explicit confirmation | Fail closed with no changes | `ERR_MCP_REMOVAL_CONFIRMATION` (proposed) |
| Active process | Adapter process exists during removal | Fail and instruct operator to disable client first | `ERR_MCP_PROCESS_ACTIVE` (proposed) |
| Filesystem inspection | Unexpected entry, symlink, socket, or type exists under MCP root | Fail; do not recursively remove anything | `ERR_MCP_UNMANAGED_ARTIFACT` (proposed) |
| Known-file removal | A managed file cannot be removed | Stop before directory removal and report exact path | `ERR_MCP_ARTIFACT_REMOVAL` (proposed) |
| Directory cleanup | Directory is nonempty after known files are removed | Preserve directory and report remaining names without contents | `ERR_MCP_DIRECTORY_NOT_EMPTY` (proposed) |
| SDK removal | Other installed packages depend on MCP or dependency state is uncertain | Preserve SDK and report removal not proven safe | `ERR_MCP_SDK_DEPENDENCY` (proposed) |
| Preservation check | Runner, registry, credentials, diagnostics, or audit path changed/missing | Stop rollback validation and report boundary violation | `ERR_MCP_ROLLBACK_BOUNDARY` (proposed) |
| Runner regression | Manual runner fails after MCP removal | Treat rollback as failed; do not delete further state | `ERR_MCP_RUNNER_REGRESSION` (proposed) |
| Reinstall | Dedicated present path cannot restore reviewed artifacts | Keep client disabled; report failed task | `ERR_MCP_REINSTALL` (proposed) |
| Evidence | Raw payload, prompt, history, credential, or audit line is captured | Delete unsafe draft, sanitize from source metadata, and re-review | `ERR_MCP_EVIDENCE_SANITIZATION` (proposed) |

### VI. Security, Integrity, Idempotency, and Cleanup

#### Security

- Keep transport stdio-only and process-per-client-session.
- Never add a service unit, listener, remote endpoint, firewall rule, or bind address.
- Run the client and adapter as `assistant`, never root.
- Do not change the `assistant` login shell merely to accommodate a client.
- Keep fixed executable, adapter, runner, registry, audit, and credential paths.
- Do not enable restricted-host MCP tools.
- Do not store or commit client configuration, history, prompts, payloads, environment dumps, credentials, or raw audit records.
- Require explicit confirmation for destructive lifecycle state.

#### Integrity

- Preserve the existing owner/group/mode contracts.
- Validate lifecycle state before task branching.
- Inspect directory contents before removal and reject unknown entries.
- Do not follow symlinks during inspection or removal.
- Remove exact managed files rather than recursively deleting the MCP root.
- Preserve the manual runner, tool registry, approved scripts, credentials, diagnostics, and audit history.
- Keep Phase 07 checkbox changes tied to sanitized runtime evidence.

#### Idempotency

- Default `present` must reproduce current setup behavior.
- A second dedicated `present` run must report no MCP changes.
- A second confirmed `absent` run must succeed with no changes.
- Missing known MCP artifacts are acceptable in the absent state; unexpected artifacts are not.
- Client enablement should not create a persistent adapter service.
- Client disablement must leave no adapter process.

#### Cleanup and rollback

- The temporary/real client entry must be disabled after acceptance unless the operator separately approves ongoing use.
- Runtime-local client configuration must be removed or disabled using the selected client's supported mechanism.
- Temporary evidence helpers must be removed.
- Normal rollback is client disablement; artifact removal is an explicit secondary operation.
- SDK removal remains optional and separately confirmed.
- Reinstallation must be possible through the dedicated lifecycle playbook without running common host or credential tasks.

### VII. Validation Strategy

Validation is chunk-aware. Use the existing temporary Python environment `/tmp/openstack-lab-phase07-chunk9-venv` for Python/Ansible commands while it remains valid; otherwise create a new `/tmp` virtual environment and install repository requirements before executing Python or Ansible validation.

#### Static validation

```bash
rtk /tmp/openstack-lab-phase07-chunk9-venv/bin/ansible-playbook \
  -i ansible/ai_ops_runtime/inventories/local/local.yml \
  -e root_dir="$PWD" -e target_env=local \
  ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml \
  --syntax-check

rtk /tmp/openstack-lab-phase07-chunk9-venv/bin/ansible-playbook \
  -i ansible/ai_ops_runtime/inventories/local/local.yml \
  -e root_dir="$PWD" -e target_env=local \
  ansible/ai_ops_runtime/playbook_manage_mcp_lifecycle.yml \
  --syntax-check

rtk /tmp/openstack-lab-phase07-chunk9-venv/bin/ansible-lint \
  ansible/ai_ops_runtime/playbook_manage_mcp_lifecycle.yml \
  ansible/ai_ops_runtime/roles/assistant_runtime/tasks/mcp_lifecycle.yml
```

#### Contract and symbol checks

```bash
rtk grep -Rni "ai_ops_runtime_mcp_state\|ai_ops_runtime_mcp_removal_confirmed\|ai_ops_runtime_mcp_remove_sdk" \
  ansible/ai_ops_runtime
rtk grep -Rni "mcp_lifecycle.yml" ansible/ai_ops_runtime
rtk grep -RniE "state: absent|pgrep|rmdir" \
  ansible/ai_ops_runtime/roles/assistant_runtime/tasks/mcp_lifecycle.yml
```

Confirm that `scripts.yml` and `tooling.yml` no longer own duplicate MCP present-state tasks after migration.

#### Existing Python regression

```bash
rtk /tmp/openstack-lab-phase07-chunk9-venv/bin/python -m unittest \
  tests.ai_ops.test_tool_runner \
  tests.ai_ops.test_mcp_server
```

Phase 99 remains responsible for expanding comprehensive status and secret/audit regression coverage.

#### Live client acceptance

Run only after client selection and explicit approval:

- existing Phase 07 validation playbook passes;
- client process and adapter run as `assistant`;
- exact discovery matches reviewed names;
- reviewed low-risk calls return structured statuses and correlated audit metadata;
- disabling the entry closes stdio and leaves no adapter process;
- listener snapshot is unchanged;
- no client configuration or payload is committed.

The exact client commands are intentionally deferred to Chunk 0 confirmation.

#### Live lifecycle validation

1. Disable the client and prove no adapter process remains.
2. Run dedicated `absent` with explicit confirmation.
3. Run `absent` again; expect no changes.
4. Run manual runner smoke; expect success.
5. Verify preserved paths and audit history existence without reading sensitive contents.
6. Run dedicated `present`.
7. Run `present` again; expect no changes.
8. Run the existing Phase 07 MCP validation playbook; expect all assertions to pass.

#### Security and diff review

```bash
rtk git diff --check
rtk git diff -- \
  ansible/ai_ops_runtime/roles/assistant_runtime \
  ansible/ai_ops_runtime/playbook_manage_mcp_lifecycle.yml \
  docs/ai-ops/runtime/mcp-integration.md \
  docs/ai-ops/implementation-plan/07-mcp-integration.md
rtk grep -RniE "0\.0\.0\.0|http://|https://|WebSocket|SSE|shell:|state: restarted|recursive" \
  ansible/ai_ops_runtime/roles/assistant_runtime/tasks/mcp_lifecycle.yml \
  ansible/ai_ops_runtime/playbook_manage_mcp_lifecycle.yml 2>/dev/null || true
```

Investigate every match. Documentation references to prohibited transports are acceptable only when clearly stated as exclusions.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass.

#### Chunk 0: Client and Lifecycle Integration Confirmation
- **Goal:** Select the approved local AI client and confirm its exact version-specific stdio configuration/disable contract, process identity, data-retention behavior, and the managed MCP artifact allowlist.
- **Files to read:**
  - `docs/ai-ops/runtime/mcp-integration.md`
  - `docs/ai-ops/runtime/phase07-mcp-integration-evidence-2026-07-12.md`
  - selected client's installed help/configuration documentation
  - `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/{main,workspace,scripts,tooling}.yml`
  - deployed `/opt/openstack-ai-ops/mcp` metadata through sanitized Ansible inspection
- **Commands:**
  - `rtk git status --short`
  - selected client version/help commands, determined only after client selection
  - `rtk grep -Rni "MCP\|mcp" ansible/ai_ops_runtime/roles/assistant_runtime docs/ai-ops/runtime/mcp-integration.md`
  - sanitized Ansible `stat`/`find` inspection of managed paths
- **Evidence to confirm:** exact client add/disable mechanism, execution identity, no shell wrapper, no remote transport, no unsafe history capture, process exit semantics, known artifact paths, and SDK dependency decision.
- **Stop condition:** Record decisions and blockers. Do not edit files or configure the client.

#### Chunk 1: Client-Specific Acceptance Procedure
- **Goal:** Add a reviewed, version-specific operator procedure for the selected client without committing runtime-local configuration.
- **Files to change:**
  - `docs/ai-ops/runtime/mcp-integration.md`
- **Symbols to add/change:** client/version prerequisite, exact local add/enable steps, sanitized acceptance checklist, exact disable steps, and evidence exclusions.
- **Implementation shape:** Extend the existing generic command-and-arguments guidance with the confirmed client operation. Keep the fixed launch command and `assistant` identity. Do not add credentials or remote transport.
- **Validation:**
  - verify documented commands against selected client `--help` or official versioned docs;
  - `rtk git diff -- docs/ai-ops/runtime/mcp-integration.md`;
  - `rtk git diff --check`.
- **Stop condition:** A maintainer has an exact client procedure, but no runtime configuration or acceptance claim has been made.

#### Chunk 2: Real-Client Enable, Acceptance, and Disable Evidence
- **Goal:** Prove one approved client can use the reviewed MCP surface and then disable it cleanly.
- **Files to change:**
  - dated Phase 07 client-acceptance evidence under `docs/ai-ops/runtime/`;
  - `docs/ai-ops/implementation-plan/07-mcp-integration.md` only for newly proven client/Step 7 items.
- **Symbols to add/change:** sanitized client/version, exact discovery names, low-risk status assertions, audit-correlation count/origin, process identity, listener delta, and post-disable process state.
- **Implementation shape:** Configure only runtime-local client state, run the acceptance sequence, disable/remove the client entry, and retain metadata-only evidence. Do not retain raw output, history, prompts, resource bodies, or audit lines.
- **Validation:**
  - run `rtk /tmp/openstack-lab-phase07-chunk9-venv/bin/ansible-playbook -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_validate_phase07_mcp_integration.yml -e ai_ops_mcp_validation_server_identifier=control_plane_vm01` before acceptance;
  - run the selected-client acceptance/disable commands confirmed in Chunk 0;
  - run an exact adapter `pgrep` and `ss -H -lntu` comparison through reviewed Ansible commands after disable;
  - run `rtk grep -RniE 'BEGIN (RSA|EC|OPENSSH) PRIVATE KEY|password[=:]|token[=:]|secret[=:]' <dated-evidence-file> 2>/dev/null || true`;
  - run `rtk git diff -- <dated-evidence-file> docs/ai-ops/implementation-plan/07-mcp-integration.md` and `rtk git diff --check`.
- **Stop condition:** Real-client acceptance and disablement are evidenced, no adapter remains, and unproven Phase 07 items remain unchecked.

#### Chunk 3: Lifecycle State Contract and Compile-Safe Entry Point
- **Goal:** Introduce validated lifecycle variables and a compile-safe MCP task entrypoint without moving or removing current install behavior yet.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/mcp_lifecycle.yml` (new)
- **Symbols to add/change:** `ai_ops_runtime_mcp_state`, `ai_ops_runtime_mcp_removal_confirmed`, `ai_ops_runtime_mcp_remove_sdk`; state-validation assertion.
- **Implementation shape:** The new task file validates `present|absent` and returns without artifact changes. This is the Ansible equivalent of a compile-safe stub. Default `present` preserves behavior because existing install tasks remain in place for this chunk.
- **Validation:**
  - `rtk yq '.' ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml >/dev/null`;
  - `rtk yq '.' ansible/ai_ops_runtime/roles/assistant_runtime/tasks/mcp_lifecycle.yml >/dev/null`;
  - `rtk /tmp/openstack-lab-phase07-chunk9-venv/bin/ansible-lint ansible/ai_ops_runtime/roles/assistant_runtime/tasks/mcp_lifecycle.yml`;
  - `rtk git diff -- ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml ansible/ai_ops_runtime/roles/assistant_runtime/tasks/mcp_lifecycle.yml`.
- **Stop condition:** Variables and fail-closed state assertion exist; no call site or runtime behavior has changed.

#### Chunk 4: Present-State Migration and Dedicated Playbook
- **Goal:** Move existing MCP installation into the lifecycle entrypoint and add a narrow MCP-only playbook while preserving default setup behavior.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/mcp_lifecycle.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/scripts.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/tooling.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/main.yml`
  - `ansible/ai_ops_runtime/playbook_manage_mcp_lifecycle.yml` (new)
- **Symbols to add/change:** present-state directory/copy/template/pip tasks, role include, dedicated playbook target assertion.
- **Implementation shape:** The five-file exception is justified because one coherent move must eliminate duplicate ownership while keeping every referenced task available. Use `when: ai_ops_runtime_mcp_state == 'present'`; keep paths, modes, owner/group, package pin, and policy defaults unchanged. The dedicated playbook invokes only lifecycle tasks.
- **Validation:**
  - run syntax checks for `playbook_setup_assistant_runtime.yml` and `playbook_manage_mcp_lifecycle.yml` using the commands in Section VII;
  - run the Section VII `ansible-lint` command;
  - run `rtk grep -RniE 'Install AI-OPS MCP|mcp_python_package|mcp_resources_path' ansible/ai_ops_runtime/roles/assistant_runtime/tasks` and verify lifecycle-task ownership is unique;
  - run `rtk /tmp/openstack-lab-phase07-chunk9-venv/bin/python -m unittest tests.ai_ops.test_tool_runner tests.ai_ops.test_mcp_server`;
  - when live execution is approved, run the dedicated playbook twice with `-e ai_ops_runtime_mcp_state=present` and require zero MCP changes on the second run.
- **Stop condition:** Both setup and dedicated lifecycle paths install the same reviewed MCP surface; the dedicated path does not run common or credential tasks.

#### Chunk 5: Guarded Artifact Removal
- **Goal:** Implement the explicit, fail-closed absent state without recursive deletion or collateral changes.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/mcp_lifecycle.yml`
  - `docs/ai-ops/runtime/mcp-integration.md`
- **Symbols to add/change:** removal confirmation assertion, exact process check, managed-entry inspection/allowlist, known-file removal, empty-directory removal, optional SDK removal, preservation assertions.
- **Implementation shape:** Require confirmation; fail on active adapter or unexpected entries; remove known files individually; remove directories only when empty; preserve all non-MCP runtime paths. Document exact normal-disable versus artifact-removal behavior.
- **Validation:**
  - run the lifecycle playbook syntax and Section VII `ansible-lint` commands;
  - run `rtk grep -nE 'ansible\.builtin\.shell|recurse: true|rm -rf|state: restarted' ansible/ai_ops_runtime/roles/assistant_runtime/tasks/mcp_lifecycle.yml` and require no unsafe match;
  - run `rtk /tmp/openstack-lab-phase07-chunk9-venv/bin/ansible-playbook -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_manage_mcp_lifecycle.yml -e root_dir="$PWD" -e target_env=local -e ai_ops_runtime_mcp_state=absent -e ai_ops_runtime_mcp_removal_confirmed=true --check` only after confirming check-mode behavior is non-destructive;
  - run `rtk git diff -- ansible/ai_ops_runtime/roles/assistant_runtime/tasks/mcp_lifecycle.yml docs/ai-ops/runtime/mcp-integration.md` and `rtk git diff --check`;
  - do not perform live removal in this chunk.
- **Stop condition:** The absent path is reviewable and fail-closed but has not yet been executed against `assistant01`.

#### Chunk 6: Live Remove, Preserve, Reinstall, and Evidence
- **Goal:** Prove lifecycle removal and restoration on `assistant01` without affecting manual diagnostics or OpenStack state.
- **Files to change:**
  - dated sanitized Phase 07 lifecycle evidence under `docs/ai-ops/runtime/`;
  - `docs/ai-ops/implementation-plan/07-mcp-integration.md` only where the run proves completion.
- **Symbols to add/change:** removal/repeat-removal results, preservation assertions, manual runner smoke status, reinstall/repeat-reinstall results, final MCP validation status.
- **Implementation shape:** Disable client; run confirmed absent twice; validate runner and preserved paths; run present twice; rerun Phase 07 MCP validation; keep client disabled afterward unless separately approved.
- **Validation:**
  - with explicit live approval, run the dedicated lifecycle playbook twice with `-e ai_ops_runtime_mcp_state=absent -e ai_ops_runtime_mcp_removal_confirmed=true`;
  - run `rtk /tmp/openstack-lab-phase07-chunk9-venv/bin/ansible-playbook -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_validate_phase04_tool_runner_safety_gateway.yml -e root_dir="$PWD"` as the manual-runner regression;
  - run the dedicated lifecycle playbook twice with `-e ai_ops_runtime_mcp_state=present`;
  - run `rtk /tmp/openstack-lab-phase07-chunk9-venv/bin/ansible-playbook -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_validate_phase07_mcp_integration.yml -e ai_ops_mcp_validation_server_identifier=control_plane_vm01`;
  - run the evidence secret-pattern scan, `rtk git diff --check`, and a final scoped diff/security review.
- **Stop condition:** Lifecycle control is evidence-backed, Phase 07 closure state is accurate, and Phase 99 has not begun.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.
Activate rtk-command-prefix for shell commands.

Task:
Implement Phase 07 Extended — Local AI Client Acceptance and MCP Lifecycle Control from docs/ai-ops/implementation-plan/ads/07-extended-mcp-client-lifecycle-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm the approved client/version, exact local stdio configuration and disable mechanism, assistant identity compatibility, client data-retention behavior, managed artifact allowlist, and SDK dependency/removal decision. Stop after reporting evidence and blockers.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Resume from the Phase 07 extended ADS and latest handoff.
Execute Chunk 1 only.
Do not continue to Chunk 2.
After editing, run targeted documentation validation, review git diff, assess security risk, and stop.
```

For lifecycle implementation:

```text
Use the chunked-implementation skill.
Resume from the latest Phase 07 extended handoff.
Execute exactly the next approved chunk only.
Do not enable remote transport, restricted-host MCP tools, recursive MCP directory deletion, or broad runtime rollback.
Run chunk-specific syntax/lint/tests, review the scoped diff, assess security and rollback risk, and stop.
```

For live lifecycle validation:

```text
Use the chunked-implementation skill.
Execute Chunk 6 only after explicit approval for artifact removal and restoration on assistant01.
Disable the client first. Stop on an active adapter, unexpected artifact, preservation failure, manual-runner regression, credential issue, listener creation, or any destructive implication. Update evidence and checkboxes only after successful sanitized validation. Do not begin Phase 99.
```

### X. Conclusion and Next Steps

This extension is justified because real-client acceptance and repository-managed MCP artifact removal are Phase 07 operational closure concerns not explicitly guaranteed by Phase 99. Keeping them in a separate extended ADS prevents Phase 99 from silently inheriting unresolved client and lifecycle design decisions.

The extension must remain narrow: one approved local client, fixed stdio launch, no committed client state, no restricted-host expansion, and exact MCP-only lifecycle control. Comprehensive status-equivalence testing and secret/audit review remain Phase 99 responsibilities. The Chrony repeat-change remains a separate common-role idempotency issue.

Next recommended action: execute Chunk 0 only to select the client and confirm its version-specific configuration, identity, retention, process-lifecycle, and SDK-removal constraints before editing runtime or Ansible files.
