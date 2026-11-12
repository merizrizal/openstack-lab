# Manual AI-OPS Workflows

## Scope and Document Path

This runtime-facing document defines the Phase 05 MVP manual AI-OPS workflow boundary for operators using the local runner and approved read-only tools.

It exists to complement, not replace, the implementation-plan source document at `docs/ai-ops/implementation-plan/05-manual-aiops-workflows.md`.

This runtime document is the operator-facing workflow reference requested by the Phase 05 ADS. The implementation-plan document remains the planning and checklist source of truth.

Phase 05 MVP workflow boundary:

```text
operator question -> approved tool sequence -> local runner outputs -> AI explanation prompt -> manual recommendation only
```

This document intentionally covers the Phase 05 MVP policy baseline plus the currently documented manual workflows:

- diagnostic-only assistant behavior
- refusal guidance
- approved MVP tools
- unavailable or deferred tools
- safety principles
- basic project inspection workflow
- server inspection workflow
- metadata troubleshooting workflow

Runtime validation procedures are still intentionally deferred until the later validation chunk lands.

## Diagnostic-Only Assistant Behavior

The Phase 05 MVP assistant is diagnostic-only.

The assistant may:

- observe operator-provided, redacted local-runner output
- explain what healthy signals appear in the evidence
- explain what failing, missing, incomplete, or unavailable signals appear in the evidence
- identify likely failure domains based on the approved tool outputs
- ask focused follow-up questions when the provided evidence is incomplete
- recommend manual next steps only

The assistant must not:

- execute fixes
- mutate OpenStack resources
- mutate runtime files
- request or use MCP automation
- request or use a chat UI integration as an execution surface
- request or use SSH access to OpenStack nodes
- request or use sudo access
- request or use a generic shell tool
- request or use raw OpenStack CLI passthrough
- invent unsupported tools or hidden data sources
- present remediation as completed

The assistant response model for Phase 05 is explanation first, manual recommendation second, and no execution.

## Refusal Guidance

If an operator asks for mutation, privileged execution, or unsupported access, the assistant must refuse and redirect to the approved diagnostic boundary.

Refusal cases include requests such as:

- fix it
- restart it
- delete it
- create it
- edit config
- SSH into the host
- run this shell command
- use sudo
- run the raw OpenStack command for me

Expected refusal pattern:

1. state that the Phase 05 MVP is diagnostic-only
2. state that execution, mutation, SSH, sudo, shell passthrough, and raw CLI passthrough are outside scope
3. offer the next approved diagnostic step using the available runner tools
4. keep recommendations manual and text-only

Example refusal style:

> I cannot restart services, edit configuration, SSH to hosts, run shell commands, or mutate OpenStack resources in the Phase 05 MVP. I can help interpret approved diagnostic output from the local runner and suggest manual next steps.

## Approved MVP Tools

Only the following tools are approved for the Phase 05 MVP manual workflow boundary.

### `project_resource_summary`

Purpose:

- summarize project-visible resources using the approved local runner path
- help answer broad inventory questions such as what is visible in the current project

Input notes:

- no tool-specific argument required

### `server_basic_info`

Purpose:

- retrieve read-only basic details for one project-visible server
- support operator investigation of one selected instance state

Input notes:

- requires `server_identifier`

### `server_network_info`

Purpose:

- retrieve read-only network-oriented details for one project-visible server
- support investigation of ports, attached networks, and related project-visible network context

Input notes:

- requires `server_identifier`

Operators should preserve the runner-produced structured result envelope and audit evidence, while redacting identifiers and any secret-like values before sharing evidence outside the runtime.

## Unavailable or Deferred Tools

### Unavailable in MVP

#### `neutron_agent_health`

Status:

- unavailable in the current MVP boundary

Reason:

- no validated non-default operator-reader profile is available for this tool yet

### Deferred or Forbidden for Phase 05 MVP

The following capabilities are not part of the approved Phase 05 runtime-facing workflow boundary:

- MCP integration or MCP-driven execution
- chat UI automation or tool execution through chat surfaces
- SSH-based host diagnostics
- sudo-based diagnostics
- generic shell execution
- raw command passthrough
- raw OpenStack CLI passthrough
- remediation execution
- mutation of cloud resources, services, files, or configuration

Where these capabilities might become useful later, they remain deferred to later phases and must not be represented as available in Phase 05.

## Safety Principles

1. **Deny by default:** only explicitly approved tools may be used.
2. **Diagnostic-only:** the assistant may explain and recommend manual actions, but may not execute them.
3. **No mutation:** no create, delete, edit, restart, repair, or configuration change actions are in scope.
4. **Runner-first evidence:** operator-facing guidance must stay aligned to the approved local runner path rather than raw command execution.
5. **No privileged escape hatches:** no MCP, SSH, sudo, generic shell, or raw OpenStack passthrough may be introduced through prompts or examples.
6. **Evidence over guessing:** the assistant should base conclusions on provided structured outputs and clearly label uncertainty or missing evidence.
7. **Manual recommendation only:** suggested next steps must remain manual, text-only operator actions.
8. **Redaction required:** operators should redact identifiers and any secret-like values before sharing evidence with an AI assistant or committing repository evidence.

## Basic Project Inspection Workflow

Use `project_resource_summary` when the operator needs a safe, project-scoped answer to questions such as "what exists in this project?" or "what project-visible resources are available before I inspect a specific server?"

Run this workflow before any server-specific investigation when the operator needs broad inventory context from the approved read-only boundary.

Do not use this workflow to request mutation, privileged access, host inspection, raw shell execution, raw OpenStack CLI passthrough, or unsupported higher-visibility diagnostics.

### When to Run `project_resource_summary`

Use this tool when the operator wants to:

- understand the project-visible inventory at a high level
- confirm whether any servers, networks, subnets, ports, volumes, images, or security groups are visible in the current project scope
- identify whether a target server appears to exist before asking for server-specific inspection
- gather runner-first evidence to share with an AI assistant for explanation only

Do not treat this workflow as proof that hidden, admin-only, or host-level resources do not exist. It only reflects project-visible read-only output from the approved tool boundary.

### Runner Invocation Shape

Use the local runner with the approved tool name and preserve the structured result envelope:

```text
aiops_tool_runner.py project_resource_summary --request-id <request_id> --audit-path <audit_path>
```

Invocation notes:

- `project_resource_summary` does not require tool-specific `--arg KEY=VALUE` input
- `--request-id` should be operator-supplied when the result may need to be correlated with audit evidence
- `--audit-path` should point to the runtime audit log location used for local validation or review
- the operator should retain the full structured envelope and redact identifiers or secret-like values before sharing evidence with an AI assistant

### Expected Result Envelope Fields

The local runner returns a structured result envelope with these fields:

- `tool`
- `status`
- `arguments`
- `exit_code`
- `stdout`
- `stderr`
- `duration_ms`
- `truncated`
- `timestamp`
- `request_id`

Interpretation guidance:

- verify `tool` is `project_resource_summary`
- use `status` as the primary success or failure signal before interpreting content
- expect `arguments` to be empty for this tool
- use `stdout` for the project summary content and `stderr` for explicit error context
- preserve `request_id` and `timestamp` for audit correlation
- check `duration_ms` to understand whether the run completed normally or may have been unusually slow
- check `truncated` before assuming the visible `stdout` contains the complete summary

### Interpreting Empty Output or Unavailable Sections

If the structured envelope shows `status: ok` but `stdout` is empty or sparse, interpret that carefully:

- the current project may truly have few or no visible resources
- one or more resource sections may be empty because nothing project-visible matched that section
- policy or credential limits may prevent some sections from returning useful data even when the tool itself ran successfully

If the output appears to omit a resource category, the assistant should say that the section is unavailable or not visible from current evidence, not that the resource category is globally absent.

If the envelope shows permission or availability limits in `stdout` or `stderr`, interpret them as scope boundaries rather than proof of platform failure.

If `status` is not `ok`, the assistant should first explain the execution state using the envelope:

- non-zero `exit_code` indicates the runner did not complete the tool successfully
- `stderr` may describe validation, timeout, denial, or unavailable conditions
- `truncated: true` means the visible output may be incomplete and should not be treated as a full inventory

### AI Prompt Template

Use this prompt shape after redacting sensitive identifiers:

```text
You are helping with Phase 05 manual AI-OPS analysis.

Scope rules:
- Diagnostic-only explanation.
- No mutation, remediation execution, SSH, sudo, generic shell, raw command passthrough, or raw OpenStack CLI passthrough.
- Manual recommendations only.

Question:
What exists in this project?

Structured runner envelope:
- tool: <tool>
- status: <status>
- arguments: <arguments>
- exit_code: <exit_code>
- duration_ms: <duration_ms>
- truncated: <truncated>
- timestamp: <timestamp>
- request_id: <request_id>
- stderr: <redacted stderr>
- stdout: <redacted stdout>

Please:
1. summarize the project-visible resources that appear to exist
2. identify any empty, unavailable, missing, or permission-limited sections
3. explain what cannot be concluded from this evidence alone
4. propose manual next diagnostic questions only
5. do not claim any mutation or remediation was performed
```

### Redacted Sample Summary

Example operator-to-AI summary based on a successful redacted run:

> Request `<request_id>` used `project_resource_summary` and returned `status: ok` with `duration_ms: 842` and `truncated: false`. The visible project inventory shows two servers, one private network, one subnet, several ports tied to the visible instances, one attached volume, and standard project security groups. No admin-only or host-level evidence is available from this workflow. One section appears empty for images, which may mean no project-visible images were returned rather than proving no images exist anywhere outside current scope. Manual next steps: choose one visible server identifier and run the approved server inspection workflow if deeper instance detail is needed.

## Forward Reference

Later Phase 05 chunks may add additional workflow steps and validation material beyond the project and server workflows documented here.
## Server Inspection Workflow

### Goal
Collect read-only evidence for one OpenStack server by using the approved `server_basic_info` and `server_network_info` tools with the same `server_identifier` value in both calls.

### Safe `server_identifier` Rules
- Reuse the exact same `server_identifier` string for both tools in the same inspection.
- Prefer the server UUID when it is already available from authoritative evidence.
- If a name must be used, use the exact server name as shown by authoritative OpenStack output and only when it is unique in the target scope.
- Do not guess, shorten, partially match, normalize, or “correct” the identifier between tool calls.
- Do not switch from name to UUID mid-workflow unless you restart the workflow and clearly note that a new evidence collection run began.
- If the operator supplies an ambiguous identifier, ask for the server UUID before continuing.

### Approved Evidence Collection Sequence
1. Run `server_basic_info` for the target `server_identifier`.
2. Run `server_network_info` for the same `server_identifier`.
3. Summarize only what the tool outputs show.
4. If either tool returns permission-related gaps or incomplete output, keep the confirmed evidence and ask follow-up questions instead of inferring missing data.

### Evidence to Capture from `server_basic_info`
Record the following when present in tool output:
- server identity evidence: UUID, name, project, and tenant-scoped context when shown
- status evidence: server status and power or task state clues when shown
- image and flavor evidence when shown
- availability zone or host placement clues when shown
- attached volume evidence, including any volume identifiers exposed by the tool
- config-drive clues, including whether config drive appears enabled, disabled, or otherwise reported
- top-level addresses or network labels shown in the basic server record

If a field is absent from output, state that it was not shown by the approved tool output rather than filling it in from assumption.

### Evidence to Capture from `server_network_info`
Record the following when present in tool output:
- network names associated with the server
- port identifiers associated with the server
- fixed IP addresses associated with each discovered port
- MAC address or device ownership clues when shown
- port status or binding details when shown
- floating IP relationships only if explicitly shown by the approved tool output

When multiple ports exist, keep the network-to-port-to-fixed-IP relationships as shown by the evidence.

### Interpreting Volumes and Config-Drive Clues
- Treat attached volume data as storage attachment evidence only; do not infer application state from attachment presence.
- Treat config-drive data as a provisioning clue only; do not infer successful cloud-init completion, guest health, or metadata reachability from config-drive presence alone.
- If config-drive information is missing, say that the approved output did not provide a config-drive conclusion.

### Permission Errors and Incomplete Output
The approved tools may return partial evidence when the executing identity lacks permission to read some related resources.

Handle this as follows:
- preserve the successful portion of the evidence
- quote or summarize the permission error precisely enough for operator review
- mark the missing area as `incomplete due to permissions` or `not returned by approved output`
- do not substitute guessed ports, IPs, volumes, or metadata details

Common follow-up questions:
- Can you provide the server UUID if the current identifier may be ambiguous?
- Was this server inspection run in the correct project or tenant scope?
- Do you want a cloud operator with read-only privileges to rerun the same approved tools for ports or attachments that were not visible?
- Is partial evidence acceptable for the current triage decision, or is complete network/attachment evidence required?
- Are there other authoritative artifacts for this same server identifier that should be compared with this output?

### AI Prompt Template: Server Inspection
Use this prompt template when asking the AI to summarize the evidence from the two approved tools.

```text
You are summarizing read-only OpenStack server evidence.

Server identifier used for both tools: <server_identifier>

Approved tool outputs:
1. server_basic_info
<insert redacted output>

2. server_network_info
<insert redacted output>

Instructions:
- Use only the evidence shown in these outputs.
- Confirm whether the same server_identifier was used for both tools.
- Summarize status, networks, ports, fixed IPs, volumes, and config-drive clues.
- Keep network-to-port-to-fixed-IP relationships explicit when available.
- If data is missing or blocked by permissions, say exactly that.
- Do not infer guest OS state, application health, metadata success, or remediation steps.
- End with follow-up questions needed to resolve incomplete evidence.
```

### Redacted Sample Server Inspection Summary

```text
Server inspection target
- server_identifier: 2f4d1b7e-xxxx-xxxx-xxxx-9a32c8d4b111
- Evidence sources: server_basic_info, server_network_info
- Identifier consistency: confirmed; the same server_identifier was used in both tool runs

Confirmed server evidence
- Server name: app-prod-01
- Server UUID: 2f4d1b7e-xxxx-xxxx-xxxx-9a32c8d4b111
- Status: ACTIVE
- Flavor: m1.medium
- Image: redacted-image-name
- Config-drive clue: reported as enabled

Storage evidence
- Attached volumes:
  - 8d91d4aa-xxxx-xxxx-xxxx-0b77a7f33001

Network evidence
- Network: prod-net
  - Port: 3f2c4a10-xxxx-xxxx-xxxx-6e45d2b22001
  - Fixed IPs:
    - 10.24.8.17
- Network: backup-net
  - Port: 2a13e990-xxxx-xxxx-xxxx-5d02ab8ef002
  - Fixed IPs:
    - 172.18.4.23

Gaps or access limits
- Port details for one attachment were partially visible due to a permission error from the approved output.
- No conclusion was made about guest OS health or application reachability.

Follow-up questions
- Do you want an operator with read-only network privileges to rerun the same server_identifier through the approved tools?
- Is the partial port evidence sufficient for current triage, or is complete attachment visibility required?
```

## Metadata Troubleshooting Workflow

### Goal
Start from guest symptoms such as cloud-init metadata failure or failed access to `169.254.169.254`, then use only approved project-visible runner outputs to localize what is healthy, what is failing or missing, and what must remain deferred to later host-level diagnostics.

### Starting Symptoms and Investigation Boundary
Use this workflow when the operator reports symptoms such as:
- cloud-init errors that mention metadata retrieval failure
- guest access failures to `http://169.254.169.254/openstack`
- newly built instances that boot but do not receive expected metadata, SSH keys, or user-data clues

Treat the metadata request path conceptually as:

```text
guest cloud-init
  -> 169.254.169.254
  -> Neutron metadata proxy / metadata agent
  -> Nova metadata API
  -> instance metadata response
```

Within the Phase 05 MVP, only the project-visible portions of this path can be examined directly through approved runner output. Do not claim that Neutron metadata routing, the Nova metadata API, or host listeners are healthy unless that evidence is explicitly available through approved tools.

### Approved Evidence Sources for Metadata Triage
Use only these approved evidence sources:
1. `project_resource_summary`
2. `server_basic_info`
3. `server_network_info`

Use them in this order when possible:
1. run `project_resource_summary` to confirm the project-visible inventory and locate the target server
2. run `server_basic_info` for the chosen `server_identifier`
3. run `server_network_info` for the same `server_identifier`
4. summarize what the evidence confirms, what it does not confirm, and what remains outside current visibility

If the target server is not visible in the current project scope, say that the metadata workflow cannot continue from approved evidence alone until the operator provides the correct server identifier or correct project context.

### Healthy Signals to Look For
The following are healthy or at least non-alarming signals within current MVP evidence scope:
- `project_resource_summary` returns `status: ok` and shows the target server in the expected project-visible inventory
- `server_basic_info` returns the expected server identity and a stable instance state such as `ACTIVE`
- `server_network_info` returns one or more expected network attachments for the same `server_identifier`
- one or more fixed IP addresses are visible on the expected tenant network attachments
- config-drive is reported as enabled, if that is expected for the image or provisioning path
- the runner envelopes are not truncated and do not show permission or availability failures

Interpret these signals carefully:
- healthy project-visible server and network evidence means the instance exists and is attached to visible network resources
- config-drive presence is only a provisioning clue; it does not prove metadata success through `169.254.169.254`
- visible fixed IPs do not prove that the Neutron metadata proxy path or Nova metadata API is healthy

### Failing, Missing, or Inconclusive Signals
The following signals may point to a failure domain or require cautious follow-up:
- the server is missing from `project_resource_summary` when the operator expects it to exist
- `server_basic_info` cannot find the target server or returns a non-`ok` status
- the server exists but is not in a stable state, such as not `ACTIVE`
- `server_network_info` shows missing, partial, permission-limited, or unexpected network attachments
- expected ports or fixed IPs are absent from approved output
- the runner returns `error`, `validation_error`, `timeout`, `unavailable`, or `truncated`
- config-drive is disabled or not shown when the operator expected metadata-related provisioning clues

Interpretation guidance:
- missing server visibility may indicate wrong project scope, wrong identifier, or a lifecycle issue before metadata troubleshooting can be narrowed further
- missing or incomplete network attachment evidence may indicate a project-visible network association problem or a permission boundary in the current read-only scope
- a stable server with expected ports and fixed IPs can still have a metadata-path failure that is not visible from project-reader evidence alone

### Likely Failure Domains from Approved Evidence
Use the approved evidence to separate likely domains without over-claiming:

1. **Project or identifier mismatch**
   - target server not visible
   - ambiguous or incorrect `server_identifier`
   - wrong tenant or project context

2. **Project-visible server lifecycle issue**
   - server not in expected state
   - incomplete provisioning clues in basic info
   - related evidence missing because the server was never fully established

3. **Project-visible network attachment issue**
   - expected port or fixed IP evidence is missing
   - network relationships are incomplete or unexpected
   - permission-limited output blocks confident interpretation

4. **Metadata path beyond current evidence scope**
   - server exists, appears stable, and has expected network attachments, but the operator still reports `169.254.169.254` or cloud-init metadata failure
   - this pattern is consistent with a path failure that may involve the Neutron metadata proxy or agent, the Nova metadata API, or the listener path behind it, but current MVP evidence cannot prove which component failed

### Manual Next Steps Only
Keep recommendations manual and non-executing. Appropriate manual next steps include:
- confirm the exact server UUID and rerun the approved server workflows using the same `server_identifier`
- confirm the investigation is being performed in the correct project scope
- compare the visible fixed IP and network attachments against the operator's expected design for the instance
- ask a cloud operator to review higher-visibility metadata-path evidence if the project-visible server and network evidence looks healthy but metadata still fails
- preserve the structured runner envelopes, including `status`, `stderr`, `truncated`, `timestamp`, and `request_id`, for escalation context

Do not present service restarts, config edits, SSH actions, sudo actions, or raw shell commands as Phase 05 workflow steps.

### Deferred to Phase 06 Host and Service Diagnostics
The following evidence is not available through the current approved Phase 05 MVP tools and must be labeled deferred to Phase 06 unless safely exposed later through new approved diagnostics:
- Neutron metadata agent logs
- Nova metadata API listener checks on `8775`
- Apache configuration or virtual host checks for the metadata API
- host process, host listener, or host log checks on controller or network nodes

When the approved project-visible evidence suggests a metadata-path problem beyond the tenant scope, say so explicitly and identify these as Phase 06 follow-up categories rather than as current executable steps.

### Follow-Up Questions for Incomplete Metadata Evidence
- What exact cloud-init or guest error text mentions metadata failure?
- What server UUID should be used for both `server_basic_info` and `server_network_info`?
- Is the instance expected to use config-drive, metadata service, or both?
- Are the visible networks and fixed IPs the ones the operator expected for this instance?
- Did either approved tool return `truncated`, `timeout`, permission-related gaps, or a non-`ok` status that needs clarification?
- Does the operator need a cloud operator to gather Phase 06 evidence because the project-visible server and network data appears healthy?

### AI Prompt Template: Metadata Troubleshooting
Use this prompt template after redacting sensitive identifiers.

```text
You are helping with Phase 05 manual AI-OPS metadata troubleshooting.

Scope rules:
- Diagnostic-only explanation.
- Use only the approved runner outputs provided here.
- No mutation, remediation execution, SSH, sudo, generic shell, raw command passthrough, or raw OpenStack CLI passthrough.
- Manual recommendations only.

Reported symptom:
- <cloud-init or 169.254.169.254 symptom>

Known metadata path:
guest cloud-init -> 169.254.169.254 -> Neutron metadata proxy / metadata agent -> Nova metadata API -> instance metadata response

Structured runner evidence:
1. project_resource_summary
<insert redacted output>

2. server_basic_info
<insert redacted output>

3. server_network_info
<insert redacted output>

Please:
1. summarize the healthy signals that appear in the approved evidence
2. summarize the failing, missing, incomplete, permission-limited, unavailable, or truncated signals
3. identify the most likely failure domain using only this evidence
4. explain what remains unproven from the current project-visible evidence
5. clearly label Neutron metadata agent logs, Nova metadata API listener 8775, Apache config, and host checks as deferred to Phase 06 unless safely exposed later
6. propose manual next steps only
7. do not claim any fix, mutation, restart, config edit, or privileged access was performed
```
