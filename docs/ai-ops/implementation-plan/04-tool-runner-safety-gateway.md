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

- [ ] The initial diagnostic scripts already exist and run manually.
- [ ] A simple local CLI runner is sufficient for MVP.
- [ ] Tool definitions can live in a reviewed configuration file or equivalent registry.
- [ ] The runner implementation language can be chosen by maintainers, with Python preferred if OpenStack SDK migration is likely.

## 04.5 Ordered Tasks

### Step 1 - Define Tool Registry Contract

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [ ] Define a registry schema containing tool name, description, script target, credential profile, risk level, timeout, output limit, and argument definitions.
- [ ] Define supported argument validation types: required string, safe identifier pattern, allowed host list, optional default, and bounded time window.
- [ ] Register the first tools: project resource summary, server basic info, and server network info.
- [ ] Mark Neutron agent health unavailable or higher-visibility unless the credential exists.
- [ ] Explicitly omit generic shell, SSH, sudo, OpenStack CLI, file, database, and remediation tools.

Done when:

- [ ] The registry describes exactly which diagnostic actions are executable and what inputs each accepts.

### Step 2 - Implement Local Runner CLI

Estimate:

```text
0.75-1 engineer-days
4.5-6 hours
```

Tasks:

- [ ] Implement a CLI entrypoint that accepts a tool name and declared parameters.
- [ ] Load the registry and reject unknown tools.
- [ ] Validate required and optional parameters before execution.
- [ ] Execute scripts with argument arrays, not shell strings.
- [ ] Return a non-zero status for denied, validation-error, unavailable, and execution-error outcomes.

Done when:

- [ ] A maintainer can run an approved tool by name and cannot run an unregistered tool.

### Step 3 - Add Timeout and Output Limits

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [ ] Enforce per-tool timeout from the registry.
- [ ] Kill or stop tool execution cleanly when timeout is reached.
- [ ] Enforce stdout and stderr size limits.
- [ ] Mark result envelopes as truncated when limits are exceeded.
- [ ] Preserve enough error detail to diagnose timeouts and truncation.

Done when:

- [ ] Long-running or noisy tools fail safely with structured timeout or truncation status.

### Step 4 - Add Structured Result Envelopes

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Return tool name, status, sanitized arguments, exit code, stdout, stderr, duration, and truncation flag.
- [ ] Use stable status values for ok, error, denied, validation_error, timeout, unavailable, and truncated cases.
- [ ] Ensure output is machine-readable for later MCP reuse.
- [ ] Add examples of successful, failed, denied, and timed-out results.

Done when:

- [ ] The operator and future AI client can distinguish “diagnostic found nothing” from “diagnostic failed to run.”

### Step 5 - Add Audit Logging

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Log every allowed request with timestamp, tool, sanitized arguments, status, duration, and exit code.
- [ ] Log every denied, unavailable, timeout, and validation-error request.
- [ ] Redact or omit secret-like values from audit entries.
- [ ] Ensure audit logs are written to the assistant workspace and not to committed files.
- [ ] Add rotation or cleanup guidance for lab use.

Done when:

- [ ] A maintainer can answer what the runner attempted, when, with which sanitized inputs, and what happened.

### Step 6 - Add Safety-Focused Tests

Estimate:

```text
0.75-1.25 engineer-days
4.5-7.5 hours
```

Tasks:

- [ ] Test that unknown tools are denied.
- [ ] Test that unsafe parameters are denied before script execution.
- [ ] Test that approved tools use argument-vector execution.
- [ ] Test timeout behavior with a controlled slow tool fixture.
- [ ] Test output truncation with a controlled noisy tool fixture.
- [ ] Test audit events for allowed, denied, validation-error, unavailable, and timeout outcomes.
- [ ] Test that no generic shell/OpenStack/SSH tool appears in the registry.

Done when:

- [ ] The runner’s safety behavior is regression-tested without needing a live OpenStack deployment.

## 04.6 Phase Definition of Done

This phase is done when:

- [ ] The local runner executes only allowlisted diagnostic tools.
- [ ] Unknown and unsafe requests are denied.
- [ ] Tool parameters are validated.
- [ ] Execution uses argument arrays rather than shell strings.
- [ ] Timeouts and output limits are enforced.
- [ ] Structured results are emitted.
- [ ] Audit logs are written for all request outcomes.
- [ ] Safety tests pass.

## 04.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Runner accidentally becomes generic command execution | Keep registry intent-based and test absence of generic command tools. |
| Input validation misses injection patterns | Use strict allowlists and argument-vector execution as a second layer. |
| Audit logs leak sensitive data | Sanitize arguments and scan result/audit output for secret-like fields. |
| Timeout handling leaves orphaned processes | Implement process cleanup and add tests with controlled slow fixtures. |