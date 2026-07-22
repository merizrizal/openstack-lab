## Architectural Design Specification: Local MCP Tool Loop, Redaction, and Metadata Evidence

**Source:** `docs/ai-ops/implementation-plan/10-mcp-tool-loop-redaction-and-evidence.md`

**Goal:** Connect the fake-backed repository orchestrator to the reviewed local stdio MCP adapter and authoritative runner, enforce fail-closed input and tool-result handling before fake-model observation, bound the tool loop, and emit a separate versioned metadata-only evidence contract without enabling Codex, credentials, provider access, remote MCP, deployment, or egress changes.

**Status:** Draft for review. Implementation must begin with Chunk 0 and keep `OfficialCodexAdapter` disabled.

---

### I. Overview and Contract

#### Selected local execution boundary

```text
synthetic operator request
  -> LocalOrchestrator validates closed request and workflow
  -> repository redactor bounds, classifies, redacts, and leak-scans context
  -> FakeCodexAdapter emits one typed tool request
  -> LocalOrchestrator validates order, allowlist, arguments, and cumulative policy
  -> LocalMcpClient launches the fixed local stdio adapter
  -> MCP adapter delegates to the authoritative runner
  -> LocalMcpClient validates the MCP result envelope
  -> repository redactor independently bounds, redacts, and leak-scans result
  -> only SafeToolResult reaches FakeCodexAdapter
  -> untrusted advisory text is validated
  -> versioned orchestrator metadata is validated and written
  -> MCP streams/process close on success, rejection, timeout, or cancellation
```

The orchestrator owns workflow, tool-selection, redaction, cumulative limits, evidence, cancellation, and cleanup policy. The existing MCP adapter remains the interface to the existing runner; it does not become a second executor or safety boundary. The runner continues to own its registry, fixed script argv, credential profile selection, subprocess timeout, output truncation, structured status, and audit event.

Phase 10 proves the pre-model boundary only with `FakeCodexAdapter`. It does **not** prove that the public Codex SDK can intercept a tool result before the Codex runtime consumes it. `OfficialCodexAdapter` therefore remains disabled after Phase 10. A future real-adapter path must either demonstrate a supported interception seam or introduce a separately reviewed local stdio policy adapter.

#### Existing contracts retained (concrete)

- `DiagnosticTurnRequest.from_mapping()` accepts exactly `workflow`, `correlation_id`, and `redacted_context`, each a non-empty string.
- The sole implemented workflow is `project_resource_summary`.
- `RuntimePolicy` already bounds workflow deadline, event count, output bytes, and turn count.
- `AdapterEventType` already reserves `TOOL_STARTED` and `TOOL_COMPLETED`, although the current lifecycle validator rejects tool events and any event metadata.
- The default deployed MCP surface is exactly:
  - tools: `project_resource_summary`, `server_basic_info`, `server_network_info`;
  - resources: `aiops://policy/diagnostic-safety`, `aiops://runbooks/metadata-troubleshooting`, `aiops://architecture/lab-summary`;
  - prompts: `metadata_diagnosis`, `server_inspection`, `project_summary`.
- Restricted-host tools remain disabled by default.
- Runner result categories are `ok`, `error`, `denied`, `validation_error`, `timeout`, `unavailable`, and `truncated`.
- The fixed deployed MCP command is `/opt/openstack-ai-ops/.venv/bin/python /opt/openstack-ai-ops/mcp/aiops_mcp_server.py`.

#### Local MCP client contract

**Function Signature Contract (Conceptual):** inferred from the Phase 10 plan and the Phase 07 validation client; confirm in Chunk 0.

A proposed `LocalMcpClient` owns one stdio session per workflow and exposes typed operations equivalent to:

- `open()` / async context entry: launch only a fixed executable and argument tuple, initialize MCP, discover tools/resources/prompts, and reject any surface drift before model lifecycle begins;
- `call_tool(request) -> RawMcpToolResult`: execute one already-validated allowlisted request with a per-call timeout and return an internal raw result that cannot be passed to an adapter;
- `close()` / async context exit: close session/streams and wait for deterministic child cleanup on every terminal path.

The temporary compile-safe stub must raise a fixed `MCP_CLIENT_NOT_READY`-style error (proposed), not return success, because false success would claim a validated MCP boundary that does not yet exist.

The production constructor must not accept caller-supplied executable paths, shell strings, URLs, environment mappings, bearer tokens, OAuth settings, or remote transport. Tests may inject an explicitly test-only process/session factory; that seam must not be exported as runtime configuration.

#### Tool-loop contracts

**Type Contract (Conceptual):** proposed `ToolCallRequest`.

- exact fields: tool name, closed string-to-string arguments, and a non-secret request sequence number;
- tool name must belong to the workflow-specific allowlist;
- arguments must use exact fields, bounded strings, and no duplicate or unknown names;
- the initial Phase 10 success slice permits one `project_resource_summary` call with no arguments;
- server-identifier workflows remain deferred until their workflow contracts and synthetic identifier fixtures are accepted.

**Type Contract (Conceptual):** proposed `SafeToolResult`.

- contains only allowlisted status/category fields, bounded redacted textual content needed by the fake, truncation metadata, and non-secret counters;
- cannot be constructed directly from unvalidated MCP objects;
- excludes raw `CallToolResult`, raw runner envelopes, exceptions, process output, audit lines, and rejected values;
- construction succeeds only after exact-field/type checks, byte bounds, redaction, and a post-redaction leak scan.

**Adapter Handshake Contract (Conceptual):** the fake lifecycle must expose a typed tool request to `LocalOrchestrator`, and the orchestrator must return only `SafeToolResult`. The exact method names are deferred to Chunk 0. A likely compile-safe shape is a closed adapter-step union plus a result-submission method; no raw MCP value may appear in `AdapterEvent` or `AdapterResult`.

#### Redaction contract

**Function Signature Contract (Conceptual):** proposed pure functions in an orchestrator-owned `redaction.py` module.

- input redaction accepts bounded text and returns an immutable redacted value plus classification/count metadata;
- tool-result redaction accepts the validated internal MCP envelope, independently validates JSON-compatible content, rejects duplicate keys/binary/non-finite/ambiguous/oversized values, redacts protected labels and discovered protected values, then leak-scans the rebuilt safe result;
- errors expose fixed categories only and never include raw values;
- shared protected-marker fixtures prove parity with reviewed historical rules without importing the provider-gateway module or coupling to its payload schema.

A redaction stub must fail with a fixed policy error. A pass-through stub is prohibited.

#### Orchestrator evidence contract

**Type Contract (Conceptual):** proposed `OrchestratorEvidenceRecord` schema version `1`, independent of all provider-gateway schema versions.

Each JSON Lines record has an exact bounded field allowlist covering only:

- schema version and UTC timestamp;
- correlation identifier and reviewed workflow;
- closed event category and workflow state;
- fixed error category or `null`;
- input classification category;
- allowlisted tool name or `null`;
- runner/MCP result category or `null`;
- bounded event, turn, tool-call, redaction, and content-byte counters;
- truncation and cleanup outcome categories.

Records must never contain prompts, model text, raw context, arguments, tool output, stdout, stderr, headers, routes, credentials, account data, SDK events, exception text, audit lines, filesystem/runtime-home paths, or provider metadata. The serializer accepts only the new dataclass. The parser rejects duplicate keys, extra/missing fields, wrong types, unsupported versions, excessive record size, invalid categories, and impossible event/state combinations. A sequence validator accepts only `workflow_started -> zero or more tool_completed -> workflow_terminal`, with monotonic bounded counters and exactly one terminal record.

**Writer Contract (Conceptual):** an injected evidence writer validates serialized bytes before appending. Local acceptance uses only a bounded temporary file. A production evidence path, service ownership, retention policy, and deployment are deferred to Phase 11. Evidence failure overrides apparent workflow success and returns `EVIDENCE_FAILED` without raw exception text.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops/implementation-plan/10-mcp-tool-loop-redaction-and-evidence.md` requires local stdio lifecycle, exact capability allowlists, independent pre-model result redaction, bounded turns/calls/concurrency/content, a separate metadata parser, and fake-Codex end-to-end validation.
- `ansible/ai_ops_runtime/files/orchestrator/src/openstack_ai_ops_orchestrator/contracts.py` contains closed request/state/event/result contracts, but `RuntimePolicy` has no tool-call, concurrency, per-call, or cumulative MCP content limits.
- `ansible/ai_ops_runtime/files/orchestrator/src/openstack_ai_ops_orchestrator/orchestrator.py` injects context redaction and metadata recording. It currently rejects all tool events and event metadata, and `WorkflowMetadata` is neither versioned nor serialized.
- `ansible/ai_ops_runtime/files/orchestrator/src/openstack_ai_ops_orchestrator/fake_codex_adapter.py` emits a finite thread/turn sequence only; it has no typed tool-request/result handshake.
- `ansible/ai_ops_runtime/files/orchestrator/requirements.in` has no `mcp` client dependency, while the assistant runtime separately pins `mcp==1.28.1`.
- `ansible/ai_ops_runtime/roles/assistant_runtime/files/mcp/aiops_mcp_server.py` validates fixed policy/registry inputs, exposes the reviewed surface, limits runner envelope size, uses `asyncio.create_subprocess_exec`, applies one-call concurrency, terminates cancelled/timed-out children, and serves only through `stdio_server()`.
- The same MCP server's `map_envelope_to_mcp_result()` serializes the validated envelope directly into both text and `structuredContent`. The envelope includes arguments, stdout, and stderr. It is therefore not an independent pre-model redaction boundary.
- `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py` validates allowlisted tools/arguments, uses fixed argv with `shell=False`, enforces timeout/output limits, and preserves structured categories. Its `sanitize_arguments()` omits secret-like argument **names**, but it does not provide the Phase 10 independent stdout/stderr result redaction contract.
- `ansible/ai_ops_runtime/playbook_validate_phase07_mcp_integration.yml` demonstrates the concrete client APIs `StdioServerParameters`, `stdio_client`, and `ClientSession`, validates discovery and no-listener delta, and confirms adapter exit after disconnect. Its temporary client summarizes results and does not implement the Phase 10 fake-model loop.
- `docs/ai-ops/runtime/phase07-mcp-lifecycle-evidence-2026-07-12.md` records successful deployed lifecycle, stdio-only operation, cleanup, and 58 runner/MCP regressions.
- `docs/ai-ops/runtime/phase08-orchestrator-local-validation-evidence.md` records 23 passing package tests and confirms no MCP, Codex, credential, listener, DNS, provider, deployment, or egress boundary was entered.
- Provider-gateway modules contain useful strict-JSON, duplicate-key, exact-field, serializer/parser, and bounded-writer patterns. The Phase 10 plan and architecture decision explicitly prohibit reuse or migration of provider-gateway evidence schemas and require historical ledgers to remain untouched.
- No standalone repository Python test directory for `aiops_mcp_server.py` was found. Existing MCP integration validation is primarily the Ansible playbook and live evidence.

#### Assumptions

- `mcp==1.28.1` remains the accepted MCP client/server version, but adding it to the orchestrator lock is a supply-chain change that Chunk 0 must verify before implementation.
- One workflow owns one MCP process/session. There is no pooling, daemon, listener, or reuse across workflows.
- Initial concurrency is exactly one active workflow and one in-flight tool call. Queueing and retries are disabled.
- The real deployed adapter/runner acceptance on `assistant01` requires explicit approval and occurs only in the final acceptance chunk. Earlier chunks use fakes or a test-only stdio fixture and perform no OpenStack/provider access.
- The existing runner status values are preserved as categories after content redaction; no raw runner reason text is required by the fake.
- A temporary local evidence writer is sufficient for Phase 10 design/acceptance; production placement belongs to Phase 11.

#### Open confirmations for Chunk 0

- Confirm whether direct `ClientSession` consumption is the accepted Phase 10 pre-model boundary for the fake, while the official adapter remains blocked.
- Confirm exact fixed client command/arguments for repository-local tests versus approved live `assistant01` acceptance; runtime paths must never become caller input.
- Confirm whether the orchestrator lock may add `mcp==1.28.1` and all resolved hashes without changing the assistant-runtime MCP pin.
- Confirm the exact three tool/resource/prompt names and default restricted-host denial against current policy and registry.
- Confirm the protected-marker fixture classes and whether identity labels as well as secrets must be redacted in both operator context and tool results.
- Confirm initial numeric policy values for maximum calls, per-call timeout, cumulative result bytes, cleanup timeout, and maximum evidence record/ledger bytes.
- Confirm whether the final live synthetic workflow may call `project_resource_summary`; if not explicitly approved, stop after fixture-backed local stdio acceptance.

### III. Required Technical Dependencies and Imports

| Dependency/artifact | Policy | Evidence/gate |
|---|---|---|
| Python | Existing package baseline `>=3.12` | Current `pyproject.toml` |
| `mcp` | Proposed exact `1.28.1` in orchestrator input/lock | Matches assistant runtime; Chunk 0 supply-chain confirmation required |
| `openai-codex` | Preserve exact `0.144.4`; never invoke in Phase 10 | Existing disabled adapter contract |
| stdlib | `asyncio`, `contextlib`, `dataclasses`, `enum`, `json`, bounded `pathlib` use, typing/collections protocols | No shell or network client imports |
| MCP client API | `ClientSession`, `StdioServerParameters`, `stdio_client` | Concrete usage exists in Phase 07 validator |
| MCP adapter and runner | Existing files remain authoritative | No second runner or direct script execution |
| evidence storage | Proposed injected protocol and temporary bounded JSONL implementation | Production path/deployment deferred |

Dependency rules:

- Update `requirements.in` and regenerate `requirements.lock` only through the existing hash-locked procedure in a `/tmp` virtual environment.
- Do not import code from `roles/ai_client_runtime/files/provider_gateway/` into the orchestrator.
- Do not import or call the runner or diagnostic scripts directly from the orchestrator.
- Do not add HTTP clients, socket listeners, SSH libraries, OpenStack clients, database drivers, shell wrappers, filesystem mutation tools, or provider-gateway dependencies.
- Tests must inject fake sessions/processes until a separately approved local stdio acceptance. No test may inspect credential or runtime-home paths.

Expected new package modules are proposed until Chunk 0 confirms names:

```text
src/openstack_ai_ops_orchestrator/mcp_client.py
src/openstack_ai_ops_orchestrator/redaction.py
src/openstack_ai_ops_orchestrator/evidence.py
```

Expected focused tests are correspondingly proposed:

```text
tests/test_mcp_client.py
tests/test_redaction.py
tests/test_evidence.py
```

### IV. Step-by-Step Procedure / Execution Flow

1. Parse the exact request mapping and reject unknown/missing fields, wrong types, unsupported workflow, oversized context, and invalid correlation identifiers before creating an MCP process.
2. Bound, redact, and leak-scan operator context. On ambiguity or failure, discard content and return a fixed policy category before invoking either fake adapter or MCP.
3. Resolve an immutable workflow policy with one active workflow, one in-flight tool call, fixed MCP command/args, exact discovery surface, maximum turn/call/event/content counts, per-call timeout, workflow deadline, cleanup timeout, and zero retries.
4. Open one `LocalMcpClient` as an async context. Launch directly with fixed command/arguments and no shell, URL, caller environment, or remote transport.
5. Initialize the MCP session and discover tools, resources, and prompts. Compare names and closed tool schemas with exact immutable sets. Reject missing, extra, duplicate, malformed, unavailable, or restricted-host capabilities before starting fake lifecycle.
6. Start `FakeCodexAdapter` with already-redacted context. Accept only legal closed adapter steps.
7. When the fake requests a tool, validate sequence, workflow allowlist, exact argument schema, duplicate status, per-workflow call count, one-call concurrency, and cumulative input/content budget before MCP invocation.
8. Emit sanitized `TOOL_STARTED` metadata, call the fixed local MCP session under the shorter of per-call timeout and remaining workflow deadline, and propagate cancellation.
9. Validate the returned MCP object and structured envelope: exact fields, expected tool/request correlation, known status, JSON-compatible values, text/structured consistency where required, byte bounds, and no binary or ambiguous content.
10. Independently redact and leak-scan every content-bearing field. Never include rejected raw content in errors, events, logs, evidence, or object representations.
11. Convert the result to `SafeToolResult`, update cumulative counters, emit sanitized `TOOL_COMPLETED` metadata, and submit only that safe type to the fake adapter.
12. Reject duplicate, unknown, malformed, out-of-order, post-terminal, or excessive tool requests. Do not retry denied, validation, timeout, unavailable, error, or truncated results automatically.
13. Validate final fake advisory text as bounded, leak-scanned, inert data. It may explain evidence and recommend manual next steps only; it cannot trigger another executor or remediation.
14. Build only the new schema-version-1 orchestrator evidence records from repository categories and counters. Serialize, parse back, validate sequence, and append through the injected bounded writer.
15. If evidence validation or writing fails, discard apparent success and return `EVIDENCE_FAILED` with no raw exception text.
16. On every return, exception, deadline, or cancellation, close the adapter stream, MCP session, stdio streams, and child process within the cleanup bound. A surviving child or cleanup timeout is a failed workflow, not a warning.
17. For final separately approved acceptance, run one synthetic fake workflow through the deployed stdio adapter and existing runner, validate audit correlation and no-listener delta using sanitized summaries, and prove cleanup. Do not invoke Codex, authentication, DNS/provider traffic, or inspect credentials/runtime home.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
|---|---|---|---|
| Request | Unknown field/workflow, malformed identifier, oversized context | Reject before redaction, MCP launch, or fake invocation | `REJECTED` / `INVALID_REQUEST` (proposed) |
| Input redaction | Binary, ambiguity, unsupported content, protected marker survives | Discard input; do not start MCP or fake | `POLICY_FAILED` / `REDACTION_FAILED` (proposed) |
| MCP launch | Executable/args differ, process fails, shell/URL/env requested | Refuse or terminate; no fallback path | `POLICY_FAILED` / `MCP_START_FAILED` (proposed) |
| MCP initialization | Handshake/version/capability negotiation fails | Close session/process within cleanup bound | `POLICY_FAILED` / `MCP_CONTRACT_FAILED` (proposed) |
| Discovery | Missing/extra/duplicate tool, resource, prompt, open schema, restricted-host exposure | Abort before adapter lifecycle | `POLICY_FAILED` / `MCP_CAPABILITY_DRIFT` (proposed) |
| Fake lifecycle | Unknown, duplicate, malformed, or out-of-order step | Close fake stream and MCP process | `ADAPTER_FAILED` / `INVALID_ADAPTER_EVENT` |
| Tool selection | Tool not allowed for workflow or generic capability requested | Do not call MCP | `POLICY_FAILED` / `TOOL_DENIED` (proposed) |
| Tool arguments | Extra/duplicate/wrong-type/oversized/unsafe arguments | Do not call MCP; retain category only | `POLICY_FAILED` / `TOOL_REQUEST_INVALID` (proposed) |
| Tool bounds | Turn, call, concurrency, event, or cumulative content limit exceeded | Cancel active call, close workflow, no retry | `POLICY_FAILED` / `TOOL_LIMIT_EXCEEDED` (proposed) |
| MCP call | Per-call timeout, cancellation, session loss, malformed protocol object | Terminate call/process as needed; sanitize failure | fixed timeout/cancel/MCP failure category (proposed) |
| Runner result | `denied`, `validation_error`, `timeout`, `unavailable`, `error`, `truncated` | Preserve category and bounded safe metadata; never auto-retry | Safe non-success tool result; workflow policy decides terminal behavior |
| Result validation | Tool/request mismatch, extra field, bad type/status, binary, oversized, text/structured mismatch | Discard complete result | `POLICY_FAILED` / `TOOL_RESULT_INVALID` (proposed) |
| Result redaction | Protected marker remains or redaction cannot classify safely | Discard complete result before fake observation | `POLICY_FAILED` / `TOOL_RESULT_REDACTION_FAILED` (proposed) |
| Advisory output | Oversized, malformed, or leak scan fails | Discard model text | `POLICY_FAILED` / `OUTPUT_REJECTED` (proposed) |
| Evidence parse | Duplicate/extra/missing field, wrong version/type/category, invalid transition | Do not write or report success | `EVIDENCE_FAILED` / `EVIDENCE_FAILED` |
| Evidence write | Permission, size, short-write, fsync, or injected writer failure | Do not report completed workflow; retain no raw error | `EVIDENCE_FAILED` / `EVIDENCE_FAILED` |
| Cleanup | Adapter/session/process survives, close hangs, or deadline expires | Terminate owned process within bound; no unrelated process action | sanitized cleanup failure; workflow not completed |
| Official adapter | Any Phase 10 path attempts Codex/app-server/auth/provider entry | Refuse before runtime entry | `VENDOR_BLOCKED` / `REAL_ADAPTER_DISABLED` |
| Live acceptance | Credential path, DNS/provider socket, listener delta, or unexpected process detected | Stop acceptance and preserve sanitized failure metadata only | Phase 10 remains incomplete |

No failure authorizes generic shell access, SSH, OpenStack CLI exposure, direct script calls, restricted-host enablement, filesystem mutation, remediation, remote MCP, HTTP listeners, provider-gateway reuse, credential inspection, or automatic retry.

### VI. Security, Integrity, Idempotency, and Cleanup

- **Security — transport:** only one fixed local stdio child is allowed. HTTP, SSE, WebSocket, URL configuration, bearer/OAuth settings, remote MCP, listeners, and shell wrappers are prohibited.
- **Security — capabilities:** compare exact tools/resources/prompts before lifecycle start. Default restricted-host tools stay disabled. Generic command, file, database, package, service, mutation, and remediation capabilities are never model-facing.
- **Security — credentials/network:** Phase 10 code must not import OpenStack/provider clients, invoke Codex, authenticate, inspect credential/runtime-home paths, perform DNS, or open provider sockets. The existing runner alone may use its already-reviewed read-only profile during separately approved live acceptance.
- **Security — data flow:** raw MCP and runner values are tainted internal data. Only `SafeToolResult` may cross into the fake adapter. Error strings and `repr` assertions must exclude protected markers.
- **Integrity:** exact schemas, duplicate-key rejection, immutable allowlists, monotonic state transitions, request/tool correlation, fixed status enums, byte counters, and serialize-then-parse evidence validation fail closed on drift.
- **Evidence separation:** create new orchestrator names/types/schema version. Do not import, mutate, migrate, truncate, relabel, append to, or use provider-gateway ledgers as Phase 10 evidence.
- **Idempotency:** no implicit retry. Repeating an operator request creates a new workflow/correlation identifier. Duplicate tool requests in one workflow are rejected. Close/terminate operations tolerate already-closed resources.
- **Concurrency:** initial policy permits one workflow and one active tool call. There is no pool or background daemon. Semaphore acquisition must respect cancellation and remaining deadline.
- **Cleanup:** async context managers close fake streams, client session, stdio streams, and the exact owned child. Timeout escalates only against that child; no broad process matching or unrelated artifact deletion is allowed.
- **Filesystem:** only a test-owned temporary evidence path may be written during local validation. Production evidence path, permissions, retention, and deployment remain deferred. No diagnostic output is persisted.
- **Advisory-only output:** fake/model text is inert, manually reviewed data and cannot authorize code execution, OpenStack changes, service operations, or remediation.

### VII. Validation Strategy

All Python execution must use a dedicated temporary virtual environment, following the repository’s existing package evidence procedure.

```bash
rtk python3 -m venv /tmp/openstack-ai-ops-phase10-venv
source /tmp/openstack-ai-ops-phase10-venv/bin/activate
rtk python -m pip install --require-hashes -r ansible/ai_ops_runtime/files/orchestrator/requirements.lock
rtk python -m ruff format --check ansible/ai_ops_runtime/files/orchestrator
rtk python -m ruff check ansible/ai_ops_runtime/files/orchestrator
rtk python -m mypy ansible/ai_ops_runtime/files/orchestrator/src ansible/ai_ops_runtime/files/orchestrator/tests
rtk python -m py_compile ansible/ai_ops_runtime/files/orchestrator/src/openstack_ai_ops_orchestrator/*.py ansible/ai_ops_runtime/files/orchestrator/tests/*.py
rtk python -m pytest -q ansible/ai_ops_runtime/files/orchestrator/tests
rtk git diff --check
```

Chunk-aware proofs:

- **Contracts:** exact schemas and enums reject unknown fields/types/categories; stubs fail explicitly and compile.
- **Redaction:** shared synthetic markers cover identity labels, token/password/secret/API/private-key forms, embedded JSON, malformed/duplicate-key JSON, binary/non-finite values, ambiguity, and byte limits. Markers must be absent from fake observations, returned execution, evidence bytes, exception text, and representations.
- **MCP client:** fake session/process tests prove fixed command/args, exact discovery, no URL/env/shell path, per-call timeout, cancellation, and deterministic close. Static imports exclude HTTP/OpenStack/Codex/provider modules.
- **Tool loop:** approved one-call success, unknown tool, malformed arguments, duplicate request, out-of-order request, excessive calls/turns/events/content, cancellation, and all runner statuses.
- **Evidence:** exact-field/type/version checks, duplicate-key rejection, record/ledger bounds, valid and invalid lifecycle sequences, write failure override, and no forbidden key/value markers.
- **Official adapter:** existing tests continue proving it fails before SDK runtime/authentication entry.
- **Integration smoke:** first use a test-only stdio fixture. The final deployed adapter/runner workflow requires separate approval and must record only sanitized categories/counts.
- **No-provider safety:** tests monkeypatch or statically forbid Codex construction, credential/runtime-home access, DNS, network connection, and listener creation. Live acceptance compares listener/process summaries without retaining raw snapshots.
- **Audit correlation:** final approved live validation compares request IDs and fixed `client_id=local-mcp-client` / `transport=stdio` using sanitized summaries only; it does not copy raw audit events.
- **Diff review:** after every chunk, run `rtk git diff --check`, `rtk git diff --stat`, and scoped `rtk git diff -- <changed-files>`.

Documentation validation for this ADS:

```bash
rtk grep -nE '^### (I|II|III|IV|V|VI|VII|VIII|IX|X)\.' docs/ai-ops/implementation-plan/ads/10-00-mcp-tool-loop-redaction-and-evidence-ads.md
rtk grep -nE '^#### Chunk [0-7]:' docs/ai-ops/implementation-plan/ads/10-00-mcp-tool-loop-redaction-and-evidence-ads.md
rtk git diff --check
rtk git diff -- docs/ai-ops/implementation-plan/ads/10-00-mcp-tool-loop-redaction-and-evidence-ads.md
```

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass. Each chunk ends after targeted validation and diff review.

#### Chunk 0: Discovery and Integration Confirmation
- **Goal:** Resolve the fake pre-model integration seam, exact fixed stdio launch/discovery contract, dependency pin, redaction fixture classes, numeric limits, evidence shape, and live-acceptance permission before implementation.
- **Files to read:** this ADS; Phase 10 plan; orchestrator contracts/lifecycle/fake/tests/lock; MCP server/policy/defaults; runner/registry; Phase 07 MCP validator and runtime evidence; Phase 08 evidence. Provider-gateway files may be read only for strict-parser pattern evidence, not as dependencies.
- **Commands:** targeted `rtk find`, `rtk grep`, and bounded reads; `rtk git status --short --branch`; no package install, process launch, authentication, credential/runtime-home inspection, DNS, provider call, deployment, or edit.
- **Evidence to confirm:** direct client boundary is accepted for fake-only pre-model enforcement; exact MCP names and command/args; `mcp==1.28.1` lock policy; initial bounds; protected-marker classes; no existing orchestrator evidence schema/path; final live acceptance allowed or explicitly deferred.
- **Validation:** discovery report classifies each item as confirmed, proposed, deferred, or blocker.
- **Stop condition:** stop without editing if redaction placement, dependency policy, fixed launch contract, or official-adapter stop gate remains ambiguous.

#### Chunk 1: Tool Contracts and Compile-Safe Stubs
- **Goal:** Add the minimum typed tool request/result/client contracts and policy limits while preserving all Phase 09 behavior and keeping tool execution disabled.
- **Files to change:** `src/openstack_ai_ops_orchestrator/contracts.py`; `tests/test_contracts.py`.
- **Symbols to add/change:** conceptual `ToolCallRequest`, `SafeToolResult`, `McpCapabilityContract`, `LocalMcpClientProtocol`, closed tool/result categories, and confirmed `RuntimePolicy` call/concurrency/per-call/cumulative/cleanup limits.
- **Implementation shape:** immutable exact-field types and protocols only. The client stub raises a fixed not-ready policy error; no `mcp` import, process, tool call, or pass-through redaction. Existing adapters still compile and existing tests pass.
- **Validation:** focused contract pytest, mypy, Ruff, `py_compile`, symbol grep, and scoped diff.
- **Stop condition:** invalid contracts fail closed, stub invocation cannot report success, and the full existing 23-test baseline remains green.

#### Chunk 2: Input and Tool-Result Redaction Slice
- **Goal:** Implement pure fail-closed redaction/validation that produces safe typed values before any adapter observation.
- **Files to change:** proposed `src/openstack_ai_ops_orchestrator/redaction.py`; proposed `tests/test_redaction.py`.
- **Symbols to add/change:** conceptual `RedactionError`, classification enum/result, strict duplicate-key parser, `redact_operator_context`, `redact_tool_result`, and leak-scan functions.
- **Implementation shape:** adapt reviewed behavior into a new orchestrator-owned module; do not import provider-gateway code. Apply byte limits before and after rebuilding. Errors contain categories only. Use synthetic shared fixtures for parity.
- **Validation:** focused redaction pytest, mypy, Ruff, `py_compile`, marker grep, and scoped diff.
- **Stop condition:** clear/redacted synthetic inputs succeed, malformed/ambiguous/binary/oversized cases fail closed, and protected markers cannot appear in safe values or errors.

#### Chunk 3: Fixed Local MCP Client Boundary
- **Goal:** Launch and validate one fixed stdio MCP session, expose one typed call seam, and prove deterministic cleanup without contacting the deployed runner.
- **Files to change:** proposed `src/openstack_ai_ops_orchestrator/mcp_client.py`; proposed `tests/test_mcp_client.py`; `requirements.in`; `requirements.lock` (the dependency pair is inseparable from the client slice).
- **Symbols to add/change:** conceptual fixed launch configuration, `LocalMcpClient`, discovery validator, raw internal result parser, per-call deadline, and close/termination coordinator.
- **Implementation shape:** use `StdioServerParameters`, `stdio_client`, and `ClientSession`; constructor runtime configuration is immutable. Test-only injected session/process fixtures simulate discovery and calls. No URL, shell, caller environment, OpenStack, Codex, credential, or network API. Regenerate the exact hash lock in `/tmp` only after Chunk 0 approval.
- **Validation:** focused MCP client tests plus full package Ruff/mypy/pytest and lock install verification in `/tmp`; static prohibited-import/config assertions; scoped dependency diff review.
- **Stop condition:** exact discovery succeeds, every drift/call/timeout/cancel path closes, fixed command/args are asserted, and no real MCP/runner/provider process is started.

#### Chunk 4: Fake Tool-Request Handshake
- **Goal:** Extend the deterministic fake with one typed tool request and safe-result receipt while retaining SDK/network/process independence.
- **Files to change:** `src/openstack_ai_ops_orchestrator/fake_codex_adapter.py`; `tests/test_fake_codex_adapter.py`.
- **Symbols to add/change:** conceptual fake tool scenario, adapter-step emission, safe-result submission/observation, duplicate/out-of-order guards, cleanup state.
- **Implementation shape:** the fake may request only `project_resource_summary` with no arguments in the first success scenario. It receives only `SafeToolResult`; raw MCP/result types are unimportable from this module. Existing no-tool scenario remains valid.
- **Validation:** focused fake tests, mypy, Ruff, static forbidden-import assertions, marker non-observation assertion, and scoped diff.
- **Stop condition:** the fake deterministically requests one tool, cannot receive raw data, resumes only after a safe result, and cleans up on success/cancel/deadline.

#### Chunk 5: One Bounded Orchestrator Tool-Loop Slice
- **Goal:** Connect validated/redacted input, fake tool request, fixed MCP client, result redaction, fake continuation, and terminal advisory output for one meaningful workflow.
- **Files to change:** `src/openstack_ai_ops_orchestrator/orchestrator.py`; `tests/test_orchestrator.py`.
- **Symbols to add/change:** tool-step lifecycle handling, workflow allowlist check, call/concurrency/cumulative counters, per-call deadline composition, `TOOL_STARTED`/`TOOL_COMPLETED` validation, and client cleanup integration.
- **Implementation shape:** dependency-inject the typed MCP client protocol; no direct runner/script call. Reject generic/duplicate/malformed/out-of-order/excessive requests before call. Redact every result before fake submission. Preserve runner statuses as closed safe categories and perform zero automatic retries.
- **Validation:** focused orchestrator tests for success and all bounds/statuses, full package checks, marker leak assertions, official-adapter disabled regressions, and scoped diff.
- **Stop condition:** one fake-backed `project_resource_summary` loop completes through a fake MCP session; every negative path closes all owned resources and no raw marker reaches fake/result/error.

#### Chunk 6: Versioned Orchestrator Evidence Slice
- **Goal:** Add a standalone strict schema/parser/sequence validator and injected bounded writer contract while preserving historical gateway evidence untouched; defer orchestration wiring to Chunk 7.
- **Files to change:** proposed `src/openstack_ai_ops_orchestrator/evidence.py`; proposed `tests/test_evidence.py`.
- **Symbols to add/change:** conceptual `OrchestratorEvidenceRecord`, schema/category constants, serializer, duplicate-key parser, sequence validator, writer protocol, and test-only/local bounded JSONL writer.
- **Implementation shape:** exact metadata fields and version `1`; category/counter data only; serialize then parse before append; bound record and ledger size; no imports from gateway modules. Writer failure is a fixed exception without path/content leakage. No existing orchestrator call site changes in this chunk.
- **Validation:** focused evidence tests, mypy, Ruff, malformed/duplicate/extra/oversized/transition tests, forbidden-field/marker scan, and a diff proving provider-gateway files unchanged.
- **Stop condition:** valid standalone lifecycle metadata round-trips, invalid metadata never writes, writer failures are fixed and sanitized, the package remains compile-safe without orchestration wiring, and historical gateway files have no diff.

#### Chunk 7: Evidence Integration and Local Safety Acceptance
- **Goal:** Replace the unversioned callback path with the accepted evidence contract, run the complete fake-backed stdio safety slice, and record sanitized Phase 10 acceptance without enabling remote boundaries.
- **Files to change:** `src/openstack_ai_ops_orchestrator/orchestrator.py`; `tests/test_orchestrator.py` (or one dedicated integration test if Chunk 0 proves necessary); proposed `docs/ai-ops/runtime/phase10-mcp-tool-loop-local-validation-evidence.md` only after all validation passes. Three files are justified because this final vertical slice must connect production evidence handling, prove it, and record acceptance.
- **Symbols to add/change:** evidence-record construction from closed workflow/tool counters, writer integration, evidence-failure override, final integration assertions, and acceptance fixture only.
- **Implementation shape:** wire only the Chunk 6 evidence protocol into the existing orchestrator; do not add another writer or schema. First run repository-local fixture-backed stdio acceptance. Run one deployed MCP/runner synthetic call only with explicit approval and safe synthetic inputs. Verify exact discovery, approved/denied calls, status/audit correlation, redaction, cleanup, no listener delta, and zero Codex/auth/credential/DNS/provider access. Evidence note stores only outcomes/categories/counts.
- **Validation:** full package format/lint/type/compile/tests, approved scoped MCP validator, no-provider safety assertions, `rtk git diff --check`, security grep, and final scoped diff. Do not run broad deployment playbooks.
- **Stop condition:** the orchestrator reports `EVIDENCE_FAILED` on any schema/writer failure; otherwise the Phase 10 definition of done is evidenced locally, or the phase remains explicitly blocked on live acceptance. `OfficialCodexAdapter` is still disabled and Phases 11–13 remain untouched.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Phase 10 local MCP tool loop, fail-closed input/tool-result redaction, bounded fake lifecycle, and separate metadata evidence as specified by docs/ai-ops/implementation-plan/ads/10-00-mcp-tool-loop-redaction-and-evidence-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm the fake pre-model integration seam, exact fixed stdio launch/discovery contract, mcp dependency policy, redaction fixtures, numeric bounds, evidence schema decisions, and live-acceptance permission. Do not install packages, launch MCP/Codex, authenticate, inspect credentials or runtime-home paths, open sockets, perform DNS/provider traffic, or change deployment/egress. Keep OfficialCodexAdapter disabled. Stop after the evidence report.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.
Execute Chunk 1 only from the accepted Phase 10 ADS and Chunk 0 decisions.
Do not continue to Chunk 2. Add contracts and explicit fail-closed stubs only; do not import mcp, start a process, call a runner, or enable OfficialCodexAdapter. Run targeted Ruff, mypy, py_compile, pytest, and show the scoped git diff before stopping.
```

### X. Conclusion and Next Steps

- Phase 10 has an evidence-backed local design: the orchestrator directly owns the fake-only pre-model MCP client loop, while the existing stdio adapter and runner remain the execution/audit boundary.
- Independent tool-result redaction is required after MCP result validation and before `SafeToolResult` reaches the fake. Existing MCP envelope validation and runner argument sanitization are necessary but not sufficient for this requirement.
- The new orchestrator evidence contract is versioned and metadata-only, with its own parser/writer/types. Provider-gateway schemas and historical ledgers remain unchanged and cannot serve as Phase 10 evidence.
- The design deliberately does not claim that the official Codex runtime has a supported pre-consumption MCP interception seam. `OfficialCodexAdapter` remains disabled after Phase 10.
- The next action is review and acceptance of this ADS, followed by Chunk 0 only. Implementation must stop on any unresolved redaction placement, dependency, fixed-launch, or live-acceptance boundary.
- Deployment identity, production evidence path, authentication, runtime home, egress, provider acceptance, remote operations, and gateway retirement remain deferred to Phases 11–13 and Phase 99 as applicable.
