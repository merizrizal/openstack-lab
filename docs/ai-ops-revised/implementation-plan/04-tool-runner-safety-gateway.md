# 04. Tool Runner Safety Gateway

## 04.1 Goal

Put one deny-by-default execution boundary in front of every diagnostic so only named implementations with validated inputs, bounded execution, structured results, and complete sanitized auditing can run.

Target outcome:

```text
registered request -> schema validation -> fixed argv execution -> timeout/output enforcement -> structured result -> audit event
```

## 04.2 Estimate

Total estimate:

```text
3-5 engineer-days
18-30 focused hours
```

## 04.3 Scope

Included:

* Tool-registry contract and schema validation.
* Local command-line runner for named diagnostics.
* Strict request validation and fixed argument-vector execution.
* Per-tool timeouts, process cleanup, output limits, and truncation metadata.
* Stable result and audit contracts.
* Secret redaction and safety-focused unit/integration tests.

Excluded:

* MCP server or remote network API.
* Generic shell, SSH, sudo, OpenStack CLI, file, database, or remediation tools.
* Host diagnostics not yet approved in Phase 06.
* Chat UI or model-provider integration.

## 04.4 Assumptions

- [ ] Initial revised tools already pass manual safety and behavior validation.
- [ ] Any selected or newly implemented runner and registry use revised identifiers and cannot load prior runtime paths, profiles, audit locations, or service configuration.
- [ ] Prior runner and registry sources remain unchanged; selected runner behavior is adapted only in the revised implementation for documented requirements.
- [ ] A local CLI is sufficient for the first automated execution workflow.
- [ ] The revised registry is the single source of truth for revised public tool capabilities.
- [ ] The runner can use the project’s existing Python testing and linting conventions where practical.

## 04.5 Ordered Tasks

### Step 1 - Define and Validate the Tool Registry

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Compare the prior runner candidate with the revised PRD, select its required dependency closure, and derive a minimal revised registry containing only accepted tools.
- [x] Define required fields for name, description, revised implementation target, revised credential profile, risk class, timeout, output limit, and mutation guarantee.
- [x] Define parameter constraints for required/optional values, types, patterns, ranges, bounded time windows, and exact allowlists.
- [x] Register only project resource summary, server basic info, and server network info initially.
- [x] Resolve implementation targets only from the trusted revised deployment root rather than user-controlled or prior-runtime paths.
- [x] Reject malformed registries, duplicate names, unknown schema fields, unsafe targets, and missing safety metadata at startup.

Done when:

- [x] The registry describes exactly what may execute and fails closed when its configuration is invalid.

### Step 2 - Implement Request Parsing and Denial Behavior

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [x] Accept a named tool and declared parameters through a stable local interface.
- [x] Reject unknown tools, undeclared parameters, missing required parameters, wrong types, and invalid values before execution.
- [x] Use stable result statuses: `ok`, `error`, `denied`, `timeout`, `validation_error`, and `unavailable`.
- [x] Ensure denial errors do not reveal internal paths, credentials, or sensitive registry details.
- [x] Return non-success process status for denied, invalid, unavailable, timed-out, and failed requests.

Done when:

- [x] An operator can request a registered diagnostic by name and cannot reach any unregistered behavior.

### Step 3 - Implement Fixed, Shell-Free Execution

Estimate:

```text
0.5-1 engineer-days
3-6 hours
```

Tasks:

- [x] Build the child-process argument vector solely from trusted implementation metadata and validated parameter values.
- [x] Disable shell-string execution and reject configurations that require it.
- [x] Set an explicit minimal environment and selected revised credential profile per tool.
- [x] Use a controlled revised working directory and prohibit user-selected, historical-runtime, executable, or file paths.
- [x] Prevent inherited admin credentials or unrelated environment secrets from reaching child processes.

Done when:

- [x] Tests and code review prove requests cannot become arbitrary shell, OpenStack, SSH, or file commands.

### Step 4 - Enforce Time, Process, and Output Bounds

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [x] Enforce registry-defined per-tool timeouts.
- [x] Terminate the complete child process group on timeout and verify no orphan remains.
- [x] Enforce separate or combined stdout/stderr byte limits.
- [x] Mark truncation explicitly while retaining enough context for diagnosis.
- [ ] Handle unavailable endpoints, interrupted calls, and decoder errors as structured failures without unsafe fallback.

Done when:

- [x] Slow or noisy diagnostics end predictably with correct timeout or truncation metadata.

### Step 5 - Implement the Result Envelope

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Return tool name, status, sanitized arguments/target, exit code when applicable, stdout or data, stderr or error, duration, truncation flag, timestamp, and correlation ID.
- [ ] Define deterministic serialization and schema-version behavior.
- [ ] Distinguish successful empty findings from failed execution.
- [ ] Redact secret-like values from errors and output before returning the envelope.
- [ ] Add reviewed examples for every status without real topology secrets or credentials.

Done when:

- [ ] Human and machine consumers can reliably interpret all runner outcomes.

### Step 6 - Implement Complete Audit Events

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Record timestamp, actor/client identifier when available, event type, requested tool, sanitized arguments, status, duration, correlation ID, and denial/failure reason.
- [ ] Audit allowed, denied, validation-error, unavailable, failed, timed-out, and truncated calls.
- [ ] Avoid recording credential contents, tokens, passwords, private keys, raw secret-bearing configs, or unnecessary full tool output.
- [ ] Use restrictive audit-file ownership and permissions.
- [ ] Define lab-appropriate rotation, retention, integrity review, and cleanup procedures.

Done when:

- [ ] A maintainer can reconstruct what was requested and what happened without exposing secrets.

### Step 7 - Add Safety Regression Tests

Estimate:

```text
0.75-1.25 engineer-days
4.5-7.5 hours
```

Tasks:

- [ ] Test unknown tools and forbidden generic tool names are denied.
- [ ] Test invalid parameters are denied before implementation execution.
- [ ] Test argument-vector execution and minimal environment behavior.
- [ ] Test timeout cleanup and output truncation with controlled fixtures.
- [ ] Test each result status and audit-event class.
- [ ] Test registry corruption, unsafe implementation targets, prior-runtime paths/profile names, and unavailable revised credential profiles fail closed.
- [ ] Test secrets placed in controlled fixture output or arguments are redacted from results and audit events.

Done when:

- [ ] Automated tests cover the complete gateway contract without requiring a live OpenStack deployment.

## 04.6 Phase Definition of Done

This phase is done when:

- [ ] Only registry-approved tools can execute.
- [ ] All parameters are validated before execution.
- [ ] Child processes use fixed argument vectors, minimal environments, and controlled paths.
- [ ] Timeouts, process cleanup, and output limits are enforced.
- [ ] Structured results cover all required statuses.
- [ ] Every allowed and denied outcome is audited without secrets.
- [ ] Safety regression tests pass and no generic execution entry exists.

## 04.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Registry becomes a disguised command catalog | Restrict schema to reviewed implementations and the trusted revised deployment root. |
| Revised runner silently executes prior-runtime tools or profiles | Give all roots and profiles distinct identifiers and add negative tests for prior-runtime references. |
| Selected runner code imports unwanted historical behavior | Review dependency closure, derive a minimal registry, and map every reused behavior to a revised requirement and test. |
| Validation misses command injection | Combine strict allowlists with shell-free argument-vector execution. |
| Child processes inherit privileged environment | Build an explicit minimal environment and select one declared credential profile. |
| Timeout leaves orphan processes | Manage process groups and test cleanup with a controlled slow fixture. |
| Audit or result data leaks secrets | Apply shared redaction, minimize recorded fields, and test with secret canaries. |
| MCP later reimplements execution | Make the runner/registry the only accepted execution contract. |
