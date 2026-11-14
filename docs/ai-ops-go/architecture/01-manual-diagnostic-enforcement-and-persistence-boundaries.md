# 01. Manual Diagnostic Enforcement and Persistence Boundaries

**Status:** Owner-approved and accepted. Uncommitted at the approval-record update; commitment, implementation preflight and execution authorization remain separate gates.
**Approval record:** After the independent initial draft review returned `DRAFT_SPEC_READY`, the user stated in this conversation: “I approved both document, now update the document because I have approved and accpeted it.” Approval covers the reviewed task and ADR and the status/provenance updates recording that approval; it does not approve a concrete G1–G4 realization, authorize implementation or establish implementation acceptance.
**Reviewed candidate:** ADR SHA-256 `67218412cb5bbac8ca290fd65ee64f9f0d646de504825071a73701c36199fc5d`; task SHA-256 `3566e2e2dc32a35681f57f394b678e7427dbe84ba5de67933019ac59c1468488`. These identify the pre-approval-update bytes reviewed, not the modified files' current hashes. The review report was returned in the conversation; no report file was created.
**Selected scope:** Owner-approved Phase 01 scope only; not all of Delivery 1.
**Related contract:** [Phase 01 task](../tasks/01-safety-foundation-and-manual-diagnostics.md).
**Governing sources:** [Current PRD](../prd.md), Implementation Decisions (product decisions 1–3, 8–10), FR-002–FR-003, FR-010–FR-011, FR-021–FR-024, FR-027–FR-029, FR-043–FR-044, FR-048–FR-050; NFR-001–NFR-006, NFR-008, NFR-012, NFR-014. [Phase 01](../implementation-plan/01-safety-foundation-and-manual-diagnostics.md) §§01.3–01.6 supplies the scope ceiling.

This ADR records the approved architectural ownership and admission boundaries needed to close existing bypass and persistence risks. It is not a technical ADS, implementation ladder, approval of a concrete transport/storage mechanism, or implementation authorization.

## 1. Context and evidence

Authoring base: branch `aiops-go-phase01`, HEAD `e29fa87e293246c187f5b01604e6f012dfbb4761`, tree `2ed028bf34f68a75f63d885b0967df6c80852089`. Initial tracked staged/unstaged diffs were empty; the nine roadmap files were untracked. Source fingerprints and drift classification are in task §2. No current Phase 01 implementation acceptance is evidenced.

Observed implementation, not accepted architecture:

- `aiops/Makefile` builds four executables. The agent, workflow and project command `main` functions construct model/cloud clients and a `tools.Registry` before their interactive command loops. The chat executable constructs a model client but has no diagnostic tools in its inspected `main`.
- `tools.Registry.Execute` invokes a registered implementation with only context, name and raw arguments. It does not carry an explicit application-owned cloud/project/target/profile/policy authorization contract or durable audit dependency.
- `agent.Runtime.run` and `workflow.collectBaselineStep.Run` call that registry. `scopedtools.Broker.Execute` has assignment, relationship-response and in-process budget checks, but is not the boundary wired into those command mains; its caller-supplied assignment is not independent authority.
- `GetServerTool.Execute` trims input; `resolveServer` uses an unbounded `AllPages` lookup and then exact-name filtering. The observation omits image, networks and config drive, permits raw fault details/host fields and does not express all required field-availability states. `GetFlavorTool.Execute` accepts a flavor ID and reads extra specs without proving a server relationship at that boundary.
- The port tool has useful finite record/page and returned project/device checks; these do not establish shared authorization or complete networking semantics. Existing restrictive temp-file writes, file sync and rename are useful patterns, not proof of directory durability, writer arbitration, audit recovery or quota handling. Engine pause/failure paths sometimes discard save errors.

These are reasons to propose a real boundary, not evidence that a renamed facade or a passing old helper test would satisfy it.

## 2. Settled product decisions and fidelity

The following IDs belong to the current PRD; architectural labels B1–B5 below are local to this ADR and are not product-decision IDs. Rationale in §3 is engineering analysis unless attributed to a source.

| Source | Required affirmative rule | Negative constraint | ADR / task fidelity and future evidence |
| --- | --- | --- | --- |
| Product decisions 1–2, 8; FR-010, FR-023–FR-024, FR-044; NFR-001 | Go owns the registry and actual per-call authorization, including tool-local validation. | Plans, public arguments, client/model identity assertions or a package boundary cannot grant execution authority; no enabled bypass. | B1–B2; task §§4–6, V1–V3. |
| Diagnostic implementation form; FR-021–FR-022, FR-043; NFR-002 | One Go executable, external Ubuntu 24.04 x86-64 non-root observer, dedicated project reader, separated access domains. | No equivalence between executable/process/principal; no admin/root/service credential fallback; no diagnostic utility dependency. | B1–B2; task §§3–6, V1/V3/V12. |
| FR-003, FR-011, FR-025 | Canonical UUID or supported literal case-sensitive exact name, preserved meaningful whitespace and identity; required basics fields and verified related reads. | No normalization that changes intent, guessed match, implicit project/host discovery or caller-asserted relationship. | B2; task §§4/7, V4–V5. |
| FR-027–FR-029; NFR-006/NFR-008/NFR-012 | Sanitize/minimize before sinks; durable intent before allowed dispatch; result audit before payload delivery. | No raw-secret sink, payload release on outcome-audit failure, invented denial audit, or claim of undoing a read. | B3–B4; task §§6–7, V6–V9. |
| FR-014, FR-048–FR-050; NFR-004–NFR-005 | Protected versioned new store, atomic/transactional records, writer control, finite limit, actual disk-full detection, applicable audited cleanup. | No unsafe saved-state claim, silent unexpired eviction, premature audit deletion, legacy access/import/index/cleanup or approval reuse. | B4–B5; task §6, V9–V11. |
| FR-028; FR-015 uncertainty rule | Recovery pauses for acknowledgement of known gaps/uncertain calls; current authorization and separate uncertain re-collection confirmation. | Acknowledgement cannot restore revoked authority or authorize silent replay; no exactly-once read/persistence claim. | B4; task §§6–7, V9. |

## 3. Architectural decision

### B1 — Close the capability boundary, not just the CLI facade

The credential-bearing reader clients, actual diagnostic implementation mapping and dispatch authority shall be owned by the reviewed gateway security domain. Public adapters may request a named diagnostic with bounded arguments; they shall not receive reusable reader credentials/clients or select endpoints, implementations, profiles, authority, audit destinations or effective limits.

Every retained diagnostic entry reaches that same enforcement owner, or is disabled before model invocation, cloud authentication, diagnostic reads or legacy-store initialization. The Phase 01 runtime exposes manual/readiness behavior only. Retaining source code for future workflows is not permission to enable it. Unrelated lab provisioning workflows remain separate and untouched.

The runtime has no infrastructure mutation capability. Go diagnostic implementations perform narrow approved reads, not shell/SSH/sudo/OpenStack CLI passthrough, arbitrary HTTP/file/database tools or separate diagnostic scripts/interpreters. Required authentication is not a mutation tool.

### B2 — Authority must be trusted independently of request content

An application-owned authorization context binds the authenticated caller/security context, configured cloud/project, explicit selected original/resolved target, permitted capabilities/profile/related-read categories, policy identity, finite limits and correlation. The actual boundary revalidates it for each API operation, including name resolution and related reads. Request strings, resource names and returned catalog/relationship data cannot create grants.

For manual use, the operator's explicit named diagnostic is the action request; no model plan is required. Its lookup and related-read effects must be visible, bounded and inside trusted authorization. A separate pre-plan name-lookup consent mechanism belongs to Phase 03, not a hidden Phase 01 plan or discovery grant. Denied pre-dispatch requests make zero downstream calls. If a response reveals a scope violation after an authorized read, withhold it and report/audit that read honestly; do not retroactively claim zero contact.

One executable may run in multiple separately controlled non-root processes. A transport must authenticate and bind the caller context; arbitrary local processes must not gain diagnostic authority by reaching it. OS access controls, not Go packages, CLI flags or environment filtering, enforce separation from credential/state domains. No particular identity name, IPC transport, sandbox or credential-input format is selected here. Before affected execution, the concrete realization must be documented, separately reviewed/approved and negatively verified under G1/G3 (task §3). Phase 02 must independently prove harness/credential isolation and egress before any model feature is enabled; this ADR does not preapprove that integration or scaffold it.

### B3 — Audit is a dispatch and disclosure prerequisite

An allowed operation requires a durable sanitized intent before dispatch, including authorized lookup/related collection. Each attempted request has an auditable safe outcome when the store is available. Each distinct API read must remain attributable to the request, relationship, intent and finite budget; a request-level intent cannot authorize unbounded subcalls.

Minimization/sanitization precedes audit, evidence, errors, CLI output and all other sinks. Complete required result auditing precedes diagnostic payload delivery. Outcome-audit failure stops subsequent work across callers, withholds the payload, and returns only a locally visible safe operational failure explaining possible prior collection. Denial-audit failure is a visible gap, not evidence of a persisted record. There is no transaction that rolls back an OpenStack read when local storage fails.

### B4 — Persistent health and recovery constrain admission

The gateway shall not dispatch when required policy/audit/checkpoint/storage integrity or capacity is unknown or failed. Separate processes/restarts cannot erase a known failure or unresolved intent and resume automatically. Implementations may serialize writers/admissions or finitely reject contention. A purely in-memory health flag or mutex is insufficient for cross-process/restart guarantees.

The concrete storage realization must specify durable ordering for initial creation, append/replacement, version/integrity state, writer exclusion, acknowledgement and any cleanup. A successful rename or file sync alone is not proof. Corrupt/incompatible/uncertain state is refused without automatic repair, false saved-state claims or replay.

After recovery, remain paused until the operator acknowledges known gaps and uncertain calls. Recheck current authorization. Any uncertain re-collection needs separate explicit confirmation and a new timestamped observation; acknowledgement is neither consent to recollect nor restoration of expired/revoked rights. A withheld result can be disclosed only after the fault is resolved, it is durably audited and current disclosure authorization holds. If it cannot be safely recovered, report that limitation rather than recreating it silently. No command/UI for this acknowledgement is prescribed here, and investigation resume is not introduced.

### B5 — New-store isolation and first-use lifecycle are non-negotiable

Use a protected, explicitly versioned new namespace, never the existing investigation/memory/workflow/project directories. No legacy data read, import, indexing, sending, modification, deletion, cleanup or approval reuse is part of this path. Legacy data can consume physical disk even though outside the managed quota.

Require a finite usable storage limit at startup; distinguish managed-limit exhaustion from actual disk exhaustion. Budget admission and durable control writes safely; do not evict unexpired records to make execution succeed. Retain sanitized audit for the configurable 90-day default; bounded cleanup runs at startup and during operation, reports failures and requires durable intent before deletion. Outcome-audit failure after deletion reports a gap and possible completed deletion, never rollback.

The 30-day terminal-investigation default and protection of running/paused/active-dependent evidence apply as those record types appear. Phase 01 does not introduce investigation lifecycle/history/reference graphs; unsupported record types/references cannot be silently accepted or deleted. No later Phase 04 expansion waives safeguards applicable to today's records. The task does not require retaining full manual payloads; any retained payload must have an explicit compliant data classification/lifecycle before use, not an invented terminal-investigation status.

## 4. Alternatives and permissible design latitude

- **Selected boundary:** One enforcement owner with private reader capabilities, authenticated scoped ingress, durable audit/disclosure gating and shared fail-closed persistent admission. This addresses existing direct-registry and file-store limitations without selecting technology prematurely.
- **Permitted Level 1 alternatives after approval:** Safe authenticated local transports and OS separation mechanisms within reviewed constraints; compiled versus protected registry representation; atomic local records/journal versus another compliant protected local persistence design; serialized versus rejected concurrent admission. Each must document meaningful tradeoffs and prove the same invariants. Database-backed/shared-service operation or new infrastructure is not assumed authorized.
- **Not compliant:** Adding a new gateway while leaving raw registry/SDK routes enabled; trusting an environment/project string as authority; sharing diagnostic credentials with model-facing processes; treating disabled harness flags as isolation; script wrappers; best-effort audit after disclosure; a health latch cleared by restart; importing old approvals or applying legacy HTTP/auth exceptions automatically.

The engineering consequence is lower availability when mandatory storage/control dependencies fail, in exchange for truthful evidence and no unaudited dispatch. This is derived analysis, not a fabricated stakeholder rationale. Safe manual diagnostics remain independent of optional model, knowledge, host and operator-reader availability, not independent of their own mandatory audit/policy/storage controls.

## 5. Compatibility and historical sources

The four selected historical contracts were read in full: archived Go-owned ADR/task and their architecture/task environment-auth amendments under `docs/archive-dont-look-here/aiops-go/`. They describe different candidates and sources. Their three-tool scope, seven outer statuses, fixed identities/paths, audit rotation rules, restricted identifier syntax, environment-only application-credential input and lab HTTP risk exceptions are not current architecture authority. The current PRD requires eight logical statuses including `partial`, narrower Phase 01 server scope, meaningful-whitespace names and first-use managed storage/lifecycle protections.

This record neither supersedes nor amends those historical contracts or their independent runtimes. There is no inherited approval, transport exception, installation grant, fixed reader project/host or migration authority. Existing compatible validation/test patterns may inform a new design, but importing historical implementation contracts or loosening current rules is prohibited. Any retained interface incompatibility is declared/versioned and safely disabled rather than silently translated or activated.

## 6. Required evidence, gates and open matters

Task V1–V12 specifies future public-entry denial, identity/relationship, field-availability, sanitizer, finite-bound, audit, real filesystem/concurrent-writer/crash, recovery acknowledgement, cleanup/quota/disk-full, legacy-preservation and utility-free evidence. Source inspection and document QA are not those tests.

| Gate | Needed now for this draft | Still required before affected execution/acceptance |
| --- | --- | --- |
| G1 | Credential-owning versus requesting security domains and authenticated ingress invariants B1–B2; model features disabled. | Reviewed/approved concrete non-root OS/IPC realization and unauthorized-local-caller negative proof before manual enablement; separate harness proof in Phase 02 and client proof in Phase 07. |
| G2 | No deployment values inferred. | Operator-supplied cloud/project/endpoints, usable finite limit and protected setup before startup/live work; disposable-scope approval and cleanup owner before policy-denial probes. |
| G3 | Explicit target/related-read rules, response checks and no stronger-profile fallback. | Reviewed exact project-reader APIs/visibility and transport/destination policy before collector enablement; actual reader/mutation-denial evidence at separately authorized live gate. |
| G4 | B3–B5 and task failure/lifecycle guarantees are approved constraints. | Reviewed/approved concrete durability/versioning/writer/quota/cleanup/recovery realization before persistent execution; actual fault evidence before acceptance. |

No genuine Level 2 change to current product rules is identified as necessary to draft this bounded proposal. Mechanism feasibility and deployment facts are unverified, not resolved by this ADR. A future design that cannot satisfy these constraints must stop with a precise Level 2 decision request, not accept weaker safety. Review/approval of this boundary record alone is not proof that a concrete mechanism exists or works.

G5 release thresholds and G6 real MCP verification remain allocated to later phases; no SLA, client egress mechanism or rollout is selected here. Independent draft review and owner approval are recorded above. The approved documents were uncommitted at the approval-record update; commitment, separately requested implementation preflight and separate implementation authorization remain distinct gates. No preflight, product tests, build, live diagnostic, credential inspection, deployment, stage or commit is implied by this approval.

**End of ADR.**
