# Delivery 1 — Go-owned Safety Boundary and Manual Slice

## 1. Plan identity and objective

- **Planning status: PLAN_BLOCKED for implementation — the environment-auth direction, restricted application credential, protected policy and lab HTTP risks are owner decisions; these revised working-tree bytes are proposed, not approved or committed.** The prior candidate was committed at `84e921f1c72695c7ce1ca2e34720d08b941b5283`. Independent review, applicable exact-candidate approval/commit and fresh preflight remain pending before separately authorized offline implementation. Unverified real policy-value provenance and deployment/route evidence gate live use, not independent review or synthetic offline work. This is not an implementation instruction.
- **Sole execution ladder:** this document, `docs/aiops-go/delivery/01-safety-boundary-and-manual-slice-delivery.md`. Source phase files/old revised ADSs are requirements/design history, never another executable ladder.
- **Scope:** Go Phase 01 Steps 1–3 / §01.6 under the committed [Go-owned ADR](../architecture/01-go-owned-safety-boundary-adr.md) and [bounded task](../tasks/01-go-owned-safety-boundary-task.md), supplemented by the proposed reconciled [environment-auth ADR amendment](../architecture/01-go-owned-safety-boundary-env-auth-amendment.md) and [task amendment](../tasks/01-go-owned-safety-boundary-env-auth-amendment.md). U4 approved the earlier environment-auth candidate; the later owner decision selects restricted application credentials. Neither approves these revised bytes; the later policy/HTTP decisions and documentation-only authorization likewise do not approve this exact reconciliation.
- **Objective:** useful named manual diagnostics without model or Python dependency through one Go-owned scoped, bounded, sanitized and durably audited boundary.
- **Project mode:** existing project with partial implementation. Source presence is not safety acceptance.
- **Original reconciliation base:** `0015097ff8cd73d80cf04e38c0f088f18e48b384`; historical requirements/code baseline: `0182da9f7c2b322df5da49262748974009db7332`. The accepted Go source candidate was inspected at `16cfe0ede231df7b90b4f93961a7b6eff16512a1`, branch `aiops-go-phase01`, clean before this documentation-only change. The candidate contains only specification, approval-record and handoff documents; no implementation delta is introduced. Verify the exact commit and tree at review time.
- **Implementation authorization:** none. Mode **UNSELECTED**. The separately authorized Chunk 0 discovery/offline baseline was completed against the prior candidate at `16cfe0ede231df7b90b4f93961a7b6eff16512a1` and is recorded in §4. U4 documentation work is not a fresh implementation preflight and authorizes no later chunk.

Smallest useful outcome:

```text
trusted current policy + requested server_basic_info scope
  -> Go owner validates/admits -> durable intent
  -> fixed bounded SDK read -> sanitize -> durable terminal
  -> one safe versioned result, no inference or Python runner
```

### Supersession and approval history

The original plan at the reconciliation base has blob `ffb89dc6d69a9bc051d11acf9fb0de1261affa4b`, initially authored at `10c4784754a0189535af7c310959a83d51d7a7c0` and committed in `4c5e6ae987cfeaafe5abc79bbeb6b5df076b5f74`. It contained 17 unstarted chunks (0–16) for conditional revised-Python-runner ownership; none was completed or accepted. This in-place reconciliation replaces that unexecuted ladder, preserving its history and full-scope safety requirements, not carrying its `PLAN_READY` self-assessment forward to a changed architecture.

The prior [ADR](../architecture/01-safety-boundary-and-manual-slice-adr.md), [task](../tasks/01-safety-boundary-and-manual-slice-task.md) and [complete addendum](../../ai-ops-revised/runtime/go-phase01-versioned-diagnostic-amendments.md) remain unchanged. Prior AM1–AM5/whole-document/incorporation approval and Q1–Q3 attestation belong to their exact prior content. They do not approve the replacement.

ADR U1 records the owner's explicit acceptance of review against the current committed publication candidate instead of recovery of missing addendum blobs; U2 selects reassessment of Go ownership; U3 authorizes the original documentation; U4 approves the Go-only process-environment authentication direction and the earlier documentation candidate for commitment. The later owner decision recorded in the 003/004 handoffs preserves the restricted application-credential mechanism. The 005 handoff records the initial Keystone-only risk decision for the management path from `assistant02` to `http://192.168.121.5:5000/v3`. In the current clarification conversation the owner reported no HTTPS in the OpenStack deployment, accepted service-HTTP risk for all deliveries in this lab until another PRD/story addresses it, identified themselves as risk owner, confirmed no expiry for either exception and said no further individual endpoint or route approvals are needed within this lab. The owner confirmed the separate protected JSON policy path, ownership/modes and independent identity/endpoint grants, but rejected a 30-day policy-validity limit for this MVP PRD/story. The broader risk decision does not itself amend legacy runtime contracts, authorize route changes or live use, or extend this ladder beyond Go Delivery 1. The earlier candidate's claimed administrative confirmation of real IDs/endpoints remains independently unverified. The present documentation-only authorization does not approve these exact revised bytes or live use. The [U4 approval record](02-go-environment-auth-approval-record.md) binds the earlier exact candidate, not these revised bytes; the prior approval record remains unchanged. No recovered historical comparison is claimed. G1–G7 identify proposed ownership/definition/audit namespace/consumer/verification deltas. A separate fresh agent must independently review those deltas, U4's credential-source implications, and historical approval/review ordering. If review requires a material change, obtain affected re-review and renewed approval/commit. Then perform fresh implementation preflight at the actual base and obtain separate execution authorization. Do not implement either old or new ladder while these gates are unresolved.

## 2. Sources and authority

| Source | Identity / inspected material | Role |
| --- | --- | --- |
| Repository instructions | `.agents/AGENTS.md` (symlink to `$HOME/.agents/AGENTS.md`), session `$HOME/.pi/agent/AGENTS.md`, entire instructions. | Scope, authority, verification and fresh-session review. |
| Go PRD | `docs/aiops-go/prd.md`, blob `18add68f88a07ace80979f86b2009d2435524743`, entire document through Further Notes. | Product truth; Q1 attests bounded Phase 01 at the historical revision, not all phases. |
| Source phase / overview / baseline | `implementation-plan/01-safety-boundary-and-manual-slice.md`, blob `0b02155576fdeec1d899ed9cc59142e2bce01d9b`; overview and educational baseline, read through endings. | Scope/deferred ownership; curriculum does not grant capabilities. |
| Committed Go-owned ADR/task | ADR Git blob `a585c1c9f7881d8cead7c0cb4b904ba14899e3ac`; task Git blob `b8bc812cef8b9b662b10c3c80715fd48ea9405fa`. | Accepted prior candidate; unchanged. |
| U4 environment-auth amendments | Proposed reconciled [ADR amendment](../architecture/01-go-owned-safety-boundary-env-auth-amendment.md) and [task amendment](../tasks/01-go-owned-safety-boundary-env-auth-amendment.md); earlier candidate fingerprints and approval provenance in [U4 record](02-go-environment-auth-approval-record.md). | Go-only process-environment inputs with restricted application credential; preserve identity/project/no-fallback and legacy contracts. Changed bytes require independent review and applicable approval/commit. |
| Addendum/current affected contracts | Addendum `d415d14414e6887fa71b3a9dea04520e9f88f4d1`; toolbox `3062e3b4b9fca362ea3d51decb8637dd8ad1b396`; runner 1–4 `993d8542232e92b0f3f81ae3957e0064f83b3900`; runner 5–7 `761faeb7e01e0348f8b08087af9f5ec503591079`. Entire files read. | U1's alternative review basis; not a Python dependency or approval of Go replacement. Missing historical addendum candidates remain missing. |
| Revised placement/foundation/identity/reuse, runner ADSs and restricted-host contracts; Go Phase 03 | Complete relevant documents inspected. | Explicit compatibility/safety references; no legacy runtime/host/MCP activation or shared mutable audit. |
| Current `aiops/` code, tests, `go.mod`, Makefile | Paths/symbols in §4 inspected; offline tests/vet/race and four command builds executed as recorded below. | Partial implementation/reuse evidence only; passing baseline is not safety acceptance. |

The Go PRD, original Go ADR/task, proposed reconciled amendments, and this sole ladder are the candidate source set for this slice; the prior candidate was committed at `84e921f1`, while these revised working-tree bytes require independent review, applicable exact-candidate approval/commit and fresh preflight before implementation. Legacy contracts remain governing for their own runtimes. The source Phase 01 reconciliation is not silently discarded: ownership/compatibility replacement deltas are G1–G7; Go-only authentication and protected policy, and the owner's broader lab-only HTTP risk decision, are recorded in the proposed amendments. Fixed identity/placement and remaining safety guarantees are retained; changed Go audit paths require explicit replacement approval. U4 changes the Go authentication-input source, not identity, privilege or legacy profile contracts. The HTTP risk decision does not itself authorize other deliveries, route changes or legacy contract amendments. No PRD, roadmap or old approval record is edited here.

Executor compatibility checked by reading installed `chunked-implementation` entrypoint, core safety, execution policy and delivery execution contract. Their defaults are embedded in §8. Real fresh-session orchestration was not tested and no executor was launched. Chunk 0 inspected the transitive consumers/code needed for the recorded baseline. No protected profile, `.env` value, inventory, generated cloud data, or raw audit data was read or used; `.env` inspection was limited to key names.

## 3. Scope, guardrails and proposed file ownership

Implement only the three tools `server_basic_info`, `server_network_info`, `project_resource_summary`, closed definitions/inputs, trusted per-call policy/scope, bounded exact-name/UUID/derived relationships, reader isolation, seven-status `2.0` outcomes, durable intent/terminal/control recovery, manual CLI, offline evidence and guidance. Task §§4–7 contain exact fields, limits, event counts, filesystem protections and rollback; the ladder cannot weaken them.

Preserve isolated `assistant02` / `ai_ops_assistant` / `aiops_assistant` / `/opt/openstack-ai-ops-assistant`, the dedicated reader identity, project/domain scope, expiry/rotation/revocation ownership, and applicable restricted metadata. For Go only, authentication inputs arrive in process environment supplied by a trusted operator-controlled launcher; Go must not load `.env` itself or use `clouds.yaml`, `secure.yaml`, or another profile as credential source/fallback. The owner selected a separate protected noncredential JSON policy at proposed `/opt/openstack-ai-ops-assistant/policy/diagnostics.json`, root-managed and runtime-unwritable; the amendments define its metadata and revalidation, without a 30-day policy-validity requirement. Independent confirmation of expected IDs/service endpoints and actual route evidence remain unverified. The existing revised/Python profile contracts remain unchanged for those runtimes. The proposed Go audit subdirectory is `/opt/openstack-ai-ops-assistant/audit/go/`, not the Python log/lock/state. Never forward OpenStack credentials to a model/child process or let proxy/provider/SSH environment alter the approved transport. This environment-source choice does not prove reader privileges; effective access remains a separate live gate.

Exclude mutation/remediation, generic executable/shell/SSH/HTTP/file/database tools, stronger credentials, historical runtime reuse, model/agent/planner integration, specialists, investigation recovery/memory/RAG, project/domain/volume workflows, host/MCP, full eval platform, public API/service/UI or future infrastructure. No installation, provisioning, live calls/probes, credential operation, protected-data/audit inspection, root Makefile/Molecule/host Ansible execution, staging/commit/push/merge/deploy.

New paths below are **proposed** and must be reconfirmed at fresh preflight; the prior Chunk 0 inspected current code/consumers but created no application file:

| Alias | Proposed source / responsibility |
| --- | --- |
| GO | `aiops/internal/diagnostics/`: `definitions.go`, `boundary.go`, `result.go`, `sanitize.go` and focused `_test.go` files. One owner, not a second policy registry. |
| AUDIT | Same package: `audit.go`, `control.go`, corresponding tests for filesystem and multiprocess lifecycle. Only audit/control state, not investigation persistence. |
| READER | Same package: `reader.go`, `server.go`, `network.go`, `summary.go`, with focused tests. Closed process-environment auth mapping, authenticated identity/project verification and narrow Gophercloud SDK calls under owner lifecycle. |
| CLI | `aiops/cmd/openstack-diagnostic/main.go`, `main_test.go`; manual command, no model construction. |
| GUIDE | `docs/aiops-go/manual-diagnostics.md`: implemented usage, entry/consumer matrix, deployment manifest, accepted Go authentication variable names and trusted-launcher ownership (no values), extension/revocation/live prerequisites and rollback. |

Internal organization is Level 1 after approval; create only current-chunk necessities. Proposed filenames are not a mandate for broad abstraction. Record and check exact runtime/control artifact metadata in its introducing implementation chunk; the final manifest must receive applicable review before installation/live use. Document accepted Go auth variable names and trusted-launcher ownership without values or a Go credential-file layout. Temporary internal fixture roots are not production path overrides. A new dependency, credential-file layout, or infrastructure needs separate approval, not merely a manifest entry.

## 4. Current state and baseline strategy

| Observed source | Existing behavior / remaining work |
| --- | --- |
| `internal/tools/registry.go`, `Registry.Execute` | Named dispatch, no general trusted scope/audit. Route/disable rather than advertise it as safe. |
| `internal/tools/get_server.go`, `resolveServer`; `get_server_test.go` | UUID/exact-name/missing/ambiguous tests; `AllPages`, host/raw fault fields and raw errors require safe replacement on enabled path. |
| `internal/tools/get_flavor.go` | Arbitrary flavor/extra-spec reads not selected capability. Use only derived bounded fields under owner. |
| `internal/tools/get_ports.go`, `get_ports_test.go` | Project/device/response checks and 32-record/four-page ceilings; bound transport/decoding too. |
| `internal/openstackclient/compute.go`, `network.go` | Existing constructors call `AuthOptionsFromEnv`, which consumes ambient variables and supports modes broader than the selected application-credential ID form. The new Go boundary must constrain inputs to the closed environment allowlist; disabled routes must not authenticate. |
| Three automatic `cmd/*/main.go` paths | Agent/workflow/project initialize model/SDK/registry directly. Quarantine diagnostics before side effects; preserve pure config/planning regression seams. |
| `internal/scopedtools/broker.go` | Specialist assignment/budget/reader seam, not global owner; specialists remain disabled. |
| `internal/planning/prepared.go`, `review.go` and tests | Digest/immutable copies/single-start/zero-start/original-goal/exact-name regressions to preserve, not new planning work. |
| `internal/agent/filestore.go`, `internal/project/store.go` | Temp/sync/rename seam, not complete audit/control durability. No investigation schema change. |
| `go.mod`, `Makefile` | Module declares Go `1.27.1`, Gophercloud `v2.14.0`; baseline tests/vet and four-command build succeeded offline. Existing Makefile build was avoided to preserve ignored binaries. Root Makefile is not a credential loader/wrapper. |

Chunk 0 was completed at base `16cfe0ede231df7b90b4f93961a7b6eff16512a1`: verified branch/HEAD, clean worktree and expected hashes for the original ladder/task/ADR/approval record; inspected relevant sources and consumers; no repository files were edited. With `GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off`, focused tests passed: **108 tests across 4 packages**; `go test ./...` passed: **182 tests across 16 packages**; `go vet ./...` passed; race tests passed: **96 tests across 3 packages**. All four existing commands built to `/tmp/aiops-go-chunk0-build.7RXsPF`; `make build` was avoided so pre-existing ignored binaries in `aiops/bin` remained untouched. Temporary build outputs were not cleaned up. No cloud/live service, credential values, protected profiles, Python/legacy asset, formatter, or external dependency operation was used. `.env`/`.env.example` inspection was key-name-only; no `.env` value was displayed or used. These are pre-change discovery results, not verification of the draft amendments or future implementation. Fresh preflight must revalidate source identities and any material drift after exact-candidate approval/commit.

## 5. Requirement-to-chunk coverage

R labels are local tracking labels, not PRD IDs. Task §8 separately maps every FR/NFR/AC including partial acceptance and deferred owners. Every row below is verified again in final Chunk 15.

| ID | Source / required local behavior | Current state | Implement/preserve | Verify / intended evidence |
| --- | --- | --- | --- | --- |
| R1 | G1/G2/G5, task §§2/7: provenance, all-entry/consumer versions and one Go owner | Partial inventory only | 0, 1, 2, 12, 14 | V1/V2/V11; enabled/disabled route matrix, no legacy activation |
| R2 | FR-002/010/023, AM1 safety: immutable policy/context, closed definitions, zero pre-admission auth/bypass | Absent generally | 1, 2, 6 | V1/V2/V3; forged/stale/missing policy gives zero forbidden read |
| R3 | FR-003/011/025: identity, server/fault/derived flavor, exact projected data | Broad/unbounded Go seams | 7, 8 | V4/V9; missing/ambiguous/wrong-scope no unintended target |
| R4 | FR-011/025: authorized network/subnet relationships and separate project summary | Port seam only for Go | 9, 10 | V4/V5; no broad discovery; bounded name search only with its own grant, no project summary from server-only scope |
| R5 | FR-021/022/024/033; NFR-002/012: restricted reader application-credential ID form, trusted process environment, transport/model isolation | Existing constructors consume broad ambient auth | 1, 6, 12, 14 | V3/V10/V11; synthetic ID-form fixtures, endpoint check before credentials, principal/project checks, no dotenv/profile fallback or child canary leakage; live role/expiry proof deferred |
| R6 | FR-008/009/040; NFR-003: collection-time bytes/pages/memory/deadline/retries/concurrency/cancel | Partial ceilings | 5, 6, 7–11 | V5/V8; no post-cancel/exhausted/fault request, safe resource cleanup |
| R7 | FR-027/039; AC-014: exact seven outcomes/target/correlation/time/independent flags/SDK null exit | Not implemented | 3, 5, 11 | V6; closed shapes and status-mapped process exits |
| R8 | FR-028; NFR-004/006: durable intent before first contact, terminal before success, every-request terminal attempt | No general Go audit | 4, 5 | V7; real-filesystem ordered trace and fault injection |
| R9 | FR-028; G3: shared/restart fail closure, no replay, unresolved intent retention, isolated namespace | Absent | 4, 5, 12, 13 | V7/V8/V11; physical independent-process crash/restart/rotation tests |
| R10 | FR-018/029/030; NFR-001/005/012: pre-sink minimization/redaction, no mutation | Broad raw output paths | 1, 2, 3, 6–11, 13 | V2/V9; zero canary/unauthorized dispatch at enabled sinks |
| R11 | FR-001/017/034; AC-018 local: manual catalog/invoke without inference/Python/knowledge | No manual Go command | 11, 13 | V10; compiled CLI against fake API with initialization traps |
| R12 | FR-019, NFR-007/013, FR-037 seed: truthful empty/partial/unavailable and three versioned scenarios | Fixtures reusable, seed missing | 3, 7–11, 13 | V6/V10 expected/actual calls/status/evidence, not root-cause claims |
| R13 | NFR-010/011/014/015; AC-024: versions/manifest/disable-first rollback, preserve planning/data/legacy | Existing seams, unproven | 1, 12, 14, 15 | V11; untouched state, reject incompatible consumer, no flattening/unsafe fallback |
| R14 | FR-041/042, source Step 3: manual/extension/revocation/deployment/denial guidance and full local evidence | Historical docs only | 12, 14, 15 | V11; offline reproduction and operator-owned live prerequisites |

Task §8's deferrals remain: 02 model/agent/nested calls/planning/initial reports; 03 checkpoint/resume/memory/retrieval/export/cumulative recovery budgets; 04 graph/domain/attachments/multi-server/full review; 05 host/MCP; 06 full eval/telemetry; 07 deployed acceptance. No full-product AC pass is claimed from local subsets, especially AC-004/011/012/017/018/021–025. Educational curriculum/non-goals confer no additional capability. Compared with the original ladder, Python transport/SDK-script parity work is replaced explicitly by Go owner/transport/isolation evidence; its safety intent is not omitted.

## 6. Verification catalog and prerequisites

The §4 discovery baseline has run against base `16cfe0ede231df7b90b4f93961a7b6eff16512a1`. The commands below must be repeated as applicable after implementation; those future post-change checks remain planned. Root working directory unless stated. Inspect discovered tests/skips and external effects; a zero-test/mandatory-skip result is not success.

| ID | Working directory / command or procedure | Prerequisites and required evidence |
| --- | --- | --- |
| B0 | Root: `rtk git rev-parse HEAD`, `rtk git status --porcelain=v1 --untracked-files=all`, full staged/unstaged and base-to-candidate source comparisons. | Actual base, source/approval freshness and pre-existing work. |
| G0 | From `aiops/`: `rtk go version`; `rtk go test ./internal/tools ./internal/scopedtools ./internal/planning ./internal/workflow`. | Discovery baseline passed: 108 tests across 4 packages with `GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off`; repeat after implementation. No download/install. |
| G1 | From `aiops/`: `rtk go test ./...`, `rtk go vet ./...`, and build each actual command with explicit `-o` paths outside the repository (do not overwrite ignored `aiops/bin` files). | Discovery baseline passed offline: 182 tests across 16 packages, `go vet ./...`, and all four existing command builds to `/tmp/aiops-go-chunk0-build.7RXsPF`. Repeat after implementation; build the new command when it exists. `make build` is not used because it overwrites pre-existing ignored binaries. |
| GF | From `aiops/`: `rtk go test ./internal/diagnostics -run '<actual-test-pattern>' -count=1`; command tests after CLI exists. | Proposed paths/patterns must first exist and discover intended cases; focused V1–V11, not helper-only claims. |
| GR | From `aiops/`: `rtk go test -race ./internal/tools ./internal/scopedtools ./internal/planning`; add `./internal/diagnostics ./cmd/openstack-diagnostic` once created. | Discovery baseline passed: 96 tests across 3 packages. Repeat for affected packages after implementation; does not replace V8 independent processes. |
| GOFMT | `rtk gofmt -w <actual-changed-go-files>` then verify no formatter delta remains. | Actual paths; syntax/import/symbol checks and focused tests after formatting. |
| OS | Proposed Go tests in AUDIT/control fixtures launched by GF/full suite. | Linux temp directories, real OS locks and independent subprocesses; crash/restart/rotation/write/fsync/corruption failures V7/V8, bounded cleanup. No credentials/cloud. |
| CLI | From `aiops/`: `rtk go test ./cmd/openstack-diagnostic ./internal/diagnostics`; `rtk go build -o bin/openstack-diagnostic ./cmd/openstack-diagnostic`. | Proposed paths after creation; compiled command fixture demonstrates no-model list/invoke with controlled API/owner configuration. No public test override. |
| DOC | Validate local Markdown links/tables/fences/endings, guide commands vs actual help; static manifest metadata/version/default/namespace assertions via Go tests. | No privileged installer/Ansible host evaluation. Document Go auth variable names/provenance without values; no Go credential-file layout. New runtime/control artifact allowlists need applicable approval before use. |
| F0 | Root: `rtk git diff --check`, `rtk git diff --cached --check`; complete recorded-base tracked/staged/unstaged diff and full relevant untracked content review. | Scope, symbol/caller/config consistency, no protected data/secrets/unrelated edits or future stubs. |

No Python/script suite is automatically required for an independent Go path that does not change/call it. If a substantiated retained consumer requires such changes, stop to resolve scope/contract authority and run its actual applicable regression/static/syntax checks with a user-confirmed venv where Python executes. Do not silently waive a selected consumer's tests or introduce Python merely for document QA.

## 7. Engineering choices, estimates and dependencies

The owner approved Go ownership and U4's process-environment-only authentication direction, then selected restricted application credentials. Earlier candidate approval does not transfer to this reconciliation; independent review and applicable exact-candidate approval/commit remain pending and this is not implementation authorization. The candidate uses narrow SDK reads, a Go-owned definition source and isolated Go audit state. Internal package layout, use of the pinned auth helper behind closed checks versus explicit option construction, closed JSON policy schema details, serialization of minimal control state and compliant sequential/conflict-rejecting admission are Level 1 after approval. The owner-selected protected JSON policy file is distinct from the permitted compiled representation for reviewed tool definitions. Demonstrate a closed environment allowlist, trusted launcher, fixed identity/project checks, no Go dotenv or credential-profile fallback, and child-process isolation; CLI input is not its own authority. Do not add a service, new dependency, dotenv/auth-profile parser, credential-file format or relaxed audit retention.

Rough effort for one experienced engineer; **1 engineer-day ≈ 6 focused hours**. Tests/docs/verification included once per chunk; external approval/access waits excluded. Lower/upper ranges assume existing Go dependencies and Linux fixtures/toolchain remain available. The environment-auth direction removes the YAML profile as a Go authentication source; the offline module cache lacked the old `gopkg.in/yaml.v2@v2.4.0` source. The selected separate policy uses closed JSON and the Go standard library, not a YAML parser. The estimates below predate the policy-lifecycle and service HTTP reconciliation; re-estimation at a later authorized planning step is required rather than assuming the added work fits. Effort is not agent runtime/calendar duration.

| Chunk | Goal | Depends on accepted chunks | Hours | State |
| --- | --- | --- | --- | --- |
| 0 | Source/feasibility/consumer discovery and baseline | Separate discovery authorization | 3–5 | Completed at base `16cfe0e`; revalidate exact sources/drift at fresh preflight |
| 1 | Quarantine unsafe automatic diagnostics | 0 and specification gates | 2–4 | Not started |
| 2 | One closed Go owner and denied recording slice | 1 | 4–6 | Not started |
| 3 | Safe seven-status results and sanitizer | 2 | 4–6 | Not started |
| 4 | Secure Go audit filesystem and records | 3 | 5–8 | Not started |
| 5 | Intent/terminal lifecycle and shared restart control | 4 | 6–10 | Not started |
| 6 | Environment-auth and bounded SDK transport | 2–5 | 5–8 | Not started |
| 7 | First useful scoped server UUID read | 6 | 4–6 | Not started |
| 8 | Exact-name and bounded fault/flavor completion | 7 | 4–7 | Not started |
| 9 | Authorized bounded network evidence | 8 | 4–7 | Not started |
| 10 | Separately authorized project summary | 9 | 4–6 | Not started |
| 11 | No-model manual Go CLI | 10 | 4–6 | Not started |
| 12 | Version/consumer/manifest/rollback closure | 11 | 3–5 | Not started |
| 13 | Highest-seam adversarial scenario seeds | 12 | 4–6 | Not started |
| 14 | Manual/operator guide and gap matrix | 13 | 2–3 | Not started |
| 15 | Delivery-wide verification and cleanup | 0–14 | 4–6 | Not started |

**Historical total: 62–99 focused hours, about 10.3–16.5 engineer-days.** This replaced the old 68–108-hour estimate for the different Python-owned design but predates the selected policy lifecycle and service HTTP reconciliation; it is not a current estimate or a promise that Go reduces implementation risk.

## 8. Execution contract — for later authorization only

- Core safety: approved bounded sources, actual verification, complete diff/security review and no weakening of scope/data integrity. A plan status never supplies approval/preflight/execution permission. Re-read current task/ADR/plan/instructions/handoff per chunk; record fingerprints, actual base/worktree and material drift.
- Before code: independent review, applicable approval/commit, fresh preflight at actual base, and explicit execution instruction selecting mode. Separately authorized Chunk 0 discovery can report facts/blockers but cannot silently approve sources or start Chunk 1.
- Default failure budget: **two failed validation attempts for the same current-chunk issue**. Diagnose/fix smallest in-scope defects autonomously; preserve counts across sessions, no infinite repair loop or advancement with known required failure. Classify pre-existing/environment failures separately.
- Mode UNSELECTED. **Single-chunk:** only requested chunk, then stop; ask before creating an unrequested handoff. **Continuous-loop:** explicit authorization and capable coordinator, exactly one chunk per real fresh session; non-final handoff/evidence checked before next dispatch. If real orchestration is unavailable, disclose and offer manual next-session instructions; do not simulate sessions.
- Environment: repo and temporary loopback HTTP/files/process fixtures only. Set offline Go variables in §6 before checks; no dependency/toolchain download, package install, root `.env` loading, protected profile inputs, credential values, or live systems. Go auth tests use synthetic process variables only; no dotenv loader. Python environment prerequisite applies only to actual authorized Python work; no venv has been supplied or assumed.
- Every implementation chunk includes changed-file discovery, formatting/syntax/import/symbol checks, focused behavior tests and applicable full checks, complete staged/unstaged/relevant untracked diff review, functional/integration/security risk, validation gaps and safe rollback. Re-run affected checks after repairs. Common gate applies to every chunk below.
- Rollback disables task-owned new bindings, preserves evidence/fault state and unrelated work; never deletes audit, resets repository work, clears faults or restores ambient/legacy bypass. Future feature defects require an explicit bounded repair in this same plan, not a competing ladder or hidden feature work during final cleanup.
- Evidence defaults to the chunk report; GUIDE holds final sanitized matrix/manifest. Future handoffs, if authorized/required: `docs/handoffs/aiops-go-delivery-01-chunk-<N>-to-<N+1>.md` plus separate next-session instructions. None is created by planning. Include source/base/candidate/mode/policy/failure counts, paths/symbols, actual tests/counts/skips, diff/risks/rollback, blockers and precise next step; never credentials.
- Non-final executor states: `CONTINUABLE`, `BLOCKED`, `INCOMPLETE`; final `READY_FOR_REVIEW` only after all approved scope and mandatory offline verification pass. Independent review/acceptance/commit/merge/deploy remain separate. No automatic next delivery.

## 9. Implementation Ladder: Delivery 1 Go-owned safety boundary

**Common entry/post-work/handoff:** §8 applies to every chunk, including focused validation, complete diff/risk review, bounded repair, mode-specific handoff and mandatory session stop. New runtime paths stay disabled/unreachable until their full controls pass. Stubs must return explicit safe non-success, not fabricated success. Proposed paths/symbol responsibilities are confirmed before use; create callees/contracts before caller wiring.

### Chunk 0: Discovery and baseline

- **Goal / coverage / entry:** discovery-only authorization; confirm R1–R14, G1–G7 source gates and actual base. The prior Chunk 0 completed this against the then-current candidate at `16cfe0ede231df7b90b4f93961a7b6eff16512a1`; §4 records its evidence. This amended ladder still requires exact-candidate governance and fresh preflight before any implementation. Do not implement a feature.
- **Inspect / changes:** complete sources in §2; Go callers/SDK/auth/tests/build; exact proposed packages, policy/credential/consumer/manifest seams. No application changes; report evidence only.
- **Tasks:**
  - [ ] Verify the committed U4 approval record and exact source fingerprints, U1 alternative provenance basis, independent review/ordering and review verdict. Stop before code if unmet; do not amend sources to pass.
  - [x] At the prior base, record HEAD/branch/clean worktree, expected source hashes and implementation/requirements drift; the new amendment candidate still needs fresh source/status verification after approval/commit.
  - [x] Inventory relevant enabled/disabled Go SDK, command, legacy script/runner and host/MCP consumers without executing legacy assets; inspect the pinned Gophercloud auth helper and model-child environment seams.
  - [x] Inspect Go environment-auth inputs without displaying/using `.env` values; record unsupported Gophercloud auth modes, no-Go-dotenv/credential-fallback boundary, offline cache limitation for the old YAML parser path if still required by the parent noncredential policy source, and byte-bounded SDK/OS-lock test approach. No protected profile values were read.
  - [x] Run the offline baseline at `16cfe0e` with `GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off`: focused 108/4 packages, full 182/16, vet pass, race 96/3, and four existing commands built to the unique `/tmp` directory. Preserve existing ignored binaries; no live cloud or Python asset.
  - [ ] At fresh preflight, verify the exact approved amendment/ladder commits and revalidate material code/toolchain/cache drift. No assumed Python prerequisite.
- **Validation / safe state:** read-only inspections and authorized baseline only; no new source. Check generated artifacts/worktree after commands.
- **Risk / rollback / stop:** report unresolved authority/environment/feasibility precisely; no destructive cleanup. Stop with confirmed gates/baseline or BLOCKED, never auto-enter Chunk 1. Handoff only per §8.

### Chunk 1: Quarantine unsafe automatic Go diagnostic paths

- **Goal / requirements / entry:** R1/R2/R5/R10/R13; accepted 0 plus approved superseding sources and preflight.
- **Inspect / files / symbols:** observed `aiops/cmd/openstack-agent/main.go`, `openstack-workflow/main.go`, `openstack-project/main.go` and their tests; narrow early diagnostic guards before model/SDK setup. Six-file cohesive boundary is justified by one repeated bypass across three commands and their regression tests.
- **Tasks:**
  - [ ] Visibly disable noncompliant diagnostic startup before inference, OpenStack environment/auth processing, registry or specialist side effects; preserve pure local/config/planning behavior where independently safe.
  - [ ] Add startup traps/counters proving zero model/auth/SDK dispatch; preserve existing planning/config tests rather than delete them.
- **Excluded / compile-safe state:** no Phase 02 investigation integration, generic lifecycle refactor or broken binary. Existing pure helpers/tests still compile; disabled diagnostic routes return safe limitation.
- **Validation / post-work:** from `aiops/`, `rtk go test ./cmd/openstack-agent ./cmd/openstack-workflow ./cmd/openstack-project`, G0/G1 and GOFMT/F0; V2/V3/V11, counters zero, not just nonzero exit.
- **Risk / repair / rollback / stop:** narrow guard repair only under §8; rollback must not revive unsafe execution. Stop when all three routes reject before credentials/model; escalate broader unrelated lifecycle requirements. §8 handoff/stop.

### Chunk 2: Closed definitions, immutable context and denied request

- **Goal / requirements / entry:** R1/R2/R10; accepted 1. Inspect existing registry/tool/scopedtools interfaces and approved task §4.
- **Files / symbols:** proposed GO `definitions.go`, `boundary.go`, `boundary_test.go`, plus policy-specific source/tests and GUIDE artifact-metadata documentation if materialized. The larger cohesive boundary is justified by the selected policy's security-critical loading/currentness and its negative fixtures; confirm exact names before execution. No parallel registry or new collectors.
- **Tasks:**
  - [ ] Define immutable reviewed three-tool metadata and trusted context/policy intersection. Implement the selected fixed protected noncredential JSON policy and closed standard-library parser, safe path/owner/mode/ancestor checks, independently expected IDs/endpoints and current-policy revalidation, without a 30-day validity requirement. Use synthetic fixtures only; actual policy values/provenance and deployment remain separately gated. Validate required fields/limits/versions/duplicate and unknown keys, invalid or revoked policy and reliable time for required controls before contact.
  - [ ] Add denied/invalid recording-executor vertical slice: zero forbidden auth/read, one terminal attempt through an internal audit seam. Bind copies against caller mutation/drift.
- **Excluded / safe state:** no authentication resolution or positive runtime dispatch yet; the later reader boundary accepts only approved process-environment authentication inputs and has no Go dotenv or profile-credential fallback. Explicit non-success for unavailable controls. Types/callees exist before wiring; no future schemas.
- **Validation / post-work:** GF admission/definitions/policy tests, G1/GOFMT/F0; V1/V2, including wrong types/validators/defaults/extra args/unknown/mutation, unsafe paths and symlinks, untrusted environment/catalog values, IDs/endpoints, no mandatory 30-day policy validity, independently established currentness, stale/revoked/superseded policy replay and rollback after restart, atomic replacement/revocation and context races.
- **Risk / rollback / stop:** validator repairs Level 1; no product normalization/schema changes outside approved task. Roll back only unused disabled owner. Stop at proven negative slice; §8 handoff.

### Chunk 3: Closed outcomes and pre-sink sanitizer

- **Goal / requirements / entry:** R7/R10/R12; accepted 2. Inspect task §5 and existing raw result/error sinks.
- **Files / symbols:** proposed GO `result.go`, `sanitize.go` and corresponding tests. Four files are one result-safety unit; no runtime collector wiring.
- **Tasks:**
  - [ ] Build exact inner/outer `2.0` shapes, all seven status/process exits, SDK null child exit, target/correlation/time and independent redacted/truncated metadata.
  - [ ] Add bounded key/text/PEM/bearer sanitization, strict encoding/serialization and explicit unsafe withholding; test byte/character/depth/work/multibyte boundaries and every status.
- **Excluded / safe state:** no early raw stream/output, silent legacy extension or success stub. New dispatch remains disabled.
- **Validation / post-work:** GF outcome/sanitizer tests, G1/GOFMT/F0; V6/V9 at serializer boundaries, null SDK child exit in all statuses.
- **Risk / rollback / stop:** repair against closed approved contract, never bless raw existing errors. Remove only unused disabled builders to roll back. Stop at complete safe representation matrix; §8 handoff.

### Chunk 4: Secure isolated Go audit files and events

- **Goal / requirements / entry:** R8/R9; accepted 3 and approved G3 namespace. Inspect task §6 and actual file/OS lock semantics.
- **Files / symbols:** proposed AUDIT `audit.go`, `audit_test.go`; safe event builder/append/lock/rotation/path/durability helpers. No general persistence framework.
- **Tasks:**
  - [ ] Implement closed safe intent/terminal event records with fixed local actor/minimum-disclosure scope and internal IDs; no diagnostic identifiers/payload.
  - [ ] Implement real temporary-filesystem safe create/append/revalidation/OS lock/rotation/directory durability, 16 KiB event/1 MiB active/three archives and Go-only namespace; reject unsafe paths/collisions without repair/fallback.
  - [ ] Test permissions/owners/symlinks/non-regular files, concurrency and write/flush/fsync/directory-sync/rotation failures; preserve uncertain writes for subsequent control handling.
- **Excluded / safe state:** production contact still unavailable; no shared Python files, live audit inspection or retrospective replay. File primitives compile and work only on fixtures until lifecycle complete.
- **Validation / post-work:** GF audit, OS/G1/GR/GOFMT/F0; V7 basic durability/real-filesystem evidence.
- **Risk / rollback / stop:** filesystem/metadata bugs in scope; changed path/retention beyond approval escalates. Never delete operational audit as rollback. Stop with secure append/rotation primitives, not a claim of shared healthy admission yet; §8 handoff.

### Chunk 5: Intent publication, shared admission and restart control

- **Goal / requirements / entry:** R6/R7/R8/R9; accepted 4. Inspect approved recovery/budget/order rules and minimal control-artifact manifest obligation.
- **Files / symbols:** GO `boundary.go`, proposed AUDIT `control.go`, `control_test.go`, and initial GUIDE artifact-metadata section if state is materialized. This cohesive four-file boundary keeps the control mechanism, tests and exact metadata together; necessary audit-test edits only for substantiated gaps.
- **Tasks:**
  - [ ] Wire durable intent → recording executor → sanitize → durable terminal → publication; denials/pre-cancel still terminal attempt without intent/contact.
  - [ ] Serialize or finitely reject cross-process admission, shared budgets/cancellation/fault health and policy/definition snapshots; establish bounded lock ordering.
  - [ ] Fail closed across crash/restart, uncertain terminal append/unwriteable control state and unresolved-intent rotation; local safe fault visible without failed sink, trusted recovery only, no replay or duplicate terminal.
  - [ ] Record/check chosen control filenames, schema/bounds and required metadata with this chunk; final manifest consolidation in 12 does not defer the introducing chunk's integrity checks. No installation/live use before applicable final review.
  - [ ] Add independent-process crash/race/partial-write/restart tests and no-deadlock/no-over-admission/remaining-budget checks at this boundary.
- **Excluded / safe state:** no investigation resume/scheduler or real SDK contact. Complete recorders-only lifecycle; runtime collectors still unavailable. Minimal state is current audit control only.
- **Validation / post-work:** GF control/lifecycle, OS/GR/G1/GOFMT/F0; V7/V8, zero contact on failed intent, zero success payload on failed terminal and zero post-fault admission even after fresh process.
- **Risk / rollback / stop:** Level 1 mechanism repair within §8; inability to prove restart closure blocks integration, no availability exception. Rollback disables owner, preserves evidence/control faults. Stop at physical-process publication/recovery proof; §8 handoff.

### Chunk 6: Trusted process-environment authentication and bounded SDK transport

- **Goal / requirements / entry:** R2/R5/R6/R10; accepted 2–5, approved U4 amendment and validated exact environment-input contract.
- **Inspect / files / symbols:** existing `openstackclient` constructors and pinned Gophercloud `AuthOptionsFromEnv`; proposed READER `reader.go`, `reader_test.go` for closed process-environment mapping, authenticated identity/project verification, fixed endpoints and response/request budgeting. GUIDE records accepted variable names and trusted-launcher ownership only, never values or a Go credential-file layout.
- **Tasks:**
  - [ ] Read only `OS_AUTH_URL`, `OS_APPLICATION_CREDENTIAL_ID` and `OS_APPLICATION_CREDENTIAL_SECRET` from the trusted launcher environment. Use the selected SDK application-credential ID form with Keystone v3, implicit project scope and no explicit scope or v2 fallback. Reject missing/malformed inputs and credential-name, username/domain, user-ID, password/passcode, project/tenant, system-scope and token-input conflicts before auth; the helper does not read `OS_TOKEN` but it remains forbidden. Construct explicit options or constrain the helper before it can consume unsupported inputs.
  - [ ] Do not load `.env` in Go or use `clouds.yaml`, `secure.yaml`, or another profile as an authentication source/fallback; do not invoke root Makefile. Keep any separate noncredential policy/configuration source within the parent contract. Add no dotenv/auth-profile parser. No stronger-credential fallback.
  - [ ] Admit and durably record intent before authentication/contact; revalidate the protected current policy before every credential-bearing operation and related lookup. Validate the authentication endpoint against independent approved deployment context before sending credentials. Denied, disabled, missing, malformed, conflicting or unsupported inputs cause zero auth/resource calls. Compare authenticated canonical user/project IDs and expected identity/domain labels where available to trusted policy before SDK reads; mismatch causes zero resource calls, and env/catalog values are never authorization policy. Missing, unsafe, invalid, revoked or incompatibly changed policy or unreliable time for required controls stops subsequent contact without automatic retry/readmission.
  - [ ] Keep region/interface/service endpoints, targets, budgets, capabilities, audit paths and approvals outside ambient auth environment authority. Validate catalog-derived destinations against trusted policy before token-bearing service discovery or resource calls; prevent proxy/redirect/unapproved destination influence. Synthetic fixtures prove the documented Keystone destination and independently policy-authorized service destinations, with no credentials/tokens sent to denied destinations. Neither HTTP exception has an expiry for now; do not impose the previously asserted cutoff or further individual endpoint/route risk approvals within this lab. Verify reliable-time failure for other required controls. Offline fixtures do not establish actual endpoints or management routes; those remain separately authorized live gates. Bound body bytes before SDK decoding, pages/records/memory/request/time/retry/cancel and approved endpoint origins.
  - [ ] Prove no OpenStack auth variable reaches Codex/Pi/model/child processes and no actual credential or synthetic canary reaches arguments, logs, errors, results, audit, reports or model input. Exercise existing Codex/Pi environment filters using synthetic-only fixtures; offline fixtures do not establish effective cloud role or expiry.
- **Excluded / safe state:** no real credential values, live authentication, permissive helper modes, Go dotenv/credential-profile loader, new dependency/broker/credential-file layout, or legacy runtime changes. Any noncredential policy source remains under the parent contract. Collector implementations remain unavailable; fixtures use synthetic environment values and fake/local transports only.
- **Validation / post-work:** GF auth/transport and child-environment tests, GR/G1/GOFMT/F0; V2/V3/V5, unsupported/malformed pre-auth inputs with zero auth/resource calls, authenticated identity/project mismatch with zero resource calls, no dotenv or profile-credential fallback, hostile body/redirect/pagination and cancellation-between-requests counters.
- **Risk / rollback / stop:** if the pinned helper cannot be constrained without weakening the closed allowlist, construct explicit options within approved design discretion; no ambient or profile-credential fallback. Rollback disables binding without touching legacy profile data. Stop unless trusted-launcher provenance, no-dotenv behavior, identity/project checks, bounded transport and model isolation are proven; §8 handoff.

### Chunk 7: First useful authorized server UUID read

- **Goal / requirements / entry:** R3/R6/R10/R12; accepted 6. Inspect existing get-server HTTP fixtures and approved projection.
- **Files / symbols:** proposed READER `server.go`, `server_test.go`; fixed UUID server collector bound to owner lifecycle, not public raw SDK tool.
- **Tasks:**
  - [ ] Implement one authorized UUID GET with response identity/project checks, finite transport/collection bounds and selected safe server projection.
  - [ ] Exercise actual owner→SDK→audit→result with healthy, permission-denied, mismatched/oversized/hostile response fixtures and exact call ordering. Leave unsupported extensions explicitly unavailable/partial, never claim full basics completion yet.
- **Excluded / safe state:** no arbitrary name/flavor/host/config read. Network/summary remain unavailable; definition-bound registration only when this path's controls work.
- **Validation / post-work:** GF server UUID/lifecycle, G0/G1/GOFMT/F0; V4/V5/V7/V9/V10, useful bounded data and no raw faults/host leakage.
- **Risk / rollback / stop:** repair projection/scope only; unsafe response blocks downstream work. Disable binding for rollback, preserve records. Stop at first useful safe UUID tracer; §8 handoff.

### Chunk 8: Exact-name resolution and bounded fault/flavor completion

- **Goal / requirements / entry:** R3/R6/R10/R12; accepted 7. Inspect old exact-name/flavor seams/tests and task §4.3.
- **Files / symbols:** READER server source/tests; bounded authorized exact-name resolver and observation-derived flavor projection. No standalone public flavor capability.
- **Tasks:**
  - [ ] Add separately granted and disclosed exact-name resolution under intent/budgets, bounded pages/responses and exact matching. An explicitly granted search is limited to the fixed project and may receive limited metadata for servers outside the permitted-ID list: minimize it, reject missing/ambiguous/deceptive matches, and perform no further reads unless the resolved ID is approved. Without the grant require a UUID and make no name search. Retain original/resolved identities and UUID guidance.
  - [ ] Add absent-fault null/safe fault code/message and fixed derived flavor fields, verify IDs/visibility, return explicit unavailable/partial for missing linkage/detail; never enumerate flavors, fetch extra specs or publish raw details.
  - [ ] Test forged flavor, cross-project/mismatched server, huge name pages, casing/substrings/script-incompatible input and secret messages with API counters.
- **Excluded / safe state:** no name normalization/uniqueness invention, project summary or host access. Basics complete only when every required positive/negative case passes.
- **Validation / post-work:** GF server identity/fault/flavor, existing `rtk go test ./internal/tools`, G1/GOFMT/F0; V4/V5/V9/V10.
- **Risk / rollback / stop:** relationship/identity code fixes in scope; a new visibility grant escalates. Disable extension only for rollback without evidence rewriting. Stop at full bounded basics capability; §8 handoff.

### Chunk 9: Authorized server network evidence

- **Goal / requirements / entry:** R4/R6/R10/R12; accepted 8. Inspect bounded ports seam and task projections/visibility rules.
- **Files / symbols:** proposed READER `network.go`, `network_test.go`; fixed attached-port/network/subnet collection under same owner, plus binding if needed.
- **Tasks:**
  - [ ] Establish permitted server first, derive attached ports with project/device/response checks and validate every network/subnet link/visibility before lookup.
  - [ ] Bound records/pages/deduplicated derived reads/body bytes/aggregate memory/deadline/cancel, preserve tighter port ceilings and explicit empty/partial limitations.
  - [ ] Test forged/mismatched/shared visibility, missing detail, endless/malicious pages and denied subsequent reads. No broad topology or fallback.
- **Excluded / safe state:** no metadata/host diagnosis or new shared-resource authority. Summary remains unavailable.
- **Validation / post-work:** GF network, existing ports tests, G1/GOFMT/F0; V4/V5/V9, positive provenance and zero forbidden downstream lookups.
- **Risk / rollback / stop:** unreviewed visibility needs escalation, not guessing. Disable network binding to roll back. Stop at complete scoped network fixtures; §8 handoff.

### Chunk 10: Separately permitted project summaries

- **Goal / requirements / entry:** R4/R6/R10/R12; accepted 9. Inspect task seven-section field/limit contract and existing SDK APIs.
- **Files / symbols:** proposed READER `summary.go`, `summary_test.go`; fixed seven-section collector and its owner binding.
- **Tasks:**
  - [ ] Require explicit current project-wide permission distinct from server assignment; absent a separately granted bounded name-resolution search, a server-only request performs zero project lists. A name-resolution grant never grants a project summary.
  - [ ] Collect seven selected-field sections with bounds during transport/decoding; distinguish true empty/independent partial/fatal auth/config, no stronger profile/retry/attachment traversal.
  - [ ] Test oversized pages/bytes, unavailable services, cancellation and fatal early-stop with exact request counts and aggregate-output bounds.
- **Excluded / safe state:** no cross-project list, new resource family or domain workflow. Exactly three tools enabled only through complete owner controls.
- **Validation / post-work:** GF summary, G1/GOFMT/F0; V4/V5/V9/V10, useful summary or honest bounded limitation.
- **Risk / rollback / stop:** fix selected operation/projection only; unsupported API/dependency escalates. Disable summary binding for rollback. Stop at all three catalog fixtures; §8 handoff.

### Chunk 11: Model-independent catalog/invoke Go command

- **Goal / requirements / entry:** R6/R7/R10/R11/R12; accepted 10. Inspect command conventions, protected context loading, owner catalog and `aiops/Makefile`.
- **Files / symbols:** proposed CLI pair plus observed `aiops/Makefile`; three files are one command/build/test unit. Public naming/flags are Level 1 within task; no caller path/profile/policy authority.
- **Tasks:**
  - [ ] Wire owner-derived list/invoke with requested scope intersected with trusted policy and finite limits; no model/provider/knowledge/store/specialist initialization. Listing is metadata-only, no API/auth or fabricated diagnostic audit event, and marks blocked controls/capabilities honestly.
  - [ ] Emit exact safe versioned result/process mapping and identity/unavailable/denial guidance, no raw input/reflected errors or duplicate adapter audit/retry/fallback.
  - [ ] Build actual CLI fixtures against controlled owner/API, all seven statuses, malformed/unsupported/trailing JSON and unknown/mutation/override inputs; verify initialization traps and owned subprocess cleanup/cancellation.
- **Excluded / safe state:** no automatic investigation/approval/resume wiring. Existing unsafe commands stay disabled, live entry remains gated even though binary builds.
- **Validation / post-work:** CLI/G1/GR/GOFMT/F0; V2/V5/V6/V9/V10 at compiled subprocess seam, zero inference/Python initialization or authentication processing for metadata-only listing.
- **Risk / rollback / stop:** command-only repairs; context-integrity issue escalates without public JSON authority. Rollback removes new command binding but retains old guards. Stop at useful no-model list/invoke; §8 handoff.

### Chunk 12: Consumers, exact deployment manifest and safe rollback

- **Goal / requirements / entry:** R1/R5/R9/R13/R14; accepted 11. Inspect consumer matrix, G3/G5/G6 and actual artifact choices.
- **Files / symbols:** GO `compatibility_test.go` (proposed), GUIDE manifest/matrix sections; necessary private version/inspection helpers only when a retained consumer needs them. No general migration/installer.
- **Tasks:**
  - [ ] Enumerate explicit Go/legacy consumers and enabled versions; reject unsupported selection, no inferred `2.0` compatibility, legacy output flattening or in-place record conversion.
  - [ ] Document exact binary/policy/definition/control artifacts, paths, ownership/modes, Go-only audit namespace and disabled-live prerequisites; record accepted Go auth variable names and trusted-launcher responsibility without values. Test static source/manifest assertions. No credential-file format/dependency becomes approved merely by listing it.
  - [ ] Exercise synthetic disable-first rollback, bounded active-work cleanup, preserved intents/events/faults/legacy state and no ambient/Python fallback. Isolated inspection must not append to or reinterpret Python control state.
- **Excluded / safe state:** no legacy runtime/source/roles/host/MCP consumer changes, provisioning or audit inspection of real data. If required, substantiate and resolve scope first.
- **Validation / post-work:** GF compatibility, G1/GR/DOC/F0; V3/V6/V11 and preserved planning regressions.
- **Risk / rollback / stop:** unapproved consumer contract change blocks dependent integration, not triggers migration work. Rollback leaves new path disabled/evidence preserved. Stop at explicit compatibility/manifest/rollback proof; §8 handoff.

### Chunk 13: Full-boundary adversarial scenario seeds

- **Goal / requirements / entry:** R9/R10/R11/R12; accepted 12. Inspect V1–V11 coverage already added; tests are not postponed until this chunk.
- **Files / symbols:** proposed GO `scenarios_test.go`, synthetic versioned `testdata/manual-diagnostics/`; extend existing tests only for substantiated current-scope coverage gaps.
- **Tasks:**
  - [ ] Seed healthy server, permission denial and hostile-output expected/actual calls/targets/status/evidence/limitation/safety records with source/version identity.
  - [ ] Exercise actual CLI→owner→controlled API→audit lifecycle, including no-model/Python/host/MCP traps, mutation insistence and multi-chunk/multibyte/depth/work-limit canaries at every enabled sink.
  - [ ] Repeat shared fault/crash/restart/rotation/cancel behavior at highest practical command seam; enumerate and close all current V1–V11 gaps without new features.
- **Excluded / safe state:** no full eval metrics/corpus/rubric or diagnosis/model campaign. Fixtures use only synthetic data and internal hooks.
- **Validation / post-work:** GF scenarios plus CLI/OS/G1/GR/GOFMT/F0; V8/V9/V10, exact expected/actual sequence/discovery/no leaks/orphans.
- **Risk / rollback / stop:** regression defects repaired under §8, never weaken assertions; feature defects require bounded repair entry in this plan. Roll back only synthetic artifacts. Stop at three complete deterministic scenario seeds; §8 handoff.

### Chunk 14: Manual, extension and owner guidance

- **Goal / requirements / entry:** R1/R13/R14; accepted 13. Inspect actual help/build/limits/version/matrix/manifest and task guidance requirements.
- **Files / symbols:** GUIDE only; no source-contract/PRD/roadmap checkbox changes.
- **Tasks:**
  - [ ] Document exact implemented no-model list/invoke, safe offline fixture reproduction, all enabled/disabled routes/versions, identity guidance, budgets, partial/unavailable and incomplete-audit recovery.
  - [ ] Complete sanitized entry/consumer/provenance matrix and deployment manifest, significant Level 1 choices, extension review, version/disable-first rollback and no replay.
  - [ ] Describe fixed placement/control-artifact metadata, Go process-environment auth names and trusted-launcher boundary (no secret values or `.env` path), dedicated reader identity, one-month rotation/revocation/admin ownership and live deployment gate. Operator-only disposable create/update/delete denial needs conclusive authorization signature plus independent admin no-change postconditions/cleanup owner; unexpected mutation means stop/revoke, never an agent probe/tool.
- **Excluded / safe state:** no live command execution/deployment recipe that silently enables access; no private env path or sensitive topology/evidence.
- **Validation / post-work:** DOC/CLI documented offline reproduction and F0, V11. Read through guide ending, compare commands with real help and fixture behavior.
- **Risk / rollback / stop:** documentation corrections only; behavior defects use explicit bounded repair. Rollback guide-only; stop with accurate reproducible guidance and live gaps, §8 handoff.

### Chunk 15: Delivery-wide verification and cleanup

- **Goal / requirements / entry:** R1–R14; all accepted 0–14, source/approval drift revalidated. No new feature.
- **Inspect / files:** entire implementation-base delta, enabled/disabled entry points/SDK consumers, artifacts and full untracked contents. Only task-created accidental-artifact cleanup/docs corrections planned.
- **Tasks:**
  - [ ] Run complete G1, GR on affected concurrency packages, GOFMT and all mandatory V1–V11/OS/CLI/DOC cases. Check suite discovery/skips/tool versions, new command builds and no implicit download/network.
  - [ ] Repeat documented manual fixture demo, no-model traps, response/process cleanup, real multiprocess crash/restart/intent/terminal/rotation failure and rollback evidence. Do not label offline evidence deployed acceptance.
  - [ ] Compare each R row/task §8 subset to actual evidence; reject unsafe stubs, hidden raw SDK/auth/Python fallback, generic capability, future module or unreviewed contract change.
  - [ ] Inspect full base-to-candidate plus staged/unstaged/untracked diff; preserve unrelated work/legacy/state/events/control faults; remove only proven task-created accidental files, no reset/clean.
  - [ ] Rerun affected verification after cleanup/repair; report source/base/candidate/worktree, choices, actual commands/results/counts/skips, local/deferred coverage, demo/lifecycle evidence, risks and live gates.
- **Validation / post-work:** full mandatory catalog and F0/security/source audit; any required unrun/failed check prevents READY_FOR_REVIEW. A discovered feature defect goes to a bounded named repair in this same plan before repeating this final gate.
- **Risk / rollback / stop:** preserve evidence/disable new path rather than erase uncertainty or revive bypass. No next-delivery handoff. Final execution status per §8; stop for independent fresh-session review, no merge/deploy.

## 10. Final acceptance and evidence obligations

- [ ] Approved committed superseding ADR/task/plan/source identities, actual implementation base and exact candidate/worktree are recorded; no stale gate reuse.
- [ ] Exactly three Go manual diagnostics are useful or honestly limited without model/Python/knowledge; every enabled local route uses one actual owner, disabled routes do not authenticate as side effect.
- [ ] Identity/related visibility/dedicated reader/finite collection/cancel and no-mutation/no-secret obligations pass at real command/API seams.
- [ ] Exact seven-status result, independent flags/identity/correlation and minimum-disclosure intent/terminal durability/cardinality pass; no success before required persistence.
- [ ] Real OS/process/shared/restart/crash/rotation/control failure evidence proves no replay, orphan, fallback sink, post-fault admission or Python-audit interference.
- [ ] Three scenario seeds, complete matrix/manifest, compatible version gating, evidence-preserving rollback and reproducible manual/extension/owner guidance exist.
- [ ] All mandatory Go tests/build/vet/affected race checks and V1–V11 ran successfully; discovery/skip/failure/not-run evidence and separate live limitations are explicit.
- [ ] Full diff/security audit shows no unrelated work, future scaffold, source weakening, legacy/data rewrite or secret/private `.env`/profile/raw operational evidence. Independent acceptance remains separate.

## 11. Risks and exact escalation boundaries

| Risk | Evidence / remaining work | Action / authority |
| --- | --- | --- |
| Independent review pending | U4 approved earlier bytes; the later owner decisions do not approve this revised candidate or waive review and approval. | Obtain a fresh independent review and applicable approval/commit of exact revised bytes before separate preflight and named offline implementation authorization. Real policy-value/route evidence is a separate live gate and need not be established before this review. Do not edit old approvals to manufacture readiness. |
| Environment-auth boundary | Existing Go calls broad `AuthOptionsFromEnv`; the SDK can select conflicting password/passcode modes and supports additional application-credential forms. Trusted-launcher provenance and child isolation need implementation tests. | Chunk 6 must prove the ID-form closed allowlist, endpoint validation before credentials, principal/project verification, implicit scope, no fallback, zero denied auth and zero resource reads on mismatch. No Go `.env` loader or new parser dependency. |
| Trusted noncredential policy | The owner confirmed the fixed protected JSON policy, independent expected canonical user/project IDs and endpoint grants, and rejected the 30-day policy-validity limit for this MVP PRD/story. Administrative provenance of real values, an actual artifact and deployed currentness remain unverified. | Keep live access disabled until independent administrative provenance and applicable deployment/live gates are satisfied. These facts do not block independent review or, after candidate approval/commit, fresh preflight and separately authorized offline implementation with synthetic fixtures. Proposed path `/opt/openstack-ai-ops-assistant/policy/diagnostics.json`; directory `root:aiops_assistant` `0750`, regular non-symlink file `root:aiops_assistant` `0640`; runtime cannot modify/replace it. Revalidate before each credential-bearing operation/related lookup; independently establish currentness and prevent stale or revoked policy replay after restart. Invalid or revoked policy fails closed. Do not impose a 30-day validity limit or infer another mandatory period; retain reliable time for required controls. No new parser/dependency or environment-derived authority. |
| Keystone and service transport | The owner accepted credential exposure on the documented Keystone path and, as risk owner, separately accepted service HTTP for all deliveries in this lab until another PRD/story addresses it, without further individual endpoint or route approvals. No HTTPS is configured according to the owner; actual endpoints/routes remain unverified. | Neither exception expires for now. The Go Delivery 1 implementation retains the documented Keystone destination and independent service destination policy, proxy/redirect restrictions and live gate. HTTP permits interception, impersonation and response manipulation; origin and identity checks do not authenticate an HTTP peer. The broader risk decision does not itself amend legacy contracts or authorize routes, deployment or live use. |
| Cross-process crash durability | Existing FileStore and broker mutex are insufficient proof. | Chunks 4/5 require physical OS/file/process failures. Retention/path/availability tradeoff changes require approval. |
| Legacy coexistence/consumer confusion | Same runtime root but separate Go audit; schema version alone does not identify producer/compatibility. | Exact manifest/consumer configuration and rejection tests in 12; no shared append/rotation/control or automatic adapters. |
| Collection/transport escape | AllPages/raw outputs and unbounded decoding; SDK links/redirects may change destination. | Chunk 6–10 response-byte/origin and relationship tests; no silent broad reads/token forwarding. |
| Toolchain/cache/race environment | Offline baseline passed at `16cfe0e` for tests/vet/race/four existing builds; future new-package coverage remains untested. | Revalidate at fresh preflight and run required checks after implementation; missing required checks BLOCKED, no auto-download/install/downgrade. |
| Current live policy unknown | Historical reader/placement acceptance not proof of current Go deployment. | Keep live disabled until owner-authorized Phase 07/equivalent; guide lists exact proof/cleanup/revocation ownership. |

Ordinary engineering difficulty stays Level 0/1. A genuine escalation includes category, exact evidence/problem, alternatives/tradeoffs, recommendation, precise authorization and independent safe remaining work. The user's alternative publication-review determination is recorded; do not repeatedly demand missing unchanged historical candidates or reopen unchanged historical approvals by default.

## 12. Suggested later execution prompt

This prompt is **not executed**. The revised candidate remains proposed; independent fresh-session review and applicable exact-candidate approval/commit remain required before preflight or implementation. Unverified real deployment values/routes remain a separate live-use gate, not a prerequisite for that review:

```text
In a separate fresh session independently review the exact revised U4 amendments and ladder, including whether offline synthetic implementation can safely proceed while real policy-value provenance and endpoint/route evidence remain live-use gates. Stop after reporting findings; do not run implementation preflight or implement in this review session. Applicable exact-candidate approval and commitment remain necessary; a later separate session must perform fresh preflight and implementation still requires separate explicit chunk authorization.
Controlling ladder: docs/aiops-go/delivery/01-safety-boundary-and-manual-slice-delivery.md
Task/ADR amendments:
  docs/aiops-go/tasks/01-go-owned-safety-boundary-env-auth-amendment.md
  docs/aiops-go/architecture/01-go-owned-safety-boundary-env-auth-amendment.md
Original accepted task/ADR remain unchanged and linked from those amendments.
Perform fresh preflight against exact approved commits and actual base/status;
revalidate U1 provenance, independent review/order evidence and material drift.
Chunk 0's offline baseline was completed at 16cfe0e; reuse only if fresh preflight
confirms no relevant drift. Do not start implementation unless separately authorized
for a named chunk. If a gate is unmet, report the exact blocker; do not silently amend
sources, reuse old approvals for changed architecture, or recover missing blobs by guesswork.
No `.env`/profile values or dotenv loading, live/credential/host/provider operation,
installation, root Makefile, legacy runtime execution, commit or later delivery.
Ask before an unrequested handoff.
```

**End of revised candidate plan. PLAN_BLOCKED for implementation: the prior candidate was committed at `84e921f1`, but these revised working-tree bytes are proposed and not approved or committed; independent review, applicable exact-candidate approval/commit, fresh preflight and separate named-chunk authorization remain required. Real policy-value provenance and service endpoint/route evidence remain unverified live-use gates, not prerequisites for independent review or synthetic offline implementation. Chunk 0 discovery/offline baseline was completed against the prior candidate at `16cfe0ede231df7b90b4f93961a7b6eff16512a1`; it is not review, fresh preflight, or implementation authorization.**
