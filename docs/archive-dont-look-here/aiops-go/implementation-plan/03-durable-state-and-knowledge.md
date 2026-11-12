# 03. Durable State and Knowledge

## 03.1 Goal

Make investigations safely recoverable and preserve context without confusing stale memory or runbook text with fresh infrastructure evidence.

```text
approved investigation -> atomic scoped checkpoints -> interruption -> policy-checked resume -> cited fresh/historical context
```

## 03.2 Estimate

Total: **5-8 engineer-days / 30-48 focused hours**.

## 03.3 Scope

Included: versioned investigation/workflow/project persistence, writer exclusion, interruption semantics, migration/rollback, context classes, scoped memory, curated lexical retrieval and protected exports. Primary requirements: FR-014–FR-018, continued FR-001/FR-019/FR-029/FR-039–FR-040; NFR-004–NFR-005, NFR-012. Evidence: AC-007–AC-009, resumed-call portion of AC-004 and recovery subset of AC-022.

Excluded: database/distributed stores, concurrent operators, parallel scheduling, raw repository ingestion, embeddings/vector services and automatic in-place historical conversion.

## 03.4 Assumptions

- [ ] Phases 01-02 provide bounded execution, evidence IDs and initial versioned state.
- [ ] Maintainer approves supported schema versions, conversion and uncertain-call recovery policy before enabling resume.
- [ ] Data owner selects retention, size ceilings, freshness windows and export permissions before persistent production use.
- [ ] Single local operator and sequential execution are sufficient; conflicting writers are serialized or rejected explicitly.

Dependency: [Phase 02](02-bounded-investigation.md), including its inherited [Phase 01 contract reconciliation](01-safety-boundary-and-manual-slice.md#constraint-reconciliation-and-authority). Before execution, identify the approved PRD revision, accepted Phase 01–02 revisions, applicable amendments and verification evidence; a commit or draft review does not establish approval. Provides durable contracts for multi-server orchestration and MCP resources.

Checkpoint intent is application state, not authorization to extend the accepted runner's closed audit protocol. Preserve its event fields and cardinality, fixed paths, rotation/retention and unsafe-path recovery rules unless an applicable amendment is approved; a proposed audit intent/event extension requires Level 2 approval and governing contract amendment before activation. General data retention must not silently replace those audit rules.

## 03.5 Ordered Tasks

### Step 1 - Make persistence and resume truthful

Estimate: **2-3 days / 12-18 hours**.

- [ ] Reconcile investigation/workflow/project schemas into versioned linked records retaining goal, scope, plan/policy/approval, budgets, lifecycle/outcome, task/step attempts, child IDs, observations, hypotheses, errors, usage and timestamps.
- [ ] Preserve atomic replacement/transactional commitment and restrictive permissions; validate paths and record IDs, reject traversal/symlink escapes, corrupt or unsupported versions and incomplete linkage. Surface directory/sync/rename/disk failures rather than claiming a durable save.
- [ ] Implement single-writer locking or equivalent conflict rejection for start/resume/update. Test concurrent resume and lock cleanup on crash; no double dispatch is allowed.
- [ ] Persist intent before dispatch and result/state afterward. Distinguish never-started, running/interrupted, result-recorded and uncertain completion; define conservative replay decisions without claiming exactly-once external execution.
- [ ] Resume unchanged completed work without redispatch, validate current policy/credentials/capabilities and approval, and reject revoked access. Scope changes require a new plan and approval; stale approval never restores authority.
- [ ] Make intentional refresh/re-observation explicit and audited, creating a new timestamped observation rather than replacing historical evidence. Preserve cumulative budgets and usage across resume; no reset loophole.
- [ ] Separate pause from cancellation and operational completion from diagnostic outcome. Inspect interrupted/blocked work without a provider, and propagate checkpoint errors from all failure and pause paths.
- [ ] Inject crashes before dispatch, during calls, after results before checkpoint and during finalization; test failed writes, corrupt versions, revoked policy, duplicate resume and uncertain-call display at the CLI boundary.
- [ ] Test restart with exhausted and partially consumed budgets, including a crash after dispatch before result/checkpoint. Keep uncertain usage explicit as unknown and enforce conservative limits, never treating it as zero or replenishing allowance; if remaining allowance cannot be bounded safely, prevent further dispatch. Prove intentional re-observation consumes remaining allowance and exhausted budgets permit no further model or tool dispatch. [Phase 06](06-evaluation-and-operational-readiness.md) consolidates and reruns these regressions; it does not defer this gate.
- [ ] Exercise cross-sink recovery for terminal-audit failure and for checkpoint failure after a durable terminal audit: no premature successful publication or automatic replay, committed evidence and persisted audit events remain intact, and incomplete/uncertain transitions are visible on restart. For audit failure, withhold diagnostic payload and raw errors, expose failure locally and block further calls until safe recovery. Do not erase an audit event to simulate rollback or claim atomicity across external calls and both sinks.
- [ ] Test duplicate record/evidence IDs and requested-versus-stored ID mismatch; reject collisions or mismatches without overwriting unrelated records. Test an exact name resolving to a different canonical resource after restart: never silently rebind the approved target; do not impose uniqueness on OpenStack names.

Done when:

- [ ] AC-007 and resumed AC-004 cases prove no silent replay or scope expansion, no falsely reported save, and preservation of completed work.
- [ ] Before resume is enabled, the restart, uncertain-usage, re-observation and exhaustion tests above pass for cumulative budgets (FR-039–FR-040, recovery subset of AC-022), alongside the cross-sink and identity regressions.

### Step 2 - Bound and partition context and retrieval

Estimate: **2-3 days / 12-18 hours**.

- [ ] Partition evidence/memory/approvals by cloud, OpenStack project and investigation authorization. Names alone cannot join historical investigations across tenants; canonical identity and current visibility are checked.
- [ ] Represent fresh observations, derived working summaries, historical memory and reference knowledge separately in storage, model context and reports. Summaries retain evidence IDs; stale conclusions never satisfy fresh-evidence requirements.
- [ ] Bound summary/context size and preserve provenance, contradictions and unknowns when compacting. Failure to summarize must not silently discard necessary evidence or remove safety context.
- [ ] Approve a curated source manifest, not an arbitrary repository root. Reuse lexical retrieval and chunking with fixed roots, safe path handling, source/revision/content identity, section/chunk IDs, bounded excerpts and relevance.
- [ ] Restrict ingestion size/type and visibility; reject symlink/traversal escapes and withhold secret-bearing content. Curated material is still untrusted and cannot grant capabilities or change policy/provider/approval.
- [ ] Make no-match, stale/conflicting knowledge and inaccessible optional roots visible limitations while preserving manual diagnostics. Define freshness/display policy rather than silently dropping historical references.
- [ ] Test malicious instructions in goals, logs, observations, summaries, prior reports and retrieved chunks, as well as oversized documents, missing roots and cross-project same-name memories. Assert no authority change or prohibited disclosure.

Done when:

- [ ] AC-008–AC-009 distinguish context classes and preserve stable citations; secret/injection and cross-scope fixtures cannot broaden access.

### Step 3 - Migrate and operate protected local data

Estimate: **1-2 days / 6-12 hours**.

- [ ] Inventory representative existing state/exports with sanitized fixtures. Define supported legacy versions, read-only inspection of unsupported records and explicit conversion to a new destination with verification and backup.
- [ ] Test migration preservation of original goals, original/resolved identity, IDs, timestamps, child links and outcomes; absent legacy authority/evidence fields must not be invented. Legacy records without sufficient authority remain non-resumable until the existing validated-plan and exact-approval requirements, including current authorization, are satisfied.
- [ ] Test duplicate record/evidence IDs and conversion-destination collisions; reject unsafe conversions without overwriting unrelated records or silently rebinding a target.
- [ ] Rehearse rollback using untouched backups and compatible runtime/configuration. Do not migrate saved state in place or remove original audit evidence on conversion failure.
- [ ] Implement approved retention, maximum data volume, safe export/deletion and restrictive permissions without changing the inherited audit retention and unsafe-path contract. Protect exports with the same scope/redaction policy; constrain local application writes to its data area.
- [ ] Verify cross-version export schemas, dangling evidence handling after retention, provider-independent inspection and full checkpoint/resume/knowledge regression of the Phase 02 workflow.

Done when:

- [ ] A documented, tested conversion/recovery path exists or legacy resume is explicitly refused; retention/export cannot silently corrupt evidence support or cross scope boundaries.

## 03.6 Phase Definition of Done

- [ ] Durable state/resume handles all defined interruption points, writer conflicts and policy changes honestly.
- [ ] Completed work is retained; re-observation is visible, budgeted and auditable. Resume remains disabled until the focused restart and cumulative-budget regressions pass, including uncertain usage and zero dispatch on exhaustion.
- [ ] Scoped memory and curated retrieval enrich reports with provenance without acquiring authority.
- [ ] Schema, retention, freshness and migration decisions have owners and tests; no unresolved production-data assumption is hidden.

## 03.7 Risks

| Risk | Mitigation |
| --- | --- |
| Read call completed but result was not persisted | Persist intent, expose uncertain state and require an explicit bounded replay policy. |
| Atomic file write mistaken for whole-project transaction | Validate child links and crash boundaries; serialize writers and test recovery. |
| Historical names leak another tenant's evidence | Partition by cloud/project/canonical identity and current authorization. |
| Summaries or curated docs become trusted instructions | Separate data/control, retain evidence references and run injection fixtures. |
| Migration destroys rollback or creates approval | Convert into new storage, preserve backups, never synthesize missing authority. |
