# Phase 07 Codex SDK Orchestrator Decision

**Date:** 2026-07-21
**Status:** Selected architecture; design and implementation not yet approved
**Supersedes for future remote integration:** the Codex custom-provider gateway recovery path in `07-03-openai-remote-provider-boundary-ads-revised.md` and `codex-custom-provider-profile-contract.md`

## Purpose

Adopt a repository-owned AI-OPS orchestrator while using the official Codex SDK/runtime as the supported ChatGPT authentication and provider-transport boundary. This decision ends attempts to proxy, infer, or reproduce Codex's private ChatGPT provider protocol.

The existing local read-only tools, tool-runner safety gateway, stdio MCP boundary, credential controls, and validated direct-`assistant` egress denial remain prerequisites.

## Decision

The project will build a hybrid purpose-built orchestrator:

```text
operator
  -> repository-owned AI-OPS orchestrator
       -> validate and redact diagnostic context
       -> invoke only approved read-only MCP/tool capabilities
       -> enforce workflow, timeout, cancellation, and evidence policy
       -> official Codex SDK
            -> local Codex runtime
            -> Codex-managed ChatGPT sign-in and provider transport
```

This is not a custom HTTP provider client. The Codex SDK/runtime remains a vendor-managed dependency and owns the private provider protocol.

## Responsibility Boundary

### Repository-owned orchestrator

The orchestrator owns:

- accepted workflow and input schemas;
- fail-closed redaction before model submission;
- allowlisted read-only tool exposure and tool-result bounds;
- orchestration state, maximum turns, timeouts, and cancellation policy;
- process identity, filesystem access, and cleanup;
- metadata-only operational evidence;
- suppression of raw prompts, responses, credentials, and tool output from logs;
- explicit operator approval gates for initial remote acceptance.

### Codex SDK/runtime

The supported Codex dependency owns:

- ChatGPT sign-in and session refresh;
- credential storage and use inside its supported runtime;
- provider route, headers, response framing, and compatibility;
- vendor protocol changes between supported versions.

The project accepts these functions as opaque. It will pin and validate a supported SDK/runtime version but will not reverse-engineer or patch its private provider protocol.

## Authentication Contract

A ChatGPT subscription is used only through the supported Codex authentication flow.

- The operator authenticates Codex interactively in a dedicated runtime home.
- The orchestrator and repository automation never read, parse, copy, print, export, or directly use `auth.json`, access tokens, refresh tokens, account identifiers, or device codes.
- No credential value enters Git, Ansible inventory, process arguments, environment variables, evidence, logs, tests, or handoff documents.
- Codex is responsible for credential caching and refresh.
- Authentication expiry is a bounded operator-action failure, not a reason to inspect or extract tokens.
- API-key fallback is not part of this design.

The phrase “use the Codex auth token” means allowing the official Codex SDK/runtime to use its own managed session. It never means giving token material to repository code.

## Runtime and Egress Contract

The implementation ADS must define a dedicated sandboxed orchestrator service identity and runtime home. The final identity name is not selected by this decision record.

Required properties:

- `assistant` retains deny-by-default direct public-provider egress;
- only the reviewed orchestrator/Codex process boundary receives the minimum outbound DNS and HTTPS capability required by the supported runtime;
- no generic proxy, caller-selected endpoint, alternate transport, or unrestricted shell becomes an AI-facing capability;
- the service receives only the filesystem paths and local IPC needed for its workflow;
- Codex SDK/runtime retries and concurrency are disabled or bounded through supported public configuration;
- version changes require local contract tests before deployment;
- remote acceptance remains a separately approved one-request operation.

Because Codex controls provider transport, the project must not claim application-layer fixation of private provider host, route, or response media type unless the supported SDK publicly guarantees it. Egress claims must match what is actually enforceable.

## Tool and Data Boundary

- Existing read-only diagnostic tools and the tool-runner safety gateway remain authoritative.
- Local MCP remains stdio unless separately redesigned.
- No generic shell, SSH, OpenStack CLI, database access, file mutation, package installation, service restart, or remediation tool is exposed to the model.
- Diagnostic context is structurally validated, bounded, redacted, and leak-scanned before it reaches Codex.
- Tool results are separately bounded and redacted before model submission.
- Model output is treated as untrusted data and cannot directly authorize or execute remediation.

## Evidence Contract

The new orchestrator requires a separate metadata schema. It must not reuse provider-gateway outcomes in a way that implies gateway transport.

Allowed evidence should be limited to reviewed categories such as:

- workflow identifier and timestamps;
- local validation/redaction classification;
- bounded lifecycle state;
- tool name from an explicit allowlist and result category;
- Codex invocation exit category;
- timeout/cancellation category.

Prompts, responses, tool output, headers, provider routes, credentials, account data, raw exceptions, and raw Codex logs are prohibited.

Existing provider-gateway schema 1/schema 2 ledger records remain historical and must not be rewritten, relabelled, truncated, or used as orchestrator acceptance evidence.

## Existing Gateway Disposition

The deployed provider gateway is not part of the selected remote request path.

Until a separate retirement ADS is approved:

1. keep remote use disabled;
2. make no further provider requests through it;
3. preserve its ledger and historical evidence;
4. do not remove egress controls that protect `assistant`;
5. do not silently reuse its service identity or metadata schema for the orchestrator.

Retirement, package removal, service disablement, firewall changes, or ledger preservation actions require an explicit implementation and rollback plan.

## Failure and Stop Rules

| Failure | Required action |
| --- | --- |
| Supported Codex SDK/runtime cannot authenticate | Return a bounded operator-action status; do not inspect credentials. |
| SDK/runtime provider operation fails | Record only a bounded exit category; pin/update through a reviewed dependency change or classify as a vendor blocker. |
| A feature requires private protocol inspection | Stop; the feature is outside this architecture. |
| Redaction or tool-policy validation fails | Fail before Codex invocation. |
| Output, evidence, or logs could retain sensitive content | Stop and revise the local boundary before deployment. |
| Required egress cannot be bounded honestly | Stop and revise the deployment design. |

No failure authorizes restoration of custom-provider gateway recovery.

## Consequences

### Benefits

- Removes custom translation of the private ChatGPT provider protocol.
- Makes workflow, tool policy, redaction, and evidence repository-owned and testable.
- Supports the existing ChatGPT subscription without extracting credentials.
- Creates a clear vendor-blocker boundary and prevents repeated protocol-guessing loops.

### Costs and accepted uncertainty

- The Codex SDK includes or depends on the local Codex runtime; it does not remove that dependency.
- Authentication and provider transport remain opaque and version-sensitive.
- Transport-level host, route, header, status, and media-type evidence may be unavailable.
- A dedicated service identity, runtime-home lifecycle, egress policy, SDK version policy, and operator login runbook still require design.

## Required Next Documents

Before implementation:

1. Create an ADS for the minimal hybrid orchestrator vertical slice.
2. Create a phased implementation plan covering local no-provider tests, sandboxed deployment, authentication runbook, bounded egress validation, and separately approved remote acceptance.
3. Create a retirement ADS for the old provider gateway only after the orchestrator path is locally accepted.

The first implementation slice must be local-only and must use a fake SDK adapter or injected process seam. It must not authenticate, contact a provider, change egress, or access the existing Codex runtime home.

## Public Documentation Basis

- Official Codex SDK documentation describes `@openai/codex-sdk` as a TypeScript library for programmatically controlling local Codex agents and identifies the Codex CLI as a runtime dependency.
- Official Codex authentication documentation supports ChatGPT sign-in and states that Codex caches and refreshes its credentials.

These public contracts support delegating authentication and transport to Codex. They do not authorize extracting its token or treating the SDK as a fully independent provider client.
