# Phase 12 One-Shot Remote Operation Boundary ADS

## Status

**Decision:** replace the permanent terminal stub only inside a separately approved, one-shot operation path. Preserve fail-closed behavior for ordinary invocation, fake validation, missing or invalid approval, repeated invocation, and every cleanup failure.

This ADS is the missing implementation prerequisite for **Chunk 9: One Separately Approved Live Codex MVP Acceptance** in `docs/ai-ops/implementation-plan/ads/12-01-phase12-gated-remote-boundary-ads.md`. The previously described “Phase 9” is therefore **Chunk 9 of the Phase 12 ADS**, not a separate project phase. Chunks 0–8 of that ADS established the offline contracts; Chunk 9 cannot execute while the operation capability, production SDK factory, remote entrypoint, and operation playbook remain intentionally unreachable.

This document authorizes design and offline implementation only. It does not itself authorize authentication, DNS, temporary provider egress, bridge or remote-unit activation, or a provider request. Final live acceptance still requires fresh operation-specific and temporary-egress approvals after all implementation and preflight gates pass.

**Source:**

- `docs/ai-ops/implementation-plan/ads/12-01-phase12-gated-remote-boundary-ads.md`
- `docs/ai-ops/implementation-plan/ads/12-00-controlled-remote-acceptance-and-operations-ads.md`
- `docs/ai-ops/runtime/orchestrator-remote-operations.md`
- `docs/ai-ops/runtime/phase12-sdk-mcp-vendor-blocker-decision.md`

**Goal:** make exactly one approved live workflow reachable without enabling a regular remote mode or weakening the repository's disabled baseline.

---

### I. Overview and Contract

The remote operation is a narrow capability, not a global adapter switch. A root-controlled operation playbook validates fixed inputs and current deployment state, materializes one private approval artifact and one temporary egress window, starts the exact assistant bridge socket and static remote unit once, and then performs unconditional cleanup. The runtime atomically consumes the approval artifact before constructing any SDK object, issues an in-process opaque operation capability, creates one curated official SDK client, and executes the already-fixed request through the existing orchestrator and bridge boundaries.

The following defaults remain unchanged:

- `main()` with no arguments runs the deterministic fake profile.
- Arbitrary arguments remain rejected.
- `--profile remote` without the exact fresh artifact remains disabled.
- `OFFICIAL_ADAPTER_ENABLED` must not become an unconditional `True` global.
- The remote service, bridge socket, and bridge service remain static, disabled, and stopped outside the bounded operation.
- Permanent orchestrator egress remains `mode: disabled`.

The current `run_remote_operation_cleanup_stub()` is replaced only after a valid one-shot artifact has been atomically exhausted. The disabled function may be retained for prohibited-path regression tests, but it must no longer be the approved operation's terminal behavior.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `remote_acceptance.py` defines `RemoteOperationCapability`, but its private token is never issued; `run_remote_operation_cleanup_stub()` always raises `REMOTE_ACCEPTANCE_DISABLED`.
- `runtime_entrypoint.py` contains a complete injected offline slice in `_run_fixed_remote_mocked()`, while public `main()` returns `REMOTE_DISABLED` for the remote profile.
- `official_codex_adapter.py` implements bounded notification reduction and an injected mocked lifecycle. Its production configuration is blocked by `OFFICIAL_ADAPTER_ENABLED = False`, and no production factory is connected.
- `playbook_operate_orchestrator_remote_acceptance.yml` asserts that apply is false and then stops the unit and removes the approval artifact.
- `aiops-orchestrator-remote.service.j2` is static, one-shot, conditioned on the approval artifact, has no restart, and has a 45-second start timeout.
- `playbook_operate_orchestrator_auth_egress_window.yml` is authentication-only; it unconditionally removes its DNS/HTTPS rules.
- `playbook_operate_orchestrator_egress_window.yml` proves rollback only against a fixed synthetic endpoint. It is not a reviewed live-provider operation.
- `playbook_validate_phase12_assistant_bridge_activation.yml` validates bridge activation with a fake runner only and cleans up the socket and service.
- The corrected no-provider preflight passes when invoked with `-e @generated/runtime.yml`.

#### Assumptions requiring confirmation in Chunk 0

- The pinned `openai-codex==0.144.4` production constructor and close behavior still match the public API characterized by existing tests.
- The deployed assistant bridge service entrypoint uses the reviewed real read-only runner when no fake validation drop-in exists.
- A provider request egress policy can be represented by a separately approved, bounded owner-scoped DNS/HTTPS window without recording destination or provider content. If this cannot be proven, implementation stops.
- Authentication status remains operator-reported metadata; automation does not inspect Codex-home or login output.

### III. Required Technical Dependencies and Contracts

Existing dependencies remain pinned; this design adds no package, gateway, proxy, API-key path, generic HTTP client, or private protocol.

**Operation Capability Contract (Conceptual):** an opaque `RemoteOperationCapability` is issued only after atomic approval-artifact consumption. It binds the consumed approval identifier and cannot be constructed by ordinary callers. A process restart cannot reuse the removed artifact.

**Production Factory Contract (Conceptual):** a repository-owned factory accepts only the curated `CodexConfig` and returns the pinned public async client. It is reachable only when both a consumed approval and a valid operation capability are present. There is no boolean environment override or caller-selected factory, model, prompt, working directory, MCP command, or provider endpoint.

**Runtime Contract (Concrete from existing code):** one fixed workflow, one turn, one tool call, one concurrent tool call, zero automatic retries, a 30-second runtime deadline, bounded events/output, metadata-only evidence, and one ephemeral advisory presenter.

**Artifact Contract (Conceptual):** the operation playbook writes one regular, non-symlink private JSON artifact with the existing exact fields and bounded expiry. The runtime opens and validates it without following links, removes it atomically before SDK construction, and fails closed if removal or directory synchronization fails. Ownership and mode must allow only root materialization and the dedicated remote service's one read/consume operation.

Expected implementation surfaces:

- `remote_acceptance.py` and `test_remote_acceptance.py`
- `official_codex_adapter.py` and `test_official_codex_adapter.py`
- `runtime_entrypoint.py` and `test_runtime_entrypoint.py`
- `playbook_operate_orchestrator_remote_acceptance.yml`
- operation/preflight tests or repository-native static validation
- `orchestrator-remote-operations.md` and metadata-only acceptance evidence

### IV. Step-by-Step Procedure / Execution Flow

1. Run the Phase 12 no-provider preflight with `generated/runtime.yml`; retain only pass/fail.
2. Validate a fresh operation approval and a separate fresh temporary-egress approval. Confirm fixed workflow/model/prompt/tool limits, target host, expiry, one attempt, and zero retries.
3. Reject stale approval artifacts, active bridge/remote units, temporary egress markers, socket residue, work residue, or mismatched deployed source/unit integrity before any operation mutation.
4. Materialize the private approval artifact and reviewed temporary remote egress window in one Ansible `block` guarded by unconditional `always` cleanup.
5. Start the exact static assistant bridge socket. Do not enable it and do not install a fake-runner drop-in.
6. Start the exact static remote one-shot service once. Do not invoke its Python module a second time and do not retry a failed systemd start.
7. In the remote process, load and validate the exact approval artifact, then atomically exhaust it before constructing MCP or SDK runtime objects.
8. Issue the opaque in-process operation capability and build only the curated pinned SDK configuration and fixed MCP stdio proxy command.
9. Run one client, thread, turn, and fixed tool workflow. Reduce tainted SDK notifications immediately; present only bounded sanitized advisory text ephemerally; persist metadata-only evidence.
10. Stop on the first terminal category, including bounded SDK/vendor failure.
11. In process cleanup, close the exact notification stream, turn/client, proxy, and temporary workspace. Never retry or inspect raw failure data.
12. In playbook cleanup, stop the bridge socket before its service, stop the remote service, remove the approval artifact and exact temporary egress markers, reload policy, and restore permanent denial.
13. Verify remote/bridge units are static and inactive, socket/artifact/work residue is absent, request allowance is exhausted, no process/listener delta remains, and permanent egress denial is restored.
14. Re-run no-provider preflight and fake regression. Record only request count, terminal category, cleanup results, versions, and validator outcomes.

### V. Failure Modes and Resilience

| Stage | Failure mode | Required action | Closed outcome |
|---|---|---|---|
| Preflight | Deployment, integrity, fake, bridge, approval-absence, or permanent-deny check fails | Mutate nothing; stop | `REMOTE_PREREQUISITE_FAILED` |
| Approval | Missing, malformed, expired, reused, broad, unsafe file, or atomic consumption failure | Construct no proxy/SDK; clean artifact | `REMOTE_APPROVAL_INVALID` |
| Capability | Ordinary caller or invalid capability reaches production factory | Construct no client | `REMOTE_ACCEPTANCE_DISABLED` |
| Authentication | Operator reports not authenticated | Restore baseline; require separate auth operation | `AUTH_ACTION_REQUIRED` |
| Egress | Temporary rule cannot be bounded, applied, or validated | Remove exact markers; start no service | `REMOTE_EGRESS_FAILED` (proposed) |
| Bridge | Socket/unit/peer/redaction contract fails | Stop socket then service; issue no request | `MCP_INTERCEPTION_UNSUPPORTED` |
| SDK start | Curated client/thread/turn cannot start | No retry; close owned resources | `SDK_START_FAILED` |
| SDK event | Unknown type/order/identity/size or unsafe advisory | Interrupt at most once; suppress content | Existing closed adapter failure |
| Tool | Unknown request, extra call, timeout, or unsafe result | Deny, close bridge/proxy, no fallback | Existing closed MCP/policy failure |
| Deadline/cancel | Bounded deadline or operator cancellation | Interrupt once; cleanup | `DEADLINE_EXCEEDED` or `CANCELLED` |
| Evidence | Metadata validation/write fails or content would persist | Persist no unsafe record; block acceptance | `EVIDENCE_FAILED` |
| Cleanup | Unit, process, socket, artifact, workspace, or egress marker remains | Block all further requests; operator repair | `REMOTE_CLEANUP_FAILED` (proposed) |
| Postflight | Disabled baseline or fake regression fails | Phase remains incomplete | `REMOTE_BASELINE_FAILED` (proposed) |

No failure permits a second request, automatic retry, broader egress, credential inspection, raw exception retention, packet capture, private-protocol debugging, or provider-gateway fallback.

### VI. Security, Integrity, Idempotency, and Cleanup

- **Default deny:** the ordinary adapter and remote entrypoint remain disabled; only the exact consumed operation capability reaches production construction.
- **Single use:** artifact exhaustion happens before runtime construction and is durable enough that service restart cannot replay the approval.
- **No global enable flag:** do not set `OFFICIAL_ADAPTER_ENABLED = True` as a deployment default, inventory variable, environment variable, or test bypass.
- **Credentials:** never inspect, copy, hash, parse, log, or delete Codex-home or OpenStack credential contents.
- **Network:** temporary owner-scoped remote egress exists only inside the operation block and is removed on every terminal path. Permanent disabled policy remains the deployment baseline.
- **IPC:** the assistant bridge remains Unix-socket-only, exact-peer-UID checked, fixed-tool-only, and redacts before Codex receives the runner result.
- **Content:** raw SDK/provider/tool/authentication data stays out of logs, evidence, Ansible registered output, handoffs, and persistent files.
- **Idempotency:** validators and cleanup are repeatable; the provider request is deliberately non-idempotent and cannot be repeated under one approval.
- **Rollback:** stop socket before service, stop remote unit, remove only exact artifacts/markers/workspace, restore permanent denial, and rerun preflight.

### VII. Validation Strategy

All Python execution uses a dedicated temporary virtual environment populated from the pinned lock/wheelhouse. Offline validation must not authenticate, change provider egress, resolve provider DNS, start live units, or contact a provider.

Required offline checks:

```bash
rtk python3 -m venv /tmp/openstack-lab-phase12-operation-venv
source /tmp/openstack-lab-phase12-operation-venv/bin/activate
rtk python -m pip install --require-hashes -r ansible/ai_ops_runtime/files/orchestrator/requirements.lock
rtk python -m ruff format --check <changed-python-files>
rtk python -m ruff check <changed-python-files>
rtk python -m py_compile <changed-python-files>
rtk python -m mypy --strict <changed-source-and-test-files>
rtk python -m pytest -q <targeted-remote-adapter-entrypoint-tests>
rtk ansible-playbook -i ansible/ai_ops_runtime/inventories/local/local.yml -e @generated/runtime.yml ansible/ai_ops_runtime/playbook_operate_orchestrator_remote_acceptance.yml --syntax-check
rtk ansible-playbook -i ansible/ai_ops_runtime/inventories/local/local.yml -e @generated/runtime.yml ansible/ai_ops_runtime/playbook_validate_phase12_remote_preflight.yml --syntax-check
rtk git diff --check
```

Tests must prove:

- missing, invalid, expired, reused, or non-atomically-consumed approval never constructs a production SDK client;
- production construction requires the opaque capability while fake and injected mocked behavior remain unchanged;
- exactly one factory/client/thread/turn/tool call occurs and no retry path exists;
- all resource-close and operation-cleanup paths execute once on success, cancellation, timeout, adapter failure, and presenter/evidence failure;
- the operation playbook begins and ends with static inactive units, absent artifact/socket/markers, and permanent disabled egress;
- no raw prompt, response, advisory, event, tool result, credential, destination, or exception content enters evidence or Ansible output.

Final live validation is a separate operation after offline acceptance. It requires fresh explicit authorization because the prior authorization preceded this new operation-boundary implementation. Its stop condition is one attempt completed or one bounded failure, followed by verified cleanup and disabled baseline restoration.

### VIII. Thin Vertical Slice Chunk Design

Implementation must proceed through `chunked-implementation`; do not combine the operation boundary into one broad patch.

#### Chunk 0: Production Integration Confirmation
- **Goal:** confirm pinned SDK constructor/close contracts, deployed real bridge entrypoint, artifact ownership/atomic-consumption mechanism, and enforceable temporary remote egress shape.
- **Files to read:** official adapter, remote acceptance/entrypoint, operation and egress playbooks, bridge units/entrypoint, pinned SDK public package, tests.
- **Commands:** targeted `grep`, bounded reads, Ansible variable inspection, and public SDK signature inspection in `/tmp/openstack-lab-phase12-operation-venv`.
- **Evidence to confirm:** no caller-selected values, no second request path, real bridge delegates only to reviewed runner, operation can always roll back.
- **Validation:** discovery report only; no files changed and no live action.
- **Stop condition:** every production integration point is concrete; otherwise record a blocker and do not continue.

#### Chunk 1: Atomic Capability Issuance
- **Goal:** replace the unissuable capability stub with a single-use, artifact-backed in-process authorization while retaining disabled defaults.
- **Files to change:** `remote_acceptance.py`, `test_remote_acceptance.py`.
- **Symbols to add/change:** atomic approval consumption/issuance helper, `RemoteOperationCapability`, cleanup/error categories as confirmed by Chunk 0.
- **Implementation shape:** validate and atomically exhaust one exact artifact, return consumed approval plus opaque capability; all other paths fail closed.
- **Validation:** Ruff, py_compile, strict mypy, targeted approval tests, diff scan.
- **Stop condition:** replay/restart/symlink/permission/cleanup tests pass and no SDK/MCP/network object is introduced.

#### Chunk 2: Capability-Gated Production SDK Lifecycle
- **Goal:** connect the pinned public SDK factory without global enablement.
- **Files to change:** `official_codex_adapter.py`, `test_official_codex_adapter.py`.
- **Symbols to add/change:** curated official factory and capability-gated adapter construction/lifecycle.
- **Implementation shape:** one client/thread/turn, existing tainted reducer, interrupt at most once, exact close, no retry, injected production-shaped tests.
- **Validation:** Ruff, py_compile, strict mypy, targeted adapter tests, prohibited global-enable/network scans.
- **Stop condition:** valid capability reaches one injected production lifecycle; every ordinary path remains `REAL_ADAPTER_DISABLED`.

#### Chunk 3: Fixed Live Entrypoint Wiring
- **Goal:** connect the remote profile to atomic capability issuance, fixed proxy, official adapter, metadata evidence, ephemeral presenter, and cleanup.
- **Files to change:** `runtime_entrypoint.py`, `test_runtime_entrypoint.py`.
- **Symbols to add/change:** fixed remote runner and remote branch in `main()`; preserve fake and arbitrary-input behavior.
- **Implementation shape:** exact repository constants only; one attempt; consume before construction; cleanup in `finally`; closed exit categories only.
- **Validation:** Ruff, py_compile, strict mypy, targeted entrypoint/integration tests, raw-content and caller-input scans.
- **Stop condition:** offline injected end-to-end operation succeeds once and all failure paths restore process-local state; no real client is invoked in tests.

#### Chunk 4: Reviewed Operation and Remote Egress Playbook
- **Goal:** replace the playbook's unconditional rejection with a default-false, explicitly approved one-shot orchestration block.
- **Files to change:** remote acceptance operation playbook and the smallest required egress operation artifact selected in Chunk 0.
- **Symbols/variables to add/change:** fixed apply flag, separate approval/expiry, exact artifact, bounded remote egress, unit-start count, cleanup assertions.
- **Implementation shape:** validate inputs; preflight; reject stale state; materialize artifact/egress; start bridge and remote unit once; unconditional stop/remove/restore/postflight. `apply: false` performs no live operation.
- **Validation:** Ansible syntax/lint, check-mode/static tests where safe, `systemd-analyze verify`, prohibited enable/restart/raw-output scans.
- **Stop condition:** default invocation is no-op/fail-closed and injected failure tests prove artifact, unit, socket, and egress cleanup without provider traffic.

#### Chunk 5: Offline Full-Scope Gate and Deployment Refresh
- **Goal:** validate and deploy the reviewed boundary while preserving the disabled baseline; do not issue a provider request.
- **Files to change:** tests/runbook only if evidence-backed corrections are required.
- **Symbols to add/change:** none unless a targeted gate identifies a defect.
- **Implementation shape:** full scoped Python suite, Ansible/static validation, source deployment, fake bridge/deployment checks, no-provider preflight.
- **Validation:** formatter/type/compile/tests, role/playbook syntax/lint, deployed integrity, fake regression, process/listener/artifact/egress absence.
- **Stop condition:** all offline and target preflight gates pass with remote and bridge units static/inactive and permanent egress disabled.

#### Chunk 6: Separately Approved One-Shot Live Acceptance
- **Goal:** satisfy Chunk 9 of the prior ADS with exactly one live attempt.
- **Files to change:** metadata-only evidence and operations record after outcome review; no request behavior changes during this chunk.
- **Symbols to add/change:** none.
- **Implementation shape:** obtain fresh one-request and temporary-egress approvals; run once; no retry; ephemeral advisory; unconditional cleanup; postflight and fake regression.
- **Validation:** request count, terminal category, approval exhaustion, unit/process/socket/workspace/egress cleanup, metadata-only evidence, disabled baseline restoration.
- **Stop condition:** exactly one attempt reaches a bounded terminal category and every cleanup/postflight gate passes. Any cleanup failure leaves Phase 12 incomplete and blocks further requests.

### IX. Handoff to `chunked-implementation`

Recommended next agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline and rtk-command-prefix.

Task:
Implement the one-shot remote operation boundary specified by
`docs/ai-ops/implementation-plan/ads/12-02-phase12-one-shot-remote-operation-boundary-ads.md`.

Mode:
Execute Chunk 0 only. Do not edit files, authenticate, alter egress, activate
units, inspect credentials/Codex-home, resolve provider DNS, or contact a
provider. Confirm the production SDK, bridge, artifact-consumption, and egress
integration points; report evidence and stop.
```

After Chunk 0 is accepted, execute each subsequent chunk in a separate session with targeted validation, diff review, risk assessment, and a confirmed handoff. Chunk 6 always requires fresh explicit live-operation authorization.

### X. Conclusion and Next Steps

Phase 12 is not completed by deleting the fail-closed checks or globally enabling the official adapter. Completion requires replacing only the approved operation's terminal stub with an opaque, atomically consumed one-shot capability and a reviewed orchestration path that always restores the disabled baseline.

The immediate next action is Chunk 0 discovery. No live request is permitted until Chunks 0–5 of this ADS pass and Chunk 6 receives fresh one-request and temporary-egress approvals. Successful Chunk 6 then supplies the missing outcome for Chunk 9 of `12-01-phase12-gated-remote-boundary-ads.md`.
