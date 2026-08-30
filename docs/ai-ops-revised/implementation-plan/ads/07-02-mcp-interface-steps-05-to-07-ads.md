## Architectural Design Specification: MCP Diagnostic Prompts, Safety Acceptance, and Lifecycle Closure — Steps 5–7

**Source:** `docs/ai-ops-revised/implementation-plan/07-mcp-interface.md`, Steps 5 through 7; PRD requirements FR-032 through FR-039, NFR-001 through NFR-010, NFR-016 through NFR-017, and the Phase 07 definition of done.

**Goal:** Complete the Phase 07 MCP interface by adding a closed set of repeatable diagnostic-only prompts to the accepted local-stdio adapter, proving prompt/tool/resource safety and runner equivalence through local fixtures, and documenting and statically validating client-owned lifecycle, disablement, and rollback. The work must add no diagnostic authority, remediation primitive, client registration, provider integration, listener, uncontrolled file access, or alternate runner path.

---

### I. Overview and Contract

This ADS begins after the locally implemented and statically accepted Steps 1–4 boundary:

```text
owner-managed local client
  -> local-stdio MCP prompt discovery/rendering
  -> advisory workflow message naming only discovered tools
  -> client-selected MCP tool calls
  -> accepted local-stdio adapter
  -> fixed revised runner
  -> accepted result/redaction/audit boundary
  -> diagnostic explanation and unexecuted manual next actions
```

Prompt rendering is non-executable. Listing or getting a prompt must not invoke the runner, read a credential or audit file, inspect OpenStack, access the network, or create a child process. The MCP client may subsequently choose approved tools, but every such call remains governed by the existing Step 1–4 tool and runner contracts.

#### Prompt allowlist contract

The initial local-stdio prompt set is exactly:

| Prompt | Arguments | Approved tool sequence | Required boundary |
| --- | --- | --- | --- |
| `project_summary` | none | `project_resource_summary` | Project-visible summary only; no cloud-wide, host, guest, or service-health inference. |
| `server_inspection` | required `server_identifier` | `server_basic_info`, then `server_network_info` with the same identifier | Keep server and attachment evidence separate; do not infer guest, packet, metadata, or host health. |
| `metadata_diagnosis` | required `server_identifier` | `project_resource_summary`, `server_basic_info`, then `server_network_info` with the same identifier | Label guest, Neutron proxy/agent, Nova metadata, listener, log, and host evidence as unavailable unless separately exposed. |

`server_identifier` uses the already accepted schema:

```text
pattern: ^[A-Za-z0-9._:-]+$
maximum length: 255
```

Unknown, missing, extra, non-string, empty, unsafe, or oversized prompt arguments fail before a prompt message is returned. Prompt names, argument names, descriptions, order, and rendered instructions are fixed and deterministic.

Standalone `network_diagnosis` and `volume_diagnosis` prompts are not registered initially. The current three-tool local exposure can describe project-visible server attachments and project-visible volume inventory, but it does not prove end-to-end network behavior, volume attachment health, guest behavior, control-plane service health, or host state. A future prompt requires an explicit evidence-sufficiency review and exact approved tool sequence; absence is safer than an overclaiming prompt.

#### Prompt response contract

Every rendered prompt must instruct the client/model to produce these sections in order:

1. **Observed evidence**;
2. **Healthy signals**;
3. **Failing signals**;
4. **Inferences and likely failure domain**;
5. **Missing or unavailable evidence**; and
6. **Manual next actions — not executed**.

Every prompt must also instruct the client/model to:

- use only the exact named tools when they are present in discovery;
- preserve tool status, correlation ID, duration, timestamp, and truncation semantics;
- treat `unavailable`, `timeout`, `denied`, `validation_error`, `error`, empty sections, and truncation as evidence gaps rather than health;
- keep operator-reported symptoms distinct from tool-observed evidence;
- refuse create, update, delete, restart, stop, install, edit, SSH, sudo, shell, raw OpenStack, file, database, package, service-control, and remediation requests;
- never invent a command, tool, result, identifier, credential, or observed fact; and
- state that every recommendation is manual, advisory, and unexecuted.

A “fix it” request does not select a remediation prompt or tool. The prompt text requires refusal of mutation and permits only approved read-only evidence collection followed by manual recommendations.

**Function Signature Contract (Conceptual):** inferred from the current low-level SDK adapter and the reviewed historical prompt seam; exact SDK types must be confirmed in Chunk 0.

```text
list_diagnostic_prompts() -> list[MCP Prompt descriptor]
```

- **Input:** none; uses one closed in-code prompt definition table.
- **Output:** the three deterministic descriptors above.
- **Temporary stub:** return only the implemented prompt descriptors for the current chunk; never advertise a prompt whose renderer is absent.
- **Safety:** no file, network, subprocess, runner, audit, or credential access.

**Function Signature Contract (Conceptual):**

```text
validate_prompt_arguments(prompt_name, arguments) -> validated string map
```

- **Input:** one allowlisted prompt name and an optional MCP string map.
- **Output:** an exact closed argument map.
- **Temporary stub:** raise a bounded prompt-contract error for prompt names not yet implemented.
- **Safety:** unknown/extra/unsafe input is rejected without rendering or child creation.

**Function Signature Contract (Conceptual):**

```text
render_diagnostic_prompt(prompt_name, arguments, exposed_tool_names)
  -> MCP GetPromptResult
```

- **Input:** one validated prompt request and the already validated discovered-tool name set.
- **Output:** one bounded deterministic user-role text message with the required workflow and refusal boundaries.
- **Temporary stub:** return a clear bounded unavailable error until that prompt's complete workflow text and tests exist; never return false success.
- **Safety:** if a required tool is not exposed, the message labels it unavailable or the prompt is omitted according to the frozen contract; it never suggests a replacement command or broader capability.

#### Step 6 acceptance contract

Step 6 extends, rather than replaces, the existing focused tests. Acceptance must prove:

- discovery is exactly the three approved tools, six static resources, and three prompts for local stdio;
- Phase 06, generic, provider, file, network-fetch, and remediation capabilities remain absent;
- prompt rendering is deterministic, bounded, argument-validated, and non-executable;
- valid/invalid tool requests preserve accepted runner behavior;
- all six runner terminal statuses, truncation, timestamp, and correlation ID mappings remain intact;
- timeout, cancellation, EOF, and shutdown leave no runner child;
- resources and prompts reject secret/topology canaries and arbitrary access;
- the adapter writes no duplicate tool audit and preserves fixture correlation semantics; and
- no test requires mutation, package acquisition, network access, a live runner, OpenStack, or raw audit inspection.

#### Step 7 lifecycle and rollback contract

Local stdio has no service and no listener. The externally managed client owns registration and launches the exact adapter process as `aiops_assistant`. Repository documentation may describe the required command and environment constraints, but it must not commit or modify the client's registration artifact.

Local disablement order is:

1. prevent new launches by disabling/removing the owner-managed client registration outside this repository;
2. close stdin or terminate the exact client-owned adapter session;
3. verify the adapter reaps its runner child and exits;
4. verify no local MCP or runner child remains and no listener was created;
5. preserve the revised manual/local runner workflow; and
6. retain inert artifacts or remove only exact local-stdio artifacts under separate rollback approval.

Upgrade order is disable, verify process absence, validate the approved hash-locked SDK/offline artifact and reviewed repository artifacts, materialize the new revision under the fixed paths, run static/fixture checks, and only then allow the external owner to re-enable client registration.

The proposed repository deployment entrypoint is `ansible/ai_ops_assistant/playbook_deploy_mcp_stdio.yml`, subject to Chunk 0 approval. It remains limited to `ai_ops_assistant`/`assistant02`, includes only the local-stdio role, defaults to disabled, and performs no package install, client registration, process start, runner call, audit read, or rollback action.

Option B remains governed by `07-01-internal-network-mcp-extension-ads.md` and `mcp-interface-internal-network-operations-contract.md`. Step 7 may prove one authenticated project-summary call and one same-identifier server basic/network fixture sequence without opening a listener. Live TLS, firewall, listener, external-client, and rollback validation remain separately approved.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops-revised/implementation-plan/07-mcp-interface.md` leaves Steps 5–7 and the Phase 07 definition of done unchecked.
- The Step 1–4 completion boundary records local implementation, static acceptance, and default-disabled artifact packaging while the SDK lock/offline wheel and operational actions remain blocked.
- `docs/ai-ops-revised/prd.md` FR-032 through FR-039 require diagnostic-only behavior, “fix it” refusal, reviewed MCP capabilities/resources, and repeatable prompts such as metadata troubleshooting.
- `docs/ai-ops-revised/runtime/manual-aiops-workflows.md` defines the approved project summary, same-identifier server inspection, metadata evidence sequence, six-part explanation structure, unavailable-evidence handling, and refusal behavior.
- `docs/ai-ops-revised/runtime/mcp-interface-steps-01-to-04-operations-contract.md` fixes local stdio, the owner-managed client boundary, the three initial tools, six resources, `local_cli` audit actor, one runner child, no persistent logging, default-disabled artifacts, and separate operational approvals.
- `ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio/files/mcp_stdio/aiops_assistant_mcp_stdio_server.py` currently registers tools/resources only. Its `create_server` seam has the validated exposed tools and can register low-level `list_prompts`/`get_prompt` handlers without changing runner delegation.
- `test_stdio_lifecycle.py` and `test_curated_resources.py` explicitly assert that `ListPromptsRequest` and `GetPromptRequest` are absent. Those assertions are the exact Step 5 transition points.
- Existing local tests already cover configuration failure, stdio-only imports, initial discovery, resource allowlisting, request validation, result mapping, cancellation, and sanitized adapter errors.
- The historical `ansible/ai_ops_runtime/.../aiops_mcp_server.py` demonstrates low-level prompt APIs and three similarly named workflows, but its paths, result/request identity, optional-tool assumptions, and runtime contract are historical evidence only and must not be copied unchanged.
- `ai_ops_assistant_mcp_stdio/defaults/main.yml` and `tasks/main.yml` are artifact-only, default-disabled, and currently accept only lifecycle action `present`. No local-stdio deployment playbook exists.
- `test_deployment_static.sh` deliberately fails if a local-stdio deployment playbook or removal behavior exists; a later approved lifecycle chunk must update this acceptance boundary intentionally.
- The SDK requirement is `mcp==1.28.1`, but `requirements.lock` and the approved offline wheel remain absent. Enabled deployment must therefore continue to fail closed.
- The repository contains a disabled Option B adapter and focused tests under `roles/ai_ops_assistant_mcp/` and `tests/mcp/`. Existing tests prove authenticated three-tool/resource fixture behavior and no prompt handler, but the Option B operations contract's “Current Scope and Next Gate” still describes implementation as future work. Chunk 0 must reconcile that documentation/source status before Step 7 relies on it.

#### Assumptions

- **Proposed:** prompt support is added first to the accepted local-stdio baseline. Option B prompt exposure is not implied; it requires a separate explicit decision because its adapter and lifecycle are independently controlled.
- **Proposed:** prompt definitions and rendered text remain in the adapter source to avoid a new dynamically loaded instruction path. If reviewers require a separate catalog, Chunk 0 must freeze its schema, bounds, deployment path, and scans before implementation.
- **Proposed:** the exact initial prompt names are `project_summary`, `server_inspection`, and `metadata_diagnosis`, following existing domain language without inheriting historical runtime authority.
- **Proposed:** no standalone network or volume prompt is initially exposed because current evidence is insufficient for a bounded end-to-end diagnosis.
- **Assumed:** fixture validation is acceptable for the Option B Step 7 workflow requirement unless an owner separately authorizes an integration environment.
- **Assumed:** disabling external client registration is sufficient to disable local MCP execution because no local service, listener, or restart loop exists.
- **Assumed:** inert local artifacts may remain after disablement; artifact removal and dedicated venv removal are separate rollback actions requiring exact ownership and dependency checks.

#### Open confirmations for Chunk 0

1. Approve the exact three prompt names, descriptions, ordering, argument contract, text owners, and maximum rendered-message byte limit.
2. Confirm that local stdio is the initial prompt-bearing mode and whether Option B must also expose prompts in Phase 07.
3. Confirm that standalone network and volume prompts remain non-discoverable based on current evidence sufficiency.
4. Confirm whether prompt text is in-code or stored in a new closed static catalog.
5. Confirm the exact SDK 1.28.1 low-level prompt handler signatures and error behavior in the approved validation environment.
6. Approve the proposed Steps 5–7 operations-contract path and the documentation owner for external client lifecycle instructions.
7. Decide whether `playbook_deploy_mcp_stdio.yml` is required and authorize only its default-disabled static addition.
8. Decide whether fixture-only Option B workflow validation satisfies Step 7 or whether a separately approved TLS integration environment is required.
9. Reconcile the Option B operations contract's implementation-status statement with the executable files and tests currently present.
10. Confirm SDK lock/wheel provenance status and keep deployment, registration, runner execution, audit inspection, and rollback as independent approvals.
11. Confirm the exact outcome-only evidence owner, protected location, retention, and allowed fields if any operational validation is later authorized.

### III. Required Technical Dependencies and Imports

- Existing official Python MCP SDK requirement `mcp==1.28.1`; no new package or extra is introduced by prompt support.
- Existing low-level `mcp.types` prompt descriptors/results and `Server.list_prompts()`/`Server.get_prompt()` registration APIs, subject to Chunk 0 signature verification.
- Existing Python standard-library types and regex validation. No provider, model, HTTP, socket, SSH, database, shell, file-serving, or orchestration import is required.
- Existing local adapter tool-name/schema constants and validated exposed-tool set. Prompt code must not import runner implementations or diagnostic scripts.
- Existing `unittest` test style under `ansible/ai_ops_assistant/tests/mcp_stdio/` and Option B fixture tests under `tests/mcp/`.
- Proposed operations contract: `docs/ai-ops-revised/runtime/mcp-interface-steps-05-to-07-operations-contract.md`.
- Proposed default-disabled playbook: `ansible/ai_ops_assistant/playbook_deploy_mcp_stdio.yml`, only if separately approved in Chunk 0.
- Not permitted: historical prompt module imports, external-client packages/configuration, provider/model SDKs, prompt templates selected by caller paths/URLs, arbitrary user-authored instruction files, package download, or live infrastructure dependencies.

### IV. Step-by-Step Procedure / Execution Flow

1. Confirm the reviewed Steps 1–4 aggregate, current branch/diff, existing local adapter/test contracts, missing lock/wheel blocker, and unchanged external client boundary.
2. Reconcile the Option B documentation/source status before treating its fixture tests as accepted Step 7 evidence.
3. Freeze the Steps 5–7 non-activation operations contract: prompt allowlist, argument schemas, required output structure, refusal language, byte bounds, test matrix, client lifecycle, upgrade, disablement, Option B fixture scope, rollback, and authorization gates.
4. Add a compile-safe prompt definition/validation/rendering seam to the local adapter. Initially advertise only `project_summary`; prompt listing/getting performs no tool call or I/O.
5. Register low-level prompt handlers in `create_server` only after the corresponding renderer and focused tests exist.
6. Extend the same seam to `server_inspection`, enforcing one safe identifier and an exact same-identifier basic/network sequence in the advisory text.
7. Add `metadata_diagnosis`, preserving the project/basic/network sequence and explicitly naming unavailable guest, proxy/agent, Nova metadata, listener, host, and log evidence.
8. Keep standalone network/volume prompts absent. Add tests proving they are not discoverable.
9. Add prompt tests for exact discovery, argument validation, deterministic bounded rendering, required explanation sections, refusal language, unavailable evidence, secret/topology canaries, and no subprocess/file/network/audit access.
10. Extend safety/integration fixtures to cover exact tools/resources/prompts, forbidden capabilities, six runner statuses, timeout/truncation/correlation behavior, cancellation/reaping, and no duplicate adapter audit.
11. Add one Option B fixture project-summary request and one same-identifier server basic/network sequence under the accepted authenticated principal, without constructing or running a listener.
12. Document the external client launch/lifecycle contract without committing registration configuration. Define process-health, stderr, upgrade, disablement, and artifact rollback checks.
13. If separately approved, add the default-disabled local deployment playbook and update static acceptance to require the exact host/role/limit boundary and prohibit activation or operational calls.
14. Run focused local-stdio and Option B fixture tests in the approved environment. Run Ansible/static checks only for changed deployment files.
15. Stop before package acquisition, host deployment, client registration, process startup, live runner/OpenStack calls, raw audit inspection, TLS/firewall changes, or rollback execution.
16. Reconcile Step 5–7 and Phase DoD checkboxes only from reviewed evidence. Leave operationally blocked items unchecked.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| --- | --- | --- | --- |
| Prerequisite | Steps 1–4 diff/acceptance changed or lock/wheel provenance is unresolved | Continue only with local source/fixture work; prohibit activation | prerequisite or dependency blocker |
| Prompt contract | Prompt name, argument, ordering, owner, or text is unresolved | Advertise no new prompt | `prompt_contract_error` (proposed) |
| Prompt discovery | Descriptor exists without a complete renderer or required tool contract | Fail startup or omit the incomplete prompt; never advertise false capability | `prompt_exposure_error` (proposed) |
| Prompt request | Unknown prompt or missing/extra/non-string argument | Reject with bounded protocol error; invoke no tool | prompt validation error |
| Identifier | Empty, unsafe, or overlong `server_identifier` | Reject before rendering | prompt validation error |
| Tool availability | Prompt requires a tool absent from validated discovery | Omit prompt or render an explicit unavailable-evidence boundary according to the frozen contract | bounded unavailable result |
| Prompt rendering | Output exceeds fixed byte bound or omits safety/refusal sections | Reject the rendered message and expose no partial text | `prompt_render_error` (proposed) |
| Prompt disclosure | Rendered text contains secret canary, address, protected path, raw command, credential, or private topology | Fail tests/startup and reject the revision | content-review blocker |
| Remediation intent | Prompt implies execution, restart, mutation, command invention, or broader authority | Reject content; preserve diagnostic-only refusal | safety acceptance failure |
| Network/volume prompt | Evidence does not support a bounded workflow | Keep prompt non-discoverable | evidence-sufficiency blocker |
| Tool integration | Valid/invalid call behavior differs from accepted runner semantics | Fail Step 6; do not weaken MCP or runner validation | equivalence failure |
| Result mapping | Status, truncation, timestamp, correlation, or error mapping changes | Reject the adapter revision | result-equivalence failure |
| Audit | Adapter writes a duplicate tool audit or drops fixture correlation semantics | Fail tests; retain runner as sole audit writer | audit-equivalence failure |
| Cancellation | EOF/cancel/timeout leaves a runner child | Fail lifecycle acceptance and keep client disabled | orphan-process blocker |
| Local client | Registration owner, launch user, environment, or shutdown behavior is unknown | Document blocker; do not add repository registration | external-client blocker |
| Deployment playbook | Playbook broadens hosts, enables role, installs packages, starts processes, or invokes runner | Reject playbook; preserve artifact-only default-disabled state | deployment-scope error |
| Disablement | Client can automatically restart the adapter or stdin closure does not stop it | Keep integration disabled and require owner correction | lifecycle error |
| Option B status | Contract and present source disagree or authenticated fixture boundary is unclear | Do not claim Option B Step 7 evidence | status-reconciliation blocker |
| Option B integration | Fixture would open a listener, require credentials, or contact a network | Stop and use injected handlers only | authorization blocker |
| Rollback | Removal target contains shared/unknown artifacts or affects runner/manual workflow | Abort removal and preserve shared state | rollback-scope error |
| Evidence | Raw prompts/results/audits, identifiers, addresses, or secrets would enter Git | Retain only normalized outcomes in approved protected storage | evidence-disclosure blocker |

### VI. Security, Integrity, Idempotency, and Cleanup

- **Security:** prompts are advisory static messages, not an execution or authorization boundary. They name only discovered approved tools and cannot add shell, SSH, sudo, OpenStack passthrough, file, database, package, service, provider, or remediation capability.
- **Prompt injection resistance:** operator symptoms and tool-returned strings are untrusted evidence. Static prompt instructions require evidence/inference separation and never interpolate arbitrary user prose into executable instructions.
- **Minimum disclosure:** prompt definitions contain no addresses, inventory, credentials, profile paths/content, audit paths/content, protected topology, raw result examples, or live identifiers. Tests use synthetic canaries only.
- **Integrity:** prompt definitions, descriptors, arguments, order, and output headings are closed and deterministic. Unknown fields/names fail rather than widening behavior.
- **Single execution boundary:** listing/getting prompts creates no child. Subsequent calls still use only `invoke_revised_runner` and the accepted runner-owned validation, credentials, bounds, redaction, result, and audit path.
- **Deny by default:** only three prompts are initially discoverable. Standalone network/volume prompts and all remediation prompts remain absent.
- **Idempotency:** repeated prompt list/get requests return the same content and create no state. Static lifecycle checks are repeatable. Tool requests remain at-most-once and are never automatically retried.
- **Client isolation:** no client configuration, provider/model identity, token, proxy, OpenStack environment, or free-form client identity is added to the repository or runner audit.
- **Logging:** local stdio stdout remains protocol-only. Persistent logging remains disabled; bounded sanitized stderr contains no prompt arguments/content, tool payload, result, path, or raw exception.
- **Cleanup:** prompt requests have no cleanup side effects. Tool cancellation continues to terminate/reap only the request child. Client shutdown closes stdin and leaves no adapter or runner child.
- **Rollback:** disable external registration first, verify process/child absence, then preserve or remove only exact local MCP artifacts under approval. The runner, diagnostics, credentials, audits, evidence, Option B, and historical runtime remain untouched.

### VII. Validation Strategy

Validation is local, fixture-driven, and chunk-aware. Commands do not authorize downloads, deployment, registration, listeners, live diagnostics, OpenStack access, audit inspection, or rollback.

#### Documentation and static checks

```bash
rtk grep -n '^### ' docs/ai-ops-revised/implementation-plan/ads/07-02-mcp-interface-steps-05-to-07-ads.md
rtk grep -n 'project_summary\|server_inspection\|metadata_diagnosis\|fix it\|rollback' docs/ai-ops-revised/implementation-plan/ads/07-02-mcp-interface-steps-05-to-07-ads.md
rtk git diff --check
rtk git diff -- docs/ai-ops-revised/implementation-plan/ads/07-02-mcp-interface-steps-05-to-07-ads.md
```

#### Future Python validation

Use only the operator-confirmed approved Python environment. Do not use system Python or acquire packages during implementation.

```bash
<approved-python-venv>/bin/python -m py_compile \
  ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio/files/mcp_stdio/aiops_assistant_mcp_stdio_server.py
<approved-python-venv>/bin/python -m unittest discover \
  -s ansible/ai_ops_assistant/tests/mcp_stdio -p 'test_*.py'
<approved-python-venv>/bin/python -m unittest discover \
  -s ansible/ai_ops_assistant/tests/mcp -p 'test_*.py'
```

Chunk 0 must confirm an existing repository-approved Python formatter/linter. If none exists, do not install one; preserve current style and use compilation, focused tests, and diff review. If one is confirmed, freeze and run its check-only command on the changed adapter/test files.

#### Future shell/Ansible validation

```bash
rtk bash -n ansible/ai_ops_assistant/tests/mcp_stdio/test_deployment_static.sh
PYTHON_BIN=<approved-python-venv>/bin/python \
  rtk bash ansible/ai_ops_assistant/tests/mcp_stdio/test_deployment_static.sh
rtk yamllint ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio/defaults/main.yml \
  ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio/tasks/main.yml \
  ansible/ai_ops_assistant/playbook_deploy_mcp_stdio.yml
rtk ansible-lint ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio \
  ansible/ai_ops_assistant/playbook_deploy_mcp_stdio.yml
rtk ansible-playbook --syntax-check ansible/ai_ops_assistant/playbook_deploy_mcp_stdio.yml
```

The syntax check must use a non-executing inventory/harness confirmed in Chunk 0 and must not contact a host.

#### Required behavior checks

1. Local discovery returns exactly three prompt descriptors in reviewed order.
2. Unknown prompt names and invalid argument maps fail without runner/subprocess/file/network access.
3. Project prompt names only `project_resource_summary` and states project-scope limitations.
4. Server prompt names basic then network tools and requires the same validated identifier.
5. Metadata prompt uses project/basic/network evidence and labels all unavailable guest/Phase 06 evidence.
6. Every prompt contains the six required output sections and mutation/refusal/manual-unexecuted language.
7. `network_diagnosis`, `volume_diagnosis`, `fix_it`, and every generic/remediation prompt are absent.
8. Prompt content rejects secret, private-key, token, password, bearer, address, protected-path, command, and raw-output canaries.
9. Prompt list/get performs no child creation, audit write, resource read, or network operation.
10. Existing tool/resource discovery and schema tests remain unchanged except intentional prompt registration assertions.
11. Six status classes, truncation, timeout, validation, correlation, and sanitized errors remain equivalent.
12. Cancellation, EOF, and shutdown leave no child; stdout remains protocol-only.
13. Option B fixtures perform one authenticated project call and same-identifier server basic/network sequence without listener construction.
14. Local deployment wiring remains default-disabled, assistant-host-limited, artifact-only, and free of package/client/process/network/audit/rollback actions.
15. Final diff contains no secrets, addresses, protected evidence, client registration, provider integration, or unsupported completion claims.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass.

#### Chunk 0: Discovery and Integration Confirmation

- **Goal:** Confirm the current Steps 1–4 aggregate, prompt API seam, exact prompt contract, test baseline, Option B status, lifecycle decisions, and authorization gates without edits.
- **Files to read:** Phase 07 plan; this ADS; both Phase 07 operations contracts; local and Option B adapters/tests; manual workflow contract; local role defaults/tasks/static test; SDK metadata available in the approved environment.
- **Commands:** bounded `rtk git status`, `rtk find`, `rtk grep`, targeted reads, and SDK signature inspection using only the approved environment. Do not execute servers, runners, networks, package tools, audits, or deployment.
- **Evidence to confirm:** three prompt names/text owners/bounds; low-level SDK signatures; no standalone network/volume prompt; in-code versus catalog decision; proposed contract/playbook paths; Option B source/contract reconciliation; fixture versus live Step 7 scope; lock/wheel and independent approvals.
- **Stop condition:** no edits. Produce a decision/blocker report. Any unresolved prompt safety, SDK signature, Option B status, or client lifecycle decision blocks Chunk 1.

#### Chunk 1: Steps 5–7 Non-Activation Operations Contract

- **Goal:** Freeze prompt, safety-test, external-client lifecycle, disablement, upgrade, Option B fixture, evidence, and rollback contracts before executable changes.
- **Files to change:** proposed `docs/ai-ops-revised/runtime/mcp-interface-steps-05-to-07-operations-contract.md` only.
- **Symbols to add/change:** no executable symbols; exact prompt table, output/refusal contract, byte bounds, test matrix, lifecycle/health checks, deployment/playbook decision, authorization matrix, and rollback order.
- **Implementation shape:** documentation only; unresolved operational actions remain blockers. Do not include client registration content or protected values.
- **Validation:** heading/term/security scans, Markdown fence/table review, `rtk git diff --check`, and focused diff.
- **Stop condition:** reviewers can predict every prompt, test, lifecycle state, approval, and rollback boundary; no implementation or operational action occurs.

#### Chunk 2: Project Summary Prompt Slice

- **Goal:** Add the smallest complete prompt path: discover and render `project_summary` without any I/O or tool invocation.
- **Files to change:** local-stdio adapter; proposed `ansible/ai_ops_assistant/tests/mcp_stdio/test_diagnostic_prompts.py`.
- **Symbols to add/change:** closed prompt definition type/table, `list_diagnostic_prompts`, `validate_prompt_arguments`, `render_diagnostic_prompt`, and low-level list/get handlers for `project_summary` only.
- **Implementation shape:** define helpers before registration; advertise only the implemented prompt. Return one deterministic bounded message with required headings/refusal language. Other prompts remain absent or fail with a bounded temporary error.
- **Validation:** Python compile, focused project prompt discovery/render/unknown-argument/no-I/O tests, existing lifecycle tests updated only for intentional prompt presence, forbidden import/path scan, focused diff.
- **Stop condition:** one useful prompt is complete and safe; server/metadata prompts, lifecycle wiring, deployment, and live actions remain untouched.

#### Chunk 3: Server and Metadata Prompt Slices

- **Goal:** Complete the three-prompt allowlist with same-identifier server inspection and bounded metadata diagnosis.
- **Files to change:** local-stdio adapter; `test_diagnostic_prompts.py`.
- **Symbols to add/change:** `server_inspection` and `metadata_diagnosis` definitions/renderers, exact identifier validation, exposed-tool checks, deterministic ordering, and unavailable-evidence wording.
- **Implementation shape:** reuse the Chunk 2 validation/rendering seam. Add no automatic tool calls. Keep network/volume/remediation prompts absent.
- **Validation:** Python compile; focused safe/unsafe identifier, exact sequence, same-identifier, required headings, evidence-gap, refusal, canary, byte-bound, and absent-prompt tests; complete local focused suite; focused diff.
- **Stop condition:** all three prompts are discoverable/renderable and non-executable with reviewed text; no lifecycle or operational action occurs.

#### Chunk 4: MCP Safety and Integration Acceptance

- **Goal:** Close Step 6 with one coherent fixture test matrix over tools, resources, prompts, result states, negative capabilities, and lifecycle behavior.
- **Files to change:** proposed `ansible/ai_ops_assistant/tests/mcp_stdio/test_safety_integration.py`; local adapter only if a test exposes a narrowly scoped defect.
- **Symbols to add/change:** fixture helpers for closed discovery, six-status envelopes, no-child assertions, correlation preservation, capability-denial lists, and EOF/cancellation cleanup.
- **Implementation shape:** black-box low-level request-handler fixtures where practical; reuse existing runner envelope fixtures; do not copy runner validation or read live audit files.
- **Validation:** Python compile; new test module; full local `mcp_stdio` unittest discovery; existing focused runner result/redaction/audit tests selected in Chunk 0; generic/remediation/network/import scans; focused diff.
- **Stop condition:** Step 6 fixture/static acceptance passes with no mutation or external dependency; no Option B listener or local deployment is used.

#### Chunk 5: Option B Fixture Workflow and Advisory Refusal

- **Goal:** Prove the conditional Step 7 Option B project-summary and same-identifier server-inspection workflows through authenticated injected fixtures, and prove prompts expose no remediation capability.
- **Files to change:** `ansible/ai_ops_assistant/tests/mcp/test_aiops_assistant_mcp_equivalence.py`; `test_diagnostic_prompts.py` only if additional cross-mode advisory assertions are required.
- **Symbols to add/change:** explicit authenticated project call fixture, ordered server basic/network fixture, no-listener assertion, and shared forbidden-capability/refusal assertions.
- **Implementation shape:** call existing handlers/factories with fake runner and synthetic principal/configuration. Do not construct a transport manager, bind, issue certificates, modify firewall state, or contact a client.
- **Validation:** focused Option B equivalence tests, focused local prompt tests, source scan for prompt/remediation capability drift, focused diff.
- **Stop condition:** conditional fixture workflows pass or a concrete Option B status blocker is recorded; no live network claim is made.

#### Chunk 6: Default-Disabled Local Deployment Entrypoint and Static Lifecycle Acceptance

- **Goal:** Add the separately approved non-executing local role entrypoint and update static acceptance for exact host scope, default-disabled behavior, and external-client-owned lifecycle.
- **Files to change:** proposed `ansible/ai_ops_assistant/playbook_deploy_mcp_stdio.yml`; `ansible/ai_ops_assistant/tests/mcp_stdio/test_deployment_static.sh`.
- **Symbols to add/change:** exact `ai_ops_assistant` play/role inclusion, default-disabled variables, required limit warning/contract, and static prohibitions for package install, client registration, process start, listener, runner, audit, and rollback actions.
- **Implementation shape:** no service, handler, package task, venv creation, process action, or client configuration. Missing lock continues to fail enabled role execution before artifact materialization.
- **Validation:** `bash -n`, static script with approved `PYTHON_BIN`, strict YAML lint, Ansible lint/syntax using a non-executing harness, default/host/path/forbidden-capability scans, focused diff.
- **Stop condition:** repository wiring is statically safe and default-disabled; do not deploy it or fabricate dependency artifacts.

#### Chunk 7: Final Review, Lifecycle Documentation, and Plan Reconciliation

- **Goal:** Review aggregate Steps 5–7 evidence, finalize lifecycle/rollback documentation, and update only checklist items directly supported by accepted static/fixture evidence.
- **Files to change:** Steps 5–7 operations contract if review corrections are required; `docs/ai-ops-revised/implementation-plan/07-mcp-interface.md` for evidence-backed checklist reconciliation.
- **Symbols to add/change:** no executable symbols; final status, known gaps, approval blockers, and exact unchecked operational items.
- **Implementation shape:** documentation/review only. Run complete focused suites and static checks. Do not turn missing lock, deployment, registration, live workflow, audit, or rollback evidence into completion.
- **Validation:** all accepted local/Option B fixture suites, static deployment checks, documentation scans, staged/unstaged `rtk git diff --check`, changed-file list, and complete aggregate diff review.
- **Stop condition:** Steps 5–7 static/fixture evidence and remaining blockers are explicit. Phase 07 is marked complete only if every applicable DoD item has independent reviewed evidence; otherwise stop with unchecked gates.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Implement Phase 07 Steps 5–7 from docs/ai-ops-revised/implementation-plan/07-mcp-interface.md using docs/ai-ops-revised/implementation-plan/ads/07-02-mcp-interface-steps-05-to-07-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm the accepted Steps 1–4 aggregate, exact prompt names/content owners/bounds, MCP SDK prompt signatures, local prompt-bearing mode, absence of standalone network/volume prompts, operations-contract and playbook decisions, Option B source/contract status, fixture-versus-live Step 7 scope, approved validation environment, dependency provenance blocker, and independent operational approvals. Do not install packages, start MCP, open a listener, register a client, invoke a runner, contact OpenStack, inspect audits, deploy, or execute rollback. Stop with evidence and blockers.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Execute Chunk 1 only.
Do not continue to Chunk 2.
Create only the non-activation Steps 5–7 operations contract. Run targeted documentation validation, review staged and unstaged diffs, and stop. Do not implement prompts, install packages, register a client, deploy, start a process/listener, invoke a runner, inspect audits, or perform rollback.
```

For later chunks:

```text
Use the chunked-implementation skill.
Execute only the next explicitly approved chunk from the Phase 07 Steps 5–7 ADS. Do not continue to another chunk. Keep every intermediate state syntax-safe, advertise only complete prompts, preserve the fixed runner as the sole execution/audit boundary, run chunk-specific validation, review the complete focused diff, and stop with a handoff. Treat package acquisition, deployment, client registration, process/listener startup, live runner/OpenStack calls, audit inspection, TLS/firewall work, and rollback as separate authorization scopes.
```

### X. Conclusion and Next Steps

This design completes the planned MCP user-facing workflow without expanding authority. It adds three bounded local-stdio prompts over the already accepted project diagnostics, preserves deterministic safety/refusal language, extends fixture/static acceptance across prompts/tools/resources/lifecycle, and documents client-owned disablement and rollback. It intentionally omits standalone network/volume prompts until sufficient approved evidence exists.

The next action is Chunk 0 discovery and decision confirmation only. Implementation remains blocked on prompt-content approval, SDK prompt-signature verification, Option B status reconciliation, lifecycle/playbook decisions, and the existing hash-locked SDK/offline-wheel provenance gate. No package acquisition, deployment, registration, process startup, live diagnostic, audit inspection, network change, or rollback is authorized by this ADS.
