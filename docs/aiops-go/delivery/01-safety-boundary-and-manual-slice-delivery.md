# Delivery 1 — Safety Boundary and Manual Slice

## 1. Plan identity and objective

- **Planning status: PLAN_READY — planner self-assessment for the complete Delivery 1 ladder.** The user's explicit AM1–AM5 approval resolves the amendment-content approval blocker. Remaining source incorporation/commit and specification-preflight requirements are hard implementation gates, not a claim that this plan is incomplete or permission to execute it.
- **Scope:** Go Delivery Phase 01 only: source phase Steps 1–3 and §01.6 definition of done, bounded by the companion task. Revised-runtime phase numbers are a different roadmap.
- **Objective:** useful, model-independent named diagnostics through one deny-by-default, scoped, bounded, sanitized and durably audited execution boundary.
- **Project mode:** existing project with partial implementation; observed source behavior is not verified acceptance.
- **Initial planning base:** `10c4784754a0189535af7c310959a83d51d7a7c0`, branch `aiops-go-phase01`. The original planning tree was clean and the destination directory existed and was empty.
- **Readiness-update candidate:** same HEAD; only this pre-existing untracked plan was present before the status update. PRD/ADR/task blobs still match §2. This update changes only the plan, preserves all unchecked execution work, and neither commits nor amends governing sources.
- **Historical requirements/code baseline:** `0182da9f7c2b322df5da49262748974009db7332`. The delta from that revision to planning HEAD contains only the ADR/task pair, not implementation changes. Future execution must record its actual base independently.
- **Controlling ladder:** this document, `docs/aiops-go/delivery/01-safety-boundary-and-manual-slice-delivery.md`. Earlier phase plans are roadmap inputs; revised ADS ladders are candidate design, not additional executable ladders.
- **Execution authorization:** not granted. User requested planning only. **Execution mode: UNSELECTED.** All tasks remain unchecked.
- **Approval/preflight:** the user explicitly approved AM1–AM5 in this conversation: `I explicitly approve AM1–AM5`. This applies to task §6.6 at blob `04991e450d6659eeffc69f660749fb8b27700d65`. It is not blanket approval of the whole ADR/task, incorporation into governing contracts, independent plan acceptance, `PREFLIGHT_PASS` or execution authorization. No formal preflight or independent review was initiated.

Smallest useful outcome:

```text
application-owned scope + server_basic_info
  -> current definition/context/target/profile/limit validation
  -> durable intent -> fixed bounded read -> sanitize
  -> durable terminal event -> one safe versioned result
```

### Approval record and remaining implementation gates

After the initial plan was written, the user explicitly approved **AM1–AM5 as written in task §6.6 at the content identity above**. Their human-approval gate is resolved; do not request the same approval again unless material amendment content changes. This records the actual conversational approval, not a manufactured timestamp, signed attestation or claim of prior independent review.

The named ADR and task still contain **DRAFT / not execution-ready** headers and explicit source-incorporation gates. This planning-only update does not amend their status or the governing contracts. Their recorded Q1–Q3 choices remain the Phase 01 baseline, conditional revised-runner ownership and **full** Phase 01 through versioned amendments; the older provenance limitation remains distinct from the new, explicit AM1–AM5 approval. Whole-document approval/review and committed governing-source readiness must still be established before implementation.

**Required before implementation:** preserve this approval with its exact amendment-content identity; satisfy the remaining ADR/task review, bounded approval/provenance and commitment requirements; incorporate/commit AM1–AM5 into affected governing contracts; then pass execution-time specification preflight against the actual sources/base under a separate execution instruction. Chunk 0 checks these prerequisites and stops with `BLOCKED` if they are unmet; it does not silently amend sources. No unresolved AM1–AM5 content decision prevents planning readiness. `PLAN_READY` means the ladder is ready for separately authorized Chunk 0 discovery, not that implementation is authorized or those prerequisites have passed. Missing live evidence is a separate live-use gate, not a reason to omit otherwise authorized offline work.

## 2. Sources and authority

Paths in this section are relative to this plan. Git blob IDs identify inspected content, not approval.

| ID | Source | Identity / inspected sections | Authority and observation |
| --- | --- | --- | --- |
| S1 | [Repository instructions](../../../.agents/AGENTS.md) | Entire document; symlink to `$HOME/.agents/AGENTS.md`; session also supplies `$HOME/.pi/agent/AGENTS.md` | Applicable scope, authority, verification and review rules. No root `AGENTS.md` exists at planning HEAD. |
| S2 | [Go PRD](../prd.md) | Entire document through Further Notes; blob `18add68f88a07ace80979f86b2009d2435524743` | Product truth. Header remains draft; Q1 records only bounded Phase 01 approval at the historical baseline. Later product requirements are not authorized by this plan. |
| S3 | [Safety ADR](../architecture/01-safety-boundary-and-manual-slice-adr.md) | Entire document, especially §§1–7 / F01–F12; blob `ff53a9fe28359592494e637a7f8e16186b8bddb0` | Requested architectural boundary; source still marked draft. AM1–AM5 now have explicit conversational approval, but whole-document/source-incorporation gates remain. Do not substitute a Go-owned boundary for Q2. |
| S4 | [Bounded task](../tasks/01-safety-boundary-and-manual-slice-task.md) | Entire document through its ending; §§2–11, AM1–AM5, V1–V11; blob `04991e450d6659eeffc69f660749fb8b27700d65` | Full Delivery 1 task contract candidate, tracked/committed at HEAD but still marked not execution-ready. User explicitly approved its AM1–AM5 clauses after initial planning; incorporation/commit and remaining whole-task gates are not inferred from that approval. |
| S5 | [Source Phase 01](../implementation-plan/01-safety-boundary-and-manual-slice.md), [overview](../implementation-plan/00-implementation-overview.md) | Both read in full; phase blob `0b02155576fdeec1d899ed9cc59142e2bce01d9b` | Requirements decomposition, Steps 1–3, constraints, exclusions and later ownership; roadmap estimates are not implementation evidence. |
| S6 | [Placement](../../ai-ops-revised/runtime/runtime-placement-contract.md), [foundation](../../ai-ops-revised/runtime/foundation-operations-contract.md), [identity](../../ai-ops-revised/runtime/identity-policy-operations-contract.md), [reuse manifest](../../ai-ops-revised/runtime/selective-reuse-manifest.md) | Read in full | Binding revised placement, identity, permissions, provenance, dependency-closure and non-activation restrictions. Historical acceptance does not establish current readiness. |
| S7 | [Toolbox](../../ai-ops-revised/runtime/manual-diagnostic-toolbox-operations-contract.md), [runner Steps 1–4](../../ai-ops-revised/runtime/tool-runner-safety-gateway-steps-01-to-04-operations-contract.md), [runner Steps 5–7](../../ai-ops-revised/runtime/tool-runner-safety-gateway-steps-05-to-07-operations-contract.md) | Read in full | Retained closed contracts until approved replacements; AM1–AM5 cannot silently extend them. |
| S8 | Existing Go, revised runner/toolbox, tests, role defaults, Makefiles and static checker | Concrete evidence in §4 | Current-state evidence only; neither safety acceptance nor deployment authorization. |

The ADR/task were last changed in planning HEAD. Their references to an earlier correction worktree are historical, not the current tree. Sources were accessible. Inspection did not read `.env`, protected inventories, generated cloud configuration, profiles, raw audit/log/evidence or credentials. Educational baseline, topology studies, historical ADSs, later host/MCP contracts and all transitive consumers were not exhaustively re-reviewed for this plan; Chunk 0 must inspect relevant lineage/consumer contracts before touching shared behavior. They confer no new capabilities here.

Executor compatibility was checked against the installed `chunked-implementation` entrypoint, core safety, execution policy and delivery contract. Observed entrypoint blob: `edff2d0e902703914977e0085528f77ecfd7dce8`; delivery-contract blob: `57cd6daa2765fbc6342f2336a4720c8e7c11a72a`; execution-policy blob: `3c55c7d56a2892292cb73d3579b8b862c0011682`. Compatibility with their documented interface is checked; fresh-session orchestration capability was not established and is not needed to write this plan.

## 3. Scope, invariants and exclusions

### Included once implementation gates pass

1. Entry-point/capability/consumer gap matrix, one maintained definition source and the revised runner as policy/registry/dispatch owner, conditional on actual-boundary scope/parity proof.
2. Application-owned cloud/project/canonical targets, capability/profile, policy/approval identity where applicable, client classification and finite budgets. Public tool arguments cannot establish authority.
3. Exactly the Delivery 1 enabled set: `server_basic_info`, `server_network_info`, `project_resource_summary`, including the approved versioned fault/flavor extension. Summary authority is distinct from a single-server assignment.
4. Closed input/definition validation, bounded exact-name/UUID resolution, authorized derived relationships, fixed argv/minimal environment or equivalently narrow SDK reads, pre-sink minimization/redaction, cancellation/cleanup.
5. Full versioned result/audit behavior, durable intent before dispatch and terminal durability before success; shared/restart-safe fail closure, truthful uncertainty and no automatic replay.
6. Go manual catalog/invoke integration without inference; unsafe existing SDK/automatic entry points routed through the same owner or disabled before authentication. Preserve planning/identity regressions.
7. Applicable offline tests, three scenario seeds, explicit compatibility/rollback and manual/extension/revocation/deployment-preflight guidance.

### Fixed guardrails

- Preserve `assistant02`, group `ai_ops_assistant`, runtime user/group `aiops_assistant`, root `/opt/openstack-ai-ops-assistant`, separate from `assistant01`. No historical runner/registry copying, installation, import or execution.
- Fresh `aiops-assistant-project-reader`, project label `admin`, domain `default`, role `reader` only; one-month expiry; OpenStack admin-team rotation/revocation. The project label does not grant admin privileges. No ambient credential, operator or SSH fallback.
- Executables/configuration remain trusted/root-owned and caller-unwritable. Profile directory `0700`, regular non-symlink profile files `0600`, owner/group `aiops_assistant`; no profile-content inspection by this work.
- Direct script identifiers: nonempty ASCII `[A-Za-z0-9._:-]+`, maximum 255 bytes, no slash or `..`. Do not case-fold exact names, impose name uniqueness or widen script validation. Preserve original/resolved identity and UUID guidance.
- Retain selected field projections. AM2 permits only bounded fault code/safe message and observation-derived flavor detail; no raw fault details, extra specs, user-data or opaque configuration objects. List sections cap at 50, complete diagnostic at 1 MiB; tighter tool ceilings continue to apply.
- Audit stays under the fixed revised audit root: `tool-runner.jsonl`, `.tool-runner.lock`, archives `.1`–`.3`; directory `0700`, files `0600`; exclusive `flock`, flush/fsync, 16 KiB event maximum, 1 MiB rotation. No fallback sink, unsafe-path auto-repair, compression, age deletion or eviction of unresolved intent to keep execution available.
- Denial/invalid/control failure is not transient. At most one execution per request; terminal audit failure suppresses diagnostic payload/raw details, preserves intent/committed events, exposes uncertainty locally and blocks new admission across callers/restart. No ACID or exactly-once external-read claim.
- Legacy `1.0` remains closed: six statuses/exits `0`–`5`, interruption `error`/`interrupted`, one terminal attempt. The explicitly approved AM3/AM4 representations define separate `2.0` result/audit and cancellation exit `6`; their governing-contract incorporation/commit must precede implementation. Approval does not silently extend `1.0`.

### Excluded / deferred

No infrastructure mutation, remediation, generic shell/SSH/sudo/OpenStack CLI/file/database tools, caller executable paths, admin/root/service/database/RabbitMQ credentials, new infrastructure/dependencies or historical activation. Fixed application-owned diagnostic invocations are not generic execution tools.

No model/provider/disclosure integration, agent loops, planning changes, project scheduling, specialist activation, full reports/evidence review, investigation-state schemas/checkpoints/resume, memory/RAG/export/retention platform, domain metadata/volume-attachment workflows, host/operator diagnostics, MCP adapters, full evaluation/telemetry platform, web/API/service, vector/distributed infrastructure or curriculum artifacts. Existing later seven-tool definitions and independently governed host/MCP behavior are preserved, not deleted or enabled by Delivery 1.

No installation, provisioning, cloud/provider/host calls, live audit inspection, mutation-denial probes, Ansible host contact/check mode/apply, Molecule runs, credential modification, staging, commit, push, merge or deployment. Live use remains disabled until Phase 07 or a separately authorized equivalent gate. Documentation describes operator-owned disposable denial procedures; it never registers them as diagnostics.

## 4. Repository observations and remaining work

Aliases below denote **observed** paths unless marked proposed; they are shorthand, not new modules:

| Alias | Path |
| --- | --- |
| R | `ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/aiops_tool_runner.py` |
| G | Same directory, `tool_registry.json` |
| I | Same directory, `audit_inspector.py` |
| T | `ansible/ai_ops_assistant/tests/tool_runner/` |
| D | `ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved/` |
| DT | `ansible/ai_ops_assistant/tests/diagnostic_toolbox/test_diagnostic_toolbox.sh` |
| RD / RT | `ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/defaults/main.yml` / `tasks/main.yml` |
| SDK-P | **Proposed** fixed revised-owner collector module alongside R, `scoped_project_reader.py`; not a public arbitrary SDK/query tool |
| GO-P | **Proposed** `aiops/internal/diagnostics/runner.go` and `runner_test.go`; a client adapter, not policy owner |
| CLI-P | **Proposed** `aiops/cmd/openstack-diagnostic/main.go` and `main_test.go` |
| GUIDE-P | **Proposed** `docs/aiops-go/manual-diagnostics.md`, including final gap/consumer matrix and operator guidance |

All new paths/symbol responsibilities require execution-time confirmation. Internal SDK/helper organization is Level 1 only within approved AM1; any new fixed runtime artifact/control file needs its exact approved manifest/allowlist before use.

| Observed source / symbols | Existing behavior | Missing work / preservation obligation |
| --- | --- | --- |
| `aiops/internal/tools/registry.go`: `NewRegistry`, `Registry.Execute` | Rejects empty/duplicate/unknown names; raw dispatch interface | No general scope/profile/audit admission. Do not use it as an independent permissive owner. |
| `get_server.go`: `resolveServer`, `ServerObservation` | UUID/exact-name path, missing/ambiguous rejection; `AllPages` name query; includes host/raw fault details | Preserve identity tests; bound resolution/response/memory, scope checks and safe projection before enabled use. |
| `get_flavor.go`: `GetFlavorTool.Execute` | Caller flavor ID, extra-spec lookup and raw error text | Not the AM2 relationship contract; do not expose it via manual CLI. Disable standalone production use or place only narrow derived reads under owner. |
| `get_ports.go`: `GetPortsTool.Execute` | Device/project filtering, 32-record/four-page checks, response mismatch rejection | Useful fixture/algorithm seam, not complete cloud/profile/audit authorization; do not relax its tighter bound silently. |
| `internal/openstackclient/compute.go`, `network.go`; three diagnostic `cmd/*/main.go` files | Ambient `AuthOptionsFromEnv`, clients/registry constructed directly; model setup precedes execution | Quarantine diagnostic paths before SDK authentication; do not enable automatic investigation in this delivery. `openstack-ai` is model chat, not a manual diagnostic command. |
| `internal/planning/prepared.go`, planning/review tests | Digest-bound immutable preview, copied dependencies, mutex single-start; original goal/name regressions | Regression-only; preserve zero start for non-ready/declined/stale/cancelled cases. |
| `internal/workflow/review_snapshot.go` | Existing specialist selector/dispatcher seam | Must not be reached by manual path. New investigation/specialist gating integration belongs to Phase 02. |
| R: `load_registry`, `validate_request`, `build_child_environment`, `execute_fixed_diagnostic` | Closed definition/parameter checks, fixed targets, fresh environment, subprocess fixtures | No general trusted application scope. Full registry has seven tools; derive exactly permitted enabled view without deleting later entries. |
| R: `capture_bounded`, `terminate_process_group` | Concurrent bounded stream capture, timeout/interruption path | Early return when direct child exited can leave descendants/pipes; add parent-exit-survivor and cancellation-race regressions. This is inspection-based risk, not a reproduced test failure. |
| R: `build_result_envelope`, `emit_result_outcome`, `main` | Sanitization, closed `1.0` result, terminal audit before output | Dispatch precedes audit; no durable intent/shared fault latch. No-child `exit_code` uses status exit rather than documented null: reconcile contract/tests, do not bless divergence. |
| R: `append_audit_event`, `_rotate_locked`; `test_audit_persistence.py` | `flock`, restricted file metadata, flush/fsync, rotation; concurrency test uses threads | Extend real-process admission/crash/restart/rotation evidence. Existing suite does not establish restart-safe stop-new-dispatch. |
| D helper and three scripts | Fixed CLI/jq, identifier rules, projected sections/partial/empty outcomes | Command substitutions buffer raw collection before output slicing. Enforce collection-time API/bytes/memory bounds, not only final output. Preserve script-contract versions and fixed paths. |
| RD | Runner defaults disabled; explicit files/targets/audit metadata | Preserve disabled defaults. Any approved additional collector/control artifact must be reflected in exact static deployment allowlists, without deployment. |
| `aiops/Makefile`, `go.mod`; root `Makefile` | Go test/build targets; `go 1.27.1`; root includes `.env` and lab Molecule targets | Verify local toolchain first, no automatic download/install. Use Go subdirectory targets, not root Makefile. |

**Actually performed during planning:** read-only path/symbol/test discovery, full named-source reads including endings, relevant source/test reads, Git status/log/diff/blob inspection; selective-reuse historical tree resolves to `3abc4bcf3fa4caf1c6d89f8d25865e2c0aef8e07` at its pin and HEAD. Per-path closure and all consumers still need discovery. No project tests, builds, formatter, runtime, Python executable or cloud/model operation ran. No pre-existing test failure or passing baseline is asserted. Cached files are not evidence.

## 5. Requirement-to-chunk coverage

D1 labels are **plan-local tracking IDs**, not PRD identifiers. Source task §8 owns the exact current/deferred splits. Every implementation/preservation column is conditional on the remaining implementation gates and is reverified in final Chunk 16.

| ID | Source / required Delivery 1 behavior | Current state | Implementation / preservation | Verification and intended evidence |
| --- | --- | --- | --- | --- |
| D1-01 | S5 Step 1; S3 F01/F12; S4 §2/AM5: provenance, caller/consumer matrix, single revised owner, no historical activation | Partial inventory; gate unresolved | 0, 1, 2, 13, 15 | V1/V2/V11; exact lineage/version/entry-route matrix, no alternate enabled route |
| D1-02 | FR-002, FR-010; S4 AM1: immutable application-owned cloud/project/targets/capabilities/profile/policy/budgets, actual dispatch checks | General context absent | 2, 5, 6, 11 | V2/V3; changed/forged/missing context or stale definition gives zero forbidden read/spawn, terminal attempt |
| D1-03 | FR-003; AC-002 local subset: canonical UUID/exact names, original/resolved identity, ambiguity/missing rejection, narrow-script guidance | Go behavior partial, unbounded name pages | 8, 11, 12 | V4; API counters show no unintended target; exact casing/substrings/unsupported script names tested |
| D1-04 | FR-011, FR-025 local subset; AM2: server basics/fault/flavor only from authorized observation | Raw/overbroad Go fields; script lacks extension | 8 | V4/V9/V10; no fault details/extra specs, absent fault null, missing flavor partial, forged flavor zero lookup |
| D1-05 | FR-011, FR-025 local subset: server→ports→network/subnet rules, identity/scope validation | Script relationships and bounded Go port seam | 9 | V4/V5; allowed shared visibility explicitly checked; no unrelated discovery or forged derived lookup |
| D1-06 | FR-011, FR-025 local subset: separately authorized project summary, seven fixed sections, no attachment traversal | Script exists; collection buffers unbounded | 10 | V4/V5/V10; server-only context cannot list project; empty/partial/fatal auth outcomes and section bounds |
| D1-07 | FR-023; FR-041 local subset; S5 Step 1: closed versioned definitions, startup corruption denial, exact subset and availability | Closed older seven-tool registry only | 2, 6, 13 | V1; duplicate JSON keys/names/positions, bool-as-int, unknown fields/versions, defaults/limits, invalid subset fail closed |
| D1-08 | FR-021–FR-022 design/local subset; NFR-002/NFR-012: fixed observer/profile isolation and no privilege fallback | Constants/role metadata, not current deployment proof | 1, 6, 8, 13, 15 | V3; ambient admin/token/proxy/SSH/provider canaries absent, unsafe/missing profile fails safely; static metadata only |
| D1-09 | FR-024; AC-012 local subset: fixed argv/cwd/env/targets, narrow SDK parity or disable, direct invocation cannot bypass | Multiple Go/runner paths | 1, 6, 7, 8–13 | V2/V3/V5; highest-seam markers/counters, no credential authentication on disabled route, test-only overrides inaccessible publicly |
| D1-10 | FR-008/FR-009/FR-040 local subset; NFR-003: finite pages/records/memory/time/retries/concurrency/streams; no denial retry | Partial bounds only | 5, 7–10, 11 | V5/V8; floods/oversize pages/endless pagination stop within ceilings; shared admission finite |
| D1-11 | FR-027; FR-039 local subset; AC-014: every target status, safe payload/error/identity, correlation/time/duration, separate child/process exit and redacted/truncated flags | Six-status contract, no target/redacted fields | 3, 7, 11–13 | V6; closed approved-version matrices, all seven outcomes, strict UTF-8, one complete line, no added `1.0` fields |
| D1-12 | FR-028; NFR-004 audit subset; AM4: durable intent before dispatch, terminal before success, every request terminal attempt | Terminal-only audit exists | 3, 4, 6 | V7; ordered trace and filesystem faults show zero dispatch on failed intent, zero success publication on failed terminal |
| D1-13 | FR-028; NFR-003/NFR-004/NFR-006 local subset: shared/restart-safe fault stop, crash uncertainty, no replay, safe recovery | Not established | 4, 5, 6, 14 | V7/V8; independent processes/crash windows/restart/corrupt control state, no later dispatch or duplicate terminal |
| D1-14 | S3 F08/F10; S4 §6.3/AM4: audit identity/cardinality/minimum disclosure/permissions/locks/rotation/integrity | Foundation present; versioned extension missing | 3–5, 13 | V6/V7/V8; request timestamp/correlation, event UUIDs, fixed actor, no identifiers/payload, complete lines, bounded archives, unresolved intents protected |
| D1-15 | FR-018/FR-029; NFR-001/NFR-005/NFR-008/NFR-012 local subset: untrusted input/output, minimization/redaction before every enabled sink | Sanitizer exists, raw Go outputs bypass it | 1, 3, 6–12, 14 | V9; nested/text/stderr/error/cross-chunk/multibyte canaries absent from all enabled sinks, unsafe values withheld |
| D1-16 | FR-030; AC-015; PRD non-goals: permanent mutation/generic-command denial, including insistence | Allowlist foundations | 2, 6, 12, 14 | V2/V9; fix/restart/edit/create/delete/override cases have zero mutation or arbitrary dispatch |
| D1-17 | FR-001/FR-017/FR-031–FR-034 local independence subset; AC-018 subset: manual list/invoke without provider/knowledge/model initialization | No standalone Go manual CLI | 11, 12, 14 | V10; actual CLI fixture with inference/client-init traps, absent knowledge/provider/host/MCP; useful safe output |
| D1-18 | FR-019/NFR-007/NFR-013 local output subset: empty not unavailable/error; collection success not diagnosis proof | Existing inner sections, incomplete outer parity | 3, 8–12, 14 | V6/V10; denial never healthy, partial gaps retained, no invented root cause |
| D1-19 | FR-037 seed subset; NFR-011/NFR-015; S5 Step 3: healthy/permission-denied/hostile versioned expected/actual seeds | Existing fixtures, no selected scenario seed verified | 14 | V9/V10; expected calls/targets/status/evidence/safety assertions, credentials absent; not a full evaluation platform |
| D1-20 | NFR-010; AC-024 local subset; AM5: preserve manual/planning/data contracts, explicit versions/consumers/rollback | Reuse seams and frozen contracts | 1, 3, 11, 13, 15 | V6/V11; mixed versions, incompatible consumers rejected, no audit flattening, no in-place conversion or unsafe rollback fallback |
| D1-21 | FR-041–FR-042 local guidance subset; NFR-014 design/offline subset; S5 Step 3: manual/extension/revocation/preflight and operator-owned read/denial procedures | Multiple historical docs, not Delivery 1 guide | 13, 15 | V11; reviewed reproducible fixture instructions, admin cleanup owner, disabled-live prerequisite matrix, full diff scope audit |
| D1-22 | S5 §01.6: all enabled local paths safe, complete required offline verification, unchanged source/security boundaries | Unverified | 0, 16 | V1–V11; all mandatory commands executed/discovered, complete candidate diff, no future modules or secrets |

### Explicit partial-acceptance and deferral accounting

- **FR-001–FR-003:** manual call/scope/identity only now. **FR-004–FR-007:** preserve existing plan/graph/review behavior; new integration deferred to Phases 02/04. **FR-008–FR-011:** call-boundary limits/authority/relationships now; nested/delegated integration Phase 02, resumed calls Phase 03.
- **FR-012–FR-013:** domain workflows and multi-server synthesis Phase 04. **FR-014–FR-017:** investigation checkpoints/resume/context/memory/retrieval Phase 03; audit/control state here is not an investigation schema. **FR-018–FR-020:** local untrusted-output/truthful limitations now; model reports/review and knowledge handling Phases 02–04/06.
- **FR-021–FR-025:** local/design subset now, actual reader policy/isolation Phase 07, attachments Phase 04, higher visibility Phase 05. **FR-026:** host diagnostics Phase 05. **FR-027–FR-030:** full applicable local outcome/audit/privacy/mutation obligations now.
- **FR-031–FR-034:** no model launch and manual independence now; model contracts/disclosure/isolation/outage/state/report behavior Phases 02/03/07. **FR-035–FR-036:** MCP Phase 05, specialist integration gate Phase 02 and optional evaluation Phase 06; neither enabled here. **FR-037–FR-040:** scenario seeds/tool provenance/call limits now, full evaluations/usage/run budgets Phases 02/03/06. **FR-041–FR-042:** local required-control readiness and owner guidance now; operational consolidation/lifecycle Phase 06/07.
- **NFR-001–NFR-003:** mandatory local safety/design/bounds now; deployed proof later. **NFR-004–NFR-008:** audit concurrency, call/evidence isolation, honest local limits and provenance now; checkpoint/memory and full semantic/pipeline guarantees Phases 03/04/06. **NFR-009:** measured release thresholds Phase 06. **NFR-010–NFR-015:** applicable local compatibility/extension/privacy/UX/offline-test/design obligations now; complete data/egress/deployment/release evidence remains with later phases as S4 §8.2 specifies.
- **AC-002–AC-004, AC-012, AC-014–AC-015, AC-018, AC-021–AC-024:** claim only the exact local subsets in the matrix and S4 §8.3. **AC-001** is preservation only, not new acceptance. **AC-005** contributes a seed, not domain findings acceptance. **AC-006–AC-010, AC-013, AC-016–AC-017, AC-019–AC-020, AC-025** are deferred; zero specialist/model dispatch here is a prerequisite, not their full pass. **AC-011** is design/prerequisite guidance only; fixture success never proves deployed reader policy.

## 6. Verification catalog and environment

**All execution checks in this section are PLANNED_NOT_RUN.** Read-only planning inspections in §4 are the only current execution evidence. Commands are documentation, not authorization. Working directory is repository root unless stated otherwise.

| Check | Command/procedure and provenance | Prerequisites | Required evidence |
| --- | --- | --- | --- |
| B0 | `rtk git status --short`, `rtk git diff --cached`, `rtk git diff`, `rtk git rev-parse HEAD`; source/blob/lineage comparisons | Read-only Git access, no protected file reads | Actual base/candidate/pre-existing work and source freshness |
| G0 | From `aiops/`: `GOTOOLCHAIN=local rtk go version`, then `rtk go test ./internal/tools ./internal/scopedtools ./internal/planning ./internal/workflow` | Compatible Go for `go 1.27.1`, existing local dependencies; no implicit toolchain download/install | Baseline test discovery/failures; no cloud/provider calls |
| G1 | From `aiops/`: `rtk go test ./...` and `rtk make build` (observed Makefile/task commands) | Same as G0; reviewed fake-only test paths | Full Go package result and four existing binaries build; new CLI built explicitly until Makefile includes it |
| G2 | From `aiops/`: `rtk go test -race ./internal/tools ./internal/scopedtools ./internal/planning`; after GO-P exists also `rtk go test -race ./internal/diagnostics ./cmd/openstack-diagnostic` | Supported race toolchain/compiler; actual affected concurrency packages confirmed | Race checks on changed Go boundary, not a substitute for multiprocess audit tests |
| P0 | `rtk "$VENV_PYTHON" -m unittest discover -s ansible/ai_ops_assistant/tests/tool_runner -p 'test_*.py'` (task-required existing suite) | User-confirmed activated venv; `VENV_PYTHON` its executable; fixture-only imports reviewed; Linux process/lock facilities | Complete applicable revised suite, counts/skips; no historical runtime import or host/cloud access |
| PF | Same discovery command with a named `test_*.py` file pattern from the chunk | P0; proposed files must first exist/discover | Focused behavior assertions V1–V11, not zero-test success |
| P1 | `rtk "$VENV_PYTHON" -m py_compile <changed-python-files>`; `rtk "$VENV_PYTHON" -m ruff format <changed-python-files>`; `rtk "$VENV_PYTHON" -m ruff check --ignore EXE001 <changed-python-files>` | Confirmed venv and existing tools; actual paths substituted | Syntax/import/format/lint checks; inspect format diff, no new dependencies installed |
| J0 | `rtk "$VENV_PYTHON" -m json.tool <changed-registry>` plus version-specific closed-schema/duplicate-key tests | Confirmed venv; reviewed definitions | Syntax alone insufficient; schema corruption fails closed |
| S0 | `rtk bash scripts/check_ai_ops_revised_diagnostic_toolbox_safety.sh` and `rtk bash ansible/ai_ops_assistant/tests/diagnostic_toolbox/test_diagnostic_toolbox.sh` (observed scripts) | Bash, existing fixture dependencies including `/usr/bin/jq`; preserve fixed production jq path/version | Full applicable manual/static regression. Test jq override is not production permission |
| S1 | `rtk bash -n <changed-shell-files>`; existing shell formatter/lint if available/configured | Confirm existing repository tool, do not introduce/install one | Syntax/safety/format review of exact changed files |
| Y0 | If role/default/manifest files change: YAML parsing, existing offline lint and syntax checks with synthetic inventory, no secret vars | Approved existing environment; inspect playbook/includes first, confirm no protected inventory/plugin/cloud evaluation; concrete safe command fixed in Chunk 0 | Exact file/target/permission/default assertions and syntax; no host contact. No root Molecule target |
| F0 | `rtk git diff --check`, `rtk git diff --cached --check`; full base-to-candidate tracked diff plus staged/unstaged and complete relevant untracked contents | Recorded implementation base and pre-existing-work inventory | Full scope/security audit; untracked additions cannot be omitted by plain diff |

PF proposed test files: `test_scoped_admission.py` (Chunks 2/6), `test_versioned_outcomes.py` (3), `test_intent_publication.py` (4), `test_shared_admission.py` (5), `test_scoped_project_reader.py` (8–10), `test_version_compatibility.py` (13), `test_manual_scenarios.py` (14), all under T. Existing focused files include `test_request_gateway.py`, `test_execution_gateway.py`, `test_profile_isolation.py`, `test_process_bounds.py`, `test_result_redaction.py`, `test_result_envelope.py`, `test_audit_events.py`, `test_audit_persistence.py`. Add tests alongside each behavior, not only in Chunk 14.

**Mandatory future V1–V11 coverage:** V1 definitions→2/6/13; V2 all-entry authorization→1/6/11/12/14; V3 credential/profile→1/6/8/13; V4 identity/relationships→8–10/12; V5 process/collection→7–11; V6 outcomes→3/7/11–13; V7 publication/durability→3/4/6; V8 real-process/shared/crash→5/6/14; V9 all enabled sinks/injection→3/8–12/14; V10 CLI/scenarios→12/14; V11 compatibility/regressions/guidance→1/13/15/16. S4 §9 scenario details remain mandatory, including disk-full/permission/write/flush/fsync/lock/rotation faults, parent-exit descendants, policy/definition races, minimum audit disclosure, mixed-version inspection and rollback.

Mandatory checks are not waived by missing tooling, skipped tests or a passing build. Check discovery/counts and investigate unexpected skips. Real Linux filesystem/process tests are mandatory for admission/durability; mock fsync errors complement rather than replace them. Recommended extras only: additional repeated stress seeds and coverage reporting with existing tools; these are not substitutes for mandatory cases. Live/model/Molecule campaigns are neither mandatory nor authorized for this offline delivery.

## 7. Decisions and effort

### Established constraints versus implementation discretion

| Item | Category | Choice / validation |
| --- | --- | --- |
| Q1–Q3 / AM1–AM5 | Recorded direction plus explicit current amendment approval | Preserve full scope and selected revised owner. User explicitly approved AM1–AM5 at the task blob in §1; preserve that evidence without reopening it. Complete governing incorporation/commit and remaining ADR/task gates before implementation. No reduced six-status completion. |
| Unsafe Go CLI paths | Proposed Level 1 safety implementation | Disable diagnostic dispatch before AI/SDK setup instead of implementing Phase 02. Preserve pure planning tests/local data; any non-diagnostic command affected needs a narrow gate, not deletion. |
| SDK integration | Proposed Level 1 mechanism under AM1 | Prefer a fixed bounded collector within revised-owner lifecycle, reusing installed approved SDK capabilities; SDK-P is a candidate, not a dependency addition. Existing broad Go SDK tools stay unreachable to enabled clients. Prove SDK/script parity; a different compliant language/layout is allowed without changing ownership. |
| Trusted context transport | Level 1, feasibility obligation | Select protected application-to-owner context intersected with current trusted policy; no public JSON/env assertion becomes authority. Prove direct-invocation negatives before enabling collectors. If impossible within approved placement/privileges, escalate; do not invent a signed service or new infrastructure. |
| Concurrency | Level 1 | Sequential admission/serialization or bounded conflict rejection is sufficient. Shared lock/control health must work across processes/restart; no parallel scheduler required. |
| Versions, data and rollback | Approved-contract constraint after amendment | Explicit consumer selection, unchanged historical data/audit, no automatic state migration/event flattening; disable new path without restoring weaker bypass. |
| CLI spelling and helper files | Level 1 proposal | CLI-P/GO-P and list/invoke shape are proposed. Go merely presents owner-derived catalog/results; no duplicate definitions, credentials or user-selectable executables. |

One experienced engineer; **1 engineer-day ≈ 6 focused hours**; no approval/access waits included. Estimates include tests, formatting, documentation and verification once per chunk. Ranges are conditional on feasible revised-owner transport and available local toolchains. This is a fresh full-amendment estimate, not the earlier roadmap's 6–10 days: durable shared/restart admission, collection-time bounds and compatibility proof materially increase observed work. Re-estimate in Chunk 0 without reducing requirements.

| Chunk | Goal | Depends on accepted chunks | Hours | State |
| --- | --- | --- | --- | --- |
| 0 | Discovery, source gate and baseline | Separate discovery authorization | 3–6 | Not started |
| 1 | Quarantine unsafe Go diagnostic entry points | 0 and specification gates | 2–4 | Not started |
| 2 | Closed definitions/context and first denied fixture | 1 | 4–6 | Not started |
| 3 | Safe versioned results and audit records | 2 | 4–6 | Not started |
| 4 | Durable intent/terminal publication barrier | 3 | 5–8 | Not started |
| 5 | Cross-process admission, fault and restart control | 4 | 6–10 | Not started |
| 6 | Actual-owner authorization/dispatch integration | 2–5 | 5–8 | Not started |
| 7 | Bounded process/cancellation lifecycle | 6 | 4–6 | Not started |
| 8 | Bounded server resolution/fault/flavor slice | 7 | 6–10 | Not started |
| 9 | Authorized server network relationships | 8 | 4–6 | Not started |
| 10 | Separately authorized bounded project summary | 9 | 4–6 | Not started |
| 11 | Go client adapter to authoritative owner | 10 | 4–6 | Not started |
| 12 | No-model catalog/invoke CLI | 11 | 3–5 | Not started |
| 13 | Versioned consumers/static deployment/rollback parity | 12 | 4–6 | Not started |
| 14 | Full-boundary adversarial scenarios | 13 | 4–6 | Not started |
| 15 | Manual, extension and operator guidance | 14 | 2–3 | Not started |
| 16 | Delivery-wide verification and cleanup | 0–15 | 4–6 | Not started |

**Total: 68–108 focused hours, about 11.3–18 engineer-days.** This is effort, not agent runtime or calendar duration.

## 8. Execution contract (for later authorization only)

Resolved policy: repository instructions/task plus inspected executor defaults. No project override was observed: **two failed validation attempts per same current-chunk issue**; no infinite repair loop or reset by opening another session. Baseline failures are classified separately. Level 0 repairs and Level 1 compliant choices proceed within the current chunk without routine permission; no advancement with a known required failure.

- Re-read this plan, complete applicable sources, repository instructions and latest authorized handoff before each chunk. Record base/candidate/source drift. Material changes require affected mapping/approval/preflight revalidation, not reuse of stale approval or this planning status.
- Do not start implementation until approval/amendment gates are satisfied and execution-time specification preflight passes against the actual committed task/base. A plan status is neither preflight nor execution authorization.
- Explicitly select mode. **Single-chunk:** exactly the requested chunk and stop; ask before creating an unrequested handoff. **Continuous-loop:** explicit authorization and a capable coordinator dispatching exactly one chunk per real fresh session; non-final handoff required, coordinator checks evidence before next dispatch. If orchestration is unavailable, disclose that and provide manual next-session instructions; do not simulate fresh sessions.
- Confirm/activate the user-provided Python venv once before Python execution; reuse it. No venv was supplied during planning. Go toolchain compatibility and existing dependencies must be verified; do not silently install or downgrade `go.mod`. Missing required tools/access is a blocker, not a green skip.
- Environment: development repository, temporary loopback API/subprocess/filesystem fixtures only; no cloud/provider/host contact or credentials. Before Go checks, set session-local `export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off` so tests/builds cannot silently download toolchains/modules; missing cached dependencies are reported, not fetched. Do not load root `.env`, private profile/inventory/generated data or raw operational evidence. Test hooks are internal only and must not become caller overrides.
- Keep delivery/phase/chunk/task labels in planning and evidence documents, not executable application symbols or configuration. Add only the current delivery's necessary contracts/helpers, never future-delivery stubs.
- Every chunk runs applicable syntax/format/build/symbol/import checks, focused behavioral regressions, complete relevant staged/unstaged/untracked diff review, and functional/integration/security risk assessment. Record actual commands, discovered tests, pass/fail/skip/not-run, validation gaps and safe rollback. Use §6 checks; preserve unrelated work.
- All implementation checklists below inherit this per-chunk post-work and bounded repair policy. Rollback means reverting only task-owned source changes after inspection, never deleting audit/intents, clearing an unresolved fault or reactivating a legacy bypass.
- Proposed future handoff locations, if authorized/required: `docs/handoffs/aiops-go-delivery-01-chunk-<N>-to-<N+1>.md` and a separate next-session instruction document per the installed handoff skill. No such artifacts are created while planning. Default evidence is the chunk completion report; GUIDE-P holds the final sanitized capability/consumer matrix. Raw operational evidence stays outside Git.
- A handoff carries source/plan identity, base/candidate/pre-existing work, mode/resolved policy/failure count, completed/next chunk, exact paths/symbols, actual checks/results/skips, diff/risk/rollback, blockers and precise next-session instructions. No credentials.
- Non-final statuses: `CONTINUABLE`, `BLOCKED`, `INCOMPLETE`. Final only: `READY_FOR_REVIEW` when approved scope is complete and all required offline verification passed; otherwise `BLOCKED` or `INCOMPLETE`. Review readiness never authorizes merge/deploy or another delivery. Independent review uses a separate fresh session.

## 9. Implementation Ladder: Delivery 1 safety boundary and manual slice

**Common chunk gate:** §8 post-work/repair/handoff/stop rules apply to every chunk below. Each worker handles only its named chunk. Tests accompany changes. New caller wiring occurs only after its contracts exist. New versioned paths remain disabled/unreachable until all required controls for that path work; any unfinished stub returns explicit safe non-success, never fake evidence. No legacy path is enabled merely to make an intermediate build useful.

### Chunk 0: Discovery and baseline

- **Goal / requirements:** confirm D1-01–D1-22 mapping, source gates, exact candidate and practical baseline; implement no feature.
- **Entry / inspect:** separately authorized discovery; S1–S8, aliases in §4, relevant caller/consumer and approved amendment sources through their endings. Inventory SDK, CLI, agent/workflow/project/specialist, direct runner/scripts, MCP/host and compatibility routes without executing them.
- **Changes / symbols:** no application changes. Record sanitized matrix/baseline in the authorized report; this plan is the only ladder.
- **Tasks:**
  - [ ] Verify tracked/committed source identities, the recorded AM1–AM5 approval against its exact task content, governing incorporation/commit and remaining ADR/task approval/provenance gates. Preserve the supplied amendment approval; do not reopen it absent material content drift. If execution prerequisites remain unmet, report the exact blocker and stop before implementation; do not amend sources to pass.
  - [ ] Record actual base/branch/staged/unstaged/untracked work; compare to planning base and historical baseline.
  - [ ] Resolve per-path lineage/dependency closure and exact consumer versions without importing/executing historical assets. Confirm current seven-tool source versus Delivery 1 three-tool view.
  - [ ] Confirm context/direct-invocation feasibility, collector/test seams and which existing diagnostics must remain disabled. Confirm no hidden policy owner or ambient authentication route.
  - [ ] Confirm approved venv, Linux subprocess/lock facilities, Go compatibility and fixture dependencies. Inspect baseline tests for external effects before running them.
  - [ ] When separately authorized and gates permit, run B0, G0, G1, P0, S0; record counts/skips and pre-existing failures. Fix exact offline Y0 command if role files will change; do not run host inventory or root Makefile.
- **Validation / compile-safe state:** read-only inspections and authorized baseline only; no production source changes. Planning did not complete this chunk.
- **Post-work / risk / rollback:** audit command side effects/generated files and full starting diff; no destructive cleanup. Toolchain/approval/transport ambiguity is reported, not guessed.
- **Handoff / stop:** §8 mode rule. Stop with confirmed gates/baseline/ladder and explicit limitations, or `BLOCKED`; no Chunk 1 implementation here.

### Chunk 1: Quarantine ambient-credential diagnostic entry points

- **Goal / requirements:** D1-01/08/09/15/20; prevent old executable paths from bypassing the new owner while building it.
- **Entry / inspect:** accepted 0 and approved specifications; `aiops/cmd/openstack-agent/main.go`, `openstack-workflow/main.go`, `openstack-project/main.go`, their tests and `internal/openstackclient/*`. Inspect startup ordering and local-inspection paths.
- **Changes / symbols:** three observed mains and their tests: one narrow diagnostic-admission guard per entry before AI/SDK construction. Six-file boundary is justified by the same bypass across three binaries and regression coverage; no generic runtime refactor.
- **Tasks:**
  - [ ] Disable noncompliant diagnostic execution before ambient authentication/model setup, with an actionable safe limitation; preserve non-diagnostic inspection when it can remain independent.
  - [ ] Add startup traps proving no SDK/provider/registry/specialist side effect on disabled paths; keep existing adapter-configuration/planning tests valid.
- **Excluded / safe state:** no new model, agent, workflow, project or resume integration. Libraries remain compilable; unverified executables do not dispatch.
- **Validation:** from `aiops/`, `rtk go test ./cmd/openstack-agent ./cmd/openstack-workflow ./cmd/openstack-project`, then G0/G1; V2/V3/V11. Expected counters are zero, not merely nonzero CLI exit.
- **Post-work / repair / risk / rollback:** format changed Go files, symbol/startup review and F0. Repair only narrow gating regressions within budget. Reverting a guard must not restore an enabled unsafe path; escalate if preserving unrelated inspection requires broader lifecycle work.
- **Handoff / stop:** §8; stop when all three diagnostic routes are visibly disabled before credentials and existing pure regressions pass.

### Chunk 2: Closed definitions, immutable context and a denied-request fixture

- **Goal / requirements:** D1-01/02/07/16; establish approved AM1 contracts before callers.
- **Entry / inspect:** accepted 1; R/G and `test_request_gateway.py`, `test_steps_01_to_04_integration_gate.py`; approved AM1/AM5 exact clauses.
- **Changes / symbols:** R definition/context validation responsibilities, G maintained versioned definition view, proposed T/`test_scoped_admission.py`. Three files are one closed-contract/test boundary. Do not introduce a second permissive Go registry.
- **Tasks:**
  - [ ] Add approved-version closed definitions and immutable application context with binding to reviewed policy/limits; derive exactly three enabled tools while retaining later definitions unchanged.
  - [ ] Reject duplicate keys/names/positions, missing metadata/limits, unknown fields/validators/versions, invalid defaults and caller overrides before executor access.
  - [ ] Prove an out-of-scope/unknown/mutation request with recording executor and audit seam: zero dispatch, one required terminal attempt. Positive new execution remains explicitly disabled.
- **Excluded / safe state:** no real collector, public actor/context/path overrides or speculative schemas. Absent required context/control returns safe non-success.
- **Validation:** J0, P1, PF for scoped admission and request/integration gate tests; V1/V2. Verify context/definition mutation after validation cannot alter the admitted request.
- **Post-work / repair / risk / rollback:** §8/F0; inspect closed-version and legacy-consumer diff. Fix validator/test defects only; escalate any needed closed-schema change beyond approved amendments. Roll back only disabled new view, preserving old source entries.
- **Handoff / stop:** §8; contracts compile/load, invalid requests cannot dispatch, first negative fixture passes; no useful-read claim yet.

### Chunk 3: Safe versioned result and audit representations

- **Goal / requirements:** D1-11/14/15/18/20; implement approved AM3/AM4 shapes without dispatch changes.
- **Entry / inspect:** accepted 2; R `build_result_envelope`, sanitizer, `build_audit_event`, serializers; existing result/redaction/audit tests and approved version clauses.
- **Changes / symbols:** R safe versioned builders/serializers; proposed T/`test_versioned_outcomes.py`; retain existing legacy tests, add assertions there only if needed to substantiate a divergence.
- **Tasks:**
  - [ ] Implement closed new result/intent/terminal records, all seven statuses and exact approved exits, safe target and independent redacted/truncated indicators; maintain frozen `1.0` field sets/translations.
  - [ ] Bind internally generated timestamp/correlation, per-event IDs, fixed `local_cli`, minimum-disclosure audit scope/presence fields and precise child-exit/null behavior.
  - [ ] Validate strict inner/outer shapes, safe partial/empty distinctions, UTF-8/compact single-line serialization, sanitizer depth/work/error limits and hostile values before any publication.
- **Excluded / safe state:** builders only; no early output, extra legacy fields, duplicate adapter events or success stubs. New execution still disabled.
- **Validation:** P1, PF new outcome tests plus existing result/redaction/audit files; V6/V9. Enumerate seven outcomes and legacy interruption translation, child versus process exits, and both redaction/truncation combinations.
- **Post-work / repair / risk / rollback:** §8/F0; audit field-count/disclosure and every serializer sink. Fix code against approved contracts; do not alter frozen tests to normalize unsafe observed exits. Revert only unused new builders, not retained data.
- **Handoff / stop:** §8; exact schema/status/identity/sanitization matrices pass, with no new dispatch enabled.

### Chunk 4: Durable intent and terminal publication barrier

- **Goal / requirements:** D1-12/13/14; ordered durable publication, no execution replay.
- **Entry / inspect:** accepted 3; R audit path/append/rotation/emit functions, `test_audit_persistence.py`, approved AM4 filesystem/control constraints.
- **Changes / symbols:** R intent/terminal lifecycle and durability helpers; proposed T/`test_intent_publication.py`. Keep filesystem primitives under the same owner.
- **Tasks:**
  - [ ] Persist safe intent before the recording executor; attempt terminal for every request, including rejection, and persist terminal before successful payload publication.
  - [ ] Preserve fixed metadata/locks/bounds/rotation; revalidate under lock and establish required durable file/directory transitions without weakening accepted rules.
  - [ ] Inject write/disk-full/permission/flush/fsync/lock/rotation failures at both stages: zero dispatch on failed intent; terminal failure suppresses payload/raw detail, preserves uncertain evidence, never retries execution or blindly duplicates a terminal.
- **Excluded / safe state:** no general checkpoint store, fallback audit, unsafe-path repair or real cloud execution. Recorders only; until shared fault control exists, new runtime stays disabled.
- **Validation:** P1, PF intent publication plus existing audit persistence; V7. Assert ordering and actual temporary-filesystem path/mode/symlink/non-regular/archive-collision checks, not only mocks.
- **Post-work / repair / risk / rollback:** §8/F0; inspect lock release, error normalization and fault-injection cleanup. Escalate if retained paths/rotation/durability must change. Never erase committed intent/event as rollback.
- **Handoff / stop:** §8; positive and fault ordering proofs pass; shared/restart health still explicitly pending.

### Chunk 5: Shared admission, crash uncertainty and restart-safe fail closure

- **Goal / requirements:** D1-02/10/13/14; stop-new-dispatch is cross-process and survives restart.
- **Entry / inspect:** accepted 4; R audit lifecycle and approved control-state/retention clauses. Confirm any materialized control filename/metadata in approved allowlist before use.
- **Changes / symbols:** R bounded shared admission/control-health/recovery responsibilities; proposed T/`test_shared_admission.py`. Extract a necessary helper only if cohesive and manifest-approved, not a generic persistence framework.
- **Tasks:**
  - [ ] Serialize or finitely reject concurrent admission, budgets, cancellation and policy/definition snapshots across independent callers; define lock ordering and bounded contention.
  - [ ] Detect unresolved intent, uncertain terminal persistence and corrupt/unprovable health across restart; no automatic replay, retrospective success or restart-as-recovery. Make safe local operational faults visible without an alternate sink.
  - [ ] Prevent rotation evicting unresolved required intent; stop safely within existing archive limits. Require trusted operator recovery when durability cannot establish health.
  - [ ] Add physical-process crash windows before/after dispatch/result/terminal, concurrent append/rotation/admission, failed control-state durability, recovery and no-deadlock/no-over-admission tests.
- **Excluded / safe state:** no resumable investigation/scheduler, cumulative investigation budgets or automatic recovery. New production dispatch still closed.
- **Validation:** P1, PF shared admission and intent/persistence tests; V8. Independent subprocesses and real files mandatory; preserve prior failure attempt counts.
- **Post-work / repair / risk / rollback:** §8/F0; security review admission races, crash durability and unresolved-intent retention. Mechanism fixes are Level 1; new paths/retention risks beyond AM4 require escalation. Rollback disables admission and preserves evidence/control faults.
- **Handoff / stop:** §8; another process/restart cannot dispatch through an unresolved fault, and safe recovery/no-replay tests pass.

### Chunk 6: Integrate authorization at the actual revised-owner boundary

- **Goal / requirements:** D1-01/02/07/08/09/12/16; no wrapper-only scope checks.
- **Entry / inspect:** accepted 2–5; R main/request/dispatch/environment code, G, source/consumer matrix, direct runner/script/SDK call paths and approved trusted-context design.
- **Changes / symbols:** R common admission/lifecycle wiring; T/`test_scoped_admission.py` and existing execution/profile tests. Additional narrow direct-entry guard changes are allowed only for the inventory's proven reachable bypasses.
- **Tasks:**
  - [ ] Route new requests through definition→current context/policy/profile/limits→intent→dispatch→safe terminal/publication. Bind copies/snapshots against caller or concurrent mutation.
  - [ ] Enforce trusted application context at the credential-bearing owner. Deny missing/forged scope and public override attempts before authentication/lookup/spawn. Direct callable routes must enforce controls or be unavailable to the enabled client.
  - [ ] Enforce exact reader/fresh minimal environment/integrity checks and explicit optional unavailability; no admin/operator/SSH fallback. Unknown/mutation requests attempt terminal without intent/dispatch.
  - [ ] Prove direct invocation, ambient environment and stale definition/policy races with recording API/executor fixtures. Keep collectors unregistered/unavailable until their own chunks pass.
- **Excluded / safe state:** no new approval workflow or privileged broker infrastructure. Catalog may describe unavailable capabilities honestly; no real useful read until controls and collector exist.
- **Validation:** P1/J0, PF scoped admission, request/execution/profile/integration tests; V1/V2/V3/V7/V8; zero forbidden operations at every retained enabled route.
- **Post-work / repair / risk / rollback:** §8/F0; audit actual credential-bearing path, not facade alone. If trusted transport/direct-invocation safety cannot be proven within approved architecture, `BLOCKED`, not a Go-owned replacement. Rollback keeps new admission disabled.
- **Handoff / stop:** §8; complete denied-request vertical slice is durable and bypass-tested; allowed fixture dispatch occurs only within the approved lifecycle.

### Chunk 7: Bound subprocess lifetime, output and cancellation

- **Goal / requirements:** D1-09/10/11; owned descendants/pipes cannot escape timeout or cancellation.
- **Entry / inspect:** accepted 6; R `terminate_process_group`, `capture_bounded`, `execute_fixed_diagnostic`; existing process-bound tests.
- **Changes / symbols:** R process/capture/cancellation logic; T/`test_process_bounds.py` with versioned outcome assertions as needed.
- **Tasks:**
  - [ ] Maintain exact shell-free argv/cwd/env and immediate target integrity revalidation; bound both streams before decode and never stream raw data.
  - [ ] Terminate/reap owned process groups even if direct parent exits first; bound drain/close/wait and handle interruption before/during/after spawn without uninitialized state.
  - [ ] Distinguish approved cancellation from timeout and cleanup failure; stop subsequent dispatch/retry when cancelled/budget-exhausted. Test floods, malformed encoding/JSON, split multibyte boundaries and surviving descendants.
- **Excluded / safe state:** no generic executable option or caller limits; test paths only internal. Cleanup failure never returns successful cancellation.
- **Validation:** P1, PF process bounds/execution/versioned outcomes; V5/V6. Record PIDs/marker absence and bounded elapsed time; no orphan/pending pipe after tests.
- **Post-work / repair / risk / rollback:** §8/F0; inspect cleanup races and sanitizer-after-capture ordering. Repair only bounded lifecycle defects; unsupported OS facilities block required evidence. Rollback disables affected dispatch, does not leave active fixtures.
- **Handoff / stop:** §8; exact process/environment/stream/cleanup matrix passes before real collector integration.

### Chunk 8: First useful bounded server, fault and flavor read

- **Goal / requirements:** D1-03/04/08/09/10/15/18; complete useful server slice under the revised owner.
- **Entry / inspect:** accepted 7 and approved AM1/AM2 artifact/field/relationship clauses; D server basics/helper, Go get-server/flavor tests, SDK-P prerequisites without credentials.
- **Changes / symbols:** proposed SDK-P and T/`test_scoped_project_reader.py`; R fixed collector binding; D/`server_basic_info.sh` and helper/DT only as necessary for the approved versioned script view. A larger cohesive boundary is justified only for the same safe collector, its fixed adapter and behavior tests, not unrelated refactoring.
- **Tasks:**
  - [ ] Implement finite separately scoped/disclosed exact-name resolution and direct UUID lookup; retain original input and verified identity, reject missing/ambiguous/deceptive matches. Bound pages/records/response bytes/collection memory as consumed.
  - [ ] Collect selected basic fields, absent/present safe fault and only observation-derived flavor fields; verify returned identity/project/relationship. Never request raw fault details/user-data/extra-spec maps or enumerate flavors as fallback.
  - [ ] Bind the narrow SDK and fixed script versioned view to the same revised owner/context/limits/audit lifecycle. Preserve direct script restrictions/UUID guidance and legacy projections. If retaining a direct script route would bypass scope, disable that client route rather than call stock code underneath a facade.
  - [ ] Test useful healthy/empty-fault, permission denial, wrong scope/identity, missing flavor, hostile strings, huge pages and unsupported script-name fixtures with exact API/argv counters.
- **Excluded / safe state:** no general flavor tool, host output, extra-specs, new package install or live SDK. Existing broad Go SDK helpers remain disabled for enabled clients; network/summary remain unavailable until their chunks.
- **Validation:** P1/PF collector plus G0 identity preservation, S0/S1 for changed script view, V3/V4/V5/V9/V10. Exact versions and fault/flavor projections must match approved clauses, not invented wire fields.
- **Post-work / repair / risk / rollback:** §8/F0; review actual API collection/memory and credential paths. A needed new capability/SDK dependency/allowlist expansion beyond amendments blocks integration. Disable new binding to roll back, retaining prior evidence and identity/data.
- **Handoff / stop:** §8; one useful safe bounded server result traverses actual-owner authorization and durable audit, with SDK/script fixture parity and no unintended reads.

### Chunk 9: Server-scoped network relationships

- **Goal / requirements:** D1-05/09/10/15/18; collect only authorized attached network evidence.
- **Entry / inspect:** accepted 8; D/`server_network_info.sh`, bounded Go ports seam/tests, SDK-P and approved visibility rules.
- **Changes / symbols:** SDK-P network collector, D network adapter if retained, T collector tests and DT regression cases (cohesive adapter/behavior boundary).
- **Tasks:**
  - [ ] Derive ports from verified requested server; validate returned device/project, then network/subnet linkage and permitted visibility before each lookup. Model assertions never create a relationship.
  - [ ] Bound pagination, section records, deduplicated related reads, aggregate bytes/memory and elapsed/call budget during collection; carry cancellation through every read.
  - [ ] Preserve projected fields and empty/partial/unavailable behavior. Test forged/mismatched/shared resources, unavailable detail and large/flooded responses without broad discovery or fallback.
- **Excluded / safe state:** no metadata diagnosis, host/listener/agent health or unrelated topology list. Summary still unavailable.
- **Validation:** P1/PF collector, S0/S1 if scripts change, existing Go port regressions; V4/V5/V9. Assert positive derived reads and zero forbidden subsequent lookup, not only safe final output.
- **Post-work / repair / risk / rollback:** §8/F0; inspect relationship provenance/visibility and bounds. Escalate unreviewed shared-resource policy instead of guessing. Disable network binding on rollback; preserve server slice.
- **Handoff / stop:** §8; network evidence remains within authorized relationships under both retained adapter seams.

### Chunk 10: Separately authorized project summaries

- **Goal / requirements:** D1-06/09/10/15/18; bounded project visibility never follows from server scope.
- **Entry / inspect:** accepted 9; D/`project_resource_summary.sh`, SDK-P, existing seven-section DT fixtures and approved summary mapping.
- **Changes / symbols:** SDK-P summary collector, fixed summary adapter as necessary, T collector tests/DT. No new resource-type modules.
- **Tasks:**
  - [ ] Require explicit project-wide capability and current cloud/project reader context, with no public target/profile/field selector.
  - [ ] Collect the seven fixed selected-field sections with finite API/response/memory/time/call limits during collection; preserve 50-record section cap, complete-document and tighter runner bounds.
  - [ ] Distinguish successful empty, independent unavailable partial and fatal authentication/configuration; stop forbidden subsequent reads, never promote missing data to healthy state. No volume/attachment traversal beyond existing summary fields.
- **Excluded / safe state:** no cross-project list, attachment investigation, operator visibility or automatic role retry.
- **Validation:** P1/PF collector, S0/S1 where applicable; V4/V5/V9/V10. Server-only assignment yields zero project list; oversized/fatal/partial fixtures have exact expected calls and safe evidence gaps.
- **Post-work / repair / risk / rollback:** §8/F0; review all seven operations and aggregate bounds. Repair only permitted projection/collection behavior; disable summary binding if authority cannot be proven.
- **Handoff / stop:** §8; exactly the three Delivery 1 tools are useful or explicitly limited through the same boundary, without later catalog activation.

### Chunk 11: Go adapter without policy or credential ownership

- **Goal / requirements:** D1-02/03/09/10/11/15/17/20; Go consumes the authoritative owner, not raw SDK/independent registry.
- **Entry / inspect:** accepted 10; existing Go tool interfaces/callers, approved fixed runner transport/context/version contract and test seams.
- **Changes / symbols:** proposed GO-P pair. Responsibilities: bounded fixed owner invocation, trusted context handoff, versioned decoding/cancellation and safe catalog/result presentation; exact exported names are Level 1.
- **Tasks:**
  - [ ] Add minimal request/result/client contracts and compile-safe explicit-failure behavior before caller wiring; implement only named owner calls, no caller executable/profile/env/path.
  - [ ] Pass application-owned context through approved transport, without credentials in Go process arguments/results or public claims becoming authority. Preserve owner-generated correlation/identity and exact safe outcome semantics.
  - [ ] Bound invocation/decoding and cancellation with no post-terminal dispatch, duplicate audit, silent retry or fallback to legacy/SDK. Consume derived catalog, not a handwritten capability copy.
  - [ ] Test the real adapter against controlled runner processes with all statuses, malformed/unsupported versions, extra/trailing data, hostile errors, blocked audit and disabled SDK traps.
- **Excluded / safe state:** no agent/workflow/project integration or new provider. Until CLI wiring, adapter is exercised only by fixtures.
- **Validation:** from `aiops/`, `rtk go test ./internal/diagnostics`, G2 for new package, G1; V2/V5/V6/V9/V11.
- **Post-work / repair / risk / rollback:** gofmt changed files, §8/F0; symbol/interface and transport security review. Escalate unprovable context integrity, not downgrade to public context JSON. Roll back unused adapter without re-enabling old command paths.
- **Handoff / stop:** §8; Go client proves equivalent bounded owner behavior with zero inference/authentication bypass.

### Chunk 12: Model-independent manual catalog and invoke

- **Goal / requirements:** D1-03/09/11/16/17/18; operator-visible standalone CLI.
- **Entry / inspect:** accepted 11; command conventions, GO-P, approved manual behavior, `aiops/Makefile`.
- **Changes / symbols:** proposed CLI-P pair and observed `aiops/Makefile` to build the new command. Three-file CLI/build/test boundary; public syntax selected/documented here, not guessed as an existing API.
- **Tasks:**
  - [ ] Add list/invoke behavior using the owner-derived enabled catalog and explicit application scope/budgets. No model/client/knowledge/store/specialist construction.
  - [ ] Print exactly safe versioned results/exit mappings and actionable UUID/unavailable/denial guidance; do not echo raw malformed input or internal filesystem errors.
  - [ ] Test compiled CLI/list/invoke in fixture-only environment with absent provider/knowledge/credentials and traps for inference/ambient SDK/host/MCP. Include unknown/mutation/override inputs and exact expected stdout/exit/dispatch.
- **Excluded / safe state:** no automatic investigations or new plan approval UX; existing unsafe command diagnostic paths remain disabled. Live launch requires separate live gates even after build.
- **Validation:** from `aiops/`, `rtk go test ./cmd/openstack-diagnostic ./internal/diagnostics`, `rtk go build -o bin/openstack-diagnostic ./cmd/openstack-diagnostic`, then G1/G2; V2/V4/V6/V9/V10. Actual subprocess CLI smoke, not private parser tests alone.
- **Post-work / repair / risk / rollback:** gofmt/§8/F0, command help/build target and early-init review. Repair CLI-only defects; rollback removes new binding/binary target while leaving guards intact.
- **Handoff / stop:** §8; useful manual catalog/invoke fixture works without any inference prerequisite and all forbidden paths show zero dispatch.

### Chunk 13: Compatibility consumers, static deployment metadata and rollback

- **Goal / requirements:** D1-01/07/08/11/14/20/21; safe version transition without breaking or silently enabling later consumers.
- **Entry / inspect:** accepted 12; approved AM5 and consumer inventory, I/R/G/RD/RT, static role assertions and affected independent consumer contracts identified in 0.
- **Changes / symbols:** I version-aware inspection where retained; approved exact RD/RT file/target/control metadata; proposed T/`test_version_compatibility.py`. R/G compatibility fixes only if substantiated. Larger boundary is limited to one version transition and its deployment/inspection assertions.
- **Tasks:**
  - [ ] Verify explicit old/new definition/result/audit selection; preserve legacy common outcomes and output-only cancellation translation without second execution/event.
  - [ ] Accept mixed retained audit versions only through approved inspection rules; reject incompatible consumers and malformed versions, no two-event flattening or historical-record rewriting. Leave deferred host/MCP adapters disabled for the new protocol rather than implement them now.
  - [ ] Enumerate only approved fixed collector/control artifacts and restrictive ownership/modes; retain disabled defaults, project-only enablement and later source entries unchanged.
  - [ ] Exercise disable-new-path rollback using synthetic data: stop admission, bound active work, retain intent/events/faults and prohibit unsafe old credential/runner fallback. No live deployment or state conversion.
- **Excluded / safe state:** no host/MCP implementation/migration or privileged installer run. Source artifacts do not grant runtime installation/activation.
- **Validation:** P1/J0/PF compatibility, P0, S0, G1, Y0 if files change; V1/V3/V6/V11. Inspect pure planning/digest/zero-start and existing manual regressions.
- **Post-work / repair / risk / rollback:** §8/F0; full source/consumer/allowlist diff/security audit. Unapproved incompatible independently governed consumers are escalation, not scope expansion. Reversion leaves new path disabled and evidence readable/preserved.
- **Handoff / stop:** §8; version/consumer matrix and static rollback evidence are explicit, with no silent live activation or weaker fallback.

### Chunk 14: Highest-seam scenario seeds and adversarial coverage closure

- **Goal / requirements:** D1-13/15/16/17/18/19; close full-boundary gaps, not defer all testing to this chunk.
- **Entry / inspect:** accepted 13; CLI-P/GO-P, T/DT, §5 mapping and task V1–V11 against tests already added.
- **Changes / symbols:** proposed T/`test_manual_scenarios.py` and versioned synthetic fixture data under T/`fixtures/manual-diagnostics/`. Extend existing redaction/shared-admission fixtures only for substantiated coverage gaps.
- **Tasks:**
  - [ ] Seed healthy server, permission denial and hostile output records with version/source identity, expected calls/targets/status/evidence/limitations/safety and deterministic actual comparison; no full evaluation metrics platform.
  - [ ] Exercise actual CLI→adapter→revised owner→controlled API/script lifecycle with no cloud/provider credentials. Include operator-insistent mutation/ignore-policy attempts and model-init traps.
  - [ ] Place nested/text/argument/error/stderr/PEM/bearer canaries across split/multibyte/truncated output and sanitizer work/depth/malformed cases. Assert absence at every enabled public/store/audit sink; no future sink is scaffolded merely for this test.
  - [ ] Confirm shared fault/crash/restart tests still apply when entry is the CLI; enumerate all V1–V11 missing cases and add bounded regressions for current behavior only.
- **Excluded / safe state:** no domain root-cause claims, model quality/cost rubric, full incident corpus or deployed-policy proof.
- **Validation:** PF scenarios/redaction/shared control, P0, S0, G1/G2; V8/V9/V10. Inspect discovery/counts and expected/actual sequences; zero mutations/disclosures/forbidden executions.
- **Post-work / repair / risk / rollback:** §8/F0; sanitize fixtures and scan retained test artifacts. Ordinary scenario/test defects repaired here; newly discovered feature defects require explicit bounded repair under the same controlling plan, not weakened assertions. Roll back only synthetic task fixtures.
- **Handoff / stop:** §8; three deterministic scenario seeds and complete applicable V coverage have evidence, all fixture limitations stated.

### Chunk 15: Manual and operator guidance

- **Goal / requirements:** D1-01/08/20/21; document safe use and remaining live gates.
- **Entry / inspect:** accepted 14; actual CLI help/build behavior, final source/consumer matrix, S6/S7 and task guidance obligations.
- **Changes / symbols:** proposed GUIDE-P only, with links to approved sources; this plan remains the only controlling ladder. No source-contract amendment or roadmap checkbox completion.
- **Tasks:**
  - [ ] Document exact implemented no-model list/invoke and credential-free fixture reproduction, versions, enabled/disabled capabilities, limits/identity guidance, partial/unavailable meaning and incomplete-audit fault behavior.
  - [ ] Record entry-point/provenance/consumer gap matrix and significant Level 1 choices, legacy/new compatibility, safe disable/rollback and no-replay constraints.
  - [ ] Describe extension review, fixed placement/profile/file metadata, required/optional startup gates, admin-team month-expiry rotation/revocation and separate deployment acceptance ownership.
  - [ ] Describe operator-only approved reads/disposable create/update/delete-denial procedure: conclusive 403/Forbidden plus independent administrator postconditions, cleanup owner, immediate stop/revoke on unexpected mutation; never a registered tool. No live command execution or credential values.
- **Excluded / safe state:** no operational readiness claim, new retention policy or deployment recipe that silently enables unverified access.
- **Validation:** V11 document/link/command/scope review; run only the documented offline fixture/demo path using existing test harness, never a live invocation. Read through document ending; F0.
- **Post-work / repair / risk / rollback:** §8; verify commands match actual CLI and no sensitive topology/operational artifacts are copied. Correct docs only; behavior defects go to bounded repair. Rollback affects guide only, not controls/evidence.
- **Handoff / stop:** §8; accurate reproducible manual/owner guidance exists, all live and deferred capability gaps explicit.

### Chunk 16: Final verification, documentation and cleanup

- **Goal / requirements:** D1-01–D1-22; verify selected delivery, not add another capability.
- **Entry / inspect:** all accepted 0–15 and approved sources unchanged or revalidated. Inspect entire implementation delta and every enabled entry/consumer, including relevant untracked files.
- **Changes / symbols:** no planned feature additions. Only task-created accidental artifact cleanup or documentation corrections; preserve unrelated work, legacy records and durable control evidence.
- **Tasks:**
  - [ ] Run complete G1, G2 on affected packages, P0, applicable P1/J0/S0/S1/Y0, and all mandatory new V1–V11 fixtures with discovery/skips reviewed. Confirm Go Makefile builds the new CLI as well as existing commands.
  - [ ] Repeat actual CLI offline demo/scenarios, process cleanup, cross-process/crash/restart/audit-publication/rotation faults and versioned rollback checks as applicable. Report offline versus unrun live/model tiers distinctly.
  - [ ] Check matrix rows against actual evidence, approved AM clauses and enabled catalog. Verify no unfinished success stubs, direct SDK/runner bypass, future schemas/modules, model/host/MCP activation or raw sink remains.
  - [ ] Review full base-to-candidate plus staged/unstaged/relevant untracked diff, formatting, source/import/caller/allowlist consistency and security boundaries. Confirm protected requirements/architecture and historical data were not altered without separate authorization.
  - [ ] Remove only proven task-created accidental/generated artifacts; do not reset/clean or erase unrelated work/audit. Rerun affected verification after any repair/cleanup.
  - [ ] Produce evidence-based final report: approved source/amendment identity, implementation base/candidate/worktree, changed paths, meaningful choices, per-requirement local subset, commands/results/counts/skips, manual fixture outcomes, risks/limitations/deviations and live gates.
- **Validation / safe state:** all mandatory offline checks pass with actual evidence; no claim of deployed reader/route/profile/model isolation from fixtures. F0 covers complete delta, not only last chunk.
- **Post-work / repair / risk / rollback:** final scope/security/diff audit. If a feature defect is discovered, name an explicit bounded in-scope repair entry in this same plan, preserve completed evidence and repeat final gate; no hidden feature work in cleanup and no competing ladder. Apply failure budget/escalation, never weaken tests.
- **Handoff / stop:** no automatic next-delivery handoff. `READY_FOR_REVIEW` only with approved scope complete and required offline checks passed; `BLOCKED` for unresolved authority/access/safety, `INCOMPLETE` for unfinished work. Stop for independent fresh-session review; no merge/deploy/Delivery 2.

## 10. Final acceptance and evidence obligations

These are future execution gates; none is completed by writing this plan.

- [ ] Authority resolved: approved/committed task/ADR/amendments and actual implementation base/candidate recorded; full scope preserved, no silent legacy-compatible reduction.
- [ ] Every retained enabled local CLI/SDK/script route reaches one revised policy/registry/dispatch owner; disabled automatic/deferred paths cannot authenticate/execute as a side effect.
- [ ] Exactly three permitted manual tools produce useful bounded safe evidence or explicit limitations without model/provider/knowledge dependency; exact-name/UUID intent and safe relationships remain intact.
- [ ] Unknown/mutation/invalid/out-of-scope/profile/relationship/override requests never execute forbidden reads or arbitrary processes; required terminal attempts are verified.
- [ ] Approved seven-status result and two-stage audit behavior, independent metadata, minimum disclosure, pre-dispatch intent and pre-success terminal durability pass. Legacy closed views remain versioned and unchanged in meaning.
- [ ] Audit/control/collection/process faults, cross-process concurrency, crash/restart, unresolved-intent rotation and cancellation cleanups pass with real filesystem/process evidence; no replay, leaked payload, fallback sink or restart bypass.
- [ ] Secret/injection canaries show zero prohibited disclosures; successful empty/partial/unavailable/error are not misrepresented as diagnosis/health.
- [ ] Three scenario seeds, consumer/entry matrix, manual/extension/revocation/preflight and safe rollback guidance are verified; required repository offline checks pass, discovery/skips and limitations reported.
- [ ] Complete final diff/scope/security audit shows no unrelated edits, future delivery scaffolding, secret/private `.env`/profile/raw operational evidence, unapproved source change or deployment. Independent acceptance remains a separate human decision.

## 11. Risks, decision requests and limitations

| ID | Category / problem / evidence | Alternatives and recommendation | Decision or remaining work | Blocking? |
| --- | --- | --- | --- | --- |
| K1 | Source-publication/implementation gate: AM1–AM5 explicitly approved in this conversation at the task blob in §1, while S3/S4 still say draft and governing incorporation/commit is pending; older Q1–Q3 provenance limitation is separate | Record actual approval and retain source/commit/preflight gates (recommended); do not pretend conversational approval amended governing files or repeatedly request unchanged AM approval | Incorporate/commit approved amendments through a separately authorized documentation process; establish remaining whole-ADR/task review/approval/provenance readiness, then execution preflight. No unresolved amendment-content decision blocks the completed plan | **Implementation only; not planning readiness** |
| K2 | Architecture/security: trusted context/direct runner and ambient SDK bypass not yet proven | Retain revised owner with protected context and route/disable (recommended); Go-owned replacement would change Q2 | Chunk 0/6 feasibility evidence; escalate with paths/counters/options if compliant transport fails. Do not choose new infrastructure silently | Conditional |
| K3 | Environment: Go `1.27.1`, approved venv/race/compiler/jq availability unverified | Use verified existing supported environment; otherwise report required tooling gap, no automatic installs/downgrade | Confirm in 0 before checks; no private venv path in repository | Conditional |
| K4 | Integrity: terminal-only/thread tests do not prove cross-process admission/restart durability; archive limits constrain unresolved intent retention | Serialize/fail closed within AM4 (recommended), not clear faults/evict intent for availability | 4–6 real process/filesystem/crash evidence; any new material retention risk requires owner approval | Conditional |
| K5 | Scope/compatibility: current revised source has seven tools and later host/MCP consumers | Preserve independent definitions, explicit versioned three-tool view, gate incompatible consumers (recommended); deleting later tools or implementing adapters would exceed scope | 0/13 consumer review; no later feature work | Conditional |
| K6 | Bound collection: scripts slice after buffering and Go server resolution uses `AllPages` | Bounded collector/response/page/memory algorithms and safe truncation/rejection (recommended), not cosmetic output slicing | 7–10 fixtures must prove collection-time limits and tighter inherited ceilings | No new product decision |
| K7 | Deployment evidence: current routes/effective reader privileges/profile readiness unknown | Keep live disabled (recommended); fixtures cannot prove policy. Separate owner-approved Phase 07/equivalent gate later | 15 documents exact read/denial/admin-postcondition/revocation ownership; no live work here | Live only |

Meaningful Level 1 choices are documented, not elevated to product decisions. Escalations must state category, concrete evidence, alternatives/tradeoffs, recommendation, precise human decision and independent safe remaining work. Do not reopen recorded Q1–Q3 merely because mechanisms are difficult. Do not claim planned checks ran or turn an unverified requirement optional for a positive status.

## 12. Suggested later execution prompt

The plan is ready for separately authorized Chunk 0 discovery; remaining source gates still prevent implementation. This prompt is **not executed** and does not authorize itself:

```text
Use chunked-implementation in single-chunk mode.
Controlling plan: docs/aiops-go/delivery/01-safety-boundary-and-manual-slice-delivery.md
Task: Delivery 1 only. Execute Chunk 0 discovery/baseline only, then stop.
First verify the complete current source/approval/amendment gate and actual base.
Honor the recorded AM1–AM5 approval for the exact task blob identified in §1;
verify governing incorporation/commit and remaining whole-ADR/task prerequisites.
If execution prerequisites are unmet, report the exact blocker; do not reopen
unchanged amendment approval, start code or silently amend sources.
Run baseline checks only when their
authority, offline safety and required environment are confirmed. No live calls,
provider, credentials, installation, root Makefile, deployment, commit or later delivery.
Report actual evidence and limitations; ask before creating an unrequested handoff.
```

Continuous-loop mode requires a separate explicit instruction and real fresh-session orchestration. Planning ends here. **PLAN_READY** is the planner's assessment of this complete ladder, not independent plan acceptance, approved/committed source readiness, `PREFLIGHT_PASS`, execution authorization or a passing implementation/test result. Implementation remains gated as specified in §1 and Chunk 0.
