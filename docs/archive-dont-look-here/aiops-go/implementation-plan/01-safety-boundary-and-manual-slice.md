# 01. Safety Boundary and Manual Slice

## 01.1 Goal

Deliver the first model-independent diagnostic through one authoritative, deny-by-default boundary, and define the deployment isolation it requires.

```text
explicit scope + named tool -> authorization/schema checks -> fixed bounded read -> sanitized evidence + audit
```

## 01.2 Estimate

Total: **6-10 engineer-days / 36-60 focused hours**.

## 01.3 Scope

Included: runtime/registry decisions, reader isolation contracts, application-owned authorization, related-resource rules, reviewed manual catalog baseline, SDK/script compatibility, structured results, redaction and audit. Primary requirements: FR-010–FR-011, FR-021–FR-025, FR-027–FR-030; NFR-001–NFR-003, NFR-010–NFR-011. Evidence: AC-004, AC-012, AC-014–AC-015; design prerequisites for AC-011.

Excluded: live provisioning during implementation without authorization, inference, project scheduling, host access, MCP, generic executable/shell/CLI tools and infrastructure mutation.

## 01.4 Assumptions

- [ ] Maintainer selects one authoritative registry/policy owner before adapters are wired, within the binding constraints below. Prefer compatibility-first Go integration; do not assume Go must replace Python.
- [ ] Operator verifies observer placement, initial cloud/project, approved endpoints and dedicated project-reader policy against the binding contracts below. Any change to their approved values requires the applicable amendment and approval; privileged provisioning is outside the product.
- [ ] Existing scripts/SDK tools and tests are reuse candidates only where their lineage and applicable contracts permit review; they are not already accepted capabilities or permission to invoke historical runtime paths.
- [ ] Offline fixtures require no cloud/provider credentials; live enablement waits for Phase 07 or an explicitly authorized equivalent early acceptance gate.

Dependency: none. Blocks all new automatic diagnostic paths.

### Constraint reconciliation and authority

This draft does not supersede accepted revised contracts. Phase numbers in those contracts refer to the revised AI-OPS plan, not the phases in this Go plan.

- **Binding placement and separation:** The [runtime placement contract](../../ai-ops-revised/runtime/runtime-placement-contract.md) fixes the separate observer and revised namespace, including host, runtime user/root, profile and audit locations. Do not alter, replace, share or invoke the historical `assistant01` runtime, paths or registrations. Preserve the documented rollback boundary.
- **Binding identity and scoped exceptions:** The [identity and policy contract](../../ai-ops-revised/runtime/identity-policy-operations-contract.md) fixes the initial `admin` project label, fresh revised reader identity, restricted credential provenance/scope, profile protections, expiry, rotation and revocation ownership. Historical, human, member, service and administrator credentials are not fallback candidates. Its local-lab transport exception applies only to the specified host and inventory; do not generalize it.
- **Binding source and capability restrictions:** The [selective-reuse manifest](../../ai-ops-revised/runtime/selective-reuse-manifest.md) is fail-closed, tied to its recorded provenance, exact paths, phase owners and dependency closure. Selection permits only the stated review, not copying, execution or activation; reference-only and excluded paths retain their restrictions. The [runner Steps 1–4 contract](../../ai-ops-revised/runtime/tool-runner-safety-gateway-steps-01-to-04-operations-contract.md) forbids copying, installing, importing or executing the historical runner/registry and fixes the initial three-tool set and revised targets. A retained runner means an eligible **revised** runner, not the historical runtime.
- **Binding result and audit guarantees:** Preserve the [runner Steps 5–7 contract](../../ai-ops-revised/runtime/tool-runner-safety-gateway-steps-05-to-07-operations-contract.md), including its closed, versioned result and single terminal-event contracts, fixed audit filesystem and persistence protections, until a replacement is approved. Compatibility means behavioral and security parity across authorization, credentials, execution, redaction, audit and failure handling, not merely matching result envelopes.
- **Revalidation, not presumed readiness:** Before reuse or enablement, check manifest provenance and dependency closure, retained entry points, actual deployment/profile/policy state and applicable prior test/acceptance evidence. Historical acceptance claims and offline fixtures do not prove current deployed isolation or credential readiness; record gaps and keep affected capabilities disabled.
- **Proposed changes and decision authority:** The proposed additional catalog, cancellation status and durable pre-dispatch intent/event protocol must not silently extend the existing closed allowlist or schemas. Identify each affected contract, proposed replacement, compatibility/migration and rollback; obtain explicit Level 2 approval and amend the governing contracts before enabling any conflicting behavior. Selecting a compliant adapter, helper or persistence mechanism within the approved contracts is Level 1; it does not permit changing fixed paths, security guarantees or scope. If reconciliation is unresolved, block the affected integration and continue only independent fixture/design work that does not prejudge it.

## 01.5 Ordered Tasks

### Step 1 - Reconcile authority and prove a denied request

Estimate: **2-3 days / 12-18 hours**.

- [ ] Inventory retained CLI/agent/workflow/runner/MCP entry points and deployed asset lineages; record owner, contract versions, bypass risks, compatibility consumers and current verification status.
- [ ] Decide whether Go invokes an eligible revised runner or owns a parity-tested boundary, subject to the constraint reconciliation above. Establish one reviewed definition source, not independent permissive registries. Record migration and rollback strategy, and obtain any required contract amendments before integration.
- [ ] Define versioned tool definitions: name/version, intent, argument schema, fixed implementation, profile, risk, scope/relationships, prerequisites, timeout, output bound and read-only guarantee.
- [ ] Define application-controlled request context: actor/client, cloud/project, canonical targets, capability/profile set, policy/approval identity, correlation IDs and budgets. Model/client arguments cannot override this context.
- [ ] Review relationship rules for server-to-flavor/port/subnet/volume reads. Require an authorized observation plus approved visibility; separately authorize project-wide summaries and host evidence. Reject relationship claims supplied only by the model.
- [ ] Define result statuses `ok`, `error`, `denied`, `validation_error`, `timeout`, `cancelled`, `unavailable`; include sanitized target/arguments, correlation, duration, data/error, applicable exit code and independent truncation/redaction metadata. Document legacy status translations.
- [ ] Define isolated observer placement, minimal management/API reachability, credential separation and owner-restricted executable/configuration versus writable data locations. Operator/SSH profiles remain disabled and never fallback credentials.
- [ ] Build the first recording-executor fixture: an out-of-scope request is denied and audited without dispatch. Reject malformed registry definitions, duplicate names and missing limits at startup.

Done when:

- [ ] Maintainer-approved ownership/scope contracts and a capability gap matrix exist; the negative vertical slice proves authorization precedes execution.

### Step 2 - Complete one bounded read and extend the manual catalog

Estimate: **2-4 days / 12-24 hours**.

- [ ] Route a server-basics call through the existing Go/manual interface and selected adapter; extend the same path to server fault/flavor, server networking and separately scoped project summaries only within the approved capability set or after the required explicit contract amendment. Do not enable unapproved additions by registry edit alone.
- [ ] Preserve canonical UUID and exact-name resolution with ambiguous/missing rejection. Retain original/resolved identifiers, reject unsupported script names with UUID guidance, and never silently widen conservative validation.
- [ ] Validate required/extra fields, types, ranges and length before dispatch; enforce cloud/project/target/profile/relationship rules on every call. Bring SDK tools under the same boundary or disable them; no direct-agent registry bypass remains.
- [ ] Use fixed executable mappings and argument vectors, a minimal explicit environment and trusted paths. Reject caller-selected implementation, command, credential, profile override or generic CLI arguments.
- [ ] Bound API pagination, elapsed time, retries, concurrency, stdout/stderr capture and aggregate payloads during collection. Propagate cancellation; terminate and reap owned subprocess descendants, with no subsequent dispatch.
- [ ] Minimize fields and redact before results, errors or streams reach storage, reports or model-facing consumers. Withhold sensitive data that cannot be transformed safely; do not collect user-data/full configurations.
- [ ] Require durable sanitized request intent before dispatch and a durable terminal audit before publishing a successful result. Intent persistence failure denies dispatch. If terminal persistence fails, return a sanitized generic non-success result with diagnostic data and raw filesystem details withheld; never redispatch the diagnostic on audit failure. Preserve the recorded intent, expose incomplete or uncertain completion locally without relying on the failed sink, and block further calls until safe recovery. Never silently replay interrupted calls; any later intentional re-observation remains subject to Phase 03 recovery rules.
- [ ] Specify and version the intent and terminal event types, correlation, cardinality, interrupted/incomplete outcomes and legacy-consumer translations. Every request, including a pre-dispatch denial, must attempt a terminal audit; intent is required before any dispatch. The proposed two-stage protocol extends the existing closed single-terminal-event contract and requires the amendment and approval above before activation; retain its minimum-disclosure and durability guarantees.
- [ ] Expose named-tool catalog/invoke behavior without inference and with versioned output/exit mappings; clearly distinguish empty results, unavailable tools, denied access and collection failure.

Done when:

- [ ] Manual fixtures return useful scoped evidence or explicit limitations through the authoritative boundary for both SDK and script-backed tools, without broadening existing contracts.

### Step 3 - Lock in safety and compatibility evidence

Estimate: **2-3 days / 12-18 hours**.

- [ ] Reuse temporary-executable/API fixtures and runner tests; cover every result status, fixed argv, unknown tools, invalid/extra arguments, ambient admin environment, profile/cloud/target escape and valid related reads.
- [ ] Add secret canaries in nested payloads, errors and split output chunks; test truncation/redaction boundaries, output floods, malformed encoding, timeouts and cancellation cleanup.
- [ ] Verify intent is durable before dispatch and terminal audit is durable before successful publication; test write, disk-full, permission, flush/fsync and rotation failures at both applicable stages. Assert no current diagnostic payload or raw error leaks, no replay, preserved intent, visible incomplete completion, shared fail-closed behavior across concurrent callers, and safe recovery before new dispatch.
- [ ] Retain or provide equivalent audit regressions for fixed paths and modes/ownership, symlinks, non-regular and unsafe paths, locked non-interleaving concurrent append/rotation, integrity and recovery. No fallback sink or automatic unsafe-path repair. Bound and log-injection-proof audit records.
- [ ] Exercise every retained enabled entry point and approved profile, including SDK/script paths, with authorization, ambient-credential, executable/profile-override and no-dispatch denial regressions. Reject duplicate registry names and ambiguous exact server names; do not impose invented uniqueness on OpenStack names.
- [ ] Prove fix/restart/edit/create/delete requests never map to a mutation capability, including explicit operator requests to ignore restrictions.
- [ ] Seed a versioned offline scenario/result format with a healthy server, permission denial and hostile tool output. Record expected calls, targets, statuses, evidence and safety assertions for later phases.
- [ ] Run targeted Go tests/build and applicable existing runner/static diagnostic checks in their documented environments; compare legacy/current envelopes and record any intentional versioned differences.
- [ ] Document manual no-model use, extension review requirements, credential revocation ownership and deployment preflight. Specify operator-only read/mutation-denial procedures using disposable fixtures; never register those probes as tools.

Done when:

- [ ] AC-004, AC-012 and AC-014–AC-015 have only their applicable local/SDK/script fixture subset evidenced here. [Phase 02](02-bounded-investigation.md) owns nested-call scope-escape coverage and gates specialist dispatch; [Phase 03](03-durable-state-and-knowledge.md) owns resumed-call scope coverage; [Phase 05](05-gated-host-and-mcp-integrations.md) owns MCP parity when enabled. Specialists remain disabled unless separately approved and gated. No fixture result is labeled deployed reader-policy proof; [Phase 07](07-acceptance-and-rollout.md) owns the deployed gate.

## 01.6 Phase Definition of Done

- [ ] One authoritative boundary and registry are selected and observable at every enabled local diagnostic entry point.
- [ ] Named manual diagnostics work without inference; rejected requests never execute and accepted results are bounded, sanitized and audited.
- [ ] Binding revised contracts have behavioral/security parity evidence; any proposed incompatible version, capability or deployment replacement has an approved amendment and explicit migration/rollback requirements. No historical runtime is activated or silently changed.
- [ ] Runtime/profile deployment prerequisites are documented; unverified live capabilities remain disabled.

## 01.7 Risks

| Risk | Mitigation |
| --- | --- |
| Competing runtime/registry ownership | Resolve before integration; inventory all bypass paths and test parity. |
| Related reads become broad discovery | Derive relationships from authorized observations and review each visibility rule. |
| Output is sanitized only after leakage | Test every storage/display/stream boundary with canaries. |
| Read-only role name is mistaken for policy proof | Require separately authorized deployed acceptance before live use. |
| Timeout leaves descendants or retries alive | Verify cleanup and zero post-cancellation dispatch on the supported OS. |
