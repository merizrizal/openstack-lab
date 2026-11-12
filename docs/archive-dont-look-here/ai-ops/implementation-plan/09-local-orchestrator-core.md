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

* Minimal Python application compatible with `openai-codex==0.144.4` and its pinned CLI runtime.
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

- [x] Phase 08 ADS and dependency policy are approved.
- [x] The orchestrator can extend the repository's existing Python safety conventions while isolating the beta SDK behind a repository adapter.
- [x] The fake adapter can represent only reviewed bounded lifecycle events needed by the orchestrator.

## 09.5 Ordered Tasks

### Step 1 - Scaffold the Deterministic Application

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Create the minimal Python package, deterministic lockfile, format, lint, type-check, and test commands defined by the ADS.
- [x] Pin direct dependencies and prevent lifecycle scripts or undeclared network downloads during tests.
- [x] Add a non-network test command suitable for CI and local validation.
- [x] Document the application entry point without adding a service or public listener.

Done when:

- [x] A clean deterministic install can build and run the local test suite.

### Step 2 - Add Typed Workflow Contracts

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Define a closed diagnostic-request schema with a reviewed workflow name and bounded parameters.
- [x] Define bounded workflow states and terminal categories without raw provider details.
- [x] Define the Codex adapter interface and event allowlist before any real adapter implementation.
- [x] Define explicit timeout, cancellation, turn-count, and output-size limits.
- [x] Reject unknown fields, workflows, events, and state transitions.

Done when:

- [x] Invalid or ambiguous requests fail before adapter invocation and defined state transitions are type-checked.

### Step 3 - Implement the Fake Codex Adapter

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Implement deterministic success, bounded failure, timeout, cancellation, malformed-event, and excessive-event scenarios.
- [x] Ensure the fake never imports credentials, starts Codex, opens sockets, or reads a runtime home.
- [x] Make the fake observable by counts and categories rather than prompt or response retention.
- [x] Verify dependency injection prevents accidental use of a real adapter in local tests.

Done when:

- [x] The orchestrator exercises reviewed local terminal categories without network or credential access.

### Step 4 - Implement One Bounded Workflow Slice

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [x] Accept one reviewed diagnostic workflow request.
- [x] Run it through validation, deadline, state transition, fake adapter, and bounded result handling.
- [x] Return only a sanitized operator-facing status and manual next-step category.
- [x] Clean up temporary state on success, failure, cancellation, and test interruption.
- [x] Prevent model output from becoming an executable action.

Done when:

- [x] One local end-to-end workflow is repeatable, bounded, and independent of Codex authentication or transport.

### Step 5 - Add Core Regression Tests

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Test valid and invalid request schemas.
- [x] Test reviewed allowed and forbidden state transitions.
- [x] Test deadline, cancellation, event-count, turn-count, and output-size limits.
- [x] Test cleanup and absence of raw content in errors and test snapshots.
- [x] Test that the local suite opens no listener and invokes no real Codex process.

Done when:

- [x] Build, type-check, lint, and focused tests pass without credentials or network access.

## 09.6 Phase Definition of Done

This phase is done when:

- [x] The local orchestrator package installs and validates deterministically from its accepted lockfile.
- [x] One fake-backed workflow passes end to end.
- [x] Limits and cancellation fail closed.
- [x] No credential, runtime-home, MCP, provider, or deployment access occurs.
- [x] Errors and metadata contain no raw prompt or response content.

### Completion Record — 2026-07-21

The accepted fake-backed package is under
`ansible/ai_ops_runtime/files/orchestrator/`; local validation is recorded in
`../runtime/phase08-orchestrator-local-validation-evidence.md`.

Phase 09 is complete only for the local fake-backed slice. The official adapter
remains disabled. Phase 10 must provide pre-model MCP result redaction and
bounded local tool-loop controls before any later deployment, authentication, or
egress phase is considered.

## 09.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| The fake diverges from supported SDK lifecycle semantics | Base its event contract only on reviewed public SDK types and add real-adapter contract tests later. |
| The Python SDK is beta and may change before 1.0 | Pin `openai-codex==0.144.4` with `openai-codex-cli-bin==0.144.4`, isolate it behind the adapter, lock dependencies, and require contract tests before upgrades. |
| Workflow state grows into an autonomous remediation engine | Keep one diagnostic-only workflow, bounded turns, and untrusted text output. |
| Tests accidentally invoke the real runtime | Require explicit adapter injection and make the fake the only test/default adapter. |
