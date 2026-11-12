## Architectural Design Specification: Phase 06 Completion and Phase 05 Prerequisite Closure

**Source:** `docs/ai-ops-revised/implementation-plan/06-restricted-operator-and-host-diagnostics.md`, the Phase 06 live-acceptance requirements and operations contracts, and the unresolved Phase 05 prerequisite carried by the Phase 06 validation producer.

**Goal:** Finish, deploy, validate, and obtain owner acceptance for the complete Phase 06 seven-tool diagnostic capability while closing the contradictory Phase 05 prerequisite evidence. This ADS replaces repeated readiness-only work with one finite completion campaign: implement every missing live path, collect one complete owner authorization package, execute the ordered acceptance scopes, reconcile evidence, and establish an objective Phase 07 entry decision.

---

### I. Overview and Contract

The completion path is:

```text
verified Phase 05 acceptance evidence
  -> executable live source and authority paths
  -> protected operator-reader and observer materialization
  -> one complete owner authorization/readiness package
  -> ordered deployment and live validation scopes
  -> positive, negative, audit, unchanged-state, and rollback evidence
  -> representative seven-tool workflow
  -> owner acceptance and checklist reconciliation
  -> Phase 07 entry gate
```

This ADS starts from the completed static/synthetic boundary in `06-01`. It does not authorize another round of compile-safe stubs that deliberately return `unavailable`. Every implementation chunk after discovery must remove at least one named blocker and leave its covered path executable behind a default-disabled, explicit authorization gate.

#### Completion invariant

Phase 06 is complete only when all of the following are true for one current run:

1. Phase 05 acceptance is represented by one non-contradictory, owner-accepted outcome reference.
2. All seven registered tools have executable local/deployed paths; supported live capabilities do not return a placeholder `authorization_pending`, `collector_stub`, or `approved_optional_capability_absent` result.
3. Operator-reader and host-observer authorities are independently deployable, validated, and revocable.
4. The protected projection, key, collector, policy, and profile pass ownership, mode, regular-file, non-symlink, freshness, and revision checks.
5. All 11 Phase 06 scopes have separately named approvals in one owner-provided authorization package.
6. Positive diagnostics pass or return an explicitly accepted `empty` result; all 18 negative observer controls are denied.
7. Result/audit correlation, redaction, unchanged-state, evidence recording, and rollback/revocation pass.
8. The representative seven-tool metadata workflow completes without an unresolved required evidence gap.
9. The named evidence owner records `accepted` for the exact run and source revisions.

Anything less is `blocked`, `unavailable`, or `failed`; static tests, a readiness manifest, or playbook completion alone are not acceptance.

#### Single authorization-package contract

To avoid repeated authorization interviews, the owner prepares one package before live execution. It contains separate entries—not one broad approval—for:

- `prerequisite_readiness`;
- `operator_reader_deployment`;
- `observer_deployment`;
- `host_source_contact`;
- `positive_validation`;
- `negative_boundary_validation`;
- `outcome_evidence_recording`;
- `protected_audit_inspection`;
- `unchanged_state_comparison`;
- `revocation_rollback`; and
- `representative_workflow`.

The package may pre-authorize the complete ordered campaign. Once the applicable gate passes, execution proceeds scope by scope without requesting the same decisions again. A scope still stops on a safety failure, stale revision, missing protected input, unexpected mutation, or revoked approval.

#### Two-stage readiness sequencing contract

The current readiness rule is circular: it requires deployed operator-reader/observer target integrity to be `passed` before the deployment scopes that create those targets. This ADS resolves the cycle without treating an unchecked target as ready:

1. **Campaign authorization gate:** before deployment, validate the complete 11-scope approval set, current run/revision references, timestamps, deployment-source integrity, owner labels, and rollback ownership. This gate authorizes only the two deployment scopes. It does not claim runtime readiness or Phase 06 acceptance.
2. **Runtime readiness gate:** after operator-reader and observer deployment, evaluate all 8 existing integrity checks against deployed state. Only then materialize the existing closed `ready` manifest and permit host/source contact and subsequent live scopes.

Both gates consume the same owner package and run ID. The authoritative readiness requirement, validator/materializer semantics, operations contract, and tests must be reconciled to this sequence before live execution. Deployment failure prevents the runtime manifest from being written. Any revision change invalidates both gates and requires a fresh run.

#### Phase 05 closure contract

The Phase 05 plan records all definition-of-done items complete. The remaining problem is contradictory Phase 06 producer state: `phase05_acceptance_confirmed: true` is emitted together with `phase05_acceptance_pending`.

**Evidence Contract (Concrete):** the current Phase 06 validation result has one boolean Phase 05 acceptance field and a closed unresolved-gate list.

The corrected producer must obey this invariant:

```text
phase05_acceptance_confirmed == true
  -> phase05_acceptance_pending is absent

phase05_acceptance_confirmed == false
  -> phase05_acceptance_pending is present
```

The boolean must come from an owner-provided Phase 05 acceptance outcome/reference, not a hard-coded success. If the referenced Phase 05 evidence cannot be validated, the value remains false and Phase 06 stops before authority deployment.

#### Live collector contract

**Function Signature Contract (Concrete):** the existing collector entry point is:

```python
run(argv=(), environment=None, raw_request=b"") -> tuple[int, dict]
```

Its current implementation validates the invocation/request and always returns `unavailable/authorization_pending`. The completed implementation must:

1. reject arguments and `SSH_ORIGINAL_COMMAND` before source access;
2. load only the fixed root-owned host policy and non-transport collector metadata;
3. resolve the fixed tool-to-source selector and host-role relationship;
4. invoke only fixed source adapters for the approved metadata, Neutron, and Nova sources;
5. enforce the frozen D05-D07 windows, line/record/message/byte limits and timeouts;
6. redact and canary-check before transport;
7. return the existing closed schema and exit-code mapping; and
8. never fall back to arbitrary paths, units, commands, sudo, or broader sources.

**Source Adapter Contract (Conceptual):** exact helper names are confirmed during Chunk 0, but adapters must have the equivalent boundary:

```text
read_approved_source(fixed_policy_entry, fixed_bounds, collection_started_at)
  -> bounded source records | normalized source failure
```

A caller cannot supply the policy entry, path, service unit, command, timeout, or output cap. Missing/unreadable approved sources produce bounded `unavailable` or `denied`, never source broadening.

#### Authority materialization contract

The operator-reader deployment must replace the current intentional failure with guarded, idempotent materialization from:

```text
/run/openstack-ai-ops/<run-id>/operator-reader/
```

into:

```text
/opt/openstack-ai-ops-assistant/credentials/operator-reader/
```

Only `clouds.yaml` and `secure.yaml` are accepted. The source and destination contracts remain `0700` directories and `0600` regular, non-symlink files. Source material is removed after successful target verification. Credential contents remain under `no_log` and outside retained evidence.

The observer deployment must create only the approved `aiops-host-observer` group/account, `nologin` shell, dedicated public key entry with exact `/32` source restriction, forced collector, disabled forwarding/PTY options, root-owned collector, and root-owned policy. `sudo_required` remains false. It must support host-by-host disablement and complete removal without affecting project-reader or operator-reader authority.

#### Acceptance evidence contract

The normalized producer result remains:

```text
/run/openstack-ai-ops/phase06-validation/<run-id>.json
```

Retained evidence remains beneath:

```text
/opt/openstack-ai-ops-assistant/evidence/phase06/
```

The final record may contain only run/reference/revision labels, tool and scope outcomes, result/audit booleans, limitation classes, unchanged-state result, rollback result, and final acceptance. It must not contain addresses, identifiers, commands, raw logs, source payloads, credentials, keys, projection contents, audit lines, or comparator data.

#### Phase 07 entry contract

Phase 07 implementation may begin only when a single final Phase 06 record states `accepted` and references:

- the reconciled Phase 05 acceptance outcome;
- all seven tool acceptance outcomes;
- all 11 completed scope outcomes;
- all 18 denied negative controls;
- passed audit, redaction, unchanged-state, rollback, and representative-workflow outcomes; and
- the exact accepted registry, collector, connector, policy, projection, profile, and source revisions.

Planning Phase 07 remains allowed. MCP implementation, registration, or exposure is prohibited before this record exists.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops-revised/implementation-plan/05-mvp-workflows-and-live-validation.md` marks every Phase 05 task and definition-of-done item complete.
- `ansible/ai_ops_assistant/playbook_produce_restricted_diagnostics_validation.yml` currently emits `phase05_acceptance_confirmed: true` while adding `phase05_acceptance_pending` to `unresolved_gates`.
- `docs/ai-ops-revised/implementation-plan/06-restricted-operator-and-host-diagnostics.md` explicitly identifies that contradiction as a Phase 06 acceptance blocker.
- `06-01` and Handoffs 164-169 establish that registry, connector, synthetic collector slices, deployment wiring, workflow fixtures, readiness validator, gate, and materializer are present and statically validated.
- `host_observer_collector.py` still returns `unavailable/authorization_pending` from `run()` and opens no live source.
- `roles/ai_ops_assistant_operator_identity_boundary/tasks/main.yml` deliberately fails whenever operator-reader materialization is enabled.
- The observer role validates and copies the collector but does not yet create the observer account, authorized-key forced-command policy, protected host policy, or full lifecycle state.
- The readiness materializer defaults its approvals to `[]`, protected references to `{}`, integrity checks to `{}`, and timestamps to `unconfirmed`; its prior bounded execution correctly wrote no manifest.
- The current readiness requirement requires all 8 deployed-state integrity outcomes to pass before any live scope while ordering operator-reader and observer deployment after readiness. This is a circular gate and must be reconciled before execution.
- The Phase 06 readiness requirement defines 11 ordered scopes, 6 protected revision references, 8 integrity checks, 18 negative controls, and the final acceptance decision rule.
- The current Git branch is `ai-ops-assistant-phase06`; the new ADS path did not previously exist.

#### Assumptions requiring confirmation in Chunk 0

1. The owner can provide the existing Phase 05 outcome-only evidence reference or explicitly re-run only the missing acceptance check.
2. Approved local host source commands can be expressed as fixed argv without shell evaluation and are available on the target Ubuntu/OpenStack nodes.
3. The protected policy can map approved logical selectors to exact paths/units without placing protected values in Git.
4. The administrator can provide fresh operator-reader files, observer key material, destination projection, inventory projection, and `/32` restriction through external protected procedures.
5. `controller01`, `compute01`, and `compute02` are reachable only through the approved maintained projection and can be placed in `ai_ops_host_observers` for the bounded campaign.
6. One owner authorization package may pre-authorize all separately named scopes while preserving ordered stop conditions.
7. A representative project-visible server exists; Phase 06 will not create one.

Any rejected assumption becomes a concrete Chunk 0 blocker with an owner and required resolution. It must not create another indefinite design phase.

### III. Required Technical Dependencies and Imports

No new third-party Python package is required or approved.

Required repository components:

- existing seven-tool registry and `aiops_tool_runner.py`;
- `host_observer_connector.py` and `host_observer_collector.py`;
- readiness validator, materializer, and gate playbooks;
- operator identity and host-observer Ansible roles;
- Phase 05 and Phase 06 validation/evidence playbooks;
- focused tests under `ansible/ai_ops_assistant/tests/phase06` and `tests/tool_runner`;
- authoritative Phase 05/06 plans, ADS files, operations contracts, and runbook.

Required runtime dependencies:

- approved Python environment for repository validation: `<user defined Python Venv>`;
- standard-library Python on the assistant and observer hosts;
- fixed OpenSSH client path already enforced by the connector;
- Ansible inventory and protected extra-vars supplied outside Git;
- owner-controlled OpenStack credentials, observer key, projection, policy, attestations, and evidence storage;
- approved service/log access available to `aiops-host-observer` without sudo.

Exact commands used by source adapters must be selected from utilities already installed on target hosts and fixed in protected policy. No shell, generic journal/file reader, caller-defined executable, or additional network service is introduced.

### IV. Step-by-Step Procedure / Execution Flow

1. Freeze one baseline: current branch, complete diff, accepted source revisions, existing static test results, and all protected/generated files excluded from Git.
2. Resolve Phase 05 evidence and readiness sequencing. Validate the Phase 05 outcome reference, fix the producer invariant, split campaign authorization from post-deployment runtime readiness, and rerun focused prerequisite tests.
3. Implement fixed live source adapters and replace the collector's unconditional unavailable return with policy-gated execution for all three approved diagnostics.
4. Validate source adapters entirely with injected/fake fixed readers first, including malformed output, denied reads, timeout, truncation, redaction canaries, and prohibited-source attempts.
5. Complete operator-reader profile deployment, integrity verification, source cleanup, explicit tool selection, mutation-denial linkage, rotation, and independent revocation behavior.
6. Complete observer deployment: account/group, public key restriction, forced command, collector, protected policy, host inventory projection, disablement, and removal.
7. Complete the Phase 06 validation/evidence orchestrator so it covers all seven tools, exact result/audit pairing, positive and negative paths, unchanged-state attestations, and rollback outcomes.
8. Run full static, unit, integration-fixture, Ansible syntax, and security regression validation. No live campaign starts while any implementation-readiness test fails.
9. Obtain one owner package containing all 11 separately named approvals, 6 current revision references, fresh timestamps, deployment-source integrity outcomes, and exact run/reference/class labels.
10. Run the campaign authorization gate. A failed gate stops before deployment; changed inputs require a fresh run ID/package.
11. Deploy operator-reader authority to `assistant02`, verify metadata and named-tool isolation, then remove the transient source.
12. Deploy observer state only to the approved observer hosts and validate exact file/account/key/policy metadata.
13. Evaluate all 8 deployed-state integrity checks, materialize the runtime readiness manifest, and run its gate. Write no ready manifest if any check fails.
14. Contact one approved host/source pair and stop if transport, source policy, redaction, or audit behavior differs from the accepted contract.
15. Execute positive validation for each required tool/host/source mapping and retain only normalized outcomes.
16. Execute all 18 negative controls. Any unexpected success triggers immediate revocation and fails the run.
17. Record outcome-only evidence, inspect protected audit outcomes under its approved scope, and obtain the post-run unchanged-state attestation.
18. Rehearse independent operator-reader and observer revocation/rollback, then restore only through the approved rotation/redeployment path if the representative workflow still requires authority.
19. Execute the representative seven-tool workflow, preserving unavailable/truncated/contradictory evidence as explicit gaps and producing advisory-only interpretation.
20. Have the named evidence owner decide `accepted`, `blocked`, or `failed` from the closed outcome set.
21. On `accepted`, reconcile Phase 05/06 plan checkboxes and operations-contract status, delete transient readiness/profile inputs according to policy, and permit Phase 07 implementation.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| --- | --- | --- | --- |
| Baseline | Existing diff or generated/protected content is not understood | Stop before edits; classify and preserve unrelated work | `PHASE06_BASELINE_BLOCKED` (proposed) |
| Phase 05 | Acceptance reference is absent, stale, or contradictory | Keep confirmation false; run only the missing Phase 05 acceptance evidence step | `PHASE05_ACCEPTANCE_UNRESOLVED` (proposed) |
| Collector | Policy/source mapping is missing, broad, or caller-controlled | Read nothing; return normalized unavailable/error | Existing source/policy error class |
| Source adapter | Fixed command is absent, denied, malformed, oversized, or timed out | Do not retry with alternate source, sudo, or broader command | Existing bounded source failure |
| Redaction | Canary or protected identifier survives | Discard all source-derived output and stop | `error/redaction_failure` |
| Operator reader | Source files, ownership, freshness, role, or mutation-denial reference fail | Materialize nothing or remove partial target atomically | `operator_reader_deployment` failed |
| Observer deployment | Account/key/policy/collector metadata differs from contract | Stop host-by-host deployment and revoke partial observer authority | `observer_deployment` failed |
| Projection | Entry is missing, stale, duplicate, ambiguous, disabled, or role-incompatible | Stop before SSH child creation | `unavailable/stale_projection` or integrity error |
| Readiness | Approval, revision, integrity outcome, or timestamp is incomplete | Write no manifest; request corrected owner package | `prerequisite_readiness` blocked |
| Positive validation | Required diagnostic is malformed, unsafe, or unexpectedly unavailable | Stop campaign; retain normalized failure only | `positive_validation` failed |
| Negative validation | Any shell, PTY, forwarding, command, source, sudo, or redirection succeeds | Revoke observer authority immediately; do not continue | Critical `negative_boundary_validation` failure |
| Audit/evidence | Pair is missing, mismatched, or contains prohibited data | Reject acceptance and stop retention | Audit/evidence scope failed |
| State comparison | Post-attestation is absent, contradictory, or changed | Do not claim acceptance; administrator investigates externally | `unchanged_state_comparison` failed |
| Rollback | Authority cannot be revoked independently or leaves a bypass | Keep Phase 06 failed and correct lifecycle design | `revocation_rollback` failed |
| Workflow | Required evidence gap remains or interpretation overclaims | Return blocked/failed; do not suppress the gap | `representative_workflow` incomplete |
| Acceptance | Owner outcome is not explicitly `accepted` | Keep Phase 07 implementation disabled | Phase 06 not accepted |

No failed live scope is automatically retried. Correcting an authorization, revision, projection, key, policy, credential, source, or implementation gate requires a fresh run ID and readiness package.

### VI. Security, Integrity, Idempotency, and Cleanup

- **Least privilege:** Project-reader, operator-reader, and host-observer authority remain separate and independently revocable. Host tools receive no `OS_*`; API tools receive no observer state.
- **No generic execution:** Public inputs never select commands, paths, units, services, destinations, users, keys, ports, sudo, timeouts, or output bounds.
- **Fixed transport:** Connector uses fixed argv, no shell, bounded stdin/stdout, one destination resolved from protected projection, and no fallback identity or address.
- **Host minimization:** Only fixed approved sources are read. Redaction and canary checks occur before transport and again at the runner boundary.
- **Protected inputs:** Credentials, keys, projections, policies, addresses, raw audits, source payloads, and comparator data remain outside Git and ordinary logs. Sensitive Ansible tasks use `no_log`.
- **Integrity:** All executables, policies, projections, keys, profiles, readiness files, and evidence records have exact path, owner, group, mode, regular-file, and non-symlink checks.
- **Idempotency:** Reapplying deployment with unchanged approved inputs reports no change. Readiness/evidence writers refuse destructive overwrite. Host diagnostics perform bounded reads only.
- **Atomicity:** Profile, policy, projection, readiness, and evidence writes use restrictive temporary state and atomic replacement where replacement is contractually permitted. Partial authority is removed on deployment failure.
- **Cleanup:** Delete transient operator-reader source and readiness manifest after the campaign. Diagnostics create no remote temporary files. Timeouts terminate local child process groups.
- **Emergency stop:** Unexpected mutation, disclosure, shell/forwarding/sudo success, destination bypass, or state difference immediately revokes affected authority and invalidates the run.
- **No acceptance by documentation:** Checkboxes and contract status change only after owner-accepted outcomes exist.

### VII. Validation Strategy

Validation is cumulative and must prove implementation readiness before protected live inputs are used.

#### Static and syntax validation

```bash
rtk "$PYTHON_BIN" -m py_compile <changed-python-files>
rtk "$PYTHON_BIN" -m black --check <changed-python-files>
rtk bash -n <changed-shell-tests>
rtk ansible-playbook --syntax-check -i ansible/ai_ops_assistant/inventories/local/local.yml <changed-playbook>
rtk git diff HEAD --check
```

`PYTHON_BIN` is `<user defined Python Venv>` unless the owner changes the approved environment.

#### Targeted tests

- Phase 05 producer/recorder integration proves the prerequisite invariant.
- Collector tests prove all three live adapter paths using fixed injected readers without host contact.
- Connector/runner tests prove seven-tool registration, authority isolation, fixed argv, timeout, result schema, redaction, and audit behavior.
- Operator-reader tests prove exact source/target metadata, no fallback, source cleanup, and independent revocation.
- Observer tests prove account/key/forced-command/policy materialization and all negative-control definitions.
- Readiness tests prove exact 11/6/8 schema, freshness, duplicate rejection, normalized output, and no protected disclosure.
- Evidence tests prove exact scope outcome closure and final acceptance derivation.

Use focused repository commands confirmed in each chunk. Before live execution, run the full existing Phase 06 Python discovery, tool-runner discovery, Phase 06 shell/static harnesses, JSON/YAML parsing, and Ansible syntax checks.

#### Live validation

Live commands require the accepted readiness package and exact inventory limits. Capture mode-`0600` temporary logs and report only Ansible recaps or normalized outcomes. Never show protected values. Each scope validates its precondition and refuses to run out of order.

#### Final review

Review:

```bash
rtk git status --short
rtk git diff --stat HEAD
rtk git diff HEAD --check
rtk git diff HEAD -- docs/ai-ops-revised ansible/ai_ops_assistant
```

Confirm no protected/generated file is tracked, no placeholder unavailable path remains for an accepted capability, and no Phase 07 implementation exists before Phase 06 acceptance.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. It is a finite eight-chunk campaign. Do not insert additional planning-only or stub-only chunks. A chunk may stop on a concrete safety blocker, but successful completion must remove its named blocker.

#### Chunk 0: Baseline and Integration Confirmation

- **Goal:** Freeze the implementation baseline, map each missing capability to an exact file/test, validate the Phase 05 evidence location, and produce one owner-input checklist for the entire campaign.
- **Files to read:** current Git diff; Phase 05/06 plans and contracts; collector, connector, registry, operator-reader role, observer role, readiness/evidence playbooks, and focused tests.
- **Commands:** targeted `rtk git status`, `rtk git diff`, `rtk grep`, `rtk find`, and bounded reads; no protected values or live commands.
- **Evidence to confirm:** exact source adapter mechanism; target-host utilities; Phase 05 outcome reference; exact inventory groups; required playbooks/tests; complete 11/6/8 owner package fields; rollback owners.
- **Stop condition:** one bounded blocker matrix exists and every implementation blocker is assigned to Chunks 1-5. Continue directly to Chunk 1 when no owner decision is missing; do not create another design artifact.

#### Chunk 1: Phase 05 and Readiness-Sequencing Prerequisite Closure

- **Goal:** Remove the contradictory Phase 05 state and the circular readiness-before-deployment gate.
- **Files to change:** Phase 06 validation producer and focused tests; readiness requirement/operations contract; readiness validator/materializer/gate and focused tests only where required for the two-stage sequence.
- **Symbols to add/change:** owner-provided Phase 05 acceptance outcome/reference; conditional `phase05_acceptance_pending`; campaign authorization result; post-deployment runtime-readiness result; closed assertions for both gates.
- **Implementation shape:** no hard-coded acceptance. The campaign gate permits only deployment after source-side prerequisites pass. The existing `ready` manifest remains fail-closed and is materialized only after all 8 deployed-state checks pass.
- **Validation:** focused producer/recorder and readiness tests, Python compilation/formatting, Ansible syntax, YAML parsing, and diff check.
- **Stop condition:** no result can contain both confirmed Phase 05 acceptance and a pending Phase 05 gate, and no deployed-target integrity check is required before its authorized deployment scope.

#### Chunk 2: Executable Fixed Live Source Adapters

- **Goal:** Replace the collector's unconditional `authorization_pending` path with executable policy-gated metadata, Neutron, and Nova adapters.
- **Files to change:** `host_observer_collector.py`, its focused tests, and the protected-policy schema/template only if required by the confirmed seam.
- **Symbols to add/change:** fixed source adapter(s), policy loader, timeout/bounded reader, and `run()` dispatch into existing `collect_*_slice` functions.
- **Implementation shape:** fixed argv/no shell; source definitions come only from validated protected policy; no generic reader and no sudo fallback. Tests inject source output and never read developer-host logs.
- **Validation:** Python compilation/formatting, complete collector tests, malformed/timeout/truncation/redaction/role/source regressions, and forbidden-operation scan.
- **Stop condition:** all three approved tools can produce schema-valid results through `run()` in tests; no supported source remains a placeholder stub.

#### Chunk 3: Operator-Reader Deployment and Lifecycle

- **Goal:** Replace intentional operator-reader deployment failure with guarded materialization, validation, cleanup, and independent revocation.
- **Files to change:** operator identity role defaults/tasks, `playbook_deploy_operator_identity_profile.yml`, and focused tests as one cohesive deployment slice.
- **Symbols to add/change:** exact owner/revision/freshness gates; copy/verify/remove-source tasks; rotation/revocation and mutation-denial outcome handling.
- **Implementation shape:** default disabled; enabled only with exact approval and protected source. No credential content in output. Reapply is idempotent.
- **Validation:** YAML parsing, focused static tests, Ansible syntax/check mode using non-secret fixtures, and diff/security review.
- **Stop condition:** an authorized operator-reader profile can be materialized and independently removed without fallback or intentional fail task.

#### Chunk 4: Observer Provisioning and Protected Policy Integration

- **Goal:** Complete host-observer account, key restriction, forced collector, policy, inventory projection, disablement, and removal.
- **Files to change:** observer role defaults/tasks, host-observer deployment/validation playbook(s), and focused tests.
- **Symbols to add/change:** account/group tasks; authorized-key forced-command entry; exact `/32` restriction; policy materialization; host-by-host lifecycle; metadata assertions.
- **Implementation shape:** default disabled and one approved host at a time. No sudo. Use owner-supplied protected key/projection/policy inputs under `no_log`.
- **Validation:** Ansible syntax/check mode with safe fixtures, static policy tests, negative configuration assertions, idempotence check, and complete diff/security review.
- **Stop condition:** the role can deploy and remove the exact observer authority; it no longer stops after validation/collector copy.

#### Chunk 5: Seven-Tool Acceptance and Evidence Orchestration

- **Goal:** Make the validation/evidence path cover all seven tools and every acceptance outcome without contradictions.
- **Files to change:** restricted-diagnostics validation producer, evidence recorder, host-observer validation playbook, and their focused integration tests.
- **Symbols to add/change:** seven-tool result closure; 18 negative outcomes; audit-pair outcomes; pre/post attestation; rollback; representative workflow; final acceptance derivation.
- **Implementation shape:** normalized outcomes only. Scope order is enforced; no raw source/audit/comparator content is retained. Existing project-reader/Neutron-only assumptions are removed.
- **Validation:** focused producer/recorder/observer tests, JSON/YAML and Ansible syntax checks, closed-schema tests, and evidence disclosure scan.
- **Stop condition:** one normalized result can objectively derive accepted/blocked/failed for every Phase 06 criterion.

#### Chunk 6: Authorization, Deployment, and Runtime Readiness Campaign

- **Goal:** Consume the complete owner package, pass campaign authorization, deploy both authorities, and then pass runtime readiness.
- **Files to change:** no repository files unless an authorized execution exposes a reproducible implementation defect; owner extra-vars remain untracked and protected.
- **Symbols to add/change:** none expected.
- **Implementation shape:** validate the complete package without printing values; run the campaign gate; deploy `assistant02`, then approved observer hosts one at a time; verify idempotence/metadata; evaluate all 8 target integrity checks; materialize and validate the runtime readiness manifest once.
- **Validation:** normalized campaign/runtime gate outcomes, bounded Ansible recaps, deployed integrity outcomes, and owner-confirmed scope records.
- **Stop condition:** prerequisite, operator-reader deployment, observer deployment, and runtime readiness pass for one current run; otherwise invalidate the run and report the exact normalized blocker.

#### Chunk 7: Live Acceptance, Rollback, and Phase Transition

- **Goal:** Execute remaining live scopes, obtain owner acceptance, reconcile plans/contracts, and open Phase 07.
- **Files to change:** Phase 05/06 plan status, relevant operations-contract status, and runbook only after accepted evidence exists; no protected evidence enters Git.
- **Symbols to add/change:** evidence-backed checklist/status text and explicit Phase 07 entry reference.
- **Implementation shape:** one host/source contact; positive diagnostics; all 18 negative controls; evidence/audit; unchanged-state; revocation/rollback; restored authority if approved; representative workflow; owner decision.
- **Validation:** normalized scope outcomes, final evidence schema validation, all regression suites, complete Git diff/security review, and confirmation that transient inputs were deleted.
- **Stop condition:** Phase 06 is explicitly `accepted` and Phase 07 entry criteria are satisfied, or one precise failed scope is recorded. No additional readiness-only chunk follows.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, pre-edit-discipline, safe-python-edit, post-edit-discipline, and rtk-command-prefix if available.

Task:
Complete Phase 06 and close its Phase 05 prerequisite using docs/ai-ops-revised/implementation-plan/ads/06-02-phase06-completion-and-phase05-prerequisite-closure-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files. Produce the exact blocker-to-file matrix and the single complete owner-input checklist. Do not inspect protected values or perform live operations. Stop only for a concrete unresolved owner decision; do not create another planning document.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Execute the next numbered chunk only.
Do not continue to another chunk in the same implementation session.
The chunk must remove its named blocker and may not finish by adding another intentional unavailable stub. Run targeted validation, review staged and unstaged diffs, and write a compact handoff naming the next chunk.
```

For Chunks 6-7:

```text
Use the chunked-implementation skill and the accepted owner authorization package.
Execute only the ordered scopes assigned to the current chunk. Report normalized outcomes only. Stop immediately on a failed safety gate, invalidate changed/stale runs, and never broaden authority or expose protected values.
```

### X. Conclusion and Next Steps

This ADS defines a finite route from the current static/synthetic Phase 06 boundary to accepted deployed capability. It closes the Phase 05 contradiction and circular readiness sequencing first, then removes the three implementation blockers—live collector execution, operator-reader lifecycle, and observer provisioning—before the live campaign. It consolidates owner decisions into one package while retaining separately named scope approvals and fail-closed ordering.

The next action is Chunk 0, followed directly by implementation Chunks 1-5. The readiness materializer is not the next engineering task; it is used only after implementation readiness is proven. Chunks 6-7 then perform one bounded acceptance campaign and either produce the explicit Phase 06 acceptance needed for Phase 07 or identify one concrete failed scope without returning to indefinite readiness work.
