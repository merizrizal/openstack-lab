## Architectural Design Specification: Hybrid Codex SDK Orchestrator Contracts

**Source:** `docs/ai-ops/implementation-plan/08-orchestrator-architecture-and-sdk-contracts.md` (Phase 08, Steps 1-4)

**Goal:** Define an implementation-ready, fake-first repository orchestrator boundary around the supported public Codex Python SDK/runtime contract without accessing credentials, invoking a provider, reproducing private protocol behavior, or weakening the existing local MCP and egress controls.

**Status:** Draft for review. Fake-first local implementation may begin after the dependency/toolchain pins and package location are accepted. A real Codex adapter remains blocked until the MCP result-redaction ownership question in Section II is resolved.

---

### I. Overview and Contract

#### Selected execution boundary

```text
operator
  -> repository-owned orchestrator
       -> validate, bound, and redact workflow input
       -> enforce state, turn, event, output, deadline, and cancellation limits
       -> injected CodexAdapter
            -> FakeCodexAdapter (Phases 09-10 local default)
            -> OfficialCodexAdapter (later approval gate)
                 -> openai-codex==0.144.4
                      -> pinned openai-codex-cli-bin==0.144.4 app-server runtime
                           -> Codex-managed ChatGPT authentication and transport
                           -> one reviewed local stdio MCP entry
                                -> existing AI-OPS MCP adapter
                                     -> existing read-only runner
       -> sanitize advisory output
       -> emit bounded metadata categories only
```

The repository owns workflow safety and policy. The official SDK/runtime owns process-level Codex operation, ChatGPT session use and refresh, and private provider transport. The SDK is not an independent HTTP provider client.

The old provider gateway is outside this request path. Its service identity, provider configuration, and evidence schemas must not be reused.

#### Public vendor lifecycle contract (concrete for reviewed `openai-codex==0.144.4`)

- Package: `openai-codex==0.144.4`, installed from PyPI into a dedicated Python virtual environment.
- Runtime: Python 3.10 or later.
- Runtime relationship: the SDK controls the local Codex app-server over JSON-RPC. Published package metadata pins `openai-codex-cli-bin==0.144.4` as its compatible runtime dependency.
- Clients: `Codex(config: CodexConfig | None = None)` and async-parity `AsyncCodex(config: CodexConfig | None = None)`.
- Thread creation: `codex.thread_start(...) -> Thread` or `await codex.thread_start(...) -> AsyncThread`.
- Thread resume: `codex.thread_resume(thread_id, ...) -> Thread` with asynchronous parity.
- Buffered turn: `thread.run(input, ..., output_schema=None, sandbox=None) -> TurnResult` with asynchronous parity.
- Controlled/streamed turn: `thread.turn(...) -> TurnHandle`; `TurnHandle.stream()` yields turn-scoped notifications and `TurnHandle.run()` collects the result. Async equivalents return awaitables/async iterators.
- Cancellation: `TurnHandle.interrupt()` and `AsyncTurnHandle.interrupt()` are public explicit interruption contracts. Repository timeout policy must call interruption and still enforce a bounded cleanup deadline.
- Structured output: `output_schema` is accepted by `run()` and `turn()`.
- Reviewed thread/turn controls: `cwd`, `model`, `sandbox`, `approval_mode`, `config`, reasoning effort, output schema, and asynchronous lifecycle pairing.
- Reviewed results/errors: `TurnResult` exposes bounded status, error, timestamps, final response, items, and usage; public JSON-RPC error classes and retry classification helpers exist.
- Public login and account methods, API-key login, model-provider selection, arbitrary config, steering, forking, full-access sandbox, and SDK retry helpers are prohibited or disabled unless a later ADS explicitly approves them.

These symbols are the vendor-facing contract only. Repository code must isolate them behind its own adapter and must not expose SDK objects to workflow code.

#### Repository adapter contract (conceptual)

**Type Contract (Conceptual): `CodexAdapter`**

Inputs:

- one validated and already-redacted diagnostic turn request;
- closed runtime policy containing a deadline, maximum event count, maximum output bytes, approved model alias, read-only sandbox requirement, fixed working directory, and cancellation signal;
- no credentials, API key, base URL, arbitrary environment, arbitrary Codex config, or caller-selected MCP definition.

Outputs:

- an asynchronous stream or bounded collection of repository lifecycle events;
- one terminal `AdapterResult` category;
- optional advisory text only after size checks and leak scanning.

Temporary stub behavior:

- the real adapter stub must return an explicit `REAL_ADAPTER_DISABLED` category and must never enter `AsyncCodex` or start the app-server;
- this is safer than returning success because no local test may accidentally imply remote acceptance.

**Method Signature Contract (Conceptual):**

```text
CodexAdapter.run_turn(request, policy, cancellation) -> async AdapterEvent stream + terminal AdapterResult
```

Exact repository protocol/class names and module paths remain proposed until the Phase 09 Python package root is approved.

#### Repository lifecycle event contract (proposed closed allowlist)

Repository event types must not mirror arbitrary vendor payloads. They may contain only:

- `thread_started` without persisting the vendor thread identifier in evidence;
- `turn_started`;
- `tool_started` with an allowlisted local tool name;
- `tool_completed` with a bounded status category, never tool output;
- `turn_completed` with bounded usage counters if accepted by the evidence review;
- `turn_failed` with a repository error category;
- `cancelled`;
- `adapter_failed`.

Unknown SDK event types, malformed events, excessive events, and invalid transitions fail closed. Raw SDK event objects, item text, error messages, stderr, prompts, responses, and thread identifiers must not enter logs or evidence.

#### Workflow state contract (proposed)

```text
received
  -> validated
  -> redacted
  -> adapter_started
  -> running
  -> output_validating
  -> completed
```

Permitted terminal alternatives are:

```text
rejected | cancelled | timed_out | auth_action_required |
adapter_failed | policy_failed | evidence_failed | vendor_blocked
```

Every state transition is monotonic and terminal states cannot be retried implicitly. A retry is a new operator-authorized workflow with a new correlation identifier.

#### Dedicated identity and runtime-home contract (conceptual)

- A dedicated non-root orchestrator identity, distinct from `assistant` and the superseded gateway identity, is required before real SDK use. Its final name is intentionally deferred to the deployment ADS.
- Its runtime home is dedicated to Codex-owned state and inaccessible to repository application logic except as an opaque home directory supplied to the Codex process environment.
- Repository code must never open, enumerate, copy, parse, hash, log, or test for credential files or values.
- The runtime environment is an explicit allowlist. It must not inherit the operator shell environment.
- `assistant` retains direct-public-egress denial. Only the later reviewed orchestrator/Codex process identity may receive minimum required outbound access.
- Local tests use a temporary non-credential test home and the fake adapter only; they must not inspect or reuse the existing Codex runtime home.

#### MCP ownership contract and unresolved interception seam

Public contracts confirm that Codex supports fixed stdio MCP configuration, including command, arguments, working directory, enabled tools, required startup behavior, startup timeout, and tool timeout. The Python SDK accepts reviewed app-server configuration, but its public API does not expose a documented application callback for intercepting an MCP result before the Codex runtime consumes it.

Therefore:

1. The real adapter may configure only one fixed stdio MCP server and exact tool allowlist.
2. No HTTP MCP transport, URL, bearer token, OAuth configuration, remote executor, shell wrapper, or caller-supplied environment is allowed.
3. Observing `mcp_tool_call` item events is not an enforcement or redaction seam.
4. Phase 10's requirement to independently redact every MCP result before model submission must be enforced inside the repository-owned model-facing MCP/runner boundary, or through a separately approved local stdio policy adapter.
5. Until that ownership and placement are approved and tested, the real adapter remains disabled. Fake-first workflow and contract implementation may proceed.

### II. Observed Evidence and Assumptions

#### Documented and supported

- `https://developers.openai.com/codex/sdk` documents the beta Python package, Python 3.10+ requirement, pinned runtime inclusion, synchronous/asynchronous clients, thread start, repeated turns, and read-only sandbox selection.
- `https://github.com/openai/codex/tree/rust-v0.144.4/sdk/python` publicly documents `Codex`, `AsyncCodex`, `thread_start`, `thread_resume`, `run`, `turn`, turn-scoped streaming, explicit interruption, structured output, public result/error models, and retry helpers for the pinned release.
- PyPI metadata for `openai-codex==0.144.4` records Python `>=3.10`, exact dependency `openai-codex-cli-bin==0.144.4`, distribution hashes, and provenance links.
- `https://developers.openai.com/codex/auth` documents ChatGPT subscription sign-in, local login caching, automatic token refresh during use, and configurable file/keyring/automatic credential storage.
- The Python SDK reuses an existing Codex authentication session. This architecture permits the official runtime to use its own session but prohibits repository code from calling SDK login/account methods or reading that cache.
- `https://developers.openai.com/codex/config-reference` documents fixed stdio MCP server command/arguments, exact enabled-tool filtering, required startup, startup timeout, and per-tool timeout.
- `docs/ai-ops/runtime/mcp-integration.md` confirms the existing model-facing diagnostic boundary is local stdio and delegates to the authoritative read-only runner.
- `docs/ai-ops/implementation-plan/09-local-orchestrator-core.md` requires a Python application with an injected fake adapter as the local default.
- `docs/ai-ops/implementation-plan/10-mcp-tool-loop-redaction-and-evidence.md` requires MCP result redaction, bounded tool-loop policy, and a separate metadata schema before provider use.

#### Documented limitations

- The Python SDK is beta and its public API may change before 1.0.
- The SDK controls the local Codex app-server over JSON-RPC; it is not an independent provider transport client.
- Explicit turn interruption is supported, but no distinct repository workflow-timeout option was found. The orchestrator must compose its own deadline around `interrupt()` and bounded cleanup.
- Public typed JSON-RPC errors and `TurnResult.error` exist, but a stable authentication-expiry discriminator was not confirmed.
- Retry helpers are public and opt-in. This architecture prohibits their use initially and applies zero automatic orchestrator retries.
- One client can consume multiple active turns concurrently, but the repository must enforce its stricter initial concurrency limit of one workflow.
- MCP controls remain Codex app-server configuration rather than a repository pre-consumption callback.
- Turn streams report activity but do not document a pre-consumption MCP result interception callback.
- Public package support is Python `>=3.10`; it does not select the project's exact Python patch or lockfile-generation tool.

#### Unknowns and implementation blockers

- **MCP result-redaction placement:** must be resolved before a real adapter can invoke Codex with MCP.
- **Authentication-expiry classification:** no stable public Python discriminator is confirmed. Initial real-adapter design may map only a conservative process/turn failure category; an operator-facing auth category requires a supported public discriminator.
- **Exact deployment toolchain:** the exact Python patch, deterministic lockfile-generation command, and repository package root need operator approval before Phase 09 scaffolding.
- **Dedicated identity and egress implementation:** deferred to Phase 11 and must not reuse `assistant` or gateway assumptions.
- **Vendor version compatibility:** no runtime experiment was performed. The first real-adapter contract test remains a separately approved local app-server test without provider traffic where possible.

#### Assumptions

- `openai-codex==0.144.4` and its exact `openai-codex-cli-bin==0.144.4` dependency are the accepted initial pair; beta/prerelease upgrades are excluded until separately reviewed.
- No package has been installed during Phase 08 documentation work.
- A repository-owned concurrency limit of one active workflow is the safe initial policy despite SDK support for concurrent turns.
- SDK retry helpers and all automatic orchestrator retries are disabled.
- The final real workflow uses `Sandbox.read_only`, fixed approval policy, disabled web search, no additional writable directories, and a fixed working directory.

### III. Required Technical Dependencies and Imports

#### Pinned dependency set

| Component | Accepted policy | Evidence / gate |
|---|---|---|
| `openai-codex` | Exact `0.144.4`; no range | Reviewed published PyPI package |
| `openai-codex-cli-bin` | Exact transitive `0.144.4` | SDK package metadata pins the same version |
| Python | Must satisfy `>=3.10`; exact deployment patch required in Chunk 0 | Public package/runtime requirement |
| pip/lock generator | Exact approved versions | Record alongside deterministic hash-locked requirements |
| Pydantic/test/lint/type tools | Exact resolved versions with hashes | Select and lock in Phase 09; no floating runtime environment |

No SDK package is needed to define the repository adapter protocol or fake. The first contracts/tests chunk should avoid importing `openai_codex`; the vendor dependency enters only with the disabled real-adapter module and contract tests.

#### Supply-chain policy

- Commit a direct-input requirements file and a fully resolved lockfile with hashes; install with `pip --require-hashes` inside a dedicated virtual environment.
- Record the exact supported Python patch, pip version, and lockfile-generation command accepted in Chunk 0.
- Review PyPI provenance, wheel/sdist hashes, license, direct/transitive dependency diff, package build metadata, vulnerabilities, and public API/type diff before initial acceptance and every update.
- CI/local safety tests run with network denied after dependencies are materialized through the separately approved dependency process.
- Never execute unreviewed package installation hooks or build an sdist when an accepted reviewed wheel is required.
- An upgrade changes `openai-codex` and `openai-codex-cli-bin` as one reviewed pair, reruns local adapter contract tests, and requires a separately approved remote acceptance later.
- Rollback restores the previously committed input/lockfile pair and virtual-environment build procedure; it never edits installed package contents or patches private protocol behavior.
- A supported-version failure is either a reviewed pair upgrade/rollback or `VENDOR_BLOCKED`; it is not a gateway recovery trigger.

#### Proposed repository artifacts

Paths are proposed and must be confirmed in Chunk 0:

```text
orchestrator/
  pyproject.toml
  requirements.in
  requirements.lock
  src/openstack_ai_ops_orchestrator/__init__.py
  src/openstack_ai_ops_orchestrator/contracts.py
  src/openstack_ai_ops_orchestrator/codex_adapter.py
  src/openstack_ai_ops_orchestrator/fake_codex_adapter.py
  src/openstack_ai_ops_orchestrator/official_codex_adapter.py
  src/openstack_ai_ops_orchestrator/orchestrator.py
  tests/test_contracts.py
  tests/test_fake_codex_adapter.py
  tests/test_orchestrator.py
```

Deployment, runtime-home, service, firewall, and evidence-ledger files are intentionally excluded from this ADS's implementation chunks.

### IV. Step-by-Step Procedure / Execution Flow

1. Accept one closed diagnostic request schema and reject unknown fields, workflows, duplicate keys, malformed input, and excessive size.
2. Assign a non-secret local correlation identifier.
3. Normalize and fail-closed redact operator context before adapter invocation.
4. Resolve a repository-owned immutable policy: one active workflow, fixed deadline, zero automatic retries, bounded turns/events/output, fixed model alias, read-only sandbox, web search disabled, fixed working directory, and no additional directories.
5. Select an injected adapter. Local tests and initial runtime select `FakeCodexAdapter`; selecting `OfficialCodexAdapter` requires an explicit later configuration gate.
6. Start a controlled turn through `turn()`, link operator cancellation and the workflow deadline to exactly one `interrupt()` call, and enforce a bounded post-interruption cleanup deadline.
7. Validate every adapter event against the closed repository event union and legal state transition table. Reject unknown, malformed, duplicated, out-of-order, or excessive events.
8. For fake-backed MCP scenarios, permit only the exact reviewed tool names and bounded result categories. Do not treat fake events as evidence that real MCP interception is supported.
9. On cancellation or timeout, interrupt once, stop consuming notifications, wait a bounded cleanup interval, and return a sanitized terminal category.
10. Validate final advisory text as untrusted data: type, byte limit, schema where required, and leak scan. It cannot authorize or execute remediation.
11. Construct metadata only from repository counters and categories. Never serialize vendor objects or errors.
12. Fail closed if metadata validation or persistence fails; advisory output must not be reported as a successfully evidenced workflow.
13. Dispose adapter/process resources and temporary schema files on every terminal path.
14. For the future real adapter only, enter `AsyncCodex` through its context manager with a curated process environment and reviewed `CodexConfig`. Reject SDK login/account methods, API-key login, arbitrary config, caller-selected model providers, `Sandbox.full_access`, live web search, steering/forking, retry helpers, and caller-selected MCP settings.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
|---|---|---|---|
| Input | Unknown workflow/field, malformed or oversized input | Reject before redaction and adapter selection | `rejected` / `INVALID_REQUEST` (proposed) |
| Redaction | Ambiguous or unscannable sensitive content | Discard content; do not invoke adapter | `policy_failed` / `REDACTION_FAILED` (proposed) |
| Adapter selection | Real adapter selected without explicit gate | Refuse construction | `policy_failed` / `REAL_ADAPTER_DISABLED` (proposed) |
| SDK start | Pinned app-server runtime missing, incompatible, or cannot start | Classify without retaining raw process output | `adapter_failed` / `SDK_START_FAILED` (proposed) |
| Authentication | Runtime reports an auth-related failure without a supported discriminator | Do not inspect credentials; report conservative operator action | `adapter_failed`; `auth_action_required` only after a public discriminator is confirmed |
| Event parsing | Unknown, malformed, duplicated, out-of-order, or excessive event | Abort and discard raw event | `adapter_failed` / `INVALID_ADAPTER_EVENT` (proposed) |
| MCP startup | Required fixed stdio server fails or surface drifts | Abort before workflow continues | `policy_failed` / `MCP_CONTRACT_FAILED` (proposed) |
| MCP request | Unknown or non-allowlisted tool appears | Abort; never execute fallback | `policy_failed` / `TOOL_DENIED` (proposed) |
| MCP result | Pre-model redaction seam is not proven | Keep real adapter disabled | `vendor_blocked` / `MCP_INTERCEPTION_UNSUPPORTED` (proposed) |
| Deadline | Workflow deadline expires | Interrupt once and perform bounded cleanup | `timed_out` / `DEADLINE_EXCEEDED` (proposed) |
| Cancellation | Operator cancellation interrupts turn | Interrupt once; no retry | `cancelled` / `CANCELLED` (proposed) |
| SDK/runtime | Process exits, turn fails, or stream raises | Map to fixed category; discard message/stderr | `adapter_failed` / `SDK_RUNTIME_FAILED` (proposed) |
| Output | Missing, malformed, oversized, or leak-scan failure | Discard advisory output | `policy_failed` / `OUTPUT_REJECTED` (proposed) |
| Evidence | Metadata cannot validate or persist | Do not claim completed workflow | `evidence_failed` / `EVIDENCE_FAILED` (proposed) |
| Version change | Contract/type tests differ from accepted pair | Reject upgrade or roll back lockfile | `vendor_blocked` / `SDK_CONTRACT_DRIFT` (proposed) |
| Private protocol | A fix requires route/header/response/token inspection | Stop; do not proxy, infer, or patch | `vendor_blocked` / `PRIVATE_PROTOCOL_REQUIRED` (proposed) |

No failure authorizes an API-key fallback, custom provider gateway recovery, credential inspection, generic shell access, broader MCP exposure, or automatic remote retry.

### VI. Security, Integrity, Idempotency, and Cleanup

- **Credentials:** Repository code receives no credential values and does not inspect credential storage. It must not call `login_api_key`, `login_chatgpt`, `login_chatgpt_device_code`, `account`, or otherwise inject credential material through the SDK.
- **Authentication:** ChatGPT login is an operator action performed later through the supported Codex flow in the dedicated runtime home. Codex alone caches and refreshes its session.
- **Environment:** The real adapter launches the pinned app-server with a minimal explicit environment instead of inheriting the full `os.environ`. Environment values must never be dumped.
- **Filesystem:** The real thread uses a fixed reviewed `cwd`, `Sandbox.read_only`, no caller-selected path, and no additional writable roots unless separately approved.
- **Tools:** Only fixed local stdio MCP and exact enabled tools are allowed. No URL MCP, listener, remote executor, shell wrapper, generic command, SSH, OpenStack CLI, database, mutation, or remediation capability is model-facing.
- **Network:** Fake/local phases deny network and never instantiate the SDK. Later egress belongs to the dedicated process identity; direct `assistant` public egress remains denied.
- **Private protocol:** Provider routes, headers, media types, response framing, tokens, and raw transport failures are opaque vendor concerns.
- **Logs/evidence:** Record only closed categories, counts, timestamps, correlation identifier, and reviewed usage counters. Exclude prompts, responses, tool output, raw events, thread IDs, exception text, stderr, credentials, account data, provider data, routes, and headers.
- **Integrity:** Reject unknown fields/events/transitions. Pin manifest and lockfile, verify registry integrity/provenance, and diff public types on upgrades.
- **Idempotency:** No implicit retry. A repeated request is a new workflow. Cancellation is applied once; cleanup tolerates already-exited processes.
- **Cleanup:** Close notification iteration, interrupt active work once, bound app-server shutdown, remove only orchestrator-owned temporary schema/state, and preserve Codex-owned session/credential state untouched.
- **Advisory output:** Model text is untrusted and cannot trigger code execution, deployment, OpenStack mutation, or remediation.

### VII. Validation Strategy

#### Phase 08 documentation validation

- **Structure:** `rtk grep -nE '^### (I|II|III|IV|V|VI|VII|VIII|IX|X)\.' docs/ai-ops/implementation-plan/ads/08-00-orchestrator-architecture-and-sdk-contracts-ads.md`
- **Safety terms:** verify explicit prohibitions for credentials, API keys, private protocol, provider traffic, HTTP MCP, and raw evidence.
- **Whitespace:** `rtk git diff --check`
- **Diff:** `rtk git diff -- docs/ai-ops/implementation-plan/ads/08-00-orchestrator-architecture-and-sdk-contracts-ads.md`

#### Future chunk-aware implementation validation

Exact scripts are finalized with the package root in Chunk 0. The intended sequence is:

```bash
rtk python3 -m venv /tmp/openstack-ai-ops-orchestrator-venv
source /tmp/openstack-ai-ops-orchestrator-venv/bin/activate
rtk python -m pip install --require-hashes -r orchestrator/requirements.lock
rtk python -m ruff format --check orchestrator
rtk python -m ruff check orchestrator
rtk python -m mypy orchestrator/src orchestrator/tests
rtk python -m pytest -q orchestrator/tests
rtk git diff --check
```

Required targeted proofs:

- invalid input fails before adapter invocation;
- fake adapter is the only default/test adapter;
- the disabled real adapter cannot enter `AsyncCodex` or start the app-server;
- cancellation and deadline reach terminal states and clean up;
- event, turn, output, and concurrency bounds fail closed;
- raw prompt/response/tool/error markers do not appear in logs, snapshots, or metadata;
- tests open no listener, perform no DNS/provider connection, inspect no credential path, and start no real Codex process;
- SDK version changes run exported-type and adapter contract comparison before acceptance;
- real MCP/provider tests remain absent until their separate approval gates.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass.

#### Chunk 0: Integration, Toolchain, and Blocker Confirmation

- **Goal:** Accept the package root, exact Python/pip/lock-generator pins, accepted `openai-codex==0.144.4`/CLI pair, repository scripts, and disposition of the MCP pre-model redaction blocker.
- **Files to read:** this ADS; Phase 09 and Phase 10 plans; local MCP runbook; existing Python/CI/toolchain files; official pinned SDK public API documentation.
- **Commands:** repository discovery, public API comparison, and documentation-only checks; do not install, authenticate, invoke Codex, or contact a provider.
- **Evidence to confirm:** exact package path; exact Python toolchain/lock policy; no package/module collision; supported SDK symbols; fake default; real-adapter stop gate; approved MCP redaction placement.
- **Validation:** no repository changes; report findings as supported, limitation, or blocker.
- **Stop condition:** all decisions are recorded, or implementation stops on an unresolved package/toolchain or MCP ownership blocker.

#### Chunk 1: Package Skeleton and Closed Contracts

- **Goal:** Add a deterministic Python package and compile-safe workflow/adapter protocols without importing or invoking the Codex SDK.
- **Files to change:** proposed `orchestrator/pyproject.toml`, input/lock requirements, `src/openstack_ai_ops_orchestrator/contracts.py`, and one focused contract test file; final paths come from Chunk 0.
- **Symbols to add/change:** request schema, workflow states, repository event union, adapter result/error categories, limits, and conceptual `CodexAdapter` `Protocol`.
- **Implementation shape:** exact pins and hash-locked requirements; closed enums/unions; fake adapter not yet functional; no network/runtime code.
- **Validation:** Ruff formatting/lint, mypy, and focused pytest contract tests through accepted package commands.
- **Stop condition:** package validates offline after approved dependency materialization and invalid contracts fail closed.

#### Chunk 2: Fake Adapter Cancellation Slice

- **Goal:** Implement one deterministic fake success path plus cancellation/deadline behavior.
- **Files to change:** proposed `src/openstack_ai_ops_orchestrator/fake_codex_adapter.py` and `tests/test_fake_codex_adapter.py`.
- **Symbols to add/change:** `FakeCodexAdapter`, deterministic scenario input, bounded async event iterator, cancellation handling.
- **Implementation shape:** emit only repository events; no `openai_codex` import, app-server start, filesystem credential access, or socket use.
- **Validation:** focused pytest fake-adapter tests plus mypy.
- **Stop condition:** success, cancellation, and timeout are deterministic and cleanup assertions pass.

#### Chunk 3: One Fake-Backed Workflow Slice

- **Goal:** Connect request validation, redaction seam, state transitions, fake adapter, output bounds, and sanitized terminal result for one diagnostic workflow.
- **Files to change:** proposed `src/openstack_ai_ops_orchestrator/orchestrator.py` and `tests/test_orchestrator.py`.
- **Symbols to add/change:** async workflow entry point, state reducer, limit enforcement, advisory-output validator.
- **Implementation shape:** constructor/function dependency injection is mandatory; caller cannot select the real adapter; model output remains data.
- **Validation:** focused pytest end-to-end local tests, mypy, leak-marker assertions, and no-network/process assertions.
- **Stop condition:** one fake-backed workflow completes locally and every negative path stops before any real runtime boundary.

#### Chunk 4: Disabled Official Adapter and Public Type Mapping

- **Goal:** Add the vendor import boundary and compile-safe mapping against the pinned public SDK types while keeping execution disabled.
- **Files to change:** proposed `src/openstack_ai_ops_orchestrator/official_codex_adapter.py` and one adapter contract test file.
- **Symbols to add/change:** `OfficialCodexAdapter`, SDK-to-repository notification/result mapper, curated `CodexConfig` builder, explicit disabled gate.
- **Implementation shape:** reject SDK login/account methods, API-key login, arbitrary config, unsafe sandbox, web search, steering/forking, retries, and uncontrolled paths; construction or `run_turn` returns `REAL_ADAPTER_DISABLED` before entering `AsyncCodex`.
- **Validation:** mypy against exact SDK version; static tests prove prohibited methods/config cannot be reached or produced; no app-server invocation.
- **Stop condition:** public type drift is detectable and all tests prove the real process cannot start.

#### Chunk 5: Bounds, Error Sanitization, and Metadata Contract

- **Goal:** Complete fake-first failure coverage and metadata-only lifecycle mapping.
- **Files to change:** proposed orchestrator/contract modules and focused tests, limited to one implementation file plus one test file per subchunk if needed.
- **Symbols to add/change:** event/turn/output counters, error classifier, metadata builder/validator, cleanup coordinator.
- **Implementation shape:** map all free-form failures to fixed categories and discard raw content; evidence failure overrides apparent success.
- **Validation:** malformed/excessive event tests, raw-marker leak tests, cleanup tests, format/lint/type-check.
- **Stop condition:** every planned terminal category is deterministic under the fake and no raw content survives.

#### Chunk 6: Local Safety Acceptance and Phase 09 Handoff

- **Goal:** Validate the complete fake-backed vertical slice and document remaining real-adapter gates without enabling any remote boundary.
- **Files to change:** tests and accepted local validation documentation only; no deployment/auth/egress files.
- **Symbols to add/change:** only missing acceptance fixtures or assertions.
- **Implementation shape:** run the full package validation with fake injection; prove no real Codex process, credential path, listener, DNS, or provider access.
- **Validation:** accepted package scripts, `rtk git diff --check`, changed-file diff review, and secret/risky-pattern review.
- **Stop condition:** Phase 09 can proceed/close locally; real adapter remains disabled until MCP redaction, deployment identity, authentication, and egress gates are separately approved.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Phase 08/09 hybrid Codex SDK orchestrator fake-first vertical slice, as specified by docs/ai-ops/implementation-plan/ads/08-00-orchestrator-architecture-and-sdk-contracts-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm repository evidence, exact toolchain/package decisions, and the MCP result-redaction blocker. Do not install packages, authenticate, invoke Codex, inspect credentials, or contact a provider. Stop after the discovery report.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Execute Chunk 1 only from the accepted ADS and Chunk 0 decisions.
Do not continue to Chunk 2.
Keep the real Codex adapter absent or explicitly disabled. After editing, run targeted format, lint, type-check, tests, and show git diff.
```

### X. Conclusion and Next Steps

- Phase 08 Step 1 confirms a supported beta Python SDK/app-server contract, Python 3.10+ baseline, synchronous/asynchronous threads, turn-scoped streaming, structured output, explicit interruption, reviewed sandbox/configuration controls, fixed stdio MCP configuration, and Codex-managed ChatGPT session caching/refresh.
- Accepted dependency pair `openai-codex==0.144.4` plus `openai-codex-cli-bin==0.144.4` is grounded in public PyPI metadata but must not be installed until the exact Python toolchain, hash-lock procedure, and package location are accepted.
- Fake-first local architecture is implementation-ready after Chunk 0 decisions. It requires no credentials, provider traffic, deployment, egress, or private protocol behavior.
- The real adapter is not implementation-ready because the public Python SDK does not document a pre-model MCP result interception callback. Phase 10 must place independent result redaction in the repository-owned model-facing MCP/runner boundary or approve another local stdio enforcement seam.
- Authentication-expiry reporting must remain conservative until a public stable discriminator is identified; repository code must never inspect credential state to classify it.
- The next action is review and acceptance of this revised ADS, followed by Chunk 0 only. Deployment, login, egress, provider acceptance, and gateway retirement remain later separately approved phases.
