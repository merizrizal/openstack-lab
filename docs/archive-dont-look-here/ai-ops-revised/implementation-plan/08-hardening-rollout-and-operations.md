# 08. Hardening, Rollout, and Operations

## 08.1 Goal

Consolidate AI-OPS safety checks into repository quality gates, prove live read-only behavior, establish secure operations and rollback, and define how future diagnostics can be added without weakening the boundary.

Target outcome:

```text
complete capability -> consolidated safety gates -> live regression evidence -> controlled rollout -> observable operations -> governed expansion
```

## 08.2 Estimate

Total estimate:

```text
2.5-4.5 engineer-days
15-27 focused hours
```

## 08.3 Scope

Included:

* Consolidated static, unit, integration, and deployed-lab validation.
* Compatibility checks with existing Ansible and Molecule workflows.
* Credential, file-permission, output, resource, and audit security review.
* Metadata workflow regression and negative remediation tests.
* Rollout, rollback, revocation, support, and audit-review procedures.
* Monitoring for denial, failure, timeout, truncation, and authorization trends.
* Risk-based governance for adding new diagnostics.

Excluded:

* Autonomous remediation, self-healing, anomaly detection, or predictive operations.
* Public/multi-user MCP service design.
* Full production compliance certification.
* Local-model capacity and lifecycle work.
* Broad observability integrations before separate tool review.

## 08.4 Assumptions

- [ ] Required earlier phases are complete or optional capabilities are explicitly disabled and reported unavailable.
- [ ] The prior implementation remains the immutable comparison baseline until a separate retirement decision; hardening applies only to the selectively built revised implementation.
- [ ] A deployed OpenStack Lab is available for runtime acceptance checks.
- [ ] Existing Molecule smoke/e2e workflows remain the primary deployed-system quality seams.
- [ ] Any safety failure can block rollout and trigger credential or interface revocation.

## 08.5 Ordered Tasks

### Step 1 - Consolidate Repository Safety Checks

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Provide one documented validation sequence for diagnostic syntax, forbidden-operation scans, unit tests, runner tests, MCP tests, and configuration checks.
- [ ] Ensure forbidden patterns cover mutation, package install, service control, file mutation, eval/shell, generic SSH/OpenStack/sudo, and database/message-bus access.
- [ ] Ensure negative tests cover unknown tools, malformed registries, unsafe arguments, wrong profiles, arbitrary hosts, timeout, truncation, unavailable capabilities, and secret redaction.
- [ ] Add targeted checks to existing CI where they do not require a live lab.
- [ ] Keep live credentials and raw runtime evidence out of CI artifacts.

Done when:

- [ ] Maintainers can run one repeatable local/CI sequence that blocks known safety regressions.

### Step 2 - Integrate With Existing Deployment Validation

Estimate:

```text
0.5-1 engineer-days
3-6 hours
```

Tasks:

- [ ] Add revised inventory/configuration validation under distinct identifiers without changing the prior AI-OPS validation or replacing existing lab checks.
- [ ] Add read-only runtime smoke checks at the appropriate existing Molecule seam.
- [ ] Keep tests requiring a deployed lab optional and explicitly gated, consistent with current smoke/e2e conventions.
- [ ] Verify existing OpenStack and Ceph validation commands and prior AI-OPS validation entrypoints remain unchanged after revised integration.
- [ ] Add coexistence checks for repository paths, inventory groups/variables, runtime users/paths, service names, profile names, key names, audit locations, ports/listeners, and MCP client registrations.
- [ ] Document which checks are static, fixture-based, runtime smoke, and deployed-lab end-to-end.

Done when:

- [ ] AI-OPS participates in repository quality gates while existing deployment behavior remains compatible.

### Step 3 - Run Security and Secret Review

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Scan committed files and retained evidence for credentials, tokens, passwords, private keys, connection strings, and secret-bearing configurations.
- [ ] Verify credential, SSH key, workspace, audit, and process runtime permissions.
- [ ] Review environment inheritance, process arguments, errors, results, MCP logs/resources, and revised audit events for disclosure.
- [ ] Verify no live credential, key, raw audit event, secret-bearing state, or unredacted evidence was copied from the prior runtime.
- [ ] Re-run project-reader and operator-reader mutation-denial checks after policy or OpenStack upgrades.
- [ ] Verify no generic command, network MCP listener, admin credential, root SSH, unrestricted sudo, database credential, or RabbitMQ credential is available.

Done when:

- [ ] A security review confirms least privilege, deny-by-default behavior, and no known secret leakage.

### Step 4 - Run Live Workflow Regressions

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Run project summary, server basic, and server network workflows against representative deployed state.
- [ ] Run operator/host diagnostics only when their separately protected profiles are enabled.
- [ ] Exercise the metadata workflow and verify evidence distinguishes or bounds likely Nova, Neutron, guest/network, and unavailable domains.
- [ ] Verify result/audit correlation for allowed, denied, invalid, failed, timed-out, unavailable, and truncated fixture or live cases.
- [ ] Compare relevant state before and after diagnostics and confirm no mutation.
- [ ] Test “fix it” intent through manual and MCP workflows and verify advisory-only behavior.

Done when:

- [ ] External behavior and safety boundaries are proven against representative lab state.

### Step 5 - Define Controlled Rollout and Rollback

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Roll out the revised implementation in order: minimal runtime, fresh project-reader, accepted manual tools, revised runner, MVP workflows, optional fresh operator/host access, then local stdio MCP.
- [ ] Require an acceptance checkpoint before each increase in authority or automation.
- [ ] Document rollback for each layer: disable MCP, disable runner, remove host observer access, revoke operator-reader, revoke project-reader, and disconnect/destroy runtime.
- [ ] Verify rollback does not alter OpenStack resources, prior AI-OPS source/runtime state, or leave revised credentials and orphan processes.
- [ ] Define emergency stop ownership and conditions for immediate revocation.

Done when:

- [ ] Operators can enable or disable each safety layer independently without guessing.

### Step 6 - Add Operational Observability and Support Notes

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Document interpretation of denied, validation-error, unavailable, error, timeout, and truncation statuses.
- [ ] Define periodic review of audit events, authorization failures, denied requests, timeout rates, and truncation rates.
- [ ] Define audit rotation/retention and safe evidence preservation.
- [ ] Document credential expiry, endpoint failures, policy drift, service-placement changes, observer access failures, and MCP lifecycle troubleshooting.
- [ ] Ensure support procedures never recommend bypassing the runner or installing broader credentials.

Done when:

- [ ] Operators can diagnose the diagnostic system itself without weakening its controls.

### Step 7 - Govern Future Diagnostic Expansion

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Create a review checklist requiring intent, read-only operation proof, profile, risk class, schema, timeout, output bound, redaction, audit, tests, and rollback for every new tool.
- [ ] Prioritize router/network path, VM boot, volume attach, image, Ceph health, OpenSearch query, and Prometheus query candidates by value and authority.
- [ ] Require manual trust before runner registration and runner trust before MCP exposure.
- [ ] Require observability queries to be bounded and read-only with separate data-source credentials.
- [ ] Keep remediation, local-model hosting, anomaly detection, and self-healing in separate future requirements and security reviews.

Done when:

- [ ] New revised diagnostics have a repeatable path that cannot bypass the revised safety contracts.

## 08.6 Phase Definition of Done

This phase is done when:

- [ ] Static and fixture-based safety checks run through a documented local/CI sequence.
- [ ] A source catalog and selective-reuse manifest exist, every reused path maps to a current requirement and validation owner, and the prior source/runtime remains unchanged.
- [ ] Existing inventory, Molecule, bootstrap, and deployed-lab validation paths remain compatible.
- [ ] Security and secret reviews pass.
- [ ] Live API, optional host, metadata, audit, and refusal regressions pass or have explicit blocking issues.
- [ ] Layered rollout, emergency stop, credential revocation, and rollback are documented and tested.
- [ ] Audit review and common support procedures exist.
- [ ] Future tools must pass the same manual, runner, MCP, credential, limit, redaction, audit, and test gates.

## 08.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Safety checks remain optional | Put non-live checks in CI and require live gates before runtime rollout. |
| Runtime checks mutate state accidentally | Use only approved diagnostics and safe credential-denial procedures with before/after verification. |
| Audit data grows or leaks details | Minimize fields, protect permissions, rotate, and retain only redacted evidence. |
| OpenStack upgrades change reader policy | Re-run the access matrix and block tools whose authority is no longer proven. |
| Expansion weakens deny-by-default behavior | Require the full review checklist and manual-before-runner-before-MCP progression. |
| Prior and revised paths collide or the revised runtime invokes prior state | Validate distinct source, automation, runtime, identity, credential, key, service, audit, listener, and MCP identifiers. |
| Selective reuse drifts into undocumented historical dependencies | Keep the reuse manifest current, test dependency boundaries, and require a new approved requirement before expanding selection. |
| Prior baseline is modified accidentally | Add source-tree and runtime coexistence checks and block rollout on unexpected prior-state changes. |
