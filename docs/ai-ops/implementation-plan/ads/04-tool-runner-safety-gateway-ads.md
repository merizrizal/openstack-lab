## Architectural Design Specification: AI-OPS Tool Runner Safety Gateway

**Source:** `docs/ai-ops/implementation-plan/04-tool-runner-safety-gateway.md`

**Goal:** Add a local deny-by-default tool runner that maps named diagnostic requests to allowlisted Phase 03 scripts, validates parameters before execution, runs fixed scripts through argument vectors with time and output bounds, emits structured JSON result envelopes, and writes sanitized audit events for allowed and denied requests.

---

### I. Overview and Contract

Phase 04 places a safety gateway between an operator or future AI client and the reviewed Phase 03 diagnostic scripts. The gateway is not a general shell, OpenStack CLI, SSH, sudo, file, database, or remediation interface. It must expose only diagnostic intent names from a reviewed registry.

Target execution path:

```text
allowlist config
  -> validated tool request
  -> fixed script execution by argv
  -> structured result envelope
  -> sanitized audit event
  -> denied unknown/unsafe requests
```

#### Runtime Script Boundary Contract (Concrete)

Observed Phase 03 approved scripts are repository-managed under:

```text
ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved/
```

Observed runtime install target from `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/scripts.yml` is:

```text
/opt/openstack-ai-ops/scripts/approved/
```

The initial allowlist should target only these fixed approved scripts:

- `project_resource_summary.sh`
- `server_basic_info.sh`
- `server_network_info.sh`
- `neutron_agent_health.sh` as unavailable until a validated non-default operator-reader profile exists

#### Tool Registry Contract (Conceptual, to confirm in Chunk 0)

The Phase 04 plan permits a reviewed configuration file or equivalent registry. Because repository discovery found no YAML parser dependency and only `requirements.txt` with Ansible/OpenStack-related packages, the preferred MVP registry format is JSON or a Python stdlib data structure.

A registry entry should declare:

- public tool name
- human-readable diagnostic description
- fixed implementation target path
- credential profile classification
- risk level
- availability state and unavailable reason, when applicable
- timeout seconds
- output limit bytes
- argument schema
- mutation guarantee

Proposed initial public tool names:

- `project_resource_summary`
- `server_basic_info`
- `server_network_info`
- `neutron_agent_health` with `available=false`

The registry must explicitly omit generic shell, SSH, sudo, raw OpenStack CLI passthrough, file read/write, database, RabbitMQ, restart, package, and remediation tools.

#### Request Contract (Conceptual)

A local CLI request should provide:

- tool name
- declared arguments only
- optional actor/client label for audit
- optional request ID/correlation ID if supplied by caller

The exact CLI syntax is not confirmed. A reasonable MVP shape is one command that accepts a tool name plus explicit key/value or JSON arguments. The runner must reject unknown argument names rather than passing them through.

#### Result Envelope Contract (Conceptual)

Each runner invocation should print one machine-readable JSON envelope containing:

- `tool`
- `status`: `ok`, `error`, `denied`, `validation_error`, `timeout`, `unavailable`, or `truncated`
- `arguments`: sanitized argument object
- `exit_code`: script exit code when applicable
- `stdout`: bounded stdout text
- `stderr`: bounded stderr text or error message
- `duration_ms`
- `truncated`: boolean
- `timestamp`
- `request_id` or correlation identifier when available

#### Audit Event Contract (Conceptual)

Each request outcome should append one sanitized JSON Lines event under the runtime audit workspace, proposed:

```text
/opt/openstack-ai-ops/audit/tool-runner.jsonl
```

Each event should include timestamp, actor/client identifier when available, requested tool name, sanitized arguments, status, duration when executed, exit code when applicable, denial/failure reason when applicable, and request ID if available.

Audit events must not include credential file contents, tokens, passwords, private keys, raw profile contents, or secret-like argument values.

#### Function Signature Contracts

**Function Signature Contract (Conceptual):** exact Python module path and function names must be confirmed in Chunk 0. Proposed contracts for a Python stdlib implementation:

```text
load_registry(path) -> registry mapping
validate_request(registry, tool_name, raw_args) -> validated request or validation error
run_tool(validated_request, timeout_seconds, output_limit_bytes) -> execution result
build_result_envelope(request, execution_result) -> JSON-serializable dict
write_audit_event(audit_path, event) -> None
main(argv) -> process exit code
```

Stub behavior should fail closed. Early stubs may return explicit `unavailable` or `denied` envelopes rather than success. Returning success before execution is implemented would be unsafe because it could make callers believe a diagnostic actually ran.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops/implementation-plan/04-tool-runner-safety-gateway.md` defines the Phase 04 target as allowlist config, validated request, fixed script execution, structured result, audit event, and denied unsafe requests.
- The Phase 04 plan includes registry design, local CLI runner, validation, argument-vector execution, timeouts, output limits, structured envelopes, audit logging, and safety tests.
- The Phase 04 plan excludes MCP server, chat UI/bot integration, SSH host diagnostics unless safely implemented, automatic remediation, and generic command passthrough.
- `docs/ai-ops/implementation-plan/00-implementation-overview.md` places Phase 04 after the safe diagnostic toolbox and before manual AI-OPS workflows.
- The overview states cross-phase principles: no generic shell/SSH/sudo/OpenStack CLI/file-write/database/restart/remediation tool, deny-by-default diagnostics, narrow parameters, structured results, auditability, and least-privileged credentials.
- `docs/ai-ops/prd.md` FR-022 through FR-031 require an allowlist, rejection of unknown tools, rejection of generic unsafe capabilities, parameter validation, argument-vector execution, timeouts, output-size limits, structured envelopes, and audit for allowed and denied requests.
- `docs/ai-ops/prd.md` NFR-004 through NFR-010 require no secrets in logs/results, fail-safe structured states, clear unavailable diagnostics, auditable calls, intent-based tool names, concise outputs, and one consistent model for new diagnostics.
- `docs/ai-ops/prd.md` defines tool registry, result, and audit event contracts.
- `docs/ai-ops/prd.md` AC-009 through AC-016 match the Phase 04 definition of done.
- `docs/ai-ops/runtime/README.md` defines `/opt/openstack-ai-ops/audit/` as future tool-runner audit events and says `/opt/openstack-ai-ops/mcp/` remains inactive until trusted scripts and runner exist.
- `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved/README.md` defines the Phase 03 approved script safety policy and default credential profile.
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/scripts.yml` installs approved scripts to `/opt/openstack-ai-ops/scripts/approved/` with executable modes for the scripts.
- `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml` defines runtime root `/opt/openstack-ai-ops`, runtime user/group `assistant`, OpenStack profile name `aiops-project-reader`, and workspace directories including `audit` and `mcp`.
- Current repository discovery found no existing Python package, pytest config, or test tree at shallow depth. Only `requirements.txt` exists and does not list a YAML parser.
- Current branch observed while creating this ADS: `main...origin/main`.

#### Assumptions

- Phase 03 scripts are already trusted for MVP diagnostic scope and remain the only script execution targets for Phase 04.
- Python is the preferred runner language for MVP because the plan says Python is preferred if OpenStack SDK migration is likely, and runtime dependencies already include Python 3.
- The MVP can use only Python standard library features for CLI parsing, JSON, subprocess execution, timeouts, file appends, and tests.
- A JSON registry is preferable to YAML for the first slice unless maintainers add or confirm a YAML parser dependency.
- The initial runner should be local-only and manually invoked; no MCP or network server is introduced in Phase 04.
- The future implementation must decide exact source paths for runner files during Chunk 0. Proposed paths in this ADS are implementation guidance, not observed facts.

### III. Required Technical Dependencies and Imports

#### Runtime dependencies

- `assistant01` AI-OPS runtime.
- `/opt/openstack-ai-ops/scripts/approved/` containing Phase 03 approved scripts.
- `/opt/openstack-ai-ops/audit/` writable by the runtime user.
- Python 3 available on the assistant runtime.
- Default Phase 02/03 `aiops-project-reader` profile for project-reader scripts.
- No admin OpenStack credentials, root SSH, unrestricted sudo, database, RabbitMQ, or remediation authority.

#### Proposed Python standard-library dependencies

Implementation can stay in Python stdlib:

- `argparse` for CLI parsing
- `json` for registry, result envelopes, and JSON Lines audit events
- `subprocess` for argument-vector script execution
- `datetime` or `time` for timestamps and durations
- `pathlib` for path handling
- `os` for environment handling if needed
- `uuid` for request/correlation IDs if generated locally
- `unittest` and `tempfile` for safety tests and fixtures

#### Proposed repository source paths, subject to Chunk 0 confirmation

- runner source: `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py`
- registry source: `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/tool_registry.json`
- tests: `tests/ai_ops/test_tool_runner.py`
- install task changes: `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/scripts.yml`
- optional Phase 04 runtime validation playbook: `ansible/ai_ops_runtime/playbook_validate_phase04_tool_runner_safety_gateway.yml`

No new external service, SDK integration, MCP server, host SSH diagnostic path, sudo rule, database credential, or OpenStack write-capable credential is required.

### IV. Step-by-Step Procedure / Execution Flow

1. Confirm implementation paths and current repository conventions.
   - Verify whether maintainers prefer runner code under the Ansible role static files, top-level `scripts/`, or another path.
   - Confirm test convention; if none exists, create minimal stdlib `unittest` tests rather than requiring pytest.
2. Define the registry contract.
   - Add a reviewed registry for only Phase 03 diagnostic tools.
   - Mark unavailable tools explicitly instead of omitting safety rationale.
   - Reject any generic or unsafe tool category by absence and by tests.
3. Add CLI runner stubs.
   - The runner loads registry and emits structured JSON for fail-closed paths.
   - Unknown tools return `denied` and non-zero status.
   - Unavailable tools return `unavailable` and non-zero status.
4. Implement validation.
   - Validate required/optional arguments by registry schema.
   - Reject unknown arguments.
   - Use conservative identifier patterns matching Phase 03 script policy for server identifiers.
   - Validate before opening a subprocess.
5. Implement fixed script execution.
   - Resolve tool name to exactly one configured script target.
   - Execute with `subprocess.run` or equivalent using an argv list and `shell=False`.
   - Pass only validated arguments in the order declared by the registry.
6. Add timeout and output limits.
   - Use per-tool timeout from registry.
   - Terminate timed-out scripts and return a structured `timeout` status.
   - Bound stdout/stderr and set truncation metadata when output exceeds configured limits.
7. Add structured result envelopes.
   - Emit stable JSON for success, failure, denied, validation error, unavailable, timeout, and truncation cases.
   - Preserve script exit code and bounded stderr for operator diagnosis.
8. Add audit logging.
   - Append one sanitized JSON Lines event for every request outcome.
   - Ensure denied and validation-error outcomes are audited even when no script runs.
   - Do not log secret-like values or credential material.
9. Install runner into the runtime through Ansible.
   - Create a runtime tool-runner directory or agreed location.
   - Copy runner and registry with safe ownership/mode.
   - Keep approved scripts in their existing approved directory.
10. Add safety-focused tests.
    - Unit-test registry rejection, validation, unavailable tools, argv execution, timeout, output truncation, and audit events using controlled fixtures.
    - Do not require a live OpenStack deployment for core safety regression tests.
11. Record Phase 04 evidence only after actual runtime validation.
    - Runtime evidence should include command outcomes and audit event shape, not secrets or raw credential files.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| ----- | ------------ | ------------------- | ----------------------- |
| Registry load | Registry file missing, malformed, or unreadable | Fail closed before executing any script | `ERR_AI_OPS_REGISTRY_UNAVAILABLE` (proposed); result `error` |
| Registry contents | Tool maps to a path outside approved/runtime runner policy | Reject registry during validation or startup | `ERR_AI_OPS_UNSAFE_TOOL_TARGET` (proposed); no execution |
| Tool lookup | Requested tool is not in the allowlist | Deny, audit, print structured envelope, return non-zero | result `denied` |
| Capability boundary | Registry includes generic shell, SSH, sudo, OpenStack passthrough, file/database/remediation tool | Test and review must fail; remove tool | `ERR_AI_OPS_FORBIDDEN_CAPABILITY` (proposed) |
| Availability | Tool is registered but marked unavailable | Do not execute script; audit unavailable outcome | result `unavailable` |
| Argument parsing | Unknown argument name is supplied | Reject before validation/execution | result `validation_error` |
| Required arguments | Required server identifier is missing | Reject before execution | result `validation_error` |
| Pattern validation | Identifier contains whitespace, shell metacharacter, path separator, or expansion syntax | Reject before execution | result `validation_error` |
| Execution | Script target missing or not executable | Return structured execution error and audit | result `error` |
| Execution safety | Runner uses shell string execution | Tests must fail; implementation is blocked | `ERR_AI_OPS_SHELL_EXECUTION` (proposed) |
| Timeout | Script exceeds configured timeout | Terminate process, return timeout status, audit | result `timeout` |
| Output bound | stdout/stderr exceeds configured size | Truncate deterministically, set metadata, audit truncation | result `truncated` or result with `truncated=true` |
| Script failure | Approved script exits non-zero | Preserve bounded stderr/stdout and exit code | result `error` or script-specific unavailable |
| Audit write | Audit path missing or not writable | Return structured error; do not silently skip audit for executed requests | `ERR_AI_OPS_AUDIT_WRITE_FAILED` (proposed) |
| Secret handling | Argument/result/audit contains token, password, private key, or profile content | Redact or omit; treat confirmed exposure as a safety incident | `ERR_AI_OPS_SECRET_EXPOSURE` (proposed) |
| Runtime install | Runner not copied to expected runtime path | Validation playbook fails path check | Phase 04 runtime validation blocked |
| MCP pressure | Caller expects network/MCP integration in Phase 04 | Reject as out of scope; keep local CLI only | MCP deferred to Phase 07 |

### VI. Security, Integrity, Idempotency, and Cleanup

- Deny by default: no tool is callable unless explicitly present in the registry.
- The registry must be intent-based. Tool names describe diagnostics, not command strings.
- The runner must not accept arbitrary executable paths, subcommands, command fragments, shell strings, environment overrides, working directories, or file paths from the caller.
- Execution must use an argument vector with shell execution disabled.
- Parameter validation must happen before subprocess creation.
- The runner must not add OpenStack authority. It only invokes reviewed Phase 03 scripts that use the established credential policy.
- Unknown, invalid, unavailable, timed-out, and failed requests must return non-zero process status.
- Audit logging must cover both executed and denied requests.
- Audit/result sanitization must omit or redact secret-like values. Do not log credential files, tokens, passwords, private keys, or raw profile material.
- Output bounds protect human review, AI context size, and audit safety. Truncation must be explicit.
- Idempotency expectation: repeated runner calls may append audit events but must not mutate OpenStack resources or lab hosts.
- Cleanup expectation: timed-out child processes must be terminated. No temporary files are required for the MVP unless tests create fixtures.
- If an implementation accidentally adds generic execution or mutation-capable tools, stop and remove the capability before continuing.

### VII. Validation Strategy

Validation must be chunk-aware and stop after each slice.

#### Static and syntax validation

- Python syntax: `python3 -m py_compile <runner-file>`.
- JSON registry syntax: `python3 -m json.tool <registry-file> >/dev/null`.
- Unit tests: `python3 -m unittest discover -s tests -p 'test_tool_runner.py'` after tests exist.
- Ansible syntax for installation/validation playbooks when changed: `ansible-playbook --syntax-check <playbook.yml>` with required inventory/vars if the repository convention requires them.
- Diff review: `git diff -- <changed-files>` after every chunk.

#### Safety validation

- Verify no call path uses `shell=True` or command strings.
- Verify unknown tools are denied and audited.
- Verify invalid/unsafe parameters are rejected before any fixture script is executed.
- Verify no registry entry exposes forbidden generic capabilities.
- Verify `neutron_agent_health` remains unavailable unless a validated non-default operator-reader profile exists.
- Verify audit and result payloads do not include obvious secret keys or credential file contents.

#### Runtime smoke validation

After the runner is installed on `assistant01`:

- Run an allowlisted no-argument tool such as `project_resource_summary` through the runner.
- Run `server_basic_info` with a safe known server identifier when available.
- Run an unknown tool and confirm `denied` status plus audit event.
- Run unsafe identifier input and confirm `validation_error` before script execution.
- Run `neutron_agent_health` and confirm structured `unavailable`.
- Confirm audit JSON Lines events are created under `/opt/openstack-ai-ops/audit/` and contain no secrets.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass.

#### Chunk 0: Discovery and Integration Confirmation
- **Goal:** Confirm exact runner source path, runtime install path, registry format, test convention, and whether Ansible should install the runner in Phase 04.
- **Files to read:**
  - `docs/ai-ops/implementation-plan/04-tool-runner-safety-gateway.md`
  - `docs/ai-ops/implementation-plan/ads/04-tool-runner-safety-gateway-ads.md`
  - `docs/ai-ops/implementation-plan/ads/03-safe-diagnostic-toolbox-ads.md`
  - `docs/ai-ops/runtime/README.md`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/scripts.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved/README.md`
  - candidate test and script directories discovered with `find`
- **Commands:**
  - inspect branch/status
  - discover Python/test files and role static files
  - search for existing runner/registry/audit terms
- **Evidence to confirm:**
  - selected source path for runner and registry
  - selected runtime path for runner and registry
  - whether JSON registry is accepted for MVP
  - available local test style
  - target audit file path
- **Stop condition:** Evidence is summarized; no files edited.

#### Chunk 1: Registry Contract and Initial Allowlist
- **Goal:** Add the reviewed allowlist before adding executable runner behavior.
- **Files to change:**
  - proposed `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/tool_registry.json`
  - optional adjacent `README.md` if maintainers want registry policy documented near the file
- **Symbols to add/change:** Registry entries for `project_resource_summary`, `server_basic_info`, `server_network_info`, and unavailable `neutron_agent_health`.
- **Implementation shape:** Use JSON with fixed script target names/paths, argument schemas, timeout seconds, output byte limits, credential profile classification, risk level, availability state, and mutation guarantee. Do not include generic unsafe capabilities.
- **Validation:** `python3 -m json.tool <registry-file> >/dev/null`; inspect `git diff -- <registry-file>`.
- **Stop condition:** Registry is parseable and reviewable; no runner code exists yet.

#### Chunk 2: CLI Runner Stub and Envelope Shape
- **Goal:** Add a compile-safe local CLI stub that loads the registry and emits fail-closed JSON envelopes without executing scripts.
- **Files to change:**
  - proposed `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py`
  - proposed `tests/ai_ops/test_tool_runner.py`
- **Symbols to add/change:**
  - conceptual `load_registry`
  - conceptual `build_result_envelope`
  - conceptual `main`
- **Implementation shape:** Parse minimal CLI arguments, load registry, and return structured `denied` for unknown tools and `unavailable` for unavailable tools. For available tools, return an explicit temporary `error` such as `execution not implemented` rather than success. Add unit tests for JSON envelope shape and unknown-tool denial.
- **Validation:** `python3 -m py_compile <runner-file>`; `python3 -m unittest discover -s tests -p 'test_tool_runner.py'`.
- **Stop condition:** Runner/test compile and fail closed; no subprocess execution is implemented.

#### Chunk 3: Argument Validation Slice
- **Goal:** Validate declared arguments and reject unsafe input before any execution path exists.
- **Files to change:**
  - runner file
  - `tests/ai_ops/test_tool_runner.py`
- **Symbols to add/change:**
  - conceptual `validate_request`
  - conceptual validation helpers for required strings, safe identifier pattern, optional default, and bounded time window if needed by initial registry
- **Implementation shape:** Enforce required/optional args from registry, reject unknown args, reject unsafe identifiers using the Phase 03 conservative pattern, and produce `validation_error` envelopes. Keep execution stubbed with explicit not-implemented error for valid requests.
- **Validation:** `python3 -m py_compile <runner-file>`; `python3 -m unittest discover -s tests -p 'test_tool_runner.py'`.
- **Stop condition:** Tests prove invalid parameters are denied before any subprocess helper is reachable.

#### Chunk 4: Fixed Argv Execution, Timeout, and Output Limits
- **Goal:** Implement the first real execution path safely.
- **Files to change:**
  - runner file
  - `tests/ai_ops/test_tool_runner.py`
- **Symbols to add/change:**
  - conceptual `run_tool`
  - conceptual output truncation helper
  - conceptual timeout handling path
- **Implementation shape:** Resolve tool name to exactly one configured script target. Execute with an argv list and shell disabled. Pass only validated arguments in registry-declared order. Apply per-tool timeout. Bound stdout/stderr and set truncation metadata. Use controlled test fixture scripts or temporary test files; do not require live OpenStack.
- **Validation:** `python3 -m py_compile <runner-file>`; `python3 -m unittest discover -s tests -p 'test_tool_runner.py'`; grep/diff review confirming no `shell=True`.
- **Stop condition:** One no-argument fixture and one single-argument fixture execute by argv, timeout/truncation tests pass, and no generic command path exists.

#### Chunk 5: Audit Logging for All Outcomes
- **Goal:** Append sanitized audit events for allowed, denied, validation-error, unavailable, timeout, truncated, and execution-error outcomes.
- **Files to change:**
  - runner file
  - `tests/ai_ops/test_tool_runner.py`
- **Symbols to add/change:**
  - conceptual `write_audit_event`
  - conceptual `sanitize_arguments`
  - optional request ID generation
- **Implementation shape:** Write JSON Lines audit events to a configurable path with default runtime audit path. Unit tests use a temporary audit file. Ensure denied/validation paths audit even when no script runs. Redact or omit secret-like argument names and values.
- **Validation:** `python3 -m py_compile <runner-file>`; `python3 -m unittest discover -s tests -p 'test_tool_runner.py'`.
- **Stop condition:** Tests verify all major outcomes create sanitized audit events.

#### Chunk 6: Runtime Installation Wiring
- **Goal:** Install the runner and registry to the assistant runtime without changing approved script behavior.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/scripts.yml`
  - optionally `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml` if new runtime paths or modes need variables
- **Symbols to add/change:** Ansible tasks/vars for creating the tool-runner directory and copying runner/registry files.
- **Implementation shape:** Create a runtime tool-runner directory under the agreed `/opt/openstack-ai-ops/scripts/` area. Copy runner with executable mode only if intended as a CLI entrypoint; copy registry read-only. Do not alter Phase 03 approved scripts except as needed for path references.
- **Validation:** `ansible-playbook --syntax-check ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml` using the repository's inventory/vars convention; `git diff -- <changed-files>`.
- **Stop condition:** Ansible syntax validation passes or a concrete inventory/vars blocker is reported; runner behavior code is not changed in this chunk.

#### Chunk 7: Phase 04 Runtime Validation and Evidence Path
- **Goal:** Add or document a repeatable validation path for the complete safety gateway.
- **Files to change:**
  - proposed `ansible/ai_ops_runtime/playbook_validate_phase04_tool_runner_safety_gateway.yml` or a documented validation note if maintainers prefer manual commands first
  - optional `docs/ai-ops/runtime/phase04-tool-runner-safety-gateway-evidence-YYYY-MM-DD.md` only after actual runtime execution
- **Symbols to add/change:** Ansible validation tasks or documented checks for allowed, denied, validation-error, unavailable, timeout/truncation fixture, and audit outcomes.
- **Implementation shape:** Validate installed runner paths, registry parseability, unknown tool denial, unsafe parameter rejection, unavailable Neutron gate, one safe approved script path, and audit event creation. Evidence must not include secrets or raw profile files.
- **Validation:** `ansible-playbook --syntax-check <phase04-validation-playbook>` when a playbook is added; review diff for secret-like content.
- **Stop condition:** Validation path is available and Phase 04 completion claims are not made until runtime evidence exists.

#### Chunk 8: Checklist, Safety Review, and Final Diff
- **Goal:** Mark Phase 04 tasks complete only after behavior and evidence exist.
- **Files to change:**
  - `docs/ai-ops/implementation-plan/04-tool-runner-safety-gateway.md`
  - runtime evidence document, if produced in Chunk 7
- **Symbols to add/change:** not applicable.
- **Implementation shape:** Update checkboxes only for verified tasks. Include references to tests, validation playbook, and redacted runtime evidence. Do not include secrets or live credential contents.
- **Validation:** `git diff -- docs/ai-ops/implementation-plan/04-tool-runner-safety-gateway.md docs/ai-ops/runtime/`; run final targeted unit tests and Ansible syntax checks relevant to changed files.
- **Stop condition:** Phase 04 status is evidence-backed, diff reviewed, and next phase is not started.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Start Phase 04 Tool Runner Safety Gateway from docs/ai-ops/implementation-plan/04-tool-runner-safety-gateway.md using docs/ai-ops/implementation-plan/ads/04-tool-runner-safety-gateway-ads.md as the design.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm repository evidence, selected runner source path, registry format, runtime install path, audit path, and validation commands. Stop after summarizing evidence and uncertainties.
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
Keep changes to the listed files, run syntax/static/unit validation for that chunk, review git diff, and stop before the following chunk.
```

### X. Conclusion and Next Steps

Phase 04 should begin with a reviewed allowlist and fail-closed runner contracts, then add validation, execution, bounds, audit, and runtime installation one slice at a time. The gateway must remain local-only for this phase and must not become a generic command execution service.

Next recommended action: execute Chunk 0 discovery to confirm exact runner/registry source paths and local test convention before creating the registry file.
