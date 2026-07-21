# 09. Local Orchestrator Core

## 09.1 Goal

Build a minimal repository-owned orchestrator that can execute one bounded diagnostic workflow through a fake Codex adapter without authentication, network access, deployment changes, or provider traffic.

Target outcome:

```text
validated operator request
  -> bounded workflow state machine
  -> fake Codex adapter
  -> sanitized result category and metadata
  -> deterministic local tests
```

## 09.2 Estimate

Total estimate:

```text
1.5-2.5 engineer-days
9-15 focused hours
```

## 09.3 Scope

Included:

* Minimal TypeScript application compatible with the supported Codex SDK.
* Typed input, workflow-state, adapter, event, result, and error contracts.
* Fake/injected Codex adapter as the default test seam.
* Bounded turns, deadlines, cancellation, output handling, and metadata categories.
* Unit and local process tests with network access prohibited.

Excluded:

* Real Codex SDK provider invocation.
* ChatGPT login or runtime-home access.
* MCP tool execution beyond a compile-safe interface seam.
* Ansible deployment, service identity, or egress changes.
* Persistent prompts, responses, or raw SDK event logs.

## 09.4 Assumptions

- [ ] Phase 08 ADS and dependency policy are approved.
- [ ] The repository can add a small pinned TypeScript package without changing existing Python safety components.
- [ ] The fake adapter can represent only reviewed bounded lifecycle events needed by the orchestrator.

## 09.5 Ordered Tasks

### Step 1 - Scaffold the Deterministic Application

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Create the minimal package, lockfile, build, test, lint, and type-check commands defined by the ADS.
- [ ] Pin direct dependencies and prevent lifecycle scripts or undeclared network downloads during tests.
- [ ] Add a non-network test command suitable for CI and local validation.
- [ ] Document the application entry point without adding a service or public listener.

Done when:

- [ ] A clean deterministic install can build and run an empty local test suite.

### Step 2 - Add Typed Workflow Contracts

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Define a closed diagnostic-request schema with a reviewed workflow name and bounded parameters.
- [ ] Define bounded workflow states and terminal categories without raw provider details.
- [ ] Define the Codex adapter interface and event allowlist before any real adapter implementation.
- [ ] Define explicit timeout, cancellation, turn-count, and output-size limits.
- [ ] Reject unknown fields, workflows, events, and state transitions.

Done when:

- [ ] Invalid or ambiguous requests fail before adapter invocation and all state transitions are type-checked.

### Step 3 - Implement the Fake Codex Adapter

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Implement deterministic success, bounded failure, timeout, cancellation, malformed-event, and excessive-event scenarios.
- [ ] Ensure the fake never imports credentials, starts Codex, opens sockets, or reads a runtime home.
- [ ] Make the fake observable by counts and categories rather than prompt or response retention.
- [ ] Verify dependency injection prevents accidental use of a real adapter in local tests.

Done when:

- [ ] The orchestrator can exercise every terminal workflow category without network or credential access.

### Step 4 - Implement One Bounded Workflow Slice

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Accept one reviewed diagnostic workflow request.
- [ ] Run it through validation, deadline, state transition, fake adapter, and bounded result handling.
- [ ] Return only a sanitized operator-facing status and manual next-step category.
- [ ] Clean up temporary state on success, failure, cancellation, and test interruption.
- [ ] Prevent model output from becoming an executable action.

Done when:

- [ ] One local end-to-end workflow is repeatable, bounded, and independent of Codex authentication or transport.

### Step 5 - Add Core Regression Tests

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Test valid and invalid request schemas.
- [ ] Test every allowed and forbidden state transition.
- [ ] Test deadline, cancellation, event-count, turn-count, and output-size limits.
- [ ] Test cleanup and absence of raw content in errors and test snapshots.
- [ ] Test that the local suite opens no listener and invokes no real Codex process.

Done when:

- [ ] Build, type-check, lint, and focused tests pass without credentials or network access.

## 09.6 Phase Definition of Done

This phase is done when:

- [ ] The local orchestrator package builds deterministically.
- [ ] One fake-backed workflow passes end to end.
- [ ] Limits and cancellation fail closed.
- [ ] No credential, runtime-home, MCP, provider, or deployment access occurs.
- [ ] Errors and metadata contain no raw prompt or response content.

## 09.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| The fake diverges from supported SDK lifecycle semantics | Base its event contract only on reviewed public SDK types and add real-adapter contract tests later. |
| TypeScript introduces an unmanaged toolchain | Pin versions, lock dependencies, and provide one deterministic validation sequence. |
| Workflow state grows into an autonomous remediation engine | Keep one diagnostic-only workflow, bounded turns, and untrusted text output. |
| Tests accidentally invoke the real runtime | Require explicit adapter injection and make the fake the only test/default adapter. |
