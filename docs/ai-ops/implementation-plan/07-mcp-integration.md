# 07. MCP Integration

**Status:** Local stdio MCP foundation validated; the runtime client entry is currently disabled. Future integrated AI-OPS work proceeds through the hybrid Codex SDK orchestrator decision in `docs/ai-ops/runtime/phase07-codex-sdk-orchestrator-decision-2026-07-21.md`.

## 07.1 Goal

Expose the already-trusted diagnostic toolbox through MCP so an AI client can discover and call approved read-only tools without gaining arbitrary command execution.

Target outcome:

```text
trusted local runner
  -> local stdio MCP tool/resource/prompt schema
  -> repository-owned AI-OPS orchestrator calls approved capability
  -> same validation/execution/audit path
  -> bounded structured result returned
```

The future orchestrator may use the official Codex SDK/runtime for ChatGPT authentication and provider transport, but that dependency remains outside the MCP execution boundary. Codex must not gain a second or less-restricted path to OpenStack diagnostics.

## 07.2 Estimate

Total estimate:

```text
3-5 engineer-days
18-30 focused hours
```

This is the original estimate for the local MCP integration only. It excludes the hybrid Codex SDK orchestrator, authentication/runtime lifecycle, remote-provider transport, sandboxed deployment, egress validation, and remote acceptance. Those concerns require a separate phased implementation plan.

## 07.3 Scope

Included:

* Build an MCP server wrapper around the existing tool registry and runner.
* Register only approved diagnostic tools.
* Expose read-only resources for AI-OPS runbooks and architecture context.
* Add prompts for repeatable diagnostic workflows.
* Validate MCP uses the same allowlist, input validation, timeouts, output limits, and audit logs.
* Add local stdio-first integration guidance.
* Provide the sole approved model-facing path to the existing runner for the future repository-owned orchestrator.

Excluded:

* Public unauthenticated MCP network exposure.
* Remote multi-user access.
* Remediation tools.
* Generic shell, SSH, sudo, OpenStack CLI, file, or database tools.
* Replacing the local runner safety boundary.
* Implementing the hybrid orchestrator or its Codex SDK/runtime dependency.
* Managing, extracting, or forwarding ChatGPT/Codex credentials.
* Implementing or proxying private provider routes, headers, or stream protocols.
* Provider egress, remote acceptance, or retirement of the historical provider gateway.

## 07.4 Assumptions

- [x] The local runner already works and is trusted.
- [x] The first MCP transport is local/stdin-stdout unless a secure remote design is explicitly approved later.
- [x] The MCP server delegates execution to the runner or shared execution layer rather than reimplementing looser behavior.
- [x] A temporary local stdio client validated discovery, approved calls, rejection behavior, audit correlation, and adapter cleanup on the assistant runtime.

## 07.5 Ordered Tasks

### Step 1 - Choose MCP Server Implementation Style

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [x] Choose implementation language and MCP SDK/runtime compatible with the assistant runtime.
- [x] Decide whether MCP calls invoke the local runner process or share runner library code.
- [x] Keep the runner/registry as the source of truth for tools.
- [x] Document why MCP is an interface layer, not a new safety boundary.

Done when:

- [x] The MCP implementation approach cannot bypass the existing allowlist and validation model.

### Step 2 - Register Initial MCP Tools

Estimate:

```text
0.75-1 engineer-days
4.5-6 hours
```

Tasks:

- [x] Register project resource summary as an MCP tool.
- [x] Register server basic info as an MCP tool with the same server validation as the local runner.
- [x] Register server network info as an MCP tool with the same server validation as the local runner.
- [ ] Register host/log tools only if Phase 06 is complete and the tools are safe locally.
- [x] Add tool descriptions that clearly state read-only behavior and credential class.

Done when:

- [x] An MCP client can discover the approved diagnostic tools and no generic command tool exists.

### Step 3 - Reuse Structured Result and Audit Path

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [x] Return the same result envelope fields through MCP.
- [ ] Preserve timeout, truncation, unavailable, validation-error, and denied statuses.
- [x] Write audit events for MCP-originated tool calls.
- [x] Add client identifier or transport identifier where available.
- [ ] Verify secrets are not written to MCP logs or audit entries.

Done when:

- [ ] MCP calls are indistinguishable from local runner calls in safety and audit behavior.

### Step 4 - Add MCP Resources

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [x] Expose the AI-OPS safety policy as a read-only resource.
- [x] Expose the metadata troubleshooting runbook as a read-only resource.
- [x] Expose a lab architecture summary as a read-only resource.
- [x] Ensure resources are static/read-only and contain no secret material.
- [x] Document how the AI client should use resources before or during diagnostics.

Done when:

- [x] The AI client can retrieve lab-specific context without reading arbitrary files.

### Step 5 - Add MCP Prompts

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [x] Add a metadata diagnosis prompt that calls approved tools in order and forbids remediation.
- [x] Add a server inspection prompt for one server name or ID.
- [x] Add a project summary prompt for high-level inventory questions.
- [x] Mark prompts as diagnostic workflows, not autonomous repair flows.
- [x] Include expected explanation structure: healthy signals, failing signals, likely failure domain, evidence gaps, and manual next steps.

Done when:

- [x] The AI client can offer repeatable OpenStack Lab diagnostic workflows without inventing raw commands.

### Step 6 - Add MCP Integration Tests

Estimate:

```text
0.75-1.25 engineer-days
4.5-7.5 hours
```

Tasks:

- [x] Test MCP tool discovery includes approved tools.
- [x] Test MCP tool discovery excludes generic command tools.
- [x] Test valid tool calls return the same structured envelope as the runner.
- [x] Test invalid parameters are rejected through MCP.
- [x] Test audit logging for MCP calls.
- [x] Test resources and prompts are discoverable and contain no obvious secrets.

Done when:

- [x] MCP integration passes safety and behavior tests without a live remediation capability.

### Step 7 - Document MCP Client Setup and Rollback

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Document how to start the MCP server locally on the assistant runtime.
- [x] Document how an AI client connects to the server.
- [x] Document that remote exposure is not part of this phase.
- [x] Document rollback: stop MCP server, disable client config, retain local runner for manual use.

Done when:

- [x] A maintainer can enable or disable MCP without touching OpenStack Lab state.

## 07.6 Phase Definition of Done

This phase is done when:

- [x] MCP server starts locally.
- [x] MCP exposes only approved diagnostic tools.
- [x] MCP tools reuse the same validation, timeout, output-limit, and audit behavior as the runner.
- [x] MCP resources expose safe lab context.
- [x] MCP prompts encode repeatable diagnostic workflows.
- [x] MCP tests verify no generic command execution capability exists.
- [x] Remote unauthenticated exposure remains out of scope.
- [x] Local stdio MCP remains the sole approved model-facing route to the diagnostic runner.

## 07.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| MCP accidentally bypasses local runner controls | Use the existing registry/execution layer as the only execution path and test equivalence. |
| AI client treats tools as remediation | Tool descriptions and prompts must explicitly state diagnostic-only behavior. |
| MCP resources expose sensitive files | Expose curated resources only; never implement arbitrary file read. |
| Remote MCP exposure creates a new attack surface | Start with local stdio only; require a separate design for authenticated remote access. |
| The orchestrator bypasses MCP and reaches diagnostics directly | Keep MCP/runner as the only approved execution path and test that no generic or alternate diagnostic interface is available. |
| Codex SDK/runtime concerns leak into the MCP safety boundary | Keep authentication, provider transport, SDK lifecycle, and provider failures in the separate orchestrator plan; MCP remains provider-agnostic. |

## 07.8 Successor Architecture Boundary

The local MCP phase is complete and remains an accepted prerequisite. The selected successor is the hybrid Codex SDK orchestrator described in `docs/ai-ops/runtime/phase07-codex-sdk-orchestrator-decision-2026-07-21.md`.

That successor must preserve this phase's contracts:

1. MCP remains local stdio with no network listener.
2. The orchestrator receives only curated resources, prompts, and allowlisted read-only tools through the local MCP boundary.
3. The Codex SDK/runtime cannot select a broader diagnostic interface or bypass runner validation, limits, and audit behavior.
4. Authentication and provider transport remain inside the supported Codex boundary; MCP never receives or handles Codex credentials.
5. Model output remains untrusted and cannot authorize remediation.

The historical custom-provider gateway is not part of this successor path. Its preservation and eventual retirement require a separate ADS and must not be combined with initial orchestrator implementation.

The next planning action is a separate phased implementation plan for the hybrid orchestrator. It must begin with local dependency and integration discovery, use an injected or fake SDK adapter before any authentication or provider traffic, and retain a separate approval gate for deployment and remote acceptance.
