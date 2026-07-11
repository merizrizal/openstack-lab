## Architectural Design Specification: MCP Integration for Trusted AI-OPS Diagnostics

**Source:** `docs/ai-ops/implementation-plan/07-mcp-integration.md` (Phase 07)

**Goal:** Expose approved read-only AI-OPS diagnostics, curated context resources, and diagnostic workflow prompts through a local stdio MCP adapter while preserving the existing runner as the only execution and audit boundary.

---

### I. Overview and Contract

Phase 07 adds an interface over the proven local tool runner; it does not add a second executor or safety boundary.

```text
local AI client
  -> one local MCP stdio process running as assistant
  -> MCP discovery filtered by reviewed MCP exposure policy
  -> MCP tool call with declared JSON arguments
  -> existing aiops_tool_runner.py subprocess
  -> existing registry validation and fixed argv execution
  -> existing timeout, output bound, envelope, redaction, and audit path
  -> MCP structured result preserving the runner envelope
```

The MCP process must not execute diagnostic scripts directly, import and call `run_tool` as an alternate path, construct OpenStack or SSH commands, or accept a caller-selected executable. The subprocess boundary is preferred because it preserves the currently reviewed CLI, registry, exit behavior, and audit write as one indivisible path.

#### Transport and Process Lifecycle Contract (Proposed)

- Use the Python MCP SDK in the existing `/opt/openstack-ai-ops/.venv` after its exact compatible version is confirmed and pinned in Chunk 0.
- Use stdio only. The AI client starts one MCP process locally for its session.
- Do not bind a TCP, HTTP, SSE, or WebSocket listener and do not install a network-facing service in this phase.
- Run as the existing unprivileged `assistant` user. Do not use `sudo`, root, a service credential, or a second runtime identity.
- Reserve stdout for MCP protocol frames. Send only bounded, non-sensitive lifecycle diagnostics to stderr.
- Apply a default concurrency limit of one dispatched runner process per MCP process. A later increase requires measured resource bounds and proof that audit correlation remains reliable.
- Do not automatically retry tool calls. A retry is a distinct read and must receive a new request ID and audit event.

Local stdio has no protocol-level remote authentication requirement because no network endpoint exists. Access is controlled by local process identity, filesystem permissions, and the AI client's local MCP configuration. Any remote or multi-user transport requires a separate security design covering authentication, authorization, binding, TLS, rate limits, and tenant isolation.

#### Initial MCP Tool Exposure Contract (Proposed, Narrower Than Registry)

The runner registry remains the source of truth. MCP discovery is the intersection of:

1. a tool exists in `tool_registry.json`;
2. the registry entry is `available: true`;
3. the name is present in a reviewed MCP exposure allowlist; and
4. its risk class is enabled by MCP policy.

The initial MCP allowlist contains only:

- `project_resource_summary`;
- `server_basic_info`;
- `server_network_info`.

`neutron_agent_health` remains excluded while its registry entry is unavailable. The Phase 06 tools `recent_metadata_errors`, `recent_nova_errors`, and `recent_neutron_errors` are proven at the runner boundary but carry `high_readonly_restricted_host_scope`; MCP exposure must remain disabled by default and require an explicit reviewed opt-in. Opt-in must not change their exact host, fixed-kind, window, credential, timeout, output-limit, redaction, or forced-command restrictions.

Unknown, unavailable, or policy-excluded registry entries are not advertised. No MCP tool named or shaped as shell, command, SSH, sudo, OpenStack CLI passthrough, file access, database access, service control, credential access, or remediation may exist.

#### Registry-to-MCP Input Schema Contract (Proposed)

MCP input schemas are derived from reviewed registry argument definitions, not separately hand-maintained permissive schemas:

- every public argument is JSON `string`;
- `required: true` entries appear in JSON Schema `required`;
- registry `pattern` becomes JSON Schema `pattern` for client guidance;
- registry `allowed_values` becomes JSON Schema `enum`;
- registry defaults may be shown as JSON Schema defaults but the runner still applies and validates them;
- `additionalProperties` is `false`;
- `fixed_arguments` are never represented as client inputs;
- descriptions state read-only intent, credential class, risk class, and evidence limitations.

MCP schema validation improves client UX but is not trusted as enforcement. Every handler-dispatched request is converted only into repeated runner `--arg key=value` arguments, and the runner validates it again. Chunk 0 must confirm whether the selected SDK rejects schema-invalid calls before entering the handler. Tests must prove invalid known-tool parameters reach the runner and produce its correlated `validation_error`; if the SDK prevents that, implementation must use the lowest-level supported call handler that still delegates validation to the runner rather than adding a parallel validator/auditor.

#### Existing Runner Contracts (Concrete)

Confirmed source:

```text
ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py
```

Confirmed integration points:

```text
load_registry(path: str | Path) -> dict[str, Any]
validate_request(registry, tool_name, raw_args) -> (requested_tool, validated_args)
build_command_argv(requested_tool, validated_args) -> list[str]
run_tool(registry, requested_tool, validated_args) -> dict[str, Any]
build_result_envelope(...) -> dict[str, Any]
build_audit_event(envelope) -> dict[str, Any]
write_audit_event(path, event) -> None
main(argv) -> int
```

The runner uses `subprocess.run(..., shell=False)`, registry-derived fixed argv, per-tool timeouts, byte limits, secret-like argument omission, and JSON Lines audit events.

**Function Signature Contract (Conceptual):** add optional origin metadata to the runner without changing execution decisions or result fields:

```text
parse_cli_args(argv) -> Namespace containing optional --client-id and --transport
build_audit_event(envelope, *, client_id=None, transport=None) -> dict
```

For MCP calls, proposed bounded constants are `client_id="local-mcp-client"` and `transport="stdio"`; do not accept arbitrary client-provided labels in the first phase. These fields belong only in sanitized audit metadata. Existing manual callers remain compatible when the options are omitted. A fail-closed stub may reject non-constant or malformed origin values; it must not return a false success.

#### MCP Adapter Contracts (Conceptual)

Exact SDK decorators/types are intentionally deferred until Chunk 0 confirms the installed SDK API.

```text
load_mcp_policy(path) -> dict
load_runner_registry(path) -> dict
build_mcp_tool_schema(registry_tool) -> dict
list_exposed_tools(registry, policy) -> list[dict]
invoke_runner(tool_name, arguments, request_id, paths, timeout) -> dict
validate_runner_envelope(envelope, expected_tool, request_id) -> dict
map_envelope_to_mcp_result(envelope) -> MCP tool result
read_curated_resource(uri, resource_map) -> text
render_diagnostic_prompt(name, arguments, exposed_tools) -> prompt messages
main() -> process exit behavior required by the selected SDK
```

Stub behavior must fail closed with an explicit adapter-unavailable/protocol error. A stub must not return `status: ok`, synthetic diagnostic output, or a runner-shaped success before the runner actually executes.

`invoke_runner` must:

1. generate an adapter-controlled request ID with an `mcp-stdio-` prefix and random UUID;
2. construct argv containing only the fixed Python/runner path, fixed registry/audit paths, tool name, repeated declared `--arg` values, request ID, and fixed origin metadata;
3. use `shell=False`, no inherited caller command text, and no secret-bearing environment additions;
4. bound the outer subprocess wait to the reviewed tool timeout plus a small fixed adapter grace period;
5. parse exactly one JSON envelope from stdout;
6. verify `tool` and `request_id` match the dispatched request and required envelope fields exist;
7. ignore the runner process exit code as a status translation mechanism and use the validated envelope status; and
8. fail closed if output is absent, malformed, mismatched, oversized beyond the runner contract, or contains extra protocol noise.

The validated runner envelope remains unchanged:

- `tool`
- `status`: `ok`, `error`, `denied`, `validation_error`, `timeout`, `unavailable`, or `truncated`
- `arguments`
- `exit_code`
- `stdout`
- `stderr`
- `duration_ms`
- `truncated`
- `timestamp`
- `request_id`

Return it as MCP structured content when the confirmed SDK/protocol version supports structured content, plus one JSON text content item for compatible clients. Set MCP `isError=true` for `error`, `denied`, `validation_error`, `timeout`, and `unavailable`. Preserve `truncated` as partial evidence with `isError=false`, while retaining `status="truncated"` and `truncated=true`; clients must not mistake partial evidence for complete evidence.

#### MCP Resource Contract (Proposed)

Expose only three curated, packaged, read-only resources through fixed URIs:

| URI | Curated source basis | Purpose |
|---|---|---|
| `aiops://policy/diagnostic-safety` | approved diagnostic safety policy and runner prohibitions | Explain the non-mutation boundary. |
| `aiops://runbooks/metadata-troubleshooting` | metadata incident note plus the Phase 06 runbook | Explain evidence order without exposing raw host commands or sensitive payloads. |
| `aiops://architecture/lab-summary` | `docs/architecture.md` | Explain topology and service placement in a concise sanitized form. |

Repository documents are source material, not arbitrary runtime file targets. Implementation should package reviewed copies under the assistant role's MCP files and map fixed URI constants to fixed deployed files under `/opt/openstack-ai-ops/mcp/resources/`. The server must not join caller input to filesystem paths, support `file://`, enumerate directories, follow caller-selected symlinks, or read credentials, audit logs, diagnostic raw output, keys, known-host files, or system configuration.

#### MCP Prompt Contract (Proposed)

Expose fixed diagnostic workflow prompts:

- `metadata_diagnosis` — requires a safe server identifier; uses API tools first and references restricted host evidence only when those tools are explicitly exposed;
- `server_inspection` — requires one server name or ID and orders basic then network inspection;
- `project_summary` — uses project resource summary for high-level inventory questions.

Prompt output is instructions, not execution. Every prompt states: diagnostic-only, no remediation, no invented commands, use only discovered named tools, preserve request IDs and truncation/unavailable states, and explain healthy signals, failing signals, likely failure domain, evidence gaps, and manual next steps. Prompt arguments use the same conservative identifier rules where applicable. Prompts must not embed credentials, topology secrets, raw logs, audit lines, or executable shell examples.

### II. Observed Evidence and Assumptions

#### Observed Evidence

- `07-mcp-integration.md` requires a wrapper around the existing registry/runner, local stdio-first transport, identical safety/audit behavior, static resources, diagnostic prompts, integration tests, setup guidance, and reversible enablement.
- `00-implementation-overview.md` places MCP after the trusted runner and says MCP is an interface, not the safety boundary.
- `docs/ai-ops/prd.md` FR-036 through FR-039, NFR-016, and AC-018 through AC-019 require reviewed tools only, read-only resources/prompts, and no public unauthenticated or generic execution surface.
- The concrete registry is `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/tool_registry.json`; it is deny-by-default and currently contains three available low-risk API tools, one unavailable operator tool, and three available high-risk restricted-host tools.
- The concrete runner validates exact declared arguments, fixed arguments, allowed host lists, bounded windows, timeouts, output limits, argv-only execution, result envelopes, secret-like argument omission, and audit events.
- `docs/ai-ops/runtime/restricted-host-diagnostics.md` states that the runner is the only public entry point and that host tools must preserve exact aliases, kinds, and windows.
- The Phase 06 evidence snapshot records successful positive/negative runner validation, bounded/redacted host evidence, and correlated audits without retaining sensitive payloads.
- `assistant_runtime/defaults/main.yml` already creates `/opt/openstack-ai-ops/mcp`, uses user/group `assistant`, and defines one Python virtualenv.
- `assistant_runtime/tasks/tooling.yml` currently installs only OpenStack Python tooling; neither repository `requirements.txt` nor runtime package defaults include an MCP SDK.
- `assistant_runtime/tasks/scripts.yml` installs the runner and registry but no MCP artifacts.
- Existing focused tests are under `tests/ai_ops/test_tool_runner.py` and `tests/ai_ops/test_host_diagnostics.py`; there is no MCP test file yet.
- `docs/architecture.md`, `docs/troubleshooting/01-openstack-instance-metadata-503.md`, the approved-script safety policy, and the restricted-host runbook provide source material for curated resources.
- ADS work started from clean merged `main` on `ai-ops/07-mcp-integration-ads`; during drafting the checkout moved to `ai-ops/07-mcp-integration` at the same commit. No Phase 07 implementation existed during design.

#### Assumptions

- The initial AI client supports a local stdio MCP process on `assistant01`; the specific client remains unconfirmed.
- The official Python MCP SDK is preferred because the runtime is Python-based, but its exact package/version and API are proposed until verified.
- One-at-a-time dispatch is adequate for the lab and safer than unbounded concurrency.
- A subprocess adapter has acceptable overhead for bounded diagnostic calls.
- Curated resources may intentionally summarize repository documents to remove command-heavy or sensitive operational details.

#### Open Confirmations for Chunk 0

- Exact first AI client, MCP protocol revision, Python version, SDK package/version, structured-content support, and stdio launch syntax.
- Whether the SDK performs JSON Schema rejection before the call handler and how invalid known-tool calls can still use runner validation/audit.
- Exact SDK error and prompt/resource registration APIs.
- Maximum acceptable MCP frame/result size relative to the runner's current 131072-byte output limit.
- Whether client configuration can force the `assistant` identity and fixed environment without exposing profile contents.
- Whether optional runner audit origin fields are required by operators or request-ID prefix plus transport is sufficient.
- Final reviewed wording/content hashes for the three curated resources.
- Whether restricted-host MCP exposure remains entirely deferred or is tested as an explicit disabled-by-default policy branch in Phase 07.

### III. Required Technical Dependencies and Imports

#### Proposed Runtime Dependency

- Python MCP SDK package, exact name/version pinned only after Chunk 0 compatibility validation.
- Existing Python standard-library modules should cover adapter support: `argparse`, `json`, `os`, `pathlib`, `subprocess`, `sys`, `time`, `uuid`, and typing/dataclass helpers as needed.
- No shell library, SSH SDK, OpenStack SDK call, HTTP server framework, file browser, database client, or remediation dependency belongs in the MCP adapter.

#### Proposed Repository Artifacts

Paths are proposed and must be confirmed in Chunk 0:

```text
ansible/ai_ops_runtime/roles/assistant_runtime/files/mcp/aiops_mcp_server.py
ansible/ai_ops_runtime/roles/assistant_runtime/files/mcp/resources/diagnostic-safety.md
ansible/ai_ops_runtime/roles/assistant_runtime/files/mcp/resources/metadata-troubleshooting.md
ansible/ai_ops_runtime/roles/assistant_runtime/files/mcp/resources/lab-architecture.md
ansible/ai_ops_runtime/roles/assistant_runtime/templates/mcp/mcp_policy.json.j2
tests/ai_ops/test_mcp_server.py
ansible/ai_ops_runtime/playbook_validate_phase07_mcp_integration.yml
docs/ai-ops/runtime/mcp-integration.md
```

Proposed runtime paths:

```text
/opt/openstack-ai-ops/mcp/aiops_mcp_server.py
/opt/openstack-ai-ops/mcp/mcp_policy.json
/opt/openstack-ai-ops/mcp/resources/*.md
/opt/openstack-ai-ops/.venv/bin/python
/opt/openstack-ai-ops/scripts/tool_runner/aiops_tool_runner.py
/opt/openstack-ai-ops/scripts/tool_runner/tool_registry.json
/opt/openstack-ai-ops/audit/tool-runner.jsonl
```

Ansible defaults should define fixed source/runtime paths, the low-risk initial allowlist, a boolean restricted-host exposure defaulting to `false`, concurrency `1`, and a small outer timeout grace. Policy rendering must reject unknown names and must never broaden the runner registry.

### IV. Step-by-Step Procedure / Execution Flow

1. The local AI client starts the configured MCP command through the runtime virtualenv as `assistant`; no listener is opened.
2. The server loads the reviewed MCP policy and runner registry. Invalid/missing JSON, duplicate names, unknown policy tools, forbidden risk classes, or unsafe resource mappings fail startup.
3. The server computes the exposure intersection and registers only eligible tools. It derives schemas from registry declarations with `additionalProperties=false`; it never exposes fixed arguments.
4. The server registers only fixed curated resource URIs and fixed diagnostic prompt names.
5. For a tool request, the handler checks that the requested name is in the startup exposure snapshot. This is interface policy only; it does not replace runner validation.
6. The handler converts JSON scalar strings into ordered `--arg key=value` argv entries. Missing, unknown, or malformed string arguments reach the runner's validation seam where the SDK permits. Non-string JSON values are rejected as MCP type errors because the runner CLI contract accepts strings; they are never coerced into command text or misrepresented as runner validation.
7. The adapter creates a unique `mcp-stdio-<uuid>` request ID and invokes the existing runner with fixed paths and `shell=False`.
8. The runner reloads its registry, denies unknown/unavailable tools, validates all arguments/defaults, builds fixed argv, executes the reviewed script/connector, applies timeout/output limits, builds the envelope, and appends the audit event.
9. The adapter parses and verifies one envelope. It does not expose runner stderr outside the bounded envelope or log raw output separately.
10. The adapter maps the unchanged envelope to MCP structured/text content and error signaling. The client correlates the result using `request_id`.
11. Resource requests resolve only fixed URI-map entries. Prompt requests render only fixed text and list only currently exposed tools.
12. On client disconnect or EOF, the MCP process exits. It leaves the runner, registry, credentials, audit file, and OpenStack Lab state unchanged.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
|---|---|---|---|
| Startup | MCP SDK missing or incompatible | Fail before advertising capabilities; emit one sanitized stderr message. | Process exits non-zero; runner remains usable manually. |
| Startup | MCP policy/registry missing, malformed, duplicate, or inconsistent | Fail closed; do not register a subset guessed from defaults. | Process exits non-zero with bounded configuration error. |
| Discovery | Policy names a tool absent/unavailable in registry | Exclude it and fail startup in strict mode so drift is reviewed. | No MCP session until policy is corrected. |
| Discovery | Forbidden/generic capability appears | Reject startup through explicit forbidden-name/capability tests and review. | No tools exposed. |
| Request decode | Invalid MCP frame or unknown MCP tool | Return protocol error; do not execute any subprocess. | Session remains usable if SDK permits. |
| Schema/arguments | Missing, unknown, unsafe, host, or window string argument | Route known-tool calls through runner validation when the SDK permits. Reject non-string JSON as a protocol type error without coercion. | Preserve runner `validation_error` and audit request ID for dispatched string requests; report pre-handler protocol rejection as a Chunk 0-resolved limitation. |
| Policy | Tool exists in runner but is not MCP-exposed | Do not invoke runner; return MCP authorization/unavailable error without revealing hidden implementation details. | No diagnostic execution. |
| Runner launch | Executable/path/permission error | Return fail-closed adapter error; never fall back to shell or direct script. | Manual runner remains available for operator diagnosis. |
| Runner timeout | Runner reports timeout | Preserve exact `timeout`, bounded streams, and request ID. | `isError=true`; no automatic retry. |
| Outer timeout | Runner exceeds per-tool timeout plus grace | Terminate only the runner subprocess group if safely supported; report adapter timeout and audit-correlation uncertainty. | Operator reviews runner/audit health before retry. |
| Runner result | Non-zero exit with valid envelope | Ignore exit code as translation logic; map the envelope's validated status. | Exact runner failure/truncation state returned. |
| Runner result | Empty, multiple, malformed, oversized, wrong-tool, or wrong-request-ID envelope | Reject as `ERR_MCP_RUNNER_ENVELOPE` (proposed); do not synthesize success. | Security/contract failure requiring operator review. |
| Audit | Runner cannot append audit event | Existing runner converts outcome to `error`; adapter preserves it. | No successful MCP result is claimed. |
| Resource | Unknown URI or missing curated file | Return not found/unavailable; never search another directory. | Other fixed resources remain available. |
| Resource | Curated content fails secret/static review | Block deployment or startup based on manifest/hash validation. | Resource is not exposed. |
| Prompt | Unsupported prompt or unsafe argument | Return validation error; do not generate commands or execute tools. | Session remains diagnostic-only. |
| Disconnect | Client closes stdio during a call | Cancel/terminate adapter-owned child safely where supported; do not kill unrelated processes. | Process exits; any completed runner audit remains. |

### VI. Security, Integrity, Idempotency, and Cleanup

- **Security boundary:** MCP is only an adapter. Registry decisions, exact argument validation, fixed argv, credentials, restricted SSH/sudo, timeout, output bounds, redaction, envelope creation, and audit remain in the runner and downstream reviewed tools.
- **Local binding:** stdio only; no listening socket, remote bind, port forwarding, or unauthenticated endpoint.
- **Identity:** run as `assistant`; MCP files and policy are repository-managed with non-writable-by-other modes. Do not grant MCP root or new credentials.
- **Exposure:** the MCP allowlist may narrow but never expand registry availability. Restricted-host tools are disabled by default and cannot accept a host, kind, or window beyond registry policy.
- **Command safety:** use fixed absolute paths and `shell=False`. Never pass a command string, environment-selected runner, caller-selected registry/audit path, arbitrary working directory, or user-controlled executable.
- **Input integrity:** derive schema from registry; set `additionalProperties=false`; still delegate final decisions to the runner. Fixed arguments remain invisible and immutable.
- **Result integrity:** require matching tool/request ID and all concrete envelope fields. Preserve status, truncation, errors, and bounded streams exactly; do not merge protocol logs into stdout.
- **Audit integrity:** every handler-dispatched call receives a unique request ID. Optional fixed `client_id`/`transport` metadata must be sanitized and must not include prompt text, resource contents, raw payloads, credentials, keys, or arbitrary client claims.
- **Resource integrity:** fixed URI-to-file map only. Curated copies are reviewed for drift and secrets. No arbitrary file read, glob, directory listing, symlink traversal, or dynamic URI path resolution.
- **Prompt safety:** prompts recommend manual next steps only and cannot define or invoke generic command/remediation tools.
- **Confidentiality:** never include credentials, tokens, private keys, known-host contents, cloud profile contents, raw audit lines, raw protected host payloads, or secret-bearing configuration in MCP logs, resources, prompts, tests, documentation, or evidence.
- **Concurrency:** default semaphore/worker limit is one. No unbounded task creation or subprocess fan-out.
- **Idempotency:** discovery, resources, and prompts are read-only. Tool calls are observational but can return time-varying data; they are not automatically retried. Each explicit retry creates a distinct audit event.
- **Deployment idempotency:** Ansible package, directory, copy, and template tasks must converge without restarting OpenStack services or changing lab resources.
- **Cleanup:** on cancellation/EOF, close stdio and terminate only adapter-owned runner children. Do not delete audit events or diagnostic evidence as cleanup.
- **Rollback:** remove/disable the AI client's MCP command first; remove MCP adapter/policy/resources and optionally its SDK dependency through Ansible; retain the local runner and audit records. Rollback must not revoke unrelated read-only credentials or modify OpenStack state.

### VII. Validation Strategy

Validation is chunk-aware and starts locally before deployment.

- **Python syntax:** `rtk python3 -m py_compile <changed-python-files>` using a temporary virtualenv if MCP imports must execute locally.
- **JSON syntax:** `rtk python3 -m json.tool <policy-or-registry.json>`.
- **Ansible syntax:** `rtk ansible-playbook --syntax-check -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml` and the Phase 07 validation playbook.
- **Formatter:** use the repository's established Python formatting if confirmed in Chunk 0; otherwise do not introduce a formatter dependency solely for this phase.
- **Targeted tests:** `rtk python3 -m unittest tests.ai_ops.test_tool_runner tests.ai_ops.test_mcp_server` plus host tests when restricted-host exposure policy is touched.
- **Symbol checks:** `rtk grep -RniE "def (load_mcp_policy|build_mcp_tool_schema|invoke_runner|validate_runner_envelope|main)" ansible/ai_ops_runtime/roles/assistant_runtime/files/mcp tests/ai_ops`.
- **Safety scan:** verify no listener/server transport, shell execution, generic command tool, arbitrary file mapping, secret literal, or remediation action is introduced.
- **Discovery tests:** exact initial three tools; unavailable/operator and restricted-host tools absent by default; forbidden generic capabilities absent.
- **Schema tests:** no additional properties; required identifiers; exact enum host/window behavior; no fixed diagnostic-kind input; registry drift fails closed.
- **Equivalence tests:** valid and invalid calls preserve the runner envelope fields/status/request ID and produce correlated sanitized audit metadata.
- **Resource/prompt tests:** exact fixed names/URIs, no arbitrary paths, no obvious secret patterns, diagnostic-only wording, and safe behavior when restricted tools are disabled.
- **Runtime smoke:** launch through the selected AI client or an MCP inspector over stdio; list tools/resources/prompts; call one low-risk tool; reject invalid parameters; verify audit correlation; prove no listening socket is created.
- **Deployment/idempotency:** run setup twice and require no changes on the second run, then execute rollback/client disablement without affecting the manual runner.
- **Final review:** `rtk git status --short`, `rtk git diff --stat`, and `rtk git diff -- <Phase-07-files>`; evidence must remain sanitized.

A broad `go test ./...` or unrelated full-stack deployment is not applicable because Phase 07 is Python/Ansible scoped. Existing OpenStack workflows must remain unchanged; runtime validation should invoke only read-only diagnostics.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass. Each chunk must be independently validated, diff-reviewed, and stopped before the next chunk.

#### Chunk 0: Discovery and Integration Confirmation

- **Goal:** Resolve SDK/client/protocol behavior and all remaining security contracts without editing.
- **Files to read:** this ADS, Phase 07 plan, runner/registry, runtime defaults/tasks, selected AI client documentation/config, and candidate SDK documentation/version metadata.
- **Commands:** inspect branch/status; inspect Python/runtime versions and installed packages; run a throwaway stdio SDK probe in `/tmp` if needed; do not alter repository/runtime state.
- **Evidence to confirm:** exact SDK package/version/API, structured results, pre-handler validation, process identity, launch command, frame/output bounds, cancellation behavior, resource/prompt APIs, and restricted-host exposure decision.
- **Stop condition:** no edits; decisions, commands, evidence, and blockers are recorded in a handoff.

#### Chunk 1: Runner Origin Metadata Compatibility

- **Goal:** Add optional fixed MCP origin metadata to existing audit events without changing execution or envelope behavior.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py`
  - `tests/ai_ops/test_tool_runner.py`
- **Symbols to add/change:** CLI options and `build_audit_event` optional metadata handling.
- **Implementation shape:** Start with optional fields defaulting to absent. Accept only bounded safe labels or fixed reviewed values; preserve all old call sites and tests. Do not add MCP code.
- **Validation:** Python compile; targeted runner tests for old behavior, fixed origin fields, rejection/redaction, and unchanged result envelope.
- **Stop condition:** manual runner compatibility is green and no MCP capability exists.

#### Chunk 2: MCP Contracts and Fail-Closed Server Stub

- **Goal:** Add importable MCP adapter contracts that start over stdio but advertise no executable tools.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/files/mcp/aiops_mcp_server.py` (proposed new file)
  - `tests/ai_ops/test_mcp_server.py` (proposed new file)
- **Symbols to add/change:** policy/registry loaders, adapter configuration, SDK entrypoint, explicit unavailable invocation stub.
- **Implementation shape:** Use the confirmed SDK. Startup validates fixed paths/config; tool list is empty; call stub returns a clear failure and cannot synthesize success. No network transport or runner execution.
- **Validation:** temporary-venv dependency install, Python compile, focused startup/fail-closed tests, no-listener static check, scoped diff.
- **Stop condition:** stdio server initializes and exits cleanly while exposing no executable capability.

#### Chunk 3: Registry-Derived Discovery for One Tool

- **Goal:** Advertise only `project_resource_summary` with a schema derived from the concrete registry, still without execution.
- **Files to change:** MCP server and MCP tests only.
- **Symbols to add/change:** `build_mcp_tool_schema`, exposure intersection, forbidden-capability checks.
- **Implementation shape:** Implement strict registry/policy validation and one low-risk policy constant/fixture. Keep invocation fail-closed. Reject unavailable, unknown, duplicate, malformed, and generic capabilities.
- **Validation:** focused discovery/schema/drift tests; verify exact one-tool discovery and no generic command surface.
- **Stop condition:** one safe tool is discoverable, but calls still return explicit unavailable and no runner is launched.

#### Chunk 4: First End-to-End Runner Call

- **Goal:** Execute `project_resource_summary` through the existing runner and return its exact envelope through MCP.
- **Files to change:** MCP server and MCP tests only.
- **Symbols to add/change:** `invoke_runner`, `validate_runner_envelope`, `map_envelope_to_mcp_result`.
- **Implementation shape:** Fixed argv, request-ID prefix, fixed origin metadata, outer timeout grace, single concurrency slot, strict JSON/envelope verification. Mock subprocess for failure cases and use a temporary fake reviewed runner fixture for the local success seam; do not execute OpenStack in unit tests.
- **Validation:** valid envelope, runner error, timeout, malformed/multiple/mismatched envelope, audit-failure envelope, cancellation, and shell-disabled tests.
- **Stop condition:** one complete MCP-to-runner-to-envelope slice is green; no argument-bearing or host tool is exposed.

#### Chunk 5: Complete Low-Risk Tool and Argument Slice

- **Goal:** Add `server_basic_info` and `server_network_info` with registry-derived identifier schemas and runner-owned validation.
- **Files to change:** MCP server and MCP tests only.
- **Symbols to add/change:** argument conversion, SDK handler seam, initial low-risk allowlist.
- **Implementation shape:** Add one argument-bearing tool at a time. Prove missing/unsafe/unknown arguments preserve runner `validation_error` and audit correlation. Stop and redesign the handler seam if SDK pre-validation bypasses runner audit.
- **Validation:** exact three-tool discovery; valid identifiers; runner-audited missing/metacharacter/unknown string arguments; adapter-rejected non-string values; extra parameters; no unavailable/operator/host/generic tools.
- **Stop condition:** all three initial tools work through the same runner path and every dispatched call has one correlated audit event.

#### Chunk 6: Curated Resources and Diagnostic Prompts

- **Goal:** Add fixed read-only context and repeatable non-remediating workflows without arbitrary file access.
- **Files to change:**
  - three proposed curated resource Markdown files under the assistant role MCP resources directory;
  - MCP server and `tests/ai_ops/test_mcp_server.py` for fixed registration.
- **Symbols to add/change:** fixed URI map, `read_curated_resource`, fixed prompt registry, `render_diagnostic_prompt`.
- **Implementation shape:** The five-file exception is justified because each resource is independently reviewable content while server/tests provide one narrow read-only registration slice. Resource paths are constants; prompts name only exposed tools and never execute.
- **Validation:** exact URI/prompt discovery, unknown URI rejection, traversal/symlink tests, secret-pattern scan, prompt wording/argument tests, and scoped content review.
- **Stop condition:** three curated resources and three prompts are available; no file browser, command example generator, or remediation flow exists.

#### Chunk 7: Restricted-Host Opt-In Policy

- **Goal:** Encode and test a disabled-by-default MCP policy for Phase 06 tools without weakening their runner controls.
- **Files to change:**
  - proposed `templates/mcp/mcp_policy.json.j2`
  - `tests/ai_ops/test_mcp_server.py`
- **Symbols to add/change:** low-risk allowlist, high-risk opt-in flag/list, policy validation fixtures.
- **Implementation shape:** Default policy renders only the three API tools. Test explicit host opt-in against registry risk class, exact names, fixed arguments, host enums, and window enums. Do not enable host exposure in deployed defaults during this chunk.
- **Validation:** template render/JSON syntax; policy tests proving default exclusion, explicit-only inclusion, no kind override, exact aliases/windows, and runner-delegated calls.
- **Stop condition:** the policy mechanism can narrow safely; deployed restricted-host exposure remains false.

#### Chunk 8: Deployment and Local Client Slice

- **Goal:** Deploy the MCP adapter, dependency, policy, and resources idempotently for local stdio use.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/tooling.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/scripts.yml`
- **Symbols to add/change:** pinned SDK package/defaults, MCP paths/policy variables, directory/copy/template tasks.
- **Implementation shape:** Three files are required to connect package, policy, and artifact deployment. Keep restricted-host exposure false, modes minimal, identity `assistant`, and transport stdio. Do not install a system service or open a port.
- **Validation:** Ansible syntax; targeted deploy; owner/group/mode and package checks; stdio startup/list discovery; no listening socket; second-run idempotency; manual runner regression.
- **Stop condition:** a local client can launch the deployed server and discover only the initial safe surface; OpenStack state is unchanged.

#### Chunk 9: Runtime Validation, Runbook, Rollback, and Evidence

- **Goal:** Prove Phase 07 externally and document safe enable/disable operation before updating phase status.
- **Files to change:**
  - `ansible/ai_ops_runtime/playbook_validate_phase07_mcp_integration.yml` (proposed)
  - `docs/ai-ops/runtime/mcp-integration.md` (proposed)
  - `docs/ai-ops/runtime/phase07-mcp-integration-evidence-<date>.md` only after successful execution
  - `docs/ai-ops/implementation-plan/07-mcp-integration.md` validated checkboxes only
- **Symbols to add/change:** discovery/call/resource/prompt/negative assertions, local client setup, rollback, sanitized evidence, accurate completion state.
- **Implementation shape:** Four files are justified by separate executable validation, operator guidance, immutable evidence, and plan status. Validate low-risk tools first. Record only names, schemas, statuses, request-ID correlation metadata, modes, and sanitized assertions—not raw payloads/audit lines.
- **Validation:** syntax and runtime playbook; valid/invalid calls; exact discovery; resource/prompt checks; audit correlation; no network listener; disable/rollback; secret scan; final scoped diff/security review.
- **Stop condition:** Phase 07 definition of done has sanitized proof; unchecked failures remain documented; Phase 99 hardening has not begun.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.
Activate rtk-command-prefix for shell commands.

Task:
Implement Phase 07 MCP Integration from docs/ai-ops/implementation-plan/07-mcp-integration.md using docs/ai-ops/implementation-plan/ads/07-mcp-integration-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm the AI client, Python/MCP SDK version and API, stdio lifecycle, schema-validation handler behavior, structured result support, process identity, output limits, cancellation, resource/prompt API, audit-origin requirement, and restricted-host exposure decision. Write a handoff and stop.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Use the Phase 07 ADS and latest handoff.
Execute Chunk 1 only.
Do not continue to Chunk 2.
After editing, run targeted validation, review git diff, assess security risk, write the Chunk 1-to-2 handoff, and stop.
```

For later chunks:

```text
Use the chunked-implementation skill.
Resume from the latest Phase 07 handoff.
Execute exactly the next approved chunk only.
Do not expose later tools, enable restricted-host capabilities, add a network transport, or update phase completion early.
Run chunk-specific validation, review the scoped diff, assess security risk, write the next handoff, and stop.
```

### X. Conclusion and Next Steps

Phase 07 should make the trusted local diagnostics easier for an AI client to discover and call without increasing execution authority. The preferred design is a local Python stdio adapter that derives narrow schemas from the reviewed registry, delegates every dispatched call to the existing runner process, preserves exact envelopes and audit correlation, exposes only curated static resources and diagnostic prompts, and keeps restricted-host tools disabled by default.

The next implementation action is Chunk 0 only: confirm the concrete MCP client/SDK behavior and close the remaining protocol/audit questions before any executable MCP artifact is added. Phase 07 implementation, deployment, runtime validation, and checklist updates remain future work.
