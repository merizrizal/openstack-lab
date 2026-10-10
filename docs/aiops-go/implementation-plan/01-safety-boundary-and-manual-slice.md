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

- [ ] Maintainer selects one authoritative registry/policy owner before adapters are wired. Prefer compatibility-first Go integration; do not assume Go must replace Python.
- [ ] Operator specifies observer placement, initial cloud/project, approved endpoints and dedicated project-reader policy. Privileged provisioning is outside the product.
- [ ] Existing scripts/SDK tools and tests are reviewed reuse candidates, not already accepted capabilities.
- [ ] Offline fixtures require no cloud/provider credentials; live enablement waits for Phase 07 or an explicitly authorized equivalent early acceptance gate.

Dependency: none. Blocks all new automatic diagnostic paths.

## 01.5 Ordered Tasks

### Step 1 - Reconcile authority and prove a denied request

Estimate: **2-3 days / 12-18 hours**.

- [ ] Inventory retained CLI/agent/workflow/runner/MCP entry points and deployed asset lineages; record owner, contract versions, bypass risks, compatibility consumers and current verification status.
- [ ] Decide whether Go invokes the retained runner or owns a parity-tested boundary. Establish one reviewed definition source, not independent permissive registries. Record migration and rollback strategy.
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

- [ ] Route a server-basics call through the existing Go/manual interface and selected adapter, then extend the same path to server fault/flavor, server networking and separately scoped project summaries.
- [ ] Preserve canonical UUID and exact-name resolution with ambiguous/missing rejection. Retain original/resolved identifiers, reject unsupported script names with UUID guidance, and never silently widen conservative validation.
- [ ] Validate required/extra fields, types, ranges and length before dispatch; enforce cloud/project/target/profile/relationship rules on every call. Bring SDK tools under the same boundary or disable them; no direct-agent registry bypass remains.
- [ ] Use fixed executable mappings and argument vectors, a minimal explicit environment and trusted paths. Reject caller-selected implementation, command, credential, profile override or generic CLI arguments.
- [ ] Bound API pagination, elapsed time, retries, concurrency, stdout/stderr capture and aggregate payloads during collection. Propagate cancellation; terminate and reap owned subprocess descendants, with no subsequent dispatch.
- [ ] Minimize fields and redact before results, errors or streams reach storage, reports or model-facing consumers. Withhold sensitive data that cannot be transformed safely; do not collect user-data/full configurations.
- [ ] Record sanitized request intent before execution and outcome afterward. Audit failure before dispatch denies execution; terminal audit failure is visible and blocks further calls until recovery. Local error reporting must not depend on the failed sink.
- [ ] Expose named-tool catalog/invoke behavior without inference and with versioned output/exit mappings; clearly distinguish empty results, unavailable tools, denied access and collection failure.

Done when:

- [ ] Manual fixtures return useful scoped evidence or explicit limitations through the authoritative boundary for both SDK and script-backed tools, without broadening existing contracts.

### Step 3 - Lock in safety and compatibility evidence

Estimate: **2-3 days / 12-18 hours**.

- [ ] Reuse temporary-executable/API fixtures and runner tests; cover every result status, fixed argv, unknown tools, invalid/extra arguments, ambient admin environment, profile/cloud/target escape and valid related reads.
- [ ] Add secret canaries in nested payloads, errors and split output chunks; test truncation/redaction boundaries, output floods, malformed encoding, timeouts and cancellation cleanup.
- [ ] Verify required audit/policy failure stops dispatch; disk-full and permission errors cannot claim a successful audit or leak raw denied payloads. Bound and log-injection-proof audit records.
- [ ] Prove fix/restart/edit/create/delete requests never map to a mutation capability, including explicit operator requests to ignore restrictions.
- [ ] Seed a versioned offline scenario/result format with a healthy server, permission denial and hostile tool output. Record expected calls, targets, statuses, evidence and safety assertions for later phases.
- [ ] Run targeted Go tests/build and applicable existing runner/static diagnostic checks in their documented environments; compare legacy/current envelopes and record any intentional versioned differences.
- [ ] Document manual no-model use, extension review requirements, credential revocation ownership and deployment preflight. Specify operator-only read/mutation-denial procedures using disposable fixtures; never register those probes as tools.

Done when:

- [ ] AC-004, AC-012 and AC-014–AC-015 have local/SDK/script fixture evidence, with future nested/resume/MCP cases assigned to their phases. No fixture result is labeled deployed reader-policy proof.

## 01.6 Phase Definition of Done

- [ ] One authoritative boundary and registry are selected and observable at every enabled local diagnostic entry point.
- [ ] Named manual diagnostics work without inference; rejected requests never execute and accepted results are bounded, sanitized and audited.
- [ ] Existing contracts have parity evidence or explicit migration requirements; no old runner is silently removed.
- [ ] Runtime/profile deployment prerequisites are documented; unverified live capabilities remain disabled.

## 01.7 Risks

| Risk | Mitigation |
| --- | --- |
| Competing runtime/registry ownership | Resolve before integration; inventory all bypass paths and test parity. |
| Related reads become broad discovery | Derive relationships from authorized observations and review each visibility rule. |
| Output is sanitized only after leakage | Test every storage/display/stream boundary with canaries. |
| Read-only role name is mistaken for policy proof | Require separately authorized deployed acceptance before live use. |
| Timeout leaves descendants or retries alive | Verify cleanup and zero post-cancellation dispatch on the supported OS. |
