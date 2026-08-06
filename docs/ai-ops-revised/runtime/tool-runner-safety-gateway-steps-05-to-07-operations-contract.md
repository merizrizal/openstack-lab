# Revised AI-OPS Tool Runner Safety Gateway Operations Contract — Steps 5–7

## Status and Authority

This is the approved Phase 04 Steps 5–7 operations contract. It extends:

- `docs/ai-ops-revised/implementation-plan/04-tool-runner-safety-gateway.md`;
- `docs/ai-ops-revised/implementation-plan/ads/04-01-tool-runner-result-audit-safety-regression-ads.md`;
- `docs/ai-ops-revised/runtime/tool-runner-safety-gateway-steps-01-to-04-operations-contract.md`;
- `docs/ai-ops-revised/runtime/manual-diagnostic-toolbox-operations-contract.md`;
- `docs/ai-ops-revised/runtime/foundation-operations-contract.md`; and
- `docs/ai-ops-revised/runtime/selective-reuse-manifest.md`.

It freezes the final result envelope, redaction boundary, audit event, audit persistence, rotation/retention, and regression-test contracts before executable implementation. It does not authorize live deployment, profile access, OpenStack calls, host diagnostics, MCP, remediation, or Phase 04 checklist completion.

The runner remains the only execution boundary. Every request, including denied and pre-execution failures, follows one normalized result and audit path. No branch may emit raw child output, raw exceptions, or partially redacted content.

## Non-Activation and Capability Boundary

This contract introduces no executable file, deployment change, profile, credential, host connection, Ansible run, OpenStack request, MCP registration, or cloud-state authority. Validation remains fixture-driven.

The approved public tools remain exactly:

| Tool | Parameters | Profile | Risk class |
| --- | --- | --- | --- |
| `project_resource_summary` | none | `aiops-assistant-project-reader` | `low_readonly_project_scope` |
| `server_basic_info` | required validated `server_identifier` | `aiops-assistant-project-reader` | `low_readonly_project_scope` |
| `server_network_info` | required validated `server_identifier` | `aiops-assistant-project-reader` | `low_readonly_project_scope` |

Generic shell, SSH, sudo, OpenStack CLI passthrough, file/database/message-bus access, mutation, remediation, Phase 06 diagnostics, and caller-selected executable, profile, environment, working-directory, timeout, output, audit-path, actor, or correlation-ID values remain forbidden.

## Terminal Status and Exit-Code Contract

The result `status` is exactly one of the six statuses already established by Steps 1–4:

| Status | Exit code | Meaning |
| --- | ---: | --- |
| `ok` | `0` | Approved diagnostic completed; an empty diagnostic section is still successful. |
| `error` | `1` | Runner, decoding, execution, redaction, serialization, interruption, or audit failure not classified otherwise. |
| `denied` | `2` | Requested capability is not in the reviewed allowlist. |
| `validation_error` | `3` | Request or registry-declared input failed validation before execution. |
| `timeout` | `4` | Deadline was reached and complete process-group cleanup was attempted. |
| `unavailable` | `5` | Approved target/profile/service is unavailable, or the diagnostic reports an approved unavailable class. |

Output truncation is metadata, never a seventh status. Successful empty findings remain `ok` and are represented by Phase 03 section status `empty`. Approved unavailable diagnostic classes are `service_unavailable`, `catalog_missing`, and `connectivity_error`; other diagnostic failures remain `error`.

Every non-`ok` result returns a non-zero process exit code. The public status and exit code are deterministic and must agree.

## Request Identity, Timestamp, and Actor

For every request the runner generates internally:

- one UUIDv4 `correlation_id`;
- one UTC RFC 3339 `timestamp`; and
- one monotonic start time for `duration_ms`.

Caller-provided correlation IDs, timestamps, actors, request IDs, and arbitrary client text are rejected or ignored. Tests may inject only clock and UUID factories. The reviewed local entrypoint uses the fixed actor classification `local_cli`; it must not claim an authenticated operator identity.

The same timestamp and correlation ID are used in the result and its corresponding audit event. A request executes at most once. Audit failure never retries the diagnostic.

## Result Envelope Contract

The result is a closed UTF-8 JSON object with exactly these top-level fields:

| Field | Type | Required behavior |
| --- | --- | --- |
| `schema_version` | string | Exactly `"1.0"`. |
| `tool` | string | Sanitized approved tool name; malformed/unresolved labels use a fixed non-sensitive placeholder. |
| `status` | enum | One of the six statuses above. |
| `arguments` | object | Validated public arguments only. `server_identifier` may be retained after redaction. |
| `exit_code` | integer or null | Child exit code when a child completed; otherwise `null`. |
| `data` | object or null | Parsed, validated, recursively redacted Phase 03 diagnostic content. |
| `stdout` | string or null | Always `null` for current JSON diagnostics. |
| `stderr` | string or null | `null` by default; never raw child stderr. |
| `error` | object or null | Normalized error object or `null` on success. |
| `duration_ms` | integer | Non-negative monotonic elapsed duration. |
| `truncated` | boolean | True if bounded output or a public field discarded content. |
| `timestamp` | string | Request UTC RFC 3339 timestamp. |
| `correlation_id` | string | Internally generated UUIDv4. |

The `error` object is closed and contains exactly:

```json
{"class":"execution_error","message":"sanitized bounded message"}
```

It is `null` for `ok`. Public error messages are sanitized and limited to 512 UTF-8 bytes. They contain no raw stderr, exception representations, stack traces, credentials, profile data, catalogs, implementation paths, commands, or response bodies.

`data` preserves the validated Phase 03 diagnostic shape, including section-level `empty`, `unavailable`, and truncation semantics. Raw bytes never enter the envelope. Invalid UTF-8, malformed JSON, invalid diagnostic shape, or unsafe values fail closed.

Serialization is deterministic: UTF-8 JSON, sorted keys, compact separators, standard JSON values only, and exactly one complete object followed by one newline. Partial or duplicate result lines are prohibited.

### Normalized Error Classes

The approved normalized classes are:

- `request_context_error`
- `registry_error`
- `validation_error`
- `target_unavailable`
- `target_integrity_error`
- `execution_error`
- `timeout`
- `interrupted`
- `output_decode_error`
- `redaction_error`
- `serialization_error`
- `audit_integrity_error`
- `audit_write_error`
- `audit_rotation_error`

A class is a bounded public category, not a place to expose implementation detail. Audit `reason` values use the same normalized classes where applicable.

### Result Examples

Examples use fake values only and are illustrative contract fixtures. They contain no real topology, credential, profile, or implementation data.

#### `ok` with data

```json
{"schema_version":"1.0","tool":"server_basic_info","status":"ok","arguments":{"server_identifier":"demo-server"},"exit_code":0,"data":{"schema_version":"1.0","tool":"server_basic_info","status":"ok","sections":[{"name":"server","status":"ok","data":{"id":"fake-id","name":"demo-server","status":"ACTIVE"},"error":null,"truncated":false}],"error":null},"stdout":null,"stderr":null,"error":null,"duration_ms":42,"truncated":false,"timestamp":"2030-01-02T03:04:05Z","correlation_id":"00000000-0000-4000-8000-000000000001"}
```

#### `ok` with an empty finding

```json
{"schema_version":"1.0","tool":"project_resource_summary","status":"ok","arguments":{},"exit_code":0,"data":{"schema_version":"1.0","tool":"project_resource_summary","status":"ok","sections":[{"name":"servers","status":"empty","data":[],"error":null,"truncated":false}],"error":null},"stdout":null,"stderr":null,"error":null,"duration_ms":18,"truncated":false,"timestamp":"2030-01-02T03:04:05Z","correlation_id":"00000000-0000-4000-8000-000000000002"}
```

#### `error`

```json
{"schema_version":"1.0","tool":"server_network_info","status":"error","arguments":{"server_identifier":"demo-server"},"exit_code":1,"data":null,"stdout":null,"stderr":null,"error":{"class":"output_decode_error","message":"Diagnostic output could not be accepted."},"duration_ms":31,"truncated":false,"timestamp":"2030-01-02T03:04:05Z","correlation_id":"00000000-0000-4000-8000-000000000003"}
```

#### `denied`

```json
{"schema_version":"1.0","tool":"unknown_tool","status":"denied","arguments":{},"exit_code":2,"data":null,"stdout":null,"stderr":null,"error":{"class":"validation_error","message":"Requested tool is not available."},"duration_ms":1,"truncated":false,"timestamp":"2030-01-02T03:04:05Z","correlation_id":"00000000-0000-4000-8000-000000000004"}
```

#### `validation_error`

```json
{"schema_version":"1.0","tool":"server_basic_info","status":"validation_error","arguments":{"server_identifier":"[REDACTED]"},"exit_code":3,"data":null,"stdout":null,"stderr":null,"error":{"class":"validation_error","message":"Request arguments are invalid."},"duration_ms":1,"truncated":false,"timestamp":"2030-01-02T03:04:05Z","correlation_id":"00000000-0000-4000-8000-000000000005"}
```

#### `timeout`

```json
{"schema_version":"1.0","tool":"server_network_info","status":"timeout","arguments":{"server_identifier":"demo-server"},"exit_code":4,"data":null,"stdout":null,"stderr":null,"error":{"class":"timeout","message":"Diagnostic exceeded its time limit."},"duration_ms":1000,"truncated":false,"timestamp":"2030-01-02T03:04:05Z","correlation_id":"00000000-0000-4000-8000-000000000006"}
```

#### `unavailable`

```json
{"schema_version":"1.0","tool":"project_resource_summary","status":"unavailable","arguments":{},"exit_code":5,"data":null,"stdout":null,"stderr":null,"error":{"class":"target_unavailable","message":"Approved diagnostic is unavailable."},"duration_ms":4,"truncated":false,"timestamp":"2030-01-02T03:04:05Z","correlation_id":"00000000-0000-4000-8000-000000000007"}
```

## Redaction and Sanitization Contract

Redaction occurs before result construction and before audit construction. Audit derives only from already-safe normalized fields.

| Input | Required handling |
| --- | --- |
| Object keys matching `password`, `passphrase`, `secret`, `token`, `credential`, `private key`, `api key`, or `authorization`, case-insensitively | Replace the complete value with `[REDACTED]`. |
| Assignment/header forms such as `password=...`, `Authorization: ...`, and secret-like key/value text | Replace the sensitive value with `[REDACTED]`. |
| `Bearer <token>` text | Replace the token, preserving only the safe scheme marker if needed. |
| PEM private-key blocks | Replace the complete block with `[REDACTED]`. |
| Nested objects and arrays | Recurse while preserving safe JSON types. |
| Depth greater than 32 | Fail closed with `redaction_error`; emit no partially sanitized value. |
| More than 100,000 visited values | Fail closed with `redaction_error`; emit no partially sanitized value. |
| Unsupported values, cyclic test values, invalid UTF-8, or sanitizer failure | Fail closed with `redaction_error`; emit no raw or partial content. |

The marker is exactly `[REDACTED]`. Matching is case-insensitive. Sanitization is bounded and applies to arguments, diagnostic data, public messages, and any retained text. No raw secret-bearing value may remain in a result or audit event.

The result may retain the validated `server_identifier` after redaction. The audit event records only `server_identifier_present: true` or `false`, never the identifier itself.

## Audit Event Contract

Every request attempts one minimal audit event, including allowed, denied, validation-error, unavailable, failed, timed-out, interrupted, and truncated calls. The event is a closed JSON object with exactly:

| Field | Type | Required behavior |
| --- | --- | --- |
| `schema_version` | string | Exactly `"1.0"`. |
| `timestamp` | string | Same request timestamp as the result. |
| `event_type` | string | Exactly `"tool_request_completed"`. |
| `actor` | string | Exactly `"local_cli"`. |
| `tool` | string | Same sanitized tool label as the result. |
| `arguments` | object | Minimum-disclosure summary; server requests use only `server_identifier_present`. |
| `status` | enum | Terminal result status, unless persistence failure forces the public result to `error`. |
| `duration_ms` | integer or null | Measured duration when available. |
| `correlation_id` | string | Same internally generated UUIDv4 as the result. |
| `reason` | string or null | Normalized bounded class, not raw stderr or exception text. |
| `exit_code` | integer or null | Child exit code when applicable. |
| `truncated` | boolean | Whether bounded output discarded content. |

The audit event contains no `data`, `stdout`, raw `stderr`, credentials, tokens, passwords, private keys, profile/configuration content, environment values, absolute command paths, or full diagnostic output.

Example:

```json
{"schema_version":"1.0","timestamp":"2030-01-02T03:04:05Z","event_type":"tool_request_completed","actor":"local_cli","tool":"server_basic_info","arguments":{"server_identifier_present":true},"status":"ok","duration_ms":42,"correlation_id":"00000000-0000-4000-8000-000000000001","reason":null,"exit_code":0,"truncated":false}
```

## Fixed Audit Filesystem Contract

The audit destination is fixed and cannot be overridden:

- directory: `/opt/openstack-ai-ops-assistant/audit`;
- active file: `/opt/openstack-ai-ops-assistant/audit/tool-runner.jsonl`;
- lock file: `/opt/openstack-ai-ops-assistant/audit/.tool-runner.lock`;
- active file and archives: mode `0600`;
- directory: existing foundation-owned `aiops_assistant:aiops_assistant`, mode `0700`;
- archives: `tool-runner.jsonl.1`, `.2`, and `.3` only;
- no compression and no age-based deletion.

Before every append or rotation operation, the implementation must verify the fixed directory and each relevant file path. It must reject symlinks, non-regular files, unsafe path resolution, wrong ownership, and unsafe modes. It must not automatically replace, unlink, repair, or rename an unsafe file. Operator cleanup or redeployment is required.

### Append Algorithm

1. Validate the fixed audit directory, active file, lock file, and any archives without following symlinks.
2. Acquire exclusive `fcntl.flock` on the fixed lock file beneath the audit directory.
3. Revalidate active-file metadata after locking.
4. Rotate only when the active file reaches 1 MiB, using the fixed numbered archives and retaining at most three.
5. Reject archive collisions or unsafe archive metadata; do not overwrite unsafe paths.
6. Serialize one compact event and reject any event larger than 16 KiB.
7. Append exactly one complete JSON line while holding the lock.
8. Flush and call `fsync` before reporting persistence success.
9. Recheck active-file mode/ownership, release the lock, and report success.

The event must not interleave with another event. A successful runner result is not reported until its audit append and durability step succeed.

### Rotation and Retention

Rotation is size-based only. At or above 1 MiB, under the exclusive lock:

1. validate `.1`, `.2`, and `.3` if present;
2. remove only the oldest safe `.3` archive when needed;
3. shift `.2` to `.3` and `.1` to `.2` only after safety checks;
4. rename the active file to `.1`;
5. create a new active file with mode `0600`; and
6. revalidate ownership, regular-file status, and mode.

Any failed check, rename, creation, or metadata operation aborts rotation and leaves existing files untouched as far as the operating system permits. It returns `audit_rotation_error` and does not use a fallback sink. No more than three numbered archives are retained.

## Audit-Failure Semantics

Audit persistence is fail-closed:

- diagnostic data is discarded from the public response if audit persistence fails;
- the runner returns a generic non-zero `error` result with no raw audit/filesystem detail;
- the error class is normalized as `audit_integrity_error`, `audit_write_error`, or `audit_rotation_error`;
- the diagnostic is never retried;
- no stdout audit copy, alternate path, temporary fallback, or insecure replacement is permitted; and
- the failure is an operational fault requiring operator inspection and cleanup/redeployment.

If audit failure occurs after an original terminal outcome was known, the public result reports `status: error`, `exit_code: 1`, `data: null`, and a bounded generic message. The audit failure must not cause a second diagnostic execution.

## Interruption and Process-Cleanup Contract

Step 4 interruption behavior must be corrected and proven before Step 7 is complete. Interruption handling must be safe if it occurs before, during, or immediately after `Popen`:

- initialize the process reference before entering the protected execution path;
- if a child exists, terminate the complete process group, wait up to one second, escalate to group kill if required, and reap the direct child;
- close all pipes and release capture resources;
- terminate descendants and prove no fixture descendant remains;
- normalize exactly one non-zero `interrupted` result;
- pass the normalized outcome through redaction, result construction, and audit persistence; and
- never emit a partially initialized result or bypass audit handling.

## Regression Contract

Fixture-driven tests must cover, without live OpenStack or profile access:

- unknown and generic tools denied without spawning;
- undeclared, missing, malformed, and unsafe arguments rejected before spawning;
- fixed argument-vector execution with `shell=False` and the minimal environment;
- successful data and successful empty findings;
- `error`, `denied`, `validation_error`, `timeout`, and `unavailable` results with exact exit codes;
- child failure, unavailable target, malformed registry, invalid UTF-8, malformed JSON, and diagnostic-shape errors;
- combined output limits and explicit truncation;
- nested key, assignment/header, bearer-token, PEM, argument, error, stderr, depth, work-limit, and invalid-value redaction;
- closed result and audit field sets, deterministic serialization, shared timestamp/correlation/status, and secret exclusion;
- audit event coverage for every terminal outcome;
- safe audit create/append, 16 KiB event bound, 1 MiB rotation, three-archive retention, mode/owner/path checks, locking, flush/fsync, and concurrent JSONL integrity;
- symlink, non-regular, wrong-owner, wrong-mode, unsafe-path, write, fsync, and rotation failures fail closed without fallback;
- audit failure discards diagnostic data and does not retry execution; and
- timeout and interruption leave no child or descendant and reap/close all resources.

No regression test may require a deployed cloud, credential profile, host access, MCP, remediation, or live diagnostic.

## Validation, Rollback, and Deferred Work

Documentation-only validation for this contract is:

```bash
rtk git diff --check
rtk grep -n '^##\|^###' docs/ai-ops-revised/runtime/tool-runner-safety-gateway-steps-05-to-07-operations-contract.md
rtk grep -n 'schema_version\|correlation_id\|REDACTED\|tool-runner.jsonl\|fsync\|interrupted' docs/ai-ops-revised/runtime/tool-runner-safety-gateway-steps-05-to-07-operations-contract.md
```

Python validation is deferred until the user provides and confirms a virtual environment. When authorized, use only `<user-provided-venv>/bin/python`; never commit a private venv path.

Rollback of this chunk is limited to reverting this documentation file. It must not alter executable Python, tests, Ansible role files, Phase 03 diagnostics, identity material, protected inventory, profiles, OpenStack resources, or external evidence.

The following remain deferred: executable redaction helpers, final result implementation, in-memory audit construction, secure audit persistence, deployment metadata, the complete interruption regression, Phase 04 checklist reconciliation, live deployment, OpenStack diagnostics, MCP, host diagnostics, and remediation.
