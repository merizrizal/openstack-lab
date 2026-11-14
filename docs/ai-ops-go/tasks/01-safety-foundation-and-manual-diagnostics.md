# 01. Safety Foundation and Manual Diagnostics

**Status:** Owner-approved and accepted. Uncommitted at the approval-record update; commitment, implementation preflight and execution authorization remain separate gates.
**Approval record:** After the independent initial draft review returned `DRAFT_SPEC_READY`, the user stated in this conversation: “I approved both document, now update the document because I have approved and accpeted it.” Approval covers the reviewed task and ADR and the status/provenance updates recording that approval; it does not approve a concrete G1–G4 realization, authorize implementation or establish implementation acceptance.
**Reviewed candidate:** Task SHA-256 `3566e2e2dc32a35681f57f394b678e7427dbe84ba5de67933019ac59c1468488`; ADR SHA-256 `67218412cb5bbac8ca290fd65ee64f9f0d646de504825071a73701c36199fc5d`. These identify the pre-approval-update bytes reviewed, not the modified files' current hashes. The review report was returned in the conversation; no report file was created.
**Scope authority:** [Owner-approved Phase 01 boundary](../implementation-plan/01-safety-foundation-and-manual-diagnostics.md), four ordered steps and §01.6. Its approval is not approval of this contract.
**Requirements:** [Current Delivery 1 PRD](../prd.md), including its endings, open decisions, testing decisions and AC-001–AC-031.
**Architecture:** [Owner-approved boundary ADR](../architecture/01-manual-diagnostic-enforcement-and-persistence-boundaries.md), B1–B5. The approved constraints do not select a concrete transport or storage mechanism.
**Original authoring authorization:** The invoking user explicitly authorized the action in the `002` specification-authoring instruction and requested task/architecture outputs under the current `docs/ai-ops-go/` tree. That was documentation-only authorization, not execution, self-approval or automatic advancement.

## 1. Objective and observable outcomes

An operator can select and run a named server-basic diagnostic with explicit project-reader scope through one Go-owned reviewed boundary, without inference, MCP, arbitrary command composition or separately installed diagnostic utilities/interpreters:

```text
explicit manual action + authorized project/target/capabilities/limits
  -> validated authenticated boundary -> durable sanitized intent
  -> bounded read-only server / permitted related flavor-port API reads
  -> minimized sanitized durably audited result -> concise human / JSON output
```

Success means useful scoped evidence, not proof of health or root cause. Missing/denied fields, unavailable capabilities, truncation and unsafe withheld content remain visible. All supported diagnostic paths either enforce this contract or fail safely before side effects. Required policy/audit/store failure stops execution, even when a read may already have happened. Model, optional knowledge, host and operator-reader dependencies are unnecessary for manual operation.

This contract defines outcomes and constraints, not another execution ladder. The Phase 01 plan remains the scope/decomposition source. No ADS, future feature skeleton, second roadmap or chunk list is created here.

## 2. Source identity, freshness and observed baseline

### 2.1 Repository and approval evidence

| Item | Observed authoring baseline |
| --- | --- |
| Project root | `/home/meriz/Documents/Synctech.ID/CI_CD/openstack-lab` |
| Branch / HEAD | `aiops-go-phase01` / `e29fa87e293246c187f5b01604e6f012dfbb4761` |
| HEAD tree | `2ed028bf34f68a75f63d885b0967df6c80852089` |
| Committed current requirements | PRD blob `37a7a291d27934a6fa19d71eb4a7f7e250df786f`; baseline blob `d3049659d9d40b6b7cb7012f57d02cbe579693a8`, verified with `git ls-tree HEAD`. |
| Initial project changes | No tracked staged/unstaged changes; nine untracked roadmap Markdown files (overview and Phases 01–08). No committed current roadmap/task/ADR candidate established. |
| Parent repository | `/home/meriz/Documents/Synctech.ID`, branch `main`, HEAD `74c01ca9de6c2153a0306b037860bfe3c276b649`, tree `479ab2554139c368375a6a7aa77c4e97e75fb2f7`. |
| Parent pre-existing state | Modified `Etc/goose/handoff-openstack-aiops/aiops-prompt.md`, `Etc/skills/README.md`; untracked `001` and `002` handoff/instruction pairs. No staged changes. Preserve all. No output goes there. |
| Approval evidence at authoring | PRD header states owner-approved `scope_ready` product scope. Phase 01 records scope/decomposition approval only. `002` reports preceding scope review, but no standalone report/original transcript was supplied. At authoring, no independent review or exact-candidate approval of these drafts was established; the subsequent review and approval are recorded above. |

Measured SHA-256, matching all four `002` preparation fingerprints:

| Current source | SHA-256 |
| --- | --- |
| `docs/ai-ops-go/prd.md` | `a685452c2b2d7303a342376117299d777131fd4ff6dfd3ffc19dd397974da9ed` |
| `docs/ai-ops-go/aiops-baseline.md` | `cd03daa694691852842d4812b983cdbd220fba205d02d318d4f57ca9e9503e01` |
| `docs/ai-ops-go/implementation-plan/00-implementation-overview.md` | `92bd72c67805ff2f8350dc6bcff5f7228f6b262e6e20d9fd3c627d8ebd31b1f0` |
| `docs/ai-ops-go/implementation-plan/01-safety-foundation-and-manual-diagnostics.md` | `3f489644009010e68077749dbcc9d4cb983dd87bb83747cf46b912bf1cb20f14` |

**Drift classification:** Nonmaterial confirmed relative to `002`: same HEAD/tree, exact four source bytes and same nine roadmap candidates; the parent additionally contains the expected prepared `002` pair. All seven later phase hashes also match `001`. The `001` Phase 01 hash `63bd230ffba4b3e365cb16a5e34aeae5671e5e27c975290e2e647145e7eb573d` is historical, not this candidate. Current Phase 01 explicitly separates boundary approval from task/preflight/execution gates; no broadened implementation scope is identified. The historical pre-update review verdict is not reissued or treated as fresh certification. The overview still describes the initial proposed phase set/no supplied boundary approval; the specific later Phase 01 approval record governs this selected boundary, not the other proposed phases.

### 2.2 Code observations, not accepted behavior

All code paths below are under `aiops/` at the stated base. Source presence and existing tests do not establish passing safety or deployed acceptance.

| Seam / precise anchor | Observation and consequence |
| --- | --- |
| `Makefile:build`, `go.mod` | Four runtime binaries today; Go `1.27.1`, Gophercloud v2 `v2.14.0` declared. Toolchain/cache availability not checked. Consolidation is required work, not an accepted baseline. |
| `cmd/openstack-agent/main.go:main`, `cmd/openstack-workflow/main.go:main`, `cmd/openstack-project/main.go:main` | Each constructs AI and Nova/Neutron clients, generic registry and legacy stores. Existing start/resume/show paths cannot be enabled as an implicit Phase 01 workflow. |
| `cmd/openstack-ai/main.go:main` | Chat/model path, no diagnostic tool wiring in inspected main. Inference is outside Phase 01 runtime exposure; no new analysis feature is authorized. |
| `internal/tools/registry.go:Registry.Execute`, `tool.go:Tool` | Registered-name dispatch directly to implementation; no explicit scope/profile/policy/audit contract. |
| `internal/agent/runtime.go:Runtime.run`, `internal/workflow/server_incident.go:collectBaselineStep.Run` | Both dispatch through that registry. Project workflow execution composes these paths through the project CLI. |
| `internal/scopedtools/broker.go:Broker.Execute`, `verifyCall`, `spend` | Role/target/flavor/project response checks and shared in-process budget are useful selective patterns, not the general trusted boundary or cross-process health control. |
| `internal/tools/get_server.go:Execute`, `resolveServer`, `ServerObservation` | Trims whitespace; `AllPages`; exact comparison after server-side name filtering; required fields/availability states incomplete. Raw fault details/host projection need minimization review. |
| `internal/tools/get_flavor.go:Execute` | Caller-selected flavor and extra-specs collection; no verified server relationship at that boundary. Do not inherit it as unrestricted public capability. |
| `internal/tools/get_ports.go:Execute` | Finite 32-record/four-page limits and project/device response checks; no shared intent/audit/result contract. Preserve useful checks without claiming full server-network scope. |
| `internal/openstackclient/compute.go:NewComputeClient`, `network.go:NewNetworkClient`, `project.go:ScopedProjectID` | Ambient auth/region inputs and project extraction, not proof of a dedicated reader, independently trusted scope or safe endpoints. No authentication source is selected by this contract. |
| `internal/agent/filestore.go:writeJSONAtomic`, workflow/project `store.go:writeJSONAtomic` | Restricted directory/file creation, file sync and rename patterns; no demonstrated quota/audit/retention/concurrent-writer guarantees. Initial creation and directory durability require evidence. |
| Agent `pause`, workflow engine `pause`, project engine failure/`pause` | Some save errors discarded. These engines remain disabled, not broadly repaired for deferred workflow scope. Reusing a path requires meeting current fail-closed guarantees. |
| `internal/tools/get_server_test.go`, `get_ports_test.go`, `internal/scopedtools/broker_test.go` | HTTP fixtures, argument/no-call checks, project/device/role checks, cancellation and in-process budget tests exist. Read in full; not run and not sufficient for new invariants. |
| `internal/ai/codex.go:run`, `pi_env.go:NewPiClientFromEnv` | Process/config seams observed; flags/environment handling are not independent OS isolation proof. No harness enablement or redesign here. |
| Root `Makefile`, `.github/workflows/ansible-sanity-test.yml` | Root Make loads `.env`; current CI is Ansible/Python 3.12/3.13/3.14, not Go acceptance. Neither root targets nor live automation may be invoked as documentation QA. |

### 2.3 Revalidated carried review leads

These are author-side substantiations of `002` leads, not independent draft-review findings or proof of repair.

| Lead | Current evidence / required closure |
| --- | --- |
| SR-001 dispatch bypasses | Registry and three diagnostic command mains above lack the proposed common boundary. Close every retained route or disable it before side effects; V1–V3 must exercise public paths, not only a new helper. |
| SR-002 identity/projection | Input trimming, unbounded lookup and incomplete `ServerObservation` conflict with current required behavior. Literal identity and explicit field states are specified in §§4/7; prove V4–V5. |
| SR-003 audit/storage | No common audit/quota/retention control appears in the inspected registry/tools/stores; file rename and ignored saves do not establish it. §§6–7 and V8–V11 cover first-use durability, all faults and payload withholding. |
| SR-004 legacy isolation | Current mains use old store roots. New-store separation must prevent those initializations, reads, ingestion, cleanup and approval reuse; V1/V11. Historical contracts do not authorize current reuse. |
| SR-005 recovery acknowledgement | PRD FR-028 expressly requires acknowledgement now, even though full resume is Phase 04. §6.3/V9 require it for manual admission after audit recovery; do not defer it away. |

## 3. Prerequisites and gate timing

The current PRD governs behavior. The baseline is conceptual only. `README.md` and `docs/architecture.md` describe lab placement/operations, not approval of new security mechanisms or environment defaults. No existing implementation is classified `ALREADY_ACCEPTED` without acceptance evidence.

| Gate | Contract constraint now | Prerequisite for affected future work |
| --- | --- | --- |
| G1 security domains / authenticated IPC | ADR B1–B2: credential-owning actual boundary, authenticated scoped ingress, separate non-root access domains; model/MCP disabled. | Concrete compliant OS/IPC design must be documented and separately reviewed/approved before affected execution, with negative unauthorized-local-caller proof before enablement. Package boundaries/shared process/flags are insufficient. Harness/egress design and proof stay in Phase 02; standalone client context/egress stays in Phase 07. |
| G2 acceptance configuration | No project, endpoint, identity, host alias, storage value or credential inferred from defaults, `.env` or archive. | Trusted operator configuration, finite usable limit and protected setup before startup/use; explicit live/disposable scope and cleanup owner before any policy probe. Real environment evidence is not required merely to draft or use synthetic offline fixtures. |
| G3 reader policies / relationships | One configured dedicated project reader, approved bounded APIs/visibility, explicit target and relationship checks; no stronger fallback. | Review exact Nova/Neutron/flavor read relationships and transport/destination restrictions before collector enablement. Cloud-side reader/mutation-denial proof is separate live acceptance, never established by fixtures. |
| G4 storage / audit recovery | ADR B3–B5 and §6 apply from first persistent/manual execution. | Concrete protected versioning, durability/writer arbitration, admission capacity, cleanup and acknowledgement realization must be documented and separately reviewed/approved before persistent execution. Prove its filesystem/crash/fault behavior before acceptance; no requirement to choose a database, fixed path or IPC technology while drafting. |

These are not blanket Level 2 blockers to writing a constraint-based contract. They are not declared resolved either. Routine compliant mechanisms remain Level 1; infeasibility requiring weaker safety, new material risk/architecture, infrastructure or expanded scope requires a precise Level 2 request and stop of dependent work. G5 quality/resource thresholds remain Phase 08 release gates; G6 real MCP verification remains Phase 07. Neither authoring nor Phase 01 completion authorizes live access/deployment.

## 4. Exact in-scope boundary

### 4.1 Runtime and ingress

- One Go runtime executable provides named manual diagnostics and safe help/catalog/readiness behavior. Multiple independently controlled processes using it are permitted, not mandatory scaffolding for models/MCP. Binary name, command spelling and package layout are Level 1 choices, not invented existing APIs.
- Inventory the four current commands, their start/resume/show branches, generic registry, direct tool/SDK paths and scoped broker; repeat discovery at implementation time for any additional caller. Record retained/routed/disabled status, authority source and corresponding public-entry test. No reachable diagnostic route may remain outside the actual boundary. Retained legacy automatic/model paths must refuse before authentication, inference or legacy-store initialization; do not implement plans/resume merely to preserve them.
- Help/readiness/catalog do not perform diagnostic name lookup, resource discovery or model calls merely to display information. Separate local prerequisite checks from any explicitly requested, authorized and audited connectivity check. No cloud call is implied by a readiness label.
- Trusted application configuration and authenticated caller context establish cloud/project, selected targets, allowed capability/profile/related-read set, policy identity, finite budgets and correlation. Public arguments cannot forge or override these, reusable credentials or implementation paths. Arbitrary local process access is not assumed trusted.
- Ubuntu 24.04 LTS x86-64 non-root observer placement outside the observed cloud/control plane, management/API-only required routes and separate credential/state/provider access boundaries are documented prerequisites; no actual host/route selection or provisioning here.

### 4.2 Reviewed registry, dispatch and limits

- Each enabled public tool name/version maps to one reviewed built-in Go implementation for the selected configuration. Declare diagnostic intent, strict arguments, scope/relationship rules, required reader profile, risk/read-only guarantee, prerequisites, timeout and collection/output limits.
- Deny unknown/disabled tools, malformed/extra arguments, executable/endpoint/host/path/profile overrides, generic commands, mutations and out-of-scope requests before implementation invocation. Tool-local validation independently defends the narrow operation.
- Recheck current authorization and remaining limits before each lookup/read and related call; validate returned resource/project/relationship consistency before use or disclosure. Authentication failures, denials and invalid inputs do not trigger stronger credentials or transient-retry loops.
- Set finite documented time, request/retry, page/record, argument/response/output and resource bounds appropriate to each enabled operation. Enforce while collecting/decoding, not only after unbounded buffering; keep cancellation effective through pagination and nested reads. Existing port ceilings are observed safeguards, not authorization to broaden collection. Numerical limits must be justified/recorded in reviewed definitions, not copied from legacy contracts.
- Only trusted configured approved destinations receive authentication or requests; no caller-selected endpoints or response-driven redirects/pagination may expand authority or expose credentials. Required authentication is narrowly controlled infrastructure access, not permission to mutate resources.

### 4.3 Manual identity, related reads and projection

- Accept canonical server UUIDs and supported literal case-sensitive exact names within the authorized project. Preserve original input, meaningful whitespace and resolved identity; do not trim/case-fold/Unicode-normalize names or silently turn malformed UUID intent into a different target. Reject unsupported representations safely with UUID guidance rather than expanding validation by guesswork. Do not invent an ASCII-only rule or import historical name restrictions.
- A direct named manual action may authorize its disclosed bounded name resolution through the same gateway, under current project/target policy and audit; it is not a model plan. Help/readiness is not that action. Phase 03 separately requires explicit disclosed pre-plan lookup consent that does not authorize diagnostic tasks; no plan-consent UI is implemented now.
- Bound lookup pages/records/time; if uniqueness cannot be established within bounds, refuse to pick a target. Server-side name filters can be approximate; match literal returned names independently and verify resolved target/project. Missing, ambiguous, case/whitespace mismatch or unauthorized matches cause no diagnostic GET of a guessed target. Retain safe original/resolved identity and actionable UUID guidance; do not disclose unrelated candidates.
- Server basics explicitly reports status, image, flavor, networks, config drive and availability zone when exposed/permitted, otherwise a per-field `unavailable`, `denied` or `not-applicable` indication with safe reason; include fault when available. Do not invent absent fault details or treat missing/denied evidence as healthy. Retain validated server ID/name needed for traceability. These are logical field outcomes, not a mandated wire schema.
- Minimize image/flavor/network/fault projections to the required evidence; do not dump opaque nested objects, host placement, raw secret-bearing details, extra specs or full configuration merely because the old tool returns them. Safely withhold prohibited content with a visible limitation.
- Narrow related-flavor/port reads are permitted only when their category is explicitly granted for this manual action and a verified authorized server observation establishes the corresponding relationship. Verify flavor identity, and port project/device linkage on return. A caller-asserted flavor/network/port ID is not proof. No broad flavor search, unrelated ports, automatic network/subnet traversal, project summary or host authority follows from discovery. Full server-network/volume/catalog work remains Phase 05/06; server-basic network context uses only permitted available evidence and explicit gaps.

## 5. Exclusions and explicit later ownership

No model analysis, automatic tool selection, investigation planning/execution, resume, MCP, broad project discovery, full catalog, host/operator enablement, migration, local-model deployment, custom direct-API harness, speculative services/schemas, parallel/distributed scheduler, database infrastructure or unrelated lab provisioning. No mutation, generic shell/SSH/sudo/OpenStack CLI/database/file tool, stronger-credential fallback or separate diagnostic executable/script dependency exists.

Later PRD obligations remain inside Delivery 1, not waived: Phase 02 both isolated inference adapters/disclosure/egress and protected paste-to-Go analysis; Phase 03 exact-approved single-server investigation, separately authorized pre-plan lookup, checkpoints/evidence review/report; Phase 04 full resume/history/freshness/curated retrieval/reference-aware lifecycle/export/confirmed deletion; Phase 05 full project-visible catalog/domain/multi-server workflows; Phase 06 restricted controller/two-compute diagnostics and gated higher-visibility catalog; Phase 07 local/stdio MCP and real separately approved Pi sessions; Phase 08 integrated evaluations, pinned release thresholds, live/model/observer/operations/rollback evidence. Other phase boundaries remain proposals, not current execution authorization. No stubs for them are required here.

## 6. Security, persistence, audit and recovery contract

### 6.1 Scope and data integrity

ADR B1–B5 constrains this task. Reader credentials and application state have restrictive separate access boundaries; provider credentials are not available to diagnostics, and diagnostic credentials are never given to clients/models. Prefer dedicated Keystone application credentials where supported per FR-043, but no authentication-input source, concrete account/path or inherited HTTP exception is selected here. Independently reviewed transport/credential design is required before use.

New records are explicitly versioned, protected and cloud/project/request scoped, retaining only needed correlation, original/resolved target, permitted action/policy identity, limits, safe intent/outcome/error and observation provenance. Minimal durable manual-request/recovery state is current scope, not a full investigation schema. Required records are durably saved before/after significant enabled execution transitions; full goals/hypotheses/child links and investigation checkpoints follow Phase 03/04 when those features exist.

Minimize/sanitize arguments, errors, nested payloads and text before evidence, audit, CLI, telemetry, reports or any persistence/disclosure sink. Necessary local identifiers remain sensitive, scope-protected and storage-managed; prohibited fields/secrets never persist. Unsupported or unsafely transformable content is withheld explicitly. No raw-error fallback, debug sink, temporary file or truncation boundary may leak secrets. Persisted payload is optional; if retained, its data classification and compliant lifecycle must be explicit before use, without inventing an investigation lifecycle for a manual call. No raw export feature is added.

Atomic replacement/transactional commit, complete writes, initial file/directory creation durability, version/integrity validation and serialized/rejected writers are required. Fail corrupt/incompatible/unsafe state visibly; do not auto-repair or claim resumability/saved success. Restrictive ownership/permissions and path handling must prevent unauthorized reads/replacement/symlink escape. Reusing the old store helper alone does not prove these guarantees.

### 6.2 Audit and failure ordering

1. Validate trusted scope, strict input, available capability and finite limits. Pre-dispatch rejection makes zero tool/SDK/authentication calls; do not construct ambient clients before rejection. Record safe denial/invalid/unavailable outcome when audit is available, with timestamp, tool/version, sanitized arguments/scope, correlation, safe reason, status and duration explicitly not applicable for non-execution.
2. Durably persist sanitized intent before allowed dispatch, including allowed bounded name lookup and any separately dispatched related read. Verify required storage/checkpoint health and safe capacity. If intent/required persistence fails, execute nothing. The intent identifies scope and permitted bounded effects, not an unbounded grant.
3. Perform only the admitted bounded read(s); account for each and check cancellation/current authorization between them. Persist only sanitized observations/state. If response scope is wrong after an authorized read, withhold unsafe output, deny further related reads and audit the true contact rather than asserting zero calls.
4. Durably audit result/outcome before any diagnostic payload reaches client/model. The audit includes required status/timing/provenance, not an automatic copy of full result data. On result-audit failure, stop subsequent work, withhold payload and expose locally a safe failure, known audit gap and possible completed read. A read cannot be rolled back.
5. If a denied request/outcome cannot be audited because the store is unavailable, report the gap locally and never claim the record exists. Local visibility must not depend exclusively on the failed sink. Do not fabricate retrospective events, silently retry ambiguous writes, switch to an unprotected fallback sink or advertise exactly-once behavior.

### 6.3 Recovery, revocation and restart

- Required store/audit/checkpoint failure stops diagnostic admission across processes and restart, not just the failing call's in-memory loop. Preserve known gaps/unresolved intent safely; absence of a writable marker is not proof of health. Acknowledgement state must not silently disappear or be inferred from a successful restart.
- After recovery, remain paused until the operator acknowledges known gaps and uncertain calls. Acknowledgement is not renewed authorization. Recheck current cloud/project/target/capability/profile/policy/limits before another dispatch.
- Re-collecting an uncertain dispatched call requires a separate explicit operator confirmation, current authorization and a new timestamped observation; preserve prior uncertainty/provenance. Do not silently replay, replace prior evidence or claim that a call definitely did not occur. This manual recovery rule does not introduce investigation resume or prescribe a new command/UI.
- A withheld result is releasable only after fault resolution, durable result audit and current authorization; no automatic release to a now-unauthorized requester. If safe recovery of payload is impossible, say so and require the uncertain re-collection rules rather than silently reconstructing it.
- Authorization expiry/revocation during a read stops new dispatch, attempts bounded cancellation/cleanup and withholds results from an unauthorized requester. Audit where possible and explain that collection may already have occurred. Shutdown/cancellation stops later dispatch and cleans up owned resources; it cannot undo collection.

### 6.4 Capacity, retention and cleanup from first use

- Require a finite usable operator-configured protected-data limit; absent/unusable limit fails startup actionably. Count managed records and required retained provenance/control data; reserve/validate capacity so required writes are guaranteed or dispatch stops.
- Detect physical disk exhaustion separately from managed quota, including unmanaged legacy disk use. Clean only safely expired eligible records; never silently delete unexpired data to free capacity. Preserve safe authorized local inspection/export and operator-controlled cleanup where possible without weakening failed required controls; this does not add the deferred rich export/deletion feature.
- Configurable sanitized audit retention defaults to 90 days. Bounded automatic cleanup runs at startup and during operation, not while stopped; restart handles overdue eligible data and reports failures. Before cleanup deletion, durably audit intent; intent failure means no automatic deletion. If outcome auditing fails after deletion, report the gap and possibly completed deletion, not rollback. Do not erase recovery-critical unresolved information merely to permit dispatch.
- The configurable 30-day terminal-investigation default applies when investigation records appear; running/paused and active-dependent evidence are protected. Phase 01 introduces no investigation history/reference graph and cannot delete unknown or referenced records by treating them as terminal. Full active-reference retention accounting, confirmed early terminal deletion and alias-default exports stay Phase 04; applicable present-data safeguards cannot wait for that phase. Audit records never become deletable under a shorter investigation policy.
- Delivery 1 starts only in the new versioned namespace. No runtime read, import, index, disclosure, approval reuse, mutation or cleanup of old Go investigation/memory/workflow/project files. They remain separately protected/operator-managed outside automatic retention. Future migration requires separate approval, versioned testing, backup and rollback, not work in this task.

## 7. Domain outcomes and edge cases

Logical statuses follow the PRD Data and API Contracts: `ok`, `partial`, `error`, `denied`, `validation_error`, `timeout`, `cancelled`, `unavailable`. Version human/JSON semantics and document status translations; do not import the archived seven-status contract or invent exact schema/exit codes as approved requirements.

Every result carries tool/request identity, safe target/arguments, correlation, collection timing/duration (or explicit not applicable), safe structured payload/error, redaction/withholding and truncation metadata, plus evidence/provenance references when present. Exit code is present only when applicable, not a fictitious subprocess result for SDK reads. All eight statuses require fixtures even if some are injected outcomes. Partial evidence/gaps do not imply complete collection, health or diagnosis. Project-summary per-category semantics are reserved for Phase 05; do not build summaries to test the envelope.

| Situation | Required observable outcome |
| --- | --- |
| Valid permitted server and related categories | Only bounded authorized reads; useful sanitized required fields, identity/provenance and durable intent/outcome before disclosure. |
| Malformed/extra input, unknown/generic/mutation tool, scope/profile override | Appropriate validation/denial outcome; zero implementation/auth/API calls; sanitized outcome audit or visible gap. |
| Missing/ambiguous literal name or uniqueness unresolved within bounds | No guessed target GET or unrelated disclosure; clear UUID guidance; lookup may have occurred only under explicit manual authority and durable intent. |
| Wrong returned project/ID or forged relationship | Withhold out-of-scope payload; no subsequent relationship read; record real prior collection/denial rather than false zero-contact claim. |
| Missing/denied required basic field | Explicit field availability/reason; qualify overall result when incomplete; never silently omit or invent the value. |
| Permission failure or optional operator/host/model absence | No stronger credentials or alternate utility; explicit denied/unavailable/partial outcome as applicable; healthy independent manual path remains possible. |
| Timeout, cancellation, exhausted limits or revocation | Finite cleanup, stop later calls, honest status/metadata; unauthorized results withheld, possible prior read acknowledged. |
| Secret-bearing/unsafe content | Safe minimization/redaction before every sink or explicit withholding; no raw echo, including error/truncation/telemetry paths. |
| Intent/checkpoint/result write, corruption, writer, quota or disk failure | §6 ordering, no false save; zero dispatch on failed intent; payload withholding and stop on post-read audit failure; visible gaps and acknowledged recovery. |
| Restart/recovery or intentional later manual request | No implicit replay; acknowledged gaps/current authorization; separate uncertain re-collection confirmation/new observation. A normal intentional new action is newly audited, not an audit-free no-op. |

## 8. Independent requirement and acceptance traceability

Dispositions: `CURRENT_TASK` is a future implementation obligation, not a completed claim; `EXPLICITLY_DEFERRED` names later responsibility within Delivery 1. `ALREADY_ACCEPTED` is not used: no current acceptance evidence was supplied. Educational lessons and future-delivery features are `OUTSIDE_SELECTED_SCOPE`. No `MISSING_OR_CONFLICTING` current product requirement is identified as preventing this bounded draft; unverified mechanisms/environment remain prerequisites, not claimed acceptance. Mixed rows partition a requirement rather than claiming whole-AC completion.

### 8.1 Functional requirements

| PRD ID | Disposition and exact boundary | Future evidence |
| --- | --- | --- |
| FR-001 | CURRENT_TASK manual/readiness; EXPLICITLY_DEFERRED analysis 02, single execution/inspection/report 03, resume 04, project 05. | V1/V12 |
| FR-002 | CURRENT_TASK application-owned one-project scope/target/profile/budget and protected request partitioning; EXPLICITLY_DEFERRED full investigation/child records 03–05. | V2/V3/V10 |
| FR-003 | CURRENT_TASK manual UUID/literal exact name, original/resolved identity and guidance; EXPLICITLY_DEFERRED separate pre-plan lookup authorization flow 03. | V4 |
| FR-004–FR-008 | EXPLICITLY_DEFERRED planner/approval/graphs/agent control 03/05, structured inference foundation 02. No current plan/agent execution. | V1 disabled paths; later contracts |
| FR-009 | CURRENT_TASK deterministic dispatch/no denial retry or credential fallback; EXPLICITLY_DEFERRED orchestrator task transitions 03/05. | V2/V7 |
| FR-010 | CURRENT_TASK actual-boundary checks, current authorization and revocation/withholding; EXPLICITLY_DEFERRED enabled nested/resumed/delegated/MCP integrations 03–07. | V1–V3/V7 |
| FR-011 | CURRENT_TASK narrow verified flavor/port categories only; EXPLICITLY_DEFERRED approved plan categories 03, full network/volume relationships 05; no inferred host/project-wide grant. | V5 |
| FR-012–FR-013 | EXPLICITLY_DEFERRED server/boot workflow 03, domains/multi-target synthesis 05 and host support 06. | V1 disabled paths; later scenarios |
| FR-014 | CURRENT_TASK durable enabled manual intent/outcome/provenance/core recovery records; EXPLICITLY_DEFERRED full goals/approval/task/hypothesis/child checkpoints 03–05. | V8–V10 |
| FR-015 | CURRENT_TASK uncertain manual re-collection confirmation/new observation as required by FR-028; EXPLICITLY_DEFERRED investigation resume/terminal lifecycle 04. | V9 |
| FR-016 | CURRENT_TASK timestamped collected evidence, no implicit current-state claims; EXPLICITLY_DEFERRED 15-minute freshness enforcement/overrides in investigations 03, summaries/history/refresh 04. | V6; no history/retrieval now |
| FR-017 | CURRENT_TASK no automatic knowledge/archive ingestion and no optional-knowledge dependency; EXPLICITLY_DEFERRED curated runbook 03, bounded retrieval 04, MCP resources 07. | V1/V11/V12 |
| FR-018 | CURRENT_TASK request/output text cannot change authority; EXPLICITLY_DEFERRED model/retrieval/delegated-content paths 02–07. | V2/V6 |
| FR-019–FR-020 | CURRENT_TASK truthful collection limitations, not diagnostic confirmation; EXPLICITLY_DEFERRED analysis 02, evidence-reviewed reports 03/05, historical exports 04. | V5/V6 |
| FR-021 | CURRENT_TASK observer target/readiness/design documentation; EXPLICITLY_DEFERRED actual deployed separation/reachability proof 08. | V3/V12; live not claimed |
| FR-022 | CURRENT_TASK dedicated project reader/no stronger fallback and access separation; EXPLICITLY_DEFERRED operator/SSH enablement 06, cloud-side live policy proof 08. | V2/V3 |
| FR-023–FR-024 | CURRENT_TASK reviewed registry, strict validation, fixed Go implementation and actual boundary; EXPLICITLY_DEFERRED host catalog 06 and MCP adapter 07. | V1/V2/V7/V12 |
| FR-025 | CURRENT_TASK server basics including fault/flavor and explicit required field states, narrow related reads; EXPLICITLY_DEFERRED full project/network/volume 05 and scheduler/Placement/capacity/agent/log catalog 06. | V4/V5 |
| FR-026 | CURRENT_TASK host unavailable/not enabled, no arbitrary host dispatch; EXPLICITLY_DEFERRED fixed host operations/windows/controller+two-compute validation 06/08. | V1/V2 |
| FR-027 | CURRENT_TASK eight statuses, safe target/correlation/duration/truncation; EXPLICITLY_DEFERRED project-summary category rules 05 and later adapter parity 06/07. | V6/V7 |
| FR-028 | CURRENT_TASK durable intent/result, denial gaps, stop/withhold, acknowledged recovery and uncertain-call rules from first manual use. Full investigation recovery extension remains 04, not a waiver. | V8/V9 |
| FR-029 | CURRENT_TASK minimization/sanitization before every enabled sink, protected needed local IDs; EXPLICITLY_DEFERRED model aliases/disclosure 02, protected export/history 04, client disclosure 07. | V6/V10 |
| FR-030 | CURRENT_TASK no mutation capability, even on operator insistence; EXPLICITLY_DEFERRED model fix-it plan/recommendation UX 02/03. | V1/V2/V6 |
| FR-031–FR-034 | CURRENT_TASK model paths disabled, manual independence; EXPLICITLY_DEFERRED both tested harnesses/disclosure/isolation/egress/outage/revocation 02, full persisted local report behavior 03/04, real acceptance 08. | V1/V3/V12 |
| FR-035 | EXPLICITLY_DEFERRED required local/stdio MCP 07, after manual trust; no network MCP in Delivery 1. | V1 disabled path |
| FR-036 | EXPLICITLY_DEFERRED disabled-specialist release proof 05; enablement not selected and requires separate evaluated proposal. | V1 no specialist path |
| FR-037–FR-038 | CURRENT_TASK deterministic versioned manual scenario/result seeds; EXPLICITLY_DEFERRED full evaluator/quality/resource scoring 03/05/08. | V12 |
| FR-039 | CURRENT_TASK correlated tool/request/audit events without secrets/hidden reasoning; EXPLICITLY_DEFERRED model/task/project/review/resume pipeline 02–08. | V6/V8 |
| FR-040 | CURRENT_TASK finite enabled diagnostic budgets; EXPLICITLY_DEFERRED model/token/cost 02 and run/project/session limits 03/05/07. | V7 |
| FR-041 | CURRENT_TASK required/optional readiness, usable finite storage limit and mandatory-control failure; EXPLICITLY_DEFERRED adapters/domain/lifecycle readiness extensions 02/04/06/07, release operation 08. | V1/V3/V10 |
| FR-042 | CURRENT_TASK safe shutdown, basic reader-revocation/store/recovery/operator guidance; EXPLICITLY_DEFERRED full data lifecycle 04, live rotation/rollback exercises 08. | V7/V9/V12 |
| FR-043–FR-044 | CURRENT_TASK one Go diagnostic executable, reader/endpoint prerequisites, fixed read-only mapping, tool-local validation and minimized structured data; EXPLICITLY_DEFERRED full catalog 05/06, harness packaging 02, live proof 08. | V2/V3/V5/V12 |
| FR-045 | CURRENT_TASK diagnostic naming/no generic primitives; EXPLICITLY_DEFERRED model diagnostic-only instructions 02/03 and MCP prompts 07. | V1/V2 |
| FR-046 | CURRENT_TASK named manual selection/execution/shared-boundary guidance; EXPLICITLY_DEFERRED protected paste analysis 02 and automated/MCP parity 03/07. Independent external sharing is not protected by this product. | V1/V12 |
| FR-047 | EXPLICITLY_DEFERRED separately approved bound standalone MCP sessions/egress/lifetime 07; no session scaffolding. | V1 disabled path |
| FR-048 | CURRENT_TASK applicable 90-day audit default, bounded startup/runtime audited cleanup/protected data; EXPLICITLY_DEFERRED terminal investigations' 30-day policy as introduced 03 and full active-reference lifecycle 04. | V10/V11 |
| FR-049 | CURRENT_TASK finite usable limit, physical disk-full, fail-closed writes/no silent eviction and safe local access where possible; EXPLICITLY_DEFERRED confirmed early deletion and protected alias/identifier export UX 04. | V10/V11 |
| FR-050 | CURRENT_TASK new versioned store, no legacy data read/import/index/send/cleanup or approval reuse; EXPLICITLY_DEFERRED isolation regressions/release rollback integration 04/08. Future migration OUTSIDE_SELECTED_SCOPE. | V1/V11 |

### 8.2 Non-functional requirements

| PRD ID | Disposition / observable obligation | Future evidence |
| --- | --- | --- |
| NFR-001 | CURRENT_TASK zero unauthorized execution, mutation or prohibited disclosure across retained paths; later adapters must preserve it. | V1–V12 |
| NFR-002 | CURRENT_TASK restrictive separated reader/state/caller domains, required routes only; EXPLICITLY_DEFERRED enabled model/host/client proofs 02/06/07 and deployed integration 08. | V3 |
| NFR-003 | CURRENT_TASK finite call limits/cancellation/cleanup/no later dispatch; EXPLICITLY_DEFERRED broader run budgets 02–07. | V7 |
| NFR-004 | CURRENT_TASK atomic/transactional durable enabled records, corrupt/version refusal, serialized/rejected writers; EXPLICITLY_DEFERRED full investigation resume 04. | V9/V10 |
| NFR-005 | CURRENT_TASK cloud/project/request visibility and no authorization by common name; EXPLICITLY_DEFERRED memory/knowledge/approval history partitions 03–05/07. | V3/V4/V10/V11 |
| NFR-006 | CURRENT_TASK structured bounded errors/no fallback/mandatory-control stop, manual independence; EXPLICITLY_DEFERRED required three-host live and complete report behavior 06/08/03–04. | V6–V10/V12 |
| NFR-007 | CURRENT_TASK do not equate successful read with health/root cause; EXPLICITLY_DEFERRED evidence-review/scenario diagnosis quality 03/05/08. | V5/V6 |
| NFR-008 | CURRENT_TASK safe auditable outcomes, timestamps/correlation/duration or explicit not applicable; EXPLICITLY_DEFERRED full pipeline provenance 03–08. | V6/V8/V9 |
| NFR-009 | EXPLICITLY_DEFERRED measured model/resource metrics and pre-pinned release thresholds 02/03/05/08; no SLA/cost claim now. | Later release evidence |
| NFR-010 | CURRENT_TASK versioned manual semantics and no unrelated lab disruption; EXPLICITLY_DEFERRED enabled automated/MCP parity/release integration 03/05/07/08. | V1/V12 |
| NFR-011 | CURRENT_TASK reviewed tool contracts/classification/offline safety/scenario extension without generic execution. | V2/V5/V12 |
| NFR-012 | CURRENT_TASK minimization/redaction/storage access/lifecycle; EXPLICITLY_DEFERRED remote consent/aliasing/egress 02/07 and richer lifecycle 04. | V3/V6/V10/V11 |
| NFR-013 | CURRENT_TASK diagnostic intent, concise human/versioned JSON output, explicit gaps/truncation and no health confusion; EXPLICITLY_DEFERRED proposal/report/export UX 02–05/07. | V1/V5/V6 |
| NFR-014 | CURRENT_TASK single-executable/offline validation and independently stoppable external-observer design; EXPLICITLY_DEFERRED real reproducible install, both external harness and deployed isolation evidence 02/08. | V3/V7/V12 |
| NFR-015 | CURRENT_TASK deterministic credential-free safety/CLI/API fixtures; EXPLICITLY_DEFERRED separately authorized real cloud/model acceptance 06–08. | V12 |

### 8.3 Acceptance criteria

Whole-Delivery AC closure remains the overview's later integration responsibility. A current subset below is not a full passing AC.

| AC | Disposition and selected contribution / later closure | Future evidence |
| --- | --- | --- |
| AC-001 | EXPLICITLY_DEFERRED exact-plan single/multi execution and separate pre-plan lookup 03/05; no current plan feature. | V1 disabled paths |
| AC-002 | CURRENT_TASK manual canonical UUID/literal names/case/whitespace/ambiguity/missing/original-resolved/UUID guidance; EXPLICITLY_DEFERRED investigation identity integration 03. | V4 |
| AC-003 | CURRENT_TASK invalid/unknown tool and finite call subset; EXPLICITLY_DEFERRED structured decisions/graphs/loops 02/03/05. | V2/V7 |
| AC-004 | CURRENT_TASK actual-boundary wrong-scope and legitimate-related-read fixtures; EXPLICITLY_DEFERRED enabled nested/resumed/delegated/MCP full parity 03–07. | V2/V3/V5 |
| AC-005–AC-006 | EXPLICITLY_DEFERRED domain findings and multi-target dependencies 03/05/06; manual evidence is not diagnosis acceptance. | Later scenarios |
| AC-007 | CURRENT_TASK corruption/write/writer-conflict core subset; EXPLICITLY_DEFERRED complete checkpoint/resume/terminal/approval cases 04. | V9/V10 |
| AC-008–AC-010 | EXPLICITLY_DEFERRED freshness/history/curated retrieval/evidence-review closure 03–05; current sanitization/provenance are prerequisites only. | V6/V11 |
| AC-011 | CURRENT_TASK observer/reader/no-fallback design and synthetic security-context tests; EXPLICITLY_DEFERRED deployment/policy/mutation-denial record 08 (host contribution 06). | V3/V12 |
| AC-012 | CURRENT_TASK manual/public retained-path validation/Go-only boundary; EXPLICITLY_DEFERRED enabled automated/MCP parity 03/06/07. | V1/V2 |
| AC-013 | CURRENT_TASK host unavailable/no fallback only; EXPLICITLY_DEFERRED fixed windows/operations and required live three-host proof 06/08. | V1/V2 |
| AC-014 | CURRENT_TASK all eight statuses, duration/correlation/truncation, intent/result faults, visible gaps, withholding and acknowledgement; EXPLICITLY_DEFERRED partial project-summary categories 05/full adapter parity 07. | V6–V9 |
| AC-015 | CURRENT_TASK secret canaries/no mutation including override requests; EXPLICITLY_DEFERRED model fix-it plan/runbook-cited manual recommendations 02/03, integrated release proof 08. | V2/V6 |
| AC-016–AC-017 | CURRENT_TASK no model initialization/credential sharing and separation constraints; EXPLICITLY_DEFERRED both harness/real-model and independent deployed model isolation acceptance 02/08. | V1/V3/V12 |
| AC-018 | CURRENT_TASK manual no-model independence; EXPLICITLY_DEFERRED provider revocation/outage/late-response/report cases 02–04. | V1/V12 |
| AC-019–AC-020 | EXPLICITLY_DEFERRED real approved local MCP/Pi sessions 07 and disabled-specialist evaluation branch 05. No current scaffolding/enablement. | V1 disabled paths |
| AC-021–AC-022 | CURRENT_TASK versioned manual fixture seeds, tool events/bounds/cancellation; EXPLICITLY_DEFERRED full evaluator/usage/pipeline evidence 03–08. | V6/V7/V12 |
| AC-023 | CURRENT_TASK readiness/mandatory-store stop/shutdown/recovery guidance and offline faults; EXPLICITLY_DEFERRED full lifecycle/credential/rollback operation exercises 04/06/07/08. | V7/V9–V12 |
| AC-024 | CURRENT_TASK new-store/legacy protection, applicable manual compatibility and no lab changes; EXPLICITLY_DEFERRED full delivery/lab/rollback integration 04/05/07/08. | V1/V11/V12 |
| AC-025 | EXPLICITLY_DEFERRED pinned evaluation matrix/corpus/rubric/thresholds and real lab investigation 08, exploratory contributions 03/05; no fixture-as-live claim. | Later release record |
| AC-026 | CURRENT_TASK target observer/project-reader prerequisites; EXPLICITLY_DEFERRED live project-resource/server-network/three-host/disposable mutation-denial record 05/06/08. | V3/V12 |
| AC-027 | CURRENT_TASK server basics fields/availability/read-only/input/static/behavioral subset; EXPLICITLY_DEFERRED full project/network catalog 05 and higher-visibility/host catalog 06. | V4/V5/V12 |
| AC-028 | CURRENT_TASK named manual select/execute/shared-boundary docs; EXPLICITLY_DEFERRED sanitized copy-paste/approved harness analysis 02 and full entry parity 07. | V1/V12 |
| AC-029 | CURRENT_TASK utility-free single-runtime diagnostic fixture proof; EXPLICITLY_DEFERRED deployed package/both harness/MCP/non-root isolation/client egress record 02/06/07/08. | V3/V12 |
| AC-030 | CURRENT_TASK manual lookup/relationship/revocation/cancellation/withholding subset; EXPLICITLY_DEFERRED plan/session lifetimes and model alias/disclosure 02/03/04/07. | V4/V5/V7/V9 |
| AC-031 | CURRENT_TASK finite limit vs real disk-full, applicable audit/default cleanup, intent/outcome faults and legacy isolation; EXPLICITLY_DEFERRED full terminal/active-reference lifecycle/confirmed deletion/alias-export cases 03/04, release integration 08. | V9–V11 |

## 9. Future implementation verification contract

Everything in this section is **PLANNED_NOT_RUN**. Tests must use highest practical public CLI/gateway/API seams with recording fakes and synthetic state/credentials. Existing helper tests alone do not establish closure. No live/cloud/model/SSH/MCP call or destructive working-lab probe is implied.

| ID | Required scenarios / seam | Observable acceptance |
| --- | --- | --- |
| V1 ingress/no bypass | Actual manual/help/readiness and all inventoried retained/disabled command branches; authentication, inference, legacy-store and raw-dispatch traps. Inspect new callers too. | One executable; enabled diagnostics reach the boundary; disabled features reject before any trapped side effect; help has no lookup; optional model/knowledge/host absence does not disable healthy manual operation. |
| V2 registry/denial | Unknown/generic/mutation tool, missing/forged context, extra/malformed arguments, caller implementation/host/endpoint/profile/budget overrides, direct registry/tool route attempts; valid counterpart. | Strict fixed definitions/tool-local checks; every pre-dispatch denial causes zero downstream implementation/auth/API calls, with safe denial audit or visible gap. No stronger fallback/retry. |
| V3 authority/security domains | Forged local caller, cloud/project/target/profile mismatch, project switch/stale context, unauthorized credential/state access, endpoint/redirect/pagination escape; actual target-OS fixture security contexts where correctness depends on them. | No unauthorized tool execution/credential access; no cross-project disclosure, token forwarding or inferred grants; document configured scope independent of input. Synthetic tests do not prove deployed reader policy. |
| V4 identity | UUID, literal exact name, meaningful leading/trailing/internal whitespace, case mismatch, supported Unicode, malformed/unsupported representations, missing/duplicate names, approximate API matches, lookup bound exhaustion; no-help-lookup. | Original/resolved identity preserved; no trim/case folding/guessed GET; no unrelated candidate disclosure; audited bounded authorized lookup, explicit UUID guidance. No implicit pre-plan authorization. |
| V5 relationships/projections | Required basic fields each available/denied/unavailable/not-applicable; available/absent/secret fault; referenced flavor, wrong/changed flavor, valid/foreign/wrong-device ports, forged IDs and missing relationship proof. | Minimal safe fields or explicit states; correct target/project/relationship checks before downstream reads; no extraspec/host/project-wide/network-subnet traversal or healthy inference from gaps. |
| V6 sinks/result contract | Every eight-status envelope, partial/manual gaps, safe errors, correlation/time/duration/not-applicable, no fictional subprocess exit, truncation/redaction combinations; nested/text/error secret canaries, hostile instructions, invalid encoding and oversized input. | Versioned human/JSON semantics; zero prohibited disclosure across CLI/audit/evidence/control/telemetry/temp sinks; minimization/sanitization before sinks; unsafe content withheld, not echoed. |
| V7 bounds/races | Deadline/cancel before/between/during reads, streamed floods, endless/hostile pagination, finite requests/retries/resources/output, authorization expiry/revocation during read, shutdown. | Bounded cleanup and closed resources; no later dispatch or denial retry, unauthorized payload withheld; possible prior read reported, not undone. |
| V8 audit order/faults | Recording reader/store sequence; intent failure and ambiguous append; result audit failure after read; denied audit failure; unsafe raw-error paths. | Durable intent precedes each admitted dispatch, result audit precedes disclosure; failed intent means zero calls, failed outcome means stop/withhold/local gap; no phantom audit, fallback sink or duplicated ambiguous event. |
| V9 crash/acknowledgement | Independent processes/restart; interruption before dispatch, in-flight, after read/before result audit; known gap with unwritable marker; recovery without ack, ack with revoked rights, ack without recollection confirmation, fully confirmed recollection. | Preserve uncertainty across restart; no automatic admission/replay; ack required but not authority; separate confirmation/current authorization/new observation for uncertain collection. Withheld payload released only under §6.3 or explicitly unavailable. |
| V10 persistence/capacity | Actual temporary-filesystem first creation/reopen, partial write/flush/file+directory-sync/rename failure, permission/path/symlink attack, corrupt/incompatible version, concurrent independent writers, finite-limit missing/unusable/exhausted, actual disk-full distinct from quota. | Complete atomic/durable state or honest refusal; writer serialization/rejection/no interleaving; failure prevents dispatch/saved-success; disk pressure cannot trigger silent unexpired eviction. Use real OS/filesystem evidence as well as fault hooks. |
| V11 lifecycle/legacy | Controlled clock 90-day audit default, configurable retention, bounded startup/runtime cleanup and overdue restart; cleanup intent failure and post-delete outcome failure; unknown/active/reference protection; legacy fixtures and old approvals, legacy disk consumption. | Eligible deletion only with durable intent; no premature audit or active-dependent deletion; outcome gap/possible deletion honest; no read/index/send/import/cleanup/reuse of synthetic legacy data and unchanged content hashes. Current implementation must not inspect real legacy records to test this. |
| V12 manual/scenario/package/compatibility | End-to-end manual CLI → boundary → controlled API fixtures → sanitized audit/result; healthy-server, permission-denied, hostile/secret evidence; versioned expected/actual result records; controlled utility/interpreter-free environment. | Useful model-independent server diagnostic and named gaps; fixed built-in Go reads only, no mutation; artifact/config/prerequisites and disabled capabilities documented. No unrelated lab automation changes or claim of full Delivery 1 acceptance. |

Use existing Go HTTP fixture conventions (`httptest`), recording readers and temporary files/processes, with synthetic values and local transports. Do not substitute mocks for OS durability/access-boundary properties or confuse a post-read response denial with a zero-contact pre-dispatch denial. Use a bounded filesystem test environment for actual exhaustion, not the working repository or lab disk. Test mechanisms must not become public path/policy overrides.

For separately authorized implementation, first inspect available toolchain/dependencies and test side effects without auto-install/download or credential access. The module declares Go 1.27.1; missing required tooling is reported, not silently downgraded. From `aiops/`, focused relevant checks will include `rtk go test ./internal/tools ./internal/scopedtools` plus actual changed CLI/safety/store packages as discovered, then required repository Go verification `rtk go test ./...` and `rtk make build` after build consolidation. Format only changed Go files with `rtk gofmt`; include appropriate vet/race checks and independent-process/crash tests for new concurrency/persistence. Exact new package/test/packaging commands must be recorded by the future executor, not fabricated as existing commands here. Full build must prove the one-runtime output, not accept today's four binaries as compliance.

Review static read-only/mutation/input/privilege/unsafe-file patterns and supplement with behavior tests; source scans alone cannot prove safety. Root Make/Molecule/Ansible targets load environment/contact systems or can mutate resources; they are not offline wrappers. Any applicable lab regression must be separately scoped/authorized, or reported not run—not silently represented as passing. Live reader policy/mutation-denial checks require explicit disposable scope, preflight and cleanup owner and are never diagnostic tools.

## 10. Implementation authority and open questions

- **LEVEL_0 after separate execution authorization:** Routine compile/debug/format/test/fixture construction and substantiated in-scope repairs; no repeated permission between routine steps.
- **LEVEL_1 after the remaining preflight and execution-authorization gates:** Internal packages/CLI spelling/schema representation; compliant strict validators, sanitizer implementation, finite documented per-tool limits; reviewed local IPC/OS separation and protected persistence mechanisms that meet G1–G4. Record meaningful tradeoffs and concrete safety realization before affected execution. No particular transport, principal, path, auth source or storage technology is implicitly approved by this contract.
- **LEVEL_2:** Product behavior/identity semantics changes, weakened auth/audit/isolation/privacy/lifecycle, material new security risk, approved architecture changes, expanded catalog/privilege/scope/infrastructure, automatic legacy migration, deployment/credentials/live access or destructive probes. Stop dependent work and state exact question, evidence, alternatives/tradeoffs, recommendation and safe independent work. Difficulty or multiple compliant mechanisms alone are not Level 2.

No genuine Level 2 product-rule change is identified as necessary for this bounded documentation. Concrete feasibility, independently trusted configuration, mechanism approval and live acceptance evidence remain unresolved prerequisites, not certified by a draft. If a safe realization cannot meet the contract, escalate its precise required change rather than selecting a weaker mechanism or resurrecting archived exceptions.

## 11. Completion criteria and required future evidence

Future implementation completion requires all selected Phase 01 behavior, not merely a facade/happy path or green old suite:

- Actual one-executable manual/readiness flow, complete current entry inventory with safe disabled paths, authenticated actual-boundary enforcement and zero unauthorized execution/mutation/prohibited disclosure.
- Exact identity/projection/relationship outcomes, versioned eight-status semantics, finite execution and cancellation/revocation behavior.
- Durable sanitized intent/outcome, payload withholding, honest gaps, recovery acknowledgement and separate uncertain re-collection confirmation.
- Protected new versioned data, first-use integrity/writer/capacity/cleanup safeguards, distinct disk-full handling and untouched/unused legacy records and approvals.
- Reviewed applicable G1–G4 realization and actual V1–V12 evidence; all focused/full required Go checks run successfully, with any separately authorized lab/live gaps explicitly distinguished from offline acceptance. Missing mandatory offline verification prevents completion.
- Operator guide covering observer/setup ownership, reader scope/no fallback, registry, field gaps, limits, audit failure/recovery acknowledgement, storage/cleanup/legacy isolation, safe stop, future gates and limits of independent sharing. No provisioning automation, inferred endpoints or secret examples.

The future executor reports exact base/candidate/status and source/approval fingerprints; changed components/entry map; requirement/evidence matrix; significant Level 1 choices; commands/results/test counts and failures/skips/not-run reasons; no-model fixture demo; actual OS/crash/recovery/capacity evidence; complete tracked/staged/untracked diff/security review; incompatibilities, limitations and unresolved gates. No secret, real credential/configuration or raw protected record belongs in Git.

Future execution verdicts may be `READY_FOR_REVIEW`, `BLOCKED` or `INCOMPLETE`; none is granted here. Self-check is not independent review. The reviewed candidate has received owner approval as recorded above; it was uncommitted at the approval-record update. Commitment, separately requested implementation preflight and separately authorized execution remain distinct gates. Approval does not automatically authorize implementation, Phase 02, product tests, deployment or live access.

## 12. Sources, legacy comparison and authoring limits

Current sources read completely: `.agents/AGENTS.md`; current PRD and learning baseline; overview and all eight phase files. Current README/architecture were read completely for lab context. Selected code/test files and anchors are in §2; reading engine/adapter seams was targeted, not an exhaustive code or threat audit. No current acceptance record was discovered under `docs/ai-ops-go/`.

External `002-instruction-ai-ops-go-phase01-specification-authoring.md` and paired handoff were read completely, as were the historical `001` pair, under `/home/meriz/Documents/Synctech.ID/Etc/goose/handoff-openstack-aiops/`. The `001` review instruction was not re-executed; the legacy `aiops-prompt.md` was not followed. The present user supplies explicit authoring authority absent from those prepared packets.

Only specifically relevant archived compatibility contracts were read completely, all under `docs/archive-dont-look-here/aiops-go/`:

- `architecture/01-go-owned-safety-boundary-adr.md` and `tasks/01-go-owned-safety-boundary-task.md`;
- `architecture/01-go-owned-safety-boundary-env-auth-amendment.md` and `tasks/01-go-owned-safety-boundary-env-auth-amendment.md`.

They are historical candidates, not current requirements, approval or implementation authority. They describe three diagnostic tools, seven outer statuses, older phase allocations, fixed deployment/audit identities/paths, restricted identifiers and specific auth/HTTP exceptions. None is imported into this narrower Phase 01 contract. This task does not supersede/amend/revive their independent runtimes or inspect their actual protected data. The current PRD's eight statuses, literal meaningful-whitespace semantics, current phase allocation and first-use lifecycle govern. No legacy implementation contract is copied as the new task.

The ADR is justified by the material ownership/admission/disclosure/persistent-health boundaries B1–B5 needed to prevent the observed direct-registry and storage shortcuts. It does not merely approve a mechanism from the roadmap. Both documents preserve the same constraints: task §§4/6/7 and ADR §§2–3; task §3/10 and ADR §6 preserve gate/decision authority. Any wording change must be checked in both documents.

Authoring checks concern document completeness, source consistency, references, full new contents, whitespace and repository state only. No Go tests/build/formatters, cloud/SSH/model/MCP call, `.env`/credential read, product check, provisioning, stage/commit/push or deployment was performed as authoring evidence. The subsequent independent draft review and owner approval are recorded above; they are not implementation acceptance.

**End of task contract.**
