# 00. Implementation Plan Overview

**Roadmap authority:** PROPOSED decomposition; not an approved ADR, task contract, or execution authorization.
**Roadmap status:** ROADMAP_READY_FOR_SCOPE_REVIEW
**Authoritative sources and revision:** [Delivery 1 PRD](../prd.md), status `scope_ready`, owner-approved product scope as stated in the source; Git blob `37a7a291d27934a6fa19d71eb4a7f7e250df786f` at commit `e29fa87e293246c187f5b01604e6f012dfbb4761`. No independent approval of these phase boundaries was supplied.
**Repository/project state:** Existing project with partial implementation. Inspected base commit `e29fa87e293246c187f5b01604e6f012dfbb4761`, tree `2ed028bf34f68a75f63d885b0967df6c80852089`; tracked working tree initially clean and output directory empty.

This directory translates the PRD into proposed phases within the same product Delivery 1. Phase numbers are not new product deliveries or learning stages. Each selected implementation delivery needs separately bounded specifications, review, approval, and implementation preflight.

## 00.1 Directory Name and Evidence Baseline

```text
docs/ai-ops-go/implementation-plan
```

The directory is the user-requested product roadmap location. It contains one overview and eight ordered phase proposals, each with a goal, scope, assumptions, estimates, checkable tasks, verification obligations, and definition of done.

### Sources inspected

| Source | Observed evidence and limits |
| --- | --- |
| [PRD](../prd.md), complete document | Governs FR-001–FR-050, NFR-001–NFR-015, AC-001–AC-031, product exclusions, implementation form, rollout, and six open decisions. Product scope approval is not implementation or deployment approval. |
| [Learning baseline](../aiops-baseline.md#our-practical-curriculum), final Stage 0–14 curriculum | Conceptual supporting source, blob `d3049659d9d40b6b7cb7012f57d02cbe579693a8`; relevant curriculum inspected, not every educational example. Lessons and assessments are outside this roadmap. |
| [README](../../../README.md#architecture-summary) and [architecture study](../../architecture.md) | Existing OpenStack lab, service placement, management network, Vagrant/Ansible operations and Molecule patterns. Architecture prose is context, not approval of a new isolation design. |
| Go command wiring and build | `aiops/cmd/openstack-project/main.go` composes model adapters, server/flavor/port tools, file stores, lexical retrieval, workflow and project engines. `aiops/Makefile` builds four executables today; consolidation is required, not already achieved. `aiops/go.mod` declares Go 1.27.1 and Gophercloud v2.14.0; installed toolchain availability was not checked. |
| Existing execution and review | `internal/tools/registry.go` dispatches registered names without an explicit authorization context. `internal/scopedtools/broker.go` has narrower role/project/target checks but is not wired into the inspected project CLI. `internal/planning/prepared.go` and `review.go` implement validated snapshots and digest review; full lifetime/policy binding is not established. |
| Existing workflow and state | `internal/workflow/server_incident.go` implements compute routing and a review stage; other domains explicitly report no workflow. `internal/agent/runtime.go` supplies bounded loops. File state uses restricted files and temporary-file replacement, but concurrency, uncertain-call recovery, quota, retention and complete fail-closed persistence are not established. Some engine failure paths discard save errors. |
| Identifier and knowledge behavior | `internal/tools/get_server.go` filters exact-name matches but trims input whitespace; PRD literal-name semantics require compatibility repair. `internal/knowledge/loader.go` recursively discovers text/Markdown; discovery is not curated-source approval. |
| Model and test seams | Codex/Pi adapters expose text/structured contracts; Pi has version/configuration and request-authorization controls. Existing flags and environment filtering do not prove OS isolation. Planner, identifier, port, scoped-broker, team and delegation tests exist; selected planner tests were read. No existing test result is accepted as current evidence. |
| Existing verification | `aiops/Makefile` has `fmt`, `test`, `build`; root Makefile has lab validation/smoke targets. `.github/workflows/ansible-sanity-test.yml` currently uses Python 3.12/3.13/3.14 and does not establish Go coverage; this supersedes older architecture prose about its matrix. |
| Metadata reference | The symptom/path and investigation sections of [metadata troubleshooting](../../troubleshooting/01-openstack-instance-metadata-503.md) explain guest → Neutron proxy → Nova metadata API. The document includes sensitive configuration examples and operational commands; it is not automatically approved retrieval input or a diagnostic execution recipe. |

Legacy Python/shell AI-OPS deployment and test paths were discovered, not certified or adopted. Archived documents were not read or treated as current authority. No credentials, local `.env`, deployed environment, live reader policy, installed harness, or remote provider was inspected. No tests, builds, live diagnostics, or model calls were run during planning.

## 00.2 Estimation Rules

```text
1 engineer-day = about 6 focused engineering hours
```

Ranges assume one experienced Go/infrastructure engineer with reasonable access. Estimates include implementation, focused tests, documentation, in-scope repair and validation effort, but exclude access/procurement, external approvals, credential issuance delays, provider availability and unrelated incidents. Phase estimates are additive; design infeasibility or newly discovered incompatibilities require re-estimation, not relaxed controls.

## 00.3 Phase Summary

Every phase boundary and dependency below is **PROPOSED**.

| Phase | File | Goal | Estimate |
| --- | --- | --- | --- |
| 00 | `00-implementation-overview.md` | Explain roadmap, sources, gates and traceability | Documentation only |
| 01 | [Safety foundation and manual diagnostics](01-safety-foundation-and-manual-diagnostics.md) | One runtime, one reviewed gateway, protected new store and a safe manual server path | 10–15 days / 60–90 hours |
| 02 | [Inference isolation and manual analysis](02-inference-isolation-and-manual-analysis.md) | Both inference-only harnesses, disclosure/egress controls and copy-paste analysis | 7–11 days / 42–66 hours |
| 03 | [Approved bounded investigations](03-approved-bounded-investigations.md) | Exact-approved single-server evidence-to-report loop with deterministic limits | 8–12 days / 48–72 hours |
| 04 | [Durable state, knowledge and data lifecycle](04-durable-state-knowledge-and-data-lifecycle.md) | Safe resume, freshness, curated retrieval and full protected-data lifecycle | 8–12 days / 48–72 hours |
| 05 | [Domain workflows and project orchestration](05-domain-workflows-and-project-orchestration.md) | Complete project-visible catalog, domain workflows and multi-target synthesis | 9–14 days / 54–84 hours |
| 06 | [Restricted host and operator diagnostics](06-restricted-host-and-operator-diagnostics.md) | Go host diagnostics and gated higher-visibility catalog, with required host validation | 7–11 days / 42–66 hours |
| 07 | [Local MCP and approved client sessions](07-local-mcp-and-approved-client-sessions.md) | Stdio tools/resources/prompts and independently controlled standalone Pi sessions | 7–11 days / 42–66 hours |
| 08 | [Evaluation, acceptance and lab rollout](08-evaluation-acceptance-and-lab-rollout.md) | Pinned release criteria, deployed evidence, operations, recovery and rollback | 8–13 days / 48–78 hours |

Estimated full Delivery 1 MVP total:

```text
64–99 engineer-days
384–594 focused engineering hours
```

The first manual diagnostic increment is Phase 01; protected manual analysis follows Phase 02. The first bounded automated slice is Phases 01–03: 25–38 days / 150–228 hours. These are intermediate capabilities, not completion of Delivery 1 acceptance.

## 00.4 Recommended Build Order and Decision Gates

1. Establish the real execution boundary, audit durability, sanitization, storage limits and manual server diagnostics before exposing inference or MCP.
2. Prove independent model/credential isolation and both harness contracts through manual analysis, before allowing model-proposed tool calls.
3. Complete one approved server investigation against deterministic fixtures before expanding domain or orchestration breadth.
4. Harden resume and evidence/knowledge lifecycle before allowing historical reuse or cross-investigation references.
5. Extend project-visible evidence and dependency scheduling; keep specialist execution disabled.
6. Validate restricted host diagnostics and independently gate operator-reader capabilities. Start operator access preparation earlier if needed, without enabling tools early.
7. Add local MCP only over manually validated tools and the same gateway; independently verify session binding and client egress.
8. Close full offline, live-lab, real-model and operational acceptance before rollout. Evaluation fixtures start in Phase 01 and grow with each phase, not only here.

No phase may enable a feature before its applicable safety prerequisites work. Minimal checkpoint, retention, quota, audit and sanitization controls are required as soon as the relevant data or execution path exists; Phase 04 expands them rather than granting an earlier waiver. Live/manual/model/MCP checks require separate authorization and any applicable release thresholds; phase order is not such authorization.

### Open decisions retained from the PRD

These do not prevent proposing the dependency order. They do block their affected specifications, enablement or release until resolved. No concrete mechanism or environment is selected by this roadmap.

| Gate | PRD open decision | Required resolution / timing |
| --- | --- | --- |
| G1 | #1: OS identities, isolation, authenticated IPC, session-bound egress | Approve a feasible non-root Ubuntu 24.04 x86-64 design for the single executable in separated processes/security contexts. Gateway/model boundary before Phase 01 contract where applicable; harness proof before Phase 02 enablement; client binding/teardown before Phase 07. Escalate if no compliant design exists. |
| G2 | #2: acceptance environment | Operator supplies project, disposable test scope, host aliases, management endpoints, finite storage limit, installed/approved harness versions and provider/model combinations before relevant startup/live work. Never infer them from lab defaults or `.env`. |
| G3 | #3: reader policy and API relationships | Review project-reader API scope and bounded relationship rules before each tool. Independently validate any operator-reader access before enablement in Phase 06; unavailable safe operator-reader access is allowed, admin fallback is not. |
| G4 | #4: protected state and recovery | Approve versioned storage, durability/concurrency, quota, retention and audit-recovery design before Phase 01 persistent execution; complete active-reference/resume rules before Phase 04 exposure. Local file storage is a proposal, not a binding technology selection. |
| G5 | #5: release thresholds | Build exploratory corpus/baseline incrementally; owner agrees and pins corpus, rubric, capability matrix and quality/latency/token-cost/unnecessary-call thresholds before release-candidate evaluation and model-enabled rollout. No invented SLA. |
| G6 | #6: independent MCP verification | Approve how tools/resources/prompts, real standalone Pi interoperability, client security context and egress teardown will be independently validated before Phase 07 enablement. |

## 00.5 Cross-Phase Principles

- [ ] Go owns one authoritative diagnostic policy/registry and actual dispatch. Model proposals, plans, retrieved text and MCP requests cannot grant authority.
- [ ] One runtime executable does not mean one process, identity or trust domain. OS-enforced credential isolation, authenticated IPC and egress enforcement need independent negative evidence.
- [ ] Every dispatch rechecks cloud/project, target/relationship, capability/profile, approval and budgets; all entry points share the boundary.
- [ ] Diagnostic implementations are reviewed Go operations, not shell/SSH/OpenStack CLI passthrough or separately deployed diagnostic scripts/utilities. Operator-installed Codex/Pi prerequisites are inference-only exceptions.
- [ ] Persist sanitized audit intent before every allowed call; stop and withhold payloads on outcome-audit failure. Required checkpoint/storage failures stop execution too.
- [ ] Every long operation is finite and cancellable; sequential CLI execution is sufficient initially. No queue, service, database, parallel scheduler or new provider gateway is assumed.
- [ ] Cancellation, authorization/disclosure revocation and session teardown stop new work and explain irreversible prior reads/transmissions; they never claim to undo them.
- [ ] Separate operational lifecycle from diagnostic confidence. Missing, stale, denied and truncated evidence cannot prove health or root cause.
- [ ] Minimize and sanitize before any persistence or model/client disclosure. Alias outbound identifiers and default exports; protect necessary local identifiers.
- [ ] Preserve legacy files untouched and outside ingestion/cleanup. No legacy approval is valid in the new store.
- [ ] Tests verify external behavior with deterministic fakes first; source presence, static scans and model agreement are not safety or diagnosis proof.
- [ ] Deployment administration and live mutation-denial validation are separately authorized operator activities, never diagnostic tools.

## 00.6 Recommended MVP Slice

First useful automated increment, not the complete Delivery 1 MVP:

```text
explicit one-project server target + goal
  -> separately authorized bounded name lookup if needed
  -> approved destination/data disclosure + isolated tested harness
  -> structured plan preview + exact plan/scope/policy approval
  -> bounded server/flavor/related evidence through audited Go gateway
  -> evidence review -> supported or honestly limited report + protected export
```

Before this increment, prove named manual CLI diagnostics and sanitized paste-to-Go analysis with no automatic tool calls. The complete MVP adds durable resume, all required domains/catalog, multi-server orchestration, required restricted-host coverage, both harness integrations, local MCP and release operation.

## 00.7 Tracking Format

```text
- [ ] Proposed task, not verified complete
- [x] Implemented behavior with recorded verification evidence
```

All tasks are unchecked at roadmap creation. Later tracking should record candidate/contract identity, source revision, evidence command or record, result and remaining gap. A checkbox, estimate or roadmap status never grants implementation authority.

## 00.8 Definition of MVP Done

```text
safe observer + validated reader/host prerequisites
  -> manual diagnostics + protected manual Go analysis
  -> approved single/multi-server plans
  -> bounded boot / metadata-network / volume-attachment collection
  -> durable, scope-checked pause/resume + curated knowledge
  -> reviewed evidence-linked report, gaps and protected export
  -> approved standalone local/stdio Pi MCP interoperability
  -> pinned evaluation + both real harness checks + real lab investigation
  -> recorded operation, shutdown/recovery and rollback evidence
```

Completion requires all applicable AC-001–AC-031, not just a passing existing test suite. The normal approved diagnostic path is repeatable and observable without manual command composition; explicit approvals and operator-controlled provisioning remain intentional. Required host acceptance covers one controller and two compute nodes. Safe operator-reader access may remain unavailable, but the reviewed catalog and offline safety coverage are still required. Specialist roles may remain disabled.

## 00.9 Requirement-to-Phase Traceability

All locators below refer to [PRD requirements](../prd.md#functional-requirements), [NFRs](../prd.md#non-functional-requirements) and [acceptance criteria](../prd.md#acceptance-criteria). Phase numbers denote proposed responsibility, not accepted existing coverage. No existing behavior is accepted solely from inspection. Later acceptance integrates earlier evidence.

### Functional requirements

| PRD requirement | Proposed phase responsibility | Existing evidence / decision gap / disposition |
| --- | --- | --- |
| FR-001 | 01 manual; 02 analysis; 03 single execution/inspection/export; 04 resume; 05 project | Multiple CLIs exist; consolidate without losing safe operator workflows. |
| FR-002 | 01 scope context; 03 approved investigation record; 04 stored partitioning; 05 projects | Scope must survive nested execution and project changes; G1/G4. |
| FR-003 | 01 manual identity validation; 03 explicit pre-plan lookup authorization | Existing exact-name filter trims whitespace; repair semantics, audit bounded lookups; G3. |
| FR-004 | 03 validated ready/needs-input/unsupported planning | Existing planner is reuse candidate, not full acceptance. |
| FR-005 | 03 exact plan/policy approval, 24-hour default, invalidation/revocation; 04 resume | Existing digest review lacks established full lifetime contract. |
| FR-006 | 03 graph validation; 05 complete dependency scheduling | Existing planner/project seams; no generic DAG authority implied. |
| FR-007 | 02 common structured contract; 03 control-flow semantic validation | Existing adapters/planner need end-to-end negative fixtures. |
| FR-008 | 03 bounded agent, stop reasons | Existing step limit/duplicate-call controls; expand finite budgets. |
| FR-009 | 03 deterministic orchestration; 05 project propagation | Denial is not a retryable transient or privilege trigger. |
| FR-010 | 01 call boundary; 03 expiry/revocation; 04 resume; 07 sessions | Shared registry currently lacks explicit context; G1/G3. |
| FR-011 | 01 relationship rules; 03 approved related categories; 05 network expansion | Scoped broker is a pattern, not globally enforced gateway. |
| FR-012 | 03 server/boot; 05 metadata/network and volume/attachment; 06 host evidence | Non-compute workflows currently unsupported; no requirements deferred. |
| FR-013 | 05 per-target evidence and qualified synthesis | Project engine exists; failures must not imply full success. |
| FR-014 | 01 durable core records; 03 transition checkpoints; 04 full recovery; 05 child links | Restricted file store is partial; G4. |
| FR-015 | 04 terminal/resume/uncertain-call handling | Existing resume behavior is not accepted safe replay. |
| FR-016 | 03 evidence typing/freshness; 04 summaries/history and explicit refresh | 15-minute default, overrides and distinct event/collection times required. |
| FR-017 | 03 minimal explicitly curated runbook; 04 bounded lexical retrieval; 07 resources | Recursive file discovery is not approval; no archive/repository ingestion. |
| FR-018 | 02 model input; 03 decisions; 04 retrieval/memory; 05 nested outputs; 07 clients | Injection fixtures across all untrusted input classes. |
| FR-019 | 02 manual analysis; 03 reviewed reports; 04 exports/history; 05 synthesis | Plain-language manual recommendations, no runnable mutation commands. |
| FR-020 | 03 baseline evidence review; 05 cross-domain/task review | Existing review stage is a seam, not semantic correctness proof. |
| FR-021 | 01 observer design/readiness; 08 deployed proof | Ubuntu 24.04 x86-64, outside cloud/control plane, non-root; G1/G2. |
| FR-022 | 01 project-reader separation; 06 optional operator/restricted host; 08 live policy proof | No admin/root/service credentials or privilege fallback; G2/G3. |
| FR-023 | 01 reviewed registry/schema/prerequisites; 05/06 catalog extensions | Tool interface today lacks full declared contract. |
| FR-024 | 01 built-in Go execution; 06 fixed Go host mechanism; 07 same runtime MCP; 08 packaging proof | Existing four binaries and legacy scripts do not satisfy target; G1. |
| FR-025 | 01 server basics; 05 project/network/volume catalog; 06 scheduler/Placement/capacity and agent/log catalog | Higher visibility disabled if unsafe access; implementation/offline coverage still required. |
| FR-026 | 06 host aliases/fixed operations/windows/bounds; 08 acceptance integration | Required controller + two computes; storage-host scope excluded; G1–G3. |
| FR-027 | 01 result envelope; 05 per-category partial summaries; 06/07 parity | All eight statuses and safe truncation/error metadata required. |
| FR-028 | 01 durable intent/outcome handling; 04 acknowledged recovery; 07 parity | G4; withholding and locally visible audit gaps, not fabricated success. |
| FR-029 | 01 sanitization before storage; 02 outbound aliases; 04 lifecycle/export; 07 client disclosure | Protected necessary local identifiers remain sensitive. |
| FR-030 | 02 analysis refusal; 03 scoped “fix it” diagnostic plan; all tools | Never implement mutation, even after approval. |
| FR-031 | 02 both tested inference-only adapters; 08 real-model/release proof | External operator installation/authentication; no automatic updates or future SDK substitution. |
| FR-032 | 02 reusable destination/data policy; 03 investigation disclosure; 07 client egress | Consent, redaction and enforced egress are separate; G1/G2. |
| FR-033 | 01 security-domain design; 02 negative isolation proof; 08 deployed record | No credentials or bypass tools in model-facing context; G1. |
| FR-034 | 02 outage/revocation handling; 03/04 local inspection | No silent provider switch, late responses discarded. |
| FR-035 | 07 local/stdio tools/resources/prompts after trusted manual execution | Required, not optional; no network MCP. |
| FR-036 | 05 verify specialist roles remain disabled | Conditional feature intentionally not enabled; enabling later needs separate scope and measured comparison. |
| FR-037 | 01 fixture skeleton; 03–07 scenario growth; 08 complete versioned evaluator | Offline, no cloud/provider credentials; no replacement for live evidence. |
| FR-038 | 03 exploratory metrics; 05 full scenarios; 08 pinned scoring/report | Include supported inconclusive outcome, unsupported claims, calls, time and usage. |
| FR-039 | 01 tool correlations; 02 model; 03 task/review; 04 resume; 05 project; 08 release | No hidden reasoning or secrets in telemetry. |
| FR-040 | 01 tool limits; 02 model limits; 03 run budgets; 05 aggregated project; 07 session | Missing provider usage is unknown, never false zero. |
| FR-041 | 01 required/optional readiness; 02/04/06/07 extension; 08 operations | Capability matrix, actionable failures, required storage limit. |
| FR-042 | 01 minimum safe shutdown; 04 protected lifecycle; 08 rotation/recovery/rollback | Runtime rollback never changes workloads. |
| FR-043 | 01 single runtime/management reachability/identity; 02 harness prerequisites; 08 live proof | G1–G3; prefer application credentials when supported. |
| FR-044 | 01 tool-local validation/read-only mapping; 05/06 full catalog; 08 safety gate | Fixed reviewed implementation, minimized structured output; no full configurations. |
| FR-045 | 02 diagnostic-only instructions; 03 goal handling; 07 diagnostic prompts | Defense in depth, not authorization. |
| FR-046 | 01 named manual CLI; 02 protected paste-to-Go analysis/docs; 07 parity | No automatic calls in analysis; independent sharing outside product is not protected. |
| FR-047 | 07 approved bound client context/egress, one-hour lifetime, teardown | G1/G6; fresh session approval after disconnect/shutdown. |
| FR-048 | 01 applicable retention/cleanup baseline; 04 full reference-aware lifecycle | 30-day terminal / 90-day audit defaults; startup and runtime cleanup, G4. |
| FR-049 | 01 finite quota/disk failure; 04 confirmed deletion/protected exports; 08 operations | Never delete active-dependent evidence/unexpired audit; G2/G4. |
| FR-050 | 01 new versioned store; 04 isolation regressions; 08 rollback/legacy proof | Preserve old records untouched; migration is outside Delivery 1. |

### Non-functional requirements

| PRD requirement | Proposed phases | Evidence / decision gap |
| --- | --- | --- |
| NFR-001 Safety | 01–08 | Zero unauthorized executions, mutations or prohibited disclosures in deterministic safety suite. |
| NFR-002 Least privilege | 01/02/06/07; 08 proof | Independently enforced credential, state and route separation; G1–G3. |
| NFR-003 Bounded execution | 01/02/03/05/06/07 | Deadline, cleanup and no-later-dispatch tests at each enabled boundary. |
| NFR-004 Persistence | 01/03/04/05 | Atomic/transactional persistence and serialized/rejected writers; G4. |
| NFR-005 Isolation | 01/03/04/05/07 | Partition evidence, memory, knowledge and approvals by authorized scope. |
| NFR-006 Reliability | 01–08 | Fail closed on required dependency failure; optional profiles degrade honestly, required host acceptance remains mandatory. |
| NFR-007 Evidence quality | 03/04/05/06/08 | Direct evidence for confirmed cause; confidence/reviewer agreement is insufficient. |
| NFR-008 Observability | 01–08 | Correlation/provenance through all paths; denied non-execution duration is not applicable. |
| NFR-009 Performance/cost | 02/03/05/08 | Versioned counts/distributions and honest usage; pre-candidate thresholds, G5. |
| NFR-010 Compatibility | 01/05/07/08 | Shared CLI/automated/MCP semantics; preserve lab deployment/validation operability. |
| NFR-011 Maintainability | 01/05/06/07/08 | Versioned contracts, classifications, offline tests/scenarios for extensions. |
| NFR-012 Privacy | 01/02/04/07/08 | Minimization, redaction, consent, storage lifecycle and enforced egress. |
| NFR-013 Usability | 01/02/03/04/05/07 | Diagnostic naming, visible proposal/execution/confidence differences, versioned machine export. |
| NFR-014 Deployability | 01/02/06/07/08 | Single executable, independently stoppable external observer, approved external harnesses; G1/G2. |
| NFR-015 Testability | 01–08 | Deterministic core; separately authorized lab/model acceptance, never claimed from fixtures. |

### Acceptance closure owners

This ledger assigns every AC explicitly; “owner” means proposed integration responsibility, not completed acceptance.

| Acceptance criterion | Proposed closure owner and contributing phases | Required distinguishing evidence |
| --- | --- | --- |
| AC-001 | 05; 01/03/04 | Single + multi exact approval, explicit audited pre-plan lookup, stale/cancelled plans do not dispatch. |
| AC-002 | 03; 01 | Literal case/whitespace identity, ambiguous/missing refusal, original/resolved identity. |
| AC-003 | 05; 02/03 | Malformed control output/graphs and unproductive loops stop finitely. |
| AC-004 | 07; 01/03/04/05 | Nested/resumed/delegated-like adversarial requests and legitimate relationships checked at dispatch. |
| AC-005 | 06; 03/05 | All required domain fixtures, sufficient evidence and unavailable-tool variants. |
| AC-006 | 05 | Dependency outcomes, per-target evidence and qualified partial synthesis. |
| AC-007 | 04 | Crash boundaries, uncertain replay confirmation, terminal refusal, writer conflicts. |
| AC-008 | 04; 03 | Typed evidence/history, 15-minute freshness and distinct log event times. |
| AC-009 | 04; 02/03 | Curated bounded citations, hostile/secret/stale/missing sources; no archive ingestion. |
| AC-010 | 05; 03/04 | Unsupported/contradictory/missing support review and bounded follow-up. |
| AC-011 | 08; 01/06 | Deployed observer/reader/reachability proof and authorized disposable mutation-denial checks. |
| AC-012 | 07; 01/03/06 | Manual/automated/MCP denial parity and only reviewed Go diagnostics. |
| AC-013 | 06; 08 integration | Three required hosts, exact windows, bounded fixed operations, no fallback. |
| AC-014 | 07; 01/04/05 | All result states, partial summaries, intent/outcome faults, withholding and acknowledged recovery. |
| AC-015 | 08; 01–07 | Secret canaries, fix-it scoped diagnostics and manual recommendations without runnable mutation. |
| AC-016 | 08; 02 | Both deterministic harness contracts + both real-model checks; at least one real lab run. |
| AC-017 | 08; 01/02 | Independent deployed isolation and negative bypass/credential-access tests. |
| AC-018 | 04; 02/03 | Provider outage/disclosure revocation, late-response rejection, local/manual availability. |
| AC-019 | 07 | Tools/resources/prompts, real standalone Pi, client context/session/egress teardown. |
| AC-020 | 05 | Specialists disabled and unreachable; enabling is conditional on separate evidence/scope. |
| AC-021 | 08; 01/03/05 | Versioned machine-readable offline evaluation without credentials. |
| AC-022 | 08; 01–07 | Correlated events, aggregated budgets, exhaustion/cancellation and unknown usage. |
| AC-023 | 08; 01/04/06/07 | Readiness, retention, revocation, shutdown, recovery and rollback records. |
| AC-024 | 08; 01/04/05/07 | New-store and legacy preservation plus applicable manual/lab regressions. |
| AC-025 | 08; 03/05 | Pre-pinned candidate criteria, exploratory baseline, safety evidence and authorized real lab investigation. |
| AC-026 | 08; 01/05/06 | Target Ubuntu observer, live project catalog, three hosts, disposable mutation-denial record. |
| AC-027 | 06; 01/05 | Full Go catalog/offline safety, explicit field availability, gated higher visibility. |
| AC-028 | 07; 01/02/03 | Named manual selection → sanitized paste → approved isolated analysis; all entry-point parity. |
| AC-029 | 08; 01/02/06/07 | Utility-free diagnostic packaging, both external harness prerequisites, isolated principals/client egress. |
| AC-030 | 07; 01/02/03/04 | Plan/session defaults, lookup/relationships, revocation races/withholding and alias/disclosure tests. |
| AC-031 | 04; 01/08 | Quota + physical disk full, defaults/cleanup/references, audit faults, exports, deletion and legacy isolation. |

**Unassigned requirements:** none identified. **Mandatory requirements deferred beyond Delivery 1:** none proposed. Higher-visibility operator capabilities remain conditionally unavailable only as expressly permitted; missing required restricted-host live evidence blocks release. FR-036/AC-020 are satisfied by keeping specialist roles disabled, not by silently requiring a multi-agent implementation.

**Explicit exclusions:** mutation/remediation execution; generic shell/SSH/sudo/CLI passthrough; database queries; model repository/file editing; admin/root/service credentials; automatic surveillance; web/public APIs; network MCP; storage-node host diagnostics; local model hosting/training; new provider-protocol gateways; future direct remote-API custom harness; automatic legacy migration; unrelated lab provisioning replacement; learning lessons/assessments. Parallel scheduling, advanced retrieval and specialist enablement are not needed for this proposed slice and require separate justification/review rather than implicit scaffolding.

## 00.10 Next Governance Gate

Select **Phase 01 — Safety Foundation and Manual Diagnostics** for independent `specification-readiness-authority` review in **scope readiness** mode. Review the proposed boundary, PRD references, inspected revision, reuse limits, G1–G4 dependencies, manual-only first capability, exclusions and safety/verification expectations. The reviewer may recommend a smaller bounded delivery; this file does not establish a task contract.

After that independent assessment, specification authoring must be separately authorized. Draft/review/approve the required ADR and bounded task contract; only an approved and committed contract can proceed to implementation preflight and a separately authorized execution ladder. Do not automatically start review, specification authoring, implementation, tests, deployment, commits or pushes from this roadmap.
