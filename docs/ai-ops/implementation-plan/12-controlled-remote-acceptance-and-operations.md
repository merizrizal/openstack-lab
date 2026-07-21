# 12. Controlled Remote Acceptance and Operations

## 12.1 Goal

Validate exactly one bounded remote diagnostic workflow through the supported Codex SDK/runtime, then establish operational, upgrade, failure, and rollback procedures without inspecting private provider behavior.

Target outcome:

```text
approved preflight
  -> one non-sensitive diagnostic request
  -> Codex-managed authentication and transport
  -> allowlisted local MCP workflow
  -> bounded metadata classification
  -> validation and rollback rechecks
```

## 12.2 Estimate

Total estimate:

```text
1-2 engineer-days
6-12 focused hours
```

## 12.3 Scope

Included:

* Final local preflight and explicit one-request approval.
* One non-sensitive remote acceptance workflow with bounded turns and retries.
* Metadata-only acceptance classification.
* Post-request deployment, egress, process, listener, MCP, and evidence checks.
* Operator runbooks for authentication expiry, SDK/runtime failure, version upgrades, disablement, and rollback.

Excluded:

* Provider response/header inspection or packet capture.
* Private protocol debugging, custom routing, or gateway fallback.
* Raw prompt, response, tool output, SDK event, or Codex log retention.
* Automated remediation or unattended recurring provider requests.
* Historical gateway retirement before acceptance is approved.

## 12.4 Assumptions

- [ ] Phase 11 deployment and synthetic egress validation pass immediately beforehand.
- [ ] Codex login status succeeds without exposing output or credential values.
- [ ] The operator explicitly approves one request and one non-sensitive diagnostic prompt.
- [ ] Failure at the supported SDK/runtime boundary is accepted as a vendor blocker, not a private-protocol investigation trigger.

## 12.5 Ordered Tasks

### Step 1 - Define the Acceptance Procedure

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Specify exact approval, prompt, model, workflow, maximum turns, tool calls, deadline, output handling, and retry bounds.
- [ ] Require permanent deployment and egress validators immediately before and after the request.
- [ ] Define allowed metadata categories and prohibit raw terminal, model, provider, and ledger output.
- [ ] Define immediate stop conditions for drift, evidence failure, unexpected tools, extra requests, or sensitive markers.
- [ ] Define cleanup and rollback for every failure stage.

Done when:

- [ ] The operator can review the entire one-request procedure without accessing protected data.

### Step 2 - Run Final No-Provider Preflight

Estimate:

```text
0.25 engineer-days
1.5 hours
```

Tasks:

- [ ] Validate pinned versions, package integrity, service identity, runtime-home metadata, sandboxing, and no listeners.
- [ ] Re-run fake-adapter and local MCP safety tests.
- [ ] Validate evidence capacity and schema without reading raw records.
- [ ] Validate `assistant` direct-egress denial and orchestrator policy materialization.
- [ ] Stop on any failure or unreviewed drift.

Done when:

- [ ] Every local and synthetic gate passes immediately before remote approval is consumed.

### Step 3 - Execute One Approved Remote Workflow

Estimate:

```text
0.25 engineer-days
1.5 hours
```

Tasks:

- [ ] Obtain fresh explicit approval for exactly one request.
- [ ] Use the reviewed non-sensitive input and fixed bounded workflow.
- [ ] Bound and sanitize advisory model output for the operator while prohibiting raw Codex/model/provider output in logs, evidence, or persistent files; prohibit retries beyond the approved bound.
- [ ] Retain only parsed approved orchestrator metadata categories.
- [ ] Stop after the first terminal result; do not troubleshoot private transport behavior.

Done when:

- [ ] Exactly one approved workflow reaches a bounded terminal category, presents only sanitized advisory output, and retains no protected content.

### Step 4 - Revalidate and Record Sanitized Evidence

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Re-run deployment, egress, process, listener, MCP, and evidence validators.
- [ ] Confirm temporary workspaces and process state are removed.
- [ ] Record only approved versions, categories, counts, and validation outcomes.
- [ ] Classify SDK/runtime failure as a version/update or vendor blocker without private-protocol inspection.
- [ ] Keep the remote path disabled by default until regular-use policy is separately accepted.

Done when:

- [ ] Sanitized acceptance evidence and post-operation validation are complete.

### Step 5 - Complete Operational and Upgrade Runbooks

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Document normal invocation, approval, timeout, cancellation, and disablement procedures.
- [ ] Document login expiry and operator reauthentication without token inspection.
- [ ] Document pinned SDK/runtime upgrade tests and rollback.
- [ ] Document vendor-blocker escalation and the prohibition on private-protocol recovery.
- [ ] Define review and retention rules for orchestrator metadata.

Done when:

- [ ] Operators can use, disable, update, and troubleshoot the supported boundary without bypassing controls.

## 12.6 Phase Definition of Done

This phase is done when:

- [ ] One explicitly approved remote workflow completes or yields a bounded documented vendor blocker.
- [ ] No raw sensitive or provider content is retained.
- [ ] Post-operation safety validators pass.
- [ ] Operational, authentication-expiry, upgrade, disablement, and rollback runbooks exist.
- [ ] No custom-provider gateway fallback is available.

## 12.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Acceptance turns into repeated live debugging | Authorize one request, disable retries, and stop at the SDK/runtime boundary. |
| Raw model or SDK output reaches logs | Suppress output and permit only parsed metadata categories. |
| A version change silently alters behavior | Pin versions and require fake, local MCP, deployment, and one-request reacceptance gates. |
| Successful acceptance is treated as remediation approval | Keep tools read-only and model output advisory with manual next steps. |
