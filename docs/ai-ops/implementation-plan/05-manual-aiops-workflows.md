# 05. Manual AI-OPS Workflows

## 05.1 Goal

Make the MVP usable by documenting and validating repeatable diagnostic workflows that use the approved toolbox and local runner before MCP automation exists.

Target outcome:

```text
operator question -> approved tool sequence -> local runner outputs -> AI explanation prompt -> manual recommendation only
```

## 05.2 Estimate

Total estimate:

```text
1-2 engineer-days
6-12 focused hours
```

## 05.3 Scope

Included:

* Document the manual and local-runner workflows.
* Add initial troubleshooting workflows for project summary, server inspection, and metadata failure diagnosis.
* Add AI prompt guidance that forbids remediation execution.
* Validate the MVP flow with a real or representative OpenStack server.
* Capture redacted sample outputs and expected interpretations.

Excluded:

* MCP integration.
* Chat UI implementation.
* Host-level SSH log diagnostics unless already available.
* Automatic selection and execution by an AI client.

## 05.4 Assumptions

- [ ] The local runner can execute project-resource, server-basic, and server-network tools.
- [ ] At least one project-visible server exists for validation, or a representative deployed lab can be used.
- [ ] The operator is willing to copy results into an AI chat manually for the MVP.
- [ ] AI recommendations remain text only and do not execute fixes.

## 05.5 Ordered Tasks

### Step 1 - Document the Diagnostic-Only Assistant Behavior

Estimate:

```text
0.25 engineer-days
1.5 hours
```

Tasks:

- [ ] Write the assistant behavior policy: observe, explain, recommend manual actions, never mutate.
- [ ] Include explicit refusal guidance for “fix it”, “restart it”, “delete it”, “create it”, and “edit config” requests.
- [ ] List approved MVP tools and their purpose.
- [ ] List unavailable/deferred tools so operators understand current limits.

Done when:

- [ ] A user can understand what the AI-OPS MVP can and cannot do before running it.

### Step 2 - Add Basic Project Inspection Workflow

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Document when to run project resource summary.
- [ ] Document how to interpret empty or permission-denied output.
- [ ] Document how to pass the output to an AI assistant for explanation.
- [ ] Include a redacted sample successful output or summary.

Done when:

- [ ] An operator can use the MVP to answer “what exists in this project?” safely.

### Step 3 - Add Server Inspection Workflow

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Document how to run server basic info for a server name or ID.
- [ ] Document how to run server network info for the same server.
- [ ] Document how to identify server status, attached networks, fixed IPs, ports, config-drive clues, and permission errors.
- [ ] Include expected next questions the AI should ask when output is incomplete.

Done when:

- [ ] An operator can collect enough read-only evidence to discuss one server’s state and network attachments with AI.

### Step 4 - Add Metadata Troubleshooting Workflow

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Convert the existing metadata troubleshooting knowledge into an MVP-safe workflow using available tools.
- [ ] Document which evidence comes from project-reader tools and which evidence remains deferred until host/log diagnostics exist.
- [ ] Include an AI explanation prompt that asks for healthy signals, failing signals, likely failure domain, and manual next steps.
- [ ] Ensure the workflow does not ask the AI to restart services, edit config, or run raw commands.

Done when:

- [ ] An operator can begin debugging `169.254.169.254` or cloud-init metadata symptoms using the approved MVP tools.

### Step 5 - Validate the Full MVP Workflow

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Run project resource summary through the tool runner.
- [ ] Run server basic info against a project-visible server.
- [ ] Run server network info against the same server.
- [ ] Confirm structured results and audit events are produced.
- [ ] Paste or provide redacted outputs to an AI assistant and verify it gives explanation and manual recommendations only.
- [ ] Record any confusing output or missing evidence as follow-up work.

Done when:

- [ ] The MVP path is demonstrated end-to-end without MCP and without system mutation.

## 05.6 Phase Definition of Done

This phase is done when:

- [ ] Manual AI-OPS usage documentation exists.
- [ ] Project summary, server inspection, and metadata-oriented workflows are documented.
- [ ] The AI behavior policy forbids remediation execution.
- [ ] The local-runner MVP workflow has been validated with representative data.
- [ ] Structured results and audit events are visible to the operator.
- [ ] Remaining gaps are documented for host diagnostics or MCP phases.

## 05.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Manual workflow feels less impressive than autonomous AI | Treat it as the safety and learning milestone before MCP. |
| AI suggests unsafe remediation text too confidently | Use explicit prompt policy and ask for manual recommendations with risk notes. |
| Metadata workflow lacks host log evidence in MVP | Label host/log checks as deferred to Phase 06 rather than adding unsafe SSH now. |
| Users bypass the runner and run raw commands | Documentation should show runner-first examples and explain the safety reason. |