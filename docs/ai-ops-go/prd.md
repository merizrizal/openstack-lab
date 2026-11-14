# PRD: Read-Only Go OpenStack Investigation and Orchestration Assistant

Status: scope_ready — owner-approved Delivery 1 product requirements for a non-production, tinkering OpenStack Lab. This is approval of product scope for implementation planning, not implementation approval or evidence of deployed safety. Concrete architecture, environment configuration, and release thresholds remain subject to design and verification.

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

The agent, orchestration, diagnostic tools, safety gateway, manual CLI, and local/stdio MCP interface shall be implemented primarily in Go and delivered as one AI-OPS runtime executable. Manual diagnostics use the same reviewed built-in tools and safety boundary before automatic tool calling or MCP is introduced. Diagnostic execution must not depend on separately deployed diagnostic scripts, interpreters, or CLI utilities.

Delivery 1 uses separately installed, operator-managed Codex CLI and Pi CLI harnesses as inference-only backends during Go-owned investigations. They and their own runtime dependencies are explicit external prerequisites for model-enabled work, not part of the Go executable; those dependencies are not diagnostic implementations. The Go application owns planning, state, approvals, orchestration, and diagnostic dispatch; the harnesses do not call tools or MCP directly during those investigations. A custom agent harness using an official remote model API is a future-delivery direction, not Delivery 1 scope. Configuration, credentials, protected state, curated knowledge, and independently operated OpenStack, host, and model services are separately managed and remain subject to their own access controls.

One Go executable does not imply one security principal or process: multiple processes and OS-enforced separation may be required. Go runtime components and harnesses run under appropriately separated non-root identities; privileged account, sandbox, egress, and host-observer setup is operator-controlled and outside the diagnostic agent. Isolation must independently prevent model-facing components from accessing diagnostic credentials or bypassing the tool boundary and must be verified. Environment-variable filtering, disabled tool flags, or a shared Go process alone are not sufficient evidence. Model-enabled work fails closed if required isolation cannot be established; safe manual diagnostics remain available.

Offline fixtures and model evaluations do not replace deployed-lab diagnostic validation. Delivery 1 requires authorized live project-reader diagnostics, restricted-host validation on one controller and two compute nodes, and at least one real model-backed lab investigation. Operator-reader capabilities may remain unavailable if safe access cannot be validated. No destructive probe against the working lab is authorized.

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

Manual diagnostics remain available without a model. Local/stdio MCP is required in Delivery 1 after manual diagnostics and the shared gateway are validated. It provides interoperability over the same reviewed tools and curated knowledge; it is neither the orchestrator nor a replacement security boundary. Pi is the first required real standalone MCP client in a separately approved, egress-controlled session, distinct from its inference-only role inside Go-owned investigations. A single capable agent is the baseline. Specialist investigator/reviewer roles may be added only when evaluation demonstrates a benefit; multiple processes or models are not prerequisites for an evidence-review step.

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
8. Deliver an operable lab product with reproducible validation, rollback, and required local/stdio MCP interoperability.

## Non-Goals / Out of Scope

1. Infrastructure mutation, including restarts, configuration edits, installation, resource creation/deletion, or autonomous remediation. Human approval within this product cannot enable these actions.
2. General-purpose coding agents, repository editing, deployment execution, database querying, or unrestricted filesystem access by the model.
3. Generic shell, SSH, sudo, OpenStack CLI passthrough, or user- or model-selected diagnostic executable paths.
4. Admin cloud credentials, root SSH, unrestricted sudo, service/database/RabbitMQ credentials, or unrestricted control-plane file access in the diagnostic execution boundary.
5. Self-healing, predictive scaling, autonomous incident triggering, or continuous infrastructure surveillance in the initial release.
6. A mandatory multi-agent framework, distributed scheduler, vector database, or embeddings service. These require demonstrated need, not curriculum completion.
7. A web dashboard, public multi-tenant service, or external HTTP API in the first release. CLI and approved MCP clients are sufficient.
8. Local-model deployment, GPU procurement, model training, or a new provider-protocol gateway. A future local inference option requires separate operational approval.
9. Replacement of existing OpenStack deployment, Ansible, Vagrant, observability, or Molecule workflows.
10. Treating the educational roadmap's stage numbers as release milestones or evidence of product readiness.
11. Network-exposed MCP and storage-node host diagnostics in Delivery 1. Project-visible volume and attachment diagnostics remain in scope.

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

FR-002. Each investigation shall retain the original goal, cloud/OpenStack project scope, explicitly selected resources, permitted capability/profile set, and execution budgets as application-owned data. Delivery 1 supports one configured project-reader project at a time. Changing projects shall not permit access to or resumption of records under a mismatched authorized scope.

FR-003. Target selection shall accept canonical server UUIDs and supported exact names. Name matching shall be literal and case-sensitive within the authorized project, preserving meaningful whitespace; ambiguous or missing matches shall be rejected without guessing. Retain the original identifier and resolved identity and provide UUID guidance. Before plan approval, name resolution requires separately disclosed and explicit operator authorization for bounded project-reader lookup of the selected names through the safety boundary; the lookup shall be audited and does not authorize diagnostic tasks.

FR-004. The planner shall return a validated structured disposition of ready, needs-input, or unsupported. Non-ready plans shall execute no diagnostic tasks and explain what prevents execution.

FR-005. Before any single- or multi-server model-driven investigation executes diagnostic tasks, the operator shall see its targets, tasks, dependencies, capability/profile requirements, limits, and expected outputs and approve the exact validated plan and scope. Approval defaults to 24 hours and is operator-configurable; revocation, expiration, changed plan, scope, or relevant policy invalidates it. Within approved tasks, targets, related-read categories, capabilities, and budgets, Go may select individual calls without per-call approval, subject to FR-010. A changed task graph or expanded targets, capabilities, or limits requires renewed approval. Expiry pauses new work and applies FR-010's in-flight revocation handling. A direct named manual diagnostic remains an operator action through the gateway without a model-generated plan.

FR-006. Task graphs shall reject duplicate task IDs, missing dependencies, cycles, unsupported task types, and tasks outside approved scope before execution. The orchestrator shall execute only ready tasks whose required dependencies have succeeded.

### Agent and workflow execution

FR-007. Every model response used for control flow shall undergo structural and semantic validation. Invalid responses shall produce a bounded retry or explicit failure, never execution of free-form text.

FR-008. Agent loops shall request only registered tools and stop on completion, insufficient capabilities/evidence, repeated unproductive requests, cancellation, or exhausted budgets. Stop reasons shall be visible in persisted state and reports.

FR-009. The orchestrator, not the model, shall own task readiness, state transitions, retries, timeouts, approvals, and completion. Denials and invalid requests shall not be retried as transient failures or rerouted to stronger credentials.

FR-010. Before each tool call, the execution boundary shall revalidate the permitted cloud/project, resource target, capability, profile, and limits. This includes resumed calls and calls proposed by delegated roles; plan validation alone is insufficient. If diagnostic authorization is revoked or expires during a read, stop new dispatch, attempt cancellation, and withhold results from an unauthorized requester. Audit the outcome where possible and report that the read may already have occurred; do not claim cancellation undid it.

FR-011. An approved server plan may authorize specific categories of related reads, including its referenced flavor and project-visible ports, networks, and subnets. Each read requires a verified relationship derived from authorized observations and the approved visibility scope. A discovered relationship shall not automatically authorize unrelated resources, broad cloud discovery, project-wide summaries, or hosts; each requires its own explicit scope or approval.

FR-012. Workflows shall support server/boot investigation, metadata/network investigation, and bounded project-visible volume/attachment inspection. Unsupported subdiagnostics shall be identified explicitly rather than fabricated or replaced with arbitrary commands.

FR-013. Multi-server projects shall retain per-target results and produce a cross-task synthesis only after the required dependency outcomes are known. Failed or unavailable evidence shall prevent an unqualified successful diagnosis.

### State, memory, knowledge, and evidence

FR-014. The system shall checkpoint goals, scope, approval identity, task/step state, observations, hypotheses, errors, usage, and child-investigation links before and after significant execution transitions.

FR-015. Resume shall validate stored state, approval, and current policy, preserve completed work, and make interrupted or uncertain calls visible. Re-collecting an uncertain dispatched call requires explicit operator confirmation, current authorization checks, and a new timestamped observation. An intentional re-observation shall not silently replace prior evidence. Completed, failed, and cancelled investigations are terminal and cannot be resumed; a new investigation may link authorized historical evidence but requires its own scope and approval. Paused or unexpectedly interrupted work remains resumable.

FR-016. The system shall distinguish recent observations, derived working summaries, historical investigation memory, and reference knowledge. Summaries shall retain evidence references; historical material shall never be promoted to fresh observations merely by retrieval. Observation freshness defaults to 15 minutes, configurable with justified per-tool overrides. Stale evidence remains timestamped history but cannot establish current state. A refresh must be within the approved plan and budget or receive new authorization; source log event time remains distinct from collection time.

FR-017. Retrieval and MCP resources shall use only explicitly approved, curated current knowledge sources, return bounded relevant excerpts with stable source/chunk identity, and expose missing or stale knowledge as a limitation. Automatic archive or whole-repository ingestion is prohibited. Useful older knowledge may be used only after operator review, sanitization, and deliberate promotion into an approved source. An optional knowledge source may be unavailable without disabling permitted manual diagnostics.

FR-018. Goals, retrieved documents, logs, tool output, memories, and delegated reports shall be treated as untrusted content. Instructions in them shall not modify tool permissions, scope, approval, provider selection, or orchestration policy.

FR-019. Reports shall separate observed facts, interpretations, hypotheses, missing/contradictory evidence, and manual next steps. Material factual claims shall reference evidence or be labeled unverified; knowledge citations shall remain distinguishable from infrastructure observations. Manual remediation recommendations shall describe actions in plain language and cite curated runbooks, without generating runnable mutation commands or executing changes.

FR-020. Before finalization, an evidence-review step shall check required evidence references, task coverage, collection failures, and unsupported claims. Review concerns shall cause bounded further investigation or an explicitly inconclusive/partial report, not invented confirmation.

### Diagnostic safety and access

FR-021. Diagnostic execution shall use a dedicated isolated observer VM or host outside the OpenStack cloud it observes and outside control-plane services, with only required management/API and separately approved host/observability reachability. Initial placement shall not require the tenant network. Ubuntu 24.04 LTS on x86-64 is the required Delivery 1 observer and acceptance target; other platforms require separate validation before being described as supported.

FR-022. Project-visible tools shall use a dedicated project-reader identity by default. Operator-reader and restricted SSH-observer capabilities shall be separately configured, validated, and enabled; no permission failure shall trigger fallback to admin or another profile. Host diagnostics require a dedicated non-root observer identity or an existing identity verified as equivalently restricted, with only approved read-only operations and restricted sudo where needed. Operator-controlled provisioning and validation may configure host access, but the diagnostic agent shall not create accounts, install components, or edit SSH/sudo configuration.

FR-023. Available tools shall be determined by a reviewed registry declaring argument schema, implementation, scope/profile, risk, availability prerequisites, timeout, and output bound. Unknown tools, extra/invalid arguments, arbitrary commands, and model-supplied executable locations shall be denied before execution.

FR-024. Diagnostic tools shall be implemented as reviewed Go capabilities within the runtime executable, exposing narrow read-only operations through the same authorization, validation, limits, and audit boundary. They shall not depend on separately deployed diagnostic executables or invoke arbitrary shell commands. Restricted host diagnostics remain subject to FR-026.

FR-025. The diagnostic catalog shall include approved read-only Go tools for project resource summaries (servers, networks, subnets, volumes and images where project-visible), server basic information including fault and flavor, and server networking, as well as project-visible volume/attachment evidence. Server basics shall report status, image, flavor, networks, config drive, and availability zone when exposed and permitted, with explicit unavailable, denied, or not-applicable indications rather than silently missing or invented values; include fault information when available. Networking should include related ports, fixed IPs, networks, and subnets. Delivery 1 shall include reviewed narrow scheduler/Placement or capacity diagnostics and offline safety coverage. These and Neutron agent health are enabled only with validated safe reader access, which may be the separately approved operator-reader profile; otherwise they report unavailable and do not block completion. Recent Nova, Neutron, and metadata errors require validated restricted SSH/log access. Higher-visibility diagnostics remain gated by validated access and enablement.

FR-026. Host diagnostics shall use approved host aliases, fixed diagnostic operations, restricted observer access and sudo where needed, and bounded recent windows/output. The selectable recent-log windows are 15 minutes, 30 minutes, and 1 hour, defaulting to 30 minutes, with bounded lines and bytes. Caller-selected SSH destinations, log paths, commands, unsupported host/operation combinations, and unrestricted configuration dumps shall be rejected. Live acceptance covers one controller and two compute nodes; storage-node host diagnostics are deferred.

FR-027. Every tool request shall return a structured result distinguishing success, partial, error, denial, invalid input, timeout, cancellation, and unavailable capability, with target, correlation ID, duration, safe payload/error details, and truncation metadata. A project summary with some successful categories shall return partial data with an explicit status per category; denied or unavailable categories shall not be represented as empty or healthy. If no category succeeds, return an appropriate failure status.

FR-028. Every allowed and denied request shall generate a sanitized audit record when the audit store is available. An allowed request requires a durably persisted audit intent before dispatch; if intent persistence fails, do not execute. If result-audit persistence fails after a read, stop further calls, return a locally visible safe failure, and withhold the diagnostic payload from the model and client until the failure is resolved and the result is durably audited. The read may already have occurred and cannot be undone. If audit storage is unavailable for a denied request or outcome, expose the audit gap locally and never claim the record exists. After recovery, pause until the operator acknowledges known gaps and uncertain calls; recheck current authorization and separately confirm uncertain re-collection.

FR-029. Secrets and prohibited sensitive fields shall be omitted or redacted before results enter model context, any local persistence including evidence, audit, or memories, reports, exports, or telemetry. Security-sensitive data that cannot be safely transformed shall be withheld with an explicit limitation. Protected local evidence and audit may retain only real lab identifiers needed for local operation and traceability; these remain sensitive and subject to scope, access, retention, and storage controls. Outbound model context uses consistent aliases for lab-specific identifiers where practical, while retaining bounded sanitized evidence and relevant error messages.

FR-030. Requests to fix, restart, edit, create, delete, or otherwise mutate the lab shall never invoke a mutation capability. For a “fix it” request, the assistant shall offer a separately scoped read-only diagnostic plan, collect permitted evidence within the approved scope and applicable authorization, and provide manual recommendations rather than executing remediation. If approval, access, or evidence is unavailable, it shall not execute unauthorized diagnostics and shall report the limitation.

### Model boundary and interoperability

FR-031. Codex CLI and Pi CLI adapters shall expose a common bounded text/structured-output contract with cancellation, error reporting, and usage metadata. In Go-owned investigations they are inference-only: native tools and direct MCP access are disabled, and Go validates and dispatches proposed calls. Provider adapters shall not own infrastructure execution. Harness installation, update, and authentication are operator-managed; the runtime shall not perform them automatically. Model-enabled execution requires an operator-approved, tested harness version and provider/model combination; unknown or unvalidated versions fail closed while manual diagnostics remain available.

FR-032. Remote inference shall require a reusable explicit operator-approved policy for the identifiable provider/model destination and permitted outbound data classes, valid until revoked. Disclosure covers goals, observations, summaries, memory, and retrieved knowledge; show the categories before the first model call in an investigation or manual analysis. An unknown or changed destination or changed permitted data classes requires renewed approval. Operators may configure provider/model combinations, but only tested combinations in the capability matrix are supported; egress enforcement, sanitization, and consent are separate controls. Credentials, tokens, passwords, and full configurations shall never be sent as model context or diagnostic evidence; provider authentication is used only for its intended authentication purpose. Withhold evidence that cannot be safely sanitized.

FR-033. Model runtimes shall not possess cloud/SSH credentials or independent shell/file/network tools that can bypass the reviewed diagnostic boundary. Provider authentication shall remain opaque to diagnostic tools and reports.

FR-034. Provider failure or absent outbound approval shall stop model-dependent work safely while retaining local state inspection, reports, and permitted manual diagnostics. The application shall not silently switch providers. On disclosure-policy revocation, stop new model requests and attempt to cancel in-flight requests; do not use responses received after revocation. Report that data already transmitted cannot be recalled.

FR-035. Delivery 1 shall provide a local/stdio MCP interface exposing only the enabled reviewed diagnostic subset, curated read-only resources, and diagnostic prompts for repeatable metadata, VM boot, network, and volume workflows. Calls shall preserve the same scope, validation, limits, redaction, audit, and result semantics as local execution; no protocol bypass is permitted. MCP follows manual and gateway validation. Network-exposed MCP is outside Delivery 1.

FR-036. Optional specialist roles shall receive explicit tasks, restricted tools, bounded context/budgets, and structured evidence-linked outputs. The orchestrator shall own their dependencies and resolve conflicting outputs as review issues; agents shall not self-delegate unrestricted work.

### Evaluation and operation

FR-037. An offline evaluation harness shall run versioned incident fixtures with deterministic model/tool substitutes, record expected/actual behavior, and produce machine-readable results without cloud access or inference credentials.

FR-038. Evaluation results shall report task success, appropriate tool selection, unsupported factual claims, unnecessary tool calls, safety violations, elapsed time, and available token/cost data. A fixture-supported inconclusive result shall be scored separately from a fabricated diagnosis.

FR-039. Each run shall expose correlated project/task/investigation/tool/model events and usage, including retries, denials, timeouts, truncation, approval, and terminal outcome, without requiring hidden model reasoning traces.

FR-040. Operators shall be able to configure finite limits for task count, agent steps, tool calls, retries, elapsed time, context/output size, and available token/cost budgets. When exact provider usage is unavailable, conservative limits and explicit unknown usage shall replace false zero-cost reporting.

FR-041. Deployment shall provide startup checks for configured tools, profiles, stores, curated knowledge, enabled adapters, and policy/audit dependencies. Capabilities with unmet prerequisites shall be disabled or startup shall fail with actionable diagnostics according to their required/optional classification.

FR-042. Release operation shall include credential revocation/rotation procedures, protected data retention/export/deletion procedures, policy version identification, shutdown/recovery, and rollback to a validated configuration without modifying OpenStack workloads.

### Retained toolbox and manual-operation requirements

FR-043. The observer shall reach Keystone and other explicitly approved management endpoints without requiring tenant-network placement. The product's runtime capabilities shall be delivered in one Go executable without separately installed utilities or interpreters for diagnostic execution; operator-installed Codex/Pi executables and their own runtime dependencies are explicit model-enabled prerequisites. External infrastructure services, approved configuration, credentials, state, and curated knowledge remain separately managed prerequisites. Use a dedicated diagnostic identity, prefer Keystone application credentials when supported, protect credential files, and validate reader access and mutation denial against the actual release policy.

FR-044. Each diagnostic tool shall perform only read-only operations. Diagnostic implementations shall validate their inputs as well as passing gateway validation, prefer structured API output such as JSON where practical, avoid full secret-bearing configuration files, and redact secret-like fields in any permitted snippets. Logs shall default to a recent, bounded window and bounded output. Each public tool name shall map to one reviewed Go implementation for the selected version/configuration; callers cannot choose or override implementations.

FR-045. The AI instruction layer shall explicitly identify the assistant as diagnostic-only and prohibit mutation requests. This instruction is defense in depth, not an authorization boundary. Tool names and descriptions shall express diagnostic intent, not expose generic execution primitives.

FR-046. A first usable manual workflow shall support an operator selecting and running approved named diagnostics through the runtime CLI and pasting output into the Go CLI for analysis without automatic tool calling or MCP. The supported analysis path applies the same sanitization, disclosure, harness-isolation, and egress controls; analysis alone does not create an investigation plan or dispatch tools. Independently sharing output outside the product is outside its control and must not be described as protected by it. Manual, automated, and MCP diagnostic requests shall pass through the same reviewed authorization, validation, limits, redaction, and audit boundary with appropriately scoped credentials. Document safety boundaries, credential scopes, the registry, audit, and rollout.

### Session, data lifecycle, and legacy records

FR-047. A standalone MCP client requires a separately approved session. Before connection, the operator uses the Go CLI to review and approve the cloud/project, permitted targets, capabilities, egress profile, and session lifetime. Project-wide summaries require explicit project-wide approval. The runtime shall bind the connection to that approval and independently verify the client's security context; reusable credentials must not be exposed in command arguments or logs. Approval defaults to one hour, configurable by the operator, and ends on revocation, expiry, client disconnect, or runtime shutdown. A new session requires fresh approval. Standalone clients may receive diagnostic evidence only under an operator-approved, independently enforced egress profile consistent with approved destinations and data classes; fail closed if it cannot be verified. Revoke the dedicated client environment's approved egress on session end. Data already received, copied, or sent cannot be recalled; do not claim erasure.

FR-048. Retention defaults to 30 days for investigation data after a completed, failed, or cancelled terminal transition and 90 days for sanitized audit records; both are operator-configurable. Running and paused investigations are protected. If a terminal case expires while an active investigation references it, retain only the minimum sanitized evidence and provenance required by the active investigation, report the exception, and count it against the storage limit; the evidence remains historical or stale. Bounded cleanup runs automatically while the runtime operates, including at startup. It cannot run while stopped; overdue data is handled on restart and cleanup failures are reported. Cleanup requires durable audit intent before deletion; if that fails, do not delete automatically. If outcome auditing fails after deletion, report the gap and possible completed deletion, not a rollback.

FR-049. The operator shall configure a finite protected-data storage limit; startup fails with an actionable error if it is absent or unusable. Detect actual disk exhaustion separately. Clean up expired data where safe, but do not silently delete unexpired records to free space. If required audit or checkpoint writes cannot be guaranteed, stop diagnostic dispatch and model-dependent work, report the problem, and preserve safe local inspection/export and operator-controlled cleanup where possible. The operator may explicitly and with confirmation delete unexpired terminal investigation data after durable audit intent, but shall not remove evidence needed by an active investigation or delete audit records before their separate retention period. If outcome auditing fails after deletion, report the gap and possible completed deletion rather than claiming rollback. The model shall not request or perform deletion. Protected exports use aliases by default; an explicit operator request may include necessary real operational identifiers with a warning and audited action, but never secrets or prohibited fields. The operator is responsible for copies after export.

FR-050. Delivery 1 starts with a new versioned store. Preserve existing Go investigation, memory, workflow, and project files without modifying, deleting, automatically indexing, sending, or importing them; do not reuse legacy approvals. These files remain separately protected, operator-managed legacy data outside Delivery 1 automatic retention and cleanup. Any future migration requires separate operator approval, a tested versioned procedure, backup, and rollback. Physical disk exhaustion must still be detected when legacy data occupies space outside the managed limit.

## Non-Functional Requirements

NFR-001. **Safety:** No agent/client path may bypass authorization at the actual tool boundary. The deterministic safety suite must record zero unauthorized executions, mutations, or secret disclosures.

NFR-002. **Least privilege:** Cloud credentials, host-observer credentials, provider authentication, and application state shall have separate access boundaries and restrictive permissions. Only explicitly required network routes shall be available.

NFR-003. **Bounded execution:** Every enabled call and run shall have finite documented limits. Deadline/cancellation tests shall verify cleanup of owned operations and resources and absence of later tool dispatch after termination.

NFR-004. **Persistence:** Checkpoints shall be atomically replaced or transactionally committed; corrupt, incompatible, or unsuccessfully persisted state shall not be reported as safely saved or resumable. Concurrent writers shall be serialized or rejected.

NFR-005. **Isolation:** Evidence, memory, knowledge visibility, and approvals shall be partitioned by authorized cloud/project and investigation scope. A shared resource name alone shall not authorize cross-project memory reuse.

NFR-006. **Reliability:** Tool calls shall fail safely with structured error states, finite bounds, and no unsafe execution fallback. Missing operator-reader or SSH/log access shall result in explicit capability degradation without privilege escalation; restricted-host live validation is nevertheless required for Delivery 1 acceptance. Required policy, audit, or checkpoint failures shall stop new execution; provider availability shall not be required to inspect local results.

NFR-007. **Evidence quality:** Root-cause confirmation requires direct supporting evidence. Relevance scores, model confidence, reviewer agreement, and successful tool exit codes alone are not proof of a diagnosis.

NFR-008. **Observability:** Every allowed and denied tool request shall be auditable with timestamp, tool name, sanitized arguments, status, and duration; when execution does not occur, duration shall be explicitly marked not applicable rather than invented. Correlation and provenance shall survive planning, execution, review, resume, and export. Telemetry shall contain concise decisions and outcomes, not secrets or hidden chain-of-thought.

NFR-009. **Performance and cost:** Versioned evaluation reports shall publish per-scenario tool counts, latency distributions, and measured or explicitly unavailable usage/cost. Release-specific quality and latency thresholds must be agreed before model-enabled rollout; this PRD claims no measured SLA.

NFR-010. **Compatibility:** Manual CLI, automated Go, and MCP entry points shall preserve reviewed tool semantics or declare a versioned incompatibility. The product's manual diagnostics and the lab's deployment/validation workflows shall remain operable.

NFR-011. **Maintainability:** New tools and workflows shall supply contracts, safety classification, offline tests, and scenario coverage. Extension shall not require granting generic execution primitives.

NFR-012. **Privacy:** Redaction shall be supplemented by data minimization, disclosure approval, storage permissions, retention, and network egress enforcement. Outbound opt-in alone is not a redaction or firewall control.

NFR-013. **Usability:** Tool names and descriptions shall express diagnostic intent rather than implementation details. Outputs shall be concise enough for AI reasoning and human review without hiding evidence gaps or truncation. The CLI shall distinguish proposal from execution, operational completion from diagnostic confidence, and permission denial from healthy state. Machine-readable exports shall be versioned.

NFR-014. **Deployability:** The runtime shall be reproducibly installable and independently stoppable outside the observed cloud and control plane as one Go executable, with documented external service, configuration, credential, and data prerequisites and an offline validation path. Diagnostics shall not require separately installed diagnostic utilities or interpreters. Model-enabled work requires separately operator-installed and authenticated Codex/Pi executables and their runtime dependencies, approved versions, and verified isolation.

NFR-015. **Testability:** Core orchestration and safety tests shall not depend on a live cloud or nondeterministic provider. Required live lab and real-model acceptance shall be explicitly authorized and reported separately from offline tests; additional live/model evaluations are optional and explicitly selected.

## Implementation Decisions

### Product decisions

1. The application, not the LLM, executes tools and controls workflows. Structured output is a proposal requiring deterministic validation.
2. Scope and permissions are execution-time constraints, not merely planner instructions. Approval and graph validation do not replace call-boundary checks.
3. A separate observer runtime, dedicated reader profiles, reviewed diagnostic tools, restricted host access, and auditability remain mandatory.
4. State, memory, retrieval, workflow, and orchestration are separate concepts. Persisted observations and application state are authoritative records; summaries and model recommendations are derived content.
5. The initial architecture uses a single-agent execution path with an evidence-review stage. Multi-agent distribution is an optional evaluated extension, not a condition of curriculum completion.
6. Delivery 1 includes local/stdio MCP over established safety and knowledge contracts after direct execution is validated. Network exposure is outside Delivery 1 and requires separate approval and design.
7. Delivery 1 supports the separately authorized Codex and Pi inference backends, while manual diagnostics remain usable without inference. Provider internals and authentication are not diagnostic capabilities.
8. Go owns one authoritative policy and registry boundary for all diagnostic entry points. The concrete independently enforced isolation and IPC mechanism remains a design question.
9. Delivery 1 targets one trusted lab operator; this does not authorize arbitrary local processes. Multi-user operation requires separate decisions.
10. Start a new versioned Delivery 1 store and preserve existing records separately under operator control. Any future import requires a separately approved, tested backup and rollback procedure.

### Proposed decisions and assumptions

1. **Assumption — Go product core:** Continue suitable existing Go CLI, agent, planner, workflow, and project orchestration components as the product core, subject to the single-executable and safety requirements.
2. **Assumption — local first:** Begin with protected local persistence and sequential ready-task scheduling. Database-backed persistence, parallel scheduling, and shared-service operation require separate concurrency and authorization decisions.
3. **Assumption — simple retrieval first:** Use curated text chunking and lexical retrieval unless measured retrieval failures justify embeddings, hybrid search, or reranking.
4. **Proposed hardening:** Normalize safe result envelopes across built-in Go tools and entry points, carry explicit scope through nested execution, and make persistence/audit failures visible. The current Go registry and workflow presence do not establish these guarantees.

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

A versioned record contains an identifier, original goal, cloud/OpenStack project identity, explicit target set with resolved resource identities, allowed capability/profile set, policy/plan versions, approval digest and expiry, budgets, lifecycle status, timestamps, task/child links, evidence references, usage, and terminal reason.

Operational lifecycle distinguishes proposed, awaiting approval, running, paused, completed, failed, and cancelled. Completed, failed, and cancelled are terminal; paused or unexpectedly interrupted work can be resumed under current authorization. Diagnostic outcome independently distinguishes supported findings, partial findings, and inconclusive investigation. A completed process may have an inconclusive diagnosis; neither is a claim that the cloud is healthy.

Tasks contain stable IDs, reviewed types, target scope, dependencies, attempt count, status, outputs/evidence references, and error/stop reasons. Tasks distinguish pending, ready, running, paused, completed, failed, blocked, and cancelled. A dependency failure blocks dependent success; policy-defined partial reporting may still summarize that failure explicitly.

### Plan and approval

A plan contains disposition, explanation, tasks, dependencies, expected capabilities, scope, and budgets. Approval binds its canonical validated form and relevant policy identity, defaults to 24 hours, and is configurable. Changed task graph, scope, targets, capabilities, limits, relevant policy, expiration, or revocation invalidates it. Go may select and audit individual calls within the approved plan without per-call approval. Resuming unchanged work still requires current authorization checks; expired or revoked access cannot be recovered from an old checkpoint.

### Tool definition, request, and result

A tool definition declares name/version, diagnostic intent, argument schema, fixed implementation mapping, required profile, scope/relationship rules, prerequisites, risk, timeout, output limit, and read-only guarantee.

A request carries correlation IDs, tool/version, validated arguments, and an application-controlled authorization context. Model arguments cannot supply or override credentials, implementation paths, policy, or approval state.

A result carries request/tool identity, status, sanitized targets/arguments, start/end or duration, structured data or bounded stdout, safe stderr/error, exit code when applicable, truncation/redaction indicators, and evidence references. Logical statuses are ok, partial, error, denied, validation_error, timeout, cancelled, and unavailable. A partial project summary reports per-category status; no successful category yields an appropriate failure rather than partial success. Truncation is metadata, not evidence of complete collection. Adapters must document status translations.

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
3. The model proposes a structured plan, or the operator chooses a reviewed workflow. Single- and multi-server investigations execute no diagnostic tasks until exact approval; necessary name-resolution reads require separate, disclosed authorization, project scope, and audit.
4. The orchestrator schedules approved ready tasks; the agent requests evidence through the safety boundary.
5. Progress shows concise action intent, task state, call outcome, and remaining limits. It does not expose hidden reasoning traces.
6. Evidence review checks claim support and gaps. Further collection, if needed, remains inside the approved scope and budget.
7. The final report gives findings, limitations, evidence, and manual next steps. The operator retains all change authority outside this product.

### Metadata and VM boot cases

For metadata failures, correlate server/network context with permitted Neutron/Nova/metadata evidence. Healthy agents do not establish that the Nova metadata listener is available. Missing host access must yield a named evidence gap rather than an inferred listener diagnosis.

For a NoValidHost symptom, use server faults and available flavor, scheduling, capacity, or Placement evidence only where reviewed tools and approved visibility exist. A fault string alone does not establish whether capacity, placement constraints, service availability, or another cause is responsible.

### Interruption and degraded operation

Cancellation stops new dispatch and bounds active calls. Cancelled, failed, and completed investigations are terminal; a new investigation can link authorized historical evidence under fresh scope and approval. Resume of paused or interrupted work shows completed, interrupted, and blocked work, rechecks policy and approval expiry, and requests renewed approval when required. Uncertain dispatched calls require explicit confirmation before a new audited observation. Audit recovery requires operator acknowledgement of known gaps before resuming. Evidence freshness is visible; refreshing a prior observation is explicit and audited.

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
9. **Evaluation tiers:** Deterministic offline regression and safety/contract tests for both harness adapters are mandatory. Both harnesses require an authorized real-model integration check; at least one must complete an authorized model-backed investigation against the lab. The other may use controlled fixture evidence. Additional model-backed evaluations use a versioned corpus/rubric and repeated runs with explicit provider approval. Live lab acceptance is separate and cannot be replaced by fixtures or educational milestone completion.
10. **Credential validation:** Demonstrate authorized reads and policy rejection of representative create/update/delete operations in an explicitly authorized disposable test scope. These tests are operator-controlled, not agent tools. Use preflight policy checks and disposable resources so an unexpected permission grant cannot damage the working lab; require explicit approval and a cleanup owner before live probes.
11. **Deployment validation:** Reuse the lab's existing OpenStack validation and Molecule smoke patterns for readiness, profile isolation, management reachability, and read-only workflows. Before deployed release, verify project-resource, server-basic, and server-network diagnostics against the lab with project-reader credentials and restricted host diagnostics on one approved controller and two approved compute nodes. Test operator-reader diagnostics when enabled and prerequisites are configured; otherwise report them unavailable. Fault injection is optional and confined to disposable environments; reproducing an incident must not require inducing a working-lab outage.
12. **Release gates:** All deterministic authorization, mutation-denial, redaction, graph, approval, and recovery acceptance tests must pass, with zero unauthorized execution, mutations, or prohibited secret disclosures. Build a representative versioned corpus and collect an exploratory baseline, then agree and pin the dataset, rubric, supported capability matrix, and quality/latency/cost thresholds before evaluating the release candidate. Do not tune pass criteria after observing its results.
13. **Toolbox defense in depth:** Review and statically check Go diagnostics for mutation operations, command injection, unsafe file operations, and unrestricted privilege; supplement static checks with behavioral tests because static checks alone cannot prove safety. Test tool inputs and structured output, and verify the gateway denies malformed inputs before dispatch.
14. **Single-executable deployment:** Build and exercise the runtime in a controlled environment without separately installed utilities or interpreters for diagnostic execution; provide the explicitly required operator-installed Codex/Pi harnesses and their runtime dependencies for model checks. Verify manual CLI, both model integrations, local/stdio MCP, and permitted diagnostics against controlled fixtures. Separately validate real external service and host prerequisites for deployed acceptance. Demonstrate independent non-root model/credential isolation and managed MCP-client egress enforcement; a single process, package boundary, or environment-variable filter alone is not evidence.
15. **Lifecycle and disclosure:** Test audit intent/outcome failure and acknowledged recovery; revocation and expiry races; one-hour MCP and 24-hour plan defaults; startup/operating cleanup, terminal states, active-reference retention, cleanup audit failures, quota and physical disk exhaustion; legacy-store isolation; 15-minute freshness; partial summaries; protected exports and confirmed early deletion. Exercise provider/model policy changes, aliasing, withheld unsafe data, client egress revocation, and manual Go CLI analysis without automatic calls.

## Acceptance Criteria

AC-001. Single- and multi-server CLI investigations accept explicit goal/scope, preview a plan, and start diagnostic tasks only after exact approval. Missing, cancelled, stale, expired, and changed-plan approval fixtures execute no diagnostic tasks. Separately authorized, project-scoped name resolution is disclosed and audited. Covers FR-001–FR-006.

AC-002. Ambiguous names, case/whitespace mismatches, missing resources, and unsupported tool identifiers yield clear guidance without inspecting an unintended target. Valid UUID and literal case-sensitive exact-name cases retain original and resolved identity; ambiguous names do not select a first match. Covers FR-002–FR-003.

AC-003. Invalid structured decisions, unknown task types, cycles, missing dependencies, and repeated unproductive tool requests stop safely under finite limits. Covers FR-006–FR-009, FR-040.

AC-004. An approved in-scope plan followed by an out-of-scope nested, delegated, or resumed request is denied before tool execution and audited. Reviewed relationship fixtures permit only the corresponding authorized related reads. Covers FR-010–FR-011, FR-028, FR-036.

AC-005. Offline server/boot, metadata/network, and volume/attachment scenarios produce evidence-linked supported findings when required tools exist, and named limitations when they do not. Covers FR-012, FR-025.

AC-006. A multi-server project honors dependencies, preserves per-target evidence, and labels failed/blocked coverage without reporting an unqualified successful diagnosis. Covers FR-013.

AC-007. Checkpoint/resume tests preserve completed work, expose interrupted calls, require confirmation for uncertain re-collection, reject corrupt or incompatible state, and surface failed writes and concurrent-writer conflicts. Terminal investigations cannot be resumed; paused/interrupted work rechecks approval and scope. Covers FR-014–FR-015 and NFR-004.

AC-008. Context and exported reports distinguish observations, working summaries, historical memory, and reference knowledge; historical and stale conclusions cannot satisfy current-state expectations. Freshness defaults to 15 minutes with configurable per-tool overrides; collection and log event timestamps remain distinguishable. Covers FR-016, FR-019.

AC-009. Retrieval returns bounded approved current curated chunks with stable citations; automatic archive/whole-repository ingestion is absent, and unavailable knowledge and hostile/secret-bearing content do not broaden access or leak protected data. Covers FR-017–FR-018, FR-029.

AC-010. Evidence review detects missing references, contradictory evidence, and unsupported material claims in the fixture corpus, producing further bounded collection or an explicit inconclusive/partial report. Covers FR-019–FR-020.

AC-011. A deployment acceptance record demonstrates observer-runtime separation, required reachability only, dedicated reader profiles, and fail-closed unavailable optional profiles. Controlled authorization tests establish read success and mutation denial. Covers FR-021–FR-022 and NFR-002.

AC-012. Unknown tools, generic commands, extra/invalid arguments, caller-selected executables, and profile overrides are denied across manual CLI, automated, and MCP entry points. Contract tests show that only reviewed built-in Go diagnostics can execute through the boundary. Covers FR-023–FR-024, FR-035.

AC-013. Enabled host diagnostics accept only approved host/operation combinations and the 15-minute, 30-minute, or 1-hour windows, defaulting to 30 minutes, with bounded output. Restricted observer controls are live-validated on one controller and two compute nodes. Missing prerequisites result in unavailable capability rather than fallback; absent required host evidence blocks Delivery 1 acceptance. Covers FR-026.

AC-014. Contract tests cover every result status including partial summary categories, truncation, cancellation, safe errors, correlation, and required audit records, including timestamp, tool name, sanitized arguments, status, and duration or an explicit not-applicable value. Intent-persistence failure prevents dispatch; result-audit failure stops dispatch, withholds the result from the model/client, and exposes the gap. Audit recovery requires operator acknowledgement. Covers FR-027–FR-028 and NFR-006, NFR-008.

AC-015. Secret-canary and remediation-request fixtures show no prohibited disclosures and no mutation execution, including when the operator asks the model to ignore restrictions. A “fix it” fixture produces a scoped diagnostic plan and plain-language, runbook-referenced manual recommendations without runnable mutation commands, collects evidence only with required authorization, and reports missing access or approval without unauthorized execution. Covers FR-019, FR-029–FR-030 and NFR-001.

AC-016. Both Codex and Pi adapters pass deterministic structured-response, timeout, cancellation, usage, version, inference-only, and isolation contract tests and an authorized real-model integration check. At least one completes the live-lab investigation in AC-025; the other may use controlled fixture evidence. Unknown or unvalidated versions/combinations fail closed. No provider call occurs without the required destination/disclosure authorization. Covers FR-031–FR-032.

AC-017. Runtime inspection and negative tests demonstrate that model-facing components cannot obtain diagnostic credentials or use independent tools to bypass the safety boundary. The deployment demonstrates an independently enforced isolation boundary; a shared process or Go package boundary alone is insufficient. Covers FR-033 and NFR-002.

AC-018. A provider outage or revoked outbound approval preserves local state/report inspection and manual diagnostics, with no silent provider change. Revocation stops new requests, attempts in-flight cancellation, ignores later model responses, and reports that previously transmitted data cannot be recalled. Covers FR-034.

AC-019. Local/stdio MCP discovery exposes exactly the approved enabled subset and curated resources/prompts; equivalent calls preserve local policy and result semantics. An approved Pi standalone client passes real interoperability checks, and protocol-level tests cover required tools, resources, and prompts. CLI session approval, verified client context and egress, one-hour default expiration, revocation/disconnect, and egress teardown are covered by positive and negative tests. Covers FR-035, FR-047.

AC-020. If specialist roles are enabled, scope/budget/context isolation and structured handoffs pass tests, and a versioned evaluation compares their quality, cost, and latency with the single-agent baseline. Otherwise the capability remains disabled. Covers FR-036.

AC-021. The offline evaluation suite runs without cloud/provider credentials and emits versioned scenario results for success, tool selection, unsupported claims, unnecessary calls, and safety. Covers FR-037–FR-038.

AC-022. Operators can correlate planning, task, model, tool, review, and resume events and inspect budgets/usage; missing usage is labeled unknown. Budget exhaustion and cancellation stop further dispatch. Covers FR-039–FR-040.

AC-023. Startup/readiness and rollback exercises verify required/optional capability behavior, credential revocation procedures, protected data lifecycle, and safe runtime shutdown without changing lab workloads. Covers FR-041–FR-042.

AC-024. The product's manual diagnostic paths and the lab's deployment-validation paths pass applicable regression checks. Delivery 1 starts in a new versioned store; incompatible legacy files remain unchanged and operator-managed without automatic import or old approval reuse. Any future import has a separately approved migration and rollback procedure. Covers FR-050, NFR-010–NFR-011, NFR-014.

AC-025. Before model-enabled rollout, the release record identifies the capability matrix, exploratory baseline, versioned evaluation corpus/rubric, quality/latency/cost thresholds pinned before release-candidate evaluation, passing deterministic safety results, required deployed-lab acceptance evidence, and unresolved limitations. At least one authorized real model-backed lab investigation follows approved scope, collects a relevant live observation, preserves provenance and audit, exposes gaps, and makes no unsupported claim or mutation. An honestly inconclusive report can pass; sufficient-evidence scenarios must also test a supported failure domain. No fixture result is represented as deployed validation. Covers FR-037–FR-038, NFR-007, NFR-009, NFR-015.

AC-026. The deployment record verifies the Ubuntu 24.04 x86-64 non-root observer outside the observed cloud, Keystone reachability, project-reader token issuance and project-visible reads, required project-resource/server-basic/server-network live diagnostics, and restricted observer diagnostics on one controller and two compute nodes. It records representative mutation-denial results from an explicitly authorized disposable project/resources with preflight checks and cleanup owner. Enabled operator-reader capabilities have separate live prerequisite and diagnostic evidence; unavailable safe operator-reader access does not block completion. Covers FR-021–FR-022, FR-043.

AC-027. Approved read-only Go project-summary, server-basic, server-network, scheduler/Placement or capacity, Neutron-agent, and recent Nova/Neutron/metadata diagnostics are included and pass applicable offline input, static, and behavioral safety checks. Server basics expose each required field or an explicit unavailable/denied/not-applicable indication. Operator-reader diagnostics are enabled only with validated safe access and otherwise report unavailable; restricted host diagnostics require their separately validated prerequisites and live acceptance. API results are structured where practical, and host output obeys the approved windows and bounds. Covers FR-023–FR-026, FR-044.

AC-028. An operator can perform the documented manual selection, CLI execution, sanitized copy-paste into the Go CLI, and approved harness analysis without automatic tool calling or MCP. Manual, automated, and MCP calls pass the same applicable safety and audit checks. Documentation explains the shared boundary, credential scopes, and the limits of protection when output is shared independently. Covers FR-001, FR-045–FR-046.

AC-029. A deployment validation record demonstrates that one Go runtime executable provides the manual CLI, Go-owned integration with the separately operator-installed Codex/Pi harnesses, local/stdio MCP, and built-in diagnostics without separately installed utilities or interpreters for diagnostic execution. It identifies external services, harnesses and their runtime dependencies, and protected configuration/data prerequisites and includes independent non-root model/credential isolation and managed-client egress evidence. Covers FR-024, FR-031, FR-043, FR-047, NFR-014.

AC-030. Tests exercise the approved MCP-session and investigation-plan lifetimes, explicit name lookup authorization, relationship scope, revocation during active calls, cancellation and result withholding, and data-alias/disclosure policies. No previously transmitted data is claimed to be recalled. Covers FR-003, FR-005, FR-010–FR-011, FR-032, FR-047.

AC-031. Lifecycle tests verify configured storage limits and real disk-full handling; 30-day terminal and 90-day audit defaults; bounded startup/runtime cleanup; protected active-reference exceptions; audit intent/outcome failures; confirmed early deletion without deleting active-dependent evidence or premature audit records; alias-default exports and explicitly authorized identifier exports; and isolation of operator-managed legacy files. Covers FR-048–FR-050.

## Rollout / Migration Plan

1. **Review and approve:** Review Delivery 1 scope, design Go-owned policy/registry enforcement and independently enforceable non-root isolation, and inventory relevant Go behavior before planning delivery. The single Go runtime executable and external operator-managed harness prerequisites remain required.
2. **Secure the core vertical slice:** Deliver explicit scope, one useful server investigation, exact-plan approval where applicable, execution-boundary authorization, structured results, audit/redaction, bounded model access, and an evidence-linked report. Require offline safety tests before any live use.
3. **Make investigations durable:** Harden checkpoint/resume, protected state, retention, context summarization, curated retrieval, failure reporting, and provider-independent inspection. Start the new versioned store while preserving legacy records separately; do not automatically migrate them.
4. **Complete domain and project workflows:** Add metadata/network and volume evidence, dependency-aware multi-server execution, and evidence review. Run offline evaluation scenarios and record capability gaps.
5. **Enable gated integrations:** Validate restricted host access on the required three nodes and operator-reader access independently. Add required local/stdio MCP and Pi interoperability only over proven contracts; keep network MCP exposure and specialist agents disabled unless separately reviewed and justified. Operator-reader diagnostics may remain unavailable when safe access cannot be validated.
6. **Release to the lab:** Use the existing automation/validation approach, pin runtime and adapter versions, perform authorized read-only acceptance, record quality/latency/cost baselines, and publish operational guidance. Deployment administration remains outside the diagnostic agent.
7. **Monitor and rollback:** Track denials, scope violations, incomplete reports, audit/checkpoint failures, timeouts, truncation, unsupported claims, and usage. On safety concerns, stop dispatch, disable affected adapters/tools, revoke credentials/outbound permissions, preserve protected evidence, and restore a validated runtime/configuration.

Do not automatically migrate, index, or delete operator-managed legacy state. A later migration requires separate approval and a tested versioned conversion, backup, and recovery procedure. The product's manual diagnostics should remain available during integration when their independent safety boundary is healthy. Optional specialist roles, parallelism, advanced retrieval, and network service exposure follow measured need rather than the order of a learning syllabus.

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
3. Model-enabled use can be gated independently from manual diagnostic availability; both Codex and Pi integrations and the required real-model acceptance remain in Delivery 1.
4. Specialist roles are optional until measured value exceeds coordination, cost, latency, and security overhead.

### Open decisions

1. What OS-enforced identities, isolation, authenticated IPC, and session-bound egress mechanisms can satisfy the Go-owned gateway, external harness, standalone MCP client, and revocation requirements on the target observer without weakening the specified boundaries?
2. Which operator-configured project, disposable test scope, host aliases, management endpoints, storage limit, approved harness versions, and provider/model combinations will be used for the first acceptance environment?
3. Which exact reader policies and narrowly scoped API relationships support the required project, scheduler/Placement, and capacity evidence in this lab? Unavailable higher-visibility capabilities remain disabled; no admin fallback is permitted.
4. What concrete protected storage, cleanup/audit recovery, and versioned-state designs satisfy the specified lifecycle, active-reference retention, fail-closed quota, and legacy isolation requirements?
5. What evaluated quality, latency, token/cost, and unnecessary-call thresholds define the first model-enabled release? Establish an exploratory baseline and agree the thresholds before release-candidate evaluation; these remain release blockers until agreed.
6. How will local/stdio Pi interoperability, MCP session binding, enforced client egress teardown, and the full protocol tools/resources/prompts contract be independently validated? Network exposure is outside Delivery 1.

These are design, environment, or release-evidence questions, not permission to weaken the settled product and safety decisions. If no feasible design satisfies them, escalate rather than silently changing the requirements.

## Further Notes

The product combines a safe diagnostic toolbox with stateful, evidence-driven investigation and task orchestration. Safety applies from the first executable slice, not only at a later curriculum stage.

The learning baseline supplies the concepts; this PRD supplies observable product requirements. Completion of a lesson, successful model conversation, or plausible diagnosis does not establish production behavior. Deterministic controls, negative tests, scenario evaluations, and explicitly authorized deployed acceptance provide that evidence.

This draft does not approve an implementation, decide unresolved product questions, establish deployed safety, or authorize deployment.
