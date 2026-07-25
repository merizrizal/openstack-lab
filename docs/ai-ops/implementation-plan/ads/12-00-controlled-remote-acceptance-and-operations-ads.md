## Architectural Design Specification: Controlled Remote Acceptance and Operations

**Source:** `docs/ai-ops/implementation-plan/12-controlled-remote-acceptance-and-operations.md`

**Goal:** Validate exactly one separately approved, non-sensitive diagnostic workflow through the pinned public Codex SDK/runtime and the reviewed local MCP boundary, retain only bounded metadata and sanitized advisory output, restore the Phase 11 deny-by-default state after every outcome, and establish supported operational, upgrade, disablement, and rollback procedures.

**Status:** Draft for review. Phase 11 is complete, so Phase 12 design and local no-provider implementation may begin. This ADS does not authorize authentication, temporary remote egress, official-adapter selection, or a provider request. Those actions require fresh, operation-specific approval at the chunks that perform them.

---

### I. Overview and Contract

#### Selected phase boundary

```text
accepted Phase 11 baseline
  -> repository and target drift-free preflight
  -> proven credential-preserving MCP pre-consumption boundary
  -> compile-safe one-request approval contract, remote path still unreachable
  -> mocked real-adapter and remote-entrypoint validation
  -> operator-private authentication status under separate approval
  -> fresh approval for one reviewed non-sensitive request
  -> temporary one-shot remote execution and bounded sanitized presentation
  -> unconditional process, workspace, approval, and egress rollback
  -> post-operation deployment, egress, listener, MCP, and evidence validation
  -> metadata-only acceptance record and operational runbooks
  -> normal remote path remains disabled pending a separate regular-use policy
```

Phase 12 preserves four authorities:

1. **Operator/approval authority:** selects and approves the single reviewed procedure, prompt identifier, model alias, time window, and request count. Approval is non-secret metadata, expires, is valid for one operation only, and cannot be reused after any terminal attempt.
2. **Repository orchestrator:** enforces the closed workflow, fixed bounds, redaction, lifecycle validation, metadata evidence, sanitized advisory-output validation, cancellation, and cleanup. It does not own provider authentication or transport.
3. **Codex SDK/runtime:** owns supported authentication and opaque provider transport. Repository code consumes only reviewed public lifecycle contracts and must not inspect provider response headers, private protocol state, raw SDK events, or Codex logs.
4. **MCP/runner boundary:** executes only reviewed read-only diagnostics. OpenStack credentials remain under the existing credential-bearing identity; content must be validated and redacted before Codex can consume it.

#### One-request acceptance contract

**Configuration Contract (Conceptual):** a proposed immutable `RemoteAcceptancePolicy` or equivalent closed configuration must be constructed only by the reviewed operation boundary. It contains:

- approval identifier and UTC expiry;
- exact request allowance fixed to `1`;
- exact automatic retry allowance fixed to `0`;
- fixed reviewed workflow `project_resource_summary`;
- fixed non-sensitive prompt identifier and repository-owned prompt text;
- fixed reviewed model alias;
- `maximum_turn_count = 1` and `maximum_tool_call_count = 1`;
- one overall deadline and existing bounded cleanup timeout;
- fixed work, Codex-home, evidence, and local MCP proxy paths;
- closed metadata and terminal categories only.

It must not contain a caller-selected prompt, URL, provider, base URL, proxy, executable, environment, credential, account identifier, destination tuple, arbitrary model, tool, path, or retry value.

**Function Signature Contract (Conceptual):** repository confirmation in Chunk 0 is required before finalizing names or signatures. The minimum compile-safe gate is conceptually:

```text
validate_remote_acceptance_policy(policy, current_utc) -> ValidatedOneShotApproval
consume_one_shot_approval(approval) -> ConsumedApproval
```

The Chunk 2 stub must fail with a fixed `REMOTE_ACCEPTANCE_DISABLED` or equivalent proposed category. It must not return a success-shaped capability, construct the SDK client, alter egress, or consume an approval until the contracts and callers are tested.

The one-shot capability is consumed before SDK/runtime construction. Any terminal outcome—including policy rejection, authentication required, SDK startup failure, timeout, cancellation, vendor blocker, or successful completion—exhausts that capability. A retry requires a new explicit approval and is outside the initial acceptance procedure.

#### Official adapter contract

**Function Signature Contract (Concrete):** the existing repository adapter seam remains:

```text
CodexAdapter.run_turn(request, policy, cancellation) -> AsyncIterator[AdapterEvent]
```

The adapter retains one terminal `AdapterResult`. `DiagnosticTurnRequest`, `RuntimePolicy`, `AdapterEvent`, `AdapterResult`, `WorkflowState`, and `AdapterErrorCategory` are existing closed contracts in `contracts.py`.

**Function Signature Contract (Conceptual):** the production SDK factory must be injectable and reachable only with a consumed one-shot capability. Its configuration must use the pinned public SDK/runtime, fixed working directory, fixed model alias, reviewed read-only sandbox/approval settings, fixed local MCP proxy, empty unreviewed overrides, and minimal environment. It must provide:

- one client, one thread, one turn, and no SDK-level retry;
- bounded event reduction before repository exposure;
- bounded interrupt and close;
- closed mapping for authentication-required, completed, interrupted, failed, unsupported, and compatibility-drift outcomes;
- no raw SDK object, item, message, identifier, usage payload, exception text, prompt, response, or tool content outside the adapter.

`OFFICIAL_ADAPTER_ENABLED = False` is the current permanent default. Implementation must not replace it with an unconditional `True`. A reviewed one-shot runtime path may use a separate explicit capability while all ordinary construction and the deployed fake profile continue to fail closed.

#### MCP pre-consumption contract and current blocker

The target workflow requires one allowlisted local MCP operation. Current repository evidence does **not** prove a production real-Codex MCP path:

- `LocalOrchestrator._complete_fake_tool()` handles tool completion only when the adapter is `FakeCodexAdapter`.
- `LocalMcpClient` launches the existing credential-bearing MCP command directly.
- The accepted Phase 11 ADS proposed an assistant-owned Unix-socket bridge plus credential-free stdio proxy, but repository search found no corresponding implementation artifacts.
- Phase 11 acceptance evidence proves fake-only deployment and synthetic egress, not the authoritative real-Codex MCP bridge.

Therefore Chunk 0 must either locate and prove an existing reviewed bridge/proxy omitted from the current search or approve and implement the missing boundary before any provider request. The required boundary must:

1. retain OpenStack credential access under the credential-bearing identity;
2. authenticate the `aiops-orchestrator` peer locally;
3. expose only the reviewed MCP capabilities and exact arguments;
4. validate bounds and redact the result before Codex receives it;
5. use local IPC/stdio without a TCP listener;
6. preserve cancellation, timeout, correlation, cleanup, and metadata-only evidence;
7. deny direct Codex access to credential files and the existing credential-bearing MCP command.

If this seam cannot be proven through supported public Codex MCP configuration, stop with `VENDOR_BLOCKED / MCP_INTERCEPTION_UNSUPPORTED`. A provider request without the reviewed MCP path cannot satisfy Phase 12 acceptance.

#### Remote entrypoint and sanitized presentation contract

**Function Signature Contract (Conceptual):** add a distinct one-shot operation path rather than broadening the current fake-default `main(arguments=())`. The operation path accepts only a root/operator-controlled validated approval artifact or equivalent fixed invocation contract. It must not parse an arbitrary prompt or runtime option.

The process may present only already-validated advisory text to the operator. Presentation requirements are:

- enforce the existing UTF-8 byte bound before display;
- apply sensitive-marker and control-character validation before display;
- write neither advisory text nor raw terminal/model/SDK/provider/tool output to evidence, journal, Ansible registered variables, temporary files, or handoffs;
- suppress service stdout/stderr by default and use an operator-owned ephemeral terminal channel only if Chunk 0 proves it does not persist output;
- return a closed process exit category separately from advisory text.

If a safe non-persistent presentation channel cannot be demonstrated, complete the request only as a closed terminal category and treat advisory presentation as blocked; do not weaken logging controls.

#### Egress and service-state contract

The accepted Phase 11 baseline is a static fake-only service with `PrivateNetwork=true`, `RestrictAddressFamilies=AF_UNIX`, and permanent owner rejection. Phase 12 must not permanently weaken that unit.

**Deployment Contract (Conceptual):** use a separately rendered, non-enabled one-shot remote acceptance unit or transient equivalent with the same identity, filesystem protections, empty proxy environment, no listener, exact timeout, and only the address families required by the supported runtime. Its existence does not authorize execution. The operation playbook must:

1. validate local gates and approval before mutation;
2. materialize only the reviewed temporary remote egress capability;
3. invoke the exact remote acceptance unit once;
4. stop the exact unit/cgroup at the first terminal result;
5. remove the approval artifact and temporary egress in an unconditional cleanup path;
6. restore and revalidate the Phase 11 fake-only unit and permanent reject policy.

Because vendor routing is opaque, the ADS does not claim private host/path enforcement. Chunk 0 must document the honest enforceable network boundary. If it exceeds the accepted threat model, stop rather than add a proxy, custom provider, gateway fallback, broad caller-selected destination, or private-protocol inspection.

#### Authentication contract

Authentication remains operator-owned under `aiops-orchestrator` and `/var/lib/aiops-orchestrator/codex-home`.

- Authentication status or sign-in needs its own fresh approval and bounded temporary egress if required.
- The operator alone sees command interaction and output.
- Automation records only `authenticated`, `authentication_required`, or `operator_error`.
- No automation may list, read, hash, copy, parse, delete, or recursively inspect Codex-home contents.
- Authentication approval does not authorize the one remote diagnostic request; remote approval does not authorize another authentication attempt.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops/implementation-plan/12-controlled-remote-acceptance-and-operations.md` requires one explicitly approved non-sensitive workflow, bounded turns/retries, metadata-only classification, immediate pre/post validators, sanitized advisory output, and operational/upgrade/rollback runbooks.
- `docs/ai-ops/runtime/phase11-sandboxed-deployment-validation-evidence.md` records passed fake-only deployment, sandbox, no-listener, credential-denial, permanent egress, synthetic success, and rollback checks, with zero provider requests, authentication actions, or official adapter selections.
- `docs/ai-ops/runtime/orchestrator-authentication-operations.md` fixes the dedicated identity/home and operator-only supported login/status/logout boundary while prohibiting Codex-home inspection and output retention.
- `official_codex_adapter.py` pins the permanent default `OFFICIAL_ADAPTER_ENABLED = False`, maps a small closed public lifecycle, and runs only an injected mocked lifecycle. Ordinary construction returns `VENDOR_BLOCKED / REAL_ADAPTER_DISABLED`.
- `test_official_codex_adapter.py` proves disabled construction does not enter process, socket, DNS, credential-read, authentication, SDK runtime, account, or retry boundaries.
- `runtime_entrypoint.py` exposes only `validate-local-fake`; `--profile remote` returns `REMOTE_DISABLED`, and arbitrary prompt/model/path/URL/adapter/egress inputs are rejected.
- `contracts.py` already fixes one tool call and one concurrent tool call, defaults to one turn, and provides closed workflow, event, result, MCP capability, timeout, content, evidence, and cleanup bounds.
- `LocalOrchestrator.run()` validates lifecycle order, evidence, advisory-output bytes, cancellation, and terminal categories. Its tool completion seam is explicitly fake-adapter-only.
- `orchestrator_runtime/templates/aiops-orchestrator.service.j2` is a static, fake-only, one-shot unit with `PrivateNetwork=true`, `AF_UNIX` only, no capabilities, strict filesystem protection, and exact writable paths.
- `orchestrator_egress` defaults to `mode: disabled`; its role recognizes `remote` as a closed mode but current evidence only proves disabled and synthetic operation.
- `playbook_validate_phase11_orchestrator_deployment.yml` validates artifact integrity, identity, unit hardening, protected-path denial, fake invocation, process cleanup, and listener stability without reading protected content.
- `playbook_operate_orchestrator_egress_window.yml` demonstrates approval expiry, temporary marker insertion, an `always` rollback path, permanent-policy restoration, and independent `assistant` denial for synthetic validation only.
- Repository search found the Phase 11 ADS decision for an assistant-owned Unix-socket bridge and stdio proxy, but no bridge/proxy implementation in current orchestrator or Ansible artifacts.
- The current branch was clean at ADS start and is `ai-ops/12-controlled-remote-acceptance-and-operations`, based on merged Phase 11 work.

#### Assumptions

- The accepted pinned SDK/runtime remains `openai-codex==0.144.4` and its exact hash-locked runtime dependency until Chunk 0 revalidates package and public API metadata without provider access.
- The reviewed initial workflow remains `project_resource_summary`; the exact prompt text and model alias must be selected and reviewed in Chunk 0 and then fixed in repository-owned configuration.
- A one-shot remote unit is safer than changing the fake-only unit in place, but the exact systemd mechanism remains proposed until target/systemd behavior is confirmed.
- Remote transport may require DNS plus IPv4/IPv6 HTTPS capability for the dedicated identity. No endpoint tuple or hostname is assumed or retained by this ADS.
- A successful provider terminal result is not remediation approval, recurring-use approval, gateway-retirement approval, or permission for a second request.

#### Open confirmations for Chunk 0

- Locate or design the missing credential-preserving MCP bridge and pre-Codex redaction seam.
- Confirm the pinned public SDK supports the required fixed local MCP configuration and exposes a finite lifecycle without private event inspection.
- Confirm the exact reviewed prompt identifier/text, model alias, deadline, event limit, output byte limit, and terminal categories.
- Select a non-persistent advisory presentation mechanism or accept category-only presentation.
- Define the exact one-shot approval schema, consumption point, expiry, storage, ownership, mode, and unconditional removal.
- Define the honest remote egress capability and prove rollback can restore both orchestrator and independent `assistant` denial.
- Confirm authentication status privately without exposing output, only under fresh authorization.
- Confirm Phase 11 validators pass immediately before remote approval is consumed.

### III. Required Technical Dependencies and Imports

| Dependency/artifact | Existing status | Phase 12 rule |
|---|---|---|
| Python | `>=3.12` | Keep current baseline; use a temporary venv for local validation |
| `openai-codex` | Exact `0.144.4` in the hash lock | Reconfirm public API/package integrity; no unpinned upgrade |
| `openai-codex-cli-bin` | Exact transitive `0.144.4` | Supported runtime only; no custom executable or API-key path |
| `mcp` | Exact `1.28.1` | Configure only the reviewed local proxy/bridge after its boundary is proven |
| orchestrator contracts | Existing closed Python types | Extend minimally; preserve vendor-independent contracts |
| metadata evidence | Existing bounded JSONL schema | Extend closed categories only if required; never add raw content fields |
| systemd | Existing hardened static fake unit | Proposed separate one-shot remote unit; never auto-enable or add a listener |
| UFW/netfilter | Existing owner-rule and rollback patterns | Add a separately approved remote mode with unconditional restoration |
| Ansible | Existing validators/operation patterns | `no_log: true`, exact inputs, no raw output registration, `always` cleanup |
| authentication | Existing operator runbook | Operator-private supported commands only; separate approval |

Proposed artifacts are subject to Chunk 0 confirmation:

```text
ansible/ai_ops_runtime/files/orchestrator/src/openstack_ai_ops_orchestrator/remote_acceptance.py
ansible/ai_ops_runtime/files/orchestrator/tests/test_remote_acceptance.py
ansible/ai_ops_runtime/files/orchestrator/src/openstack_ai_ops_orchestrator/mcp_bridge.py or equivalent
ansible/ai_ops_runtime/files/orchestrator/src/openstack_ai_ops_orchestrator/mcp_stdio_proxy.py or equivalent
ansible/ai_ops_runtime/files/orchestrator/tests/test_mcp_bridge.py
ansible/ai_ops_runtime/files/orchestrator/tests/test_mcp_stdio_proxy.py
ansible/ai_ops_runtime/roles/orchestrator_runtime/templates/aiops-orchestrator-remote.service.j2
ansible/ai_ops_runtime/playbook_validate_phase12_remote_preflight.yml
ansible/ai_ops_runtime/playbook_operate_orchestrator_remote_acceptance.yml
docs/ai-ops/runtime/orchestrator-remote-operations.md
docs/ai-ops/runtime/orchestrator-sdk-runtime-upgrade-and-rollback.md
docs/ai-ops/runtime/phase12-controlled-remote-acceptance-evidence.md
```

Dependency restrictions:

- Do not add a custom provider, base URL, generic HTTP client, proxy, packet-capture, browser automation, API-key, credential parser, remote MCP, generic shell, or gateway fallback dependency.
- Do not import provider-gateway modules or write provider-gateway ledgers.
- Do not use raw SDK/provider response types as repository contracts.
- Do not log or persist prompt, response, advisory, SDK event, tool output, authentication output, exception text, endpoint tuple, or firewall/probe output.

### IV. Step-by-Step Procedure / Execution Flow

1. Reconfirm the accepted Phase 11 commit lineage, clean working state, current package lock, and all Phase 12 source contracts.
2. Resolve the open MCP bridge/proxy, supported public SDK configuration, one-shot approval, advisory presentation, systemd, and enforceable egress decisions. Stop before implementation if any boundary is unsafe.
3. Add a closed one-request approval contract and fail-closed stub. Ordinary and fake deployment paths remain unchanged and remote SDK construction remains unreachable.
4. Complete the official adapter against injected public-shape mocks: one client/thread/turn, zero retries, one interrupt, bounded close, closed event/result mapping, and no raw payload escape.
5. Implement and locally prove the credential-preserving MCP bridge/proxy. Verify exact peer identity, reviewed capabilities, pre-Codex redaction, timeout/cancellation, no credential-file access, and no TCP listener.
6. Add a fixed remote acceptance entrypoint that requires a validated one-shot capability and repository-owned prompt/model/workflow. Reject arbitrary runtime input and consume approval before runtime entry.
7. Add a separate hardened remote one-shot unit and no-provider preflight/operation playbooks. Keep the existing fake-only unit unchanged and default.
8. Run static checks, mocked adapter tests, local MCP bridge tests, fake workflow tests, unit rendering checks, Ansible syntax/lint, and prohibited-boundary tests without authentication or provider traffic.
9. On the accepted target, re-run Phase 11 deployment and egress validators, package/version/integrity checks, fake adapter and local MCP safety tests, evidence schema/capacity validation, protected-path denial, process/listener checks, and temporary-workspace checks.
10. Under a separate fresh authorization, the operator privately checks authentication status. Record only its closed category. Stop if authentication is not accepted; do not inspect credentials or automatically sign in.
11. Present the full fixed procedure and obtain fresh explicit approval for exactly one reviewed request. Validate approval identity, expiry, request allowance, prompt identifier, model alias, limits, target UTC, and unchanged repository/deployment state.
12. Materialize the approved temporary remote egress capability and verify ordering/restoration guards without retaining rule or destination output.
13. Consume the approval, start the exact remote one-shot unit once, and stop on the first terminal result. Do not automatically retry or investigate private transport behavior.
14. Validate and present only bounded sanitized advisory output through the accepted non-persistent channel. Persist only closed categories, counts, versions, and validation outcomes.
15. In an unconditional cleanup path, interrupt/close the exact runtime as needed, stop the exact cgroup, remove temporary workspace and approval artifacts, remove temporary egress markers, and restore permanent disabled policy.
16. Re-run deployment, egress, process, listener, MCP, credential-denial, evidence, and cleanup validators. Independently prove `assistant` remains denied.
17. Record metadata-only Phase 12 evidence. A supported SDK/runtime failure becomes a documented vendor blocker; it does not trigger gateway fallback or private-protocol debugging.
18. Complete normal invocation, approval, timeout, cancellation, authentication-expiry, disablement, upgrade, rollback, evidence-retention, and vendor-escalation runbooks.
19. Leave ordinary remote invocation disabled. Any recurring or second request requires a separate policy and approval outside this acceptance.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
|---|---|---|---|
| Prerequisite | Phase 11 validator, package integrity, sandbox, egress, fake, MCP, or evidence gate fails | Stop before authentication/approval consumption | `ERR_REMOTE_PREFLIGHT` (proposed) |
| MCP boundary | Bridge/proxy is absent, peer identity is weak, credentials become readable, or redaction occurs after Codex consumption | Keep remote unreachable; remove incomplete local artifacts | `VENDOR_BLOCKED / MCP_INTERCEPTION_UNSUPPORTED` |
| SDK contract | Pinned public symbols/config/events differ from review | Do not construct runtime; evaluate reviewed pin update | `VENDOR_BLOCKED / SDK_CONTRACT_DRIFT` (proposed) |
| Approval | Missing, expired, reused, malformed, or broader than one request | Reject before egress/runtime mutation | `POLICY_FAILED / REMOTE_APPROVAL_INVALID` (proposed) |
| Prompt/model | Prompt, model, workflow, tool, limits, or path differ from reviewed constants | Reject before SDK construction | `POLICY_FAILED / REMOTE_PROFILE_DRIFT` (proposed) |
| Authentication | Operator reports authentication required or error | Restore disabled state; require separate operator approval | `AUTH_ACTION_REQUIRED` |
| Egress | Temporary policy cannot be bounded, ordered, materialized, or independently validated | Remove markers; do not invoke runtime | `POLICY_FAILED / REMOTE_EGRESS_FAILED` (proposed) |
| SDK start | Supported SDK/runtime fails before turn start | Sanitize, close exact client/process, consume approval | `VENDOR_BLOCKED / SDK_START_FAILED` |
| SDK lifecycle | Unknown/content-bearing/out-of-order event or extra turn appears | Interrupt once, discard payload, clean up | `ADAPTER_FAILED / INVALID_ADAPTER_EVENT` |
| Tool request | Unexpected tool, arguments, count, concurrency, or direct credential-bearing command appears | Deny tool, interrupt turn, clean bridge/proxy | `POLICY_FAILED / MCP_TOOL_DENIED` (proposed) |
| Tool result | Result exceeds bounds or cannot be validated/redacted before Codex | Withhold result, cancel workflow, retain category only | `POLICY_FAILED / MCP_RESULT_REJECTED` (proposed) |
| Timeout/cancel | Deadline expires or operator cancels | Interrupt once, close within cleanup bound, no retry | `TIMED_OUT` or `CANCELLED` |
| Advisory output | Output is oversized, malformed, contains sensitive markers, or cannot be presented ephemerally | Suppress output; retain terminal failure category only | `POLICY_FAILED / ADVISORY_OUTPUT_REJECTED` (proposed) |
| Evidence | Raw/protected content would be retained or metadata write fails | Discard unsafe draft, stop acceptance claim | `EVIDENCE_FAILED` |
| Cleanup | Process, workspace, approval artifact, temporary marker, or listener remains | Keep remote disabled; require operator repair and revalidation | `ERR_REMOTE_CLEANUP` (proposed) |
| Rollback | Permanent orchestrator or `assistant` denial is not restored | Block all further remote operations | `ERR_REMOTE_ROLLBACK` (proposed) |
| Upgrade | New pin changes public behavior or fails fake/local gates | Restore previous accepted wheelhouse/venv/unit; require reacceptance | `VENDOR_BLOCKED / SDK_UPGRADE_REJECTED` (proposed) |

No failure permits an automatic retry, second request, broader egress, credential inspection, raw-output retention, custom provider, proxy, provider-gateway fallback, packet capture, or private-protocol investigation.

### VI. Security, Integrity, Idempotency, and Cleanup

- **Approval security:** approvals are operation-specific, non-secret, bounded, expiring, consumed once, and removed after use. Authentication, remote acceptance, upgrade, and recurring use are separate authorities.
- **Credential security:** Codex-home remains opaque. OpenStack credentials remain inaccessible to `aiops-orchestrator` and Codex; only the reviewed bridge may invoke the credential-bearing read-only runner.
- **Content security:** fixed prompt text is non-sensitive and repository-owned. Raw model/provider/SDK/tool/authentication output is never logged or persisted. Only validated advisory output may reach the operator ephemerally.
- **SDK integrity:** exact hash-locked versions and reviewed public APIs only. Unknown public behavior fails closed.
- **MCP integrity:** exact capability discovery, exact tool/arguments, one call, one concurrent call, bounded result, pre-Codex redaction, correlation validation, and local peer authentication.
- **Network security:** temporary capability belongs only to the dedicated identity and approved window. No generic proxy, caller route, custom provider, listener, or permanent allow is introduced.
- **Filesystem security:** root-owned code, venv, units, and policy; exact service-writable work/home/evidence paths; private temporary approval/work artifacts; no symlink traversal or Codex-home recursion.
- **Process security:** one-shot cgroup, no auto-start, no recurring timer, bounded runtime, no retained child, and default fake-only service unchanged.
- **Evidence integrity:** append only closed categories, counts, approved versions, and validation outcomes. Validate sequence/capacity without reading raw records into repository artifacts.
- **Idempotency:** preflight and validators are repeatable. The provider operation is intentionally non-idempotent and must never be retried under the same approval.
- **Cleanup:** consume approval once; close SDK handles once; stop exact processes; remove exact temporary work/approval/egress artifacts; preserve authentication home; restore permanent deny; rerun validators after success and every failure.
- **Rollback:** restore the Phase 11 fake-only unit/artifact/venv and permanent owner rejection. Rollback does not enable the provider gateway or erase historical evidence.

### VII. Validation Strategy

All local Python checks use a dedicated temporary virtual environment. Static/local checks do not authorize authentication, firewall mutation, DNS, or provider access.

#### Python contracts, adapter, MCP, and entrypoint

```bash
rtk python3 -m venv /tmp/openstack-ai-ops-phase12-venv
source /tmp/openstack-ai-ops-phase12-venv/bin/activate
rtk python -m pip install --require-hashes -r ansible/ai_ops_runtime/files/orchestrator/requirements.lock
rtk python -m ruff format --check ansible/ai_ops_runtime/files/orchestrator
rtk python -m ruff check ansible/ai_ops_runtime/files/orchestrator
rtk python -m mypy ansible/ai_ops_runtime/files/orchestrator/src ansible/ai_ops_runtime/files/orchestrator/tests
rtk python -m py_compile ansible/ai_ops_runtime/files/orchestrator/src/openstack_ai_ops_orchestrator/*.py ansible/ai_ops_runtime/files/orchestrator/tests/*.py
rtk python -m pytest -q ansible/ai_ops_runtime/files/orchestrator/tests/test_remote_acceptance.py ansible/ai_ops_runtime/files/orchestrator/tests/test_official_codex_adapter.py ansible/ai_ops_runtime/files/orchestrator/tests/test_runtime_entrypoint.py
```

Add the confirmed bridge/proxy test files to the targeted pytest command after Chunk 0 selects them. Required proofs include:

- ordinary and fake paths cannot construct the official runtime;
- invalid/expired/reused approval fails before process, socket, DNS, SDK, MCP, or evidence mutation;
- one approval permits at most one injected SDK lifecycle and zero retries;
- fixed prompt/model/workflow/tool/path/environment cannot be caller-overridden;
- unknown events/statuses/tool calls/results fail closed without raw payload escape;
- cancellation, timeout, interrupt-once, close, and cleanup are bounded;
- bridge peer authorization and credential denial are enforced;
- tool results are validated/redacted before the SDK mock receives them;
- advisory output is byte-bounded, marker-checked, and absent from evidence/log captures.

#### Ansible and systemd static validation

```bash
rtk ansible-playbook -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_validate_phase12_remote_preflight.yml --syntax-check
rtk ansible-playbook -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_operate_orchestrator_remote_acceptance.yml --syntax-check
rtk ansible-lint ansible/ai_ops_runtime/roles/orchestrator_runtime ansible/ai_ops_runtime/roles/orchestrator_egress ansible/ai_ops_runtime/playbook_validate_phase12_remote_preflight.yml ansible/ai_ops_runtime/playbook_operate_orchestrator_remote_acceptance.yml
rtk systemd-analyze verify <rendered-remote-unit-path>
```

Static tests must prove exact inputs, one-request allowance, expiry, no raw-output registration, `no_log`, separate unit identity, no auto-enable/listener/restart, bounded timeout, empty proxy environment, exact writable paths, unconditional approval/egress cleanup, and restoration of the fake-only unit.

#### Approval-gated target validation

Target commands and exact variables must be finalized only after Chunk 0. Execute them in separate approval-gated chunks:

1. no-provider Phase 11 and Phase 12 preflight;
2. operator-private authentication status, if freshly authorized;
3. one remote acceptance operation, if freshly authorized;
4. post-operation and rollback validation.

Retain only closed outcomes and counts. Do not include command output, prompt, response, advisory text, SDK events, provider metadata, endpoint data, credentials, Codex-home contents, firewall output, or probe output in evidence or handoffs.

#### Documentation and final review

```bash
rtk grep -nE '^### (I|II|III|IV|V|VI|VII|VIII|IX|X)\.' docs/ai-ops/implementation-plan/ads/12-00-controlled-remote-acceptance-and-operations-ads.md
rtk grep -nE '^#### Chunk [0-7]:' docs/ai-ops/implementation-plan/ads/12-00-controlled-remote-acceptance-and-operations-ads.md
rtk git diff --check
rtk git diff -- docs/ai-ops/implementation-plan/ads/12-00-controlled-remote-acceptance-and-operations-ads.md
```

After every implementation chunk, review status, diff stat, `git diff --check`, complete scoped diff, prohibited provider/custom-routing patterns, credential terms, output registration, broad network rules, unsafe modes, listener/auto-start directives, and approval/retry behavior.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass. Each chunk ends after targeted validation, scoped diff review, risk assessment, and—before any live operation—confirmation of the required fresh approval.

#### Chunk 0: Discovery and Integration Confirmation
- **Goal:** Confirm all Phase 12 gates without editing or contacting a provider, especially the missing credential-preserving MCP pre-consumption boundary, pinned public SDK lifecycle, fixed acceptance profile, advisory presentation, one-shot approval, service isolation, and enforceable egress/rollback design.
- **Files to read:** this ADS; Phase 12 plan; Phase 11 ADS/evidence/authentication runbook; orchestrator contracts, official adapter, orchestrator, MCP client, evidence, entrypoint, tests, lock; runtime/egress roles, units, and validators; any located bridge/proxy implementation; pinned public SDK source/types available locally.
- **Commands:** bounded `rtk find`, `rtk grep`, targeted reads, package/lock metadata checks, local static tests, rendered-unit inspection, and sanitized target metadata only. Do not authenticate, inspect Codex-home or credential contents, alter egress, perform DNS, start the real SDK, or contact a provider.
- **Evidence to confirm:** Phase 11 passes immediately beforehand; SDK pin/public methods/config/statuses; pre-consumption MCP redaction and credential split; exact prompt/model/workflow/limits; one-shot approval lifecycle; non-persistent advisory channel; separate remote unit; honest egress boundary; cleanup/rollback; closed evidence categories.
- **Validation:** produce a decision table marking every item confirmed, proposed, deferred, or blocker with exact repository/public-source evidence.
- **Stop condition:** stop Phase 12 before source edits if the MCP bridge/redaction seam, SDK contract, credential boundary, output handling, one-request enforcement, egress restoration, or threat-model fit remains unsafe. Do not treat completed Phase 11 synthetic validation as proof of these remote boundaries.

#### Chunk 1: Credential-Preserving MCP Pre-Consumption Slice
- **Goal:** Implement and prove the approved assistant-owned Unix-socket bridge plus credential-free orchestrator stdio-proxy path so one reviewed tool result is validated and redacted before Codex can receive it.
- **Files to change:** Chunk 0-confirmed bridge/proxy modules and their focused tests. Proposed files are `mcp_bridge.py`, `mcp_stdio_proxy.py`, `test_mcp_bridge.py`, and `test_mcp_stdio_proxy.py`; more than two files are justified only if separate peer and stdio processes are required by the accepted privilege boundary.
- **Symbols to add/change:** fixed bridge request/result envelopes, exact authenticated-peer check, reviewed-capability validator, correlation/sequence guard, bounded read/write, pre-Codex redactor, timeout/cancellation, and cleanup.
- **Implementation shape:** credential-bearing execution remains under `assistant`; the Unix-socket bridge authenticates only the approved local peer. The proxy runs without credentials, TCP listeners, or caller-selected command/path/tool and forwards only validated/redacted content. Tests use fixtures/mocks and start no credential-bearing runner, listener, DNS, or provider runtime.
- **Validation:** focused unit/integration tests for allowed tool, denied peer/tool/arguments, malformed/oversized result, sensitive marker, timeout/cancel, disconnect, sequence mismatch, cleanup, no TCP listener, and credential-path denial; Ruff, mypy, `py_compile`, and scoped diff.
- **Stop condition:** the approved local boundary is demonstrably pre-consumption and privilege-separated. Otherwise stop with `MCP_INTERCEPTION_UNSUPPORTED`; do not proceed to an SDK lifecycle or remote entrypoint.

#### Chunk 2: One-Shot Approval Contracts and Fail-Closed Stubs
- **Goal:** Add minimal compile-safe acceptance policy/capability contracts while keeping all production remote paths unreachable.
- **Files to change:** proposed `remote_acceptance.py`; proposed `test_remote_acceptance.py`.
- **Symbols to add/change:** conceptual `RemoteAcceptancePolicy`, `ValidatedOneShotApproval`, policy validator, consumption guard, closed acceptance errors/categories, and a disabled operation stub.
- **Implementation shape:** exact schema and constants only. The temporary operation stub returns/raises a fixed remote-disabled result; it cannot construct SDK/MCP/process/network objects or return a success capability. Approval count is exactly one, retry count zero, expiry bounded, and reuse rejected.
- **Validation:** focused Ruff, mypy, `py_compile`, pytest for missing/invalid/expired/reused/broadened approvals, runtime-boundary monkeypatches, symbol scan, and scoped diff.
- **Stop condition:** all approval variants fail closed deterministically, stubs compile, existing fake tests remain green, and no call site can reach the real adapter.

#### Chunk 3: Bounded Official SDK Lifecycle Behind the Gate
- **Goal:** Complete one production-shaped public SDK lifecycle under an injected consumed capability while preserving the permanent disabled default.
- **Files to change:** `official_codex_adapter.py`; `test_official_codex_adapter.py`.
- **Symbols to add/change:** confirmed SDK factory/config mapper, capability check, one-client/thread/turn coordinator, closed event/status/error reducer, output extractor/validator seam, interrupt-once and close guards.
- **Implementation shape:** use public API only and public-shape mocks in tests. No live SDK client is constructed by tests. Unknown/content-bearing events fail closed. Zero retries. Ordinary adapter construction and `build_curated_codex_config()` without a consumed capability remain disabled.
- **Validation:** success/auth-required/start-failure/runtime-failure/unknown-event/extra-turn/cancel/deadline/cleanup mock tests; Ruff/mypy/compile; process/socket/DNS/auth/credential prohibition tests; full orchestrator regression; scoped diff.
- **Stop condition:** exactly one mocked lifecycle is bounded and sanitized; approval reuse is impossible; no raw payload escapes; default remote selection remains disabled.

#### Chunk 4: Fixed Remote Entrypoint and Mocked End-to-End Slice
- **Goal:** Wire one fixed remote profile from consumed approval through the official adapter and reviewed MCP proxy to bounded evidence and sanitized advisory presentation, using mocks only.
- **Files to change:** `runtime_entrypoint.py`; `test_runtime_entrypoint.py`, or a separate Chunk 0-confirmed one-shot entrypoint plus its test.
- **Symbols to add/change:** fixed remote profile builder, approval loader/consumer, repository-owned request/policy, official adapter factory injection, MCP proxy configuration, closed exit categories, and advisory presenter seam.
- **Implementation shape:** keep no-argument fake behavior unchanged. Remote use requires the one-shot capability and fixed constants; arbitrary input remains rejected. The mocked success path exercises one turn/tool/result/advisory lifecycle. The stub fails before SDK construction if any prerequisite is absent.
- **Validation:** mocked terminal categories, approval consumption, fixed profile, no retry, output bounds/marker checks, no evidence/log content, fake regression, Ruff/mypy/compile/pytest, prohibited-input scan, and scoped diff.
- **Stop condition:** one fully mocked vertical slice terminates cleanly and emits only accepted process/advisory behavior; no live runtime/network/authentication is used.

#### Chunk 5: Hardened Remote Unit, No-Provider Preflight, and Operations Runbooks
- **Goal:** Add non-enabled deployment/operation artifacts and complete operator procedures without opening egress or making a provider request.
- **Files to change:** proposed remote unit template, Phase 12 preflight playbook, remote operation playbook, egress role/templates as required, `orchestrator-remote-operations.md`, and upgrade/rollback runbook. Multiple files are justified by the systemd, approval, egress, validation, and operator procedure vertical slice.
- **Symbols to add/change:** separate one-shot unit, exact approval variables/schema, remote egress mode rendering, preflight assertions, single invocation, `always` cleanup, post-validator includes, auth-expiry/disablement/upgrade/rollback procedures.
- **Implementation shape:** install but do not enable/start the remote unit. Default remains fake-only and denied. The operation playbook defaults to no-op/fail-closed, uses `no_log`, never registers content output, consumes one approval, has no retry, and removes approval/egress artifacts in `always`.
- **Validation:** YAML parse, syntax-check, ansible-lint, rendered `systemd-analyze verify`, invalid approval/check-mode tests where meaningful, static `no_log`/no-retry/always-cleanup assertions, fake unit regression, Markdown review, and scoped diff.
- **Stop condition:** all artifacts are reviewable and fail closed with no approval; no live authentication, firewall mutation, DNS, or provider operation has occurred.

#### Chunk 6: Final Local Preflight and Authentication Gate
- **Goal:** Prove every local/synthetic gate immediately before remote approval and establish only a closed authentication status.
- **Files to change:** none unless one small evidence-backed correction is separately reviewed; do not write Phase 12 acceptance evidence yet.
- **Symbols to add/change:** none expected.
- **Implementation shape:** run package integrity, deployment, fake, local MCP bridge, evidence capacity/schema, protected-path, process/listener, permanent orchestrator egress, and independent `assistant` validators. Authentication status is operator-private and requires fresh authorization; automation receives only its closed category.
- **Validation:** accepted target preflight commands from Chunk 5, repeated Phase 11 validators, bridge/proxy local smoke, temporary-workspace absence, permanent-policy checks, and operator-declared auth category. Store no raw output in repository or handoff.
- **Stop condition:** all local gates pass immediately and authentication category is `authenticated`. Any drift or other category stops before one-request approval is requested or consumed.

#### Chunk 7: One Approved Remote Workflow, Rollback, and Sanitized Acceptance
- **Goal:** Execute exactly one freshly approved remote workflow, stop at its first terminal category, restore the Phase 11 baseline, record metadata-only evidence, and finalize runbooks.
- **Files to change:** proposed `phase12-controlled-remote-acceptance-evidence.md`; runbooks and Phase 12 plan checkboxes only after outcomes are accepted. Operation artifacts may receive only a small evidence-backed correction followed by revalidation and a new approval if the prior approval was consumed.
- **Symbols to add/change:** sanitized evidence categories/counts/outcomes and final operational clarifications; no new request behavior during the live chunk.
- **Implementation shape:** obtain explicit approval for one fixed request; materialize temporary egress; consume approval before runtime start; execute once; no retry; present only validated ephemeral advisory output; retain categories/counts only; unconditionally remove process/workspace/approval/egress state; rerun every post-validator. Supported SDK/runtime failure is an acceptable documented vendor blocker.
- **Validation:** one-request count, terminal category, approval exhaustion, zero retained temporary markers/processes/listeners/workspaces, permanent orchestrator and `assistant` denial, deployment/package/MCP/evidence validators, fake regression, documentation scans, `git diff --check`, security scan, and complete scoped diff.
- **Stop condition:** exactly one approved attempt occurred; cleanup and post-validation pass; no protected content is retained; regular remote use remains disabled; no gateway fallback exists. If cleanup or evidence fails, Phase 12 remains incomplete and further requests are blocked.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, pre-edit-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Phase 12 controlled one-request remote acceptance and operations as specified by docs/ai-ops/implementation-plan/ads/12-00-controlled-remote-acceptance-and-operations-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm the Phase 11 baseline, pinned public SDK contract, credential-preserving MCP bridge and pre-Codex redaction seam, fixed prompt/model/workflow/limits, one-shot approval lifecycle, non-persistent advisory presentation, separate remote unit, enforceable egress boundary, and unconditional rollback. Do not authenticate, inspect Codex-home or credential contents, change firewall state, perform DNS, start the real SDK, select the official adapter, or contact a provider. Produce an evidence/decision table and stop on any blocker.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, pre-edit-discipline, safe-python-edit, and post-edit-discipline if available.
Execute Chunk 1 only from the accepted Phase 12 ADS and Chunk 0 decisions.
Do not continue to Chunk 2. Implement only the approved assistant-owned Unix-socket bridge and credential-free orchestrator stdio proxy with mocked tests. Do not construct the SDK, invoke the credential-bearing MCP runner, authenticate, inspect credentials, alter egress, perform DNS, or contact a provider. Run targeted Ruff, mypy, py_compile, pytest, prohibited-boundary checks, and show the scoped git diff before stopping.
```

### X. Conclusion and Next Steps

- Phase 11 completion makes Phase 12 **ready for ADS review and no-provider Chunk 0 discovery**, not ready for immediate authentication or a provider request.
- The current repository remains fake-only: the remote entrypoint is disabled, the official adapter has only mocked lifecycle behavior, the static unit has no network, and permanent dedicated-identity egress is denied.
- Chunk 0 confirmed that no existing credential-preserving MCP bridge/stdio proxy is implemented. The assistant-owned Unix-socket bridge and credential-free orchestrator stdio-proxy design is approved; Chunk 1 implements and proves that boundary before any SDK lifecycle or remote entrypoint work.
- The safe implementation shape is a separate, one-shot, approval-capability path. It must not permanently set the official adapter enabled, weaken the fake unit, add retries, or introduce recurring remote use.
- Authentication status and the one provider request require separate fresh approvals. Neither is authorized by this ADS or by Phase 11 synthetic-validation approval.
- The next action is Chunk 1 only: implement and prove the approved local bridge/proxy with mocks. Any SDK lifecycle, authentication, egress change, DNS, or provider request remains stopped until its explicit later gate is reached and freshly authorized.
