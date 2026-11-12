# Revised AI-OPS MCP Interface Operations Contract — Steps 5–7

## Status and Authority

This is the approved non-activation operations contract for the Phase 07
Steps 5–7 local-stdio prompt, safety-acceptance, and lifecycle work. It is
subordinate to:

- `docs/ai-ops-revised/implementation-plan/07-mcp-interface.md`;
- `docs/ai-ops-revised/implementation-plan/ads/07-02-mcp-interface-steps-05-to-07-ads.md`;
- `docs/ai-ops-revised/runtime/mcp-interface-steps-01-to-04-operations-contract.md`;
- `docs/ai-ops-revised/runtime/mcp-interface-internal-network-operations-contract.md`;
- `docs/ai-ops-revised/runtime/manual-aiops-workflows.md`; and
- the accepted revised tool-runner contracts.

This contract authorizes documentation, local source/fixture work, and static
acceptance only. It does not authorize package acquisition, host deployment,
client registration, process startup, runner invocation against live state,
OpenStack access, raw audit inspection, listener/TLS/firewall changes, or
rollback execution.

The existing approved SDK validation environment is
`<user defined Python venv>`. It may be used for local
compile and fixture validation. The absent hash-locked dependency closure and
offline wheel remain a deployment and live-operations gate.

## Confirmed Decisions

| Concern | Confirmed decision |
| --- | --- |
| Prompt-bearing mode | Local stdio only for this phase. Option B remains tool/resource-only. |
| Initial prompt set | Exactly `project_summary`, `server_inspection`, and `metadata_diagnosis`. |
| Prompt order | `project_summary`, then `server_inspection`, then `metadata_diagnosis`. |
| Network/volume prompts | `network_diagnosis` and `volume_diagnosis` remain absent. |
| Remediation prompts | No remediation or “fix it” prompt is discoverable. |
| Prompt storage | One closed definition table in the local adapter source. No dynamic catalog or caller-selected file. |
| Text owner | AI-OPS repository/runtime maintainers. Client/model owners cannot modify prompt text. |
| Rendered-message bound | 16,384 UTF-8 bytes per rendered prompt message. |
| Prompt descriptor fields | `name`, `description`, and `arguments` only. No title, icons, metadata, or extra fields. |
| Rendered result shape | One description, one user-role message, and one plain-text content item. |
| Missing required tool | Omit the prompt from discovery. Never advertise an incomplete workflow. |
| Audit actor | Preserve the runner’s fixed `local_cli` actor. Do not add client identity. |
| Option B validation | Authenticated injected fixtures only; no listener or live integration. |
| Fixture evidence | Retain no raw or protected operational evidence. Future live evidence requires separate approval. |
| Local deployment entrypoint | The default-disabled playbook includes only the local-stdio role and remains artifact-only. |
| Completion claims | Plan and DoD items may be checked only for accepted static/fixture evidence; deployment, registration, live-operation, audit, and rollback gates remain separate. |

## Local Stdio Prompt Contract

### Prompt allowlist

The local adapter may discover only these prompts, in this order:

| Name | Exact description | Arguments | Approved tool sequence |
| --- | --- | --- | --- |
| `project_summary` | `Summarize project-visible diagnostic resources using approved read-only evidence.` | None | `project_resource_summary` |
| `server_inspection` | `Inspect one project-visible server using basic and network evidence.` | Required `server_identifier` | `server_basic_info`, then `server_network_info` with the same identifier |
| `metadata_diagnosis` | `Diagnose metadata symptoms using bounded project and server evidence.` | Required `server_identifier` | `project_resource_summary`, then `server_basic_info`, then `server_network_info` with the same identifier |

The prompt definition table is closed. Unknown prompt names are rejected, and
`network_diagnosis`, `volume_diagnosis`, `fix_it`, generic execution prompts,
and remediation prompts are not aliases or fallback names.

### Argument validation

`project_summary` accepts no arguments; an absent argument map or `{}` is
valid. Every other approved prompt accepts exactly one argument named
`server_identifier`.

`server_identifier` must be a string, non-empty, at most 255 UTF-8 bytes, and
match:

```text
^[A-Za-z0-9._:-]+$
```

Unknown, missing, extra, non-string, empty, unsafe, or oversized arguments
fail before rendering. Invalid prompt requests perform no tool call, file
read, network operation, subprocess creation, credential or audit read, or
persistent log write.

The validated identifier may be rendered as bounded data in the server and
metadata prompt text. No arbitrary operator prose, tool output, command,
path, credential, address, or raw result is interpolated.

### Descriptor and rendering shape

The adapter uses the approved low-level Python MCP SDK API:

- `Server.list_prompts()` registers a callback returning prompt descriptors;
- `Server.get_prompt()` registers a callback receiving the prompt name and
  optional string argument map; and
- prompt results use `Prompt`, `PromptArgument`, `GetPromptResult`,
  `PromptMessage`, and `TextContent` types.

The installed validation environment confirmed SDK version `mcp==1.28.1` and
these callback/constructor contracts. Implementation must still fail closed if
the runtime dependency is unavailable or the installed API diverges.

Each descriptor contains only `name`, `description`, and `arguments`. Each
rendered result contains exactly:

1. the approved prompt description;
2. one `user`-role `PromptMessage`; and
3. one plain-text `TextContent` item.

No prompt result includes metadata, resources, assistant messages, additional
content items, or dynamically loaded instructions.

### Required rendered instructions

Every rendered prompt must require the following sections, in this exact
order:

1. **Observed evidence**;
2. **Healthy signals**;
3. **Failing signals**;
4. **Inferences and likely failure domain**;
5. **Missing or unavailable evidence**; and
6. **Manual next actions — not executed**.

Every rendered prompt must instruct the client/model to:

- use only the exact approved tool names present in discovery;
- preserve tool status, correlation ID, duration, timestamp, and truncation;
- treat `unavailable`, `timeout`, `denied`, `validation_error`, `error`, empty
  sections, and truncation as evidence gaps;
- separate operator-reported symptoms from tool-observed evidence;
- never invent a tool, result, identifier, credential, observation, command, or
  root cause; and
- state that recommendations are manual, advisory, and unexecuted.

A rendered message exceeding 16,384 UTF-8 bytes is rejected without exposing
partial text.

### Workflow-specific boundaries

`project_summary` is limited to `project_resource_summary`. It must not
request a server identifier or instruct use of server, network, volume, host,
or Phase 06 tools.

`server_inspection` uses `server_basic_info` first and
`server_network_info` second, with exactly the same validated identifier. It
must keep server, network, port, fixed-IP, volume, and config-drive evidence
separate and must not infer guest or application health.

`metadata_diagnosis` uses only the three initial project/server tools. It must
label guest behavior, routes and packet delivery, Neutron proxy/agent state,
Nova metadata, listeners, host state, and logs as unavailable unless they are
separately exposed by a future approved contract. Phase 06 tool names and
authority are not exposed by this prompt.

For server and metadata workflows, an unavailable, denied, failed, timed-out,
validation-invalid, mismatched, or truncated earlier result stops further
narrowing. The prompt must prohibit guessing, retrying, or substituting a
second identifier.

The final manual-actions section may contain only high-level advisory follow-up,
such as reviewing separately approved normalized evidence. It must not contain
shell commands, SSH, sudo, service restarts, configuration edits, route
changes, guest access, credential escalation, raw-log requests, or any other
remediation instruction.

## Safety and Equivalence Acceptance

Step 6 acceptance must prove, through local fixtures and static checks, that:

- local discovery contains exactly the accepted three tools, six resources,
  and the three approved prompts;
- network, volume, Phase 06, generic, shell, SSH, sudo, OpenStack passthrough,
  file, database, package, service-control, and remediation capabilities are
  absent;
- prompt list/get operations perform no runner call, child creation, network
  access, credential/audit read, resource read, or persistent log write;
- prompt descriptors, arguments, rendered text, headings, refusal language,
  ordering, and bounds are deterministic;
- prompt content rejects secret, token, password, private-key, address,
  protected-path, command, raw-output, and topology canaries;
- valid and invalid tool requests preserve the accepted runner behavior;
- all six runner statuses, exit semantics, truncation, timestamp, duration,
  correlation ID, redaction, and sanitized error mappings remain intact;
- timeout, cancellation, EOF, and shutdown leave no runner child;
- the adapter writes no duplicate tool audit and preserves runner correlation
  semantics; and
- no test requires mutation, package acquisition, network access, live
  OpenStack state, or raw audit inspection.

The runner remains the sole tool-execution and tool-audit authority. MCP may
reject a request earlier but may not weaken runner validation, add authority,
retry a request, or reinterpret an evidence gap as success.

## Option B Fixture Boundary

Option B remains governed by
`docs/ai-ops-revised/runtime/mcp-interface-internal-network-operations-contract.md`.
Its repository status is a disabled network server skeleton with fixture
handlers and tests. This status does not claim listener activation, deployment,
external-client compatibility, live TLS, firewall state, live runner calls,
OpenStack calls, or audit inspection.

Option B prompt exposure is not implied by this contract. Its fixture
acceptance may cover exactly:

1. one authenticated `project_resource_summary` request; and
2. one authenticated `server_basic_info` followed by
   `server_network_info` request using the same validated identifier.

Fixtures use the existing approved principal URI and mapping:

```text
spiffe://openstack-lab/mcp/mcp-internal-reader
-> mcp-internal-reader
```

The fixture uses injected/fake runner behavior. It must not construct or start
a listener, materialize TLS, change firewall policy, register an external
client, contact OpenStack, invoke a live runner, or inspect raw audits.

## Client Lifecycle, Deployment, and Rollback

Local stdio has no service and no listener. The external owner-managed client
runs on `assistant02` and launches one exact adapter process as
`aiops_assistant`. Client registration remains outside this repository.

The client must treat stdout as MCP protocol-only. Adapter stderr, if used, is
bounded and sanitized. No client or model identity is forwarded to the runner
or audit.

The default-disabled local entrypoint is present at:

```text
ansible/ai_ops_assistant/playbook_deploy_mcp_stdio.yml
```

It may target only `ai_ops_assistant`/`assistant02`, include only
`ai_ops_assistant_mcp_stdio`, and set:

```text
ai_ops_assistant_mcp_stdio_enabled: false
ai_ops_assistant_mcp_stdio_explicit_activation: false
```

It must remain artifact-only and must not install packages, create or start a
service, open a listener, change firewall state, register a client, invoke the
runner, inspect audits, or remove artifacts. The existing local role remains
default-disabled and its missing dependency lock continues to fail closed when
enabled.

Local disablement is ordered as follows:

1. disable or remove the external client registration;
2. close stdin or terminate the client-owned adapter session;
3. verify adapter and runner child absence and reaping;
4. verify no local MCP/runner child or listener remains;
5. preserve the manual/local runner workflow; and
6. remove exact local-stdio artifacts only under separately approved rollback.

Upgrade is ordered as follows:

1. disable external client registration;
2. verify adapter and runner process absence;
3. validate the externally supplied hash-locked SDK/offline artifact;
4. materialize the reviewed adapter, catalog, and configuration;
5. run static and fixture checks; and
6. allow the external client owner to re-enable registration.

No rollback may remove shared runner, diagnostic, credential, audit, evidence,
Option B, or historical-runtime artifacts. Option B network-policy rollback
remains governed by its separate internal-network contract and is outside this
local fixture and artifact-only deployment scope.

## Evidence, Ownership, and Authorization

Fixture validation retains no raw prompts, identifiers, addresses, tool
results, audit records, credentials, or protected operational evidence. Local
and CI output is limited to normalized pass/fail outcomes.

Any future live validation requires a separate approval that names the evidence
owner, protected location, retention policy, allowed fields, client/model
handling, and deletion/rollback procedure. This contract does not create that
approval or authorize live evidence collection.

The following gates remain independent:

| Gate | Status |
| --- | --- |
| SDK version/API validation | Confirmed in the approved local venv. |
| Hash-locked SDK closure and offline wheel | Missing; deployment blocker. |
| Prompt implementation | Local stdio exposes the three approved prompts; focused prompt tests pass. Option B remains tool/resource-only. |
| Local fixture/static tests | Local stdio and Option B fixture suites and static deployment acceptance pass; no live operation was performed. |
| Local artifact deployment | Default-disabled playbook is present; deployment remains separately authorized and was not performed. |
| External client registration | Outside repository and separately authorized. |
| Option B listener/TLS/firewall | Separately authorized and not covered by fixture work. |
| Live runner/OpenStack calls | Separately authorized. |
| Raw audit inspection | Separately authorized. |
| Rollback execution | Separately authorized. |

## Failure and Stop Rules

| Failure | Required action |
| --- | --- |
| Prompt contract, description, order, owner, or bound is ambiguous | Discover no new prompt and report a contract blocker. |
| Required tool is absent | Omit the dependent prompt; never substitute another tool. |
| Invalid prompt name or argument | Return a bounded validation error without I/O or execution. |
| Prompt output is oversized or contains prohibited material | Reject the revision and expose no partial text. |
| Prompt implies mutation or executable remediation | Fail safety acceptance and keep the prompt undiscoverable. |
| Runner status, result, bounds, redaction, or audit semantics drift | Reject Step 6 acceptance. |
| Cancellation or EOF leaves a child | Keep client integration disabled and report a lifecycle blocker. |
| Option B source/contract status diverges | Do not claim Step 7 evidence; reconcile documentation first. |
| Dependency lock/wheel provenance is absent | Permit local fixture work only; prohibit deployment and activation. |
| Client registration or lifecycle behavior is unknown | Keep registration outside the repository and report an external-client blocker. |
| Rollback target is shared or ownership is unclear | Abort removal and preserve shared runtime state. |

## Validation Contract and Stop Condition

The approved local validation interpreter is:

```text
<user defined Python venv>
```

Permitted validation is local and fixture-driven:

```bash
rtk <user defined Python venv> -m unittest discover \
  -s ansible/ai_ops_assistant/tests/mcp_stdio -p 'test_*.py'
rtk <user defined Python venv> -m unittest discover \
  -s ansible/ai_ops_assistant/tests/mcp -p 'test_*.py'
rtk git diff --check
```

The focused local and Option B fixture suites and static deployment acceptance
have passed. No package download, deployment, client registration, listener,
live diagnostic, audit inspection, or rollback operation is permitted by this
contract.

This contract is complete for the non-activation implementation boundary when
reviewers can predict every prompt, argument, rendered response, evidence gap,
refusal, fixture call, lifecycle state, approval gate, and rollback boundary.
Static/fixture-supported Steps 5–7 items may be reconciled in the plan;
operational deployment, registration, live workflow, audit, and rollback
execution remain independently gated.
