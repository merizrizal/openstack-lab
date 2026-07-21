# 13. Historical Provider Gateway Retirement

## 13.1 Goal

Retire the superseded custom-provider gateway from active deployment only after the Codex SDK orchestrator path is accepted, while preserving historical evidence and all still-required assistant egress controls.

Target outcome:

```text
accepted orchestrator path
  -> reviewed gateway retirement ADS
  -> preserve ledger and evidence
  -> disable/remove active gateway deployment safely
  -> revalidate assistant, MCP, orchestrator, and egress boundaries
```

## 13.2 Estimate

Total estimate:

```text
0.5-1 engineer-days
3-6 focused hours
```

## 13.3 Scope

Included:

* Retirement ADS, inventory, dependency analysis, and rollback plan.
* Preservation of historical provider-gateway ledgers and evidence documents.
* Controlled disablement/removal of gateway service, deployment artifacts, and obsolete policy where approved.
* Revalidation of `assistant`, MCP, orchestrator, identity, listener, and egress boundaries.
* Documentation updates distinguishing historical source from active architecture.

Excluded:

* Ledger deletion, truncation, migration, relabelling, or raw inspection.
* Removal before Phase 12 acceptance.
* Weakening direct-`assistant` egress denial.
* Reuse of gateway identity, policy, or schema without separate approval.
* Rewriting historical evidence as if the gateway never existed.

## 13.4 Assumptions

- [ ] Phase 12 remote acceptance and operational runbooks are approved.
- [ ] The orchestrator has no runtime dependency on the provider gateway.
- [ ] Historical evidence retention requirements are known.
- [ ] Rollback can restore the last validated disabled gateway state without provider traffic.

## 13.5 Ordered Tasks

### Step 1 - Create the Retirement ADS and Inventory

Estimate:

```text
0.25 engineer-days
1.5 hours
```

Tasks:

- [ ] Inventory gateway service, identity, policy, source, tests, playbooks, firewall dependencies, state directory, ledger, and documentation.
- [ ] Classify each artifact as preserve, disable, remove, or historical source.
- [ ] Identify shared controls that must remain, especially `assistant` egress denial.
- [ ] Define ordering, rollback, and validation for each removal.
- [ ] Require explicit approval for ledger preservation or service-state changes.

Done when:

- [ ] Every gateway artifact has an evidence-based disposition and rollback path.

### Step 2 - Preserve Historical Evidence

Estimate:

```text
0.1-0.25 engineer-days
0.5-1.5 hours
```

Tasks:

- [ ] Preserve schema 1/schema 2 ledger bytes and ownership without reading raw lines.
- [ ] Preserve dated evidence, ADSs, handoffs, and superseded status markers.
- [ ] Record retention location, ownership, mode, and integrity category only.
- [ ] Prohibit migration into the orchestrator evidence schema.

Done when:

- [ ] Historical evidence is retained separately and cannot be mistaken for active orchestrator evidence.

### Step 3 - Disable and Remove Approved Active Components

Estimate:

```text
0.1-0.25 engineer-days
0.5-1.5 hours
```

Tasks:

- [ ] Disable and stop the gateway before removing approved active deployment artifacts.
- [ ] Confirm no listener or process remains.
- [ ] Remove only artifacts authorized by the retirement ADS.
- [ ] Preserve shared runtime, MCP, credential, audit, and egress controls.
- [ ] Make repeated retirement execution safe and idempotent.

Done when:

- [ ] The gateway cannot receive or send traffic and approved removals converge safely.

### Step 4 - Revalidate and Document Final Architecture

Estimate:

```text
0.1-0.25 engineer-days
0.5-1.5 hours
```

Tasks:

- [ ] Re-run `assistant` egress, orchestrator deployment, MCP lifecycle, process, listener, and evidence checks.
- [ ] Verify the orchestrator cannot fall back to the gateway.
- [ ] Update architecture and operator documents to show the active Codex SDK path and historical gateway status.
- [ ] Record sanitized retirement outcomes and rollback readiness.

Done when:

- [ ] Active architecture documentation and deployed state agree, with historical evidence preserved.

## 13.6 Phase Definition of Done

This phase is done when:

- [ ] The retirement ADS and inventory are approved.
- [ ] Historical ledgers and evidence are preserved without raw inspection.
- [ ] Approved gateway components are disabled or removed safely.
- [ ] `assistant` egress denial and orchestrator/MCP boundaries still pass.
- [ ] No fallback to the old gateway exists.

## 13.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Retirement destroys historical evidence | Preserve first; prohibit raw inspection, deletion, truncation, or migration. |
| Shared egress controls are removed with the gateway | Inventory ownership and test `assistant` denial before and after every change. |
| New orchestrator silently depends on gateway artifacts | Prove dependency absence before retirement and stop if any coupling exists. |
| Historical documents mislead future maintainers | Mark them superseded while retaining their evidence and rationale. |
