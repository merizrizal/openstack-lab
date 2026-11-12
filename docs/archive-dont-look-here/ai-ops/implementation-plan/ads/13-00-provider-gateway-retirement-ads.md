## Architectural Design Specification: Historical Provider Gateway Retirement

**Source:** `docs/ai-ops/implementation-plan/13-provider-gateway-retirement.md`, especially Steps 1-4; sequencing context from `docs/ai-ops/implementation-plan/00-implementation-overview.md`.

**Goal:** Retire the superseded custom-provider gateway from active deployment after the accepted Codex SDK orchestrator path, preserve historical schema 1/schema 2 ledger and design evidence when present or record approved `verified_absent_preexisting` when no recoverable ledger exists, keep the independent `assistant` egress denial intact, and prove that no runtime or fallback path can use the gateway.

---

### I. Overview and Contract

#### Selected phase boundary

Phase 13 changes deployment state and active-architecture documentation; it does not erase the gateway's history or authorize provider traffic.

```text
accepted Phase 12 orchestrator path
  -> read-only inventory and dependency proof
  -> explicit retirement approval
  -> metadata-only preservation checks
  -> stop and disable aiops-provider-gateway
  -> prove process/listener absence
  -> prevent normal deployment from recreating the gateway
  -> remove only approved active host artifacts
  -> revalidate the exact Phase 12 successor baseline and shared boundaries
  -> retain historical source and evidence, preserving any existing ledger or recording approved pre-existing absence, with rollback readiness
```

No action in this ADS authorizes another remote request, gateway fallback, credential inspection, raw ledger inspection, ledger mutation, or weakening of permanent egress denial.

#### State-transition contract

The gateway may move only through these states:

```text
historical_deployed
  -> preservation_confirmed
  -> disabled_stopped
  -> deployment_recreation_blocked
  -> active_artifacts_absent
  -> retired_validated

verified_absent_preexisting
  -> deployment_recreation_blocked
  -> active_artifacts_absent
  -> retired_validated
```

The first path applies only when the preservation targets exist. The second applies only after explicit operator confirmation of host rebuild/reset and no recoverable ledger. `verified_absent_preexisting` records an observed pre-existing absence; it is not successful preservation and must never cause a synthetic ledger, state directory, or identity to be created. A failed precondition leaves the gateway in its current state. A failure after stop/disable leaves it disabled and stopped. Rollback may restore the last validated **disabled** gateway artifact set only under separate approval and through a dedicated rollback path that never invokes the historical enable/start task. Rollback must not restore the normal deployment call site, start the service, open `127.0.0.1:8765`, select a custom-provider profile, or create provider traffic.

#### Approval contract

**Ansible/Operation Contract (Conceptual):** a dedicated Phase 13 retirement playbook should be default-false and bounded to `assistant01`. Before any service-state or filesystem mutation it must require a fresh, explicit retirement approval supplied through the repository's accepted operator mechanism. The exact variable names and approval representation must be confirmed in Chunk 0 rather than copied from unrelated one-shot remote-operation approval.

Approval must distinguish at least:

- permission to stop and disable `aiops-provider-gateway`;
- permission to de-wire the normal deployment call site while preserving independent assistant egress;
- permission to remove the unit and `/opt/openstack-ai-ops/provider-gateway` active payload;
- acknowledgement either that `/var/lib/aiops-provider-gateway` and its ledger are preservation targets or that the approved `verified_absent_preexisting` disposition applies;
- acknowledgement that the `aiops-provider` identity remains while it owns preserved evidence, or that it is absent pre-existing and must not be synthesized;
- a bounded rollback decision.

Approval is single-operation authority. It is not reusable authority for gateway traffic, ledger access, account removal, or later cleanup.

#### Preservation contract

**Filesystem Contract (Concrete):** based on the deployed role, validator, and evidence runbook:

- When present, preserve `/var/lib/aiops-provider-gateway/gateway-evidence.jsonl` byte-for-byte.
- When present, preserve its parent directory at mode `0700` and ledger at mode `0600`.
- When present, preserve owner/group `aiops-provider:aiops-provider` unless a separate evidence-custody ADS approves a different ownership model.
- For this approved rebuilt/reset-host disposition, record `verified_absent_preexisting` for the absent state directory, ledger, and identity; do not recreate, repair, replace, relabel, or otherwise synthesize any of them.
- Do not read raw lines or calculate a content-derived inventory from them.
- Do not delete, truncate, rotate, repair, rewrite, relabel, or migrate schema 1/schema 2 records.
- Do not import records into the orchestrator evidence schema.
- Preserve historical ADSs, runbooks, decisions, and dated evidence in Git with explicit historical/superseded status where needed.

**Metadata Contract (Conceptual):** retirement evidence may retain only path category, existence, non-symlink status, owner, group, mode, bounded size category, preservation result or approved `verified_absent_preexisting` disposition, closed service/listener state, validator pass/fail categories, and rollback readiness. It must not retain ledger bytes, parsed records, prompts, responses, authentication material, provider details, exception text, or command output.

#### Active retirement contract

The approved runtime retirement operation must:

1. prove Phase 12 acceptance and the absence of orchestrator/MCP gateway dependencies;
2. prove the exact Phase 12 disabled successor baseline through passive validation;
3. inspect preservation-target metadata without opening the ledger and either preserve existing targets or record the approved `verified_absent_preexisting` disposition;
4. stop and disable the service before changing deployment wiring or deleting any active artifact when the service exists; accept its pre-existing absence without recreating it;
5. prove no gateway process and no listener on TCP `8765` remain;
6. remove or fail-close the normal `ai_client_runtime` include that currently recreates the gateway while preserving the independent egress include;
7. prove ordinary setup cannot create, enable, start, or restart the gateway;
8. only then remove the approved unit and active service payload;
9. run systemd daemon reload and prove the unit cannot be started from the removed deployment;
10. preserve existing gateway state directory, ledger, evidence-owning identity, provider-ledger protected-path assertion, and Phase 12 successor artifacts; when the approved disposition is `verified_absent_preexisting`, preserve the absence and historical Git evidence without synthetic replacement;
11. leave independent `assistant_egress` and `assistant_egress_validation` roles unchanged and passing;
12. converge safely when repeated.

#### Contract labels

There are no proposed Python function signatures in this phase. The gateway Python source is a retirement target/historical source, not a module to extend.

**Playbook Contract (Conceptual):** a Phase 13 retirement operation owns preflight, approval validation, preservation metadata checks, stop/disable, approved artifact removal, rescue behavior, and sanitized result categories.

**Validator Contract (Conceptual):** a separate Phase 13 validator performs no gateway, bridge, or remote-service start and asserts preservation metadata, gateway service/unit/process/listener absence, no normal deployment wiring, independent assistant egress denial, active MCP/orchestrator boundaries, the exact Phase 12 static/inactive and artifact/marker-absent baseline, disabled permanent orchestrator egress, the fake-only profile, and no fallback references.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops/implementation-plan/13-provider-gateway-retirement.md` requires an evidence-based disposition and rollback path for service, identity, policy, source, tests, playbooks, firewall dependencies, state directory, ledger, and documentation. It expressly excludes ledger deletion, truncation, migration, relabelling, and raw inspection.
- `docs/ai-ops/implementation-plan/00-implementation-overview.md` places retirement after Phase 12 and states that a supported-runtime failure must not restart gateway recovery.
- `docs/ai-ops/runtime/phase12-one-shot-remote-acceptance-evidence-2026-07-31.md` records one accepted orchestrator operation, zero retries, cleanup, and restored disabled orchestrator egress. It does not authorize another request.
- `docs/ai-ops/runtime/orchestrator-remote-operations.md` prohibits custom-provider/proxy fallback and says future operations require fresh approval.
- `ansible/ai_ops_runtime/roles/ai_client_runtime/tasks/main.yml` unconditionally includes `provider_gateway.yml`, then independently includes the `assistant_egress` role. Removing the gateway include must not remove the following egress include.
- `ansible/ai_ops_runtime/roles/ai_client_runtime/tasks/provider_gateway.yml` creates `aiops-provider`, `/opt/openstack-ai-ops/provider-gateway`, its Python virtual environment and three payload files, the systemd unit, and an enabled/started service.
- `ansible/ai_ops_runtime/roles/ai_client_runtime/defaults/main.yml` defines the gateway identity, service, root, state directory, and ledger separately from `ai_ops_assistant_egress`.
- `ansible/ai_ops_runtime/roles/ai_client_runtime/templates/provider_gateway/aiops-provider-gateway.service.j2` starts the gateway as `aiops-provider`, binds its state directory, and grants write access only to `/var/lib/aiops-provider-gateway`.
- `ansible/ai_ops_runtime/playbook_validate_phase07_provider_gateway_deployment.yml` expects the service active/enabled, listener `127.0.0.1:8765`, root-owned active artifacts, and the protected ledger ownership/modes. It is a historical active-state validator and cannot be the final retirement validator.
- `docs/ai-ops/runtime/provider-gateway-metadata-evidence.md` fixes the ledger path, ownership, modes, 64 KiB bound, schema 1/schema 2 separation, raw-line prohibition, and stop-before-rollback requirement.
- `ansible/ai_ops_runtime/playbook_validate_phase11_orchestrator_deployment.yml` includes the provider ledger in `ai_ops_orchestrator_protected_paths`, demonstrating that the successor runtime treats it as protected historical data rather than an input.
- Scoped searches found no provider-gateway/custom-provider references in the orchestrator runtime role, MCP roles, Phase 12 preflight playbook, or Phase 12 operation playbook. This is repository evidence of separation, not proof of current host process state.
- `assistant_egress` and `assistant_egress_validation` are independent roles. `playbook_validate_phase07_provider_gateway_egress.yml` validates the `assistant` UID policy and does not deploy or start the provider gateway.
- `tests/ai_ops/test_provider_gateway.py` and `tests/ai_ops/test_provider_redaction.py` load only the historical provider-gateway source. No CI/Makefile call site for those test modules was found in the scoped search.
- Historical status is already explicit in `07-03-openai-remote-provider-boundary-ads-revised.md`, `phase07-remote-provider-decision-2026-07-14.md`, and `phase07-codex-sdk-orchestrator-decision-2026-07-21.md`.

#### Inventory and required disposition

| Artifact/category | Observed location or identity | Disposition | Integrity/rollback requirement |
|---|---|---|---|
| Normal deployment call site | `roles/ai_client_runtime/tasks/main.yml` gateway include | **Remove after stop/disable and before host artifact removal** | Keep the adjacent `assistant_egress` include. The normal call site is not restored by rollback because it invokes an enable/start task. |
| Gateway deployment task | `roles/ai_client_runtime/tasks/provider_gateway.yml` | **Historical source**; retain unwired initially | Must not remain reachable from normal setup or rollback. It unconditionally enables/starts the service and therefore is not a valid disabled-state rollback implementation. |
| Gateway defaults | `roles/ai_client_runtime/defaults/main.yml::ai_ops_provider_gateway` | **Preserve during retirement** | Needed to identify fixed paths and evidence ownership. Reclassify/remove only after validators no longer depend on it. Do not alter `ai_ops_assistant_egress`. |
| Gateway handler | `roles/ai_client_runtime/handlers/main.yml::Restart provider gateway` | **Disable/unwire** with deployment call site; preserve as historical source initially | No retirement or rollback path may notify it, flush it, or restart the gateway. |
| Gateway repository payload | `files/provider_gateway/{aiops_provider_gateway.py,gateway_policy.json,redaction.py}` | **Historical source** | Do not execute through normal deployment after retirement. A dedicated approved rollback may copy reviewed payload bytes but must leave the service disabled/stopped; no code reuse by orchestrator. |
| Unit template | `templates/provider_gateway/aiops-provider-gateway.service.j2` | **Historical source** | Do not install through normal setup. A dedicated rollback may render it only while separately enforcing disabled/stopped/no-listener state. |
| Historical deployment validator | `playbook_validate_phase07_provider_gateway_deployment.yml` | **Historical source** | Mark/interpret as pre-retirement evidence; do not run as final architecture acceptance because it expects active/enabled state. |
| Historical egress validator | `playbook_validate_phase07_provider_gateway_egress.yml` | **Preserve shared-control validation** | Its `assistant` policy checks remain relevant; it must not be treated as gateway deployment authorization. |
| Gateway unit on host | `/etc/systemd/system/aiops-provider-gateway.service` | **Disable, then remove** | Capture metadata-only pre-state; stop/disable first; daemon reload; rollback may reinstall but must leave disabled/stopped. |
| Gateway active root on host | `/opt/openstack-ai-ops/provider-gateway` including venv/payload | **Remove after stop/listener proof** | Never remove before preservation check. Rollback may restore root-owned payload without provider traffic. |
| Gateway process/listener | `aiops-provider-gateway`, `127.0.0.1:8765` | **Disable/remove** | Final state requires no process and no listener on any address at port `8765`. |
| Gateway policy | deployed `gateway_policy.json` under active root | **Remove with active root**; repository copy historical | Must not be transferred into orchestrator configuration. |
| Gateway identity | `aiops-provider` user/group | **Preserve when present; otherwise verified absent pre-existing** | Account deletion would break the concrete ownership contract when evidence exists. On the approved rebuilt/reset host it is absent pre-existing; do not synthesize or recycle its UID/name. |
| State directory | `/var/lib/aiops-provider-gateway` | **Preserve when present; otherwise verified absent pre-existing** | When present, it remains non-symlink, `aiops-provider:aiops-provider`, mode `0700`; no generic cleanup. When absent under the approved disposition, do not create it. |
| Ledger | `/var/lib/aiops-provider-gateway/gateway-evidence.jsonl` | **Preserve byte-for-byte when present; otherwise verified absent pre-existing** | When present, it is non-symlink, same owner/group, mode `0600`; no open/read/hash/migration/rotation/truncation/deletion. When absent under the approved disposition, do not recreate it. |
| Gateway tests | `tests/ai_ops/test_provider_gateway.py`, `test_provider_redaction.py` | **Historical source tests** | Retain while repository source remains. They are not successor-path acceptance and should not be expanded for orchestrator behavior. |
| Shared assistant firewall roles/templates | `roles/assistant_egress`, `roles/assistant_egress_validation` | **Preserve active control** | Revalidate before and after retirement. Never remove owner-rule markers as gateway cleanup. |
| Orchestrator ledger protection | `playbook_validate_phase11_orchestrator_deployment.yml` protected-path entry | **Preserve** | The historical ledger remains forbidden to the orchestrator after gateway retirement. |
| Orchestrator/MCP runtime | dedicated roles, units, bridge, validators, runbooks | **Preserve and revalidate** | No new gateway import, base URL, proxy, listener, or fallback may appear. |
| Phase 12 remote unit | `aiops-orchestrator-remote.service` | **Preserve installed, static, inactive** | Validate passively; never start it during retirement. |
| Phase 12 bridge units | `aiops-assistant-mcp-bridge.socket` and `.service` | **Preserve installed, static, inactive** | Passive retirement validation must not activate them. Fake bridge activation requires separate explicit local-validation approval. |
| Phase 12 ephemeral artifacts | `/run/aiops-orchestrator/remote-approval`, `/run/openstack-ai-ops/assistant-mcp-bridge.sock` | **Preserve absent** | Any presence is stale state and blocks retirement. |
| Phase 12 temporary egress markers | `AI-OPS orchestrator remote egress exception` in IPv4/IPv6 UFW files | **Preserve absent** | Do not create them; permanent orchestrator egress remains `disabled`. |
| Phase 12 normal profile | `ai_ops_orchestrator.profile == 'validate-local-fake'` | **Preserve** | Retirement must not switch profile or invoke remote acceptance. |
| Historical ADSs/decisions/evidence | `docs/ai-ops/implementation-plan/ads/07-*`, `docs/ai-ops/runtime/*provider*` | **Preserve as historical** | Add retirement status where ambiguity remains; never rewrite history as if the gateway did not exist. |
| Retirement evidence | proposed dated Phase 13 evidence document | **Create after approved operation** | Metadata-only outcomes and retention categories; no raw ledger or command output. |
| Provider-specific firewall rules | no dedicated repository-owned `aiops-provider` rule set found in scoped search | **Open confirmation** | Chunk 0 must inspect approved metadata-only live rules. Do not remove any firewall rule merely by name or assumption. |

#### Assumptions

- The Phase 12 acceptance evidence and runbooks remain approved at implementation time.
- Chunk 0 read-only discovery found the service, unit/root, ledger/state directory, identity, process, and listener absent on `assistant01`; the operator has confirmed host rebuild/reset and no recoverable ledger. The approved disposition is `verified_absent_preexisting`.
- If the ledger/state directory/identity unexpectedly appear in a later approved operation, stop and apply the existing-evidence preservation contract rather than treating the prior absence disposition as authority to alter them.
- Retaining the `aiops-provider` identity is acceptable when it exists because preserving named ownership is an explicit plan requirement. If account retirement is required, stop and create a separate evidence-custody ADS.
- Repository gateway source can remain as clearly historical, unwired rollback material. If policy requires deleting source/tests, that is a later approved cleanup after retirement evidence is accepted.

#### Open confirmations for Chunk 0

- Confirm `main` contains the Phase 12 merge and the worktree has no unrelated changes.
- Confirm the exact accepted approval mechanism for destructive Phase 13 state changes.
- Confirm current service enablement/activity, unit load state, PID/process category, and all listeners on port `8765` without exposing environment or payload data.
- Reconfirm only fixed-path metadata without opening the ledger; absence is accepted only under the recorded `verified_absent_preexisting` disposition, while unexpected presence switches to the existing-evidence preservation contract.
- Confirm no runtime override, systemd unit, inventory, profile, environment, or local configuration selects `127.0.0.1:8765` or a custom provider. Do not inspect authentication/runtime-home contents.
- Confirm the Phase 12 remote and bridge units are installed/static/inactive, approval and bridge-socket paths are absent, temporary remote-egress markers are absent, permanent orchestrator egress is `disabled`, and the normal profile is `validate-local-fake`.
- Confirm whether any live firewall rules are owned solely by `aiops-provider`; preserve unknown/shared rules and stop for review.
- Confirm which active host artifacts are approved for deletion and the exact dedicated rollback task shape that restores files/unit without invoking the historical enable/start task.

### III. Required Technical Dependencies and Imports

| Dependency | Use | Constraint |
|---|---|---|
| Existing Ansible runtime inventory | Bound operation to `assistant01` | No broad host pattern or dynamic target. |
| `ansible.builtin.assert` | Fail-closed target, approval, and path contracts | Assertions precede every mutation. |
| `ansible.builtin.stat` | Metadata-only preservation and artifact checks | Do not use checksum/content options for the ledger. |
| `ansible.builtin.systemd_service` | Stop and disable the fixed gateway unit | Never start/restart it during retirement. |
| `ansible.builtin.file` | Remove only approved unit/root artifacts | Explicitly exclude state directory and ledger. |
| `ansible.builtin.command` | Fixed `systemctl`, `ss`, and process metadata probes | Fixed `argv`, `changed_when: false`, bounded/no-log output. No shell. |
| Existing `assistant_egress` validators | Preserve direct-`assistant` denial | No rollback/removal of shared UFW markers. |
| Existing MCP/orchestrator/Phase 12 validators | Prove successor boundaries and no fallback | Local/fake/preflight checks only; no provider request. |
| Historical gateway source/template | Inputs to a dedicated disabled-state rollback path | Repository-only; never invoke the historical enable/start task, import into orchestrator, or restore the normal deployment call site. |
| Runtime documentation | Evidence retention and operator status | Preserve history; add sanitized retirement state only. |

No new Python dependency, provider SDK, HTTP client, proxy, credential, schema, database, migration tool, listener, firewall manager, or generic cleanup script is permitted.

### IV. Step-by-Step Procedure / Execution Flow

1. **Repository gate.** Confirm Phase 12 acceptance references, branch/worktree scope, inventory target, and the final reviewed Phase 13 ADS. Stop on unrelated changes or unaccepted prerequisites.
2. **Dependency inventory.** Search repository-owned Ansible, inventory, scripts, tests, units, and runtime documentation for gateway service names, identity, root, ledger path, custom-provider selection, and port `8765`. Classify each match against the inventory table.
3. **Read-only host discovery.** Collect only closed categories for unit installed/enabled/active state, process presence, port-8765 listener presence, root presence, identity state, and preservation-target metadata. Do not read service environment, credential homes, policy contents, or ledger contents unless an existing validator specifically permits safe metadata.
4. **Passive successor proof.** Run the Phase 12 no-provider preflight with its accepted runtime variables plus local/fake-only orchestrator and MCP checks. Assert the remote and bridge units are installed/static/inactive, approval/socket artifacts and temporary remote-egress markers are absent, permanent orchestrator egress is `disabled`, and the normal profile is `validate-local-fake`. Do not run fake bridge activation unless separately approved; never run remote acceptance.
5. **Shared-control preflight.** Validate permanent `assistant` egress denial and reviewed management access before gateway mutation. Unknown firewall ownership or an absent denial is a hard stop.
6. **Approval gate.** Validate fresh Phase 13 approval for the exact stop/disable, deployment de-wiring, and artifact-removal scope. Approval must not be inferred from Phase 12 or a previous gateway operation.
7. **Preservation gate.** Re-stat identity, state directory, and ledger. When present, assert fixed path, non-symlink type, owner/group, mode, and approved bounded-size category. When absent, accept only the approved `verified_absent_preexisting` disposition. Record no raw bytes or parsed lines and never create a replacement.
8. **Stop and disable.** Stop `aiops-provider-gateway`, disable it, and flush systemd state. Do not notify the historical restart handler.
9. **Closed-state proof.** Assert inactive/not-running state, no gateway process, and no IPv4/IPv6 listener on port `8765`. If stop fails, retain artifacts and report a closed failure.
10. **Prevent recreation before deletion.** Remove or fail-close the unconditional provider-gateway include from `ai_client_runtime/tasks/main.yml` while preserving the independent `assistant_egress` include. Keep the historical enable/start task unreachable from normal setup and rollback.
11. **Recreation validation.** Run syntax/lint and scoped call-site checks. Prove ordinary AI client setup cannot create, enable, start, restart, or notify the gateway before deleting host artifacts.
12. **Approved active-artifact removal.** Only after recreation validation passes, remove `/etc/systemd/system/aiops-provider-gateway.service` and `/opt/openstack-ai-ops/provider-gateway` when explicitly approved; their pre-existing absence converges as a no-op. Preserve existing `/var/lib/aiops-provider-gateway`, the ledger, and `aiops-provider`, or preserve their approved absence without synthetic replacement; always preserve shared egress roles/rules, MCP, orchestrator, credentials, runtime homes, logs, and unrelated units.
13. **Systemd convergence.** Run daemon reload, clear only an approved failed-state marker if necessary, and prove the unit is absent/not-found and cannot be activated from the retired deployment.
14. **Preservation recheck.** Re-stat the ledger directory/file and identity; compare only approved metadata categories with pre-state when they exist, or verify the recorded absence disposition remains true. Any unexpected ownership/mode/path/type drift or appearance is a retirement failure and must not be repaired ad hoc.
15. **Final runtime validation.** Run the Phase 13 retired-state validator, passive Phase 12 no-provider preflight, assistant egress, MCP lifecycle, and orchestrator deployment checks. Reassert the exact Phase 12 disabled successor baseline. No bridge activation, remote request, or authentication action is allowed by default.
16. **Idempotency run.** Repeat the bounded retirement/validator path with fresh operation approval if required by the accepted contract. It must report no active-artifact change and preserve evidence metadata.
17. **Dedicated rollback proof.** Validate offline or in an explicitly approved rollback exercise that reviewed payload/unit artifacts can be restored without restoring the normal deployment include and while leaving the unit disabled/stopped with no listener. Never invoke `provider_gateway.yml` as the rollback operation.
18. **Documentation and evidence.** Mark operational gateway instructions historical/retired, update the provider evidence and orchestrator remote-operations runbooks, preserve prior evidence unchanged, and create a dated metadata-only retirement outcome with rollback readiness.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
|---|---|---|---|
| Prerequisite | Phase 12 acceptance cannot be confirmed | Do not inspect or alter gateway runtime | `ERR_GATEWAY_RETIREMENT_PREREQUISITE` (proposed) |
| Discovery | Repository/runtime dependency on gateway exists | Stop; inventory the coupling; do not disable service | `ERR_GATEWAY_RETIREMENT_DEPENDENCY` (proposed) |
| Approval | Missing, stale, reused, malformed, or overbroad approval | Stop before service or filesystem mutation | `ERR_GATEWAY_RETIREMENT_APPROVAL` (proposed) |
| Preservation | Ledger/state path missing without approved disposition, unexpectedly present after approved absence, symlinked, wrong owner/mode, or outside fixed boundary | Preserve current state; do not open, repair, recreate, or synthesize the ledger; escalate | `ERR_GATEWAY_EVIDENCE_PRESERVATION` (proposed) |
| Shared egress | `assistant` denial or management allowance fails preflight | Stop before gateway mutation | Existing assistant-egress error category or `ERR_GATEWAY_RETIREMENT_SHARED_CONTROL` (proposed) |
| Stop/disable | Unit cannot be stopped or disabled | Do not remove unit/root; retain bounded state metadata | `ERR_GATEWAY_RETIREMENT_DISABLE` (proposed) |
| Closed-state proof | Process or listener remains | Do not remove payload; isolate through reviewed systemd action only; no generic kill | `ERR_GATEWAY_RETIREMENT_LISTENER` (proposed) |
| Removal | Approved unit/root removal fails partially | Keep service disabled; do not touch ledger/state; report exact artifact category | `ERR_GATEWAY_RETIREMENT_ARTIFACT` (proposed) |
| Preservation recheck | Ledger metadata changes after removal | Stop; do not auto-chown/chmod/read/restore | `ERR_GATEWAY_EVIDENCE_DRIFT` (proposed) |
| Recreation check | Normal setup still includes or can notify gateway deployment | Keep gateway disabled; block host artifact removal until the call path is eliminated | `ERR_GATEWAY_RETIREMENT_RECREATION` (proposed) |
| Phase 12 baseline | Remote/bridge unit state drifts, an ephemeral artifact/marker exists, egress is not disabled, or profile is not fake-only | Stop retirement; do not activate bridge or remote service; restore only through existing Phase 12 cleanup/preflight contracts | `ERR_GATEWAY_RETIREMENT_PHASE12_BASELINE` (proposed) |
| Successor validation | MCP/orchestrator/no-provider validation fails | Keep gateway retired/disabled; treat as successor blocker, never gateway-fallback authorization | `ERR_GATEWAY_RETIREMENT_SUCCESSOR` (proposed) |
| Idempotency | Second execution changes preserved or unrelated state | Stop and retain diff/result categories | `ERR_GATEWAY_RETIREMENT_NOT_IDEMPOTENT` (proposed) |
| Rollback | Rollback would start gateway or permit traffic | Reject rollback shape; restore artifacts only if they remain disabled/stopped | `ERR_GATEWAY_RETIREMENT_ROLLBACK` (proposed) |
| Documentation | Historical source appears current or evidence is rewritten | Block phase completion; correct status without deleting history | `ERR_GATEWAY_RETIREMENT_DOCUMENTATION` (proposed) |

### VI. Security, Integrity, Idempotency, and Cleanup

- **Security:** Bind all operations to `assistant01`, fixed service/path constants, and explicit approval. Do not introduce shell commands, arbitrary service/path variables, custom providers, proxies, credentials, provider endpoints, or network requests.
- **Ledger confidentiality:** Never use `cat`, `less`, `tail`, generic file reads, checksum collection, diff, backup tooling, or content parsers against the ledger during retirement. The existing metadata parser is an operator evidence-review procedure, not a retirement prerequisite.
- **Ledger integrity:** When evidence exists, preserve bytes, path, type, ownership, and modes. Under `verified_absent_preexisting`, preserve the absence and do not create a synthetic ledger or state directory. A filesystem checksum could itself require reading all bytes and is therefore not part of this ADS unless separately approved. Use metadata categories only.
- **Identity integrity:** Preserve locked, nologin `aiops-provider` while it owns the ledger. Under `verified_absent_preexisting`, do not create or recycle its UID/name for another service.
- **Network security:** Absence of gateway traffic is proved by stopped/disabled/absent service and no listener. Independent `assistant` denial remains materialized. Unknown `aiops-provider` firewall rules are preserved pending ownership confirmation rather than removed speculatively.
- **Evidence separation:** Historical gateway schema 1/schema 2 records remain distinct from orchestrator evidence. Retirement evidence records only lifecycle categories and must not copy parsed gateway events.
- **Idempotency:** Missing unit/root and inactive/disabled/not-found service states are accepted terminal states. Repeated execution must not recreate directories, users, units, files, listeners, or mutate preservation targets.
- **Cleanup:** Remove only approved active gateway unit/root artifacts and any Phase 13 ephemeral approval artifact according to its accepted mechanism. Do not clean state, ledger, identity, credentials, Codex homes, logs, source, tests, or unrelated firewall/systemd state.
- **Rescue behavior:** Any failure after service stop leaves it disabled/stopped. Rescue re-runs closed-state and preservation metadata checks; it does not restart the service.
- **Rollback:** Use a dedicated rollback task that copies only reviewed root-owned payload/unit artifacts, runs daemon reload, explicitly disables/stops the unit, and proves no listener. Never call the historical `provider_gateway.yml`, restore its normal include, or notify its restart handler because those paths enable/start the service. Rollback never restores profile selection, egress, authentication, or provider traffic.

### VII. Validation Strategy

Validation is chunk-aware. ADS creation itself performs static documentation validation only; runtime commands below belong to separately approved implementation chunks.

#### Static documentation and repository checks

```bash
rtk git diff --check
rtk grep -nE '^### (I|II|III|IV|V|VI|VII|VIII|IX|X)\.' docs/ai-ops/implementation-plan/ads/13-00-provider-gateway-retirement-ads.md
rtk grep -RniE 'provider_gateway.yml|aiops-provider-gateway|127\.0\.0\.1:8765' ansible/ai_ops_runtime/roles/ai_client_runtime ansible/ai_ops_runtime/playbook_validate_phase13_provider_gateway_retirement.yml
rtk git diff -- docs/ai-ops/implementation-plan/ads/13-00-provider-gateway-retirement-ads.md
```

#### Proposed Ansible syntax and lint

```bash
rtk ansible-playbook --syntax-check -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_retire_phase13_provider_gateway.yml
rtk ansible-playbook --syntax-check -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_validate_phase13_provider_gateway_retirement.yml
rtk ansible-playbook --syntax-check -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_setup_ai_client_runtime.yml
rtk ansible-lint ansible/ai_ops_runtime/playbook_retire_phase13_provider_gateway.yml ansible/ai_ops_runtime/playbook_validate_phase13_provider_gateway_retirement.yml ansible/ai_ops_runtime/roles/ai_client_runtime/tasks/main.yml
```

Exact proposed filenames must be reconfirmed in Chunk 0 before creation.

#### Required targeted behavior checks

- **Preflight:** Phase 12 evidence accepted; no gateway dependency/fallback; existing-evidence preservation metadata valid or approved `verified_absent_preexisting` disposition confirmed; assistant egress denial passes.
- **Exact Phase 12 baseline:** remote and bridge units installed/static/inactive; approval and Unix-socket artifacts absent; temporary IPv4/IPv6 remote-egress markers absent; permanent orchestrator egress `disabled`; normal profile `validate-local-fake`.
- **Passive-by-default:** use `playbook_validate_phase12_remote_preflight.yml` with its accepted runtime variables. Do not run `playbook_validate_phase12_assistant_bridge_activation.yml` without separate explicit local-validation approval, and never run `playbook_operate_orchestrator_remote_acceptance.yml` during retirement.
- **Disablement:** service inactive and disabled; no process; no listener on TCP `8765` on IPv4 or IPv6.
- **Recreation:** before host removal, ordinary AI client setup syntax passes and contains no reachable gateway include/start/restart/notify path.
- **Removal:** unit not found after daemon reload; active root absent; existing state directory, ledger, and identity preserved, or approved `verified_absent_preexisting` remains true without synthetic replacement.
- **Successor:** existing MCP lifecycle, orchestrator deployment, listener baseline, and Phase 12 no-provider preflight pass without bridge activation or remote traffic.
- **Shared controls:** assistant egress preflight/materialization/acceptance checks pass using only already approved non-provider synthetic validation conditions; no provider endpoint is contacted.
- **Idempotency:** a second retirement/validation run reports no active-artifact changes and unchanged approved preservation metadata categories or approved absence disposition.
- **Diff review:** every chunk ends with `rtk git status --short`, scoped `rtk git diff -- <changed-files>`, and `rtk git diff --check`.

#### Historical source checks

If source/tests remain as designed, their existing syntax/tests may be run locally only to prove retained historical source is intact; they are not final architecture acceptance:

```bash
rtk python3 -m py_compile ansible/ai_ops_runtime/roles/ai_client_runtime/files/provider_gateway/aiops_provider_gateway.py
rtk python3 -m json.tool ansible/ai_ops_runtime/roles/ai_client_runtime/files/provider_gateway/gateway_policy.json
rtk python3 -m unittest tests.ai_ops.test_provider_gateway tests.ai_ops.test_provider_redaction
```

Per repository discipline, Python execution must use a temporary virtual environment when implementation reaches these checks.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full retirement in one pass. Runtime-mutating chunks require explicit operator approval and must stop independently.

#### Chunk 0: Discovery and Integration Confirmation
- **Goal:** Confirm current repository/live gateway state, approved retirement scope, evidence metadata, successor separation, shared controls, and rollback requirements without edits or state changes.
- **Files to read:** this ADS; Phase 13 plan; Phase 12 evidence/runbook; gateway role/default/task/template; Phase 07 gateway validators; provider evidence runbook; orchestrator/MCP/assistant-egress validators.
- **Commands:** bounded repository searches; Git state; approved read-only `systemctl`, `ss`, account, file-stat, UFW, MCP, and orchestrator preflight probes. Do not open the ledger or runtime-home/authentication data.
- **Evidence to confirm:** exact host artifacts; no fallback/dependency; existing ledger/state owner/mode/type and identity retention, or the approved `verified_absent_preexisting` disposition; assistant denial; Phase 12 remote/bridge units installed-static-inactive; approval/socket artifacts and temporary remote-egress markers absent; permanent orchestrator egress disabled; fake-only profile selected; no ambiguous firewall ownership; accepted approval mechanism.
- **Stop condition:** Produce a sanitized confirmed inventory and stop with no edits. Any coupling, evidence drift, missing acceptance, missing absence disposition, or ambiguous removal scope blocks Chunk 1.

#### Chunk 1: Default-False Retirement Contract Stub
- **Goal:** Add a compile/syntax-safe operation boundary that validates target and explicit approval but performs no service or filesystem mutation.
- **Files to change:** proposed `ansible/ai_ops_runtime/playbook_retire_phase13_provider_gateway.yml` only.
- **Symbols to add/change:** conceptual fixed target/path variables, default-false approval fields, exact-key assertions, and a deliberate pre-mutation stop/debug category.
- **Implementation shape:** stub-first Ansible playbook; all external state-changing tasks are absent. A missing approval fails explicitly; a valid approval reaches a clear `retirement_contract_validated` no-op result, never success for completed retirement.
- **Validation:** Ansible syntax/lint; default invocation fails closed; approved dry contract changes nothing; scoped diff review.
- **Stop condition:** The playbook cannot stop/start/remove anything and cannot target outside `assistant01`.

#### Chunk 2: Preservation and Dependency Preflight Slice
- **Goal:** Extend the operation boundary with read-only exact Phase 12 successor-baseline, shared-control, identity, state-directory, ledger-metadata, gateway service/process/listener, and firewall ownership gates.
- **Files to change:** Phase 13 retirement playbook and, only if needed, one focused read-only task file.
- **Symbols to add/change:** conceptual preflight result categories and `ERR_GATEWAY_RETIREMENT_*` assertions.
- **Implementation shape:** fixed `argv`, `stat` without checksum/content, `changed_when: false`, `no_log` for raw command output, allowlisted boolean/category facts only. Existing targets must meet metadata contracts; absent targets may proceed only with the approved `verified_absent_preexisting` disposition. End before mutation.
- **Validation:** syntax/lint; local read-only preflight; proof no ledger read module/lookup or synthetic evidence creation is present; assistant/MCP/orchestrator validators remain unchanged.
- **Stop condition:** All prerequisites are proven and the play still makes zero host changes; otherwise stop.

#### Chunk 3: Approved Stop-and-Disable Slice
- **Goal:** Under fresh explicit approval, stop and disable only `aiops-provider-gateway`, then prove no process/listener while preserving all artifacts and evidence.
- **Files to change:** Phase 13 retirement playbook and one proposed `roles/ai_client_runtime/tasks/provider_gateway_retirement.yml` or a dedicated retirement-role task file, as confirmed in Chunk 0.
- **Symbols to add/change:** conceptual stop/disable block, closed-state assertions, and rescue checks. Do not reuse the restart handler.
- **Implementation shape:** preflight -> stop/disable when the unit exists -> prove inactive/disabled-or-not-found/process absent/port absent -> preservation or approved-absence re-stat. Rescue leaves a present service stopped and performs no removal.
- **Validation:** syntax/lint; approved bounded run; service/listener/process checks; existing-ledger metadata comparison or approved-absence verification; second disabled-state run.
- **Stop condition:** Service is disabled/stopped or not-found, listener/process absent, all non-removal host state remains unchanged, and preservation metadata or approved absence disposition is unchanged. Do not continue automatically.

#### Chunk 4: Prevent Normal Deployment Recreation
- **Goal:** After Chunk 3 leaves the gateway disabled/stopped, remove or fail-close the normal `ai_client_runtime` gateway call site before any host artifact is deleted, without changing independent assistant egress enforcement.
- **Files to change:** `ansible/ai_ops_runtime/roles/ai_client_runtime/tasks/main.yml`; optionally `handlers/main.yml` only if Chunk 0 confirms no remaining notification reference.
- **Symbols to add/change:** remove `Deploy fail-closed provider gateway service` include; remove or make unreachable `Restart provider gateway`; preserve `Enforce persistent assistant egress policy` unchanged.
- **Implementation shape:** smallest exact deletion; historical task/source/template/defaults remain as unwired history and possible byte sources for a dedicated rollback, but neither normal setup nor rollback may call the enable/start task.
- **Validation:** setup playbook syntax/lint; scoped searches for reachable include/notify call sites; assistant egress validator; prove the disabled host state remains unchanged; diff review.
- **Stop condition:** Normal AI client setup cannot create, enable, start, restart, or notify the gateway and still enforces assistant egress. Stop before host artifact removal.

#### Chunk 5: Approved Active-Artifact Removal and Disabled Rollback Slice
- **Goal:** Remove only the fixed systemd unit and active gateway root after Chunk 4 proves recreation is blocked, preserving ledger/state/identity and a genuinely disabled rollback contract.
- **Files to change:** retirement playbook and its focused retirement task file; add a separate rollback task file only if Chunk 0 proves it is required and keeps the chunk reviewable.
- **Symbols to add/change:** conceptual exact-path removal, daemon-reload, unit-not-found, root-absent, preservation recheck, and dedicated disabled-restore tasks.
- **Implementation shape:** separate removal approval -> re-prove disabled/not-found and de-wired state -> remove unit/root idempotently -> daemon reload -> assert absent -> re-stat existing preservation targets or approved absence. Rollback may copy reviewed files/render the unit only if separately authorized, then must explicitly disable/stop and prove no listener; it never invokes `provider_gateway.yml` or restores the normal include.
- **Validation:** syntax/lint; approved host run; systemd/root absence; existing ledger/state/identity metadata or approved-absence verification; no listener; idempotent second run; offline or separately approved disabled-rollback proof.
- **Stop condition:** Approved active host artifacts are absent, existing evidence/identity remain valid or approved absence remains true, recreation remains blocked, and rollback can restore only disabled/stopped/no-listener artifacts.

#### Chunk 6: Retired-State Validator and Boundary Regression
- **Goal:** Add one read-only Phase 13 validator and compose existing local/fake-only boundary checks without provider traffic.
- **Files to change:** proposed `ansible/ai_ops_runtime/playbook_validate_phase13_provider_gateway_retirement.yml` only; modify a second file only if an existing validation entrypoint requires explicit inclusion.
- **Symbols to add/change:** retired unit/root/process/listener assertions; preserved ledger/state/identity metadata assertions; no-recreation/fallback categories; imports of existing assistant/MCP/orchestrator validation roles or playbooks where composition is safe.
- **Implementation shape:** read-only checks only. Do not reuse the Phase 07 active deployment assertions or activate Phase 12 units. Do not parse the ledger. Treat successor failure as a blocker, never rollback authorization.
- **Validation:** syntax/lint; retired-state validator; passive Phase 12 no-provider preflight; exact remote/bridge static-inactive, artifact/marker-absent, disabled-egress, fake-profile assertions; assistant egress, MCP lifecycle, orchestrator deployment, and listener baseline; no changed host state.
- **Stop condition:** Active architecture and host state agree: gateway absent/inactive, exact Phase 12 disabled baseline intact, evidence protected, shared controls passing, and no fallback.

#### Chunk 7: Historical Status and Retirement Evidence
- **Goal:** Make operator documentation unambiguous and retain a dated, sanitized retirement result after all runtime checks pass.
- **Files to change:** `docs/ai-ops/runtime/provider-gateway-metadata-evidence.md`, `docs/ai-ops/runtime/orchestrator-remote-operations.md`, and one proposed dated Phase 13 retirement evidence document; update an additional active-architecture index only if Chunk 0 identifies it as authoritative and split the work if needed to preserve small reviewable edits.
- **Symbols to add/change:** historical/retired status, preservation location/owner/mode categories, active architecture summary, validator outcomes, rollback readiness, and explicit no-traffic/no-raw-inspection statement.
- **Implementation shape:** preserve old evidence text and schema history; add status rather than rewriting past tense; retain metadata-only outcomes.
- **Validation:** Markdown heading/reference checks, `rtk git diff --check`, scoped diff review, and confirmation that no raw ledger/command/provider/authentication data entered Git.
- **Stop condition:** Documents distinguish historical gateway evidence from the active Codex SDK orchestrator and Phase 13 definition of done is evidence-backed.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline and post-edit-discipline if available.

Task:
Phase 13 Historical Provider Gateway Retirement from docs/ai-ops/implementation-plan/ads/13-00-provider-gateway-retirement-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files or change host state. Confirm repository and live inventory, Phase 12 acceptance, successor dependency absence, the exact static/inactive remote and bridge unit baseline, absent approval/socket artifacts and temporary remote-egress markers, disabled permanent orchestrator egress, fake-only profile, ledger/state/identity metadata without reading the ledger, assistant egress, firewall ownership, approval mechanism, and dedicated disabled rollback scope. Produce sanitized evidence and stop.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, pre-edit-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Execute Chunk 1 only from the Phase 13 Historical Provider Gateway Retirement ADS.

Do not continue to Chunk 2. Add only the default-false, no-mutation retirement contract stub. Run targeted Ansible syntax/lint validation, prove default-fail and no-op behavior, review git diff, and stop.
```

Runtime-mutating handoff for later use only after Chunks 0-2 and explicit approval:

```text
Use the chunked-implementation skill.
Execute the currently approved Phase 13 runtime chunk only.
Do not continue to the next chunk.
Never read or mutate the provider-gateway ledger, start the gateway, contact a provider, weaken assistant egress, or reuse prior approval. Run preservation, closed-state, idempotency, diff, and risk checks and stop.
```

### X. Conclusion and Next Steps

The repository supports a narrow retirement boundary: the gateway deployment is isolated behind one unconditional `ai_client_runtime` include, while assistant egress is an independent following role and the orchestrator treats the old ledger as a protected path. Historical source, tests, ADSs, and evidence can remain in Git without remaining active, provided normal deployment is de-wired before host deletion, rollback never invokes the historical enable/start task, and documentation marks the gateway historical.

Chunk 0 has confirmed the fresh-host absence and the operator has selected `verified_absent_preexisting`; the blocker-remediation documentation slice is complete. No destructive action is authorized by this ADS alone. After this documentation revision is accepted, service disablement or pre-existing service absence handling, deployment de-wiring, host artifact removal no-ops or removal, boundary validation, and documentation updates proceed as separate validated chunks, with existing ledger/state/identity preserved when present, approved absence never synthesized, and Phase 12 successor artifacts and direct-`assistant` denial preserved throughout.
