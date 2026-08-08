# MVP Live Validation Runbook

## Status and authority

This is a procedural runbook for progressing the Phase 05 MVP live-validation attempt after the Ansible privilege-escalation correction.

It does **not** authorize deployment, runner execution, audit inspection, AI-provider interaction, credential/profile rollback, or destructive operations. The authoritative boundaries remain:

- `docs/ai-ops-revised/implementation-plan/ads/05-01-mvp-live-validation-ai-behavior-and-rollback-ads.md`
- `docs/ai-ops-revised/runtime/mvp-live-validation-and-rollback-operations-contract.md`
- `docs/ai-ops-revised/runtime/tool-runner-safety-gateway-steps-05-to-07-operations-contract.md`

Missing authorization, prerequisite evidence, secure identifier transport, attestation, or evidence ownership is a blocker. Do not bypass a gate or retry a failed live attempt automatically.

## Scope

The procedure is limited to:

- repository: `openstack-lab`;
- inventory: `ansible/ai_ops_assistant/inventories/local/local.yml`;
- target: `assistant02` only;
- Ansible limit: `assistant02` exactly;
- revised runner root: `/opt/openstack-ai-ops-assistant`;
- fixed runner: `/opt/openstack-ai-ops-assistant/scripts/tool_runner/aiops_tool_runner.py`;
- approved tools: `project_resource_summary`, `server_basic_info`, and `server_network_info`;
- fixed audit path: `/opt/openstack-ai-ops-assistant/audit/tool-runner.jsonl`.

Generic shell, raw OpenStack CLI, direct diagnostic scripts, alternate audit paths, prior-runtime fallbacks, mutation, remediation, credential disclosure, and caller-selected execution paths are out of scope.

## Procedure overview

Complete the following gates in order:

1. separately review the privilege-escalation correction;
2. reconfirm operational authorization and prerequisites;
3. create a new non-secret run ID;
4. establish administrator-owned pre/post attestation handling;
5. confirm protected outcome-only evidence handling;
6. restart deployment and validation in the required sequence; and
7. review normalized results, post-state, and stop conditions.

Do not begin the live runner invocation until Steps 1–5 are complete and explicitly approved.

## 1. Separately review the privilege-escalation correction

The correction adds play-scoped pipelining to:

```text
ansible/ai_ops_assistant/playbook_validate_mvp_runner.yml
```

```yaml
vars:
  ansible_pipelining: true
```

The focused static test also checks that this setting remains present:

```text
ansible/ai_ops_assistant/tests/mvp_runner/test_validate_mvp_runner_stub.sh
```

A separate reviewer must confirm that:

- pipelining matches existing repository precedent for unprivileged `become_user` tasks;
- the change avoids the incompatible temporary-file ACL path;
- world-readable temporary files are not enabled;
- `no_log`, ownership, modes, runner paths, and audit handling are unchanged;
- the target remains limited to `assistant02`; and
- no unrelated files or staged changes were modified.

Local evidence already completed for this correction includes YAML parsing, Ansible syntax checking, Ansible lint, shell syntax, the focused static test, and whitespace checks. The separate review remains an operational prerequisite.

## 2. Reconfirm authorization and prerequisites

Authorization categories are independent. Obtain explicit confirmation for each operation that will occur:

- deployment of the dedicated revised runner to `assistant02`;
- execution of exactly the three approved read-only runner calls;
- protected inspection of the fixed audit path;
- external outcome-only evidence recording;
- any later manual AI evaluation; and
- any rollback or authority-removal action.

Confirm the following before deployment:

- the target environment and inventory are correct;
- the operator has approved access to `assistant02`;
- the command will use `--limit assistant02`;
- foundation, project-reader profile, diagnostic toolbox, and Python prerequisites are accepted;
- a representative project-visible server is expected to exist;
- the administrator comparator owner is identified;
- the protected evidence owner and retention policy are identified;
- prior-runtime isolation is confirmed; and
- rollback authority is identified.

Approval of deployment does not automatically approve runner execution, AI interaction, or credential/profile rollback.

## 3. Create a new non-secret run ID

The prior failed attempt consumed its run ID. Generate a new value that matches:

```text
^[a-z0-9][a-z0-9-]{0,47}$
```

Example format only:

```text
phase05-retry-20260618-01
```

The run ID must not contain credentials, server IDs, project IDs, addresses, or profile contents. Do not commit it to Git, place it in inventory/defaults, or reuse the failed run ID. Record the new run ID only in the approved protected operational record and the required non-secret Ansible gate input.

## 4. Establish administrator-owned attestations

### Pre-attestation

Before deployment or runner execution, the administrator-owned comparator must establish a baseline and return only normalized status:

```text
valid: true
```

Raw resource identities, comparator commands, and state details remain outside Ansible and outside retained evidence. The pre-attestation must cover the target, prior-runtime isolation, and the state needed to determine whether the diagnostic attempt changed anything.

### Post-attestation

After the runner calls, the administrator must compare the resulting state with the same external baseline and return:

```text
valid: true
unchanged: true
```

The current validation playbook asserts the post-attestation values but does not create them. Before live execution, confirm the approved orchestration method for producing the post-attestation after the runner calls. Do not pass a guessed or pre-filled `true` value merely to satisfy the gate.

If the post-attestation interface is not concrete, stop and resolve that implementation/operational gap before live execution. A post-attestation failure is not a reason to retry the runner.

## 5. Confirm protected evidence handling

Use an administrator-approved external location. The contract proposes the following convention, subject to confirmation:

```text
/var/lib/openstack-ai-ops-evidence/phase05/<run-id>.md
```

If approved:

- directory mode must be `0700`;
- record mode must be `0600`;
- ownership must belong to the approved evidence owner; and
- retention and deletion must follow the owner’s policy.

The outcome-only record may contain source revision, UTC timestamp, non-secret run ID, fixed host/group/runtime labels, tool names, normalized statuses, correlation IDs, durations, exit-code agreement, truncation flags, audit-pair status, path-isolation status, attestation outcomes, known limitations, and rollback outcomes.

It must not contain server or project identifiers, addresses, topology payloads, command arguments, raw envelopes, stdout, stderr, raw audit lines, profile contents, credentials, tokens, comparator data, or raw AI prompts/responses.

## 6. Restart deployment and validation

Use the confirmed Python environment:

```bash
source /home/meriz/Documents/PyEnv/myEnv/bin/activate
export ROOT_DIR="$PWD"
```

All commands below are templates. Execute them only after the required authorization is recorded. Replace `<new-run-id>` only with the newly approved non-secret run ID.

### 6.1 Deployment check mode

```bash
rtk ansible-playbook \
  -i ansible/ai_ops_assistant/inventories/local/local.yml \
  ansible/ai_ops_assistant/playbook_deploy_tool_runner.yml \
  --check --diff \
  --limit assistant02 \
  -e root_dir="$ROOT_DIR" \
  -e target_env=local
```

Review the proposed changes. They must be limited to the revised runner directory and its fixed runner, registry, and bounded audit-inspector files. No credential, profile, prior-runtime, service, or alternate-path change is allowed.

Stop if check mode proposes unexpected changes or does not prove the exact target scope.

### 6.2 Apply the deployment

```bash
rtk ansible-playbook \
  -i ansible/ai_ops_assistant/inventories/local/local.yml \
  ansible/ai_ops_assistant/playbook_deploy_tool_runner.yml \
  --limit assistant02 \
  -e root_dir="$ROOT_DIR" \
  -e target_env=local
```

Confirm the deployed files have the expected ownership, modes, regular-file status, and revised-path isolation. Do not inspect or print protected profile contents.

### 6.3 Verify deployment idempotency

Run the same deployment a second time:

```bash
rtk ansible-playbook \
  -i ansible/ai_ops_assistant/inventories/local/local.yml \
  ansible/ai_ops_assistant/playbook_deploy_tool_runner.yml \
  --limit assistant02 \
  -e root_dir="$ROOT_DIR" \
  -e target_env=local
```

Expected result is `changed=0`. Any unexpected second change is a deployment blocker.

### 6.4 Execute the bounded validation

The validation playbook is fail-closed. Its activation inputs must represent real approved gates, not placeholders:

```text
ai_ops_assistant_mvp_validation_enabled=true
ai_ops_assistant_mvp_validation_implementation_ready=true
ai_ops_assistant_mvp_secure_identifier_transport=administrator-owned-protected-memory
ai_ops_assistant_mvp_comparator_interface=administrator-owned-boolean-only
ai_ops_assistant_mvp_pre_attestation_interface=administrator-owned-boolean-only
ai_ops_assistant_mvp_post_attestation_interface=administrator-owned-boolean-only
ai_ops_assistant_mvp_external_evidence_location=administrator-approved-protected-location
ai_ops_assistant_mvp_run_id=<new-run-id>
ai_ops_assistant_mvp_pre_attestation_valid=true
ai_ops_assistant_mvp_prior_runtime_isolation_confirmed=true
```

The post-attestation values must be supplied through the approved post-run comparator procedure. Do not fabricate them before execution.

Once that interface is confirmed, the bounded invocation is:

```bash
rtk ansible-playbook \
  -i ansible/ai_ops_assistant/inventories/local/local.yml \
  ansible/ai_ops_assistant/playbook_validate_mvp_runner.yml \
  --limit assistant02 \
  -e root_dir="$ROOT_DIR" \
  -e target_env=local \
  -e ai_ops_assistant_mvp_validation_enabled=true \
  -e ai_ops_assistant_mvp_validation_implementation_ready=true \
  -e ai_ops_assistant_mvp_secure_identifier_transport=administrator-owned-protected-memory \
  -e ai_ops_assistant_mvp_comparator_interface=administrator-owned-boolean-only \
  -e ai_ops_assistant_mvp_pre_attestation_interface=administrator-owned-boolean-only \
  -e ai_ops_assistant_mvp_post_attestation_interface=administrator-owned-boolean-only \
  -e ai_ops_assistant_mvp_external_evidence_location=administrator-approved-protected-location \
  -e ai_ops_assistant_mvp_run_id=<new-run-id> \
  -e ai_ops_assistant_mvp_pre_attestation_valid=true \
  -e ai_ops_assistant_mvp_prior_runtime_isolation_confirmed=true
```

The playbook must remain the only execution path. It should:

1. verify the exact `assistant02` scope;
2. verify activation gates and pre-attestation;
3. inspect runner, registry, audit, and profile metadata without exposing content;
4. run `project_resource_summary`;
5. select a representative server identifier in protected task state;
6. run `server_basic_info` and `server_network_info` with the exact same identifier;
7. inspect exactly three matching audit events through the fixed bounded helper;
8. verify result/audit agreement and exit-code semantics;
9. verify post-run metadata and administrator post-attestation; and
10. produce only a normalized outcome report.

Do not add direct scripts, raw OpenStack commands, alternate audit paths, retries, or identifier-bearing debug output.

## 7. Review the result and stop or continue

After the validation attempt, verify only approved normalized outcomes:

- all three requests used the fixed runner;
- result envelopes were schema version `1.0`;
- process exit codes agreed with result statuses;
- exactly three matching audit events were found;
- result and audit fields agreed;
- audit and runner paths remained protected;
- the same server identifier was used for both server requests without exposure;
- pre-attestation was valid;
- post-attestation was valid and reported `unchanged: true`; and
- no prior-runtime process, file, profile, audit path, or service was touched.

Write only the normalized outcome record to the approved external evidence location. Discard raw sensitive material according to the evidence policy.

If any runner call, audit check, result contract, identifier transport, path-isolation check, or attestation fails:

- stop immediately;
- do not retry under the same run ID;
- do not claim acceptance;
- preserve only the approved normalized failure evidence;
- have the administrator investigate; and
- obtain a new run ID and fresh authorization before any later attempt.

Manual AI evaluation and rollback rehearsal are separate activities. They require their own authorization, data-handling approval, and evidence review.

## 8. Authorized rollback-and-recovery rehearsal

This procedure is a controlled destructive rehearsal. It is not authorized by this runbook. Start only after the identity administrator explicitly approves the exact revised credential and profile scope, the target is exactly `assistant02`, the recovery owner/procedure is available, and an administrator-owned baseline attestation method is confirmed. Do not include credential secrets, profile content, resource identifiers, addresses, raw output, or audit data in retained evidence.

### 8.1 Prepare and set stop conditions

1. Assign the identity administrator, Ansible operator, recovery owner, evidence owner, and pre/post-attestation owner.
2. Create a new non-secret rollback run ID and an outcome-only protected evidence record. Confirm the evidence directory is mode `0700`, the record is mode `0600`, and retention, access, and deletion are approved.
3. Record only the approved non-secret credential label, profile class `aiops-assistant-project-reader`, source revision, target label, and recovery-procedure reference.
4. Confirm the recovery procedure can restore the credential, profile, and dedicated runner entrypoint from the recorded revision before revocation occurs.
5. Obtain the normalized pre-attestation `valid` result.

Stop without changing authority if any authorization, recovery procedure, protected evidence handling, or pre-attestation is missing or invalid.

### 8.2 Remove revised authority

1. Stop new revised runner use and disable or remove only its dedicated entrypoint on `assistant02` through the approved deployment/rollback boundary.
2. Have the identity administrator revoke only the approved revised project-reader credential.
3. Remove only the protected revised profile material owned by the approved identity procedure.
4. Do not touch the prior runtime, its profiles, credentials, source, services, audit data, or state.

### 8.3 Verify fail-closed behavior and baseline preservation

Using only approved protected handling, verify and record normalized pass/fail outcomes for:

- revised runner requests fail closed;
- direct revised diagnostic scripts cannot authenticate after credential/profile removal;
- no alternate profile, raw CLI, generic shell, or prior runtime was used as a bypass;
- no revised process or service remains; and
- the preserved prior baseline remains unchanged.

Obtain the normalized post-attestation `valid, unchanged: true` result. Any failure, ambiguous result, prior-runtime touch, or unavailable attestation ends the rehearsal. Do not retry automatically or claim authority removal.

### 8.4 Restore and close the rehearsal

1. The recovery owner restores the approved project-reader credential using the approved recovery procedure.
2. Restore the protected `aiops-assistant-project-reader` profile through its owning identity deployment procedure.
3. Restore the dedicated runner entrypoint from the recorded revision.
4. Verify only that the intended revised deployment artifacts are restored; do not rerun live diagnostics unless separately authorized.
5. Record only normalized outcomes: runner disabled, credential revoked, profile removed, runner fail-closed, direct-script bypass blocked, prior baseline unchanged, credential restored, profile restored, and runner restored.
6. Retain and delete the protected outcome record according to the approved evidence-owner policy.

### 8.4.1 Execute the approved recovery playbook

After the identity administrator has restored the credential and the recovery owner has confirmed the protected source revision, the Ansible operator may run the dedicated recovery playbook. The extra-vars file must be generated outside Git, contain only approved non-secret gates and the run ID, and be protected according to the evidence policy. Never put credential or profile contents in it.

```bash
rtk ansible-playbook \
  -i ansible/ai_ops_assistant/inventories/local/local.yml \
  ansible/ai_ops_assistant/playbook_recover_mvp_rollback.yml \
  --limit assistant02 \
  -e root_dir="$ROOT_DIR" \
  -e target_env=local \
  -e "@$ROOT_DIR/generated/recover_mvp_rollback.yml"
```

The playbook is fail-closed and pauses for `RESTORED` and `VERIFIED` confirmations. Review the recap for `assistant02` only. Do not use it to run diagnostics, restore prior-runtime material, or automate external credential administration.

A failed recovery is an incident: stop further changes, preserve only allowed normalized evidence, and have the designated administrator recover the capability. Documentation/tabletop review must never be represented as a completed live rehearsal.

## Completion checklist

- [ ] Separate review approved the pipelining correction.
- [ ] Deployment and runner execution authorization is explicit.
- [ ] Target and exact `assistant02` limit are confirmed.
- [ ] Foundation, profile, toolbox, and runtime prerequisites are accepted.
- [ ] New non-secret run ID was created.
- [ ] Fresh administrator pre-attestation is valid.
- [ ] Post-attestation production method is concrete and approved.
- [ ] Protected evidence owner, permissions, retention, and deletion policy are confirmed.
- [ ] Deployment check mode was reviewed.
- [ ] Deployment applied only to `assistant02`.
- [ ] Second deployment returned `changed=0`.
- [ ] Validation used only the fixed runner and three approved tools.
- [ ] Exactly three result/audit pairs were validated.
- [ ] Post-attestation reported valid and unchanged.
- [ ] Outcome-only evidence was recorded outside Git.
- [ ] No prohibited raw or secret material was retained.

## Stop conditions

Stop before live execution when authorization, prerequisites, secure identifier transport, evidence ownership, or post-attestation handling is missing. Stop after live execution on any result mismatch, audit failure, prior-runtime touch, changed-state result, unsafe evidence, or unexpected deployment change. No automatic retry is permitted.
