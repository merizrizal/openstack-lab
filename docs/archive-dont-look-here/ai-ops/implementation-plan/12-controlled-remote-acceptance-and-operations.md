# 12. Controlled Remote Acceptance and Operations

**Status:** Complete. The Phase 12 implementation and one separately approved
acceptance were completed through the successor ADSs
`ads/12-01-phase12-gated-remote-boundary-ads.md` and
`ads/12-02-phase12-one-shot-remote-operation-boundary-ads.md`. See
`../runtime/phase12-one-shot-remote-acceptance-evidence-2026-07-31.md` for the
metadata-only outcome. Any future remote operation requires a new, independent
approval.

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
* One non-sensitive remote acceptance workflow with bounded turns and zero automatic retries.
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

- [x] Phase 11 deployment and synthetic egress validation passed immediately beforehand.
- [x] Codex authentication was established without exposing output or credential values.
- [x] The operator explicitly approved one request and one non-sensitive diagnostic prompt.
- [x] Failure at the supported SDK/runtime boundary remains a vendor blocker, not a private-protocol investigation trigger.

## 12.5 Ordered Tasks

### Step 1 - Define the Acceptance Procedure

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Specified exact approval, prompt, model, workflow, maximum turns, tool calls, deadline, output handling, and retry bounds.
- [x] Required permanent deployment and egress validators immediately before and after the request.
- [x] Defined allowed metadata categories and prohibited raw terminal, model, provider, and ledger output.
- [x] Defined immediate stop conditions for drift, evidence failure, unexpected tools, extra requests, or sensitive markers.
- [x] Defined cleanup and rollback for every failure stage.

Done when:

- [x] The operator can review the entire one-request procedure without accessing protected data.

### Step 2 - Run Final No-Provider Preflight

Estimate:

```text
0.25 engineer-days
1.5 hours
```

Tasks:

- [x] Validated pinned versions, package integrity, service identity, runtime-home metadata, sandboxing, and no listeners.
- [x] Re-ran fake-adapter and local MCP safety tests.
- [x] Validated evidence capacity and schema without reading raw records.
- [x] Validated `assistant` direct-egress denial and orchestrator policy materialization.
- [x] Stopped on any failure or unreviewed drift.

Done when:

- [x] Every local and synthetic gate passed immediately before remote approval was consumed.

### Step 3 - Execute One Approved Remote Workflow

Estimate:

```text
0.25 engineer-days
1.5 hours
```

Tasks:

- [x] Obtained fresh explicit approval for exactly one request.
- [x] Used the reviewed non-sensitive input and fixed bounded workflow.
- [x] Bounded and sanitized advisory model output for the operator while prohibiting raw Codex/model/provider output in logs, evidence, or persistent files; prohibited retries beyond the approved bound.
- [x] Retained only parsed approved orchestrator metadata categories.
- [x] Stopped after the first terminal result without troubleshooting private transport behavior.

Done when:

- [x] Exactly one approved workflow reached a bounded terminal category, presented only sanitized advisory output, and retained no protected content.

### Step 4 - Revalidate and Record Sanitized Evidence

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Re-ran deployment, egress, process, listener, MCP, and evidence validators.
- [x] Confirmed temporary workspaces and process state were removed.
- [x] Recorded only approved versions, categories, counts, and validation outcomes.
- [x] Kept SDK/runtime failure classification bounded to version/update or vendor blocker without private-protocol inspection.
- [x] Kept the remote path disabled by default pending any separately accepted regular-use policy.

Done when:

- [x] Sanitized acceptance evidence and post-operation validation are complete.

### Step 5 - Complete Operational and Upgrade Runbooks

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Documented normal invocation, approval, timeout, cancellation, and disablement procedures.
- [x] Documented login expiry and operator reauthentication without token inspection.
- [x] Documented pinned SDK/runtime upgrade tests and rollback.
- [x] Documented vendor-blocker escalation and the prohibition on private-protocol recovery.
- [x] Defined review and retention rules for orchestrator metadata.

Done when:

- [x] Operators can use, disable, update, and troubleshoot the supported boundary without bypassing controls.

## 12.6 Phase Definition of Done

This phase is done when:

- [x] One explicitly approved remote workflow completed with a bounded terminal category.
- [x] No raw sensitive or provider content is retained.
- [x] Post-operation safety validators passed.
- [x] Operational, authentication-expiry, upgrade, disablement, and rollback runbooks exist.
- [x] No custom-provider gateway fallback is available.

## 12.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Acceptance turns into repeated live debugging | Authorize one request, disable retries, and stop at the SDK/runtime boundary. |
| Raw model or SDK output reaches logs | Suppress output and permit only parsed metadata categories. |
| A version change silently alters behavior | Pin versions and require fake, local MCP, deployment, and one-request reacceptance gates. |
| Successful acceptance is treated as remediation approval | Keep tools read-only and model output advisory with manual next steps. |
