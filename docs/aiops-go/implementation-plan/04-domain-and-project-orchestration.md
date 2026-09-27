# 04. Domain and Project Orchestration

## 04.1 Goal

Complete the core product: supported boot, metadata/network and attachment investigations, coordinated across explicit targets with evidence-reviewed partial or supported findings.

```text
approved domain tasks -> authorized evidence -> dependency-aware per-target execution -> review -> qualified synthesis
```

## 04.2 Estimate

Total: **6-10 engineer-days / 36-60 focused hours**.

## 04.3 Scope

Included: domain catalog completion, deterministic workflow routing, sequential task DAGs, durable child links, multi-server synthesis and full evidence review. Primary requirements: FR-006, FR-009, FR-012–FR-013, FR-019–FR-020, FR-025; NFR-007, NFR-013. Evidence: AC-003, AC-005–AC-006, AC-010 and nested-call regression of AC-004.

Excluded: unrestricted diagnostic DAG types, generic tools, parallel/distributed schedulers, speculative root-cause confirmation, broad capacity discovery and real host enablement before Phase 05. Specialist agents are not necessary for review.

## 04.4 Assumptions

- [ ] Phases 01-03 establish scope, approval, bounded execution and durable evidence/child records.
- [ ] Maintainer/operator define reviewed domain evidence and visibility. Missing scheduler/Placement/capacity or host capabilities remain explicitly unavailable, not silently added to project-reader permissions.
- [ ] A single agent plus a deterministic review stage, with bounded model-assisted semantic review where authorized, is the baseline.
- [ ] Higher-visibility positive scenarios can use offline fixtures now; deployed host/operator use remains independently gated.

Dependency: Phase 03; Phase 05 is needed only for live optional evidence, not for honest partial reports or offline domain acceptance.

## 04.5 Ordered Tasks

### Step 1 - Add domain slices through existing contracts

Estimate: **2-4 days / 12-24 hours**.

- [ ] Extend the compute-focused workflow with reviewed metadata/network and project-visible volume/attachment routes. Unknown domains and unavailable subdiagnostics return named limitations, not fabricated commands.
- [ ] Complete catalog contracts for project summaries, server basics/fault/flavor, server networking and bounded volume/attachment reads. Define exact related-resource authorization, sanitized fields, pagination and per-tool tests before enablement.
- [ ] For boot/NoValidHost, correlate fault/flavor and only approved scheduling/capacity/Placement evidence. A fault string alone cannot confirm capacity versus placement/service causes; report unavailable evidence precisely.
- [ ] For metadata, correlate server/port/subnet context with permitted Neutron/Nova/metadata observations. Preserve guest -> Neutron proxy -> Nova metadata API service placement; healthy agents do not prove listener availability.
- [ ] For volume symptoms, inspect authorized volume identity/status and server attachment relationships without tenant-wide discovery, host storage access or attach/detach actions. Distinguish missing attachment, permission denial and unavailable Cinder evidence.
- [ ] Include optional Neutron-agent/log/listener capability contracts only as disabled stubs or fixture adapters until Phase 05 prerequisites pass; unsupported operations cannot fall back to shell or broader credentials.
- [ ] Add healthy server, sufficient/insufficient NoValidHost, Nova listener failure, Neutron failure and volume-attachment fixtures with expected evidence, calls and supported/partial/inconclusive outcomes.

Done when:

- [ ] AC-005 demonstrates each required domain both with sufficient fixture evidence and with missing permissions/tools, with no unsupported root-cause claim.

### Step 2 - Schedule and recover dependency-aware projects

Estimate: **2-3 days / 12-18 hours**.

- [ ] Extend existing plan validation/readiness for reviewed task types and stable IDs, explicit per-target scope, dependencies, attempts, child links and expected evidence outputs. Reject duplicates, cycles, missing dependencies, unsupported types and out-of-scope tasks before approval/execution.
- [ ] Execute sequentially only when required dependencies have succeeded. Preserve pending/ready/running/paused/completed/failed/blocked/cancelled distinctions, and separate project lifecycle from diagnostic confidence.
- [ ] Retain per-target results and provenance; bind child workflows and nested requests to the approved cloud/project/target/capability context. A project-level target list must not grant each task unrestricted access to all targets.
- [ ] Apply project-wide and child budgets, deadlines, retry rules and cancellation. Failed/denied tasks cannot trigger hidden retries, credentials or new targets; cancellation prevents new task/tool dispatch.
- [ ] Preserve completed dependencies on resume and recheck current authorization for remaining tasks. Test child checkpoint failure, interrupted task result and approval/policy revocation without duplicating accepted work.
- [ ] Keep normal synthesis blocked if required evidence tasks fail. Provide an application-defined partial-report path after dependency outcomes are known that explicitly describes failed/blocked coverage; it must not mark failed dependencies successful or execute a success-only graph node.
- [ ] Test two-server success, one-server failure/other completed evidence, missing/blocked dependencies, cancellation and resume. Record exact call order, per-target observations and terminal/report outcomes at the CLI/orchestrator seam.

Done when:

- [ ] AC-006 and graph portions of AC-003 pass; partial project reports retain useful completed evidence without claiming an unqualified diagnosis.

### Step 3 - Review claims and finalize traceable reports

Estimate: **2-3 days / 12-18 hours**.

- [ ] Define material claims with supporting/contradicting evidence IDs and verification classifications. Deterministically validate reference existence, source/scope/time, collection status and required task coverage before finalization.
- [ ] Add semantic review against a labeled corpus: a valid citation is not automatically supporting evidence. Cover unsupported causal claims, irrelevant references, contradictions, truncated collections, stale memory and fabricated confirmation.
- [ ] Permit only bounded follow-up inside existing approved scope/capabilities and remaining budgets. A needed scope expansion returns a new proposal for approval; a review concern cannot silently schedule new authority.
- [ ] Finalize reports with scope, task coverage, facts, interpretations, hypotheses, missing/contradictory evidence, review findings, outcome, manual recommendations, citations and usage/stop metadata.
- [ ] Ensure a completed process with insufficient evidence yields partial/inconclusive diagnosis. Root-cause confirmation requires direct support, not confidence, tool success or reviewer agreement.
- [ ] Test hostile child reports and model review output; neither may alter policy, dependencies, provider, approval or evidence records. No self-delegation or mutation tools are introduced.
- [ ] Regress the single-server and no-provider paths plus versioned exports. Capture reviewer false acceptance/rejection cases for Phase 06 quality measurement, not merely snapshot formatting tests.

Done when:

- [ ] AC-010 catches missing references, contradictory and unsupported claims and yields bounded follow-up or explicitly qualified reports; multi-target exports preserve provenance.

## 04.6 Phase Definition of Done

- [ ] Core domain and multi-server scenarios complete through one approved, bounded, durable execution path.
- [ ] Failed/blocked/unavailable evidence never becomes successful task coverage or fabricated confirmation.
- [ ] Reports support inspection of every material claim or label it unverified; manual remediation remains outside execution.
- [ ] The stateful engineering MVP is ready for consolidated evaluation/operations, not yet declared released.

## 04.7 Risks

| Risk | Mitigation |
| --- | --- |
| Domain coverage requires unavailable operator tools | Support named limitations and offline positives; enable access only through Phase 05. |
| Summary bypasses failed dependency rules | Separate application-owned partial reporting from success-only synthesis tasks. |
| Per-project scope accidentally broadens child scope | Bind each task's authorized subset and test cross-target nested requests. |
| Model review validates its own hallucination | Deterministic provenance checks plus independently labeled semantic fixtures. |
| Extra task types become arbitrary execution | Reviewed finite task catalog with schema, scope and acceptance tests. |
