## Architectural Design Specification: Revised Tool Runner Safety Gateway — Steps 1–4

**Source:** `docs/ai-ops-revised/implementation-plan/04-tool-runner-safety-gateway.md`, Steps 1 through 4; PRD requirements FR-022 through FR-029.

**Goal:** Establish the first executable half of the revised deny-by-default gateway: a strictly validated three-tool registry, a stable local named-tool request interface, fixed shell-free execution under the revised project-reader boundary, and deterministic timeout/process/output enforcement. Steps 5–7 (the final result-envelope contract, complete audit events, and full phase regression suite) remain explicitly out of scope.

---

### I. Overview and Contract

The capability is a local CLI boundary between an operator or future local client and the three Phase 03 diagnostics:

```text
local named-tool request
  -> load fixed adjacent registry
  -> validate complete registry or fail closed
  -> resolve exact registered tool
  -> validate declared parameters
  -> build trusted argv
  -> build minimal revised credential environment
  -> spawn one process group without a shell
  -> enforce timeout and bounded output
  -> return a minimal structured Steps 1–4 outcome
```

The gateway does not accept arbitrary executable, registry, profile, audit, working-directory, shell, SSH, sudo, OpenStack CLI, file, database, or remediation selections. It registers exactly:

1. `project_resource_summary`
2. `server_basic_info`
3. `server_network_info`

The trusted revised deployment boundary is concrete from Phase 01–03 evidence:

| Concern | Required value |
| --- | --- |
| Runtime root | `/opt/openstack-ai-ops-assistant` |
| Runner directory | `/opt/openstack-ai-ops-assistant/scripts/tool_runner` (proposed) |
| Approved implementation root | `/opt/openstack-ai-ops-assistant/scripts/approved` |
| Runtime user/group | `aiops_assistant:aiops_assistant` |
| Credential profile | `aiops-assistant-project-reader` |
| Profile configuration | `/opt/openstack-ai-ops-assistant/credentials/profiles/clouds.yaml` |
| Controlled working directory | `/opt/openstack-ai-ops-assistant` (proposed) |

#### Registry contract

**Module Contract (Conceptual):** a newly derived `tool_registry.json` is installed adjacent to the revised runner. It is not copied from the historical registry. The public CLI cannot override its location.

The registry root must use a versioned, closed schema. Proposed root fields are:

- `schema_version`: supported exact version;
- `registry_name`: revised identifier;
- `defaults`: bounded defaults permitted by the schema;
- `tools`: exactly three unique tool entries.

Each tool entry requires the plan-mandated fields:

- `name`
- `description`
- `implementation_target`
- `credential_profile`
- `risk_class`
- `timeout_seconds`
- `output_limit_bytes`
- `mutation_guarantee`
- `parameters`

Every object is closed: unknown root, defaults, tool, and parameter fields are rejected. Duplicate JSON keys must also be rejected rather than silently overwritten. Names are unique and map one-to-one to exact targets below:

| Tool | Exact target | Parameters |
| --- | --- | --- |
| `project_resource_summary` | `/opt/openstack-ai-ops-assistant/scripts/approved/project_resource_summary.sh` | none |
| `server_basic_info` | `/opt/openstack-ai-ops-assistant/scripts/approved/server_basic_info.sh` | required `server_identifier` |
| `server_network_info` | `/opt/openstack-ai-ops-assistant/scripts/approved/server_network_info.sh` | required `server_identifier` |

`server_identifier` follows the concrete Phase 03 contract: string, required, non-empty, no more than 255 bytes, ASCII `[A-Za-z0-9._:-]+`, no slash, and no `..`. The schema supports required/optional values, scalar types, patterns, integer ranges, bounded-time-window enums, and exact allowlists, but the initial three tools use only the constraints they need. Unsupported validators, inconsistent combinations, invalid bounds, booleans where integers are required, defaults that fail their own constraints, and duplicate parameter names/positions are startup errors.

The only accepted profile is `aiops-assistant-project-reader`; the only accepted mutation guarantee is the reviewed read-only guarantee selected in Chunk 0. Timeout and output limits must be positive integers within conservative global ceilings selected in Chunk 0. Registry targets must equal one of the three exact revised paths; lexical containment alone is insufficient.

#### Request interface contract

**Function Signature Contract (Conceptual):**

```text
parse_declared_args(raw_args: list[str]) -> dict[str, scalar]
validate_request(registry, tool_name, raw_args) -> ValidatedRequest
```

The initial local CLI is proposed as:

```text
aiops_tool_runner.py TOOL_NAME [--arg KEY=VALUE ...]
```

The implementation may choose JSON request input instead only if Chunk 0 finds an approved repository convention. In either form, callers can supply only a tool name and declared parameter values. Duplicate keys, malformed encoding, missing values, unknown tools, undeclared parameters, missing required parameters, wrong types, and invalid values fail before process creation.

Stable statuses are concrete from Step 2: `ok`, `error`, `denied`, `timeout`, `validation_error`, and `unavailable`. Truncation is metadata, not a seventh status. Proposed process exit codes are `0` for `ok`, and distinct non-zero codes for every other status; Chunk 0 must freeze the exact mapping before implementation. Denial and validation messages expose public tool/parameter facts only, never internal paths, registry contents, environment values, credentials, or profile details.

#### Execution contract

**Function Signature Contract (Conceptual):**

```text
build_command_argv(tool: ValidatedTool, parameters: dict[str, scalar]) -> list[str]
build_child_environment(tool: ValidatedTool) -> dict[str, str]
execute_bounded(request: ValidatedRequest) -> ExecutionOutcome
```

`build_command_argv` starts with the exact registry-validated target and appends only validated values in registry-defined positional order. There is no shell string, interpolation, executable override, path argument, generic passthrough, or fallback command.

`build_child_environment` constructs a new allowlist rather than copying `os.environ`. At minimum it supplies a fixed safe `PATH`, deterministic locale, `OS_CLIENT_CONFIG_FILE`, and `OS_CLOUD`. It omits inherited `OS_*` authentication values, tokens, passwords, application credentials, SSH agent variables, provider secrets, and unrelated process state. The runner does not read profile contents.

Before spawn, the target must still be the expected regular, executable, non-symlinked file under the exact revised approved-script root. Missing or unsafe runtime targets fail closed without fallback.

#### Timeout and output contract

**Function Signature Contract (Conceptual):**

```text
terminate_process_group(process, grace_seconds) -> CleanupOutcome
capture_bounded(process, timeout_seconds, output_limit_bytes) -> ExecutionOutcome
```

The child starts in a new process session/group. On timeout or runner interruption, the runner signals the complete child process group, waits a fixed short grace period, escalates to a hard kill when necessary, reaps the direct child, and reports `timeout` or `error` only after cleanup has been attempted and recorded in the in-memory outcome.

The implementation must stream bytes from stdout and stderr instead of allowing unbounded `subprocess.run(..., capture_output=True)` buffering. The proposed meaning of `output_limit_bytes` is one combined retained-byte budget across both streams; Chunk 0 must freeze deterministic allocation and truncation behavior. Once the retained budget is exhausted, both pipes are still drained/discarded so the child cannot deadlock. `truncated: true` is set whenever bytes are omitted. Decoding occurs after byte bounds; invalid UTF-8 is a structured `error`, not replacement-decoded success.

The runner validates the diagnostic JSON after execution. Successful empty findings remain `ok`. A child payload reporting `service_unavailable`, `catalog_missing`, or `connectivity_error` may map to runner status `unavailable`; malformed diagnostic JSON, interrupted reads, and unknown error classes fail closed as `error`. The exact mapping is proposed and must be frozen in the Steps 1–4 operations contract before executable behavior is added.

A minimal deterministic JSON outcome is required during these chunks so tests and the CLI can express status, tool, non-sensitive error reason, exit code when available, bounded stdout/stderr or parsed data, duration, and truncation. Step 5 remains responsible for freezing the complete public result envelope, schema version, timestamp, correlation ID, redaction behavior, and reviewed examples.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops-revised/implementation-plan/04-tool-runner-safety-gateway.md:51-134` requires registry fail-closed behavior, request denial, fixed argv/minimal environment, process-group cleanup, and output bounds.
- `docs/ai-ops-revised/prd.md:159-177` defines FR-022 through FR-031; this ADS covers FR-022 through FR-029 only, with final envelope details deferred to Step 5 and audit behavior deferred to Step 6.
- `docs/ai-ops-revised/runtime/manual-diagnostic-toolbox-operations-contract.md` fixes the three tool names, exact revised root/profile, server-identifier rules, diagnostic JSON behavior, and error classes.
- `ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox/defaults/main.yml` and `tasks/main.yml` deploy only the revised helper, three diagnostics, and acceptance consumer beneath `/opt/openstack-ai-ops-assistant/scripts/approved` as root-owned, non-symlinked files.
- `ansible/ai_ops_assistant/roles/ai_ops_assistant_foundation/defaults/main.yml` confirms Python 3, runtime user/group, root, audit directory, and restrictive workspace modes.
- `docs/ai-ops-revised/runtime/selective-reuse-manifest.md:41,54,98` selects only the historical runner candidate for Phase 04 review and explicitly requires a newly derived registry; the historical registry is reference-only.
- The historical `aiops_tool_runner.py` offers reviewable seams for registry loading, request validation, argv construction, execution, and output truncation, but it uses historical paths/profile names, accepts caller-selected registry/audit paths, incompletely validates schema, inherits the environment, and does not explicitly clean a child process group.
- The historical registry includes Phase 06 host and Neutron capabilities and `/opt/openstack-ai-ops` targets, so it cannot be copied or installed.
- Existing revised Python tests use the standard-library `unittest` convention under `ansible/ai_ops_assistant/tests/`.

#### Assumptions

1. **Proposed source layout:** the revised runner and registry will live under a new `ai_ops_assistant_tool_runner` role, following the existing one-role-per-boundary pattern. Chunk 0 must confirm exact paths.
2. **Standard-library implementation:** no third-party JSON-schema or process-management package is required; strict validation, duplicate-key rejection, bounded pipe reads, and process groups can use Python standard-library facilities.
3. **Local-only caller:** no network listener, MCP endpoint, or provider integration is introduced.
4. **Steps 1–4 interim output:** a minimal structured outcome is permissible, but it cannot be called the final Step 5 envelope.
5. **No complete audit yet:** Steps 1–4 must not claim FR-030/FR-031 or Phase 04 completion. If temporary test instrumentation records whether spawn occurred, it remains fixture-only and contains no secrets.

#### Open confirmations for Chunk 0

- Exact source/deployment filenames and whether the runner is installed executable or invoked through `/usr/bin/python3`.
- Exact registry schema version, closed-field sets, risk/mutation enum values, global timeout/output ceilings, and deterministic combined-stream allocation.
- Exact non-zero exit-code mapping and endpoint/error-class mapping.
- Exact minimal environment keys, locale, safe `PATH`, working directory, and process-termination grace period.
- Whether deployment belongs in the existing toolbox role or a dedicated tool-runner role.
- Repository-approved formatter/linter commands and the Python virtual environment to use before any Python executable or test is run.

### III. Required Technical Dependencies and Imports

The revised implementation should use Python 3 standard-library modules only. Exact imports are subject to Chunk 0 and implementation shape:

- `argparse` for the fixed local CLI;
- `json` with duplicate-key detection for registry/request/result parsing;
- `os`, `signal`, and `subprocess` for fixed environment, process groups, and child lifecycle;
- `selectors` (proposed) for bounded concurrent stdout/stderr draining;
- `time` for monotonic timeout/duration tracking;
- `dataclasses`, `enum`, `re`, `pathlib`, and typing helpers for internal validated contracts;
- `unittest`, `tempfile`, and controlled fixture executables for local tests.

Repository/deployment dependencies:

- the existing three Phase 03 revised diagnostics;
- existing `python3` package and `aiops_assistant` user/group;
- the existing project-reader profile path, used by name/path without content inspection;
- proposed new role-local runner, registry, and fixture/test files;
- no shell helper, `jsonschema`, SDK call, OpenStack API call from the runner, SSH, sudo, MCP, database, or network service dependency.

### IV. Step-by-Step Procedure / Execution Flow

1. Load only the fixed adjacent revised registry using UTF-8 and duplicate-key rejection.
2. Validate the entire closed registry before resolving any request. Reject the process startup on malformed shape, unknown fields, duplicates, unsupported schema/version, missing metadata, unsafe target/profile, invalid bounds, or any tool set other than the exact initial three.
3. Parse the fixed local CLI and convert declared values into typed request data. Do not expose registry, target, profile, environment, audit, or working-directory overrides.
4. Resolve the named tool. Return `denied` with non-sensitive public text if it is not registered or names a forbidden generic capability.
5. Validate all parameters and defaults. Return `validation_error` before target metadata inspection or child creation on malformed, missing, duplicate, unknown, wrong-type, out-of-range, pattern-invalid, or non-allowlisted input.
6. Revalidate the resolved implementation against the exact tool-to-path map and runtime filesystem constraints. Return `unavailable` for a missing approved implementation and `error` for an unsafe mismatch; never search `PATH` or another root.
7. Build argv from the trusted target plus only ordered validated values. Build a fresh minimal environment with the exact revised profile labels and fixed working directory.
8. Start the child with `shell=False`, closed unrelated file descriptors, byte-mode pipes, and a new process session/group.
9. Drain stdout and stderr concurrently into a deterministic bounded retained buffer while measuring monotonic elapsed time. Discard excess bytes while continuing to drain and mark truncation.
10. On deadline expiry or interruption, terminate the entire process group, escalate after the fixed grace interval, reap the child, close pipes, and return a non-zero structured outcome.
11. Decode retained bytes strictly and validate the diagnostic JSON/error class. Decoder or malformed-payload failures become bounded sanitized `error`; approved endpoint-unavailable classes become `unavailable` if the operations contract freezes that mapping.
12. Emit exactly one deterministic minimal JSON outcome and return the status-mapped process code. Do not claim final Step 5 envelope or Step 6 audit completion.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| --- | --- | --- | --- |
| Registry read | Missing, unreadable, oversized, invalid UTF-8, malformed JSON, or duplicate key | Stop startup; do not resolve or execute a tool; emit bounded generic failure | `error` / `ERR_RUNNER_REGISTRY_INVALID` (proposed) |
| Registry schema | Unknown field/version, duplicate tool/parameter, invalid validator/default/bound, or missing safety metadata | Reject the complete registry | `error` / `ERR_RUNNER_REGISTRY_SCHEMA` (proposed) |
| Registry boundary | Historical root/profile, non-approved target, symlink-capable target, extra/later-phase tool | Reject the complete registry; do not disclose offending internal value publicly | `error` / `ERR_RUNNER_REGISTRY_UNSAFE` (proposed) |
| CLI parsing | Malformed `KEY=VALUE`, duplicate argument, unsupported input form | Do not inspect or spawn target | `validation_error` |
| Tool resolution | Unknown or generic capability name | Deny before execution and report only public request name where safe | `denied` |
| Parameter validation | Missing, undeclared, wrong type, invalid pattern/range/allowlist/default | Do not create a child process | `validation_error` |
| Runtime target check | Approved target missing or non-executable | No fallback or `PATH` search | `unavailable` |
| Runtime target check | Target changed, escaped root, or is a symlink/non-regular file | Fail closed as integrity/safety error | `error` / `ERR_RUNNER_TARGET_UNSAFE` (proposed) |
| Environment | Required revised profile labels cannot be constructed | Do not spawn; never inherit parent credentials as fallback | `unavailable` or `error`, frozen in Chunk 0 |
| Spawn | OS/process creation failure | Return sanitized bounded failure; close opened descriptors | `error` |
| Capture | Child fills one or both pipes | Concurrently drain; retain only bounded bytes; mark omitted data | original outcome plus `truncated: true` |
| Timeout | Deadline reached with descendants running | TERM process group, grace wait, KILL group if needed, reap child | `timeout`, non-zero |
| Cleanup | Process group cannot be confirmed reaped | Return failure with generic cleanup marker; do not retry execution | `error` / `ERR_RUNNER_PROCESS_CLEANUP` (proposed) |
| Decode | Invalid UTF-8 or incomplete multibyte sequence after bounded capture | Do not replacement-decode as success | `error` / `ERR_RUNNER_OUTPUT_DECODE` (proposed) |
| Diagnostic payload | Invalid JSON, wrong tool/schema, unknown status/error class | Fail closed; retain only bounded sanitized context | `error` |
| Endpoint | Diagnostic reports approved unavailable endpoint class | Preserve no raw endpoint/catalog details; map per frozen contract | `unavailable` (proposed) |
| Runner interruption | SIGINT/SIGTERM while child active | Apply the same complete process-group cleanup, then exit non-zero | `error` / interrupted marker |

### VI. Security, Integrity, Idempotency, and Cleanup

- **Security:** Registry and implementation paths are fixed by installation, not caller input. The CLI exposes no generic command/path/profile/environment controls. `shell=False` is necessary but insufficient; argv, target, environment, working directory, and open descriptors are independently constrained.
- **Credential isolation:** Build a fresh environment. Never copy and then unset a partial list. Only fixed revised `OS_CLIENT_CONFIG_FILE` and `OS_CLOUD` values enter the child; profile content is never read, logged, returned, or checksummed by the runner.
- **Integrity:** Registry loading rejects duplicate keys and unknown fields. Tool-to-target mapping is exact. Pre-spawn checks reject symlinks and non-regular targets. Chunk 0 should decide whether descriptor-based execution or post-open inode checks are needed to reduce check/use races.
- **Output confidentiality:** Failure text is normalized and bounded. Registry internals, absolute paths, environment values, credentials, catalogs, and raw exception representations are not returned. Full redaction remains a Step 5/6 deliverable, so Steps 1–4 fixtures must not use real secrets.
- **Idempotency:** Requests are read-only by registry guarantee and Phase 03 script contract. A timeout or interrupted request is not automatically retried because the runner cannot assume a partially observed external read is safe to duplicate for all future tools.
- **Cleanup:** Every completion path closes pipes and reaps the direct child. Timeout/interruption cleans the process group with bounded TERM/KILL waits. No temporary output file is required; test fixtures use temporary directories cleaned by the test harness.
- **Activation boundary:** Deployment remains disabled by default until local tests, role assertions, and an explicitly authorized deployment step pass. No live OpenStack diagnostic is required to validate Steps 1–4 safety behavior.
- **Future compatibility:** MCP must later call this same validated runner contract. It must not duplicate registry parsing or execution in Phase 07.

### VII. Validation Strategy

Validation is local and fixture-driven for these steps. Before any Python test or executable is run, the implementation agent must obtain and activate the user-provided Python virtual environment as required by repository editing discipline.

- **Markdown/ADS structure:** `rtk grep -n '^### [IVX]' docs/ai-ops-revised/implementation-plan/ads/04-00-tool-runner-safety-gateway-steps-01-to-04-ads.md`
- **Python syntax:** `rtk <venv-python> -m py_compile <changed-python-files>`
- **Registry JSON syntax:** `rtk <venv-python> -m json.tool <revised-registry-file>`
- **Targeted tests:** `rtk <venv-python> -m unittest discover -s ansible/ai_ops_assistant/tests/tool_runner -p 'test_*.py'`
- **Formatter/linter:** use only the Chunk 0-confirmed repository formatter/linter; do not introduce a new dependency.
- **Symbol checks:** `rtk grep -Rni 'def load_registry\|def validate_request\|def build_command_argv\|def execute_bounded\|def terminate_process_group' <revised-runner-root>`
- **Forbidden behavior scan:** `rtk grep -RniE 'shell=True|os\.system|subprocess\.(call|check_call|check_output).*shell|/opt/openstack-ai-ops([^-a]|$)|operator-reader|restricted-ssh|neutron_agent|recent_(metadata|nova|neutron)_errors' <revised-runner-role> ansible/ai_ops_assistant/tests/tool_runner`
- **Shell/Ansible syntax when deployment files are introduced:** `rtk ansible-playbook --syntax-check -i ansible/ai_ops_assistant/inventories/local/local.yml <target-playbook>`
- **Ansible lint:** `rtk ansible-lint <changed-role-and-playbook-files>`
- **Diff integrity:** `rtk git diff --check`
- **Diff review:** `rtk git diff -- <changed-files>`

Targeted tests must prove externally visible behavior, including:

- malformed/duplicate/unknown-field registries fail before requests;
- historical roots/profiles and extra Phase 06 tools fail closed;
- unknown tools and generic capability names are denied without spawn;
- missing, duplicate, undeclared, unsafe, wrong-type, and overlong parameters fail without spawn;
- argv is an array with exactly one approved target and validated positions;
- child environment contains only the frozen allowlist and no canary parent secrets;
- shell use and caller-selected paths are impossible;
- fast success, non-zero child failure, unavailable target/endpoint, timeout, interruption, invalid UTF-8, and malformed diagnostic JSON are structured and non-zero where required;
- a fixture that forks a descendant leaves no child or descendant after timeout;
- noisy stdout and stderr remain within the byte contract, do not deadlock, and set truncation metadata deterministically.

A final Steps 1–4 review must verify that no checklist item for Step 5, Step 6, Step 7, or the full Phase 04 definition of done is marked complete from this work.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass.

#### Chunk 0: Discovery and Integration Confirmation
- **Goal:** Freeze unresolved Steps 1–4 contracts and exact revised source/deployment/test paths without editing or executing Python, Ansible, diagnostics, profiles, or OpenStack.
- **Files to read:** this ADS; Phase 04 plan; revised PRD FR-022–FR-029 and testing decisions; selective reuse manifest; Phase 03 toolbox contract/role/tests; foundation and identity defaults; historical runner, registry, and Phase 04 validator as reference only.
- **Commands:** bounded RTK-prefixed `find`, `grep`, and file reads; inspect repository formatter/test conventions and obtain the approved Python virtual-environment path for later chunks.
- **Evidence to confirm:** role ownership, fixed runner/registry paths, schema/enum/bound values, exit-code/error mapping, minimal environment, working directory, output-budget allocation, cleanup grace period, and deployment activation boundary.
- **Stop condition:** write a Chunk 0 handoff with decisions and blockers; do not edit files or continue to Chunk 1.

#### Chunk 1: Steps 1–4 Operations Contract
- **Goal:** Record the frozen registry, request, execution, process, output, status, and non-activation decisions before executable code.
- **Files to change:** proposed `docs/ai-ops-revised/runtime/tool-runner-safety-gateway-steps-01-to-04-operations-contract.md` only.
- **Symbols to add/change:** no executable symbols; exact schema tables, status/exit mapping, environment allowlist, output allocation, process cleanup algorithm, and historical-reuse decision.
- **Implementation shape:** documentation-only and fail-closed; explicitly defer final envelope, auditing, full regression, and live activation.
- **Validation:** required-section grep, historical-identifier scan, `rtk git diff --check`, and focused diff review.
- **Stop condition:** reviewers can answer every Chunk 0 open confirmation from one authoritative contract; stop before code.

#### Chunk 2: Strict Registry and Compile-Safe Runner Stub
- **Goal:** Add a newly authored three-tool registry and a Python runner module that validates startup completely but cannot execute diagnostics yet.
- **Files to change:** proposed role-local `files/scripts/tool_runner/tool_registry.json` and `aiops_tool_runner.py`.
- **Symbols to add/change:** proposed `RegistryError`, `load_registry`, closed-schema validators, internal validated registry/tool/parameter records, fixed path/profile constants, and `main`.
- **Implementation shape:** loader rejects duplicate/unknown/unsafe data and exact-tool-set drift. A valid named request returns an explicit non-zero `unavailable`/not-implemented outcome; it never spawns. This is compile-safe and cannot falsely report success.
- **Validation:** JSON parse, Python compile, direct loader smoke with valid and corrupted temporary registries only after approved venv activation, forbidden-identifier scan, and diff review.
- **Stop condition:** exact registry loads; every malformed/unsafe variant fails closed; no subprocess call exists.

#### Chunk 3: Request Validation and Denial Slice
- **Goal:** Make the local interface accept only registered names and schema-declared values while preserving the no-execution stub.
- **Files to change:** revised runner and proposed `ansible/ai_ops_assistant/tests/tool_runner/test_request_gateway.py`.
- **Symbols to add/change:** `parse_declared_args`, `validate_parameter_value`, `validate_request`, status-to-exit mapping, and spawn-canary fixtures.
- **Implementation shape:** unknown/generic tools return `denied`; malformed/duplicate/missing/unknown/wrong-type/unsafe arguments return `validation_error`; valid requests still return the explicit non-zero execution-unavailable stub.
- **Validation:** Python compile and targeted request tests with assertions that no fixture executable marker was created; forbidden behavior scan and diff review.
- **Stop condition:** Step 2 denial behavior is externally testable and no request path can start a child.

#### Chunk 4: One Fixed Shell-Free Success Path
- **Goal:** Execute only `project_resource_summary` through a fixed argv and minimal environment, proving the first end-to-end allowlisted path.
- **Files to change:** revised runner and proposed `ansible/ai_ops_assistant/tests/tool_runner/test_execution_gateway.py`.
- **Symbols to add/change:** `build_command_argv`, `build_child_environment`, runtime target validation, and a narrow execution stub for the no-argument tool.
- **Implementation shape:** create the callee helpers before wiring the caller; use a controlled fixture target mapped through an internal test seam, never a public CLI path override. Server tools remain explicit non-zero `unavailable`. Use `shell=False`, fixed cwd, closed descriptors, and a fresh environment.
- **Validation:** Python compile; targeted tests inspect argv/environment canaries and prove parent secret canaries, shell strings, historical paths, and executable overrides do not reach the child; diff review.
- **Stop condition:** one registered tool completes through the safe path; the two parameterized tools remain safely unavailable.

#### Chunk 5: Parameterized Fixed Execution Slice
- **Goal:** Wire `server_basic_info` and `server_network_info` through the same fixed execution path with exactly one validated identifier.
- **Files to change:** revised runner and execution test file.
- **Symbols to add/change:** registry-position argv assembly and parameterized execution cases.
- **Implementation shape:** append only validated `server_identifier`; no flags, extra values, profile overrides, paths, or command fragments. Preserve all Chunk 3 pre-spawn rejection behavior.
- **Validation:** targeted valid/boundary/injection tests, argv exactness assertions, no-spawn markers for invalid values, Python compile, and diff review.
- **Stop condition:** all three registered tools have one safe execution path; no timeout/output behavior is added yet beyond a safe temporary hard limit frozen in the contract.

#### Chunk 6: Bounded Output and Complete Process-Group Cleanup
- **Goal:** Replace temporary execution with concurrent bounded capture, deadline enforcement, interruption cleanup, and structured endpoint/decode failures.
- **Files to change:** revised runner and proposed `ansible/ai_ops_assistant/tests/tool_runner/test_process_bounds.py`.
- **Symbols to add/change:** `capture_bounded`, `terminate_process_group`, stream-budget helper, strict decode/payload validation, timeout and truncation outcome fields.
- **Implementation shape:** start a new session; concurrently drain both pipes; retain only the frozen byte budget; TERM/grace/KILL/reap the process group on timeout/interruption; map failures without fallback. Called helpers are introduced before replacing the earlier narrow call site.
- **Validation:** fast/noisy/slow/forking/invalid-byte/malformed-JSON fixtures; process-table or PID-liveness assertions for no orphan; byte-count assertions; Python compile and diff review.
- **Stop condition:** Step 4 behavior is deterministic under all controlled fixtures and no orphan remains after the test suite.

#### Chunk 7: Disabled-by-Default Deployment Slice
- **Goal:** Materialize the validated runner/registry under the revised root without activating live diagnostic execution.
- **Files to change:** proposed dedicated role `defaults/main.yml` and `tasks/main.yml` (or exact Chunk 0-approved existing-role equivalents).
- **Symbols to add/change:** enable flag, exact runtime/runner/registry/target/profile values, source allowlist, owner/group/mode assertions, and non-symlink checks.
- **Implementation shape:** assert revised-only constants before copy; root owns runner/registry, runtime group receives only required read/execute access; default remains disabled. Do not deploy historical registry, tests, host tools, MCP, or audit behavior.
- **Validation:** YAML/Ansible syntax, `ansible-lint`, check-mode-safe role validation where available, path/mode assertions, historical-identifier scan, and diff review.
- **Stop condition:** deployment contract is syntax-valid and fail-closed while disabled; no live host run occurs.

#### Chunk 8: Steps 1–4 Integration Gate and Reconciliation
- **Goal:** Add one local integration entrypoint that proves the Steps 1–4 contract with fixtures and reconcile only evidence-backed Steps 1–4 checklist items.
- **Files to change:** proposed focused local test/validation entrypoint and `04-tool-runner-safety-gateway.md`; use a second session if the exact files exceed the 1–2 file rule.
- **Symbols to add/change:** exact three-tool assertion, registry corruption cases, spawn denial marker, environment canary, timeout descendant, dual-stream noise, and deterministic status/exit checks.
- **Implementation shape:** no live OpenStack, profile read, host connection, MCP, audit-completion claim, or final envelope claim. Checklist edits follow passing evidence and final diff review only.
- **Validation:** all Steps 1–4 targeted tests; Python/JSON syntax; Ansible syntax/lint if deployment files exist; forbidden-capability scan; `rtk git diff --check`; complete changed-file diff review.
- **Stop condition:** Steps 1–4 are either evidence-backed complete or explicitly blocked. Stop before Step 5 and do not mark the Phase 04 definition of done complete.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.
Activate rtk-command-prefix for shell commands.

Task:
Phase 04 Tool Runner Safety Gateway, Steps 1–4, from docs/ai-ops-revised/implementation-plan/ads/04-00-tool-runner-safety-gateway-steps-01-to-04-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files. Do not run Python, Ansible, diagnostics, profiles, or OpenStack. Confirm repository evidence, exact contracts, the approved Python virtual environment, and blockers; write a handoff and stop.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.
Activate rtk-command-prefix for shell commands.

Task:
Phase 04 Tool Runner Safety Gateway, Steps 1–4.

Mode:
Execute Chunk 1 only from docs/ai-ops-revised/implementation-plan/ads/04-00-tool-runner-safety-gateway-steps-01-to-04-ads.md.
Do not continue to Chunk 2. Change only the approved operations-contract file. Run targeted documentation validation, show git diff, write a handoff, and stop.
```

### X. Conclusion and Next Steps

This ADS designs a narrow revised gateway around the three already approved Phase 03 diagnostics. It deliberately rejects the unsafe parts of the historical runtime: historical roots and profiles, caller-selected registry/audit paths, extra Phase 06 tools, inherited environments, unbounded capture, and incomplete process cleanup.

The next action is Chunk 0 discovery only. Implementation must then proceed contract-first and one compile-safe vertical slice at a time. Completion of these chunks does not complete Phase 04: the final result envelope, redaction, complete auditing, full safety regression scope, live evidence, and phase-level checklist remain owned by Steps 5–7 and separately authorized work.
