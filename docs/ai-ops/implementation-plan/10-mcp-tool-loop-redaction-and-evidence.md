# 10. MCP Tool Loop, Redaction, and Evidence

## 10.1 Goal

Connect the local orchestrator to the validated stdio MCP boundary, enforce redaction and bounded tool-loop policy, and produce a new metadata-only evidence contract without invoking a real Codex provider.

Target outcome:

```text
synthetic diagnostic request
  -> validate and redact
  -> fake Codex lifecycle requests one allowlisted MCP capability
  -> runner-enforced read-only result
  -> bounded redaction and metadata evidence
  -> no provider traffic
```

## 10.2 Estimate

Total estimate:

```text
1.5-2.5 engineer-days
9-15 focused hours
```

## 10.3 Scope

Included:

* Local stdio MCP lifecycle controlled by the orchestrator.
* Curated resource, prompt, and tool allowlists.
* Input and tool-result validation, redaction, leak scanning, and size limits.
* Maximum turns, tool calls, concurrency, and cancellation behavior.
* A separate orchestrator metadata schema and parser.
* Fake-Codex end-to-end integration tests against the existing MCP adapter.

Excluded:

* Real Codex authentication or provider traffic.
* Remote MCP transport or network listener.
* Generic shell, SSH, OpenStack CLI, filesystem, database, or remediation tools.
* Reuse or migration of provider-gateway evidence schemas.
* Deployed service or firewall changes.

## 10.4 Assumptions

- [ ] Phase 09 core contracts and fake adapter pass.
- [ ] The existing MCP deployment and runner remain the authoritative diagnostic execution boundary.
- [ ] Existing MCP validation can run with synthetic identifiers and sanitized results.

## 10.5 Ordered Tasks

### Step 1 - Add the Local MCP Client Boundary

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Launch only the reviewed stdio MCP adapter with fixed executable and arguments.
- [ ] Validate negotiated capabilities and exact allowed tool, resource, and prompt names.
- [ ] Reject capability drift before a workflow begins.
- [ ] Tie adapter lifetime to one orchestrator workflow and prove cleanup after disconnect or cancellation.
- [ ] Assert that no MCP network listener is created.

Done when:

- [ ] The orchestrator can discover the exact reviewed local MCP surface and shut it down deterministically.

### Step 2 - Enforce Input and Tool-Result Redaction

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Reuse or adapt the existing fail-closed redaction rules through a reviewed language boundary.
- [ ] Validate and redact operator context before it reaches the Codex adapter.
- [ ] Independently validate, bound, redact, and leak-scan every MCP result before model submission.
- [ ] Reject binary, malformed, ambiguous, oversized, or secret-like content.
- [ ] Ensure errors never contain rejected raw values.

Done when:

- [ ] Synthetic protected markers cannot reach the fake Codex adapter, returned result, evidence, or logs.

### Step 3 - Implement the Bounded Tool Loop

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Permit only reviewed diagnostic workflows and MCP capabilities.
- [ ] Enforce maximum turns, tool calls, concurrency, per-call timeout, workflow deadline, and cumulative content bounds.
- [ ] Reject duplicate, unknown, malformed, or out-of-order tool requests.
- [ ] Preserve runner denial, validation, timeout, truncation, unavailable, and error categories.
- [ ] Treat all model text as untrusted and require manual next steps.

Done when:

- [ ] A fake model cannot escape the allowlist, exceed bounds, or convert text into remediation.

### Step 4 - Add Orchestrator Metadata Evidence

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Define a new versioned metadata allowlist specific to orchestrator lifecycle and local tool categories.
- [ ] Exclude prompts, model responses, tool output, headers, routes, credentials, account data, raw SDK events, and exception text.
- [ ] Add duplicate-key, exact-field, type, size, and lifecycle-transition validation.
- [ ] Fail closed if evidence cannot be safely written or validated.
- [ ] Keep historical provider-gateway ledgers separate and untouched.

Done when:

- [ ] Evidence records only approved bounded metadata and rejects any extra field or sensitive marker.

### Step 5 - Run Local End-to-End Safety Validation

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Run one synthetic fake-Codex workflow through the real local MCP adapter and runner.
- [ ] Verify approved calls, denied generic calls, redaction, structured statuses, audit correlation, and evidence categories.
- [ ] Verify adapter/process cleanup and no listener delta.
- [ ] Prove no Codex runtime, credential path, DNS lookup, or provider socket is accessed.
- [ ] Add regression coverage to the documented validation sequence.

Done when:

- [ ] The complete local workflow passes with fake Codex, real MCP/runner controls, and zero provider access.

## 10.6 Phase Definition of Done

This phase is done when:

- [ ] The orchestrator uses only the reviewed local stdio MCP surface.
- [ ] Input and tool-result redaction fail closed.
- [ ] Tool-loop bounds and cancellation are enforced.
- [ ] The new evidence schema retains metadata only.
- [ ] Local end-to-end validation proves no provider or credential access.

## 10.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| The orchestrator creates a second tool execution path | Require all model-facing diagnostic calls to pass through local MCP and the existing runner. |
| Cross-language redaction behavior drifts | Use shared fixtures and parity tests for all protected-marker classes. |
| Tool output leaks through errors or evidence | Validate and scan every boundary; store categories rather than raw content. |
| A model loops over safe tools until bounds are exhausted | Enforce cumulative turn, call, time, and content limits. |
