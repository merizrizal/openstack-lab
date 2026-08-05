## Architectural Design Specification: Revised Manual Diagnostic Toolbox

**Source:** `docs/ai-ops-revised/implementation-plan/03-manual-diagnostic-toolbox.md`, Steps 1–7

**Goal:** Deliver three inspectable, manually runnable, project-reader-only diagnostics for project resources, server basic state, and server networking, with strict identifier validation, stable bounded JSON envelopes, explicit unavailable/error outcomes, automated read-only safety checks, and redacted deployed-lab acceptance evidence.

---

### I. Overview and Contract

Phase 03 adds diagnostic implementations to the isolated revised runtime but does not add a generic runner, MCP integration, operator-reader authority, SSH/log access, or remediation:

```text
accepted Phase 02 project-reader boundary
  -> reviewed toolbox and output contract
  -> revised shared validation/output helper
  -> project resource summary
  -> server basic information
  -> server network information
  -> static and fixture-backed safety validation
  -> namespace-safe deployment
  -> approved manual lab validation
  -> Phase 04 eligibility
```

The only historical implementation paths eligible for Phase 03 review are the four exact paths selected in `selective-reuse-manifest.md`: `lib/aiops_common.sh` and the three named project-level scripts. Selection permits content and dependency review only. The revised implementation must live under `ansible/ai_ops_assistant/`; the historical paths remain unchanged.

#### Activation prerequisites

Phase 03 implementation and live execution fail closed unless the applicable gate is satisfied:

1. The selective-reuse manifest provenance remains valid and the historical tree identity remains `3abc4bcf3fa4caf1c6d89f8d25865e2c0aef8e07`.
2. Phase 02 outcome evidence supports authentication and the required project-reader read matrix. The remaining administrator-owned transient-source and stale-profile cleanup actions must not be performed or inferred by Phase 03.
3. The only usable profile is `aiops-assistant-project-reader` at `/opt/openstack-ai-ops-assistant/credentials/profiles/clouds.yaml`; `secure.yaml` may be present under the Phase 02 contract. Scripts must not read either file's contents.
4. Operator-reader, administrator, member, service, host, database, message-bus, provider, egress, and remediation authority remain unavailable.
5. The deployed OpenStack CLI and `jq` behavior needed for stable JSON processing is confirmed against the installed versions before implementation contracts are finalized.
6. No host connection, Ansible execution, profile access, or OpenStack call occurs until the exact implementation/live-validation chunk is approved.

An unresolved prerequisite produces an unavailable or blocked state. It never authorizes profile fallback, policy expansion, historical-runtime activation, or administrator credentials.

#### Diagnostic interface contracts

The public manual names are **proposed contracts**, subject to Chunk 0 collision and convention confirmation:

| Diagnostic | Invocation contract | Read-only intent | Required sections |
| --- | --- | --- | --- |
| `project_resource_summary` | no arguments | Summarize project-visible servers, networks, subnets, ports, volumes, images, and security groups | `servers`, `networks`, `subnets`, `ports`, `volumes`, `images`, `security_groups` |
| `server_basic_info` | exactly one validated server name or ID | Show safe server state and boot context | `server` |
| `server_network_info` | exactly one validated server name or ID | Show the requested server's attachment and metadata-relevant network path | `server`, `ports`, and permitted related `networks`/`subnets` detail |

Every external invocation uses a fixed argument vector. User input may occupy only the one server-identifier argument position. No script accepts flags, subcommands, additional OpenStack arguments, profile names, executable paths, output paths, or arbitrary field selectors.

#### Identifier validation contract

**Function Signature Contract (Conceptual):** `aiops_require_safe_identifier VALUE FIELD_NAME`

- **Input:** one non-empty server name or ID and a fixed diagnostic field label.
- **Accepted shape:** deliberately conservative ASCII letters, digits, dot, underscore, colon, and hyphen only.
- **Additional bounds:** maximum length is proposed as 255 bytes and must be confirmed against deployed identifier expectations in Chunk 0.
- **Rejected:** empty values, additional arguments, whitespace, control/non-ASCII characters, shell metacharacters, quotes, expansion syntax, glob characters, path separators, `..` path-traversal segments, and overlong values.
- **Output:** no success payload; validation failure emits one bounded structured error envelope and exits before any external process runs.

The helper validates again inside each diagnostic even though Phase 04 will later validate at the runner boundary.

#### Profile-selection contract

**Function Signature Contract (Conceptual):** `aiops_use_project_reader_profile`

- Sets only the revised `OS_CLIENT_CONFIG_FILE` and `OS_CLOUD` values required by the OpenStack client.
- Uses `/opt/openstack-ai-ops-assistant/credentials/profiles/clouds.yaml` and `aiops-assistant-project-reader`.
- Unsets or overrides ambient profile selectors that could choose another cloud; the exact minimal environment must be confirmed in Chunk 0.
- Does not parse, print, checksum, copy, transform, or validate credential content.
- Has no operator-reader or administrator fallback.

#### External invocation contract

**Function Signature Contract (Conceptual):** `aiops_run_read_section TOOL SECTION [FIXED_ARGV...]`

Inputs:

- fixed tool and section names owned by the script;
- the fixed OpenStack CLI path `/usr/bin/openstack`, provided by the installed `python3-openstackclient` foundation package;
- a fixed read-only argument vector, with at most one already validated server identifier.

Outputs:

- one section object conforming to the output-envelope contract;
- a normalized result class and bounded, sanitized service error when the read cannot complete;
- no shell-string evaluation and no caller-selected executable or operation.

The helper must never return a successful empty section for an invocation failure. During a stub-only chunk it must return a clear temporary non-zero `not_implemented` result rather than falsely claiming diagnostic success.

#### Stable output-envelope contract

All three diagnostics write exactly one valid JSON document to stdout. Human-readable diagnostics belong in JSON fields rather than ad hoc headings. The following schema is a **proposed concrete phase contract**, finalized in the operations-contract chunk before script implementation:

```json
{
  "schema_version": "1.0",
  "tool": "server_basic_info",
  "status": "ok",
  "sections": [
    {
      "name": "server",
      "status": "ok",
      "data": {},
      "error": null,
      "truncated": false
    }
  ],
  "error": null
}
```

Contract rules:

- Top-level `status` is exactly `ok`, `partial`, or `error`.
- Section `status` is exactly `ok`, `empty`, or `unavailable`.
- Normalized error classes are `invalid_input`, `not_found`, `ambiguous`, `policy_denied`, `service_unavailable`, `catalog_missing`, `connectivity_error`, `authentication_error`, `configuration_error`, or `execution_error`. These extend, but do not weaken, the Phase 02 result classes.
- `error` is `null` on success or an object containing only a normalized `class` and bounded sanitized `message`; it contains no command arguments, profile content, token, stack trace, catalog, or unbounded response body.
- A supported successful read with no records is `empty`, not `unavailable`.
- A blocked/missing service is `unavailable`, not an empty successful result.
- Aggregate diagnostics continue through independent read-only sections after a section-level unavailable result and finish `partial`; authentication or configuration failures that invalidate all subsequent reads may stop early with `error`.
- Project summary data uses reviewed fields and a documented per-section record limit. `truncated: true` indicates omitted records. Exact fields and limits are finalized against deployed CLI output in Chunk 0/1.
- Server diagnostics return only the requested server and related attachment context. They do not emit unrelated full-project topology as a substitute for relationship resolution.
- Secret-like object keys are replaced with a fixed redaction marker recursively before output. The key pattern must cover at least password, secret, token, credential, private key, and authorization variants without blanket suppression.
- Exit `0` means the requested diagnostic completed with `ok`; a documented non-zero code distinguishes invalid input, partial/unavailable reads, and internal/configuration failure. Exact numeric values are fixed in the operations contract and tested as public behavior.

Raw OpenStack JSON may be transformed into the stable envelope, but raw CLI stdout/stderr is not itself the contract. Raw service error meaning must be preserved through a sanitized, bounded message and normalized class.

#### Proposed repository and runtime placement

The following paths are **conceptual/proposed** until Chunk 0 confirms repository convention:

```text
ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox/
  defaults/main.yml
  tasks/main.yml
  files/scripts/approved/
    lib/aiops_common.sh
    project_resource_summary.sh
    server_basic_info.sh
    server_network_info.sh

ansible/ai_ops_assistant/tests/diagnostic_toolbox/
  test_diagnostic_toolbox.sh
  fixtures/

ansible/ai_ops_assistant/playbook_deploy_diagnostic_toolbox.yml
ansible/ai_ops_assistant/playbook_validate_diagnostic_toolbox.yml
```

Runtime destination:

```text
/opt/openstack-ai-ops-assistant/scripts/approved/
```

Scripts are root-owned, grouped to `aiops_assistant`, non-writable by the runtime user, and executable by that group. The helper is readable but need not be executable. No historical README, Neutron-agent script, registry, runner, MCP resource, or validation playbook enters the revised role.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `03-manual-diagnostic-toolbox.md` requires three manually runnable diagnostics, shared identifier/profile/output behavior, bounded structured output, explicit unavailable results, static safety tests, and project-reader live validation.
- `prd.md` FR-011 through FR-018 require these three scripts, read-only behavior, pre-execution parameter validation, and structured OpenStack output. NFR-001 through NFR-006 and NFR-009 require least privilege, deny-by-default behavior, no privileged credentials, no secret output, safe structured failures, explicit unavailable behavior, and concise results.
- `identity-policy-operations-contract.md` fixes profile `aiops-assistant-project-reader`, the protected profile directory, accepted Phase 02 result classes, and the prohibition on broader-profile fallback. Operator-reader remains unavailable.
- The revised foundation fixes runtime root `/opt/openstack-ai-ops-assistant`, user/group `aiops_assistant`, and the `scripts/approved` workspace. It installs OpenStack CLI, OpenStack SDK, and `jq` capabilities.
- The revised identity-boundary role owns profile materialization and protects `clouds.yaml` and `secure.yaml` as `0600` regular files under a `0700` directory. Phase 03 must consume the named profile without reading credential content.
- `selective-reuse-manifest.md` selects exactly the historical common helper and three project diagnostics for Phase 03 review. It requires revised root/profile/validation/output behavior and declares every other Phase 03-adjacent historical path unselected.
- Historical scripts demonstrate fixed CLI argument vectors and a shared helper, but retain `/opt/openstack-ai-ops`, `aiops-project-reader`, unbounded/raw output, incomplete length/traversal checks, and section formatting that is not one JSON document.
- Historical `server_network_info.sh` emits project-wide network/subnet lists for correlation rather than resolving only requested-server relationships. The revised plan requires useful related context without unrelated project data.
- Historical `playbook_validate_phase03_diagnostic_toolbox.yml` targets the historical runtime, includes Neutron-agent validation, stores raw stdout/stderr and a server identifier in evidence, and is reference-only. It must not be copied.
- `scripts/check_ai_ops_diagnostic_safety.sh` is a repository-level historical guardrail whose default scan root is `ansible/ai_ops_runtime`; it may inform rule coverage but is not selected implementation and must not be weakened to conceal revised false positives.
- `ansible/ai_ops_assistant/` currently contains foundation and identity-boundary roles and no diagnostic toolbox implementation.
- Discovery observed branch `ai-ops-assistant-phase03`, HEAD `8f469ea`, a clean worktree, and no diff under `ansible/ai_ops_runtime` or `inventories/local/nodes.yml`. The pinned historical tree identity resolves to the manifest value.

#### Assumptions

- Bash remains acceptable because the plan explicitly permits inspectable shell scripts and the selected candidates are shell-based.
- `jq` can provide deterministic envelope construction, field selection, recursive key redaction, and fixture assertions without adding a new runtime dependency; exact installed behavior must be confirmed before use.
- OpenStack CLI JSON shapes and error text vary by release, so fixtures must represent deployed outcomes and classifiers must fail to `execution_error` rather than guess.
- One valid server name/ID can be supplied by an operator for approved live validation without retaining it in Git or evidence.
- Manual output may contain requested project topology needed for diagnosis, but retained evidence contains only outcome classes, shape checks, bounds/redaction checks, and unchanged-state confirmation.

#### Open confirmations for Chunk 0

1. Does the current source revision still match the manifest's accepted historical path content and tree identity?
2. Are the four historical paths best adapted or reimplemented after line-by-line dependency and safety review?
3. What exact OpenStack executable path is available in the revised runtime when installed from `python3-openstackclient`?
4. Which `jq` version/features are available and appropriate for recursive redaction and deterministic fixtures?
5. What output fields and per-section limits are useful and stable for each deployed service/version?
6. What exact CLI error signatures distinguish not found, ambiguous name, policy denial, authentication, endpoint/catalog, connectivity, and unknown execution failures without exposing raw errors?
7. Can server port/network/subnet relationships be resolved through fixed project-reader calls without broad project dumps or SDK migration?
8. What numeric exit-code table is approved for `ok`, invalid input, partial/unavailable, and internal/configuration failures?
9. Are the proposed source, test, role, entrypoint, and validation paths consistent with revised Ansible conventions and collision-free?
10. What external evidence location and approved fields will record manual validation without resource identifiers, addresses, raw output, or credentials?

### III. Required Technical Dependencies and Imports

#### Confirmed repository dependencies

- `docs/ai-ops-revised/prd.md`
- `docs/ai-ops-revised/implementation-plan/00-implementation-overview.md`
- `docs/ai-ops-revised/implementation-plan/02-readonly-identity-and-policy-boundary.md`
- `docs/ai-ops-revised/implementation-plan/03-manual-diagnostic-toolbox.md`
- `docs/ai-ops-revised/implementation-plan/04-tool-runner-safety-gateway.md`
- `docs/ai-ops-revised/implementation-plan/ads/02-00-readonly-identity-and-policy-boundary-ads.md`
- `docs/ai-ops-revised/runtime/identity-policy-operations-contract.md`
- `docs/ai-ops-revised/runtime/runtime-placement-contract.md`
- `docs/ai-ops-revised/runtime/source-capability-catalog.md`
- `docs/ai-ops-revised/runtime/selective-reuse-manifest.md`
- revised foundation and identity-boundary roles and entrypoints
- four exact Phase 03 historical selected paths at pinned provenance

#### Runtime dependencies

- Bash with `set -u` and `pipefail` support;
- the installed OpenStack CLI, invoked only through a fixed absolute path and argument arrays;
- `jq` for JSON validation/transformation/envelope generation, if Chunk 0 confirms required features;
- the protected revised project-reader profile;
- project-service endpoint connectivity already accepted by Phase 02;
- no new daemon, listener, SDK migration, package download, network route, profile, or external service.

#### Proposed implementation dependencies

- Ansible built-in `assert`, `file`, `copy`, `stat`, and `command` with `argv` for deployment and non-mutating validation;
- a Bash fixture harness using temporary directories only during repository tests, with a fake fixed OpenStack executable selected through a test-only seam that production scripts cannot accept from user input;
- `bash -n`, `shellcheck` when already available, `jq -e`, and a revised-root static forbidden-operation scan;
- an isolated `/tmp` Python virtual environment populated from root `requirements.txt` only when Ansible lint/syntax tooling must be run.

### IV. Step-by-Step Procedure / Execution Flow

1. Reconfirm branch, HEAD, clean state, pinned historical provenance, revised/historical isolation, and Phase 02 boundary status.
2. Review only the four selected historical files. Record for each `reuse`, `adapt`, or `implement-new`, its full helper/runtime dependency closure, unsafe differences, and revised destination. Do not inspect credential contents or activate historical code.
3. Finalize a toolbox operations contract: names, intent, profile, argument count/pattern/length, fixed read operations, selected fields, limits, envelope schema, statuses, error classes, exit codes, redaction, evidence, and rollback.
4. Add the shared revised helper and fixture seam. The production default fixes revised paths/profile; test overrides are accepted only under an explicit test mode unavailable to normal callers.
5. Implement identifier rejection before every external call. Prove empty, extra, metacharacter, control, path-like, traversal, non-ASCII, and overlong values cannot reach the fake CLI.
6. Implement envelope construction and normalization. Validate JSON before including service data; malformed or unrecognized output fails closed as `execution_error`.
7. Implement `project_resource_summary` with seven fixed list operations, reviewed selected fields, record bounds, independent unavailable sections, and aggregate `ok`/`partial`/`error` status.
8. Implement `server_basic_info` with exactly one server identifier and a fixed `server show` operation. Select safe status/image/flavor/address/availability-zone/config-drive/boot-context fields supported by deployed output.
9. Implement `server_network_info`: establish the server first, query only its attached ports, derive network/subnet IDs from validated structured output, and resolve fixed related reads only where policy permits. Do not accept derived values unless they satisfy the same identifier constraints.
10. Add static checks for mutation verbs, generic execution, shell strings, SSH/sudo, service/package/database operations, file mutation, redirect-write, credential reads, historical paths/profile names, and unapproved scripts.
11. Add fixture-backed behavior tests for successful, empty, partial, unavailable, malformed JSON, service-error, auth/configuration failure, redaction, truncation, argument order, and no-invocation-on-invalid-input paths.
12. Add the revised toolbox role. Copy only the helper and three diagnostics into the revised runtime with explicit ownership/modes; reject symlinks, extra registered scripts, historical paths, and writable-by-runtime implementations.
13. Add a deployment entrypoint targeting only `ai_ops_assistant` and requiring operator limitation to `assistant02`. Do not combine credential deployment or expose protected values.
14. Add a non-mutating validation entrypoint that checks exact files/types/modes, Bash syntax, static safety, project-reader profile selection, JSON shape, bounds, and normalized outcomes without retaining raw payloads.
15. Run local syntax, fixture, static safety, secret-pattern, historical-identifier, Ansible lint/syntax, and exact diff checks. Historical runtime and protected inventory must remain unchanged.
16. After explicit approval, deploy only to `assistant02`, rerun deployment for idempotency, and execute all three diagnostics as `aiops_assistant` against representative project state.
17. Confirm cloud resource state is unchanged through the approved operator comparison. Treat any observed change as a blocking incident; scripts have no cleanup authority.
18. Retain only redacted outcome-level evidence outside Git: revision, UTC time, non-secret run label, tool names, normalized outcomes, shape/bounds/redaction results, idempotency, and unchanged-state confirmation.
19. Reconcile Phase 03 plan checkboxes only where automated and live evidence exists. Stop before implementing the Phase 04 runner.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| --- | --- | --- | --- |
| Prerequisite | Phase 02 project-reader profile/read matrix is unavailable or broader authority is proposed | Stop; do not deploy or execute diagnostics and do not fall back | `ERR_PHASE02_BOUNDARY_UNAVAILABLE` (proposed) |
| Provenance | Historical revision/tree/path differs from the approved manifest | Stop reuse review until the manifest is reconciled | `ERR_PHASE03_REUSE_PROVENANCE` (proposed) |
| Reuse | Unselected README, validator, Neutron tool, runner, or other historical dependency is copied | Reject change and restore revised/historical isolation | `ERR_PHASE03_REUSE_UNAPPROVED` (proposed) |
| Invocation | Wrong argument count, unsafe/control/path-like/overlong identifier, or user-supplied flag | Emit bounded `invalid_input`; invoke no external process | exit code fixed by contract |
| Profile | Revised profile is absent, unreadable to runtime user, or configuration is invalid | Emit `configuration_error`; never choose another profile | top-level `error` |
| Executable | Fixed OpenStack CLI or required `jq` capability is absent | Emit `configuration_error`/`service_unavailable`; do not use PATH fallback unless explicitly contracted | top-level `error` |
| CLI output | Successful command returns malformed/non-JSON output | Reject payload and emit `execution_error` | section `unavailable` or top-level `error` |
| Empty result | Service succeeds with no records | Emit an empty data collection with section `empty` | top-level `ok` if all sections complete |
| Policy/service | One aggregate section is denied, missing, or unavailable | Preserve normalized bounded error, continue independent sections | top-level `partial` |
| Authentication | Credential is rejected or expired | Stop further calls that would repeat the same failure | `authentication_error` |
| Server lookup | Identifier is not found | Emit distinct `not_found`; do not broaden query | top-level `error` |
| Server lookup | Name is ambiguous | Emit distinct `ambiguous`; require an exact ID | top-level `error` |
| Relationship expansion | Network/subnet detail is policy-blocked or absent | Keep attached port evidence and mark only related detail unavailable | top-level `partial` |
| Derived identifier | CLI response contains an unsafe network/subnet/port identifier | Do not invoke follow-up lookup; classify response as malformed/untrusted | `execution_error` |
| Output bound | Resource count or sanitized error exceeds the approved limit | Truncate deterministically and set `truncated: true` | valid bounded envelope |
| Redaction | Secret-like key/value survives transformation | Fail test/deployment gate; do not retain output/evidence | `ERR_DIAGNOSTIC_REDACTION` (proposed) |
| Static safety | Forbidden verb/pattern appears or suppression is blanket/undocumented | Block deployment; require line-specific review or safe redesign | `ERR_DIAGNOSTIC_FORBIDDEN_OPERATION` (proposed) |
| Deployment | Destination is outside revised root, a symlink, wrong owner/mode, or includes extra scripts | Stop before execution and restore only revised toolbox files | `ERR_TOOLBOX_DEPLOYMENT_BOUNDARY` (proposed) |
| Live safety | Any cloud resource state changes after diagnostics | Stop all execution, revoke authority if exposure is suspected, and use administrator-owned investigation/repair | `ERR_DIAGNOSTIC_MUTATION_OBSERVED` (proposed) |
| Evidence | Raw output, identifier, address, command arguments, profile data, or secret enters retained evidence | Stop retention, sanitize/delete, rotate credential if exposure is possible | `ERR_PHASE03_EVIDENCE_DISCLOSURE` (proposed) |

### VI. Security, Integrity, Idempotency, and Cleanup

#### Security

- Execute only fixed read-only `list` and `show` operations required by the three diagnostics. Mutation verbs are forbidden even in dormant branches or examples shipped with the toolbox.
- Validate caller and derived identifiers before external invocation. Quote every argument and never use `eval`, `bash -c`, `sh -c`, command passthrough, or user-built command strings.
- Fix the revised profile and executable location in implementation. Normal callers cannot override them through arguments or inherited historical profile variables.
- Do not read or print credential files, environment secrets, tokens, catalogs, private keys, full secret-bearing configuration, or unrestricted raw service responses.
- Keep scripts root-owned and non-writable by `aiops_assistant`; runtime output is stdout only. No diagnostic writes cloud state, runtime files, audit files, evidence, or configuration.
- Keep operator-reader and host diagnostics absent. Missing detail returns unavailable; Phase 06 owns any later broader scope.
- Treat test-only executable/profile seams as non-production contracts: explicit test mode, repository fixtures only, and static proof that normal manual invocation cannot select arbitrary executables.

#### Integrity

- Preserve `ansible/ai_ops_runtime/` and protected inventory unchanged. Adapt selected logic into new revised paths rather than patching historical files.
- Validate all successful CLI payloads as JSON before field selection; never interpolate untrusted JSON into shell code.
- Build envelopes with `jq` or another confirmed structured mechanism, not string concatenation of unescaped service data.
- Normalize only recognized deployed error signatures. Unknown failures remain `execution_error` rather than being mislabeled as empty, not found, or denied.
- Keep the deployed file allowlist exact: one helper and three diagnostics only.
- Static scans are guardrails, not proof. Any false positive needs a narrow documented review; blanket exclusions, directory skips, and disabling rules are prohibited.

#### Idempotency

- Diagnostics are read-only and safe to retry against unchanged state; output may reflect legitimate concurrent cloud changes.
- Reapplying the role with identical source files must report zero changes.
- Fixture tests are deterministic and create temporary local state only under their test directory or `/tmp`, then remove it.
- A partial service result can be retried without changing profile, policy, or cloud state.
- Evidence records are per approved run and never append raw output.

#### Cleanup and rollback

Repository rollback removes only the new revised ADS/contract/toolbox/test/entrypoint changes from the affected chunk. It does not alter the historical runtime or Phase 02 identity material.

Runtime rollback:

1. disable the revised toolbox deployment entrypoint;
2. remove only the four Phase 03 deployed files and empty revised toolbox subdirectories through an approved administrator/Ansible procedure;
3. leave the foundation workspaces, profile files, runtime identity, and historical runtime untouched;
4. preserve only approved redacted outcome evidence;
5. revoke the project-reader credential only when a mutation or credential-exposure incident warrants the Phase 02 emergency procedure.

Diagnostics have no cleanup function and no authority to repair cloud state.

### VII. Validation Strategy

No validation command that connects to `assistant02`, reads profiles, or calls OpenStack is authorized until its chunk and exact invocation receive operator approval.

#### Documentation and repository checks

```bash
rtk git status --short --branch
rtk git diff --check
rtk grep -nE '^### (I|II|III|IV|V|VI|VII|VIII|IX|X)\.' docs/ai-ops-revised/implementation-plan/ads/03-00-manual-diagnostic-toolbox-ads.md
rtk git diff --exit-code -- ansible/ai_ops_runtime inventories/local/nodes.yml
```

#### Shell syntax, static safety, and behavior

Proposed commands, finalized after Chunk 0 path confirmation:

```bash
rtk bash -n ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved/lib/aiops_common.sh
rtk bash -n ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved/project_resource_summary.sh
rtk bash -n ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved/server_basic_info.sh
rtk bash -n ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox/files/scripts/approved/server_network_info.sh
rtk bash ansible/ai_ops_assistant/tests/diagnostic_toolbox/test_diagnostic_toolbox.sh
```

The behavior harness must prove:

- invalid input never reaches the fake CLI;
- exact argument vectors and profile selectors are used;
- success, empty, partial, unavailable, not-found, ambiguous, auth/configuration, malformed JSON, and unknown-error fixtures produce the contracted envelope and exit code;
- every stdout result parses with `jq -e` and contains only allowed status/error values;
- outputs remain under approved record/message/byte bounds and indicate truncation;
- secret-like fixture keys/values are redacted;
- the three scripts cannot accept arbitrary OpenStack arguments.

Static scanning must inspect only the revised helper and diagnostics, reject all plan-listed mutation/generic-execution families, and separately assert absence of historical roots/profiles and credential-content reads. Comment/documentation matches require line-specific review rather than automatic suppression.

#### Ansible lint and syntax

If Ansible tooling is needed, use an isolated `/tmp` environment from root `requirements.txt`:

```bash
rtk python3 -m venv /tmp/openstack-lab-ai-ops-phase03-venv
. /tmp/openstack-lab-ai-ops-phase03-venv/bin/activate
rtk python -m pip install -r requirements.txt
rtk ansible-lint ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox ansible/ai_ops_assistant/playbook_deploy_diagnostic_toolbox.yml ansible/ai_ops_assistant/playbook_validate_diagnostic_toolbox.yml
rtk ansible-playbook --syntax-check -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_deploy_diagnostic_toolbox.yml
rtk ansible-playbook --syntax-check -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_validate_diagnostic_toolbox.yml
```

Validate exact host targeting, revised-only paths, copied-file allowlist, owners/modes, `command.argv`, `changed_when: false` for checks, suppressed raw results, and absence of credentials or Neutron/operator tools.

#### Secret, scope, and path checks

```bash
rtk grep -RniE '/opt/openstack-ai-ops/|aiops-project-reader|assistant01|neutron_agent|operator.reader|operator_reader' ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox ansible/ai_ops_assistant/playbook_*diagnostic_toolbox.yml
rtk grep -RniE 'password|secret|token|credential|private[_ -]?key|authorization' ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox ansible/ai_ops_assistant/tests/diagnostic_toolbox
rtk git diff -- ansible/ai_ops_assistant docs/ai-ops-revised | rtk grep -nE 'create|update|delete|set|unset|start|stop|restart|eval|sudo|ssh|bash -c|sh -c|>|tee|OS_CLOUD|OS_CLIENT_CONFIG_FILE'
```

Every match is manually classified. Test fixtures may contain unmistakable fake secret-like keys solely to prove redaction; no credential-shaped values or profile content are permitted.

#### Approved deployment and live smoke checks

Only after local checks pass, Phase 02 availability is confirmed, and the operator approves the exact commands:

```bash
rtk ansible-playbook --check --diff --limit assistant02 -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_deploy_diagnostic_toolbox.yml
rtk ansible-playbook --limit assistant02 -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_deploy_diagnostic_toolbox.yml
rtk ansible-playbook --limit assistant02 -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_validate_diagnostic_toolbox.yml
```

The concrete representative server identifier and protected transport inputs are intentionally omitted. They must not enter Git, command examples, shell history, or retained evidence. Live acceptance includes a second deployment with zero changes and administrator-confirmed unchanged cloud state.

#### Final diff review

```bash
rtk git diff --check
rtk git status --short
rtk git diff -- docs/ai-ops-revised ansible/ai_ops_assistant
rtk git diff --exit-code -- ansible/ai_ops_runtime inventories/local/nodes.yml
```

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full Phase 03 toolbox in one pass.

#### Chunk 0: Discovery and Integration Confirmation

- **Goal:** Resolve provenance, reuse/adapt/new decisions, deployed CLI/`jq` behavior, exact fields/limits/errors/exit codes, relationship expansion, repository paths, Phase 02 availability, and evidence gates.
- **Files to read:** this ADS; Phase 02/03 plans and operations contracts; selective-reuse manifest; revised foundation/identity implementation; the four selected historical files; current test/Ansible conventions.
- **Commands:** bounded Git/provenance/path/symbol inspection and local syntax/version discovery only. No edits, host connection, profile read, Ansible play, or OpenStack call.
- **Evidence to confirm:** all Section II open confirmations; exact destination/test paths; complete dependency closure; no registration collision; approved output and live-evidence contracts.
- **Validation:** historical tree identity and revised/historical immutability checks; discovery report with observed facts versus assumptions.
- **Stop condition:** every contract needed for Chunk 1 is explicit. Any unresolved authority, provenance, output, or error-classification decision blocks implementation.

#### Chunk 1: Toolbox Operations and Reuse Decision Contract

- **Goal:** Record one reviewable safety/output contract and per-path reuse disposition before adding executable files.
- **Files to change:** proposed `docs/ai-ops-revised/runtime/manual-diagnostic-toolbox-operations-contract.md`; `selective-reuse-manifest.md` only if evidence requires a disposition/dependency clarification without broadening its four-path Phase 03 allowlist.
- **Symbols to add/change:** no executable symbols; names, intent, profile, parameter/length rules, fixed operations, selected fields, limits, envelope schema, statuses, errors, exit codes, redaction, evidence, rollback, and per-path reuse/adapt/new record.
- **Implementation shape:** documentation only; no activation authority. Historical code remains unchanged.
- **Validation:** Markdown/diff checks, manifest provenance and exact-path checks, secret/historical-identifier review.
- **Stop condition:** reviewers can assess any proposed diagnostic invocation and output against one complete contract; no implementation exists.

#### Chunk 2: Shared Helper and Fixture Harness

- **Goal:** Add tested identifier, profile-selection, JSON-envelope, redaction, bound, and normalized-error contracts without implementing a diagnostic success path.
- **Files to change:** proposed revised `files/scripts/approved/lib/aiops_common.sh` and `tests/diagnostic_toolbox/test_diagnostic_toolbox.sh`.
- **Symbols to add/change:** conceptual `aiops_error`, `aiops_require_safe_identifier`, `aiops_use_project_reader_profile`, envelope/redaction/bound helpers, and `aiops_run_read_section` compile/syntax-safe stub.
- **Implementation shape:** helper performs no OpenStack call in this chunk. The invocation stub returns explicit non-zero `not_implemented`; returning success is unsafe. Tests cover helper contracts with fake data and prove no credential-file read.
- **Validation:** `bash -n` for both files; helper-focused fixture tests; `jq -e` envelope checks; static secret/path/generic-execution scan; exact diff review.
- **Stop condition:** shared contracts are syntax-valid and behavior-tested, while no diagnostic can falsely succeed or contact OpenStack.

#### Chunk 3: Project Resource Summary Slice

- **Goal:** Implement one end-to-end manual diagnostic over seven fixed project-reader list sections.
- **Files to change:** proposed `project_resource_summary.sh` and the existing Phase 03 test harness only.
- **Symbols to add/change:** diagnostic entrypoint plus completed fixed read helper behavior required by this slice; seven section specifications and aggregate status logic.
- **Implementation shape:** no arguments; fixed list argv; selected fields and record limits; valid one-document JSON; independent empty/unavailable sections; no server-specific or network-expansion logic.
- **Validation:** Bash syntax; success/empty/partial/auth/malformed/truncation/redaction fixtures; exact argv assertions; static forbidden-operation scan; diff review.
- **Stop condition:** project summary satisfies its contract through the fake CLI and remains manually invocable; server tools do not exist.

#### Chunk 4: Server Basic Information Slice

- **Goal:** Add one validated-server diagnostic with distinct lookup and service outcomes.
- **Files to change:** proposed `server_basic_info.sh` and the existing Phase 03 test harness only.
- **Symbols to add/change:** one-argument entrypoint, fixed `server show` argv, safe field selection, and not-found/ambiguous/auth/error mapping.
- **Implementation shape:** validate argument count/content/length before invocation; emit one server section; reject arbitrary trailing options; do not add networking expansion.
- **Validation:** Bash syntax; valid identifier and exact argv fixture; empty/missing/extra/metacharacter/control/path/overlong tests; success/not-found/ambiguous/policy/auth/malformed/redaction output tests; safety scan.
- **Stop condition:** server basic info is independently contract-complete and project summary remains passing; network tool is absent.

#### Chunk 5: Server Network Information Slice

- **Goal:** Add bounded requested-server attachment and metadata-path context without unrelated project-wide topology.
- **Files to change:** proposed `server_network_info.sh` and the existing Phase 03 test harness only.
- **Symbols to add/change:** fixed server/port reads, structured relationship extraction, derived-identifier revalidation, permitted network/subnet lookups, and partial-section aggregation.
- **Implementation shape:** establish one server, list only its ports, resolve only IDs derived from validated JSON, mark policy-blocked expansion unavailable, and support multiple ports. No Neutron-agent or host access.
- **Validation:** Bash syntax; exact argv/order checks; multiple-port, no-port, not-found, unsafe-derived-ID, unavailable-network/subnet, malformed JSON, truncation, and redaction fixtures; safety scan.
- **Stop condition:** all three scripts pass local behavior/output contracts; nothing is deployed or registered.

#### Chunk 6: Static Safety and Contract Gate

- **Goal:** Make forbidden-operation, syntax, parameter, output-shape, profile, path, and exact-file checks one repeatable local gate.
- **Files to change:** the proposed Phase 03 test harness and, if separation is confirmed in Chunk 0, one proposed revised safety-check script under `scripts/`.
- **Symbols to add/change:** conservative rule table, exact revised scan root, exact four-file allowlist, line-specific false-positive reporting, and aggregate test entrypoint.
- **Implementation shape:** scan revised diagnostics only; do not alter the historical checker or blanket-ignore comments/directories. Add negative fixtures only when they cannot be mistaken for deployable scripts.
- **Validation:** run the gate against accepted files; prove representative forbidden fixtures fail; Bash syntax; historical/revised path and secret scans; diff review.
- **Stop condition:** one local command proves all static and fixture-backed Phase 03 contracts before deployment automation exists.

#### Chunk 7: Revised Toolbox Deployment Role

- **Goal:** Add idempotent revised-only file placement without executing diagnostics.
- **Files to change:** proposed role `defaults/main.yml` and `tasks/main.yml`.
- **Symbols to add/change:** enable flag, revised root/user/group, exact source/destination allowlist, helper/script modes, path/type/symlink assertions, and copy tasks.
- **Implementation shape:** deploy exactly four approved files to `/opt/openstack-ai-ops-assistant/scripts/approved`; no profile content access, package install, command execution, historical path, runner registry, or Neutron tool.
- **Validation:** YAML/Ansible lint of the role; path/owner/mode/exact-file assertions; secret/historical/excluded-capability scan; diff review. No live role execution.
- **Stop condition:** role is syntax-valid and inspectable but has no deployment caller and has executed nothing.

#### Chunk 8: Deployment and Non-Mutating Validation Entrypoints

- **Goal:** Wire the role only to the revised host and add outcome-only toolbox validation.
- **Files to change:** proposed `playbook_deploy_diagnostic_toolbox.yml` and `playbook_validate_diagnostic_toolbox.yml`.
- **Symbols to add/change:** exact `ai_ops_assistant` host target, role invocation, runtime metadata checks, fixed script argv, JSON/shape/status assertions, output bounds, sanitized outcome summary, and `changed_when: false` validation tasks.
- **Implementation shape:** validation runs as `aiops_assistant`, uses project-reader only, never logs raw stdout/stderr or representative identifiers, and does not include Neutron/operator/host checks. No live run in this chunk unless separately approved after static review.
- **Validation:** inventory graph; ansible-lint and syntax checks; target/argv/no-log/output-flow checks; static gate; full revised diff; historical/protected-path immutability.
- **Stop condition:** deployment and validation paths are locally accepted and ready for an explicit live gate; no host or OpenStack call has occurred by default.

#### Chunk 9: Approved Manual Lab Acceptance and Reconciliation

- **Goal:** Prove deployment idempotency, useful manual output, unchanged cloud state, redacted evidence, and Phase 03 completion; stop before Phase 04.
- **Files to change:** Phase 03 operations contract and `03-manual-diagnostic-toolbox.md` only after external evidence supports each update.
- **Symbols to add/change:** no executable symbols; normalized per-tool outcomes, accepted policy/version limitations, shape/bounds/redaction results, idempotency, unchanged-state confirmation, unresolved gates, and evidence-backed checkboxes.
- **Implementation shape:** after explicit operator approval, limited deployment/validation on `assistant02`; representative identifiers and raw outputs remain external and transient. No runner, registry, MCP, operator-reader, or remediation work.
- **Validation:** approved check/apply/idempotent rerun; all three manual diagnostics; pre/post cloud-state confirmation; evidence redaction scan; final local static tests and diff review.
- **Stop condition:** Phase 03 is evidence-backed complete or explicitly blocked. All broader authority remains unavailable and implementation stops before Phase 04.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline and post-edit-discipline if available.

Task:
Execute Chunk 0 only from docs/ai-ops-revised/implementation-plan/ads/03-00-manual-diagnostic-toolbox-ads.md.

Mode:
Discovery only. Do not edit files, connect to hosts, read profile contents, run Ansible, call OpenStack, or execute historical diagnostics. Confirm provenance, the four path-level reuse decisions and dependency closure, revised destination/test paths, installed CLI/jq assumptions, output fields and limits, error signatures, exit codes, server-network relationship strategy, Phase 02 availability, and evidence handling. Stop with exact evidence and blockers.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Execute Chunk 1 only.
Do not continue to Chunk 2.
Create only the Phase 03 toolbox operations/reuse contract and make a manifest clarification only if the accepted discovery evidence requires it. Run targeted Markdown, manifest, secret, provenance, and historical-runtime immutability checks; show the diff and stop. Do not change Ansible or scripts, connect to a host, access profiles, or call OpenStack.
```

For later chunks:

```text
Execute only the explicitly approved chunk and stop with a handoff. Run the chunk's narrow syntax, fixture, static safety, secret/path, and diff checks. Do not perform host deployment or OpenStack calls before Chunk 9 receives explicit operator approval. Never fall back from aiops-assistant-project-reader to broader authority, and never retain raw outputs, identifiers, addresses, profile content, or credentials in Git or evidence.
```

### X. Conclusion and Next Steps

Phase 03 is a narrow manual diagnostic boundary: one shared helper and three project-reader-only scripts in the revised namespace. Stable bounded JSON, strict validation before every external call, fixed read-only argument vectors, explicit unavailable behavior, and exact-path deployment are part of the capability—not later hardening. Historical code supplies four review candidates, not activation authority, and all broader diagnostic families remain excluded.

The next implementation session must execute Chunk 0 only. It must resolve output/error/limit contracts and repository integration from evidence before any operations contract or executable toolbox file is created. Live deployment and OpenStack validation remain gated until Chunk 9 and explicit operator approval.
