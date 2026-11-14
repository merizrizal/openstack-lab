# 04. Durable State, Knowledge and Data Lifecycle

**Phase boundary:** PROPOSED.
**Authority:** Roadmap phase, not an approved implementation task contract.
**Source requirements:** [PRD](../prd.md), State, memory, knowledge, and evidence; Session, data lifecycle, and legacy records; Interruption and degraded operation; Testing Decisions 5–7, 15. FR-001–FR-002, FR-005, FR-010, FR-014–FR-020, FR-028–FR-029, FR-034, FR-039, FR-041–FR-042, FR-048–FR-050; NFR-001, NFR-004–NFR-008, NFR-012–NFR-013, NFR-015; AC-004, AC-007–AC-010, AC-014, AC-018, AC-023–AC-024, AC-030–AC-031.
**Decision gaps:** G4 concrete durability, writer arbitration, reference accounting, cleanup and audit recovery design; G2 finite storage configuration; approved curated source set under FR-017. File persistence and lexical retrieval remain proposals until appropriately reviewed.

## 04.1 Goal

Make interruptions recoverable and context reusable without replaying uncertain calls, reviving stale authority, leaking historical data or losing lifecycle protections.

```text
paused/interrupted versioned case -> validated current scope/policy/approval
  -> acknowledged gaps + confirmed uncertain re-collection where needed
  -> preserved completed work + fresh authorized observations -> reviewed report
```

## 04.2 Estimate

```text
8–12 engineer-days
48–72 focused hours
```

## 04.3 Scope

Included:

- Full pause/resume/crash recovery, writer control and terminal-state enforcement over the new store.
- Explicit evidence freshness, working summaries, authorized historical links and approved lexical knowledge retrieval.
- Reference-aware retention, quota/disk failure, audited cleanup/deletion, protected exports and lifecycle operations.
- Provider-independent state/report access and recovery tests through CLI/orchestrator seams.

Excluded:

- Legacy conversion/import/indexing, automatic promotion of archived knowledge, database infrastructure, embeddings/vector services, parallel execution and cross-project memory reuse.
- New diagnostic domains or specialist roles.

## 04.4 Assumptions

- [ ] Phase 01/03 provide safe applicable baseline retention/quota, versioned records, checkpoints, evidence identity and audit before this expansion.
- [ ] Sequential scheduling remains sufficient; multiple process writers are nevertheless serialized or rejected.
- [ ] Operator-reviewed current curated sources can be sanitized and assigned explicit scope/revision; repository discovery alone grants no approval.
- [ ] Historical evidence may be linked only under current authorized visibility and stays historical/stale, including when retained for an active reference.

## 04.5 Ordered Tasks

### Step 1 - Make persisted transitions and recovery trustworthy

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Complete versioned records for goal/scope, approval/policy, budgets, task/step and child links, observations, hypotheses, errors, usage and terminal reasons. Atomically/transactionally commit significant before/after transitions.
- [ ] Validate schema, integrity, authorization scope and current policy on load/resume; reject incompatible/corrupt state and concurrent resume/writer conflicts without claiming saved or resumable work.
- [ ] Distinguish proposed, awaiting approval, running, paused, completed, failed and cancelled lifecycle from supported/partial/inconclusive diagnosis. Completed, failed and cancelled cases cannot resume; a new case needs its own scope/approval.
- [ ] Preserve completed work. Mark a possibly dispatched call uncertain rather than resetting it silently to pending; require explicit operator confirmation before authorized new collection and create a new observation.
- [ ] On approval expiry/revocation/policy change, block new work and renew approval as required. Audit recovery pauses until the operator acknowledges known gaps/uncertain calls; acknowledgement is not renewed diagnostic authority.

Done when:

- [ ] Crash tests before dispatch, in-flight, after result/before checkpoint and during finalization preserve the actual known/unknown state and never silently replay uncertain operations.

### Step 2 - Separate observation, summary and historical memory

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Maintain distinct current observations, derived working summaries, historical investigation memory and reference knowledge, with evidence/provenance links preserved through compaction and export.
- [ ] Apply configurable 15-minute observation freshness with justified per-tool overrides; retain collection time separately from source log event time. Expired evidence cannot establish current state.
- [ ] Make intentional refresh explicit: verify plan/budget/current access or request renewed authorization; retain prior evidence instead of replacing it. Uncertain re-collection also requires the separate confirmation rule.
- [ ] Partition context, memory, approvals and knowledge visibility by cloud/project/investigation; identical names or project switches cannot grant access or resume mismatched records.
- [ ] Bound summary/context size and sanitize before persistence. Historical retrieval cannot convert old summaries or conclusions into fresh facts or tool permissions.
- [ ] Keep local state/report inspection and authorized exports available without a model when storage/policy permit; provider outages and revoked disclosure do not force remote calls for inspection.

Done when:

- [ ] Time-controlled stale/fresh/log-time and cross-project fixtures preserve typed provenance across resume, summaries and exports, without model availability.

### Step 3 - Add explicitly curated bounded knowledge retrieval

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Use an explicit approved current-source selection with scope/access checks, not recursive repository/archive ingestion. Older knowledge requires deliberate operator review, sanitization and promotion before inclusion.
- [ ] Adapt existing text chunking/lexical retrieval to return bounded excerpts, stable source/section/chunk identities and revision/content identity where available. Indexing must obey storage/privacy controls too.
- [ ] Surface stale, missing, conflicting or inaccessible sources as limitations; optional knowledge failure must not disable otherwise safe manual diagnostics.
- [ ] Treat documents, observations, summaries and prior reports as untrusted data; embedded instructions cannot change scope, provider, approval, permissions or policy.
- [ ] Test no matches, oversized/secret-bearing sources, inaccessible roots, out-of-scope history, changed revisions, conflicting knowledge and hostile text. Distinguish runbook citations from live infrastructure evidence in reports.

Done when:

- [ ] Approved sources produce bounded reproducible citations, unapproved/archived sources remain absent, and malicious content cannot broaden access or leak protected fields.

### Step 4 - Complete reference-aware lifecycle and storage operations

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Enforce configurable 30-day terminal-investigation and 90-day sanitized-audit retention, protecting running/paused cases. Run bounded cleanup at startup and while operating; report overdue cleanup after downtime and any failures.
- [ ] If an expired terminal case is referenced by an active case, retain only minimum sanitized evidence/provenance, report the exception and count it against the finite storage limit. Do not make it fresh.
- [ ] Require durable audit intent for automatic or operator-confirmed deletion; intent failure prevents deletion, outcome-audit failure reports the gap and possible completed deletion rather than claiming rollback.
- [ ] Permit confirmed operator-only early deletion of unexpired terminal data, but never active-dependent evidence or audit before its separate retention. The model cannot request/perform deletion.
- [ ] On quota or actual disk-full failure, safely clean only eligible expired data; never silently evict unexpired records. Stop dispatch/model work when audit/checkpoint guarantees fail and preserve inspection/export/operator cleanup where possible.
- [ ] Default protected exports to aliases. Real necessary operational identifiers require explicit operator request, warning and audited action; secrets/prohibited fields remain excluded. Explain responsibility for exported copies.
- [ ] Prove legacy files remain unchanged, unimported, unindexed, unsent and outside cleanup, including when legacy files contribute to physical disk exhaustion.

Done when:

- [ ] Time/disk/audit-fault fixtures cover retention defaults, startup/runtime cleanup, active-reference exceptions, confirmed deletion and alias/identifier exports, with no premature audit deletion or legacy modification.

## 04.6 Phase Definition of Done

- [ ] Paused/interrupted work resumes only under validated current authority and explicit uncertain-call rules; terminal cases never resume.
- [ ] All required writes are reliable or visibly failed; concurrent writers and corrupt/incompatible records fail safely.
- [ ] Freshness, summaries, history and curated knowledge remain distinct and scope-isolated.
- [ ] Full retention/quota/cleanup/deletion/export tests pass, including physical disk exhaustion and audit gaps.
- [ ] Local reports/inspection/manual diagnostics remain provider-independent when their own safety dependencies are healthy.
- [ ] No old approvals, archived ingestion or legacy migration has been introduced.

## 04.7 Risks

| Risk | Mitigation |
| --- | --- |
| A saved running task is blindly retried | Persist call intent/uncertainty and require explicit re-collection confirmation. |
| Atomic rename is assumed sufficient durability/concurrency | Specify/test crash behavior, writer arbitration and visible failed saves. |
| Retention removes evidence an active case needs | Track minimum authorized references, retain/report exceptions and count quota. |
| Disk pressure triggers unsafe eviction | Stop execution; only eligible audited cleanup or confirmed permitted operator deletion. |
| A knowledge directory includes sensitive/archived content | Explicit approval and sanitization, bounded index, negative ingestion fixtures. |

## 04.8 Proposed Requirement Coverage and Handoff

| Requirement / AC source | Proposed phase responsibility | Existing behavior / deferral | Risk or unapproved decision |
| --- | --- | --- | --- |
| FR-014–FR-015; AC-007/030 | Atomic scoped state, terminal rules, uncertainty and acknowledged recovery | Existing file replacement/resume is partial, not accepted | G4 writer and crash semantics. |
| FR-016–FR-018; AC-008/009 | Freshness, typed memory and approved bounded retrieval | Existing lexical/chunking seams reused selectively | Approved source set still operator-owned. |
| FR-019–FR-020/034; AC-010/018 | Provenance-preserving reports/context and provider-independent inspection | Domain/project review grows in 05 | Historical claims cannot satisfy fresh evidence. |
| FR-028–FR-029/048–FR-050; AC-014/023/024/031 | Audit recovery and complete protected lifecycle | No legacy migration in this roadmap | G2/G4; deleted/transmitted data cannot be recalled. |

Proposed handoff to Phase 05: safe resume API, reference/freshness contracts, curated citations, lifecycle fault fixtures and unchanged legacy baseline. Independent scope readiness and a separate approved task contract are still required; this phase file is neither.
