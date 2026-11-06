# DRAFT task contract — Phase 01 safety boundary and manual slice

**Status:** DRAFT for independent specification review. [ADR §6](../architecture/01-safety-boundary-and-manual-slice-adr.md#6-recorded-human-decisions-and-amendment-gate) records the user's Q1–Q3 decisions; detailed AM1–AM5 clauses below are proposed, not already approved/committed governing amendments. Not execution-ready.

**Project:** aiops openstack lab.

**Source task identity:** [01. Safety Boundary and Manual Slice](../implementation-plan/01-safety-boundary-and-manual-slice.md), Steps 1–3, §01.6 definition of done. This contract bounds that delivery; it is not a replacement phase plan or chunk ladder.

**Requirements:** [canonical Go PRD](../prd.md), [overview](../implementation-plan/00-implementation-overview.md), [educational baseline](../aiops-baseline.md).

**Design companion:** [DRAFT ADR](../architecture/01-safety-boundary-and-manual-slice-adr.md). The ADR is proposed, not already approved architecture.

**Approval reference:** `Approved-phase-01` plus the conversational Q1–Q3 record in ADR §6. Q1 confirms the Phase 01 PRD/source-plan requirements at `0182da9f7c2b322df5da49262748974009db7332`; Q2 selects conditional compatibility-first revised-runner reuse; Q3 selects full Phase 01 through versioned amendments, not scope reduction.

**Inspection / approved requirements baseline:** `0182da9f7c2b322df5da49262748974009db7332`, branch `aiops-go-phase01`. Future preflight records the actual implementation base after the approved specifications/amendments are committed; source approval is not implementation authorization.

**Working tree:** the original authoring pass started clean. This approval-revision pass starts with only the two already-renamed untracked draft files; user filename/cross-reference and portability edits are preserved. **Candidate:** only this file and `docs/aiops-go/architecture/01-safety-boundary-and-manual-slice-adr.md`, still untracked/unstaged/uncommitted.

## 1. Objective and observable outcomes

After separate approval and execution, an operator can list and invoke named, scoped local diagnostics without initializing a model or possessing inference credentials:

```text
explicit application-owned scope + named reviewed tool
  -> definition/schema/policy/relationship checks
  -> one fixed bounded read, only if permitted
  -> sanitized structured evidence or explicit limitation
  -> required durable audit before successful publication
```

A recording executor/API fixture must show zero dispatch for out-of-scope/unknown/invalid requests. A healthy-server fixture must show useful bounded evidence; a permission-denied or hostile-output fixture must show an honest safe non-success/limitation. No enabled local adapter may retain a bypass. Reader deployment prerequisites are documented, not represented as freshly proven.

Q3 explicitly selects **full Phase 01 behavior through versioned amendments**, including seven logical statuses, the bounded fault/flavor catalog extension and durable pre-dispatch intent. AM1–AM5 in §6.6 draft that replacement for review. A six-status/single-terminal implementation may preserve legacy behavior but cannot complete this selected task. Final amendment approval/incorporation is a prerequisite, not authority inferred from this draft.

## 2. Prerequisites and authority gates

### 2.1 Required before implementation

- Preserve the Q1 evidence in ADR §6: the user confirmed the Phase 01 PRD/source-plan requirements at the recorded revision. This later bounded approval does not retroactively edit draft source headers or approve later phases.
- Follow Q2's approved direction: retain/harden the eligible revised runner as the policy/registry/dispatch owner, subject to actual-boundary scope and parity proof; use one maintained definition source and an explicit consumer/version inventory. Go-owned replacement is not an automatic fallback. Apply initial related-resource constraints plus the proposed AM2 extension, without new project/operator/host authority.
- Follow Q3's full-scope amendment route: independently review, approve and incorporate AM1–AM5 into the affected runner/toolbox/adapter/deployment contracts before conflicting integration. The exact field/status/event/version details drafted in §6.6 are proposals, not already approved amendments. This pass modifies none of those governing sources; no code/registry edit substitutes for approval.
- Independently review the ADR/task in a fresh session, obtain human approval and commit the authoritative documents through a separately authorized process. Future preflight must read both through their endings and identify the actual implementation base and worktree.
- Inventory retained entry points and exact asset/dependency provenance. The selective-reuse manifest's pin/tree resolves as recorded in ADR §1, but each selected path and its closure must still be checked; a source change requires manifest review, not blind copying. Historical runner/registry must not be copied, installed, imported or executed.
- Establish practical offline verification baseline in the future execution session. Confirm Go toolchain compatibility with `aiops/go.mod` (`go 1.27.1`). Before running Python validation, obtain/confirm the user-provided virtual environment and use its executable; no system-Python fallback or committed private venv path.

These are future execution prerequisites, not a request to begin preflight now. No implementation work is authorized by this draft.

### 2.2 Separate live gate, not an offline prerequisite

Live capabilities stay disabled until current owner-approved placement, exact cloud/project, endpoints/routes, policy/profile deployment, source integrity and lifecycle evidence pass Phase 07 or an explicitly authorized equivalent early gate. Keep the fixed revised values from ADR F02–F03; missing evidence is not permission to select a new host, profile or endpoint. Deployment, provisioning, host contact, live probes, audit inspection, revocation and cleanup each need their own authority. Fixtures do not establish any of them.

### 2.3 Existing interfaces to preserve or reconcile

Observed paths are documented in ADR §2. Scope-bearing transport and any new Go boundary interfaces are **proposed**, not existing function signatures. Preserve `tools.Registry` callers only through a compliant adapter or disable their diagnostic path. Preserve planning exact-digest, immutable-snapshot, original-goal and single-start regressions; do not implement new planning behavior here. Reuse Go HTTP/recording-reader seams and revised Python temporary-executable/audit fixtures, not historical runtime imports.

No tracked AI-OPS SQL migrations were found under `aiops/`. Application state is file-backed. Do not add a database, SQL role/grant, stored operation or speculative persistence migration. DB transaction/SECURITY DEFINER mechanisms are not applicable to this slice. Local audit publication, filesystem integrity and cross-process concurrency obligations are applicable.

## 3. Binding behavior and decision fidelity

ADR §3 F01–F12 is the cross-document fidelity register; its row labels are not approved decision IDs. `Approved-phase-01` and the user's Q1–Q3 confirmations in ADR §6 identify the approved requirements/direction. AM1–AM5 are draft amendment clause identifiers. Preserve all affirmative and negative rules, especially:

1. Only reviewed named read diagnostics; no model-owned execution, credentials, policy, implementation path, approval state, authority or scope.
2. Application context contains trusted client/actor classification, cloud/OpenStack project, canonical permitted targets, capability/profile set, policy/approval identity, correlation and finite budgets. Request arguments cannot override it. The legacy runner's `local_cli` actor is not an authenticated user; it generates its own correlation/time. No arbitrary actor/client text is inserted into legacy audit.
3. Revalidate cloud/project/target/capability/profile/relationship/limits at actual dispatch, not only CLI parsing or plan review. Bound/scoped name resolution is separately authorized evidence collection, not permission for broad discovery.
4. Initial compatible manual set is `project_resource_summary`, `server_basic_info`, `server_network_info`. The current revised source registry has seven tools under later separate contracts; do not remove those accepted definitions or expose operator/host tools through this task. A reviewed enabled subset must be derived from one owner, not a second permissive registry.
5. Server-to-ports-to-network/subnet relationships derive from authorized observations and permitted visibility. AM2 drafts the full-scope bounded fault/flavor extension; raw fault details, flavor extra-spec/configuration dumps, volume/attachment traversal and host reads are not added. Until the detailed amendment is approved, conflicting extensions stay disabled. Server-scoped permission does not grant project-wide summaries or host discovery.
6. Script contract: exactly required `server_identifier` for the two server tools, none for summary; nonempty ASCII `[A-Za-z0-9._:-]+`, maximum 255 bytes, no slash or `..`. No unsupported name normalization, new name uniqueness rule or silent validation widening. Preserve original and resolved identity and UUID guidance.
7. Preserve selected fields, successful-empty section semantics, explicit partial/unavailable/error distinctions and version-specific mappings. A successful process is not root-cause confirmation or cloud-health proof.
8. Fresh dedicated reader identity/profile only, independent of provider/host authority. No fallback, especially after permission/auth/configuration errors. Runtime installation and credential provisioning are human operations outside the product.
9. Bound API collection as it happens, process lifetime/descendants, both output streams, retries, concurrency and aggregate output. No later dispatch after cancellation or exhausted limits.
10. Minimize and sanitize before any report/storage/model/stream sink. No user-data, full configuration or raw secret-bearing errors. Unsafe-to-transform content is withheld with a limitation.
11. Every request, including pre-dispatch denial, attempts its required terminal audit. Q3 selects durable intent before dispatch and terminal durability before successful publication; AM4 drafts the versioned event/control replacement. No silent replay, duplicate terminal adapter audit, fallback sink or unsafe-path auto-repair.
12. Fix/restart/edit/create/delete and requests to ignore restrictions never map to mutation. Diagnostic-plan approval never authorizes remediation. No inference, host, MCP or project scheduling is introduced here.

No domain edit/canonical-unchanged-edit feature exists in this task, so there is no invented edit timestamp/event no-op rule. The actual no-execution, no-replay and event-cardinality rules are specified in §§6–7.

## 4. In-scope implementation boundary

Subject to §2 approval gates, implement only:

- A capability/entry-point gap matrix recording owner, lineage, versions, callers, profile, actual dispatch route, bypass risk and evidence status. Include CLI, agent, workflow, project, SDK, revised runner and any compatibility consumers; host/MCP/specialist integration stays disabled/deferred.
- One authoritative definition source and deny-by-default boundary. Each versioned definition declares name/version, diagnostic intent, argument schema, fixed implementation, required profile, risk, scope/relationship rules, availability prerequisites, timeout, output bound and read-only guarantee. Reject malformed/duplicate definitions, missing metadata/limits, unsupported schema/validator/defaults, extra/invalid arguments and caller-selected commands/paths/profiles before dispatch; apply the reviewed AM1 definition amendment selected under Q3.
- A manual catalog/invoke path through the existing Go/manual integration seams without model initialization; useful server-basics fixture first, then permitted network and separately authorized project summary through the same boundary. Do not invent exact public CLI flags or package names; compliant naming is Level 1.
- Route every retained enabled SDK/script/local diagnostic entry through that boundary, or visibly disable it before unsafe client construction/dispatch. Do not leave ambient-credential authentication as a startup side effect on a rejected/disabled path.
- Bounded validation, target resolution, relationship/response-scope checks, fixed argv/environment or equally narrow SDK reads, cancellation and resource cleanup.
- Versioned structured safe outcomes, exact legacy translations, minimum-disclosure durable auditing, approved intent/fault protocol, cross-caller fail-closed admission and local operational fault visibility.
- Focused fixture regressions, healthy/permission-denied/hostile scenario seed format with expected calls/targets/status/evidence/safety assertions; manual no-model, extension review, credential-revocation owner and deployment-preflight guidance as implementation evidence.

Do not treat scope bullets as authorization to change fixed runtime contracts. A necessary conflicting change stays blocked until §2 is satisfied. Future implementation may add only documentation/tests/helpers needed for this boundary, not scaffolding for later phases.

## 5. Explicit exclusions and named deferrals

- **Permanently excluded by PRD non-goals 1–4:** infrastructure mutation/remediation; repository/coding/deployment tools; generic shell/SSH/sudo/CLI/file/database/message-bus tools; caller executables; admin/root/service/database/RabbitMQ credentials or unrestricted control-plane files. No approval inside this product permits them.
- **Non-goals 5–10 / outside selected scope:** autonomous triggering/surveillance/scaling, required multi-agent/distributed/vector infrastructure, web UI/public multi-tenant or HTTP service, local model/GPU/training/new provider gateway, replacement lab automation, curriculum-as-release acceptance. Lessons/assessment are a separate learning plan, not artifacts here.
- **Phase 02:** goal-to-plan/approval integration, bounded model/agent investigation, initial evidence-linked report/review, nested-call scope-escape integration, provider isolation/disclosure and specialist routing gates. This task preserves existing approval behavior but does not enable that execution path.
- **Phase 03:** investigation/workflow/project checkpoints and schemas, resume, cross-sink state recovery, cumulative recovery budgets, historical memory, curated retrieval, export/retention/freshness and versioned state conversion. Do not generalize audit retention under later data policy.
- **Phase 04:** metadata/network diagnosis and volume/attachment workflows, multi-server dependencies and synthesis, complete evidence review. Bounded network evidence collection now is not full metadata diagnosis.
- **Phase 05:** operator-reader/host profiles, host SSH/log/listener evidence and MCP. Current revised source definitions and accepted historical host run are not activation approval. Preserve them without enabling or silently changing their mappings.
- **Phase 06:** full evaluation metrics/corpus/rubric, telemetry/readiness/lifecycle consolidation and specialist comparison. Seed scenarios now; no complete evaluation platform or measured SLA now.
- **Phase 07:** live deployment/policy/route/credential acceptance, mutation-denial probes, release compatibility and operations/rollback exercises. They may occur earlier only under explicit equivalent gate authorization, never as a test side effect.
- No live/cloud/provider calls, credentials/profile-content reads, protected inventory/generated configuration reads, package installation, provisioning, migrations, audit inspection/export, staging/commit/push/merge/deploy in this authoring task. Future offline implementation likewise does not imply live permission.

## 6. Authorization, privilege, consistency and audit-integrity constraints

### 6.1 Effective authorization and least privilege

Trust application-established context, not model fields, CLI actor strings, environment credentials or discovered relationships. Unknown/unreviewed cloud/project/profile/target and unavailable controls fail closed. Inspect actual SDK/runner direct invocation capabilities, not only a facade's checks. Test that a client cannot bypass scope through an underlying callable path; either move the checks to that boundary or prevent that path from being enabled for the client. Root-owned executables/configuration must not be writable by the runtime caller. A privileged installer/admin procedure is not a diagnostic capability.

Keep `assistant02` / `ai_ops_assistant` / `/opt/openstack-ai-ops-assistant` and the fresh `aiops-assistant-project-reader`, project `admin`, domain `default`, role `reader`; one-month expiry and OpenStack admin-team rotation/revocation. Profile directory `0700`, regular non-symlink files `0600`, owner/group `aiops_assistant`. No historical/human/member/service/admin credentials; no operator/SSH fallback. Confirm effective capabilities and least-privilege metadata with fixtures/static role checks; live policy proof remains separate. Do not copy the local transport waiver beyond its exact host/inventory.

### 6.2 Definition, identity and race consistency

Definitions and authorization context must remain bound to the reviewed request through dispatch; caller mutation of a map/preview, registry drift or a concurrent request cannot substitute another target/profile/implementation. Preserve exact fixed mappings and pre-spawn integrity revalidation. SDK output must match the requested canonical target/project/relationship before publication; out-of-scope results are not usable evidence. Do not enforce uniqueness on OpenStack names; ambiguous resolution rejects rather than arbitrarily selecting a match.

Set and enforce finite page/record/memory/time/retry/concurrency/output budgets before collection, not solely after complete buffering. Share admission/budget/cancellation/fault state across all concurrent callers of the selected boundary, including separate local processes. Compliant serialization or conflict rejection is Level 1; parallel project scheduling is not required. Test lock ordering/contention, no deadlock, duplicate admission, cancellation races and policy/profile/definition tampering.

### 6.3 Retained terminal audit contract

Until a scoped replacement is approved, retain [runner Steps 5–7](../../ai-ops-revised/runtime/tool-runner-safety-gateway-steps-05-to-07-operations-contract.md) exactly:

- Closed result/audit `1.0`; six statuses and runner exits in §7. Runner-generated UUIDv4/time, fixed `local_cli`, single `tool_request_completed` terminal attempt per request. The adapter does not write a second terminal event or forward caller actor/correlation. Audit stores only `server_identifier_present`, never the identifier, payload or raw errors.
- Fixed directory `/opt/openstack-ai-ops-assistant/audit`, active `tool-runner.jsonl`, lock `.tool-runner.lock`, numbered archives `tool-runner.jsonl.1`–`.3` only. Directory owner/group `aiops_assistant`, mode `0700`; files/archives mode `0600` with required ownership. No caller overrides.
- Validate path resolution, directory/file/lock/archive metadata without following symlinks; reject non-regular, wrong-mode/owner, unsafe paths or archive collisions. Do not auto-unlink/repair unsafe paths or fall back elsewhere.
- Exclusive `fcntl.flock` coordinates append and rotation; revalidate after lock acquisition. Compact bounded JSONL records must not interleave. Maximum event 16 KiB; rotate at 1 MiB, retain three numbered archives, no compression or age deletion. Complete flush and fsync before persistence success; verify metadata again.
- Audit failure yields generic nonzero error, diagnostic data withheld and no raw filesystem details; never retry diagnostic execution, write stdout audit copies, alternate sinks or insecure replacements. Operator inspection/recovery owns unsafe paths.

The original result contract's child `exit_code` is nullable when no child completed; process exit is independently status-mapped. Current code/tests that use a status code in that field are observed divergence, not authority to revise the contract. Resolve parity via in-scope repair or approved versioned amendment; do not weaken tests/specifications to bless divergence.

### 6.4 Target intent/terminal protocol and publication barrier

These source-plan Steps 2–3 obligations are selected by Q3, **not additions inside legacy `1.0`**. AM3–AM5 in §6.6 propose the replacement versions, closed fields, identity/cardinality, minimum disclosure, incomplete/uncertain outcomes and compatibility/recovery controls. They require final review/approval/incorporation before activation; the product/approach choice itself is no longer unanswered.

Required observable ordering after approval:

1. Validate/authorize against current context and controls. Attempt terminal audit even for a rejected request. No intent is required solely for a request that never dispatches unless the approved amendment explicitly says so; do not invent an extra event per denial.
2. Persist sanitized request intent durably **before** any allowed dispatch. Failed write/disk/permission/flush/fsync/rotation means zero dispatch; locally show the control fault.
3. Execute at most once for that request under its fixed scope/budgets. Interruption or missing terminal evidence creates incomplete/uncertain completion, not proof the read never happened.
4. Sanitize/normalize, persist the required terminal event durably, then publish successful evidence. Terminal audit failure returns sanitized generic non-success, with current diagnostic payload/raw errors withheld. Preserve intent and any durable event. Never redispatch to fix an audit error.
5. Expose incomplete/uncertain completion locally without relying on the failed sink. This operational fault indication is not a replacement audit sink and contains no raw diagnostics. Block new dispatch across concurrent callers and restart until safe recovery of the required control boundary. Another process cannot clear the fault simply by starting fresh.
6. No automatic replay of interrupted calls or audit repair by deleting events. Later intentional re-observation/recovery belongs to Phase 03 policy, current authorization and remaining budgets.

There is no ACID transaction spanning OpenStack read, audit and future checkpoint files. Require ordered durable publication and truthful uncertainty, not impossible exactly-once guarantees. Do not erase audit to simulate rollback. Phase 03 must later prove checkpoint-after-audit failure as well; Phase 01 must preserve its own intent/terminal artifacts for that future recovery.

### 6.5 Redaction, collection and local data boundary

Use the binding selected fields, result/audit schemas and sanitizer limits. Legacy runner marker is `[REDACTED]`, case-insensitive secret-key/text matching, maximum recursion depth 32 / 100,000 visited values, bounded safe error messages (512 UTF-8 bytes for runner); raw script error bound is separately 512 characters. Toolbox list sections cap at 50 records and the complete diagnostic at 1 MiB; runner per-tool limits may be tighter. Preserve each bound rather than treating characters as bytes or confusing section/stream limits.

Redact nested keys, assignments/headers, bearer values and private-key blocks; withhold unsafe/unsupported/malformed/depth-excess content. Test split multibyte/output chunks and truncation boundaries so canaries never reach errors, streams, result serialization, reports, stores or audit. Streaming raw child output before redaction is forbidden. AM3 proposes an independent `redacted` indicator in result `2.0`; no field is added silently to the closed legacy result.

No future investigation-state schema is scaffolded. If the approved intent protocol requires protected local state, limit it to that protocol with approved paths/permissions/version compatibility. Existing investigation IDs, original goals, identities, timestamps, child links and evidence must remain untouched; no automatic in-place conversion. Retain legacy audit/history and a tested disable-new-path rollback, not fallback to weaker credentials or an old bypass.

### 6.6 Draft versioned amendment package — AM1–AM5

**Authority and status:** Q3 authorizes the full-scope amendment route, not automatic acceptance of the technical representations below. These are DRAFT replacement clauses for independent review/human approval and later incorporation into the governing contracts identified in ADR §6. They do not amend source files by reference alone. `2.0`, definition schema `2`, new field/event names and cancellation process exit `6` are proposed engineering choices, not values dictated by the user. Once approved, changing a closed published contract requires its compatibility/version process. No new product question is needed merely to choose a compliant internal implementation mechanism.

#### AM1 — Revised owner, definitions and trusted request context

Amend runner Steps 1–4's closed definition/execution contract for a versioned Phase 01 view under the **same eligible revised owner**. One maintained, reviewed definition source owns both scripts and SDK implementations; frozen legacy snapshots and mechanically derived versioned views are allowed, independent permissive edits are not. The schema `2` view declares all metadata in §4, rejects unknown/duplicate/missing fields and enforces fixed implementation/profile/relationship/limit mappings. Concrete internal layout and generated-view technique are Level 1, with closed-schema fixtures and provenance supplied for review.

The Phase 01 enabled view includes only the three project tools, with AM2's versioned server extension; later operator/host definitions in the maintained source remain governed separately and disabled for this delivery. Preserve their definitions, not an activation grant. Trusted application context and current policy must reach actual revised-owner admission/dispatch; a caller cannot supply actor, policy, credentials, executable, profile, scope expansion or correlation as authoritative tool arguments. Transport and package/helper organization are Level 1, subject to direct-invocation negatives and protected configuration. A direct legacy CLI/SDK callable path available to the Phase 01 client must enforce the same required controls or be disabled. No ambient credential authentication occurs before that decision.

The AM1 execution extension permits an equivalently narrow fixed SDK implementation under that owner's authorization, credentials, limits, sanitization and audit lifecycle, not an independent SDK registry. The original fixed script paths/argv/environment and profile boundary remain unchanged; any additional fixed implementation artifact must be enumerated in the reviewed deployment file/target allowlist before use. No caller-selected target, package installation, observer compiler/toolchain or new infrastructure is authorized.

#### AM2 — Full bounded Phase 01 manual capability/relationship view

Amend the toolbox and runner field/capability mapping for a proposed tool-contract version `2.0`. Its inner diagnostic document has `schema_version: "2.0"` and exactly `schema_version`, `tool`, `status`, `sections`, `error`; sections retain exactly `name`, `status`, `data`, `error`, `truncated`. Preserve inner top-level `ok`/`partial`/`error` and section `ok`/`empty`/`unavailable` semantics with safe normalized errors. AM3 is the distinct outer runner result contract; its seven statuses are not silently copied into an incompatible inner schema. Legacy inner `1.0` remains unchanged for its explicitly compatible consumers.

| Named capability | Required observation / permitted traversal | Exact extension boundary |
| --- | --- | --- |
| `server_basic_info` | One authorized server, its fault and associated flavor. Resolve the original target under current cloud/project/reader authority; then read only the flavor identity derived from that server observation. | Preserve existing basic-server projection; add fault `code` and sanitized bounded `message` when present, plus a `flavor_detail` section limited to `id`, `name`, `vcpus`, `ram_mb`, `disk_gb`, `ephemeral_gb`, `swap_mb` when available. Do not retain/publish raw fault `details` or extra-spec maps; do not request user-data or full configurations. This is a versioned projection extension, not a changed `1.0` payload. |
| `server_network_info` | Requested server → attached ports → validated derived networks/subnets within the reader's approved project-visible relationship rules. | Preserve existing field projections and section bounds. No unrelated port/network/subnet discovery, broader topology dump, host lookup or alternate profile. Model assertions never establish a relationship. |
| `project_resource_summary` | Existing fixed project-reader summary sections, only under an explicit project-wide capability distinct from a server assignment. | Preserve current selected fields and bounds. Existing volume summary fields are not authority for volume/attachment traversal. |

Absent server fault is represented as no fault (`null` in the versioned server `fault` field), not fabricated failure text. Missing flavor linkage/detail produces an explicit unavailable `flavor_detail` section and partial/limitation outcome; it does not invent a new identity or suppress valid independent server evidence. Preserve existing basic field names while validating/minimizing nested identity values; no opaque nested flavor/image/configuration object bypasses the selected-field policy.

The public arguments remain none for summary and one `server_identifier` for the server tools; neither a flavor ID nor field selector/profile/command becomes caller authority. A flavor lookup must match the observation-derived ID and current permitted visibility, and cannot enumerate all flavors as fallback. Missing relationship, policy rejection or unavailable flavor evidence yields a named gap/partial result, not a fabricated flavor or stronger profile. The table's `flavor_detail` field spelling is a proposed normalization of the existing Go observation seam; encoding remains versioned and tested, not a change attributed to the user.

Retain canonical server UUID/exact-name intent, ambiguity/missing rejection and original/resolved identity. Direct scripts keep the conservative identifier rules. A supported client resolver may pass a verified canonical UUID after a separately scoped exact-name read; it never silently widens the direct script contract. Without that permitted resolution path, return UUID guidance. No new role, route, endpoint, profile, host authority or cloud-name uniqueness is granted. Operator confirmation of current deployed reader policy remains a live prerequisite, not proof supplied by this table.

#### AM3 — Proposed closed result `2.0` and exits

Amend runner Steps 1–4's status/exit map and Steps 5–7's result contract. The proposed `2.0` result has exactly the 13 legacy top-level fields (`schema_version`, `tool`, `status`, `arguments`, `exit_code`, `data`, `stdout`, `stderr`, `error`, `duration_ms`, `truncated`, `timestamp`, `correlation_id`) plus `tool_version`, `target`, `redacted`:

- `schema_version` is `"2.0"`; `tool_version` is the reviewed tool-contract version or `null` for unresolved tools.
- `target` is `null` for a non-targeted/invalid request or unresolved tool, otherwise a closed object with `original_identifier` and `resolved_identifier`, each sanitized string or `null`. A resolved value is present only after verification; redaction may withhold either value. Unknown/malformed input is not reflected unsafely. Project-wide summaries do not invent a server target.
- `redacted` is a boolean independent of `truncated`; it records replacement/withholding during sanitization. Truncation alone does not set redaction, and redaction alone does not imply complete collection. Unsafe sanitizer failures still withhold the payload and return an error.
- `status` is exactly `ok`, `error`, `denied`, `validation_error`, `timeout`, `cancelled`, `unavailable`. Proposed process exits preserve `0`–`5` for their existing meanings and reserve `6` for `cancelled`. `exit_code` remains the actual completed child exit or `null` when none completed; do not substitute the runner process exit.
- `cancelled` requires an application cancellation/interruption with bounded owned-process cleanup; timeout remains `timeout`, and cleanup failure or required audit failure overrides success/cancellation with nonzero `error`. Pre-cancelled requests dispatch nothing but still attempt terminal audit.
- Keep the legacy safe error `{class,message}` shape and existing normalized classes; cancellation uses `interrupted`. No new raw error channel is introduced. `stdout` and `stderr` remain `null` for the supported structured diagnostics. Safe partial sections may be returned with an explicit non-success/limitation; policy/missing/error never becomes healthy empty evidence.
- Generate request timestamp/correlation inside the trusted revised boundary, not from public arguments. Use one request UTC timestamp across its result and audit events and monotonic elapsed duration. Maintain deterministic compact UTF-8 JSON, closed nested shapes, strict encoding, sanitizer bounds, one result line and pre-publication durability.

No `2.0` fields or status are inserted into `1.0`. AM5 defines version negotiation/translation obligations; an old adapter cannot receive a silent format change.

#### AM4 — Proposed closed audit `2.0`, cardinality and control recovery

Amend runner Steps 5–7's single-event schema/cardinality to a versioned two-stage protocol. Both event types use exactly the 12 legacy audit fields (`schema_version`, `timestamp`, `event_type`, `actor`, `tool`, `arguments`, `status`, `duration_ms`, `correlation_id`, `reason`, `exit_code`, `truncated`) plus `event_id`, `tool_version`, `policy_version`, `approval_present`, `scope`, `redacted`, `completion`:

- `schema_version` is `"2.0"`; `event_id` is an internally generated UUIDv4 per event. One internally generated `correlation_id` binds the request's intent/result/terminal; caller IDs never authorize or replace it.
- `actor` remains fixed `local_cli` for this local slice, not an authenticated human assertion. `tool_version` and `policy_version` are bounded non-secret trusted version labels or `null` if unavailable; no arbitrary client text/configuration path is used.
- `arguments` retains only the existing minimum-disclosure presence summary. `scope` is a closed object with booleans `cloud_present`, `project_present`, `project_wide` and non-negative integer `target_count`, derived from validated application context. `approval_present` is a boolean, not an approval token/digest or requirement to invent plan approval for a manual call. Do not store raw cloud/project/target identifiers, profile content, diagnostic data or outbound context in audit.
- `redacted` and `truncated` are independent booleans derived from safe normalization. `reason` is a reviewed bounded normalized class or `null`; no raw exception/filesystem/source message. `exit_code` is completed child exit or `null`.

| Event type | Fields specific to the stage | Cardinality / durable ordering |
| --- | --- | --- |
| `tool_request_intent` | `status: null`, `duration_ms: 0`, `reason: null`, `exit_code: null`, `completion: pending`; safe request/definition/scope summary only. | One durable intent required before any allowed diagnostic dispatch. A request rejected before dispatch does not require an extra intent. An uncertain/failed persistence never permits dispatch. |
| `tool_request_completed` | `status` is one of the seven result statuses; measured `duration_ms`; `completion` is `not_dispatched`, `completed` or `interrupted`, consistent with actual dispatch/cleanup. | Every request attempts one terminal event; at most one successfully committed terminal event per request. A dispatched request normally has one intent + one terminal; a pre-dispatch denial normally has one terminal only. Terminal durability precedes successful result publication. No adapter adds a duplicate terminal or an extra activation event. |

If a process dies after durable intent without a durable terminal, leave completion locally **incomplete/uncertain**; do not fabricate success, infer zero execution or automatically append a retrospective terminal/replay. AM4 does not introduce a general resume workflow; Phase 03 owns later intentional re-observation and cross-checkpoint recovery. Audit failure attempts no redispatch. If terminal persistence is uncertain, do not retry blindly and create duplicate lines; preserve any committed evidence and fail closed pending safe recovery.

Retain the fixed audit root/active/lock/archive paths, ownership/modes, `flock`, 16 KiB per-event bound, 1 MiB rotation threshold, three-archive maximum, no compression/age deletion/fallback and no unsafe-path auto-repair. Version-aware validation may read mixed `1.0`/`2.0` records under explicit compatibility rules; do not convert or rewrite retained records. Rotation must not evict an unresolved intent required for truthful recovery: if rotation would do so, stop new dispatch and surface a bounded operational fault rather than exceed retention or silently discard it. Review/verify this interaction as part of AM4, not an exception hidden in implementation.

AM4 additionally permits only minimal protected **execution-control state** needed for shared audit-health/admission/incomplete-call handling under the same revised audit root; it is not another audit sink, evidence payload store or future investigation schema. Any materialized control file must be declared in the reviewed deployment manifest, regular/non-symlink, owned by `aiops_assistant`, mode `0600`, bounded and versioned, with the same safe-path discipline. Its exact name, serialization/atomic update and lock/admission mechanism are Level 1 choices within this amendment; they cannot be supplied by a public caller. A compliant design that needs no additional file is also permitted.

Local fault visibility must remain available without writing the failed audit sink, disclose no payload/raw details, and never count as a persisted audit replacement. A required-control fault stops new admission across callers and restart; inability to prove healthy control state keeps execution disabled. If durable fault storage itself fails, do not assume restart is recovery: require trusted operator recovery/readiness before enabling dispatch. Preserve existing events/intents, coordinate pending work/locks and never erase audit to simulate rollback. Test physical filesystem/process behavior, rotation, disk/permission/fsync failures, concurrent admission and restart; an in-memory latch or mocks alone do not prove this guarantee.

#### AM5 — Compatibility, migration and rollback

Inventory all retained local callers, schema consumers, inspectors, deployment role assertions, script/SDK adapters and independently governed MCP/host assets. Record exact old/new versions and which are enabled. The selected Phase 01 Go/manual path requires the new scope/intent controls and versioned `2.0` behavior; it cannot silently fall back to a stock unscoped `1.0` runner. Version choice is trusted configuration/adapter binding, not an unvalidated caller execution override.

For common outcomes, preserve established semantics/exits. For an **explicit compatibility result view**, `cancelled` may translate to legacy `error`/`interrupted` and process exit `1`, while new target/redaction fields are not injected into legacy JSON. This is an output-only, explicitly labelled translation from one execution; it writes no additional audit and does not establish full legacy result/audit parity by itself. A legacy consumer must be upgraded/approved for `2.0` intent/terminal evidence or remain disabled: never flatten two events to claim the old single-event contract. Conversely, frozen `1.0` tests remain tests of `1.0`, not proof of full Phase 01 acceptance.

No historical records, state or audit are migrated in place. Test old and new envelopes, malformed/unsupported versions, exact-name identity preservation, mixed-version inspection and rejection by incompatible consumers. Before any rollout, final governing amendments must enumerate applicable file/implementation/definition allowlist changes and protected control-state metadata. Existing later host/MCP definitions and their separate contracts remain unchanged/disabled for this task.

Rollback first stops new admission, bounds/cancels active work and preserves durable intents/events plus local incomplete/fault state. Disable new adapters/tools/configuration without exposing ambient credentials or restoring a bypass. A previous runtime may resume only with compatible version-aware inspection and its independently valid authorization/audit boundary; if it cannot safely handle retained evidence, remain disabled pending operator review. Do not delete/rewrite `2.0` events to make a legacy inspector pass. Re-enablement requires explicit safe recovery and applicable live gates, not source reversion alone.

## 7. Domain outcomes, no-execution and no-replay rules

| Condition | Required observable result / side effects |
| --- | --- |
| Authorized bounded read | Useful safe projected evidence, versioned outcome/correlation/duration, independent truncation/redaction semantics as approved; required audit durable before success. At most one diagnostic execution for that request. |
| Successful no records | Successful `ok` result with appropriate diagnostic section `empty`, not an unavailable/error disguise and not confirmation of cloud health. Still a real request with required audit, not an audit-free cache/no-op. |
| Unknown/generic/mutation tool | Pre-dispatch `denied`, no SDK operation/child spawn; sanitized terminal audit attempted. Operator insistence grants nothing. |
| Missing/extra/duplicate/wrong-type/range/overlong/unsafe input | Pre-dispatch `validation_error`; no diagnostic dispatch or execution to “validate” arbitrary commands. Malformed trusted registry is normalized non-success and disables affected startup/dispatch. |
| Scope/profile/cloud/project/relationship escape | Denied before the forbidden lookup/dispatch, audited; no privilege fallback or transient retry. Legitimate scoped resolution may already have occurred, but no unintended target is inspected. |
| Missing/ambiguous server | Authorized bounded resolver returns normalized not-found/ambiguous error and guidance; never select a random match or imply an empty healthy server. Preserve original identifier and only a verified resolved identity. |
| Unsupported direct script name | Reject under the conservative script contract with UUID guidance; no silent character widening or caller-selected executable. Any permitted prior name resolution remains separately scoped. |
| Optional tool/profile/endpoint unavailable | Explicit `unavailable`/limitation using reviewed mappings, no stronger profile, command substitution or healthy-state claim. Authentication/policy/configuration/not-found/malformed failures are not automatically unavailable/empty. |
| Timeout/cancellation | Stop new dispatch, terminate/reap all owned descendants, drain/close bounded pipes; nonzero safe normalized outcome and terminal audit attempt. Cleanup failure is failure, never successful cancellation. |
| Unsafe output/encoding/redaction | Withhold data, normalized bounded non-success; no partial/raw leak and no automatic second observation. |
| Required authorization/control/intent failure | Fail closed, zero new dispatch, safe local fault; attempt required terminal audit where possible. |
| Terminal persistence failure | Non-success, payload/raw filesystem details withheld; preserve intent/committed audit, visible incomplete/uncertain completion, shared stop-new-dispatch and no replay until safe recovery. |
| Repeated request intentionally made later | A new independently authorized, budgeted observation and request identity/audit; do not suppress audit because a read looks identical. This is not automatic retry of an uncertain request. |
| Plan review declined/EOF/non-ready/stale digest | Preserve zero project/task start. No tool audit is invented when there was no tool request. Reusing an approved prepared plan cannot start it twice in memory. |

**Legacy mapping:** `ok → 0`, `error → 1`, `denied → 2`, `validation_error → 3`, `timeout → 4`, `unavailable → 5`. Interruption is `error` with `interrupted` class, not a seventh status. Only approved unavailable classes map to `unavailable`; other failures retain their reviewed normalization. Diagnostic script top/section statuses and exits are a different inner contract and require explicit translation, not blind copying.

**Selected target mapping:** Q3 selects all seven logical statuses and richer independent metadata. AM3 proposes result `2.0` with `cancelled → 6`; AM4 proposes audit `2.0`. These are explicitly authored engineering representations, not numeric/schema values supplied by the user or extensions to `1.0`. All target statuses require reviewed examples and tests; a legacy translation is not full target completion.

## 8. Requirement and acceptance traceability

Vocabulary: **CURRENT_TASK** = obligated here after its approval gates; **ALREADY_ACCEPTED** = binding accepted invariant to preserve/regress, not a fresh assertion that current implementation passes; **EXPLICITLY_DEFERRED** = named later owner; **OUTSIDE_SELECTED_SCOPE** = unrelated/excluded; **MISSING_OR_CONFLICTING** = genuine gap, not implicitly deferred. Mixed rows name the exact split. This matrix uses canonical PRD identifiers, not the older revised PRD's different FR numbering.

### 8.1 Functional requirements

| PRD | Disposition and exact boundary | Future evidence |
| --- | --- | --- |
| FR-001 | CURRENT_TASK manual named diagnostics; EXPLICITLY_DEFERRED investigation/project to Phase 02/04 and inspect/pause/resume/export integration to Phase 03. | V10 manual no-model entry point; no claim of all CLI modes. |
| FR-002 | CURRENT_TASK application-owned per-request cloud/project/targets/profiles/budgets; EXPLICITLY_DEFERRED investigation lifecycle record to Phase 02/03. | V2/V4 scope identity cannot be overridden. |
| FR-003 | CURRENT_TASK UUID/exact-name resolution, original/resolved identities, ambiguity/missing and narrow-script guidance; observed Go behavior preserved, not presumed accepted safety. | V4 and existing server/approval regressions. |
| FR-004 | EXPLICITLY_DEFERRED Phase 02 planner integration; preserve existing non-ready zero-start behavior. | V11 existing planning regressions only. |
| FR-005 | EXPLICITLY_DEFERRED Phase 02 scope/policy-bound exact approval; preserve current digest/immutable-preview/cancel semantics. | V11; no new approval workflow here. |
| FR-006 | EXPLICITLY_DEFERRED Phase 04 full graph/readiness; preserve existing rejection/single-start regressions if callers change. | V11. |
| FR-007 | EXPLICITLY_DEFERRED Phase 02 model control validation. Manual path uses no model. | V10 zero inference calls. |
| FR-008 | EXPLICITLY_DEFERRED Phase 02 agent loops; CURRENT_TASK tool-call bounds/cancellation prerequisites only. | V5 zero post-cancel dispatch. |
| FR-009 | CURRENT_TASK deterministic dispatch/limits and no retry/fallback for denial/invalid/control failure; EXPLICITLY_DEFERRED task transitions/retries Phase 02/04. | V2/V5/V8. |
| FR-010 | CURRENT_TASK local SDK/script call-boundary scope; EXPLICITLY_DEFERRED nested/delegated integration Phase 02, resumed integration Phase 03, MCP Phase 05. | V2; disabled paths not advertised accepted. |
| FR-011 | CURRENT_TASK reviewed initial network relationships, separate project visibility and AM2 bounded fault/flavor relationship; EXPLICITLY_DEFERRED volume/attachment traversal Phase 04 and host Phase 05. Q2/Q3 direction resolved; detailed amendments still require approval. | V4 positive provenance and negative forged/unreviewed reads. |
| FR-012 | EXPLICITLY_DEFERRED Phase 04 domain workflows. Current basic/network evidence is prerequisite, not complete diagnosis. | Seed scenarios only; named evidence gaps. |
| FR-013 | EXPLICITLY_DEFERRED Phase 04 multi-server synthesis/dependencies. | No scheduler or synthesis scaffold. |
| FR-014 | EXPLICITLY_DEFERRED Phase 03 checkpoint records. CURRENT_TASK audit intent is distinct and specified by draft AM4 under Q3's selected route. | V7/V8 only audit ordering/recovery. |
| FR-015 | EXPLICITLY_DEFERRED Phase 03 validated resume/intentional refresh; CURRENT_TASK no automatic replay and honest uncertainty. | V8 no redispatch on interruption/audit failure. |
| FR-016 | EXPLICITLY_DEFERRED Phase 03 memory/context classes. | No memory ingestion added. |
| FR-017 | EXPLICITLY_DEFERRED Phase 03 curated retrieval; manual diagnostic availability independent of knowledge. | V10 absent knowledge cannot force model/ingestion. |
| FR-018 | CURRENT_TASK untrusted request/output cannot alter permissions/scope/profile; EXPLICITLY_DEFERRED knowledge/memory/delegation context Phase 02/03/06. | V9 hostile-output/request fixtures. |
| FR-019 | EXPLICITLY_DEFERRED Phase 02 initial reports / Phase 04 full review; CURRENT_TASK truthful evidence/limitation outputs. | V6/V10 no “denial means healthy” result. |
| FR-020 | EXPLICITLY_DEFERRED Phase 02 initial / Phase 04 full evidence review. | Do not invoke existing specialist review as manual tooling. |
| FR-021 | ALREADY_ACCEPTED fixed revised placement; CURRENT_TASK design/preflight preservation; EXPLICITLY_DEFERRED current deployment proof Phase 07. | V3 static constraints, not deployed AC-011 pass. |
| FR-022 | ALREADY_ACCEPTED identity/lifecycle restrictions; CURRENT_TASK dedicated-profile/no-fallback path; EXPLICITLY_DEFERRED optional profiles Phase 05 and live policy Phase 07. | V3 direct/ambient isolation; owner procedures. |
| FR-023 | CURRENT_TASK reviewed definitions, closed schema/startup and no-dispatch validation. AM1 drafts definition extensions under Q3's selected route. | V1/V2. |
| FR-024 | CURRENT_TASK fixed script argv/environment and equivalent SDK boundary or SDK disabled. | V2/V3/V5. |
| FR-025 | CURRENT_TASK summary/basics/network and AM2 bounded server fault/flavor; EXPLICITLY_DEFERRED attachments Phase 04 and higher-visibility logs/agents Phase 05. No role expansion or arbitrary extra specs. | V4/V10 exact versioned catalog and explicit unavailable gaps. |
| FR-026 | EXPLICITLY_DEFERRED Phase 05; host tool definitions in revised source do not enable them here. | V2 disabled/denied host access. |
| FR-027 | CURRENT_TASK AM3 seven-status result `2.0` and explicit legacy translations; ALREADY_ACCEPTED closed six-status `1.0` preserved for its compatible consumers, never silently extended. | V6 version/exit/status matrix; no unversioned extension. |
| FR-028 | CURRENT_TASK AM4 intent/terminal protocol, all-request terminal audit and fail-closed publication; ALREADY_ACCEPTED filesystem/durability/minimum-disclosure protections preserved. | V7/V8; exact event cardinality per version. |
| FR-029 | CURRENT_TASK pre-sink redaction/minimization; later memory/export/disclosure privacy EXPLICITLY_DEFERRED Phase 02/03. | V9 all enabled local sinks/canaries. |
| FR-030 | CURRENT_TASK permanent mutation denial, including operator override requests. | V2/V9 zero mutation dispatch. |
| FR-031 | EXPLICITLY_DEFERRED Phase 02 enabled model adapter contract. | V10 manual no-model independence. |
| FR-032 | EXPLICITLY_DEFERRED Phase 02 provider/model/disclosure authorization. No inference authorized now. | V10 zero provider calls. |
| FR-033 | CURRENT_TASK manual path never launches a model or forwards diagnostic credentials to it; EXPLICITLY_DEFERRED model-runtime isolation/egress Phase 02/07. | V3/V10; no claim of deployed isolation. |
| FR-034 | CURRENT_TASK manual use without inference; EXPLICITLY_DEFERRED outage/revocation plus local-state/report integration Phase 02/03/07. | V10. |
| FR-035 | EXPLICITLY_DEFERRED Phase 05 MCP parity/discovery/knowledge; preserve existing independent revised contracts, no adapter activation here. | No MCP acceptance from local tests. |
| FR-036 | EXPLICITLY_DEFERRED Phase 02 routing gate and Phase 06 optional specialist status/comparison; specialists disabled in new manual path. | V2/V10 zero specialist dispatch. |
| FR-037 | CURRENT_TASK versioned healthy/denied/hostile scenario seed; EXPLICITLY_DEFERRED full offline harness Phase 06. | V10 seed expected/actual safety assertions. |
| FR-038 | EXPLICITLY_DEFERRED Phase 06 quality/tool-selection/claim/cost reporting. | No invented scores/SLA. |
| FR-039 | CURRENT_TASK tool-call correlation/time/terminal outcome; EXPLICITLY_DEFERRED cross-investigation/task/model/review/resume telemetry Phase 02/03/06. | V6/V7 exact correlation and timestamps. |
| FR-040 | CURRENT_TASK finite tool limits/retry/concurrency/cancellation; EXPLICITLY_DEFERRED full task/context/token/cost budgets Phase 02/03/06. | V5/V8 shared limits and no later dispatch. |
| FR-041 | CURRENT_TASK definition/required-control startup checks and documented deployment preflight; EXPLICITLY_DEFERRED complete readiness/lifecycle Phase 06/07. | V1/V3/V7; unmet capabilities disabled. |
| FR-042 | ALREADY_ACCEPTED reader/audit lifecycle constraints; CURRENT_TASK owner/revocation/extension/deployment guidance; EXPLICITLY_DEFERRED full retention/export/rollback rehearsal Phase 03/07. | V11 compatibility/documentation; no live rehearsal now. |

### 8.2 Non-functional requirements

| PRD | Disposition and exact boundary | Future evidence |
| --- | --- | --- |
| NFR-001 | CURRENT_TASK deterministic local no-bypass/no-mutation/no-disclosure guarantee; later paths regressed in their phases. | V2/V9 zero violations. |
| NFR-002 | ALREADY_ACCEPTED fixed profile/runtime metadata; CURRENT_TASK credential separation/least-privilege design and fixture paths; EXPLICITLY_DEFERRED deployed routes/policy Phase 07. | V3; AC-011 not claimed. |
| NFR-003 | CURRENT_TASK finite per-call/aggregate bounds and cleanup; full investigation budgets Phase 02/03. | V5/V8. |
| NFR-004 | CURRENT_TASK approved audit intent/terminal durable ordering and concurrent writer integrity; EXPLICITLY_DEFERRED checkpoint/resume atomicity Phase 03. AM4's detailed amendment approval precedes activation. | V7/V8 actual filesystem/process tests. |
| NFR-005 | CURRENT_TASK call/evidence scope isolation; EXPLICITLY_DEFERRED scoped memory/knowledge/approval persistence Phase 03. | V2/V4; no name-only authority. |
| NFR-006 | CURRENT_TASK explicit optional degradation and required-control fail closure, no model dependence; EXPLICITLY_DEFERRED consolidated reliability Phase 02/06. | V7/V8/V10. |
| NFR-007 | CURRENT_TASK collection failure/empty not diagnosis proof; EXPLICITLY_DEFERRED semantic root-cause/review corpus Phase 04/06. | V6/V10 truthful outputs. |
| NFR-008 | CURRENT_TASK tool provenance/correlation without secrets/hidden reasoning; EXPLICITLY_DEFERRED full pipeline Phase 06. | V6/V7/V9. |
| NFR-009 | EXPLICITLY_DEFERRED Phase 06 measured distributions and pre-agreed release thresholds. | No false zero usage or claimed measurements now. |
| NFR-010 | CURRENT_TASK local Go/script semantics and versioned compatibility; EXPLICITLY_DEFERRED MCP Phase 05 and release regression Phase 07. | V6/V11 and Q3 migration/rollback gate. |
| NFR-011 | CURRENT_TASK definition/safety/test/scenario extension obligations, no generic primitives. | V1/V9/V10. |
| NFR-012 | CURRENT_TASK minimization/redaction/protected local audit; EXPLICITLY_DEFERRED model disclosure/egress Phase 02 and data retention/export Phase 03. | V3/V9, preserved audit retention. |
| NFR-013 | CURRENT_TASK distinguish denial/error/empty/unavailable/truncation in versioned output; EXPLICITLY_DEFERRED proposal/confidence/report UX Phase 02/04. | V6/V10. |
| NFR-014 | CURRENT_TASK placement/install prerequisite design and offline checks; EXPLICITLY_DEFERRED reproducible deployment/stopping proof Phase 06/07. | V3/V11, no live Molecule side effect. |
| NFR-015 | CURRENT_TASK deterministic credential-free fixtures; EXPLICITLY_DEFERRED release/live/model campaigns Phase 06/07. | V10/V11, report tiers separately. |

### 8.3 Acceptance criteria

| PRD | Disposition / scope of claim | Evidence required |
| --- | --- | --- |
| AC-001 | EXPLICITLY_DEFERRED Phase 02; existing approval behavior is regression-only here. | V11 digest/cancel/zero-start tests if touched. |
| AC-002 | CURRENT_TASK manual identity subset; EXPLICITLY_DEFERRED end-to-end planning identity Phase 02. | V4 exact names, missing/ambiguous, UUID guidance and preserved identity. |
| AC-003 | CURRENT_TASK unknown-tool/finite collection subset; EXPLICITLY_DEFERRED structured loops Phase 02 and graph/readiness Phase 04. | V1/V2/V5; not full AC pass. |
| AC-004 | CURRENT_TASK local SDK/script unauthorized-call and reviewed-related-read subset; EXPLICITLY_DEFERRED nested/delegated Phase 02 and resumed Phase 03. | V2/V4; no specialist enablement for a test claim. |
| AC-005 | EXPLICITLY_DEFERRED Phase 04 full domain findings; CURRENT_TASK basic/manual scenario seed only. | V10 named missing evidence, no causal invention. |
| AC-006 | EXPLICITLY_DEFERRED Phase 04 multi-server dependencies/partial synthesis. | No new scheduler. |
| AC-007 | EXPLICITLY_DEFERRED Phase 03 checkpoint/resume; CURRENT_TASK audit uncertainty does not satisfy it. | V8 scoped audit tests only. |
| AC-008 | EXPLICITLY_DEFERRED Phase 03 context/export classes. | No memory/report schema scaffolding. |
| AC-009 | EXPLICITLY_DEFERRED Phase 03 curated retrieval; CURRENT_TASK output redaction is only a prerequisite. | V9 without ingestion. |
| AC-010 | EXPLICITLY_DEFERRED Phase 04 full evidence review (initial review Phase 02). | No manual-path model/reviewer calls. |
| AC-011 | EXPLICITLY_DEFERRED Phase 07 or expressly authorized equivalent early gate; CURRENT_TASK design prerequisites only. | Operator-owned placement/read/policy/denial/postcondition evidence, not fixture proof. |
| AC-012 | CURRENT_TASK SDK/script/local validation/fixed argv; EXPLICITLY_DEFERRED MCP parity Phase 05. | V1/V2/V3/V5 every retained enabled local entry. |
| AC-013 | EXPLICITLY_DEFERRED Phase 05/07 host fixture/live scope, disabled here. | No SSH/collector activity. |
| AC-014 | CURRENT_TASK AM3/AM4 local seven-status, cancellation, safe-error/correlation and two-stage audit/failure contract; Q3 selects full target behavior. | V6/V7/V8; legacy coverage alone cannot pass target AC. |
| AC-015 | CURRENT_TASK secret canaries and no mutation, including override requests. | V9 zero prohibited disclosures/dispatch. |
| AC-016 | EXPLICITLY_DEFERRED Phase 02/07 model adapter/disclosure validation. | V10 zero inference here. |
| AC-017 | EXPLICITLY_DEFERRED Phase 02/07 model runtime inspection; CURRENT_TASK no model process/credential forwarding prerequisite. | V3/V10, no deployed isolation claim. |
| AC-018 | CURRENT_TASK manual model-independent subset; EXPLICITLY_DEFERRED provider outage/revocation/state/report Phase 02/03/07. | V10 no provider requirement. |
| AC-019 | EXPLICITLY_DEFERRED Phase 05 MCP. | No discovery or protocol change here. |
| AC-020 | EXPLICITLY_DEFERRED Phase 06 explicit disabled record or approved comparison; CURRENT_TASK manual path cannot dispatch specialists. | V2/V10 zero specialist calls. |
| AC-021 | CURRENT_TASK versioned three-scenario seed; EXPLICITLY_DEFERRED full evaluation outputs Phase 06. | V10 seed format and actual/expected safety checks only. |
| AC-022 | CURRENT_TASK tool correlation and finite call budgets/cancel; EXPLICITLY_DEFERRED full run telemetry Phase 02/06 and restart cumulative budgets Phase 03. | V5/V6/V8; no resumed-run claim. |
| AC-023 | CURRENT_TASK preflight/owner guidance; EXPLICITLY_DEFERRED live startup/lifecycle/rollback Phase 07. | V11 review only, not operational rehearsal. |
| AC-024 | CURRENT_TASK applicable local adapter/manual compatibility; EXPLICITLY_DEFERRED MCP/state/deployed-validation release gates Phase 03/05/07. | V11 required local tests and approved Q3 version/rollback. |
| AC-025 | EXPLICITLY_DEFERRED Phase 07 release record, with Phase 06 corpus/thresholds. | No fixture mislabelled deployed validation. |

### 8.4 Source-plan and accepted-invariant accounting

| Source locator | Disposition | Required outcome / gap |
| --- | --- | --- |
| Phase 01 Step 1 inventory/owner/context/relationships/startup denial | CURRENT_TASK; Q1 baseline and Q2 conditional revised-owner direction recorded, with AM1/AM2 draft constraints. | V1–V4 and detailed amendment approval before adapters. |
| Step 1 seven statuses/definitions versus retained closed contracts | CURRENT_TASK via draft AM1/AM3 under Q3's full-scope route, never extensions inside `1.0`. | Approved versioned replacement/translation; reduced scope is not selected. |
| Step 1 placement/profile | ALREADY_ACCEPTED fixed values; CURRENT_TASK preserve/document; live proof deferred. | V3; no historical shared runtime. |
| Step 2 basic/fault/flavor/network/project summary + SDK parity | CURRENT_TASK complete AM1/AM2 bounded catalog under the selected revised owner. | V2–V6/V10; exactly advertised permitted catalog. |
| Step 2 intent + terminal protocol, incomplete completion/local/shared failure stop | CURRENT_TASK via draft AM4; Q3 route is resolved and final amendment approval remains mandatory. | V7/V8 ordering, failures, restart/parallel no bypass. |
| Step 3 safety/compatibility/canaries/process/audit failure/scenario/manual guidance | CURRENT_TASK applicable local subset. Nested/resumed/MCP integration EXPLICITLY_DEFERRED as source ending requires. | V1–V11; no full deployed or full-product AC claim. |
| §01.6 phase definition of done | CURRENT_TASK all enabled local paths plus documented live prerequisites. | Full completion requires approved/incorporated AM1–AM5 and passing full-scope verification; recorded Q1–Q3 decisions are not implementation acceptance. |
| Revised runner/toolbox/identity/placement contracts (ADR F02–F10) | ALREADY_ACCEPTED invariants to preserve, not current test/deployment acceptance. | Exact versions/paths/modes/actor/event/no-fallback/no-op semantics; V3–V8/V11. |
| Baseline Stages 0–14 and PRD learning-plan boundary | OUTSIDE_SELECTED_SCOPE lessons/learner assessment and optional technology expansion. Safety/tool-calling concepts inform this task, not permission. | No extra curriculum, vector/distributed/model/DB infrastructure artifacts. |
| PRD non-goals and overview §00.5 | CURRENT_TASK binding exclusions (§5); OUTSIDE_SELECTED_SCOPE future unapproved technologies. | V2/V9 plus final diff/scope inspection. |

No applicable requirement is silently discarded. Q1–Q3 product/approach choices are now recorded; detailed amendment approval, implementation evidence and live gates remain explicit prerequisites, not “already accepted” implementation.

## 9. Verification contract for future implementation

All checks below are **required future evidence**, not tests run while authoring. Default environment has no cloud/profile/provider credentials and no network outside loopback fixtures. Use actual CLI/orchestrator/adapter entry points at the highest practical seam; do not prove safety solely by private helper tests. Fixture overrides must be internal test seams, never production command/path/profile overrides.

| ID | Required positive and negative scenarios | Existing seam / real dependency | Observable acceptance outcome |
| --- | --- | --- | --- |
| V1 | Valid definitions and startup corruption: duplicate JSON keys/names/positions, unknown fields/versions, missing metadata/limits, wrong types/defaults/paths/profiles, invalid enabled subset. | Go registry tests plus revised `test_steps_01_to_04_integration_gate.py`/registry loader fixtures. | Valid reviewed catalog loads; invalid definitions fail closed before dispatch. No independent permissive catalog. |
| V2 | Every retained enabled CLI/SDK/script entry: permitted request, unknown/generic/mutation tool, extra args, scope/cloud/project/target/profile/policy escape, direct invocation bypass, disabled agent/specialist/host paths. | Recording executor/readers, HTTP request counters, temporary executable markers; `test_request_gateway.py`, Go scopedtools tests. | Zero forbidden SDK operation/child spawn, audit attempted; valid request traverses the same authoritative boundary. Disabled path does not authenticate from ambient credentials. |
| V3 | Ambient admin `OS_*`, tokens/proxies/SSH/provider canaries; executable/profile override; missing/revoked profile; wrong owner/mode/symlink; fixed runtime-role assertions; model initialization trap. | Revised execution/profile tests, role defaults/tasks and controlled fixtures; no profile contents or live access. | Fresh minimal exact environment/fixed profile; no inherited secret/fallback; credentials/config separated; missing prerequisites unavailable/denied. Static role proof is not API policy proof. |
| V4 | Canonical UUID, supported exact name, missing, duplicate exact names, deceptive casing/substring, unsupported script identifiers; forged and valid derived port/network/subnet/flavor, wrong or missing flavor relationships and policy denial; fault absence/presence/secret message with raw details/extra specs excluded; other project/target responses and separately permitted project summary. | Go `httptest` server/ports tests; revised script fixtures; response recording. | Original/resolved identity retained; ambiguity rejected; no unintended read; reviewed relationships only. Only AM2-derived in-scope flavor reads permitted after amendment approval; volume/host/unreviewed expansion denied. |
| V5 | Exact argv, fixed cwd, no shell; API page/record/payload/memory bounds; simultaneous stdout/stderr floods, invalid UTF-8/malformed JSON, deadline/cancel before/during/after spawn, direct-parent exit with surviving descendant, exhausted limits. | Real temporary subprocess process groups/pipes on supported Linux; Go HTTP fixtures; revised `test_process_bounds.py`. | Finite bounded capture/collection, correct truncation, no orphan or open pipe, reaped owned child; zero later dispatch/retry after cancel/control failure. |
| V6 | Each retained/approved target status, empty versus unavailable/error/partial, child versus process exit, duration/time/correlation, compact deterministic serialization, closed fields and nested target shape, actual child-exit/null semantics, independent redaction/truncation combinations in AM3, explicit legacy translation without a second execution/event. | `test_result_envelope.py`, `test_audit_events.py`, CLI JSON/exit assertions, versioned fake fixtures. | Exact schema-specific maps, one complete result line, meaningful safe limitations. All seven target statuses follow approved AM3/AM4 clauses; legacy interrupted translation is not mislabelled target completion. |
| V7 | Terminal cardinality for success/error/denial/invalid/unavailable/timeout/interruption/truncation; required intent before dispatch; terminal before publication; symlink/non-regular/unsafe-path/wrong-owner/mode/archive-collision rejection, bounded log-injection-proof records, disk-full/permission/write/flush/fsync/lock/rotation failure at both applicable stages. | Revised audit event/persistence tests; injected faults plus actual temporary filesystem/locks; recording dispatch and publication sequence. | No dispatch on intent failure, no successful payload on terminal failure, no duplicate terminal adapter event, no raw filesystem leakage/fallback/replay; retained intent and committed events preserved. |
| V8 | Cross-process append/rotation and admission races, shared budgets/fault state, crash after intent/during read/after read before terminal, restart during unresolved fault, attempted concurrent next call, unresolved-intent rotation protection, control-state corruption/permissions/durable-write failure and operator-only safe re-enablement, recovery without silent replay. | Real filesystem and independent fixture processes, approved protocol failure seams; not mocks alone or only thread tests. | Non-interleaved complete bounded events; no over-admission, double dispatch, deadlock or post-fault new dispatch; incomplete/uncertain completion locally visible, restart cannot clear it; safe recovery required. No exactly-once external-read claim. |
| V9 | Nested and text secret canaries in arguments/data/errors/stderr, split chunks/multibyte/truncation, depth/work-limit/malformed values; hostile instructions and “ignore restrictions, fix/restart/edit/create/delete” requests. | Revised redaction tests and full result/audit/CLI/storage-consumer fixtures. | Zero canary/prohibited data at any enabled sink; unsafe data withheld with limitation, zero mutation/generic execution. No user-data/full-config collection. |
| V10 | Healthy server, permission denial, hostile output seed cases; manual list/invoke without model credentials/provider/knowledge/host/MCP, explicit gap/unavailable outputs. | CLI fake-model-call trap plus SDK/API/script substitutes; versioned offline scenario expected/actual records. | Useful manual output with zero inference/specialist/host/MCP calls and honest limitations. No learned/semantic/root-cause or deployed-policy claim. |
| V11 | Existing Go manual/identity/planning tests, reviewed snapshot/exact approval/no-start regressions; revised runner/toolbox/static checks; AM5 mixed-version inspection/incompatible-consumer rejection, no event flattening or in-place conversion, disable-new-path rollback without evidence deletion or bypass; guidance/revocation owner review. | Repository Go Makefile/test packages, revised unittest suite, static diagnostic checker; synthetic legacy envelopes and untouched state/audit fixtures. | Required local checks actually pass; incompatible consumers remain gated until approved migration; prior paths/data unchanged and unsafe legacy bypass not reenabled. Deployment/Molecule live acceptance remains unrun without permission. |

### 9.1 Required execution-time commands and evidence

The executor must discover available tools and run focused tests first, then repository-required offline verification. Representative repository-native commands (adjust focused package paths only to actual implementation):

```bash
cd aiops
rtk go test ./internal/tools ./internal/scopedtools ./internal/planning ./internal/workflow
rtk go test -race ./internal/tools ./internal/scopedtools ./internal/planning
rtk go test ./...
rtk make build
```

Apply `gofmt` to changed Go files and prove clean formatting; verify the actual new concurrency boundary under `-race` and cross-process tests, not only the unchanged packages above. `aiops/Makefile` supplies the full Go test/build baseline. Do not run the root Makefile as an innocent wrapper: it includes local `.env`; root Molecule test targets can contact the lab.

For changed/reused revised Python behavior, from repository root, only after confirming the user-provided environment (the generic token below is an execution-time input, not a private path to commit):

```text
rtk <confirmed-venv-python> -m py_compile <changed-python-files>
rtk <confirmed-venv-python> -m ruff format <changed-python-files>
rtk <confirmed-venv-python> -m ruff check --ignore EXE001 <changed-python-files>
rtk <confirmed-venv-python> -m unittest discover -s ansible/ai_ops_assistant/tests/tool_runner -p 'test_*.py'
```

Run JSON syntax/closed-schema validation for any changed registry and the full applicable revised runner suite even when Go calls it unchanged. Run `rtk bash scripts/check_ai_ops_revised_diagnostic_toolbox_safety.sh` and applicable revised manual toolbox fixtures; use `bash -n`/existing shell lint for changed scripts. The existing shell fixture's explicit test jq path is not approval to change the production `/usr/local/bin/jq` contract. Ansible YAML/syntax/lint/static checks are mandatory if deployment files change; no host/check-mode/apply or Molecule smoke/E2E without explicit authorization. Do not invoke historical runner/registry or assume historical test commands are permitted.

Finish with full tracked/staged/untracked changed-path and diff review, `rtk git diff --check`, source/symbol/import/path checks and a security review of credentials, subprocess/environment, filesystem locks/durability, retained data and bypasses. Do not introduce new tooling/dependencies simply to make a command pass. Missing required verification environment is a reported blocker, not a skipped green check. Never weaken safety tests to match an unsafe implementation.

### 9.2 Separately authorized deployed evidence

AC-011/Phase 07 must demonstrate actual observer separation, only justified management/API routes, exact fresh reader profile/policy, approved reads and valid disposable create/update/delete denials with independent administrator no-change postconditions and cleanup ownership. Record only permitted outcome-only evidence at owner-approved protected locations; keep raw identifiers, envelopes/audit lines, addresses, catalog, comparator data and credentials transient/outside Git. Stop/revoke on unexpected mutation or disclosure; no agent cleanup or probe tool. Those operations are not authorized by future offline test success.

## 10. Implementation decision authority

| Level | Granted authority after task approval | Boundary |
| --- | --- | --- |
| LEVEL_0 | Compile/debug/format, construct safe fixtures, add focused tests, fix in-scope failures and ordinary integration defects. | No repeated human permission needed for these routine steps. Substantiate review findings before repair. |
| LEVEL_1 | Internal packages/helpers, compliant validators/adapter shape, finite collection algorithms, internal fixture seams, safe admission/fault coordination and lock ordering within approved contracts. | Choose autonomously and document meaningful choices. Preserve fixed audit mechanism/paths/modes when retained; no material behavior/security change. |
| LEVEL_2 | Change to the recorded Q1 baseline, selected Q2 owner or Q3 full-scope direction; final governing amendment approval; changes to fixed placement/identity/permissions/retention or material risk; new infrastructure/dependencies, live/deployment/credential actions, destructive operations or later-phase scope. | Q1–Q3 choices are recorded, not open questions. Human approval still governs new material decisions and detailed amendments; general autonomy/tests do not supply it. |

ADR §6 records Q1–Q3 evidence, bounded decisions and the remaining formal amendment gate; no additional unanswered Level 2 choice is identified for drafting. For any new material issue, investigate and provide category, evidence, alternatives, recommendation, exact decision needed and independently safe remaining work. Continue independent in-scope work only when separately authorized and it cannot prejudge the decision. Multiple safe mechanism choices are not a Level 2 blocker. Do not amend authoritative sources merely to remove a contradiction.

## 11. Completion criteria and future review evidence

The future executor may report **READY_FOR_REVIEW** only when:

- The approved committed task/architecture/source identities, actual implementation base and initial working tree are recorded; the recorded Q1–Q3 choices are preserved and AM1–AM5 are approved/incorporated without silently reducing the selected full scope. No gap is hidden by changing a status label.
- One selected owner/definition source is observable at every retained enabled local diagnostic entry; gap matrix names disabled/deferred paths. Unauthorized requests never dispatch, SDKs have no ambient/direct bypass and manual diagnostics need no model.
- All selected scope/relationship/profile/identity/collection/result/audit/no-replay/mutation/privacy obligations and applicable V1–V11 cases pass. Full target completion includes the approved seven-status/intent protocol; legacy preservation alone is not enough.
- Required audit durability, real-filesystem cross-process concurrency, crash/fault/cleanup and compatibility regressions ran successfully. Current audit/control faults prevent new dispatch and payload publication as specified; no audit erasure simulates rollback.
- Scenario seeds and manual/deployment-preflight/extension/revocation guidance exist, with versions and exact limitations. No future modules or unapproved catalog entries are scaffolded.
- Required repository offline verification passes; source-presence-only, mocks-only concurrency/durability claims and historical acceptance are insufficient. No fixture is labelled deployed policy/runtime/egress proof.
- Complete final diff (including new files) is inspected; unrelated changes are removed without overwriting pre-existing work. No secret/local `.env`/profile/raw evidence is committed. No staging/commit/push/deploy is implied.

Required review evidence packet:

1. Approved source and amendment references, implementation base, exact candidate revision/worktree and changed paths/components; accepted dependencies distinguished from source observations.
2. Entry-point/capability gap matrix and per-requirement/AC disposition, including local subset versus nested/resumed/MCP/deployed evidence.
3. Significant Level 1 choices and parity/migration/rollback decisions, with applicable versions and consumers; unresolved Level 2 items, if any.
4. Actual commands, environment/tool versions and results, focused/full test counts where available, formatting/static/security checks, subprocess/PID cleanup, filesystem/crash/concurrency and manual fixture outcomes. Explicitly list failed, unavailable, skipped and unverified checks.
5. Sanitized evidence references for no-dispatch denials, scope/relationship positives/negatives, status/exit mapping, pre-sink canaries, audit ordering/cardinality/durability, intent/terminal faults, shared stop and restart recovery. No raw operational acceptance material in Git.
6. Known limitations and separately gated live operations; exact final status and assurance that no source requirement/security guarantee was silently changed.

Future execution verdicts: **READY_FOR_REVIEW** = approved bounded implementation complete and required verification passed; **BLOCKED** = unresolved decision/access/control prerequisite prevents completion; **INCOMPLETE** = unfinished authorized work/checks. Review readiness is not human acceptance, merge or deployment. Implementation self-check does not replace independent fresh-session review.

## 12. Sources, authoring checks and remaining limitations

The complete source hierarchy, binding contract links, observed interfaces and F01–F12 fidelity register are in [ADR §§1–3 and §7](../architecture/01-safety-boundary-and-manual-slice-adr.md). Primary source locators are Phase 01 §§01.3–01.6, overview §§00.4–00.7, PRD functional/non-functional/acceptance and non-goal sections, and the binding revised runner/toolbox/identity/placement contracts. Later-phase ownership follows overview §00.7; [Phase 03](../implementation-plan/03-durable-state-and-knowledge.md) explicitly separates checkpoint intent from the closed audit protocol.

Authoring evidence for this approval-revision pass: HEAD remains `0182da9f7c2b322df5da49262748974009db7332`; starting and ending worktrees contain only these two pre-existing renamed untracked drafts, with no tracked/staged change. The original full-source inspection remains applicable because governing tracked sources are unchanged. Both revised documents are reread through their endings and checked against the saved pre-revision contents, preserving the user's filename/cross-reference and `$HOME` portability edits. Read-only document validation passes all 29 local links/anchors, 42 FR + 15 NFR + 25 AC unique disposition rows, 12 fidelity rows, five cross-linked amendment clauses, complete tables/fences/endings and whitespace/stale-decision checks. Tracked/staged `git diff --check` and explicit untracked-document whitespace checks are required for this candidate; complete untracked contents and revision differences are reviewed, not omitted by plain `git diff`. No implementation tests/builds/formatters, source-contract amendment, runtime probe, commit or deployment is performed. These are author self-checks, not independent review/approval or implementation verification.

Remaining limitations: these detailed AM1–AM5 clauses and the revised drafts have not completed independent review, human approval, incorporation into governing contracts or commit. Actual test/toolchain/deployment/credential readiness is unverified. Q1–Q3 choices are recorded, not waiting for the same approval again. Missing live proof keeps live capabilities disabled; no source/security weakening, new audit sink, DB, state migration or stakeholder rationale is inferred. Draft wire/version choices are identified explicitly rather than attributed to the user.

**End of DRAFT task contract. Q1–Q3 decisions are recorded; review, approve, incorporate and commit the detailed specifications/amendments before separately authorized implementation preflight or execution.**
