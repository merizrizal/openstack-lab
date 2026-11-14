# 05. Domain Workflows and Project Orchestration

**Phase boundary:** PROPOSED.
**Authority:** Roadmap phase, not an approved implementation task contract.
**Source requirements:** [PRD](../prd.md), Agent and workflow execution; Diagnostic safety and access; Metadata and VM boot cases; Data and API Contracts; Testing Decisions 1–8. FR-001–FR-002, FR-005–FR-014, FR-016–FR-020, FR-023–FR-025, FR-027, FR-036–FR-040, FR-044; NFR-001, NFR-003–NFR-011, NFR-013, NFR-015; AC-001, AC-003–AC-006, AC-010, AC-014, AC-020–AC-022, AC-024–AC-027.
**Decision gaps:** G3 exact API visibility/related-read rules; G5 pinned evaluation criteria before rollout. Higher-visibility diagnostics remain gated in Phase 06; absent safe access must not be replaced with broader discovery.

## 05.1 Goal

Complete project-visible diagnostics and required domain workflows, then coordinate several explicitly chosen servers without losing per-target evidence or overstating project success.

```text
approved single/multi-target plan -> dependency-ready scoped tasks
  -> boot / metadata-network / volume-attachment evidence
  -> per-target review -> qualified cross-task synthesis
```

## 05.2 Estimate

```text
9–14 engineer-days
54–84 focused hours
```

## 05.3 Scope

Included:

- Project summary categories: servers, networks, subnets, project-visible volumes and images, with explicit project-wide authorization.
- Complete server-basic/network evidence and bounded project-visible volume/attachment diagnostics.
- Metadata/network and volume workflows alongside server/boot investigation, with safe gaps for unavailable subdiagnostics.
- Sequential dependency-aware multi-server orchestration, per-target evidence, child-state links and synthesis.
- Expanded offline evaluation and explicit disabled-specialist checks.

Excluded:

- Generic diagnostic DAG execution, implicit project-wide scope from one server, cloud-wide inventory, host enablement, storage-host access, parallel/distributed scheduling and specialist activation.
- Advanced retrieval and speculative services/schemas for future capabilities.

## 05.4 Assumptions

- [ ] Phases 01–04 provide scoped dispatch, approval, isolation, recovery and provenance contracts.
- [ ] Existing Go server/port tools, project engine and evidence-review seams can be extended without retaining their unverified failure/scope behavior.
- [ ] Required project-visible reads have safe reader policies; exact service availability and relationships must be established, not inferred from successful authentication.
- [ ] The single-agent plus evidence-review baseline remains enabled; existing team/delegation code need not be activated because it exists.

## 05.5 Ordered Tasks

### Step 1 - Complete the project-visible diagnostic catalog

Estimate: **3–4 engineer-days / 18–24 hours**.

- [ ] Add reviewed Go API capabilities for project resource summaries across servers, networks, subnets, volumes and images where project-visible. Project summary is separately scoped; a server relationship does not imply project-wide approval.
- [ ] Complete required server-basic fields and explicit unavailable/denied/not-applicable states; preserve fault, image, flavor, networks, config drive and availability-zone semantics across CLI and automated use.
- [ ] Add bounded related ports, fixed IPs, networks and subnets, verifying project/target relationships from authorized observations at dispatch and on returned resources.
- [ ] Add bounded volume and attachment evidence with explicit tenant visibility and attachment relationships. Do not infer permission to query storage hosts or service databases.
- [ ] Return per-category project-summary statuses: mixed success is partial; denied/unavailable categories are not empty/healthy; no successful category produces an appropriate failure rather than partial success.
- [ ] Register schema/risk/profile/bounds and tool-local validation for each addition; add controlled API/input/static/behavioral safety tests, including pagination/count/output limits and wrong-scope responses.

Done when:

- [ ] Manual and automated fixtures expose complete project-visible semantics with no unrelated or broader reads, and all category/status permutations are distinguishable.

### Step 2 - Implement the required domain investigations

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Extend routing with reviewed metadata/network and volume/attachment workflows, not model-selected arbitrary commands. Plans declare expected capabilities, related-read categories and output/evidence requirements.
- [ ] Preserve the guest `169.254.169.254` → Neutron proxy/metadata agent → Nova metadata API model. Healthy Neutron agents alone never prove the Nova listener is available.
- [ ] Correlate permitted server/network and volume observations; where host/operator capabilities are unavailable, name the missing evidence and return partial/inconclusive findings rather than fabricating a failure domain.
- [ ] Preserve the NoValidHost distinction between observed fault and confirmed scheduling/capacity/Placement cause. Supporting higher-visibility tools follow Phase 06, not implicit privilege escalation.
- [ ] Reuse evidence review for contradictory facts, absent references, collection failures and stale observations. Bounded additional collection must stay within current plan/scope/budget, otherwise require renewed approval.
- [ ] Keep recommendations plain-language/manual and tied to approved curated runbooks; do not copy runnable remediation from source documents into reports/prompts.

Done when:

- [ ] Offline sufficient-evidence and unavailable-tool variants for boot, metadata/network and volume attachment yield supported or honestly limited findings, with no confidence-only diagnosis.

### Step 3 - Enforce multi-server dependencies and qualified synthesis

Estimate: **2–4 engineer-days / 12–24 hours**.

- [ ] Extend exact-approved planning to several explicit targets while retaining original/resolved identifiers, cloud/project, child links, capabilities and total budgets.
- [ ] Validate graph types/dependencies/scope before dispatch; schedule only ready tasks with successful required dependencies. Keep sequential scheduling until separately justified.
- [ ] Preserve pending/ready/running/paused/completed/failed/blocked/cancelled task states and per-target outputs. Required dependency failure blocks dependent success; any permitted partial-report path must label blocked coverage explicitly.
- [ ] Aggregate project/task/tool/model/review usage and limits so child tasks cannot reset budgets or authorizations; cancelled/expired/revoked parent work cannot dispatch new child calls.
- [ ] Propagate pause/resume, uncertain calls, lifecycle references and current approval checks through child investigations; serialize/reject conflicting writers and preserve completed work.
- [ ] Produce cross-task synthesis only when required dependency outcomes are known. Failed/unavailable evidence cannot produce an unqualified successful diagnosis or an unsupported shared-cause claim.

Done when:

- [ ] Multi-target partial-failure/resume fixtures retain isolated evidence, correct ready/blocked transitions and qualified synthesis without calls outside approved targets or aggregate budgets.

### Step 4 - Expand evaluation and keep specialists conditional

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Extend versioned offline scenarios with metadata listener failure, Neutron failure, volume-attachment symptoms, NoValidHost sufficient/unavailable evidence, permission denial and multi-server partial failure.
- [ ] Score task success, appropriate tool selection, unnecessary calls, unsupported claims, safety violations, elapsed time and known/unknown usage. Score expected inconclusive separately from fabricated diagnosis.
- [ ] Verify scopes/budgets/relationships through public CLI/orchestrator seams, including hostile nested/delegated-like requests without enabling real specialists.
- [ ] Make specialist capabilities disabled and unreachable by default and record that AC-020 follows its disabled branch. If enabling is later proposed, require separate authorization, restricted task/context/tool/budget contracts and a versioned quality/cost/latency comparison against this baseline.
- [ ] Run applicable manual/automated catalog regressions and record changed semantics/version compatibility; publish exploratory corpus/rubric results for G5 agreement, not tuned release pass thresholds.

Done when:

- [ ] Required domain/project scenarios run without live credentials or inference, specialist execution is demonstrably disabled, and evaluation results reveal missing evidence instead of rewarding invention.

## 05.6 Phase Definition of Done

- [ ] Full project-visible manual and automated catalog satisfies required fields, relationships, category statuses and bounds.
- [ ] All three required domain workflows pass sufficient-evidence and unavailable-capability fixtures.
- [ ] Multi-server planning, dependencies, aggregate limits, child recovery and cross-task review preserve per-target provenance and honest partial outcomes.
- [ ] Every new diagnostic has a reviewed contract, classification, offline safety and scenario coverage.
- [ ] Specialists, parallel scheduling and broad discovery remain disabled; live/operator/host requirements remain explicitly outstanding where not yet validated.

## 05.7 Risks

| Risk | Mitigation |
| --- | --- |
| Tenant-visible APIs return shared/foreign resources | Explicit visibility and response relationship checks; no approval by mere discoverability. |
| Empty results hide permission errors | Per-category result states and no-success failure rule. |
| Task engine labels failure as a completed diagnosis | Independent lifecycle/outcome, blocked dependencies and coverage-aware synthesis. |
| Metadata cause inferred from agent health | Require direct relevant listener/path evidence or a named limitation. |
| Existing multi-agent code is activated prematurely | Test disabled feature boundary; separate evaluated proposal for any enablement. |

## 05.8 Proposed Requirement Coverage and Handoff

| Requirement / AC source | Proposed phase responsibility | Existing behavior / deferral | Risk or unapproved decision |
| --- | --- | --- | --- |
| FR-012/023–FR-025/027/044; AC-005/014/027 | Project-visible catalog and all domain workflows | Higher-visibility/host tools in 06 | G3 exact reader and relationship scope. |
| FR-005–FR-006/009–FR-014; AC-001/003/004/006 | Exact multi-target approval, dependencies and child-state handling | Existing project engine only a reuse seam | Full nested constraints and aggregate budgets required. |
| FR-016–FR-020; AC-010 | Cross-domain/per-target review and qualified synthesis | No automatic archive or stale-memory promotion | Semantic support needs fixtures, not reviewer agreement alone. |
| FR-036–FR-040; AC-020/021/022/025 | Disabled specialists, expanded corpus and metrics | Optional enablement deliberately not included | G5 thresholds pinned before candidate evaluation. |

Proposed handoff to Phase 06: complete project-visible catalog, required domain fixtures, capability gaps, multi-server baseline and explicit host/operator evidence needs. Independent scope readiness and a separate approved task contract are still required; this phase file is neither.
