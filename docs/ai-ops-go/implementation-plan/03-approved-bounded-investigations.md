# 03. Approved Bounded Investigations

**Phase boundary:** PROPOSED.
**Authority:** Roadmap phase, not an approved implementation task contract.
**Source requirements:** [PRD](../prd.md), Entry, scope, and planning; Agent and workflow execution; State, memory, knowledge, and evidence; Data and API Contracts; Normal investigation; Testing Decisions 1–8. FR-001–FR-020, FR-028–FR-030, FR-032, FR-034, FR-037–FR-040, FR-045; NFR-001, NFR-003–NFR-009, NFR-012–NFR-013, NFR-015; AC-001–AC-005, AC-008–AC-010, AC-014–AC-015, AC-018, AC-021–AC-022, AC-025, AC-030.
**Decision gaps:** Approved boundary/storage designs and configured scope from G1–G4; G5 thresholds before model-enabled rollout. Canonical approval representation and bounded related-read rules need specification, not invention by the model.

## 03.1 Goal

Prove one useful single-server investigation from explicit intent and exact approval to a reviewed evidence-linked report, using deterministic orchestration and the existing safe manual/model foundations.

```text
goal + explicit target -> authorized name lookup if needed
  -> validated plan preview -> exact approval
  -> bounded audited evidence loop -> evidence review -> qualified report
```

## 03.2 Estimate

```text
8–12 engineer-days
48–72 focused hours
```

## 03.3 Scope

Included:

- One configured project, explicit single-server scope, structured planner dispositions and exact plan/policy approval.
- Audited pre-plan name resolution under separate explicit lookup authorization; full literal identity behavior.
- Go-owned bounded server/boot investigation, transition checkpoints, state inspection, pause/cancellation and versioned report export.
- Minimal approved sanitized runbook context, deterministic evidence checks and bounded semantic review without specialist distribution.
- Offline end-to-end fixtures and exploratory quality/resource measurements.

Excluded:

- Multi-server execution and full metadata/network/volume workflows, which follow in Phase 05.
- User-exposed resume/history retrieval until Phase 04’s uncertain-call, scope and recovery checks pass.
- Host/operator enablement, MCP, general task execution, runnable remediation and automatic scope expansion.

## 03.4 Assumptions

- [ ] Phase 01/02 safety, persistence and inference prerequisites are evidenced before automatic calls are enabled.
- [ ] Existing validated planner/digest review and compute workflow are selective reuse candidates, not complete approval/scope guarantees.
- [ ] Sequential execution and one capable agent plus an evidence-review stage are sufficient.
- [ ] Investigation records receive applicable quota/cleanup/retention protection immediately; unsupported resume remains explicitly unavailable, never an unsafe fallback to legacy engine behavior.

## 03.5 Ordered Tasks

### Step 1 - Bind explicit intent to a validated plan

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Persist original goal, cloud/project, selected identifier and resolved UUID, allowed capabilities/profiles, related-read categories, policy identity and finite budgets as application-owned data.
- [ ] For names, disclose and obtain separate explicit authorization for bounded project-reader lookup before approval; audit the lookup and reject missing/ambiguous/case/whitespace mismatches without diagnostic task execution.
- [ ] Produce validated `ready`, `needs-input` or `unsupported` dispositions; non-ready or invalid plans explain gaps and execute no diagnostics. Planning model calls still require prior disclosure approval.
- [ ] Reject duplicate IDs, unknown task types, missing dependencies, cycles and scope/capability/budget expansion. Do not grant a generic DAG interpreter merely because a structured graph is valid.
- [ ] Preview targets, dependencies, required profiles, limits and expected outputs. Bind approval to the canonical validated plan/scope/relevant policy with configurable 24-hour default; cancellation or mismatch dispatches nothing.

Done when:

- [ ] Full CLI fixtures distinguish separate lookup permission from plan permission, and stale/changed/revoked/expired/unapproved plans cannot start diagnostic tasks.

### Step 2 - Run the bounded deterministic investigation

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Carry approval identity and all scope constraints through workflow, agent and gateway calls; revalidate each request instead of trusting a planner-approved target.
- [ ] Let Go own readiness, transitions, transient retries, deadlines and completion. Structurally and semantically validate every control response; invalid outputs get bounded repair or explicit failure, never free-form execution.
- [ ] Permit only approved server-related reads proven by authorized evidence. Discovered resources do not grant host, project-summary or unrelated discovery rights.
- [ ] Stop on completion, insufficient evidence/capability, repeated unproductive requests, cancellation or finite task/step/tool/retry/time/context/output/token-cost limits. Denials are not transient retries or opportunities to switch credentials.
- [ ] Enforce revocation/expiry during active calls using cancellation attempts and result withholding; do not claim an already performed read was undone.
- [ ] Checkpoint before/after significant transitions and expose status, safe errors and uncertain/interrupted operations. Required persistence/audit failure prevents later dispatch.

Done when:

- [ ] A valid approved plan followed by hostile nested requests for another server/project/host/profile is denied at dispatch; cancellation/budget exhaustion produces no later calls.

### Step 3 - Review findings and export honest reports

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Give observations stable evidence IDs, authorized source/target, collection status and timestamps; distinguish interpretations and working summaries from raw observations and curated reference knowledge.
- [ ] Enforce the 15-minute freshness default and justified configurable per-tool overrides from first use. Stale evidence cannot confirm current state; refresh is explicit, budgeted and authorized, never silent replacement.
- [ ] Use only explicitly approved bounded sanitized runbook content with stable citations; absence of suitable knowledge is a named limitation. Broader curated indexing follows in Phase 04.
- [ ] Validate evidence references and required task coverage deterministically, then review whether material claims are actually supported. Contradictory, missing, denied or stale evidence yields bounded in-scope follow-up or partial/inconclusive output.
- [ ] Separate operational completion from diagnosis outcome. A NoValidHost fault string alone cannot establish capacity/Placement root cause; unavailable supporting tools remain explicit gaps.
- [ ] Support a “fix it” goal by offering a separately approved read-only plan and manual plain-language, runbook-cited recommendations without runnable mutation commands. If approval/access is absent, collect nothing unauthorized.
- [ ] Provide local state/report inspection and versioned alias-default exports, with facts, hypotheses, contradictions, unknowns, review findings, limits/usage and provenance. Never describe unpersisted state as safely saved.

Done when:

- [ ] Supported, incomplete, fabricated and contradictory fixtures yield appropriately qualified reports, and every material verified claim has valid supporting provenance rather than merely a citation-shaped string.

### Step 4 - Establish the first end-to-end scenario baseline

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Run full CLI/orchestrator scenarios with deterministic model responses and controlled API fixtures; assert approved scope, exact call sequence, audit/checkpoints, evidence links and terminal/diagnostic outcomes.
- [ ] Cover healthy server, boot fault with sufficient evidence, unavailable capacity evidence, ambiguous/missing resource, malformed model control, provider outage, hostile output and fix-it refusal/diagnostic behavior.
- [ ] Add approval expiry/revocation races, budget/cancellation, wrong relationship, secret-canary and persistence/audit fault regressions at public seams.
- [ ] Emit correlated planning/task/model/tool/review events, concise action explanations and remaining limits; no hidden model reasoning. Record exploratory task success, unnecessary calls, unsupported claims, latency and known/unknown usage in versioned results.
- [ ] Document first automated slice limitations, disabled resume and required follow-up gates. Obtain any live/model authorization separately; do not infer it from a passing offline scenario.

Done when:

- [ ] Offline single-server scenarios are reproducible without cloud/provider credentials and provide the exploratory baseline needed to extend, not a release SLA or deployed validation claim.

## 03.6 Phase Definition of Done

- [ ] One approved single-server investigation completes an evidence-to-report path with no bypass, mutation or prohibited disclosure.
- [ ] Approval defaults/invalidation, explicit name lookup, call-boundary relationship checks and all applicable budgets are tested.
- [ ] Pausing/cancellation and persistence failures are visible; unsafe resume is not exposed.
- [ ] Reports distinguish operational completion, supported findings, partial findings and inconclusive outcomes.
- [ ] Versioned offline baseline and remaining domain/live/recovery gaps are recorded. This intermediate slice is not full Delivery 1 acceptance.

## 03.7 Risks

| Risk | Mitigation |
| --- | --- |
| Pre-plan lookup becomes unapproved discovery | Separate explicit bounded lookup authorization, project constraint and audit. |
| Approval digest excludes policy, scope or limits | Canonical reviewed representation includes all authority-bearing fields; change/revocation fixtures. |
| Model reviewer endorses unsupported statements | Deterministic reference/provenance checks plus fixture-grounded semantic evaluation. |
| Evidence refresh silently changes history | New timestamped observation and explicit scope/budget check, no replacement. |
| Existing generic runtime is trusted downstream | Recording gateway tests for nested scope/profile changes, independent of plan validity. |

## 03.8 Proposed Requirement Coverage and Handoff

| Requirement / AC source | Proposed phase responsibility | Existing behavior / deferral | Risk or unapproved decision |
| --- | --- | --- | --- |
| FR-001–FR-007; AC-001/002/003/030 | Single-server entry, lookup, validated exact approval and graph restrictions | Multi-target closure in 05; existing planner only partial | G3 approved related-read rules and policy-bound canonical form. |
| FR-008–FR-011/014/040; AC-004/014/022 | Bounded deterministic execution and checkpoints | Full resume/recovery in 04 | G4; required writes must never be ignored. |
| FR-012/016–FR-020/030; AC-005/008/009/010/015 | Boot workflow, minimal curated context, evidence review and manual recommendations | Full domains in 05/06; curated retrieval/history in 04 | Root-cause evidence cannot be substituted by model confidence. |
| FR-037–FR-039; AC-021/025 | Offline end-to-end baseline and correlated metrics | Pinned release evaluation/live proof in 08 | G5 remains a release blocker. |

Proposed handoff to Phase 04: approved-record/transition contracts, evidence IDs/timestamps, paused/interrupted fixtures and baseline reports. Independent scope readiness and a separate approved task contract are still required; this phase file is neither.
