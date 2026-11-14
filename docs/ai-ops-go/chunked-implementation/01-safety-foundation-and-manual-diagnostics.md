# Phase 01 — Safety Foundation and Manual Diagnostics: Single Implementation Plan

## 1. Identity, outcome and authorization

**Planning status: PLAN_READY.** This is the planning author's self-assessment, not independent plan acceptance, implementation authorization, deployed validation or release approval. A subsequent separately authorized independent implementation preflight returned `PREFLIGHT_PASS`; its complete response and evidence boundary are recorded in §14. The verdict is separate from the planning status and does not authorize execution.

- **Mode:** `single-implementation-plan / SINGLE_PLAN`; execution mode **UNSELECTED**.
- **Selected contract:** [Phase 01 task](../tasks/01-safety-foundation-and-manual-diagnostics.md), four roadmap steps and [§01.6](../implementation-plan/01-safety-foundation-and-manual-diagnostics.md#016-phase-definition-of-done), not all Delivery 1.
- **Project mode:** existing project with partial implementation; no existing behavior is classified accepted from source inspection alone.
- **Sole controlling ladder:** this file, `docs/ai-ops-go/chunked-implementation/01-safety-foundation-and-manual-diagnostics.md`, Chunks 0–21. Roadmap steps are scope/design inputs, not a second executable ladder. No candidate technical ADS was supplied or discovered in the current source tree.
- **Authorization:** the invoking user explicitly authorized the action in the external `004` instruction and selected this directory and phase-index filename convention. That authorizes exactly this new plan and its planning report; it does not authorize executing any chunk, reviewing independently, running preflight, committing or deploying.
- **Planning revision:** initial one-file candidate at the repository identities below; no timestamp or unavailable session identity is invented.
- **Access limits:** current requirements/task/ADR, roadmap, specified historical contracts and relevant code are available. The original review transcript/report and pre-update draft files were not independently supplied; historical review/approval provenance is attributed to the packet and committed headers. Toolchain, filesystem fixture facilities, deployed identities/configuration and all product behavior are unverified.

Smallest useful outcome:

```text
explicit authenticated manual server-basic action + trusted project/target/grants/limits
  -> one credential-owning Go boundary -> durable sanitized intent
  -> bounded read-only server and explicitly permitted related flavor/port reads
  -> minimized sanitized durably audited evidence -> versioned JSON / concise human result
```

Successful collection is not proof of health or root cause. Unknown, denied, unavailable, truncated and withheld evidence remains visible. Mandatory policy/audit/store failures disable admission, not merely inference.

## 2. Sources, candidate verification and freshness

### 2.1 Observed Git state

All observations in this section were actually made during planning using read-only commands; no tests/builds/formatters were executed.

| Item | Observation |
| --- | --- |
| Project root | `/home/meriz/Documents/Synctech.ID/CI_CD/openstack-lab` |
| Branch | `aiops-go-phase01` |
| HEAD / tree | `ae7983c9af3a243ac4b1b104f6949d3afa56f6e1` / `1965507f8b104f0ba2ed92586a51d951413ff467` |
| Parent / subject | `e29fa87e293246c187f5b01604e6f012dfbb4761` / `docs(ai-ops): approve Phase 01 safety contract and ADR` |
| Initial worktree/index | Full porcelain with all untracked files empty; staged/unstaged name-status empty. |
| Candidate delta from parent | Exactly 11 added Markdown files: overview, phases 01–08, task and ADR. No application delta in this commit. |
| Destination | User-selected `chunked-implementation/` exists, empty by both listing and full bounded find; no execution plan exists under the suggested `execution-plans/` location. No controlling plan/progress is overwritten. |
| Enclosing repository | `/home/meriz/Documents/Synctech.ID`, `main`, HEAD `74c01ca9de6c2153a0306b037860bfe3c276b649`, tree `479ab2554139c368375a6a7aa77c4e97e75fb2f7`. Separate repository, unchanged by this work. |
| Enclosing pre-existing work | Modified `Etc/goose/handoff-openstack-aiops/aiops-prompt.md` and `Etc/skills/README.md`; untracked handoff/instruction pairs 001–004; no staged changes. Preserve all. The prompt was neither read as instructions nor executed. |

Observed commands, working directory project root unless `-C` identifies the enclosing repository: `rtk git branch --show-current`, `rtk git rev-parse HEAD 'HEAD^{tree}'`, `rtk proxy git status --porcelain=v1 --untracked-files=all`, staged/unstaged `rtk git diff --name-status`, `rtk proxy git ls-files -- docs/ai-ops-go`, `rtk proxy git log -1 --format='%H%n%P%n%s'`, `rtk proxy git show --stat --oneline HEAD`, parent-to-HEAD name-status, `rtk proxy git ls-tree HEAD` for the sources, and `rtk proxy sha256sum` for every current source below. These distinguish committed blobs, working bytes and untracked state; a commit alone does not establish approval.

### 2.2 Controlling source fingerprints

Paths in this table are relative to `docs/ai-ops-go/`. The measured SHA-256 values match the `004` packet. Task and ADR Git blobs were checked against HEAD; a clean worktree and the measured working bytes bind this plan to that committed candidate.

| Source | SHA-256 | Authority / inspection |
| --- | --- | --- |
| [PRD](../prd.md) | `a685452c2b2d7303a342376117299d777131fd4ff6dfd3ffc19dd397974da9ed` | Product truth, owner-approved `scope_ready`; read completely, including decisions, tests, ACs and ending. Blob `37a7a291d27934a6fa19d71eb4a7f7e250df786f`. |
| [Baseline](../aiops-baseline.md) | `cd03daa694691852842d4812b983cdbd220fba205d02d318d4f57ca9e9503e01` | Educational context only; final curriculum through ending inspected, not the entire educational discussion. Blob `d3049659d9d40b6b7cb7012f57d02cbe579693a8`. |
| [Overview](../implementation-plan/00-implementation-overview.md) | `92bd72c67805ff2f8350dc6bcff5f7228f6b262e6e20d9fd3c627d8ebd31b1f0` | Proposed roadmap; read completely. Specific later Phase 01 approval supersedes its historical statement of no supplied boundary approval, not the status of other phases. |
| [Phase 01](../implementation-plan/01-safety-foundation-and-manual-diagnostics.md) | `3f489644009010e68077749dbcc9d4cb983dd87bb83747cf46b912bf1cb20f14` | Owner-approved scope/decomposition; read completely. |
| [Task](../tasks/01-safety-foundation-and-manual-diagnostics.md) | `977965efc06c760ce13c70b6547ac04ddf4ff2c25fd93a252e5550db7d0d5133` | Approved bounded contract, read completely; blob `469814bee1c8bb30a52b1461b8efbb04de62e4f3`. |
| [ADR](../architecture/01-manual-diagnostic-enforcement-and-persistence-boundaries.md) | `e1f8fb358ff230f5ff1812404bc24fba5d1906d796179d8c1a93cae9b521781d` | Approved B1–B5 constraints, read completely; blob `de9ad8d08bf305a30202168888f14fb393426da4`. |
| [Phase 02](../implementation-plan/02-inference-isolation-and-manual-analysis.md) | `4c0d3e973e8dc32448cf764709c3647eb07d726eac251c299c341c1042ca00bc` | Later roadmap proposal; read completely for dependencies/deferrals. |
| [Phase 03](../implementation-plan/03-approved-bounded-investigations.md) | `4387a26bca9af75b467a948b533d11afccae8054350e4b82cf58f44ae40cfeba` | Same later-proposal status. |
| [Phase 04](../implementation-plan/04-durable-state-knowledge-and-data-lifecycle.md) | `b564539fa265b0579e9e5c5d2337e1c2dff1b7067397bc3451c37c075f9fef89` | Same later-proposal status. |
| [Phase 05](../implementation-plan/05-domain-workflows-and-project-orchestration.md) | `a3ae87b7fe64e8b159f7edaab6a86a3af80d7ab4c8228e28a8356cc02093ef56` | Same later-proposal status. |
| [Phase 06](../implementation-plan/06-restricted-host-and-operator-diagnostics.md) | `4b6fab61c9663cb42902522aaa7867581bc4959367c5170bcca3c48e15e7ab07` | Same later-proposal status. |
| [Phase 07](../implementation-plan/07-local-mcp-and-approved-client-sessions.md) | `f2f683cbd170f93f151367affc2350936c03fe6bb73d4e1fce5bac090c27c335` | Same later-proposal status. |
| [Phase 08](../implementation-plan/08-evaluation-acceptance-and-lab-rollout.md) | `27f09c98b37af72d9cf20965a61e8203632008303d650e43fb0a1e2f61b096fa` | Same later-proposal status. |

**Review and approval are separate facts.** The `004` pair reports a fresh independent initial review returning `DRAFT_SPEC_READY` for task `3566e2e2dc32a35681f57f394b678e7427dbe84ba5de67933019ac59c1468488` and ADR `67218412cb5bbac8ca290fd65ee64f9f0d646de504825071a73701c36199fc5d`. Those are pre-approval-update bytes, not today's hashes. Current headers quote the user's approval of both documents and explain status/provenance updates; their historical “uncommitted at update” wording is not a claim that today's files remain untracked. The full committed content was inspected, including remaining gates. The original reviewed bytes were not supplied in the packet or retrieved during this inspection, so no independent byte-by-byte update comparison or new independent review is claimed here.

**Freshness classification: NONMATERIAL_CONFIRMED relative to the recorded `004` committed candidate.** There is no HEAD/source/approval-byte drift from that packet. The older review applies only to its original hashes; the packet's explanation of approval updates is attributed provenance, not a newly certified verdict. Chunk 0 must repeat this gate. Any new material change requires affected source/approval/plan/preflight revalidation; unknown drift is `UNVERIFIED_DRIFT`, not presumed harmless.

### 2.3 Instructions, skills and historical compatibility

- Applicable `.agents/AGENTS.md` was read completely (symlink to the installed shared instructions); no additional `AGENTS.md` was discovered under `aiops/` or current product docs. User scope, requirements, approved ADR/task and preservation rules govern.
- The external `004-instruction-ai-ops-go-phase01-single-implementation-plan.md` and paired `004-ai-ops-go-phase01-review-to-single-plan-handoff.md` under `/home/meriz/Documents/Synctech.ID/Etc/goose/handoff-openstack-aiops/` were read through their endings. Their prepared-not-authorized state is satisfied only for planning by this invocation, not by the packet itself.
- Installed `single-implementation-plan` and all its required SINGLE_PLAN references (integrated ownership, template, execution contract, quality checklist) were read fully, as were `chunked-implementation`, delivery/core-safety/execution-policy references, and pre-read/pre-edit/post-edit/RTK skills. They are available through `.agents/skills`, a symlink to `/home/meriz/.agents/skills`, not repository-versioned executor code.
- Installed skill SHA-256: planner `dab6b9242e808313d6ea4087a668195c7b5b055be232413a0e4cc353c01b1478`; executor `1facb456e5ad8f29e0849dda09930f2a5a3c2234a6161b1dacf5898289b9230c`; delivery contract `f1dbc726a84774a52c1420eb75a707a63ffc8190624088665e2adcf14c3f0c38`; core safety `4d5ed44e7b5823d7a005933bbf198cd391224e98cff57fb2c932cae1e83dd614`; policy `1f367383c371aac18dd2fbdea1a930015b718a190ad711d070d2d8c2fb9a2f31`. Re-resolve policy if these change materially.
- Current harness exposes read/write/exact-edit/bash and parallel tool calls, **not a fresh-worker/session orchestration tool**. Parallel reads are not isolated independent agents. Continuous-loop feasibility is therefore not established; single-chunk manual sessions remain possible after separate authorization.
- [README](../../../README.md) architecture/prerequisite sections and [lab architecture](../../architecture.md) in full were inspected. They describe lab topology, not authorization to select production routes, identities or defaults. No protected configuration/credentials were read.

Four historical documents were read in full, only as compatibility context:

| Historical contract | Difference that must not be imported |
| --- | --- |
| [Go-owned ADR](../../archive-dont-look-here/aiops-go/architecture/01-go-owned-safety-boundary-adr.md) | Different three-tool slice, fixed placement/identities/audit paths and prior supersession governance. |
| [Go-owned task](../../archive-dont-look-here/aiops-go/tasks/01-go-owned-safety-boundary-task.md) | Seven outer statuses, restricted identifier syntax, rotation limits and older phase allocation. Current scope requires eight statuses including `partial`, meaningful whitespace and first-use lifecycle. |
| [Environment-auth ADR amendment](../../archive-dont-look-here/aiops-go/architecture/01-go-owned-safety-boundary-env-auth-amendment.md) | Environment-only auth, fixed protected JSON policy and lab HTTP risk exceptions belong to a different candidate. |
| [Environment-auth task amendment](../../archive-dont-look-here/aiops-go/tasks/01-go-owned-safety-boundary-env-auth-amendment.md) | Specific selectors, identity/project/path grants, HTTP/non-expiry decisions and tests do not authorize this runtime. |

No legacy tool catalog, identity, path, auth source, HTTP exception, schema/exit mapping, numeric ceiling, approval or execution ladder is adopted. Compatible bounded-reader/negative-fixture patterns may inform implementation; legacy runtimes/contracts/data remain untouched.

## 3. Exact scope and guardrails

**Included:** the four Phase 01 steps: (1) one runtime, real enforcement owner, authenticated trusted ingress, safe help/readiness and disabled legacy/model paths; (2) reviewed fixed Go registry, validation, finite bounds, eight-status safe outcomes, sanitization, durable audit, revocation/cancellation; (3) protected scoped versioned new data, integrity/writer/capacity/cleanup/recovery safeguards from first use; (4) model-independent named server basics with literal identity, required field states and narrow verified flavor/port reads, deterministic fixtures and operator guidance.

**Excluded everywhere:** model analysis or automatic selection, model-driven plans/investigations, resume, MCP/client sessions, broad project discovery/summary, full network/subnet/volume or domain catalog, host/operator enablement, specialist activation, arbitrary commands/scripts/SSH/sudo/CLI/HTTP/file/database tools, separate diagnostic utility/interpreter dependencies, stronger credentials, migration/import/indexing, infrastructure/provisioning, local-model hosting, direct-model API harness, unrelated lab changes, future schemas/services/modules. No stubs for later phases.

**Protected invariants:** no unauthorized execution, mutation or prohibited disclosure; pre-dispatch denial means zero implementation/authentication/API calls; a post-read scope failure reports actual contact honestly. No raw-error/debug/temp/truncation fallback. Sanitize before every sink. No payload delivery until durable outcome audit. Audit gaps must be locally visible independently of the failed sink. Restart cannot clear uncertainty. Acknowledgement is not authorization or re-collection confirmation. Uncertain re-collection requires separate explicit confirmation, current authorization and a new timestamped observation; no replay or replacement of prior uncertainty.

**Documentation/demo:** explain registry/version/limits, reader/no-fallback and observer prerequisites, required versus optional readiness, identity/gaps/status semantics, credential/state boundaries, startup/shutdown, audit fault/acknowledgement/re-collection, storage/cleanup/legacy protection, utility-free fixture reproduction, operator-owned setup and separately gated live evidence. Independent sharing outside the product is not protected. No real secret/example credential values or inferred deployment values.

**Later ownership is preserved, not implemented:** Phase 02 isolated Codex/Pi/disclosure/egress/paste analysis; 03 exact-approved single investigation, separate pre-plan lookup and evidence report; 04 full resume/history/freshness/retrieval/reference-aware lifecycle/export/confirmed early deletion; 05 full project/domain/multi-server catalog; 06 higher-visibility/restricted three-host diagnostics; 07 approved local MCP/Pi sessions; 08 integrated release/live/model/operations/rollback evidence. G5/G6 remain later gates.

## 4. Current-state findings and baseline strategy

All paths below are **observed**, relative to `aiops/`. Inspection was targeted, not an exhaustive code or deployment security audit.

| Evidence anchor | Observed gap / reuse boundary |
| --- | --- |
| `Makefile:build`, `go.mod` | Four binaries; Go `1.27.1`, Gophercloud `v2.14.0`. No toolchain/cache execution. Keep declared version; do not auto-install/download or downgrade it. |
| Four `cmd/openstack-*/main.go` mains | Agent/workflow/project initialize model, ambient cloud clients and legacy stores before interactive commands. Start/resume/show/memory are not safe current exposure. Chat initializes inference, with no diagnostic tools in its inspected main. |
| `internal/tools/registry.go:Registry.Execute`, `tool.go:Tool` | Direct registered-name dispatch without trusted scope/audit. Not the new boundary by renaming it. |
| `internal/agent/runtime.go:Runtime.run`, `internal/workflow/server_incident.go:collectBaselineStep.Run` | Direct registry consumers; project main composes them. Keep deferred engines inaccessible, not broadly repair future workflow behavior. |
| `internal/scopedtools/broker.go:Execute`, `verifyCall`, `spend` | Selective role/relationship and in-memory budget patterns only. No independent caller authority or multiprocess persistent health proof. |
| `internal/tools/get_server.go:Execute`, `resolveServer`, `ServerObservation` | Trims identifiers; `AllPages`; incomplete required field states, raw fault details/host projection. Must not be enabled unchanged. |
| `internal/tools/get_flavor.go:Execute` | Caller-selected flavor and extra-spec collection/raw error; not a permitted standalone public relationship grant. |
| `internal/tools/get_ports.go:Execute` | Useful project/device checks and 32-record/four-page safeguards; response-byte bounds and complete shared boundary still needed. Reuse tighter compatible safeguards, not archived ceilings. |
| `internal/openstackclient/{compute,network,project}.go` | `AuthOptionsFromEnv`, region env and project extraction; not independent policy or dedicated-reader/destination evidence. New runtime cannot inherit ambient authority. |
| Agent `filestore.go:writeJSONAtomic`, workflow/project `store.go` | Restrictive temp/file sync/rename patterns, no complete initial-directory durability, arbitration, capacity or recovery proof. Engine discarded-save leads were located; no deferred engine repair is authorized. |
| Tools HTTP tests; `scopedtools/broker_test.go` | Read in full: `httptest`, request counters, scope/relationship/denial/cancellation and in-process concurrency seams. They are baseline regressions, not V1–V12 acceptance proof. |
| Root `Makefile` | `-include .env`; Molecule targets write artifacts/contact systems and can mutate. Not an offline wrapper. |

### Verification command ledger

**Every command/check below is PLANNED_NOT_RUN.** Working directory is the project `aiops/` directory unless stated otherwise. Existing `make test/build` and tools/scopedtools checks are observed entry points; new packages, test names, artifacts and fixtures are **proposed** and must be confirmed in Chunk 0/introducing chunk. Do not run these as document QA.

Execution prerequisites for all Go checks: separately authorized chunk; inspect test startup, subprocess/network/file side effects first; compatible already installed Go 1.27.1 and cached existing modules; sanitized credential-free launcher with synthetic inputs only, temporary HOME/config/data, no inherited cloud/provider/proxy authentication, and loopback-only controlled fixtures. Set session-local `GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOENV=off GOWORK=off`; select verified safe cache locations without reading credentials. No network module/toolchain downloads. Missing tooling is reported, not silently replaced. Compiler/race support and fixture ownership/access are checked before relying on them.

| Check ID | Command / procedure and provenance | Intended evidence |
| --- | --- | --- |
| B0 | `rtk go version`; inspect safe tool/cache availability (proposed guarded invocation) | Installed version satisfies declared module; no auto-download. |
| B1 | `rtk go test -count=1 ./internal/tools ./internal/scopedtools` (observed packages, uncached run proposed) | Baseline existing HTTP/denial/relationship cases and discovery/count/skips. |
| B2 | `rtk go test -count=1 ./...`; `rtk make build` (observed full entry points) | Record pre-existing failures and today's four outputs in Chunk 0; after consolidation prove exactly one runtime in a fresh isolated build output, no stale binaries mistaken for outputs. |
| F | `rtk gofmt -w <explicit changed Go files>`; `rtk go test -count=1 <explicit affected packages>`; `rtk go build -o <disposable output> ./cmd/aiops` once it exists (proposed) | Format only changed files, compile symbols/callers, focused behavior and safe runtime linkage. Expand actual paths before execution; placeholders are not literal commands. |
| D | `rtk go test -count=1 ./internal/diagnostic` (proposed package) | Result/validation/sanitization/admission/reader/identity/relationship/race fixtures introduced beside behavior. |
| S | `rtk go test -count=1 ./internal/protectedstore` (proposed package) | Durable versioned filesystem/locks/capacity/recovery/cleanup behavior, not only mocks. |
| I | `rtk go test -count=1 ./cmd/aiops ./internal/diagnostic ./internal/protectedstore` plus old command package tests (proposed combined check) | Public CLI-to-owner/API/store chain and disabled-entry traps; full package execution, not a filter matching zero tests. |
| R | `rtk go test -race -count=1 ./internal/diagnostic ./internal/protectedstore` (proposed) | Data races checked; not a replacement for separate-process lock/crash evidence. |
| A | `rtk go vet ./...`; B2 after consolidation (proposed additional vet, observed full entries) | Full module regression and build. No mandatory offline skips hidden by exit zero. |
| O | Introduced Go test subprocess fixtures; actual Ubuntu 24.04 x86-64 non-root security contexts, temporary private store, crash barriers and pre-provisioned bounded expendable filesystem (proposed; exact test selectors recorded at introduction) | Unauthorized peer/credential/state denial; separate writers; kill/restart at intent/read/outcome boundaries; real ENOSPC distinct from managed quota. Never fill repository/host/lab disk or require agent provisioning/root. |
| P | Built-runtime Go-driven fixture demo in a pre-approved controlled utility/interpreter-free environment (proposed; record exact launch/manifest and process tree) | One executable, read-only local API fixtures, synthetic policy/credentials, no harness, shell-out diagnostic or external diagnostic utility. PATH filtering alone is insufficient proof. |
| X | Static import/call/SDK mutation/exec/path/privilege/error-sink review, supplemented by recording transport and secret-canary tests (proposed) | No unauthorized linked route or request method, no prohibited sink, no live lab/config changes. Static grep alone is not proof. |

B2 is scheduled in Chunk 0 after side-effect inspection and at the final gate, with focused checks first. No known test failure is established during planning. If safe full baseline cannot run, record exact environment/failure and apply the blocker rules; no feature work may hide required baseline uncertainty. Fixture OS/storage tests need separately available safe local facilities; their absence prevents acceptance, not an excuse to mark mandatory tests optional. Live cloud/host/model/MCP, real reader policy/mutation-denial probes, installation and root Make/Molecule/Ansible remain NOT_RUN and separately authorized later.

## 5. Requirement-to-chunk and evidence coverage

Numbers refer to the sole ladder in §9. Every row is an obligation, **not completed evidence**. Current implementation is unaccepted/gapped as §4 documents. Verification includes the indicated behavior tests alongside changes and final rerun in Chunk 21; command IDs refer to §4 with all prerequisites and PLANNED_NOT_RUN state. All task §8 mixed requirements are partitioned below; later portions stay excluded.

### 5.1 Current functional obligations

| PRD / task source | Selected observable obligation | Implementation / preservation chunks | Verification and intended evidence |
| --- | --- | --- | --- |
| FR-001, FR-046; task §4.1 | Named manual/readiness/catalog, no model/knowledge dependency or unsafe old branches | 2, 12, 19 | I/P in 19–21; V1/V12 traps help, start, show, resume, memory and inference. |
| FR-002; §§4.1/6.1 | Trusted one-project/target/profile/capability/policy/limits/correlation and partitioning | 3–4, 6–7, 12–14 | D/S/O; forged context, project switch/stale context and same-name cross-project refusal. Full investigation records deferred. |
| FR-003; §4.3 | Canonical UUID or literal exact case-sensitive names, original/resolved identity, meaningful whitespace, bounded audited lookup and UUID guidance | 4, 9, 14, 19 | D/I; V4 matrix incl Unicode/unsupported/malformed intent, duplicates, approximate filtering and bound exhaustion, zero guessed GET. Pre-plan consent belongs to 03. |
| FR-009–FR-010; §§4.2/6.2–6.3 | Actual per-call authorization and finite budgets; no denial retry/fallback; cancellation/revocation and withheld unauthorized results | 4, 7, 9–10, 12–13, 18–19 | D/R/I/O; request-order counters and before/between/in-flight races. Nested/resumed/delegated adapters remain disabled. |
| FR-011; §4.3 | Only explicitly granted flavor/port categories derived from verified authorized server | 14–17 | D/I; valid counterpart vs forged ID/category, changed flavor, wrong project/device, no later traversal. |
| FR-014; §6 | Durable minimal manual request/intent/outcome/provenance/recovery transitions | 3, 6–10 | S/D/O; no false save, crash ordering. Full goal/hypothesis/task/child checkpoint schema deferred. |
| FR-015 current subset; §6.3 | Uncertain manual collection requires separate confirmation/current authority/new observation, no replay | 7, 9–10, 19–20 | S/D/I/O; ack alone and revoked-rights acknowledgement do not dispatch. Full resume excluded. |
| FR-016 current subset; §7 | Timestamped observations, honest collection rather than current-state/health inference | 3, 15, 19 | D/I; provenance and gaps. Investigation freshness/summary/history machinery deferred. |
| FR-017–FR-018; §§4.1/5 | No automatic archive/knowledge/legacy ingestion; untrusted request/output never grants authority; optional knowledge independence | 2, 4–5, 12, 19–20 | D/I/P; hostile text and inaccessible optional sources, read/ingestion traps. Retrieval deferred. |
| FR-019–FR-020 current contribution; §7 | Truthful required fields/gaps; successful collection not diagnosis; no fabricated claim | 3, 5, 15–17, 19, 21 | D/I; field-state/status assertions and no-model demo; no evidence-review/report feature. |
| FR-021; §§3/4.1 | Ubuntu 24.04 x86-64 external non-root observer design/readiness, required management routes only | 1, 12, 19, 21 | O and guide; synthetic security-context evidence, no assertion of actual observer placement/reachability. Deployed proof 08. |
| FR-022; §§4.2/6.1 | Dedicated project reader/access separation, optional host/operator absent, no stronger fallback | 1–2, 12–13, 19 | D/O/I; synthetic credentials, identity/project/destination checks; no live privilege claims. |
| FR-023–FR-024; §4.2 | Fixed reviewed built-in mapping, metadata/schema/risk/profile/prerequisites/limits, strict gateway plus tool-local validation | 3–4, 13–17, 19 | D/I/X/P; zero calls on unknown/generic/mutation/extra/override request, one implementation per definition. |
| FR-025; §4.3 | Required server status/image/flavor/networks/config drive/AZ and available fault, explicit safe states and narrow related reads | 14–17, 19 | D/I; each field available/denied/unavailable/not-applicable, absent/unsafe fault, minimized nested projections. Full catalog deferred. |
| FR-026 current preservation; §5 | No host path enabled or arbitrary host fallback | 2, 4, 19 | I/X; zero connection/utility traps. Host operations/windows/live proof deferred. |
| FR-027; §7 | All eight logical statuses, versioned human/JSON semantics, identity/correlation/timing/NA/truncation/redaction, no fictitious SDK subprocess exit | 3, 5, 9, 18–19 | D/I; injected eight-outcome snapshots and independent truncation/redaction metadata. Summary categories deferred. |
| FR-028; §§6.2–6.3 | Durable intent before admitted dispatch, durable outcome before disclosure, denial gap, shared failure stop/acknowledged recovery | 6–10, 18–20 | S/D/I/O; order traces, ambiguous writes, failed outcome payload withholding, unwritable fault marker, restart/ack matrix. |
| FR-029; §6.1 | Minimize/sanitize every enabled sink, unsafe withholding, protected necessary local identifiers | 3, 5–6, 9–10, 13–19 | D/S/I; canaries in nested fields/text/errors/args/truncation/temp/control/audit/CLI. No raw-error fallback. Remote aliases/export deferred. |
| FR-030; §§4.2/5 | No mutation capability even on insistence | 2, 4, 13–19 | D/I/X; record method/path allowlist and generic/fix/override rejection, no mutation dispatch. Model fix-it UX deferred. |
| FR-031–FR-034 current preservation; §§4.1/5 | Model paths disabled before initialization, no diagnostic credential sharing; healthy manual independence | 2, 12, 19–20 | I/O/P; model constructor/process traps. Both inference adapters/disclosure/egress enablement deferred to 02. |
| FR-037–FR-038 current seeds; §9 V12 | Versioned deterministic expected/actual manual scenarios without credentials | 19–21 | I/P; healthy, denied, hostile cases with calls/outcomes/limits. No full evaluator/scoring platform. |
| FR-039; §§6/7 | Correlated request/tool/audit provenance and concise safe outcomes, no secrets/hidden reasoning | 3, 5, 9, 19 | D/S/I; correlation/order/time/status consistency. Model/task/project pipeline deferred. |
| FR-040; §4.2 | Finite time/request/retry/page/record/argument/response/output/resource limits enforced during collection | 4, 7–9, 13–18 | D/R/I; floods, hostile pagination, exhaustion/no later dispatch/closed resources. Model/run/project budgets deferred. |
| FR-041; §§3/4.1/6.4 | Required/optional local readiness; missing policy/audit/store/finite usable limit disables startup/admission, not silent optional failure | 1–2, 6–13, 19 | S/D/I; local help/catalog/readiness no auth/name lookup, actionable fail-closed required controls. |
| FR-042 current subset; §§6.3/11 | Safe shutdown, reader revocation/store/recovery guidance | 10, 18–21 | D/I/P and guide; no later dispatch after stop, honest prior reads. Full operations/live rotation/rollback 08. |
| FR-043–FR-044; §§4/6 | One utility-free runtime, dedicated reader/approved destination prerequisites, narrow read-only mappings/tool-local validation | 1–2, 4, 12–19, 21 | D/I/O/P/X; no ambient fallback, client-owned credentials or external diagnostic executable. No selected auth input source from archive. |
| FR-045 current subset; §4.2 | Diagnostic names/descriptions, no generic primitive | 4, 19, 21 | Registry/CLI review plus I/X; model instruction layer deferred. |
| FR-048; §6.4 | Configurable 90-day audit default, bounded audited startup/runtime cleanup, overdue restart and unknown/active/reference protection | 8, 11, 19–20 | S/I/O; controlled clocks, intent failure prevents deletion, post-delete audit gap. 30-day investigation default applies only when those types exist; no new investigation history. |
| FR-049; §6.4 | Finite usable managed limit vs actual disk-full; required-write admission stop, no unexpired eviction; safe local access where possible | 6–8, 10–11, 19–20 | S/O/I; quota vs real ENOSPC, safe scope-checked inspection/copy of already sanitized current records and operator-triggered eligible audited cleanup where possible; explicit limitations if required controls fail. Rich export/confirmed early deletion deferred. |
| FR-050; §6.4 | Protected new namespace, no legacy read/import/index/send/mutate/cleanup/approval reuse | 1–2, 6, 11, 19–21 | S/I/O/P; synthetic legacy traps plus unchanged hashes, legacy disk consumption outside quota; never inspect real legacy records. |

**Explicitly deferred entire functional capabilities:** FR-004–FR-008 planning/graph/model/loop work (02/03/05), FR-012–FR-013 domain/project execution (03/05/06), FR-035 MCP and FR-047 sessions (07), FR-036 specialist enablement (not selected; disabled branch only). No task full-Delivery traceability row authorizes them here.

### 5.2 Non-functional obligations

| PRD ID | Current obligation and implementation/preservation | Verification path |
| --- | --- | --- |
| NFR-001 | Zero unauthorized execution/mutation/prohibited disclosure; all implementation chunks, especially 2, 4–5, 9, 12–19 | V1–V12, O/I/X/P, final 21. No nonzero safety allowance. |
| NFR-002 | Separated non-root caller/credential/state domains and required routes; 1, 6, 12–13 | V3/V10 real OS contexts, guide; model/host/client/deployed extensions deferred. |
| NFR-003 | Finite execution, cancellation/cleanup/no later dispatch; 4, 7–9, 13–18 | V7/R/I/O. |
| NFR-004 | Atomic/transactional complete durable records, corrupt/version refusal and independent writer control; 6–10 | V9/V10/S/O; no claim of full investigation resume. |
| NFR-005 | Cloud/project/request isolation, no same-name authority; 4, 6–7, 12, 14 | V3/V4/V10/V11. Memory/knowledge/approval history deferred. |
| NFR-006 | Safe structured bounded failures, mandatory-control stop, optional degradation/manual independence; 2–19 | V1/V6–V10/V12; missing required offline evidence cannot be waived. |
| NFR-007 | Collection/status/confidence not diagnosis; 3, 15–19 | V5/V6/V12; no inference/reviewer added. |
| NFR-008 | Safe auditable allowed/denied outcome, time/correlation/duration or NA; 3, 5, 9–10, 19 | V6/V8/V9 and order traces. |
| NFR-009 | Performance/model cost thresholds not current scope; preserve no SLA/cost claims in 19/21 | G5 deferred to 08; metadata not false zero. |
| NFR-010 | Versioned manual semantics and safe legacy disablement; no lab disruption; 2–3, 19–21 | V1/V12, full Go regression; lab live regression separately gated/not claimed. |
| NFR-011 | Reviewed definitions/classification/offline extension tests; 4, 13–17, 19 | V2/V5/V12 and X. |
| NFR-012 | Minimization/storage access/retention; 5–11, 12, 19 | V3/V6/V10/V11; remote disclosure/alias/egress deferred. |
| NFR-013 | Concise human/versioned JSON, visible gaps/truncation/denial, no health fiction; 3, 15–19, 21 | V1/V5/V6/V12. |
| NFR-014 | One utility-free independently stoppable executable, external observer prerequisites and offline validation; 1–2, 12, 18–21 | V3/V7/V12/P; actual install/harness/deployed proof later. |
| NFR-015 | Deterministic credential-free fixtures; all behavior chunks and 20–21 | V12 plus full rerun; live/model acceptance distinct and NOT_RUN. |

### 5.3 Acceptance contributions (not whole-Delivery closure)

| AC | Phase 01 contribution / owner chunks | Required evidence; later boundary |
| --- | --- | --- |
| AC-002 | Literal manual identity/original-resolved/UUID guidance: 14/19 | V4; investigation integration 03. |
| AC-003 | Invalid/unknown tool and finite calls: 4/13/18 | V2/V7; model/control graph/loop closure 02/03/05. |
| AC-004 | Actual-boundary wrong scope and legitimate related reads: 4/12–17 | V2/V3/V5; full nested/resumed/delegated/MCP parity 03–07. |
| AC-007 | Corruption/write/writer/uncertainty core: 6–10/20 | V9/V10; full investigation checkpoint/resume/terminal/approval 04. |
| AC-011 | Observer/reader/no-fallback design and security-context fixtures: 1/12–13/21 | V3/V12; deployed/policy/mutation-denial evidence 06/08. |
| AC-012 | Every retained public manual path, Go-only validation: 2/4/12/19 | V1/V2; enabled automated/MCP parity later. |
| AC-013 | Host unavailable, zero fallback: 2/4/19 | V1/V2; three-host/windows/operations acceptance 06/08. |
| AC-014 | Eight statuses/metadata/audit/faults/ack: 3/5/9–10/18–20 | V6–V9; summary categories 05, full adapter parity 07. |
| AC-015 | Secret canaries/no mutation: 4–5/9/13–19 | V2/V6; model fix-it plan/manual runbook recommendations 02/03, release integration 08. |
| AC-016–AC-017 | No model initialization/credential sharing; domain separation: 2/12/19–20 | V1/V3/V12; both harnesses/real model and deployed isolation 02/08. |
| AC-018 | Manual no-model independence: 2/19–21 | V1/V12; provider revocation/outage/local investigation report cases 02–04. |
| AC-021–AC-022 | Versioned manual fixture seeds/events/bounds/cancellation: 3/18–21 | V6/V7/V12; full evaluator/usage/pipeline 03–08. |
| AC-023 | Readiness/store stop/shutdown/ack guidance/offline faults: 6–12/18–21 | V7/V9–V12; full lifecycle/live operations/rollback 04/06/07/08. |
| AC-024 | New-store/legacy/no lab changes/manual compatibility: 2/6/11/19–21 | V1/V11/V12; full delivery/lab/rollback integration later. |
| AC-026 | Target observer/project-reader prerequisites: 1/12–13/21 | V3/V12; live project/full network/three-host/disposable denial 05/06/08. |
| AC-027 | Basics fields/input/static/behavioral read-only subset: 4/14–17 | V4/V5/V12; full catalog 05/06. |
| AC-028 | Named select/execute/shared-boundary guide: 19/21 | V1/V12; protected paste/harness analysis 02 and full parity 07. |
| AC-029 | Utility-free single-runtime manual proof: 2/19–21 | V3/V12/P; deployed/both harness/MCP/client egress later. |
| AC-030 | Manual lookup/relationships/revocation/cancel/withhold: 9–10/14–18 | V4/V5/V7/V9; plan/session lifetime and remote aliases/disclosure later. |
| AC-031 | Quota vs real disk-full, applicable audit cleanup/fault/legacy: 6–11/20 | V9–V11; full terminal/reference/confirmed deletion/export lifecycle 03/04. |

AC-001, AC-005–AC-006, AC-008–AC-010, AC-019–AC-020 and AC-025 have no whole current feature closure: preserve disabled/no-ingestion/no-fabrication/no-release-claim invariants in 2/5/19/21; their implementation owners remain 02–08 as task §8.3 specifies. No current partial contribution is claimed as a whole passing AC.

### 5.4 Mandatory V1–V12 verification obligations

These are **mandatory offline** evidence, not recommendations. All rerun at Chunk 21; mocks alone cannot close OS/filesystem/process properties.

| ID | Implement/test alongside chunks | Specific required observation |
| --- | --- | --- |
| V1 | 2, 12, 19–20 | One artifact; actual manual/help/readiness plus every retained/disabled command branch; traps for authentication/model/legacy store/raw dispatch, zero help lookup; optional prerequisites absent without breaking healthy manual path. |
| V2 | 4, 9, 12–19 | Unknown/generic/mutation, missing/forged scope, malformed/extra/duplicate input and endpoint/host/path/profile/implementation/budget override, direct-route attempts: zero downstream calls on pre-dispatch denial, safe audit or visible gap, valid counterpart, no retry/fallback. |
| V3 | 6, 12–13, 19–20 | Real target-OS non-root unauthorized local caller/credential/state denial, cloud/project/target/profile/policy mismatch/switch, endpoint/redirect/pagination escape and token traps. Post-auth mismatch means zero subsequent resource reads, not a false claim of zero auth. |
| V4 | 14, 19 | UUID/literal whitespace/case/Unicode/unsupported/malformed intent/missing/ambiguous/approximate matches/bounds; preserve original-resolved; no guessed GET/unrelated disclosure, audited disclosed manual lookup only, UUID guidance. |
| V5 | 15–17, 19 | Required field states and safe/absent/secret fault, authorized referenced flavor vs forged/changed flavor, correct vs foreign/wrong-device ports; no extra specs/host/broad topology/network-subnet traversal. |
| V6 | 3, 5, 9, 19 | Every eight-status envelope, safe errors/NA duration/time/correlation/truncation/redaction; nested/text/error canaries/hostile instructions/invalid encoding/oversized input; all sinks including temp/control, no raw fallback or fictional process exit. |
| V7 | 4, 13–18 | Cancel/deadline before/between/during reads, stream floods/endless/hostile pagination, all finite bounds, expiry/revocation/shutdown; cleanup/closed resources, no later dispatch or denial retry, withheld unauthorized payload and honest possible prior read. |
| V8 | 6, 9, 18–20 | Trace durable intent before admitted operation and durable result before payload; failed/ambiguous intent zero dispatch, result fault stop/withhold/local gap, denial audit unavailable visible, no phantom event/fallback/ambiguous append retry. |
| V9 | 7, 9–10, 19–20 | Separate process/restart/crash before dispatch/in-flight/after read-before audit; fault marker unwritable; no automatic admission/replay; ack required but not authority or recollection confirmation; confirmed recollection new observation; withheld recovery authorized/audited or explicitly unavailable. |
| V10 | 6–8, 20 | Real first creation/reopen, complete-write/flush/file+directory-sync/rename faults; permission/path/symlink, corrupt/version mismatch, concurrent independent writers, missing/unusable/exhausted limit, actual bounded-filesystem ENOSPC vs quota, no unexpired eviction/false save. |
| V11 | 8, 11, 19–20 | Controlled clock 90-day default/config override, bounded startup/runtime/overdue cleanup, intent failure no delete, post-delete audit gap, unknown/active/reference protection, synthetic legacy read/index/import/send/cleanup/approval traps and unchanged hashes, unmanaged legacy disk use. No real legacy inspection. |
| V12 | 19–21 | Actual CLI→boundary→API fixtures→sanitized intent/outcome/result, healthy/denied/hostile versioned expected-actual records, utility/interpreter-free controlled execution and reviewed artifact/prerequisite/guide. No live/full-Delivery claim. |

Recommended extras (not replacements for any mandatory row): bounded fuzzing of parsers/sanitizer and extended soak runs once existing local tools permit. Do not add frameworks, performance thresholds or dependencies merely for these extras.

## 6. Decision authority and timed prerequisites

| Item | Level/status and source | Required treatment |
| --- | --- | --- |
| B1–B5, exact identity/eight statuses/no legacy/no mutation | Approved constraint, PRD/task/ADR | Preserve; changing behavior/isolation/audit/privacy/lifecycle is Level 2. |
| G1 | Open concrete Level 1 realization within task §3/ADR §6 | Chunk 1 records non-root credential-owner/requester domains, authenticated ingress and unauthorized-local-caller design. Document and separately review/approve before affected execution; actual unauthorized-local-caller OS proof in 12 before controlled manual enablement in 19, with aggregate evidence rerun in 20 before acceptance. No particular IPC, account, path or privilege is approved by the abstract ADR. Harness/client proof remains 02/07. |
| G2 | Operator configuration prerequisite, not inferred | Trusted scope/endpoints/reader source/protected setup/finite usable limit before startup/use. Synthetic offline fixture configuration may establish tests without real deployment values. Disposable/live scope and cleanup owner required before any live policy probe, never scheduled here. |
| G3 | Open exact reader/relationship/destination realization | Review exact allowed Nova/Neutron/flavor operations, returned identities/visibility and transport restrictions before collector enablement (13–17). Actual cloud reader/mutation-denial evidence remains separately authorized live acceptance, not established by fixtures. |
| G4 | Open concrete Level 1 protected-store realization | Record versioning, first-create durability, writer/health/admission/capacity/cleanup/ack ordering in 1; separately review/approve before persistent execution (6 onward). Prove actual filesystem/crash/fault behavior before acceptance. No DB/fixed deployment path is selected. |
| Package/CLI/schema/test spelling; strict validators/safe numeric limits | Level 1 after preflight/execution authorization, task §10 | Proposed below; confirm actual paths, choose documented finite limits with rationale, no unnecessary human blocker for ordinary compliant details. Do not copy archived constants or arbitrarily prohibit literal names. |
| New data policy | Level 1 proposal subject to G4 | Prefer minimal sanitized request/audit/recovery metadata without full retained manual payload. If payload not safely recoverable, report unavailable and use explicit uncertain recollection rules; do not silently rebuild it. If retaining payload instead, specify compliant classification/lifecycle before use. No investigation lifecycle invented. |
| Local protected persistence/sequential admission; existing dependency only | Proposal within approved bounds | Demonstrate feasibility; serialized or finitely rejected writers permitted. No new service/database/infrastructure is presumed. |
| Safe routine editing/tests/format/debug/fixture repair | Level 0 after separate authorization | Proceed within selected chunk and finite failure budget without repeated permission. |
| Weaker boundary, changed product semantics, new material risk/privilege/catalog/infrastructure/dependencies, migration/live credentials/deploy | Level 2 or separate environment authorization | Stop dependent work; supply exact evidence, options/tradeoffs, recommendation and decision needed. Engineering difficulty or several compliant choices alone is not Level 2. |
| G5/G6 | Later-phase gates | Do not pin release thresholds, enable MCP or invent client/egress approval here. |

No unresolved Level 2 product change is necessary to write this plan. G1/G3/G4 engineering realizations and G2 environment are **not resolved or preapproved**. Design selection can proceed under Level 1 when execution is authorized; required separate review/approval/negative evidence cannot be replaced by that discretion. Pending gates block affected enablement/execution, not safe source revalidation or ordinary compliant design work. If no compliant realization exists, escalate instead of weakening the contract.

## 7. Rough effort and dependencies

One experienced engineer; **1 engineer-day ≈ 6 focused hours**. Ranges include discovery, concrete design documentation, implementation/tests, scoped repair, evidence and final guide/demo/verification, excluding external approval/access/provisioning waits. Quarter-day entries are scheduling granularity, not precision or agent-runtime promises. This evidence-based estimate is **15–27.25 engineer-days / 90–163.5 focused hours**, broader than the roadmap's 10–15-day proposal because independent-process/OS access/crash/real-disk evidence and first-use recovery/lifecycle are explicit task obligations. Scope is unchanged; re-estimate after Chunk 0/1 if feasibility changes.

| Chunk | Goal | Depends on | Engineer-days | Execution state |
| --- | --- | --- | --- | --- |
| 0 | Source/base/ladder and safe baseline | Separate authorization | 0.5–1 | Not started |
| 1 | Concrete G1–G4 realization record | 0 | 1–2 | Not started |
| 2 | Quarantine old routes, dormant single runtime | 1 | 0.5–1 | Not started |
| 3 | Versioned safe result contract | 2 | 0.5–0.75 | Not started |
| 4 | Reviewed strict definitions and trusted requests | 3 | 0.5–0.75 | Not started |
| 5 | Minimized safe sink transformations | 4 | 0.5–1 | Not started |
| 6 | Protected durable new namespace | 5, G4 review/approval | 1–1.5 | Not started |
| 7 | Independent writer/admission health | 6 | 0.75–1.5 | Not started |
| 8 | Managed capacity versus disk failure | 7 | 0.5–1 | Not started |
| 9 | Durable audit dispatch/disclosure state machine | 8 | 1–1.5 | Not started |
| 10 | Acknowledged uncertainty recovery | 9 | 0.5–1 | Not started |
| 11 | Applicable bounded audited cleanup | 10 | 0.75–1.25 | Not started |
| 12 | Authenticated OS-bound ingress | 11, G1 review/approval | 1–2 | Not started |
| 13 | Private bounded trusted reader transport | 12, G3 review, synthetic G2 | 0.75–1.5 | Not started |
| 14 | Bounded literal identity resolution | 13 | 0.75–1.25 | Not started |
| 15 | Required server basics projection | 14 | 0.5–1 | Not started |
| 16 | Verified related flavor read | 15 | 0.5–0.75 | Not started |
| 17 | Verified related port read | 16 | 0.5–0.75 | Not started |
| 18 | Cancellation/revocation/bounds integration | 17 | 0.5–1 | Not started |
| 19 | Manual CLI integration and scenario seeds | 18 | 0.75–1.25 | Not started |
| 20 | Cross-process/OS/disk/package evidence closure | 19 | 1–2 | Not started |
| 21 | Final verification, guide/demo and scope audit | 20 | 0.75–1.5 | Not started |
| **Total (each chunk once)** | | | **15–27.25** | **Not started** |

## 8. Resolved executor contract (embedded)

**Policy source:** installed executor/core-safety/delivery/policy fingerprints in §2.3, applicable repository instructions, and task. No compatible project retry/environment/handoff override was supplied. The following defaults apply at execution, not as permission to execute now:

1. Use this single controlling plan only after explicit chunk execution authorization and controlling-plan adoption. For this governed workflow, current approved/committed task/ADR and applicable formal preflight evidence are required before feature edits; the subsequent preflight report is recorded in §14 and must be revalidated for material drift. A separately authorized source/baseline-only Chunk 0 is not itself a preflight verdict. Re-read plan, sources, instructions and authorized handoff before each session; verify source/approval/base drift and classify impacts before reuse.
2. **Single-chunk:** exactly the selected chunk, post-work/report, then stop. Default is to obtain confirmation before creating an unrequested handoff. A prior explicit handoff instruction may satisfy that confirmation; it never authorizes the next chunk.
3. **Continuous-loop:** explicit authorization and real fresh-session orchestration required. A capable main agent selects one chunk, dispatches one fresh worker, accepts its evidence/exit conditions and complete non-final handoff, then dispatches the next. Each worker stops. Missing orchestration means report the gap and supply a manual next-session prompt; do not simulate isolation or silently run all chunks in one session.
4. **Failure budget:** at most **two failed validation attempts for the same current-chunk issue**, absent a separately authorized finite override fixed before retries. Count and report failed attempts; session changes do not reset the budget. Diagnose current regression versus baseline/environment, repair only smallest safe in-scope defect, add regression coverage, rerun affected checks. Do not weaken tests, advance with unresolved required failures/gaps, or implement future chunks to fix the current one. Missing tools/access or exhaustion stops with a concrete blocker.
5. **Environment:** current development repo and safe disposable offline fixtures only. No `.env` or real credentials/protected records, automatic package/toolchain/module installs/downloads, live infrastructure/model/MCP, root Make, provisioning, deployment or destructive external actions. Go prerequisites are in §4. If Python execution actually becomes necessary, obtain/activate a user-provided or verified approved venv once and reuse it; no Python is needed merely for Go or Markdown planning and none is executed here.
6. **Mandatory per-chunk post-work:** changed-file discovery, relevant full tracked/staged/untracked diff review, formatter on changed language files, syntax/type/build/symbol/import/caller validation, focused behavior/regression tests, discovered test counts/skips, and functional/integration risk/validation-gap/rollback statement. Always apply §4 F plus relevant D/S/I/R/O/X checks; documentation-only chunks instead validate complete contents/links/whitespace, without product formatting/build. No observed result may be fabricated from an expected outcome.
7. **Common chunk exit E:** all explicit tasks and required focused checks actually pass; safe intermediate state and scope-conforming full diff; risks/gaps/choices/base/candidate/failed-attempt count recorded; selected mode's handoff rule satisfied. Non-final report: `CONTINUABLE`, `BLOCKED` or `INCOMPLETE`; a `CONTINUABLE` worker still stops. No bypass/new exposure while its required controls are incomplete. Final gate uses `READY_FOR_REVIEW`, `BLOCKED` or `INCOMPLETE`, never automatic acceptance/deployment/Phase 02.
8. **Handoff H for every non-final rung below:** single-chunk asks confirmation before unrequested creation and stops; continuous non-final requires complete handoff and worker exit before main-agent acceptance. Proposed fallback path, no current-repository convention established: `docs/handoffs/ai-ops-go-manual-diagnostics-chunk-N-to-M.md`. Use installed handoff skill if authorized/available; its paired next-session instruction, when required, remains an execution artifact, not an extra planning output now. Include exact task/plan/source/base/candidate/mode/policy identity, completed/next chunk, files/symbols, actual commands/results/discovery/skips, full diff summary, decisions/approvals/gates, risks/gaps/rollback, blockers/environment and precise next instructions. No secrets. No automatic final/next-phase handoff.
9. Evidence defaults to the chunk completion response and authorized handoffs; fixture-generated expected/actual records live only in controlled temporary outputs or explicitly reviewed synthetic fixtures. No execution logs/handoffs are created by this planning invocation. Keep phase/chunk labels in documents, not executable symbols/config.
10. Authoritative source conflict, required scope expansion, changed approved architecture, material safety/privacy/integrity risk, unavailable required tooling or unauthorized environment access is an escalation. Stop dependent work and report evidence/options, not a permissive fallback. Self-check does not replace independent review in a separate fresh session. Reproduce/substantiate review findings before repair.

## 9. Implementation Ladder: Phase 01 Manual Diagnostic Safety Boundary

**Conventions for all rungs:** every task is unchecked; all execution checks are PLANNED_NOT_RUN. Dependencies/entry require accepted predecessor exit E and explicit current-chunk authorization (plus applicable preflight before feature edits). H, E, the two-failure repair budget and per-chunk post-work in §8 apply to **each** non-final rung; references below are intentional embedded policy, not a waiver. Commands/check IDs inherit §4 working directory, prerequisites and observed/proposed status. Every introducing source file includes its focused `_test.go` counterpart in the same chunk. Keep dependencies acyclic: `protectedstore` owns primitive scoped record/health types and persistence interfaces and must not import `diagnostic`; `diagnostic` owns authorization/sanitization/collection and may consume `protectedstore` once it exists; `cmd/aiops` composes the owner. Inject minimal store-defined durable-event callbacks for cleanup rather than importing the gateway. Early pure contracts reference no nonexistent package or undefined symbol. New paths/symbols below are **proposals**, never assertions that they already exist.

### Chunk 0: Discovery, Source Revalidation and Safe Baseline

- **Goal/requirements:** revalidate all sources, authority, scope, V1–V12 feasibility and this ladder; implement nothing.
- **Dependencies/entry:** separately authorized discovery/baseline-only session, read-only source access; no inferred implementation or preflight authorization.
- **Inspect:** §§2/4 sources and anchors, complete worktree/index/untracked state, installed policy, command/test side effects, available toolchain/cache and offline OS/filesystem/package facilities.
- **Changes/symbols:** none in application/tests/config/dependencies. Only separately authorized evidence/plan corrections, never a second ladder.
- **Tasks:**
  - [ ] Re-read complete task/ADR/PRD/Phase 01 and instructions; remeasure hashes/blobs/HEAD/tree, approval provenance and all relevant work; preserve unrelated changes.
  - [ ] Inventory commands/branches, registry/SDK constructors/callers, build outputs and actual supported routes; confirm proposed paths and no competing plan.
  - [ ] Confirm formal preflight status separately; do not issue a verdict or treat the old draft review as current preflight.
  - [ ] Inspect test startup/side effects, sanitized offline launch, installed Go 1.27.1/cache, race/OS contexts/bounded filesystem utility-free fixture access. No auto-provisioning/downloads/credential inspection.
  - [ ] Run B0/B1 then safe B2; record actual tests discovered, skips/errors and four-binary baseline, source/command side effects. If unavailable, classify exact blocker; do not begin features.
  - [ ] Confirm coverage, chunk feasibility/estimate and G1–G4 timing; record any supported refinement in this same plan without marking unperformed work complete.
- **Compile-safe state/excluded:** source unchanged; no feature or concrete gate approval fabricated.
- **Validation/post-work:** repository drift/authority evidence, safe baseline results, final status/diff and risk review; no formatter on untouched files.
- **Risk/rollback/repair:** unsafe test side effects or unavailable toolchain are blockers; no baseline reset/cleanup of user work. Remove only identified task-generated disposable outputs if safe.
- **Handoff/stop:** H and E, or precise blocker; stop before Chunk 1.

### Chunk 1: Document the Concrete G1–G4 Realization

- **Goal/requirements:** settle feasible compliant engineering mechanisms, not change B1–B5/product rules. Supports V1–V3/V8–V12.
- **Entry/dependencies:** 0; separate design-work authorization and actual current sources; no feature edits without applicable preflight.
- **Inspect:** task §3/§6/§10, ADR B1–B5/§6, code inventory, permitted OS/filesystem facilities.
- **Proposed changes:** `docs/ai-ops-go/manual-diagnostics.md` realization/operator-guide section (new documentation, no deployment values); record identity of gate evidence in this plan only if execution authorization permits plan tracking. No ADR/PRD rewrite.
- **Tasks:**
  - [ ] Specify credential-owning/requesting non-root domains, authenticated local ingress, independently trusted configuration/current authorization and negative OS-context proof. No inference/MCP scaffolding.
  - [ ] Specify exact permitted authentication/reader destinations and API/relationship rules, input-source controls and no ambient/proxy/redirect fallback; synthetic fixture setup only. Do not adopt archived HTTP/auth decisions.
  - [ ] Specify protected namespace/versioning, initial file/directory durability ordering, writer/admission/health lock ordering, quota reservation, audit/result publication, crash/recovery/ack and bounded audited cleanup. Explain minimal payload-retention choice.
  - [ ] Identify G2 synthetic prerequisites vs real operator-supplied environment and safe bounded filesystem/security-context fixture availability; record exact tests needed.
  - [ ] Obtain separately reviewed/approved concrete G1/G4 realizations before their affected execution and G3 review before enabling collectors. Record pending/satisfied states honestly; do not self-approve. Ordinary compliant details remain Level 1.
- **Compile-safe/excluded:** documentation only; no enabled reader/persistence or new infrastructure, account/path/endpoint/credential values.
- **Validation/post-work:** complete document/links/consistency against task §3 and ADR §6, diff/scope/security review. No product test implied.
- **Risk/rollback/repair:** if realization needs weakened safety/expanded privilege, stop for precise Level 2 decision. Revise only proposed design text, not approved sources; unresolved gates block dependent chunks, not independent compliant design.
- **Handoff/stop:** H/E with explicit gate ledger, no claim of implemented controls.

### Chunk 2: Close Legacy Exposure and Build One Dormant Runtime

- **Goal/requirements:** V1/V2/V12; step 1 and FR-050 preservation before exposing any new diagnostic.
- **Entry/dependencies:** 1, feature preflight/authorization; reviewed inventory. No real configuration needed.
- **Inspect observed:** four `cmd/openstack-*/main.go`/tests, `aiops/Makefile`, registry/agent/workflow/project call graph.
- **Proposed changes:** `cmd/aiops/main.go` and test, `Makefile` one-artifact build, minimal early refusals/tests in four old command packages. This deliberately larger cohesive boundary closes all inventoried command startups together; do not refactor their deferred engines.
- **Tasks:**
  - [ ] Add minimal new manual/help/readiness dispatcher whose diagnostic route returns explicit unavailable until mandatory controls are complete; called symbols exist first.
  - [ ] Gate old agent/workflow/project/chat start/resume/show/memory/model branches before authentication, inference, legacy store initialization or ingestion, even when built/invoked directly. Inventory any extra routes and safely disable them.
  - [ ] Build only proposed `bin/aiops`; old source may remain compileable/tested but is not another delivered artifact. Never auto-delete installed/stale user binaries.
  - [ ] Add public-entry traps for model/cloud/store/registry side effects and catalog/help/readiness zero lookup; record retained/routed/disabled status and compatibility guidance.
- **Compile-safe/excluded:** one dormant runtime; no real auth/store/lookup, no false-success stub, no model analysis/resume compatibility implementation.
- **Validation/post-work:** F, old command focused tests, B2 build/output inventory, I/X as available; review all linked routes and complete diff.
- **Risk/rollback/repair:** accidental surviving startup is high risk; fix within this bounded inventory. Roll back only task code with author review, keep unsafe routes disabled—never restore bypasses as an operational fallback.
- **Handoff/stop:** H/E; new diagnostics unavailable, all old public branches safely refuse.

### Chunk 3: Define Versioned Safe Results and Provenance

- **Goal/requirements:** V6; FR-027/039, NFR-008/013 contract before callers.
- **Entry/dependencies:** 2.
- **Inspect:** PRD Data/API Contracts, task §7, old `ServerObservation` only for compatibility.
- **Proposed changes/symbols:** `internal/diagnostic/result.go` and test; logical `Result`, safe error/field-state/provenance types and human/JSON representation contract.
- **Tasks:**
  - [ ] Define all eight statuses, request/tool/version/correlation/original-resolved target, time/duration or explicit NA, truncation/redaction/withholding and evidence links.
  - [ ] Define safe error categories and logical available/denied/unavailable/not-applicable field states; distinguish unsupported collection from healthy/empty evidence.
  - [ ] Version semantics, document translations without inheriting seven-status/exit-code schema; SDK calls have no invented subprocess exit.
  - [ ] Add table fixtures for all outcomes and independent truncation/redaction combinations, immutable identity/provenance and bounded public error representation.
- **Compile-safe/excluded:** pure contract, no unsafe raw serializer fallback or connected reader; later fields are not speculative investigation schema.
- **Validation/post-work:** F/D, snapshots and symbol/import checks; no production sink yet.
- **Risk/rollback/repair:** ambiguous missing data or health implication; repair contract tests/representation in scope. Revert only unconsumed new contracts if needed, keeping runtime dormant.
- **Handoff/stop:** H/E; explicit complete contract available for later safe callers.

### Chunk 4: Reviewed Definitions, Strict Inputs and Trusted Requests

- **Goal/requirements:** V2/V7 and per-call authority contract; FR-002/010/023/040/044/045.
- **Entry/dependencies:** 3.
- **Inspect:** observed tools registry/interface, scoped broker checks; current task §§4.1–4.2.
- **Proposed changes/symbols:** `internal/diagnostic/registry.go` and test; fixed definitions/validated request/trusted-context/internal read-operation contracts, no public SDK handle.
- **Tasks:**
  - [ ] Define only current named server-basic capability and private necessary suboperations, not a three-tool/full-domain catalog; immutable fixed mapping with reviewed metadata/profile/prerequisites/limits.
  - [ ] Validate exact request shape, duplicate/unknown/missing/extra/wrong-type/malformed/oversized data and complete input consumption; reject implementation/endpoint/path/host/profile/policy/budget overrides.
  - [ ] Establish application-owned context and internal contracts for authorization/admission/audit/readers before wiring callers. Unimplemented operations explicitly unavailable, not success.
  - [ ] Document finite justified argument/time/requests/retries/pages/records/response/output/resource limits; copy no archived numeric contract. Test zero-call pre-dispatch denials and valid counterpart, tool-local validation obligations and no denial retry/fallback.
- **Compile-safe/excluded:** definitions do not authorize calls; no caller-forged context, auth/client construction or enabled collection.
- **Validation/post-work:** F/D/X; counters/traps for every override and safe invalid/denied outcomes.
- **Risk/rollback/repair:** a validator can change literal-name intent; do not trim/case-fold names or invent ASCII restrictions. Roll back proposed definition changes only; retain disabled exposure.
- **Handoff/stop:** H/E; trusted/internal contracts ready, diagnostics still unavailable.

### Chunk 5: Minimize and Sanitize Before Every Sink

- **Goal/requirements:** V6 and FR-018/029; zero prohibited disclosure.
- **Entry/dependencies:** 4.
- **Inspect:** result contract, old raw fault/extra-spec/error projection; task §6.1/§7.
- **Proposed changes/symbols:** `internal/diagnostic/sanitize.go` and test; safe transformation/error normalization and reviewed sink-value contract.
- **Tasks:**
  - [ ] Implement bounded structured/text/error/argument transformations and explicit withholding for unsupported/unsafe values; allowed projections precede redaction.
  - [ ] Cover nested secret keys, headers/bearer/PEM/assignments, invalid encoding, hostile instructions, huge/deep/work-limit inputs and split/multibyte truncation. Never fall back to raw error/string/debug/temp output.
  - [ ] Test canaries across every proposed sink representation (CLI, audit, control/evidence metadata, telemetry, serialization/temp), retaining only necessary scoped local identifiers.
- **Compile-safe/excluded:** pure tested transformation; all later sinks must accept only minimized/sanitized values. No remote aliases, exports or knowledge pipeline.
- **Validation/post-work:** F/D/X, independent truncation/redaction/withholding fixtures, diff review.
- **Risk/rollback/repair:** partial output before failure leaks; make transformation atomic-to-caller and fail closed. Revert unconsumed helper only, no raw fallback.
- **Handoff/stop:** H/E; safe transform contract ready before persistence.

### Chunk 6: Protected Versioned New Namespace and Durable Commit

- **Goal/requirements:** V10/V11; FR-014/029/050, NFR-004/005/012.
- **Entry/dependencies:** 5; **concrete G4 separately reviewed/approved before persistent execution**, safe synthetic fixture setup.
- **Inspect:** G4 realization, observed store helpers and their missing directory durability; no real legacy records.
- **Proposed changes/symbols:** `internal/protectedstore/store.go` and test; minimal versioned scoped records/complete durable commit and safe open/reopen; accept bounded already-sanitized values without importing `diagnostic` or its authorization types.
- **Tasks:**
  - [ ] Implement protected new namespace distinct from every legacy root, scope/request partitioning and version/integrity validation; unsupported/corrupt/unsafe data visibly refused, never auto-repaired/imported.
  - [ ] Enforce reviewed ownership/modes/ancestor/regular-file/symlink/replacement controls and initial file/directory creation durability, full write/file-sync/rename/directory-sync ordering.
  - [ ] Add real temporary-filesystem first-create/reopen and synthetic legacy hash/read traps; inject short write/flush/sync/rename/permission faults. All persisted values already sanitized.
- **Compile-safe/excluded:** storage primitive only; no active diagnostic; no investigation history/migration or raw payload retention without approved classification.
- **Validation/post-work:** F/S/O/X; real filesystem and hooks both required; no false saved-success on ambiguous failure.
- **Risk/rollback/repair:** unsafe metadata or partial commit; stop/refuse rather than repair/delete user state. Rollback new code only, preserve synthetic evidence and any authorized new-store records.
- **Handoff/stop:** H/E; durable protected primitive demonstrated, no concurrent/admission claim yet.

### Chunk 7: Cross-Process Writer Arbitration and Persistent Admission Health

- **Goal/requirements:** V9/V10; ADR B4, serialized/rejected writers and restart-safe fail-closed admission.
- **Entry/dependencies:** 6; approved G4 lock/health ordering, independent fixture process capability.
- **Inspect:** store implementation and G4 admission/lock-order design; scoped broker mutex is comparison only.
- **Proposed changes/symbols:** `internal/protectedstore/admission.go` and test; shared admission lease/lock, health/uncertainty checks.
- **Tasks:**
  - [ ] Serialize writers/admissions or finitely reject contention across independent processes with bounded lock acquisition and no deadlock/interleaving.
  - [ ] Preserve unresolved intents/control faults across caller exit/restart; absence of a writable health marker is not proof of safety. Default refusal when state/health cannot be established.
  - [ ] Test independent writers, process death/reopen, corrupt/incompatible control, unwritable marker and stale healthy-memory state. No production dispatch wired yet.
- **Compile-safe/excluded:** common health prerequisite, no ack UI or auto replay/reset; no shared-service/distributed lock infrastructure.
- **Validation/post-work:** F/S/R/O; process barriers and actual lock observations, not goroutine-only proof.
- **Risk/rollback/repair:** crash clears latch/unsafe parallel grant; repair within current primitive and budget. Revert code while retaining fail-closed data, never clear a fault to make rollback appear healthy.
- **Handoff/stop:** H/E; separate processes cannot bypass failed/unresolved admission.

### Chunk 8: Finite Managed Capacity and Honest Physical Disk Failure

- **Goal/requirements:** V10/V11; FR-049 and capacity portion FR-048.
- **Entry/dependencies:** 7; G2 synthetic finite limit, approved G4 capacity/reservation design, expendable bounded filesystem facility.
- **Inspect:** new managed/control records and protected data accounting; no real legacy data.
- **Proposed changes/symbols:** `internal/protectedstore/capacity.go` and test; accounting/reservation/check-health and distinct quota/ENOSPC outcomes.
- **Tasks:**
  - [ ] Reject absent/nonfinite/unusable limit at startup; account managed records, necessary retained provenance/control and safe required-write capacity before admission.
  - [ ] Distinguish managed exhaustion from actual disk-full/inode/write exhaustion; unexpected required-write failures retain fail-closed semantics even after capacity checks.
  - [ ] Test missing/unusable/exhausted quota, real ENOSPC on supplied bounded fixture filesystem, and synthetic unmanaged legacy allocation outside quota; no silent unexpired eviction.
- **Compile-safe/excluded:** no automatic cleanup until 11, no host/repository disk filling, no agent mounting/provisioning privilege or rich export/delete UX.
- **Validation/post-work:** F/S/O; record actual filesystem capacity/failure evidence separately from injected write errors; unavailable facility is blocker to this evidence.
- **Risk/rollback/repair:** false reservation guarantee or unmanaged pressure; never claim quota predicts all OS failures. Roll back capacity code only with admission disabled, not record eviction.
- **Handoff/stop:** H/E; startup/admission refuses unsafe capacity and reports distinct failures.

### Chunk 9: Durable Intent/Outcome Dispatch and Disclosure Ordering

- **Goal/requirements:** V2/V6/V8/V9; FR-028 and ADR B3/B4 actual state machine.
- **Entry/dependencies:** 8; result/registry/sanitizer/store/admission contracts exist. Readers are synthetic recording substitutes, no credential construction.
- **Inspect:** task §6.2/§6.3, store failure semantics and internal operation contracts.
- **Proposed changes/symbols:** `internal/diagnostic/gateway.go` and test; `Gateway.Execute`-style coordinator (name proposed), bounded private per-operation read and result publication gates.
- **Tasks:**
  - [ ] Validate authority/input/prerequisites and audit safe pre-dispatch rejections with timestamp/status/NA duration, or expose unavailable denial audit as local gap with zero downstream calls.
  - [ ] Persist sanitized durable intent and required control/capacity before each admitted bounded lookup/read/suboperation; attribute every API read to finite scope/budget and intent.
  - [ ] Recheck authorization between operations; sanitize observations/outcomes then durably audit result before returning any diagnostic payload.
  - [ ] On failed/ambiguous intent dispatch nothing; on outcome failure stop shared admission, withhold payload and expose safe failure/possible read/gap independently of broken sink. No fallback sink, fabricated audit or ambiguous append retry.
  - [ ] Add operation-order and secret-canary recording tests for successful/denied/invalid/unavailable paths and every persistence transition; preserve uncertainty after process failure.
- **Compile-safe/excluded:** gateway tested with private fakes, production runtime unavailable; no credentials, model, automatic replay, exact-once claim or audit of raw payload by default.
- **Validation/post-work:** F/D/S/O/X, explicit order trace showing intent→read→outcome→disclosure; result failure means zero payload and zero next read.
- **Risk/rollback/repair:** publication races audit failure; fix state machine, never weaken withholding/assertions. Rollback unexposed coordinator only, preserve intents/control faults.
- **Handoff/stop:** H/E; durable ordering and fail-closed shared failure propagation evidenced.

### Chunk 10: Acknowledged Recovery and Explicit Uncertain Re-collection

- **Goal/requirements:** V9; FR-028/015 current subset, task §6.3.
- **Entry/dependencies:** 9 and approved G4 recovery ordering; no user-exposed resume.
- **Inspect:** unresolved intent/outcome states and authorization contract; failure marker semantics.
- **Proposed changes/symbols:** `internal/protectedstore/recovery.go` and test; minimal scoped gap/acknowledgement/confirmation records and admission decision contract.
- **Tasks:**
  - [ ] Keep recovered store paused until operator acknowledges known gaps/uncertain calls; acknowledgement survives restart and is never inferred from successful startup or silently fabricated.
  - [ ] Require current authorization after ack; separately record explicit confirmation for uncertain re-collection and new request/observation identity/timestamp, retaining prior uncertainty.
  - [ ] Define withheld payload release only after resolution, durable result audit and current authorization. If unrecoverable under chosen minimal retention, report unavailable rather than reconstruct/replay.
  - [ ] Test no ack, ack revoked, ack without recollection confirmation, fully authorized confirmed recollection, fault during ack and restart; no automatic admission/release.
- **Compile-safe/excluded:** recovery primitive only; no investigation lifecycle/resume/full export/deletion feature.
- **Validation/post-work:** F/S/D/O with independent restart cases and zero-read unauthorized branches.
- **Risk/rollback/repair:** ack conflated with consent/authority; preserve separate tests/records. Rollback code only with admission paused; never erase recovery state.
- **Handoff/stop:** H/E; manual recovery rules explicit and testable before CLI wiring.

### Chunk 11: Applicable Retention and Bounded Audited Cleanup

- **Goal/requirements:** V11/V8; FR-048/049/050 current first-use safeguards.
- **Entry/dependencies:** 10; reviewed G4 cleanup/audit/capacity rules and controlled fixture clock.
- **Inspect:** current record classifications and recovery-critical provenance; task §6.4.
- **Proposed changes/symbols:** `internal/protectedstore/cleanup.go` and test; bounded eligibility/cleanup admission using store-defined durable-event interfaces/callbacks, composed with the gateway at the command layer without an import cycle.
- **Tasks:**
  - [ ] Apply configurable 90-day sanitized-audit default, bounded startup and operating cleanup, overdue restart handling and visible failures. Never claim cleanup ran while stopped.
  - [ ] Delete only eligible known data after durable cleanup intent; failed intent deletes nothing; post-delete outcome-audit fault records gap/possible deletion, stops affected admission, never claims rollback.
  - [ ] Protect unresolved recovery information, unknown/active/referenced records and unexpired audit/data. Unknown investigation types cannot be invented as terminal; 30-day terminal default is documented for later introduction, not a new schema now.
  - [ ] Test clock/default/override/boundaries/work budget, audit faults, quota pressure, unknown/active/reference protection and synthetic legacy no-access/no-delete/no-approval-use/hash invariance.
- **Compile-safe/excluded:** only applicable present-data cleanup; no reference graph, early terminal deletion, rich export, legacy retention or migration.
- **Validation/post-work:** F/S/O/D; exact deleted/retained sets and audit order, no premature audit deletion.
- **Risk/rollback/repair:** cleanup can destroy evidence; fix eligibility/order rather than auto-repair. Rollback disables cleanup while preserving data/audit; actual deletion cannot be undone.
- **Handoff/stop:** H/E; bounded audited cleanup proven for current record classes.

### Chunk 12: Authenticated Ingress and Independent OS Authority

- **Goal/requirements:** V1–V3, FR-002/010/021/022/033; actual boundary domain, not package trust.
- **Entry/dependencies:** 11; **concrete G1 separately reviewed/approved**, G2 synthetic non-root context fixture setup, approved protected configuration/access design. No operator provisioning by agent.
- **Inspect:** G1 realization, command inventory, policy/context and health contracts.
- **Proposed changes/symbols:** `internal/diagnostic/ingress.go` and test; authenticated caller binding/configuration-to-request context, mechanism-specific file split only if build/platform constraints justify it and ladder is updated in place.
- **Tasks:**
  - [ ] Authenticate/bind caller security context independently of request strings; trusted configuration selects cloud/project/targets/profile/capabilities/relationships/policy/limits/correlation and currentness, public inputs only narrow authority.
  - [ ] Keep reader/state/control credentials private to enforcement owner; no reusable credential or SDK handle returned. Arbitrary local process access is not trusted.
  - [ ] Test genuine permitted and unauthorized non-root OS contexts, peer forgery/replay/stale scope/project switch, credential/state reads/replacement and ingress denial before any downstream/auth call. Synthetic single-user mocks cannot close OS properties.
  - [ ] Local help/readiness/catalog classify required policy/audit/store/config vs optional model/knowledge/host/operator, without connectivity/lookup. No real host/route selected.
- **Compile-safe/excluded:** no reader yet, production diagnostics remain unavailable; no model/client isolation enablement, network-exposed service, account creation or extra privileges.
- **Validation/post-work:** F/D/I/O/X, credential/state canaries and unauthorized-local-caller proof on target OS. Missing actual security-context fixture blocks enablement.
- **Risk/rollback/repair:** IPC without independent authentication creates bypass; stop if realization infeasible. Disable ingress on rollback, never widen permissions or share credentials for convenience.
- **Handoff/stop:** H/E with G1 evidence and all unverified deployment facts separated.

### Chunk 13: Private Trusted Reader and Collection-Time Transport Bounds

- **Goal/requirements:** V2/V3/V7; FR-022/023/024/040/043/044.
- **Entry/dependencies:** 12; G3 exact API/destination/reader review before collector enablement, G2 synthetic setup, G1/G4 satisfied for affected fixture execution.
- **Inspect observed:** `internal/openstackclient/{compute,network,project}.go`, Gophercloud declared dependency; do not reuse ambient constructors unchanged.
- **Proposed changes/symbols:** `internal/diagnostic/reader.go` and test; enforcement-owner-private trusted configuration/client creation and bounded operation transport. Existing helpers may remain unreachable in dormant code; no public ambient route.
- **Tasks:**
  - [ ] Construct only approved dedicated-reader authentication from the reviewed current source, after pre-dispatch validation/intent; independently verify authenticated principal/project before resource reads, with no stronger/ambient/profile/provider fallback.
  - [ ] Enforce fixed approved auth/service destinations, redirects/pagination and proxy restrictions before credentials/token delivery; response/catalog data never creates grants.
  - [ ] Apply response-byte/resource/time/request/retry bounds during authentication and collection/decoding, close resources and preserve cancellation. Tool-local operation validation remains mandatory.
  - [ ] Add local synthetic transport counters/token traps for invalid/denied no-auth, post-auth mismatch no resource calls, hostile destination/stream/redirect/page links and cancellation. No real credentials or archived HTTP exception.
- **Compile-safe/excluded:** reader only accessible within authenticated audited owner, public runtime still gated; no generic HTTP/SDK/utility caller or independent client handles.
- **Validation/post-work:** F/D/X/O as applicable; request methods/destinations and no credential disclosure across errors.
- **Risk/rollback/repair:** authentication precedes denial or credential exfiltration; correct ordering, do not add fallback. Rollback disconnects reader and keeps runtime unavailable.
- **Handoff/stop:** H/E; narrowly bounded private transport ready for identity helpers.

### Chunk 14: Bounded Literal Server Identity Resolution

- **Goal/requirements:** V4/V2/V7; FR-003 and preserved manual authorization semantics.
- **Entry/dependencies:** 13; reviewed exact lookup permission/bounds in G3.
- **Inspect observed:** `get_server.go:resolveServer`, HTTP identity fixtures, request and audit contracts.
- **Proposed changes/symbols:** `internal/diagnostic/identity.go` and test; canonical UUID/literal-name classifier and bounded authorized resolver.
- **Tasks:**
  - [ ] Preserve original input and meaningful leading/trailing/internal whitespace/case/Unicode; reject unsupported or malformed UUID intent safely with UUID guidance, never silently reinterpret/normalize into a different target.
  - [ ] Require explicit manual action/disclosed bounded lookup effects under current trusted project/target grants; help/readiness does not authorize lookup. No pre-plan approval UX is added.
  - [ ] Bound pages/records/time/bytes and audit every admitted lookup operation; independently exact-match approximate API results and verify resolved UUID/project/grant before diagnostic GET.
  - [ ] Reject missing/ambiguous/unresolved uniqueness/case-whitespace mismatch and out-of-scope response without guessed GET or unrelated candidate disclosure; record original/resolved identity only after verification.
  - [ ] Add full V4 table with call-order/denial/audit/boundary/cancellation tests including supported Unicode and invalid encoding.
- **Compile-safe/excluded:** helper only through owner; no `AllPages`, broad discovery, investigation/planner consent or invented ASCII/archived identifier rules.
- **Validation/post-work:** F/D/I when seam exists; exact lookup/GET counts and literal query evidence.
- **Risk/rollback/repair:** filters can overmatch or hide duplicates beyond bounds; refuse on uncertainty. Disconnect resolver on rollback, never choose a first match as fallback.
- **Handoff/stop:** H/E; safe exact identity for projection without wider grant.

### Chunk 15: Required Server Basics and Explicit Field Availability

- **Goal/requirements:** V5/V6; FR-025, NFR-007/013.
- **Entry/dependencies:** 14.
- **Inspect observed:** `ServerObservation`, raw fault/host and old projections; required field list in task §4.3.
- **Proposed changes/symbols:** `internal/diagnostic/server.go` and test; minimal server-basic projection and per-field state assembly.
- **Tasks:**
  - [ ] Read only verified permitted target; validate returned ID/project before any use/related calls/disclosure. Wrong response records real prior contact honestly and withholds unsafe output.
  - [ ] Provide status, image, flavor, networks, config drive and AZ with available values or explicit denied/unavailable/not-applicable safe reason; include available safe fault, never fabricate absence as healthy.
  - [ ] Minimize nested image/flavor/network/fault content; omit host placement, raw fault details, user data/full configurations and unrelated fields. Feed only safe values to result/audit path.
  - [ ] Test each required state, missing/denied/unsafe fields and fault, malformed responses, target/project mismatch, partial limitation and timestamp/provenance.
- **Compile-safe/excluded:** explicit incomplete related evidence until later helpers, never silent successful placeholder; no health/root-cause inference or full catalog.
- **Validation/post-work:** F/D/X; expected field/state table and canaries.
- **Risk/rollback/repair:** opaque nested output escapes minimization; whitelist projections, withhold unsafe data. Rollback disables collection rather than restoring old raw projection.
- **Handoff/stop:** H/E; required server evidence and safe relationship provenance available.

### Chunk 16: Verified Related Flavor Only

- **Goal/requirements:** V5/V2; FR-011 current flavor subset.
- **Entry/dependencies:** 15; G3 allowed related category.
- **Inspect observed:** `get_flavor.go`, scoped broker flavor check, authorized server provenance.
- **Proposed changes/symbols:** `internal/diagnostic/flavor.go` and test; private relationship-checked flavor operation/projection.
- **Tasks:**
  - [ ] Admit only explicitly granted related-flavor category with verified referenced flavor from current authorized server observation; caller assertion is not proof.
  - [ ] Recheck current authorization/budgets, persist intent, perform one bounded permitted GET, verify returned identity and minimize required flavor evidence before outcome audit/disclosure.
  - [ ] Test valid, absent, forged/changed flavor, wrong identity, denied/missing detail, secret payload and revoked category; no broad flavor search or extra-spec read, no stronger profile.
- **Compile-safe/excluded:** no standalone arbitrary flavor public tool, unrelated fields/catalog or fallback search.
- **Validation/post-work:** F/D/X; zero related call without proof/category, exact GET/outcome trace for valid counterpart.
- **Risk/rollback/repair:** stale/forged linkage creates grant; refuse and qualify field state. Rollback disables related flavor, never enables old unrestricted flavor route.
- **Handoff/stop:** H/E; narrow relationship evidence only.

### Chunk 17: Verified Project/Device-Confined Ports Only

- **Goal/requirements:** V5/V7/V2; FR-011 current port subset.
- **Entry/dependencies:** 16; G3 approved port visibility and category, verified server observation.
- **Inspect observed:** `get_ports.go` and tests; preserve compatible project/device checks and tight collection safeguards.
- **Proposed changes/symbols:** `internal/diagnostic/ports.go` and test; private bounded related-port collection/projection.
- **Tasks:**
  - [ ] Require explicit related-port grant and verified current server/project relationship before lookup; revalidate authority/limits and durably audit admitted reads/pages.
  - [ ] Bound collection before buffering, verify returned project/tenant consistency and device/ID, minimize server-basic network context with explicit gaps.
  - [ ] Test valid/foreign/wrong-device/conflicting-tenant/missing-proof/forged-ID responses, pagination/bounds/denial/cancellation and secret-bearing fields; record real prior read on post-response denial.
- **Compile-safe/excluded:** no public arbitrary port selector, network/subnet traversal, project summary, host discovery or full server-network feature.
- **Validation/post-work:** F/D/X; counterpart and negative request counts, response resource closure and safe outcome ordering.
- **Risk/rollback/repair:** broad port list or response-driven topology expansion; deny and stop later reads. Rollback disconnects related ports, not unrestricted legacy collector.
- **Handoff/stop:** H/E; only reviewed server-basic port context reachable internally.

### Chunk 18: Cancellation, Revocation and Limit Race Closure

- **Goal/requirements:** V7/V8/V9; NFR-003 and current FR-010/040/042 end-to-end behavior.
- **Entry/dependencies:** 17; reader/state machine complete.
- **Inspect:** complete request lifecycle from ingress through lookup/server/flavor/ports/audit; shutdown and publish points.
- **Proposed changes/symbols:** `internal/diagnostic/lifecycle.go` and test; only missing current lifecycle coordination, not a scheduler/retry engine.
- **Tasks:**
  - [ ] Propagate deadline/cancel/current authorization across each suboperation/page and before publication; stop new work on expiry/revocation/fault, attempt bounded cancellation/cleanup and withhold unauthorized results.
  - [ ] Cover pre/between/in-flight/late-result races, floods/endless pagination, all finite budget exhaustion, shutdown and closed resources; no denial retry or later dispatch.
  - [ ] Preserve honest possible completed read/gap/uncertainty and outcome audit; cancellation cannot undo collection. Integrate recovery/disclosure checks with no raw fallback.
- **Compile-safe/excluded:** safe unavailable gate still guards public runtime; no general background orchestration/model paths.
- **Validation/post-work:** F/D/S/R/O as relevant; deterministic barriers not sleep-only races, bounded cleanup timings and call counters.
- **Risk/rollback/repair:** late payload races revocation; make final authorization check part of publication. Rollback cancels/disables dispatch, not weaken race tests.
- **Handoff/stop:** H/E; lifecycle safe before public CLI activation.

### Chunk 19: Integrate Named Manual CLI and Versioned Scenario Seeds

- **Goal/requirements:** V1/V4/V6/V8/V9/V11/V12; operator-visible four-step slice.
- **Entry/dependencies:** 18; reviewed concrete G1–G4, synthetic operator config, existing focused proofs. No live enablement.
- **Inspect:** dormant command, current entry inventory, safe gateway/recovery/readiness interfaces, old command traps.
- **Proposed changes/symbols:** `cmd/aiops/manual.go` and test, narrow wiring in existing new `main.go`, and synthetic `internal/diagnostic/testdata/manual/` expected/actual-version fixture inputs as needed. Larger set justified only by public integration and deterministic seeds, no feature detached from tests.
- **Tasks:**
  - [ ] Route explicit named manual action, disclosed lookup/related effects and operator choices through authenticated owner; expose concise human and versioned JSON output, safe catalog/help/readiness without contact.
  - [ ] Wire minimal scoped local inspection/copy of already sanitized current records and recovery acknowledgement/separate uncertain recollection confirmation to current controls. Preserve safe inspection/copy and operator-triggered eligible cleanup where possible during storage failure, with the same scope/sanitization/audit protections; explain what cannot run when required controls fail. Do not add investigation resume, rich export/early-deletion UI or a generic file tool. Missing mandatory controls refuse dispatch, optional dependencies remain unnecessary.
  - [ ] Wire bounded startup/runtime cleanup and safe shutdown within current runtime; no cleanup of legacy data or silent release/replay after restart.
  - [ ] Create healthy-server, permission-denied and hostile/secret scenario seeds and versioned expected/actual record format recording calls/targets/outcomes/provenance/gaps without scoring platform.
  - [ ] Exercise actual CLI→owner→controlled API→sanitized intent/outcome/result; retest old commands/start/resume/show/memory and direct-route attempts under side-effect traps.
- **Compile-safe/excluded:** only tested manual/readiness surface active in controlled configuration; real startup still requires trusted operator setup/gates. No automatic tool selection/model/MCP/broad catalog.
- **Validation/post-work:** F/I/D/S/X, all eight outcomes through public seam, no-model demo and exact command inventory; full diff review.
- **Risk/rollback/repair:** CLI bypasses final audit or normalizes whitespace; assert public behavior, not helper alone. Disable new route on rollback, preserve data/faults and old route refusals.
- **Handoff/stop:** H/E; useful manual fixture workflow, no deployed/live acceptance claimed.

### Chunk 20: Close Mandatory OS, Process, Crash, Capacity and Package Evidence

- **Goal/requirements:** V1–V12 evidence closure, especially V3/V9–V12; no new capability.
- **Entry/dependencies:** 19; existing introducing-chunk tests already pass, target-OS non-root/security-context, independent-process, bounded filesystem and utility-free fixture facilities actually available and authorized.
- **Inspect:** §5 coverage, all fixture discovery/skip results, command linkage/artifact map and actual store/ingress failure states.
- **Proposed changes:** test-only `internal/diagnostic/system_test.go` and `internal/protectedstore/process_test.go` plus strictly needed synthetic fixtures; exact tests/selectors recorded here at introduction. No new production API or test bypass flag.
- **Tasks:**
  - [ ] Run and close actual separate-process writer/admission/crash barriers before dispatch, in-flight, after read/before outcome, ambiguous append, unwritable marker, restart/no ack/revoked ack/no-confirm/confirmed recollection; prove no replay/unaudited admission/disclosure.
  - [ ] Reproduce real first-use/reopen and OS permission/path/symlink/context attacks and credential/state access denials; no mocks-only isolation/durability claim.
  - [ ] Run actual bounded-filesystem exhaustion distinct from managed quota including synthetic legacy consumption; cleanup intent/outcome faults/default/runtime/startup/overdue/protected-record cases, hashes plus no-read/index/send/import/approval-use traps.
  - [ ] Build and exercise single-runtime artifact in controlled utility/interpreter-free environment using synthetic local API fixtures; record process/file access, disabled capabilities and absence of diagnostic subprocess/dependency. Do not install or provision fixture infrastructure implicitly.
  - [ ] Record exact commands, fixture environment, expected tests discovered/counts/skips and evidence limitations. A missing mandatory facility/test is blocker, never a green skip.
- **Compile-safe/excluded:** test-only strengthening; no feature, future module, live lab or destructive host test. Production defects uncovered require explicit bounded in-scope repair/revalidation, not hidden broad changes.
- **Validation/post-work:** O/P/I/R/S/D/X plus F for changed test files; full test/diff/security review, preserve unrelated work.
- **Risk/rollback/repair:** test kills/fills wrong target; fixture confinement must be checked before execution. Stop on unsafe access; clean only owned disposable artifacts, preserve evidence and no state-reset workaround.
- **Handoff/stop:** H/E; mandatory non-mock evidence closed or exact blocker reported.

### Chunk 21: Final Verification, Operator Guide, Demo and Full-Diff Audit

- **Goal/requirements:** complete selected task §11, four steps/§01.6 and V1–V12; no new feature or next phase.
- **Entry/dependencies:** 20 and every implementation/evidence exit; current source/approval/preflight/candidate identities still valid.
- **Inspect/changes:** all task delta from recorded base, relevant staged/unstaged/untracked work, proposed operator guide from 1, fixtures and build outputs. Documentation corrections and safe task-created accidental artifact cleanup only; no application feature work in this chunk.
- **Tasks:**
  - [ ] Rerun focused checks then full `rtk go test -count=1 ./...`, `rtk make build`, `rtk go vet ./...`, affected race checks and mandatory OS/process/crash/disk/package/manual suites. Inspect actual discovery/counts/skips, not only exit status.
  - [ ] Demonstrate documented no-model named workflow and help/readiness/disabled entries with fixture evidence and exactly one fresh runtime artifact; verify every required field/status/gap/identity and no utility/interpreter dependency.
  - [ ] Complete operator guide: non-root external Ubuntu observer/route prerequisites, operator-only setup/reader source/scope/revocation/no fallback, registry/versions/limits, human/JSON/gaps, audit ordering/fault/ack/recollection, protected new data/quota/disk/retention/cleanup/legacy handling, safe scoped inspection/copy and operator-triggered eligible audited cleanup during faults where possible, stop/recovery and utility-free fixture reproduction. No real endpoint/identity/path/secret values inferred from archive or `.env`.
  - [ ] Map actual evidence to all current PRD/NFR/AC contributions and V1–V12. Distinguish local target-OS fixtures from actual deployed observer/reader policy and later cloud/three-host/model/MCP requirements, which remain separately gated/NOT_RUN.
  - [ ] Inspect full base-to-candidate diff plus working/index/untracked files; validate symbols/imports/callers, all supported routes, fixed read-only methods, authority boundaries, no raw-error/sink leakage and no future scaffolding/source-of-truth edits/unrelated lab changes.
  - [ ] Remove only identified task-created accidents/generated temporary artifacts, never reset/clean user work, erase protected records or revive old bypasses for rollback. Recheck full state/diff after corrections.
  - [ ] Report base/candidate/source fingerprints, chosen Level 1 realizations and gate evidence, changed components/entry map, exact commands/test counts/skips/results, manual demo/actual OS evidence, functional/integration risk/rollback and all unverified items/deviations.
- **Validation/post-work:** B2/A/R/O/P/I/X and complete document/link QA; no mandatory offline evidence can be reclassified optional. Format only files actually changed; rerun affected checks after allowed corrections.
- **Repair/escalation:** a feature defect requires an explicit bounded repair rung recorded in this same controlling plan and separately selected execution, preserving previous evidence, then repeat final gate; do not hide implementation in cleanup or auto-run it.
- **Risk/rollback:** green old suite can miss public invariant; requirement evidence is mandatory. Operational rollback disables new admission, preserves audit/uncertainty and operator data; no migration/fallback/live activation implied.
- **Handoff/stop:** no automatic next-delivery handoff. Report exactly `READY_FOR_REVIEW`, `BLOCKED` or `INCOMPLETE` under task/executor requirements. Mandatory offline failures/missing evidence prevent `READY_FOR_REVIEW`. Self-check is not independent review; stop, without commit/Phase 02/deployment.

## 10. Final execution acceptance checklist

All remain unchecked during planning:

- [ ] Four steps and §01.6 are satisfied, with actual one-runtime/public-entry/unauthorized-local-caller proof.
- [ ] Every current requirement contribution and V1–V12 has discovered, executed, successful mandatory offline evidence; zero unauthorized execution, mutation or prohibited disclosure.
- [ ] Literal identity, explicit field states, verified narrow relationships, eight-status/versioned output, limits/revocation/cancellation and truthful gaps are demonstrated at public seams.
- [ ] Durable sanitized intent/outcome precede dispatch/disclosure respectively; failure/uncertainty survives processes/restart; ack/current authority/separate recollection/new observation remain distinct.
- [ ] Protected new-store first-use/writer/quota/real-disk/cleanup safeguards pass; synthetic legacy content/approvals untouched and unused, no real legacy inspection.
- [ ] Applicable G1–G4 concrete realization approvals/reviews/evidence recorded; deployed/live evidence not fabricated from fixtures, G5/G6 and later phases untouched.
- [ ] Full Go verification/build/vet/affected race and mandatory OS/process/package suites pass; test discovery, skips and limitations explicitly reported.
- [ ] Operator guide and safe no-model fixture demo reproducible, full tracked/staged/untracked diff/security/scope audit complete, no unsafe stubs or speculative future modules remain.

## 11. Risks, unresolved prerequisites and escalation

| Risk/prerequisite | Evidence and mitigation | Planning/execution effect |
| --- | --- | --- |
| Concrete boundary/storage not selected or approved | Current ADR intentionally constraint-based; 1 records mechanisms, task §3/ADR §6 govern timed separate review/approval and 6/12/13 gate affected work. | Not a Level 2 planning blocker; no immediate enablement permitted. If infeasible without changed guarantees, stop with precise Level 2 request. |
| Go 1.27.1 unavailable/caches missing | Module declares version; nothing was executed to verify it. B0/Chunk 0 must confirm with offline/no-download controls. | Unverified prerequisite, not claimed failure; required unavailable tooling blocks execution, not silently downgrade/install. |
| Real OS identity/disk/crash/utility-free fixtures unavailable | Tests require more than ordinary mocks; facility/access/provisioning not established here. Discover early in 0/1, execute alongside changes and close in 20. | Mandatory missing offline evidence blocks acceptance; obtain separately provided safe facilities, never root/host-disk workaround. |
| Historical review differs from approved bytes | Exact old hashes recorded; original review/update diff remains unavailable. The later initial-depth preflight independently inspected the current committed contents; see §14. | Historical draft-to-approved drift remains `UNVERIFIED_DRIFT`; the old draft verdict is not reused. Revalidate affected checks on material changes. |
| Entry consolidation leaves raw route or old binary | Four mains and registry consumers observed; 2/19 inventory includes direct builds/branches, 20 package proof. | Disable before side effects; no delivered second runtime or bypass revival. |
| Audit fault cannot persist its own marker | Required state may be uncertain/unwritable; durable intent/control validation and fail-closed startup, 7/9/10/20. | Absence of marker never restores health; independent caller/restart tests mandatory. |
| Full payload optionality obscures withholding recovery | Minimal metadata/no payload is a proposal; G4 must document classification. | If payload irrecoverable, explicitly unavailable and confirm re-collection; no implicit cached release/reconstruction. |
| Cleanup removes required uncertainty/evidence | Current types only, 90-day audit default, protected unknown/active/reference records and durable delete intent. | No early audit deletion, silent eviction or legacy cleanup; full graph/lifecycle remains 04. |
| Scope expands from full PRD/task traceability | §5 partitions mixed rows and preserves later obligations. | No model/resume/MCP/catalog/host/infrastructure feature can enter this ladder for convenience. |
| Plan adoption and execution remain separate | The later independent preflight is recorded in §14; the plan itself has not been independently accepted and no implementation has begun. | Explicitly adopt the controlling plan and separately authorize the chosen chunk; do not proceed automatically. |

Escalation reports must state exact blocked dependent work, evidence, authority level, viable alternatives/tradeoffs and recommendation. Do not ask for another approval for ordinary in-scope test/repair details; do not treat compliance tradeoffs as permission to decide a real material risk.

## 12. Conservative next-session prompt (not executed)

The following is a **suggested separately authorized invocation**, not current authorization or an automatically started preflight:

```text
Use chunked-implementation in SINGLE-CHUNK mode. Execute Chunk 0 only from
 docs/ai-ops-go/chunked-implementation/01-safety-foundation-and-manual-diagnostics.md
in /home/meriz/Documents/Synctech.ID/CI_CD/openstack-lab.

I authorize source/base/approval/ladder revalidation and reviewed safe credential-free
local Go baseline checks only. Re-read the current approved task, ADR, PRD,
Phase 01 roadmap, instructions and executor policy. Recheck all source/approval/base
fingerprints and tracked/staged/untracked work; preserve unrelated changes.
Verify the recorded preflight in §14 against the actual sources, base and plan;
obtain affected revalidation if material drift occurred before feature edits.
Do not implement Chunk 1 or any feature.

Confirm already installed Go 1.27.1/cached dependencies and inspect test side effects
before running. Use sanitized temporary HOME/config/data and synthetic credentials,
local-only fixtures, GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOENV=off GOWORK=off.
No downloads/installs, .env or real credentials/records, root Make/Molecule/Ansible,
live/cloud/host/model/MCP or non-loopback network service access, provisioning, destructive work,
stage/commit/push/merge/deploy. Report missing tool/OS/filesystem fixture access.

Apply the default finite two-failed-validation budget and required diff/risk checks.
No Python is needed; ask for an approved venv only if Python execution truly becomes
necessary. Report actual baseline discovery/counts/skips/results and exact candidate
state as CONTINUABLE, BLOCKED or INCOMPLETE, then stop. Ask before creating an
unrequested single-chunk handoff. Do not continue automatically.
```

Continuous-loop execution needs separate explicit selection and real fresh-session orchestration, currently unavailable in this harness. This prompt grants neither.

## 13. Planning QA and terminal assessment

This section records the original planning-stage observations and assessment, not the subsequent preflight or this later documentation update. See §14 for the subsequent review.

**Actual planning checks:** read-only Git identity/status/tracking/blob/commit-delta checks and SHA-256 comparisons; complete current PRD/task/ADR/overview/Phase 01 and later phase readings; full paired instruction/handoff, installed required skill/reference and selected historical-contract readings; relevant code/test/build/source inspection. Baseline educational text and README were inspected only to the bounded sections identified above. No full code/deployment audit is claimed.

**Document QA for this one new file:** complete read-through including ending; requirement/current-versus-deferred and V1–V12 mapping review; consecutive 0–21 numbering and earlier-only dependencies; 22 disjoint estimates totaling 15–27.25 days (90–163.5 hours); gate wording, compile-safe intermediate states, policy/handoff/failure-budget compatibility, unchecked execution tasks, relative-link/path and Markdown fence/whitespace checks; full new-file content review and final project/enclosing-repository status/diff checks. A new untracked plan is not visible in ordinary `git diff`; full read and new-file diff are required, and no staged change is intended. Final command outcomes/fingerprint are reported with delivery after these checks, not inferred from this paragraph.

### Actual document-check results

| Check | Observed result |
| --- | --- |
| Complete new-file review | Read the plan through its ending; self-checked task §8/§9 coverage, each intermediate state, gate timing and independent review boundaries. Clarified acyclic package ownership and pre-enable OS proof; no product rule changed. |
| Numbering and estimates | Text checks found 22 consecutive headings 0–21 and 22 estimate rows; sums 15–27.25 days and 90–163.5 hours. Dependencies reviewed against earlier rungs. |
| Links/Markdown | All 21 relative link targets exist; the §01.6 target heading exists; four fenced delimiters balanced; no trailing whitespace or checked execution tasks found. |
| New-file diff | Full new contents reviewed as the all-added delta; `git diff --no-index --numstat` confirms additions only. `git diff --no-index --check /dev/null <plan>` emitted no whitespace diagnostics and returned 1 for the new-file difference; this is not represented as a zero-exit check. |
| Repository/source preservation | Project staged/unstaged tracked diffs empty; exactly this plan untracked. Enclosing repository status matches the recorded unrelated modifications and 001–004 pairs. PRD/task/ADR SHA-256 rechecked unchanged. |
| Syntax/formatter/product checks | Markdown-only structural/link/whitespace checks performed. No application syntax/build/test/import check or product formatter applies to the sole Markdown addition; implementation commands remain scheduled, not executed. |

**Not run:** product tests/builds/vet/race/formatters, Chunk 0, formal preflight, independent plan/post-update specification review, real OS/product fault fixtures, cloud/host/model/MCP/lab calls, credential/.env inspection, installs, stage/commit/push/merge/deploy. All proposed implementation commands and expected behavior above remain PLANNED_NOT_RUN.

**Can proceed further?** Documentation planning is complete and suitable to propose a separately authorized Chunk 0. No material source conflict or necessary Level 2 product change was found in inspected sources. Actual implementation cannot proceed from this report alone: independent governance/preflight and execution authorization remain separate, concrete G1–G4 obligations retain their exact timing, and toolchain/mandatory fixture/environment evidence is still unverified. Do not automatically start any next action.

**Terminal planning status at the end of the planning stage: PLAN_READY.**

## 14. Recorded independent implementation preflight

The following is the complete response-only report returned by the separately authorized independent preflight in the current conversation. The user subsequently authorized recording it here. The reviewed plan fingerprint below identifies the **pre-recording** candidate, not the bytes after adding this report and clarifying historical references. This documentation update does not itself approve the plan, authorize a chunk, or extend the verdict to materially changed sources or execution states. A future executor must assess whether intervening changes, including this recording-only update, require affected revalidation.

---

# AI-OPS Go Phase 01 — Implementation Preflight

**Mode:** IMPLEMENTATION PREFLIGHT, read-only

**Pass:** INITIAL, round 1; no previous preflight report available

**Project:** Existing project with partial implementation

**Authorization:** Your invocation explicitly authorized this review—not implementation.

### 1. Verified candidate and repository state

| Item | Observed state |
|---|---|
| Branch | `aiops-go-phase01` |
| HEAD | `ae7983c9af3a243ac4b1b104f6949d3afa56f6e1` |
| Tree | `1965507f8b104f0ba2ed92586a51d951413ff467` |
| Parent | `e29fa87e293246c187f5b01604e6f012dfbb4761` |
| Commit subject | `docs(ai-ops): approve Phase 01 safety contract and ADR` |
| Commit delta | Exactly 11 added roadmap/task/ADR Markdown files; no application changes |
| Tracked staged/unstaged changes | None |
| Untracked project files | Exactly the single implementation-plan candidate below |

Under `docs/ai-ops-go/`, measured SHA-256 identities are:

| Source | SHA-256 |
|---|---|
| `prd.md` | `a685452c2b2d7303a342376117299d777131fd4ff6dfd3ffc19dd397974da9ed` |
| `aiops-baseline.md` | `cd03daa694691852842d4812b983cdbd220fba205d02d318d4f57ca9e9503e01` |
| `implementation-plan/00-implementation-overview.md` | `92bd72c67805ff2f8350dc6bcff5f7228f6b262e6e20d9fd3c627d8ebd31b1f0` |
| `implementation-plan/01-safety-foundation-and-manual-diagnostics.md` | `3f489644009010e68077749dbcc9d4cb983dd87bb83747cf46b912bf1cb20f14` |
| `tasks/01-safety-foundation-and-manual-diagnostics.md` | `977965efc06c760ce13c70b6547ac04ddf4ff2c25fd93a252e5550db7d0d5133` |
| `architecture/01-manual-diagnostic-enforcement-and-persistence-boundaries.md` | `e1f8fb358ff230f5ff1812404bc24fba5d1906d796179d8c1a93cae9b521781d` |
| `chunked-implementation/01-safety-foundation-and-manual-diagnostics.md` | `b12c42012e1b4084e17c6874750547f40885e176ce0792c951f9681b36ba5d42` |

The task and ADR are tracked and committed, with HEAD blobs:

- Task: `469814bee1c8bb30a52b1461b8efbb04de62e4f3`
- ADR: `de9ad8d08bf305a30202168888f14fb393426da4`

All measured source identities match the supplied packet. Phases 02–08 also match their recorded fingerprints.

The enclosing repository remains on `main`, HEAD `74c01ca9de6c2153a0306b037860bfe3c276b649`, with the two documented unrelated modifications and untracked `001`–`005` packet pairs. Everything was preserved.

#### Approval and freshness

**Documented approval evidence:** Both committed headers quote the owner’s approval of the task and ADR. The `004` handoff corroborates that approval and distinguishes it from commitment.

**Limitation:** The original response-only draft review and pre-update bytes were not available. Therefore:

- `NONMATERIAL_CONFIRMED` applies relative to the unchanged `004`/`005` committed snapshot.
- The exact historical draft-to-approved update remains `UNVERIFIED_DRIFT`.
- I did not reuse the older draft verdict; this review independently assessed the current committed contents.
- The documented approval records are sufficient for this preflight; no claim of independently recovering the original conversation is made.

### 2. Sources inspected

Read completely through their endings:

- The `005` instruction and paired handoff; both `004` provenance documents.
- `.agents/AGENTS.md`.
- Current PRD, task, ADR, roadmap overview, Phases 01–08, and the entire 757-line untracked plan.
- Installed readiness skill and readiness, freshness, authority, reporting, and convergence references.
- Relevant executor safety, policy, delivery, and plan-ownership contracts.
- All four specifically identified archived Go-owned/auth-amendment contracts.
- `docs/architecture.md`.

Code inspection covered command startup, registry dispatch and callers, server/flavor/port collectors, scoped broker, authentication constructors, persistence and discarded-save seams, tests, and verification entry points. The three tools/broker test files were read completely. README inspection was limited to its opening architecture/prerequisite sections; the educational baseline to its final curriculum.

### 3. Gate assessment

| Gate | Status | Evidence |
|---|---|---|
| Task approved separately from Git state | PASS | Committed approval headers and `004` provenance |
| Task committed | PASS | Tracking, HEAD blob, clean HEAD/worktree comparison |
| Contract/source freshness | PASS | Current fingerprints match packet; historical verdict not reused |
| Base identified | PASS | Exact branch, HEAD/tree, parent, and complete status |
| Complete document, including ending | PASS | Task §§1–12 and explicit ending inspected |
| Objectives/outcomes | PASS | Task §1 defines observable model-independent manual behavior |
| Scope/exclusions | PASS | Task §§4–5 preserves all four Phase 01 steps and §01.6 |
| Acceptance/verification | PASS | Task §§7, 9, 11; V1–V12; plan mapping and final gate |
| PRD/ADR/security fidelity | PASS | B1–B5 preserved; concrete mechanisms remain timed gates |
| Prior implementation dependencies | PASS | Existing code is explicitly unaccepted; unsafe paths must be disabled |
| No blocking contradiction/missing Level 2 decision | PASS | None substantiated in the inspected candidate |

These assess **contract readiness**, not whether the existing implementation already satisfies the contract.

### 4. Independent traceability and security assessment

| Governing obligation | Current coverage and evidence path |
|---|---|
| FR-001/002/010/023/024/043/046; AC-012/028/029 contributions | One runtime, trusted scope, fixed Go execution and manual independence: task §§4.1–4.2; plan Chunks 2–4, 12–13, 19–21; V1–V3/V12 |
| FR-003; AC-002 contribution | Literal case-sensitive names, meaningful whitespace, original/resolved identity and bounded audited lookup: task §4.3; Chunks 14/19; V4 |
| FR-011/025; AC-004/027 contributions | Explicit required field states and authorized server-derived flavor/port relationships: Chunks 15–17; V5 |
| FR-027/029/039/040; AC-014/015/022 contributions | Eight statuses, safe metadata, minimization before sinks and collection-time bounds: Chunks 3–5, 13–19; V6–V7 |
| FR-014/015/028; AC-007/014/030 contributions | Durable intent before dispatch, outcome before disclosure, shared/restart failure admission, acknowledged uncertainty and separate confirmed recollection: Chunks 6–10/18; V8–V10 |
| FR-048–050; AC-024/031 contributions | Protected versioned store, quota versus actual disk-full, audited bounded cleanup and legacy isolation: Chunks 6–11/20; V10–V11 |
| Relevant NFRs | Authorization, separation, durability, bounded operation, privacy, observability and public-seam verification are retained; release performance/cost claims remain deferred |

#### Existing risks are real—and correctly treated as implementation work

1. **Current dispatch is not the approved boundary.**
   `aiops/internal/tools/registry.go:35–42` directly invokes tools. Agent and workflow callers use it, while diagnostic mains construct clients/stores before their command loops. The plan requires disabling old entry paths first, then implementing authenticated credential-owning enforcement. A facade alone cannot pass V1–V3.

2. **Current identity and projection behavior needs replacement or constrained reuse.**
   `get_server.go` trims input, uses `AllPages`, exposes host/raw fault details, and omits required field states. `get_flavor.go` reads extra specs without verified server linkage. Chunks 14–17 explicitly address these differences.

3. **Existing persistence is insufficient evidence.**
   Store helpers sync files and rename them but do not establish the required directory durability, independent-writer admission, capacity, lifecycle, or recovery guarantees. Discarded saves also exist in deferred engines. The plan does not enable those engines or mistake their presence for accepted behavior.

These are substantiated baseline deficiencies, **not missing preflight specifications**. Their repairs remain LEVEL_0/LEVEL_1 within the approved task and mandatory implementation evidence.

The contract also correctly distinguishes:

- Pre-dispatch rejection: zero implementation/authentication/API calls.
- Post-read scope rejection: withhold unsafe output and honestly record prior contact.
- Recovery acknowledgement: neither authorization nor consent to recollect.
- Uncertain recollection: separate confirmation, current authorization, and a new observation.

### 5. Plan feasibility and status

**No material plan contradiction was substantiated.**

Observed:

- 22 consecutive headings, Chunks 0–21.
- Dependencies point to earlier work.
- Estimates total **15–27.25 days / 90–163.5 hours**.
- Contracts precede callers; persistence precedes audited dispatch.
- Public diagnostics remain unavailable until security/storage/reader/lifecycle controls exist.
- Tests accompany introducing behavior.
- Real OS, independent-process, crash, first-create and bounded-filesystem disk-full evidence are mandatory—not replaceable by mocks.
- Chunk 21 reserves full verification, documentation/demo and complete-diff review without new features.

These are sound planned intermediate states; actual compilability and behavior remain untested.

#### Plan adoption remains separate

The plan is **untracked, uncommitted and not independently accepted**. This review does not approve it.

The installed executor requires use of the accepted controlling ladder. That is an execution-stage adoption requirement. I found **no current governing rule requiring this plan to be committed before task-contract preflight**. The archived task’s stronger plan-commitment rule belongs to a different candidate and is not imported.

Before execution, the owner/coordinator should explicitly select the exact reviewed plan as controlling. Its untracked status does not invalidate the committed-task gate.

### 6. Remaining timed gates

Task §3 and ADR §6 govern—not the older roadmap’s historical wording.

| Gate | Required timing and closure |
|---|---|
| **G1** | Document and separately review/approve the concrete non-root OS/IPC realization before affected execution. Actual unauthorized-local-caller proof must precede manual enablement. Plan Chunks 1/12/19 preserve this. |
| **G2** | Trusted configured scope/endpoints, protected setup and finite usable storage limit before startup/use. Synthetic offline fixtures do not require actual deployment values. Live probes require their own explicit scope and cleanup owner. |
| **G3** | Review exact reader APIs, relationships and transport/destination controls before collector enablement. Actual cloud reader/mutation-denial proof remains separately authorized live acceptance. |
| **G4** | Separately review/approve concrete versioning, durability, arbitration, capacity, cleanup and recovery before persistent execution. Actual fault/crash/filesystem results precede acceptance. |
| **G5/G6** | Remain later release/MCP gates; not approved here. |

Compliant package/schema organization, finite limits, test seams, local transport and persistence choices remain **LEVEL_1** within these constraints. Routine verification and repair are **LEVEL_0**.

No present LEVEL_2 change is requested. If a realization requires weaker safety, new material risk, privilege, infrastructure or expanded scope, dependent work must stop for that precise decision.

### 7. Findings, evidence timing and limitations

**Material preflight blockers:** None substantiated.

**Required contract/plan repairs:** None identified.

**Prior finding closure:** Not applicable; initial-depth review, no fabricated remediation history.

**Non-convergence:** Not applicable.

| Evidence maturity | Assessment |
|---|---|
| `AVAILABLE_NOW` | Approval records, commitment, current sources, code seams and complete plan inspected |
| `REQUIRED_BEFORE_THIS_GATE` | No indispensable unresolved source/authority gap identified |
| `FUTURE_IMPLEMENTATION` | Baseline checks, actual compilation/tests, G1–G4 realization evidence, OS/process/crash/disk/package verification |
| `OPTIONAL_ADVISORY` | Additional fuzz/soak coverage must not replace mandatory evidence |

Go `1.27.1` is declared, but installed toolchain/cache and safe fixture facilities remain **unverified**, not proven unavailable. Chunk 0 must establish them before relying on them.

No product tests, builds, vet/race checks, formatters, services, downloads, credentials/`.env`, protected records, cloud/host/model/MCP calls, provisioning or deployment were performed. No repository file was changed.

The four historical contracts were used only for compatibility comparison. Their identities, paths, authentication source, HTTP exceptions, catalog, seven-status envelope and approvals were not inherited.

### 8. May work proceed?

**Yes—a separately authorized executor may proceed at this reviewed base**, after explicitly adopting the controlling plan and selecting the bounded execution mode/chunk.

The safe next work is **Chunk 0 only**: source/base revalidation and guarded offline baseline/facility discovery. Subsequent work remains constrained by the G1–G4 timing above. No model analysis, investigation/resume, MCP, broad catalog, host/operator enablement, migration or unrelated lab work is authorized.

This report supplies neither execution authorization nor plan/concrete-mechanism approval, implementation acceptance, or deployment permission. Material changes to the task, ADR, PRD, plan, approval evidence or relied-on implementation require affected revalidation.

The authorized response-only preflight is complete; I am stopping here.

PREFLIGHT_PASS

---

**End of recorded preflight report.**
