# 04. Tool Runner Safety Gateway

## 04.1 Goal

Add a local tool runner that exposes a fixed diagnostic menu, validates all inputs, executes only allowlisted scripts, returns structured results, and audits every request.

Target outcome:

```text
allowlist config -> validated tool request -> fixed script execution -> structured result -> audit event -> denied unknown/unsafe requests
```

## 04.2 Estimate

Total estimate:

```text
2.5-4 engineer-days
15-24 focused hours
```

## 04.3 Scope

Included:

* Tool registry/allowlist design.
* Local command-line tool runner.
* Input validation.
* Argument-vector script execution.
* Per-tool timeout.
* Output-size limits and truncation metadata.
* Structured result envelopes.
* Audit logging for allowed and denied requests.
* Wrapper tests for safety behavior.

Excluded:

* MCP server.
* Chat UI or bot integration.
* SSH-based host diagnostics unless already implemented safely.
* Automatic remediation.
* Generic command passthrough.

## 04.4 Assumptions

- [x] The initial diagnostic scripts already exist and run manually.
- [x] A simple local CLI runner is sufficient for MVP.
- [x] Tool definitions can live in a reviewed configuration file or equivalent registry.
- [x] The runner implementation language can be chosen by maintainers, with Python preferred if OpenStack SDK migration is likely.

## 04.5 Ordered Tasks

### Step 1 - Define Tool Registry Contract

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [x] Define a registry schema containing tool name, description, script target, credential profile, risk level, timeout, output limit, and argument definitions.
- [x] Define supported argument validation types: required string, safe identifier pattern, allowed host list, optional default, and bounded time window.
- [x] Register the first tools: project resource summary, server basic info, and server network info.
- [x] Mark Neutron agent health unavailable or higher-visibility unless the credential exists.
- [x] Explicitly omit generic shell, SSH, sudo, OpenStack CLI, file, database, and remediation tools.

Done when:

- [x] The registry describes exactly which diagnostic actions are executable and what inputs each accepts.

### Step 2 - Implement Local Runner CLI

Estimate:

```text
0.75-1 engineer-days
4.5-6 hours
```

Tasks:

- [x] Implement a CLI entrypoint that accepts a tool name and declared parameters.
- [x] Load the registry and reject unknown tools.
- [x] Validate required and optional parameters before execution.
- [x] Execute scripts with argument arrays, not shell strings.
- [x] Return a non-zero status for denied, validation-error, unavailable, and execution-error outcomes.

Done when:

- [x] A maintainer can run an approved tool by name and cannot run an unregistered tool.

### Step 3 - Add Timeout and Output Limits

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [x] Enforce per-tool timeout from the registry.
- [x] Kill or stop tool execution cleanly when timeout is reached.
- [x] Enforce stdout and stderr size limits.
- [x] Mark result envelopes as truncated when limits are exceeded.
- [x] Preserve enough error detail to diagnose timeouts and truncation.

Done when:

- [x] Long-running or noisy tools fail safely with structured timeout or truncation status.

### Step 4 - Add Structured Result Envelopes

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Return tool name, status, sanitized arguments, exit code, stdout, stderr, duration, and truncation flag.
- [x] Use stable status values for ok, error, denied, validation_error, timeout, unavailable, and truncated cases.
- [x] Ensure output is machine-readable for later MCP reuse.
- [x] Add examples of successful, failed, denied, and timed-out results.

Done when:

- [x] The operator and future AI client can distinguish “diagnostic found nothing” from “diagnostic failed to run.”

### Step 5 - Add Audit Logging

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [x] Log every allowed request with timestamp, tool, sanitized arguments, status, duration, and exit code.
- [x] Log every denied, unavailable, timeout, and validation-error request.
- [x] Redact or omit secret-like values from audit entries.
- [x] Ensure audit logs are written to the assistant workspace and not to committed files.
- [x] Add rotation or cleanup guidance for lab use.

Done when:

- [x] A maintainer can answer what the runner attempted, when, with which sanitized inputs, and what happened.

### Step 6 - Add Safety-Focused Tests

Estimate:

```text
0.75-1.25 engineer-days
4.5-7.5 hours
```

Tasks:

- [x] Test that unknown tools are denied.
- [x] Test that unsafe parameters are denied before script execution.
- [x] Test that approved tools use argument-vector execution.
- [x] Test timeout behavior with a controlled slow tool fixture.
- [x] Test output truncation with a controlled noisy tool fixture.
- [x] Test audit events for allowed, denied, validation-error, unavailable, and timeout outcomes.
- [x] Test that no generic shell/OpenStack/SSH tool appears in the registry.

Done when:

- [x] The runner’s safety behavior is regression-tested without needing a live OpenStack deployment.

## 04.6 Phase Definition of Done

This phase is done when:

- [x] The local runner executes only allowlisted diagnostic tools.
- [x] Unknown and unsafe requests are denied.
- [x] Tool parameters are validated.
- [x] Execution uses argument arrays rather than shell strings.
- [x] Timeouts and output limits are enforced.
- [x] Structured results are emitted.
- [x] Audit logs are written for all request outcomes.
- [x] Safety tests pass.

### 04.6.1 Validation Evidence and Audit Cleanup Guidance

Evidence for Phase 04 completion:

- Source registry: `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/tool_registry.json`.
- Source runner: `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py`.
- Safety tests: `tests/ai_ops/test_tool_runner.py` (`python3 -m unittest discover -s tests -p 'test_tool_runner.py'`, 18 tests observed passing).
- Runtime installation wiring: `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/scripts.yml`.
- Runtime validation playbook: `ansible/ai_ops_runtime/playbook_validate_phase04_tool_runner_safety_gateway.yml`.
- Runtime evidence: `docs/ai-ops/runtime/phase04-tool-runner-safety-gateway-evidence-2026-07-08.md`.

Result examples are covered by the runtime evidence for `ok`, `denied`, `validation_error`, and `unavailable` outcomes, and by the unit tests for `error`, `timeout`, and `truncated` outcomes.

Audit logs are runtime artifacts under `/opt/openstack-ai-ops/audit/tool-runner.jsonl`; they must stay out of the repository. For lab cleanup, archive only redacted evidence summaries when needed, then rotate or truncate the runtime JSONL audit file manually as the `assistant` runtime owner or through a reviewed maintenance task. Do not commit raw audit logs, credential contents, tokens, passwords, private keys, or raw profile material.

## 04.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Runner accidentally becomes generic command execution | Keep registry intent-based and test absence of generic command tools. |
| Input validation misses injection patterns | Use strict allowlists and argument-vector execution as a second layer. |
| Audit logs leak sensitive data | Sanitize arguments and scan result/audit output for secret-like fields. |
| Timeout handling leaves orphaned processes | Implement process cleanup and add tests with controlled slow fixtures. |