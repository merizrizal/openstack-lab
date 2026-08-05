## Architectural Design Specification: Secure Diagnostic Acceptance Automation

**Source:** `docs/ai-ops-revised/implementation-plan/03-manual-diagnostic-toolbox.md`, proposed Step 8; approved Phase 03 acceptance-automation amendment.

**Goal:** Add a narrowly scoped, operator-approved Ansible acceptance path that runs the three deployed Phase 03 diagnostics as `aiops_assistant`, receives only sanitized outcome facts, and requires an administrator-owned boolean pre/post cloud-state comparison before Phase 03 reconciliation.

---

### I. Overview and Contract

This extension automates repetitive acceptance orchestration; it does not broaden diagnostic, profile, host, cloud, or remediation authority.

```text
operator-approved secure identifier transport
  -> administrator pre-state boolean attestation
  -> fixed diagnostics as aiops_assistant
  -> in-memory redaction/shape/bound validation
  -> administrator post-state boolean attestation
  -> outcome-only evidence record
  -> Phase 03 reconciliation
```

The proposed playbook is revised-only, targets only `assistant02` with an explicit `assistant02` limit, and invokes only the four deployed approved-script paths. It uses the existing fixed project-reader profile through the scripts; it must not inspect profile content or select an alternate profile.

**Administrator comparison interface contract (conceptual):** an administrator-owned external procedure receives a non-secret run label and phase label, owns all resource identity/state collection, and returns only a machine-readable boolean `unchanged` plus a non-secret comparison status. It must never return resource identifiers, addresses, cloud payloads, command text, stdout, stderr, credentials, or profile content. The acceptance playbook fails closed unless both pre and post attestations are present and the post attestation reports `unchanged: true`.

**Secure identifier transport contract (conceptual):** the server identifier is supplied through an approved operator-controlled mechanism which is unavailable to Git, inventory, extra-vars, process listings, shell history, Ansible callback output, and retained evidence. The playbook may hold it only in `no_log: true` task state long enough to execute the two fixed server diagnostics, then must discard it. Chunk 0 must confirm the actual mechanism before implementation; absent that confirmation, no executable playbook is created.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `03-00-manual-diagnostic-toolbox-ads.md` requires all three manual diagnostics, pre/post unchanged-state confirmation, outcome-only evidence, and a stop before Phase 04.
- `manual-diagnostic-toolbox-operations-contract.md` prohibits retaining identifiers, command arguments, raw output, cloud payloads, or profile data and fixes the Phase 03 evidence location outside Git.
- `playbook_validate_diagnostic_toolbox.yml` verifies deployment metadata without cloud reads and reports only non-sensitive booleans.
- Existing validation playbooks use `ansible.builtin.command` with `argv`, `become_user: aiops_assistant`, `changed_when: false`, `failed_when: false`, and `no_log: true` for sensitive runtime work.

#### Assumptions requiring Chunk 0 confirmation

1. An administrator provides the boolean-only comparison interface and owns its invocation, retention, and incident response.
2. An approved secret-safe identifier transport exists and can be consumed without using inventory, `--extra-vars`, controller logs, or shell history.
3. The Ansible callback/logging configuration does not retain `no_log` task data or prompt/input material outside the approved evidence boundary.
4. The operator separately approves the exact live playbook command after local review.

### III. Required Technical Dependencies and Imports

- Existing `ansible.builtin.assert`, `command`, `set_fact`, `debug`, and `pause` capabilities only where their deployed behavior has been verified safe for the selected identifier mechanism.
- Existing deployed diagnostic scripts and Phase 03 static/fixture safety gates.
- An administrator-owned comparator integration; no OpenStack admin credential, inventory value, or comparison command is added to this repository.
- No new Python dependency, generic shell executor, runner, MCP resource, SSH capability, or credential-copy mechanism.

### IV. Step-by-Step Procedure / Execution Flow

1. Assert exact host/group/limit, approved run-label syntax, and the declared secure-transport/comparator integration labels.
2. Obtain a pre-run boolean-only administrator attestation; stop unless it is successful.
3. Invoke `project_resource_summary.sh` as `aiops_assistant` with fixed `argv` and no arguments.
4. Obtain the protected server identifier only through the confirmed secure transport and invoke `server_basic_info.sh` and `server_network_info.sh` with fixed `argv`.
5. Keep raw results in `no_log` task state; parse only JSON shape, tool name, top-level status, bounded size, and redaction result into normalized non-sensitive facts.
6. Obtain the post-run boolean-only administrator attestation; stop on absent, failed, or changed state.
7. Emit or write only contract-approved outcome facts outside Git. The operator decides whether those facts satisfy Phase 03 reconciliation.

### V. Failure Modes and Resilience

| Stage | Failure mode | System action | Next state |
| --- | --- | --- | --- |
| Scope | Wrong host, group, limit, script path, or runtime user | Stop before any diagnostic | `ERR_PHASE03_ACCEPTANCE_SCOPE` (proposed) |
| Identifier | Secure transport unavailable or leaks to an unsafe channel | Stop; do not invoke server diagnostics | `ERR_PHASE03_ACCEPTANCE_IDENTIFIER` (proposed) |
| Pre-state | Administrator attestation absent or non-successful | Stop before diagnostics | `ERR_PHASE03_STATE_COMPARISON_UNAVAILABLE` (proposed) |
| Diagnostic | Invalid JSON, unsafe redaction/bound result, or execution error | Retain no raw output; report normalized tool outcome | `ERR_PHASE03_DIAGNOSTIC_ACCEPTANCE` (proposed) |
| Post-state | Comparator reports changed or cannot attest | Stop acceptance; administrator investigates externally | `ERR_DIAGNOSTIC_MUTATION_OBSERVED` (proposed) |
| Evidence | Sensitive material reaches playbook output/evidence | Stop retention, sanitize/delete, and follow credential incident procedure when warranted | `ERR_PHASE03_EVIDENCE_DISCLOSURE` (proposed) |

### VI. Security, Integrity, Idempotency, and Cleanup

- All identifier-bearing, raw-result-bearing, and profile-adjacent tasks use `no_log: true`; public debug output is limited to normalized outcome facts.
- Every command uses a fixed `argv` array; no shell, `stdin` redirection, `eval`, caller-selected executable, generic command, arbitrary argument, or profile override is allowed.
- The playbook has no mutation, cleanup, repair, profile-read, credential-write, or cloud-state comparison implementation authority.
- Administrator comparison data and outcome-only evidence remain outside Git. The repository retains only contract and checklist conclusions after external review.
- Re-running a completed acceptance playbook is safe only with a new approved run label and fresh administrator attestations. A failed/changed post-state is an incident, not a retry condition.
- Rollback removes the acceptance playbook and its local tests only. It does not alter deployed diagnostics, profiles, inventories, cloud resources, or administrator evidence.

### VII. Validation Strategy

Before any live execution:

```bash
rtk ansible-lint ansible/ai_ops_assistant/playbook_accept_diagnostic_toolbox.yml
rtk ansible-playbook --syntax-check --limit assistant02 -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_accept_diagnostic_toolbox.yml
rtk bash ansible/ai_ops_assistant/tests/diagnostic_toolbox/test_diagnostic_toolbox.sh
rtk bash scripts/check_ai_ops_revised_diagnostic_toolbox_safety.sh
rtk git diff --check
```

Static review must prove exact target, `aiops_assistant` execution, fixed script allowlist/`argv`, `no_log` coverage, absence of raw-result debug/output persistence, absence of credentials/identifiers in defaults or inventory, and absence of OpenStack admin commands. Live execution requires separate explicit operator approval and administrator comparator availability.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full acceptance path in one pass.

#### Chunk 0: Secure Integration Discovery
- **Goal:** Confirm the actual identifier transport, boolean-only comparator interface, Ansible logging behavior, and evidence ownership.
- **Files to read:** this ADS, Phase 03 operations contract, existing validation playbooks, and the approved operator/admin integration documentation.
- **Commands:** bounded repository inspection and local Ansible capability discovery only; no host connection, secret access, diagnostic invocation, or cloud call.
- **Evidence to confirm:** both integrations exist, have no sensitive output path, and can fail closed.
- **Stop condition:** implementation is blocked unless both interfaces are concrete and approved.

#### Chunk 1: Acceptance Playbook Contract and Syntax-Safe Stub
- **Goal:** Add a non-live playbook with exact scope assertions and explicit failure when secure integrations are absent.
- **Files to change:** proposed `ansible/ai_ops_assistant/playbook_accept_diagnostic_toolbox.yml` and a focused local static test.
- **Symbols to add/change:** proposed acceptance variables, fixed script allowlist, and explicit unavailable assertions.
- **Implementation shape:** no diagnostic execution; no identifier transport implementation; compile-safe failure is required.
- **Validation:** Ansible lint, syntax check, static `no_log`/path/forbidden-operation review, and diff review.
- **Stop condition:** the stub cannot falsely report acceptance or contact OpenStack.

#### Chunk 2: Outcome Normalization and Evidence Boundary
- **Goal:** Add in-memory normalization of fixture-backed diagnostic results into non-sensitive facts.
- **Files to change:** the acceptance playbook and its focused local test.
- **Symbols to add/change:** proposed per-tool normalized outcome records and outcome-only summary schema.
- **Implementation shape:** use fake command fixtures only; assert raw results cannot reach debug/evidence fields.
- **Validation:** syntax/lint, fixture tests, secret/identifier scan, and diff review.
- **Stop condition:** only allowed outcome fields can leave `no_log` state.

#### Chunk 3: Approved Secure Interfaces and Live Gate
- **Goal:** Wire only the accepted identifier transport and comparator integration, then perform one separately approved live acceptance run.
- **Files to change:** acceptance playbook and focused test only if Chunk 0 confirms stable interfaces.
- **Symbols to add/change:** concrete integration calls and fail-closed pre/post attestation checks.
- **Implementation shape:** execute fixed diagnostics as `aiops_assistant`; no generic/admin cloud command enters the repository.
- **Validation:** all local gates, approved limited live run, administrator unchanged-state confirmation, external evidence redaction scan, and diff review.
- **Stop condition:** Phase 03 is evidence-backed complete or explicitly blocked; stop before Phase 04.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline and post-edit-discipline if available.

Task:
Execute Chunk 0 only from docs/ai-ops-revised/implementation-plan/ads/03-01-secure-diagnostic-acceptance-automation-ads.md.

Mode:
Discovery only. Do not edit files, connect to hosts, access identifiers/profiles, run Ansible, call OpenStack, or invoke diagnostics. Confirm the approved secure identifier transport, administrator boolean-only comparator, logging boundary, and evidence ownership. Stop with evidence and blockers.
```

### X. Conclusion and Next Steps

The acceptance playbook is permissible only as a narrow orchestrator around existing Phase 03 diagnostics and an external administrator-owned state comparison. Its safety depends on concrete secure integrations confirmed in Chunk 0. The next implementation session executes Chunk 0 only.
