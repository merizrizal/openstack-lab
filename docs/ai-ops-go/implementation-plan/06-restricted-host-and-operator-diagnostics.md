# 06. Restricted Host and Operator Diagnostics

**Phase boundary:** PROPOSED.
**Authority:** Roadmap phase, not an approved implementation task contract.
**Source requirements:** [PRD](../prd.md), Diagnostic implementation form; Diagnostic safety and access; Metadata and VM boot cases; Testing Decisions 10–11, 13–14. FR-010–FR-012, FR-019–FR-030, FR-041, FR-043–FR-044; NFR-001–NFR-003, NFR-006–NFR-008, NFR-011, NFR-014–NFR-015; AC-004–AC-005, AC-011–AC-015, AC-026–AC-027, AC-029.
**Decision gaps:** G1 compliant fixed Go-owned host diagnostic mechanism and security contexts; G2 approved controller/compute aliases/endpoints; G3 exact safe reader policies for scheduler/Placement/capacity/Neutron-agent access. Do not assume remote scripts or arbitrary SSH execution are permissible.

## 06.1 Goal

Complete the required reviewed diagnostic catalog, add narrowly constrained host evidence, and validate the mandatory three-host coverage without changing lab workloads.

```text
explicitly approved higher-visibility/host scope + validated profile
  -> fixed bounded Go diagnostic -> sanitized audited evidence
  -> stronger supported finding or explicit unavailable/partial result
```

## 06.2 Estimate

```text
7–11 engineer-days
42–66 focused hours
```

External host/profile provisioning and approval delays are excluded. Live validation effort is included when separately authorized access is available; absence of required host evidence blocks Delivery 1 acceptance.

## 06.3 Scope

Included:

- Reviewed Go scheduler/Placement or capacity diagnostics and Neutron agent health, with mandatory offline safety coverage and conditional live enablement.
- Restricted recent Nova, Neutron and metadata errors, approved host aliases/operation combinations and exact bounded windows.
- Required authorized host validation on one controller and two compute nodes; no storage-host diagnostics.
- Capability readiness and degraded operation integrated with manual/automatic workflows.

Excluded:

- Admin fallback, root SSH, unrestricted sudo, arbitrary destinations/commands/paths, secret-bearing configuration dumps and service/database/RabbitMQ credentials.
- Runtime account creation, package installation, SSH/sudo policy editing and mutation/fault injection in the working lab.
- Requiring operator-reader enablement when safe access cannot be validated; required offline catalog and host acceptance are not waived.

## 06.4 Assumptions

- [ ] Phase 01’s boundary and Phase 05’s catalog/workflows are proven before higher-visibility operations are exposed.
- [ ] Operator-controlled provisioning can establish equivalent restricted non-root observer identities and permitted read-only operations on the required hosts.
- [ ] A reviewed Go-owned mechanism can satisfy host diagnostics without separately deployed diagnostic scripts, interpreters or CLI utilities. If infeasible, escalate before implementation rather than weaken the PRD.
- [ ] API and host credentials are separately scoped; failed access never triggers a stronger profile or an alternate execution mechanism.

## 06.5 Ordered Tasks

### Step 1 - Establish explicit profile, host and operation readiness

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Following approved specifications, define separate project-reader, optional operator-reader and restricted SSH-observer capability prerequisites with explicit credentials/identity ownership and approved routes.
- [ ] Bind fixed host aliases to approved service placement and allowed diagnostic operations; do not expose caller-selected SSH destination, account, path, command or sudo options.
- [ ] Design/implement only the approved fixed Go-owned host transport/operation contract. Any required privileged account, sandbox or host setup is an operator action outside the diagnostic agent.
- [ ] Reject unsupported host/operation combinations and missing access as unavailable/denied, not a route to root, admin, unrestricted files or legacy diagnostic collectors.
- [ ] Publish actionable readiness and a capability matrix with enabled/unavailable reasons; no plan may infer host approval merely from an observed server-host relationship.

Done when:

- [ ] Negative profile/host/operation fixtures prove no unauthorized connection or alternate dispatch, and operator setup responsibilities are separate from runtime capabilities.

### Step 2 - Add the gated catalog with strict windows and bounds

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Provide reviewed narrow scheduler/Placement or capacity and Neutron-agent Go capabilities, with schema, exact visibility, profile, risk, timeout, output bounds and tool-local validation.
- [ ] Keep them disabled/unavailable unless safe reader access is independently validated; include their offline contracts even if the live operator-reader profile remains unavailable.
- [ ] Add fixed recent Nova/Neutron/metadata error operations appropriate to approved controller/compute placement. Accept only 15 minutes, 30 minutes or 1 hour, defaulting to 30 minutes, with finite lines/bytes/time.
- [ ] Sanitize logs/snippets before local persistence, audit, model or export, withholding unsafe content; distinguish source event time, collection time and truncation.
- [ ] Apply the common gateway rechecks, audit intent/outcome, revocation/cancellation and result semantics to all higher-visibility calls. No generic file or command capability is introduced.
- [ ] Perform static and behavioral mutation/injection/path/privilege/secret tests, including wrong host, unsupported operation/window, output floods and denied credentials.

Done when:

- [ ] Full required catalog passes offline safety coverage, and every unavailable prerequisite produces an honest structured limitation without fallback.

### Step 3 - Strengthen domain findings without overclaiming

Estimate: **1–2 engineer-days / 6–12 hours**.

- [ ] Add higher-visibility evidence steps to reviewed boot/metadata/network workflows only when explicitly included in approved scope/capabilities/budgets; expanded plans require fresh exact approval.
- [ ] Correlate authorized scheduler/Placement/capacity data with NoValidHost, distinguishing observed faults from directly supported failure domains.
- [ ] Correlate restricted Neutron/Nova/metadata evidence along the actual metadata path; healthy agents cannot prove listener availability. Collect direct permitted supporting evidence or state the gap.
- [ ] Add sufficient-evidence, contradictory, stale, denied and unavailable-host/operator fixtures with review outcomes and plain-language manual recommendations.

Done when:

- [ ] Direct evidence supports stronger findings where present, while absent host/operator access produces partial/inconclusive reports rather than invented confirmation or privilege escalation.

### Step 4 - Validate restricted access on the required lab hosts

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Obtain separate operator authorization for live read-only validation, exact hosts, credentials, permitted operations and evidence handling. Review preflight safety and rollback/revocation procedures before connecting.
- [ ] Verify restricted diagnostics on one approved controller and two approved compute nodes, including identity, permitted combinations/windows, output bounds, denied paths/operations and no unrestricted sudo/root access.
- [ ] Validate operator-reader diagnostics separately if enabled and safely provisioned; otherwise record unavailable access as an allowed limitation, not skipped catalog implementation.
- [ ] Record authorized live evidence with runtime/policy/profile versions, target aliases, timestamps, statuses and sanitized audit/provenance references. Do not induce a working-lab failure to reproduce fixture incidents.
- [ ] Carry the required host evidence to Phase 08’s deployment acceptance record. If it cannot be obtained, mark this acceptance incomplete; offline fixtures cannot replace it.

Done when:

- [ ] All three required hosts have separately authorized validation evidence, or an explicit blocking evidence/access gap is recorded without claiming phase/live acceptance completion.

## 06.6 Phase Definition of Done

- [ ] Reviewed Go project/operator/host catalog is complete and passes applicable offline static/input/behavioral safety tests.
- [ ] Enabled host diagnostics accept only fixed approved combinations and exact windows/bounds through the same gateway.
- [ ] Required controller/two-compute live restricted-access evidence is recorded; missing evidence blocks full phase acceptance and Delivery 1 release.
- [ ] Optional operator-reader enablement is supported only by independent safe-access evidence; otherwise it stays unavailable.
- [ ] Reports distinguish supported scheduling/metadata failure domains from missing evidence, and no host administration or workload mutation is exposed.

## 06.7 Risks

| Risk | Mitigation |
| --- | --- |
| Host collection depends on old Python/shell collectors | Require a compliant Go mechanism before authorizing implementation; no hidden utility dependency. |
| “Read-only sudo” grants broad execution | Review fixed operations, account restrictions and negative live tests independently. |
| Operator-reader scope exposes excessive control-plane data | Narrow API contracts and separate enablement evidence; unavailable is acceptable. |
| Missing host validation is treated like optional operator access | Track required three-host acceptance separately; release remains blocked. |
| Testing damages working workloads | Read-only validation only; any policy mutation-denial probes use separately approved disposable scope in 08. |

## 06.8 Proposed Requirement Coverage and Handoff

| Requirement / AC source | Proposed phase responsibility | Existing behavior / deferral | Risk or unapproved decision |
| --- | --- | --- | --- |
| FR-022/025–FR-026/043–FR-044; AC-013/026/027 | Complete gated catalog and mandatory three-host validation | Existing deployment scripts are not adopted diagnostic implementations | G1–G3 fixed mechanism, identity and policy choices. |
| FR-010–FR-012/019–FR-020; AC-004/005 | Scoped domain integration and direct-evidence findings | Project workflows from 05; stronger evidence remains conditional | No automatic host authority from discovery. |
| FR-023–FR-024/027–FR-029; AC-012/014/015/029 | Same Go validation/result/audit/privacy boundary | MCP parity follows in 07, packaging proof integrates in 08 | No alternate host collector or bypass. |
| FR-021/041; AC-011/026 | Live readiness/profile evidence | Full observer/project/disposable-policy acceptance in 08 | Absent required host evidence is a release blocker. |

Proposed handoff to Phase 07: manually trusted full catalog, enabled/unavailable matrix, host/operator validation records and domain review fixtures. Independent scope readiness and a separate approved task contract are still required; this phase file is neither.
