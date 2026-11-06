# DRAFT ADR — Phase 01 authoritative diagnostic safety boundary

**Status:** DRAFT; proposed architecture, not approved or executable authority.

**Project:** aiops openstack lab; existing project with partial implementation.

**Source scope:** [01. Safety Boundary and Manual Slice](../implementation-plan/01-safety-boundary-and-manual-slice.md), Steps 1–3 and definition of done.

**Related contract:** [DRAFT bounded Phase 01 task](../tasks/01-safety-boundary-and-manual-slice-task.md).

**Approval reference:** `Approved-phase-01`, supplemented by the user's Q1–Q3 decisions recorded in §6. Q1 confirms the Phase 01 requirements baseline at `0182da9f7c2b322df5da49262748974009db7332`; Q2 approves compatibility-first revised-runner reuse subject to scope/parity proof; Q3 selects versioned amendments for full Phase 01 behavior.

**Disposition:** Ready for independent draft specification review, not implementation. The product/approach choices are recorded; the detailed amendment clauses remain DRAFT proposals requiring review, approval and incorporation before activation. This ADR neither approves itself nor edits governing sources.

## 1. Source hierarchy and revision record

1. Repository instructions are exposed by `.agents/AGENTS.md`, a symlink to `$HOME/.agents/AGENTS.md`; there is no root `AGENTS.md` at the inspected revision. The session also supplies `$HOME/.pi/agent/AGENTS.md`. They require explicit scope, committed approved task contracts, independent review and Level 0/1/2 authority separation.
2. The canonical [Go PRD](../prd.md) defines intended product behavior. Its file header and [Overview 00](../implementation-plan/00-implementation-overview.md) still describe draft status and historically missing approval. The later user Q1 confirmation in §6 approves **only the Phase 01 requirements in the PRD and source plan at the recorded revision**. It does not approve all later phases, alter those source files, or authorize implementation/deployment. Q2/Q3 record the selected approach and amendment route, not approval of every newly drafted wire detail.
3. Source plan §01.4, “Constraint reconciliation and authority,” expressly preserves the revised placement, identity, selective-reuse and runner contracts. Their fixed constraints govern this integration until specifically amended. Revised phase numbers are not Go phase numbers. Later restricted-host amendments do not grant this task host access.
4. [Knowledge base](../../base-knowledge.md), [architecture study](../../architecture.md), root `README.md` and `docs/README.md` describe existing lab topology and validation. They do not grant diagnostic privileges. The [baseline](../aiops-baseline.md), including its ending curriculum, is conceptual/educational; generic coding, deployment, database and write-approval examples are not product capabilities.
5. Current code and test sources establish observed seams, not accepted deployment or a fresh passing baseline. These two new draft files are below all approved sources in authority.

| Observation | Recorded state |
| --- | --- |
| Inspection base / candidate implementation-base proposal | `0182da9f7c2b322df5da49262748974009db7332` |
| Branch | `aiops-go-phase01` |
| Original authoring working tree | Clean before the first drafts were created. |
| Approval-revision starting tree | Only these two untracked drafts, already renamed to their current `01-...-adr.md` / `01-...-task.md` paths. Existing user filename, cross-reference and `$HOME` portability edits are preserved. No tracked or staged changes. |
| Approved requirements baseline | Q1 confirms Phase 01 requirements in `docs/aiops-go/prd.md` and `docs/aiops-go/implementation-plan/01-safety-boundary-and-manual-slice.md` at `0182da9f7c2b322df5da49262748974009db7332`. This is not whole-PRD/later-phase approval. |
| Future implementation base | Current HEAD is the inspected code baseline; future preflight must identify the actual base after approved specifications/amendments are committed. No implementation authorization is inferred. |
| Selective-reuse provenance | Manifest pins repository `0fbc8a45d5a31e5728caafe90d3cda7da616c911` and historical runtime tree `3abc4bcf3fa4caf1c6d89f8d25865e2c0aef8e07`. Read-only Git object resolution confirmed that tree at the pin and at current HEAD. This is not complete per-path dependency review or activation permission. |
| Authoring candidate | Only `docs/aiops-go/architecture/01-safety-boundary-and-manual-slice-adr.md` and `docs/aiops-go/tasks/01-safety-boundary-and-manual-slice-task.md`, new untracked Markdown files; not staged or committed. |

At initial inspection no repository approval record/ref/message matching `Approved-phase-01` existed. The subsequent user confirmations reproduced in §6 now supply the missing Phase 01 approval provenance; these drafts record them without inventing a tracker reference, timestamp or separate signed record.

## 2. Context and observed integration seams

The approved safety direction is one deterministic, deny-by-default boundary. Manual diagnostics must work without inference. A registry describing a read operation is not proof that every caller is scoped, credentials are least-privileged, collection is bounded, output is safe, or audit publication is durable.

| Observed source | What exists / what it does not establish |
| --- | --- |
| `aiops/internal/tools/registry.go`, `NewRegistry`, `Registry.Execute` | Rejects duplicate/empty names and unknown tools; dispatches raw arguments without explicit application authorization context, durable audit or general limits. |
| `aiops/internal/openstackclient/compute.go`, `network.go`, `project.go` | Uses `AuthOptionsFromEnv`; Neutron client extracts authenticated project ID. This is not approved dedicated-profile isolation and cannot remain an ambient-admin fallback in an enabled Phase 01 path. |
| `aiops/internal/tools/get_server.go`, `get_flavor.go`, `get_ports.go` | UUID/exact-name resolution, fault/flavor observations, and bounded project/device-filtered port reads are reuse seams. Server name lookup uses `AllPages`; flavor extra-spec errors can carry raw error text; server output includes host/fault detail absent from the initial revised projection. Existing SDK behavior is not new disclosure or capability approval. |
| `aiops/cmd/openstack-agent/main.go`, `openstack-workflow/main.go`, `openstack-project/main.go` | Each constructs SDK clients and a registry directly. Agent/workflow execution reaches that registry. These are integration/bypass candidates, not already compliant entry points. `openstack-ai` is model chat without diagnostic wiring, not the requested manual tool interface. |
| `aiops/internal/scopedtools/broker.go` and its tests | Specialist role/project/target/flavor checks, shared mutex-protected call budget, response-scope checks and a reader-function seam exist. They are not the general cloud/profile/audit boundary; do not enable specialists to reuse them. |
| `aiops/internal/planning/prepared.go`, `review.go`, `planning_test.go`, `review_test.go` | Exact-digest approval, immutable preview/tasks, in-memory single-start, cancellation/non-ready zero-start and original goal/exact-name regressions exist. Preserve them; full planning integration belongs to Phase 02. |
| `aiops/internal/workflow/review_snapshot.go` | Constructs specialist selection/dispatch during review. It must not be invoked by the manual path; Phase 02 owns gating it when integrating investigations. |
| Revised runner `ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/aiops_tool_runner.py` | Fixed argv/environment, six-status result/audit builders, locked/fsynced terminal audit and subprocess seams exist. `main` executes before `emit_result_outcome`; there is no durable pre-dispatch intent or general application-scope admission. Per-process terminal failure does not establish a shared/restart-safe stop-new-dispatch protocol. |
| Revised `tool_registry.json`, runner role defaults/tasks and `test_profile_isolation.py` | Current closed source registry has **seven** tools, including separately governed operator/host tools, not just the initial three. Role deployment defaults disabled. Do not delete later accepted entries or enable them as part of Go Phase 01; reconcile an exactly permitted local subset without an independent permissive registry. |
| Revised diagnostic scripts/helper | Initial three diagnostics, conservative identifiers, selected fields, explicit empty/partial/error sections and requested-server network relationships exist. Script post-collection slicing alone is not proof of bounded API collection/memory; parity must verify collection-time bounds. |
| `aiops/internal/agent/filestore.go` | Protected temporary-file, sync and rename foundation; not whole-investigation transactionality or writer exclusion. No AI-OPS SQL migrations were found in tracked `aiops/` paths. No database, DB role, stored procedure or migration framework is required here. |

Relevant revised test seams include `tests/tool_runner/test_request_gateway.py`, `test_execution_gateway.py`, `test_process_bounds.py`, `test_result_envelope.py`, `test_result_redaction.py`, `test_audit_events.py`, `test_audit_persistence.py`, `test_profile_isolation.py` under `ansible/ai_ops_assistant/`; Go HTTP fixtures are in `aiops/internal/tools/get_server_test.go` and `get_ports_test.go`. Inspection is not execution or acceptance.

## 3. Decision fidelity register

F01–F12 are **local traceability row labels, not invented approved decision IDs**. `Approved-phase-01` and the user Q1–Q3 confirmations in §6 provide decision provenance. “Binding” means a retained existing constraint; “target” means the approved full Phase 01 behavior whose detailed versioned amendment is drafted in task §6.6. AM1–AM5 identify proposed amendment clauses, not already approved source changes. Original stakeholder rationale beyond the sources was not provided; engineering consequences in §4 are the author's reasoning.

| Row / authority | Affirmative rule and explicit negative/no-op rule | ADR consequence | Task location / future proof |
| --- | --- | --- | --- |
| F01 — plan §01.4, Step 1 | Q2 selects compatibility-first reuse of the eligible **revised** runner as policy/registry/dispatch owner, subject to actual-boundary scope/parity proof; a Go-owned replacement is not an automatic fallback. Never copy/install/import/execute historical runner/registry. | §4.1; Q2 | §§2–4; V1/V2 entry-point inventory and no-dispatch tests. |
| F02 — placement/foundation contracts | `assistant02`, group `ai_ops_assistant`, user/group `aiops_assistant`, root `/opt/openstack-ai-ops-assistant`; distinct from `assistant01`; management/API routes only when justified. No historical shared state, listener, provider or host-route activation. | §4.2 | §§2, 6; V3 isolation/metadata; live AC-011 deferred. |
| F03 — identity contract | Fresh `aiops-assistant-project-reader`, domain `default`, project label `admin`, role `reader` only; restricted fresh credential, one-month expiry, admin-team rotation/revocation. `admin` is not admin authority. No historical/human/member/service/admin or profile fallback. | §4.2 | §6; V3 ambient-credential/direct-invocation negatives; current deployed gate separate. |
| F04 — plan Steps 1–2; PRD FR-010–FR-011 | Trusted application context binds actor/client classification, cloud/project, canonical targets, capability/profile, policy/approval, correlation and finite budgets. Derive relationships from authorized observations, separately permit project summaries and deny unreviewed flavor/volume/host reads. Model/client claims confer no authority. | §4.1 | §§3, 6–7; V2/V4/V9. |
| F05 — plan Step 2; PRD FR-003; toolbox contract | Keep original/resolved identity; canonical UUID and exact-name resolution, missing/ambiguous rejection and UUID guidance for narrower scripts. Script identifier is nonempty ASCII `[A-Za-z0-9._:-]+`, at most 255 bytes, no slash or `..`. Do not case-fold names, invent name uniqueness or silently widen validation. | §4.3 | §7; V4 identity and no-unintended-target tests. |
| F06 — runner Steps 1–4; plan Steps 1–2 | Initial project tools are `project_resource_summary`, `server_basic_info`, `server_network_info`; fixed mappings, closed validation and argv, fresh minimal environment, finite limits. No caller command/path/profile/limit override or generic executable tool. Current later seven-tool source is not a grant to this task. | §4.1–4.3; Q3 | §§3–5; V1/V2/V5; AM1/AM2 draft the versioned definition and bounded fault/flavor extension. |
| F07 — runner Steps 5–7 versus plan target | Binding schema `1.0` has exactly six statuses/exit mappings; interruption is `error` / `interrupted`, not `cancelled`. Plan/PRD target adds `cancelled` and independent redaction metadata. No silent seventh status/extra field. | §4.4; Q3 | §§6.6–7; V6; AM3 proposes explicit `2.0` outcomes, never extra `1.0` fields. |
| F08 — runner Steps 5–7 | Runner generates UUIDv4 correlation/time, fixed actor `local_cli`; one terminal `tool_request_completed` audit attempt per request, including denial. Audit records identifier presence, not identifiers or payload. No client actor/correlation injection and no duplicate adapter audit. | §4.4 | §§6–7; V6/V7 cardinality, time, minimum-disclosure tests. |
| F09 — plan Steps 2–3 target; runner persistence minimum | Durable sanitized intent before dispatch; terminal durable audit before success; intent failure means no dispatch. Terminal failure withholds payload/raw details, never redispatches, preserves intent, exposes incomplete completion locally and blocks further calls until recovery. Two-stage event protocol requires amendment first. | §4.5; Q3 | §6; V7/V8 fault/crash/concurrency tests. |
| F10 — runner audit filesystem contract | Fixed audit directory/file/lock, `0700` directory, `0600` files/archives, exclusive `flock`, flush+fsync, 16 KiB event bound, 1 MiB rotation, archives `.1`–`.3` only. Reject unsafe paths; no fallback sink, compression, age deletion or automatic unsafe-path repair. | §4.5 | §6; V7/V8 real-filesystem tests and retained regressions. |
| F11 — plan Steps 2–3; PRD FR-029–FR-030 | Minimize/redact before any public/storage/model/stream sink; withhold untransformable sensitive data. No user-data/full configurations. Fix/restart/edit/create/delete requests never invoke mutation, even with operator insistence. | §4.2–4.5 | §§5–7; V5/V9 secret/injection/mutation tests. |
| F12 — plan §01.6 and overview §00.5 | Default verification offline, no credentials/model; manual catalog/invoke useful without inference. No live enablement without Phase 07 or separately authorized equivalent deployed gate. Fixtures never prove reader policy/isolation. | §§4–7 | §§2, 5, 9–11; V10/V11, scoped evidence declarations. |

## 4. Proposed architectural decision and constraints

### 4.1 One actual enforcement boundary, not a wrapper-only policy

The proposed architecture extends the selected existing responsibility, not parallel policy owners. Every retained enabled local diagnostic path must pass startup definition validation, per-call scope/profile/relationship authorization, bounded dispatch, sanitization and required audit publication. All SDK paths must enter the same boundary or remain disabled; the `tools.Registry` interface alone is insufficient.

Inventory direct CLI, SDK, agent, workflow, project, specialist and runner entry points and compatibility consumers; classify each as enabled and tested, disabled, or outside this delivery under an independently preserved contract. A Go wrapper cannot claim actual-boundary authorization if the same client can invoke a credential-bearing runner or SDK path without its scope checks. Resolve trusted context transport and direct invocation before enabling adapters. Local client text is untrusted; the retained `local_cli` audit actor is a classification, not authenticated human identity. Do not forward application actor/correlation into the closed legacy audit schema.

Q2's approved direction is to retain/harden the eligible revised runner as the one policy/registry/dispatch owner, subject to actual-boundary scope and parity proof. Go is its manual/client integration, not an independent policy owner. SDK helpers must execute under that owner's validated scope/credentials/audit path or remain disabled. A failed feasibility/parity check stops dependent integration; it does not authorize silently switching to a Go-owned replacement. Helper layout, safe trusted-context transport, SDK implementation language and compliant generated version views are Level 1 within that direction.

### 4.2 Least privilege and deployment separation

Retain the exact revised host, namespace, profile locations and metadata from the binding contracts. Executable/configuration locations are root-owned and not writable by the diagnostic caller; only protected approved data areas are runtime-writable. Reader profile directory is `0700`, files are regular non-symlink `0600`, owned by `aiops_assistant:aiops_assistant`. Profile contents/IDs/tokens, generated cloud files, `.env`, protected inventory and raw audit evidence are not authoring inputs or repository artifacts.

Diagnostic credentials, provider authentication, host keys and application state have separate access boundaries. This task adds neither a provider nor a model runtime; no manual path initializes inference. No permission error selects a different profile. Optional operator/SSH/host/MCP capabilities remain disabled for this delivery. Historical acceptance of narrowly scoped transport/host exceptions is not permission to generalize them. The local SSH waiver is only for `assistant02` in the `local` inventory; other environments retain verified host identity.

Dedicated-reader labels do not establish effective API privileges. Phase 01 specifies operator-owned read and disposable create/update/delete-denial procedures and lifecycle ownership; Phase 07 (or separately authorized equivalent) proves actual policy and routes. Conclusive denial needs the approved authorization signature **and** independent administrator postconditions; malformed input, 404, network/auth failure or a “reader” role name is insufficient. No probe is a registered tool; runtime credentials never clean up unexpected mutations.

### 4.3 Catalog, identity and collection

The first useful path is server basics, followed only by the permitted network relationships and separately authorized project summaries. Preserve the toolbox selected field projection, section bounds and exact script parameter rules; AM2 proposes a narrow versioned server fault/flavor extension for full Phase 01; it does not permit raw fault details, flavor extra-spec/configuration dumps, attachments, project-wide/host discovery or extra commands merely by renaming an SDK tool. Model-provided resource relationships are not evidence. Review visible related resources and their scope at each lookup; reject response identity/scope mismatch.

Resolve exact names only through separately scoped/disclosed bounded reads, never guessed matching. Do not impose globally unique names or arbitrary new casing/Unicode rules. Unsupported direct script identifiers receive UUID guidance; they are not passed to the script after permissive normalization. Preserve original input separately from canonical resolved identity.

Finite limits cover API pages/records, aggregate payload and collection memory, elapsed time, retry count, concurrent work and both output streams. Registry ceilings remain binding; adapters may tighten but not silently loosen them. Denials, invalid requests, audit/control failures and interrupted calls are not transient retry candidates. Cancellation stops new dispatch, terminates/reaps owned descendants and closes pipes even if the direct child exits first. No cloud/host mutation is introduced by local audit/state writes.

### 4.4 Versioned outcomes and audit identity

Until amended, the retained runner uses closed result schema `1.0`: `ok:0`, `error:1`, `denied:2`, `validation_error:3`, `timeout:4`, `unavailable:5`. Truncation is metadata, never a status; cancellation/interruption maps to nonzero `error` with normalized `interrupted` reason and full cleanup. Successful empty diagnostic sections remain `ok`/`empty`; missing/denied/failed collection never becomes empty success. Child exit code and runner process exit are distinct; implementation differences from the written contract require reconciliation rather than blessing code by observation.

Q3 selects the full seven-status, richer-metadata and intent/terminal protocol through versioned amendments, not reduced scope or silent `1.0` extension. Task §6.6 supplies proposed AM1–AM5 replacements and compatibility/rollback obligations for review. Approval of that route is not automatic approval of the newly authored field/exit representations; detailed governing amendments must be reviewed, approved and incorporated before activation. With the legacy protocol there is exactly one runner-generated terminal event attempt, not an adapter-generated duplicate. Planning cancellation with no tool request executes no task and does not invent a tool audit event. A tool request rejected before execution still attempts its required terminal audit.

### 4.5 Publication integrity, concurrency and recovery

A read against OpenStack and local audit writes cannot form one ACID transaction. Do not claim exactly-once external execution or roll back an observation by deleting committed audit. The required boundary is **durable authorization/intent before dispatch and durable terminal audit before successful evidence publication**, once its protocol is approved. Safe normalized fault reporting remains available if the audit sink fails; it is not a fallback audit sink and includes no diagnostic payload or raw filesystem error.

Use the retained audit filesystem rules exactly unless an approved amendment changes them. Serialize append/rotation across processes, not just goroutines. Coordinate admission, finite shared budgets, cancellation and audit-health failure across all concurrent callers to that boundary. Once a required-control fault is observed, no new call is admitted until safe recovery; already admitted work is bounded/cleaned and must not publish unaudited success. Restart or another process must not bypass an unresolved fault. Mechanism is Level 1 within approved protocol/storage constraints; permission to add a new sink/path/schema is not implied.

Every dispatched request has its required durable intent; every request including denials attempts its terminal event; no successful payload is published before required durability. On terminal write/flush/fsync/rotation failure preserve durable intent and any already committed event, mark completion incomplete/uncertain locally without relying on the failed sink, suppress current payload, and never replay the read automatically. Safe operator recovery fixes the original control boundary, not unsafe-path auto-repair or audit deletion. Phase 03 owns resumable investigation state, cumulative recovery budgets and intentional fresh re-observation; this task does not build a resumable scheduler.

## 5. Alternatives, consequences and Level 1 latitude

- **Selected direction — eligible revised runner retained:** Approved under Q2, subject to actual-boundary scope/parity proof. Reuse fixed script/credential/process/audit protections and fixture seams, adding the AM1–AM5 versioned full-scope contracts. A permissive Go precheck around the stock runner is insufficient.
- **Not selected — Go-owned replacement:** Remains an alternative only if separately approved after a substantiated revised-runner feasibility blocker. Q2 does not authorize it as an engineering fallback. Go SDK/HTTP fixture reuse under the selected owner remains permitted.
- **Safe Level 1 choices after approval:** Internal package/helper organization, standard-library validators, fake/HTTP/subprocess fixture construction, compliant bounded capture algorithms and admission/fault coordination. Preserve specified `flock`/paths/rotation for the retained audit contract. New dependencies/infrastructure, weakened durability or a different closed contract are not Level 1.
- **Rejected:** Historical runtime activation; two independently editable permissive registries; ambient admin credentials; generic commands; scope only in planner prompts; auditing only success; in-memory-only claims of durable intent; automatic replay after audit failure; broad new DB privileges or a database added solely for this task.

Engineering consequences: parity costs more than envelope translation; many existing Go paths must be routed or disabled. Unavailable evidence must remain explicit, but Q3 did not select a smaller delivery: full Phase 01 behavior and its amendment/verification obligations remain required for task completion. Source code's seven-tool catalog must be preserved under its separate contracts, not flattened to three by destructive migration.

No cloud resource IDs, names, relationships or existing application state may be rewritten in place. There is no DB migration in the observed AI-OPS seam. Any versioned result/audit/registry transition needs fixture-based compatibility, untouched legacy state/audit, explicit consumer selection and rollback that disables the new path without reviving an unsafe bypass. Runtime installation (including any proposed Go runtime artifact), routes and credential provisioning remain separately authorized operations. AM4 normally doubles audit-event count for dispatched requests within the unchanged size/archive bounds; unresolved intents may halt rotation/admission rather than be evicted. That availability/retention tradeoff and any protected control-state artifact are explicit draft amendment review items, not silent changes to the accepted audit filesystem.

## 6. Recorded human decisions and amendment gate

### Q1 — Phase 01 requirements baseline confirmed

**User evidence:** After approving the Q1/Q2 recommendations, the user answered `Q1: Yes` to the explicit question whether approval covers the Phase 01 requirements in the PRD and source plan at `0182da9f7c2b322df5da49262748974009db7332`.

**Disposition:** Resolved for that bounded requirements baseline. This does not approve unrelated PRD/later-phase work, these subsequently revised drafts, a future code candidate, staging/commit or deployment. The source headers are not edited retroactively.

### Q2 — Compatibility-first revised-runner direction confirmed

**User evidence:** `Q1 and Q2 I follow and approve the recommendation`. The recorded recommendation prefers revised-runner reuse **if actual-boundary scope and shared fail-closed behavior can be proven**; the subsequent assistant clarification retained that condition.

**Disposition:** Use the eligible revised runner as the policy/registry/dispatch owner, not the historical runtime. Preserve the existing initial project relationship rules; AM2 drafts the bounded full-Phase-01 fault/flavor visibility without granting broader project/operator/host access. Current deployed policy, routes and profile verification remain live gates. A feasibility blocker requires substantiated escalation, not an unapproved Go replacement. Routine compliant adapter/helper choices remain Level 1.

### Q3 — Full Phase 01 through versioned amendments selected

**User evidence:** `Q3: versioned amendments for full Phase 01 behavior`.

**Disposition:** The reduced legacy-compatible slice is **not** selected. Draft AM1–AM5 in the companion task §6.6 retain full server basics/fault/flavor/network/separately scoped summary behavior, seven statuses and durable intent plus terminal auditing, while preserving privilege, data-minimization, audit-integrity and no-replay constraints. Their exact wire representations are proposed engineering choices for review, not words supplied by the user or already approved contract amendments.

| Draft amendment | Governing contracts affected | Proposed replacement / invariant retained |
| --- | --- | --- |
| AM1 — ownership/definitions/context | Runner Steps 1–4; source-plan reconciliation | Revised owner, versioned closed definitions and trusted application context; no parallel permissive registry or public override. |
| AM2 — bounded manual catalog | Manual toolbox and runner capability/field mappings | Versioned fault/flavor extension plus initial network and separately scoped summaries; no new profile, host access, attachment traversal or raw configuration. |
| AM3 — public outcomes | Runner Steps 1–4 status/exit map and Steps 5–7 result schema | Proposed result `2.0`, seven logical statuses, safe target and independent redaction/truncation metadata; frozen `1.0` remains unchanged. |
| AM4 — intent/terminal/control integrity | Runner Steps 5–7 event cardinality/schema/persistence; any role file allowlist affected by approved control-state materialization | Proposed audit `2.0`, durable pre-dispatch intent and one terminal attempt; shared failure stop and truthful crash uncertainty; same audit root, least privilege and no fallback sink. |
| AM5 — consumers/migration/rollback | All affected runner/toolbox/result/audit consumers and deployment assertions | Explicit version selection and compatibility evidence; no audit flattening, silent migration, weaker fallback or unscoped legacy entry. Host/MCP/state integration stays deferred. |

**Remaining approval gate, not an unanswered product choice:** Independently review these drafts, approve the detailed amendment clauses and incorporate them into the governing contracts through a separately authorized documentation process before implementation/activation. This session changes only these two drafts. No source contract, registry, runtime file or accepted deployment is amended by this decision record.

No additional Level 2 product decision is identified for preparing these drafts. New evidence requiring a change to the chosen ownership, required behavior, fixed deployment/credential boundary or accepted risk still requires Level 2 escalation. Missing live evidence blocks **live use**, not properly authorized offline work.

## 7. Traceability, verification and authoring boundary

The companion task §§8–9 maps all FR-001–FR-042, NFR-001–NFR-015 and AC-001–AC-025 to current work, preserved accepted invariants, named phase deferrals, exclusions or explicit gaps. It also maps source-plan Steps 1–3. Partial acceptance is never a full-criterion pass. F01–F12 link each source rule to both drafts and observable tests.

Binding references, read through their endings:

- [Placement](../../ai-ops-revised/runtime/runtime-placement-contract.md), [foundation](../../ai-ops-revised/runtime/foundation-operations-contract.md), [identity](../../ai-ops-revised/runtime/identity-policy-operations-contract.md), [selective reuse](../../ai-ops-revised/runtime/selective-reuse-manifest.md).
- [Manual toolbox](../../ai-ops-revised/runtime/manual-diagnostic-toolbox-operations-contract.md), [runner Steps 1–4](../../ai-ops-revised/runtime/tool-runner-safety-gateway-steps-01-to-04-operations-contract.md), [runner Steps 5–7](../../ai-ops-revised/runtime/tool-runner-safety-gateway-steps-05-to-07-operations-contract.md).
- Runner [Steps 1–4 ADS](../../ai-ops-revised/implementation-plan/ads/04-00-tool-runner-safety-gateway-steps-01-to-04-ads.md), [Steps 5–7 ADS](../../ai-ops-revised/implementation-plan/ads/04-01-tool-runner-result-audit-safety-regression-ads.md) and [revised Phase 04 plan](../../ai-ops-revised/implementation-plan/04-tool-runner-safety-gateway.md). Later fixed operations contracts constrain mechanisms proposed in older ADSs.
- Restricted-host [Steps 1–4](../../ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-steps-01-to-04-operations-contract.md) and [Steps 5–7](../../ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-steps-05-to-07-operations-contract.md): inspected to account for current seven-tool source; their run-specific acceptance grants no Go Phase 01 host scope.
- [Go Phase 03 recovery](../implementation-plan/03-durable-state-and-knowledge.md): owns later resumability, not authorization to extend this runner audit contract.

The first authoring pass completed full-source inspection and document checks. This approval-revision pass preserves the user's renamed files and portability edits, records Q1–Q3 and adds draft AM1–AM5; its own full rereads, cross-document fidelity/requirement/link checks and complete pre-existing-untracked-versus-revised diff review are recorded with the task's authoring evidence. HEAD and approved sources remain unchanged; only these two untracked draft files are revised. No implementation formatter, test, build, migration, cloud call, credential operation or deployment is part of this pass. Author self-checks are not independent specification review.

Approval of these drafts, approval/commit of any amendments, later implementation preflight and a separately authorized compile-safe implementation plan/execution are distinct future gates. No execution ladder or automatic next phase is issued here.

**End of DRAFT ADR. Q1–Q3 decisions are recorded; detailed amendments remain DRAFT for review and approval. No implementation or deployment is authorized.**
