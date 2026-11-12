# 99. Hardening, Validation, and Rollout

## 99.1 Goal

Harden the AI-OPS implementation with safety regression tests, integration validation, operational documentation, audit review, and rollback procedures.

Target outcome:

```text
implemented diagnostics -> safety tests -> deployed-lab validation -> audit review -> documented rollout/rollback -> ready for regular lab use
```

## 99.2 Estimate

Total estimate:

```text
2-4 engineer-days
12-24 focused hours
```

## 99.3 Scope

Included:

* Safety regression test suite across scripts, runner, MCP, orchestrator, and deployment boundaries.
* Fake/real Codex-adapter contract, dependency, redaction, evidence, and vendor-blocker validation.
* Deployed-lab read-only integration validation.
* Verification that the historical provider gateway is disabled or retired according to Phase 13.
* Secret and audit-log review.
* Rollout and rollback documentation.
* Operational support notes for common failures.
* Backlog for post-MVP diagnostics.

Excluded:

* Production-grade multi-user access control.
* Automated remediation.
* Broad observability analytics or anomaly detection.
* Refactoring existing OpenStack deployment roles unless required by safety validation.

## 99.4 Assumptions

- [ ] MVP phases and the selected orchestrator phases are implemented or have documented blockers.
- [ ] Phase 12 remote acceptance is complete or records a bounded vendor blocker.
- [ ] Phase 13 gateway disposition is complete or explicitly deferred with the gateway disabled.
- [ ] A deployed OpenStack Lab is available for integration validation when needed.
- [ ] Existing Molecule validation remains the baseline project validation pattern.
- [ ] Safety issues found in this phase can block rollout.

## 99.5 Ordered Tasks

### Step 1 - Consolidate Safety Regression Tests

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Ensure script syntax checks run for every AI-OPS shell script.
- [ ] Ensure static forbidden-command checks cover mutation, service control, file mutation, package install, generic shell, generic SSH, and unrestricted sudo patterns.
- [ ] Ensure runner tests cover unknown tools, invalid parameters, timeout, truncation, unavailable tools, and audit logging.
- [ ] Ensure MCP tests cover tool discovery, resource discovery, prompt discovery, invalid input, and absence of generic tools.
- [ ] Ensure orchestrator tests cover fake-adapter isolation, schema/state validation, redaction, tool-loop bounds, cancellation, evidence allowlists, and absence of private-protocol handling.
- [ ] Ensure deployment tests cover dedicated identity, protected runtime home, no listener, bounded egress, `assistant` denial, and disabled gateway fallback.
- [ ] Ensure pinned SDK/runtime upgrade tests run locally before any remote reacceptance.
- [ ] Provide a single documented command or test sequence for maintainers.

Done when:

- [ ] A maintainer can run one documented validation sequence before trusting AI-OPS changes.

### Step 2 - Validate Against a Deployed Lab

Estimate:

```text
0.5-1 engineer-days
3-6 hours
```

Tasks:

- [ ] Run project-reader authentication validation from the assistant runtime.
- [ ] Run project resource summary through the runner.
- [ ] Run server basic and server network diagnostics against a representative server.
- [ ] If host diagnostics are enabled, run recent metadata/Nova/Neutron log tools against approved hosts.
- [ ] Verify every run emits structured result envelopes and audit events.
- [ ] Run the deployed orchestrator with the fake adapter through local stdio MCP and verify bounded metadata, cleanup, and no network access.
- [ ] If remote acceptance is approved, verify only its sanitized categories and post-operation validators; do not repeat provider traffic for hardening.
- [ ] Verify no diagnostic changes lab state.
- [ ] Record any policy or endpoint-specific limitations.

Done when:

- [ ] AI-OPS has been proven against live lab state with read-only behavior.

### Step 3 - Add Metadata Regression Workflow

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Create a repeatable validation checklist for metadata/cloud-init diagnostics.
- [ ] Confirm the workflow collects server state and network attachment evidence.
- [ ] Confirm host/log evidence is included when Phase 06 is enabled.
- [ ] Confirm the workflow can distinguish missing Nova metadata listener, Neutron metadata agent errors, and lack of evidence.
- [ ] Confirm the workflow recommends manual action rather than executing remediation.

Done when:

- [ ] The known metadata troubleshooting class has a repeatable AI-OPS diagnostic workflow.

### Step 4 - Review Secrets and Audit Outputs

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [ ] Scan committed AI-OPS files for credential material, tokens, passwords, secrets, and private keys.
- [ ] Review sample result envelopes for secret-like values.
- [ ] Review audit logs for sanitized arguments and absence of secret values.
- [ ] Confirm real credential files are ignored or outside the repository.
- [ ] Confirm orchestrator code, process arguments, environment, evidence, tests, and logs contain no Codex token, account data, prompt, response, tool output, or raw SDK event.
- [ ] Validate Codex runtime-home ownership and modes without reading its contents.
- [ ] Confirm log diagnostics redact known secret-like fields.

Done when:

- [ ] No AI-OPS committed file, audit sample, or diagnostic sample contains real secret material.

### Step 5 - Document Rollout and Rollback

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Document rollout order: runtime, credential, scripts, runner, manual workflow, host diagnostics, MCP, orchestrator contracts, fake-backed integration, sandboxed deployment, controlled acceptance, and gateway retirement.
- [ ] Document rollback steps for each layer.
- [ ] Document how to revoke OpenStack application credentials.
- [ ] Document how to disable host SSH diagnostics.
- [ ] Document how to stop or disable MCP while preserving manual runner use.

Done when:

- [ ] An operator can safely enable or disable AI-OPS without guessing.

### Step 6 - Create Operational Support Notes

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Document common credential failures and how to interpret them.
- [ ] Document common endpoint reachability failures.
- [ ] Document common runner statuses: denied, validation_error, timeout, unavailable, truncated, and error.
- [ ] Document how to review audit logs.
- [ ] Document when to escalate from project-reader tools to operator-reader or host diagnostics.
- [ ] Document Codex login expiry, pinned-version upgrade, bounded SDK/runtime failures, and vendor-blocker escalation without credential or private-protocol inspection.

Done when:

- [ ] Operators can troubleshoot the AI-OPS tooling itself without bypassing safety controls.

### Step 7 - Prepare Post-MVP Backlog

Estimate:

```text
0.25 engineer-days
1.5 hours
```

Tasks:

- [ ] List candidate diagnostics for router namespace info, metadata path checks, volume attach checks, image service checks, Ceph health, OpenSearch search, and Prometheus query access.
- [ ] Classify each candidate by risk and required credential.
- [ ] Require every candidate to follow the same allowlist, validation, timeout, output-limit, and audit model.
- [ ] Mark remediation and self-healing ideas as separate future work outside the current safety boundary.

Done when:

- [ ] Future expansion is captured without creating pressure to weaken the MVP boundary.

## 99.6 Phase Definition of Done

This phase is done when:

- [ ] Safety regression tests pass.
- [ ] Deployed-lab read-only validation passes or documented blockers exist.
- [ ] Metadata regression workflow is documented and validated.
- [ ] Secret scans and audit-output reviews pass.
- [ ] Rollout and rollback docs exist.
- [ ] Operational support notes exist.
- [ ] Post-MVP backlog is classified by risk and credential needs.
- [ ] Orchestrator fake/local/deployment regressions pass and any remote result remains metadata-only.
- [ ] Codex credentials remain opaque and private provider protocol recovery is absent.
- [ ] The historical gateway cannot act as an unreviewed fallback.

## 99.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Safety checks are treated as optional | Make them part of the documented validation sequence and block rollout on failure. |
| Integration validation mutates lab state | Use only read-only tools and credential denial checks; keep mutation tests safe and controlled. |
| Audit logs grow without review | Add cleanup guidance and periodic review notes for lab use. |
| Post-MVP expansion weakens boundaries | Require every new tool to satisfy the same registry, validation, timeout, output-limit, and audit contracts. |
| SDK/runtime upgrades reintroduce opaque integration debugging | Pin versions, run local contract tests first, and classify unsupported behavior as a vendor blocker. |
| Hardening accidentally reads Codex credentials or raw provider data | Validate metadata, permissions, and categories only; prohibit content inspection. |
| Retired gateway becomes an undocumented fallback | Test process/listener absence and ensure no orchestrator configuration references it. |
