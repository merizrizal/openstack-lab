# 07. Acceptance and Rollout

## 07.1 Goal

Release only the validated capability matrix, with separately authorized deployed evidence, compatibility protection and rehearsed shutdown/revocation/rollback.

```text
passing offline gates -> explicit live approval -> isolated read-only acceptance -> incremental enablement -> monitor or safely rollback
```

## 07.2 Estimate

Total: **3-5 engineer-days / 18-30 focused hours**.

## 07.3 Scope

Included: requirement evidence audit, existing workflow regressions, reproducible observer installation, reader-policy and isolation checks, conditional host/MCP/model acceptance, operational rehearsal and release record. Primary requirements: FR-021–FR-022, FR-041–FR-042; NFR-002, NFR-010–NFR-012, NFR-014–NFR-015. Evidence: AC-011, AC-023–AC-025 and deployed portions of AC-013/AC-017; release review covers all AC-001–AC-025.

Excluded: automatic deployment during coding/planning, live probes without authorization, production fault injection, workload mutation/remediation, unapproved inference and rollback to weaker credentials or policy.

## 07.4 Assumptions

- [ ] Phases 01-04 and 06 pass applicable gates. Phase 05 is accepted for each enabled integration; disabled capabilities remain visible limitations.
- [ ] Before execution, identify the approved revision of the [canonical PRD](../prd.md), accepted prerequisite phase revisions, applicable amendments and current owner-approved verification for the exact environment and scope. A committed draft, prior review or historical accepted run is not current approval or deployed readiness.
- [ ] Reconfirm the approved environment, cloud/project, observer placement, credentials, endpoint/egress controls, live procedures and cleanup owner with the relevant authorities. Reconfirmation does not authorize changing settled values: inherit [Phase 01 reconciliation](01-safety-boundary-and-manual-slice.md#constraint-reconciliation-and-authority), [Phase 05 retained contracts](05-gated-host-and-mcp-integrations.md#retained-contracts-readiness-and-amendment-gates) when applicable, and the [live-validation and rollback contract](../../ai-ops-revised/runtime/mvp-live-validation-and-rollback-operations-contract.md). Changes require applicable Level 2 decisions and approved amendments before affected enablement; obtain separate authorization for each live scope.
- [ ] Mutation-denial probes use approved disposable fixtures and human-controlled provisioning, never diagnostic agent tools.
- [ ] Release corpus/rubric, capability matrix and quality/latency/cost thresholds are frozen before candidate measurement; no safety failure is waivable by model confidence.

Dependency: all enabled delivery phases. Consume their complete applicable prerequisite evidence, including Phase 03's cumulative-budget, concurrent start/resume, identity/collision, migration-preservation and cross-sink recovery regressions; a smaller smoke suite is not a substitute. These procedures may be reused for a separately authorized early manual/single-server pilot, but such a pilot is not complete product acceptance.

### Evidence and unchanged-state boundaries

- Distinguish synthetic/offline artifacts, protected application investigation records and operational acceptance evidence. Each follows its applicable approved data, scope and retention policy; redaction alone does not authorize retaining operational acceptance material.
- For live acceptance, apply the applicable [identity evidence contract](../../ai-ops-revised/runtime/identity-policy-operations-contract.md#evidence-and-retention), [live-validation evidence contract](../../ai-ops-revised/runtime/mvp-live-validation-and-rollback-operations-contract.md#step-6-evidence-contract) and, when host diagnostics are enabled, [host readiness evidence contract](../../ai-ops-revised/runtime/phase06-live-acceptance-readiness-requirement.md#evidence-and-unchanged-state-requirements), including their distinct outcome-only field allowlists, owners, approved locations, modes, access and retention. Confirm any conceptual location and applicable policy with its owner before use. Keep permitted raw review material transient and discard it after approved review; never retain raw envelopes, identifiers, addresses, topology, audit lines or comparator data as operational acceptance evidence. Publish only approved non-sensitive outcomes or references. General retention/export exercises do not override the retained audit contract.
- For each applicable live diagnostic or rehearsal, obtain fresh, run-bound administrator-owned independent pre/post attestations under the governing contract. A valid pre-attestation is required before execution; the post-attestation must be valid and report `unchanged: true`, subject to the host contract's approved expected deployment manifest. Runner output is not the comparator. Obtain all administrator-owned probe postconditions separately. Missing, invalid, stale, contradictory or changed attestations or postconditions invalidate acceptance and stop the sequence for owner investigation; a new attempt follows the applicable fresh-run and authorization rules.

## 07.5 Ordered Tasks

### Step 1 - Audit offline acceptance and compatibility

Estimate: **1-2 days / 6-12 hours**.

- [ ] Map every current FR/NFR and AC to concrete tests/procedures and evidence appropriate to its class and governing contract, using pass/fail/blocked/optional-disabled with owner, revision, environment and versions. Do not reuse superseded requirement IDs or count disabled as passed.
- [ ] Run targeted then integrated Go tests/build/vet and race-sensitive recovery checks, retained script/Python runner and MCP contracts, syntax/static safety checks and complete deterministic evaluation in documented environments.
- [ ] Regress exact-name/UUID and original goal preservation, plan approval, graph scheduling, nested/resumed scope, version-specific result status parity, output bounds, canary redaction, audit failure, checkpoint recovery and provider-independent inspection. Preserve the full applicable Phase 01–06 prerequisite regressions, including Phase 03's no-redispatch, explicit fresh re-observation, immutable approved target binding, cumulative budgets, collision/concurrency, migration and cross-sink failure guarantees. Do not imply parity approves extensions to a closed status or audit contract.
- [ ] Negatively verify the acceptance gates with offline fixtures: missing, invalid, stale, contradictory or changed pre/post attestations and missing or failed probe postconditions cannot yield acceptance or permit the next live step. Verify operational evidence rejects non-allowlisted fields and that redaction alone cannot permit retention.
- [ ] Verify manual diagnostics and existing deployment-validation interfaces remain usable. Review any state/tool/export incompatibility and require versioned conversion/parity evidence and tested rollback, rather than silent replacement.
- [ ] Reuse applicable existing Molecule/inventory validation seams, distinguishing offline checks from procedures that provision or contact hosts. Obtain approval before those procedures; report pre-existing failures without hiding them.
- [ ] Review runtime binaries, script/registry/policy/configuration versions and required/optional capability classifications; no unreviewed tool or profile may enter the release catalog.

Done when:

- [ ] All applicable offline gates pass and AC-024 compatibility evidence is ready; unresolved safety/authority/migration decisions block affected deployment.

### Step 2 - Validate the isolated observer and enabled capabilities

Estimate: **1-2 days / 6-12 hours**.

- [ ] With operator approval, install/pin the selected runtime through the maintained automation outside control-plane services. Preserve existing controller/compute/storage roles; separate immutable tools/configuration from protected application data.
- [ ] Verify only approved management/API, host and model destinations are reachable; validate required/optional startup behavior with missing tools, profiles, knowledge, stores, audit/policy and adapters. Do not weaken egress to make readiness pass.
- [ ] Prove dedicated project-reader authentication and required scoped reads, restrictive credential permissions, explicit profile binding and no inherited admin fallback. Independently verify operator-reader/SSH only if enabled.
- [ ] Review read-only role policies first, then run separately approved representative create/update/delete denial probes in a disposable scope with valid inputs and cleanup ownership. Under the [identity mutation-denial contract](../../ai-ops-revised/runtime/identity-policy-operations-contract.md#mutation-denial-and-emergency-contract), require conclusive authorization denial and independent administrator confirmation that no create occurred, the update baseline is unchanged and the delete target remains. Generic failure or a denial signature alone is insufficient; stop/revoke on unexpected success and use human-controlled cleanup.
- [ ] Reconcile `ansible/ai_ops_assistant/playbook_validate_mutation_denial.yml` before reuse: its default `aiops-probe-` prefix differs from the contract's `aiops-deny-<run-id>-` target names. Require a contract-consistent invocation or repair before live use; the playbook's `administrator_postcondition_required` flag is not the external administrator's postcondition evidence. A replacement procedure needs applicable approval.
- [ ] Verify model processes cannot obtain diagnostic credentials or use independent tool/filesystem/network authority. If remote inference is enabled, require selected destination/disclosure authorization and deployed egress enforcement; never infer isolation from an opt-in flag.
- [ ] Run approved server/boot, network/attachment and multi-target read-only smoke cases, inspect/report/export and interruption/resume. Use recorded failure fixtures rather than breaking lab services to reproduce metadata faults.
- [ ] If host tools are enabled, verify aliases/operations/windows, SSH restrictions, unavailable profiles and independent disablement. If MCP is enabled, run the selected local client smoke/parity path without implicit inference or listening ports.
- [ ] Run optional model evaluation only with separate provider/disclosure permission and repeated versioned scenarios. Record quality/latency/usage against frozen thresholds; unavailable cost data must satisfy the agreed unknown-usage policy, not be reported as free.

Done when:

- [ ] AC-011 and applicable deployed host/model checks have owner-accepted, contract-compliant outcome-only evidence, including independent unchanged-state and probe postconditions where applicable. Fixture-only, unavailable and failed gates remain explicit and block the corresponding enablement.

### Step 3 - Rehearse operations and publish the release record

Estimate: **1 day / 6 hours**.

- [ ] Have a second operator follow documented startup, no-provider diagnosis, state/report inspection, partial-outcome handling, pause/resume and safe shutdown without manual internal-state repair.
- [ ] Rehearse stop-new-dispatch, bounded active-call cancellation, adapter/tool disablement, credential and observer-key rotation/revocation, outbound-approval revocation and protected evidence preservation. Independently verify revoked access fails through direct credential-backed diagnostic scripts and, where applicable, direct observer-key/collector paths as well as normal entry points; stopping an entry point alone is not authority removal.
- [ ] Exercise retention/quota/export/deletion controls and checkpoint/audit failure recovery within each evidence class's approved policy. Preserve provenance or visibly report removed evidence; never log credentials, export unapproved context or override inherited audit retention. Preserve committed audit/evidence across cross-sink failures, expose uncertain completion, stop dispatch and never delete audit to simulate rollback.
- [ ] Rehearse rollback to validated runtime/configuration and compatible state backups; never restore admin credentials, weaker policy or silently downgrade incompatible state. OpenStack workloads remain untouched.
- [ ] Roll out in gates: manual boundary, single-server investigation, durable/domain/project workflows, then independently accepted optional integrations. Review denials, incomplete reports, unsupported claims, timeouts, truncation and usage before expansion.
- [ ] Publish the release record: exact capability matrix, runtime/registry/policy/schema versions, corpus/rubric/thresholds, deterministic results, separately labeled live/model evidence, migration/rollback procedure, known limitations and revalidation owners/triggers.
- [ ] Keep specialists, unreviewed hosts, network MCP and unsupported adapters disabled. On safety concerns stop dispatch, disable affected capabilities, revoke access and restore only a previously validated configuration.

Done when:

- [ ] AC-023–AC-025 are evidenced for the selected release, another operator can recover/revoke safely, and every conditional or blocked acceptance has an explicit disposition.

## 07.6 Phase Definition of Done

- [ ] The overview MVP path is repeatable, bounded, inspectable, durable and evidence-linked with no unacknowledged safety gap.
- [ ] All enabled capabilities satisfy applicable offline and deployed gates; disabled optional capabilities and missing evidence are visible to users.
- [ ] Existing manual/deployment workflows remain operable with tested compatibility/migration and rollback.
- [ ] Credential/data lifecycle, shutdown/recovery and release quality/usage reporting are verified; applicable independent, fresh run-bound attestations establish unchanged protected state, and all probe postconditions pass. Missing or changed comparisons block acceptance.

## 07.7 Risks

| Risk | Mitigation |
| --- | --- |
| Fixtures hide deployed RBAC/egress differences | Separate version-specific isolation, reads and denial evidence before enablement. |
| Mutation-denial probe unexpectedly succeeds | Preflight policy review, valid disposable fixtures, explicit approval, stop/revoke and independent cleanup. |
| Conditional tests look like full acceptance | Record pass/fail/blocked/optional-disabled separately for each capability and criterion. |
| Rollback leaves credentials or incompatible state active | Verify revocation and version-compatible restoration independently of stopping processes. |
| Lab changes invalidate prior acceptance | Pin versions and require revalidation on policy, runtime, provider, registry or script changes. |
