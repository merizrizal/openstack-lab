# PRD: Read-Only Go OpenStack Investigation and Orchestration Assistant

Status: Draft for product and architecture review. This document defines the intended end-product; it is not an implementation approval or evidence of deployed safety. Unresolved product decisions below require an owner decision before affected work is approved.

## Problem Statement

OpenStack Lab operators need to investigate incidents whose evidence spans tenant resources, compute scheduling, network attachments, metadata delivery, storage, service health, and host logs. A collection of safe diagnostic commands helps collect facts, but still leaves the operator responsible for planning the investigation, tracking dependencies, remembering failed approaches, correlating evidence, and deciding whether the final explanation is actually supported.

The desired product turns an operator's diagnostic goal into a bounded, inspectable investigation: understand the goal, propose a plan, collect permitted evidence, retain progress, consult relevant runbooks, review findings, and produce a traceable report. It must remain useful when evidence or permissions are incomplete and must never turn a troubleshooting request into an infrastructure change.

For the maintainer and learner, the system must also make the distinction between probabilistic model suggestions and deterministic application control visible. The end-product is a reliable engineering system around a model, not simply a chatbot, a toolbox exposed through MCP, or a collection of agents conversing without accountable workflow ownership.

## Source Materials

1. **[AI-OPS baseline learning roadmap](aiops-baseline.md)** — conceptual source for structured output, application-owned tool execution, bounded agent loops, state and memory, retrieval, workflows, dependency graphs, optional specialist agents, evaluation, guardrails, observability, and deployment. Its examples are educational, not an approved infrastructure capability list.
2. **Existing Go AI-OPS application** — contains model interfaces, agent runtime, file-backed investigation memory, knowledge loading, task engine, planning validation and approval, server-incident workflow, and project CLI wiring. It establishes partial implementation, not production readiness.
3. **OpenStack Lab deployment and validation workflows** — provide the lab context and validation approach. Deployed behavior has not been verified for this PRD.

The read-only OpenStack requirements and exclusions are stated in this document. Educational examples of code modification, deployment tasks, read-only database queries, and approval of writes do not override those exclusions.

## Baseline Alignment and Learning Scope

The [AI-OPS baseline](aiops-baseline.md) supplies the conceptual progression; this PRD translates it into observable behavior for a read-only OpenStack investigation product. The mapping below uses the final Stage 0–14 list in [Our practical curriculum](aiops-baseline.md#our-practical-curriculum), which separates observability, MCP, and deployment from the earlier combined production-engineering stage.

### Product traceability

These references describe intended product coverage, not verified implementation or learner achievement. Stage numbers are not release milestones or a required implementation order. Safety applies from the first executable slice, and optional technologies do not become mandatory merely because they appear in the curriculum.

| Stage | Baseline concept | Product coverage | Acceptance / disposition |
| --- | --- | --- | --- |
| 0 | Mental model of AI engineering | Product vocabulary; User Story 31; separation of model proposals from application authority | Inspectable concepts support learning; lessons and learner assessment are outside product acceptance. |
| 1 | LLM application fundamentals | FR-031–FR-034: bounded model interfaces, disclosure, isolation, and degraded operation | AC-016–AC-018 verify runtime contracts, not mastery of LLM fundamentals. |
| 2 | Structured output | FR-004, FR-007, FR-031: validated plans and control-flow responses | AC-001, AC-003, AC-016. |
| 3 | Tool calling | FR-010–FR-011, FR-023–FR-024, FR-027: authorized, reviewed calls and structured results | AC-004, AC-012, AC-014. |
| 4 | Agent loop | FR-008–FR-009, FR-040: bounded decisions, application-owned transitions, and stop reasons | AC-003, AC-022. |
| 5 | Context, state and memory | FR-014–FR-016; NFR-004: checkpoints, resume, provenance, and distinct memory classes | AC-007–AC-008. |
| 6 | RAG and external knowledge | FR-017–FR-018: curated retrieval, citations, and untrusted-content handling | AC-009; lexical retrieval first, with advanced retrieval justified by measured need. |
| 7 | Workflow orchestration | FR-005, FR-009, FR-012, FR-020: approved workflows, deterministic control, and evidence review | AC-001, AC-005, AC-010. |
| 8 | Project/task orchestration | FR-006, FR-013: validated dependency graphs and per-target project synthesis | AC-003, AC-006. |
| 9 | Multi-agent systems | FR-036: optional restricted specialist roles under orchestrator control | AC-020; remain disabled unless evaluation demonstrates value over the single-agent baseline. |
| 10 | Evaluation | FR-037–FR-038: versioned offline scenarios and quality/resource measurements | AC-021, AC-025. |
| 11 | Guardrails and human approval | FR-005, FR-010, FR-021–FR-030, FR-032–FR-033: exact approval, least privilege, policy, audit, and disclosure | AC-004, AC-011–AC-017; approval never permits infrastructure mutation. |
| 12 | Observability, cost and reliability | FR-039–FR-040; NFR-003–NFR-009: correlated events, finite budgets, recovery, and honest usage reporting | AC-007, AC-014, AC-022, AC-025. |
| 13 | MCP and integration architecture | FR-035; NFR-010: interoperability over the same reviewed tool and knowledge contracts | AC-012, AC-019, AC-024; introduce MCP after direct execution is validated. |
| 14 | Production deployment | FR-041–FR-042; NFR-014: readiness, protected operation, recovery, and rollback | AC-023–AC-025; deployment administration stays outside the diagnostic agent. |

The baseline's generic coding, deployment-task, database-query, and write-approval examples are educational illustrations, not additional product capabilities. The Non-Goals and read-only boundary continue to govern. Likewise, specialist distribution, vector databases, embeddings, parallel scheduling, and network service exposure require their existing justification and review rather than curriculum-driven expansion.

### Learning-plan boundary

Lessons, exercises, demonstrations, and learner assessments belong in a separate learning plan, not in this product acceptance contract. That plan should use the same progressively developed investigation project and include a genuine Stage 0 lesson on models, LLMs, agents, tokens, context windows, inference, prompts, tool calling, and deterministic versus probabilistic control. Product vocabulary alone does not satisfy that lesson.

The learning plan should define stage-specific learning outcomes, exercises, and evidence of understanding while reusing permitted product workflows and fixtures. It must not authorize excluded capabilities or live infrastructure access. Completing a lesson does not establish product acceptance; passing product tests does not establish learner mastery. This PRD neither creates that separate plan nor claims that the curriculum has been delivered.

### Diagnostic implementation form

The agent, orchestration, diagnostic tools, safety gateway, manual CLI, and enabled MCP interface shall be implemented primarily in Go and delivered as one runtime executable. Manual diagnostics use the same reviewed built-in tools and safety boundary before automatic tool calling or MCP is introduced. The runtime must not depend on separately deployed diagnostic scripts, interpreters, CLI tools, or model-client executables. Configuration, credentials, protected state, curated knowledge, and independently operated OpenStack, host, and model services are not part of the executable and remain subject to their own access controls.

One executable does not imply one security principal or process: any isolation needed to prevent model-facing components from accessing diagnostic credentials or bypassing the tool boundary must be independently enforced and verified. An isolation design that cannot meet these requirements is not acceptable.

Offline fixtures and model evaluations do not replace deployed-lab diagnostic validation. A deployed release needs authorized live project-reader evidence; operator-reader and host tests apply when those capabilities are enabled. Additional live/model evaluations remain separately selected, and no destructive probe against the working lab is authorized.

## Project Mode

**Existing Project with Partial Implementation.**

The repository already contains Go chat, structured-model, agent, knowledge-retrieval, workflow, project/task, and planning components.

The inspected Go project CLI composes server/flavor tools, file-backed state, lexical retrieval, a compute-focused investigation workflow, and reviewed plans. It does not establish complete coverage of network, storage, host diagnostics, evaluations, or the safety controls required below. Existing Go components must be assessed and verified rather than assumed complete.

## Solution

Build a CLI-first, read-only OpenStack investigation assistant around a deterministic orchestrator. The operator supplies a goal and explicit scope, inspects the proposed investigation, approves its exact scope and plan, and can follow, pause, inspect, or resume execution. The assistant selects only reviewed diagnostic capabilities and produces a report linked to observations and reference knowledge.

The product has five cooperating responsibilities:

1. **Model assistance:** interpret goals, propose structured decisions and plans, classify symptoms, and explain evidence.
2. **Agent runtime:** perform bounded observe/decide/request/observe loops within an assigned task.
3. **Workflow and project orchestration:** own task dependencies, validation, scheduling, approvals, budgets, checkpoints, retries, and final outcomes.
4. **Diagnostic safety boundary:** authorize each request and execute only reviewed read-only tools using the allowed credentials and resource scope.
5. **Evidence and operations:** preserve provenance, retrieve curated knowledge, review claims, measure quality and resource use, and support safe deployment and recovery.

Manual diagnostics remain available without a model. MCP provides interoperability over the same reviewed tools and curated knowledge; it is neither the orchestrator nor a replacement security boundary. A single capable agent is the baseline. Specialist investigator/reviewer roles may be added only when evaluation demonstrates a benefit; multiple processes or models are not prerequisites for an evidence-review step.

### Product vocabulary

- **Model:** inference component that produces text or structured proposals; it has no independent infrastructure authority.
- **Agent:** bounded decision loop assigned a goal and a restricted capability set.
- **Workflow:** application-defined sequence or branching process with validated transitions.
- **Orchestrator:** deterministic owner of execution, dependencies, state, limits, and approvals.
- **Investigation:** one diagnostic case, including its goal, approved scope, observations, hypotheses, and outcome.
- **Investigation project:** a coordinated set of diagnostic tasks, potentially covering several explicitly selected servers. It is not an OpenStack tenant project or a software-development project.
- **OpenStack project:** the tenant and authorization scope of cloud resources.
- **Evidence:** a timestamped observation with source, target, collection status, and provenance. Model-generated claims and historical summaries are not fresh observations.
- **Approval:** authorization for a specific diagnostic plan, scope, or disclosure; never permission to mutate the lab.

## Goals

1. Complete useful single-server and multi-server investigations with traceable, evidence-based findings.
2. Preserve the original read-only, least-privilege, isolated-observer safety model at every execution boundary.
3. Make planning, progress, missing evidence, task dependencies, and final outcomes inspectable.
4. Retain investigation context across interruptions without treating stale memory as current fact.
5. Use curated runbooks and architecture knowledge without granting retrieved content authority over tools or policy.
6. Measure diagnosis quality, tool selection, unsupported claims, safety, latency, and resource consumption.
7. Reuse and harden suitable Go application components and build reviewed diagnostic capabilities through explicit contracts.
8. Deliver an operable lab product with reproducible validation, rollback, and optional MCP/client integration.

## Non-Goals / Out of Scope

1. Infrastructure mutation, including restarts, configuration edits, installation, resource creation/deletion, or autonomous remediation. Human approval within this product cannot enable these actions.
2. General-purpose coding agents, repository editing, deployment execution, database querying, or unrestricted filesystem access by the model.
3. Generic shell, SSH, sudo, OpenStack CLI passthrough, or user-selected executable paths.
4. Admin cloud credentials, root SSH, unrestricted sudo, service/database/RabbitMQ credentials, or unrestricted control-plane file access in the diagnostic execution boundary.
5. Self-healing, predictive scaling, autonomous incident triggering, or continuous infrastructure surveillance in the initial release.
6. A mandatory multi-agent framework, distributed scheduler, vector database, or embeddings service. These require demonstrated need, not curriculum completion.
7. A web dashboard, public multi-tenant service, or external HTTP API in the first release. CLI and approved MCP clients are sufficient.
8. Local-model deployment, GPU procurement, model training, or a new provider-protocol gateway. A future local inference option requires separate operational approval.
9. Replacement of existing OpenStack deployment, Ansible, Vagrant, observability, or Molecule workflows.
10. Treating the educational roadmap's stage numbers as release milestones or evidence of product readiness.

Application-owned writes of checkpoints, audit events, indexes, and reports are permitted within a protected local data area. They do not authorize cloud/host mutation or expose a generic file-write tool to the model. Runtime installation and credential provisioning remain separate human-controlled operations.

## User Stories

1. As a lab operator, I want to describe an incident in natural language, so that I can start from the symptom rather than recall every diagnostic command.
2. As a lab operator, I want to select exact resource targets and cloud scope, so that the assistant cannot silently investigate unrelated resources.
3. As a lab operator, I want ambiguous server names rejected with clarification guidance, so that the wrong server is not inspected.
4. As a lab operator, I want a plan preview with dependencies and capability requirements, so that I understand what execution will do.
5. As a lab operator, I want approval tied to the exact plan, so that subsequent changes cannot reuse stale consent.
6. As a lab operator, I want to cancel a proposal without tool execution, so that review is not itself authorization.
7. As a lab operator, I want a bounded single-server investigation, so that routine incidents do not require unnecessary orchestration.
8. As a lab operator, I want a coordinated multi-server investigation, so that I can compare symptoms while preserving per-target evidence.
9. As a lab operator, I want task dependencies enforced by software, so that a summary cannot run before its required evidence tasks finish.
10. As a lab operator, I want visible progress and stop reasons, so that I can distinguish useful work from a stuck loop.
11. As a lab operator, I want to pause and resume an investigation, so that interruptions do not discard valid completed work.
12. As a lab operator, I want failed or blocked tasks identified separately, so that partial results are not presented as complete diagnosis.
13. As a lab operator, I want server status, fault, flavor, and network context, so that VM boot symptoms can be investigated coherently.
14. As a lab operator, I want a metadata investigation to distinguish Neutron proxy symptoms from Nova metadata availability, so that a healthy agent list does not create false confidence.
15. As a lab operator, I want unavailable operator/host diagnostics reported honestly, so that missing permissions never trigger privilege escalation.
16. As a lab operator, I want bounded host logs only from approved hosts, so that higher-visibility diagnostics remain controlled.
17. As a lab operator, I want runbook citations, so that I can inspect the reasoning context used in the report.
18. As a lab operator, I want old investigations labeled as historical, so that yesterday's explanation is not mistaken for today's state.
19. As a lab operator, I want observations, hypotheses, contradictions, and unknowns separated, so that I can judge the strength of a conclusion.
20. As a lab operator, I want findings reviewed against collected evidence, so that fluent but unsupported diagnoses are caught.
21. As a lab operator, I want remediation suggestions marked as manual actions, so that diagnosis never becomes an unapproved change.
22. As a security-conscious operator, I want every attempted tool call audited, so that allowed and denied behavior is inspectable.
23. As a security-conscious operator, I want outbound model context disclosed and sanitized, so that remote inference does not silently export sensitive lab data.
24. As a security-conscious operator, I want the model unable to bypass the diagnostic gateway, so that runtime features cannot evade tool restrictions.
25. As a lab operator, I want manual diagnostics without inference, so that provider outages do not remove the safe toolbox.
26. As an MCP client user, I want the same tool policy and result semantics as local execution, so that changing clients does not change safety.
27. As a maintainer, I want offline scenario evaluations, so that regressions can be detected without cloud credentials or paid model calls.
28. As a maintainer, I want usage and latency metrics per investigation, so that quality improvements can be weighed against cost and delay.
29. As a maintainer, I want explicit compatibility and migration checks, so that changes do not silently weaken the product's diagnostic safety contract.
30. As a maintainer, I want controlled deployment and rollback, so that a new agent version cannot compromise the lab's operation.
31. As a lab learner, I want inspectable state transitions and concise action explanations, so that I understand how deterministic software controls model decisions.
32. As a maintainer, I want optional specialist roles evaluated against a single-agent baseline, so that added orchestration complexity must justify itself.
33. As a lab operator, I want a project-resource summary, so that I can quickly understand which servers, networks, subnets, volumes, and images exist.
34. As a lab operator, I want server basic info by name or ID, so that I can inspect status, image, flavor, networks, config drive, and availability zone.
35. As a lab operator, I want server network info, so that I can inspect ports, fixed IPs, networks, subnets, and related metadata debugging context.
36. As a lab operator, I want Neutron agent health diagnostics, so that I can identify down or unhealthy network services.
37. As a lab operator, I want recent Nova errors, so that I can identify API, scheduler, compute, or metadata issues.
38. As a lab operator, I want recent Neutron errors, so that I can identify DHCP, L3, metadata, or OVS issues.
39. As a lab operator, I want recent metadata errors, so that I can debug cloud-init and `169.254.169.254` failures.
40. As a lab operator, I want diagnostic tools to use JSON where practical, so that AI and tooling can parse results reliably.
41. As a lab operator, I want the AI to choose from named diagnostic tools, so that it cannot invent unsafe commands.
42. As a lab operator, I want a deny-by-default tool allowlist, so that unknown or unsafe requested actions are rejected.
43. As a lab operator, I want tool parameters validated, so that command injection and accidental malformed inputs are blocked.
44. As a lab operator, I want audit logs for every allowed and denied tool request, so that I can review what the assistant inspected.
45. As a lab operator, I want the assistant to explain likely failure domains, so that I can decide the next manual action.
46. As a lab operator, I want the assistant to refuse direct fix execution, so that “fix it” requests do not mutate the lab.
47. As a lab operator, I want secrets redacted from collected config snippets and logs, so that read-only diagnostics do not expose sensitive material unnecessarily.
48. As a lab operator, I want MCP tools only after the built-in diagnostics are trusted manually, so that protocol integration does not hide unsafe behavior.
49. As a lab operator, I want MCP resources for runbooks and architecture notes, so that the AI reasons with lab-specific context.
50. As a lab operator, I want MCP prompts for repeatable workflows, so that metadata, VM boot, network, and volume diagnostics follow consistent steps.
51. As a lab maintainer, I want diagnostics aligned with existing service placement, so that tools query the right controller, compute, storage, Ceph, and observability locations.
52. As a future operator, I want the assistant to be extensible with new diagnostics, so that additional OpenStack services can be covered without weakening the safety model.

## Functional Requirements

All requirements describe target behavior, not verified current implementation. Conditional capabilities remain disabled until their documented prerequisites pass; disabling them must not hide required limitations from the operator.

### Entry, scope, and planning

FR-001. The CLI shall support manual named diagnostics, single-investigation execution, investigation-project planning/execution, state inspection, pause/cancellation, resume, and report export without requiring an MCP client.

FR-002. Each investigation shall retain the original goal, cloud/OpenStack project scope, explicitly selected resources, permitted capability/profile set, and execution budgets as application-owned data.

FR-003. Target selection shall accept canonical server UUIDs and supported exact names. Resolution shall reject ambiguous or missing matches, retain the original identifier and resolved identity, and provide UUID guidance when a downstream diagnostic has a narrower name contract.

FR-004. The planner shall return a validated structured disposition of ready, needs-input, or unsupported. Non-ready plans shall execute no diagnostic tasks and explain what prevents execution.

FR-005. Before a proposed project executes, the operator shall see its targets, tasks, dependencies, capability/profile requirements, limits, and expected outputs. Approval shall bind the validated plan and scope; cancellation, absent approval, or a changed plan shall prevent execution.

FR-006. Task graphs shall reject duplicate task IDs, missing dependencies, cycles, unsupported task types, and tasks outside approved scope before execution. The orchestrator shall execute only ready tasks whose required dependencies have succeeded.

### Agent and workflow execution

FR-007. Every model response used for control flow shall undergo structural and semantic validation. Invalid responses shall produce a bounded retry or explicit failure, never execution of free-form text.

FR-008. Agent loops shall request only registered tools and stop on completion, insufficient capabilities/evidence, repeated unproductive requests, cancellation, or exhausted budgets. Stop reasons shall be visible in persisted state and reports.

FR-009. The orchestrator, not the model, shall own task readiness, state transitions, retries, timeouts, approvals, and completion. Denials and invalid requests shall not be retried as transient failures or rerouted to stronger credentials.

FR-010. Before each tool call, the execution boundary shall revalidate the permitted cloud/project, resource target, capability, profile, and limits. This includes resumed calls and calls proposed by delegated roles; plan validation alone is insufficient.

FR-011. Related resources such as flavor, port, subnet, or host information shall be queried only through reviewed relationship rules derived from authorized observations and the approved visibility scope. A discovered relationship shall not automatically authorize broad cloud or host discovery.

FR-012. Workflows shall support server/boot investigation, metadata/network investigation, and bounded project-visible volume/attachment inspection. Unsupported subdiagnostics shall be identified explicitly rather than fabricated or replaced with arbitrary commands.

FR-013. Multi-server projects shall retain per-target results and produce a cross-task synthesis only after the required dependency outcomes are known. Failed or unavailable evidence shall prevent an unqualified successful diagnosis.

### State, memory, knowledge, and evidence

FR-014. The system shall checkpoint goals, scope, approval identity, task/step state, observations, hypotheses, errors, usage, and child-investigation links before and after significant execution transitions.

FR-015. Resume shall validate stored state and current policy, preserve completed work, and make interrupted or uncertain calls visible. An intentional re-observation shall create a new timestamped record rather than silently replacing prior evidence.

FR-016. The system shall distinguish recent observations, derived working summaries, historical investigation memory, and reference knowledge. Summaries shall retain evidence references; historical material shall never be promoted to fresh observations merely by retrieval.

FR-017. Retrieval shall search only curated, approved knowledge sources, return bounded relevant excerpts with stable source/chunk identity, and expose missing or stale knowledge as a limitation. An optional knowledge source may be unavailable without disabling permitted manual diagnostics.

FR-018. Goals, retrieved documents, logs, tool output, memories, and delegated reports shall be treated as untrusted content. Instructions in them shall not modify tool permissions, scope, approval, provider selection, or orchestration policy.

FR-019. Reports shall separate observed facts, interpretations, hypotheses, missing/contradictory evidence, and manual next steps. Material factual claims shall reference evidence or be labeled unverified; knowledge citations shall remain distinguishable from infrastructure observations.

FR-020. Before finalization, an evidence-review step shall check required evidence references, task coverage, collection failures, and unsupported claims. Review concerns shall cause bounded further investigation or an explicitly inconclusive/partial report, not invented confirmation.

### Diagnostic safety and access

FR-021. Diagnostic execution shall use an isolated observer runtime outside control-plane services, with only required management/API and separately approved host/observability reachability. Initial placement shall not require the tenant network.

FR-022. Project-visible tools shall use a dedicated project-reader identity by default. Operator-reader and restricted SSH-observer capabilities shall be separately configured, validated, and enabled; no permission failure shall trigger fallback to admin or another profile.

FR-023. Available tools shall be determined by a reviewed registry declaring argument schema, implementation, scope/profile, risk, availability prerequisites, timeout, and output bound. Unknown tools, extra/invalid arguments, arbitrary commands, and model-supplied executable locations shall be denied before execution.

FR-024. Diagnostic tools shall be implemented as reviewed Go capabilities within the runtime executable, exposing narrow read-only operations through the same authorization, validation, limits, and audit boundary. They shall not depend on separately deployed diagnostic executables or invoke arbitrary shell commands. Restricted host diagnostics remain subject to FR-026.

FR-025. The diagnostic catalog shall include approved read-only Go tools for project resource summaries (servers, networks, subnets, volumes and images where project-visible), server basic information including fault and flavor, and server networking, as well as project-visible volume/attachment evidence. Server basics should include image, networks, config drive, and availability zone when permitted; networking should include related ports, fixed IPs, networks, and subnets. An approved Neutron agent health tool shall be provided when a safe operator-reader credential is available; approved tools for recent Nova, Neutron, and metadata errors shall be provided when restricted SSH/log access is available. Higher-visibility diagnostics remain gated by validated access and enablement.

FR-026. Host diagnostics shall use approved host aliases, fixed diagnostic operations, restricted observer access and sudo where needed, and bounded recent windows/output. Caller-selected SSH destinations, log paths, commands, and unrestricted configuration dumps shall be rejected.

FR-027. Every tool request shall return a structured result distinguishing success, error, denial, invalid input, timeout, cancellation, and unavailable capability, with target, correlation ID, duration, safe payload/error details, and truncation metadata.

FR-028. Every allowed and denied request shall generate a sanitized audit record. If required authorization, audit, or execution-control infrastructure is unavailable, new diagnostic execution shall fail closed and the failure shall be visible locally.

FR-029. Secrets and prohibited sensitive fields shall be omitted or redacted before results enter model context, reports, persistent memories, exports, or telemetry. Security-sensitive data that cannot be safely transformed shall be withheld with an explicit limitation.

FR-030. Requests to fix, restart, edit, create, delete, or otherwise mutate the lab shall never invoke a mutation capability. For a “fix it” request, the assistant shall offer a separately scoped read-only diagnostic plan, collect permitted evidence within the approved scope and applicable authorization, and provide manual recommendations rather than executing remediation. If approval, access, or evidence is unavailable, it shall not execute unauthorized diagnostics and shall report the limitation.

### Model boundary and interoperability

FR-031. Model adapters shall expose a common bounded text/structured-output contract with cancellation, error reporting, and usage metadata. Provider-specific integration shall not own infrastructure execution.

FR-032. Remote inference shall require explicit authorization for the selected provider/model and permitted outbound data classes. Disclosure shall cover goals, observations, summaries, memory, and retrieved knowledge; changing the authorized destination or disclosure policy shall require renewed authorization.

FR-033. Model runtimes shall not possess cloud/SSH credentials or independent shell/file/network tools that can bypass the reviewed diagnostic boundary. Provider authentication shall remain opaque to diagnostic tools and reports.

FR-034. Provider failure or absent outbound approval shall stop model-dependent work safely while retaining local state inspection, reports, and permitted manual diagnostics. The application shall not silently switch providers.

FR-035. MCP integration shall expose only the enabled reviewed diagnostic subset, curated read-only resources, and diagnostic prompts. Calls shall preserve the same scope, validation, limits, redaction, audit, and result semantics as local execution; no protocol bypass is permitted.

FR-036. Optional specialist roles shall receive explicit tasks, restricted tools, bounded context/budgets, and structured evidence-linked outputs. The orchestrator shall own their dependencies and resolve conflicting outputs as review issues; agents shall not self-delegate unrestricted work.

### Evaluation and operation

FR-037. An offline evaluation harness shall run versioned incident fixtures with deterministic model/tool substitutes, record expected/actual behavior, and produce machine-readable results without cloud access or inference credentials.

FR-038. Evaluation results shall report task success, appropriate tool selection, unsupported factual claims, unnecessary tool calls, safety violations, elapsed time, and available token/cost data. A fixture-supported inconclusive result shall be scored separately from a fabricated diagnosis.

FR-039. Each run shall expose correlated project/task/investigation/tool/model events and usage, including retries, denials, timeouts, truncation, approval, and terminal outcome, without requiring hidden model reasoning traces.

FR-040. Operators shall be able to configure finite limits for task count, agent steps, tool calls, retries, elapsed time, context/output size, and available token/cost budgets. When exact provider usage is unavailable, conservative limits and explicit unknown usage shall replace false zero-cost reporting.

FR-041. Deployment shall provide startup checks for configured tools, profiles, stores, curated knowledge, enabled adapters, and policy/audit dependencies. Capabilities with unmet prerequisites shall be disabled or startup shall fail with actionable diagnostics according to their required/optional classification.

FR-042. Release operation shall include credential revocation/rotation procedures, protected data retention/export/deletion procedures, policy version identification, shutdown/recovery, and rollback to a validated configuration without modifying OpenStack workloads.

### Retained toolbox and manual-operation requirements

FR-043. The observer shall reach Keystone and other explicitly approved management endpoints without requiring tenant-network placement. The product's runtime capabilities shall be delivered in one Go executable without requiring separately installed diagnostic utilities, interpreters, or model-client executables. External infrastructure services, approved configuration, credentials, state, and curated knowledge remain separately managed prerequisites. Use a dedicated diagnostic identity, prefer Keystone application credentials when supported, protect credential files, and validate reader access and mutation denial against the actual release policy.

FR-044. Each diagnostic tool shall perform only read-only operations. Diagnostic implementations shall validate their inputs as well as passing gateway validation, prefer structured API output, avoid full secret-bearing configuration files, and redact secret-like fields in any permitted snippets. Logs shall default to a recent, bounded window and bounded output. Each public tool name shall map to one reviewed Go implementation for the selected version/configuration; callers cannot choose or override implementations.

FR-045. The AI instruction layer shall explicitly identify the assistant as diagnostic-only and prohibit mutation requests. This instruction is defense in depth, not an authorization boundary. Tool names and descriptions shall express diagnostic intent, not expose generic execution primitives.

FR-046. A first usable manual workflow shall support an operator selecting and running approved named diagnostics through the runtime CLI, and obtaining analysis of appropriately sanitized pasted output without automatic tool calling or MCP. Manual, automated, and MCP requests shall pass through the same reviewed authorization, validation, limits, redaction, and audit boundary with appropriately scoped credentials. Document safety boundaries, credential scopes, the registry, audit, and rollout. MCP follows manual and gateway validation and shall provide curated runbooks, architecture notes, safety policies, and repeatable diagnostic prompts subject to the same visibility and disclosure controls.

## Non-Functional Requirements

NFR-001. **Safety:** No agent/client path may bypass authorization at the actual tool boundary. The deterministic safety suite must record zero unauthorized executions, mutations, or secret disclosures.

NFR-002. **Least privilege:** Cloud credentials, host-observer credentials, provider authentication, and application state shall have separate access boundaries and restrictive permissions. Only explicitly required network routes shall be available.

NFR-003. **Bounded execution:** Every enabled call and run shall have finite documented limits. Deadline/cancellation tests shall verify cleanup of owned operations and resources and absence of later tool dispatch after termination.

NFR-004. **Persistence:** Checkpoints shall be atomically replaced or transactionally committed; corrupt, incompatible, or unsuccessfully persisted state shall not be reported as safely saved or resumable. Concurrent writers shall be serialized or rejected.

NFR-005. **Isolation:** Evidence, memory, knowledge visibility, and approvals shall be partitioned by authorized cloud/project and investigation scope. A shared resource name alone shall not authorize cross-project memory reuse.

NFR-006. **Reliability:** Tool calls shall fail safely with structured error states, finite bounds, and no unsafe execution fallback. Missing optional capabilities, including operator-reader and SSH/log access, shall result in capability degradation with explicit limitations. Required policy or audit failures shall stop new execution; provider availability shall not be required to inspect local results.

NFR-007. **Evidence quality:** Root-cause confirmation requires direct supporting evidence. Relevance scores, model confidence, reviewer agreement, and successful tool exit codes alone are not proof of a diagnosis.

NFR-008. **Observability:** Every allowed and denied tool request shall be auditable with timestamp, tool name, sanitized arguments, status, and duration; when execution does not occur, duration shall be explicitly marked not applicable rather than invented. Correlation and provenance shall survive planning, execution, review, resume, and export. Telemetry shall contain concise decisions and outcomes, not secrets or hidden chain-of-thought.

NFR-009. **Performance and cost:** Versioned evaluation reports shall publish per-scenario tool counts, latency distributions, and measured or explicitly unavailable usage/cost. Release-specific quality and latency thresholds must be agreed before model-enabled rollout; this PRD claims no measured SLA.

NFR-010. **Compatibility:** Manual CLI, automated Go, and MCP entry points shall preserve reviewed tool semantics or declare a versioned incompatibility. The product's manual diagnostics and the lab's deployment/validation workflows shall remain operable.

NFR-011. **Maintainability:** New tools and workflows shall supply contracts, safety classification, offline tests, and scenario coverage. Extension shall not require granting generic execution primitives.

NFR-012. **Privacy:** Redaction shall be supplemented by data minimization, disclosure approval, storage permissions, retention, and network egress enforcement. Outbound opt-in alone is not a redaction or firewall control.

NFR-013. **Usability:** Tool names and descriptions shall express diagnostic intent rather than implementation details. Outputs shall be concise enough for AI reasoning and human review without hiding evidence gaps or truncation. The CLI shall distinguish proposal from execution, operational completion from diagnostic confidence, and permission denial from healthy state. Machine-readable exports shall be versioned.

NFR-014. **Deployability:** The runtime shall be reproducibly installable and independently stoppable outside the control plane as one Go executable, with documented external service, configuration, credential, and data prerequisites and an offline validation path. Its runtime functions shall not require separately installed diagnostic utilities, interpreters, or model-client executables.

NFR-015. **Testability:** Core orchestration and safety tests shall not depend on a live cloud or nondeterministic provider. Optional live/model evaluations shall be explicitly selected and reported separately.

## Implementation Decisions

### Product decisions

1. The application, not the LLM, executes tools and controls workflows. Structured output is a proposal requiring deterministic validation.
2. Scope and permissions are execution-time constraints, not merely planner instructions. Approval and graph validation do not replace call-boundary checks.
3. A separate observer runtime, dedicated reader profiles, reviewed diagnostic tools, restricted host access, and auditability remain mandatory.
4. State, memory, retrieval, workflow, and orchestration are separate concepts. Persisted observations and application state are authoritative records; summaries and model recommendations are derived content.
5. The initial architecture uses a single-agent execution path with an evidence-review stage. Multi-agent distribution is an optional evaluated extension, not a condition of curriculum completion.
6. MCP is an adapter over established safety and knowledge contracts, introduced after direct execution is validated. Initial exposure should remain local/stdio; network exposure requires a separate authenticated transport and network-control review.
7. Remote inference is optional and separately authorized. Provider internals and authentication are not diagnostic capabilities.

### Proposed decisions and assumptions

1. **Assumption — Go product core:** Continue suitable existing Go CLI, agent, planner, workflow, and project orchestration components as the product core, subject to the single-executable and safety requirements.
2. **Assumption — diagnostic boundary ownership:** Define one authoritative policy and registry owner for the product; do not maintain independent permissive copies. All diagnostic implementations must meet the same safety contract.
3. **Assumption — local first:** Begin with a single-operator runtime, protected local persistence, and sequential ready-task scheduling. Database-backed persistence, parallel scheduling, and shared-service operation require separate concurrency and authorization decisions.
4. **Assumption — simple retrieval first:** Use curated text chunking and lexical retrieval unless measured retrieval failures justify embeddings, hybrid search, or reranking.
5. **Proposed hardening:** Normalize safe result envelopes across built-in Go tools and entry points, carry explicit scope through nested execution, and make persistence/audit failures visible. The current Go registry and workflow presence do not establish these guarantees.
6. **Proposed migration discipline:** Introduce contract versions and parity tests before changing product state or tool behavior; preserve a rollback path rather than silently converting historical records.

## Existing System Fit

| Existing area observed | Product fit | Readiness limitation |
| --- | --- | --- |
| Text and structured model interfaces | Potential inference boundary | Adapters must meet disclosure, isolation, cancellation, policy, and single-executable requirements; existing interfaces alone do not establish these guarantees. |
| Agent runtime with step limits, observations, summaries, and memory | Starting point for bounded investigations | Full scope confinement, budgets, persistence-failure handling, and scenario quality remain acceptance work. |
| File-backed investigation state and atomic file replacement | Local checkpoint foundation | Schema migration, concurrency, interrupted execution, and recovery require explicit contracts and tests. |
| Markdown/text chunks and lexical retrieval | Curated knowledge baseline | Discovery of files is not approval to ingest them; confidentiality, scope, stale content, and injection must be controlled. |
| Planner graph validation and exact-digest review | Reviewed project execution | Current plans are constrained to server investigations plus synthesis; arbitrary diagnostic DAGs are not established functionality. |
| Compute-focused server workflow | First domain workflow | Network/storage classifications currently report unsupported rather than implement those investigations. |

Preserve exact-name/UUID user intent, approval semantics, fail-closed identifier restrictions, the required manual workflow, and the lab's controller/compute/storage/management-network separation. Unsupported names must not be made acceptable by silently weakening input validation. Preserve service placement and the guest-to-Neutron-to-Nova metadata model.

## Data and API Contracts

These are logical target contracts, not declarations that the current persisted schemas already contain every field.

### Investigation and project

A versioned record contains an identifier, original goal, cloud/OpenStack project identity, explicit target set with resolved resource identities, allowed capability/profile set, policy/plan versions, approval digest, budgets, lifecycle status, timestamps, task/child links, evidence references, usage, and terminal reason.

Operational lifecycle distinguishes proposed, awaiting approval, running, paused, completed, failed, and cancelled. Diagnostic outcome independently distinguishes supported findings, partial findings, and inconclusive investigation. A completed process may have an inconclusive diagnosis; neither is a claim that the cloud is healthy.

Tasks contain stable IDs, reviewed types, target scope, dependencies, attempt count, status, outputs/evidence references, and error/stop reasons. Tasks distinguish pending, ready, running, paused, completed, failed, blocked, and cancelled. A dependency failure blocks dependent success; policy-defined partial reporting may still summarize that failure explicitly.

### Plan and approval

A plan contains disposition, explanation, tasks, dependencies, expected capabilities, scope, and budgets. Approval binds its canonical validated form and relevant policy identity. Scope expansion, target changes, or capability/profile changes invalidate approval. Resuming unchanged work still requires current authorization checks; expired or revoked access cannot be recovered from an old checkpoint.

### Tool definition, request, and result

A tool definition declares name/version, diagnostic intent, argument schema, fixed implementation mapping, required profile, scope/relationship rules, prerequisites, risk, timeout, output limit, and read-only guarantee.

A request carries correlation IDs, tool/version, validated arguments, and an application-controlled authorization context. Model arguments cannot supply or override credentials, implementation paths, policy, or approval state.

A result carries request/tool identity, status, sanitized targets/arguments, start/end or duration, structured data or bounded stdout, safe stderr/error, exit code when applicable, truncation/redaction indicators, and evidence references. Logical statuses are ok, error, denied, validation_error, timeout, cancelled, and unavailable. Truncation is metadata, not evidence of complete collection. Legacy adapters must document status translations.

### Observation, knowledge, and report

An observation records evidence ID, producing call/source, authorized target/scope, timestamp, collection status, and sanitized payload or protected payload reference. Derived claims contain supporting/contradicting evidence references and a verification classification.

Knowledge results contain source identity, document revision/content identity where available, section/chunk ID, bounded text, and relevance. Historical memory additionally records investigation provenance and observation time. Neither contract permits embedded instructions to become policy.

A report contains scope, plan/task coverage, observations, interpretations, hypotheses, gaps/contradictions, review findings, outcome, manual recommendations, knowledge citations, and usage/stop metadata. Missing or stale evidence remains visible in exports.

### Audit and model usage

Audit events contain event/correlation IDs, time, actor/client when known, policy/approval identity, tool and sanitized scope/arguments, decision, result status, duration, and safe denial/failure reasons. Event content must not contain credential values or full secret-bearing configurations.

Model events identify adapter/provider/model, request purpose, disclosure-policy identity, latency, attempts, and available input/output/cached-token usage. Costs are estimates with an identified pricing basis or explicitly unavailable, not silently zero. The model interface never returns executable authority.

## UX / Workflow Notes

### Normal investigation

1. Operator selects a cloud/project context and supplies a goal and explicit targets.
2. The application checks identifier/scope validity and configured capability readiness. Missing targets produce a clarification, not guessed resource discovery.
3. The model proposes a structured plan, or the operator chooses a reviewed workflow. Project proposals execute nothing until exact approval; any necessary target-resolution reads must be separately disclosed and scoped.
4. The orchestrator schedules approved ready tasks; the agent requests evidence through the safety boundary.
5. Progress shows concise action intent, task state, call outcome, and remaining limits. It does not expose hidden reasoning traces.
6. Evidence review checks claim support and gaps. Further collection, if needed, remains inside the approved scope and budget.
7. The final report gives findings, limitations, evidence, and manual next steps. The operator retains all change authority outside this product.

### Metadata and VM boot cases

For metadata failures, correlate server/network context with permitted Neutron/Nova/metadata evidence. Healthy agents do not establish that the Nova metadata listener is available. Missing host access must yield a named evidence gap rather than an inferred listener diagnosis.

For a NoValidHost symptom, use server faults and available flavor, scheduling, capacity, or Placement evidence only where reviewed tools and approved visibility exist. A fault string alone does not establish whether capacity, placement constraints, service availability, or another cause is responsible.

### Interruption and degraded operation

Cancellation stops new dispatch and bounds active calls. Resume shows completed, interrupted, and blocked work, rechecks policy, and requests renewed approval if scope changed. Evidence freshness is visible; refreshing a prior observation is explicit and audited.

Without inference access, operators can inspect state, read completed reports, and run permitted named diagnostics manually. Without optional host/operator access, the assistant completes only the supported portion and names the missing evidence.

## Testing Decisions

1. **Highest practical seam:** Execute a full CLI/orchestrator investigation against fake model responses and controlled tool/API fixtures. Assert approved targets, call sequence/permissions, persisted transitions, report evidence, and terminal outcome rather than private helper structure.
2. **Planner and approval:** Use structured fake clients and recording project starters. Cover needs-input/unsupported dispositions, malformed output, cycles, extra targets, changed plans, exact approval, cancellation, and exhausted planning retries.
3. **Execution scope:** Test a valid approved plan whose downstream agent requests a different server, cloud/project, host, or profile. Require denial at dispatch, including after resume and from specialist roles. Test legitimate related-resource reads separately.
4. **Gateway and adapter tests:** Use Go fixtures and CLI/MCP contract tests for unknown tools, invalid/extra arguments, caller-selected executables, timeout, cancellation, truncation, unavailable profiles, audit failures, and secret canaries. Require manual, automated, and MCP parity where they expose equivalent capabilities.
5. **State and recovery:** Exercise interruptions before dispatch, during a call, after a result but before checkpoint, and during finalization. Test corrupt/version-incompatible state, failed writes, concurrent resume, revoked approval/access, stale evidence, and visible replay decisions.
6. **Knowledge and memory:** Test source/chunk citation, no matches, inaccessible curated roots, stale/conflicting documents, scope isolation, oversized content, secret-bearing input, and prompt injection in retrieved text, observations, summaries, and prior reports.
7. **Evidence review:** Use known-supported, contradictory, incomplete, and fabricated claims. Deterministic checks validate reference existence and provenance; semantic review/evaluation assesses whether references actually support claims. Model self-review alone is not an oracle.
8. **Scenario suite:** Include healthy server, NoValidHost with sufficient evidence, NoValidHost with unavailable capacity tools, metadata listener failure, Neutron failure, volume-attachment symptom, permission denial, ambiguous name, missing resource, provider outage, hostile log content, and multi-server partial failure.
9. **Evaluation tiers:** Deterministic offline regression is mandatory. Optional model-backed evaluations use a versioned corpus/rubric and repeated runs with explicit provider approval. Live lab acceptance is separate and cannot be replaced by fixtures or educational milestone completion.
10. **Credential validation:** Demonstrate authorized reads and policy rejection of representative create/update/delete operations in an explicitly authorized disposable test scope. These tests are operator-controlled, not agent tools. Use preflight policy checks and disposable resources so an unexpected permission grant cannot damage the working lab; require explicit approval and a cleanup owner before live probes.
11. **Deployment validation:** Reuse existing automation and Molecule smoke patterns for readiness, profile isolation, management reachability, and read-only workflows. Before deployed release, verify project-resource, server-basic, and server-network diagnostics against the lab with project-reader credentials; test operator and SSH diagnostics when enabled and their restricted prerequisites are configured. Fault injection is optional and confined to disposable environments; reproducing an incident must not require inducing a working-lab outage.
12. **Release gates:** All deterministic authorization, mutation-denial, redaction, graph, approval, and recovery acceptance tests must pass. Pin the evaluation dataset, rubric, supported capability matrix, and agreed quality/latency/cost thresholds before model-enabled release; do not tune pass criteria after observing a release result.
13. **Toolbox defense in depth:** Review and statically check Go diagnostics for mutation operations, command injection, unsafe file operations, and unrestricted privilege; supplement static checks with behavioral tests because static checks alone cannot prove safety. Test tool inputs and structured output, and verify the gateway denies malformed inputs before dispatch.
14. **Single-executable deployment:** Build and exercise the runtime in a controlled environment without separately installed diagnostic utilities, interpreters, or model-client executables. Verify manual CLI, enabled model integration, enabled MCP, and permitted diagnostics against controlled fixtures. Separately validate real external service and host prerequisites for deployed acceptance. Demonstrate the independent enforcement of model/credential isolation; a single process or language boundary alone is not evidence.

## Acceptance Criteria

AC-001. A CLI workflow accepts an explicit goal/scope, previews a plan, and starts only after exact approval. Missing, cancelled, stale, and changed-plan approval fixtures execute no tasks. Covers FR-001–FR-006.

AC-002. Ambiguous names, missing resources, and unsupported tool identifiers yield clear guidance without inspecting an unintended target. Valid UUID and supported exact-name cases retain original and resolved identity. Covers FR-002–FR-003.

AC-003. Invalid structured decisions, unknown task types, cycles, missing dependencies, and repeated unproductive tool requests stop safely under finite limits. Covers FR-006–FR-009, FR-040.

AC-004. An approved in-scope plan followed by an out-of-scope nested, delegated, or resumed request is denied before tool execution and audited. Reviewed relationship fixtures permit only the corresponding authorized related reads. Covers FR-010–FR-011, FR-028, FR-036.

AC-005. Offline server/boot, metadata/network, and volume/attachment scenarios produce evidence-linked supported findings when required tools exist, and named limitations when they do not. Covers FR-012, FR-025.

AC-006. A multi-server project honors dependencies, preserves per-target evidence, and labels failed/blocked coverage without reporting an unqualified successful diagnosis. Covers FR-013.

AC-007. Checkpoint/resume tests preserve completed work, expose interrupted calls, reject corrupt or incompatible state, and surface failed writes and concurrent-writer conflicts. Covers FR-014–FR-015 and NFR-004.

AC-008. Context and exported reports distinguish observations, working summaries, historical memory, and reference knowledge; historical conclusions cannot satisfy fresh-observation expectations. Covers FR-016, FR-019.

AC-009. Retrieval returns bounded curated chunks with stable citations; unavailable knowledge and hostile/secret-bearing content do not broaden access or leak protected data. Covers FR-017–FR-018, FR-029.

AC-010. Evidence review detects missing references, contradictory evidence, and unsupported material claims in the fixture corpus, producing further bounded collection or an explicit inconclusive/partial report. Covers FR-019–FR-020.

AC-011. A deployment acceptance record demonstrates observer-runtime separation, required reachability only, dedicated reader profiles, and fail-closed unavailable optional profiles. Controlled authorization tests establish read success and mutation denial. Covers FR-021–FR-022 and NFR-002.

AC-012. Unknown tools, generic commands, extra/invalid arguments, caller-selected executables, and profile overrides are denied across manual CLI, automated, and MCP entry points. Contract tests show that only reviewed built-in Go diagnostics can execute through the boundary. Covers FR-023–FR-024, FR-035.

AC-013. Enabled host diagnostics accept only approved host/operation/window combinations and return bounded output. Missing observer prerequisites result in unavailable capability rather than fallback. Covers FR-026.

AC-014. Contract tests cover every result status, truncation, cancellation, safe errors, correlation, and required audit records, including timestamp, tool name, sanitized arguments, status, and duration or an explicit not-applicable value; audit failure prevents new execution. Covers FR-027–FR-028 and NFR-006, NFR-008.

AC-015. Secret-canary and remediation-request fixtures show no prohibited disclosures and no mutation execution, including when the operator asks the model to ignore restrictions. A “fix it” fixture produces a scoped diagnostic plan and manual recommendations, collects evidence only with required authorization, and reports missing access or approval without unauthorized execution. Covers FR-029–FR-030 and NFR-001.

AC-016. Each enabled model adapter passes structured-response, timeout, cancellation, and usage contract tests. No provider call occurs without the required destination/disclosure authorization. Covers FR-031–FR-032.

AC-017. Runtime inspection and negative tests demonstrate that model-facing components cannot obtain diagnostic credentials or use independent tools to bypass the safety boundary. The deployment demonstrates an independently enforced isolation boundary; a shared process or Go package boundary alone is insufficient. Covers FR-033 and NFR-002.

AC-018. A provider outage or revoked outbound approval preserves local state/report inspection and manual diagnostics, with no silent provider change. Covers FR-034.

AC-019. MCP discovery exposes exactly the approved enabled subset and curated resources/prompts; equivalent calls preserve local policy and result semantics. Covers FR-035.

AC-020. If specialist roles are enabled, scope/budget/context isolation and structured handoffs pass tests, and a versioned evaluation compares their quality, cost, and latency with the single-agent baseline. Otherwise the capability remains disabled. Covers FR-036.

AC-021. The offline evaluation suite runs without cloud/provider credentials and emits versioned scenario results for success, tool selection, unsupported claims, unnecessary calls, and safety. Covers FR-037–FR-038.

AC-022. Operators can correlate planning, task, model, tool, review, and resume events and inspect budgets/usage; missing usage is labeled unknown. Budget exhaustion and cancellation stop further dispatch. Covers FR-039–FR-040.

AC-023. Startup/readiness and rollback exercises verify required/optional capability behavior, credential revocation procedures, protected data lifecycle, and safe runtime shutdown without changing lab workloads. Covers FR-041–FR-042.

AC-024. The product's manual diagnostic paths and the lab's deployment-validation paths pass applicable regression checks; any adapter/state incompatibility is versioned and accompanied by an approved migration and rollback procedure. Covers NFR-010–NFR-011, NFR-014.

AC-025. Before model-enabled rollout, the release record identifies the capability matrix, evaluation corpus/rubric, agreed quality/latency/cost thresholds, passing deterministic safety results, required deployed-lab acceptance evidence, any additional optional live/model evaluation evidence, and unresolved limitations. No fixture result is represented as deployed validation. Covers NFR-007, NFR-009, NFR-015.

AC-026. The deployment record verifies Keystone reachability, project-reader token issuance and project-visible reads, and the required project-resource, server-basic, and server-network live diagnostics. It records representative mutation-denial results from an explicitly authorized disposable test scope; enabled operator and host capabilities have their own live prerequisite and diagnostic evidence. Covers FR-021–FR-022, FR-043.

AC-027. Approved read-only Go project-summary, server-basic, and server-network tools are included in the runtime and pass input, static, and behavioral safety checks. With validated and enabled operator-reader or restricted SSH/log access, the corresponding Neutron-agent or recent Nova, Neutron, and metadata error tools are available and pass those checks; without the prerequisites, those diagnostics report unavailable. API results are structured where practical, and enabled log tools default to bounded recent output. Covers FR-023–FR-026, FR-044.

AC-028. An operator can perform the documented manual selection, CLI execution, sanitized copy-paste, and analysis workflow without automatic tool calling or MCP. Manual, automated, and MCP calls pass the same applicable safety and audit checks. Documentation explains the shared boundary and credential scopes. Covers FR-001, FR-045–FR-046.

AC-029. A deployment validation record demonstrates that one Go runtime executable provides the manual CLI, enabled model integration, enabled MCP interface, and permitted built-in diagnostics without separately installed diagnostic utilities, interpreters, or model-client executables. It identifies external services and protected configuration/data prerequisites separately and includes the independent model/credential isolation evidence required by AC-017. Covers FR-024, FR-043, NFR-014.

## Rollout / Migration Plan

1. **Review and approve:** Review product scope, decide authoritative policy/registry ownership and independently enforceable isolation, and inventory relevant Go behavior before planning delivery. The single Go runtime executable remains required.
2. **Secure the core vertical slice:** Deliver explicit scope, one useful server investigation, exact-plan approval where applicable, execution-boundary authorization, structured results, audit/redaction, bounded model access, and an evidence-linked report. Require offline safety tests before any live use.
3. **Make investigations durable:** Harden checkpoint/resume, protected state, context summarization, curated retrieval, failure reporting, and provider-independent inspection. Validate compatibility with existing records before migration.
4. **Complete domain and project workflows:** Add metadata/network and volume evidence, dependency-aware multi-server execution, and evidence review. Run offline evaluation scenarios and record capability gaps.
5. **Enable gated integrations:** Validate operator-reader and restricted host access independently. Add MCP interoperability only over proven contracts; keep network MCP exposure and specialist agents disabled unless separately reviewed and justified.
6. **Release to the lab:** Use the existing automation/validation approach, pin runtime and adapter versions, perform authorized read-only acceptance, record quality/latency/cost baselines, and publish operational guidance. Deployment administration remains outside the diagnostic agent.
7. **Monitor and rollback:** Track denials, scope violations, incomplete reports, audit/checkpoint failures, timeouts, truncation, unsupported claims, and usage. On safety concerns, stop dispatch, disable affected adapters/tools, revoke credentials/outbound permissions, preserve protected evidence, and restore a validated runtime/configuration.

Do not migrate saved state in place without a versioned conversion and recovery procedure. The product's manual diagnostics should remain available during integration when their independent safety boundary is healthy. Optional specialist roles, parallelism, advanced retrieval, and network service exposure follow measured need rather than the order of a learning syllabus.

## Risks and Open Questions

### Risks and observed limitations

1. The baseline includes generic engineering and write-approval examples; they do not override this product's read-only OpenStack boundary.
2. Current Go workflow routing supports compute investigation and explicitly lacks other domain workflows. The broader catalog and workflows specified here are delivery requirements, not current capabilities.
3. The Go planner validates target scope, while the inspected generic tool registry dispatches by registered name without an explicit per-investigation scope parameter. Runtime confinement must be demonstrated end to end before release; planner validation is not sufficient evidence.
4. Identifier rules across tool implementations may differ. Compatibility requires explicit resolution and guidance, not unreviewed validation widening.
5. Runbooks and lab artifacts may contain sensitive configuration examples. Raw repository ingestion or unrestricted forwarding to a remote model is unsafe.
6. Current Go evidence is source inspection, not a fresh test run, deployment audit, or reader-policy validation.

### Assumptions requiring confirmation during design

1. Suitable existing Go components can be adapted to the single-executable runtime and the independently enforced safety boundary; their current presence does not prove this.
2. A single operator, local protected persistence, sequential scheduling, and a curated lexical knowledge index are sufficient initially.
3. Remote inference remains optional; model-enabled use can be gated independently from manual diagnostic availability.
4. Specialist roles are optional until measured value exceeds coordination, cost, latency, and security overhead.

### Open decisions

1. Which product component owns the diagnostic policy and tool registry, and how will the single-executable deployment independently enforce model/credential isolation and prevent tool-boundary bypass?
2. Which runtime placement, initial cloud/OpenStack project, reader policy configuration, host aliases, and approved management endpoints define the first acceptance environment?
3. Which related-resource reads are authorized for a server investigation, and how are project-wide summaries and host visibility separately approved?
4. Which initial inference adapter/provider/model is supported, what data may leave the lab, and what enforceable egress controls accompany disclosure approval?
5. What retention periods, maximum local data volume, evidence freshness windows, and export permissions apply?
6. What schema migration and interrupted-call recovery semantics are acceptable for the existing investigation/workflow/project stores?
7. What evaluated quality, latency, token/cost, and unnecessary-call thresholds define the first model-enabled release? These remain release blockers until agreed, not invented measurements.
8. Which initial MCP client and transport are required? Authenticated network exposure needs its own design if local/stdio is insufficient.
9. Which domain evidence requires new reviewed tools, especially scheduler/Placement capacity and volume attachment diagnostics, and which portions must remain unavailable under project-reader access?

## Further Notes

The product combines a safe diagnostic toolbox with stateful, evidence-driven investigation and task orchestration. Safety applies from the first executable slice, not only at a later curriculum stage.

The learning baseline supplies the concepts; this PRD supplies observable product requirements. Completion of a lesson, successful model conversation, or plausible diagnosis does not establish production behavior. Deterministic controls, negative tests, scenario evaluations, and explicitly authorized deployed acceptance provide that evidence.

This draft does not approve an implementation, decide unresolved product questions, establish deployed safety, or authorize deployment.
