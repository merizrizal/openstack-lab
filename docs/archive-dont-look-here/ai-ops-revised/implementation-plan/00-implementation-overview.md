# 00. Implementation Plan Overview

This directory translates the revised read-only AI-OPS PRD and the existing OpenStack Lab implementation context into executable engineering work.

The repository contains a prior AI-OPS runtime implementation, but the revised product is not a migration of every prior capability. The revised implementation follows a goal-aligned selective-reuse rule: preserve the prior implementation unchanged as historical evidence, inventory it at a fixed revision, and reuse only assets that directly support the approved path from manual diagnostics to one deny-by-default runner and then to a local stdio MCP interface.

Selective reuse applies per capability and per delivery phase. An asset is copied or adapted only after its owning phase confirms that it satisfies a current PRD requirement and does not import an excluded capability. Historical provider gateways, model orchestration, remote-provider bridges, egress management, device-auth operations, wheelhouse transfer, and unrelated host-observer automation are excluded unless a later approved requirement explicitly adds them.

Live credentials, tokens, private keys, raw audit logs, secret-bearing runtime state, generated artifacts, and unredacted evidence are never copied. Required credentials and operational state must be created fresh for the revised runtime.

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

The estimates assume one experienced engineer with reasonable access to the repository, assistant runtime, and a deployed OpenStack Lab. Estimates include prior-source classification, selective reuse review, isolated revised implementation, and independent validation. Reuse may shorten a phase only when the selected asset passes the revised phase contract without importing excluded dependencies.

## 00.3 Phase Summary

| Phase | File | Goal | Estimate |
| ----- | ---- | ---- | -------- |
| 00 | `00-implementation-overview.md` | Explain the execution plan | Documentation only |
| 01 | `01-baseline-and-runtime-foundation.md` | Catalog the prior baseline, define the selective-reuse boundary, and establish the minimal revised runtime | 2-3.5 engineer-days |
| 02 | `02-readonly-identity-and-policy-boundary.md` | Create and prove least-privilege credential boundaries | 1.5-3 engineer-days |
| 03 | `03-manual-diagnostic-toolbox.md` | Deliver reviewed read-only API diagnostics for manual use | 2.5-4 engineer-days |
| 04 | `04-tool-runner-safety-gateway.md` | Enforce allowlisting, validation, limits, structured results, and auditing | 3-5 engineer-days |
| 05 | `05-mvp-workflows-and-live-validation.md` | Prove useful diagnostic workflows against deployed lab state | 1.5-2.5 engineer-days |
| 06 | `06-restricted-operator-and-host-diagnostics.md` | Add higher-visibility service and log evidence behind separate controls | 3-5 engineer-days |
| 07 | `07-mcp-interface.md` | Expose the trusted toolbox through local or authenticated internal-network, read-only MCP | 3-6 engineer-days |
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

1. Pin and inventory the prior AI-OPS source, classify assets by current PRD capability, and explicitly exclude unrelated orchestration, provider, egress, device-auth, wheelhouse, and remote-operation paths.
2. Create the smallest isolated revised runtime foundation from new namespace-safe automation; selectively adapt only foundation behavior needed for workspace, tooling, and later credentials.
3. Create fresh project-reader identity material and prove both useful reads and denied mutations.
4. Select and adapt only the three initial project-level diagnostics, then validate them manually.
5. Select or implement one revised deny-by-default runner and registry for those accepted diagnostics.
6. Prove project inspection, server inspection, and metadata-oriented workflows against a deployed lab.
7. Add operator-reader and restricted host diagnostics only after the lower-risk API path is accepted.
8. Select or implement a local stdio MCP adapter over the accepted revised runner, or separately design an authenticated internal-network MCP service, without the historical orchestrator bridge or external-client implementation.
9. Consolidate security, regression, deployment, audit, rollback, and extension controls.

This order preserves historical evidence without importing unrelated architecture. Each reuse decision is made in the phase that can validate the capability, so copied code cannot silently activate provider, orchestration, egress, host-access, or remote-operation behavior.

## 00.5 Cross-Phase Principles

- [ ] The prior AI-OPS source and deployed runtime remain unchanged and available as the historical reference until an explicit retirement decision.
- [ ] Revised work starts from a minimal isolated foundation; every reused asset is allowlisted by source path, requirement, owning phase, dependency closure, and validation evidence before it enters the revised namespace.
- [ ] Absence from the selective-reuse manifest means excluded; complete source-tree parity is neither required nor desired.
- [ ] Revised repository paths, Ansible identifiers, package/module names, runtime paths, service names, users, credential-profile names, SSH keys, audit locations, and MCP client registrations must not collide with the prior runtime.
- [ ] Live credentials, tokens, private keys, raw audit logs, secret-bearing state, generated artifacts, and unredacted evidence are never copied from the prior runtime.
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
- [ ] Revised MCP reuses the revised registry and runner; it does not introduce an alternate execution path or historical orchestrator dependency.
- [ ] Any internal-network MCP mode is separately authenticated, authorized, bounded, non-public, and independently disableable; external client implementation remains out of scope.
- [ ] Important security-boundary changes are recorded with reproducible validation evidence.
- [ ] Existing Vagrant, Ansible, OpenStack bootstrap, observability, and Molecule workflows remain unchanged unless a reviewed compatibility change is required.
- [ ] Tests verify external behavior and safety rules rather than private implementation details.

## 00.6 Recommended MVP Slice

```text
minimal isolated revised assistant runtime reaches Keystone
  -> dedicated project-reader authenticates and lists project-visible resources
  -> representative create/update/delete attempts are denied
  -> selectively adapted project_resource_summary, server_basic_info, and server_network_info run manually
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

Subtasks should be checked only when behavior exists in the isolated revised implementation and has been verified against the revised contracts. Historical completion markers and prior-runtime tests are supporting evidence, not substitutes for revised validation.

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
