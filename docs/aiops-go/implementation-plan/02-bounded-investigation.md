# 02. Bounded Investigation

## 02.1 Goal

Prove one useful single-server investigation from explicit intent and exact approval to a reviewed evidence-linked report, with no model-owned authority.

```text
goal + scope -> validated plan -> exact approval -> bounded agent/gateway -> evidence review -> report
```

## 02.2 Estimate

Total: **6-10 engineer-days / 36-60 focused hours**.

## 02.3 Scope

Included: CLI entry/review, original/resolved targets, structured decisions, bounded single-agent/workflow execution, initial checkpoints, reports, model adapters/disclosure/isolation and correlation. Primary requirements: FR-001–FR-009, FR-019–FR-020, FR-031–FR-034, FR-039–FR-040; NFR-001–NFR-003, NFR-006, NFR-012–NFR-013. Evidence: AC-001–AC-003, AC-016–AC-018, initial AC-010/AC-022.

Excluded: full multi-server scheduling, production-safe resume/migration (Phase 03), broad domain coverage (Phase 04), specialist agents and unapproved remote inference. Unsafe legacy resume must be gated off until Phase 03, not silently retained as supported.

## 02.4 Assumptions

- [ ] Phase 01 supplies the only diagnostic dispatch path and identifier/relationship contract.
- [ ] Existing planner, structured client and compute workflow are extended rather than replaced wholesale.
- [ ] Fake models establish default acceptance. Remote provider/model, outbound classes and enforced isolation require operator approval before enablement.
- [ ] Single-server and project proposals both use explicit review in this delivery, so a natural-language goal is never mistaken for dispatch consent.

Dependency: Phase 01. Durable resume and full review are completed in Phases 03-04; this phase is a tracer slice, not the releasable MVP.

## 02.5 Ordered Tasks

### Step 1 - Preserve intent through validated plan approval

Estimate: **2-3 days / 12-18 hours**.

- [ ] Accept explicit cloud/project, target identifiers, original goal, capability/profile set and finite budgets as application data. Avoid reparsing model prose as target authority.
- [ ] Resolve canonical UUIDs/supported exact names within disclosed scope; reject ambiguity/missing matches with actionable guidance. Necessary resolution reads require their own scoped authorization/audit before proposal execution.
- [ ] Extend structured plans with ready/needs-input/unsupported disposition, tasks/dependencies, capabilities, scope, limits and expected output. Validate schemas and semantics before review; non-ready plans dispatch no diagnostic tasks.
- [ ] Preview the canonical validated plan and bind approval to its digest, scope and relevant policy identity. Changed targets, capabilities, budgets or plan content invalidate consent; cancellation/EOF/no approval starts nothing.
- [ ] Preserve existing exact-digest review and goal/identifier regressions. Reject duplicate IDs, missing dependencies, cycles, unknown task types and extra targets before execution, even while the first accepted graph is small.
- [ ] Create a versioned investigation record with correlation IDs, original/resolved identity, plan/approval, limits and lifecycle. Separate operational lifecycle from supported/partial/inconclusive diagnostic outcome from the start.

Done when:

- [ ] CLI fixtures demonstrate ready approval and all non-execution paths, including changed-plan approval, while recording zero unintended target calls (AC-001–AC-002).

### Step 2 - Execute and review a finite investigation

Estimate: **2-4 days / 12-24 hours**.

- [ ] Adapt the agent/workflow to carry application-owned scope to all baseline, nested and related-resource calls. Test an approved server-A plan whose downstream agent requests server B or another project/profile.
- [ ] Structurally and semantically validate every model control response. Invalid JSON, extra fields, unknown decisions/tools and contradictory completion states cause bounded correction or visible failure, never text execution.
- [ ] Make the orchestrator own transitions, attempts, deadlines and completion. Permit retries only for classified transient reads; denials and invalid input stop or become named evidence gaps, never stronger-credential retries.
- [ ] Enforce finite task/step/tool/retry/time/context/output budgets and supported token/cost caps. Stop repeated unproductive requests, cancellation, insufficient evidence/capabilities and exhausted budgets with persisted/reportable reasons.
- [ ] Checkpoint before/after significant transitions; propagate failed writes and stop unsafe continuation. Mark interrupted work clearly; do not promise resumability until Phase 03 recovery tests pass.
- [ ] Record timestamped observation IDs with call provenance and sanitized scope/status. Link claims to evidence and keep knowledge citations distinct, even if the first slice uses no retrieval.
- [ ] Render scope, coverage, facts, interpretations, hypotheses, gaps/contradictions, review concerns, manual next steps and usage. Completion of execution must not imply cloud health or confirmed root cause.
- [ ] Add initial deterministic reference/coverage checks before finalization. Unsupported claims produce bounded in-scope follow-up or an inconclusive/partial report; confirmation needs direct evidence. Full semantic/contradiction fixtures follow in Phase 04.
- [ ] Expose progress, pause/cancel, terminal reasons and versioned report export/inspection. Preserve available local evidence when model/report generation fails; writes remain confined to protected application storage.

Done when:

- [ ] A fake-model server/boot case yields a traceable report, while malformed decisions, scope escape, unproductive loops and budget exhaustion terminate safely with auditable evidence.

### Step 3 - Constrain inference and prove degraded operation

Estimate: **2-3 days / 12-18 hours**.

- [ ] Normalize enabled text/structured adapters behind cancellation, timeout, safe errors and usage contracts; identify unavailable token/cost fields as unknown, not zero.
- [ ] Require explicit selected provider/model and outbound data-class authorization covering goals, observations, summaries, memory and knowledge. Destination or disclosure-policy changes require renewed consent; no silent provider switch.
- [ ] Apply redaction/minimization before provider calls, including error/debug paths; keep authentication opaque to tools/reports. Untrusted goals/logs/retrieved text cannot modify provider choice or disclosure.
- [ ] Specify and implement the selected runtime's enforceable credential/filesystem/tool/network isolation. Model subprocesses cannot read cloud/SSH credentials or invoke independent shell/file/network tools to bypass dispatch. If isolation cannot be established, keep that adapter disabled.
- [ ] Test scrubbed environments, denied credential/file access, disabled independent tools, destination/disclosure revocation, cancellation and hung subprocess cleanup. Separate local isolation tests from deployed egress proof required in Phase 07.
- [ ] Verify provider outage or absent/revoked authorization preserves manual diagnostics and local inspect/export, retains state and stops model-dependent work without switching provider.
- [ ] Extend offline fixtures with secret-bearing goals, hostile tool text, remediation intent, planning failures, unavailable capabilities and budget exhaustion. Record project/task/investigation/tool/model correlations, attempts and terminal outcomes without hidden reasoning traces.

Done when:

- [ ] Each enabled adapter passes AC-016–AC-018 locally; no unauthorized provider request occurs, and any pending deployed isolation/egress evidence explicitly blocks remote enablement.

## 02.6 Phase Definition of Done

- [ ] One scoped single-server CLI investigation traverses approval, bounded execution, initial evidence review and versioned report export using fakes.
- [ ] No nested call escapes Phase 01 authorization; failures never become invented evidence or privileged fallback.
- [ ] Model-dependent work can stop without losing permitted manual diagnostics or local inspection.
- [ ] Incomplete resume/domain/review capabilities are explicitly gated and assigned to Phases 03-04.

## 02.7 Risks

| Risk | Mitigation |
| --- | --- |
| Exact approval is mistaken for call authorization | Carry scope to every dispatch and test post-approval scope escape. |
| A provider runtime has hidden tools | Disable unsupported adapters until OS/tool/network isolation is proven. |
| Budget/accounting gaps imply free execution | Conservative finite call/time/context limits and explicit unknown usage. |
| Plausible output passes as confirmed diagnosis | Reference checks, direct evidence requirement and partial/inconclusive outcomes. |
| Legacy resume bypasses new state/policy contracts | Disable unsupported resume paths until Phase 03 acceptance. |
