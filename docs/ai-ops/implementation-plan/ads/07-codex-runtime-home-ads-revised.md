## Architectural Design Specification: Phase 07 Codex Runtime-Home and Configuration Boundary

**Status:** Revised prerequisite and handoff contract.

**Dependency order:** Phase 07 MCP integration -> this ADS Chunks 0-5 -> `07-extended-mcp-client-lifecycle-ads-revised.md` Chunks 0-4 -> `07-openai-remote-provider-boundary-ads-revised.md` Revised Chunks 0-7 -> Phase 99.

**Source:** The Chunk 0 real-client blocker recorded against the original extended MCP-client ADS, the observed `assistant01` Codex CLI installation, and the coordinated lifecycle/provider ADS sequence.

**Goal:** Provide the prerequisite assistant-owned Codex runtime-home and local stdio MCP boundary without creating `/home/assistant`, changing the `assistant` login shell, exposing MCP remotely, or storing provider credentials, prompts, history, or client configuration in the repository. MCP artifact removal/restoration belongs to the next lifecycle ADS; remote-provider routing and redaction belong to the later gateway ADS.

---

### I. Overview and Contract

The existing `assistant` system account deliberately has `/usr/sbin/nologin` and no home directory. Codex CLI `0.144.1` uses `~/.codex/config.toml`; it can execute through `runuser` but warns when its configured home does not exist. The solution is a dedicated runtime home under the existing AI-OPS runtime root, not an interactive account home.

**Runtime-Home Contract (Conceptual):**

```text
ai_ops_runtime_codex_home: /opt/openstack-ai-ops/codex-home
owner/group: assistant:assistant
mode: 0700
state: present
```

- The path is fixed by repository-managed defaults, is owned only by `assistant`, and is not `/home/assistant`.
- Codex processes must run as `assistant` through a fixed-argv `runuser` invocation with `HOME` set to the fixed runtime-home path. No shell wrapper, login shell, caller-controlled home, or caller-controlled executable is allowed.
- The expected Codex configuration location is therefore `${HOME}/.codex/config.toml`, which is runtime-local and uncommitted.
- The MCP entry must use Codex's command-and-arguments stdio form and the existing fixed adapter command. Its configured name, executable, and arguments are reviewed values, not operator-supplied values.
- `model_mode=remote` records future backend intent only and remains separate from MCP transport. This ADS does not enable direct provider access. Any remote model use must wait until `07-extended-mcp-client-lifecycle-ads-revised.md` has restored and validated the local MCP deployment, then follow `07-openai-remote-provider-boundary-ads-revised.md` through its reviewed loopback gateway.
- The first implementation supports only `present`. Automatic deletion of the runtime home is excluded because it may contain operator-managed client configuration, credentials, or history; any removal design needs separate explicit confirmation and content classification.

**Generic AI-Client Runtime Role Contract (Conceptual):** A proposed `ansible/ai_ops_runtime/roles/ai_client_runtime` owns installation and runtime-home provisioning for an allowlisted client profile selected by `assistant01` inventory metadata. A proposed `ansible/ai_ops_runtime/playbook_setup_ai_client_runtime.yml` targets only the `assistant` group and invokes only this role; it must not include `common`, `assistant_runtime`, credentials, the MCP lifecycle, or remote-provider setup. The first profile maps `client: codex` and `version: "0.144.1"` to the observed global npm package `@openai/codex`; future clients add a reviewed role-default profile rather than new client-specific playbooks.

**Function Signature Contract:** not applicable. This is Ansible lifecycle configuration, controlled process invocation, and operator documentation; existing Python MCP and runner contracts remain unchanged.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/workspace.yml` creates `assistant` as a system user with `create_home: false` and `/usr/sbin/nologin`.
- Read-only inspection found `/home/assistant` absent.
- Codex CLI is installed on `assistant01` at `/opt/nodejs/bin/codex`, reports `codex-cli 0.144.1`, and documents `~/.codex/config.toml` as its default configuration path.
- `ansible/ai_ops_runtime/inventories/local/group_vars/all/common_vars.yml` records the non-secret `assistant01` selection: enabled Codex client, version `0.144.1`, and `model_mode: remote`; no provider or client configuration is present there.
- Codex `mcp add` supports `NAME -- COMMAND...`, which can launch the fixed adapter over stdio; `mcp remove NAME` provides the normal disable operation. The URL mode must not be used.
- `runuser -u assistant -- /opt/nodejs/bin/codex --version` succeeds but warns that it cannot create PATH aliases, consistent with the missing home directory.
- `ansible/ai_ops_runtime/playbook_validate_phase07_mcp_integration.yml` already uses fixed-argv `/usr/sbin/runuser -u assistant -- ...` for the temporary stdio validation client.
- The deployed MCP root contains exactly the adapter, policy, resources directory, and three curated resources with the expected `assistant:assistant` ownership and modes. The shared virtual environment contains `mcp==1.28.1` and has no installed reverse dependency on `mcp`.

#### Assumptions

- `/opt/openstack-ai-ops` remains the repository-managed local runtime root and is suitable for an `assistant`-owned `0700` child directory.
- The observed `/opt/nodejs/bin/codex` path and `0.144.1` behavior remain pinned for the first client-acceptance path; version changes require a new Chunk 0 confirmation.
- Setting `HOME` is sufficient for this Codex version. No XDG environment override is approved unless separately confirmed from version-specific help or documentation.
- The revised MCP lifecycle architecture is the immediate follow-on and must prove guarded removal/restoration while preserving this runtime home. The revised remote-provider architecture remains downstream and unimplemented until both prerequisite ADSs are accepted.

### III. Required Technical Dependencies and Imports

#### Existing dependencies

- `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml`
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/main.yml`
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/workspace.yml`
- `ansible/ai_ops_runtime/playbook_validate_phase07_mcp_integration.yml`
- `docs/ai-ops/runtime/mcp-integration.md`
- `docs/ai-ops/implementation-plan/ads/07-extended-mcp-client-lifecycle-ads-revised.md` as the immediate follow-on ADS
- `docs/ai-ops/implementation-plan/ads/07-openai-remote-provider-boundary-ads-revised.md` as the downstream provider ADS
- fixed `/usr/sbin/runuser`, `/usr/bin/env`, `/opt/nodejs/bin/codex`, and existing MCP adapter paths on `assistant01`

#### Inventory selection contract (concrete)

`ansible/ai_ops_runtime/inventories/local/group_vars/all/common_vars.yml` declares only the reviewed, non-secret selection on `assistant01`:

```text
ai_ops_client_runtime:
  enabled: true
  client: codex
  version: "0.144.1"
  model_mode: remote
```

These values select a profile; they do not contain an executable path, package source, provider endpoint, model name, credential, egress setting, client configuration, prompt, or history. `model_mode: remote` is declarative intent, not an activation flag. It does not authorize provider login, direct OpenAI access, custom-provider configuration, gateway deployment, or remote-model use.

#### Proposed role-default contracts

```text
ai_client_runtime_profiles:
  codex:
    installer: npm_global
    package: "@openai/codex"
    executable: /opt/nodejs/bin/codex
    runtime_home: "{{ ai_ops_runtime_root }}/codex-home"
    runtime_home_mode: "0700"
```

The generic role must reject an unsupported `client`, an unreviewed version, or an inventory profile that does not match the fixed role-default mapping. No credential, model, provider endpoint, provider API key, or client configuration content is a repository variable.

### IV. Step-by-Step Procedure / Execution Flow

1. The dedicated AI-client setup playbook asserts the target is only `assistant01` in the `assistant` group and invokes only `ai_client_runtime`.
2. The role reads the inventory selection, requires `enabled=true`, and rejects unknown keys, an unsupported client, an unreviewed version, or a model mode other than `local|remote` before installation.
3. The fixed role-default profile resolves `client: codex` and version `0.144.1` to global npm package `@openai/codex`; the installer and executable path are never inventory-provided.
4. The role installs or verifies only the selected allowlisted profile, then validates the resolved executable/version. A client switch is an inventory selection plus a reviewed profile addition, not a new playbook.
5. The role creates the fixed runtime-home directory with `assistant:assistant` ownership and mode `0700`; it does not create `/home/assistant` or modify the account shell.
6. Confirm fixed-argv invocation can run the approved client as `assistant` with `HOME` set to the runtime-home directory and without PATH-alias warnings or unintended listener creation.
7. After the runtime-home boundary is accepted, add or validate the reviewed local stdio MCP entry using the client-supported command-and-arguments form. This local MCP configuration does not require remote-provider approval and must never use URL/remote-MCP mode.
8. Confirm discovery and the reviewed low-risk MCP surface, then remove the entry with the supported client operation during rollback or acceptance cleanup.
9. Declare this ADS complete only when the Codex version, fixed `HOME`, local stdio MCP entry, warning-free invocation, and metadata-only evidence are accepted while remote mode remains disabled.
10. Hand off to `07-extended-mcp-client-lifecycle-ads-revised.md`. That ADS alone may move MCP installation ownership and implement guarded artifact removal/restoration; it must preserve this runtime home and client state.
11. After the lifecycle handoff is accepted and MCP is restored, proceed to `07-openai-remote-provider-boundary-ads-revised.md` for the loopback custom-provider route, redaction gateway, provider identity, egress controls, authentication compatibility, and remote acceptance.
12. Preserve the runtime-home contents. Do not copy them to evidence, logs, the OpenStack profile area, MCP policy, runner arguments, provider-gateway policy, or Git.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
|---|---|---|---|
| Profile selection | Inventory selection is missing, contains unsupported keys, or does not match a reviewed role-default profile | Fail before package or filesystem action; do not accept executable/package values from inventory | `ERR_AI_CLIENT_PROFILE` (proposed) |
| Client installation | The profile installer cannot verify the requested package version or resolved executable | Stop before runtime-home/client configuration | `ERR_AI_CLIENT_INSTALL` (proposed) |
| Runtime-home validation | Path is outside the fixed AI-OPS runtime root, is a symlink, or is not owned by `assistant` | Fail before client invocation; do not create an alternate path | `ERR_CODEX_HOME_BOUNDARY` (proposed) |
| Account boundary | Implementation tries to create `/home/assistant` or change `/usr/sbin/nologin` | Stop; reject the change | `ERR_CODEX_ACCOUNT_BOUNDARY` (proposed) |
| Client identity | Codex cannot run as `assistant` with the fixed `HOME`, or emits an alias/config permission warning | Keep MCP unconfigured and report the exact metadata-only failure | `ERR_CODEX_IDENTITY` (proposed) |
| Client configuration | Codex requires a shell string, URL mode, caller-controlled command, or caller-controlled environment for the MCP entry | Reject the configuration | `ERR_CODEX_MCP_BOUNDARY` (proposed) |
| Follow-on boundary | MCP artifact removal is attempted here, or provider work starts before lifecycle restoration is accepted | Reject the change; hand off first to the lifecycle ADS and then to the provider ADS | `ERR_CODEX_HANDOFF_BOUNDARY` (proposed) |
| Cleanup | Request attempts automatic removal of a nonempty runtime home | Preserve all contents; require a separately reviewed removal design | `ERR_CODEX_HOME_REMOVAL` (proposed) |
| Evidence | Client configuration, credential, prompt/history, or raw tool data is captured | Delete unsafe draft and retain metadata-only evidence | `ERR_CODEX_EVIDENCE_SANITIZATION` (proposed) |

### VI. Security, Integrity, Idempotency, and Cleanup

#### Security

- Keep the `assistant` account non-interactive and do not create `/home/assistant`.
- Constrain client state to one fixed `0700` runtime-home directory owned by `assistant`.
- Use `/usr/sbin/runuser` and `/usr/bin/env HOME=<fixed-path>` as fixed argv, never `shell`, `su -`, or a login session.
- Keep MCP stdio-only. Codex's URL option, remote MCP transport, listener, HTTP, SSE, and WebSocket MCP paths are prohibited.
- Do not use Codex MCP `--env` to inject provider credentials or OpenStack credentials into the adapter process.
- Do not implement MCP artifact removal in this ADS; that belongs to `07-extended-mcp-client-lifecycle-ads-revised.md`.
- Do not run `codex login`, configure a custom provider, store provider credentials, deploy a gateway, or perform model actions. Those actions belong exclusively to `07-openai-remote-provider-boundary-ads-revised.md` after both prerequisite ADSs are accepted.

#### Integrity and idempotency

- Re-running the `present` path must preserve mode and ownership and must not rewrite or inspect runtime-home contents.
- The role may create only the known runtime-home directory. It must not template, copy, delete, or commit the client configuration file.
- A client upgrade, executable-path change, or changed configuration semantics invalidates acceptance and requires a new discovery confirmation.

#### Cleanup

- Normal cleanup removes the reviewed MCP entry through the client's supported remove operation and closes the client session; it does not remove the runtime-home directory.
- A future destructive cleanup design must classify and explicitly confirm removal of provider credentials, client history, and configuration before acting.

### VII. Validation Strategy

#### Static and structural validation

```bash
rtk yq '.' ansible/ai_ops_runtime/inventories/local/group_vars/all/common_vars.yml >/dev/null
rtk yq '.' ansible/ai_ops_runtime/roles/ai_client_runtime/defaults/main.yml >/dev/null
rtk yq '.' ansible/ai_ops_runtime/roles/ai_client_runtime/tasks/main.yml >/dev/null
rtk /tmp/openstack-lab-phase07-chunk0-venv/bin/ansible-playbook \
  -i ansible/ai_ops_runtime/inventories/local/local.yml \
  -e root_dir="$PWD" -e target_env=local \
  ansible/ai_ops_runtime/playbook_setup_ai_client_runtime.yml --syntax-check
rtk /tmp/openstack-lab-phase07-chunk0-venv/bin/ansible-lint \
  ansible/ai_ops_runtime/playbook_setup_ai_client_runtime.yml \
  ansible/ai_ops_runtime/roles/ai_client_runtime
rtk git diff --check
```

#### Runtime metadata validation

After explicit implementation approval, use sanitized Ansible commands to verify only:

- the runtime-home path is a directory, not a symlink, has `assistant:assistant`, and mode `0700`;
- `/home/assistant` remains absent and the account remains `/usr/sbin/nologin`;
- the fixed client executable reports the reviewed version when launched under `runuser` with the fixed `HOME`;
- the prior PATH-alias/config permission warning is absent;
- no new listener appears during a version/help-only invocation.

No client configuration, credential, prompt/history, provider response, OpenStack profile, or raw tool result may be emitted in evidence. MCP artifact lifecycle work is blocked until this ADS completes; remote acceptance is additionally blocked until the lifecycle ADS restores and validates MCP and the provider ADS completes its fake-provider, redaction, gateway, identity/egress, authentication-compatibility, and remote synthetic-acceptance chunks.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full capability in one pass.

#### Chunk 0: Runtime-Home Integration Confirmation
- **Goal:** Confirm the approved client version, its documented home-based configuration contract, and the current no-home/account constraint without modifying host state.
- **Files to read:** this ADS, the Phase 07 extended ADS, current assistant-runtime defaults/tasks, and selected-client version/help output.
- **Commands:** sanitized Ansible `stat`, fixed-argv version/help, and metadata-only account inspection.
- **Evidence to confirm:** fixed executable, configuration-path behavior, the current permission warning, and no account mutation. Warning-free fixed-`HOME` execution is deferred until Chunk 4 creates the directory.
- **Stop condition:** Record evidence and blockers; do not create the runtime home or client configuration.

#### Chunk 1: Inventory Client-Selection Foundation
- **Goal:** Declare only the non-secret selected client, reviewed version, and model mode for `assistant01`.
- **Files to change:** `ansible/ai_ops_runtime/inventories/local/group_vars/all/common_vars.yml`.
- **Symbols to add/change:** `ai_ops_client_runtime.enabled`, `client`, `version`, and `model_mode`.
- **Implementation shape:** Selection-only YAML; it does not install a package or create a runtime home because no role consumes it yet.
- **Validation:** `rtk yq '.' ansible/ai_ops_runtime/inventories/local/group_vars/all/common_vars.yml >/dev/null` and scoped diff review.
- **Stop condition:** Inventory contains no executable, package source, provider, credential, endpoint, model name, or client configuration.

#### Chunk 2: Generic Role and Dedicated Playbook Stub
- **Goal:** Add an allowlisted generic client-runtime role and a dedicated assistant-only playbook with fail-closed profile validation but no installation.
- **Files to change:** `ansible/ai_ops_runtime/roles/ai_client_runtime/defaults/main.yml`; `ansible/ai_ops_runtime/roles/ai_client_runtime/tasks/main.yml`; `ansible/ai_ops_runtime/playbook_setup_ai_client_runtime.yml`.
- **Symbols to add/change:** `ai_client_runtime_profiles`, inventory-selection assertions, and the dedicated role invocation.
- **Implementation shape:** The initial profile maps `codex` to the fixed npm package/executable observed in Chunk 0. The task stub validates selection and exits without package, directory, account, client, or provider changes.
- **Validation:** YAML parse, dedicated-playbook syntax check, targeted `ansible-lint`, and scoped diff review.
- **Stop condition:** The standalone playbook is compile-safe and rejects invalid selections; the broad assistant setup playbook remains unchanged.

#### Chunk 3: Generic Client Installation Slice
- **Goal:** Make the generic role install or verify only the selected allowlisted client profile and its exact version.
- **Files to change:** `ansible/ai_ops_runtime/roles/ai_client_runtime/tasks/main.yml`; `ansible/ai_ops_runtime/roles/ai_client_runtime/tasks/install.yml`.
- **Symbols to add/change:** fixed installer dispatch, resolved executable/version assertion, and installer failure handling.
- **Implementation shape:** The initial profile uses global npm only for the reviewed package/version. Future client profiles must be added to role defaults and use their own reviewed installer; inventory cannot select an arbitrary package or command.
- **Validation:** syntax/lint, profile-selection tests or assertions, approved read-only version check, and scoped diff review. Live package installation requires explicit approval.
- **Stop condition:** The selected CLI is proven installed at the reviewed version; no runtime home, client configuration, login, or model action occurs.

#### Chunk 4: Assistant-Owned Runtime-Home Provisioning
- **Goal:** Provision only the selected profile's fixed `0700` runtime-home directory.
- **Files to change:** `ansible/ai_ops_runtime/roles/ai_client_runtime/tasks/main.yml`; `ansible/ai_ops_runtime/roles/ai_client_runtime/tasks/runtime_home.yml`.
- **Symbols to add/change:** fixed runtime-home path assertion and directory task.
- **Implementation shape:** Use built-in `assert` and `file`; preserve `/home/assistant`, the login shell, client configuration contents, all MCP artifacts, and the broad assistant-runtime role.
- **Validation:** dedicated-playbook syntax/lint and approved read-only `stat` verification after an explicit live-apply approval.
- **Stop condition:** Directory metadata is proven and the selected CLI runs under `assistant` with the fixed `HOME`; MCP and remote model use remain unconfigured.

#### Chunk 5: Controlled Client Invocation and Local MCP Acceptance
- **Goal:** Document and validate fixed-argv Codex invocation with the runtime home and the reviewed local stdio MCP entry, without credentials or live remote-model use.
- **Files to change:** `docs/ai-ops/runtime/mcp-integration.md`; a dated sanitized evidence note only if invocation and local MCP discovery are approved and observed.
- **Symbols to add/change:** controlled `runuser`/`HOME` invocation, version prerequisite, fixed MCP add/remove contract, expected low-risk discovery surface, rollback, and evidence exclusions.
- **Implementation shape:** Validate version/help, warning-free fixed-home startup, and local MCP command-and-arguments semantics. Use only the reviewed adapter command; never use URL mode, a shell wrapper, provider login, custom-provider configuration, or remote traffic.
- **Validation:** compare commands with installed client help, verify exact MCP discovery, verify no unexpected listener, remove/re-add behavior, review evidence for sensitive patterns, and run `rtk git diff --check`.
- **Stop condition:** The runtime-home and local MCP client boundary is evidence-backed and ready for the dependent lifecycle ADS; MCP artifact removal and all provider work remain blocked.

#### Handoff Gate: Revised MCP Lifecycle ADS
- **Goal:** End this ADS cleanly and start repository-managed MCP artifact lifecycle work only after Chunks 0-5 are accepted.
- **Prerequisites:** reviewed Codex version installed; fixed runtime home present with correct ownership/mode; `/home/assistant` absent; account remains non-interactive; fixed-argv invocation is warning-free; local MCP stdio discovery and normal client disablement are proven; remote mode is disabled.
- **Next document:** `docs/ai-ops/implementation-plan/ads/07-extended-mcp-client-lifecycle-ads-revised.md`.
- **Implementation shape:** This handoff adds no lifecycle or provider code. The next ADS begins with lifecycle-only discovery, then owns task extraction, guarded removal, restoration, and lifecycle evidence. It must not modify or remove the Codex runtime home.
- **Validation:** Review the runtime-home evidence and assert no MCP artifact removal toggle, provider endpoint, custom provider, gateway listener, provider identity, credential, authentication state, or remote request was introduced by this ADS.
- **Stop condition:** The prerequisite handoff is accepted. Do not treat lifecycle or provider work as an internal Chunk 6 of this document.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.
Activate rtk-command-prefix for shell commands.

Task:
Implement the controlled assistant-owned runtime-home boundary described by the latest Phase 07 client-runtime ADS.

Mode:
Execute Chunk 2 only. Add the generic role/playbook profile-validation stub. Do not install a client, create directories, change the account, configure the client, authenticate, or invoke a remote model. Run targeted syntax/lint validation, review the scoped diff, and stop.
```

After Chunk 2 is accepted, execute exactly Chunks 3, 4, and 5 one at a time with targeted validation, scoped diff review, risk assessment, and an explicit stop after each chunk.

After Chunk 5 and the handoff gate are accepted, use this prompt for the dependent ADS:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.
Activate rtk-command-prefix for shell commands.

Task:
Continue Phase 07 with `07-extended-mcp-client-lifecycle-ads-revised.md`.

Mode:
Execute Chunk 0 only. Treat the accepted runtime-home and local MCP evidence as prerequisites. Confirm the exact managed MCP artifact set, task ownership, adapter process match, SDK dependency state, and preservation metadata plan. Do not modify the runtime-home role, configure Codex, remove artifacts, contact a provider, log in, or enable remote mode. Record the lifecycle handoff and stop.
```

### X. Conclusion and Next Steps

The approved client can run as `assistant`, but its default home-based configuration model is incompatible with the intentionally home-less system account. A dedicated `assistant`-owned `0700` runtime home under `/opt/openstack-ai-ops` resolves that boundary without granting interactive account access or weakening the MCP contract.

This ADS is the prerequisite client-runtime layer. It ends after local Codex invocation and local stdio MCP discovery are proven with remote mode still disabled. The revised MCP lifecycle ADS is the immediate dependent implementation; the revised remote-provider ADS follows only after lifecycle restoration is accepted. Neither may be folded into this document as Chunk 6.

**Deferred enhancement TODO:** evaluate an alternative MCP-capable client and `model_mode=local` only through a new client/backend discovery confirmation. The alternative must use the same fixed stdio adapter, `assistant` identity, runtime-local uncommitted configuration, fail-closed data boundary, and no remote MCP exposure. This TODO does not authorize a local model runtime, provider egress, credential storage, or client replacement.

The inventory-selection foundation is recorded. Next action: obtain approval to execute Chunk 2, which creates only the generic role and dedicated playbook validation stub. Continue through Chunks 3-5 one at a time. Only after the handoff gate is accepted should the implementation agent begin Chunk 0 of `07-extended-mcp-client-lifecycle-ads-revised.md`; the provider ADS remains downstream.
