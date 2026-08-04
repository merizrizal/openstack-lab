# 07. MCP Interface

## 07.1 Goal

Expose the already-trusted diagnostic registry through a local MCP interface so an AI client can discover curated tools, resources, and prompts without gaining a second or broader execution path.

Target outcome:

```text
local AI client -> revised MCP schema -> revised runner/registry -> revised audit path -> bounded diagnostic -> advisory explanation
```

## 07.2 Estimate

Total estimate:

```text
3-5 engineer-days
18-30 focused hours
```

## 07.3 Scope

Included:

* Select a supported MCP implementation and local stdio-first transport.
* Mirror approved registry tools and argument schemas.
* Evaluate the prior local stdio MCP server as a path-level reuse candidate; select or reimplement only the parts that match the revised contract and accepted runner.
* Delegate all execution to the accepted revised runner/shared safety layer.
* Expose curated read-only runbook, architecture, and safety resources.
* Add repeatable project, server, metadata, network, and volume diagnostic prompts as appropriate.
* Add discovery, equivalence, redaction, audit, and negative-capability tests.
* Document client setup, lifecycle, and rollback.

Excluded:

* Unauthenticated or publicly reachable network MCP.
* Generic command, file, SSH, sudo, OpenStack, database, or remediation primitives.
* Provider-specific private protocols or credential handling.
* Local LLM deployment.
* Any tool not already trusted through the revised local runner.
* Modifying or registering the prior MCP server/client configuration in place.
* Reusing the historical orchestrator-dependent MCP bridge, remote-provider protocol, provider gateway, or egress stack.

## 07.4 Assumptions

- [ ] The revised runner and desired selectively reused or newly implemented tools have passed local and deployed-lab validation.
- [ ] Revised MCP package, process, service, client-registration, resource, prompt, log, and audit identifiers are distinct from the prior MCP integration.
- [ ] The first selected AI client supports a local stdio MCP process or equivalent non-network integration.
- [ ] MCP is an interface layer; the revised registry, validation, execution limits, credentials, and audit path remain authoritative.
- [ ] Remote MCP would require a separate approved authentication, authorization, network, and threat design.

## 07.5 Ordered Tasks

### Step 1 - Decide MCP Runtime and Boundary

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [ ] Select a maintained MCP SDK/runtime compatible with the assistant host and repository language/tooling constraints.
- [ ] Choose local stdio as the initial transport and confirm no TCP listener is required.
- [ ] Compare the prior local stdio MCP server, resources, policy, and lifecycle behavior with the revised contract; record the selected path-level dependency closure and every required modification before reuse.
- [ ] Decide whether revised MCP invokes the revised runner process or calls a shared revised runner library while preserving one validation/execution implementation.
- [ ] Define distinct revised process identity, environment, working directory, credential access, startup, shutdown, and crash behavior.
- [ ] Record the first supported AI client and explicitly defer provider/model-specific expansion.

Done when:

- [ ] The design cannot bypass the revised runner, invoke prior-runtime paths, alter prior client registration, or expose MCP over an unauthenticated network.

### Step 2 - Generate or Register MCP Tools From the Registry

Estimate:

```text
0.75-1 engineer-days
4.5-6 hours
```

Tasks:

- [ ] Expose the initial project-resource, server-basic, and server-network tools.
- [ ] Expose Phase 06 tools only when their local capability and credentials are enabled and accepted.
- [ ] Mirror names, descriptions, required/optional arguments, types, patterns, ranges, and allowlists from the runner registry.
- [ ] Include diagnostic-only and credential/risk descriptions without revealing implementation paths or secrets.
- [ ] Fail startup or mark a tool unavailable when MCP and registry schemas diverge.

Done when:

- [ ] MCP discovery contains exactly the enabled approved diagnostics with equivalent schemas.

### Step 3 - Preserve Result, Limit, and Audit Semantics

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Return the runner’s status, data/stdout, error/stderr, exit code, duration, truncation, timestamp, and correlation ID semantics through MCP.
- [ ] Preserve runner timeout and output-size enforcement instead of implementing looser MCP-specific limits.
- [ ] Pass a sanitized client/transport identifier into audit events where available.
- [ ] Redact MCP protocol logs and errors using the same secret rules.
- [ ] Ensure MCP cannot request raw audit files, credential files, arbitrary resources, or unbounded diagnostic output.

Done when:

- [ ] A local runner call and equivalent MCP call have the same safety, result, and audit behavior.

### Step 4 - Add Curated Read-Only Resources

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Expose a concise lab architecture and service-placement summary.
- [ ] Expose the AI-OPS safety, credential-profile, tool-registry, and audit policies.
- [ ] Expose reviewed metadata and other relevant troubleshooting runbooks.
- [ ] Build an explicit resource allowlist and prohibit arbitrary path or file reads.
- [ ] Scan all resources for credentials, private keys, tokens, passwords, and unnecessary sensitive topology.

Done when:

- [ ] The AI client can retrieve useful lab context only from a reviewed static resource set.

### Step 5 - Add Repeatable Diagnostic Prompts

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Add project summary and single-server inspection prompts.
- [ ] Add a metadata diagnosis prompt that sequences available tools and labels missing optional evidence.
- [ ] Add network and volume diagnosis prompts only when approved tools provide enough evidence.
- [ ] Require prompt output to separate healthy signals, failures, likely domains, uncertainty, and manual next actions.
- [ ] Require prompts to refuse mutation and never invent generic commands for AI execution.

Done when:

- [ ] Common workflows are discoverable and consistently diagnostic-only.

### Step 6 - Add MCP Safety and Integration Tests

Estimate:

```text
0.75-1.25 engineer-days
4.5-7.5 hours
```

Tasks:

- [ ] Test tool discovery exactly matches the enabled registry subset.
- [ ] Test generic shell, SSH, sudo, OpenStack passthrough, file, database, package, service-control, and remediation tools are absent.
- [ ] Test valid and invalid calls match runner results and validation behavior.
- [ ] Test timeout, truncation, unavailable, denied, and audit-correlation behavior.
- [ ] Test resources and prompts are allowlisted, discoverable, read-only, and free of secret canaries.
- [ ] Test process shutdown and cancellation leave no diagnostic child process running.

Done when:

- [ ] MCP passes contract-equivalence and negative-capability tests without requiring mutation access.

### Step 7 - Validate Client Setup and Rollback

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Configure the selected client to launch the local MCP process without embedding OpenStack secrets in client configuration.
- [ ] Validate one low-risk project summary and one server inspection workflow before enabling higher-risk tools.
- [ ] Verify “fix it” prompts remain advisory and cannot discover a remediation tool.
- [ ] Document logs, process health, upgrades, client disablement, and MCP shutdown.
- [ ] Verify rollback leaves the manual/local runner workflow available unless the safety issue affects the runner itself.

Done when:

- [ ] A maintainer can safely enable, use, inspect, and disable local MCP without changing lab state.

## 07.6 Phase Definition of Done

This phase is done when:

- [ ] Local MCP starts without a public network listener.
- [ ] MCP exposes exactly the approved enabled diagnostics and equivalent parameter schemas.
- [ ] Every revised tool call traverses the revised safety, credential, timeout, output, redaction, and audit boundary without invoking prior-runtime components.
- [ ] Curated resources and prompts contain no arbitrary file access or secrets.
- [ ] Tests prove generic and remediation capabilities are absent.
- [ ] The selected client completes representative advisory-only workflows.
- [ ] MCP can be disabled independently and safely.

## 07.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| MCP duplicates or weakens validation | Generate/mirror schemas from the registry and test call equivalence. |
| Curated resources become arbitrary file access | Use a fixed resource allowlist with content scanning. |
| Remote exposure appears as a convenience change | Enforce stdio/no-listener checks and require separate approval for networking. |
| AI client logs sensitive results | Minimize/redact tool data and document client-log handling. |
| Model integration expands into provider credential handling | Keep provider authentication outside repository diagnostic contracts and separately approved. |
| Revised MCP collides with or modifies prior MCP registration | Use distinct process/client names and configuration locations; test both configurations independently. |
| Selected MCP code imports historical orchestration or unrelated dependencies | Require a path-level dependency review; reject the orchestrator bridge and validate the stdio adapter directly against the revised runner. |
