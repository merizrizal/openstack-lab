# 08. Evaluation, Acceptance and Lab Rollout

**Phase boundary:** PROPOSED.
**Authority:** Roadmap phase, not an approved implementation task contract or deployment authorization.
**Source requirements:** [PRD](../prd.md), Evaluation and operation; Testing Decisions 1–15; Acceptance Criteria; Rollout / Migration Plan; Risks and Open Questions. FR-021–FR-022, FR-025–FR-026, FR-031–FR-034, FR-037–FR-044, FR-046–FR-050; NFR-001–NFR-015; integration closure for all AC-001–AC-031, especially AC-011, AC-016–AC-017, AC-021–AC-027 and AC-029.
**Decision gaps:** All applicable G1–G6 must close with recorded decisions/evidence. G5 corpus/rubric/capability matrix and quality/latency/token-cost/unnecessary-call thresholds must be agreed and pinned before candidate evaluation. G2 exact environment/disposable scope and explicit live/model authorization are prerequisites, not assumptions that access exists.

## 08.1 Goal

Turn verified increments into an operable lab release with honest offline/live/model evidence, protected lifecycle procedures and a rehearsed safe rollback.

```text
exploratory baseline -> pre-pinned release criteria -> candidate evaluation
  -> authorized deployed/manual/host/model/MCP acceptance
  -> operations and recovery/rollback evidence -> operator rollout decision
```

## 08.2 Estimate

```text
8–13 engineer-days
48–78 focused hours
```

This is integration/acceptance effort after per-phase tests, not the first time safety is tested. External approval/access/harness installation delays are excluded. A failing gate needs repair and re-evaluation, not post-hoc relaxation.

## 08.3 Scope

Included:

- Complete credential-free evaluator, representative corpus/rubric and pinned release criteria using earlier exploratory results.
- Reproducible runtime packaging/readiness and independent observer/credential/model/client boundary validation.
- Required live project-reader, restricted-host, both real harness and at least one model-backed lab investigation evidence.
- Credential/data/session operation, shutdown/recovery, independent stop and runtime/configuration rollback, without changing workloads.
- Applicable manual/Go/lab regressions and a complete acceptance/limitations record.

Excluded:

- Claiming production SLA, live/model access from planning authority, destructive working-lab probes, application-controlled deployment or mutation-denial tools.
- Automatic legacy migration, changing acceptance thresholds after candidate results, network MCP, specialist enablement or future custom harness work.

## 08.4 Assumptions

- [ ] Phases 01–07 supply versioned contracts, focused safety/regression tests, exploratory results and actual evidence for any enabled capability.
- [ ] Operator supplies explicit authorization for observer deployment, exact endpoints/resources, safe policy probes, required hosts, provider/model destinations and standalone client egress.
- [ ] One controller/two computes have valid restricted-host evidence or remain a release blocker; operator-reader diagnostics may remain unavailable if safe access cannot be validated.
- [ ] Existing Ansible/Molecule workflows remain operator-controlled and may be selectively extended, not replaced or invoked blindly against the lab.

## 08.5 Ordered Tasks

### Step 1 - Pin the evaluation contract before candidate scoring

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Consolidate the versioned deterministic corpus and model/tool/API substitutes; run offline without cloud/provider credentials and emit machine-readable expected/actual scenario results.
- [ ] Include healthy server, NoValidHost sufficient and unavailable-capacity evidence, metadata listener failure, Neutron failure, volume attachment, denial, ambiguous/missing resource, outage, hostile logs and multi-server partial failure.
- [ ] Include authorization/graph/approval, secret-canary, audit/checkpoint/quota/cleanup, uncertain recovery, revocation races, entry-point parity and disabled-specialist regressions. Require zero unauthorized executions, mutations and prohibited disclosures.
- [ ] Publish task success, tool appropriateness, unsupported claims, unnecessary calls, latency distributions and measured/unknown token-cost data. Expected inconclusive results must not be scored as fabricated diagnosis or silently dropped.
- [ ] Use the exploratory baseline to obtain owner agreement on versioned corpus, semantic rubric, supported matrix and quality/latency/cost/unnecessary-call thresholds before evaluating the release candidate. Record timing/version evidence and keep criteria fixed for that candidate.
- [ ] Separate deterministic acceptance from nondeterministic repeated model evaluation. Additional model evaluations require explicit provider approval and a versioned repeated-run methodology; do not require unapproved spending.

Done when:

- [ ] Candidate evaluation is reproducible against pre-agreed criteria, with any failed threshold visible and no retroactive tuning of pass rules.

### Step 2 - Validate the observer and required diagnostic access

Estimate: **2–4 engineer-days / 12–24 hours**.

- [ ] Build/reproducibly install one Go executable on the authorized Ubuntu 24.04 x86-64 non-root observer outside the observed cloud/control plane. Record runtime/toolchain/dependency/artifact/policy versions and external service/configuration/state prerequisites.
- [ ] Verify management-only required reachability, Keystone token issuance, dedicated project-reader access and required live project-resource/server-basic/server-network diagnostics. Tenant-network placement must not be required.
- [ ] Use separate operator-controlled preflight and explicitly authorized disposable project/resources to validate representative create/update/delete denial. Require a cleanup owner and safeguards for unexpected permission grants; do not add mutation tools or probe working resources destructively.
- [ ] Integrate/revalidate restricted-host evidence on one controller and two compute nodes, with actual profiles, fixed operations/windows and safe output bounds. Required missing host evidence blocks release.
- [ ] Live-validate enabled operator-reader diagnostics separately; otherwise record unavailable profile/capabilities and their offline catalog evidence. No admin fallback.
- [ ] Exercise readiness of required policy/audit/checkpoint/store/quota/isolation dependencies and optional knowledge/operator/model capabilities. Missing required controls stop execution; provider absence alone cannot disable healthy manual/local access.
- [ ] Verify built-in diagnostics without separately deployed diagnostic scripts/utilities/interpreters, including the host mechanism. External operator-installed Codex/Pi and their runtime dependencies remain explicit model-only prerequisites.

Done when:

- [ ] A sanitized deployment record demonstrates actual observer, reader, three-host and packaging properties, with controlled disposable policy-denial evidence distinct from fixture results.

### Step 3 - Close real harness, client and end-to-end acceptance

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Complete authorized real-model integration checks for both Codex and Pi using approved tested combinations. One may use controlled fixture evidence; both still require deterministic inference/version/cancellation/isolation contract results.
- [ ] Complete at least one real model-backed lab investigation under explicit diagnostic scope, exact plan approval, destination/data consent and verified isolation; collect a relevant live observation and preserve provenance/audit.
- [ ] Verify the investigation exposes gaps, makes no unsupported claim or mutation, and reports operational completion separately from confidence. An honestly inconclusive live result may pass; sufficient-evidence corpus scenarios must also demonstrate supported failure domains.
- [ ] Record independently enforced model/credential isolation and negative bypass tests in the deployed context; flags, shared processes or filtered environments alone are not evidence.
- [ ] Integrate real standalone Pi MCP tools/resources/prompts, client-context binding, one-hour approval and independently enforced egress/teardown evidence. Keep it distinct from Pi’s Go inference-only role.
- [ ] Re-run applicable entry-point parity and manual selection → sanitized Go paste-analysis checks in the acceptance configuration; label each result offline, controlled real-model or deployed live evidence.

Done when:

- [ ] Both real harness checks, the real lab investigation and real standalone Pi interoperability have separate authorized records linked to supported versions and the acceptance ledger.

### Step 4 - Rehearse operation, recovery and rollback; publish release evidence

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Document/rehearse startup, independent stop, bounded shutdown, safe in-flight cancellation, session/egress revocation and audit-gap/uncertain-call acknowledged recovery.
- [ ] Provide operator credential revocation/rotation and disclosure-policy change procedures for cloud, SSH observer, provider and client contexts without exposing secrets in logs/reports.
- [ ] Rehearse configured quota and physical disk-full behavior, cleanup after downtime, retention/active-reference exceptions, alias-default export, warned/audited identifier export and confirmed permitted deletion. Preserve legacy files and audit retention.
- [ ] Roll back to a validated runtime/configuration with compatible new-store handling, protected backups/recovery where required and no legacy import/approval reuse. Do not claim incompatible state is resumable or alter OpenStack workloads.
- [ ] Verify applicable Go/manual contracts and lab deployment/validation paths remain operable; extend existing CI with credential-free Go gates as appropriate. Separate safe static/fixture checks from any authorized live Molecule runs.
- [ ] Publish artifact and policy identities, capability matrix, exploratory baseline, pinned corpus/rubric/thresholds, candidate results, deterministic safety outcomes, deployed/model/client evidence, acceptance coverage, operating guide and unresolved limitations.
- [ ] Define rollback/stop triggers for scope violations, unsupported claims, audit/checkpoint failures, timeouts/truncation and isolation/egress problems; preserve protected evidence and disable/revoke affected capabilities before any operator-directed restoration.

Done when:

- [ ] Recovery/rollback and applicable regressions have recorded outcomes, every AC is evidenced or explicitly blocking/conditionally unavailable, and the operator can make a separate rollout decision without relying on roadmap authority.

### Proposed verification commands and safety classification

Observed existing Go targets, to run only during separately authorized implementation/verification:

```bash
rtk make -C aiops test
rtk make -C aiops build
```

The current build emits four binaries; it must be revised under the approved consolidation task before it can prove the single-executable target. Focused package tests, formatting and new scenario/protocol/packaging checks should be specified for each actual change, not assumed to exist today. Additive offline CI wiring is a proposal.

Existing lab entry points include `rtk make validate-openstack`, `rtk make validate-ceph`, `rtk make test-openstack` and `rtk make test-ceph`. These are context, not instructions to execute now: root Makefile loads `.env`, validation writes result artifacts, smoke tests reach lab services, and optional E2E lifecycle paths can mutate resources. Review commands/playbooks and obtain explicit access/test authorization before any use. No test was run to generate this roadmap.

## 08.6 Phase Definition of Done

- [ ] All applicable AC-001–AC-031 have source/version-linked evidence; no mandatory requirement is silently deferred.
- [ ] Pre-pinned quality/resource criteria and all deterministic safety gates pass; no prohibited execution/mutation/disclosure is accepted.
- [ ] Required project-reader, three-host, both real harness, standalone Pi MCP and real lab investigation evidence is complete and distinct from offline fixtures.
- [ ] One-executable diagnostic deployment and independent non-root credential/model/client isolation/egress are demonstrated.
- [ ] Manual/local degraded operation, lifecycle, credential rotation/revocation, shutdown/recovery and workload-preserving rollback are verified.
- [ ] Conditional operator-reader unavailability and disabled specialists are explicit; missing mandatory host/model/MCP evidence is a blocker, not a limitation waived by documentation.
- [ ] Rollout/deployment authorization is a separate operator decision; this roadmap never grants it.

## 08.7 Risks

| Risk | Mitigation |
| --- | --- |
| Candidate results drive easier pass criteria | Record baseline first and pin corpus/rubric/thresholds before candidate evaluation. |
| Fixture/model results are represented as deployed safety | Label evidence tiers, commands, versions, scope and actual results separately. |
| Mutation-denial probe unexpectedly succeeds | Preflight policy checks, explicitly authorized disposable resources, cleanup owner; no working-lab destructive tests. |
| Single executable hides external diagnostic dependencies | Utility-free controlled packaging test plus actual API/host prerequisite validation. |
| Rollback restores unsafe policy or corrupts data | Validated version/config pairing, compatibility checks and protected recovery; no implicit legacy migration. |
| Required access is unavailable | Stop affected enablement/acceptance and report exact missing evidence; do not lower security or expand scope. |

## 08.8 Proposed Requirement Coverage and Handoff

| Requirement / AC source | Proposed phase responsibility | Existing behavior / deferral | Risk or unapproved decision |
| --- | --- | --- | --- |
| FR-037–FR-040; AC-021/022/025; NFR-007/009/015 | Final corpus, metrics, fixed criteria and release evidence | Builds on earlier offline/exploratory work | G5 owner agreement before candidate scoring. |
| FR-021–FR-022/025–FR-026/043–FR-044; AC-011/013/026/027 | Actual observer/reader/host acceptance and controlled policy checks | Optional operator-reader may stay unavailable; required host evidence cannot | G2/G3 exact authorized acceptance environment. |
| FR-031–FR-035/046–FR-047; AC-016–AC-019/028–AC-030 | Both real harnesses, independent isolation, manual analysis and real client proof | No fixture substitution for required lab/model/client evidence | G1/G6 verified isolation and managed egress. |
| FR-041–FR-042/048–FR-050; AC-023/024/031 | Readiness, protected operations, regression and rollback | Legacy files remain operator-managed, unchanged and unimported | G4 storage/compatibility and recovery design. |
| AC-001–AC-031 | Full acceptance ledger and unresolved-blocker report | No observed existing behavior is accepted without verification | Human rollout approval remains separate. |

Proposed handoff is the factual release evidence/limitations packet and an operator rollout decision request, not automatic deployment. Independent scope readiness and a separate approved task contract are still required for implementing this phase; this phase file is neither.
