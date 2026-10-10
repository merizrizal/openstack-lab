# 06. Evaluation and Operational Readiness

## 06.1 Goal

Turn accumulated scenario tests into repeatable quality/safety evidence and make the supported runtime observable, bounded and operable.

```text
versioned fixtures + pinned rubric -> reproducible evaluation -> correlated quality/usage -> readiness and release decision
```

## 06.2 Estimate

Total: **4-7 engineer-days / 24-42 focused hours**.

## 06.3 Scope

Included: consolidated offline evaluation, metrics/threshold governance, correlated telemetry, aggregate budgets, startup/readiness, protected lifecycle procedures and specialist enablement decision. Primary requirements: FR-036–FR-042; NFR-006–NFR-009, NFR-014–NFR-015. Evidence: AC-020–AC-022 and readiness preparation for AC-023/AC-025.

Excluded: a new observability platform, live inference by default, invented SLAs, mandatory specialist implementation, distributed scheduling and advanced retrieval without demonstrated need.

## 06.4 Assumptions

- [ ] Phases 01-04 already supply tests, versioned results, correlation and finite limits; this phase consolidates rather than first introduces them.
- [ ] Phase 05 evidence is included only for enabled integrations; unavailable access never justifies suppressing a required safety test.
- [ ] Product/release owner agrees corpus/rubric and quality, latency, usage/cost and unnecessary-call thresholds before release measurements. Unresolved thresholds block model-enabled rollout.
- [ ] Optional specialists remain disabled unless a separately approved design and measured comparison justify implementation; estimates exclude that future work.

Dependency: Phase 04; Phase 05 only for integrations selected for release.

## 06.5 Ordered Tasks

### Step 1 - Consolidate reproducible evaluation and release gates

Estimate: **2-3 days / 12-18 hours**.

- [ ] Package versioned incident fixtures with deterministic model/tool substitutes, expected targets/calls, required evidence, outcomes and safety assertions. Run the full CLI/orchestrator path without cloud/provider credentials or network dependency.
- [ ] Cover healthy server, sufficient and insufficient-evidence NoValidHost, metadata listener failure, Neutron failure, volume-attachment symptom, permission denial, ambiguous name, missing resource, provider outage, hostile logs and multi-server partial failure.
- [ ] Include malformed decisions/graphs, stale approval, out-of-scope nested/resumed calls, audit failure, checkpoint corruption, concurrent resume, cancellation and secret-canary regressions from earlier phases.
- [ ] Emit machine-readable versioned results with fixture/runtime/policy/model-substitute versions, expected/actual outcome, task success, appropriate tool selection, unsupported factual claims, unnecessary calls, safety violations, elapsed time and available usage/cost.
- [ ] Score fixture-supported inconclusive outcomes separately from fabricated diagnosis and unnecessary failure. Define human-labeled semantic evidence support where deterministic checks alone cannot establish causality; do not use model self-review as the oracle.
- [ ] Publish per-scenario tool counts and latency distributions with sample counts; report measured versus unavailable token/cost and pricing basis. Deterministic fake usage is labeled synthetic, not measured provider cost.
- [ ] Pin dataset/rubric and pre-agreed release thresholds before measuring a candidate. Require zero unauthorized executions, mutations and prohibited disclosures in deterministic safety tests; record other thresholds as owner-approved values, not guessed SLAs.
- [ ] Define optional repeated model-backed evaluation as a separate opt-in job with authorized provider/disclosure and protected corpus; never conflate fixture, model and deployed evidence.

Done when:

- [ ] AC-021 runs offline reproducibly and emits inspectable results; quality/latency/cost thresholds have approval or are an explicit release blocker.

### Step 2 - Expose operational signals and enforce readiness

Estimate: **1-2 days / 6-12 hours**.

- [ ] Correlate plan, project/task, investigation, tool, model, review, resume and export events with concise decisions/outcomes, policy/approval identity and safe failure reasons. Preserve provenance without hidden chain-of-thought or raw sensitive payloads.
- [ ] Expose counters/timing for retries, denials, timeouts, truncation, audit/checkpoint failures, incomplete reports and usage. Validate correlation survives failed and resumed runs; unavailable metrics remain unknown.
- [ ] Verify aggregate limits for task count, agent steps, calls, retries, elapsed time, context/output and available tokens/cost across children and resume. Exhaustion/cancellation prevents subsequent dispatch and bounds active subprocess cleanup.
- [ ] Add startup/preflight checks for configured registry/tools, profile bindings, state stores, curated knowledge, enabled model/MCP adapters, policy and audit dependencies. Required failure stops execution/startup; optional failure disables capability with actionable diagnostics.
- [ ] Verify readiness probes themselves are bounded and do not silently authenticate to cloud or call providers without approved mode. Offer offline configuration validation distinct from authorized connectivity checks.
- [ ] Implement/review shutdown, data quota/retention/export/deletion, credential rotation/revocation and policy-version identification procedures using Phase 03 data rules. Shutdown preserves interruption visibility and does not mutate workloads.
- [ ] Reuse current build/deployment/validation seams and document prerequisites/version pinning; do not add a parallel deployment lineage or require a monitoring cluster for local visibility.

Done when:

- [ ] AC-022 and startup fault fixtures demonstrate correlated, finite runs and required-versus-optional readiness behavior; Phase 07 can rehearse lifecycle procedures.

### Step 3 - Record specialist gate and release evidence package

Estimate: **1-2 days / 6-12 hours**.

- [ ] Record single-agent plus evidence-review baseline results and specialist capability as disabled in configuration, discovery and the release matrix. Review is a core stage, not dependent on specialists.
- [ ] Define future specialist enablement gate: approved task/scope/tool/context budgets, application-owned dependencies, structured evidence-linked handoffs, conflict-as-review handling and no autonomous delegation. Future work must rerun delegated scope-escape fixtures.
- [ ] Require a versioned quality/cost/latency comparison against the single-agent baseline and passing isolation tests before any specialist activation. Do not implement multi-agent complexity merely to satisfy an educational milestone; AC-020 records optional-disabled until separately authorized.
- [ ] Assemble FR/NFR/AC evidence links from the overview matrix, capability versions, pass/fail/blocked/optional-disabled statuses, security exceptions (which block affected enablement), unresolved decisions and owners.
- [ ] Document operator workflows for no-provider operation, partial diagnosis, checkpoint/audit failure, revocation, data handling, extension review and rollback; ensure a second operator can interpret evidence without private model reasoning.

Done when:

- [ ] The candidate has a reproducible offline evidence package, an explicit specialist-disabled decision and an actionable checklist for authorized deployed acceptance.

## 06.6 Phase Definition of Done

- [ ] Offline evaluation runs without secrets or external calls and distinguishes good inconclusive diagnosis from hallucination.
- [ ] Safety gates pass, metrics are honest, and release thresholds are pinned or explicitly block rollout.
- [ ] Required control failures fail closed; optional capability failures preserve permitted local workflows.
- [ ] Core operational procedures and capability/evidence matrix are ready for Phase 07 rehearsal.

## 06.7 Risks

| Risk | Mitigation |
| --- | --- |
| Rubric rewards plausible but unsupported claims | Labeled claim support, explicit inconclusive scoring and negative causal examples. |
| Thresholds tuned after seeing release results | Freeze versioned corpus/rubric/thresholds before candidate measurements. |
| Fake latency/cost represented as production performance | Label evidence tier and synthetic/unknown usage; separate model runs. |
| Evaluation leaks secrets or calls live services | Sanitized fixtures, credential-free default jobs and explicit external opt-ins. |
| Specialist work expands scope prematurely | Disabled-by-default record and separate design/measurement gate. |
