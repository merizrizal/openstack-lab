# 13. Historical Provider Gateway Retirement

## 13.1 Goal

Retire the superseded custom-provider gateway from active deployment only after the Codex SDK orchestrator path is accepted, while preserving historical evidence and all still-required assistant egress controls.

Target outcome:

```text
accepted orchestrator path
  -> reviewed gateway retirement ADS
  -> preserve existing ledger and evidence, or record verified pre-existing absence
  -> disable and stop the active gateway
  -> de-wire normal deployment recreation
  -> remove approved active gateway artifacts safely
  -> revalidate the exact Phase 12 disabled successor baseline and shared boundaries
```

## 13.2 Estimate

Total estimate:

```text
1-2 engineer-days
6-12 focused hours
```

## 13.3 Scope

Included:

* Retirement ADS, inventory, dependency analysis, and rollback plan.
* Preservation of historical provider-gateway ledgers and evidence documents when present, or an explicit `verified_absent_preexisting` disposition when a rebuilt/reset host has no recoverable ledger.
* Controlled disablement/removal of gateway service, deployment artifacts, and obsolete policy where approved.
* Revalidation of `assistant`, MCP, orchestrator, identity, listener, and egress boundaries.
* Preservation of the Phase 12 successor baseline: static/inactive remote and bridge units, absent approval/socket artifacts, absent temporary remote-egress markers, permanent orchestrator egress disabled, and the normal `validate-local-fake` profile.
* Documentation updates distinguishing historical source from active architecture, including the current orchestrator operations runbook.

Excluded:

* Ledger deletion, truncation, migration, relabelling, or raw inspection.
* Removal before Phase 12 acceptance.
* Weakening direct-`assistant` egress denial.
* Reuse of gateway identity, policy, or schema without separate approval.
* Rewriting historical evidence as if the gateway never existed.

## 13.4 Assumptions

- [x] Phase 12 remote acceptance and operational runbooks are approved.
- [x] The orchestrator has no runtime dependency on the provider gateway.
- [x] Historical evidence retention requirements are known, including an explicit operator disposition if the preservation targets are already absent.
- [ ] Rollback can restore the last validated disabled gateway state without provider traffic.

## 13.5 Ordered Tasks

### Step 1 - Create the Retirement ADS and Inventory

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Inventory gateway service, identity, policy, source, tests, playbooks, firewall dependencies, state directory, ledger, and documentation.
- [x] Inventory the accepted Phase 12 successor state: `aiops-orchestrator-remote.service`, `aiops-assistant-mcp-bridge.socket`, `aiops-assistant-mcp-bridge.service`, `/run/aiops-orchestrator/remote-approval`, `/run/openstack-ai-ops/assistant-mcp-bridge.sock`, temporary remote-egress markers, permanent orchestrator egress mode, and active profile.
- [x] Classify each artifact as preserve, disable, remove, or historical source.
- [x] Identify shared controls that must remain, especially `assistant` egress denial and the provider-ledger protected-path assertion.
- [x] Define ordering, rollback, and validation for each removal.
- [x] Require explicit approval for ledger preservation or service-state changes.
- [x] Define a dedicated rollback path that restores files and the unit disabled/stopped; do not use the historical deployment task that enables and starts the gateway.

Done when:

- [x] Every gateway artifact has an evidence-based disposition and rollback path, and every Phase 12 successor-state artifact has an explicit preservation assertion.

### Step 2 - Preserve Historical Evidence

Estimate:

```text
0.1-0.25 engineer-days
0.5-1.5 hours
```

Tasks:

- [x] When the state directory, ledger, and identity exist, preserve schema 1/schema 2 ledger bytes and ownership without reading raw lines. Not applicable to the approved rebuilt-host absence branch; no preservation target appeared.
- [x] When an operator confirms host rebuild/reset and no recoverable ledger, record `verified_absent_preexisting`; do not recreate a ledger, state directory, or identity and do not claim successful preservation.
- [x] Preserve dated evidence, ADSs, handoffs, and superseded status markers.
- [x] Record retention location, ownership, mode, and integrity category only for preserved existing evidence; record only the approved absence disposition for absent pre-existing evidence.
- [x] Prohibit migration into the orchestrator evidence schema.

Done when:

- [x] Historical evidence is retained separately and cannot be mistaken for active orchestrator evidence.

### Step 3 - Disable and Remove Approved Active Components

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Disable and stop the gateway before changing deployment wiring or removing active artifacts. The approved operation converged as a no-op because the unit was already absent.
- [x] Confirm no listener or process remains.
- [x] Remove or fail-close the normal `ai_client_runtime` gateway deployment call site while preserving its independent `assistant_egress` call site.
- [x] Prove ordinary setup cannot recreate, enable, start, or restart the gateway.
- [x] Only then remove active host artifacts authorized by the retirement ADS. The approved active artifacts were already absent and remained absent.
- [x] Preserve shared runtime, MCP, credential, audit, and egress controls.
- [ ] Keep historical deployment source unwired; use a separate approved rollback task that can restore artifacts without enabling, starting, or opening a listener.
- [ ] Make repeated retirement execution safe and idempotent.

Done when:

- [ ] The gateway cannot receive or send traffic, normal setup cannot recreate it, approved removals converge safely, and rollback can restore only disabled/stopped/no-listener artifacts.

### Step 4 - Revalidate and Document Final Architecture

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Run the passive Phase 12 no-provider preflight and re-run `assistant` egress, orchestrator deployment, MCP lifecycle, process, listener, and evidence checks.
- [x] Assert `aiops-orchestrator-remote.service`, `aiops-assistant-mcp-bridge.socket`, and `aiops-assistant-mcp-bridge.service` remain installed, static, and inactive.
- [x] Assert `/run/aiops-orchestrator/remote-approval`, `/run/openstack-ai-ops/assistant-mcp-bridge.sock`, and temporary IPv4/IPv6 remote-egress markers are absent.
- [x] Assert permanent orchestrator egress remains `disabled` and the normal profile remains `validate-local-fake`.
- [x] Treat fake bridge activation as a separate explicitly approved local validation; do not invoke it as routine retirement validation and never invoke remote acceptance.
- [x] Verify the orchestrator cannot fall back to the gateway.
- [x] Update architecture and operator documents, including `docs/ai-ops/runtime/orchestrator-remote-operations.md` and `docs/ai-ops/runtime/provider-gateway-metadata-evidence.md`, to show the active Codex SDK path and historical gateway status.
- [x] Record sanitized retirement outcomes and rollback readiness.

Done when:

- [ ] Active architecture documentation and deployed state agree, the exact Phase 12 disabled successor baseline passes, and historical evidence remains preserved.

## 13.6 Phase Definition of Done

This phase is done when:

- [x] The retirement ADS and inventory are approved.
- [x] Historical ledgers and evidence are preserved without raw inspection when present; otherwise the approved `verified_absent_preexisting` disposition is recorded without synthetic replacement.
- [x] Approved gateway components are disabled or removed safely.
- [x] `assistant` egress denial and orchestrator/MCP boundaries still pass.
- [x] The exact Phase 12 disabled successor baseline remains intact.
- [x] Normal deployment cannot recreate the gateway.
- [ ] Any approved rollback restores only a disabled/stopped, no-listener artifact set.
- [x] No fallback to the old gateway exists.

## 13.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Retirement destroys historical evidence or fabricates continuity on a rebuilt host | Preserve existing evidence first; when the operator confirms it is already absent, record `verified_absent_preexisting` and prohibit recreation, raw inspection, deletion, truncation, or migration. |
| Shared egress controls are removed with the gateway | Inventory ownership and test `assistant` denial before and after every change. |
| New orchestrator silently depends on gateway artifacts | Prove dependency absence before retirement and stop if any coupling exists. |
| Normal setup recreates the gateway after host removal | De-wire and validate the normal deployment path before deleting active host artifacts. |
| Historical rollback task starts the gateway | Use a dedicated rollback path that restores only disabled/stopped artifacts and proves no listener. |
| Retirement validation activates Phase 12 remote capability | Use passive no-provider preflight by default; require separate approval for fake bridge activation and never run remote acceptance. |
| Historical documents mislead future maintainers | Mark them superseded while retaining their evidence and rationale. |
