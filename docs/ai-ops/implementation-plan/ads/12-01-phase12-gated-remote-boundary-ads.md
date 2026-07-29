# Phase 12 Live Codex MVP and Replaceable Model Boundary ADS

## Status

**Decision:** implement a fully functional live-Codex-powered AIOPS assistant
MVP through an explicit bounded in-memory payload-reduction policy. Keep the
model integration replaceable so a later provider can implement the same
repository-owned adapter contract.

This decision supersedes the prior requirement that SDK payload objects must
never be accessed. Raw SDK payloads may be accessed only inside the official
adapter's tainted in-memory reducer. They must never be logged, persisted,
placed in evidence, returned from the adapter, or exposed to another component.
This ADS authorizes offline implementation and validation only. Authentication,
egress changes, remote-unit activation, and a provider request remain subject
to their separate Phase 12 approvals.

Where `12-00-controlled-remote-acceptance-and-operations-ads.md` requires every
payload-bearing SDK event to be rejected, this ADS supersedes that requirement
only inside the bounded official-adapter reducer. All other Phase 12 limits,
approval gates, cleanup rules, and metadata-only evidence requirements remain
controlling.

## I. Overview and Contract

**Source:**

- `docs/ai-ops/implementation-plan/ads/12-00-controlled-remote-acceptance-and-operations-ads.md`
- `docs/ai-ops/implementation-plan/12-controlled-remote-acceptance-and-operations.md`
- `docs/ai-ops/runtime/phase12-sdk-mcp-vendor-blocker-decision.md`

**Goal:** deliver one fixed, bounded live Codex workflow for the OpenStack AIOPS
MVP without binding orchestration, evidence, or tool execution to Codex-specific
payload types.

The repository-owned model boundary accepts a fixed diagnostic turn request and
emits only `AdapterEvent` metadata plus a terminal `AdapterResult`. The current
`CodexAdapter` protocol already has this provider-neutral structural shape; a
compile-safe compatibility change may expose the clearer `ModelAdapter` name
without changing callers. `OfficialCodexAdapter` is the first implementation,
while `FakeCodexAdapter` remains the deterministic regression implementation.

One reviewed tool request passes through the credential-free orchestrator stdio
proxy to the assistant-owned Unix socket bridge. The bridge validates the exact
peer UID and redacts the runner result before Codex receives it. The official
adapter may reduce Codex notification payloads in memory to approved lifecycle
metadata and bounded sanitized advisory text, then discard all raw references.

For this ADS, **fully functional MVP** means one live Codex turn can invoke the
fixed read-only OpenStack summary tool, consume its already-redacted result,
produce a bounded sanitized advisory for ephemeral operator display, terminate
in a closed category, write metadata-only evidence, and restore the disabled
baseline. It does not mean recurring autonomous operation, write access, generic
chat, arbitrary tools, or unrestricted prompts/models.

## II. Observed Evidence and Assumptions

### Observed evidence

- `official_codex_adapter.py` retains `OFFICIAL_ADAPTER_ENABLED = False`.
- `runtime_entrypoint.py` returns `REMOTE_DISABLED` for the remote profile.
- `remote_acceptance.py` consumes the approval contract then raises
  `REMOTE_ACCEPTANCE_DISABLED` before SDK, MCP, process, network, or egress
  construction.
- `mcp_bridge.py` allows only `project_resource_summary`, validates the Unix
  peer UID, and redacts results.
- `mcp_stdio_proxy.py` uses only
  `/run/openstack-ai-ops/assistant-mcp-bridge.sock` and exposes one fixed tool.
- The assistant bridge socket/service templates are static, hardened, and are
  installed disabled and stopped. The activation playbook is separately gated
  and uses a fake runner only.

### Pinned SDK evidence and policy reconciliation

The offline review of `openai-codex==0.144.4` confirmed that public
`Notification` objects always contain `method` and `payload`, and that
`AsyncTurnHandle.stream()` yields those notifications. No payload-free stream
or pre-consumption callback exists. Therefore a live Codex MVP cannot satisfy
the former no-payload-access policy.

The product requirement now explicitly accepts bounded in-memory access inside
one reducer. This is a policy revision, not evidence that the SDK changed. The
former `VENDOR_BLOCKED / MCP_INTERCEPTION_UNSUPPORTED` decision is superseded
for this fixed MVP design only. Any unrecognized notification, payload type,
tool request, terminal shape, or advisory output remains fail closed.

## III. Required Technical Dependencies and Imports

- Pinned `openai-codex==0.144.4` public `AsyncCodex`, `AsyncThread`,
  `AsyncTurnHandle`, `Notification`, and generated notification payload types.
- Repository-owned `AdapterEvent`, `AdapterResult`, `RuntimePolicy`, and the
  structural model-adapter protocol currently named `CodexAdapter`.
- `OfficialCodexAdapter`, `FakeCodexAdapter`, `McpStdioProxy`,
  `AssistantBridgeExecutor`, and existing redaction/output validators.
- A proposed tainted payload reducer owned by `official_codex_adapter.py`; its
  public output is restricted to repository contracts.

No generic provider gateway, caller-selected model/prompt/path, private Codex
protocol, second MCP route, credential copy, or API-key fallback is permitted.
A later model implementation must satisfy the same repository adapter contract
and must not require changes to orchestration, tool, or evidence contracts.

## IV. Step-by-Step Procedure / Execution Flow

1. Validate and consume one fresh one-shot approval before constructing any
   remote runtime object.
2. Build only the curated SDK configuration, fixed prompt/model/work directory,
   and fixed local MCP stdio command.
3. Start one SDK client, one thread, and one turn; permit no automatic retry.
4. Receive each public `Notification` as tainted in-memory data. Validate the
   method, exact public payload type, turn identity, order, count, and bounded
   serialized size before reduction.
5. Reduce approved lifecycle payloads immediately to `AdapterEvent`. Reduce only
   the approved terminal model text to bounded sanitized advisory text. Do not
   return raw SDK objects or raw strings from the reducer.
6. Allow Codex to call only the fixed model-facing MCP tool. The proxy and bridge
   must validate and redact the OpenStack result before Codex consumes it.
7. Validate advisory output again at the orchestrator boundary, present it only
   through the approved ephemeral presenter, and write metadata-only evidence.
8. Close the exact event stream, turn/client resources, MCP proxy, bridge units,
   process/workspace state, approval artifact, and temporary egress on every
   terminal path.
9. Keep ordinary deployment fake-only and remote-disabled. A live run requires
   the separately reviewed one-request operation and fresh egress authorization.

## V. Failure Modes and Resilience

| Stage | Failure mode | Action | Next state |
| --- | --- | --- | --- |
| Approval | Missing, expired, malformed, or reused approval | Construct no SDK object | `REMOTE_APPROVAL_INVALID` |
| SDK start | Client/thread/turn construction fails | Sanitize error; cleanup; no retry | `SDK_START_FAILED` |
| Payload reduction | Unknown method/type, wrong turn, oversized payload, or invalid order | Retain no raw value; interrupt once; cleanup | `INVALID_ADAPTER_EVENT` |
| Tool boundary | Unknown tool, malformed result, peer denial, timeout, or redaction failure | Return closed MCP failure; no fallback | `MCP_INTERCEPTION_UNSUPPORTED` or adapter failure |
| Advisory reduction | Missing, oversized, control-bearing, or sensitive output | Present nothing; retain category only | `POLICY_FAILED` |
| Cancellation/deadline | Operator cancellation or fixed deadline | Interrupt at most once; cleanup | `CANCELLED` or `DEADLINE_EXCEEDED` |
| Cleanup/evidence | Any resource, marker, or evidence validator fails | Block further requests | Phase remains incomplete |

## VI. Security, Integrity, Idempotency, and Cleanup

- Raw SDK payloads are permitted only inside the official adapter process and
  reducer call stack. They may not enter logs, exceptions, evidence,
  repository-owned dataclasses, callbacks, presenters, test snapshots, or
  persistent files.
- This policy does not claim Python memory zeroization. It minimizes exposure by
  bounding payload size, reducing immediately, dropping references, disabling
  raw logging, and terminating the one-shot process after cleanup.
- Terminal advisory text must pass allowlisted type/shape checks, byte limits,
  control-character rejection, sensitive-marker redaction, and a second
  orchestrator validation before ephemeral display.
- Codex remains isolated from OpenStack credentials. It can invoke only the fixed
  credential-free stdio proxy; the assistant-owned bridge alone reaches the
  reviewed credential-bearing runner and redacts before return.
- Preserve one request, one turn, one tool call, one concurrent tool call, no
  retry, fixed deadline, exact peer UID, static units, and dedicated identity.
- Do not inspect, copy, hash, parse, or delete Codex-home or credential contents.
- Do not add a TCP listener, generic command runner, provider gateway, API-key
  fallback, private-protocol recovery, or recurring remote operation.
- `OFFICIAL_ADAPTER_ENABLED` and the ordinary remote entrypoint remain disabled
  until offline chunks pass and a separately reviewed operation capability is
  implemented. They must never become unconditional defaults.

## VII. Validation Strategy

Offline validation must prove:

- pinned public notification fixtures reduce only approved lifecycle metadata
  and bounded advisory text;
- sentinel raw payload content cannot appear in adapter events/results,
  exceptions, logs, evidence, presenter calls, or filesystem outputs;
- unknown payload types, wrong turn IDs, excessive events/bytes, malformed
  terminal results, cancellation, and timeouts fail closed and clean up;
- fake adapter behavior remains unchanged behind the same structural contract;
- fixed proxy/bridge integration still enforces one tool, redaction, peer UID,
  timeout, and exact resource closure;
- no live SDK factory is reachable from ordinary fake deployment or an
  unapproved invocation;
- Ruff, mypy, py_compile, targeted pytest, prohibited-boundary scans,
  `git diff --check`, and scoped diff review pass.

Python checks run in a temporary virtual environment under `/tmp` using the
pinned lock inputs. Offline chunks must not authenticate, change egress, start a
real SDK client, activate remote units, resolve DNS, or contact a provider.

## VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Chunks 0-2
record the completed discovery under the former policy. The revised MVP resumes
at Chunk 3. Each chunk remains offline until the final separately approved live
acceptance chunk.

### Chunk 0: Evidence and Static-Boundary Reconciliation — Complete

- **Goal:** reconcile bridge/proxy deployment evidence.
- **Outcome:** static bridge/proxy deployment confirmed; remote use remained
  blocked.
- **Stop condition:** met.

### Chunk 1: Public Lifecycle Contract Tests — Complete

- **Goal:** characterize `openai-codex==0.144.4` notification shapes.
- **Outcome:** payload-bearing and unknown events fail closed; pinned public
  lifecycle confirmed payload-bearing.
- **Stop condition:** met.

### Chunk 2: Former No-Payload Reducer Decision — Complete

- **Goal:** decide whether the former no-payload-access policy was implementable.
- **Outcome:** it was not; the product policy is now explicitly revised by this
  ADS rather than bypassed in code.
- **Stop condition:** met.

### Chunk 3: Provider-Neutral Adapter Contract Compatibility

- **Goal:** expose a provider-neutral model adapter name while preserving all
  current callers and fake behavior.
- **Files to change:** `contracts.py` and its targeted tests.
- **Symbols to add/change:** proposed `ModelAdapter` protocol and compile-safe
  `CodexAdapter` compatibility alias.
- **Implementation shape:** structural contract only; no SDK import or runtime
  wiring.
- **Validation:** Ruff, mypy, py_compile, targeted contract/orchestrator tests.
- **Stop condition:** fake and official adapters satisfy the same provider-neutral
  contract without behavior changes.

### Chunk 4: Tainted Payload Reducer Contracts and Failing-Closed Tests

- **Goal:** define exact accepted public notification/payload shapes and sanitized
  reducer outputs.
- **Files to change:** official adapter module and test module.
- **Symbols to add/change:** reducer input/output contracts and compile-safe
  disabled stub returning an explicit compatibility failure.
- **Implementation shape:** fixtures use pinned public types and sentinel raw
  content; no factory construction or caller wiring.
- **Validation:** targeted Ruff, mypy, py_compile, pytest, and sentinel scans.
- **Stop condition:** contracts compile and every unimplemented/unknown path fails
  closed without raw output.

### Chunk 5: Bounded In-Memory Payload Reduction

- **Goal:** implement approved lifecycle and terminal advisory reduction.
- **Files to change:** official adapter module and test module.
- **Symbols to add/change:** reducer validation/mapping helpers.
- **Implementation shape:** exact method/type/turn/order checks, serialized byte
  bound, immediate sanitization, repository-only outputs, and sanitized errors.
- **Validation:** targeted adapter tests including unknown types, oversized
  payloads, sentinel non-retention, cancellation, and cleanup.
- **Stop condition:** approved fixtures reduce safely; every other fixture fails
  closed; `OFFICIAL_ADAPTER_ENABLED` remains `False`.

### Chunk 6: Pinned Official SDK Lifecycle Wiring — Offline Only

- **Goal:** connect the reducer to the pinned public async lifecycle through an
  injected factory while ordinary construction stays disabled.
- **Files to change:** official adapter module and test module.
- **Symbols to add/change:** curated production factory seam and exact owned
  stream/client cleanup.
- **Implementation shape:** one client/thread/turn, fixed SDK config and MCP
  command, no retry, no caller overrides, injected public-shape tests only.
- **Validation:** targeted adapter tests, static live-boundary scans, fake
  regression, Ruff, mypy, and py_compile.
- **Stop condition:** offline public-shape lifecycle succeeds through repository
  events/results; unapproved construction remains unreachable.

### Chunk 7: Fixed Remote Entrypoint Capability and Cleanup Stub

- **Goal:** introduce a separate one-shot capability path without changing the
  ordinary fake or disabled remote defaults.
- **Files to change:** remote entrypoint/acceptance modules and targeted tests.
- **Symbols to add/change:** explicit operation capability and fail-closed cleanup
  contract; no unconditional global enablement.
- **Implementation shape:** consume approval before runtime, exactly one attempt,
  fixed presenter, unconditional cleanup, and explicit temporary error until the
  operation playbook is reviewed.
- **Validation:** targeted entrypoint/approval tests and prohibited-input scans.
- **Stop condition:** default invocation remains fake-only; remote invocation
  without the exact operation capability remains `REMOTE_DISABLED`.

### Chunk 8: Offline End-to-End Live-Boundary Simulation

- **Goal:** prove approval-to-adapter-to-proxy/bridge-to-evidence flow entirely
  with injected SDK and runner fixtures.
- **Files to change:** targeted integration tests and operation design only.
- **Symbols to add/change:** test-only lifecycle and cleanup fixtures.
- **Implementation shape:** one fixed workflow, one tool call, sanitized advisory,
  metadata-only evidence, no network or real SDK process.
- **Validation:** full scoped orchestrator/adapter/proxy/bridge/operation tests,
  deployment validators, security scans, and diff review.
- **Stop condition:** every offline gate passes and cleanup leaves zero temporary
  artifacts, processes, listeners, or approval capability.

### Chunk 9: One Separately Approved Live Codex MVP Acceptance

- **Goal:** execute exactly one fixed live workflow and restore the disabled
  baseline.
- **Files to change:** metadata-only acceptance evidence and runbooks after the
  outcome is accepted; no request behavior is added during this chunk.
- **Implementation shape:** fresh one-request approval, separate temporary egress
  approval, one attempt, no retry, bounded ephemeral advisory presentation,
  unconditional cleanup, and post-validation.
- **Validation:** request count, terminal category, approval exhaustion, process/
  listener/workspace/egress cleanup, fake regression, and metadata-only evidence.
- **Stop condition:** exactly one approved attempt completes or reaches a bounded
  SDK/vendor failure; no raw payload is retained; regular remote use remains
  disabled.

## IX. Handoff to `chunked-implementation`

Recommended next agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, pre-edit-discipline, safe-python-edit, and
post-edit-discipline if available.

Task:
Phase 12 live Codex MVP and replaceable model boundary as specified by
`docs/ai-ops/implementation-plan/ads/12-01-phase12-gated-remote-boundary-ads.md`.

Mode:
Execute Chunk 3 only. Add only the provider-neutral adapter protocol and a
compile-safe compatibility alias with targeted tests. Do not implement payload
reduction, construct an SDK client, enable units, materialize approval, change
egress, authenticate, perform DNS, or contact a provider. Run targeted Ruff,
mypy, py_compile, pytest, and scoped diff review; then stop.
```

## X. Conclusion and Next Steps

The live Codex MVP is now an explicit product and security decision: raw public
SDK payloads may be reduced only in bounded process memory and may never cross
the repository adapter boundary unsanitized. Codex is the first replaceable
model implementation, not an orchestration dependency. The next permitted work
is offline Chunk 3 only. A live request remains prohibited until Chunks 3-8 pass
and Chunk 9 receives fresh one-request and temporary-egress approvals.
