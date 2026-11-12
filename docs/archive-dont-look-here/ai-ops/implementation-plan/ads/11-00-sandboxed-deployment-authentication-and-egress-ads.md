## Architectural Design Specification: Sandboxed Orchestrator Deployment, Authentication, and Egress

**Source:** `docs/ai-ops/implementation-plan/11-sandboxed-deployment-authentication-and-egress.md`

**Goal:** Implement the pinned public Codex SDK adapter behind a still-disabled remote gate, deploy the locally validated orchestrator under a dedicated sandboxed identity, preserve credential and MCP privilege separation, define operator-owned opaque Codex authentication, and prove temporary synthetic egress plus rollback without making a provider request.

**Status:** Draft for review. Implementation must begin with Chunk 0. Phase 11 does not authorize a provider request or enable the official adapter for remote invocation.

---

### I. Overview and Contract

#### Selected phase boundary

```text
reviewed repository artifacts and hash lock
  -> mocked public-SDK adapter contract, remote-disabled
  -> dedicated non-root orchestrator identity and protected Codex home
  -> deterministic fake-only on-demand deployment
  -> deployed fake workflow with network denied
  -> operator-owned supported Codex login/status/logout procedure
  -> disabled-by-default identity egress policy
  -> approved non-provider synthetic HTTPS window
  -> unconditional rollback and permanent-policy revalidation
  -> Phase 12 remains separately approval-gated
```

Phase 11 separates four authorities:

1. **Repository orchestrator:** validates workflow input, applies redaction and bounds, owns local evidence, and remains the only workflow-policy authority.
2. **Codex SDK/runtime:** owns supported ChatGPT authentication and opaque provider transport. Repository code never receives Codex credential values.
3. **Existing MCP/runner boundary:** owns reviewed diagnostic execution and OpenStack credential use. The new Codex identity must not gain general read access to `assistant` credentials or runtime state.
4. **Ansible/operator boundary:** owns deterministic installation, identity/filesystem policy, authentication approval, egress activation, rollback, and sanitized validation.

The default deployed mode is fake-backed and network-disabled. A real adapter may be importable and mock-testable, but production selection and provider invocation remain disabled. Phase 12 must not consume an implicit Phase 11 approval.

#### Official SDK adapter contract

**Function Signature Contract (Concrete):** the repository protocol remains:

```text
CodexAdapter.run_turn(request, policy, cancellation) -> AsyncIterator[AdapterEvent]
```

The adapter owns a terminal `AdapterResult`. Inputs are the existing `DiagnosticTurnRequest`, `RuntimePolicy`, and cancellation event. Outputs are only closed `AdapterEvent` and `AdapterResult` values; raw SDK objects, IDs, messages, errors, usage payloads, prompts, and tool output cannot escape the adapter.

**Function Signature Contract (Conceptual):** a revised `build_curated_codex_config(policy)` and an injected SDK client/runtime factory will:

- select only the pinned public `openai-codex==0.144.4` API;
- set the fixed working directory, reviewed model alias, read-only sandbox, fixed approval mode, zero unreviewed configuration overrides, and an explicit minimal environment;
- configure no web search, API key, custom provider, base URL, proxy, remote MCP, caller-selected executable, or caller-selected environment;
- enforce one workflow, one turn, zero automatic retries, the repository deadline, one interrupt on cancellation/timeout, and bounded cleanup;
- map only recognized public lifecycle/status values into existing closed repository categories;
- fail closed on unknown SDK events, unsupported public options, or pinned-version contract drift.

The compile-safe Chunk 1 stub must retain `OFFICIAL_ADAPTER_ENABLED = False`, return `VENDOR_BLOCKED / REAL_ADAPTER_DISABLED`, and refuse SDK runtime construction. It must not return success.

#### Real MCP compatibility gate

The current public repository contract does not prove a callback through which the orchestrator can validate and redact an MCP result before the Codex runtime consumes it. Phase 10 proved that boundary only for `FakeCodexAdapter` through `LocalOrchestrator._complete_fake_tool()` and `LocalMcpClientProtocol`.

Therefore:

- mocked SDK lifecycle implementation may proceed in Phase 11;
- no real adapter test may start Codex, configure live MCP, authenticate, perform DNS, or open a provider socket;
- real remote selection remains disabled unless Chunk 0 confirms a supported public pre-consumption seam or approves a separate local stdio policy adapter that preserves Phase 10 redaction;
- observing SDK tool events after consumption is not an enforcement seam;
- unresolved compatibility yields `VENDOR_BLOCKED / MCP_INTERCEPTION_UNSUPPORTED`, not a weaker redaction path.

#### Dedicated deployment identity and filesystem contract

**Configuration Contract (Conceptual):** select in Chunk 0 a dedicated non-root system identity, proposed as `aiops-orchestrator`, distinct from `assistant` and `aiops-provider`.

Proposed fixed layout, subject to Chunk 0 confirmation:

```text
application root: /opt/openstack-ai-ops/orchestrator        root-owned, not writable by service
virtualenv:       /opt/openstack-ai-ops/orchestrator/venv   root-owned, hash-locked
working root:     /var/lib/aiops-orchestrator/work           service-owned, bounded
Codex home:       /var/lib/aiops-orchestrator/codex-home     service-owned, mode 0700
orchestrator log/evidence root: /var/lib/aiops-orchestrator/evidence, mode 0700
unit:             aiops-orchestrator@.service or equivalent on-demand fixed launcher
```

The deployment must not reuse `/opt/openstack-ai-ops/codex-home`, the `assistant` account, `aiops-provider`, provider-gateway paths, or historical gateway evidence. Application files and dependency locks are root-owned and immutable to the service identity. Only the exact work, Codex-home, and new orchestrator-evidence paths are writable.

The unit is on-demand, has no `WantedBy` auto-start requirement, opens no listener, accepts only a closed invocation profile, clears proxy/environment inheritance, uses a restrictive umask, and applies the strongest compatible systemd sandbox controls. A fake-only invocation profile must be the sole default.

#### MCP/credential privilege-separation contract

Current MCP and runner execution relies on the `assistant` runtime, including OpenStack profile files owned `assistant:assistant` with mode `0600`. Directly running that path as the proposed orchestrator identity is not currently valid. Granting the Codex process broad read access to those credentials is prohibited.

Chunk 0 must choose and approve one concrete local boundary before deployment:

1. a fixed privilege-separated local stdio bridge that lets the orchestrator/Codex side access only reviewed MCP operations while the credential-bearing runner remains under `assistant`; or
2. another reviewed mechanism that prevents the Codex process from opening credential files while preserving local stdio, exact tool allowlists, independent result redaction, timeout/cancellation, audit correlation, and no listener.

A shared group, ACL, copied credential, sudo rule, setuid helper, Unix socket, or service split is **not approved by this ADS merely by being listed**. Each changes the threat model and must be selected in Chunk 0 with exact permissions and failure behavior. If no mechanism satisfies the boundary, deployed fake acceptance may use a credential-free MCP fixture, but Phase 11 cannot claim the deployed authoritative runner path complete.

#### Deployable entrypoint contract

**Function Signature Contract (Conceptual):** a proposed package entrypoint accepts no arbitrary prompt, path, adapter, command, URL, environment, or egress setting. It selects one compile-time/repository-reviewed invocation profile:

- `validate-local-fake`: fixed synthetic request, `FakeCodexAdapter`, fixed local MCP/fixture policy, bounded temporary or production evidence writer, and network-disabled execution;
- `remote`: absent or explicitly disabled in Phase 11.

The temporary Chunk 3 entrypoint must fail with a fixed category if a real adapter is requested. This provides an invocable deployment path without claiming remote readiness.

#### Authentication operations contract

Authentication is an operator action using only supported pinned Codex commands under the dedicated identity and fixed Codex home.

- Automation may verify executable version and runtime-home metadata, but never list or read runtime-home contents.
- Login/device code, browser URL, token, account identifier, raw status, refresh details, and logout output are never registered, logged, copied, parsed, displayed by Ansible, or retained as evidence.
- If automation validates a command, it uses `no_log: true`, suppresses stdout/stderr, and retains only a closed success/failure category and return-code class.
- Login egress requires a fresh explicit approval and a bounded temporary policy. Failure must not broaden destinations or trigger credential inspection.
- Logout/recovery preserves the home unless the operator uses the supported logout command. Automation must not delete credential files.

#### Egress policy contract

The proposed dedicated-identity egress role has closed modes:

```text
disabled   -> loopback/local IPC only, then owner reject
synthetic  -> exact approved non-provider numeric destination(s), exact protocol/port,
              bounded expiry, then owner reject
login      -> separately approved supported-auth capability, only if Chunk 0 can bound it honestly
remote     -> defined for later review but not activated in Phase 11
```

`disabled` is permanent and default. `synthetic` and `login` are temporary, approval-gated, and always roll back to `disabled`. Phase 11 must not install a general proxy, caller-selected URL/hostname, arbitrary CIDR, unrestricted destination, or provider-specific private route assertion.

Because Codex controls vendor routing, a future remote policy may be enforceable only as identity + DNS + TCP/443 capability rather than fixed host/path policy. The ADS requires honest documentation: if the supported runtime's egress cannot meet the threat model, stop with a blocker. Do not claim host, route, content-type, or private endpoint guarantees not provided by the vendor.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops/implementation-plan/11-sandboxed-deployment-authentication-and-egress.md` requires a mocked real adapter, deterministic sandboxed deployment, a deployed fake workflow with network disabled, opaque operator authentication, bounded egress, and synthetic rollback without a provider request.
- `ansible/ai_ops_runtime/files/orchestrator/requirements.in` pins `openai-codex==0.144.4`, `mcp==1.28.1`, and exact local validation tools; `requirements.lock` includes the exact `openai-codex-cli-bin==0.144.4` runtime dependency.
- `official_codex_adapter.py` currently defines `OFFICIAL_ADAPTER_ENABLED = False`, a minimal `build_curated_codex_config()`, terminal result mapping, and a disabled adapter that never constructs `AsyncCodex`.
- `test_official_codex_adapter.py` proves the adapter fails before runtime entry and statically excludes login, account, turn, interrupt, and retry calls.
- `contracts.py` already contains closed workflow/event/error categories, fixed MCP command/arguments, one-turn/one-tool limits, deadlines, cleanup bounds, and the `CodexAdapter` protocol.
- `LocalOrchestrator._complete_fake_tool()` is explicitly guarded by `isinstance(..., FakeCodexAdapter)`. The official adapter therefore has no implemented repository-owned tool request/result handshake.
- The orchestrator package has no reviewed deployment entrypoint or script in `pyproject.toml`; its package dependency list is empty even though the external hash lock contains runtime dependencies.
- `ai_client_runtime` currently deploys global npm Codex `0.144.1`, creates `/opt/openstack-ai-ops/codex-home` as `assistant:assistant` mode `0700`, deploys the historical provider gateway, and enforces the `assistant` egress role. That role cannot be reused unchanged for the new orchestrator architecture.
- `assistant_runtime/tasks/credentials.yml` deploys `clouds.yaml` and `secure.yaml` as `assistant:assistant` mode `0600`. The proposed orchestrator identity cannot read them, and making them readable to the Codex process would expand credential exposure.
- The existing provider-gateway systemd template demonstrates root-owned units, proxy unsetting, `UMask=0077`, `NoNewPrivileges`, `PrivateTmp`, `PrivateDevices`, `ProtectSystem=strict`, `ProtectHome`, kernel/control-group protections, address-family restriction, empty capability sets, and exact writable paths. Its identity, service behavior, listener, paths, and evidence cannot be reused.
- `assistant_egress`, `assistant_egress_validation`, and `assistant_device_auth_egress` demonstrate UFW preflight, owner matching, restore-test validation, materialization/order checks, approval expiry, marker-only rollback, and `always` cleanup. Their fixed `assistant` identity and historical endpoint tuples are not valid Phase 11 defaults.
- `playbook_operate_device_auth_egress_window.yml` already establishes the operator-owned pause pattern and prohibits capturing authentication output, but it targets `assistant` and the old runtime home.
- `docs/ai-ops/runtime/phase07-codex-sdk-orchestrator-decision-2026-07-21.md` requires a dedicated identity, opaque Codex credentials, minimum DNS/HTTPS capability, unchanged `assistant` denial, no generic proxy, and a stop if egress cannot be bounded honestly.

#### Assumptions

- The accepted Python SDK/runtime pair remains `0.144.4`; the older global npm Codex `0.144.1` is historical and is not the deployment source for the orchestrator.
- Hash-locked installation into a root-owned dedicated virtual environment is the deterministic deployment method, but the exact executable exposed by `openai-codex-cli-bin` must be confirmed without provider use in Chunk 0.
- The dedicated identity can own only new Codex state, work, and orchestrator evidence; it must not own or modify assistant MCP artifacts, OpenStack credentials, or gateway evidence.
- A systemd on-demand template unit is preferred over a daemon because no listener or unattended recurring execution is required. The exact invocation mechanism remains proposed until Chunk 0.
- Temporary egress can be tested against an operator-approved non-provider HTTPS endpoint using numeric destinations and sanitized result categories.
- Authentication endpoint scope may change with the vendor. No existing Phase 07 destination tuple is assumed valid for Phase 11.

#### Accepted Chunk 0 local-boundary decisions

The following repository-controlled decisions are accepted for the later implementation chunks. They do not authorize a provider request or change `OFFICIAL_ADAPTER_ENABLED = False`.

- **Identity and layout:** create the non-login `aiops-orchestrator` identity. Only `/var/lib/aiops-orchestrator/work`, `/var/lib/aiops-orchestrator/codex-home`, and `/var/lib/aiops-orchestrator/evidence` are service-writable. The application root, virtual environment, unit files, and policy artifacts are root-owned.
- **Credential-preserving MCP split:** retain the credential-bearing reviewed runner under `assistant`, using the existing `aiops-project-reader` credential profile. Deploy an `assistant`-owned local Unix-socket bridge that accepts only the reviewed MCP operations, validates peer UID `aiops-orchestrator`, applies the existing request bounds, independently validates/redacts the result, and returns only the sanitized result envelope.
- **Bridge permissions:** use a dedicated `aiops-mcp-client` group only for bridge connectivity. The bridge socket is `assistant:aiops-mcp-client`, mode `0660`; `aiops-orchestrator` is its only non-`assistant` member. The orchestrator/Codex process receives no credential-file, assistant-home, or gateway-ledger access. The Unix socket is local IPC, not a TCP listener.
- **Real-MCP redaction seam:** configure any future Codex MCP integration only through a local stdio proxy that forwards to the bridge. The proxy has no credentials and forwards a result to Codex only after bridge-side validation and redaction. Direct real-Codex access to the existing MCP stdio adapter is prohibited.
- **Sandbox form:** use a non-enabled, on-demand `Type=oneshot` validation unit with fixed invocation only; clear proxy variables; set `UMask=0077`, `NoNewPrivileges=true`, `PrivateTmp=true`, `PrivateDevices=true`, `ProtectSystem=strict`, `ProtectHome=true`, empty capability sets, and an exact writable-path allowlist.
- **Egress and rollback:** materialize permanent loopback/local-IPC access followed by IPv4 and IPv6 owner rejects for `aiops-orchestrator`. Synthetic exceptions require approved numeric non-provider tuples, bounded expiry, restore-tested marker blocks before the permanent reject, and unconditional marker removal plus permanent-reject validation in an `always` cleanup path. Existing `assistant` rules and historical tuples remain independent and unchanged.

#### Pinned SDK/CLI artifact verification (completed in Chunk 0)

A temporary verification virtual environment installed the committed hash-locked `openai-codex==0.144.4` and `openai-codex-cli-bin==0.144.4` artifacts. Public source inspection confirmed `AsyncCodex`, `CodexConfig`, `ApprovalMode`, `Sandbox`, `AsyncThread.turn()`, `AsyncTurnHandle.stream()`, `AsyncTurnHandle.interrupt()`, and `TurnResult`. `TurnStatus` is closed to `completed`, `interrupted`, `failed`, and `inProgress`. The bundled executable is `codex_cli_bin/bin/codex`; help-only validation confirmed `codex login`, `codex login status`, and `codex logout`.

No SDK client was constructed and no authentication, account-status operation, runtime-home inspection, DNS, provider access, or firewall change occurred. Repository code must continue to prohibit API-key and access-token login options, retain `OFFICIAL_ADAPTER_ENABLED = False`, and fail closed if a future installed artifact differs from this contract.

#### Remaining confirmations and implementation proofs

- Implement and prove the accepted local stdio-proxy/Unix-socket bridge: exact peer authorization, fixed MCP operation surface, assistant-owned credential access, pre-Codex result validation/redaction, timeout/cancellation, audit correlation, and no TCP listener. Until this proof exists, official remote execution remains blocked.
- Confirm the fake entrypoint uses a credential-free fixture by default; authoritative-runner validation may be claimed only after the bridge proof passes.
- Confirm deterministic source-to-install behavior, hash-lock integrity, and first/repeated deployment convergence.
- Supply a fresh operator approval for any synthetic numeric non-provider tuple and verify IPv4/IPv6 parity, expiry, materialization ordering, unconditional rollback, and unchanged `assistant` denial.
- Confirm Phase 10 plan/evidence prerequisites and retain the existing `assistant` direct-public-egress denial.

### III. Required Technical Dependencies and Imports

| Dependency/artifact | Policy | Gate |
|---|---|---|
| Python | Existing `>=3.12` baseline | Exact target interpreter confirmed in Chunk 0 |
| `openai-codex` | Exact `0.144.4` | Public API mock contract only; no runtime start in adapter chunks |
| `openai-codex-cli-bin` | Exact transitive `0.144.4` | Bundled executable/path and package integrity confirmed in Chunk 0 |
| `mcp` | Exact `1.28.1` | Existing local client/server contract retained |
| package lock | Existing hash-locked `requirements.lock` | Install only with `--require-hashes` into a root-owned venv |
| Ansible | Existing repository roles/playbooks and native modules | New role names/paths proposed until Chunk 0 |
| systemd | On-demand unit, `systemd-analyze verify`, hardening property checks | No listener, no auto-start, fake default |
| UFW/netfilter | Existing restore-test, owner-rule, ordering, and rollback patterns | New dedicated identity/markers; no reuse of old destination tuples |
| Codex authentication | Supported pinned CLI/runtime operations only | Operator-owned; output suppressed; runtime-home contents opaque |

Proposed new artifacts, subject to Chunk 0:

```text
ansible/ai_ops_runtime/files/orchestrator/src/openstack_ai_ops_orchestrator/runtime_entrypoint.py
ansible/ai_ops_runtime/files/orchestrator/tests/test_runtime_entrypoint.py
ansible/ai_ops_runtime/roles/orchestrator_runtime/
ansible/ai_ops_runtime/roles/orchestrator_egress/
ansible/ai_ops_runtime/playbook_setup_orchestrator_runtime.yml
ansible/ai_ops_runtime/playbook_validate_phase11_orchestrator_deployment.yml
ansible/ai_ops_runtime/playbook_operate_orchestrator_egress_window.yml
docs/ai-ops/runtime/orchestrator-authentication-operations.md
docs/ai-ops/runtime/phase11-sandboxed-deployment-validation-evidence.md
```

Dependency rules:

- Do not import provider-gateway modules or reuse its service, user, policy, listener, egress, or evidence ledger.
- Do not add API-key, HTTP-client, proxy, SSH, generic shell, browser automation, credential parser, remote MCP, or custom provider dependencies.
- Runtime SDK imports remain isolated in `official_codex_adapter.py`; contracts, fake adapter, redaction, MCP client, and evidence modules remain vendor-independent.
- Tests inject mocked public SDK objects/factories and patch process, socket, DNS, credential-path, and environment access. They do not start Codex or MCP unless the final explicitly approved local fake validation requires a fixed fixture.
- Ansible must copy reviewed source/lock artifacts, install through the committed hash lock, and never perform an unpinned global npm install for the new runtime.

### IV. Step-by-Step Procedure / Execution Flow

1. Verify Phase 10 acceptance, clean repository state, pinned dependencies, public SDK symbols, and the unresolved real-MCP interception and credential-separation boundaries.
2. Record accepted identity, filesystem, systemd, local MCP privilege split, authentication command, and egress decisions. Stop before edits if any boundary would expose credentials or weaken result redaction.
3. Extend the official adapter only through mocked public interfaces. Keep the runtime-selection constant false and map unknown/unsupported SDK behavior to fixed compatibility categories.
4. Build a fake-only package entrypoint that constructs fixed request/policy/adapter/client/evidence dependencies. Reject caller-selected adapters, paths, commands, URLs, prompts, or environments.
5. Add a dedicated Ansible role/playbook. Validate exact configuration keys, target `assistant01`, distinct identity/group, fixed paths, package hash lock, and no symlinks before mutation.
6. Create the non-login system identity and only the protected application, work, Codex-home, and evidence directories. Copy source and locks as root-owned files and build/install the dedicated virtual environment deterministically.
7. Render an on-demand, fake-default unit/launcher. Clear proxy variables and unreviewed environment; use fixed `HOME`, working directory, umask, filesystem restrictions, address-family/network restrictions, process limits, and no listener.
8. First run package/version, ownership, mode, unit verification, hardening property, process, listener, writable-path, and credential-denial assertions before invoking the fake workflow.
9. Execute the deployed fake workflow through the accepted credential-free MCP fixture or approved privilege-separated local MCP boundary with network disabled. Validate cleanup and evidence permissions/categories.
10. Re-run the deployment and prove convergence, unchanged lock/artifact digest categories, no unexpected restart, no listener, and no broadened writable paths.
11. Publish an operator runbook for login, status category, refresh/recovery, logout, and disablement under the dedicated identity/fixed home. Do not execute login until a separate temporary-egress approval is supplied.
12. Materialize permanent dedicated-identity `disabled` egress rules and independently revalidate the existing `assistant` rules. Reject unknown identity, broad CIDR, caller hostname/URL, proxy, or missing owner reject.
13. For a fresh synthetic approval, validate target-host UTC, expiry, exact numeric non-provider destinations, protocol/port, UFW baseline, rule-file syntax, and ordering before applying temporary rules.
14. Apply the synthetic window, prove only the dedicated identity's exact test path is allowed, prove `assistant` remains denied, and retain only success/failure categories and counts.
15. In an unconditional cleanup path, remove only the temporary marker blocks, reload safely, and prove permanent orchestrator denial plus unchanged `assistant` denial. Repeat cleanup after an injected failure path.
16. Re-run deployment, ownership/mode, unit-hardening, process, listener, fake-workflow, evidence, and egress validators. Write a sanitized Phase 11 record only after all checks pass.
17. Leave official remote selection disabled. Hand Phase 12 only the accepted pinned versions, closed categories, and explicit remaining compatibility/approval gates.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
|---|---|---|---|
| Prerequisite | Phase 10 evidence is absent, stale, or local safety checks fail | Stop before SDK/deployment work | `ERR_PHASE11_PREREQUISITE` (proposed) |
| SDK contract | Public symbol/config/event differs from pinned review | Keep adapter disabled; do not start runtime | `VENDOR_BLOCKED / SDK_CONTRACT_DRIFT` (proposed) |
| SDK configuration | Caller/unreviewed model, cwd, env, proxy, MCP, sandbox, approval, retry, or concurrency value appears | Reject before client construction | `POLICY_FAILED / SDK_CONFIG_DENIED` (proposed) |
| SDK event | Unknown, malformed, content-bearing, duplicate, or out-of-order event | Discard raw object; interrupt/close mocked lifecycle | `ADAPTER_FAILED / INVALID_ADAPTER_EVENT` |
| Cancellation | Deadline/cancellation does not produce one supported interrupt and bounded close | Classify and keep remote disabled | `TIMED_OUT` or `CANCELLED`; cleanup failure category |
| MCP compatibility | No supported pre-consumption redaction seam or accepted policy adapter | Do not enable official invocation | `VENDOR_BLOCKED / MCP_INTERCEPTION_UNSUPPORTED` |
| Credential split | New identity can read credential/runtime/ledger data or cannot reach safe MCP boundary | Stop deployment claim; revoke test grants | `ERR_ORCHESTRATOR_CREDENTIAL_BOUNDARY` (proposed) |
| Entry point | Arbitrary adapter/path/prompt/command/environment requested | Reject before workflow construction | `ERR_ORCHESTRATOR_ENTRYPOINT_POLICY` (proposed) |
| Deployment contract | Unknown variable, wrong host, reused identity/path, symlink, unsafe mode | Fail before install/change | `ERR_ORCHESTRATOR_DEPLOYMENT_CONTRACT` (proposed) |
| Dependency install | Lock/hash/version mismatch or package install drifts | Remove only incomplete new venv; preserve previous accepted deployment | `ERR_ORCHESTRATOR_DEPENDENCY_INTEGRITY` (proposed) |
| Unit validation | Unit has listener, auto-start, unsafe writable path, proxy env, broad address family, or weak identity | Keep unit disabled; reject deployment | `ERR_ORCHESTRATOR_SANDBOX` (proposed) |
| Local workflow | Fake path contacts DNS/network/provider, starts real Codex, or leaks content | Stop process, discard unsafe output, keep remote disabled | `ERR_ORCHESTRATOR_LOCAL_VALIDATION` (proposed) |
| Repeat deployment | Second apply changes reviewed artifacts or loses state unexpectedly | Roll back to committed artifact set | `ERR_ORCHESTRATOR_CONVERGENCE` (proposed) |
| Authentication approval | Missing/expired approval or endpoint scope cannot be bounded | Do not open login egress | `ERR_ORCHESTRATOR_AUTH_APPROVAL` (proposed) |
| Authentication operation | Supported login/status/logout fails | Suppress output; close temporary policy; request operator action | `AUTH_ACTION_REQUIRED` |
| Credential evidence | Automation attempts to read/list/hash/copy Codex home or retain command output | Fail and remove unsafe draft evidence | `ERR_ORCHESTRATOR_AUTH_OPACITY` (proposed) |
| Egress preflight | UFW inactive, owner unknown, reject absent, tuple broad/provider-owned/unapproved, expiry invalid | Do not write rules | `ERR_ORCHESTRATOR_EGRESS_PREFLIGHT` (proposed) |
| Egress materialization | Temporary allow is absent, extra, or ordered after reject | Remove temporary markers immediately | `ERR_ORCHESTRATOR_EGRESS_MATERIALIZATION` (proposed) |
| Synthetic probe | Provider/DNS target appears, wrong identity succeeds, or `assistant` is allowed | Abort and roll back | `ERR_ORCHESTRATOR_SYNTHETIC_EGRESS` (proposed) |
| Rollback | Marker/rule survives or permanent reject is not restored | Keep all remote modes disabled; require operator repair | `ERR_ORCHESTRATOR_EGRESS_ROLLBACK` (proposed) |
| Evidence | Raw firewall, SDK, auth, credential, address, prompt, response, or exception data would persist | Discard record; retain only fixed failure category | `EVIDENCE_FAILED` |

No failure authorizes provider access, API-key fallback, private-protocol inspection, broad egress, proxying, credential inspection, gateway reuse, or automatic retry.

### VI. Security, Integrity, Idempotency, and Cleanup

- **Identity security:** use a dedicated non-root, non-login identity distinct from `assistant` and `aiops-provider`. Do not add it to broad groups or grant general sudo.
- **Credential security:** Codex credentials stay opaque in the dedicated mode-`0700` home. OpenStack credentials remain inaccessible to the Codex process; the approved MCP privilege boundary must expose operations/results, not files or values.
- **SDK security:** use only pinned public APIs. Prohibit login/account/API-key calls from repository application code, arbitrary config overrides, custom providers, web search, unsafe sandbox modes, caller environment, and SDK retry helpers.
- **Filesystem:** application/venv/unit/policy files are root-owned and immutable to the service. Writable paths are exact, new, bounded, and excluded from assistant/gateway trees. Symlinks are rejected.
- **Process sandbox:** no public listener, daemon pool, shell wrapper, broad process matching, ambient capability, writable system tree, or inherited proxy environment. Any relaxation required by the selected MCP privilege mechanism requires explicit Chunk 0 review.
- **Network:** permanent dedicated-identity policy is deny by default. Temporary windows are identity-, time-, family-, protocol-, port-, and destination-bounded where enforceable. `assistant` denial is independently checked before and after every window.
- **Authentication:** only the operator sees supported login interaction. Automation records no device code, URL, token, account, auth status text, or runtime-home contents.
- **Evidence integrity:** reuse the Phase 10 orchestrator schema only for orchestrator lifecycle records. Deployment/egress acceptance documentation stores sanitized categories/counts and never mutates provider-gateway ledgers.
- **Dependency integrity:** install exact committed hashes. A version change is a reviewed lock change plus mocked adapter tests, fake deployment validation, and later remote reacceptance.
- **Idempotency:** repeated deployment converges without rewriting Codex-owned home contents or evidence. Repeating an invocation creates a new correlation ID. Temporary approvals cannot extend themselves or broaden tuples.
- **Cleanup:** close the adapter/runtime once, stop exact owned processes, remove only test workspaces and temporary egress markers, preserve Codex-owned authentication state, and re-run permanent-policy validators after success and failure.
- **Rollback:** preserve the previous accepted root-owned artifact/venv until the replacement validates. Rollback disables the new unit, restores reviewed artifacts/policy, removes temporary egress, and does not restore the provider gateway as a request path.

### VII. Validation Strategy

All Python execution uses a dedicated temporary virtual environment. Live Ansible apply, authentication, firewall mutation, and network probes require separate explicit operator approval; syntax/static checks do not.

#### Python adapter and entrypoint

```bash
rtk python3 -m venv /tmp/openstack-ai-ops-phase11-venv
source /tmp/openstack-ai-ops-phase11-venv/bin/activate
rtk python -m pip install --require-hashes -r ansible/ai_ops_runtime/files/orchestrator/requirements.lock
rtk python -m ruff format --check ansible/ai_ops_runtime/files/orchestrator
rtk python -m ruff check ansible/ai_ops_runtime/files/orchestrator
rtk python -m mypy ansible/ai_ops_runtime/files/orchestrator/src ansible/ai_ops_runtime/files/orchestrator/tests
rtk python -m py_compile ansible/ai_ops_runtime/files/orchestrator/src/openstack_ai_ops_orchestrator/*.py ansible/ai_ops_runtime/files/orchestrator/tests/*.py
rtk python -m pytest -q ansible/ai_ops_runtime/files/orchestrator/tests/test_official_codex_adapter.py ansible/ai_ops_runtime/files/orchestrator/tests/test_runtime_entrypoint.py
```

Required adapter proofs:

- exact pinned public API/config mapping;
- unknown events/options fail closed;
- raw SDK content never reaches repository events/results/errors/evidence;
- cancellation/deadline invokes interrupt at most once and closes within policy;
- zero automatic retries and one-workflow concurrency;
- mock tests start no process, listener, DNS lookup, socket, login, credential access, MCP server, or provider call;
- official runtime selection remains false after tests.

#### Ansible and systemd

```bash
rtk ansible-playbook -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_setup_orchestrator_runtime.yml --syntax-check
rtk ansible-playbook -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_validate_phase11_orchestrator_deployment.yml --syntax-check
rtk ansible-lint ansible/ai_ops_runtime/roles/orchestrator_runtime ansible/ai_ops_runtime/roles/orchestrator_egress ansible/ai_ops_runtime/playbook_setup_orchestrator_runtime.yml ansible/ai_ops_runtime/playbook_validate_phase11_orchestrator_deployment.yml
rtk systemd-analyze verify <rendered-unit-path>
```

Approved target validation must check:

- identity/group uniqueness and non-login account metadata;
- exact paths, owners, groups, modes, symlink absence, and writable-path allowlist;
- installed package/version/lock integrity and first/repeated deployment convergence;
- unit disabled/on-demand state, exact command/environment, sandbox properties, no listener, and deterministic process cleanup;
- inability of the Codex identity to open assistant credentials, assistant Codex home, or gateway ledgers;
- fake workflow success with network disabled and metadata-only evidence;
- unchanged `assistant` direct-public-egress denial.

#### Authentication and egress

- Syntax/lint all role/playbook changes before target execution.
- Validate approval schema, target UTC/expiry, exact tuple count, UFW active state, output-chain traversal, numeric UID, restore-test parsing, rule ordering, and family parity.
- Use only an approved non-provider synthetic endpoint. Store no address or raw firewall/probe output in evidence.
- Test success rollback and injected-failure rollback; both must restore permanent dedicated-identity denial and preserve `assistant` denial.
- Authentication validation records only supported command version and operator-declared closed outcome. Runtime-home checks use `stat` on the directory only; no recursive find/list/hash/read.

#### Documentation and final review

```bash
rtk grep -nE '^### (I|II|III|IV|V|VI|VII|VIII|IX|X)\.' docs/ai-ops/implementation-plan/ads/11-00-sandboxed-deployment-authentication-and-egress-ads.md
rtk grep -nE '^#### Chunk [0-7]:' docs/ai-ops/implementation-plan/ads/11-00-sandboxed-deployment-authentication-and-egress-ads.md
rtk git diff --check
rtk git diff -- docs/ai-ops/implementation-plan/ads/11-00-sandboxed-deployment-authentication-and-egress-ads.md
```

After every implementation chunk: review `rtk git status --short`, `rtk git diff --stat`, `rtk git diff --check`, and the complete scoped diff. Security review must search changed files for provider URLs, API keys, tokens, account/device fields, proxy variables, shell execution, broad CIDRs, unsafe modes, credential paths, listener directives, and raw-output registration.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass. Each chunk must end after targeted validation and scoped diff review.

#### Chunk 0: Discovery and Integration Confirmation
- **Goal:** Resolve the pinned public SDK contract, real-MCP pre-consumption seam, dedicated identity/layout, MCP credential privilege split, deployable fake path, systemd sandbox, supported auth commands, and bounded egress/rollback policy before edits.
- **Files to read:** this ADS; Phase 11 plan; Phase 10 ADS/evidence; orchestrator contracts/adapter/orchestrator/tests/locks; assistant MCP/runner/credential tasks and policies; current client-runtime, systemd, egress, device-auth, and validation roles/playbooks; the pinned installed SDK public source/types/help where locally available.
- **Commands:** targeted `rtk find`, `rtk grep`, bounded reads, lock/package metadata inspection, Ansible check/syntax commands, and sanitized host metadata only. Do not edit, install, authenticate, inspect home contents, alter firewall, start Codex/MCP, perform DNS, or contact any endpoint.
- **Evidence to confirm:** exact SDK symbols/config/events/cancellation; official adapter compatibility status; identity/path/unit decisions; Codex-to-MCP privilege design; credential denial; fake entrypoint shape; lock installation contract; login/status/logout commands; disabled/synthetic/login egress modes; approved synthetic tuple/expiry; Phase 10 prerequisite.
- **Validation:** produce a decision table marking each item confirmed, proposed, deferred, or blocker, including exact files/public symbols that support it.
- **Stop condition:** stop without editing if the MCP result-redaction seam, credential privilege separation, identity/path ownership, SDK pin/API, or rollback boundary remains unsafe or ambiguous. Real adapter deployment cannot proceed around a blocker.

#### Chunk 1: Official Adapter Contracts and Fail-Closed Stubs
- **Goal:** Add the minimum pinned public-type/config/event mapping contracts while preserving a compile-safe disabled adapter.
- **Files to change:** `src/openstack_ai_ops_orchestrator/official_codex_adapter.py`; `tests/test_official_codex_adapter.py`.
- **Symbols to add/change:** conceptual SDK factory/client/thread/turn protocols or test seam, curated config mapper, closed public-event/status mapper, compatibility error, and explicit remote-disabled selection gate.
- **Implementation shape:** import only confirmed public SDK symbols; construct no real client/process. Unknown options/events raise a fixed compatibility error. The adapter stub returns `VENDOR_BLOCKED / REAL_ADAPTER_DISABLED`. No login/account/provider/MCP process call exists.
- **Validation:** focused Ruff, mypy, `py_compile`, pytest, prohibited-call/import scan, process/socket/DNS/credential monkeypatches, and scoped diff.
- **Stop condition:** exact mocked public objects map to repository categories, drift fails closed, and all paths prove runtime construction is unreachable.

#### Chunk 2: One Mocked SDK Lifecycle Slice
- **Goal:** Implement one finite mocked turn lifecycle with cancellation/deadline cleanup while keeping remote invocation disabled outside injected tests.
- **Files to change:** `src/openstack_ai_ops_orchestrator/official_codex_adapter.py`; `tests/test_official_codex_adapter.py`.
- **Symbols to add/change:** mocked-client lifecycle coordinator, event reducer, interrupt-once guard, terminal mapper, sanitized exception classifier, and cleanup timeout handling.
- **Implementation shape:** test-only injected factory returns public-shape mocks. Production construction still requires an unapproved gate and fails before process start. Map no content-bearing payload. Do not configure real MCP until the Chunk 0 interception decision is accepted.
- **Validation:** success/failure/unknown-event/cancel/deadline/cleanup tests; full package Ruff/mypy/pytest; no-process/network/auth assertions; scoped diff.
- **Stop condition:** the mocked lifecycle is bounded and sanitized, all cleanup paths terminate, and `OFFICIAL_ADAPTER_ENABLED` remains false.

#### Chunk 3: Fake-Only Deployable Entrypoint
- **Goal:** Add one invocable fixed local workflow profile without exposing arbitrary runtime configuration or the official adapter.
- **Files to change:** proposed `src/openstack_ai_ops_orchestrator/runtime_entrypoint.py`; proposed `tests/test_runtime_entrypoint.py`.
- **Symbols to add/change:** conceptual `main`, closed invocation profile enum, fixed policy/request builder, fake adapter/client/evidence construction, and fixed exit categories.
- **Implementation shape:** default and only enabled profile is `validate-local-fake`. Inputs cannot select prompt, context, model, adapter, executable, path, URL, proxy, environment, tool, or egress. A remote profile returns a fixed disabled error before SDK construction.
- **Validation:** focused tests, Ruff/mypy/compile, deterministic exit tests, temporary evidence permission test, prohibited-input/import scan, and full package regression.
- **Stop condition:** the package can execute one deterministic fake-backed validation profile and every remote/arbitrary input fails before a process or socket boundary.

#### Chunk 4: Deterministic Identity and Deployment Slice
- **Goal:** Deploy the pinned artifact, dedicated identity, protected directories, root-owned venv, and fake-default on-demand unit without applying egress or authentication changes.
- **Files to change:** proposed `roles/orchestrator_runtime/defaults/main.yml`, `roles/orchestrator_runtime/tasks/main.yml`, unit template, and `playbook_setup_orchestrator_runtime.yml`. More than two files are justified because the role contract, implementation, unit, and standalone invocation must converge as one deployable slice.
- **Symbols to add/change:** accepted identity/layout mapping, exact artifact/lock manifest, system account, directories, hash-locked venv install, proxy-cleared unit, handlers only if required.
- **Implementation shape:** strict exact-key assertions first; create no home outside the accepted Codex home; preserve its contents on reapply; root-own source/venv/unit; exact writable paths; no auto-start/listener; fake profile only. Do not modify `ai_client_runtime`, assistant credentials, provider gateway, or firewall roles.
- **Validation:** YAML parse, playbook syntax, ansible-lint, rendered `systemd-analyze verify`, check-mode where meaningful, first approved apply, second convergence apply, ownership/mode/version/unit checks, and scoped diff.
- **Stop condition:** repeated deployment converges, the unit remains disabled/on-demand and fake-only, and the new identity cannot read protected assistant/gateway paths.

#### Chunk 5: Network-Disabled Deployed Fake Validation
- **Goal:** Add a permanent read-only validator and prove the deployed fake workflow, sandbox, evidence, cleanup, listener absence, writable paths, and credential denial with network disabled.
- **Files to change:** proposed `playbook_validate_phase11_orchestrator_deployment.yml`; the runtime role/unit only if one small evidence-backed correction is required.
- **Symbols to add/change:** metadata-only artifact/unit/process/listener/filesystem assertions and fixed fake invocation check.
- **Implementation shape:** validator captures only closed categories/counts. It must not read evidence content, Codex-home contents, credentials, raw process environment, or raw diagnostic output. Use the accepted credential-free fixture or privilege-separated MCP boundary; otherwise report authoritative-runner validation as blocked.
- **Validation:** syntax/lint, unit hardening property checks, two validator runs, fake workflow success, no DNS/socket/provider assertion, `assistant` denial regression, process/listener delta, cleanup, and scoped diff.
- **Stop condition:** local deployed validation is repeatable with zero provider/auth traffic; any unproven authoritative-runner boundary remains explicitly incomplete rather than inferred.

#### Chunk 6: Operator Authentication and Disabled Egress Contracts
- **Goal:** Document supported opaque authentication operations and add a disabled-by-default dedicated-identity egress contract without opening a temporary window.
- **Files to change:** proposed `docs/ai-ops/runtime/orchestrator-authentication-operations.md`; proposed `roles/orchestrator_egress/defaults/main.yml`; proposed `roles/orchestrator_egress/tasks/main.yml`.
- **Symbols to add/change:** accepted login/status/logout/recovery commands, approval schema, closed egress mode enum, dedicated UID/UFW paths/markers, exact expiry/tuple validators, and permanent owner reject materialization.
- **Implementation shape:** runbook shows operator-only commands with warnings against sharing output. Role defaults to `disabled`; invalid/missing approvals fail before writes. Install and verify only loopback/local-required allows followed by dedicated owner reject. Do not activate login, synthetic, or remote rules.
- **Validation:** Markdown review, YAML parse, syntax/lint through a focused playbook or role include, UFW restore-test rendering, invalid approval tests, permanent reject ordering, and independent `assistant` policy check.
- **Stop condition:** authentication can be reviewed without exposing values, and the dedicated identity has a materially verified deny-default policy with no temporary/public allow.

#### Chunk 7: Synthetic Egress, Rollback, and Phase 11 Acceptance
- **Goal:** Exercise one approved non-provider synthetic path, prove success/failure rollback, revalidate all permanent controls, and record sanitized Phase 11 evidence while leaving provider access disabled.
- **Files to change:** proposed `playbook_operate_orchestrator_egress_window.yml`; the same egress role/templates; proposed `docs/ai-ops/runtime/phase11-sandboxed-deployment-validation-evidence.md` only after all checks pass. Multiple files are justified by the temporary policy, unconditional rollback operation, and evidence-backed final vertical slice.
- **Symbols to add/change:** exact synthetic IPv4/IPv6 rules, approval/expiry gate, materialization checks, operator-approved probe, `always` rollback, failure injection, restored-policy validator, and sanitized evidence categories.
- **Implementation shape:** exact numeric non-provider destinations and TCP/443 only unless Chunk 0 approves a narrower/different tuple. No caller URL/hostname, generic DNS, provider endpoint, proxy, raw firewall output, or retained address. Prove the orchestrator test path and `assistant` denial separately. Authentication login may be performed only under its own fresh approval; it is not implied by synthetic approval.
- **Validation:** syntax/lint, restore tests, active ordering/count checks, synthetic success, injected failure, marker removal, permanent deny restoration, repeated deployment validator, fake workflow, process/listener/evidence checks, full orchestrator package tests, `rtk git diff --check`, security scan, and final scoped diff.
- **Stop condition:** temporary rules are absent, both dedicated-identity and `assistant` permanent controls pass, no provider request occurred, official remote selection remains disabled, and the Phase 11 record contains only approved categories/counts. Otherwise Phase 11 remains incomplete.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Phase 11 sandboxed orchestrator deployment, mocked official Codex adapter, opaque operator authentication, and bounded synthetic egress as specified by docs/ai-ops/implementation-plan/ads/11-00-sandboxed-deployment-authentication-and-egress-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm the pinned public SDK API, the real-MCP pre-consumption redaction seam, the dedicated identity and paths, the credential-preserving MCP privilege boundary, the fake deployment entrypoint, systemd sandbox, supported login/status/logout commands, and disabled/synthetic egress rollback contract. Do not install packages, start Codex or MCP, authenticate, inspect runtime-home or credential contents, alter UFW, perform DNS, contact an endpoint, or enable the official adapter. Stop after the evidence and decision table.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.
Execute Chunk 1 only from the accepted Phase 11 ADS and Chunk 0 decisions.
Do not continue to Chunk 2. Add only official-adapter public contracts and fail-closed stubs. Keep OFFICIAL_ADAPTER_ENABLED false; do not construct a real SDK client, start a process, configure MCP, authenticate, inspect credentials, or access the network. Run targeted Ruff, mypy, py_compile, pytest, prohibited-call checks, and show the scoped git diff before stopping.
```

### X. Conclusion and Next Steps

- Phase 11 can safely implement and mock-test the pinned official SDK adapter while keeping production remote invocation disabled.
- Deterministic deployment requires a new dedicated identity, protected Codex home, immutable hash-locked application, fake-only entrypoint, on-demand sandbox, no listener, and explicit writable-path policy. The historical `assistant` Codex runtime and provider-gateway service are not reusable deployment targets.
- Two security decisions are mandatory before implementation: a supported pre-consumption MCP result-redaction seam for real Codex, and a privilege-separated way to reach the credential-bearing runner without making OpenStack credentials readable to the Codex process.
- Authentication remains operator-owned and opaque. Repository automation may validate categories and directory metadata only; it may not inspect or retain credential-related values or home contents.
- Egress remains deny-by-default. Phase 11 permits only separately approved temporary authentication capability and non-provider synthetic validation with unconditional rollback; it does not authorize a provider request.
- The next action is review and acceptance of this ADS, followed by Chunk 0 only. Phase 12 remains blocked until Phase 11 validation passes, the real MCP compatibility gate is resolved, authentication is established through supported operations, and a fresh one-request approval is granted.
