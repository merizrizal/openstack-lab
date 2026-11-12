# Revised AI-OPS Local-stdio MCP Operations Contract — Steps 1–4

## Status and authority

This is the non-activation operations contract for the baseline local-stdio MCP interface in Phase 07 Steps 1–4. It is subordinate to:

- `docs/ai-ops-revised/implementation-plan/07-mcp-interface.md`;
- `docs/ai-ops-revised/implementation-plan/ads/07-00-mcp-interface-steps-01-to-04-ads.md`;
- `docs/ai-ops-revised/runtime/runtime-placement-contract.md`;
- `docs/ai-ops-revised/runtime/selective-reuse-manifest.md`;
- `docs/ai-ops-revised/runtime/tool-runner-safety-gateway-steps-01-to-04-operations-contract.md`; and
- `docs/ai-ops-revised/runtime/tool-runner-safety-gateway-steps-05-to-07-operations-contract.md`.

The authenticated internal-network implementation is governed separately by:

- `docs/ai-ops-revised/implementation-plan/ads/07-01-internal-network-mcp-extension-ads.md`; and
- `docs/ai-ops-revised/runtime/mcp-interface-internal-network-operations-contract.md`.

This contract preserves that Option B implementation and does not modify, replace,
share uncontrolled configuration with, or activate it.

This document authorizes only contract work and later local fixture/static
validation. It does not authorize package acquisition, dependency installation,
client registration, deployment, process startup, runner invocation, OpenStack
access, audit inspection, or rollback execution.

## Confirmed decisions

| Concern | Confirmed decision |
| --- | --- |
| Transport | Local stdio only; no TCP, HTTP, SSE, socket, Unix listener, or bridge. |
| Option B coexistence | Preserve the existing authenticated internal-network implementation unchanged; local stdio has a separate namespace. |
| First client | `owner-managed-local-stdio-client-v1`, running on `assistant02`. |
| Client identity | The client launches the adapter as `aiops_assistant`; no client identity is passed to the runner or audit. |
| Client registration | External to this repository and separately approved; no client registration artifact is committed here. |
| SDK | Exact `mcp==1.28.1`, no extras, subject to hash-locked offline-artifact verification. |
| Registry projection | A bounded adapter-local read-only projector with exhaustive equivalence fixtures; no dynamic runner-module import. |
| Initial tools | `project_resource_summary`, `server_basic_info`, and `server_network_info`. |
| Phase 06 tools | Denied and non-discoverable in this local interface. |
| Audit actor | Preserve the runner's fixed `local_cli` actor. |
| Runner concurrency | One runner child at a time; no queueing or retry. |
| Validation environment | `<user defined Python venv>`; no system-Python fallback. |
| Evidence owner | OpenStack platform operations / lab administrator for outcome-only validation evidence. |

Role-based ownership and independent approval gates are defined in the
authorization matrix below. These decisions do not prove that protected
artifacts or host state exist.

## Non-activation and coexistence boundary

Until later approvals and prerequisite verification:

- no local MCP process is started;
- no local MCP listener or network transport is created;
- no external client is registered or configured by this repository;
- no MCP package is installed or downloaded;
- no runner or diagnostic is invoked;
- no live audit is inspected or written by the adapter;
- no certificate, key, firewall, route, or service is created;
- the Option B network MCP files, service contract, and disabled state remain unchanged;
- the revised runner, diagnostics, credentials, audit, evidence, and prior runtime remain unchanged; and
- missing or ambiguous prerequisites keep local MCP unavailable rather than widening access.

The adapter's stdout is reserved exclusively for MCP protocol frames. It must
never print diagnostics, paths, registry contents, credentials, raw exceptions,
runner output, or lifecycle logs to stdout. Sanitized bounded diagnostics may be
sent to stderr only when the selected SDK/client lifecycle requires them.

## Local stdio namespace and ownership

The local-stdio implementation owns these exact repository paths:

```text
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio/
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio/files/mcp_stdio/aiops_assistant_mcp_stdio_server.py
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio/files/mcp_stdio/mcp_resource_catalog.json
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio/files/mcp_stdio/config.json
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio/files/mcp_stdio/requirements.in
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio/files/mcp_stdio/requirements.lock
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio/defaults/main.yml
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio/tasks/main.yml
ansible/ai_ops_assistant/tests/mcp_stdio/
ansible/ai_ops_assistant/playbook_deploy_mcp_stdio.yml
```

The local runtime paths are:

```text
runtime root: /opt/openstack-ai-ops-assistant/mcp-stdio
adapter: /opt/openstack-ai-ops-assistant/mcp-stdio/aiops_assistant_mcp_stdio_server.py
catalog: /opt/openstack-ai-ops-assistant/mcp-stdio/mcp_resource_catalog.json
configuration: /etc/ai-ops-assistant/mcp-stdio/config.json
virtual environment: /opt/openstack-ai-ops-assistant/mcp-stdio/venv
runtime user/group: aiops_assistant:aiops_assistant
```

The runtime root, configuration directory, and virtual environment are owned by
`root:aiops_assistant` with mode `0750`. Deployed adapter, catalog, and
configuration files are regular non-symlink files owned by `root:aiops_assistant`
with mode `0640`. The role default is disabled:

```text
ai_ops_assistant_mcp_stdio_enabled: false
ai_ops_assistant_mcp_stdio_explicit_activation: false
```

The role may install reviewed artifacts only after a separately approved
artifact-deployment scope. It must not create a systemd unit, service, listener,
firewall rule, client registration, or network route.

The existing Option B role and paths remain separate:

```text
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp/
/opt/openstack-ai-ops-assistant/mcp/
ai-ops-assistant-mcp
```

No local-stdio task may overwrite, template, reload, stop, start, or remove an
Option B artifact.

## Dependency and SDK contract

The local adapter uses the maintained official Python MCP SDK with this exact
input requirement:

```text
mcp==1.28.1
```

No extras, provider packages, SSH/database clients, generic executor
libraries, or historical orchestrator dependencies are permitted. The adapter
must not directly import or activate HTTP server packages or network transport
APIs. The dependency closure must be generated with pip-tools using hashes and
no extras, then reviewed as a complete lock. The corresponding
wheel artifact must be supplied through an approved internal artifact source or
offline directory. Runtime package downloads are forbidden.

The lock and wheel artifact are prerequisites, not present implementation
claims. Until both are verified, the adapter remains absent or disabled and no
activation test is run.

The selected validation environment is:

```text
<user defined Python venv>
```

No system-Python fallback is permitted. Python validation is local and fixture
driven only; it must not contact the network, OpenStack, a client, a runner
process, or an audit sink.

## Client and lifecycle contract

The first supported client is the owner-managed local stdio client identified as
`owner-managed-local-stdio-client-v1`. It runs on `assistant02` and launches one
exact adapter process as `aiops_assistant`:

```text
/opt/openstack-ai-ops-assistant/mcp-stdio/venv/bin/python \
  /opt/openstack-ai-ops-assistant/mcp-stdio/aiops_assistant_mcp_stdio_server.py
```

The external client configuration and registration location are owned and
managed outside this repository. The client must provide no OpenStack, SSH,
provider, model, proxy, audit, or credential environment variables and no
adapter path, registry path, profile, executable, timeout, output, or working
directory overrides.

The client owns the child lifecycle:

- start one adapter child for a selected session;
- send and receive MCP frames over stdin/stdout;
- close stdin on shutdown;
- allow clean EOF or cancellation to terminate the session;
- ensure the adapter terminates its runner child before exiting; and
- treat a non-zero adapter exit as unavailable, without an automatic restart loop.

No client-provided name, metadata, principal, actor, correlation ID, or
transport value enters the runner request or audit event.

## Runner delegation contract

Every accepted tool call delegates to the existing revised runner and no other
execution path:

```text
/opt/openstack-ai-ops-assistant/mcp-stdio/venv/bin/python \
  /opt/openstack-ai-ops-assistant/scripts/tool_runner/aiops_tool_runner.py \
  TOOL_NAME [--arg KEY=VALUE ...]
```

The adapter uses argument-vector execution with `shell=False`. It passes only
the discovered tool name and registry-declared public arguments. It cannot pass
or accept a registry path, implementation path, profile, audit path, executable,
working directory, environment, actor, client identity, correlation ID,
timeout, or output-limit override.

The runner remains authoritative for:

- registry validation and authority selection;
- implementation target and credential profile;
- child environment and working directory;
- diagnostic timeout and output limits;
- result construction and redaction; and
- timestamp, correlation ID, and tool-audit persistence.

The adapter must not import diagnostic implementations, construct diagnostic
argv, read credential/profile files, write tool audits, retry calls, or turn a
runner failure into success.

## Registry projection and exposure contract

The adapter reads only the fixed revised registry at:

```text
/opt/openstack-ai-ops-assistant/scripts/tool_runner/tool_registry.json
```

The adapter-local projector may inspect only the public registry fields needed
to produce MCP descriptors:

- tool name;
- bounded public description;
- public parameter names and order;
- string type;
- required flag;
- pattern;
- maximum length;
- closed enum values; and
- approved default.

It must not project implementation targets, profiles, authority internals,
credential paths, environment values, audit paths, commands, or output/runtime
controls. The projector rejects duplicate keys, unknown or unsupported schema
fields, duplicate tools/parameters, unsupported validators, unknown exposure
names, and any mismatch with the approved fixtures. A projection failure stops
startup and exposes no tools.

The initial discovery set is exactly:

| Tool | Public arguments | Authority |
| --- | --- | --- |
| `project_resource_summary` | none | revised runner project-reader mapping |
| `server_basic_info` | required `server_identifier` | revised runner project-reader mapping |
| `server_network_info` | required `server_identifier` | revised runner project-reader mapping |

The two server schemas use:

```text
type: object
additionalProperties: false
server_identifier: string
pattern: ^[A-Za-z0-9._:-]+$
maxLength: 255
required: [server_identifier]
```

The project summary schema has no properties and has
`additionalProperties: false`. Missing, unknown, wrong-type, unsafe, or
oversized arguments are rejected before child creation. The runner validates
any forwarded request again.

The Phase 06 tools—`neutron_agent_health`, `recent_metadata_errors`,
`recent_neutron_errors`, and `recent_nova_errors`—are not exposed. Generic
shell, SSH, sudo, OpenStack passthrough, file, database, package,
service-control, provider, and remediation capabilities are absent and must not
be represented by placeholders.

## Result, limits, redaction, and audit contract

The adapter accepts exactly one complete runner result line as bounded UTF-8
JSON. The closed runner envelope contains:

```text
schema_version, tool, status, arguments, exit_code, data, stdout, stderr,
error, duration_ms, truncated, timestamp, correlation_id
```

The adapter validates the complete field set, status, tool, exit semantics,
argument shape, UTF-8, JSON, and byte bound before returning protocol content.
It returns the envelope as structured MCP content and one deterministic compact
JSON text item. It does not synthesize fields, drop safety metadata, re-redact
into a weaker shape, expose raw stderr, or reinterpret diagnostic findings.

The six runner statuses are preserved:

| Status | MCP error mapping |
| --- | --- |
| `ok` | `isError: false` |
| `error` | `isError: true` |
| `denied` | `isError: true` |
| `validation_error` | `isError: true` |
| `timeout` | `isError: true` |
| `unavailable` | `isError: true` |

Fixed local bounds are:

| Limit | Value |
| --- | ---: |
| Runner children | 1 |
| Queueing | none |
| Outer deadline for `project_resource_summary` | 50 seconds |
| Outer deadline for `server_basic_info` | 35 seconds |
| Outer deadline for `server_network_info` | 50 seconds |
| Cleanup grace | 5 seconds maximum |
| Accepted runner envelope | 256 KiB |
| Captured child stderr | 8 KiB maximum, never returned raw |
| Automatic retries | none |

The outer deadline is the trusted runner timeout plus five seconds. On timeout,
cancellation, EOF, or client termination, the adapter terminates and reaps only
its runner child/process group. An orphan or cleanup failure is an adapter
failure; the call is not retried.

Protocol/lifecycle logging is disabled as a persistent file. If stderr logging
is retained, it is bounded to 100 sanitized lifecycle/error events per minute
and contains no tool payload, arguments, result data, raw exceptions, paths,
credentials, profiles, audit content, or command lines. Public adapter errors
use only fixed classes such as:

- `adapter_configuration_error`;
- `tool_exposure_error`;
- `schema_equivalence_error`;
- `runner_unavailable`;
- `runner_protocol_error`; and
- `adapter_redaction_error`.

The runner remains the only tool-audit writer. Every invoked request has one
runner-generated timestamp, UUIDv4 correlation ID, and corresponding runner
`tool_request_completed` event with actor `local_cli`. The adapter writes no
duplicate audit event and accepts no free-form client identity.

## Curated static resource contract

Resources are embedded in the fixed catalog at:

```text
/opt/openstack-ai-ops-assistant/mcp-stdio/mcp_resource_catalog.json
```

The catalog is a closed duplicate-key-rejecting JSON object with schema version
`1`, unique URIs/names, deterministic order, UTF-8 content, a maximum of 64 KiB
per resource, and a maximum of 256 KiB for the complete catalog. Its exact
reviewed URI set is:

- `aiops://architecture/lab-summary`;
- `aiops://policy/diagnostic-safety`;
- `aiops://policy/credential-profile`;
- `aiops://policy/tool-registry`;
- `aiops://policy/audit`; and
- `aiops://runbooks/metadata-troubleshooting`.

Each resource is bounded Markdown containing only reviewed static context:

| Resource | Owner |
| --- | --- |
| Architecture summary | Platform operations / lab administrator |
| Diagnostic safety policy | Security / platform operations |
| Credential-profile policy | Security / platform operations |
| Tool-registry policy | Runner maintainer |
| Audit policy | Security / platform operations |
| Metadata troubleshooting runbook | Diagnostics maintainer |

Content review must reject credentials, keys, tokens, passwords, bearer values,
addresses, protected inventory, raw command/output/audit data, dynamic paths,
private topology, mutation instructions, and unsupported remediation claims.
Every catalog revision requires owner review and repeat secret, topology, and
canary scans.

Resource listing and reads are pure allowlisted lookups. Unknown URIs return a
generic not-found/protocol error without filesystem, network, audit, credential,
or command access. Prompts are not registered in Steps 1–4.

## Deployment, disablement, and rollback

The local role and playbook are default-disabled and install artifacts only.
They may not create a service unit or activate a process. Deployment requires
separate approval for:

- the complete SDK lock and offline wheel artifact;
- local artifact deployment to `assistant02`; and
- any future external client registration.

Client registration is disabled or removed first during rollback. The owner then
verifies no local adapter or runner child remains and removes only the exact
local-stdio adapter, catalog, configuration, lock/wheel artifact, and dedicated
venv. Rollback must preserve:

- the revised runner and diagnostics;
- project-reader and other credential material;
- the revised audit and evidence locations;
- the Option B network MCP artifacts and disabled state; and
- the historical runtime and manual/local runner workflow.

No rollback operation is automatic or authorized by this contract.

## Authorization and ownership matrix

Approval of one scope does not imply approval of another.

| Scope | Owner | Required before action |
| --- | --- | --- |
| Contract/static review | Phase 07 maintainer/reviewer | Reviewable diff and static checks |
| SDK lock and offline artifact | Platform operations / lab administrator | Provenance, hashes, closure, compatibility, and protected artifact reference |
| Artifact deployment | Platform operations / lab administrator | Target, exact limit, prerequisites, explicit opt-in, rollback owner |
| Client registration | Owner-managed client operator | Exact client configuration and lifecycle approval outside this repository |
| Runner execution | Diagnostic operator | Deployed integrity, protected prerequisites, and explicit request authorization |
| Audit inspection | Audit owner | Fixed path, minimum-disclosure scope, retention, and deletion policy |
| Outcome-only evidence | Platform operations / lab administrator | Protected destination, owner, retention, and normalized schema |
| Rollback | Platform operations; security escalation for credentials | Replacement/recovery plan and explicit removal approval |
| Emergency revocation | OpenStack security or senior lab administrator | Revocation trigger and normalized outcome evidence |

## Failure and stop rules

The adapter and deployment remain unavailable when any of the following occurs:

- the SDK version, lock, hashes, wheel, or validation environment is missing or
  unverifiable;
- the selected client requires a network transport, credentials, SSH, or an
  uncontrolled lifecycle;
- a path collides with Option B, the prior runtime, or a protected location;
- the registry projection is unsupported, ambiguous, or not equivalent;
- the exposure policy names an unknown, optional-disabled, or Phase 06 tool;
- a tool request has missing, unknown, unsafe, wrong-type, or oversized input;
- the runner cannot be spawned at its fixed path;
- the runner emits empty, multiple, malformed, oversized, non-UTF-8, or
  extra-field output;
- timeout or cancellation cannot safely reap the child;
- a secret, path, payload, raw exception, or audit value reaches protocol logs;
- a catalog contains unknown fields, duplicate keys, unsafe content, or an
  unreviewed URI; or
- any deployment, client registration, runner call, audit inspection, or
  rollback scope lacks separate approval.

No failed request is retried automatically. A new operational attempt requires
fresh owner authorization and, where applicable, a new protected run/evidence
reference.

## Validation contract

Chunk-local validation is non-operational and uses only repository files,
fixtures, and the approved validation environment after dependency presence is
confirmed. It must not install packages, access the network, start MCP, invoke
the runner, inspect audits, contact OpenStack, register a client, or deploy a
host.

Required later checks include:

```bash
rtk git diff --check
rtk grep -n -E '^##|^###' docs/ai-ops-revised/runtime/mcp-interface-steps-01-to-04-operations-contract.md
rtk grep -n -E 'stdio|no listener|runner|additionalProperties|resources|Rollback|Authorization' docs/ai-ops-revised/runtime/mcp-interface-steps-01-to-04-operations-contract.md
```

Before executable chunks, focused tests must prove:

1. only stdio APIs are selected and no network/listener imports or calls exist;
2. malformed configuration, registry, exposure policy, or catalog fails closed;
3. discovery is exactly the three approved project tools;
4. Phase 06 and generic/remediation capabilities are absent;
5. projected schemas match registry fixtures exactly;
6. rejected arguments create no child;
7. accepted calls use only the fixed runner argv and one concurrency slot;
8. complete result/status/truncation/error semantics are preserved;
9. timeout, cancellation, and EOF leave no child;
10. stdout contains protocol only and stderr contains no sensitive payload; and
11. resources are static, bounded, URI-allowlisted, and free of secret canaries.

No check in this contract authorizes package acquisition, deployment, client
registration, live runner execution, audit inspection, network access, or
rollback rehearsal.

## Stop condition

Steps 1–4 remain non-activating until the local adapter, dependency artifact,
resource catalog, and focused tests are separately accepted. Client registration,
deployed runner calls, audit inspection, and rollback rehearsal require later
explicit approvals. Steps 5–7 and the Option B network activation remain out of
scope for this contract.
