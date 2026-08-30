# 07. MCP Interface

## 07.1 Goal

Expose the already-trusted diagnostic registry through a local or authenticated internal-network MCP interface so an authorized MCP client can discover curated tools, resources, and prompts without gaining a second or broader execution path.

Target outcome:

```text
authorized MCP client over local stdio or approved internal network -> revised MCP schema -> revised runner/registry -> revised audit path -> bounded diagnostic -> advisory explanation
```

## 07.2 Estimate

Total estimate:

```text
3-5 engineer-days
18-30 focused hours
```

## 07.3 Scope

Included:

* Select a supported MCP implementation and local stdio-first transport; retain an explicit extension path for an authenticated internal-network service.
* Mirror approved registry tools and argument schemas.
* Evaluate the prior local stdio MCP server as a path-level reuse candidate; select or reimplement only the parts that match the revised contract and accepted runner.
* Delegate all execution to the accepted revised runner/shared safety layer.
* Expose curated read-only runbook, architecture, and safety resources.
* Add repeatable project, server, metadata, network, and volume diagnostic prompts as appropriate.
* Add discovery, equivalence, redaction, audit, and negative-capability tests.
* Document client setup, lifecycle, and rollback.

Excluded:

* Unauthenticated or publicly reachable network MCP; an authenticated internal-network service is covered only by the separate Option B extension contract.
* Generic command, file, SSH, sudo, OpenStack, database, or remediation primitives.
* Provider-specific private protocols or credential handling.
* Local LLM deployment.
* Any tool not already trusted through the revised local runner.
* Modifying or registering the prior MCP server/client configuration in place.
* Reusing the historical orchestrator-dependent MCP bridge, remote-provider protocol, provider gateway, or egress stack.

## 07.4 Assumptions

- [ ] The revised runner and desired selectively reused or newly implemented tools have passed local and deployed-lab validation.
- [ ] Revised MCP package, process, service, client-registration, resource, prompt, log, and audit identifiers are distinct from the prior MCP integration.
- [ ] External AI-client implementation, registration, and provider/model integration are out of scope for this repository phase.
- [ ] MCP is an interface layer; the revised registry, validation, execution limits, credentials, and audit path remain authoritative.
- [ ] Local stdio remains the baseline mode; Option B adds an authenticated internal-network service only after its separate transport, TLS, authentication, authorization, network, and threat contract is accepted.

## 07.5 Ordered Tasks

### Step 1 - Decide MCP Runtime and Boundary

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [x] Select a maintained MCP SDK/runtime compatible with the assistant host and repository language/tooling constraints.
- [x] Choose local stdio as the baseline transport and confirm no TCP listener is required for that mode.
- [x] If Option B is selected, freeze the separate internal-network transport, bind scope, TLS/authentication, authorization, limits, service identity, and threat controls before implementation.
- [x] Compare the prior local stdio MCP server, resources, policy, and lifecycle behavior with the revised contract; record the selected path-level dependency closure and every required modification before reuse.
- [x] Decide whether revised MCP invokes the revised runner process or calls a shared revised runner library while preserving one validation/execution implementation.
- [x] Define distinct revised process/service identity, environment, working directory, credential access, startup, shutdown, and crash behavior.
- [x] Keep external client implementation, registration, and provider/model expansion outside this repository phase.

Done when:

- [x] The design cannot bypass the revised runner, invoke prior-runtime paths, alter prior client registration, or expose MCP over an unauthenticated network.

### Step 2 - Generate or Register MCP Tools From the Registry

Estimate:

```text
0.75-1 engineer-days
4.5-6 hours
```

Tasks:

- [x] Expose the initial project-resource, server-basic, and server-network tools.
- [x] Expose Phase 06 tools only when their local capability and credentials are enabled and accepted.
- [x] Mirror names, descriptions, required/optional arguments, types, patterns, ranges, and allowlists from the runner registry.
- [x] Include diagnostic-only and credential/risk descriptions without revealing implementation paths or secrets.
- [x] Fail startup or mark a tool unavailable when MCP and registry schemas diverge.

Done when:

- [x] MCP discovery contains exactly the enabled approved diagnostics with equivalent schemas.

### Step 3 - Preserve Result, Limit, and Audit Semantics

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [x] Return the runner’s status, data/stdout, error/stderr, exit code, duration, truncation, timestamp, and correlation ID semantics through MCP.
- [x] Preserve runner timeout and output-size enforcement instead of implementing looser MCP-specific limits.
- [x] Preserve the runner’s fixed `local_cli` audit actor; no client/transport identity is accepted over the initial stdio boundary.
- [x] Redact MCP protocol logs and errors using the same secret rules.
- [x] Ensure MCP cannot request raw audit files, credential files, arbitrary resources, or unbounded diagnostic output.

Done when:

- [x] A local runner call and equivalent MCP call have the same safety, result, and audit behavior in each accepted transport mode.

### Step 4 - Add Curated Read-Only Resources

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [x] Expose a concise lab architecture and service-placement summary.
- [x] Expose the AI-OPS safety, credential-profile, tool-registry, and audit policies.
- [x] Expose reviewed metadata and other relevant troubleshooting runbooks.
- [x] Build an explicit resource allowlist and prohibit arbitrary path or file reads.
- [x] Scan all resources for credentials, private keys, tokens, passwords, and unnecessary sensitive topology.

Done when:

- [x] An authorized MCP request can retrieve useful lab context only from a reviewed static resource set; no external client implementation is required in this phase.

### Step 1–4 Completion Boundary

Steps 1–4 are complete through local implementation, static acceptance, and default-disabled artifact packaging. Steps 5–7 local and fixture evidence is recorded below. The SDK dependency lock and offline wheel remain intentionally absent pending provenance approval; package acquisition, host deployment, client registration, live runner calls, audit inspection, and rollback rehearsal remain separately authorized and are not claimed.

### Step 5 - Add Repeatable Diagnostic Prompts

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [x] Add project summary and single-server inspection prompts.
- [x] Add a metadata diagnosis prompt that sequences available tools and labels missing optional evidence.
- [x] Add network and volume diagnosis prompts only when approved tools provide enough evidence.
- [x] Require prompt output to separate healthy signals, failures, likely domains, uncertainty, and manual next actions.
- [x] Require prompts to refuse mutation and never invent generic commands for AI execution.

Done when:

- [x] Common workflows are discoverable and consistently diagnostic-only.

### Step 6 - Add MCP Safety and Integration Tests

Estimate:

```text
0.75-1.25 engineer-days
4.5-7.5 hours
```

Tasks:

- [x] Test tool discovery exactly matches the enabled registry subset.
- [x] Test generic shell, SSH, sudo, OpenStack passthrough, file, database, package, service-control, and remediation tools are absent.
- [x] Test valid and invalid calls match runner results and validation behavior.
- [x] Test timeout, truncation, unavailable, denied, and audit-correlation behavior.
- [x] Test resources and prompts are allowlisted, discoverable, read-only, and free of secret canaries.
- [x] Test process shutdown and cancellation leave no diagnostic child process running.

Done when:

- [x] MCP passes contract-equivalence and negative-capability tests without requiring mutation access.

### Step 7 - Validate Service Disablement and Rollback

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] For local stdio, document the externally managed client integration without implementing or registering that client here.
- [x] For Option B, validate one low-risk authenticated project summary and one server inspection workflow through fixtures or a separately approved integration environment.
- [x] Verify “fix it” prompts remain advisory and cannot discover a remediation tool.
- [x] Document logs, process health, upgrades, service disablement, transport shutdown, and network-policy rollback.
- [ ] Verify rollback leaves the manual/local runner workflow available unless the safety issue affects the runner itself.

Done when:

- [ ] A maintainer can safely enable, use, inspect, and disable local MCP without changing lab state.

## 07.6 Phase Definition of Done

This phase is done when:

- [ ] The accepted local stdio mode starts without a network listener, or the separately accepted Option B mode binds only to its approved internal interface with authenticated access.
- [ ] MCP exposes exactly the approved enabled diagnostics and equivalent parameter schemas in each accepted mode.
- [x] Every revised tool call traverses the revised safety, credential, timeout, output, redaction, and audit boundary without invoking prior-runtime components.
- [x] Curated resources and prompts contain no arbitrary file access or secrets.
- [x] Tests prove generic and remediation capabilities are absent.
- [x] External client implementation and registration remain outside this repository phase.
- [ ] MCP service/adapter disablement and rollback are independently safe.

## 07.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| MCP duplicates or weakens validation | Generate/mirror schemas from the registry and test call equivalence. |
| Curated resources become arbitrary file access | Use a fixed resource allowlist with content scanning. |
| Internal network exposure expands into public or unauthenticated access | Require a separate Option B contract with fixed bind scope, TLS/authentication, authorization, limits, and listener validation; reject wildcard/public binds. |
| External client or network logs sensitive results | Keep external-client implementation out of scope, minimize/redact server responses and logs, and document the integration owner’s log-handling responsibility. |
| Model integration expands into provider credential handling | Keep provider authentication outside repository diagnostic contracts and separately approved. |
| Revised MCP collides with or modifies prior MCP registration | Use distinct process/client names and configuration locations; test both configurations independently. |
| Selected MCP code imports historical orchestration or unrelated dependencies | Require a path-level dependency review; reject the orchestrator bridge and validate the adapter directly against the revised runner. |

## 07.8 Option B — Authenticated Internal-Network MCP Extension

The baseline local-stdio design remains valid, but the project may separately support an internal MCP service reachable by an independently managed external client. External-client implementation, registration, provider/model integration, and client-side logging are outside this repository phase.

Option B is not public or network-only access. It requires a separate contract for the exact wire transport, internal bind/interface and port, TLS, authentication, principal authorization, request/response bounds, service identity, lifecycle, logging, audit origin, firewall/source allowlist, and rollback. The service must continue to delegate every tool call to the revised runner and must expose only the accepted registry subset and embedded resource catalog.

Authoritative extension design:

- [`ads/07-01-internal-network-mcp-extension-ads.md`](ads/07-01-internal-network-mcp-extension-ads.md)

Option B implementation must execute its own Chunk 0 discovery and decision gate before modifying executable files, deploying a listener, issuing certificates, changing network policy, invoking the runner, inspecting audits, or registering an external client.
