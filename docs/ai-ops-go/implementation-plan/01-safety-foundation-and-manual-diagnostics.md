# 01. Safety Foundation and Manual Diagnostics

**Phase boundary:** OWNER-APPROVED — the product owner approved this Phase 01 plan in the current conversation.
**Authority:** Approval covers this phase scope/decomposition only. This is not an approved implementation task contract, implementation preflight, or execution authorization.
**Source requirements:** [PRD](../prd.md), Diagnostic implementation form; Diagnostic safety and access; Retained toolbox and manual-operation requirements; Session, data lifecycle, and legacy records. FR-001–FR-003, FR-010–FR-011, FR-014, FR-021–FR-029, FR-039–FR-044, FR-046, FR-048–FR-050; NFR-001–NFR-006, NFR-008, NFR-010–NFR-015; AC-002, AC-004, AC-011–AC-015, AC-023–AC-024, AC-026–AC-031. Full acceptance closes across later phases as allocated in the overview.
**Decision gaps:** Overview G1–G4: security domains/authenticated IPC, acceptance configuration and reader relationships, protected storage design. Resolve applicable architecture/authority decisions before persistent execution; do not silently choose weaker isolation.

## 01.1 Goal

Create the shared safety boundary and a useful manual server diagnostic path in one Go runtime, with no model or MCP prerequisite.

```text
explicit project-reader scope + named server diagnostic
  -> validated Go gateway -> durable audit intent -> bounded API read
  -> sanitized audited result -> concise human/JSON output
```

## 01.2 Estimate

```text
10–15 engineer-days
60–90 focused hours
```

## 01.3 Scope

Included:

- Consolidation of relevant existing Go command/component seams into one runtime executable, without replacing unrelated lab operations.
- Application-owned scope, reviewed registry, finite tool limits, structured results, redaction and fail-closed audit.
- New protected versioned store, finite storage limit, actual disk-full detection and applicable retention/cleanup safeguards from first use.
- Manual server basics with required fields or explicit availability states; a narrow related-flavor/port path where approved relationships permit it.
- Observer/readiness prerequisites and deterministic safety fixtures; actual deployed acceptance is separately authorized and integrated in Phase 08.

Excluded:

- Model analysis or automatic tool selection, investigation planning/execution, resume, MCP, broad project discovery, full domain catalog and host access enablement.
- Legacy data migration, script/CLI diagnostic wrappers, infrastructure/account/credential provisioning by the runtime.

## 01.4 Assumptions

- [ ] A separately reviewed G1 design can expose only authenticated, scoped gateway operations between appropriately separated non-root security contexts.
- [ ] One configured project-reader project is sufficient; project switching must isolate existing records and authorizations.
- [ ] Existing Go API clients and scoped-broker validation patterns can be reused selectively; neither registry nor broker is assumed to meet the new boundary contract.
- [ ] Local protected persistence and sequential execution are proposals subject to G4; no database or network service is presumed.

## 01.5 Ordered Tasks

### Step 1 - Establish the runtime and trust boundaries

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Inventory reachable Go command/tool paths, identify reusable components and ensure no retained entry point bypasses the authoritative gateway.
- [ ] Following separately approved specifications, deliver one executable with manual diagnostic and readiness modes; multiple isolated processes using that executable are allowed, not a shared-identity security shortcut.
- [ ] Carry authenticated application-owned cloud/project, resource, capability/profile, policy and correlation context to dispatch; reject client/model overrides.
- [ ] Make optional model/knowledge/host/operator dependencies unnecessary for safe manual diagnostics. Define actionable required/optional readiness classifications.
- [ ] Document Ubuntu 24.04 x86-64 observer placement outside the observed cloud/control plane, management/API-only reachability and separate credential/state/provider access requirements.

Done when:

- [ ] A controlled no-model invocation reaches only the scoped boundary, and an unauthorized local caller cannot obtain tool execution or diagnostic credentials.

### Step 2 - Make requests, results and audit fail closed

Estimate: **4–6 engineer-days / 24–36 hours**.

- [ ] Define versioned tool metadata: diagnostic intent, fixed Go implementation, strict argument schema, scope/relationship rules, risk, profile, prerequisites, timeout and output bounds.
- [ ] Recheck authorization and finite limits at each dispatch; deny unknown tools, extra/invalid inputs, executable paths, generic commands, arbitrary hosts and stronger-profile substitutions before implementation invocation.
- [ ] Apply tool-local input validation as defense in depth. Use bounded structured API operations, not OpenStack CLI or diagnostic scripts.
- [ ] Return `ok`, `partial`, `error`, `denied`, `validation_error`, `timeout`, `cancelled`, or `unavailable` with safe details, target/correlation/duration and redaction/truncation metadata. Mark duration not applicable when no execution occurred.
- [ ] Sanitize/minimize arguments, errors and payloads before any persistent evidence, audit, report or telemetry sink; withhold content that cannot be transformed safely.
- [ ] Durably persist sanitized audit intent before allowed dispatch. On result-audit failure, stop calls and withhold payload from clients/models; locally expose the possible completed read and audit gap. Denial-audit failure must be visible, never reported as a saved record.
- [ ] Handle authorization expiry/revocation during a read: stop new work, attempt cancellation, withhold unauthorized results and explain that the read may already have occurred.

Done when:

- [ ] Recording fakes prove every denied request causes zero downstream calls; audit fault, cancellation, secret-canary and revocation-race fixtures meet the fail-closed result contract.

### Step 3 - Protect new data without touching legacy records

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Start an explicitly versioned Delivery 1 store separate from old investigation/memory/workflow/project paths, with restrictive ownership/permissions and scope partitions.
- [ ] Reject corrupt/incompatible state and serialize or reject concurrent writers. Make required persistence failures visible and stop execution rather than claiming a successful save.
- [ ] Require a finite usable protected-data limit at startup; distinguish managed quota exhaustion from physical disk exhaustion, including disk use by unmanaged legacy files.
- [ ] Provide bounded startup/runtime cleanup for applicable data, with 90-day sanitized-audit and 30-day terminal-investigation defaults as those record types appear. Never remove running/paused work or unexpired records automatically.
- [ ] Require durable audit intent for cleanup; expose outcome-audit gaps and possible completed deletion honestly. Preserve safe local inspection/export where possible during storage failure.
- [ ] Leave legacy files untouched, unindexed and unsent, outside automatic retention/cleanup. Do not reuse their approvals. Phase 04 adds reference-aware lifecycle and richer recovery, not permission to omit these initial safeguards.

Done when:

- [ ] Disk/quota/write/corruption/writer fault fixtures fail safely, cleanup is bounded and audited, and legacy file content hashes remain unchanged.

### Step 4 - Deliver and verify the first manual diagnostic workflow

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Provide named server-basic diagnostics accepting canonical UUIDs and literal case-sensitive exact names while preserving meaningful whitespace and original/resolved identity. Resolve compatibility differences explicitly; ambiguous/missing names give UUID guidance, not a guessed match.
- [ ] Bound and audit manual name lookup within the selected project. Do not perform a name-discovery read merely to display help/readiness.
- [ ] Expose status, image, flavor, networks, config drive, availability zone and available fault, with explicit unavailable/denied/not-applicable fields. Related flavor/port reads require verified relationships and allowed visibility.
- [ ] Create deterministic Go API/CLI recording fixtures for correct scope, cross-project/resource requests, secret fields, invalid arguments, permission failure, timeout, truncation and cancellation. Begin a versioned scenario/result format for later evaluation.
- [ ] Review/static-check diagnostic code for mutation, injection, unsafe file access and privilege escalation; supplement with behavioral assertions. Verify manual diagnostics in a controlled environment without diagnostic utilities/interpreters.
- [ ] Document registry, credential scopes, audit gaps/recovery acknowledgement, limits, protected storage and operator-only provisioning. Record applicable focused/full Go checks after implementation; do not claim today’s source inventory is a passing baseline.

Done when:

- [ ] An operator can select a named diagnostic and obtain a safe structured result without inference, MCP, arbitrary command composition or tools outside the Go runtime.

## 01.6 Phase Definition of Done

- [ ] One executable provides manual diagnostics/readiness, and all reachable diagnostic entry points use the same reviewed boundary.
- [ ] Core authorization, redaction, result, audit, persistence and storage-limit tests pass with zero unauthorized execution, mutation or prohibited disclosure.
- [ ] Manual identity and field-availability behavior is explicit and compatibility changes are documented.
- [ ] New data is protected and legacy content/approvals remain untouched and unused.
- [ ] Applicable G1–G4 decisions and verification evidence are recorded; absent live/environment access remains a named limitation, not deployed validation.

## 01.7 Risks

| Risk | Mitigation |
| --- | --- |
| Consolidation preserves an old bypass | Inventory every command/registry call; negative entry-point tests, not just a new facade. |
| A package boundary is mistaken for isolation | Require approved OS identities, authenticated IPC and adversarial access checks. |
| Literal-name repair broadens unsafe identifiers | Preserve exact intent and enforce strict independent validation; fail with UUID guidance when unsupported. |
| Read succeeds but audit/store fails | Withhold payload, stop dispatch, expose gaps and require acknowledged recovery. |
| Legacy scripts appear cheaper than Go capabilities | Use them only as selectively reviewed behavioral context; never make them runtime diagnostic dependencies. |

## 01.8 Proposed Requirement Coverage and Handoff

| Requirement / AC source | Proposed phase responsibility | Existing behavior / deferral | Risk or unapproved decision |
| --- | --- | --- | --- |
| FR-010–FR-011, FR-021–FR-024; AC-004/011/012/017 | Shared execution boundary, observer/profile prerequisites and relationships | Registry/broker are reuse candidates only; deployed proof later | G1–G3; no admin or shared-process shortcut. |
| FR-025/027–FR-029/043–FR-044; AC-002/014/027/029 | Manual server catalog, fixed Go execution, safe result/audit contract | Full catalog in 05/06, entry-point parity in 07 | Required field availability must not disappear silently. |
| FR-014/041–FR-042/048–FR-050; AC-007/023/024/031 | Durable core, readiness, quota, initial cleanup and new-store isolation | Full investigation recovery/reference lifecycle in 04 | G4; lifecycle safety applies from first applicable use. |
| FR-001/039–FR-040/046; AC-022/028 | Named manual CLI, tool events/bounds and documentation | Protected paste analysis in 02; no automation yet | No model/provider dependency for manual use. |

Proposed handoff to Phase 02: stable scoped gateway, manual fixture evidence, versioned sanitized envelopes, new-store contract and reviewed isolation prerequisites. The Phase 01 scope-readiness review is complete and this phase boundary is owner-approved; the implementation task contract and preflight remain separate gates. This file is not an implementation contract or execution authorization.
