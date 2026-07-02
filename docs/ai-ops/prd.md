# PRD: Read-Only AI-OPS Assistant for OpenStack Lab

## Problem Statement

OpenStack Lab operators need faster, repeatable, and safer help during day-2 operations such as checking VM state, debugging Neutron metadata failures, reviewing recent service errors, and understanding service health. Today, those workflows require a human to remember which OpenStack, SSH, log, metrics, and troubleshooting commands to run, then manually correlate outputs across controller, compute, storage, Ceph, and observability services.

This slows learning and troubleshooting, especially for issues such as guest cloud-init metadata failures where useful evidence spans tenant resource state, Neutron metadata proxy behavior, Nova metadata API availability, Apache listeners, and service logs.

The desired AI-OPS capability is an AI-assisted diagnostic workflow that can collect facts and explain likely failure domains without creating, updating, deleting, restarting, installing, editing, or otherwise changing the OpenStack Lab.

## Source Materials

- AI-OPS Step 1 raw plan: defined the dedicated AI assistant VM as a separate observer host on or routed to the management network, with restricted credentials and no control-plane role.
- AI-OPS Step 2 raw plan: defined basic tooling for the assistant VM, including Python, OpenStack CLI, OpenStack SDK, SSH client, JSON parsing, log search, curl, and diagnostic workspace structure.
- AI-OPS Step 3 raw plan: defined dedicated read-only OpenStack credentials, preference for reader role and application credentials, separation between project-reader and operator-reader profiles, and validation that mutations fail.
- AI-OPS Step 4 raw plan: defined safe diagnostic scripts, read-only command rules, input validation, JSON-oriented output, bounded logs, and initial OpenStack/Neutron/metadata diagnostics.
- AI-OPS Step 5 raw plan: defined a tool runner or wrapper that exposes only approved diagnostic tools, rejects arbitrary shell/OpenStack/SSH execution, validates parameters, enforces timeouts/output limits, and audits every call.
- AI-OPS Step 6 raw plan: defined MCP as a later interface layer over the already-safe toolbox, with tools, resources, prompts, audit logging, and no generic shell/SSH/OpenStack command exposure.
- OpenStack Lab base knowledge: contributed the current lab topology, management/provider network model, service placement, validation mindset, OpenStack metadata path, and repository domain vocabulary.
- OpenStack Lab architecture study: contributed the layered Vagrant, Ansible, OpenStack, workload, and validation architecture, node roles, optional Ceph/observability integrations, and service dependency graph.
- OpenStack Lab workflows: contributed current deployment and operations runbooks, stage validation checkpoints, observability placement, generated cloud config behavior, and day-2 operations notes.
- OpenStack Lab quality assessment: contributed current testing posture, Molecule smoke/e2e seams, runtime verification expectations, security posture, and operational robustness concerns.
- OpenStack Lab findings and recommendations: contributed security and operational hygiene risks, especially plaintext credentials, lab-friendly defaults, and the need for stronger consistency controls.
- OpenStack metadata troubleshooting note: contributed a concrete incident workflow showing how read-only evidence can isolate failure in the guest metadata path.

## Project Mode

Existing Project.

The OpenStack Lab already has a working repository, documented architecture, Ansible automation, Vagrant topology, operational runbooks, troubleshooting notes, and validation workflows. AI-OPS is a new capability to add alongside the existing lab, not a greenfield system. No AI-OPS implementation exists yet; this PRD describes the new feature’s product and engineering requirements while fitting into the current lab model.

## Solution

Build a read-only AI-OPS assistant capability around a dedicated AI assistant VM that acts as a safe diagnostic workstation for the OpenStack Lab.

The assistant VM will live outside the OpenStack control plane but near enough to reach management APIs, observability systems, and selected nodes. It will contain OpenStack diagnostic tooling, restricted OpenStack credentials, reviewed read-only scripts, and eventually a tool runner and MCP server that expose only approved diagnostic capabilities to an AI client.

The user experience should evolve in three levels:

1. Manual diagnostic assistant: the AI recommends which approved scripts to run, the operator runs them manually, and the AI explains pasted output.
2. Local tool-runner assistant: the AI or operator requests named tools, and a wrapper validates and executes only allowlisted scripts.
3. MCP-enabled assistant: an AI client discovers and calls approved diagnostic tools through MCP while the same safety boundary remains enforced by the wrapper, scripts, credentials, and restricted SSH model.

The core product constraint is: AI reasoning and observation are allowed; system mutation is blocked.

## Goals

1. Provide an AI-assisted OpenStack troubleshooting workflow that is safe for a lab operator to use repeatedly.
2. Keep the AI assistant outside the OpenStack control plane and isolated from privileged services.
3. Allow the assistant to inspect project-level OpenStack resources using dedicated read-only credentials.
4. Support operator-level diagnostics only through separately scoped read-only credentials or restricted SSH rules.
5. Convert recurring troubleshooting actions into reviewed, narrow, read-only diagnostic tools.
6. Prevent the AI from running arbitrary shell, OpenStack CLI, SSH, sudo, file, database, or remediation commands.
7. Capture structured tool results, failures, timeouts, and audit logs for trust and repeatability.
8. Support known lab troubleshooting workflows, especially metadata, Neutron, Nova, VM boot, volume, and service-health diagnostics.
9. Fit the existing OpenStack Lab topology, management network model, observability stack, and validation mindset.
10. Create a path from manual diagnostics to MCP integration without weakening the safety model.

## Non-Goals / Out of Scope

1. Autonomous remediation is out of scope. The assistant may recommend manual remediation but must not execute it.
2. Generic shell execution by the AI is out of scope.
3. Generic SSH execution by the AI is out of scope.
4. Generic OpenStack CLI passthrough is out of scope.
5. Admin OpenStack credentials, root SSH, unrestricted sudo, database credentials, and RabbitMQ credentials are out of scope for AI tool access.
6. Installing the AI agent on the OpenStack controller or any control-plane node is out of scope.
7. Running a local LLM on the assistant VM is not required for the first implementation.
8. Full production-grade AIOps automation, self-healing, anomaly detection, predictive scaling, or automated change management is out of scope.
9. Exposing an unauthenticated network MCP server is out of scope.
10. Replacing existing Ansible deployment and Molecule validation workflows is out of scope.

## User Stories

1. As a lab operator, I want an AI assistant that can inspect OpenStack state without changing it, so that I can troubleshoot safely.
2. As a lab operator, I want the assistant to run from a separate VM, so that control-plane services are not exposed to AI runtime risk.
3. As a lab operator, I want the assistant VM to reach Keystone and other internal endpoints, so that it can gather useful operational facts.
4. As a lab operator, I want read-only OpenStack credentials, so that diagnostic commands cannot create or delete cloud resources.
5. As a lab operator, I want mutation attempts to fail with authorization errors, so that I can prove the safety boundary works.
6. As a lab operator, I want a project-resource summary, so that I can quickly understand which servers, networks, subnets, volumes, and images exist.
7. As a lab operator, I want server basic info by name or ID, so that I can inspect status, image, flavor, networks, config drive, and availability zone.
8. As a lab operator, I want server network info, so that I can inspect ports, fixed IPs, networks, subnets, and related metadata debugging context.
9. As a lab operator, I want Neutron agent health diagnostics, so that I can identify down or unhealthy network services.
10. As a lab operator, I want recent Nova errors, so that I can identify API, scheduler, compute, or metadata issues.
11. As a lab operator, I want recent Neutron errors, so that I can identify DHCP, L3, metadata, or OVS issues.
12. As a lab operator, I want recent metadata errors, so that I can debug cloud-init and `169.254.169.254` failures.
13. As a lab operator, I want diagnostic scripts to use JSON where practical, so that AI and tooling can parse results reliably.
14. As a lab operator, I want log collection to be time-bounded and size-bounded, so that outputs stay useful and do not leak excessive information.
15. As a lab operator, I want the AI to choose from named diagnostic tools, so that it cannot invent unsafe commands.
16. As a lab operator, I want a deny-by-default tool allowlist, so that unknown or unsafe requested actions are rejected.
17. As a lab operator, I want tool parameters validated, so that command injection and accidental malformed inputs are blocked.
18. As a lab operator, I want host inputs restricted to known lab nodes, so that SSH-based diagnostics cannot be redirected arbitrarily.
19. As a lab operator, I want each tool call to have a timeout, so that stuck APIs or unreachable nodes do not hang the assistant.
20. As a lab operator, I want each tool result to include stdout, stderr, exit code, status, duration, and truncation metadata, so that failures are diagnostic.
21. As a lab operator, I want audit logs for every allowed and denied tool request, so that I can review what the assistant inspected.
22. As a lab operator, I want the assistant to explain likely failure domains, so that I can decide the next manual action.
23. As a lab operator, I want the assistant to refuse direct fix execution, so that “fix it” requests do not mutate the lab.
24. As a lab operator, I want separate project-reader and operator-reader profiles, so that higher-visibility diagnostics are not used by default.
25. As a lab operator, I want SSH-based log tools to depend on restricted SSH and sudo rules, so that host-level visibility does not become host-level control.
26. As a lab operator, I want secrets redacted from collected config snippets and logs, so that read-only diagnostics do not expose sensitive material unnecessarily.
27. As a lab operator, I want MCP tools only after scripts are trusted manually, so that protocol integration does not hide unsafe behavior.
28. As a lab operator, I want MCP resources for runbooks and architecture notes, so that the AI reasons with lab-specific context.
29. As a lab operator, I want MCP prompts for repeatable workflows, so that metadata, VM boot, network, and volume diagnostics follow consistent steps.
30. As a lab maintainer, I want AI-OPS to preserve existing Ansible and Molecule workflows, so that the lab remains understandable and testable.
31. As a lab maintainer, I want diagnostics aligned with existing service placement, so that tools query the right controller, compute, storage, Ceph, and observability locations.
32. As a lab maintainer, I want credential and permission behavior documented, so that future tools do not accidentally require admin access.
33. As a lab maintainer, I want static checks that scripts contain no mutation commands, so that the toolbox remains read-only.
34. As a lab maintainer, I want wrapper tests for denied tools and invalid parameters, so that safety behavior does not regress.
35. As a lab maintainer, I want end-to-end read-only diagnostic tests against a deployed lab, so that AI-OPS proves useful on real OpenStack state.
36. As a lab learner, I want to start manually before using MCP, so that I understand every safety layer before automating AI tool calls.
37. As a lab learner, I want troubleshooting output to be structured into clear sections, so that I can learn how OpenStack evidence connects.
38. As a security-conscious operator, I want no admin-openrc, root SSH, database password, RabbitMQ password, or unrestricted sudo available to the assistant, so that compromise blast radius is limited.
39. As a security-conscious operator, I want read-only credentials protected with strict file permissions, so that topology and resource visibility are not exposed casually.
40. As a future operator, I want the assistant to be extensible with new diagnostics, so that additional OpenStack services can be covered without weakening the safety model.

## Functional Requirements

FR-001. The system shall use a dedicated AI assistant VM or equivalent isolated runtime that is not part of the OpenStack control plane.

FR-002. The assistant runtime shall be able to reach required management endpoints such as Keystone and selected observability services.

FR-003. The assistant runtime shall not require tenant-network placement for the initial implementation.

FR-004. The assistant runtime shall install or provide Python, OpenStack CLI, OpenStack SDK, SSH client, curl, JSON tooling, log-search tooling, and version-control tooling needed for diagnostics.

FR-005. The system shall use a dedicated OpenStack identity for AI diagnostics rather than reusing human admin credentials.

FR-006. The default OpenStack credential shall be project-scoped read-only where the OpenStack policy model supports it.

FR-007. The system shall support a separate operator-read-only credential for higher-visibility diagnostics when project-reader access is insufficient.

FR-008. The system shall store OpenStack credential configuration with restrictive file permissions.

FR-009. The system shall validate that read commands work with the read-only credential.

FR-010. The system shall validate that create, update, and delete commands fail with the read-only credential.

FR-011. The system shall provide an approved diagnostic script for project resource summaries.

FR-012. The system shall provide an approved diagnostic script for server basic information.

FR-013. The system shall provide an approved diagnostic script for server network information.

FR-014. The system shall provide an approved diagnostic script for Neutron agent health when a safe operator-reader credential is available.

FR-015. The system shall provide approved diagnostic scripts for recent metadata, Nova, and Neutron errors when restricted SSH/log access is available.

FR-016. Each diagnostic script shall perform only read-only operations.

FR-017. Each diagnostic script shall validate user-supplied parameters before execution.

FR-018. Diagnostic scripts shall prefer structured output such as JSON for OpenStack API data.

FR-019. Diagnostic scripts shall bound log collection by time, line count, or output size.

FR-020. Diagnostic scripts shall avoid exposing full secret-bearing configuration files.

FR-021. Diagnostic scripts that inspect configuration snippets shall redact known secret-like keys.

FR-022. The system shall provide a tool allowlist that maps each public diagnostic tool name to exactly one approved implementation.

FR-023. The tool runner shall reject any requested tool that is not present in the allowlist.

FR-024. The tool runner shall reject generic shell, SSH, sudo, OpenStack CLI passthrough, file read/write, database query, and remediation tools.

FR-025. The tool runner shall validate every tool parameter against declared type, required status, pattern, range, or allowlist rules.

FR-026. The tool runner shall execute scripts using argument-vector execution rather than shell-string execution.

FR-027. The tool runner shall enforce per-tool timeouts.

FR-028. The tool runner shall enforce output-size limits and indicate when output is truncated.

FR-029. The tool runner shall return structured result envelopes for successful, failed, denied, timed-out, and truncated tool calls.

FR-030. The tool runner shall audit every allowed tool call.

FR-031. The tool runner shall audit denied tool requests and validation failures.

FR-032. The AI instruction layer shall state that the assistant is diagnostic-only and must not request mutation.

FR-033. For “fix it” requests, the assistant shall collect read-only diagnostics and provide manual recommendations rather than executing remediation.

FR-034. The first usable workflow shall support manual tool selection and copy-paste output analysis before automatic AI tool calling is required.

FR-035. The second workflow shall support local wrapper execution through named diagnostic tools.

FR-036. The later MCP workflow shall expose the same approved diagnostic capabilities as MCP tools without adding generic command execution.

FR-037. The MCP server shall expose only reviewed tools from the diagnostic allowlist.

FR-038. The MCP server shall support read-only resources for lab runbooks, architecture notes, and safety policies.

FR-039. The MCP server should support prompts for repeatable diagnostic workflows such as metadata troubleshooting.

FR-040. The system shall preserve existing OpenStack Lab deployment, bootstrap, observability, and validation workflows.

## Non-Functional Requirements

NFR-001. Security: The assistant shall follow least privilege across network reachability, OpenStack credentials, SSH access, sudo access, and tool exposure.

NFR-002. Security: The assistant shall be deny-by-default; no capability is available unless explicitly reviewed and allowed.

NFR-003. Security: The assistant shall not possess admin OpenStack credentials, root SSH, unrestricted sudo, database credentials, RabbitMQ credentials, or unrestricted control-plane file access.

NFR-004. Security: Secrets must not be logged in audit entries, tool outputs, or diagnostic summaries.

NFR-005. Reliability: Tool calls must fail safely with structured error states rather than hanging or falling back to unsafe execution.

NFR-006. Reliability: The system must tolerate missing optional capabilities, such as operator-reader access or SSH log access, by reporting unavailable diagnostics clearly.

NFR-007. Observability: Every allowed and denied tool call must be auditable with timestamp, tool name, sanitized arguments, status, and duration.

NFR-008. Usability: Tool names and descriptions must express diagnostic intent rather than implementation details.

NFR-009. Usability: Outputs must be concise enough for AI reasoning and human review.

NFR-010. Maintainability: New diagnostic tools must be added through the same allowlist, validation, timeout, output-limit, and audit model.

NFR-011. Maintainability: The implementation should start with simple scripts and evolve toward SDK-backed tools only where that improves structure and testability.

NFR-012. Compatibility: The system must fit the current management-network, node-role, service-placement, and observability architecture of the lab.

NFR-013. Compatibility: The system must account for OpenStack policy differences across versions and deployments.

NFR-014. Performance: Common OpenStack API diagnostics should normally complete within short per-tool timeouts.

NFR-015. Performance: Log diagnostics should avoid unbounded scans and should default to recent windows.

NFR-016. Operational Safety: MCP exposure must not be publicly reachable without additional authentication and network controls.

NFR-017. Learning Value: The system should keep each safety boundary understandable and inspectable for a lab learner.

## Implementation Decisions

1. The AI assistant shall be a separate observer runtime rather than software installed directly on the controller, compute, storage, or Ceph nodes.
2. The initial assistant runtime shall be a tool/connector host, not necessarily the machine that runs the LLM.
3. The initial network placement shall prioritize management endpoint reachability rather than tenant-network access.
4. OpenStack API access shall use a dedicated read-only identity.
5. Application credentials are preferred for automation when supported by Keystone.
6. The default credential shall be project-scoped reader for tenant resource inspection.
7. A separate operator-reader credential may be introduced for service and agent visibility when required.
8. The credential model shall be empirically validated because OpenStack secure RBAC behavior can vary by release and policy configuration.
9. Read-only OpenStack API scripts shall be created before any AI or MCP integration.
10. Shell scripts are acceptable for the first learning-oriented diagnostic toolbox because they are easy to inspect.
11. Higher-value diagnostics may later migrate to Python/OpenStack SDK functions for stronger structured output and testability.
12. The initial script set shall focus on project resource summaries, server basics, server networking, Neutron agent health, and recent Nova/Neutron/metadata errors.
13. SSH-based diagnostics shall be treated as higher sensitivity than OpenStack API diagnostics.
14. SSH-based diagnostics shall require a restricted observer user and restricted sudo command set before being exposed to AI tooling.
15. The AI shall not execute arbitrary commands; it shall choose named diagnostic tools.
16. A tool runner shall act as the gatekeeper between AI requests and script execution.
17. The tool runner shall execute fixed scripts only from an allowlist.
18. Parameter validation shall be enforced by the tool runner and scripts.
19. Tool execution shall use argument arrays, not shell string interpolation.
20. Tool results shall use structured envelopes that include status, exit code, stdout, stderr, duration, and truncation metadata.
21. Audit logging shall record allowed calls, denied calls, validation errors, timeouts, and failures.
22. MCP shall be introduced only after the manual and wrapper workflows are understood and trusted.
23. MCP shall expose diagnostic tools, read-only resources, and repeatable prompts, not command-execution primitives.
24. MCP resources may expose lab architecture notes, troubleshooting runbooks, and safety policies as context.
25. MCP prompts may encode workflows such as metadata issue diagnosis, VM boot diagnosis, Neutron connectivity diagnosis, and volume attach diagnosis.
26. Assumption: the assistant VM will be managed as a lab component using the repository’s existing documentation and validation style, even if its first implementation is not fully Ansible-managed.
27. Assumption: observability integrations may later use OpenSearch, Prometheus, or Grafana data sources, but initial diagnostics can begin with OpenStack API and log scripts.

## Existing System Fit

The OpenStack Lab already has a staged architecture: local virtualization creates base nodes, Ansible deploys infrastructure services, OpenStack bootstrap creates tenant resources, optional observability services collect metrics/logs, and Molecule validates inventory and deployed runtime behavior.

AI-OPS should fit beside this model as an operator-facing diagnostic layer. It should not replace Vagrant, Ansible, OpenStack bootstrap, observability deployment, or Molecule validation. Instead, it should consume the same service topology and operational facts that current runbooks describe.

Existing behavior to preserve:

- Controller, compute, storage, and Ceph node roles remain unchanged.
- Management network remains the primary internal operations path.
- Provider and tenant networks remain separate from AI assistant default placement.
- OpenStack metadata path remains guest to Neutron metadata proxy to Nova metadata API.
- Existing OpenStack, Ceph, observability, CI/CD, and Kubernetes workflows remain operator-driven through the current automation.
- Existing Molecule validation and smoke/e2e tests remain the primary project quality gates.

Existing patterns to reuse:

- Documented stage validation after major deployment phases.
- Read-only smoke verification where possible.
- Clear separation between OpenStack, Ceph, observability, CI/CD, Kubernetes, and shared resources.
- Troubleshooting notes that capture incident evidence, root cause, fix, and validation.

Compatibility concerns:

- The lab currently has lab-friendly security defaults and documented plaintext credential risks; AI-OPS must not amplify those risks.
- Some OpenStack reader-role behavior may depend on policy configuration and must be tested rather than assumed.
- Operator diagnostics such as hypervisors, compute services, and Neutron agents may require broader read-only scope than project diagnostics.
- SSH-based diagnostics must account for service placement and node-specific log locations.

## Data and API Contracts

### Credential Profiles

The system should support named cloud profiles with these logical contracts:

- Project reader profile: project-scoped, read-only, default for server, network, subnet, port, volume, image, and security group inspection.
- Operator reader profile: broader read-only scope for service, hypervisor, agent, and cloud-health views when supported and required.
- SSH observer profile: restricted host-level log and status access through a dedicated observer user and allowlisted read-only sudo commands.

### Tool Registry Contract

Each approved tool definition should declare:

- tool name
- description
- implementation target
- argument schema
- required and optional arguments
- validation patterns or allowlists
- credential profile
- risk classification
- timeout
- output-size limit
- mutation guarantee

### Tool Result Contract

Each tool call should return a structured envelope with:

- tool name
- status: ok, error, denied, timeout, validation_error, or unavailable
- sanitized target or arguments
- exit code when applicable
- stdout or structured data
- stderr or error message
- duration
- truncation flag
- timestamp or correlation identifier

### Audit Event Contract

Each audit event should include:

- timestamp
- actor or client identifier when available
- event type
- requested tool name
- sanitized arguments
- status
- duration when executed
- denial or failure reason when applicable

Audit logs must not include credential secrets, tokens, passwords, or full secret-bearing configs.

### MCP Contract

MCP tools should mirror the approved diagnostic tool registry. MCP resources may expose static runbooks and architecture context. MCP prompts may define repeatable diagnostic workflows. MCP must not add any capability that bypasses the allowlist, validation, timeout, output-limit, credential, and audit controls.

## UX / Workflow Notes

### Manual Diagnostic Workflow

1. Operator asks the AI what to inspect.
2. AI recommends approved diagnostic tools by name.
3. Operator runs the scripts or tool runner manually.
4. Operator pastes output into the AI conversation.
5. AI explains healthy signals, failing signals, likely failure domain, and manual next steps.

### Local Tool Runner Workflow

1. Operator or AI client requests a named diagnostic tool with parameters.
2. Tool runner validates the tool and parameters.
3. Tool runner runs the fixed implementation with timeout and output limit.
4. Tool runner returns a structured result.
5. AI explains the result.
6. Audit log records the request and outcome.

### MCP Workflow

1. AI client discovers approved MCP diagnostic tools.
2. AI chooses one or more tools based on the troubleshooting prompt.
3. MCP server validates and executes through the same safe tool runner model.
4. AI receives structured results directly.
5. AI explains findings and recommends manual remediation only when needed.

### Metadata Troubleshooting Example

For a cloud-init or `169.254.169.254` problem, the assistant should prefer a workflow that inspects server state, server network attachments, recent metadata logs, recent Neutron logs, recent Nova logs, and Neutron agent health where permitted. The expected output should distinguish guest-side symptoms, Neutron proxy behavior, Nova metadata availability, and host-level listener/log evidence.

## Testing Decisions

1. The highest practical test seam for the early implementation is workflow-level validation against a deployed lab using read-only diagnostics.
2. Existing Molecule runtime smoke and optional end-to-end validation should remain the main repository-level validation pattern for deployed OpenStack behavior.
3. New AI-OPS tests should verify external behavior and safety boundaries, not private implementation details.
4. Credential validation tests must prove read operations succeed and mutation operations fail.
5. Tool scripts should have static safety checks that reject create, update, delete, restart, stop, install, edit, redirect-write, unrestricted sudo, generic shell, and dangerous file operations.
6. Script tests should verify parameter validation rejects shell metacharacters and missing required inputs.
7. Script tests should verify JSON or sectioned output shape for successful diagnostics.
8. Wrapper tests should verify unknown tools are denied.
9. Wrapper tests should verify invalid parameters are denied before script execution.
10. Wrapper tests should verify script execution uses argument-vector behavior and does not invoke a shell string.
11. Wrapper tests should verify timeouts are enforced.
12. Wrapper tests should verify output truncation is reported.
13. Wrapper tests should verify audit events are written for allowed, denied, failed, timed-out, and validation-error outcomes.
14. MCP tests should verify only approved tools are registered.
15. MCP tests should verify generic shell, SSH, OpenStack CLI passthrough, sudo, file, and database tools are absent.
16. MCP tests should verify tool schemas enforce the same argument rules as the local wrapper.
17. Security tests should verify audit logs and result envelopes do not contain credential secret fields.
18. Integration tests should verify project-resource, server-basic, and server-network diagnostics against a deployed OpenStack Lab with project-reader credentials.
19. Integration tests for operator diagnostics should run only when operator-reader credentials are configured.
20. Integration tests for SSH log diagnostics should run only when restricted observer SSH and sudo rules are configured.
21. Regression tests should cover the documented metadata failure workflow by checking that diagnostics collect the evidence needed to distinguish Nova metadata API listener failures from Neutron agent failures.
22. Negative tests should verify that “fix it” intent does not result in remediation tool execution.

## Acceptance Criteria

AC-001. A dedicated assistant runtime exists separately from OpenStack control-plane nodes.

AC-002. From the assistant runtime, Keystone reachability can be verified.

AC-003. The default AI diagnostic credential can issue a token and list project-visible resources.

AC-004. The default AI diagnostic credential cannot create, update, or delete OpenStack resources.

AC-005. The initial diagnostic toolbox includes project resource summary, server basic info, and server network info.

AC-006. No initial diagnostic tool performs mutation.

AC-007. Every diagnostic tool validates its inputs.

AC-008. Log diagnostics, when enabled, use bounded recent output rather than unbounded file dumps.

AC-009. The tool allowlist denies unknown tool names.

AC-010. The tool runner has no generic shell, generic SSH, generic sudo, generic OpenStack CLI, file-write, database, restart, or remediation capability.

AC-011. The tool runner executes fixed implementations with argument-vector execution.

AC-012. Every tool has a configured timeout.

AC-013. Every tool has an output-size limit or bounded output behavior.

AC-014. Tool results include status, exit code when applicable, stdout/data, stderr/error, duration, and truncation state.

AC-015. Allowed, denied, failed, timed-out, and validation-error tool requests are audited.

AC-016. Audit entries do not include secrets.

AC-017. The assistant responds to remediation requests with diagnostic collection and manual recommendations rather than executing changes.

AC-018. MCP integration, when introduced, exposes only approved diagnostic tools.

AC-019. MCP integration, when introduced, does not expose generic command execution capabilities.

AC-020. Documentation explains the AI-OPS safety model, credential scopes, tool registry, audit model, and rollout path.

AC-021. A metadata troubleshooting workflow can be executed with read-only diagnostics and produce enough evidence to identify the likely failure domain.

AC-022. Existing OpenStack Lab deployment and validation workflows continue to work unchanged.

## Rollout / Migration Plan

1. Foundation: create or designate the assistant runtime, place it on or route it to the management network, and install base diagnostic tooling.
2. Credentials: create dedicated read-only OpenStack access, configure the default project-reader profile, protect credential files, and run read/mutation validation.
3. Manual diagnostics: create a small reviewed script set and run it manually from the assistant runtime.
4. Tool runner: introduce the allowlist wrapper with input validation, timeouts, output limits, structured results, and audit logging.
5. Restricted host diagnostics: add SSH/log tools only after observer SSH and restricted sudo rules are designed and validated.
6. MCP integration: expose the trusted tool registry as MCP tools, add read-only resources and prompts, and test with low-risk OpenStack API diagnostics first.
7. Expansion: add more diagnostics gradually, starting with common OpenStack workflows and only after each tool passes safety, validation, and audit checks.
8. Rollback: disable the tool runner or MCP server, remove assistant credentials, and revoke application credentials if any safety concern appears.
9. Monitoring during rollout: review audit logs, denied requests, timeout rates, output truncation rates, and credential authorization failures.

## Risks and Open Questions

### Confirmed Risks

1. Existing lab documentation identifies plaintext credential risks; AI-OPS must not reuse or further expose those credentials.
2. OpenStack reader-role and scope enforcement can vary by release and policy configuration.
3. SSH-based diagnostics can become dangerous if sudo rules are too broad.
4. MCP can make unsafe tools easier to call if the allowlist is poorly designed.
5. Large logs can overwhelm AI context and leak unnecessary information if not bounded and redacted.
6. Operator-level diagnostics may reveal infrastructure topology and hostnames even when read-only.

### Assumptions

1. The first AI-OPS implementation will use the assistant runtime as a tool host and will not require a local LLM.
2. Project-reader diagnostics are sufficient for the first useful manual workflow.
3. Operator-reader and SSH-based diagnostics can be added later without blocking the initial safe prototype.
4. The lab operator will accept manual copy-paste workflow before MCP automation.
5. OpenSearch, Prometheus, and Grafana integrations can be deferred until the OpenStack API/log diagnostic path is working.

### Open Questions

1. Where exactly should the assistant VM run: inside OpenStack, outside OpenStack on the lab hypervisor, or on another machine routed to management?
2. Which management endpoints should be reachable in the first milestone beyond Keystone?
3. Which OpenStack project should the project-reader credential target initially?
4. Does the current OpenStack policy configuration fully support project-scoped reader behavior for the desired resources?
5. What restricted sudo commands should be allowed for the observer SSH user?
6. Which AI client will consume the MCP server first?
7. Should the assistant runtime itself be provisioned by the repository’s existing automation in the first release or documented manually first?

## Further Notes

The central design principle is defense in depth: AI instructions guide behavior, tool schemas describe safe use, the allowlist blocks unknown requests, input validation blocks malformed parameters, fixed scripts block arbitrary command construction, read-only credentials block OpenStack mutation, restricted SSH/sudo blocks host mutation, and audit logs preserve traceability.

The first useful product milestone is not a fully autonomous AI operator. It is a safe, repeatable diagnostic toolbox that can answer: what exists, what is healthy, what is failing, which failure domain is likely, and what manual action should a human consider next.
