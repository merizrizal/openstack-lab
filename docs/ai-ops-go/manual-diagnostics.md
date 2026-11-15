# Manual Diagnostics: Candidate G1–G4 Realization

**Status:** Candidate design for separate review. It is not approved, implemented, enabled, or evidence of deployed safety.

**Scope:** Documentation-only realization record for Phase 01 Chunk 1. This document does not change product requirements or ADR constraints, select deployment values, provision a fixture, or authorize diagnostic execution.

**Governing sources:** [Product requirements](prd.md), [approved task contract](tasks/01-safety-foundation-and-manual-diagnostics.md), [approved enforcement and persistence ADR](architecture/01-manual-diagnostic-enforcement-and-persistence-boundaries.md), and [controlling implementation plan](chunked-implementation/01-safety-foundation-and-manual-diagnostics.md), especially Chunk 1. The PRD/task/ADR and B1–B5 remain authoritative if this candidate conflicts with them.

## 1. Decision and gate ledger

This is one feasible candidate to review, not a gate decision. Reviewers must assess it against the target OS, actual operator configuration, and required negative/fault evidence. No gate is self-approved here.

| Gate | Candidate covered here | Current state | Required before |
| --- | --- | --- | --- |
| **G1 — security domains and authenticated ingress** | Separate non-root requester and credential-owning process; authenticated local IPC; server-derived current authorization. | **Review and approval pending.** Unauthorized-local-caller OS proof is **pending**. | Separately review/approve the concrete realization before affected execution; actual negative OS-context proof before manual diagnostics are enabled. |
| **G2 — acceptance configuration** | Synthetic offline configuration is distinguished from operator-supplied deployment scope, endpoints, reader and finite storage limit. | **No deployment configuration or values established.** | Trusted configuration, usable finite limit, and protected setup before startup/use. |
| **G3 — reader operations and transport** | A proposed narrow Nova/Neutron operation allowlist, relationship checks, and fixed-destination transport restrictions. | **Exact operation/destination review pending.** No live reader-policy evidence is claimed. | Review before enabling any collector; separately authorized live reader/mutation-denial evidence remains a deployment-acceptance obligation. |
| **G4 — protected persistence and recovery** | New versioned namespace, durability sequence, single-lock admission/writer ordering, capacity reservation, audit/result ordering, and bounded cleanup. | **Review and approval pending.** Filesystem/crash/fault evidence is **pending**. | Separately review/approve before persistent execution; actual fault evidence before acceptance. |

G2 synthetic fixtures can validate software behavior but do not supply deployment configuration or prove cloud policy. A successful documentation review, static inspection, mock, or built executable does not satisfy an OS/filesystem gate or enable a capability.

## 2. G1 candidate: distinct domains and authenticated local ingress

### 2.1 Security domains

The candidate uses separate OS-enforced, non-root process identities even if both processes execute the same Go runtime binary:

| Domain | Responsibility and allowed access | Must not receive |
| --- | --- | --- |
| Requesting CLI | Accept a deliberate operator action and send a named diagnostic request. It supplies only the requested target and bounded user-level arguments. | Reader credentials, SDK clients, authority to choose project/profile/endpoint/implementation, or authority to write protected state. |
| Credential-owning enforcement process | Authenticate the local caller, load protected trusted policy/configuration, own reader clients and the protected store, authorize each operation, and perform the bounded reads. | Root privileges, a mutation capability, or an automatic stronger-profile fallback. |
| OS/operator control plane | Provision and protect the two non-root identities, IPC access, trusted configuration, credential source, and data area; review/revoke configuration. | Application-agent authority to create accounts, alter permissions, provision infrastructure, or change host security policy. |

A common executable, package boundary, command-line flag, environment variable, or shared process is not the isolation boundary. The requester must not be able to read or replace the credential owner’s secrets, trusted policy, or protected records. The credential owner must refuse access to arbitrary local callers.

### 2.2 Candidate IPC and authorization flow

A candidate local transport is a permission-restricted Unix-domain socket authenticated by kernel-supplied peer credentials (for example, Linux peer-credential facilities). The operator—not the application—would provision the socket directory and OS identities. The credential owner would validate the connecting peer against an independently protected allowlist and derive the authorization context from that peer plus current trusted configuration. No principal, project, capability, endpoint, credential, policy version, or limit in the request body is authoritative; request fields may only narrow the server-derived grant.

The socket path and identities are intentionally not selected here. Socket ownership/mode, ancestor-directory protection, no-follow/replacement behavior, peer-credential checks, connection lifecycle, and revocation behavior require implementation review and target-OS tests. Peer credentials identify an OS principal, not a particular executable: this candidate is acceptable only if the requesting principal is sufficiently isolated that untrusted processes cannot run as it or inherit its authority. If that cannot be demonstrated, do not enable this transport; obtain review of a stronger independently enforced mechanism rather than treating the socket or binary as proof.

For each request, the enforcement process should:

1. Authenticate the local OS peer before constructing cloud clients or making any cloud/API request.
2. Load or validate the current protected policy and bind caller identity, configured cloud/project, selected target, allowed operation categories, policy identity, finite limits, and correlation to a server-owned context.
3. Reject missing, stale, revoked, malformed, or out-of-scope authority before any diagnostic implementation/authentication/API call; record a safe denial when the audit store is available, otherwise expose the audit gap locally without claiming a record exists.
4. Recheck current authority and remaining limits before each read and before result publication. A later response-scope failure must describe any prior contact honestly and withhold unsafe data.

A mock caller identity or in-process role check is useful for logic tests but cannot prove that an unauthorized local OS principal is denied. G1 remains open until a separately authorized target-OS test exercises allowed and unauthorized non-root contexts, credential/state access denial, and zero diagnostic/API calls on pre-dispatch denial.

## 3. G2 boundary: synthetic inputs versus operator configuration

### 3.1 Offline synthetic configuration

Credential-free tests may use synthetic cloud/project identities, synthetic reader policy, a finite test storage limit, and local-only controlled API fixtures. Fake credentials or tokens must be inert test values. These inputs exist only in the approved test process/fixture and do not establish a real tenant, reader policy, endpoint, filesystem capacity, or operator permission. Do not provision or execute these fixtures in this chunk.

### 3.2 Real operator-supplied configuration

Before any real startup/use, an operator must provide and protect the selected cloud/project scope, approved Keystone/Nova/Neutron destinations, dedicated project-reader credential source and policy, protected data-area configuration, and a finite usable managed-storage limit. The approved configuration source and credential format remain deployment decisions; no account name, endpoint, path, credential, storage technology, or privilege grant is chosen by this document.

Configuration and credentials must not be inferred from repository files, `.env`, ambient SDK environment variables, caller arguments, archived contracts, model output, or API response data. The reader credential source must be readable only by the credential-owning domain and must not be exposed in process arguments or logs. A dedicated project reader is required; permission failure means unavailable/denied, never escalation to admin, operator-reader, or another profile. The actual reader source and authorization must be reviewed before use; the PRD preference for application credentials applies only where supported and approved.

Startup/use must fail closed if trusted scope, protected setup, current policy, or a finite usable limit is missing or invalid. A local readiness check must not silently perform a name lookup or cloud connectivity probe. G2 is not satisfied by synthetic fixtures or a successful local build.

## 4. G3 candidate: narrow reader operations and fixed transport

The following is a proposed allowlist for the Phase 01 server-basic workflow, not a claim that these calls are already reviewed or permitted by the lab’s reader policy. G3 review must confirm the actual API versions, visibility, response fields, and reader permissions before a collector is enabled.

| Proposed operation | Authorization and relationship rule | Required returned-identity checks and limits |
| --- | --- | --- |
| Keystone authentication to the single operator-configured identity destination | Use only the separately approved dedicated project-reader source and configured project. Authentication is not permission to perform a diagnostic read. | Verify the authenticated reader/project against trusted configuration before resource reads. Do not accept a caller-selected identity endpoint or use stronger credentials. The precise credential method remains open for operator/reviewer decision. |
| Optional Nova server-name resolution for an explicit manual action | Only when the operator deliberately requests the named server diagnostic; a help/readiness/catalog request is not consent. Use a bounded project-scoped query and preserve the original literal name, including meaningful whitespace and case. | Treat server-side name filtering as approximate; independently compare returned names literally and case-sensitively, verify project and canonical UUID, and require a unique result within fixed page/record/time/byte bounds. Missing, ambiguous, or bound-exhausted results cause no guessed server GET. Never use unbounded `AllPages`. |
| Nova server detail for the resolved canonical server UUID | The target must be in the current trusted project and explicitly selected by the manual action. | Verify returned server UUID and project before using or disclosing fields or authorizing another read. Project mismatch means withhold the payload, stop related reads, and report that the read may already have occurred. Project only the required safe server-basic fields and explicit availability states. |
| Nova flavor detail for the flavor ID returned by the verified server response | Permit only if the current trusted grant explicitly includes the related-flavor category. Caller-supplied flavor IDs are not relationships. | Verify returned flavor identity against the server-derived ID. Do not list/search flavors, read extra specs, or collect unrelated flavor data. |
| Neutron port listing filtered by the verified server UUID (`device_id`) | Permit only if the current grant includes related-port context and the server/project relationship has been verified. No caller-supplied port ID creates authority. | Bound pages, records, bytes, time, and output during collection. Verify every returned port’s project/tenant and device linkage against the authorized project/server. Do not traverse networks/subnets or broaden into project-wide discovery. |

### 4.1 Destination and transport constraints

- Maintain a server-side allowlist containing only the operator-configured Keystone identity destination and the reviewed Nova and Neutron service destinations needed for the enabled operation. No request parameter, model content, resource response, pagination URL, or redirect may add or replace an origin.
- Treat HTTPS with certificate validation and a reviewed trust source as the candidate transport. Do not disable certificate verification. If the target environment cannot support the reviewed transport, keep collection disabled pending an explicit security review; do not silently add an exception.
- Do not inherit ambient proxy behavior or credentials. In particular, do not use proxy environment variables, default environment-derived SDK authentication, caller-selected transports, or implicit auth/profile fallback. Configure transport behavior explicitly.
- Disable redirects for authenticated requests. Reject any response/pagination link that changes the approved scheme, host, port, or permitted service path; never forward a token to a new destination. Apply finite request deadlines, retries only for explicitly safe transient cases, response-byte limits while reading, page/record caps, and cancellation throughout collection.
- A token/service catalog may not expand the trusted destination set by itself. Validate any selected service endpoint against the operator-configured allowlist before sending credentials or requests. Denials, TLS errors, timeouts, malformed links, and reader-policy failures stop the operation without fallback.
- Keep the configured project and selected target in server-owned authorization context. Verify returned identity/relationships before every subsequent read; do not treat a successful API response or common resource name as a grant.

G3 review should inspect the actual SDK/HTTP transport defaults (including proxy and redirect behavior), authentication construction, service-catalog handling, pagination, token handling, and returned identity checks. Synthetic HTTP tests can establish request order and rejection behavior, not actual cloud reader permissions or deployed policy.

## 5. G4 candidate: protected versioned state and fail-closed ordering

### 5.1 Namespace, creation, and durability

Use a new protected namespace, separate from every legacy investigation, memory, workflow, and project store. An explicit format/version marker is required. The operator-selected data root and version name are not chosen here. Never read, import, index, send, modify, delete, clean, or reuse approvals from legacy stores. Refuse corrupt, incompatible, unsafe, or uncertain state; do not auto-repair it or claim it was saved.

A candidate Linux filesystem sequence, subject to target-filesystem review and fault tests, is:

1. Open the operator-configured root relative to a trusted directory handle; verify ownership, restrictive permissions, expected directory/file types, and no symlink traversal. Do not follow untrusted replacement paths.
2. Create each new namespace directory exclusively with restrictive permissions; synchronize the parent directory after adding an entry, then synchronize the new directory after its initial contents are durably installed. If required directory synchronization is unsupported or fails, keep admission closed.
3. For a new record, create a same-directory temporary file exclusively with restrictive permissions and no-follow semantics; write the complete bounded sanitized record, synchronize the file, atomically rename it into place, then synchronize its containing directory. Do not claim success after a short write, failed sync, failed rename, or uncertain result.
4. Reopen and validate format, integrity, scope, permissions, and recovery state before admission. No automatic schema migration or fallback to a legacy path is permitted.

Exact syscall choices, filesystem/mount support, directory layout, ownership, and durability guarantees require G4 review. File sync plus rename alone is not evidence of durable directory entries. If the selected filesystem cannot meet and demonstrate the required ordering, do not enable persistence-dependent diagnostics.

### 5.2 Writer, admission, health, and lock ordering

A Level 1 candidate is one exclusive cross-process namespace lock shared by admission, health transitions, record writers, and cleanup. Always acquire that lock before reading/modifying durable health, capacity reservations, intent/outcome records, recovery acknowledgements, or cleanup state. Do not acquire a second store lock beneath it or call a helper that reacquires it. Bound lock wait; contention, lock corruption, or lock timeout rejects the request without cloud authentication or API calls.

Under the lock, verify store version/integrity, current health/recovery state, trusted configuration, usable quota, and the required write reservation before recording intent. Persist and synchronize the intent before dispatch. Keep admission serialized through the bounded read and durable result/outcome record. Release no result to the caller until its sanitized outcome is durable. A simpler single-writer policy sacrifices parallel throughput but avoids conflicting admissions/writes; any alternative must document and prove an equivalent cross-process ordering.

If a process exits while holding the OS lock, the lock may be released by the OS, but the durable pending intent must remain visible. On restart, an unresolved intent or uncertain outcome is not a healthy state: refuse new dispatch until recovery is explicitly handled. A volatile mutex/latch, process restart, or missing health marker cannot clear uncertainty.

### 5.3 Capacity, audit, result, and recovery sequence

Require an operator-supplied finite usable managed-data limit before use. Account for managed records, sanitized audit/control/recovery metadata, and outstanding reservations. Before an external read, reserve enough bounded space for its intent, maximum permitted sanitized result/outcome, and a recovery/failure marker. Use a reservation method that actually allocates capacity on the selected filesystem; if that cannot be established, refuse dispatch. Independently check and report physical filesystem exhaustion: managed-quota exhaustion and actual `ENOSPC` are distinct, and every write/sync can still fail despite reservation.

For each admitted operation:

1. Authenticate the local peer and derive current authorization; reject invalid requests before any cloud/API call.
2. Acquire the namespace lock; validate durable health, version, current scope, limits, and capacity. If any mandatory control is unavailable, fail closed.
3. Sanitize and durably persist the bounded intent and reservation before authentication or diagnostic dispatch. A failed or ambiguous intent write means no reader/API call.
4. Perform only the admitted bounded read(s), checking current authorization, relationships, cancellation, and remaining limits between operations.
5. Minimize/sanitize the response before every sink. Verify returned identity/relationships before subsequent reads or disclosure.
6. Durably persist the safe outcome/status, timing, correlation, required provenance, and audit result before returning any diagnostic payload. If outcome persistence fails after a read, stop later dispatch, withhold the payload, expose the possible prior read and audit gap locally, and leave admission unhealthy. Never claim that a read was rolled back.

A denied request with an unavailable audit store must be rejected without a reader call and must visibly report that no durable denial record could be confirmed. Do not fabricate an audit event, retry an ambiguous append as though it definitely failed, use an unprotected fallback sink, or report a saved result without durable confirmation.

### 5.4 Minimal payload retention

The candidate retains only the minimum sanitized intent, scope/policy identity, status, timing, safe error/gap, and provenance needed for audit and recovery. It does **not** retain a full diagnostic payload by default. Keep a sanitized result in process memory only long enough to commit its durable outcome; disclose it only after that commit. If the process crashes or the payload cannot be safely recovered, report the unresolved/uncertain read honestly. Recovery acknowledgement is not authorization or consent to recollect; a new collection requires separate operator confirmation, current authorization, and a new timestamped observation. This choice reduces retained sensitive data but means an interrupted result may be unavailable and need an explicitly authorized new read.

### 5.5 Cleanup and retention

Cleanup is bounded by explicit record, byte, and time limits, and runs only during startup/operation—not while the runtime is stopped. At startup, inspect required health and unresolved recovery before admitting diagnostics. Delete only known eligible records under current retention rules; protect unresolved recovery state and unknown, active, or referenced data. The PRD’s configurable 90-day sanitized-audit default applies to audit records. The 30-day terminal-investigation default applies only when such records are introduced; this manual-only candidate does not invent investigation records or lifecycle.

For each cleanup batch, acquire the same namespace lock, persist and synchronize a sanitized deletion intent before removing eligible records, then durably record the outcome. If intent persistence fails, delete nothing. If outcome audit fails after deletion, report the gap and possible completed deletion; do not claim rollback. Never silently delete unexpired data to free space, delete audit records before their retention period, or touch legacy data.

## 6. Required fixture and evidence ledger

Statuses below reflect the latest recorded Chunk 0 evidence, not tests run by this document. No fixture was created, mounted, filled, configured, executed, or cleaned up for Chunk 1.

| Required property / facility | Current evidence status and provenance | Exact future evidence required |
| --- | --- | --- |
| Unauthorized local caller versus permitted non-root requester; protected credential/state separation on the target OS | **UNVERIFIED.** Chunk 0 handoff `009` reports no target-OS security-context proof. This document ran no OS test. | On the approved target OS, use separately authorized permitted and unauthorized non-root contexts. Prove peer authentication, denial before any diagnostic/API call, and inability to read/replace credentials, policy, or state. Mocks, package boundaries, or one process do not satisfy this property. |
| Actual bounded disposable filesystem and physical exhaustion distinct from managed quota | **UNAVAILABLE among identified locations.** Plan §15 / handoff `009` reports that read-only inspection of `assistant01:/opt/aiops-openstack-lab/` found an empty directory on the VM’s ordinary root ext4 filesystem, not a bounded fixture. This does not establish that no other facility exists. | After separate facility-specific authorization, run actual exhaustion only on a named disposable bounded filesystem; capture capacity and observed `ENOSPC`, distinguish it from injected write errors and managed quota, and use an explicit owner/cleanup authority. Never fill the repository, active controller/assistant root filesystem, or lab disk. |
| Utility/interpreter-free single-runtime execution | **UNVERIFIED.** Chunk 0 handoff `009` reports no controlled runtime proof; no executable was run for this document. | In a separately approved controlled environment, run the built Go runtime directly against local synthetic API fixtures; inspect the process tree and required files to establish no diagnostic shell, CLI, script, interpreter, or external diagnostic utility dependency. `PATH` filtering alone is insufficient. |
| Independent-process writer/admission, crash/restart, and recovery ordering | **UNVERIFIED.** No independent-process or crash fixture was exercised in this documentation chunk. | Use separately authorized processes and fault barriers to interrupt before dispatch, in flight, and after a read/before durable outcome. Prove lock contention fails closed, pending intent survives restart, no replay occurs, and acknowledgement/current authorization/separate recollection confirmation remain distinct. |

Fixture availability is not permission to prepare or execute a facility. Before any dependent check, a separate explicit authorization must identify the VM/facility, owner, exact setup and test actions, capacity/other bounds, and cleanup authority. Missing facilities block their dependent verification and final acceptance; they do not block this documentation-only chunk and must never be converted into a passing skip.

## 7. Operator sequence after all applicable gates pass

This sequence describes intended safe operation only; it is not presently executable behavior.

1. **Before startup/use:** the operator supplies and protects trusted project-reader configuration, approved destinations, credential source, data area, and finite storage limit. Confirm required G1/G4 reviews and G2 setup; keep diagnostics unavailable if any mandatory control is absent.
2. **Before enabling a manual entry point:** complete the separately reviewed G1 realization and actual unauthorized-local-caller OS proof. Before enabling a collector, complete G3 review of API relationships, reader visibility, authentication, and transport. Before persistent execution, complete G4 review and the required implementation safeguards.
3. **At request time:** authenticate the local caller; derive current scope from protected configuration; validate the exact target and allowed category; reserve capacity and persist intent before any reader/API dispatch. Help/readiness must not perform diagnostic lookup.
4. **During collection:** use only the reviewed fixed API operations, bounded transport, and verified server-derived relationships. Recheck authorization and budgets between calls. Never escalate credentials or follow a redirect/pagination link outside the fixed destination policy.
5. **Before returning evidence:** minimize and sanitize first, persist the outcome/audit durably, then release the result. Show missing/denied/unavailable fields and collection limitations explicitly; do not call missing evidence healthy or assert a root cause without supporting evidence.
6. **On store/audit/capacity failure:** stop new dispatch and withhold any result whose required outcome is not durable. Report whether a read may already have occurred and whether an audit gap exists. Do not retry an uncertain operation automatically.
7. **After recovery:** remain paused until the operator acknowledges known gaps/uncertain calls. Recheck current policy; acknowledgement restores neither authority nor permission to recollect. An uncertain new read requires separate confirmation and a new timestamped observation.
8. **Cleanup:** perform only bounded, audited cleanup of known eligible data while running; report failures and possible post-delete audit gaps. Never clean legacy stores or silently evict unexpired records.

## 8. Review questions and unresolved deployment decisions

Reviewers must resolve these before the affected gate—not by treating this candidate as approved:

- Does the proposed OS principal mapping and local IPC meet G1 on the actual target OS, including the same-UID/arbitrary-process risk? If not, which independently enforced alternative satisfies the same boundary without expanding privileges?
- Which operator-controlled configuration and reader credential source are supported for G2, and how are scope, finite usable limit, ownership, revocation, and endpoint trust verified without ambient environment inputs?
- Do the proposed Nova server lookup/detail, related flavor, and Neutron port operations match actual project-reader policy and service visibility? Which API versions, response identity fields, destination allowlist, TLS trust, pagination, and transport defaults are approved for G3?
- Does the selected filesystem support the G4 first-create/directory durability, cross-process locking, bounded reservation, recovery, and cleanup semantics? Which actual disposable facilities and fault evidence are available under separate authorization?
- Can the minimal no-payload-retention policy satisfy safe recovery and operator needs? If a payload is interrupted or cannot be recovered, the documented fallback is an honest gap and separately authorized recollection—not silent reconstruction.

Until these questions have evidence-backed answers and the applicable reviews/approvals are recorded, the relevant execution or enablement gate remains **pending**. This document does not authorize Chunk 2, fixture preparation, startup, cloud access, or deployment.
