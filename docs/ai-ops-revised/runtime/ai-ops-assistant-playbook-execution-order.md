# AI-OPS Assistant Ansible Playbook Execution Order

## Status and authority

This is an operator-facing runtime procedure for the playbooks under:

```text
ansible/ai_ops_assistant/
```

It explains dependency order, purpose, prerequisites, expected evidence, and stop conditions. It does **not** grant authorization for deployment, credential use, SSH, host contact, OpenStack API calls, source reads, audit inspection, negative testing, rollback, or Phase 07/MCP exposure.

The authoritative safety boundaries remain:

- `docs/ai-ops-revised/runtime/foundation-operations-contract.md`
- `docs/ai-ops-revised/runtime/identity-policy-operations-contract.md`
- `docs/ai-ops-revised/runtime/mvp-live-validation-and-rollback-operations-contract.md`
- `docs/ai-ops-revised/runtime/phase06-live-acceptance-readiness-requirement.md`
- `docs/ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-steps-05-to-07-operations-contract.md`
- `docs/ai-ops-revised/implementation-plan/ads/06-02-phase06-completion-and-phase05-prerequisite-closure-ads.md`

A playbook completing successfully is not the same as owner acceptance. Every gate must consume current, outcome-only evidence for the same run and revisions.

## Operating rules

1. Execute one playbook at a time and stop when its gate fails.
2. Use the maintained inventory and its externally generated `nodes.yml`; do not replace it with literal addresses, DNS fallbacks, or caller overrides.
3. Use the exact Ansible limit required by each playbook. Most assistant-side playbooks require `assistant02`; host-observer deployment requires `ai_ops_host_observers` and `serial: 1`.
4. Supply protected variables through the approved external procedure. Do not put credentials, private keys, destination projections, raw audits, source payloads, or comparator data in Git, chat, shell history, or ordinary logs.
5. Keep generated runtime variables disabled until their corresponding authorization and outcome evidence exist. Never enable every gate at once.
6. Capture only normalized status, revision, evidence-reference, limitation, and Ansible recap information.
7. Any unexpected mutation, disclosure, shell/forwarding success, unsafe path, stale revision, changed state, or missing evidence stops the run and invalidates the current run ID.

## Common invocation shape

Commands below are templates, not permission to execute live operations. Before an authorized run, establish the approved environment and non-secret repository variables:

```bash
export ROOT_DIR="$PWD"
export TARGET_ENV=local
```

Use the repository inventory and exact limit required by the playbook:

```bash
rtk ansible-playbook \
  -i ansible/ai_ops_assistant/inventories/local/local.yml \
  ansible/ai_ops_assistant/<playbook>.yml \
  --limit <required-limit> \
  -e root_dir="$ROOT_DIR" \
  -e target_env="$TARGET_ENV"
```

Protected extra-vars must be supplied through the approved secret/operator mechanism. Do not show them in command output.

## High-level sequence

The complete route has three sections. Section A establishes the revised assistant runtime and Phase 05 evidence. Section B is the conditional Phase 06 campaign. Section C is rollback/recovery and is not a normal forward step.

```text
A1  pre_setup / deploy wrapper
A2  validate_foundation
A3  deploy_identity_profile
A4  validate_project_reader
A5  deploy_tool_runner
A6  deploy_diagnostic_toolbox
A7  validate_diagnostic_toolbox
A8  validate_mvp_runner                    [authorized MVP validation]
A9  record_mvp_acceptance_evidence         [after A8 result]
A10 accept_diagnostic_toolbox              [after secure acceptance record]
A11 validate_mutation_denial               [separately authorized safety probe]

B1  validate_host_observer_scope            [fixture-only, no host contact]
B2  materialize readiness in campaign mode  [11 approvals + revisions]
B3  deploy_operator_identity_profile       [assistant02, first authority]
B4  deploy_host_observer                    [one approved host at a time]
B5  external metadata/integrity inspection  [8 deployed-state checks]
B6  materialize readiness in runtime mode  [writes ready manifest once]
B7  validate_live_acceptance_readiness      [ready gate]
B8  ordered live campaign                  [host/source, positive, negative]
B9  produce_restricted_diagnostics_validation
B10 record_restricted_diagnostics_evidence
B11 owner acceptance and transient-input cleanup

C1  rehearse_mvp_rollback                   [only for an authorized rollback]
C2  recover_mvp_rollback                    [only after successful rollback]
```

The current Phase 06 implementation does not provide a generic live-execution playbook for host contact. The `validate_host_observer_scope` playbook is fixture-only; live host/source operations remain an externally authorized campaign procedure bounded by the contracts.

# Section A — Foundation and Phase 05 sequence

## A1. `playbook_pre_setup.yml`

**Purpose:** Deploy the AI-OPS foundation roles (`common` and `ai_ops_assistant_foundation`) to the assistant target.

**Scope:** `ai_ops_assistant` inventory group. The playbook loads the maintained `nodes.yml`.

**Run first:** This is the foundation entrypoint. `playbook_deploy.yml` imports only this playbook; it is not a complete deployment.

**Expected result:** Foundation directories, base ownership/modes, and approved base dependencies are materialized.

**Stop if:** The maintained inventory is unavailable, the target scope is ambiguous, the role reports an unexpected mutation, or the foundation deployment proposes unrelated service changes.

## A1 wrapper: `playbook_deploy.yml`

**Purpose:** Convenience wrapper that imports `playbook_pre_setup.yml`.

**Important:** Do not describe it as “deploy everything.” It does not deploy the identity profile, tool runner, diagnostic toolbox, operator-reader, or host observer.

## A2. `playbook_validate_foundation.yml`

**Purpose:** Verify the foundation without exposing protected content.

It checks:

- exact assistant target scope;
- foundation workspace metadata;
- approved package presence and redacted versions;
- absence of excluded AI-OPS services and processes;
- absence of excluded listeners; and
- bounded Keystone reachability without authentication.

**Prerequisite:** A successful A1 deployment.

**Expected result:** A normalized foundation validation state with no excluded runtime or listener present.

**Stop if:** Workspace metadata, package facts, excluded-service checks, listener checks, or endpoint reachability fail. Do not continue to identity or runner deployment until corrected.

## A3. `playbook_deploy_identity_profile.yml`

**Purpose:** Deploy the separate protected project-reader profile to `assistant02`.

The playbook asserts:

- exactly `assistant02` is targeted;
- the `ai_ops_assistant` group is present;
- `--limit assistant02` is used; and
- the controller has no ambient `OS_*` credentials.

The role materializes the project-reader profile with its protected ownership and mode contract.

**Prerequisite:** A2 passes and the external protected profile source is authorized and available.

**Expected result:** A separate project-reader profile exists at its fixed protected location. Contents must never be printed.

**Stop if:** Scope, ambient-credential, ownership, mode, regular-file, non-symlink, freshness, or source cleanup checks fail.

## A4. `playbook_validate_project_reader.yml`

**Purpose:** Validate the protected project-reader profile and execute the fixed read-only project operations.

It checks profile metadata, then invokes only the declared operations for token issuance and project-scoped resource reads. It normalizes empty/denied/unavailable outcomes rather than broadening access.

**Prerequisite:** A3 passes and the project-reader authorization is current.

**Expected result:** Required project-reader operations pass or return an approved empty result, with no mutation path.

**Stop if:** Profile metadata is unsafe, authentication unexpectedly succeeds outside the declared profile, an operation mutates state, or a required read fails without an accepted limitation.

## A5. `playbook_deploy_tool_runner.yml`

**Purpose:** Deploy the revised tool runner, registry, audit inspector, readiness validator, and fixed runner support files to `assistant02`.

**Prerequisite:** A2 passes. The project-reader profile should be deployed before runner validation because later validations inspect profile isolation.

**Expected result:** Fixed runner artifacts exist under the revised runner root with expected ownership, modes, paths, and no prior-runtime fallback.

**Stop if:** Check mode proposes unrelated changes, a path is symlinked or misowned, an unexpected service is enabled, or a second identical run is not idempotent.

## A6. `playbook_deploy_diagnostic_toolbox.yml`

**Purpose:** Deploy the revised diagnostic toolbox scripts and secure acceptance consumer to `assistant02`.

**Prerequisite:** A5 passes.

**Expected result:** The approved diagnostic scripts are present with fixed permissions and isolated from protected profile contents.

**Stop if:** Any script, profile, or destination metadata is unsafe or the proposed change reaches outside the revised toolbox path.

## A7. `playbook_validate_diagnostic_toolbox.yml`

**Purpose:** Validate deployed toolbox files without cloud reads.

It checks file metadata, project-reader profile metadata, shell syntax, secure consumer Python syntax, and the repository static safety contract.

**Prerequisite:** A6 passes.

**Expected result:** Toolbox artifacts are regular, non-symlinked, correctly owned/moded, syntactically valid, and statically safe.

**Stop if:** Any static safety, syntax, profile metadata, or ownership check fails.

## A8. `playbook_validate_mvp_runner.yml`

**Purpose:** Execute the separately authorized Phase 05 three-tool MVP validation through the revised runner and produce a normalized producer result.

The fixed sequence is:

1. validate exact `assistant02` scope and concrete activation gates;
2. verify protected output and runner/audit/profile metadata;
3. run `project_resource_summary`;
4. select one representative server identifier in protected task state;
5. run `server_basic_info` and `server_network_info` for that same identifier;
6. inspect only the bounded matching audit events;
7. obtain the external post-state attestation; and
8. write the normalized Phase 05 result.

**Prerequisites:** A7 passes, explicit MVP authorization exists, pre-attestation is valid, prior-runtime isolation is confirmed, protected evidence handling is approved, and a concrete post-attestation procedure exists.

**Expected result:** Outcome-only Phase 05 producer JSON with tool, audit, attestation, limitation, and rollback fields.

**Stop if:** Any runner, audit, redaction, path-isolation, identifier, or attestation gate fails. Do not retry with a broader profile or alternate path.

## A9. `playbook_record_mvp_acceptance_evidence.yml`

**Purpose:** Read the normalized Phase 05 producer result and write a protected outcome-only evidence record.

It validates producer provenance/schema, tool outcomes, evidence ownership/location, record modes, and prohibited manual fields before writing the record.

**Prerequisite:** A8 has produced a valid normalized result and the evidence owner has separately authorized recording.

**Expected result:** One protected Phase 05 evidence record containing normalized outcomes only.

**Stop if:** The producer result is missing, stale, malformed, contradictory, contains prohibited content, or the destination already exists unexpectedly.

## A10. `playbook_accept_diagnostic_toolbox.yml`

**Purpose:** Validate the secure acceptance record for the revised diagnostic toolbox. It does not execute the diagnostics itself.

It checks the fixed protected record directory and record metadata, decodes the outcome-only record in protected task state, validates the closed schema and two tool records, and confirms comparator interfaces remain boolean-only.

**Prerequisite:** The separately authorized secure acceptance consumer/process has produced the record expected by this playbook.

**Expected result:** A normalized local validation state for the secure acceptance record.

**Stop if:** The record is missing, too large, misowned, symlinked, malformed, contains unexpected fields, or lacks the required administrator post-state gate.

## A11. `playbook_validate_mutation_denial.yml`

**Purpose:** Run the fixed project-reader create/update/delete denial probes using disposable target names and normalize the results.

**Authorization:** This is a separate safety scope. It is not automatically authorized by read-only validation or deployment approval.

**Expected result:** All three mutation attempts are denied. A successful mutation is an emergency stop requiring external administrator revocation and cleanup.

**Stop if:** Any create, update, or delete operation is allowed, the target identity is not disposable, or the protected profile metadata is unsafe.

# Section B — Phase 06 authority and readiness sequence

## B1. `playbook_validate_host_observer_scope.yml`

**Purpose:** Validate the host-observer boundary using local fixture data without contacting any host.

It verifies:

- exact `ai_ops_host_observers` group and limit contract;
- the fixed synthetic collector fixture;
- exactly 18 negative-control definitions, all expected to be denied;
- normalized audit-pair and pre/post attestation shapes; and
- pending rollback fields.

**Prerequisite:** Static implementation and test validation have passed.

**Important:** This playbook is not live host validation. It must not be described as proof that SSH, forwarding, sudo, source reads, or remote collector execution work or fail.

## B2. `playbook_materialize_live_acceptance_readiness_manifest.yml` in `campaign` mode

**Purpose:** Validate the owner package before authority deployment without writing the runtime-ready manifest.

It checks:

- the fixed run/reference/class;
- all 11 separately named scope approvals;
- six protected-input revision references;
- owner labels and evidence-reference formats; and
- campaign-mode scope completeness.

**Prerequisite:** The complete owner package is current, all revisions belong to the same run, and the Phase 05 prerequisite is represented by an owner-issued evidence reference.

**Expected result:** A normalized campaign authorization result such as `authorized`, with no runtime-ready manifest and no host-contact authorization.

**Stop if:** Any approval is missing, stale, denied, revoked, duplicated, mismatched, or malformed. A campaign authorization result does not claim runtime readiness.

## B3. `playbook_deploy_operator_identity_profile.yml`

**Purpose:** Materialize and validate the separate operator-reader authority on `assistant02`.

It enforces:

- exact `assistant02` scope;
- no ambient `OS_*` credentials;
- separation from the project-reader profile;
- the fixed `neutron_agent_health` selection;
- owner-provided transient source metadata;
- Phase 05 acceptance;
- project-reader need proof; and
- independent mutation-denial outcomes.

The role validates source files, copies only the approved profile, verifies target metadata, removes transient source material after successful verification, and supports guarded rotation/revocation.

**Prerequisite:** B2 campaign authorization passes and protected operator-reader source metadata is available.

**Expected result:** Operator-reader authority is materialized, verified, and independently lifecycle-managed.

**Stop if:** Any source, ownership, freshness, role, mutation-denial, rotation, or revocation gate fails. Do not fall back to project-reader credentials.

## B4. `playbook_deploy_host_observer.yml`

**Purpose:** Deploy, disable, or remove the restricted host-observer authority.

It targets `ai_ops_host_observers`, uses `serial: 1`, and requires the exact host-observer limit. The role creates/removes only the approved observer account/group, forced authorized-key entry, collector, policy, and inventory projection.

**Prerequisite:** B2 passes, B3 completes, the maintained inventory projection is current, and protected key/policy/collector inputs are available. Deploy approved hosts one at a time.

**Expected result:** The selected host has the exact non-interactive observer authority, forced collector, disabled forwarding/PTY, source restriction, and protected policy metadata.

**Stop if:** An account, key, policy, collector, source restriction, destination, ownership, mode, or host enablement differs from the owner package. Do not use a destination override or sudo fallback.

For disablement/removal, use only the separately authorized lifecycle action. Removal must not affect project-reader or operator-reader authority.

## B5. External deployed-state integrity inspection

There is no repository playbook that can safely infer all eight deployed-state outcomes. The owner/operator procedure must inspect and return normalized outcomes for:

1. destination projection directory;
2. destination projection file;
3. destination projection freshness;
4. operator-reader source;
5. operator-reader target;
6. observer private key;
7. host collector; and
8. host policy.

Return only `status` and opaque evidence reference for each. Do not copy protected contents into Ansible variables or the runtime document.

**Stop if:** Any check is `blocked`, `failed`, `unavailable`, stale, mismatched, symlinked, or owned/moded incorrectly.

## B6. `playbook_materialize_live_acceptance_readiness_manifest.yml` in `runtime` mode

**Purpose:** Materialize the closed `status: ready` manifest after deployment and all eight integrity checks pass.

It validates all 11 approvals, six revisions, eight integrity outcomes, timestamps, fixed path/owner/mode, non-symlink status, and serialized size. It refuses to overwrite an existing manifest and writes only through the fixed protected path.

**Prerequisite:** B3, B4, and B5 pass for the same run and revisions.

**Expected result:** One protected runtime readiness manifest with `status: ready`.

**Stop if:** Any approval or integrity check is not `approved`/`passed`, timestamps are invalid/expired, revisions do not match, the destination already exists unexpectedly, or file metadata is unsafe.

## B7. `playbook_validate_live_acceptance_readiness.yml`

**Purpose:** Run the fixed readiness-manifest validator and accept only the normalized `ready` result.

It targets only `assistant02`, invokes the fixed installed validator, bounds its exit code/stdout, parses only the closed normalized result, and publishes the result in protected task state.

**Prerequisite:** B6 has materialized the manifest and the current run/revisions remain unchanged.

**Expected result:** `status: ready`, `limitation_class: none`, and `ready: true`.

**Stop if:** The validator returns blocked/unavailable, the manifest is malformed or expired, or any revision/approval/integrity mismatch appears. Do not enable host contact after a non-ready result.

## B8. Ordered live campaign

The repository currently provides the gates and evidence orchestrator, but not a generic host-contact executor. Once B7 passes and the separately named live scopes are approved, the owner procedure may execute in this order:

1. one approved host/source contact;
2. positive validation for the approved tool/host/source mappings;
3. all 18 negative observer controls;
4. outcome-only evidence preparation;
5. protected audit inspection under its separate authorization;
6. unchanged-state comparison;
7. revocation/rollback rehearsal; and
8. representative seven-tool workflow.

Stop immediately on any unexpected success, disclosure, mutation, state change, stale evidence, or source-policy deviation.

## B9. `playbook_produce_restricted_diagnostics_validation.yml`

**Purpose:** Consume normalized outcomes from the complete Phase 06 campaign and derive one closed acceptance result.

It validates:

- seven tool outcomes;
- all 18 negative-control outcomes;
- ordered 11-scope outcomes;
- seven audit/result pairs;
- pre/post attestations;
- unchanged-state comparison;
- rollback/revocation state; and
- representative workflow evidence gaps and advisory-only status.

It derives `accepted`, `blocked`, or `failed` without accepting a contradictory Phase 05 state. It writes a normalized producer result under the protected Phase 06 validation location.

**Prerequisite:** B8 has produced current outcome-only inputs for the same run and source revisions.

**Stop if:** Any collection is incomplete, out of order, contradictory, failed, or contains a non-opaque field.

## B10. `playbook_record_restricted_diagnostics_evidence.yml`

**Purpose:** Read the Phase 06 producer result, revalidate its closed schema/provenance, and write the protected outcome-only evidence record.

It refuses manual producer-derived fields, validates tool/negative/scope/audit records, enforces protected directory/record metadata, and writes only normalized evidence.

**Prerequisite:** B9 produced a valid result and the evidence-recording scope is separately authorized.

**Expected result:** One protected Phase 06 record for the exact run and source revisions.

**Stop if:** The producer result is missing, stale, malformed, contradictory, contains raw/protected data, or the destination path is unsafe or unexpectedly occupied.

## B11. Owner acceptance and transition

The named evidence owner reviews the normalized record and records `accepted`, `blocked`, or `failed` outside the code agent’s authority.

Only `accepted` may satisfy the Phase 06 completion invariant. Acceptance requires all seven tools, all 11 scopes, all 18 denied controls, audit/redaction, unchanged state, rollback, representative workflow, and exact revision references.

After acceptance only, reconcile the Phase 05/Phase 06 plans and operations-contract status, delete transient readiness/profile inputs according to policy, and allow Phase 07 planning/implementation. Phase 07/MCP exposure is prohibited before this record exists.

# Section C — Conditional rollback and recovery

## C1. `playbook_rehearse_mvp_rollback.yml`

**Purpose:** Rehearse removal of the revised MVP runner/profile authority under a separately authorized rollback scope.

It requires recovery readiness, a valid pre-attestation, fixed revised paths, and external confirmation of credential revocation. It removes only the revised runner files/profile and then requires protected fail-closed and baseline verification.

**Use:** Only after an authorized rollback decision or a failure requiring rollback. It is not a normal post-validation step and must not be run automatically.

## C2. `playbook_recover_mvp_rollback.yml`

**Purpose:** Restore the revised MVP authority after rollback, only when recovery gates and unchanged post-attestation pass.

It requires external credential restoration and protected artifact verification before restoring the identity profile and tool runner.

**Use:** Only after C1 completes and the administrator explicitly authorizes recovery. Do not use it to bypass a failed Phase 06 readiness or acceptance gate.

# Playbook-to-purpose index

| Playbook | Primary purpose | Normal position |
| --- | --- | --- |
| `playbook_deploy.yml` | Wrapper importing foundation pre-setup only | A1 wrapper |
| `playbook_pre_setup.yml` | Deploy foundation roles | A1 |
| `playbook_validate_foundation.yml` | Validate foundation/package/process/listener state | A2 |
| `playbook_deploy_identity_profile.yml` | Deploy project-reader profile | A3 |
| `playbook_validate_project_reader.yml` | Validate project-reader metadata and fixed reads | A4 |
| `playbook_deploy_tool_runner.yml` | Deploy revised runner/registry/audit/readiness files | A5 |
| `playbook_deploy_diagnostic_toolbox.yml` | Deploy diagnostic scripts and secure consumer | A6 |
| `playbook_validate_diagnostic_toolbox.yml` | Validate toolbox metadata, syntax, and static safety | A7 |
| `playbook_validate_mvp_runner.yml` | Execute authorized Phase 05 three-tool validation | A8 |
| `playbook_record_mvp_acceptance_evidence.yml` | Record Phase 05 normalized evidence | A9 |
| `playbook_accept_diagnostic_toolbox.yml` | Validate secure acceptance record | A10 |
| `playbook_validate_mutation_denial.yml` | Run authorized project-reader mutation-denial probes | A11 / conditional |
| `playbook_validate_host_observer_scope.yml` | Validate fixture-only observer boundary | B1 |
| `playbook_materialize_live_acceptance_readiness_manifest.yml` | Campaign authorization or runtime manifest materialization | B2 and B6 |
| `playbook_deploy_operator_identity_profile.yml` | Deploy/revoke operator-reader authority | B3 |
| `playbook_deploy_host_observer.yml` | Deploy/disable/remove observer authority | B4 |
| `playbook_validate_live_acceptance_readiness.yml` | Validate the fixed ready manifest | B7 |
| `playbook_produce_restricted_diagnostics_validation.yml` | Derive closed Phase 06 acceptance result | B9 |
| `playbook_record_restricted_diagnostics_evidence.yml` | Record Phase 06 outcome-only evidence | B10 |
| `playbook_rehearse_mvp_rollback.yml` | Authorized revised MVP rollback rehearsal | C1 / conditional |
| `playbook_recover_mvp_rollback.yml` | Authorized revised MVP recovery | C2 / conditional |

## Final operator checklist

Before each transition, confirm:

- current run ID and source revisions match;
- the required scope authorization exists separately;
- the exact inventory limit is used;
- generated/protected variables are external and non-disclosing;
- the previous playbook returned a normalized pass/accepted outcome;
- no unexpected file, account, service, resource, or state mutation occurred; and
- the next playbook is actually authorized by the contract.

If any answer is no, stop and report the normalized blocker. Do not broaden permissions, choose an alternate path, retry automatically, or mark a checklist item complete from playbook presence alone.

## References

- `ansible/ai_ops_assistant/`
- `docs/ai-ops-revised/runtime/phase06-live-acceptance-readiness-requirement.md`
- `docs/ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-steps-05-to-07-operations-contract.md`
- `docs/ai-ops-revised/runtime/mvp-live-validation-runbook.md`
- `docs/ai-ops-revised/implementation-plan/ads/06-02-phase06-completion-and-phase05-prerequisite-closure-ads.md`
