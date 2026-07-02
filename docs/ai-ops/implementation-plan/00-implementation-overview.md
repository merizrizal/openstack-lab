# 00. Implementation Plan Overview

This directory translates the AI-OPS PRD and supporting OpenStack Lab knowledge into implementation work.

The files are ordered by MVP phase. Each phase has:

* goal
* scope
* assumptions
* ordered tasks
* estimates
* checkboxes
* definition of done

## 00.1 Directory Name

This directory is named:

```text
docs/ai-ops/implementation-plan
```

Reason:

* the plan belongs to the AI-OPS documentation area
* each file describes implementation work for the read-only AI-OPS assistant
* the path keeps the PRD and execution plan together

## 00.2 Estimation Rules

Estimates are intentionally rough.

Use this baseline:

```text
1 engineer-day = about 6 focused engineering hours
```

The estimates do not include long external delays such as:

* waiting for access, credentials, DNS, procurement, approvals, or unrelated incidents

The estimates assume one experienced engineer working with reasonable access to the OpenStack Lab, assistant runtime, and repository.

## 00.3 Phase Summary

| Phase | File | Goal | Estimate |
| ----- | ---- | ---- | -------- |
| 00 | `00-implementation-overview.md` | Explain execution plan | Documentation only |
| 01 | `01-assistant-runtime-foundation.md` | Establish isolated assistant runtime and workspace conventions | 1-2 engineer-days |
| 02 | `02-readonly-credential-boundary.md` | Create and prove read-only OpenStack authority boundary | 1.5-3 engineer-days |
| 03 | `03-safe-diagnostic-toolbox.md` | Build the first reviewed read-only OpenStack diagnostic scripts | 2-3 engineer-days |
| 04 | `04-tool-runner-safety-gateway.md` | Add allowlisted wrapper, validation, timeouts, structured results, and audit logs | 2.5-4 engineer-days |
| 05 | `05-manual-aiops-workflows.md` | Make the MVP usable through documented manual and local-runner workflows | 1-2 engineer-days |
| 06 | `06-restricted-host-diagnostics.md` | Add host/log diagnostics behind restricted SSH and sudo rules | 2-4 engineer-days |
| 07 | `07-mcp-integration.md` | Expose trusted diagnostics through MCP tools, resources, and prompts | 3-5 engineer-days |
| 99 | `99-hardening-validation-and-rollout.md` | Harden safety controls, tests, rollout, and operations | 2-4 engineer-days |

Estimated MVP total through Phase 05:

```text
8-14 engineer-days
48-84 focused hours
```

Estimated full plan total through Phase 99:

```text
15-27 engineer-days
90-162 focused hours
```

## 00.4 Recommended Build Order

Build in this order:

1. Establish the assistant runtime and workspace boundaries.
2. Create the read-only OpenStack credential boundary and prove mutation fails.
3. Build the smallest useful OpenStack API diagnostic toolbox.
4. Put a safety gateway between AI/tool requests and script execution.
5. Document and validate the manual/local-runner troubleshooting workflows.
6. Add restricted host/log diagnostics only after API diagnostics are safe.
7. Add MCP only after the same tools are trusted outside MCP.
8. Harden validation, regression tests, audit review, and rollout controls.

Rationale:

The first valuable slice is not a fully autonomous AI operator. It is a safe, repeatable diagnostic path that lets an operator ask a question, run approved read-only tools, get structured evidence, and let AI explain likely failure domains. MCP and host-level log access come after this path is proven because they increase reach and risk.

## 00.5 Cross-Phase Principles

- [ ] AI reasoning is allowed; OpenStack Lab mutation is blocked by design.
- [ ] No generic shell, SSH, sudo, OpenStack CLI, file-write, database, restart, or remediation tool is introduced.
- [ ] Every diagnostic capability is deny-by-default and must be explicitly allowlisted.
- [ ] Every tool accepts only narrow, validated parameters.
- [ ] Every tool call returns structured status, duration, output, error, and truncation information.
- [ ] Every allowed, denied, failed, timed-out, and validation-error call is auditable.
- [ ] Every credential is dedicated, least-privileged, and empirically tested.
- [ ] Host-level diagnostics require stricter controls than OpenStack API diagnostics.
- [ ] Logs and errors should be visible without deep manual debugging.
- [ ] Tests should verify external behavior and safety boundaries, not implementation details.
- [ ] MCP is an interface layer, not the safety boundary.
- [ ] Remediation recommendations may be written as text; remediation execution remains out of scope.

## 00.6 Recommended MVP Slice

```text
assistant runtime reachable to Keystone
  -> project-scoped read-only credential configured
  -> read commands succeed and mutation commands fail
  -> project_resource_summary, server_basic_info, and server_network_info scripts run manually
  -> local tool runner executes only those tools through an allowlist
  -> tool calls are validated, timed out, size-limited, and audited
  -> operator can run a metadata-oriented diagnostic workflow and paste/hand results to AI for explanation
```

## 00.7 Tracking Format

Each task uses checkboxes:

```text
- [ ] Task not started
- [x] Task completed
```

Subtasks should be checked only when the behavior exists and has been verified.

## 00.8 Definition of MVP Done

The MVP is done when the smallest valuable workflow can move through the full path described by the PRD:

```text
operator asks an OpenStack diagnostic question
  -> AI or runbook selects approved diagnostic tools
  -> local tool runner validates the request
  -> fixed read-only scripts run with project-reader credentials
  -> structured result and audit event are produced
  -> AI explains healthy signals, failing signals, likely failure domain, and manual next steps
  -> no system mutation occurs and mutation remains impossible with the configured credential
```

The implementation can be simple. It must be repeatable, observable, and safe enough that accidental “fix it” intent cannot change the lab.