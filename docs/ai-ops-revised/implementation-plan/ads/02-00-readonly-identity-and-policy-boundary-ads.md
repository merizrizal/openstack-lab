## Architectural Design Specification: Revised Read-Only Identity and Policy Boundary

**Source:** `docs/ai-ops-revised/implementation-plan/02-readonly-identity-and-policy-boundary.md`, Steps 1–6

**Goal:** Create a fresh, revocable, distinctly named project-reader identity and protected runtime profile for `assistant02`, empirically prove the required project reads and representative create/update/delete denials, and publish a redacted lifecycle and policy matrix without importing historical credentials, broadening OpenStack policy, or enabling operator-reader authority.

---

### I. Overview and Contract

Phase 02 may begin live work only after Phase 01 foundation acceptance and its transport gates are closed. It adds the first OpenStack authority to the revised runtime:

```text
accepted isolated assistant02 foundation
  -> approved credential and policy matrix
  -> fresh dedicated identity and least-privileged project role
  -> fresh application credential where supported
  -> protected aiops-assistant-project-reader profile
  -> authentication and project-read matrix
  -> safe create/update/delete denial matrix
  -> redacted lifecycle record
  -> Phase 03 eligibility
```

This phase proves authority boundaries; it does not implement diagnostics. The assistant receives no admin, member, service, database, RabbitMQ, root SSH, unrestricted sudo, operator-reader, generic OpenStack passthrough, runner, MCP, provider, egress, or remediation capability.

#### Activation prerequisites

Live Phase 02 execution is blocked until all of the following are true:

1. Phase 01 is live-accepted with redacted evidence, including a second idempotent foundation apply.
2. SSH host verification is enabled with an operator-approved known-hosts source, or the approved Local-Lab SSH Transport Exception in `foundation-operations-contract.md` applies only to `assistant02` in the `local` inventory. The exception must not be copied to any other inventory or environment.
3. `assistant02` is verified as the isolated revised host and the credential directory exists with owner/group `aiops_assistant:aiops_assistant` and mode `0700`.
4. A human administrator approves the initial project, domain, exact reader role, identity owner, expiry, rotation, revocation, and disposable mutation-probe resources.
5. The selective-reuse manifest records the Phase 02 disposition of the three historical credential candidate paths before any historical content is adapted. Candidate status is not copy authority.
6. An operator-controlled secret transfer/source procedure is approved. It must not use repository files, shell arguments, process-visible environment values, generated prior-runtime profiles, or printed Ansible variables.

Failure of any prerequisite leaves Phase 02 gated and does not authorize a workaround.

#### Credential and policy matrix contract

The matrix must be written before credential installation and must identify:

| Matrix area | Required contract |
| --- | --- |
| Identity | Fresh revised identity; distinct name, owner, purpose, domain, project, role, creation time, expiry, rotation, and revocation procedure. |
| Default profile | Exactly `aiops-assistant-project-reader`; project-scoped and read-only. |
| Required reads | Token scope plus server, network, subnet, port, volume, image, and security-group list/show behavior needed by the MVP. |
| Expected unavailable reads | Service, hypervisor, Neutron-agent, and broader cloud-health reads remain unavailable unless Phase 06 separately approves operator-reader authority. |
| Required denials | Representative create, update, and delete operations must fail with an authorization result, not merely malformed input, missing endpoint, or missing target. |
| Blocking rule | Any unexpected mutation success immediately blocks rollout, triggers credential revocation, and requires administrator-owned verification and cleanup. |
| Policy variation | Empty state, missing service catalog, endpoint/connectivity failure, authentication failure, and policy denial are distinct result classes. |

#### Identity creation contract

**Administrative Procedure Contract (Concrete):** a human administrator creates the dedicated revised identity, assigns only the deployed least-privileged project-reader role, and preferably creates an application credential with the narrowest supported role and expiry. No assistant-side role or policy administration is permitted.

Inputs:

- approved identity/profile metadata and selected project/domain;
- exact deployed reader role and application-credential support;
- administrator-controlled secret delivery path.

Outputs:

- fresh, independently revocable credential material;
- non-secret creation metadata and revocation identifier retained in the approved operator system;
- no secret value in Git, terminal history, Ansible output, evidence, or prior runtime paths.

If application credentials are unsupported, a fresh dedicated user credential is an **exception requiring explicit approval**, documented rotation, and the same project-reader denial proof. A human, admin, member, service, or prior-runtime credential is never an acceptable fallback.

#### Runtime profile contract

The following are **concrete** from the revised namespace contracts:

| Concern | Revised value |
| --- | --- |
| Host/group | `assistant02` / `ai_ops_assistant` |
| Runtime user/group | `aiops_assistant` / `aiops_assistant` |
| Credential root | `/opt/openstack-ai-ops-assistant/credentials` |
| Default cloud profile | `aiops-assistant-project-reader` |
| Initial Keystone endpoint | `http://192.168.121.5:5000/v3` |

The following layout is a **proposed contract**, subject to Chunk 0 confirmation:

```text
/opt/openstack-ai-ops-assistant/credentials/profiles/
  clouds.yaml
  secure.yaml     # optional; only when the selected OpenStack client format supports a safe split
```

- `profiles/` must be owned by `aiops_assistant:aiops_assistant` with mode `0700`.
- Every profile file must be a regular file, not a symlink, owned by `aiops_assistant:aiops_assistant`, with mode `0600`.
- Real files remain runtime-local and uncommitted.
- The source path must be explicit, outside the repository and historical runtime, approved by the operator, and validated without printing content.
- Deployment must use Ansible `no_log: true` for every task that can observe content, checksums, command output, or secret-bearing variables.
- Unrelated operator/provisioning sessions must not inherit `OS_CLOUD`, `OS_CLIENT_CONFIG_FILE`, passwords, tokens, or application-credential values.

A committed redacted example may show keys and placeholders only. It must not be executable as a real profile and must use the revised profile name and path.

#### Ansible contracts

**Module Contract (Conceptual):** proposed role `ai_ops_assistant_identity_boundary` under `ansible/ai_ops_assistant/roles/`.

Inputs:

- exact revised host/group/runtime/profile constants;
- explicit externally controlled profile source directory;
- source-location classification (`controller-local` or `assistant02-local`, proposed);
- expected profile filenames and restrictive ownership/modes;
- explicit enable flag.

Outputs/state:

- protected revised profile directory and files only;
- no identity, role, application credential, OpenStack resource, policy, route, service, listener, or historical runtime mutation;
- secret values and secret-bearing checksums absent from output.

**Stub Behavior Contract (Conceptual):** the initial role validates constants and source-policy inputs, then returns `ERR_IDENTITY_PROFILE_NOT_IMPLEMENTED` (proposed). It must not return success because that would falsely claim credential protection.

**Profile Deployment Entrypoint Contract (Conceptual):** proposed `ansible/ai_ops_assistant/playbook_deploy_identity_profile.yml` targets only `ai_ops_assistant`, is always limited to `assistant02`, invokes only the revised identity-boundary role, and receives no secret values from committed vars.

**Read Validation Contract (Conceptual):** proposed `ansible/ai_ops_assistant/playbook_validate_project_reader.yml` authenticates and runs fixed argument-vector read operations. It logs only operation labels and normalized result classes; raw token, stdout, stderr, catalog, resource records, IDs, addresses, and profile contents remain suppressed.

**Mutation-Denial Contract (Conceptual):** proposed `ansible/ai_ops_assistant/playbook_validate_mutation_denial.yml` runs only a reviewer-approved matrix against uniquely named, administrator-prepared disposable targets. It must distinguish HTTP authorization denial from all inconclusive failures, stop at the first mutation success, never clean up with the reader credential, and emit only normalized outcome metadata.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `02-readonly-identity-and-policy-boundary.md` requires a fresh dedicated identity, preferably an application credential, a protected named profile, useful read proof, create/update/delete denial proof, revocation on unexpected success, and separate operator-reader scope.
- `prd.md` FR-005 through FR-010 require a dedicated identity, project-scoped read-only default, restrictive storage, successful read validation, and failed create/update/delete validation. NFR-001 through NFR-006 require least privilege, deny-by-default behavior, no privileged credentials, no secret logging, safe failures, and explicit unavailable behavior.
- `runtime-placement-contract.md` fixes `assistant02`, `ai_ops_assistant`, `/opt/openstack-ai-ops-assistant`, `aiops_assistant`, and `aiops-assistant-project-reader` as revised identifiers.
- `foundation-operations-contract.md` assigns `/opt/openstack-ai-ops-assistant/credentials` to Phase 02 with owner/group `aiops_assistant:aiops_assistant` and mode `0700`; it explicitly defers authentication to Phase 02.
- The current foundation role creates the credential root but no profile files, identities, or authentication state.
- `playbook_validate_foundation.yml` is non-mutating and checks only TCP reachability to the fixed Keystone endpoint; it does not authenticate.
- Phase 01 live acceptance is recorded in redacted external evidence. Its Local-Lab SSH Transport Exception permits the existing `common_vars.yml` bypass only for `assistant02` in the `local` inventory; Phase 02 must not extend that exception.
- `source-capability-catalog.md` classifies historical `credentials.yml` and two Phase 02 validation playbooks as candidates. The selective-reuse manifest has not selected them.
- Historical `credentials.yml` copies `clouds.yaml` and `secure.yaml` from a caller-provided source with `no_log`, owner/mode controls, and no backup. Those ideas may inform review, but the historical paths and variables are not revised contracts.
- Historical read validation writes raw command stdout/stderr into evidence, which conflicts with the revised minimum-disclosure boundary.
- Historical mutation validation couples to repository-generated profiles, attempts updates against a named existing network, attempts deletion of a named security group, and tries cleanup with the same reader credential after unexpected create success. These behaviors must not be copied into the revised implementation.
- Phase 03 explicitly depends on an available fresh revised project-reader profile and tested read matrix.
- The worktree was clean on branch `ai-ops-assistant-phase01` during ADS discovery.

#### Assumptions

- A human administrator can create the identity, role assignment, application credential, and disposable mutation targets outside assistant automation.
- The deployed OpenStack CLI can use a named `clouds.yaml` profile and optional `secure.yaml`; exact auth keys depend on the selected credential type and must be confirmed without exposing values.
- The selected project contains representative resources, or accepted empty-state/service limitations can be documented without broadening authority.
- CLI authorization failures contain a stable enough HTTP status or exception class to normalize without retaining raw stderr. Chunk 0 must confirm this against the installed client version before denial acceptance.
- Redacted live evidence is retained outside Git; source-controlled documents contain contracts, procedures, and reviewed result classifications only.

#### Open confirmations for Chunk 0

1. Is Phase 01 live-accepted, and are the host-verification, protected-inventory, check/apply/validation, idempotency, and evidence gates closed?
2. What project, domain, identity name, exact reader role, owner, purpose, expiry, and rotation interval are approved?
3. Does Keystone support application credentials with the required role restriction and expiry?
4. Which profile format is approved: one `clouds.yaml` or `clouds.yaml` plus `secure.yaml`?
5. What external secret source and transfer mechanism avoids Git, command arguments, inherited environments, prior-runtime paths, and printed values?
6. Must the historical candidate paths remain reference-only, or will the selective-reuse manifest select exact paths for Phase 02 review after dependency analysis?
7. Which read operations and result classifications form the MVP matrix for this deployed release?
8. Which administrator-created disposable resource types can safely prove update and delete denial, and who owns cleanup/restoration?
9. What exact authorization signatures from the installed CLI count as conclusive denial?
10. Where will redacted live evidence be retained outside Git, and which metadata fields are approved?

### III. Required Technical Dependencies and Imports

#### Confirmed repository dependencies

- `docs/ai-ops-revised/prd.md`
- `docs/ai-ops-revised/implementation-plan/00-implementation-overview.md`
- `docs/ai-ops-revised/implementation-plan/01-baseline-and-runtime-foundation.md`
- `docs/ai-ops-revised/implementation-plan/02-readonly-identity-and-policy-boundary.md`
- `docs/ai-ops-revised/implementation-plan/03-manual-diagnostic-toolbox.md`
- `docs/ai-ops-revised/implementation-plan/ads/01-01-minimal-runtime-foundation-and-isolation-ads.md`
- `docs/ai-ops-revised/runtime/runtime-placement-contract.md`
- `docs/ai-ops-revised/runtime/foundation-operations-contract.md`
- `docs/ai-ops-revised/runtime/source-capability-catalog.md`
- `docs/ai-ops-revised/runtime/selective-reuse-manifest.md`
- existing revised foundation role, inventory, setup entrypoint, and validation entrypoint

#### Runtime and administrative dependencies

- live-accepted `assistant02` foundation;
- installed `python3-openstackclient` and `python3-openstacksdk` packages;
- management connectivity to the approved Keystone and project-service endpoints required by the read matrix;
- human administrator access for identity, role, application-credential, revocation, disposable-target preparation, verification, and cleanup;
- operator-approved known-hosts and secret-delivery procedures;
- representative project resources or accepted empty-state classifications.

#### Proposed implementation dependencies

- Ansible built-in modules for assertions, file/stat, copy, command with `argv`, and sanitized facts/debug output;
- no new collection, Python package, package repository, downloaded artifact, daemon, listener, policy change, or service;
- OpenStack CLI only as a fixed validation implementation, never as a generic AI-facing capability;
- isolated `/tmp` Python virtual environment populated from root `requirements.txt` for Ansible lint/syntax checks.

### IV. Step-by-Step Procedure / Execution Flow

1. Reconfirm branch, `HEAD`, worktree/index state, Phase 01 acceptance, transport safety, and protected-input policy.
2. Review the three historical Phase 02 candidates at their pinned revision, record dependency closure and unsafe differences, then amend the selective-reuse manifest or leave them reference-only. Do not copy credential values or generated profiles.
3. Finalize the credential/policy matrix before creating authority: project, domain, role, profile, owner, lifecycle, read operations, unavailable operations, denial operations, result classes, disposable targets, emergency stop, and evidence schema.
4. Have a human administrator create the fresh revised identity and least-privileged role assignment. Prefer a narrowly scoped, expiring application credential.
5. Record non-secret creation and revocation metadata in the approved operator system. Deliver secret material only through the approved external path.
6. Add a fail-closed revised identity-boundary role contract and validate it statically.
7. Implement restrictive profile directory/file deployment from the external source. Reject symlinks, unexpected filenames, paths outside approved roots, weak modes, historical profile names, and operator-reader entries.
8. Add the revised profile deployment entrypoint, targeting only `ai_ops_assistant` and requiring `--limit assistant02`.
9. Run local lint, syntax, target, path, secret-pattern, historical-identifier, and excluded-capability checks. Obtain explicit approval before any host connection.
10. Run approved check mode for profile metadata/permissions only. Ensure diff output cannot disclose content. Review before apply.
11. Apply the protected profile to `assistant02`; verify existence, regular-file type, owner/group, mode, profile name, and absence of ambient credential environment without printing content or checksums.
12. Run fixed authentication and read checks as `aiops_assistant`. Classify each operation as `pass`, `empty`, `policy_denied`, `service_unavailable`, `catalog_missing`, `connectivity_error`, `authentication_error`, or `configuration_error` (proposed). Do not retain resource payloads.
13. Have the administrator prepare uniquely named disposable update/delete targets and record their baseline externally. Verify production resources are not selected.
14. Run create denial first. Accept only a conclusive authorization denial. On success, stop immediately, revoke the credential, and use administrator-owned verification/cleanup.
15. If create denial passes, run update denial against its approved disposable target. On success, stop and invoke the same emergency procedure.
16. If update denial passes, run delete denial against its separate approved disposable target. On success, stop and invoke the same emergency procedure.
17. Verify postconditions through the administrator-approved path: no create probe exists, the update target baseline is unchanged, and the delete target still exists. The reader credential is not the cleanup authority.
18. Capture only redacted matrix outcomes and lifecycle metadata outside Git. Scan retained evidence for secrets, tokens, raw resource data, IDs/addresses beyond classification, and raw stderr.
19. Re-run profile deployment to prove idempotency; then verify revocation and local profile removal through a controlled lifecycle rehearsal if the operator approves a replaceable test credential.
20. Reconcile Phase 02 checkboxes only where live evidence proves completion. Stop before Phase 03 implementation.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| --- | --- | --- | --- |
| Prerequisite | Phase 01 is not live-accepted, or transport is neither host-verified nor covered by the approved Local-Lab SSH Transport Exception | Do not connect, install, authenticate, or create credentials for assistant use | `ERR_PHASE01_GATE_OPEN` (proposed) |
| Reuse review | Historical candidate is copied without manifest disposition and dependency review | Reject the change and preserve historical source unchanged | `ERR_PHASE02_REUSE_UNAPPROVED` (proposed) |
| Matrix | Project, role, reads, denials, lifecycle, or disposable targets are undefined | Stop before identity creation | `ERR_CREDENTIAL_MATRIX_INCOMPLETE` (proposed) |
| Identity | Human/admin/member/service/prior-runtime credential is proposed | Reject it; require a fresh dedicated revised identity | `ERR_CREDENTIAL_PROVENANCE` (proposed) |
| Role | Assigned role is broader than approved project reader | Remove/revoke the assignment before profile deployment | `ERR_ROLE_TOO_BROAD` (proposed) |
| Application credential | Unsupported or creation denied | Require explicit dedicated-user fallback approval; never fall back silently | `ERR_APP_CREDENTIAL_UNAVAILABLE` (proposed) |
| Secret source | Source is in Git, historical runtime, command arguments, inherited environment, or an unapproved path | Stop without reading or copying content | `ERR_SECRET_SOURCE_UNSAFE` (proposed) |
| Profile deployment | Source or destination is a symlink, has unexpected files, weak modes, or wrong ownership | Fail before authentication; do not print metadata that identifies secrets | `ERR_PROFILE_STORAGE_UNSAFE` (proposed) |
| Profile scope | Profile name, project, domain, auth endpoint, or role metadata differs from the approved matrix | Quarantine/remove the revised profile and request administrator review | `ERR_PROFILE_SCOPE_MISMATCH` (proposed) |
| Authentication | Token issuance fails | Classify connectivity, configuration, secret, scope, or Keystone failure without logging token/error payload | `ERR_PROJECT_READER_AUTH` (proposed) |
| Read matrix | Required read fails or service is absent | Record the exact normalized class; do not broaden role or policy automatically | `ERR_REQUIRED_READ_UNAVAILABLE` (proposed) or accepted limitation |
| Denial classification | Command fails due to invalid input, 404, connectivity, catalog, or client error | Mark inconclusive; redesign or rerun only after review | `ERR_DENIAL_INCONCLUSIVE` (proposed) |
| Create denial | Disposable create succeeds | Stop immediately, revoke credential, verify/clean up through admin path | `ERR_MUTATION_CREATE_ALLOWED` (proposed) |
| Update denial | Disposable target changes | Stop immediately, revoke credential, restore through admin path | `ERR_MUTATION_UPDATE_ALLOWED` (proposed) |
| Delete denial | Disposable target is deleted | Stop immediately, revoke credential, recreate only through admin path | `ERR_MUTATION_DELETE_ALLOWED` (proposed) |
| Cleanup | Reader credential is used as emergency cleanup authority | Refuse; use the pre-approved administrator procedure | `ERR_MUTATION_CLEANUP_AUTHORITY` (proposed) |
| Evidence | Token, secret, profile content, raw stderr/stdout, or sensitive topology enters output | Stop retention, rotate if exposed, sanitize, and rerun | `ERR_SECRET_IN_EVIDENCE` (proposed) |
| Operator scope | Missing project visibility falls back to operator/admin profile | Return unavailable and keep broader profile absent | `ERR_UNSAFE_PROFILE_FALLBACK` (proposed) |
| Idempotency | Second profile deployment changes content or metadata unexpectedly | Stop and investigate source drift or task behavior | `ERR_PROFILE_NOT_IDEMPOTENT` (proposed) |
| Revocation | Revoked credential still authenticates | Disable identity/profile use and escalate to Keystone administrator | `ERR_REVOCATION_INEFFECTIVE` (proposed) |

### VI. Security, Integrity, Idempotency, and Cleanup

#### Security

- Create all identity and credential material fresh; never read or copy prior runtime profiles, generated cloud files, OpenRC files, human/admin credentials, tokens, or keys.
- Keep secret values out of Git, Ansible vars, CLI arguments, inherited process environments, logs, diffs, facts, check-mode output, evidence, and shell history.
- Use `no_log: true` across every profile-copy, parse, authentication, read, and denial task that could expose payload or error content.
- Execute validation as `aiops_assistant`, not root, except narrow file metadata/ownership tasks requiring privilege.
- Use exact `argv` operations from the approved matrix. Do not expose generic OpenStack CLI, shell, file, SSH, or sudo capability.
- Keep operator-reader absent by default. Missing broader visibility becomes `unavailable`, never profile fallback.
- Do not change OpenStack policy merely to pass validation.

#### Integrity

- Pin historical review to the manifest provenance and preserve `ansible/ai_ops_runtime/` unchanged.
- Validate profile destination boundaries, regular-file type, exact filenames, owner/group, and numeric modes before authentication.
- Prove authorization denial, not generic command failure. Raw errors may be inspected under `no_log` only to derive a reviewed normalized result.
- Use separate, uniquely named, administrator-created disposable resources for update and delete probes. Never target existing production/lab resources.
- Require out-of-band administrator postcondition checks after every probe sequence.
- Treat any mutation success as credential compromise or policy-boundary failure, not a cleanup branch that permits continued testing.

#### Idempotency

- Reapplying directory/file protection with the same approved external source must report no changes.
- Authentication and read checks must be non-mutating and safe to repeat.
- Denial probes require a unique approved run identifier and fresh disposable targets; a prior run cannot be silently reused.
- Evidence records use bounded, unique run identifiers outside Git and do not append raw output.
- Role assignment and application-credential creation are administrator-owned lifecycle operations, not blindly repeated Ansible tasks.

#### Cleanup and rollback

Normal profile rollback:

1. disable future revised profile deployment/validation;
2. revoke the application credential or disable the dedicated identity through the administrator path;
3. verify authentication no longer succeeds without exposing token output;
4. securely remove only revised profile files and the Phase 02-created `profiles/` directory from `assistant02`;
5. preserve reviewed redacted lifecycle evidence according to policy;
6. retain the Phase 01 credential root if the foundation remains deployed.

Unexpected mutation rollback:

1. stop all remaining probes;
2. revoke the credential immediately;
3. have an administrator verify the affected disposable resource IDs and project state;
4. remove, restore, or recreate only disposable probe resources through the administrator path;
5. investigate role assignment and policy behavior before issuing replacement credentials;
6. repeat the complete matrix with a fresh credential only after approval.

Rollback must never alter `assistant01`, historical source/runtime, shared roles, production project resources, OpenStack policy, control-plane services, or unrelated credentials.

### VII. Validation Strategy

No command that contacts `assistant02` or OpenStack is authorized until its chunk and all prerequisites are explicitly approved.

#### Documentation and repository checks

```bash
rtk git status --short --branch
rtk git diff --check
rtk grep -nE '^### (I|II|III|IV|V|VI|VII|VIII|IX|X)\.' docs/ai-ops-revised/implementation-plan/ads/02-00-readonly-identity-and-policy-boundary-ads.md
rtk grep -RniE 'assistant01|/opt/openstack-ai-ops/|aiops-project-reader' ansible/ai_ops_assistant docs/ai-ops-revised/runtime docs/ai-ops-revised/implementation-plan/ads
rtk git diff --exit-code -- ansible/ai_ops_runtime inventories/local/nodes.yml
```

Every historical-identifier match must be documentation describing rejection or history; revised execution paths must contain none.

#### Static secret and scope checks

```bash
rtk grep -RniE 'password:|token:|secret:|application_credential_secret|private_key|admin-openrc|OS_PASSWORD|OS_TOKEN' ansible/ai_ops_assistant docs/ai-ops-revised
rtk grep -RniE 'hosts:[[:space:]]+all|hosts:[[:space:]]+assistant$|operator.reader|operator_reader|admin|member|service' ansible/ai_ops_assistant
rtk git diff -- ansible/ai_ops_assistant docs/ai-ops-revised | rtk grep -nE 'clouds\.yaml|secure\.yaml|no_log|0600|0700|copy:|command:'
```

Matches require manual classification. Placeholder examples must be unmistakably redacted; no real secret-shaped values are permitted.

#### Ansible lint and syntax

Use the existing isolated environment or create another under `/tmp` from root `requirements.txt`:

```bash
rtk python3 -m venv /tmp/openstack-lab-ai-ops-phase02-venv
. /tmp/openstack-lab-ai-ops-phase02-venv/bin/activate
rtk python -m pip install -r requirements.txt
rtk ansible-lint ansible/ai_ops_assistant/roles/ai_ops_assistant_identity_boundary ansible/ai_ops_assistant/playbook_deploy_identity_profile.yml ansible/ai_ops_assistant/playbook_validate_project_reader.yml ansible/ai_ops_assistant/playbook_validate_mutation_denial.yml
rtk ansible-playbook --syntax-check -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_deploy_identity_profile.yml
rtk ansible-playbook --syntax-check -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_validate_project_reader.yml
rtk ansible-playbook --syntax-check -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_validate_mutation_denial.yml
```

All proposed paths are subject to Chunk 0 confirmation.

#### Static contract checks

Verify that:

- all playbooks target exactly `ai_ops_assistant` and require operator use of `--limit assistant02`;
- profile source and destination assertions reject repository, historical runtime, symlink, traversal, and unexpected filename cases;
- all secret-observing tasks use `no_log: true`;
- no task creates users, roles, application credentials, policies, routes, services, or non-disposable OpenStack resources;
- every OpenStack invocation uses a fixed `argv` list and the revised profile;
- read output and denial stderr/stdout cannot reach debug or evidence;
- non-authorization errors cannot satisfy a denial assertion;
- each mutation success stops execution before the next probe;
- no cleanup uses the project-reader credential;
- operator-reader and admin fallback are absent.

#### Approved live profile checks

After explicit approval and with the operator-controlled source and approved transport procedure (host verification or the scoped Local-Lab SSH Transport Exception):

```bash
rtk ansible-playbook --check --diff --limit assistant02 -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_deploy_identity_profile.yml
rtk ansible-playbook --limit assistant02 -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_deploy_identity_profile.yml
rtk ansible-playbook --limit assistant02 -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_validate_project_reader.yml
```

Exact extra-vars, secret-source arguments, vault identifiers, and transport credentials are intentionally omitted. They must not be pasted into source or evidence.

#### Approved mutation-denial checks

Run only after the read matrix passes or has explicitly accepted limitations, disposable resources are administrator-prepared, and emergency revocation/cleanup is ready:

```bash
rtk ansible-playbook --limit assistant02 -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_validate_mutation_denial.yml
```

The concrete disposable target variables are intentionally omitted. The retained record contains only operation label, normalized result class, authorization-denied boolean, postcondition boolean, and non-secret run identifier.

#### Lifecycle and idempotency checks

- rerun profile deployment with identical approved inputs and require zero changes;
- rehearse rotation with a fresh application credential when approved;
- revoke the superseded credential and prove authentication failure without logging output;
- remove stale runtime-local profile files only after replacement or rollback is accepted;
- re-run the read/denial matrix after OpenStack upgrades or policy changes.

#### Final diff review

```bash
rtk git diff --check
rtk git status --short
rtk git diff -- docs/ai-ops-revised ansible/ai_ops_assistant
rtk git diff --exit-code -- ansible/ai_ops_runtime inventories/local/nodes.yml
```

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full Phase 02 boundary in one pass.

#### Chunk 0: Discovery and Integration Confirmation

- **Goal:** Resolve Phase 01 acceptance, transport, project/role, application-credential, profile-format, secret-source, reuse-manifest, read-matrix, denial-target, authorization-signature, and evidence gates.
- **Files to read:** this ADS; Phase 01/02 plans; foundation and placement contracts; source catalog and selective-reuse manifest; revised foundation implementation; three historical candidate paths at pinned provenance; protected inputs only through approved classification procedures.
- **Commands:** bounded Git status/diff/provenance checks; path and symbol discovery; local inventory graph and syntax inspection only. No host connection or OpenStack command.
- **Evidence to confirm:** every open confirmation in Section II; exact historical disposition; Phase 01 live acceptance; approved host-verification procedure or scoped Local-Lab SSH Transport Exception; approved external secret flow and mutation safety plan.
- **Validation:** no edits, credential creation, Ansible play, host connection, profile read, or OpenStack call.
- **Stop condition:** all gates are explicit. Any unresolved prerequisite blocks Chunk 1 and all live work.

#### Chunk 1: Credential, Policy, and Lifecycle Operations Contract

- **Goal:** Write the complete matrix and administrator/runtime responsibilities before authority exists.
- **Files to change:** proposed `docs/ai-ops-revised/runtime/identity-policy-operations-contract.md` and, only if exact historical paths are approved for review, `docs/ai-ops-revised/runtime/selective-reuse-manifest.md`.
- **Symbols to add/change:** no executable symbols; approved metadata schema, role/application-credential decision, reads, unavailable scopes, denial probes, disposable targets, emergency stop, profile format, secret flow, evidence, rotation, revocation, and rollback.
- **Implementation shape:** documentation only. Manifest selection permits content review, never credential copying or activation.
- **Validation:** Markdown whitespace/local-link checks; manifest consistency checks; historical/revised implementation diff remains empty.
- **Stop condition:** reviewers can decide exactly what authority may exist and how every success/failure is handled; no credential or automation changed.

#### Chunk 2: Profile Role Contracts and Fail-Closed Stub

- **Goal:** Add a syntax-valid role contract that cannot claim profile deployment success.
- **Files to change:** proposed `ansible/ai_ops_assistant/roles/ai_ops_assistant_identity_boundary/defaults/main.yml` and `ansible/ai_ops_assistant/roles/ai_ops_assistant_identity_boundary/tasks/main.yml`.
- **Symbols to add/change:** proposed revised constants, expected filenames, source classification, destination path, owner/group/modes, enable flag, path assertions, and `ERR_IDENTITY_PROFILE_NOT_IMPLEMENTED` failure.
- **Implementation shape:** assertions plus explicit temporary failure; no file copy, profile parse, authentication, identity creation, or OpenStack call.
- **Validation:** YAML/Ansible lint; minimal role syntax harness; path/secret/historical-name scans; exact diff review.
- **Stop condition:** role inputs and denied paths are inspectable and syntax-valid, while execution fails safely before observing secrets.

#### Chunk 3: Protected Profile Materialization Slice

- **Goal:** Replace the temporary failure with idempotent, minimum-disclosure profile placement only.
- **Files to change:** the proposed role `defaults/main.yml` and `tasks/main.yml` only.
- **Symbols to add/change:** source stat assertions, destination directory/file tasks, regular-file/symlink checks, exact owner/group/modes, `no_log`, and source/destination boundary assertions.
- **Implementation shape:** copy only approved filenames from one explicit external source; no backup, content output, checksum evidence, profile parsing, authentication, or OpenStack mutation.
- **Validation:** role lint/syntax; static `no_log` and path checks; no live run unless separately approved; diff review.
- **Stop condition:** role can converge profile files safely but has no caller and performs no authentication.

#### Chunk 4: Namespace-Safe Profile Deployment Entrypoint

- **Goal:** Wire only `assistant02` to the protected profile role without importing committed secrets.
- **Files to change:** proposed `ansible/ai_ops_assistant/playbook_deploy_identity_profile.yml` and, only if needed for non-secret constants, `ansible/ai_ops_assistant/inventories/local/group_vars/all/common_vars.yml`.
- **Symbols to add/change:** exact `ai_ops_assistant` targeting, revised role invocation, required external-source assertions, and explicit absence of ambient credential variables.
- **Implementation shape:** no shared/historical role, `hosts: all`, identity administration, generated profile source, or operator-reader configuration. Host verification must already be corrected under the Phase 01 gate.
- **Validation:** inventory graph; playbook syntax/lint; target, role, secret, and historical-identifier scans; approved limited check mode only after review.
- **Stop condition:** the profile can be deployed only to `assistant02`; no read or mutation validation exists yet.

#### Chunk 5: Authentication and Required-Read Slice

- **Goal:** Prove profile protection, token scope, and fixed MVP reads with outcome-only reporting.
- **Files to change:** proposed `ansible/ai_ops_assistant/playbook_validate_project_reader.yml` and `docs/ai-ops-revised/runtime/identity-policy-operations-contract.md` only if static contract refinement is required.
- **Symbols to add/change:** fixed `argv` read matrix, minimal environment, runtime-user execution, profile metadata assertions, normalized result classes, and redacted summary.
- **Implementation shape:** suppress token/resource/error payloads; accept empty project state separately from successful non-empty reads; never broaden profile or policy on failure.
- **Validation:** syntax/lint; static output-flow and fixed-command checks; approved limited live validation; redaction review.
- **Stop condition:** authentication and each required read have an evidence-backed normalized result; no mutation command exists.

#### Chunk 6: Safe Create-Denial Slice

- **Goal:** Prove one representative create operation is authorization-denied without relying on reader-owned cleanup.
- **Files to change:** proposed `ansible/ai_ops_assistant/playbook_validate_mutation_denial.yml` only.
- **Symbols to add/change:** approved unique run identifier, fixed disposable create `argv`, authorization classifier, immediate-stop assertion, and create postcondition contract.
- **Implementation shape:** run one create probe; `no_log` raw output; only conclusive authorization denial passes. Unexpected success stops and triggers external revocation/admin cleanup instructions.
- **Validation:** syntax/lint; static assertion that success cannot continue and no reader cleanup exists; approved live probe only with emergency procedure ready.
- **Stop condition:** create denial is conclusively proved or Phase 02 is blocked/revoked. Update/delete probes remain absent.

#### Chunk 7: Disposable Update/Delete Denial Slice

- **Goal:** Extend the accepted denial play to administrator-prepared disposable update and delete targets.
- **Files to change:** proposed mutation-denial playbook and proposed identity-policy operations contract.
- **Symbols to add/change:** exact target-name/ID validation, baseline/postcondition inputs, fixed update/delete `argv`, per-step immediate stop, normalized authorization outcomes, and administrator verification requirements.
- **Implementation shape:** never target ordinary project resources; use separate disposable targets; do not treat 404/invalid input as denial; do not clean up with project-reader authority.
- **Validation:** syntax/lint; fixed-command and target-prefix checks; mocked/static result-class test vectors where practical; approved live probes and out-of-band postcondition review.
- **Stop condition:** create/update/delete are each conclusively denied and disposable resource postconditions hold, or rollout is blocked with credential revoked.

#### Chunk 8: Lifecycle Rehearsal and Phase Reconciliation

- **Goal:** Prove idempotency, rotation/revocation/removal, compatibility, evidence redaction, and Phase 02 completion without starting Phase 03.
- **Files to change:** `docs/ai-ops-revised/runtime/identity-policy-operations-contract.md` and `docs/ai-ops-revised/implementation-plan/02-readonly-identity-and-policy-boundary.md`.
- **Symbols to add/change:** reviewed matrix results, accepted limitations, evidence references, lifecycle rehearsal status, unresolved operator-reader gate, and evidence-backed checkboxes.
- **Implementation shape:** rerun profile deployment for zero changes; rehearse replacement/revocation with administrator approval; scan retained evidence; verify historical runtime and existing lab entrypoints remain unchanged. Do not commit live evidence or secrets.
- **Validation:** Markdown/link checks; full revised diff and secret scan; prior runtime/protected inventory immutability; live revoked-credential failure check under `no_log` when approved.
- **Stop condition:** Phase 02 is evidence-backed complete or explicitly gated. Operator-reader remains unavailable and implementation stops before Phase 03.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline and post-edit-discipline if available.

Task:
Execute Chunk 0 only from docs/ai-ops-revised/implementation-plan/ads/02-00-readonly-identity-and-policy-boundary-ads.md.

Mode:
Discovery only. Do not edit files, create an identity or credential, read protected values, connect to assistant02, run Ansible, or call OpenStack. Confirm Phase 01 live acceptance and transport safety; resolve the project/role, application-credential, profile-format, secret-source, selective-reuse, read-matrix, disposable-target, authorization-signature, and evidence gates. Stop with exact evidence and blockers.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Execute Chunk 1 only.
Do not continue to Chunk 2.
Create only the identity and policy operations contract and make an evidence-backed selective-reuse manifest decision if approved. Run targeted Markdown, manifest, secret, and historical-runtime immutability checks; show the diff and stop. Do not create credentials, change Ansible, connect to a host, or call OpenStack.
```

For later chunks:

```text
Execute only the explicitly approved chunk and stop with a handoff. Run narrow lint, syntax, secret-flow, target-scope, and diff checks. Never perform a live profile deployment, authentication check, read matrix, or mutation-denial probe unless that exact chunk and command have operator approval. Any mutation success requires immediate stop, credential revocation, and administrator-owned verification/cleanup.
```

### X. Conclusion and Next Steps

Phase 02 introduces one narrowly bounded authority: a fresh, protected `aiops-assistant-project-reader` profile on the isolated revised runtime. Its safety is empirical, not inferred from a role name. Useful project reads must be classified explicitly, create/update/delete denials must be conclusive, broader visibility must remain unavailable, and any mutation success must revoke the credential rather than enter an automated cleanup path.

The next session must execute Chunk 0 only. Phase 01 live acceptance is supported by redacted external evidence, and the Local-Lab SSH Transport Exception applies only to `assistant02` in the `local` inventory. All remaining Phase 02 administrative, secret-source, reuse, matrix, denial-target, authorization-signature, and evidence gates still prohibit credential creation, profile deployment, authentication, or OpenStack probes.
