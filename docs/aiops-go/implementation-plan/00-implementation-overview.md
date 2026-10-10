# 00. Implementation Plan Overview

This plan replaces the previous toolbox/advisory implementation plan with delivery of the approved [OpenStack investigation and orchestration PRD](../prd.md). The canonical source is now `docs/aiops-go/prd.md`, formerly `prd-v2.md`. The user approved its product direction in the planning conversation; its remaining draft wording does not authorize deployment or imply verified safety. This plan does not modify the PRD.

**Project mode: Existing Project with Partial Implementation.** All work remains unchecked until verified. Approval of this plan does not itself authorize coding, live cloud calls, credential provisioning, inference, staging, or deployment.

## 00.1 Directory Name

```text
docs/aiops-go/implementation-plan
```

One ordered delivery plan lives beside its requirements authority. The previous phase files are superseded, not a parallel backlog. Their useful safety, manual-tool, host, MCP, and rollout work is integrated below; their old requirement mappings and completion assumptions must not be reused.

### Observed reuse baseline

Source inspection for this plan found:

| Evidence inspected | Reuse opportunity and remaining obligation |
| --- | --- |
| `aiops/internal/tools/registry.go`, `Registry.Execute` | Named dispatch rejects unknown tools, but its interface does not carry explicit investigation scope. Enforce scope at actual dispatch, including nested calls. |
| `aiops/internal/planning/review.go`, `ReviewAndStart`; planning test cases | Preserve exact-digest review, non-ready dispositions, original goal, UUID/exact-name behavior; extend policy/scope bindings rather than replacing review. |
| `aiops/internal/workflow/server_incident.go`, routing and result validation | Compute path exists; network/storage route to unsupported. Nonempty completed-agent output is not sufficient evidence review. |
| `aiops/internal/project/engine.go`, run/pause/readiness paths | Sequential dependency scheduling and checkpoints exist; several failure/pause saves discard errors. Harden failure propagation, partial reporting, and recovery. |
| `aiops/internal/agent/filestore.go`, memory lookup and atomic writer | Protected temporary files and atomic replacement are useful foundations. Subject matching alone does not establish cloud/project isolation, schema compatibility, or concurrent-writer safety. |
| `aiops/internal/knowledge/loader.go`, `LoadDir` and chunk creation | Reuse bounded chunks and source identities; directory discovery is not content approval, scope control, or safe ingestion. |
| `tests/ai_ops/test_tool_runner.py`, fixed-argv fixtures; `test_mcp_server.py`, registry-derived discovery/schema fixtures | Reuse offline adapter seams and expected semantics; inspected tests were not run for planning. |
| `ansible/ai_ops_runtime/`, `ansible/ai_ops_assistant/`; root and Go Makefiles | Multiple runtime lineages require an ownership decision. Preserve existing Go build and Molecule/deployment validation paths. |

No runtime, credential, deployed-policy, model, or test readiness is asserted from these observations. Implementation should extend existing module responsibilities through versioned contracts, not follow brittle file-by-file instructions.

## 00.2 Estimation Rules

```text
1 engineer-day = about 6 focused engineering hours
```

Ranges assume one experienced engineer with reasonable access. They include design, reuse assessment, implementation, offline tests, documentation, and evidence capture; exclude waiting for approvals/access, procurement, incidents, and provider/infrastructure provisioning delays. Re-estimate after Phase 01 if inherited defects or the runner-ownership decision materially change work. Step ranges sum to their phase ranges.

## 00.3 Phase Summary

| Phase | File | Goal | Estimate |
| --- | --- | --- | --- |
| 00 | `00-implementation-overview.md` | Execution, traceability, and gates | Documentation only |
| 01 | [Safety boundary and manual slice](01-safety-boundary-and-manual-slice.md) | One reviewed, scoped, audited diagnostic path | 6-10 days / 36-60 hours |
| 02 | [Bounded investigation](02-bounded-investigation.md) | Exact approval to evidence-linked single-server report | 6-10 days / 36-60 hours |
| 03 | [Durable state and knowledge](03-durable-state-and-knowledge.md) | Safe resume, scoped memory, curated retrieval | 5-8 days / 30-48 hours |
| 04 | [Domain and project orchestration](04-domain-and-project-orchestration.md) | Network/storage evidence, dependency-aware projects, review | 6-10 days / 36-60 hours |
| 05 | [Gated host and MCP integrations](05-gated-host-and-mcp-integrations.md) | Independently enabled higher visibility and protocol parity | 4-7 days / 24-42 hours |
| 06 | [Evaluation and operational readiness](06-evaluation-and-operational-readiness.md) | Versioned quality gates, telemetry, readiness and lifecycle | 4-7 days / 24-42 hours |
| 07 | [Acceptance and rollout](07-acceptance-and-rollout.md) | Authorized deployed evidence and rehearsed recovery | 3-5 days / 18-30 hours |

Milestones:

- Manual diagnostic foundation, Phase 01: **6-10 days / 36-60 hours**, offline first; live use remains gated.
- First investigation tracer slice, Phases 01-02: **12-20 days / 72-120 hours**. Not the complete product MVP.
- Stateful/domain engineering slice, Phases 01-04: **23-38 days / 138-228 hours**.
- Releasable core MVP, Phases 01-04, 06-07: **30-50 days / 180-300 hours**; host/MCP/specialists disabled with explicit limitations.
- Full planned delivery including Phase 05: **34-57 days / 204-342 hours**.

Phase 05 may be skipped only with its capabilities disabled and acceptance recorded as optional-disabled, not passed. If enabled, its tests and applicable deployed gates are mandatory. Specialist implementation, advanced retrieval, parallel scheduling, and network MCP are not included in these estimates.

## 00.4 Recommended Build Order

1. Decide authoritative runtime/registry ownership and prove one safe named diagnostic offline.
2. Extend that same slice through explicit target selection, plan review, bounded agent execution, and a reviewed report using fake inference first.
3. Make the slice recoverable and its memory/retrieval safe before expanding orchestration.
4. Add metadata/network and volume cases, then dependency-aware multi-server synthesis with honest partial outcomes.
5. Independently enable host/operator and local MCP capabilities only after their prerequisites pass; core work may continue without them.
6. Consolidate the scenario corpus, quality gates, operations, and startup checks. Seed evaluations in Phase 01 and add fixtures in every phase; do not postpone safety tests until Phase 06.
7. Release only the accepted capability matrix, after separate permission for live checks and any inference.

Each phase must be designed into compile-safe, thin vertical chunks before coding: contract/fake seam, behavior, negative fixtures, targeted regression, then handoff. Do not build every abstraction before proving the first end-to-end slice. Sequential local scheduling is the baseline; no background service or queue is required.

### Decisions and blocking gates

| Decision | Owner/approval | Due / consequence if unresolved |
| --- | --- | --- |
| Authoritative runtime, registry, Go-to-runner versus Go-owned boundary, compatibility versions | Maintainer | Phase 01 Step 1; blocks real adapters, not fixture design |
| Observer placement, cloud/project, dedicated reader policy, approved endpoints | Operator/security owner | Phase 01 design; blocks live diagnostics until Phase 07 evidence or an explicitly authorized equivalent early gate |
| Related-resource authorization and separate project-wide/host visibility | Operator/security owner | Phase 01; unreviewed relationships denied |
| Initial provider/model, outbound data classes, isolation and enforceable egress | Operator/security owner | Phase 02; remote inference disabled until approved and validated |
| Retention, maximum data volume, freshness, export permissions | Data owner | Phase 03; production persistence/exports blocked pending policy |
| State version/conversion, locking, uncertain-call replay semantics | Maintainer | Phase 03; incompatible state rejected, never silently migrated |
| Supported domain evidence, including Placement/capacity and attachments | Maintainer/operator | Phase 04; unimplemented subdiagnostics explicitly unavailable |
| Initial MCP client/protocol/local transport and host aliases | Maintainer/operator | Phase 05; corresponding capabilities disabled until decided |
| Corpus/rubric and quality, latency, token/cost, unnecessary-call thresholds | Product/release owner | Phase 06 before release measurements; model rollout blocked |

Go core, local protected persistence, sequential scheduling, lexical retrieval, and one agent with an evidence-review stage are planning defaults, not permission to choose deployment details silently.

## 00.5 Cross-Phase Principles

- [ ] Application-owned scope and deterministic dispatch authorization apply to manual, nested, resumed, delegated, SDK, script, and MCP calls. Model fields never choose credentials or policy.
- [ ] Approvals cover diagnostic plans/scope/disclosure only. No mutation, generic shell/SSH/CLI/file/database tool, privileged fallback, or remediation execution exists.
- [ ] Every important transition is checkpointed and correlated. Required authorization, audit, or control failures stop new dispatch and are visible locally.
- [ ] Every call/run has finite budgets, cancellation, bounded output/context, and reviewed retry rules. Denials and invalid requests are not transient retries.
- [ ] Sanitize and minimize before any report, storage, model context, export, or telemetry. Treat goals, logs, knowledge, summaries, and delegated outputs as untrusted data.
- [ ] Keep fresh evidence, working summaries, historical memory, and reference knowledge distinct. Model agreement and tool exit success do not prove root cause.
- [ ] Preserve original/resolved identifiers, manual diagnostics, and existing automation. Version incompatible tools, exports, and state with tested rollback.
- [ ] Provider failure never disables permitted local diagnostics or inspection; no silent provider switch. Remote opt-in is not credential isolation or egress enforcement.
- [ ] Default tests run offline with no credentials. Live checks, mutation-denial probes, model evaluations, and deployment require separate explicit authorization.
- [ ] Tests verify observable behavior at CLI/orchestrator/adapter boundaries, not private helper layouts. No task is complete from source presence alone.

## 00.6 Recommended MVP Slice

```text
explicit goal + cloud/project + exact server targets + budgets
  -> scoped resolution -> ready/needs-input/unsupported plan
  -> preview + exact approval -> deterministic ready-task scheduling
  -> bounded agent -> call-boundary authorization -> sanitized evidence + audit
  -> checkpoint / pause / current-policy resume
  -> curated citations + evidence review -> supported/partial/inconclusive report
  -> versioned export and provider-independent inspection
```

Start with one server, then demonstrate metadata/network, project-visible attachments, and two-server partial failure through the same contracts. Missing host/capacity evidence is a named limitation, never invented confirmation. Manual named tools remain available without inference. No web UI, general-purpose coding agent, autonomous surveillance/remediation, new provider gateway, local model deployment, or replacement lab automation is included.

## 00.7 Tracking Format

```text
- [ ] Not implemented or not verified
- [x] Implemented and verified with recorded evidence
```

For each step record owner, revision, commands/procedures, environment, redacted evidence location, supported versions, and limitations. Acceptance states are pass, fail, blocked, or optional-disabled. Record offline, model-backed, and deployed evidence separately. Checkboxes are not carried forward from the superseded plan.

### Functional requirement ownership

Ranges below are inclusive and refer only to the current canonical PRD.

| Requirements | Primary phase(s) | Verification responsibility |
| --- | --- | --- |
| FR-001–FR-005 | 02, 03, 04 | CLI modes, target identity, dispositions, exact approval, inspect/resume/export |
| FR-006 | 04 | Graph rejection, readiness, dependency success |
| FR-007–FR-009 | 02, 04 | Structured control, bounded loops, application-owned execution |
| FR-010–FR-011 | 01 | Dispatch authorization and reviewed related reads, regressed in all later phases |
| FR-012–FR-013 | 04 | Domain workflows and per-target project synthesis |
| FR-014–FR-018 | 03 | Durable scoped state, freshness, retrieval and untrusted context |
| FR-019–FR-020 | 02, 04 | Evidence-linked reports, full review and partial outcomes |
| FR-021–FR-022 | 01, 07 | Isolation/profile design and deployed verification |
| FR-023–FR-024 | 01 | Registry, fixed argv, SDK parity |
| FR-025 | 01, 04, 05 | Catalog baseline, attachments, gated operator/log evidence |
| FR-026 | 05 | Restricted hosts, operations, windows and output |
| FR-027–FR-030 | 01 | Result/audit/redaction and permanent mutation denial |
| FR-031–FR-034 | 02 | Model contracts, disclosure/isolation and degraded operation |
| FR-035 | 05 | MCP parity, curated resources and diagnostic prompts |
| FR-036 | 06 | Disabled-by-default specialist gate; future enablement requires isolation and measured benefit |
| FR-037–FR-038 | 06 | Versioned offline evaluation and metrics |
| FR-039–FR-040 | 02, 06 | Correlation and finite budgets from first run; consolidated operational reporting |
| FR-041–FR-042 | 06, 07 | Startup, lifecycle, revocation and rollback |

### Non-functional requirement ownership

| Requirements | Primary phase(s) | Gate |
| --- | --- | --- |
| NFR-001–NFR-003 | 01, 02, 07 | Zero unauthorized execution/disclosure, isolation, bounded cancellation |
| NFR-004–NFR-005 | 03 | Atomic/versioned state, single writer, scoped evidence/memory |
| NFR-006 | 02, 06 | Explicit capability degradation; fail closed for required controls |
| NFR-007 | 04, 06 | Direct support for findings; semantic review corpus |
| NFR-008–NFR-009 | 06 | End-to-end provenance, measured distributions and pre-agreed thresholds |
| NFR-010–NFR-011 | 01, 07 | Versioned adapter/state compatibility and extension regressions |
| NFR-012 | 02, 03, 07 | Data minimization, disclosure, storage/retention, egress evidence |
| NFR-013 | 02, 04 | Clear proposal/execution and completion/confidence distinction |
| NFR-014–NFR-015 | 06, 07 | Reproducible install, offline tests, separate live acceptance |

### Acceptance evidence ownership

| Acceptance criteria | Owning phase | Required evidence |
| --- | --- | --- |
| AC-001–AC-002 | 02 | CLI review/identity fixtures; zero unapproved task execution |
| AC-003 | 02, 04 | Malformed decisions, unproductive loops, graph rejection and bounds |
| AC-004 | 01, 03, 04 | Dispatch denial including nested/resumed scope escape; related-read positives |
| AC-005–AC-006 | 04 | Domain and multi-target partial-failure scenarios |
| AC-007–AC-009 | 03 | Crash/recovery, context classes, curated retrieval and secret/injection fixtures |
| AC-010 | 04 | Missing, contradictory and unsupported-claim review fixtures |
| AC-011 | 07 | Authorized deployed runtime/profile and read/mutation-denial evidence |
| AC-012 | 01, 05 | SDK/script/local rejection and MCP parity |
| AC-013 | 05, 07 | Restricted host fixtures plus deployed evidence if enabled |
| AC-014–AC-015 | 01 | All statuses, audit failure, canaries and no mutation execution |
| AC-016–AC-018 | 02, 07 | Adapter contracts, isolation negatives, outage/revocation; deployed isolation if enabled |
| AC-019 | 05 | Registry-equivalent discovery/resources/prompts and call parity |
| AC-020 | 06 | Explicit specialist-disabled record, or separately approved comparison and isolation evidence |
| AC-021–AC-022 | 06 | Versioned offline results, correlation, budgets and unknown usage |
| AC-023–AC-025 | 07 | Readiness/rollback, compatibility regression and pinned release record |

## 00.8 Definition of MVP Done

```text
approved scoped investigation -> bounded authorized collection -> durable evidence
  -> dependency-aware review -> truthful report -> safe resume/export
  -> offline acceptance + separately authorized deployed acceptance
  -> repeatable operation and rollback without changing lab workloads
```

The releasable core includes the Phase 04 domain/project slice and Phase 06-07 quality/operations gates, not merely a working chatbot or toolbox. A second operator can execute, interrupt, resume, inspect, and export the supported workflow using documented controls. No manual repair of internal state is needed on the normal path; human plan and disclosure approval remain intentional steps.

All applicable deterministic safety, graph, approval, recovery, and evidence tests pass. Release thresholds and capability matrix are pinned before measurement. Optional-disabled host/MCP/specialists remain visible, and any diagnosis requiring unavailable evidence is partial/inconclusive. Fixture success never substitutes for deployed isolation, policy, egress, or credential validation.
