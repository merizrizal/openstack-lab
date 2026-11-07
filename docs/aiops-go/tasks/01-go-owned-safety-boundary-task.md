# DRAFT task contract — Delivery 1 Go-owned safety boundary and manual slice

**Status:** Superseding proposal for independent specification review, not approved/committed execution authority. [Draft ADR](../architecture/01-go-owned-safety-boundary-adr.md) §§1/3 records the owner direction and exact proposed deltas. The [prior approved task](01-safety-boundary-and-manual-slice-task.md) is preserved, not silently edited or treated as approval of this replacement.

**Scope and ladder:** Go Phase 01 Steps 1–3 and §01.6 only. [Delivery 1](../delivery/01-safety-boundary-and-manual-slice-delivery.md) is the sole execution ladder; this task has no chunk ladder.

**Sources:** [Go PRD](../prd.md), blob `18add68f88a07ace80979f86b2009d2435524743`; [source Phase 01](../implementation-plan/01-safety-boundary-and-manual-slice.md), blob `0b02155576fdeec1d899ed9cc59142e2bce01d9b`; [overview](../implementation-plan/00-implementation-overview.md); [educational baseline](../aiops-baseline.md). Q1 bounded requirements confirmation remains at `0182da9f7c2b322df5da49262748974009db7332`, not whole-PRD/later-phase approval.

**Authoring state:** HEAD `0015097ff8cd73d80cf04e38c0f088f18e48b384`, branch `aiops-go-phase01`, initially clean. Current code/requirements are unchanged from the historical requirements baseline in the inspected paths. Future preflight must identify the actual implementation base and all staged/unstaged/untracked work.

## 1. Objective and observable outcomes

An operator can list and invoke exactly three named manual diagnostics using Go, with no inference, Python runner or ambient cloud credentials in the call path:

```text
requested scope intersected with trusted current policy
  -> one Go definition/authorization/admission owner
  -> durable intent -> fixed bounded SDK observations
  -> minimized sanitized evidence -> durable terminal event
  -> one versioned result or honest non-success/limitation
```

Recording API/executor fixtures must show zero forbidden contact for rejected scope, tool, profile, implementation or input. Healthy-server, permission-denied and hostile-output fixtures must respectively show useful evidence, honest non-success and no prohibited disclosure. No retained enabled Go path may bypass the owner. Missing live prerequisites keep real diagnostics disabled; fixtures establish only offline behavior.

## 2. Prerequisites, authority and compatibility baseline

- U1–U3 in ADR §1 record the owner's acceptance of the current committed publication candidate as the alternative review basis, choice to reassess Go ownership, and documentation-only authorization. Historical missing blobs are not recovered. The old approvals/attestation stay valid evidence for their exact old candidates, not for these changed documents.
- Independent fresh-session review must assess this task, its ADR, revised sole plan, current committed addendum/affected contracts and relevant requirements, including approval/review ordering. The prior scope-readiness review and author self-checks are insufficient. Any substantiated correction needs separate authorization and affected review/approval revalidation.
- Approve and commit the exact superseding ADR/task/plan before implementation preflight. Proposed G1–G7 replace only the Go Delivery 1 ownership, definition, audit-sharing and verification dependencies; no blanket repeal of legacy security/deployment rules. No commit or implementation authority is inferred from this draft.
- Execution-time inventory must distinguish Go callers/SDKs, retained consumers, old Python/scripts/host/MCP assets and dependency provenance. No historical runner/registry import, copy, install or execution. Legacy independent runtimes remain unchanged. A source exception outside the enumerated supersession still needs approval.
- Confirm compatible Go for `aiops/go.mod` (`go 1.27.1`), cached existing dependencies, Linux file locking/process fixtures and credential-free offline baseline. Do not auto-download a toolchain/module, install packages or downgrade `go.mod`.
- Prove protected context and fixed-profile loading feasibility before enabling collectors. Existing profile-format support is unverified; no new parser dependency, file layout or broker service is authorized. If a compliant implementation cannot use permitted assets, escalate that specific proposal. A user-provided confirmed venv is required only for separately authorized Python execution, not for pure Go checks.
- Current placement/routes/effective reader policy, fresh profile integrity and lifecycle remain Phase 07 or separately authorized equivalent live gates. Deployment, provisioning, host contact, probes, audit inspection, revocation and cleanup require their own authority.

Observed interfaces and regressions are in ADR §2. Reuse Gophercloud/HTTP reader seams, registry name validation and planning snapshots; do not infer compliance from them. Preserve `tools.Registry` callers through a compliant adapter or disable their diagnostics before SDK/model initialization. Keep original goals, exact identity, approval digest, immutable preview/tasks, single-start and zero-start cancellation/non-ready regressions. No AI-OPS database/migration is required; do not add one.

## 3. In-scope work and explicit exclusions

**Included:** an entry-point/capability/consumer gap matrix; one Go-owned reviewed definition/policy/dispatch boundary; trusted immutable scope and budgets; narrow fixed SDK collection; versioned outcomes and sanitizer; durable two-stage audit and cross-process/restart-safe failure admission; model-independent manual catalog/invoke; negative/real-OS/HTTP/CLI tests; three deterministic scenario seeds; compatibility, manifest, rollback, extension, revocation and deployment-prerequisite guidance.

**Permanently excluded:** mutation/remediation, generic shell/SSH/sudo/OpenStack CLI/HTTP/file/database/message-bus tools, caller executables/endpoints, unrestricted configuration, admin/root/member/service/database/RabbitMQ credentials or fallback. An operator asking to ignore restrictions grants no authority. Authentication token issuance through the fixed reader configuration is not a cloud mutation tool.

**Deferred:** Phase 02 model/agent/plan integration, initial reports/review and nested/delegated execution; Phase 03 investigation-state/checkpoint/resume/memory/retrieval/export/data retention and cumulative recovery budgets; Phase 04 domain metadata/volume-attachment workflows, graph scheduling and multi-server synthesis; Phase 05 operator/host/MCP capabilities; Phase 06 full eval metrics/corpus/telemetry; Phase 07 actual deployment/policy/route/credential/read-denial/rollback acceptance. No future stubs, services, database, vector infrastructure, provider/GPU gateway, public API/UI or curriculum artifacts.

No live/cloud/provider/host call, credential/profile-content/protected inventory/generated configuration/raw audit read, package installation, root Makefile/Molecule/Ansible host execution, provisioning, staging/commit/push/merge/deploy is authorized by this task authoring. Future offline implementation does not imply live permission.

## 4. Definitions, authorization and selected diagnostic catalog

### 4.1 One actual Go enforcement owner

One maintained Go definition source declares version, name, intent, argument schema, fixed implementation, required profile, risk/read-only guarantee, cloud/project/target/relationship rules, availability prerequisites, positive finite timeout/output/collection/concurrency limits and a finite non-negative retry allowance. A versioned definition view is proposed as schema `2`; compiled immutable definitions are permitted instead of runtime JSON. No second independently editable catalog or legacy seven-tool activation. If serialized, reject duplicate keys and unknown/missing fields at every level; always reject duplicate names, unsupported validators/defaults, wrong types including bool-as-int, malformed mappings and missing limits at startup.

Public requests select only a named tool and declared arguments. Version, policy, profile, endpoints, executable, output/audit paths, limits, actor and approval are not public execution overrides. Scope requested through CLI/application input must be intersected with protected current policy. Application-owned context binds cloud, expected project identity (verified against authentication before resource reads), canonical permitted targets or explicitly scoped resolution permission, capability/profile set, policy identity, approval presence when applicable, client classification and budgets. Caller mutation, definition/policy drift and concurrent substitution must not change admitted work. Revalidate immediately before every credential-bearing operation and related lookup.

Catalog listing exposes only reviewed safe capability/availability metadata, never profile content, policy secrets or implementation paths; it performs no API/authentication/diagnostic call. A catalog query is not itself a diagnostic request and does not invent a tool intent/terminal event. A failed required control must remain an explicit unavailable limitation, not an apparently executable catalog entry.

Reject unsafe/disabled requests before constructing/authenticating SDK clients. Credential-bearing handles remain internal. Enumerate and close direct CLI/library/SDK routes available to supported clients; a wrapper check with an enabled raw SDK route is insufficient. Trusted runtime/operator/root compromise is not falsely claimed solved by these checks; future model execution must have effective OS/process isolation from reader credentials/control state.

### 4.2 Credential and transport boundary

Retain `assistant02`, inventory group `ai_ops_assistant`, user/group `aiops_assistant`, root `/opt/openstack-ai-ops-assistant`, fresh profile `aiops-assistant-project-reader`, project label `admin`, domain `default`, role `reader` only, one-month expiry and OpenStack admin-team rotation/revocation. Preserve `credentials/profiles/` directory `0700`, regular non-symlink `clouds.yaml`/`secure.yaml` files `0600`, owner/group `aiops_assistant`. Executables/policy are root-owned and runtime-caller-unwritable. No changed credential layout or new dependency is preapproved.

Go runtime credential loading uses only the fixed reviewed source and dedicated identity. It may load synthetic profile content in tests and approved runtime content during separately authorized use; the implementation agent must not inspect real content. No ambient `OS_*`, provider, SSH, proxy or alternate profile fallback. No credential in argv, output, audit, reports, inherited model environment or raw error. Fixed authentication/API endpoints come from trusted configuration and current live acceptance, not tool arguments or response links. Response redirects/pagination links must not change approved origins/routes or forward credentials elsewhere. Auth/configuration/policy failures do not select stronger credentials or automatic transient retries.

### 4.3 Exact catalog and projection

Public arguments: summary has none; the server tools have exactly one required `server_identifier`. Preserve nonempty ASCII `[A-Za-z0-9._:-]+`, maximum 255 bytes, no slash or `..` for the direct diagnostic identifier contract. The Go entry may accept a supported original exact name for a separately authorized bounded resolution step, then supply a verified canonical UUID to the narrower collector identifier slot, retaining original input and giving UUID guidance when resolution is not permitted. Validate request structure, requested resolution scope and budgets before that step; it is not an opportunity to authenticate or search merely to validate arbitrary malformed input. No case folding, invented name uniqueness or arbitrary normalization. Missing/ambiguous matches reject; no guessed or substring selection. Resolution itself is scoped evidence collection subject to intent and budgets.

| Capability | Required observations / relationship | Exact permitted disclosure and exclusions |
| --- | --- | --- |
| `server_basic_info` | One permitted server; fault and flavor ID derived from that authorized observation; fixed flavor GET must match it. | Basic server fields below, fault `code` and bounded sanitized `message`; absent fault is null. `flavor_detail`: `id`, `name`, `vcpus`, `ram_mb`, `disk_gb`, `ephemeral_gb`, `swap_mb`. Missing linkage/detail yields an unavailable flavor section and partial limitation. No raw fault `details`, host, extra specs, user-data or configuration dumps; no enumerate-flavors fallback. |
| `server_network_info` | Authorized server → attached project/device-validated ports → validated derived networks/subnets within approved visibility. | Selected fields below, no unrelated topology/port list, host lookup or alternate profile. Model claims do not establish relationships. |
| `project_resource_summary` | Seven fixed project-visible sections only under explicit project-wide permission. | Servers, networks, subnets, ports, volumes, images and security groups below. Server-only scope gives no project-wide authority. Volume summary is not volume/attachment traversal. |

| Section | Selected fields |
| --- | --- |
| Basic server | `id`, `name`, `status`, `image`, `flavor`, `addresses`, `availability_zone`, `config_drive`, `created`, plus bounded `fault` above. Validate/minimize nested image/flavor/address values; no opaque object bypass. |
| Summary servers / networks / images / security groups | `id`, `name`, `status`. |
| Summary subnets | `id`, `name`, `network_id`, `cidr`, `ip_version`. |
| Summary ports | `id`, `device_id`, `network_id`, `status`. |
| Summary volumes | `id`, `name`, `status`, `size`. |
| Server-network ports | `id`, `network_id`, `fixed_ips`, `mac_address`, `status`. |
| Related networks / subnets | Networks: `id`, `name`, `status`; subnets: `id`, `name`, `cidr`, `ip_version`. |

At most 50 records per list section and 1 MiB per complete diagnostic, preserving tighter applicable Go port ceilings of 32 records/four pages. Per-tool timeouts are positive and at most 300 seconds; output limits are positive and at most 1 MiB, with tighter reviewed per-tool ceilings preserved. Define finite positive collection-time response-byte/page/request/memory/deadline/concurrency limits and a finite non-negative retry allowance before reading/decoding, never only slice after buffering. Reviewed definition ceilings may tighten, not silently loosen inherited bounds. No later SDK request after cancellation, exhausted budgets or required-control failure. Close response resources; bound any actually owned helper/fixture process lifetime and reap it. Production collectors use narrow SDK calls, not arbitrary subprocesses.

## 5. Closed outcomes and sanitization

Inner diagnostic/tool contract `2.0` contains exactly `schema_version`, `tool`, `status`, `sections`, `error`; each section exactly `name`, `status`, `data`, `error`, `truncated`. Top-level statuses are `ok`, `partial`, `error`; section statuses `ok`, `empty`, `unavailable`. A genuine successful zero-record read is `empty`; missing/denied/failed/malformed collection is never empty health evidence. Independent unavailable sections permit partial evidence; fatal auth/configuration may stop subsequent reads. Keep inner diagnostic semantics distinct from outer runner outcomes.

Outer result `2.0` contains exactly: `schema_version`, `tool`, `status`, `arguments`, `exit_code`, `data`, `stdout`, `stderr`, `error`, `duration_ms`, `truncated`, `timestamp`, `correlation_id`, `tool_version`, `target`, `redacted`. Unresolved tool version is null; safe fixed placeholder replaces malformed/unresolved labels. Target is null for invalid/unresolved/non-targeted requests; otherwise exactly `original_identifier` and `resolved_identifier`, each sanitized string or null, resolved only after verification. Summary invents no server target.

| Outer status | Process exit | Meaning |
| --- | ---: | --- |
| `ok` | 0 | All requested evidence safely collected and required terminal audit durable, including true empty sections. Not root-cause confirmation. |
| `error` | 1 | Collection, decoding, sanitization, cleanup or required persistence failed; partial evidence only when safe and explicitly limited. |
| `denied` | 2 | Unknown/forbidden tool or authorization boundary rejected. |
| `validation_error` | 3 | Invalid/extra/duplicate/missing/wrong-type/unsafe request input before diagnostic dispatch. |
| `timeout` | 4 | Deadline expired; bounded cleanup, no later dispatch. |
| `unavailable` | 5 | Approved optional capability/source prerequisite missing, or recognized unavailable service/catalog/connectivity condition. |
| `cancelled` | 6 | Application interruption/cancellation with successful bounded cleanup; timeout is not cancellation. |

`exit_code` is an actual completed child exit only, otherwise null: all pure SDK results use null, never the Go process exit. `stdout`/`stderr` are null for structured diagnostics. Error objects are exactly `{class,message}` or null on success. Preserve normalized runner categories: `request_context_error`, `registry_error`, `validation_error`, `target_unavailable`, `target_integrity_error`, `execution_error`, `timeout`, `interrupted`, `output_decode_error`, `redaction_error`, `serialization_error`, `audit_integrity_error`, `audit_write_error`, `audit_rotation_error`. Scope denial uses a safe normalized category, not raw context. Cancellation uses `interrupted`; required audit failure overrides success/cancellation with error, and failure to establish required cleanup is error for any outcome, including timeout.

Diagnostic normalization retains `invalid_input`, `not_found`, `ambiguous`, `policy_denied`, `service_unavailable`, `catalog_missing`, `connectivity_error`, `authentication_error`, `configuration_error`, `execution_error`. Recognized signatures only; unknown errors become execution error. Only recognized unavailable conditions map to outer unavailable; auth/policy/not-found/malformed errors do not become unavailable/empty. No generic raw HTTP/SDK error reflection.

Minimize then sanitize before CLI, serialization, audit or any retained sink. Fixed marker `[REDACTED]`; case-insensitive secret-like keys include password/passphrase/secret/token/credential/private key/API key/authorization; also assignments/headers, bearer values and private-key blocks. Recurse at most depth 32 and 100,000 visited values; reject unsafe/malformed/unsupported/invalid UTF-8 values without partial leakage. Public runner messages cap at 512 UTF-8 bytes; retained diagnostic error messages keep their separate 512-character ceiling. Test split/multibyte/truncation and sanitizer work boundaries. `redacted` records replacement/withholding independently of `truncated`; neither implies the other or complete collection.

Internally generate one UUIDv4 correlation and UTC RFC 3339 request timestamp, shared across result/intent/terminal; use monotonic elapsed duration. Caller labels do not override identity. Serialization is deterministic compact sorted-key UTF-8, standard JSON only, exactly one complete result plus newline. Do not add fields/statuses to legacy `1.0` or claim that matching a schema proves policy/audit parity.

## 6. Audit, shared admission and recovery

### 6.1 Closed two-stage events

Audit `2.0` has exactly: `schema_version`, `timestamp`, `event_type`, `actor`, `tool`, `arguments`, `status`, `duration_ms`, `correlation_id`, `reason`, `exit_code`, `truncated`, `event_id`, `tool_version`, `policy_version`, `approval_present`, `scope`, `redacted`, `completion`.

Each event gets an internal UUIDv4 `event_id`; request correlation/timestamp are shared. Actor is fixed `local_cli`, not an authenticated human assertion. Tool/policy versions are bounded non-secret trusted labels or null. Arguments retain only the presence summary (`server_identifier_present` for server requests). Scope has exactly booleans `cloud_present`, `project_present`, `project_wide` and non-negative integer `target_count` from validated context. Approval presence is a boolean, not a token/digest or a new manual plan-approval requirement. Reason is a reviewed bounded normalized category or null. No raw target/cloud/project identifiers, profile/config content, outbound context, diagnostic data, stderr, filesystem detail or payload in audit.

| Event | Stage fields | Cardinality and ordering |
| --- | --- | --- |
| `tool_request_intent` | Status/reason/exit null, duration 0, completion `pending`. | One durable sanitized intent before the first possible credential-bearing/authentication/observation operation for an allowed request; failed/uncertain persistence means zero contact. No intent merely for a rejected request. |
| `tool_request_completed` | One of seven terminal statuses, measured non-negative duration; completion `not_dispatched`, `completed` or `interrupted` consistent with actual work. | Every request attempts one terminal; at most one committed terminal. Normally intent + terminal when dispatched, terminal only when rejected. Required terminal durability precedes successful payload publication. |

The audit reflects the observed terminal status; persistence failure may force the public result to error. Never append a second event just to make a public error match an uncertain already-committed terminal. Pre-cancelled requests contact nothing but attempt terminal audit. A repeated intentional later request is newly authorized/budgeted with new identity, not an audit-free no-op or automatic replay. Planning review cancellation without a tool request creates no tool audit.

### 6.2 Proposed isolated Go filesystem

G3 proposes `/opt/openstack-ai-ops-assistant/audit/go/` (directory `0700`, owner/group `aiops_assistant`), active `tool-runner.jsonl`, lock `.tool-runner.lock`, numbered archives `.1`–`.3`, regular/non-symlink `0600` files with the same ownership. The parent remains the protected revised audit directory; no Go process appends/rotates/repairs the Python active file or shares its lock/control state. This new namespace is draft architecture requiring approval, not runtime creation authority.

Use exclusive OS file locking with the retained `flock` semantics across processes, bounded contention and revalidation under lock. Reject unsafe path resolution, symlinks, non-regular/wrong-owner/wrong-mode paths and archive collisions. No auto-unlink/replace/repair of unsafe paths. Compact JSONL events cap at 16 KiB; rotate at 1 MiB with at most three numbered archives, no compression, age deletion or fallback sink. Do not evict unresolved intent needed for truthful recovery: stop admission/rotation instead of exceeding retention or hiding uncertainty.

Successful persistence requires complete append, flush/file sync and appropriate directory durability for create/rename/rotation/control transitions; check metadata again. Partial/uncertain writes fail closed, never claim a safely saved event from `Close` alone. Minimal protected bounded/versioned control state may live only under this Go root with equivalent metadata; exact filenames and deployment artifacts must be recorded and checked with the introducing implementation chunk, then appear in the reviewed final manifest before installation/live use. Temporary fixture roots are internal test seams, not production path overrides. It is not another audit/evidence store or investigation schema.

### 6.3 Failure and concurrency rules

Serialize or finitely reject concurrent admissions; protect policy/definition snapshots and shared budgets/health across independent CLI processes. Define lock ordering and prove no deadlock or double admission. Pure in-memory mutexes/latches are insufficient.

Intent failure means zero dispatch and safe local operational fault. Terminal failure withholds diagnostic payload/raw errors, returns generic non-success, preserves durable intent/events and shows incomplete/uncertain completion without relying on the failed sink. Stop new admission across callers and restart until trusted safe recovery. If a durable health marker cannot be written, startup must still require operator recovery/readiness rather than treating absence as health. A fresh process cannot clear a fault.

Crash after intent with no durable terminal is uncertain, not proof of no observation. No automatic replay, retrospective fabricated terminal, duplicate append retry or audit deletion/rewriting to simulate rollback. At most one execution attempt for the request; allowed multi-read collection remains bounded within it. No ACID/exactly-once claim spans the API and local files. Phase 03 later owns intentional re-observation/cross-checkpoint recovery; do not scaffold it here.

## 7. Compatibility, manifest and rollback

Inventory every enabled/disabled Go entry, raw SDK helper, policy/definition/result/audit consumer and independent Python/host/MCP consumer. Record source lineage, versions, authority/profile, actual dispatch and evidence status. No historical source is copied/imported/executed. The Go path need not emit legacy `1.0`; incompatible consumers must explicitly reject/remain disabled. Any selected translation requires reviewed semantics, one underlying execution, no added audit and no event flattening. Existing legacy diagnostics and records remain untouched, not silently migrated.

Provide a reviewed Go deployment manifest of the exact proposed binary, protected policy/definition and any control artifacts, ownership/modes and disabled-live defaults. Paths and format choices not fixed here are proposals to settle within these constraints before use; new credential layout/dependency/privilege requires approval. Static manifest assertions are in scope; modifying/installing Python roles or provisioning is not. No Go installation is authorized by a legacy role allowlist.

Rollback stops new admission, bounds/cancels active work and retains intents/events/control faults. Disable the new Go path/configuration without restoring ambient SDK commands or Python fallback. Reversion alone does not re-enable live use; retained evidence must remain safely inspectable under compatible versions and applicable owner recovery/live gates. Do not delete Go records to make an old inspector pass. Existing investigation goals/IDs/identity/timestamps/links and legacy audit are not converted in place.

## 8. Requirement and acceptance traceability

Vocabulary: **CURRENT** = current Go Delivery 1 obligation after approval; **PRESERVE** = prior binding requirement/regression, not an assertion that existing code passes; **DEFER** = named later owner. Mixed rows state the exact partial boundary. No implementation acceptance is inferred from source presence. Sources are canonical Go PRD IDs, not the revised PRD's different numbering.

### 8.1 Functional requirements

| PRD | Disposition and boundary | Evidence |
| --- | --- | --- |
| FR-001 | CURRENT manual list/invoke; DEFER investigations/projects to 02/04, inspect/pause/resume/export integration to 03. | V10 |
| FR-002 | CURRENT per-request trusted cloud/project/targets/profile/budgets; DEFER investigation record to 02/03. | V2/V4 |
| FR-003 | CURRENT UUID/exact-name, original/resolved identity and ambiguity/UUID guidance; PRESERVE Go intent. | V4/V11 |
| FR-004 | DEFER planner integration to 02; PRESERVE non-ready zero start. | V11 |
| FR-005 | DEFER new approval integration to 02; PRESERVE digest/immutable preview/declined zero start. | V11 |
| FR-006 | DEFER full graph to 04; PRESERVE existing readiness/single-start regressions. | V11 |
| FR-007 | DEFER model-control validation to 02; CURRENT no model initialization. | V10 |
| FR-008 | CURRENT finite call/cancel prerequisites; DEFER agent loop to 02. | V5 |
| FR-009 | CURRENT owner dispatch/bounds/no denial retries or credential fallback; DEFER task transitions to 02/04. | V2/V5/V8 |
| FR-010 | CURRENT all enabled local Go/SDK boundaries; DEFER nested/delegated to 02, resumed to 03, MCP to 05. | V2 |
| FR-011 | CURRENT derived flavor/port/network/subnet and separate summary authority; DEFER volume/attachment to 04 and host to 05. | V4 |
| FR-012 | DEFER full domain workflows to 04; current collection is a prerequisite, not diagnosis acceptance. | V10 seed only |
| FR-013 | DEFER multi-server graph/synthesis to 04. | No scheduler |
| FR-014 | DEFER investigation checkpoints to 03; CURRENT distinct audit intent. | V7/V8 |
| FR-015 | CURRENT no replay/truthful uncertainty; DEFER resume/intentional refresh policy to 03. | V8 |
| FR-016 | DEFER context/memory classes to 03. | No memory ingestion |
| FR-017 | CURRENT manual independence from knowledge; DEFER retrieval to 03. | V10 |
| FR-018 | CURRENT untrusted requests/output cannot grant authority; DEFER knowledge/model context to 02/03/06. | V9 |
| FR-019 | CURRENT truthful evidence/limitations; DEFER initial/full reports to 02/04. | V6/V10 |
| FR-020 | DEFER initial/full evidence review to 02/04. | No manual reviewer call |
| FR-021 | PRESERVE isolated observer design; CURRENT manifest/prerequisite guidance; DEFER deployed proof to 07. | V3/V11 |
| FR-022 | CURRENT dedicated reader/no fallback; PRESERVE lifecycle; DEFER optional profiles to 05, policy proof to 07. | V3 |
| FR-023 | CURRENT one reviewed Go definition owner and closed validation. | V1/V2 |
| FR-024 | CURRENT narrow SDK authorization/audit; no script execution selected, legacy scripts unchanged. Any future retained script needs the same fixed argv controls. | V2/V3/V5 |
| FR-025 | CURRENT basics/fault/flavor/network/summary; DEFER attachment to 04 and operator/log access to 05. | V4/V10 |
| FR-026 | DEFER host tools to 05; no legacy catalog activation. | V2 denial |
| FR-027 | CURRENT all seven structured statuses, safe identity/metadata/exits; legacy closed views untouched. | V6 |
| FR-028 | CURRENT all-request terminal attempts, intent, fail-closed shared/restart-safe control. | V7/V8 |
| FR-029 | CURRENT all enabled local sinks minimized/sanitized; DEFER disclosure/export/memory to 02/03. | V9 |
| FR-030 | CURRENT permanent mutation denial including operator insistence. | V2/V9 |
| FR-031 | DEFER enabled model contract to 02; CURRENT no model prerequisite. | V10 |
| FR-032 | DEFER destination/disclosure authorization to 02; no inference now. | V10 |
| FR-033 | CURRENT no model/credential forwarding; DEFER deployed model isolation to 02/07 before enabling it. | V3/V10 |
| FR-034 | CURRENT model-independent manual diagnostics; DEFER outage/state/report integration to 02/03/07. | V10 |
| FR-035 | DEFER MCP parity/discovery to 05; incompatible independent consumers disabled for Go. | V11 |
| FR-036 | DEFER routing to 02 and optional specialist evaluation to 06; none enabled now. | V2/V10 |
| FR-037 | CURRENT three versioned scenario seeds; DEFER full evaluation platform to 06. | V10 |
| FR-038 | DEFER quality/tool/cost metrics to 06; no invented scores. | Seed safety only |
| FR-039 | CURRENT tool correlation/time/outcome; DEFER full cross-run telemetry to 02/03/06. | V6/V7 |
| FR-040 | CURRENT finite tool limits/cancel/shared admission; DEFER task/token/cost/recovery budgets to 02/03/06. | V5/V8 |
| FR-041 | CURRENT definition/policy/audit readiness and manifest guidance; DEFER complete operations to 06/07. | V1/V3/V7 |
| FR-042 | CURRENT extension/revocation/deployment/rollback guidance; PRESERVE lifecycle; DEFER data lifecycle/live rehearsal to 03/07. | V11 |

### 8.2 Non-functional requirements

| PRD | Disposition and boundary | Evidence |
| --- | --- | --- |
| NFR-001 | CURRENT zero supported-path authorization bypass, mutation or disclosure. | V2/V9 |
| NFR-002 | CURRENT credential/runtime isolation design/fixture path; DEFER deployed routes/isolation to 07. | V3 |
| NFR-003 | CURRENT finite collection/output/deadline/cancel; DEFER complete investigation budgets to 02/03. | V5/V8 |
| NFR-004 | CURRENT audit/control durable ordering and writer exclusion; DEFER checkpoints to 03. | V7/V8 |
| NFR-005 | CURRENT evidence/call scope isolation; DEFER stored memory/approval partitioning to 03. | V2/V4 |
| NFR-006 | CURRENT optional degradation/required-control fail closure/manual independence; DEFER consolidation to 02/06. | V7/V8/V10 |
| NFR-007 | CURRENT collection success not diagnosis proof; DEFER semantic evaluation to 04/06. | V6/V10 |
| NFR-008 | CURRENT safe tool provenance; DEFER full pipeline to 06. | V6/V7/V9 |
| NFR-009 | DEFER measured thresholds/latency/usage to 06. | No claimed SLA |
| NFR-010 | CURRENT explicit Go compatibility and legacy preservation; DEFER enabled MCP/release proof to 05/07. | V6/V11 |
| NFR-011 | CURRENT reviewed definitions/tests/scenario extension, no generic primitive. | V1/V9/V10 |
| NFR-012 | CURRENT minimization/redaction/protected local audit; DEFER model egress/data policy to 02/03/07. | V3/V9 |
| NFR-013 | CURRENT clear denied/error/empty/unavailable/partial/truncation; DEFER report/proposal UX to 02/04. | V6/V10 |
| NFR-014 | CURRENT deployment design/manifest and offline path; DEFER actual install/stop proof to 06/07. | V3/V11 |
| NFR-015 | CURRENT deterministic credential-free fixtures; DEFER optional model/live tiers to 06/07. | V10/V11 |

### 8.3 Acceptance criteria

| PRD | Disposition / permissible claim | Evidence |
| --- | --- | --- |
| AC-001 | PRESERVE approval regressions only; DEFER full CLI investigation to 02. | V11 |
| AC-002 | CURRENT manual identity subset; DEFER end-to-end planning identity to 02. | V4 |
| AC-003 | CURRENT unknown/invalid calls and bounds; DEFER loops/graph to 02/04. | V1/V2/V5 |
| AC-004 | CURRENT local Go/SDK denial and related reads; DEFER nested/delegated/resumed to 02/03. | V2/V4 |
| AC-005 | CURRENT seed/basic evidence only; DEFER domain findings to 04. | V10 |
| AC-006 | DEFER multi-server dependencies/synthesis to 04. | No scheduler |
| AC-007 | DEFER investigation resume to 03; audit uncertainty is not a full pass. | V8 local subset |
| AC-008 | DEFER context classes/export to 03. | No state scaffold |
| AC-009 | DEFER curated retrieval to 03; sanitizer prerequisite only now. | V9 |
| AC-010 | DEFER evidence review to 02/04. | No model reviewer |
| AC-011 | DEFER deployed separation/policy/read-denial proof to 07 or explicit equivalent gate. | Guidance only |
| AC-012 | CURRENT all enabled Go/SDK validation; DEFER script/MCP integration parity unless retained to 05 or its own approved task. Legacy paths untouched. | V1/V2/V3 |
| AC-013 | DEFER host fixture/live access to 05/07. | V2 zero host dispatch |
| AC-014 | CURRENT all seven outcomes, cancellation, audit and shared failure rules. | V6/V7/V8 |
| AC-015 | CURRENT canary and no-mutation assertions including override requests. | V9 |
| AC-016 | DEFER enabled model/disclosure validation to 02/07. | V10 zero inference |
| AC-017 | CURRENT no model access prerequisite; DEFER deployed isolation proof to 02/07. | V3/V10 |
| AC-018 | CURRENT manual independence; DEFER state/report/outage/revocation flow to 02/03/07. | V10 |
| AC-019 | DEFER MCP to 05. | No registration |
| AC-020 | DEFER optional-disabled/comparison release record to 06; no specialists here. | V10 prerequisite |
| AC-021 | CURRENT three scenario seeds/expected-actual format; DEFER full eval outputs to 06. | V10 |
| AC-022 | CURRENT tool correlation/finite budgets/cancel; DEFER full telemetry/restart cumulative budgets to 02/03/06. | V5/V6/V8 |
| AC-023 | CURRENT prerequisite/revocation/rollback guidance; DEFER live exercise to 07. | V11 |
| AC-024 | CURRENT local Go regressions, unchanged legacy paths and explicit version/rollback; DEFER state/MCP/deployed release checks to 03/05/07. | V11 |
| AC-025 | DEFER release record to 07 with 06 corpus/thresholds. | No deployed claim |

Source Phase 01 Step 1 maps to §§2/4/5/6 and V1–V4; Step 2 to §§4–6 and V4–V8/V10; Step 3 to §§7/9/11 and V1–V11. Section 01.6 requires the complete bounded catalog, no enabled bypass, all applicable evidence and separately documented live prerequisites. ADR G1–G7 are explicit proposed reconciliation deltas, not silent omissions. PRD non-goals and baseline curriculum remain exclusions, not additional tool authority.

## 9. Mandatory verification contract for future implementation

All entries below are **PLANNED_NOT_RUN**. Use highest practical CLI/owner/HTTP seams, not only helpers. Internal test paths/readers/clock/UUID/fault hooks must not become public overrides. Temporary loopback API, files and subprocess fixtures only; inspect test side effects before running. No cloud/provider credentials or non-loopback network.

| ID | Required cases / seam | Observable acceptance |
| --- | --- | --- |
| V1 | Go definition source startup/serialized duplicate keys, unknown fields/versions, duplicate names/positions, validators/defaults/wrong types, missing bounds, invalid subset. | Fail closed before clients/contact; one reviewed three-tool view, immutable copied metadata. |
| V2 | Highest supported Go/SDK/CLI entry: allowed, unknown/generic/mutation, forged/missing scope/cloud/project/profile/policy, direct raw bypass, stale policy/definition and caller mutation. Recording readers/auth traps. | Zero forbidden HTTP/auth/SDK dispatch; required terminal attempt; disabled old automatic commands reject before model or ambient SDK setup. |
| V3 | Synthetic fixed profile/config metadata and credential loader; ambient admin/OS/proxy/provider/SSH canaries, missing/revoked/unsafe/symlink/wrong-owner files; hostile endpoint/redirect/pagination destination. | Dedicated source only, no inherited fallback/leak/token exfiltration; correct static runtime/manifest metadata. Live policy/isolation not claimed. |
| V4 | UUID/exact-name/missing/ambiguous/casing/substring/script-incompatible names; original/resolved identity; wrong response project/target; valid/forged flavor/network/subnet relationships; absent/secret fault; missing flavor; separately permitted summary. HTTP request counters. | No unintended target/read; selected projections only; no host/fault details/extra specs; false relationships do not cause downstream lookup. |
| V5 | Oversized/streamed responses, endless/malicious pagination, records/pages/memory/time/retry/request/concurrency/output ceilings; cancellation before/between/during reads; invalid UTF-8/JSON; actual CLI/helper processes where owned. | Bounds enforced during collection/decoding; responses closed, actual owned processes reaped, no subsequent request/retry after cancel/exhaustion/fault. |
| V6 | Seven outer statuses/exits, inner empty/partial/error, SDK child-exit null, target and independent redacted/truncated combinations, clock/correlation/event IDs, strict single-line compact JSON/closed shapes and unsupported versions. | Exact schema-specific output and safe errors; success is not health proof; no silently extended `1.0`. |
| V7 | Real temporary files/locks plus disk-full/permission/write/flush/fsync/directory-sync/lock/rotation injections at intent and terminal; unsafe paths/modes/owners/archive collision/event bounds. | Intent durable before first contact; terminal before success; all requests terminal attempt; no duplicate event, payload/raw detail/fallback/replay on failure. |
| V8 | Independent fixture processes: concurrent append/rotation/admission/budgets, crash before/after intent/during/after read/before terminal, uncertain partial append, restart, control corruption/unwriteable marker, unresolved-intent rotation and trusted recovery. | Complete non-interleaved bounded events, no over-admission/deadlock/replay/post-fault dispatch; restart cannot erase uncertainty; no mocks-only durability claim. |
| V9 | Canary secrets in nested output/arguments/text/errors/body/headers, bearer/PEM, multibyte/split/truncated/depth/work-limit data; hostile instructions and insistence on mutation. Full CLI/audit/result sinks. | Zero prohibited disclosure, no raw fallback or generic/mutation dispatch; unsafe data withheld explicitly. |
| V10 | Actual manual catalog/invoke → Go owner → controlled API; healthy, permission-denied, hostile seeds with versions/expected-actual calls/targets/outcomes/evidence/limitations; missing model/provider/knowledge/host/MCP traps. | Useful manual output without inference/Python/specialists/host/MCP; named gaps, no invented cause. |
| V11 | Existing Go tools/scopedtools/planning/workflow and command regressions; explicit consumer versions/unsupported rejection, manifest metadata and isolated Go audit; synthetic safe disable/rollback with untouched original state/legacy records; guide reproduction. | Required local suites discovered and pass; no old consumer silently receives Go evidence, no migration/rewrite/event flattening, bypass revival or installed runtime change. |

From `aiops/`, after confirming existing tools/cache and reviewing tests, use session-local `GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off`; planned baseline: `rtk go version`, `rtk go test ./internal/tools ./internal/scopedtools ./internal/planning ./internal/workflow`, then `rtk go test ./...` and `rtk make build`. Full build covers the four existing commands; explicitly build the proposed manual CLI until its target is added. Format changed Go with `rtk gofmt -w <observed-changed-files>`; run `rtk go vet ./...` and `rtk go test -race` for affected Go concurrency packages. Standard Go fixtures reuse `httptest`, temporary files/processes and the current Gophercloud dependency; no new framework/dependency is implied.

Exact proposed package/test paths are confirmed in delivery Chunk 0. Go race checks do not replace V8 multiprocess filesystem evidence. Pure Go implementation does not require Python execution or a Python venv. If an authorized change actually affects a Python/script/deployment consumer, first reconcile that scope and run its own applicable regression/static/syntax checks in the approved environment; missing tools are a blocker, not a green skip. Never invoke the root Makefile, which loads `.env`, or live Molecule/host checks as an offline wrapper.

Finish each chunk with full relevant tracked/staged/untracked diff review, symbol/import/path/format/security checks and actual discovery/pass/fail/skip/not-run evidence. Finish the delivery with complete Go tests/build/vet, affected race tests, all V1–V11, documented no-model fixture demonstration and full implementation-base-to-candidate diff including new files. Missing mandatory verification blocks completion; do not weaken assertions or infer success from source presence.

## 10. Decision authority

- **Level 0 after approval:** ordinary compilation/debug/format/testing/fixture work and smallest in-scope repairs; substantiate review findings before repair.
- **Level 1 after approval:** internal Go packages/helpers, compiled versus protected definitions, compliant validator/collection/locking/control serialization, safe sequential admission and test seam choices within this contract. Record meaningful choices; no routine permission needed.
- **Level 2:** approval of superseding G1–G7 and exact source candidates; product/scope changes, new dependency/credential layout/infrastructure, changed fixed placement/identity/retention or material risk, new live/provisioning/credential/destructive authority. U2 alone is not blanket approval of implementation mechanisms. Difficult engineering does not authorize weakening requirements.

Escalations identify category, evidence, viable alternatives, recommendation, precise decision and safe independent work. No remaining product question prevents drafting; context/credential feasibility and environment remain unverified engineering prerequisites, with specific Level 2 escalation if they cannot fit the approved design.

## 11. Completion and evidence

A future executor may report `READY_FOR_REVIEW` only when the approved committed superseding sources and actual base are identified, all selected three-tool scope is implemented without bypass, all mandatory V1–V11 and repository checks actually pass, scenarios/gap matrix/guide/manifest/rollback evidence exist, full diff is in scope and unverified live capabilities remain disabled. No partial legacy-compatible/six-status result or mocks-only concurrency proof completes this task.

The completion report must include base and exact candidate/worktree, source/approval fingerprints, changed paths, per-requirement local/deferred coverage, entry/consumer versions, significant Level 1 decisions, actual commands/tool versions/test counts/skips/failures, safe manual demo, real OS/crash/recovery evidence, complete diff/security review and remaining limitations. No credential, private environment path, raw operational evidence or secret enters Git.

`BLOCKED` means unresolved authority/access/security or mandatory verification prerequisite. `INCOMPLETE` means unfinished authorized work. Independent review, final acceptance, commit, merge and deployment are separate authorities. Implementation self-check is not independent review.

## 12. Source and authoring limitations

The ADR source ledger preserves the exact prior candidates and U1–U3. The old addendum and all legacy contracts remain unchanged; this proposal explicitly separates Go governance from legacy-runtime activation while retaining required safety. The canonical requirements and roadmap headers remain unchanged. There is no new ADS or second execution ladder.

Authoring verification is document QA only. No implementation baseline/toolchain, credential feasibility, exhaustive dependency/consumer inventory, current deployed policy or fresh independent publication/specification review is claimed. These sources must be independently reviewed, approved and committed, then receive fresh implementation preflight and separate execution authorization.

**End of DRAFT Go-owned task. Complete selected behavior remains required; this proposal authorizes no implementation or live operation.**
