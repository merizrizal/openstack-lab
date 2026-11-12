# Revised AI-OPS Internal-Network MCP Operations Contract

## Status and Authority

This is the non-activation operations contract for the separately governed Phase 07
Option B internal-network MCP extension. It is subordinate to:

- `docs/ai-ops-revised/implementation-plan/07-mcp-interface.md`;
- `docs/ai-ops-revised/implementation-plan/ads/07-01-internal-network-mcp-extension-ads.md`;
- `docs/ai-ops-revised/runtime/runtime-placement-contract.md`;
- `docs/ai-ops-revised/runtime/selective-reuse-manifest.md`;
- `docs/ai-ops-revised/runtime/tool-runner-safety-gateway-steps-01-to-04-operations-contract.md`; and
- `docs/ai-ops-revised/runtime/tool-runner-safety-gateway-steps-05-to-07-operations-contract.md`.

It freezes the internal transport, network boundary, TLS/mTLS, authorization,
limits, lifecycle, audit, deployment, and rollback contract. It does not create
a listener, route, certificate, firewall rule, package environment, service,
client registration, runner invocation, audit inspection, or host state.

The baseline local-stdio MCP design remains a separate deployment mode. This
contract does not replace, broaden, or modify that mode.

## Confirmed Decision Register

The following values are owner-confirmed design inputs. They are not evidence
that the corresponding host state exists.

| Concern | Confirmed value |
| --- | --- |
| Revised host | `assistant02` |
| Bind interface | `eth0` |
| Bind address | `192.168.121.21` |
| Transport | Streamable HTTP over TLS 1.3 |
| Service port | `8443` |
| MCP endpoint | `/mcp` |
| Canonical URL | `https://192.168.121.21:8443/mcp` |
| Source allowlist | `192.168.121.0/24` |
| Firewall owner | Vagrant |
| Firewall marker | `ai-ops-assistant-mcp-https-ingress` |
| DNS name | None |
| Authentication | Mandatory mutual TLS |
| Initial principal | `mcp-internal-reader` |
| Phase 06 tools | Denied and non-discoverable |
| Approval reference | `phase07-internal-mcp-https-mtls-0701` |

The approval reference is owner-supplied. Deployment must verify the external
approval record before using it. Its confirmed scope is dependency artifact
acquisition, TLS materialization, Vagrant firewall ingress, MCP artifact
deployment, systemd activation, runner invocation, audit inspection, and
rollback. External-client registration remains separately excluded.

## Non-Activation and Coexistence Boundary

Until the later activation gate:

- no process listens on `192.168.121.21:8443`;
- no Vagrant firewall rule is added;
- no certificate, private key, CA bundle, or CRL is issued or copied;
- no MCP package is installed or downloaded;
- no service unit is enabled or started;
- no external client is registered or configured;
- no revised runner or live audit is invoked or inspected; and
- the local-stdio design, manual runner, diagnostics, credentials, audit, and
  historical `assistant01` runtime remain unchanged.

Option B is independently disableable. A missing, invalid, stale, unexpected,
world-readable, or owner-ambiguous prerequisite keeps the service disabled and
must not result in a permissive fallback.

## Transport and HTTP Contract

The service uses the approved Python MCP SDK low-level server API:

```text
mcp.server.lowlevel.Server
mcp.server.streamable_http.StreamableHTTPServerTransport
mcp.server.streamable_http_manager.StreamableHTTPSessionManager
Starlette ASGI application
Uvicorn server with an explicit TLS SSLContext
```

`FastMCP.run()` convenience routing is not used. The service is stateful with
at most four sessions, has no event store or resumability, and uses JSON-only
POST responses. The exact endpoint behavior is:

| Concern | Contract |
| --- | --- |
| Route | `/mcp` only |
| Methods | `POST`, `GET`, and `DELETE` only |
| POST content type | `application/json` only |
| POST response framing | JSON-only (`json_response=true`); SSE streaming disabled |
| GET behavior | Authenticated session method only; no server-event stream |
| Host header | Exactly `192.168.121.21:8443` |
| Origin | Must be absent; any supplied Origin is rejected |
| CORS | Disabled |
| Authentication | Required before every method |
| Custom routes | None |
| Health/readiness route | None |
| Session identity | Bound to the authenticated client principal |
| Cross-principal reuse | Forbidden |

The service binds only when `eth0` owns the exact approved address. Wildcard,
loopback-only, public, dynamically supplied, unexpected, IPv6, or alternate
binds fail startup. The application independently rejects peers outside the
approved source CIDR; forwarded source headers are not trusted.

## TLS and Certificate Contract

TLS terminates inside the MCP process. There is no reverse proxy or alternate
TLS trust boundary.

### Fixed material paths and metadata

```text
TLS directory: /etc/ai-ops-assistant/mcp/tls
owner/group: root:aiops_assistant
mode: 0750

server certificate: /etc/ai-ops-assistant/mcp/tls/server.crt
server private key: /etc/ai-ops-assistant/mcp/tls/server.key
client CA bundle: /etc/ai-ops-assistant/mcp/tls/client-ca.crt
client CRL: /etc/ai-ops-assistant/mcp/tls/client-ca.crl
file owner/group: root:aiops_assistant
file mode: 0640
```

The files must be regular non-symlinks. Missing files, unsafe path resolution,
wrong ownership or mode, malformed material, or an invalid chain prevents
startup. No server private key or client private key is stored in Git or in the
Vagrant repository. The client private key remains only on the external client
host.

The server certificate is issued by an externally managed internal CA and must
contain exactly:

```text
SAN: IP:192.168.121.21
DNS SANs: none
wildcard SANs: forbidden
key algorithm: ECDSA P-256
signature: SHA-256 or stronger
key usage: digitalSignature
EKU: serverAuth
CN: ignored
validity: 90 days
renewal: 30 days before expiry
```

The client certificate is externally issued and must contain:

```text
key algorithm: ECDSA P-256
signature: SHA-256 or stronger
key usage: digitalSignature
EKU: clientAuth
URI SAN: spiffe://openstack-lab/mcp/mcp-internal-reader
CN: ignored
validity: 30 days
renewal: 7 days before expiry
```

The external CA/platform owner controls issuance, rotation, and revocation.
Vagrant/platform provisioning may install protected material but must not issue
certificates, create CA keys, or retain the client private key.

### TLS verification

The SSL context enforces TLS 1.3 only, `CERT_REQUIRED`, the closed client CA
bundle, and the client CRL. TLS 1.2 and older are rejected. System-wide or
unrelated CA roots are not consulted. The CRL must have a valid `nextUpdate`;
missing, malformed, expired, or stale CRL material fails closed. CRL refresh is
required at least seven days before `nextUpdate`, with emergency revocation
propagated within 15 minutes. No stale-cache or fallback trust source exists.

A client certificate is accepted only when its chain, validity, revocation,
clientAuth EKU, and exact URI SAN all pass. The server does not use CN matching,
fingerprint pinning, wildcard identities, or client-asserted identity.

## Authentication and Authorization Contract

Authentication and authorization are separate checks:

1. TLS requires a valid client certificate.
2. The server extracts the exact URI SAN.
3. Only `spiffe://openstack-lab/mcp/mcp-internal-reader` maps to the fixed
   principal `mcp-internal-reader`.
4. The principal may access only the three project-reader tools and reviewed
   static resources.
5. Phase 06 tools, generic capabilities, arbitrary resources, and all unknown
   methods are absent or denied.

The initial tool allowlist is exactly:

- `project_resource_summary`;
- `server_basic_info`; and
- `server_network_info`.

The server accepts no bearer token, anonymous request, network-only trust,
client-provided principal, actor, profile, target, registry, audit path,
timeout, output limit, executable, environment, correlation ID, or filesystem
path. Invalid or revoked certificates fail during TLS without an MCP response.
A valid certificate with an unknown identity, a peer outside the source CIDR,
or a disallowed capability receives a generic `403` response without runner
creation.

## Fixed Service Configuration

The closed, duplicate-key-rejecting configuration file is:

```text
/etc/ai-ops-assistant/mcp/config.json
owner/group: root:aiops_assistant
mode: 0640
```

Its non-secret fields are exactly:

```json
{
  "schema_version": 1,
  "transport": "streamable-http",
  "bind_interface": "eth0",
  "bind_address": "192.168.121.21",
  "port": 8443,
  "endpoint_path": "/mcp",
  "allowed_source_cidrs": ["192.168.121.0/24"],
  "tls_certificate_path": "/etc/ai-ops-assistant/mcp/tls/server.crt",
  "tls_private_key_path": "/etc/ai-ops-assistant/mcp/tls/server.key",
  "tls_client_ca_path": "/etc/ai-ops-assistant/mcp/tls/client-ca.crt",
  "tls_client_crl_path": "/etc/ai-ops-assistant/mcp/tls/client-ca.crl",
  "authorized_principal_uri": "spiffe://openstack-lab/mcp/mcp-internal-reader",
  "max_header_bytes": 8192,
  "max_request_body_bytes": 65536,
  "max_response_body_bytes": 262144,
  "max_concurrent_sessions": 4,
  "max_concurrent_runner_children": 1,
  "requests_per_minute": 10,
  "request_burst": 2,
  "session_idle_seconds": 300,
  "request_deadline_seconds": 305
}
```

Unknown fields, missing fields, duplicate keys, path changes, embedded secrets,
environment overrides, and permissive defaults fail startup. The repository
source for this fixed artifact is:

```text
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp/files/mcp/config.json
```

## Request Bounds and Failure Behavior

| Limit | Value | Exceeded behavior |
| --- | ---: | --- |
| HTTP headers | 8 KiB | HTTP `431` |
| Request body | 64 KiB | HTTP `413` |
| Response body | 256 KiB | Generic bounded failure |
| Aggregate retained bytes/request | 256 KiB | Generic bounded failure |
| Concurrent sessions | 4 | HTTP `429` |
| Concurrent runner children | 1 | HTTP `429` |
| Per-principal rate | 10 requests/minute | HTTP `429` |
| Rate burst | 2 | HTTP `429` with fixed `Retry-After: 60` |
| Session idle time | 300 seconds | Session termination |
| Request deadline | 305 seconds | Cancel, terminate, reap, and return timeout |
| Queueing | None | Immediate bounded failure |

Limit responses reveal no internal policy detail and never retry or re-execute
a request.

## Runner Delegation and Result Contract

Every authorized tool call invokes exactly:

```text
/opt/openstack-ai-ops-assistant/mcp/venv/bin/python \
/opt/openstack-ai-ops-assistant/scripts/tool_runner/aiops_tool_runner.py \
TOOL_NAME [--arg KEY=VALUE ...]
```

Execution uses `shell=False`, one child per request, and no caller or adapter
overrides. The adapter passes no registry, audit, profile, timeout, output,
environment, actor, client, correlation, or executable arguments. The runner
remains the sole diagnostic execution, result, redaction, and tool-audit
authority.

MCP returns the runner’s complete validated envelope as structured content and
one deterministic compact JSON text item. The runner’s six statuses and
truncation metadata are preserved. `isError` is true for every non-`ok` status.
Raw child stdout/stderr, exceptions, commands, paths, credentials, profiles,
and audit contents are never exposed.

## Audit and Logging Contract

The runner retains its accepted fixed tool-audit behavior:

```text
actor: local_cli
event: exactly one tool_request_completed event per runner request
MCP duplicate tool audit: forbidden
```

The server writes no duplicate tool-execution audit event. It emits only the
following bounded authentication/lifecycle event classes to the systemd
journal:

```text
schema_version: "1.0"
event_type: mcp_lifecycle | mcp_authentication | mcp_authorization
outcome: started | stopped | accepted | denied
principal: mcp-internal-reader after successful authentication; unknown otherwise
source_allowed: boolean
reason: fixed normalized class or null
```

Network logs contain no token, certificate subject, private key, source IP,
request body, headers, tool result, raw exception, command, credential, or
profile content. The journal is the only log sink, with INFO lifecycle events,
WARNING/ERROR failures, a 100-event/minute service rate limit, and 30-day
retention under the Vagrant/journald owner policy. No fallback sink is allowed.

## Service Identity and Lifecycle

The service unit is:

```text
repository template:
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp/templates/ai-ops-assistant-mcp.service.j2

host unit:
/etc/systemd/system/ai-ops-assistant-mcp.service

owner/group: root:root
mode: 0644
service name: ai-ops-assistant-mcp
ExecStart: /opt/openstack-ai-ops-assistant/mcp/venv/bin/python /opt/openstack-ai-ops-assistant/mcp/aiops_assistant_mcp_server.py
shell execution: forbidden
```

The service runs as `aiops_assistant:aiops_assistant` with working directory
`/opt/openstack-ai-ops-assistant/mcp`. The dedicated MCP directory is
`root:aiops_assistant`, mode `0750`; this requires reconciliation with the
foundation workspace declaration before deployment. MCP code and configuration
are not service-user-writable.

The unit uses the fixed MCP venv and adapter path and receives exactly this
minimal environment:

```text
PATH=/usr/bin:/bin
HOME=/nonexistent
PYTHONNOUSERSITE=1
LANG=C.UTF-8
LC_ALL=C.UTF-8
```

It has no OpenStack, SSH, proxy, provider, model, token, credential,
registry-path, audit-path, or executable overrides.

The unit is default-disabled:

```text
ai_ops_assistant_mcp_enabled: false
ai_ops_assistant_mcp_explicit_activation: false
```

Enabling requires both values to be true. The lifecycle policy is:

```text
restart: on-failure
restart delay: 5 seconds
start limit: 3 failures per 5 minutes
unauthenticated health endpoint: none
readiness: active only after fixed bind/TLS/CRL/policy validation
liveness: systemd supervision
SIGTERM: stop accepting requests, cancel/reap children, exit within 10 seconds
SIGKILL: permitted after the shutdown deadline
orphaned child/process: lifecycle failure
```

Systemd hardening is mandatory:

```text
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
PrivateDevices=true
RestrictSUIDSGID=true
LockPersonality=true
RestrictAddressFamilies=AF_INET
CapabilityBoundingSet=
AmbientCapabilities=
UMask=0077
ReadWritePaths=/opt/openstack-ai-ops-assistant/audit
```

## Deployment, Authorization, and Rollback

Deployment must occur in this order:

1. Validate the Python 3.14 hash-locked offline dependency artifact.
2. Materialize and validate server certificate, key, client CA bundle, and CRL.
3. Apply the Vagrant-owned marker-scoped firewall rule.
4. Install MCP adapter, catalog, configuration, and dependency artifacts with
   the service disabled.
5. Install the disabled systemd unit.
6. Run static, configuration, certificate, ownership, and listener checks.
7. Verify approval `phase07-internal-mcp-https-mtls-0701`.
8. Explicitly activate the service.
9. Perform only separately recorded fixture or integration calls.

The deployment target is restricted to:

```text
ansible/ai_ops_assistant/playbook_deploy_mcp.yml
hosts: ai_ops_assistant
host: assistant02
limit: assistant02
```

The Vagrant rule is:

```text
marker: ai-ops-assistant-mcp-https-ingress
allow: TCP 8443 on eth0 from 192.168.121.0/24 to 192.168.121.21
IPv6: denied
NAT/forwarding: forbidden
```

Rollback is:

1. Revoke or disable client certificate access.
2. Remove only the marker-owned Vagrant ingress rule.
3. Stop and disable `ai-ops-assistant-mcp`.
4. Verify no listener, MCP process, runner child, or orphan remains.
5. Remove only the MCP adapter, catalog, configuration, unit, and dedicated
   venv artifacts.
6. Preserve the revised runner, diagnostics, credentials, audit, evidence, and
   historical runtime.
7. Record a normalized rollback outcome.

## Dependency and Path Contract

The MCP role owns these exact repository paths:

```text
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp/
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp/files/mcp/aiops_assistant_mcp_server.py
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp/files/mcp/mcp_resource_catalog.json
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp/files/mcp/config.json
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp/files/mcp/requirements.in
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp/files/mcp/requirements.lock
ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp/templates/ai-ops-assistant-mcp.service.j2
ansible/ai_ops_assistant/tests/mcp/
ansible/ai_ops_assistant/playbook_deploy_mcp.yml
```

`requirements.in` contains only `mcp==1.28.1`. The lock is generated for Python
3.14 with pip-tools, `--generate-hashes`, and `--strip-extras`, from an approved
internal artifact index or offline wheel directory. The complete transitive
closure is hash-pinned. No historical orchestrator lock or wheelhouse is a
source of deployment authority.

The deployed runtime uses:

```text
venv: /opt/openstack-ai-ops-assistant/mcp/venv
owner/group: root:aiops_assistant
mode: 0750
MCP SDK: 1.28.1
extras: none
runtime package downloads: forbidden
```

## Validation and Evidence Contract

Documentation and static validation for this contract uses:

```bash
rtk git diff --check
rtk rg -n '^##|^###' docs/ai-ops-revised/runtime/mcp-interface-internal-network-operations-contract.md
rtk rg -n '192\.168\.121\.21|8443|client-ca\.crl|mcp-internal-reader|RestrictAddressFamilies|phase07-internal-mcp-https-mtls-0701' docs/ai-ops-revised/runtime/mcp-interface-internal-network-operations-contract.md
```

Future Python validation must use:

```bash
<user defined Python venv>/bin/python
```

No system-Python fallback is permitted. Later local validation must prove:

- exact low-level Streamable HTTP API use and absence of FastMCP convenience
  routes, proxying, public binds, or alternate transports;
- TLS 1.3, certificate EKU/SAN, closed CA, CRL freshness, and fail-closed
  certificate handling;
- exact source CIDR, Host, Origin, method, body, response, rate, idle, and
  concurrency behavior;
- exact three-tool discovery and non-discovery of Phase 06/generic tools;
- registry projection through the fixed runner loader and no duplicated runner
  authority;
- fixed runner argv, no shell, no caller overrides, and no child on denial;
- complete result-envelope/status/truncation equivalence and one runner audit;
- sanitized network event logging and no secret/topology/payload disclosure;
- disabled-by-default deployment, strict ownership/modes, no symlinks, and
  service hardening; and
- shutdown, cancellation, rollback, and listener/process absence.

No validation may issue certificates, install packages, modify firewall state,
start a listener, register a client, invoke a live runner, inspect raw audits,
or contact OpenStack without the separately confirmed approval scope.

## Failure States and Stop Rules

| Failure | Required action |
| --- | --- |
| Wrong interface/address, wildcard, IPv6, or unexpected port | Do not bind; report `network_bind_scope_error`. |
| Missing/unsafe TLS, CA, or CRL material | Do not bind; report `tls_configuration_error`. |
| Invalid/revoked/unknown client certificate | Reject before MCP handling; invoke no runner. |
| Peer outside CIDR or invalid Host/Origin/method | Reject with generic bounded response. |
| Unknown principal/tool/resource or schema drift | Deny before child creation. |
| Oversized/rate/concurrency/idle request | Apply the fixed limit response; do not retry. |
| Runner unavailable, malformed, or timed out | Preserve fail-closed adapter error; do not retry. |
| Raw secret/result/exception reaches logs | Suppress output and stop the affected operation. |
| Missing approval or external client request | Keep service disabled; report authorization blocker. |
| Orphan process or unexpected listener | Stop service and require operator review. |
| Unsafe rollback target or shared-runtime impact | Abort rollback and preserve all shared authority. |

## Current Scope and Next Gate

This contract completes the documentation-only internal-network boundary gate.
It does not claim that the service is implemented, deployed, enabled, reachable,
certificate-backed, or compatible with an external client.

The next implementation chunk may add only a disabled, syntax-safe network
server skeleton after the contract is reviewed. It must not activate a listener,
issue or install certificates, change Vagrant firewall state, register an
external client, invoke the runner, inspect audits, or perform live diagnostics.
