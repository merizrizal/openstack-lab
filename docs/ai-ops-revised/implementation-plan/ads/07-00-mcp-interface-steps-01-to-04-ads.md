## Architectural Design Specification: Local MCP Tool and Resource Interface — Steps 1–4

**Source:** `docs/ai-ops-revised/implementation-plan/07-mcp-interface.md`, Steps 1 through 4; PRD requirements FR-036 through FR-039, NFR-001 through NFR-010, NFR-016 through NFR-017, and acceptance criteria AC-009 through AC-020.

**Goal:** Define and implement, through separately reviewed chunks, a revised local stdio MCP interface that discovers only approved diagnostics from the accepted revised registry, delegates every tool call to the existing revised runner process, preserves runner result/limit/redaction/audit semantics, and serves only an explicit reviewed static resource set. The interface must create no listener, generic execution primitive, arbitrary file read, credential path, historical-runtime dependency, or second validation/execution path.

---

### I. Overview and Contract

Phase 07 Steps 1–4 add an interface over the accepted revised safety gateway; they do not add diagnostic authority:

```text
selected local AI client
  -> revised MCP process over stdin/stdout only
  -> registry-derived MCP discovery schema
  -> fixed revised runner argv
  -> accepted registry validation and authority selection
  -> accepted timeout/output/redaction/result/audit path
  -> MCP structured tool result
  -> advisory use only
```

Static context follows a separate non-executable path:

```text
MCP resource URI
  -> exact in-code/catalog allowlist lookup
  -> one reviewed bounded static resource
  -> UTF-8 text response
  -> no caller-selected filesystem path
```

The MCP process is not an authorization boundary. The revised runner remains the only component allowed to resolve tools, profiles, implementation targets, child environments, timeouts, output limits, diagnostics, result envelopes, and audit events. MCP may reject a request earlier, but it may never accept a request that the runner would reject or implement a fallback when the runner fails.

#### Step 1 runtime and boundary decision

**Runtime Contract (Proposed, subject to Chunk 0 dependency verification):** use the maintained official Python MCP SDK because the revised runtime, runner, tests, and selected historical path are Python-based. Use the SDK low-level server and stdio transport rather than an HTTP, SSE, streamable-HTTP, socket, or framework-managed network transport.

The historical runtime pins `mcp==1.28.1`; that version is evidence of prior compatibility, not revised approval. Chunk 0 must confirm a currently maintained exact version, Python compatibility, dependency closure, package provenance, hashes/offline installation method, and repository-supported validation environment before the operations contract freezes the revised pin. No unpinned install or runtime package download is allowed.

**Transport Contract (Concrete from the plan):**

```text
transport: local stdio only
listener: none
bind address/port: not applicable and prohibited
startup: selected client starts one exact revised adapter process
shutdown: clean EOF, cancellation, or client termination closes the server
crash: non-zero exit; no daemon restart loop in Steps 1–4
concurrency: bounded; initial proposal is one runner child at a time
```

The adapter must reserve stdout exclusively for MCP protocol frames. Diagnostics, stack traces, registry contents, paths, credentials, and raw exceptions must never be printed to stdout or logs. Stderr logging, if retained at all, is fixed, bounded, sanitized, and contains only lifecycle/error classes.

**Process Boundary Contract (Proposed):**

- revised process/server name, source path, runtime path, package environment, and client registration are distinct from `ansible/ai_ops_runtime/` and `/opt/openstack-ai-ops/`;
- the process runs as the existing revised runtime identity `aiops_assistant`, not as root and not as a new account that would require a second credential/runner delegation mechanism;
- the controlled working directory is `/opt/openstack-ai-ops-assistant`;
- the adapter receives a minimal fixed environment needed for Python/stdio only; it does not consume `OS_*`, SSH, proxy, provider, model, or secret variables;
- no persistent service or listener is introduced in Steps 1–4; the selected client owns the stdio child lifecycle;
- the adapter imports no historical bridge, orchestrator, provider, egress, device-auth, wheelhouse, or remote-operation module;
- startup fully validates its fixed configuration, registry compatibility, tool exposure policy, and resource catalog before serving requests; uncertainty fails startup.

**Runner Delegation Contract (Concrete decision):** revised MCP invokes the accepted revised runner process. It does not execute diagnostics directly and does not duplicate the runner's authority, target, environment, execution, redaction, result, or audit implementation.

```text
python3 <fixed revised runner path> TOOL_NAME [--arg KEY=VALUE ...]
```

Only the tool name and registry-declared public arguments are passed. The adapter cannot supply a registry path, audit path, implementation path, profile, timeout, output limit, environment, working directory, executable, actor, correlation ID, shell setting, or credential override. The runner internally generates the result/audit timestamp and correlation ID and emits exactly one closed JSON result line.

The prior adapter's path-level behavior may inform the revised implementation only under the selective-reuse manifest. Its historical runtime paths, policy schema, registry parser, request-ID injection, audit-path override, client-ID/transport flags, restricted-host assumptions, prompt implementation, and bridge integration are incompatible with the accepted revised runner and must not be copied unchanged. The excluded `aiops_assistant_bridge.py` and orchestrator tree must not be imported, invoked, packaged, or deployed.

**Module/File Contracts (Conceptual; exact paths require Chunk 0 confirmation):**

```text
source role: ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp/
adapter: files/mcp/aiops_assistant_mcp_server.py
static resource catalog: files/mcp/mcp_resource_catalog.json
role defaults/tasks: defaults/main.yml, tasks/main.yml
focused tests: ansible/ai_ops_assistant/tests/mcp/
deployment entrypoint: ansible/ai_ops_assistant/playbook_deploy_mcp.yml
runtime root: /opt/openstack-ai-ops-assistant/mcp
operations contract: docs/ai-ops-revised/runtime/mcp-interface-steps-01-to-04-operations-contract.md
```

These names are proposed from current revised role/playbook conventions. Chunk 0 must confirm them before implementation. Steps 1–4 must not modify the prior MCP files or prior client registration.

#### Step 2 registry-derived MCP tool contract

The initial enabled MCP set is exactly:

| Tool | MCP exposure default | Authority remains owned by | Public arguments |
| --- | --- | --- | --- |
| `project_resource_summary` | enabled after accepted runner prerequisite confirmation | revised runner project-reader mapping | none |
| `server_basic_info` | enabled after accepted runner prerequisite confirmation | revised runner project-reader mapping | required `server_identifier` |
| `server_network_info` | enabled after accepted runner prerequisite confirmation | revised runner project-reader mapping | required `server_identifier` |

The accepted registry currently also contains Phase 06 `neutron_agent_health`, `recent_metadata_errors`, `recent_neutron_errors`, and `recent_nova_errors`. Their Phase 06 acceptance permits Phase 07 planning but does not automatically expose them through MCP. Each remains absent from MCP discovery until the Phase 07 exposure policy confirms its local capability, required profile/projection, accepted evidence, risk description, and explicit enablement. Absence must be represented by non-discovery, not by a discoverable generic placeholder.

**Schema Projection Contract (Conceptual):**

```text
project_registry_tool(tool_descriptor, exposure_policy)
  -> exact MCP tool descriptor or startup failure
```

Inputs are a tool descriptor from the fully validated accepted revised registry and a fixed revised MCP exposure allowlist. Output includes only:

- exact registry tool name;
- bounded public diagnostic description plus fixed read-only, credential-class, and risk-class wording;
- JSON Schema object derived from registry parameters;
- `additionalProperties: false`;
- exact required list;
- exact type, description, pattern, maximum length, enum/allowlist, and default where present.

Implementation target, runtime path, profile path/content, audit path, environment, host destination projection, command argv, and credentials are not exposed. Registry fields unsupported by the schema projector, an unsupported validator/type, unknown exposure-policy tool, duplicate tool/parameter, or projection mismatch fails startup. MCP-side validation is defense in depth; the unchanged runner validates again before target inspection or execution.

**Function Signature Contract (Conceptual):**

```text
load_exposed_tool_schemas(fixed_registry_path, fixed_exposure_policy)
  -> list[MCP tool descriptor]
```

- **Inputs:** fixed deployment-controlled paths/configuration only.
- **Output:** deterministic descriptors in reviewed order.
- **Temporary stub:** return an empty descriptor list only while the server is explicitly marked non-activatable in the contract/stub chunk. It must not return a successful three-tool discovery until registry projection and equivalence tests exist.
- **Safety:** any startup uncertainty raises one bounded adapter configuration error and serves no requests.

**Function Signature Contract (Conceptual):**

```text
invoke_revised_runner(tool_name, arguments, runner_contract)
  -> validated runner result envelope
```

- **Inputs:** one discovered tool name and MCP arguments object.
- **Output:** the accepted runner's complete validated envelope, unchanged except protocol serialization.
- **Temporary stub:** return an MCP error result with a fixed `adapter_unavailable` class and invoke no child.
- **Safety:** success is prohibited until fixed argv, one-line JSON decoding, envelope schema, size bounds, timeout grace, cancellation cleanup, and exit/status equivalence are implemented.

The adapter should load the accepted registry through a repository-confirmed shared read-only loader seam if that can be done without creating import ambiguity or a second execution implementation. If no safe seam exists, Chunk 0 must decide between extracting a shared registry-schema module or implementing a narrowly bounded projector with exhaustive equivalence fixtures. Blind duplication of the complete runner registry validator is not approved.

#### Step 3 result, limit, redaction, and audit contract

The adapter starts the revised runner with argument-vector execution and no shell. It captures one bounded stdout result line and bounded stderr. The outer adapter deadline is the trusted registry timeout plus a small fixed cleanup grace; it does not replace or enlarge the runner's diagnostic timeout. On MCP cancellation or outer deadline, the adapter terminates and reaps only its runner child/process group and reports a fixed sanitized adapter failure. It does not retry the diagnostic.

The accepted runner result envelope remains authoritative and currently contains exactly:

- `schema_version`;
- `tool`;
- `status`;
- `arguments`;
- `exit_code`;
- `data`;
- `stdout`;
- `stderr`;
- `error`;
- `duration_ms`;
- `truncated`;
- `timestamp`;
- `correlation_id`.

MCP returns the envelope as structured content and, where required by the selected SDK/client compatibility contract, one deterministic compact JSON text content item. `isError` is true for `error`, `denied`, `validation_error`, `timeout`, and `unavailable`; it is false only for `ok`. Truncation remains the runner's boolean metadata, not a new status. The adapter does not synthesize missing fields, turn `unavailable` into success, expose raw stderr, or reinterpret diagnostic findings as execution success/failure.

**Result Equivalence Contract (Concrete):** for the same tool and arguments against the same accepted registry/runtime state, local runner and MCP calls must have equivalent status class, public argument handling, data/error shape, exit semantics, truncation behavior, timeout enforcement, redaction, and one corresponding runner audit event. Timestamp, duration, and correlation ID values naturally differ between separate calls but must each satisfy the same schema and result/audit pairing rules.

The runner remains the audit writer. MCP must not write raw result data or a duplicate tool-execution audit event. The accepted runner currently uses fixed actor classification `local_cli` and rejects caller-provided actor/client/correlation data. Steps 1–4 therefore must not fabricate or inject a client identity. Chunk 0/operations-contract review must choose one of these fail-closed outcomes:

1. preserve the accepted fixed actor unchanged and document that authenticated client identity is unavailable over the initial stdio boundary; or
2. separately revise the runner contract to support one closed non-authorizing invocation classification such as `local_mcp_stdio`, with regression proof that callers cannot influence authorization, correlation IDs, paths, limits, or execution.

No free-form client name from MCP initialization may enter audit. If this decision is unresolved, implementation stops before tool activation.

Protocol/lifecycle logs contain no tool payload, arguments, result data, raw error, environment, credential/profile text, audit content, topology, or command path. Sanitization uses the same secret-key/assignment/Bearer/PEM rules as the runner where text can be retained. A redaction failure emits no partial text.

#### Step 4 curated read-only resource contract

Steps 1–4 expose no arbitrary filesystem URI, file template, directory listing, glob, user-supplied path, URL fetch, or dynamic command output. Resources are a separately reviewed static allowlist. A proposed consolidated catalog may contain multiple closed resource entries in one deployment artifact to keep loading atomic and auditable.

**Resource Catalog Contract (Conceptual):**

```text
{
  "schema_version": 1,
  "catalog_name": "ai-ops-assistant-mcp-resources-steps-01-04",
  "resources": [
    {
      "uri": "aiops-assistant://...",
      "name": "...",
      "description": "...",
      "mime_type": "text/markdown",
      "content": "reviewed bounded UTF-8 Markdown"
    }
  ]
}
```

The root and every entry are closed objects with duplicate-key rejection. URIs, names, and order are unique. Content is UTF-8, bounded by a contract-frozen per-resource and total-catalog byte limit, and immutable for one deployed revision. No entry contains a source/runtime filesystem path to read dynamically.

The reviewed set should cover:

| Resource intent | Required content | Prohibited content |
| --- | --- | --- |
| Lab architecture and placement summary | sanitized roles, service relationships, metadata flow, diagnostic interpretation limits | addresses, inventory values, hidden topology, credentials, raw command output |
| AI-OPS safety policy | diagnostic-only boundary, denied generic/remediation capabilities, manual next actions | executable mutation instructions or bypass guidance |
| Credential-profile policy | conceptual project/operator/observer separation and unavailable behavior | profile contents, paths readable by clients, tokens, IDs, private keys |
| Tool-registry policy | public diagnostic names, schema/authority concepts, extension review | implementation targets, command lines, environment, unrestricted registration |
| Audit policy | minimum-disclosure event purpose, correlation semantics, operator-owned review | audit file reads, raw events, protected evidence references/content |
| Reviewed troubleshooting runbook | metadata and other accepted evidence ordering appropriate to enabled tools | arbitrary commands/files, unsupported tools, secrets, claims of automated remediation |

**Function Signature Contract (Conceptual):**

```text
list_curated_resources(validated_catalog) -> list[MCP resource descriptor]
read_curated_resource(uri, validated_catalog) -> bounded static UTF-8 content
```

- **Inputs:** the complete startup-validated catalog and exact requested URI.
- **Outputs:** deterministic metadata or the corresponding embedded static content.
- **Temporary stub:** expose no resources until the catalog passes closed-schema, bound, secret-canary, and allowlist tests.
- **Failure:** unknown URI returns a generic not-found/protocol error without attempting filesystem or network access.

Prompts are Step 5 and are not implemented or registered by this ADS. The historical prompt definitions must not be copied into Steps 1–4.

### II. Observed Evidence and Assumptions

#### Observed evidence

- The current branch is `ai-ops-assistant-phase07`; commit `aee9bba` merges the Phase 06 branch, and the working tree was clean before this ADS was created.
- `docs/ai-ops-revised/implementation-plan/07-mcp-interface.md` requires local stdio, registry-derived tools, accepted runner delegation, result/audit equivalence, fixed resources, and no prior-runtime/network/generic capability.
- `docs/ai-ops-revised/prd.md` FR-036 through FR-039 and AC-018 through AC-020 require MCP to mirror approved diagnostics, expose reviewed resources, omit generic execution, and preserve the documented safety model.
- `docs/ai-ops-revised/implementation-plan/00-implementation-overview.md` fixes MCP after accepted runner and Phase 06 work and forbids an alternate execution path or historical orchestrator dependency.
- `docs/ai-ops-revised/runtime/selective-reuse-manifest.md` selects only the exact historical `aiops_mcp_server.py` path for Phase 07 review, with the accepted revised runner/registry as its replacement dependency. Historical resources, policy, and lifecycle remain deferred candidates; the bridge and orchestrator are excluded.
- `docs/ai-ops-revised/runtime/source-capability-catalog.md` records that the historical adapter uses SDK stdio and historical paths; resources/policy/lifecycle require separate Phase 07 review.
- `ansible/ai_ops_runtime/roles/assistant_runtime/files/mcp/aiops_mcp_server.py` demonstrates useful path-level patterns for SDK low-level stdio, schema projection, bounded subprocess handling, fixed resources, and cancellation. It is incompatible in material ways: historical roots, a different registry schema, caller-supplied runner overrides, request/client/transport injection, historical result fields, and prompt/Phase 06 assumptions.
- `ansible/ai_ops_runtime/roles/assistant_runtime/files/mcp/aiops_assistant_bridge.py` imports excluded orchestrator contracts and opens a Unix listener; it is explicitly outside the revised product path.
- Historical defaults pin `mcp==1.28.1`, but no revised MCP dependency, package source, hashes, environment, or deployment role currently exists.
- `ansible/ai_ops_assistant/roles/ai_ops_assistant_foundation/defaults/main.yml` creates `/opt/openstack-ai-ops-assistant/mcp` and installs Python/venv support, but it deploys no MCP package, process, listener, client registration, or executable.
- `ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/aiops_tool_runner.py` is the accepted seven-tool authority and execution boundary. It validates a fixed adjacent registry, accepts only `TOOL_NAME [--arg KEY=VALUE ...]`, builds fixed argv/minimal authority environments, enforces process/output bounds, redacts results, writes one audit event, and emits one deterministic closed envelope.
- The runner does not accept registry, audit, path, profile, environment, timeout, output, actor, client, transport, or correlation-ID overrides. It generates timestamp/correlation internally and fixes audit actor to `local_cli`.
- `tool_registry.json` contains the three initial project tools plus accepted Phase 06 operator/host-observer tools, with exact names, descriptions, argument constraints, authority classes, risk classes, timeouts, and output limits.
- Focused runner tests exist under `ansible/ai_ops_assistant/tests/tool_runner/` for registry/request validation, process bounds, profile isolation, result envelopes, redaction, audit events/persistence, host-observer execution, and integration gates. No revised MCP test directory exists.
- `docs/ai-ops-revised/runtime/ai-ops-assistant-playbook-execution-order.md` currently ends runner/diagnostic deployment and validation without a revised MCP deployment step; any future entrypoint must remain ordered after accepted runner prerequisites.

#### Assumptions

- **Proposed:** the official Python MCP SDK remains the best fit, but its exact revised version and dependency acquisition method are blocked on Chunk 0 supply-chain and host compatibility confirmation.
- **Proposed:** subprocess delegation is safer and less invasive than extracting the monolithic accepted runner into a shared library during Phase 07. Registry schema projection may use a small shared read-only seam only if Chunk 0 proves it does not create import ambiguity or execution bypass.
- **Proposed:** the initial MCP exposure allowlist contains only the three project-reader tools. Phase 06 tools require explicit Phase 07 exposure decisions even though Phase 06 itself is accepted.
- **Proposed:** one concurrent runner child is sufficient for the first local client and avoids unreviewed parallel audit/resource pressure. The exact bound must be frozen in the operations contract.
- **Proposed:** resource content is stored in one closed static catalog rather than allowing path-based reads. If maintainers choose separate Markdown files, every filename/path must be fixed in code/config and receive equivalent regular-file, non-symlink, ownership, containment, size, and secret scans.
- **Assumed:** the first supported client can launch a stdio child under the revised runtime identity without embedding OpenStack/provider credentials. The exact client and registration format remain owner decisions.
- **Assumed:** Steps 1–4 do not need a long-running service. Client-owned stdio lifecycle is adequate and independently disableable by removing client registration or the revised adapter artifact.

#### Open confirmations for Chunk 0

1. Exact first supported AI client, owner, launch user, registration location, environment behavior, shutdown/cancellation behavior, and proof that no TCP listener is needed.
2. Exact official MCP SDK version, Python range, transitive dependency lock/hashes, package source or offline artifact method, license/provenance, and validation environment.
3. Whether a new dedicated MCP virtual environment is required and its exact root/ownership/mode/upgrade/removal contract.
4. Exact revised role, adapter, resource catalog, test, runtime, client-registration, and operations-contract paths with no prior collision.
5. Registry projection seam: safe import of a read-only accepted loader, extraction of a shared registry-schema module, or a bounded projector plus exhaustive equivalence fixtures.
6. Initial exposure allowlist and explicit per-tool decisions for all four Phase 06 tools.
7. Audit actor/transport decision: preserve accepted `local_cli` classification or separately approve one fixed non-authorizing `local_mcp_stdio` runner contract.
8. Outer envelope byte cap, timeout grace, concurrency limit, protocol log sink/retention, and sanitized adapter error classes.
9. Resource URI namespace, exact resource set/content owners, byte limits, content review, secret/topology scan patterns, and update approval process.
10. Exact deployment/disablement ordering and whether Steps 1–4 install artifacts only or may register the selected client; no registration is assumed by this ADS.
11. Protected validation/evidence owner and separate approvals for package acquisition, deployment, client registration, runner execution, audit inspection, and rollback.

### III. Required Technical Dependencies and Imports

- **Proposed external dependency:** official Python `mcp` SDK, exact version/lock/hashes pending Chunk 0. Use only stdio and required low-level types/server APIs; do not import HTTP/SSE/auth/provider modules.
- **Python standard library:** `asyncio`, `json`, `pathlib`, and narrowly required typing/dataclass/import facilities. `subprocess` behavior must use `asyncio.create_subprocess_exec` or equivalent argument-vector execution, never a shell.
- **Accepted revised runner and registry:** fixed source/runtime paths and contracts already owned by `ai_ops_assistant_tool_runner`; no copied registry or alternate target/profile map.
- **Proposed MCP role:** repository-local Ansible role, default disabled until dependencies and static tests pass. Deployment uses fixed copy/template/package operations with strict owner/mode and non-symlink checks.
- **Proposed resource catalog:** closed JSON with embedded reviewed Markdown, duplicate-key rejection, UTF-8 and byte limits, and no dynamic paths.
- **Focused tests:** Python standard-library `unittest` following existing runner test conventions; SDK protocol/client harness only if the pinned dependency provides a stable supported test seam.
- **Existing validation environment:** `/home/meriz/Documents/PyEnv/myEnv` is the approved repository Python environment from the Phase 06 handoff; Chunk 0 must verify it contains or can safely validate the selected MCP dependency before MCP tests run.
- **Not permitted:** historical orchestrator/bridge/provider/egress/device-auth/wheelhouse packages; generic executor libraries; HTTP server/listener dependencies; SSH/database/message-bus clients; provider/model authentication packages; arbitrary file-serving frameworks.

### IV. Step-by-Step Procedure / Execution Flow

1. Confirm current branch/revision, clean state, merged Phase 06 acceptance, exact selected historical path, excluded path families, and unchanged prior runtime without reading protected data.
2. Resolve all Chunk 0 decisions, especially client/stdio lifecycle, SDK supply chain, package environment, registry projection seam, initial/optional tool exposure, audit classification, resource owners, and authorization scopes.
3. Freeze a non-activation Steps 1–4 operations contract and exact path-level dependency closure. Amend the selective-reuse manifest only for exact resource/policy/lifecycle paths explicitly approved for review; do not select directories or the historical bridge.
4. Add a syntax-safe revised MCP adapter stub that can create only a stdio server, exposes no tools/resources/prompts, starts no runner, opens no listener, and exits non-zero on unresolved configuration/dependency state.
5. Add lifecycle/cancellation/static tests proving stdout protocol discipline, no network server import/call, bounded concurrency configuration, no historical path/import, and clean shutdown without child processes.
6. Implement one registry-derived low-risk vertical slice for `project_resource_summary`: load the accepted registry through the approved seam, project an exact no-argument schema, and delegate one fixed runner subprocess call.
7. Validate the runner envelope as one bounded UTF-8 JSON line with the accepted closed field set/status mapping. Return it as MCP structured content without re-redacting, dropping safety metadata, or writing a second audit event.
8. Extend projection and calls to `server_basic_info` and `server_network_info`, deriving the exact required `server_identifier` schema. Prove undeclared, missing, wrong-type, unsafe-pattern, and oversized arguments are rejected by MCP defense in depth and again by runner equivalence fixtures.
9. Encode explicit exposure decisions for each Phase 06 tool. A disabled tool is absent. An enabled optional tool must derive its exact registry schema and retain its runner-owned operator/host-observer authority; MCP cannot make a missing profile/projection available.
10. Implement cancellation, outer timeout grace, stdout/stderr/envelope byte bounds, child reap behavior, fixed adapter error classes, and protocol-log sanitization. Never retry a tool call or convert adapter uncertainty into a runner success.
11. Resolve and test the audit actor decision. Preserve one runner-generated timestamp/correlation ID and one runner-written audit event per request. Do not accept free-form client identity or expose audit files through MCP.
12. Add the closed static resource catalog with owner-reviewed architecture, safety, credential, registry, audit, and troubleshooting context. Validate all content before server startup.
13. Implement exact resource listing/read by URI. Unknown URIs fail without filesystem/network access. Do not register prompts in this ADS.
14. Add default-disabled deployment metadata and an exact revised adapter/package/resource installation path only after local tests pass. Preserve the current runner/diagnostic deployment and all prior-runtime artifacts.
15. Run static and fixture integration checks proving exact tool/resource discovery, schema/result/audit equivalence, negative capabilities, no listener, no arbitrary read, clean cancellation, and secret-canary absence.
16. Stop at Steps 1–4 static/local acceptance. Client registration, deployed runner calls, audit inspection, and rollback rehearsal require separately approved later chunks; Steps 5–7 remain out of scope.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| --- | --- | --- | --- |
| Prerequisite | Phase 06 acceptance/revision or runner deployment evidence is missing or changed | Stop before adapter activation | prerequisite gate unresolved |
| Reuse boundary | Selected historical path/revision differs or dependency closure imports excluded code | Reject adaptation; do not copy/import | reuse isolation blocker |
| SDK selection | Package is unmaintained, unpinned, incompatible, unverifiable, or requires uncontrolled network acquisition | Install nothing; keep adapter absent/disabled | dependency approval blocker |
| Client boundary | Selected client requires TCP/HTTP, embeds credentials, or cannot control stdio lifecycle safely | Reject client for initial support | client boundary blocker |
| Startup | Fixed registry/policy/catalog/package/runtime metadata is missing, unsafe, or malformed | Serve no requests and exit non-zero with bounded class | `adapter_configuration_error` (proposed) |
| Registry seam | Adapter cannot use or prove equivalence with accepted registry validation | Expose no tools; do not duplicate authority heuristically | schema projection blocker |
| Exposure policy | Policy names unknown, duplicate, unaccepted, or optional-disabled tool | Fail startup rather than widening/narrowing silently | `tool_exposure_error` (proposed) |
| Schema projection | Unsupported type/validator/field or MCP schema differs from registry | Fail startup and expose nothing | `schema_equivalence_error` (proposed) |
| Tool request | Tool is absent from discovered allowlist | Do not invoke runner | generic MCP unknown/unavailable tool error |
| MCP argument validation | Missing, unknown, wrong-type, unsafe, oversized, or out-of-allowlist value | Reject before child creation; retain runner as authoritative on any forwarded request | protocol validation error |
| Runner spawn | Fixed revised runner cannot start | Start no alternate target; return bounded MCP error | `runner_unavailable` (proposed) |
| Runner timeout | Runner exceeds trusted timeout plus cleanup grace | Terminate/reap its process group; do not retry | `runner_protocol_error`/timeout adapter failure |
| Cancellation | Client cancels/disconnects while child runs | Terminate and reap child, then propagate cancellation safely | no orphan; request incomplete |
| Runner stderr | Any unexpected stderr or oversized stderr is produced | Discard raw text, fail adapter call | `runner_protocol_error` |
| Runner stdout | Empty, multiple lines, invalid UTF-8/JSON, oversized, partial, or extra fields | Reject all content; expose no raw bytes | `runner_protocol_error` |
| Envelope | Tool/status/exit/schema/truncation/correlation fields violate accepted contract | Return fixed adapter error; do not reinterpret | `result_equivalence_error` (proposed) |
| Runner result | Status is `denied`, `validation_error`, `timeout`, `unavailable`, or `error` | Preserve envelope and mark MCP result as error | same runner terminal state |
| Audit | Runner reports audit integrity/write/rotation failure | Preserve runner error; never report diagnostic success or write substitute audit | accepted runner audit error |
| Client identity | Free-form client name/metadata is offered | Ignore/reject for audit; use only approved fixed classification decision | no unauthenticated identity claim |
| Protocol logging | Raw argument/result/exception/secret reaches log path | Stop emission, return generic error, treat disclosure as incident | `adapter_redaction_error` (proposed) |
| Resource catalog | Duplicate/unknown fields, unsafe URI, invalid UTF-8, oversized content, or unexpected entry | Fail startup; expose no partial catalog | `resource_catalog_error` (proposed) |
| Resource review | Secret/topology canary or prohibited operational detail is found | Reject catalog revision; do not deploy | content review blocker |
| Resource request | Unknown URI or attempted path/URL input | No filesystem/network operation; return not found | generic resource error |
| Network isolation | Socket/listener creation or network transport appears in source/dependencies/runtime | Fail tests and deployment review; disable adapter | critical boundary failure |
| Prior collision | Revised path/name/client registration touches prior MCP/runtime | Stop and preserve both states; no automated rewrite | coexistence failure |
| Shutdown | Child remains after EOF/cancel/crash | Fail lifecycle acceptance and disable client registration | orphan-process blocker |
| Authorization | Package acquisition, deployment, registration, runner call, audit read, or rollback lacks approval | Perform no such action | authorization blocker |

### VI. Security, Integrity, Idempotency, and Cleanup

- **Security:** stdio is the only transport. No bind address, port, HTTP route, SSE endpoint, Unix listener/bridge, remote authentication, provider protocol, or egress path is present. A future remote MCP design requires a separate threat model and approval.
- **Single execution boundary:** every accepted tool call invokes only the fixed revised runner CLI. MCP never imports diagnostic implementations, constructs target argv, chooses credentials, reads projections, or writes tool audits.
- **Deny by default:** tools are the intersection of the accepted registry, explicit revised MCP exposure policy, and optional-capability enablement. Resources are exact URI entries in one closed static catalog. Everything else is absent or rejected.
- **Credential isolation:** client configuration and MCP environment contain no OpenStack, SSH, provider, model, or audit credentials. MCP accepts no path/profile/environment override. The runner constructs the authority-specific minimal child environment.
- **Integrity:** exact source/runtime roots, root-controlled deployed code/config where repository ownership permits, strict modes, regular-file/non-symlink checks, duplicate-key rejection, deterministic schema projection, one-line envelope validation, bounded content, and no prior fallback are mandatory.
- **Redaction/minimum disclosure:** runner result/audit redaction remains authoritative. Adapter errors/logs are generic and bounded. Tool descriptions/resources omit implementation paths, addresses, profile content, protected evidence, raw audit data, credentials, and private topology.
- **Idempotency:** repeated local discovery/resource reads do not change state. Each tool request executes at most once and is never automatically retried. Reapplying deployment produces no changes after the accepted first apply. Repeated client disablement is safe.
- **Cleanup:** cancellation/timeout reaps only the request's runner process group. Failed package/artifact deployment must not leave an activatable partial adapter. Removal targets only exact revised MCP artifacts after process absence and expected-entry checks; it preserves runner, diagnostics, credentials, audit, evidence, and prior runtime.
- **Rollback:** disable/remove selected client registration first, verify no revised adapter/runner child remains, then remove only reviewed revised MCP artifacts and optionally its dedicated SDK environment after reverse-dependency checks. Manual/local runner workflows remain available unless the underlying safety issue requires their separate rollback.
- **Evidence:** Git may contain design/contracts, static resources with synthetic/sanitized context, dependency lock metadata, and fixtures. It must not contain credentials, keys, tokens, client secrets, profile content, addresses, protected inventory, raw runner output, audit lines, or live evidence.

### VII. Validation Strategy

Validation is chunk-aware and local/fixture-driven. Commands are implementation guidance and do not authorize package downloads, deployment, client registration, runner execution against live diagnostics, audit inspection, or network access.

#### Documentation and contract validation

- Verify required ADS/operations-contract headings, tables, stdio-only boundary, runner delegation, resources, failure modes, rollback, and chunk design with targeted `rtk grep`.
- Run `rtk git diff --check` and focused `rtk git diff -- <changed-files>`.
- Scan changed documentation for protected values, addresses, credentials, private keys, tokens, raw evidence/audits, historical runtime paths presented as revised paths, and unsupported completion claims.

#### Python and dependency validation

- Use `/home/meriz/Documents/PyEnv/myEnv` only after confirming the selected SDK/version is present or installation is separately authorized.
- Run `rtk /home/meriz/Documents/PyEnv/myEnv/bin/python -m py_compile <changed-python-files>`.
- Run focused `unittest` modules under `ansible/ai_ops_assistant/tests/mcp/`; do not start with the broad repository suite.
- Verify imports resolve only to standard library, the approved MCP SDK, and repository-confirmed revised read-only seams.
- Inspect the exact dependency lock/pin/hash diff and reject unpinned or unexpected network/server/provider dependencies.

#### Ansible/JSON validation

- Parse changed JSON with the approved Python environment and the implementation's duplicate-key-aware loader tests.
- Run targeted `yamllint`, `ansible-lint`, and `ansible-playbook --syntax-check` only after confirming repository tooling/environment.
- Statically assert default-disabled activation, exact revised roots, strict owner/modes, non-symlink checks, no `hosts: all`, no prior paths, no service/listener, and no embedded client/credential data.
- Run check mode or deployment only in a separately authorized chunk.

#### Required targeted behavior tests

1. Server construction selects stdio only and source/static scans contain no socket, HTTP, SSE, streamable-HTTP, listener, bridge, provider, or orchestrator activation.
2. Startup fails closed for malformed/missing registry, exposure policy, resource catalog, SDK/runtime metadata, or unsupported schema field/validator.
3. Discovery is exactly the approved enabled registry intersection; initially it is the three project tools unless optional Phase 06 exposure is separately approved.
4. Generic shell, SSH, sudo, OpenStack passthrough, file, database, package, service-control, provider, network, and remediation tools are absent.
5. MCP JSON Schemas match names, descriptions, required/optional fields, types, patterns, maximum lengths, enums/allowlists, defaults, and `additionalProperties: false` from registry fixtures.
6. `project_resource_summary`, `server_basic_info`, and `server_network_info` calls create only the fixed runner argv with no shell and no registry/audit/profile/path/timeout/output/environment/correlation overrides.
7. Invalid requests create no child. Forwarded valid and invalid fixture calls preserve runner denial/validation behavior.
8. One-line result envelopes preserve all accepted fields/statuses, error mapping, truncation, timestamps, correlation IDs, and deterministic structured/text compatibility.
9. Outer timeout/cancellation terminates and reaps child processes; repeated calls do not leak children or run concurrently beyond the approved limit.
10. Adapter stdout contains protocol only; stderr/logs never contain request arguments, result data, raw exceptions, paths, credentials, secret canaries, or audit content.
11. Exactly one runner audit event corresponds to each invoked request; adapter failures before invocation write no fake tool audit; audit failures cannot become success.
12. Resource listing exactly matches the reviewed catalog; reads return only embedded bounded UTF-8 content; unknown URIs never cause file/network reads.
13. Resource content scans reject password/token/secret/private-key/Bearer/authorization canaries, addresses, protected references/content, raw commands/output, and arbitrary-path instructions.
14. EOF, cancellation, crash, and explicit disablement leave no MCP or runner child; runner/manual workflows and prior runtime remain unchanged.
15. Existing focused runner tests continue to pass without MCP-specific weakening or call-site changes unless a separately accepted audit-classification revision explicitly requires them.

#### Separately authorized integration validation

After Steps 1–4 local implementation is accepted, later chunks may validate the selected client against fixture/fake runner first. Any deployed call must begin with `project_resource_summary`, then one server tool, and must use protected outcome-only evidence. Audit inspection, optional Phase 06 tool exposure, package installation, client registration, and rollback rehearsal are distinct approval scopes. No test may open a listener or mutate OpenStack/host state.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass.

#### Chunk 0: Discovery and Integration Confirmation

- **Goal:** Resolve the eleven open confirmations, verify accepted runner/Phase 06 prerequisites and path-level reuse closure, and freeze exact proposed file paths and per-chunk commands without edits.
- **Files to read:** Phase 07 plan; this ADS; PRD MCP sections; overview; runner Steps 1–7 contracts; Phase 06 contracts/acceptance status; selective-reuse manifest/catalog; current runner/registry/defaults/tasks/tests; selected historical adapter only; candidate resource/policy/lifecycle files only if manifest policy permits review; dependency metadata and selected client documentation available in-repository.
- **Commands:** bounded `rtk git status`, `rtk git log`, `rtk find`, `rtk grep`, and targeted reads. Do not inspect protected inventories, credentials, audits, evidence, or client secrets and do not execute MCP/runner/network/package commands.
- **Evidence to confirm:** exact SDK pin/closure, client/stdio lifecycle, role/runtime/test paths, registry projection seam, initial and optional tool exposure, audit classification, resource set/owners/bounds, deployment/rollback order, validation environment, and separate authorization gates.
- **Stop condition:** no edits and no operational actions. Produce a decision/blocker report. Any unresolved SDK, registry-equivalence, client/no-listener, audit, or resource-owner decision blocks Chunk 1 acceptance.

#### Chunk 1: Steps 1–4 Non-Activation Operations Contract

- **Goal:** Freeze runtime identity, stdio lifecycle, dependency, runner delegation, schema projection, exposure, result/audit, resource, deployment, and rollback contracts before executable work.
- **Files to change:** proposed `docs/ai-ops-revised/runtime/mcp-interface-steps-01-to-04-operations-contract.md`; `docs/ai-ops-revised/runtime/selective-reuse-manifest.md` only if exact deferred resource/policy/lifecycle paths are explicitly selected.
- **Symbols to add/change:** exact SDK/version/lock method, process/path/ownership/mode contract, closed exposure policy, schema mapping table, envelope/error mapping, audit classification decision, resource schema/allowlist/bounds, authorization matrix, and rollback sequence.
- **Implementation shape:** Markdown only; manifest selects exact files, never directories/wildcards/bridge/orchestrator. Unresolved values remain blockers rather than permissive defaults.
- **Validation:** targeted heading/security/path scans, manifest consistency checks, Markdown table/fence review, `rtk git diff --check`, and focused staged/unstaged diff.
- **Stop condition:** reviewers can predict every allowed process, input, output, dependency, tool/resource, failure, audit, and removal action; nothing is installed, started, registered, or executed.

#### Chunk 2: Stdio Server Skeleton and Fail-Closed Lifecycle

- **Goal:** Add one syntax-safe revised MCP server that uses only stdio, exposes nothing, invokes no runner, and fails clearly when activation prerequisites are absent.
- **Files to change:** proposed `ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp/files/mcp/aiops_assistant_mcp_server.py`; proposed `ansible/ai_ops_assistant/tests/mcp/test_stdio_lifecycle.py`.
- **Symbols to add/change:** proposed fixed server name/version, configuration dataclass, `create_server`, `run_server`, `main`, bounded lifecycle error, and cancellation/EOF cleanup seam.
- **Implementation shape:** import only approved SDK stdio/low-level APIs; no tools/resources/prompts, subprocess, service, registration, socket, HTTP/SSE, historical path, or successful activation claim. If the SDK/config is unavailable, exit non-zero with fixed sanitized stderr and no stdout protocol corruption.
- **Validation:** Python compile, focused lifecycle tests, import/network/historical-path scans, stdout/stderr checks, process-leak test, `rtk git diff --check`, focused diff.
- **Stop condition:** skeleton is syntax/test safe and cannot expose capability or create a listener; no package install or process deployment occurred.

#### Chunk 3: First Registry-to-Runner Tool Slice

- **Goal:** Connect one meaningful path—`project_resource_summary` discovery and call—from the accepted registry through the fixed runner subprocess and back as a validated MCP result.
- **Files to change:** MCP server source; proposed `ansible/ai_ops_assistant/tests/mcp/test_project_tool_slice.py`.
- **Symbols to add/change:** `load_exposed_tool_schemas` for one approved no-argument tool, `invoke_revised_runner`, bounded one-line envelope decoder, `map_runner_envelope_to_mcp`, and temporary explicit rejection for every other tool.
- **Implementation shape:** use the Chunk 0-approved registry seam; fixed runner path and argv; no shell/overrides; one concurrency slot; fixture/fake runner only. Define callees before wiring handlers. Adapter errors are fixed and cannot be mistaken for runner success.
- **Validation:** Python compile, focused discovery/call/invalid-tool/envelope tests, exact argv and no-child-on-rejection assertions, forbidden override/network/prior-import scans, focused diff.
- **Stop condition:** one low-risk fixture path works with exact schema/result semantics; all other tools/resources remain absent; no live runner or deployment.

#### Chunk 4: Three-Tool Schema Equivalence and Optional Exposure Gate

- **Goal:** Extend discovery/calls to the three initial project tools and encode fail-closed non-discovery for each optional Phase 06 tool unless explicitly approved.
- **Files to change:** MCP server source; proposed `ansible/ai_ops_assistant/tests/mcp/test_tool_schema_equivalence.py`.
- **Symbols to add/change:** complete registry parameter-to-JSON-Schema projector, exact initial exposure allowlist, optional-tool exposure decisions, deterministic ordering, startup divergence errors, and server basic/network handlers through the same invocation function.
- **Implementation shape:** derive types/patterns/max lengths/enums/defaults/required flags; `additionalProperties: false`; no duplicated execution/profile/target logic. Unsupported registry constructs fail startup.
- **Validation:** Python compile; exact discovery/schema fixtures; unknown/duplicate/unsupported policy cases; invalid argument/no-child tests; generic/remediation capability absence scan; existing targeted runner request/profile tests; focused diff.
- **Stop condition:** discovery equals the reviewed enabled registry subset and all calls still use one runner path; resources remain absent; no deployment.

#### Chunk 5: Result, Bounds, Cancellation, Redaction, and Audit Equivalence

- **Goal:** Complete Step 3 semantics around every runner terminal state, envelope bounds, timeout grace, cancellation/reaping, sanitized protocol errors/logs, and one-audit-event behavior.
- **Files to change:** MCP server source; proposed `ansible/ai_ops_assistant/tests/mcp/test_result_audit_equivalence.py`.
- **Symbols to add/change:** closed envelope validator, status/`isError` mapping, fixed byte/deadline/concurrency bounds, child termination helper, adapter error classes, protocol-log sanitizer, and approved fixed audit classification integration if separately authorized.
- **Implementation shape:** preserve runner envelopes; do not retry, re-execute, re-redact into a weaker shape, write duplicate audits, or accept caller identity/correlation. Malformed/partial/oversized/raw failures yield generic adapter error only.
- **Validation:** Python compile; six-status/truncation/equivalence fixtures; malformed UTF-8/JSON/fields/status/exit tests; timeout/cancel/orphan tests; stdout/stderr secret-canary tests; focused runner result/redaction/audit regressions; focused diff.
- **Stop condition:** local fixture calls have equivalent safety/result/audit behavior and no orphan/log disclosure; no live audit read or diagnostic execution.

#### Chunk 6: Curated Static Resource Slice

- **Goal:** Add a complete reviewed static resource catalog and exact list/read behavior without any arbitrary path, filesystem template, URL, or dynamic diagnostic access.
- **Files to change:** MCP server source; proposed `ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp/files/mcp/mcp_resource_catalog.json`; proposed `ansible/ai_ops_assistant/tests/mcp/test_curated_resources.py`. Three files are justified because this vertical slice requires protocol handling, separately reviewable content, and behavior/security proof.
- **Symbols to add/change:** closed catalog loader, exact resource descriptors, `list_curated_resources`, `read_curated_resource`, byte/UTF-8/duplicate/URI checks, and owner-reviewed architecture/safety/credential/registry/audit/troubleshooting entries.
- **Implementation shape:** content embedded in the fixed catalog; unknown URI is a pure lookup failure. Expose no prompt and no generic file-reading function. Temporary resource exposure remains empty if catalog validation fails.
- **Validation:** Python compile; duplicate-key/unknown-field/bounds/URI/unknown-resource tests; exact resource discovery/read tests; secret/private-key/token/address/raw-command/topology canary scans; no file/network-call assertion; focused diff.
- **Stop condition:** useful static context is locally discoverable only from the reviewed catalog and all unsafe/dynamic reads fail; no deployment or client registration.

#### Chunk 7: Default-Disabled Deployment Wiring and Static Acceptance

- **Goal:** Package the accepted Steps 1–4 adapter/dependency/resource artifacts in the revised namespace with exact metadata, default-disabled activation, no listener/service, and independent removal controls.
- **Files to change:** proposed MCP role `defaults/main.yml` and `tasks/main.yml`; split a deployment playbook or static test into a separately approved micro-chunk if adding it would exceed the two-file slice.
- **Symbols to add/change:** exact revised roots, user/group/modes, package environment/lock inputs, file allowlist, enable gate, expected-entry checks, process-absence gate for removal, and preservation assertions for runner/diagnostics/credentials/audit/prior runtime.
- **Implementation shape:** install artifacts only when explicitly enabled and prerequisites are fixed. Do not register a client, create a service, start MCP, execute runner, read audits, or remove shared dependencies. Unsafe/missing metadata fails before partial activation.
- **Validation:** targeted YAML/Ansible lint/syntax after environment confirmation; default-false/path/mode/non-symlink/no-listener/no-prior scan; idempotence/check-mode fixture if available; Python/MCP focused suite; `rtk git diff --check`; complete focused diff.
- **Stop condition:** source deployment wiring is statically accepted and independently disableable, or a concrete blocker is recorded. Stop before client registration, package acquisition not already approved, host deployment, runner execution, audit inspection, Steps 5–7, or plan completion claims.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Implement Phase 07 Steps 1–4 from docs/ai-ops-revised/implementation-plan/07-mcp-interface.md using docs/ai-ops-revised/implementation-plan/ads/07-00-mcp-interface-steps-01-to-04-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm the current repository/accepted runner state, exact selected historical path and exclusions, first local stdio client, official MCP SDK pin/dependency closure, package environment, revised paths, registry projection seam, initial and optional tool exposure, audit classification, resource owners/content/bounds, deployment and rollback order, validation environment, and separate authorization gates. Do not inspect protected values, install packages, open network connections/listeners, start MCP, execute diagnostics, read audits, register a client, deploy, or alter prior runtime. Stop with evidence and blockers.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Execute Chunk 1 only.
Do not continue to Chunk 2.
Create only the non-activation Phase 07 Steps 1–4 operations contract and any explicitly approved exact-path selective-reuse manifest amendment. Run targeted Markdown/manifest validation, review staged and unstaged diffs, and stop. Do not implement, install, register, deploy, start MCP, call the runner, inspect audits, or perform live validation.
```

For later implementation chunks:

```text
Use the chunked-implementation skill.
Execute only the next explicitly approved chunk from the Phase 07 Steps 1–4 ADS.
Do not continue to another chunk. Preserve syntax-safe fail-closed behavior, local stdio-only transport, the revised runner as the sole execution/audit boundary, exact tool/resource allowlists, and prior-runtime isolation. Run the chunk-specific targeted validation, review staged and unstaged diffs, and stop with a handoff. Treat SDK acquisition, deployment, client registration, live runner calls, audit inspection, optional Phase 06 exposure, and rollback rehearsal as separate authorization scopes.
```

### X. Conclusion and Next Steps

This design places MCP strictly above the accepted revised runner. It selects local stdio and proposes the official Python MCP SDK, fixed runner subprocess delegation, exact registry-derived schemas, unchanged runner result/limit/redaction/audit semantics, and a closed static resource catalog. It explicitly excludes the historical bridge/orchestrator, network transports, arbitrary file reads, prompts, provider/model integration, generic execution, and automatic Phase 06 tool exposure.

The next action is Chunk 0 discovery and decision confirmation only. Implementation remains blocked until the exact SDK supply chain, first client, registry projection seam, optional tool exposure, audit classification, static resource ownership/content, revised paths, and operational authorization gates are frozen. No MCP implementation, registration, listener, package installation, runner call, or deployment is authorized by this ADS.
