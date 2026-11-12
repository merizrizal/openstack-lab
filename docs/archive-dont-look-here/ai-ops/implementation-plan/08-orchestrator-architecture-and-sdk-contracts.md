# 08. Orchestrator Architecture and SDK Contracts

## 08.1 Goal

Turn the selected hybrid Codex SDK orchestrator decision into an implementation-ready architecture with supported dependency, authentication, process, egress, MCP, evidence, and failure contracts.

Target outcome:

```text
public Codex SDK/runtime contract
  -> reviewed orchestrator ADS and threat model
  -> pinned dependency and test-seam decisions
  -> implementation may begin without private-protocol assumptions
```

## 08.2 Estimate

Total estimate:

```text
1-1.5 engineer-days
6-9 focused hours
```

## 08.3 Scope

Included:

* Confirm the supported Codex SDK and local Codex runtime relationship.
* Define repository-owned versus vendor-owned responsibilities.
* Design dedicated process identity, runtime home, filesystem, MCP, egress, and evidence boundaries.
* Define a fake/injected Codex adapter for all initial tests.
* Define dependency pinning, upgrade, rollback, and vendor-blocker policies.

Excluded:

* Orchestrator implementation beyond the accepted fake-first local vertical slice.
* Codex login, credential access, or provider traffic.
* Deployment, firewall, or service changes.
* Custom provider routes, headers, response parsing, or gateway recovery.
* Historical provider-gateway retirement.

## 08.4 Assumptions

- [ ] The official `openai-codex` Python SDK remains a supported beta library for controlling its pinned local Codex runtime.
- [ ] ChatGPT subscription authentication remains available through the supported Codex login flow.
- [ ] The existing local stdio MCP boundary is the sole model-facing route to diagnostics.
- [ ] The existing `assistant` direct-public-egress denial remains in force.

## 08.5 Ordered Tasks

### Step 1 - Confirm Supported SDK and Runtime Contracts

Estimate:

```text
0.25 engineer-days
1.5 hours
```

Tasks:

- [x] Record the reviewed public Codex SDK installation, runtime dependency, invocation, cancellation, event, configuration, and error contracts.
- [x] Confirm the supported Python, `openai-codex`, and pinned `openai-codex-cli-bin` versions without installing or invoking them.
- [x] Identify publicly supported controls for retries, concurrency, working directory, sandboxing, MCP configuration, and output events.
- [x] Mark unsupported or undocumented controls as blockers rather than inferred behavior.
- [x] Confirm repository code will never read or directly use Codex credential material.

Done when:

- [x] Every planned SDK interaction is grounded in a public supported contract or explicitly deferred.

### Step 2 - Produce the Hybrid Orchestrator ADS

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Define orchestrator input, workflow-state, Codex-adapter, MCP, output, and evidence contracts.
- [x] Define the dedicated runtime identity and runtime-home ownership model conceptually.
- [x] Define fail-closed boundaries for redaction, tool selection, turn limits, cancellation, authentication expiry, SDK failure, and evidence failure.
- [x] Define the no-private-protocol and vendor-blocker stop rules.
- [x] Include a compile-safe thin-vertical-slice ladder beginning with a fake Codex adapter.

Done when:

- [x] An approved ADS can guide implementation without relying on credentials, provider traffic, or hidden session knowledge.

### Step 3 - Define Dependency and Supply-Chain Policy

Estimate:

```text
0.25 engineer-days
1.5 hours
```

Tasks:

- [x] Pin `openai-codex==0.144.4`, its exact `openai-codex-cli-bin==0.144.4` runtime dependency, the supported Python runtime policy, and deterministic package-manager/lockfile policy.
- [x] Require a lockfile and deterministic install path.
- [x] Define package provenance, integrity, vulnerability-review, and upgrade-review checks.
- [x] Define rollback to the previously validated dependency set.
- [x] Require local contract tests before every SDK/runtime version change.

Done when:

- [x] Dependency installation and upgrades have deterministic review and rollback rules.

### Step 4 - Define Validation and Threat-Model Matrix

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Map trust boundaries among operator, orchestrator, Codex SDK/runtime, local MCP, runner, credentials, filesystem, network, and evidence.
- [x] Define tests proving no token access, no generic tool path, no MCP listener, no private-protocol handling, and no provider call in local phases.
- [x] Define synthetic failure tests for cancellation, timeout, malformed events, excessive turns, denied tools, and evidence failure.
- [x] Define explicit approval gates for deployment, login, synthetic egress validation, and one remote request.

Done when:

- [x] Each identified threat has a prevention control and a verifiable acceptance test.

## 08.6 Phase Definition of Done

This phase is done when:

- [x] The hybrid orchestrator ADS is approved.
- [x] SDK/runtime interactions are grounded in public contracts.
- [x] Dependency pinning and rollback rules are documented.
- [x] Authentication values remain entirely outside repository code.
- [x] The local-only validation matrix and remote approval gates are explicit.

### Completion Record — 2026-07-21

The approved ADS is `ads/08-00-orchestrator-architecture-and-sdk-contracts-ads.md`.
Its accepted fake-first local vertical slice is implemented under
`ansible/ai_ops_runtime/files/orchestrator/` and accepted by
`../runtime/phase08-orchestrator-local-validation-evidence.md`.

This completion is local-only. `OfficialCodexAdapter` remains disabled. MCP
pre-model result redaction, the dedicated deployment identity and opaque
runtime-home controls, supported operator authentication, bounded egress, and
separately approved remote acceptance remain mandatory gates for later phases.

## 08.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| The SDK is mistaken for an independent provider client | Record and test its local Codex runtime dependency explicitly. |
| The design reintroduces private-protocol assumptions | Treat undocumented provider behavior as vendor-owned and stop on any requirement to inspect it. |
| Credential handling is accidentally designed into repository code | Require opaque Codex-managed login and prohibit token/file access in contracts and tests. |
| Phase boundaries become another broad recovery effort | Require fake-first vertical slices and explicit stop conditions in the ADS. |
