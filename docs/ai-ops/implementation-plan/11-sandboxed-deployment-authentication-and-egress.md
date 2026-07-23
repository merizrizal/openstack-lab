# 11. Sandboxed Deployment, Authentication, and Egress

## 11.1 Goal

Deploy the locally validated orchestrator under a dedicated sandboxed identity, establish an operator-owned Codex login lifecycle without credential inspection, and prove bounded egress controls before any provider request.

Target outcome:

```text
pinned orchestrator and Codex dependencies
  -> dedicated identity and protected runtime home
  -> local-only deployment validation
  -> operator-owned Codex login gate
  -> synthetic egress validation and rollback
  -> ready for separately approved remote acceptance
```

## 11.2 Estimate

Total estimate:

```text
2-4 engineer-days
12-24 focused hours
```

## 11.3 Scope

Included:

* Deterministic Ansible deployment of the orchestrator and pinned dependencies.
* Dedicated service/process identity, protected runtime home, and minimal filesystem access.
* On-demand execution or service sandbox with no public listener.
* Operator-owned supported Codex login and logout/status runbook.
* Egress policy design and synthetic non-provider validation.
* Local deployment, rollback, and repeatability validation.

Excluded:

* Reading, copying, parsing, or displaying Codex credential files or values.
* A real provider request.
* Private provider endpoint or content-type assertions.
* Relaxing `assistant` direct-public-egress denial.
* Historical provider-gateway retirement.

## 11.4 Assumptions

- [x] Phase 10 local end-to-end safety validation passes.
- [x] The approved ADS selects a dedicated identity and protected runtime-home layout.
- [x] The supported Codex login flow can operate under that identity without exposing credentials to automation.
- [x] Egress claims can be stated honestly despite vendor-managed provider routing.

## 11.5 Ordered Tasks

### Step 1 - Implement the Supported Codex SDK Adapter

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [x] Implement the approved Codex adapter interface using only public SDK APIs.
- [x] Map supported SDK lifecycle events into the orchestrator's closed bounded event categories.
- [x] Apply supported working-directory, MCP, cancellation, retry, concurrency, and timeout configuration from fixed policy.
- [x] Keep real-adapter selection explicit and remote-disabled by default.
- [x] Add mocked-SDK contract tests that invoke no Codex process, credential path, DNS lookup, or provider socket.
- [x] Treat unknown SDK events or unsupported configuration as fail-closed compatibility errors.

Done when:

- [x] The real adapter compiles and passes mocked public-contract tests while remote invocation remains disabled.

### Step 2 - Add Deterministic Deployment

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [x] Add role-owned installation for the pinned orchestrator build, lockfile dependencies, and required Codex runtime.
- [x] Create the dedicated system identity and exact protected directories with minimal modes.
- [x] Keep the existing assistant runtime, credentials, MCP artifacts, and historical provider ledger outside writable scope.
- [x] Render an on-demand sandboxed unit or equivalent fixed launcher with no network listener.
- [x] Clear or reject proxy and unreviewed environment influence where supported.

Done when:

- [x] A first and repeated deployment converge and the installed artifact matches the reviewed dependency set.

### Step 3 - Validate the Local Deployment with Network Disabled

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Run build/version, ownership, mode, unit-hardening, process, listener, and writable-path assertions.
- [x] Execute the fake-adapter workflow through deployed local MCP and runner boundaries.
- [x] Verify cleanup, evidence permissions, and no provider/DNS connection.
- [x] Verify `assistant` direct-public-egress denial remains unchanged.
- [x] Provide a permanent read-only deployment validator.

Done when:

- [x] The deployed fake-backed workflow passes while public provider access remains unavailable.

### Step 4 - Define and Exercise Codex-Managed Login Operations

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Document operator-only login, status-category, refresh behavior, logout, and recovery procedures using supported Codex commands.
- [x] Require separate approval before opening any temporary authentication egress window.
- [x] Suppress command output and retain only success/failure category where validation is required.
- [x] Never inspect runtime-home contents, `auth.json`, tokens, account identifiers, or device codes.
- [x] Verify runtime-home ownership and modes without reading content.

Done when:

- [x] An operator can establish or revoke Codex-managed authentication without repository automation handling credential values.

### Step 5 - Implement Bounded Egress Policy

Estimate:

```text
0.25-0.75 engineer-days
1.5-4.5 hours
```

Tasks:

- [x] Define the minimum DNS and HTTPS capabilities required by the supported Codex runtime identity.
- [x] Preserve deny-by-default public egress for `assistant` and unrelated identities.
- [x] Do not claim fixed private provider host/path controls that Codex does not publicly guarantee.
- [x] Add preconditions, explicit approval inputs, automatic rollback, and policy restoration checks.
- [x] Avoid generic proxy or caller-selected destination configuration.

Done when:

- [x] The enforceable egress boundary is documented, least-privileged, and fail-closed.

### Step 6 - Run Synthetic Egress and Rollback Validation

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Use only an operator-approved non-provider synthetic endpoint.
- [x] Prove the orchestrator identity's intended test path and `assistant` denial independently.
- [x] Prove temporary policy cleanup in success and failure paths.
- [x] Re-run permanent deployment, listener, identity, and egress validators after cleanup.
- [x] Record sanitized outcomes without addresses, credentials, or raw firewall output.

Done when:

- [x] Synthetic validation and rollback pass without contacting a provider or weakening `assistant` controls.

## 11.6 Completion Record

**Status:** Accepted on 2026-07-23.

The final fake-only deployment validator, approved synthetic egress success path,
independent `assistant` denial, and injected-failure rollback all passed. The
sanitized acceptance record is
[`phase11-sandboxed-deployment-validation-evidence.md`](../runtime/phase11-sandboxed-deployment-validation-evidence.md).

Phase 12 remains separately approval-gated. This acceptance does not enable the
official remote adapter, authorize authentication, or authorize a provider request.

## 11.7 Phase Definition of Done

This phase is done when:

- [x] The supported Codex SDK adapter passes mocked contract tests and remains remote-disabled by default.
- [x] Deployment is deterministic and sandboxed.
- [x] The fake-backed deployed workflow passes locally.
- [x] Codex authentication remains operator-owned and opaque.
- [x] Egress policy and synthetic rollback validation pass.
- [x] No provider request has occurred.

## 11.8 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Dedicated identity can read unrelated runtime or credential data | Use exact ownership, modes, read-only paths, and systemd filesystem restrictions. |
| Login automation leaks credentials | Keep login operator-owned, suppress output, and validate only categories and file metadata. |
| Vendor routing requires broader HTTPS than desired | Document the actual enforceable boundary and stop if it cannot meet the threat model. |
| Deployment accidentally enables remote execution | Keep fake adapter/default disabled, require explicit remote selection and separate acceptance approval. |
