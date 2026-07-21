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
| 08 | `08-orchestrator-architecture-and-sdk-contracts.md` | Define supported Codex SDK, security, dependency, and validation contracts | 1-1.5 engineer-days |
| 09 | `09-local-orchestrator-core.md` | Build a bounded local orchestrator around a fake Codex adapter | 1.5-2.5 engineer-days |
| 10 | `10-mcp-tool-loop-redaction-and-evidence.md` | Connect the orchestrator to MCP with redaction, tool-loop limits, and metadata evidence | 1.5-2.5 engineer-days |
| 11 | `11-sandboxed-deployment-authentication-and-egress.md` | Deploy a sandboxed runtime with Codex-managed login and bounded egress | 2-4 engineer-days |
| 12 | `12-controlled-remote-acceptance-and-operations.md` | Validate one controlled remote workflow and complete operations | 1-2 engineer-days |
| 13 | `13-provider-gateway-retirement.md` | Retire the superseded gateway after orchestrator acceptance | 0.5-1 engineer-days |
| 99 | `99-hardening-validation-and-rollout.md` | Harden safety controls, tests, rollout, and operations | 2-4 engineer-days |

Estimated MVP total through Phase 05:

```text
8-14 engineer-days
48-84 focused hours
```

Estimated hybrid orchestrator extension total through Phase 13:

```text
7.5-13.5 engineer-days
45-81 focused hours
```

Estimated full plan total through Phase 99:

```text
23-41 engineer-days
135-243 focused hours
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
8. Approve the hybrid orchestrator ADS and supported SDK/runtime contracts.
9. Build the orchestrator locally against a fake Codex adapter.
10. Connect the fake-backed workflow to the real local MCP safety boundary.
11. Deploy under a dedicated identity and validate authentication and egress boundaries without provider traffic.
12. Run exactly one separately approved remote acceptance workflow and complete operational runbooks.
13. Retire the historical provider gateway only after the replacement path is accepted.
14. Harden validation, regression tests, audit review, and rollout controls across the complete system.

Rationale:

The first valuable slice is not a fully autonomous AI operator. It is a safe, repeatable diagnostic path that lets an operator ask a question, run approved read-only tools, get structured evidence, and let AI explain likely failure domains. MCP and host-level log access come after this path is proven because they increase reach and risk.

The integrated extension follows the same sequence: contracts first, then a fake-backed local workflow, then the real MCP boundary, then sandboxed deployment and synthetic egress validation. Codex-managed authentication and one remote request occur only after those local gates pass. The historical provider gateway is retired last so rollback and evidence preservation remain possible.

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
- [ ] MCP is an interface layer, not the safety boundary, and remains the sole model-facing diagnostic route.
- [ ] Codex SDK/runtime owns ChatGPT authentication and provider transport; repository code never extracts or directly uses its credentials.
- [ ] Private Codex provider protocols are never inferred, proxied, patched, or treated as repository contracts.
- [ ] Every orchestrator path is proven with a fake Codex adapter before authentication, egress, or provider traffic.
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

## 00.9 Definition of Integrated Orchestrator Extension Done

The hybrid orchestrator extension is done when this bounded path is repeatable:

```text
operator submits one reviewed diagnostic workflow
  -> repository-owned orchestrator validates and redacts context
  -> supported Codex SDK/runtime uses Codex-managed ChatGPT authentication
  -> model may request only allowlisted local stdio MCP capabilities
  -> existing runner validates, executes, bounds, and audits read-only diagnostics
  -> tool results are redacted before model submission
  -> orchestrator returns advisory output and bounded metadata only
  -> no remediation occurs, no credential value is exposed, and no private provider protocol is handled by repository code
```

Initial remote acceptance remains an explicitly approved one-request operation. The supported SDK/runtime boundary may return a documented vendor blocker; that outcome must not restart custom-provider gateway recovery.
