# 00. Implementation Plan Overview

This directory translates the revised read-only AI-OPS PRD and the existing OpenStack Lab implementation context into executable engineering work.

The repository already contains a prior AI-OPS runtime implementation, tests, runbooks, and runtime evidence. The revised implementation follows a copy-first rule: preserve the prior implementation unchanged as the historical baseline, create a complete source-controlled copy of the prior AI-OPS runtime implementation under an isolated revised namespace, and modify only the copied components where the revised PRD requires a difference. The revised copy must be validated independently; historical completion evidence does not establish revised acceptance.

Copy-first applies to source-controlled implementation, configuration templates, tests, and documentation. It does not permit copying live credentials, tokens, private keys, raw audit logs, secret-bearing runtime state, or unredacted evidence. Those items must be created fresh for the revised runtime.

The files are ordered by delivery phase. Each phase has:

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
docs/ai-ops-revised/implementation-plan
```

Reason:

* the plan belongs beside the revised PRD
* it is distinct from the historical AI-OPS plan and evidence
* each file describes work needed to satisfy the revised acceptance boundary

## 00.2 Estimation Rules

Estimates are intentionally rough.

Use this baseline:

```text
1 engineer-day = about 6 focused engineering hours
```

The estimates do not include long external delays such as:

* waiting for infrastructure access, credentials, policy changes, DNS, procurement, approvals, or unrelated incidents

The estimates assume one experienced engineer with reasonable access to the repository, assistant runtime, and a deployed OpenStack Lab. Estimates include creating a complete isolated source copy of the prior AI-OPS runtime implementation, recording its provenance, and modifying only the copied components that differ from the revised contracts. Isolation or replacement work may move an item toward the upper end of its range.

## 00.3 Phase Summary

| Phase | File | Goal | Estimate |
| ----- | ---- | ---- | -------- |
| 00 | `00-implementation-overview.md` | Explain the execution plan | Documentation only |
| 01 | `01-baseline-and-runtime-foundation.md` | Copy the prior baseline into an isolated revised namespace and establish the revised runtime | 2-3.5 engineer-days |
| 02 | `02-readonly-identity-and-policy-boundary.md` | Create and prove least-privilege credential boundaries | 1.5-3 engineer-days |
| 03 | `03-manual-diagnostic-toolbox.md` | Deliver reviewed read-only API diagnostics for manual use | 2.5-4 engineer-days |
| 04 | `04-tool-runner-safety-gateway.md` | Enforce allowlisting, validation, limits, structured results, and auditing | 3-5 engineer-days |
| 05 | `05-mvp-workflows-and-live-validation.md` | Prove useful diagnostic workflows against deployed lab state | 1.5-2.5 engineer-days |
| 06 | `06-restricted-operator-and-host-diagnostics.md` | Add higher-visibility service and log evidence behind separate controls | 3-5 engineer-days |
| 07 | `07-mcp-interface.md` | Expose the trusted toolbox through local, read-only MCP | 3-5 engineer-days |
| 08 | `08-hardening-rollout-and-operations.md` | Integrate quality gates, security review, rollout, rollback, and expansion governance | 2.5-4.5 engineer-days |

Estimated MVP total through Phase 05:

```text
10.5-18 engineer-days
63-108 focused hours
```

Estimated full plan total:

```text
19-32.5 engineer-days
114-195 focused hours
```

## 00.4 Recommended Build Order

Build in this order:

1. Inventory the prior AI-OPS assets, record their provenance, and create a complete source-controlled copy of the prior runtime implementation without changing the prior implementation.
2. Assign distinct repository/runtime identifiers to the revised copy and establish its separately isolated runtime without cloning live secrets or operational state.
3. Create fresh project-reader identity material and prove both useful reads and denied mutations.
4. Modify the copied diagnostics only where the revised contracts require a difference, then validate the three smallest useful API diagnostics manually.
5. Put the revised deny-by-default tool runner in front of every executable diagnostic.
6. Prove project inspection, server inspection, and metadata-oriented workflows against a deployed lab.
7. Add operator-reader and restricted host diagnostics only after the lower-risk API path is accepted.
8. Add MCP as an interface over the revised runner, never as a second execution path.
9. Consolidate security, regression, deployment, audit, rollback, and extension controls.

This order preserves the known prior runtime while proving the smallest revised end-to-end workflow before adding host access or protocol automation. A copied component should remain unchanged when it already satisfies the revised contract. It may shorten a phase only after the revised copy passes independent acceptance checks.

## 00.5 Cross-Phase Principles

- [ ] The prior AI-OPS source and deployed runtime remain unchanged and available as the historical reference until an explicit retirement decision.
- [ ] Revised work starts from an isolated copy; changes are made only in the revised copy and only when required by a documented PRD gap.
- [ ] Revised repository paths, Ansible identifiers, package/module names, runtime paths, service names, users, credential-profile names, SSH keys, audit locations, and MCP client registrations must not collide with the prior runtime.
- [ ] Live credentials, tokens, private keys, raw audit logs, secret-bearing state, and unredacted evidence are never copied from the prior runtime.
- [ ] AI reasoning, explanation, and manual recommendations are allowed; system mutation is blocked.
- [ ] No generic shell, SSH, sudo, OpenStack CLI, file, database, package, service-control, or remediation capability is AI-facing.
- [ ] Every executable capability is deny-by-default and explicitly registered by diagnostic intent.
- [ ] Project-reader is the default profile; broader profiles are separate, optional, and tool-specific.
- [ ] Inputs are validated both at the runner boundary and inside diagnostic implementations.
- [ ] Processes are invoked with argument vectors and never with user-composed shell strings.
- [ ] Every tool has a timeout and bounded output behavior.
- [ ] Every result has a stable status and enough metadata to distinguish diagnostic findings from execution failures.
- [ ] Every allowed and denied request is auditable without recording secrets.
- [ ] Missing optional credentials or host access produce `unavailable`, not unsafe fallback behavior.
- [ ] Revised MCP reuses the revised registry and runner; it does not introduce an alternate execution path.
- [ ] Important security-boundary changes are recorded with reproducible validation evidence.
- [ ] Existing Vagrant, Ansible, OpenStack bootstrap, observability, and Molecule workflows remain unchanged unless a reviewed compatibility change is required.
- [ ] Tests verify external behavior and safety rules rather than private implementation details.

## 00.6 Recommended MVP Slice

```text
isolated revised assistant runtime created from the copied source baseline reaches Keystone
  -> dedicated project-reader authenticates and lists project-visible resources
  -> representative create/update/delete attempts are denied
  -> project_resource_summary, server_basic_info, and server_network_info run manually
  -> named requests pass through one deny-by-default runner
  -> runner validates inputs, enforces timeout/output limits, returns structured results, and writes sanitized audit events
  -> operator gives the evidence to an AI assistant
  -> AI identifies healthy signals, failure signals, evidence gaps, and manual next steps without executing remediation
```

Operator-reader, SSH log diagnostics, MCP, a local model, and observability data-source integrations are not required for MVP.

## 00.7 Tracking Format

Each task uses checkboxes:

```text
- [ ] Task not started
- [x] Task completed
```

Subtasks should be checked only when the behavior exists in the isolated revised copy and has been verified against the revised contracts. Historical completion markers and prior-runtime tests are supporting evidence, not substitutes for revised validation.

## 00.8 Definition of MVP Done

The MVP is done when this path is repeatable against a deployed lab:

```text
operator asks a project, server, network, or metadata-oriented question
  -> approved tool names are selected
  -> runner accepts only valid registered requests
  -> fixed diagnostics execute with project-reader authority
  -> structured results and sanitized audit events are produced
  -> AI explains likely failure domains and proposes manual follow-up
  -> no resource or host state changes
```

The implementation may be simple and manual at the AI boundary. It must be inspectable, observable, safe to retry, and unable to turn “fix it” intent into mutation.
