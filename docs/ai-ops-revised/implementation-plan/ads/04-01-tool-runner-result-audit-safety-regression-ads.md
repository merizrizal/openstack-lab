## Architectural Design Specification: Revised Tool Runner Results, Auditing, and Safety Regression

**Source:** `docs/ai-ops-revised/implementation-plan/04-tool-runner-safety-gateway.md`, Steps 5–7

**Goal:** Complete the revised deny-by-default tool-runner contract with deterministic redacted result envelopes, complete sanitized audit events, and fixture-driven safety regression coverage without enabling live deployment or adding MCP, host diagnostics, or remediation behavior.

---

### I. Overview and Contract

Steps 5–7 extend the existing Steps 1–4 execution boundary rather than creating a second runner path:

```text
local named request
-> strict registry and request validation
-> fixed shell-free bounded execution when approved
-> normalize one terminal outcome
-> recursively redact public result content
-> build one deterministic result envelope
-> build and securely append one minimal audit event
-> emit exactly one JSON result and return the status exit code
```

The same terminal-outcome path must handle registry failure, denied capability, validation failure, unavailable target/service, child failure, timeout, truncation, interruption, and success. No branch may bypass redaction or audit construction.

#### Result-envelope contract

**Data Contract (Conceptual):** exact field names and schema version must be frozen in Chunk 0/1 before implementation.

The proposed closed top-level result object contains exactly:

| Field | Type | Contract |
| --- | --- | --- |
| `schema_version` | string | Proposed `1.0`; exact value frozen in the operations contract. |
| `tool` | string | Bounded sanitized public tool name; malformed names use a fixed non-sensitive placeholder. |
| `status` | enum | Exactly `ok`, `error`, `denied`, `timeout`, `validation_error`, or `unavailable`. Truncation remains a boolean, not a seventh status. |
| `arguments` | object | Only schema-declared argument names and sanitized values; no executable, profile, environment, registry, audit path, or command metadata. |
| `exit_code` | integer or null | Child exit code when a child completed; otherwise `null`. The runner process still uses the existing status-to-exit mapping. |
| `data` | object or null | Strictly decoded, validated, recursively redacted diagnostic JSON; preserves Phase 03 `empty` section semantics. |
| `stdout` | string or null | Reserved for bounded sanitized non-structured output only if Chunk 0 proves it is required; proposed normal diagnostic behavior uses `data` and keeps this `null`. |
| `stderr` | string or null | Bounded sanitized public stderr only when contractually useful; raw stderr and exceptions are forbidden. |
| `error` | object or null | Proposed closed object with normalized `class` and bounded sanitized `message`; `null` on success. |
| `duration_ms` | integer | Non-negative monotonic elapsed duration. |
| `truncated` | boolean | True whenever retained child output or a public bounded field omitted content. |
| `timestamp` | string | UTC RFC 3339 timestamp generated once for the request. |
| `correlation_id` | string | Internally generated bounded identifier, proposed UUIDv4; no caller-selected CLI value. |

Successful empty findings remain `status: ok`; emptiness is represented by the validated Phase 03 diagnostic section status `empty`. A missing endpoint or blocked service remains `unavailable`, and execution failure remains `error`.

Serialization is deterministic: UTF-8 JSON, sorted keys, compact separators, one object followed by one newline, and no `NaN` or non-standard JSON values. Tests inject clock and identifier seams rather than weakening the public CLI.

#### Redaction contract

**Function Signature Contract (Conceptual):**

```text
redact_value(value, policy) -> RedactionResult
sanitize_text(text, maximum_bytes, policy) -> SanitizedText
sanitize_arguments(tool, validated_arguments, audience) -> object
```

`RedactionResult` conceptually carries the redacted value, whether replacement occurred, and truncation metadata. It must not retain a second raw copy beyond the active request.

The same redaction policy applies before result serialization and audit construction:

- recursively replace values whose object keys match reviewed case-insensitive secret-like variants including password, passphrase, secret, token, credential, private key, API key, and authorization;
- sanitize bounded text for reviewed assignment/header forms and private-key blocks;
- use one fixed public marker, proposed `[REDACTED]`;
- preserve unrelated safe fields and JSON types;
- fail closed on unsupported values, excessive nesting, cyclic test objects, invalid UTF-8, or an exceeded redaction-work bound;
- never include profile content, environment values, absolute implementation paths, raw exception representations, stack traces, service catalogs, or unbounded response bodies.

Validated `server_identifier` may be required in the operator-facing result for interpretation, but the audit event should record only its declared presence unless Chunk 0 approves retaining the sanitized value. This minimum-disclosure decision must be frozen before code.

#### Audit-event contract

**Data Contract (Conceptual):** exact fields and persistence bounds must be frozen in Chunk 0/1.

The proposed closed JSON Lines event contains exactly:

| Field | Type | Contract |
| --- | --- | --- |
| `schema_version` | string | Proposed `1.0`. |
| `timestamp` | string | Same request timestamp as the result envelope. |
| `event_type` | string | Fixed value, proposed `tool_request_completed`. |
| `actor` | string or null | Fixed trusted local-client classification when available; never arbitrary CLI text. |
| `tool` | string | Same bounded sanitized tool label used by the result. |
| `arguments` | object | Minimum-disclosure sanitized argument summary; no secrets or command metadata. |
| `status` | enum | Same terminal status as the public result, except a persistence failure forces the public result to `error`. |
| `duration_ms` | integer or null | Present for all paths when measurable. |
| `correlation_id` | string | Same internally generated identifier as the result. |
| `reason` | string or null | Normalized bounded reason class, not raw stderr or exception text. |
| `exit_code` | integer or null | Child exit code when applicable. |
| `truncated` | boolean | Records output truncation without retaining output. |

The audit event never contains stdout, diagnostic data, raw stderr, credentials, tokens, passwords, private keys, profile/configuration content, environment values, absolute command paths, or full secret-bearing configuration.

**Function Signature Contract (Conceptual):**

```text
build_audit_event(result, actor) -> dict
append_audit_event(event, fixed_path, policy) -> None
rotate_audit_if_required(fixed_path, policy) -> RotationOutcome
```

The audit destination is fixed beneath `/opt/openstack-ai-ops-assistant/audit`; no CLI registry, audit-path, profile, executable, correlation-ID, or actor override is added. The proposed file is `/opt/openstack-ai-ops-assistant/audit/tool-runner.jsonl`, owned by `aiops_assistant:aiops_assistant`, mode `0600`, beneath the existing `0700` audit directory. The runner must use no-follow, regular-file, ownership, and mode checks before append.

Audit persistence is fail-closed. The event is constructed after redaction and persisted before the result is reported as successful. If secure append cannot be confirmed, the runner emits one generic `error` envelope with no diagnostic data and exits non-zero. The unavoidable absence of an audit record for a failed audit sink is explicitly reported as an operational fault; there is no insecure fallback file, stdout audit copy, or retry of the diagnostic.

Rotation and retention are runner-owned or repository-native only if Chunk 0 confirms the exact mechanism. Proposed bounds are size-based rotation, a fixed small archive count, restrictive modes, no compression subprocess, and no age-based deletion without a trusted clock. Exact byte/count values and lock strategy are not final until the operations contract is accepted.

#### Existing concrete integration contracts

The current revised runner already concretely provides:

```text
load_registry(path=None) -> dict
parse_declared_args(argv) -> (tool_name, declarations)
validate_request(registry, tool_name, declarations) -> (tool, values)
execute_fixed_diagnostic(tool, values) -> (status, reason, capture)
emit_stub_outcome(tool_name, status, reason, capture=None) -> None
main(argv=None) -> int
```

Steps 5–7 replace `emit_stub_outcome` with the final result/audit path while preserving the existing strict registry, request, argv, environment, timeout, process-group, and output-budget behavior. New helper symbols must be created before their call sites are rewired.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops-revised/implementation-plan/04-tool-runner-safety-gateway.md:136-199` requires final envelopes, complete allowed/denied audit coverage, restrictive audit permissions, retention/rotation procedures, and safety regression tests.
- `docs/ai-ops-revised/prd.md:173-177` defines FR-029 through FR-031: structured outcomes and auditing of allowed, denied, and validation-failed calls.
- `docs/ai-ops-revised/prd.md:308-405` lists result fields, audit fields, workflow ordering, and tests for every outcome and secret exclusion.
- `docs/ai-ops-revised/runtime/tool-runner-safety-gateway-steps-01-to-04-operations-contract.md` freezes the six statuses, exit codes, minimal environment, process cleanup, combined output budget, and explicit deferral of final redaction/auditing.
- `ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/aiops_tool_runner.py` currently emits only an interim object through `emit_stub_outcome`; it has no timestamp, correlation ID, complete redaction, audit event, or audit persistence.
- Current focused tests under `ansible/ai_ops_assistant/tests/tool_runner/` cover denial, malformed parameters, fixed argv, fresh environment, target integrity, timeout descendants, dual-stream output, invalid UTF-8, malformed JSON, and registry corruption.
- `docs/ai-ops-revised/runtime/manual-diagnostic-toolbox-operations-contract.md` fixes diagnostic schema `1.0`, section-level `empty` versus `unavailable`, normalized diagnostic errors, recursive secret-key redaction, a 512-character error bound, and a 1 MiB complete diagnostic bound.
- `ansible/ai_ops_assistant/roles/ai_ops_assistant_foundation/defaults/main.yml` and `docs/ai-ops-revised/runtime/foundation-operations-contract.md` fix the audit directory at `/opt/openstack-ai-ops-assistant/audit`, owned by `aiops_assistant:aiops_assistant`, mode `0700`.
- `docs/ai-ops-revised/runtime/selective-reuse-manifest.md` selects the historical runner for Phase 04 review but requires revised implementation/profile/audit/runtime paths. The historical registry is reference-only and broader tools remain excluded.
- The historical runner demonstrates result/audit concepts but exposes caller-selected registry, request ID, actor/transport, and audit path; uses the historical root; includes raw exception/error strings; and performs permissive append/create behavior. Those behaviors must not be copied.
- Python validation requires a user-provided virtual environment. Before running any Python command or session, ask the user to provide and confirm the virtual environment path; use `<user-provided-venv>/bin/python` only for local validation and never commit the private path to the repository.
- Ansible and ansible-lint executables were not available during Chunk 7/8 local validation; this remains a validation-environment gap, not authorization for live execution.

#### Assumptions

- Python standard-library `json`, `datetime`, `uuid`, `os`, `stat`, and, on Linux, `fcntl` are sufficient; no new runtime package should be introduced.
- One final envelope schema can represent every status while retaining parsed diagnostic data and never returning raw child bytes.
- A fixed local CLI actor classification or `null` is sufficient until Phase 07 introduces a separately reviewed trusted client boundary.
- Audit writing occurs as the unprivileged runtime user inside the existing `0700` audit directory; deployment does not broaden directory access.
- Local fixture tests are sufficient for Steps 5–7 implementation. Live OpenStack validation remains separately authorized and is not part of this ADS chunk ladder.

#### Open confirmations for Chunk 0

1. What exact result and audit schema versions and closed field sets are approved?
2. Is `correlation_id` always generated internally as UUIDv4, and what test seam is permitted?
3. Which normalized runner error classes and maximum public message bytes are approved?
4. May the result retain a validated server identifier, while audit retains only parameter presence?
5. What fixed redaction marker, key pattern, text patterns, nesting limit, and redaction-work limit are accepted?
6. Is `stdout` always `null` for the current JSON diagnostics, with parsed/redacted content only in `data`?
7. Is `/opt/openstack-ai-ops-assistant/audit/tool-runner.jsonl` the exact fixed audit file?
8. What exact maximum event size, active-file size, retained archive count, lock, flush, and durability policy are appropriate for the lab?
9. Must an audit append call `fsync` before a success result, or is locked flush/close sufficient?
10. How should existing insecure/symlinked/wrong-owner audit files fail and be recovered operationally without automatic replacement?
11. Which actor classifications, if any, are trusted at the local CLI boundary?
12. Does the current Step 4 interruption behavior need correction before Step 7 can claim complete regression coverage?

### III. Required Technical Dependencies and Imports

No third-party runtime dependency is proposed.

- Existing runner dependencies: `json`, `os`, `re`, `selectors`, `signal`, `subprocess`, `sys`, `time`, `pathlib.Path`, and typing support.
- Proposed standard-library additions: `datetime.datetime`, `datetime.timezone`, `uuid`, `stat`, and Linux `fcntl` if file locking is approved.
- Existing deployment dependency: the foundation-owned audit directory and `aiops_assistant` runtime identity.
- Existing test framework: `unittest`, controlled temporary directories/files, injected clock/identifier/path seams, and fixture executables only.
- Existing formatter/linter: Ruff from the approved virtual environment.
- Proposed operations contract: `docs/ai-ops-revised/runtime/tool-runner-safety-gateway-steps-05-to-07-operations-contract.md`.
- No MCP package, OpenStack SDK call, network library, logging framework, database, shell command, compression utility, or historical module import is required.

### IV. Step-by-Step Procedure / Execution Flow

1. Generate one internal correlation ID and UTC timestamp at request start; capture monotonic start time separately.
2. Load and validate the fixed registry. Preserve the Steps 1–4 fail-closed behavior.
3. Parse the bounded public tool name and declared arguments. Normalize malformed public labels without reflecting arbitrary unbounded input.
4. Validate the request. Unknown tools become `denied`; malformed values become `validation_error`; neither path starts a child.
5. Execute only an approved request through the existing fixed argv, minimal environment, controlled cwd, process group, timeout, and output budget.
6. Convert the terminal execution state into one internal normalized outcome. Preserve child exit code only when applicable.
7. Strictly decode and validate diagnostic JSON. Preserve `empty` sections as successful data and map approved endpoint classes to `unavailable`.
8. Apply recursive structured redaction to diagnostic data and argument values. Apply bounded text sanitization to all public reason/error text.
9. Build the closed deterministic result envelope. No raw byte buffer or raw exception object enters it.
10. Derive the smaller audit event from the already-normalized/redacted outcome, not from raw request or child data.
11. Validate the fixed audit directory/file boundary, lock as approved, rotate only within fixed bounds, append one compact JSON line, apply/check mode `0600`, and complete the approved durability step.
12. If audit persistence fails, discard result data, emit a generic audit-failure `error` envelope, and return non-zero without retrying the diagnostic or writing elsewhere.
13. Otherwise emit exactly one result JSON line and return the existing status exit code.
14. Run fixture-driven regression tests across every status, truncation, corruption, redaction, audit, file-integrity, and no-spawn/no-orphan case.
15. Reconcile only evidence-backed Step 5–7 and phase-definition checklist items after all local gates pass. Do not activate deployment or run live diagnostics.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| --- | --- | --- | --- |
| Request identity | Correlation generator or clock seam fails | Use no caller fallback; normalize to internal failure | `error` / `ERR_RUNNER_REQUEST_CONTEXT` (proposed) |
| Registry startup | Registry unreadable, duplicate, malformed, unsafe, or historical | Build a minimal sanitized failure outcome; attempt required audit | `error` / `registry_error` |
| Public input | Tool label is empty, overlong, control-bearing, or unsafe | Replace reflected label with fixed placeholder; do not spawn | `validation_error` or `denied` per frozen contract |
| Request validation | Unknown tool or undeclared/unsafe parameter | Do not inspect or execute target; audit terminal denial | `denied` or `validation_error` |
| Execution | Target missing, symlinked, non-regular, wrong mapping, or non-executable | Preserve existing fail-closed target behavior | `unavailable` or `error` |
| Child outcome | Child exits non-zero or diagnostic status is error | Normalize and redact; no raw stderr/exception | `error` |
| Timeout/interruption | Deadline or signal occurs | Clean complete process group, reap child, then normalize and audit | `timeout` or `error` |
| Decode/shape | Invalid UTF-8, malformed JSON, wrong schema/tool/status | Discard raw payload and return bounded generic reason | `error` / `output_decode_error` (proposed) |
| Redaction | Unsupported type, depth/work limit, or sanitizer failure | Drop affected content; do not emit partially sanitized data | `error` / `redaction_error` (proposed) |
| Serialization | Non-JSON value or oversized final envelope | Fail closed with minimal bounded envelope; never print partial JSON | `error` / `serialization_error` (proposed) |
| Audit path | Directory/file absent, symlinked, non-regular, wrong owner/mode, or outside fixed root | Refuse append and report generic audit fault | `error` / `audit_integrity_error` (proposed) |
| Audit append | Lock, rotate, write, flush, or durability step fails | Do not report original outcome as success; no alternate sink | `error` / `audit_write_error` (proposed) |
| Rotation | Archive collision, symlink, unsafe metadata, or retention bound cannot be enforced | Refuse rotation/append; leave existing files untouched | `error` / `audit_rotation_error` (proposed) |
| Regression | Secret canary appears in result/audit or child remains alive | Fail suite and block checklist reconciliation/deployment | blocking test failure |
| Deployment | Role would broaden audit permissions or activate by default | Fail role assertions and stop | deployment blocked |

### VI. Security, Integrity, Idempotency, and Cleanup

- **Security:** Redaction is defense in depth after Phase 03 filtering. Raw output, raw errors, environment values, credentials, catalogs, stack traces, and absolute implementation paths never enter public or audit structures. Audit contains no diagnostic output.
- **Least privilege:** Audit state remains under the existing runtime-user-owned `0700` directory. The active file and archives are proposed `0600`; no group/world access is added.
- **Path integrity:** Registry, target, working directory, profile, and audit paths remain fixed constants. Audit operations reject symlinks and non-regular files and never follow caller-selected paths.
- **Concurrency:** If multiple local requests are permitted, append and rotation use one approved lock strategy. A JSON event must not interleave with another event or appear partially valid.
- **Durability:** The accepted operations contract must state whether success requires `fsync`. Tests may inject persistence failures; they must not weaken production behavior.
- **Idempotency:** A request is executed at most once. Audit failure does not retry the diagnostic. Re-running a read-only request creates a new correlation ID and a new audit event.
- **Rotation:** Rotation touches only the fixed active file and fixed numbered archives beneath the revised audit root. It rejects unsafe existing paths and retains no more than the approved count.
- **Cleanup:** Process cleanup remains unchanged. In-memory raw buffers and temporary test files are released after each request. Production implementation creates no temporary result file. Failed rotation must not leave an insecure replacement or broaden permissions.
- **Confidentiality incident:** A regression test or review finding a secret in result/audit blocks deployment. Remove unsafe retained test artifacts and follow credential rotation procedures if the canary could represent real material.
- **Activation boundary:** Role deployment remains disabled by default. This ADS authorizes no host connection, profile read, OpenStack call, MCP registration, host diagnostic, or remediation.

### VII. Validation Strategy

Use the confirmed user-provided virtual environment for every Python command. Before starting a Python session or validation, ask the user to provide and confirm its path; represent it below as `<user-provided-venv>/bin/python`.

- **Python syntax:** `rtk <user-provided-venv>/bin/python -m py_compile <changed-python-files>`
- **JSON syntax:** `rtk <user-provided-venv>/bin/python -m json.tool ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/tool_registry.json`
- **Targeted tests:** `rtk <user-provided-venv>/bin/python -m unittest discover -s ansible/ai_ops_assistant/tests/tool_runner -p 'test_*.py'`
- **Formatter:** `rtk <user-provided-venv>/bin/python -m ruff format <changed-python-files>`
- **Linter:** `rtk <user-provided-venv>/bin/python -m ruff check --ignore EXE001 <changed-python-files>`
- **ADS structure:** `rtk grep -n '^### [IVX]' docs/ai-ops-revised/implementation-plan/ads/04-01-tool-runner-result-audit-safety-regression-ads.md`
- **Symbol checks:** `rtk grep -RniE 'def (redact_value|sanitize_text|build_result_envelope|build_audit_event|append_audit_event|rotate_audit_if_required)' ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner`
- **Forbidden behavior scan:** `rtk grep -RniE 'shell=True|os\.system|/opt/openstack-ai-ops([^ -]|$)|operator-reader|restricted-ssh|--audit-path|--registry|--request-id|traceback|repr\(' ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner ansible/ai_ops_assistant/tests/tool_runner`
- **Secret-flow scan:** inspect every result/audit construction path and run canary tests for key-based, header/assignment, bearer-token, private-key, nested, argument, stderr, malformed, and truncation cases.
- **Audit filesystem tests:** temporary-directory fixtures for absent file, safe create, append, concurrent append, wrong mode/owner where locally testable, symlink, non-regular file, rotation bounds, append failure, and no insecure fallback.
- **Ansible syntax when tooling exists:** `rtk ansible-playbook --syntax-check -i ansible/ai_ops_assistant/inventories/local/local.yml <focused-local-playbook>`
- **Ansible lint when tooling exists:** `rtk ansible-lint <changed-role-and-playbook-files>`
- **Diff integrity:** `rtk git diff --check` and `rtk git diff -- <changed-files>`

Regression coverage must prove:

- every status has a deterministic closed result shape and expected process exit code;
- success with an `empty` diagnostic section remains successful and distinct from unavailable/failure;
- every allowed, denied, validation, unavailable, error, timeout, and truncated outcome yields one matching audit event;
- result and audit share timestamp/correlation/status and never diverge silently;
- malformed registries and requests fail before spawn yet still attempt sanitized audit persistence;
- secret canaries never survive in nested data, arguments, errors, stderr, results, or audit events;
- audit contains no stdout/data/raw stderr and respects size/mode/path/retention bounds;
- audit failure cannot produce a success result or trigger diagnostic retry;
- no generic command/path/profile/environment/audit override exists;
- timeout/interruption leaves no child or descendant;
- no test requires a live OpenStack deployment or credential profile.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass.

#### Chunk 0: Discovery and Contract Confirmation
- **Goal:** Freeze result/audit/redaction schemas, bounds, persistence semantics, and the remaining Step 4 interruption gap without editing or executing diagnostics.
- **Files to read:** this ADS; Phase 04 plan; PRD FR-029–FR-031 and testing decisions; Steps 1–4 operations contract; current revised runner/tests/role; foundation audit contract; Phase 03 output/redaction contract; manifest-selected historical runner as review-only evidence.
- **Commands:** bounded RTK-prefixed `git status`, `find`, `grep`, and targeted reads; verify approved venv and Ansible tool availability.
- **Evidence to confirm:** exact fields/schema versions, error classes, redaction policy/bounds, correlation policy, actor policy, fixed audit path, ownership/modes, event/file/rotation bounds, lock/durability behavior, audit-failure behavior, and interruption test requirement.
- **Stop condition:** write a decision handoff; do not edit executable files or continue to Chunk 1.

#### Chunk 1: Steps 5–7 Operations Contract
- **Goal:** Record one authoritative final result, redaction, audit, rotation/retention, and regression contract before code.
- **Files to change:** proposed `docs/ai-ops-revised/runtime/tool-runner-safety-gateway-steps-05-to-07-operations-contract.md` only.
- **Symbols to add/change:** no executable symbols; exact closed schemas, examples for every status, redaction table, audit file algorithm, failure semantics, and retention procedure.
- **Implementation shape:** documentation-only; include reviewed fake examples and explicit non-activation/rollback boundaries.
- **Validation:** required-section/example grep, historical/caller-override scan, `rtk git diff --check`, and focused diff review.
- **Stop condition:** every Chunk 0 decision can be answered from one contract; stop before Python changes.

#### Chunk 2: Redaction Boundary and Tests
- **Goal:** Add a standalone fail-closed structured/text redaction boundary without changing emitted results or writing audit files.
- **Files to change:** revised runner and proposed `ansible/ai_ops_assistant/tests/tool_runner/test_result_redaction.py`.
- **Symbols to add/change:** conceptual `RedactionError`, `RedactionResult`, `redact_value`, `sanitize_text`, and `sanitize_arguments`.
- **Implementation shape:** introduce helpers before call sites; recursive key and bounded text canaries; unsupported/deep values raise a safe error. Existing interim emission remains until Chunk 3.
- **Validation:** Python compile, Ruff, targeted redaction tests, secret-canary scan, existing suite, and diff review.
- **Stop condition:** all approved canaries redact deterministically and no production result/audit wiring has changed.

#### Chunk 3: Final Result Envelope Slice
- **Goal:** Replace interim emission with one deterministic final envelope for denial/validation first, then all existing terminal outcomes through the same builder.
- **Files to change:** revised runner and proposed `ansible/ai_ops_assistant/tests/tool_runner/test_result_envelope.py`.
- **Symbols to add/change:** conceptual `build_result_envelope`, `serialize_result_envelope`, request timestamp/correlation seam, and normalized public error mapping; replace `emit_stub_outcome` only after helpers exist.
- **Implementation shape:** closed schema, parsed/redacted data, stable empty/unavailable distinction, one JSON line, no audit persistence yet. If a temporary audit-not-implemented state is needed, keep deployment disabled and do not claim Step 6.
- **Validation:** every status/exit/shape example, deterministic serialization, empty finding, invalid output, truncation, redaction, Python/Ruff, existing suite, and diff review.
- **Stop condition:** final result behavior is complete and compile-safe; no audit file is created.

#### Chunk 4: Audit Event Construction Without Persistence
- **Goal:** Derive one minimal closed audit event from the normalized/redacted outcome for every branch without filesystem writes.
- **Files to change:** revised runner and proposed `ansible/ai_ops_assistant/tests/tool_runner/test_audit_events.py`.
- **Symbols to add/change:** conceptual `build_audit_event`, trusted actor classification, reason mapping, and event serializer.
- **Implementation shape:** audit derives from safe internal outcome/result fields; excludes all output/data/raw errors; tests compare correlation/timestamp/status across every outcome.
- **Validation:** event schema tests for allowed/denied/validation/unavailable/error/timeout/truncated, secret-exclusion tests, Python/Ruff, existing suite, and diff review.
- **Stop condition:** every outcome can produce one safe event in memory; no audit path is opened.

#### Chunk 5: Secure Audit Persistence and Bounded Rotation
- **Goal:** Persist exactly one event through the fixed revised audit path with restrictive metadata, concurrency safety, bounded rotation, and fail-closed errors.
- **Files to change:** revised runner and proposed `ansible/ai_ops_assistant/tests/tool_runner/test_audit_persistence.py`.
- **Symbols to add/change:** conceptual `validate_audit_path`, `append_audit_event`, `rotate_audit_if_required`, fixed audit constants, and persistence test seams.
- **Implementation shape:** no-follow regular-file checks, fixed root/file, approved lock and durability policy, `0600`, fixed retention count, no external subprocess. Wire persistence before successful result emission; failure discards data and returns generic non-zero error without retry.
- **Validation:** safe create/append, concurrent JSONL integrity, symlink/non-regular/wrong-mode rejection, injected write/fsync/rotation failures, retention bound, no fallback, Python/Ruff, existing suite, and diff review.
- **Stop condition:** allowed and denied fixture calls persist matching events securely; no deployment or live diagnostic runs.

#### Chunk 6: Deployment Metadata and Operational Retention Slice
- **Goal:** Extend the disabled role contract with exact audit constants/assertions and document operator review/cleanup without activating execution.
- **Files to change:** dedicated runner role defaults/tasks and, only if the accepted contract requires it, one role-local rotation artifact; split into two sessions if more than two files are required.
- **Symbols to add/change:** fixed audit directory/file, owner/group/mode, size/count bounds, non-symlink assertions, and disabled-default validation.
- **Implementation shape:** assert revised-only constants; do not broaden the foundation audit directory, modify Phase 03 allowlist, enable deployment, or introduce historical files.
- **Validation:** YAML parse, Ansible syntax/lint when available, role static assertions, historical-identifier scan, `rtk git diff --check`, and diff review.
- **Stop condition:** deployment contract is fail-closed and disabled; no host connection occurs.

#### Chunk 7: Complete Safety Regression and Phase Reconciliation
- **Goal:** Close all fixture-driven Steps 5–7 cases, resolve the explicit interruption gap, and reconcile only passing Phase 04 checklist items.
- **Files to change:** focused integration/regression tests and `docs/ai-ops-revised/implementation-plan/04-tool-runner-safety-gateway.md`; split test additions from checklist edits if needed.
- **Symbols to add/change:** status/audit matrix, spawn marker, process descendant/interruption fixture, nested secret canaries, audit-corruption/retention/concurrency fixtures, and exact three-tool assertion.
- **Implementation shape:** run the complete local gateway contract without profile access or OpenStack. Checklist edits occur only after all required checks pass; unresolved Ansible tooling or interruption behavior remains explicitly unchecked.
- **Validation:** full focused unittest discovery, Python/JSON syntax, Ruff, deployment YAML/Ansible checks where available, forbidden-capability and secret scans, `rtk git diff --check`, and complete diff review.
- **Stop condition:** Steps 5–7 and phase definition-of-done are evidence-backed complete or explicitly blocked. Stop before Phase 05, MCP, or live activation.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.
Activate rtk-command-prefix for shell commands.

Task:
Phase 04 Tool Runner Safety Gateway, Steps 5–7, from docs/ai-ops-revised/implementation-plan/ads/04-01-tool-runner-result-audit-safety-regression-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm the result schema, redaction policy, audit persistence/retention contract, test seams, approved Python virtual environment, and blockers; write a handoff and stop.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.
Activate rtk-command-prefix for shell commands.

Task:
Phase 04 Tool Runner Safety Gateway, Steps 5–7.

Mode:
Execute Chunk 1 only from docs/ai-ops-revised/implementation-plan/ads/04-01-tool-runner-result-audit-safety-regression-ads.md.
Do not continue to Chunk 2. Change only the approved Steps 5–7 operations-contract file. Run targeted documentation validation, show git diff, ask before creating a handoff, and stop.
```

Each later session must execute exactly one accepted chunk, ask the user to provide and confirm a virtual environment before any Python session or validation, use only that user-provided environment, keep its private path out of repository files, complete formatting/tests/diff/risk post-work, ask before creating a single-chunk handoff, and stop. No chunk may run a live profile, OpenStack diagnostic, host deployment, MCP workflow, or remediation.

### X. Conclusion and Next Steps

Steps 5–7 must complete one security boundary, not bolt independent result and audit paths onto the runner. Every terminal request outcome is normalized once, redacted once, represented by a deterministic result, reduced to a minimum-disclosure audit event, and persisted through one fixed restrictive sink before success is reported.

The next action is Chunk 0 discovery and decision confirmation only. Implementation must remain fixture-driven and disabled by default. Phase 04 cannot be marked complete until the final status/audit matrix, secret canaries, audit-integrity behavior, process interruption coverage, deployment assertions, and complete focused regression suite all pass.