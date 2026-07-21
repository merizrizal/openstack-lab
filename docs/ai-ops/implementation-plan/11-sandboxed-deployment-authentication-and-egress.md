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

- [ ] Phase 10 local end-to-end safety validation passes.
- [ ] The approved ADS selects a dedicated identity and protected runtime-home layout.
- [ ] The supported Codex login flow can operate under that identity without exposing credentials to automation.
- [ ] Egress claims can be stated honestly despite vendor-managed provider routing.

## 11.5 Ordered Tasks

### Step 1 - Implement the Supported Codex SDK Adapter

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Implement the approved Codex adapter interface using only public SDK APIs.
- [ ] Map supported SDK lifecycle events into the orchestrator's closed bounded event categories.
- [ ] Apply supported working-directory, MCP, cancellation, retry, concurrency, and timeout configuration from fixed policy.
- [ ] Keep real-adapter selection explicit and remote-disabled by default.
- [ ] Add mocked-SDK contract tests that invoke no Codex process, credential path, DNS lookup, or provider socket.
- [ ] Treat unknown SDK events or unsupported configuration as fail-closed compatibility errors.

Done when:

- [ ] The real adapter compiles and passes mocked public-contract tests while remote invocation remains disabled.

### Step 2 - Add Deterministic Deployment

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Add role-owned installation for the pinned orchestrator build, lockfile dependencies, and required Codex runtime.
- [ ] Create the dedicated system identity and exact protected directories with minimal modes.
- [ ] Keep the existing assistant runtime, credentials, MCP artifacts, and historical provider ledger outside writable scope.
- [ ] Render an on-demand sandboxed unit or equivalent fixed launcher with no network listener.
- [ ] Clear or reject proxy and unreviewed environment influence where supported.

Done when:

- [ ] A first and repeated deployment converge and the installed artifact matches the reviewed dependency set.

### Step 3 - Validate the Local Deployment with Network Disabled

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Run build/version, ownership, mode, unit-hardening, process, listener, and writable-path assertions.
- [ ] Execute the fake-adapter workflow through deployed local MCP and runner boundaries.
- [ ] Verify cleanup, evidence permissions, and no provider/DNS connection.
- [ ] Verify `assistant` direct-public-egress denial remains unchanged.
- [ ] Provide a permanent read-only deployment validator.

Done when:

- [ ] The deployed fake-backed workflow passes while public provider access remains unavailable.

### Step 4 - Define and Exercise Codex-Managed Login Operations

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Document operator-only login, status-category, refresh behavior, logout, and recovery procedures using supported Codex commands.
- [ ] Require separate approval before opening any temporary authentication egress window.
- [ ] Suppress command output and retain only success/failure category where validation is required.
- [ ] Never inspect runtime-home contents, `auth.json`, tokens, account identifiers, or device codes.
- [ ] Verify runtime-home ownership and modes without reading content.

Done when:

- [ ] An operator can establish or revoke Codex-managed authentication without repository automation handling credential values.

### Step 5 - Implement Bounded Egress Policy

Estimate:

```text
0.25-0.75 engineer-days
1.5-4.5 hours
```

Tasks:

- [ ] Define the minimum DNS and HTTPS capabilities required by the supported Codex runtime identity.
- [ ] Preserve deny-by-default public egress for `assistant` and unrelated identities.
- [ ] Do not claim fixed private provider host/path controls that Codex does not publicly guarantee.
- [ ] Add preconditions, explicit approval inputs, automatic rollback, and policy restoration checks.
- [ ] Avoid generic proxy or caller-selected destination configuration.

Done when:

- [ ] The enforceable egress boundary is documented, least-privileged, and fail-closed.

### Step 6 - Run Synthetic Egress and Rollback Validation

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Use only an operator-approved non-provider synthetic endpoint.
- [ ] Prove the orchestrator identity's intended test path and `assistant` denial independently.
- [ ] Prove temporary policy cleanup in success and failure paths.
- [ ] Re-run permanent deployment, listener, identity, and egress validators after cleanup.
- [ ] Record sanitized outcomes without addresses, credentials, or raw firewall output.

Done when:

- [ ] Synthetic validation and rollback pass without contacting a provider or weakening `assistant` controls.

## 11.6 Phase Definition of Done

This phase is done when:

- [ ] The supported Codex SDK adapter passes mocked contract tests and remains remote-disabled by default.
- [ ] Deployment is deterministic and sandboxed.
- [ ] The fake-backed deployed workflow passes locally.
- [ ] Codex authentication remains operator-owned and opaque.
- [ ] Egress policy and synthetic rollback validation pass.
- [ ] No provider request has occurred.

## 11.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Dedicated identity can read unrelated runtime or credential data | Use exact ownership, modes, read-only paths, and systemd filesystem restrictions. |
| Login automation leaks credentials | Keep login operator-owned, suppress output, and validate only categories and file metadata. |
| Vendor routing requires broader HTTPS than desired | Document the actual enforceable boundary and stop if it cannot meet the threat model. |
| Deployment accidentally enables remote execution | Keep fake adapter/default disabled, require explicit remote selection and separate acceptance approval. |
