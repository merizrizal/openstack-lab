# DRAFT ADR — Delivery 1 Go-owned diagnostic safety boundary

**Status:** Proposed superseding architecture, not approved for implementation.

**Scope:** Go Delivery 1 only, [source Phase 01](../implementation-plan/01-safety-boundary-and-manual-slice.md) Steps 1–3 and §01.6. [Superseding draft task](../tasks/01-go-owned-safety-boundary-task.md). The [existing delivery document](../delivery/01-safety-boundary-and-manual-slice-delivery.md) remains the sole execution ladder; this ADR contains none.

**Authoring base:** `0015097ff8cd73d80cf04e38c0f088f18e48b384`, branch `aiops-go-phase01`, initially clean, no staged or untracked work. This is the inspected code/documentation base, not an accepted implementation. The Phase 01 requirements baseline remains `0182da9f7c2b322df5da49262748974009db7332`.

## 1. Decision record and source authority

The following U labels are local provenance labels, not pre-existing approved decision IDs. Exact statements are from this authoring conversation; no timestamp, signature or original historical transcript is inferred.

| Label | User statement / bounded meaning | What it does not authorize |
| --- | --- | --- |
| U1 | In response to accepting review of the current committed addendum and three affected contracts instead of recovering the missing historical candidates: `1. Yes, I explicitly accept`. | Does not recover or compare the historical blobs, provide an independent review, approve a new architecture, or authorize implementation. |
| U2 | `2. I choose B`, referring to “Reassess the architecture for a Go-owned safety boundary, using the revised documentation as reference rather than automatically binding”. | Authorizes reassessment of ownership, not automatic approval of this design or weakening of safety requirements. |
| U3 | `Please Proceed with the recomennded step`, following the recommendation to prepare a superseding Go-owned architecture proposal, bounded task revision and reconcile the sole delivery plan. | Documentation authoring only; no implementation, independent review, preflight, commit or deployment. |

U1 identifies the candidate at `0015097…`: addendum blob `d415d14414e6887fa71b3a9dea04520e9f88f4d1`; toolbox `3062e3b4b9fca362ea3d51decb8637dd8ad1b396`; runner Steps 1–4 `993d8542232e92b0f3f81ae3957e0064f83b3900`; runner Steps 5–7 `761faeb7e01e0348f8b08087af9f5ec503591079`. The missing addendum blobs `6e4133306162418d35d131cf2b8be9e0d41b9643` and `50d590524602fe45f9a1a65f2c16b79cda96859c` remain unavailable locally. U1 supplies the requested owner determination on the alternative review basis, not equivalent historical comparison evidence.

The [committed addendum](../../ai-ops-revised/runtime/go-phase01-versioned-diagnostic-amendments.md) records prior AM1–AM5, incorporation and whole-document approvals and the bounded Q1–Q3 owner attestation. The [prior ADR](01-safety-boundary-and-manual-slice-adr.md), blob `ff53a9fe28359592494e637a7f8e16186b8bddb0`, and [prior task](../tasks/01-safety-boundary-and-manual-slice-task.md), blob `04991e450d6659eeffc69f660749fb8b27700d65`, are preserved unchanged. Their approval is historical evidence, not approval of this replacement. The original delivery blob `ffb89dc6d69a9bc051d11acf9fb0de1261affa4b` remains retrievable at the authoring base; no execution progress was recorded there.

**Proposed authority after review/approval:** the [Go PRD](../prd.md) and bounded owner decisions govern product behavior; this ADR and its task would govern Go Delivery 1. Revised-runtime documents become explicit reference/compatibility inputs for this Go-owned path, not an implicit Python execution dependency. They remain authoritative for their own legacy/revised runtimes. Neither this draft nor U2 retroactively amends those runtimes, later phases, or PRD/source-plan headers.

The source Phase 01 reconciliation currently retains revised-runner constraints. This ADR proposes an explicit, narrow exception to that reconciliation for Go Delivery 1 ownership, definitions, audit namespace and verification routing as enumerated in §3. Until the supersession is independently reviewed, approved and committed, the old reconciliation is not silently bypassed. Existing live/deployment restrictions continue throughout.

## 2. Existing system and rationale

The user prefers development in Go using `aiops/` and `docs/aiops-go/`. The following engineering rationale is this author's analysis, not a quotation of stakeholder rationale: keeping authorization, narrow SDK collection, outcomes and audit lifecycle in one Go owner avoids a second policy owner and Go-to-Python trusted-context transport. It does not eliminate the need for credential isolation, durable audit, response bounds or compatibility proof.

| Inspected implementation | Reusable seam | Required correction or limitation |
| --- | --- | --- |
| `aiops/internal/tools/registry.go`, `Registry.Execute` | Named dispatch, duplicate/unknown name rejection. | No application-owned scope, general limits or durable audit. Not the new security boundary merely by renaming it. |
| `aiops/internal/tools/get_server.go`, `resolveServer` | UUID/exact-name intent and missing/ambiguous rejection; HTTP tests. | `AllPages`, host/raw fault details and raw errors are not safe enabled behavior. |
| `aiops/internal/tools/get_flavor.go` | Gophercloud flavor projection seam. | Caller-selected flavor, extra specs and raw error strings cannot remain a public route. |
| `aiops/internal/tools/get_ports.go` | Project/device-filtered reads, response checks, 32-record/four-page ceilings and fixtures. | Bounds/checks must apply before buffering/decoding and at the common owner; preserve tighter applicable ceilings. |
| `aiops/internal/openstackclient/compute.go`, `network.go` | Existing Gophercloud client construction. | `AuthOptionsFromEnv` is not the dedicated credential contract. Do not authenticate before rejecting an unsafe/disabled route. |
| `aiops/internal/scopedtools/broker.go` | Assignment checks, reader function fixtures, shared in-process budget. | Specialist-specific, no general cloud/profile/audit or cross-process fault control. Do not activate specialists. |
| `aiops/cmd/openstack-agent`, `openstack-workflow`, `openstack-project` | Existing command and configuration tests. | Diagnostic startup constructs model/ambient SDK clients. Quarantine before either side effect; no new investigations here. |
| `aiops/internal/planning/prepared.go`, `review.go` | Exact digest, immutable copies, single-start, declined/non-ready zero-start behavior. | Preserve by regression; do not rebuild planning now. |
| `aiops/internal/agent/filestore.go`, `internal/project/store.go` | Temp-file, file sync and rename patterns. | Not an audit journal, cross-process writer exclusion or proof of directory durability. Investigation recovery remains Phase 03. |

`aiops/go.mod` declares Go `1.27.1` and Gophercloud v2 `v2.14.0`. No toolchain execution or dependency-cache validation occurred. The inspected Go sources and requirements have no Git delta from the bounded requirements baseline to authoring HEAD. Their presence is not acceptance evidence.

## 3. Proposed supersession and compatibility ledger

G labels are draft design labels, not approved decisions. Approval of the replacement must assess these deltas explicitly; unchanged safety content need not be reflexively reapproved as though U1 had reopened it.

| Design | Prior position | Proposed Go Delivery 1 position / preserved guarantee |
| --- | --- | --- |
| G1 — owner | Q2/AM1 selects conditional revised Python runner ownership. | Go owns definitions, authorization, fixed SDK calls, limits, sanitization and audit lifecycle. U2 permits proposing this replacement; it is not a fallback activated by a Python feasibility failure. No Python runner in the new call path and no second permissive registry. |
| G2 — definitions and catalog | AM1 versioned registry and script/SDK views; seven maintained revised tools. | One Go-owned reviewed definition source; compiled immutable metadata or protected closed data is Level 1. Expose exactly `server_basic_info`, `server_network_info`, `project_resource_summary`. Preserve legacy seven-tool assets untouched; do not translate them into Go host tools. Public arguments and AM2 bounded selected projections stay unchanged. |
| G3 — audit namespace | AM4 extends the shared revised `audit/tool-runner.jsonl` and lock. | Propose separate fixed `/opt/openstack-ai-ops-assistant/audit/go/`, with `tool-runner.jsonl`, `.tool-runner.lock`, `.1`–`.3` archives. Same restrictive metadata, size limits, OS lock/durability and unresolved-intent protection. Never share append, rotation, admission or control state with Python. This exact new subdirectory is a proposal requiring approval; no creation is authorized here. |
| G4 — versions | AM3/AM4 result/audit `2.0`, seven statuses and intent/terminal. | Retain the closed shapes and status/exit meanings, minimum disclosure and durability in the new task. For an in-process SDK read `exit_code` is null; process exit remains status-mapped. Go provenance is the configured implementation identity, never inferred from schema version alone. |
| G5 — retained consumers | AM5 upgrades or gates retained revised callers and inspectors. | No Go path implicitly feeds an old inspector/MCP/host adapter. Inventory consumers, reject incompatible versions and preserve old records. Output-only legacy translation is not required unless a specific retained consumer is selected and reviewed; never flatten events or claim parity from matching JSON. |
| G6 — deployment/credentials | Revised fixed paths, profile and metadata; role allowlists. | Retain observer `assistant02`, group `ai_ops_assistant`, user/group `aiops_assistant`, root `/opt/openstack-ai-ops-assistant`, fresh `aiops-assistant-project-reader`, `admin` project label, `default` domain, reader-only role, month expiry and admin-team rotation/revocation. Propose Go artifacts separately in a reviewed deployment manifest; do not edit the Python roles or reuse their allowlist as installation authority. |
| G7 — validation | Python/Go/script parity suites mandatory for revised integration. | Mandatory Go behavior and real OS/filesystem tests for the Go path; unaffected Python runtime tests are not prerequisites for a path that neither invokes nor changes it. Any actually changed/reused legacy component triggers its own contract and regression gates. No system-Python fallback; a user-confirmed venv is required only if authorized Python work is needed. |

This is not a request to discard AM1–AM5 wholesale. AM1 ownership/transport and AM4 path-sharing change; AM2 projections, AM3 outcomes and AM4 integrity are retained in Go terms. AM5 retains no-rewrite/no-replay/disable-first behavior while limiting compatibility to explicit consumers. The task spells out the full Go obligations rather than requiring an executor to guess which historical clauses apply.

## 4. Architecture and trust boundary

```text
manual Go command (no model)
  -> one Go owner: protected current policy + reviewed definitions
  -> validate request; intersect requested scope with policy
  -> shared healthy admission + finite budgets
  -> durable intent before first credential-bearing/authentication/observation operation
  -> fixed bounded SDK reads + identity/relationship checks
  -> minimize and sanitize
  -> durable terminal event
  -> one closed result + status-mapped process exit
```

Public tool arguments, CLI actor strings, environment variables, model output and resource relationships do not create authority. Operator input can request a narrower scope, never expand protected policy. Current policy establishes cloud, project, targets/allowed resolution, capability/profile set, policy identity and budgets. Invalid or disabled commands reject before client construction/authentication. Owner internals do not return credential-bearing SDK handles to callers.

**Credential-loading feasibility is unverified.** Retain the protected profile directory/files and dedicated identity. A future Go loader must acquire only the fixed reviewed profile through an explicit trusted configuration path, check safe metadata, never merge ambient `OS_*`, proxy or provider settings, and never expose secrets in argv, errors, output, audit or test artifacts. Runtime loading is not permission for an authoring agent to inspect real profile contents. No new parser dependency, credential file format, broker service or infrastructure is approved by this ADR. If safe loading of the existing format is impossible with permitted dependencies, escalate the specific dependency or format proposal before implementation; do not invent a permissive YAML parser or credential fallback. Synthetic fixtures must prove loading and revocation behavior before real use.

Linux/local single-operator execution is the initial target. Shared admission may serialize or reject contention; it must coordinate separate CLI processes and survive restart. Go standard-library OS/syscall facilities may implement the retained exclusive-file-lock semantics; no general database, queue, service or distributed lock is introduced.

The threat boundary includes all supported application/client/diagnostic entry points and untrusted content, not a promise to withstand root or arbitrary code execution as the trusted credential-owning account. Model runtimes must never run with that account's credential/control access. No model is initialized in this delivery; Phase 02/07 must prove effective process/OS isolation before enabling model-dependent diagnostics. A facade around still-enabled raw SDK commands is not compliant.

## 5. Safety, consistency and data preservation

- Every authorized observation, including resolution, is bounded and disclosed. Scope/name checks are not authority to enumerate a whole project. Exact names retain casing and original input; no invented name uniqueness or permissive script normalization. Ambiguous/missing matches never pick an arbitrary server.
- Require authorized observation-derived flavor and network relationships. Server assignment does not grant project summaries, unrelated topology, volume/attachment traversal or host visibility. No raw fault details, extra specs, user-data or configuration dumps.
- Budgets cover response bytes before SDK decoding, pages/records, requests/retries, memory, elapsed time, concurrent work and complete output. Follow only approved endpoint/pagination destinations; cross-origin links/redirects cannot exfiltrate a token or become discovery authority. Token issuance is the narrowly required authentication operation, not permission for cloud mutation.
- Persist one sanitized intent before possible contact and attempt one terminal event for every request, including denials. At most one committed terminal per request; no duplicate adapter audit. Correlation/time are internally generated. No successful payload precedes terminal durability.
- Required audit/control faults stop admission across callers/restart, preserve intent/evidence and expose safe local uncertainty independent of the failed sink. No replay, automatic audit repair, fallback sink or audit deletion. Protect unresolved intents even when rotation must stop for availability.
- Keep file/path/owner/mode checks and bounded append/rotation under a shared OS lock. File/directory creation, rename and control-state updates need appropriate durable ordering, not file `Sync` alone. Real process/crash tests are mandatory.
- Sanitization/minimization precedes every enabled sink. Cancellation stops subsequent SDK requests, closes bounded response resources and never publishes healthy success; any owned fixture/helper process must also be reaped. A pure in-process collector adds no production subprocess obligation by pretending one exists.
- Preserve original Go state, planning, IDs, timestamps and legacy audit. There is no ACID transaction spanning an OpenStack read and local persistence; require truthful uncertainty, not exactly-once claims. No database or investigation-state migration is added.

## 6. Alternatives and implementation latitude

**Selected proposal:** Go-owned narrow SDK boundary. Reuse inspected Gophercloud/test seams and preserve observable requirements; do not copy the Python runner into Go line-by-line or expose every current Go tool.

**Historical alternative:** Go client of revised Python owner. This remains inspectable in the prior approved pair but is not the current proposal. Reverting to it would need an explicit owner decision, not an automatic implementation fallback.

**Rejected:** two policy owners, direct ambient SDK bypass, Python shell-out hidden behind a “Go-native” CLI, generic HTTP/CLI execution, weakening audit intent to simplify porting, blanket deletion of legacy documentation or runtimes.

Level 1 after approval: package names, compiled versus protected definition representation, standard-library validation/locking/capture, internal fake seams, compliant sequential admission and control-file serialization. Any control artifact must be fixed, bounded, versioned, regular/non-symlink, `0600` under the proposed Go audit root and declared in the reviewed deployment manifest. New dependencies, credential layouts, privileges, retention changes or infrastructure need Level 2 approval.

## 7. Review, approval and remaining gates

1. Fresh independent review must inspect this exact ADR, task, revised sole ladder, Go requirements/code seams, prior approved pair and U1's current-candidate evidence. The earlier scope review and this author's checks do not satisfy it.
2. Review must assess approval/review ordering: prior records permitted commit before independent review and record whole-document approval before the still-outstanding publication review. Preserve those facts. U1 accepts the alternative review basis, not a retroactive positive review or approval of these replacements.
3. Substantiate findings, separately authorize necessary corrections, then obtain applicable exact-candidate approval and commitment of the superseding sources. Review/approval of revised Go clauses is not repeated approval of unchanged historical clauses. No automatic commit or source-header rewrite.
4. Fresh implementation preflight must bind the resulting approved committed task/ADR/plan to the actual implementation base. Dependency and consumer inventory, protected context/credential feasibility, Go toolchain and offline baseline remain unverified. Separately authorized Chunk 0 discovery may resolve engineering facts without authorizing code or live access.
5. Live deployment/use requires Phase 07 or an explicitly authorized equivalent acceptance gate: exact runtime placement, routes, effective reader policy, fresh credentials, deployed integrity, read/denial/admin-postcondition evidence and revocation ownership. Offline success is never that evidence.

No further product-scope decision is needed to draft this proposal. Approval of its enumerated architecture/path/compatibility deltas is still required. Feasibility failures may expose a specific new Level 2 decision; do not preapprove unknown dependencies or accept new risk by labelling it implementation detail.

## 8. Traceability and authoring boundary

The task maps all canonical FR-001–FR-042, NFR-001–NFR-015 and AC-001–AC-025, with exact current versus later boundaries and V1–V11 evidence. G1–G7 map to task §§2–10 and the delivery coverage table. Full Phase 01 is retained; neither six-status legacy behavior nor an SDK-only happy path completes it.

Sources read through their endings include the Go PRD/baseline/source Phase 01/overview, prior ADR/task/delivery, complete addendum, revised placement/foundation/identity/reuse/toolbox/runner contracts, runner ADSs, restricted-host contracts and Go Phase 03 recovery. Current Go code/test inspection is limited to relevant seams, not a complete dependency/consumer review. Generic topology/educational examples confer no privilege. No protected inventory, generated configuration, credential content or raw audit was inspected.

This authoring changes only the superseding draft pair and the existing delivery plan. It changes no PRD, roadmap, approved prior specification, legacy runtime contract, implementation, test, dependency or deployment configuration. No test/build/toolchain/formatter/live command was run to claim implementation readiness.

**End of DRAFT Go-owned ADR. Direction is recorded; replacement architecture remains subject to independent review, exact-candidate approval/commit and fresh preflight.**
