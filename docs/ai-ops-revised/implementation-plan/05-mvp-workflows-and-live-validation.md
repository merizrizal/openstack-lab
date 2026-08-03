# 05. MVP Workflows and Live Validation

## 05.1 Goal

Turn the project-reader toolbox and runner into repeatable operator workflows, then prove the complete MVP against deployed lab state without allowing AI-requested remediation.

Target outcome:

```text
operator question -> approved tool sequence -> audited structured evidence -> AI explanation -> manual next step -> unchanged lab state
```

## 05.2 Estimate

Total estimate:

```text
1.5-2.5 engineer-days
9-15 focused hours
```

## 05.3 Scope

Included:

* Diagnostic-only AI behavior and refusal guidance.
* Project inventory, server inspection, and metadata-oriented runbooks.
* Clear evidence interpretation and unavailable-data guidance.
* End-to-end runner validation against a deployed lab.
* Negative “fix it” behavior and unchanged-state verification.
* Redacted acceptance evidence for the MVP.

Excluded:

* Automatic AI tool calling.
* Host log evidence not yet approved in Phase 06.
* MCP integration.
* Chat UI implementation.
* Autonomous remediation or operator-command execution.

## 05.4 Assumptions

- [ ] The three revised-copy MVP tools execute only through the accepted revised runner.
- [ ] The revised runtime, runner, profile, audit location, and workflow identifiers are distinct from the prior AI-OPS runtime.
- [ ] A deployed lab contains at least one representative project-visible server.
- [ ] The operator can copy structured results into an approved AI client manually.
- [ ] AI output is advisory and untrusted; a human remains responsible for any remediation outside AI-OPS.

## 05.5 Ordered Tasks

### Step 1 - Define Diagnostic-Only AI Instructions

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] State that the assistant observes, correlates, explains, identifies uncertainty, and recommends manual follow-up only.
- [ ] Require the assistant to select only documented diagnostic tool names and never invent raw commands for execution by the AI boundary.
- [ ] Define refusal behavior for requests to create, update, delete, restart, stop, install, edit, or otherwise fix the lab directly.
- [ ] Require explanations to separate observed evidence, inference, missing evidence, and manual recommendations.
- [ ] Document that AI text does not override credential, allowlist, or operator approval boundaries.

Done when:

- [ ] A reviewer can predict how the assistant responds to both diagnostic and remediation intent.

### Step 2 - Document Project and Server Workflows

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Document the project summary workflow and interpretation of empty, unavailable, forbidden, and failed sections.
- [ ] Document the server basic and server network sequence for one name or ID.
- [ ] Define expected explanation fields: healthy signals, failing signals, likely failure domain, evidence gaps, and manual next steps.
- [ ] Include sanitized result examples for successful and non-success outcomes.
- [ ] Direct operators to the runner rather than raw scripts once the runner is accepted.

Done when:

- [ ] An operator can safely answer what exists and inspect one server without rereading the PRD.

### Step 3 - Build the MVP Metadata Troubleshooting Workflow

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Start with server status, config-drive context, attached ports, fixed IPs, networks, and subnets.
- [ ] Map available evidence to the guest-to-Neutron-proxy-to-Nova-metadata path.
- [ ] Mark Neutron-agent state, recent service logs, Apache listener evidence, and host status as unavailable until Phase 06 controls exist.
- [ ] Require the AI to distinguish guest-side symptoms, network attachment issues, proxy/service hypotheses, and insufficient evidence.
- [ ] End with manual operator recommendations, not executable remediation requests.

Done when:

- [ ] A cloud-init or `169.254.169.254` report produces a safe initial evidence package and a bounded likely-failure analysis.

### Step 4 - Run Deployed-Lab Integration Validation

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Run revised project resource summary through the revised runner.
- [ ] Run revised server basic and server network diagnostics for the same representative server.
- [ ] Verify result schemas, duration, exit code where applicable, correlation ID, and truncation metadata.
- [ ] Verify matching sanitized audit events for each request.
- [ ] Compare relevant project state before and after execution to prove diagnostics caused no mutation.
- [ ] Verify revised calls write only to revised audit/output locations and start no prior-runtime process or service.
- [ ] Record policy, endpoint, or service-version limitations as explicit unavailable evidence.

Done when:

- [ ] The runner produces useful, auditable evidence from live project state without changing it.

### Step 5 - Validate AI Explanation and Refusal Behavior

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Provide redacted result envelopes to the selected manual AI workflow.
- [ ] Verify the explanation cites evidence, labels inferences, and identifies missing host-level data.
- [ ] Submit representative “fix it”, restart, delete, create, and edit-config requests.
- [ ] Verify the assistant returns diagnostic collection or manual recommendations and does not request an unavailable mutation tool.
- [ ] Review output for credential, token, topology, or unnecessary log disclosure.

Done when:

- [ ] The manual AI workflow is useful for diagnosis and consistently remains advisory-only.

### Step 6 - Capture MVP Acceptance and Rollback Evidence

Estimate:

```text
0.25 engineer-days
1.5 hours
```

Tasks:

- [ ] Record the runtime, credential profile class, tool versions, request/result IDs, tests, and observed acceptance outcomes without secrets.
- [ ] Record known gaps deferred to operator/host diagnostics or MCP.
- [ ] Document immediate rollback: disable the runner, revoke application credentials, and remove protected local profile material.
- [ ] Confirm manual scripts cannot remain as an undocumented bypass if the revised runner is disabled for a safety issue.
- [ ] Confirm rollback disables only the revised capability and leaves the preserved prior baseline unchanged unless a separate operator decision retires it.

Done when:

- [ ] Maintainers can independently review MVP evidence and disable all assistant authority if needed.

## 05.6 Phase Definition of Done

This phase is done when:

- [ ] Diagnostic-only AI behavior and “fix it” refusal are documented and tested.
- [ ] Project, server, and metadata-oriented workflows are executable by an operator.
- [ ] All three tools succeed against representative deployed state or return accepted structured limitations.
- [ ] Result and audit contracts are visible end to end.
- [ ] Before/after checks show no lab mutation.
- [ ] Redacted MVP evidence and rollback instructions exist.
- [ ] Coexistence checks prove the revised workflow does not modify, invoke, or overwrite prior-runtime source, services, profiles, audit data, or state.

## 05.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Manual workflow is bypassed in favor of raw commands | Make runner-first procedures the accepted path and explain the safety rationale. |
| AI presents hypotheses as facts | Require explicit evidence, inference, and missing-evidence sections. |
| Metadata diagnosis overclaims without logs | Label host/service evidence unavailable until Phase 06. |
| “Fix it” language causes unsafe tool selection | Test refusal behavior and ensure the registry contains no mutation tool. |
| Acceptance evidence leaks project details | Redact identifiers and retain only the minimum evidence needed. |
