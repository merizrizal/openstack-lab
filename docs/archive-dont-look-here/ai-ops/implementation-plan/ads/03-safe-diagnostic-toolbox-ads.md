## Architectural Design Specification: AI-OPS Safe Diagnostic Toolbox

**Source:** `docs/ai-ops/implementation-plan/03-safe-diagnostic-toolbox.md`

**Goal:** Create the first reviewed set of read-only OpenStack API diagnostic scripts for the AI-OPS assistant runtime, using the validated project-reader credential by default, bounded/structured output, explicit input validation, and static safety checks that flag unsafe shell or OpenStack mutation patterns before scripts are trusted.

---

### I. Overview and Contract

Phase 03 turns the validated Phase 02 credential boundary into a small, inspectable diagnostic toolbox. The toolbox must support manual operator execution first; later phases may wrap the same scripts behind a local safety gateway and MCP. The target path is:

```text
credential matrix
  -> reviewed read-only scripts
  -> manual execution on assistant01
  -> structured or clearly sectioned outputs
  -> static checks prove no obvious mutation commands are present
```

The first toolbox must not introduce generic command execution, raw OpenStack CLI passthrough, SSH diagnostics, remediation, host log access, or MCP exposure.

#### Runtime Script Directory Contract (Concrete)

`docs/ai-ops/runtime/README.md` defines the assistant runtime workspace:

```text
/opt/openstack-ai-ops/
  scripts/
    approved/
  diagnostics/
    raw/
    summaries/
  credentials/
    profiles/
```

`/opt/openstack-ai-ops/scripts/approved/` is the runtime location for reviewed read-only diagnostic scripts. It may have existed empty until Phase 03.

#### Credential Profile Contract (Concrete)

`docs/ai-ops/runtime/credential-boundary-runbook.md` states:

- default profile name: `aiops-project-reader`
- credential files live on `assistant01` under `/opt/openstack-ai-ops/credentials/profiles/`
- required environment:

```bash
export OS_CLIENT_CONFIG_FILE=/opt/openstack-ai-ops/credentials/profiles/clouds.yaml
export OS_CLOUD=aiops-project-reader
```

Scripts must select this profile by default unless explicitly classified otherwise.

#### OpenStack Command Contract (Conceptual)

Initial scripts are shell scripts for inspectability. They should call the runtime OpenStack CLI directly through argument vectors, not through `eval`, command strings, user-supplied subcommands, or generic passthrough.

Expected OpenStack CLI binary:

```text
/opt/openstack-ai-ops/.venv/bin/openstack
```

This path is supported by `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml`, which defines `ai_ops_runtime_venv_path: /opt/openstack-ai-ops/.venv` and installs `openstackclient`.

#### Proposed Repository Source Contract (Conceptual, to confirm in Chunk 0)

The repository currently documents and manages the runtime through `ansible/ai_ops_runtime`, but no Phase 03 script source directory exists yet. Chunk 0 must confirm whether the source-of-truth for approved scripts will be one of:

1. an Ansible role static-files directory, for example `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved/`; or
2. a top-level repository script directory, for example `scripts/ai_ops/approved/`, copied manually or by a later task.

Because the existing runtime is Ansible-managed, the preferred proposed source is an Ansible role static-files directory plus an explicit task to install the approved scripts to `/opt/openstack-ai-ops/scripts/approved/`.

#### Script Contracts (Conceptual)

The phase requires these tool behaviors:

- `project_resource_summary`: list project-visible servers, networks, subnets, ports, volumes, images, and security groups where policy allows.
- `server_basic_info`: accept one server name or ID and return server details in JSON.
- `server_network_info`: accept one server name or ID, return server summary and related port/network/subnet details where practical.
- `neutron_agent_health`: unavailable placeholder unless a separate non-default operator-reader profile has been created and validated.

Shell helper contracts should cover:

- default profile selection
- OpenStack object identifier validation
- section or JSON-envelope output helpers
- consistent error messages and exit codes
- comments explaining shell metacharacter rejection

**Function Signature Contract (Conceptual):** shell helper names are not yet concrete and must be confirmed during implementation. Proposed shell function names may include:

```text
aiops_require_safe_identifier <value> <field_name>
aiops_use_project_reader_profile
aiops_print_section <section_name>
aiops_error <exit_code> <message>
```

Temporary stubs, if used, should fail closed with a clear non-zero error rather than returning success for unavailable diagnostics.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops/implementation-plan/03-safe-diagnostic-toolbox.md` defines the Phase 03 target outcome: `credential matrix -> reviewed read-only scripts -> manual execution -> structured outputs -> no mutation commands present`.
- The same Phase 03 plan includes seven ordered steps: safety rules, common helpers, project resource summary, server basic info, server network info, optional Neutron agent health gate, and static safety checks.
- Phase 03 excludes generic command execution, SSH-based log diagnostics, operator-reader tools unless safe credentials exist, MCP integration, and a full Python SDK rewrite.
- `docs/ai-ops/implementation-plan/00-implementation-overview.md` places Phase 03 after the read-only credential boundary and before the tool-runner safety gateway.
- `docs/ai-ops/implementation-plan/00-implementation-overview.md` states cross-phase principles: no generic shell/SSH/sudo/OpenStack CLI/file-write/database/restart/remediation tool, deny-by-default diagnostics, narrow validated parameters, structured results, and dedicated least-privileged credentials.
- `docs/ai-ops/prd.md` FR-011 through FR-014 require approved diagnostic scripts for project resource summary, server basic info, server network info, and Neutron agent health when safe operator-reader credentials are available.
- `docs/ai-ops/prd.md` FR-016 through FR-018 require read-only scripts, input validation, and structured output such as JSON.
- `docs/ai-ops/prd.md` implementation decisions state that OpenStack API scripts are created before AI/MCP integration, shell scripts are acceptable first, and parameter validation must be enforced by both tool runner and scripts.
- `docs/ai-ops/runtime/README.md` defines `/opt/openstack-ai-ops/scripts/approved/` as the reviewed script directory and says the Phase 02 `aiops-project-reader` profile is protected under `/opt/openstack-ai-ops/credentials/profiles/`.
- `docs/ai-ops/runtime/credential-boundary-runbook.md` records the default profile name `aiops-project-reader`, selected project `admin`, domain `default`, role `reader`, and runtime profile files `clouds.yaml` and `secure.yaml`.
- `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml` defines the runtime root, runtime user/group, virtualenv path, workspace directory list, credential profile mode, and OpenStack profile name.
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/tooling.yml` installs `openstackclient` and `openstacksdk` into the runtime virtual environment.
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/main.yml` currently creates workspace directories, manages credentials, and installs tooling. No script deployment task is present yet.
- `ansible/ai_ops_runtime/roles/assistant_runtime` currently has only `defaults/` and `tasks/`; there is no observed role `files/` directory for approved scripts yet.
- Current branch observed during ADS creation: `ai-ops/03-safe-diagnostic-toolbox`.

#### Assumptions

- The Phase 02 credential boundary remains valid and should not be reimplemented in Phase 03.
- The default project-reader profile can read at least some project-visible resources, but individual resource classes may be policy-denied or service-unavailable.
- Shell scripts should avoid complex JSON transformation initially; preserving raw OpenStack JSON is safer than brittle parsing.
- `jq` or equivalent JSON tooling is expected from Phase 01 documentation, but Chunk 0 should confirm whether it is installed before relying on it.
- A role static-files directory is a reasonable proposed repository source location because the runtime is already Ansible-managed, but this is not yet an observed convention in the role.
- Runtime validation on `assistant01` may be manual and evidence should be redacted under `docs/ai-ops/runtime/` only after actual execution.

### III. Required Technical Dependencies and Imports

#### Runtime dependencies

- `assistant01` as the AI-OPS runtime.
- `/opt/openstack-ai-ops/.venv/bin/openstack` with `openstackclient` installed.
- `/opt/openstack-ai-ops/credentials/profiles/clouds.yaml` and `secure.yaml`, protected with Phase 02 permissions.
- Named profile `aiops-project-reader`.
- Standard shell support for inspectable scripts.
- JSON tooling if scripts add JSON envelopes or post-processing.

#### Repository/documentation dependencies

- `docs/ai-ops/implementation-plan/03-safe-diagnostic-toolbox.md`
- `docs/ai-ops/implementation-plan/00-implementation-overview.md`
- `docs/ai-ops/runtime/README.md`
- `docs/ai-ops/runtime/credential-boundary-runbook.md`
- Proposed evidence note: `docs/ai-ops/runtime/phase03-diagnostic-toolbox-evidence-YYYY-MM-DD.md`

#### Proposed implementation dependencies

The implementation may add, subject to Chunk 0 confirmation:

- approved script source directory
- safety policy README in that directory
- common shell helper file
- one shell script per diagnostic tool
- optional Ansible task to install scripts into `/opt/openstack-ai-ops/scripts/approved/`
- repository-local static safety check script

No new OpenStack role, service credential, SSH key, sudo rule, database access, RabbitMQ access, MCP server, or generic runner is required for Phase 03.

### IV. Step-by-Step Procedure / Execution Flow

1. Confirm repository source layout for approved scripts.
   - Verify whether an existing script-source convention exists.
   - If no convention exists, select a minimal source path that can later be installed to `/opt/openstack-ai-ops/scripts/approved/`.
2. Add script safety policy before scripts.
   - Document read-only-only scope.
   - List forbidden operations.
   - Require input validation.
   - Require `aiops-project-reader` by default.
   - Require bounded/structured output.
3. Add common helper stubs and validation behavior.
   - Fail closed on unsafe input.
   - Reject shell metacharacters and empty identifiers.
   - Set `OS_CLIENT_CONFIG_FILE` and `OS_CLOUD` without exposing secrets.
   - Provide consistent non-zero exits for validation failures and unavailable tools.
4. Add project resource summary script.
   - Use fixed OpenStack read/list commands only.
   - Prefer `-f json` or clearly sectioned output.
   - Continue safely or report unavailable sections when a service/policy blocks a read.
5. Add server basic info script.
   - Accept exactly one safe server identifier.
   - Run fixed `server show` read operation in JSON.
   - Preserve OpenStack error output for not-found or permission-denied cases.
6. Add server network info script.
   - Accept exactly one safe server identifier.
   - Return server summary and port/network/subnet evidence where practical using read-only operations.
   - Keep expansion simple and avoid parsing assumptions that differ across OpenStack versions.
7. Add Neutron agent health gate.
   - If no validated operator-reader profile exists, provide an explicit unavailable placeholder.
   - Do not use project-reader for commands known to require operator-level visibility.
   - Do not add service restart, enable/disable, or repair commands.
8. Add static safety checks.
   - Scan approved scripts for mutation verbs and unsafe shell patterns.
   - Run shell syntax validation across scripts.
   - Document false positives and manual review expectations.
9. Perform runtime validation manually on `assistant01`.
   - Run scripts with `aiops-project-reader`.
   - Save only redacted/non-secret evidence.
   - Do not paste or commit secrets, tokens, or unredacted profile content.
10. Update Phase 03 checklist only after evidence exists.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| ----- | ------------ | ------------------- | ----------------------- |
| Layout selection | No approved script source path is confirmed | Stop after Chunk 0 and choose source path explicitly | `ERR_AI_OPS_SCRIPT_SOURCE_UNSET` (proposed) |
| Safety policy | Script is added before policy exists | Pause script work and add/review policy first | Phase 03 Step 1 remains incomplete |
| Credential selection | Script defaults to admin/member/operator profile | Reject change; restore `aiops-project-reader` default | `ERR_AI_OPS_UNSAFE_DEFAULT_PROFILE` (proposed) |
| Input validation | Empty or unsafe server identifier accepted | Fail closed before OpenStack CLI invocation | `ERR_AI_OPS_INVALID_IDENTIFIER` (proposed) |
| Command construction | Script uses `eval`, shell-string interpolation, or raw passthrough | Static check fails; script is not trusted | `ERR_AI_OPS_UNSAFE_SHELL_PATTERN` (proposed) |
| OpenStack operation | Script contains create/update/delete/set/start/stop/restart/install verbs | Static check fails; remove mutation command | `ERR_AI_OPS_MUTATION_PATTERN` (proposed) |
| Project reads | A read command is policy-denied or service-unavailable | Preserve non-secret error output and mark section unavailable | Script exits according to documented partial-failure policy |
| Server lookup | Server name/ID is not found | Preserve OpenStack error class; no fallback to broader search | User receives not-found/permission report |
| Output handling | Output is unbounded or too verbose | Prefer raw JSON for fixed scope; add bounded sections or truncation note | Evidence remains reviewable |
| Secret handling | Output/evidence includes token, password, secret, or profile contents | Remove/redact evidence, rotate secret if exposed | `ERR_AI_OPS_SECRET_EXPOSURE` (proposed) |
| Neutron agent health | Operator-reader profile is absent | Provide unavailable placeholder, not project-reader escalation | `unavailable: operator-reader deferred` |
| Static checks | False positive blocks safe read-only script | Document exception and require manual review | Maintainer accepts or refines pattern |
| Runtime validation | Script works locally but not on `assistant01` | Check runtime path, permissions, OpenStack CLI version, and profile env | Evidence records runtime-specific failure |

### VI. Security, Integrity, Idempotency, and Cleanup

- Scripts must be read-only by construction and review.
- Scripts must not include create, update, delete, set, unset, restart, stop, start, install, edit, write redirection, unrestricted sudo, database mutation, raw SSH forwarding, or generic shell/OpenStack passthrough.
- Scripts must not read or print credential files.
- Scripts must set or require `OS_CLIENT_CONFIG_FILE` and `OS_CLOUD` without displaying their contents.
- Inputs must be narrow and reject shell metacharacters. For MVP server names/IDs, use a conservative character set such as alphanumeric, dot, underscore, colon, and hyphen if confirmed acceptable.
- Shell implementation must avoid `eval`, backticks with user input, unquoted parameter expansion, dynamic subcommands, and user-controlled file paths.
- Static checks are a guardrail, not proof of safety. Human review remains required.
- Idempotency expectation: repeated script runs must not alter OpenStack resources or runtime files, except optional operator-captured diagnostic output outside script scope.
- Cleanup is not expected for scripts because no resources are created. If any command mutates resources during validation, treat it as a blocking safety incident and use an operator/admin path for cleanup.
- Operator-reader remains separate, non-default, and unavailable unless explicitly created and validated later.

### VII. Validation Strategy

Validation must be chunk-aware and stop after each slice.

#### Static repository validation

- Verify new shell scripts parse with shell syntax checks.
- Verify helper functions exist before scripts source or call them.
- Run the repository-local static safety check once added.
- Review `git diff` for accidental secret material, mutation commands, broad credential use, or generic passthrough.

Suggested command classes for implementation sessions:

```bash
bash -n <changed-shell-files>
grep -Rni "eval\|sudo\| openstack .* create\| openstack .* delete\| openstack .* set" <approved-script-source>
git diff -- <changed-files>
```

#### Runtime smoke validation on `assistant01`

- Confirm profile env points to `/opt/openstack-ai-ops/credentials/profiles/clouds.yaml` and `aiops-project-reader`.
- Run `project_resource_summary` manually and record section pass/fail without secrets.
- Run `server_basic_info` with one existing server and one invalid safe identifier.
- Run `server_network_info` with one existing server where policy allows.
- Confirm Neutron agent health reports unavailable if operator-reader is deferred.
- Save redacted evidence under `docs/ai-ops/runtime/` only after actual runtime validation.

#### Checklist validation

Only check Phase 03 tasks complete when:

- script exists or placeholder exists as specified,
- input validation has been tested,
- no mutation/static safety check failures remain,
- runtime manual execution evidence exists where the task requires manual validation.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass.

#### Chunk 0: Discovery and Integration Confirmation
- **Goal:** Confirm source layout, runtime installation approach, available shell/JSON tooling, and whether Phase 03 starts from a clean branch.
- **Files to read:**
  - `docs/ai-ops/implementation-plan/03-safe-diagnostic-toolbox.md`
  - `docs/ai-ops/implementation-plan/00-implementation-overview.md`
  - `docs/ai-ops/runtime/README.md`
  - `docs/ai-ops/runtime/credential-boundary-runbook.md`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/main.yml`
  - candidate script-source directories discovered with `find`
- **Commands:**
  - discover candidate script directories
  - inspect git status and branch
  - search for existing Phase 03/toolbox/safety scripts
- **Evidence to confirm:**
  - selected repository source path for approved scripts
  - whether scripts are Ansible-installed or manually copied for Phase 03
  - whether `jq` or JSON tooling is available on `assistant01`
  - default OpenStack CLI/profile path remains unchanged
- **Stop condition:** Evidence is summarized; no files edited.

#### Chunk 1: Safety Policy README
- **Goal:** Add reviewed safety policy before adding executable diagnostics.
- **Files to change:**
  - proposed approved script source README, for example `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved/README.md` or the Chunk 0-selected equivalent
  - optionally `docs/ai-ops/runtime/README.md` if it needs a pointer to the policy
- **Symbols to add/change:** not applicable; documentation only.
- **Implementation shape:** Create a README listing read-only scope, forbidden operations, input validation rules, default profile, output bounds, review expectations, and static check expectations.
- **Validation:** Markdown review plus `git diff -- <changed-files>`.
- **Stop condition:** Safety policy exists in the script directory and no scripts are added yet.

#### Chunk 2: Common Shell Helper Stub and Validation Slice
- **Goal:** Add a helper file with fail-closed input validation and default profile selection before any diagnostic script depends on it.
- **Files to change:**
  - proposed helper file, for example `<approved-script-source>/lib/aiops_common.sh` or Chunk 0 equivalent
- **Symbols to add/change:**
  - conceptual `aiops_use_project_reader_profile`
  - conceptual `aiops_require_safe_identifier`
  - conceptual `aiops_print_section`
  - conceptual `aiops_error`
- **Implementation shape:** Implement minimal shell functions. Validation rejects empty values and shell metacharacters. Profile helper exports `OS_CLIENT_CONFIG_FILE` and `OS_CLOUD`. Error helper writes concise messages to stderr and exits non-zero. Add comments explaining metacharacter rejection.
- **Validation:** `bash -n <helper-file>` and targeted grep confirming helper function names exist.
- **Stop condition:** Helper parses and can be sourced by future scripts without performing OpenStack operations.

#### Chunk 3: Project Resource Summary Script
- **Goal:** Add the first useful read-only OpenStack diagnostic script using the helper.
- **Files to change:**
  - `<approved-script-source>/project_resource_summary.sh` or Chunk 0 equivalent
  - optionally the policy README tool list
- **Symbols to add/change:** script entry point only; no user-defined public API beyond shell helper calls.
- **Implementation shape:** Fixed read/list commands for servers, networks, subnets, ports, volumes, images, and security groups using `-f json` where practical. Use the project-reader profile by default. Report section-level failures without escalating credentials.
- **Validation:** `bash -n <script>`; run static grep for mutation verbs; manually run on `assistant01` only when credentials are available.
- **Stop condition:** Script is reviewable, syntax-valid, and contains fixed read-only operations only.

#### Chunk 4: Server Basic Info Script
- **Goal:** Add a single-argument server details diagnostic.
- **Files to change:**
  - `<approved-script-source>/server_basic_info.sh`
  - optional README tool list update
- **Symbols to add/change:** script entry point; uses existing helper validation.
- **Implementation shape:** Require exactly one server name/ID. Validate it. Run a fixed `server show` read command with JSON output. Preserve not-found/permission-denied stderr and exit code.
- **Validation:** `bash -n <script>`; run validation failure case locally without OpenStack if possible; runtime success/failure smoke on `assistant01` when available.
- **Stop condition:** Invalid input is rejected before OpenStack invocation and safe input follows one fixed read-only path.

#### Chunk 5: Server Network Info Script
- **Goal:** Add server network evidence without generic CLI access.
- **Files to change:**
  - `<approved-script-source>/server_network_info.sh`
  - optional README tool list update
- **Symbols to add/change:** script entry point; uses existing helper validation.
- **Implementation shape:** Require one validated server name/ID. Return server summary and project-visible ports/networks/subnets where practical. Avoid complex parsing that is not portable across OpenStack CLI versions; prefer raw JSON sections if needed.
- **Validation:** `bash -n <script>`; static mutation grep; runtime smoke against one existing server if available.
- **Stop condition:** Script provides bounded, read-only network evidence and documents any intentionally skipped expansion.

#### Chunk 6: Neutron Agent Health Availability Gate
- **Goal:** Represent deferred operator-reader diagnostics safely.
- **Files to change:**
  - `<approved-script-source>/neutron_agent_health.sh` or documented placeholder
  - README classification update
- **Symbols to add/change:** script/placeholder entry point.
- **Implementation shape:** If no validated operator-reader profile exists, script exits with a clear `unavailable` message and non-zero or documented unavailable status. It must not run project-reader fallback commands or service operations. If a validated operator-reader exists later, only list agents; no restart/enable/disable operations.
- **Validation:** `bash -n <script>`; static mutation grep; manually confirm unavailable behavior.
- **Stop condition:** Operator-level visibility is safely deferred rather than silently omitted or escalated.

#### Chunk 7: Static Safety Check
- **Goal:** Add a maintainer-runnable safety scanner for obvious unsafe script changes.
- **Files to change:**
  - proposed check script, for example `scripts/check_ai_ops_diagnostic_safety.sh` or Chunk 0 equivalent
  - documentation pointer in safety README
- **Symbols to add/change:** check script entry point.
- **Implementation shape:** Scan approved script source for forbidden OpenStack mutation verbs, service restarts, package installation, file mutation patterns, unrestricted sudo, shell `eval`, raw SSH forwarding, and generic command passthrough patterns. Include comments for known false positives and manual review.
- **Validation:** `bash -n <check-script>`; run check against approved script source; ensure it fails on a temporary or fixture unsafe pattern only if a safe fixture approach is selected.
- **Stop condition:** Maintainer can run one local command to flag obvious unsafe patterns.

#### Chunk 8: Runtime Evidence and Checklist Update
- **Goal:** Record actual Phase 03 validation without exposing secrets.
- **Files to change:**
  - `docs/ai-ops/runtime/phase03-diagnostic-toolbox-evidence-YYYY-MM-DD.md`
  - `docs/ai-ops/implementation-plan/03-safe-diagnostic-toolbox.md` checkboxes only for completed/evidenced tasks
- **Symbols to add/change:** not applicable.
- **Implementation shape:** Add redacted evidence for manual runtime runs and static checks. Do not include token values, credentials, unredacted profile files, or raw secret-bearing output.
- **Validation:** Review diff for secrets; verify evidence references exact scripts and outcomes.
- **Stop condition:** Phase 03 completion claims are backed by evidence and the working tree diff is reviewed.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Start Phase 03 Safe Diagnostic Toolbox from docs/ai-ops/implementation-plan/03-safe-diagnostic-toolbox.md using docs/ai-ops/implementation-plan/ads/03-safe-diagnostic-toolbox-ads.md as the design.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm repository evidence, script source location, runtime installation approach, and validation commands. Stop after summarizing evidence and uncertainties.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Execute Chunk 1 only.
Do not continue to Chunk 2.
After editing, run targeted validation and show git diff for the changed files only.
```

For later chunks:

```text
Use the chunked-implementation skill.
Execute only the next approved chunk from the ADS.
Keep changes to the listed files, run syntax/static validation for that chunk, review git diff, and stop before the following chunk.
```

### X. Conclusion and Next Steps

Phase 03 should begin with a safety policy and helper contracts, not with ad hoc OpenStack commands. The initial diagnostic toolbox should remain small, shell-based, fixed-command, project-reader by default, and manually validated on `assistant01`. The only operator-reader-related work in this phase should be a clear unavailable gate unless a separate validated operator-reader profile exists.

Next recommended action: run Chunk 0 discovery and confirm the repository source path for approved scripts before creating the safety README.
