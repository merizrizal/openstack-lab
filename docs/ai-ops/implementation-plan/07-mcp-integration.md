# 07. MCP Integration

## 07.1 Goal

Expose the already-trusted diagnostic toolbox through MCP so an AI client can discover and call approved read-only tools without gaining arbitrary command execution.

Target outcome:

```text
trusted local runner -> MCP tool schema -> AI client calls approved tool -> same validation/execution/audit path -> structured result returned
```

## 07.2 Estimate

Total estimate:

```text
3-5 engineer-days
18-30 focused hours
```

## 07.3 Scope

Included:

* Build an MCP server wrapper around the existing tool registry and runner.
* Register only approved diagnostic tools.
* Expose read-only resources for AI-OPS runbooks and architecture context.
* Add prompts for repeatable diagnostic workflows.
* Validate MCP uses the same allowlist, input validation, timeouts, output limits, and audit logs.
* Add local stdio-first integration guidance.

Excluded:

* Public unauthenticated MCP network exposure.
* Remote multi-user access.
* Remediation tools.
* Generic shell, SSH, sudo, OpenStack CLI, file, or database tools.
* Replacing the local runner safety boundary.

## 07.4 Assumptions

- [ ] The local runner already works and is trusted.
- [ ] The first MCP transport is local/stdin-stdout unless a secure remote design is explicitly approved later.
- [ ] The MCP server delegates execution to the runner or shared execution layer rather than reimplementing looser behavior.
- [ ] The initial AI client can connect to a local MCP server on the assistant runtime.

## 07.5 Ordered Tasks

### Step 1 - Choose MCP Server Implementation Style

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [ ] Choose implementation language and MCP SDK/runtime compatible with the assistant runtime.
- [ ] Decide whether MCP calls invoke the local runner process or share runner library code.
- [ ] Keep the runner/registry as the source of truth for tools.
- [ ] Document why MCP is an interface layer, not a new safety boundary.

Done when:

- [ ] The MCP implementation approach cannot bypass the existing allowlist and validation model.

### Step 2 - Register Initial MCP Tools

Estimate:

```text
0.75-1 engineer-days
4.5-6 hours
```

Tasks:

- [ ] Register project resource summary as an MCP tool.
- [ ] Register server basic info as an MCP tool with the same server validation as the local runner.
- [ ] Register server network info as an MCP tool with the same server validation as the local runner.
- [ ] Register host/log tools only if Phase 06 is complete and the tools are safe locally.
- [ ] Add tool descriptions that clearly state read-only behavior and credential class.

Done when:

- [ ] An MCP client can discover the approved diagnostic tools and no generic command tool exists.

### Step 3 - Reuse Structured Result and Audit Path

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Return the same result envelope fields through MCP.
- [ ] Preserve timeout, truncation, unavailable, validation-error, and denied statuses.
- [ ] Write audit events for MCP-originated tool calls.
- [ ] Add client identifier or transport identifier where available.
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

- [ ] Expose the AI-OPS safety policy as a read-only resource.
- [ ] Expose the metadata troubleshooting runbook as a read-only resource.
- [ ] Expose a lab architecture summary as a read-only resource.
- [ ] Ensure resources are static/read-only and contain no secret material.
- [ ] Document how the AI client should use resources before or during diagnostics.

Done when:

- [ ] The AI client can retrieve lab-specific context without reading arbitrary files.

### Step 5 - Add MCP Prompts

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Add a metadata diagnosis prompt that calls approved tools in order and forbids remediation.
- [ ] Add a server inspection prompt for one server name or ID.
- [ ] Add a project summary prompt for high-level inventory questions.
- [ ] Mark prompts as diagnostic workflows, not autonomous repair flows.
- [ ] Include expected explanation structure: healthy signals, failing signals, likely failure domain, evidence gaps, and manual next steps.

Done when:

- [ ] The AI client can offer repeatable OpenStack Lab diagnostic workflows without inventing raw commands.

### Step 6 - Add MCP Integration Tests

Estimate:

```text
0.75-1.25 engineer-days
4.5-7.5 hours
```

Tasks:

- [ ] Test MCP tool discovery includes approved tools.
- [ ] Test MCP tool discovery excludes generic command tools.
- [ ] Test valid tool calls return the same structured envelope as the runner.
- [ ] Test invalid parameters are rejected through MCP.
- [ ] Test audit logging for MCP calls.
- [ ] Test resources and prompts are discoverable and contain no obvious secrets.

Done when:

- [ ] MCP integration passes safety and behavior tests without a live remediation capability.

### Step 7 - Document MCP Client Setup and Rollback

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Document how to start the MCP server locally on the assistant runtime.
- [ ] Document how an AI client connects to the server.
- [ ] Document that remote exposure is not part of this phase.
- [ ] Document rollback: stop MCP server, disable client config, retain local runner for manual use.

Done when:

- [ ] A maintainer can enable or disable MCP without touching OpenStack Lab state.

## 07.6 Phase Definition of Done

This phase is done when:

- [ ] MCP server starts locally.
- [ ] MCP exposes only approved diagnostic tools.
- [ ] MCP tools reuse the same validation, timeout, output-limit, and audit behavior as the runner.
- [ ] MCP resources expose safe lab context.
- [ ] MCP prompts encode repeatable diagnostic workflows.
- [ ] MCP tests verify no generic command execution capability exists.
- [ ] Remote unauthenticated exposure remains out of scope.

## 07.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| MCP accidentally bypasses local runner controls | Use the existing registry/execution layer as the only execution path and test equivalence. |
| AI client treats tools as remediation | Tool descriptions and prompts must explicitly state diagnostic-only behavior. |
| MCP resources expose sensitive files | Expose curated resources only; never implement arbitrary file read. |
| Remote MCP exposure creates a new attack surface | Start with local stdio only; require a separate design for authenticated remote access. |