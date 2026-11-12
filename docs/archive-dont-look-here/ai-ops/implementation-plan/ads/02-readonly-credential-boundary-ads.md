## Architectural Design Specification: AI-OPS Read-Only Credential Boundary

**Source:** `docs/ai-ops/implementation-plan/02-readonly-credential-boundary.md`

**Goal:** Create or request a dedicated OpenStack diagnostic identity, configure a protected project-reader cloud profile on `assistant01`, prove project-level read checks pass, prove representative mutation checks fail, and document the observed credential boundary without installing admin or human credentials on the assistant runtime.

---

### I. Overview and Contract

Phase 02 turns the Phase 01 runtime from an unauthenticated diagnostic workstation into a least-privileged OpenStack observer. The default AI-OPS credential must be dedicated, project-scoped, read-only, protected on disk, empirically validated, and documented before Phase 03 diagnostic scripts are built.

Target state transition:

```text
selected diagnostic project
  -> dedicated AI-OPS identity exists
  -> project-reader role/application credential or equivalent is available
  -> protected named cloud profile exists on assistant01
  -> token and project-visible read checks pass
  -> representative create/update/delete checks fail
  -> actual policy behavior and rollback are documented
```

This phase must not create operator-reader diagnostics, SSH observer access, diagnostic scripts beyond credential validation commands, tool runner behavior, MCP exposure, policy-file changes, or remediation capability.

#### Contracts

**Credential Boundary Contract (Concrete from Phase 02 plan and PRD):**

- Use a dedicated OpenStack identity for AI-OPS diagnostics.
- Do not use a human admin credential, `admin-openrc`, member-role credential, service credential, database credential, RabbitMQ credential, or SSH private key as the assistant default.
- Default scope is project-scoped reader for project-visible servers, networks, subnets, ports, volumes, images, and security groups where policy allows.
- Application credentials are preferred when Keystone supports them.
- Operator-reader scope is deferred and must not become the default profile.
- OpenStack reader behavior must be tested because policy enforcement can vary.

**Runtime Credential Storage Contract (Concrete from Phase 01 runtime docs):**

- Credential material belongs only under `/opt/openstack-ai-ops/credentials/profiles/` on `assistant01`.
- Phase 01 evidence showed `/opt/openstack-ai-ops/credentials/profiles` exists and was empty before Phase 02.
- Phase 02 must tighten credential storage permissions before or while placing real profiles.
- Real profile files must not be committed to git.

**Named Cloud Profile Contract (Conceptual):**

A default profile named `aiops-project-reader` should be used consistently by validation commands and later diagnostic tooling.

Proposed runtime-local files:

```text
/opt/openstack-ai-ops/credentials/profiles/
  clouds.yaml        # profile metadata and non-secret auth fields when possible
  secure.yaml        # secret material if OpenStackSDK secure-file split is used
```

If a single `clouds.yaml` is used instead, it must still remain runtime-local, mode `0600`, and excluded from repository commits.

Proposed invocation pattern:

```bash
OS_CLIENT_CONFIG_FILE=/opt/openstack-ai-ops/credentials/profiles/clouds.yaml \
  /opt/openstack-ai-ops/.venv/bin/openstack --os-cloud aiops-project-reader <read-command>
```

**Credential Evidence Contract (Conceptual):**

A dated evidence note should record non-secret metadata and command outcomes, for example:

```text
docs/ai-ops/runtime/phase02-credential-boundary-evidence-YYYY-MM-DD.md
```

The evidence note must include:

- selected project name or ID if non-secret
- credential purpose, scope, role, owner, creation date, and rotation expectation
- profile name and runtime storage path
- token/read command pass/fail matrix
- mutation denial matrix
- operator-level command outcomes or deferrals
- rollback/revocation instructions

It must not include passwords, application credential secrets, tokens, private keys, unredacted `clouds.yaml`, or unredacted `secure.yaml` content.

**Function Signature Contract:** not applicable. Phase 02 is credential boundary configuration, validation, and documentation. No concrete application functions/classes are present in the repository for this phase. Any future helper scripts must be designed separately in Phase 03 or later.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops/implementation-plan/02-readonly-credential-boundary.md` defines the Phase 02 target outcome: `dedicated identity -> project-reader profile configured -> read checks pass -> mutation checks fail -> credential behavior documented`.
- `docs/ai-ops/implementation-plan/02-readonly-credential-boundary.md` includes six ordered steps: choose scope, create dedicated read-only identity, configure protected profile, validate read access, validate mutation denial, and document the actual credential matrix.
- `docs/ai-ops/implementation-plan/02-readonly-credential-boundary.md` excludes operator-reader diagnostics, SSH observer access, diagnostic scripts beyond credential validation commands, and policy changes unless current policy cannot support the MVP.
- `docs/ai-ops/implementation-plan/00-implementation-overview.md` places Phase 02 after assistant runtime foundation and before safe diagnostic scripts.
- `docs/ai-ops/implementation-plan/00-implementation-overview.md` states cross-phase principles: credentials are dedicated, least-privileged, empirically tested; no generic shell, SSH, OpenStack CLI passthrough, database, restart, file-write, or remediation tool is introduced.
- `docs/ai-ops/prd.md` contains FR-005 through FR-010 for dedicated OpenStack identity, project-scoped read-only default, restrictive credential storage, read validation, and mutation denial validation.
- `docs/ai-ops/prd.md` identifies separate logical profiles: project reader, operator reader, and SSH observer. Phase 02 should implement only the project-reader default.
- `docs/ai-ops/runtime/README.md` records `assistant01` as the Phase 01 runtime and documents `/opt/openstack-ai-ops/credentials/profiles/` as the credential profile area.
- `docs/ai-ops/runtime/phase01-runtime-evidence-2026-07-04.md` reports that `assistant01` reached Keystone `/v3/`, baseline OpenStack CLI/SDK tooling exists, `credentials/profiles` had entry count `0`, and OpenStack CLI failed only because auth was not configured.
- `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml` defines `ai_ops_runtime_root: /opt/openstack-ai-ops`, runtime user/group `assistant`, virtualenv path `/opt/openstack-ai-ops/.venv`, and current workspace directory list including `credentials/profiles`.
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/workspace.yml` currently asserts the Phase 01 credential profile directory is empty; this must be revised or gated before Phase 02 can place profiles.
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/evidence.yml` currently writes Phase 01 evidence stating no OpenStack credential files are created and `credentials/profiles/` must remain empty until Phase 02.
- `ansible/ai_ops_runtime/inventories/local/local.yml` targets only `assistant01` in the `assistant` group for the AI-OPS runtime playbook.
- `inventories/local/nodes.yml` contains `assistant01` with environment `assistant`, management IP `192.168.121.20`, provider IP `192.168.123.20`, and hostname `assistant01.local`.
- `.gitignore` excludes `*.log`, `log`, `.vagrant`, `.ansible`, and `.agents`; it does not currently define a repository-local credential profile ignore rule because real profile material is intended to live on the runtime, not in the repo.
- `ansible/deploy_openstack/roles/common/tasks/create_user_and_roles.yml` shows the existing deployment uses OpenStack CLI commands for service user creation and role assignment, but those tasks are service-oriented and use admin context. Phase 02 must not reuse service credentials as the assistant default.

#### Assumptions

- A human admin or existing secure admin workflow can create the initial AI-OPS identity and role assignment outside the assistant runtime.
- The selected diagnostic project and role name may vary by OpenStack policy/version; Chunk 0 must confirm the actual project, domain, role, and application credential support.
- The default OpenStack CLI binary remains `/opt/openstack-ai-ops/.venv/bin/openstack` from Phase 01 evidence.
- The profile name `aiops-project-reader` is proposed; it can be changed during Chunk 0 if the operator has a stronger naming convention.
- A redacted example profile may be committed for documentation, but real `clouds.yaml`, `secure.yaml`, passwords, application credential secrets, and tokens must remain runtime-local only.
- Some read commands may fail because of OpenStack policy rather than misconfiguration. Those outcomes must be documented instead of hidden.
- If any mutation command succeeds, Phase 02 is blocked until the credential is revoked or policy/role assignment is corrected.

#### Open confirmations for Chunk 0

- Which OpenStack project should the default project-reader inspect first?
- Which domain should contain the AI-OPS user?
- What exact role name represents least-privileged project read access in this lab (`reader` or another role)?
- Does Keystone support application credentials in the deployed lab?
- Should profile files use `clouds.yaml` only, or `clouds.yaml` plus `secure.yaml`?
- Should Phase 02 be implemented as operator-run runbooks first, Ansible-managed profile deployment, or a hybrid where Ansible only validates/protects paths and evidence?

### III. Required Technical Dependencies and Imports

#### Existing runtime dependencies

- `assistant01` runtime from Phase 01.
- `/opt/openstack-ai-ops/.venv/bin/openstack` from Phase 01 baseline tooling.
- `/opt/openstack-ai-ops/.venv` with `openstackclient` and `openstacksdk` installed.
- Keystone reachability from `assistant01` to `controller01:5000` / `192.168.121.5:5000`.
- `/opt/openstack-ai-ops/credentials/profiles/` runtime directory.

#### OpenStack dependencies

- Human-admin ability to create or request a dedicated AI-OPS user.
- Least-privileged project role assignment for the selected project.
- Optional Keystone application credential support.
- Representative project resources for read validation, or explicit documentation that a resource class is absent.

#### Repository documentation dependencies

- `docs/ai-ops/implementation-plan/02-readonly-credential-boundary.md`
- `docs/ai-ops/runtime/README.md`
- Proposed: `docs/ai-ops/runtime/credential-boundary-runbook.md`
- Proposed: `docs/ai-ops/runtime/credential-profile-example-redacted.yaml`
- Proposed: `docs/ai-ops/runtime/phase02-credential-boundary-evidence-YYYY-MM-DD.md`

#### Optional Ansible dependencies, if automation is selected after Chunk 0

- `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml`
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/workspace.yml`
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/evidence.yml`
- Proposed: `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/credentials.yml`
- Proposed: `ansible/ai_ops_runtime/roles/assistant_runtime/templates/clouds.yaml.j2`
- Proposed: `ansible/ai_ops_runtime/roles/assistant_runtime/templates/secure.yaml.j2` only if using a split secret file

Any Ansible task that handles secret material must use `no_log: true`, must not write secrets to repository paths, and must be invoked only with operator-supplied runtime secrets or local files outside git.

### IV. Step-by-Step Procedure / Execution Flow

1. Confirm Phase 02 preconditions:
   - `assistant01` exists and Phase 01 evidence is current enough.
   - Keystone is reachable from `assistant01`.
   - `credentials/profiles/` exists and is ready to transition from empty Phase 01 state to protected Phase 02 state.
2. Choose initial credential scope:
   - Select the OpenStack project for MVP diagnostics.
   - Record why the project is representative.
   - Define expected read commands and expected deferred/operator-only commands.
3. Create or request the dedicated identity:
   - Human admin creates an AI-OPS user or approved equivalent.
   - Assign only the least-privileged project reader role for the selected project.
   - Prefer creating an application credential for the dedicated user if supported.
   - Record non-secret metadata: purpose, scope, owner, role, creation date, rotation/revocation expectation.
4. Protect runtime credential storage:
   - Set `/opt/openstack-ai-ops/credentials` and/or `credentials/profiles` ownership to the runtime user/group or root plus runtime-readable as selected.
   - Set directory permissions to a restrictive mode such as `0700` for `credentials/profiles`.
   - Set profile file permissions to `0600`.
5. Configure the named project-reader cloud profile:
   - Place real `clouds.yaml` and optional `secure.yaml` only on `assistant01` under `/opt/openstack-ai-ops/credentials/profiles/`.
   - Use profile name `aiops-project-reader` unless Chunk 0 selects another name.
   - Do not commit the real profile.
6. Validate authentication:
   - Run token issuance using `--os-cloud aiops-project-reader` and the runtime profile path.
   - Record success/failure without storing token values.
7. Validate project-level reads:
   - Run project-visible server, network, subnet, port, volume, image, and security-group list/show commands where services are installed and policy allows.
   - Record pass, expected-empty, policy-denied, service-unavailable, or configuration-error outcomes.
8. Validate mutation denial:
   - Attempt representative create operations with unique harmless test names.
   - Attempt representative update/delete operations only when safe and explicitly chosen.
   - Treat any successful mutation as a blocking safety failure.
   - If a mutation unexpectedly succeeds, stop, revoke or remove the credential, clean up any created resource through an admin/operator path, and do not proceed to Phase 03.
9. Document actual behavior:
   - Add a dated evidence matrix under `docs/ai-ops/runtime/` with redacted/non-secret outcomes.
   - Update `docs/ai-ops/runtime/README.md` to state that Phase 02 profiles are now expected to exist and be protected.
   - Update Phase 02 checkboxes only where evidence exists.
10. Stop before Phase 03 diagnostic scripts.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| ----- | ------------ | ------------------- | ----------------------- |
| Scope selection | No diagnostic project is selected | Stop before profile configuration | `ERR_AI_OPS_PROJECT_SCOPE_UNSET` (proposed); Phase 02 Step 1 remains unchecked |
| Identity creation | Human/admin credential is copied to `assistant01` | Remove credential, rotate if exposed, and restart with dedicated identity | `ERR_ADMIN_CREDENTIAL_ON_ASSISTANT` (proposed); credential boundary blocked |
| Identity creation | Dedicated user receives member/admin/service role instead of reader | Revoke incorrect role assignment before validation | `ERR_AI_OPS_ROLE_TOO_BROAD` (proposed); no default profile activation |
| Application credential | Keystone does not support application credentials or policy denies creation | Fall back to documented least-privileged user credential only if approved | Evidence records fallback and rotation expectation |
| Profile storage | Real `clouds.yaml`/`secure.yaml` is created in the repository | Remove from git/worktree, rotate exposed secret, add prevention note | `ERR_CREDENTIAL_MATERIAL_IN_REPO` (proposed); do not continue |
| Profile storage | Profile directory/file mode is too permissive | Tighten permissions before auth validation | `ERR_PROFILE_PERMISSIONS_WEAK` (proposed); validation blocked |
| Profile parsing | OpenStack CLI cannot locate profile | Verify `OS_CLIENT_CONFIG_FILE`, file syntax, profile name, and permissions | Configuration error recorded; read checks not attempted |
| Token issuance | Token request fails | Distinguish bad secret, bad auth URL, bad project scope, and Keystone reachability | Evidence records exact non-secret error class |
| Read validation | Expected read command fails | Classify as policy limitation, service unavailable, empty service, or config error | Matrix records actual behavior; future tools must avoid unsupported reads |
| Mutation validation | Mutation command succeeds | Stop immediately, revoke/repair credential, clean up resource through admin path | `ERR_MUTATION_ALLOWED` (proposed); Phase 02 DoD fails |
| Mutation validation | Mutation command fails for bad input rather than authorization | Redesign the validation command so denial proves policy boundary | Matrix marks prior attempt inconclusive, not pass |
| Documentation | Checklist is checked without evidence | Revert checkbox or add evidence note | Prevents false Phase 02 completion |
| Secret handling | Evidence includes token, secret, password, or private key | Remove secret, rotate if exposed, rerun secret scan | `ERR_SECRET_IN_EVIDENCE` (proposed) |

### VI. Security, Integrity, Idempotency, and Cleanup

#### Security

- Keep admin credentials off `assistant01`.
- Keep real profile material only under `/opt/openstack-ai-ops/credentials/profiles/` on the runtime.
- Use restrictive credential directory and file modes, preferably directory `0700` and files `0600`.
- Use dedicated project-reader identity by default; never make operator-reader the default profile.
- Do not expose generic OpenStack CLI passthrough as an AI tool in this phase. Operators may run validation commands manually.
- Do not log tokens, passwords, application credential secrets, private keys, or unredacted profile content.
- Use `no_log: true` for any Ansible path that touches secret values.

#### Integrity

- Validation must prove useful reads and denied mutations empirically, not by role-name assumption.
- Record command class and outcome, but not sensitive values.
- Mark policy-denied reads separately from configuration errors so Phase 03 tools do not depend on unavailable visibility.
- Treat successful mutation as a release-blocking defect.

#### Idempotency

- Re-running directory permission hardening should be safe.
- Re-running read validation should not modify OpenStack state.
- Mutation validation must use unique harmless names and should leave no resources behind. If a resource is created unexpectedly, cleanup must happen through an explicit admin/operator rollback path.
- Documentation updates should be dated rather than overwriting evidence needed for audit history.

#### Cleanup and rollback

- Revoke the application credential if used.
- Disable or delete the dedicated AI-OPS user if the whole boundary is rolled back.
- Remove runtime-local profile files from `/opt/openstack-ai-ops/credentials/profiles/`.
- Confirm `openstack --os-cloud aiops-project-reader token issue` no longer succeeds after revocation.
- Remove or supersede stale evidence notes only with a new dated note explaining rollback; do not erase history without cause.

### VII. Validation Strategy

Validation is chunk-aware. Do not mark Phase 02 complete until live runtime evidence exists.

#### Repository/documentation validation

- Review changed docs:

  ```bash
  rtk git diff -- docs/ai-ops/implementation-plan/ads/02-readonly-credential-boundary-ads.md docs/ai-ops/runtime docs/ai-ops/implementation-plan/02-readonly-credential-boundary.md
  ```

- Check whitespace:

  ```bash
  rtk git diff --check
  ```

- Scan AI-OPS docs and automation for high-confidence secret material:

  ```bash
  rtk grep -RniE 'BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY|OS_PASSWORD=.+|application_credential_secret:.+[^<]|auth_token|X-Subject-Token|-----BEGIN PRIVATE KEY-----' docs/ai-ops ansible/ai_ops_runtime 2>/dev/null || true
  ```

#### YAML/Ansible validation, if Ansible credential-boundary support is added

- Parse YAML files touched by the chunk:

  ```bash
  rtk yq '.' ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml >/dev/null
  rtk yq '.' ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml >/dev/null
  ```

- Run syntax check from a `/tmp` Python virtualenv containing the repo requirements, following the Phase 01 workflow:

  ```bash
  rtk bash -lc 'python3 -m venv /tmp/openstack-lab-ai-ops-ansible-venv && . /tmp/openstack-lab-ai-ops-ansible-venv/bin/activate && python -m pip install -r requirements.txt >/dev/null && ROOT_DIR=$PWD ansible-playbook -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml --syntax-check'
  ```

#### Runtime validation on `assistant01`

Use the runtime-local profile path and virtualenv OpenStack CLI:

```bash
export OS_CLIENT_CONFIG_FILE=/opt/openstack-ai-ops/credentials/profiles/clouds.yaml
export OS_CLOUD=aiops-project-reader
/opt/openstack-ai-ops/.venv/bin/openstack token issue -f json
/opt/openstack-ai-ops/.venv/bin/openstack server list -f json
/opt/openstack-ai-ops/.venv/bin/openstack network list -f json
/opt/openstack-ai-ops/.venv/bin/openstack subnet list -f json
/opt/openstack-ai-ops/.venv/bin/openstack port list -f json
/opt/openstack-ai-ops/.venv/bin/openstack volume list -f json
/opt/openstack-ai-ops/.venv/bin/openstack image list -f json
/opt/openstack-ai-ops/.venv/bin/openstack security group list -f json
```

Representative mutation-denial checks must be selected during implementation so failure indicates authorization/policy denial rather than malformed command input. Record exact non-secret failure class such as `Forbidden`, `Not authorized`, or policy denial.

#### Final review

- Confirm profile files are runtime-local and not in git:

  ```bash
  rtk git status --short
  rtk git diff --name-only
  ```

- Confirm changed checkboxes have matching evidence notes.
- Confirm no Phase 03 diagnostic script, tool runner, generic OpenStack passthrough, SSH observer access, or MCP behavior was introduced.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass.

#### Chunk 0: Discovery and Integration Confirmation

- **Goal:** Confirm actual project, role, credential mechanism, profile naming, and whether implementation should be runbook-only or include Ansible support.
- **Files to read:**
  - `docs/ai-ops/implementation-plan/02-readonly-credential-boundary.md`
  - `docs/ai-ops/runtime/README.md`
  - `docs/ai-ops/runtime/phase01-runtime-evidence-2026-07-04.md`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/workspace.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/evidence.yml`
  - `.gitignore`
- **Commands:**
  - `rtk git status --short --branch`
  - `rtk grep -Rni "aiops-project-reader\|clouds.yaml\|secure.yaml\|credentials/profiles\|application credential\|reader" docs/ai-ops ansible/ai_ops_runtime 2>/dev/null`
  - Runtime/operator check: verify Keystone/application credential support and available role names using an admin/operator context outside `assistant01`.
- **Evidence to confirm:**
  - Selected project and role name.
  - Whether application credentials are supported.
  - Current Phase 01 empty-directory assertions that must change or be gated.
  - Desired profile file shape and profile name.
  - No existing real credential material in the repo.
- **Stop condition:** Report decisions and evidence. Do not edit files.

#### Chunk 1: Documentation Contracts and Redacted Examples

- **Goal:** Add safe operator-facing documentation for credential scope, profile naming, redacted profile shape, validation matrix, and rollback without adding real secrets.
- **Files to change:**
  - Proposed: `docs/ai-ops/runtime/credential-boundary-runbook.md`
  - Proposed: `docs/ai-ops/runtime/credential-profile-example-redacted.yaml`
- **Symbols to add/change:** Documentation-only; no code symbols.
- **Implementation shape:** Document selected profile name, runtime-local profile path, required file modes, non-secret identity metadata fields, read validation command list, mutation-denial command selection rules, and rollback. Redacted example must use placeholders such as `<redacted>` and must not be executable with real credentials.
- **Validation:**
  - `rtk git diff -- docs/ai-ops/runtime/credential-boundary-runbook.md docs/ai-ops/runtime/credential-profile-example-redacted.yaml`
  - `rtk git diff --check`
  - `rtk grep -RniE 'BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY|OS_PASSWORD=.+|application_credential_secret:.+[^<]|auth_token|X-Subject-Token' docs/ai-ops/runtime 2>/dev/null || true`
- **Stop condition:** Docs explain how to configure and validate Phase 02 without real secrets in the repository.

#### Chunk 2: Protected Credential Directory Transition

- **Goal:** Update runtime automation/runbook semantics so `credentials/profiles/` is no longer required to be empty forever, but is required to be protected before profiles exist.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/workspace.yml`
- **Symbols to add/change:**
  - Proposed variable: `ai_ops_runtime_credential_profiles_mode: "0700"`
  - Proposed variable: `ai_ops_runtime_expect_empty_credentials: true` or phase-aware equivalent
- **Implementation shape:** Add a specific credential profile directory mode and gate the Phase 01 empty-directory assertion behind a variable that defaults to safe Phase 01 behavior. Do not create credential files in this chunk.
- **Validation:**
  - `rtk yq '.' ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml >/dev/null`
  - Ansible syntax check for `ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml` from the `/tmp` venv workflow.
  - `rtk git diff -- ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml ansible/ai_ops_runtime/roles/assistant_runtime/tasks/workspace.yml`
- **Stop condition:** Credential directory can be hardened and Phase 01 empty assertion remains the default unless explicitly disabled for Phase 02.

#### Chunk 3: Profile Placement Contract Stub

- **Goal:** Add an optional, compile-safe Ansible task path for profile placement that is disabled by default and cannot accidentally deploy secrets.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/main.yml`
  - Proposed: `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/credentials.yml`
- **Symbols to add/change:**
  - Proposed variable: `ai_ops_runtime_manage_openstack_profile: false`
  - Proposed variable: `ai_ops_runtime_openstack_profile_name: aiops-project-reader`
  - Proposed variable: `ai_ops_runtime_openstack_profile_source: ""`
- **Implementation shape:** Include `credentials.yml` only when `ai_ops_runtime_manage_openstack_profile | bool` is true. The initial task file should fail with a clear message if enabled without an explicit runtime-local or operator-supplied source path. It must not contain a template with secret values yet.
- **Validation:**
  - YAML parse for touched files.
  - Ansible syntax check for the playbook.
  - Secret scan of `ansible/ai_ops_runtime`.
  - `rtk grep -Rni "ai_ops_runtime_manage_openstack_profile" ansible/ai_ops_runtime`
- **Stop condition:** Playbook remains safe by default; enabling profile management without a source produces a clear failure rather than silently succeeding.

#### Chunk 4: Runtime Profile Placement and Permission Logic

- **Goal:** Implement the selected safe profile placement method after Chunk 0 decisions are accepted.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/credentials.yml`
  - Optional: `ansible/ai_ops_runtime/roles/assistant_runtime/templates/clouds.yaml.j2`
  - Optional: `ansible/ai_ops_runtime/roles/assistant_runtime/templates/secure.yaml.j2`
- **Symbols to add/change:**
  - Any additional variables must be secret-safe and documented as operator-supplied.
- **Implementation shape:** Either copy operator-provided profile files from outside the repository, or render templates from secret variables with `no_log: true`. Set profile file mode `0600` and owner/group according to runtime access decision. Do not commit real profile values.
- **Validation:**
  - Ansible syntax check.
  - Runtime dry-run/check-mode if safe.
  - `rtk git diff -- ansible/ai_ops_runtime/roles/assistant_runtime`
  - Secret scan of changed files.
- **Stop condition:** Protected runtime-local profile files can be created on `assistant01` only when explicit operator inputs are supplied.

#### Chunk 5: Authentication and Read Validation Evidence

- **Goal:** Run token and project-visible read checks with the default project-reader profile and record non-secret evidence.
- **Files to change:**
  - Proposed: `docs/ai-ops/runtime/phase02-credential-boundary-evidence-YYYY-MM-DD.md`
- **Symbols to add/change:** Documentation-only; no code symbols.
- **Implementation shape:** Execute validation commands on `assistant01` with `OS_CLIENT_CONFIG_FILE` and `--os-cloud`. Record command categories, success/failure class, and redacted excerpts. Do not store token values or full JSON if it includes sensitive fields.
- **Validation:**
  - Runtime command outcomes for token, server, network, subnet, port, volume, image, and security-group reads.
  - `rtk git diff -- docs/ai-ops/runtime/phase02-credential-boundary-evidence-YYYY-MM-DD.md`
  - High-confidence secret scan of the evidence note.
- **Stop condition:** Evidence distinguishes successful reads from policy limitations and configuration failures.

#### Chunk 6: Mutation-Denial Evidence

- **Goal:** Prove representative mutation attempts fail for authorization/policy reasons and treat any success as blocking.
- **Files to change:**
  - `docs/ai-ops/runtime/phase02-credential-boundary-evidence-YYYY-MM-DD.md`
- **Symbols to add/change:** Documentation-only; mutation matrix rows.
- **Implementation shape:** Add selected create/update/delete checks using harmless unique names. Record exact non-secret error class. If a command succeeds, stop implementation, revoke or repair the credential, and document the failure instead of marking success.
- **Validation:**
  - Runtime mutation-denial commands selected in Chunk 0/Chunk 1.
  - Admin/operator verification that no test resources remain if a mutation unexpectedly succeeded.
  - Secret scan of evidence note.
- **Stop condition:** Mutation matrix shows denial evidence or a blocking safety failure is reported.

#### Chunk 7: Phase 02 Checklist and Runtime README Update

- **Goal:** Update Phase 02 plan status and runtime README only after credential evidence exists.
- **Files to change:**
  - `docs/ai-ops/implementation-plan/02-readonly-credential-boundary.md`
  - `docs/ai-ops/runtime/README.md`
- **Symbols to add/change:** Documentation/checklist only.
- **Implementation shape:** Check only completed evidence-backed tasks. Update `credentials/profiles/` rule from “empty until Phase 02” to “contains protected project-reader profile after Phase 02” with link to evidence and rollback. Keep operator-reader as deferred.
- **Validation:**
  - `rtk git diff -- docs/ai-ops/implementation-plan/02-readonly-credential-boundary.md docs/ai-ops/runtime/README.md`
  - `rtk git diff --check`
  - Confirm every checked item links to evidence.
- **Stop condition:** Phase 02 status accurately reflects observed runtime credential behavior and does not start Phase 03.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Implement Phase 02 AI-OPS Read-Only Credential Boundary from docs/ai-ops/implementation-plan/ads/02-readonly-credential-boundary-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm repository/runtime evidence, selected project, role name, application credential support, profile naming, and automation-vs-runbook decision. Stop after reporting evidence and open questions.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Execute Chunk 1 only.
Do not continue to Chunk 2.
After editing, run targeted validation and show git diff.
```

For later runtime credential placement:

```text
Use the chunked-implementation skill.
Execute the next approved chunk only.
Do not continue to the following chunk.
Never place real OpenStack secrets in repository files or chat output.
After editing or runtime validation, run targeted checks, review git diff, and stop.
```

### X. Conclusion and Next Steps

Phase 02 should be implemented as a safety boundary, not as a convenience credential shortcut. The repository already has a bootstrapped `assistant01` runtime, OpenStack CLI/SDK tooling, Keystone reachability, and an empty credential profile area from Phase 01. The next implementation step is Chunk 0: confirm the actual project/role/application-credential details and choose whether the first Phase 02 slice is runbook-only or includes disabled-by-default Ansible support. Only after read and mutation evidence exists should the Phase 02 checklist or runtime README be marked complete.
