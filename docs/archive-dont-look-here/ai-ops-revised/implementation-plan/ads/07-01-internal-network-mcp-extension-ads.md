## Architectural Design Specification: Internal Network MCP Extension

**Source:** `docs/ai-ops-revised/implementation-plan/07-mcp-interface.md`, internal-network option B; extension of `07-00-mcp-interface-steps-01-to-04-ads.md`.

**Goal:** Extend the revised MCP boundary so an independently managed external MCP client may reach an internal, authenticated MCP service without deploying or implementing that client in the OpenStack Lab repository. The service must preserve the revised runner as the only diagnostic authority, must not be publicly reachable, and must fail closed on transport, authentication, authorization, registry, resource, or runner uncertainty.

**Relationship to the local ADS:** The local stdio design remains valid as a separate deployment mode. This ADS adds the internal-network mode; it does not silently replace the local contract or permit both modes to share uncontrolled configuration.

---

### I. Overview and Contract

The network mode adds one explicitly bounded service boundary:

```text
external MCP client (out of repository scope)
  -> approved internal network path
  -> TLS/authenticated MCP service
  -> fixed MCP schema and authorization policy
  -> fixed revised runner argv
  -> accepted registry/profile/limits/redaction/audit path
  -> bounded diagnostic result
```

The external client, its package, registration, model/provider, credentials, and client-side logging are out of scope. The repository owns only the internal MCP service, its deployment contract, server-side authentication/authorization, tool/resource policy, and server-side validation.

#### Transport contract

**Decision state:** network transport is approved as a product direction, but the exact MCP wire transport must be frozen in Chunk 0. The preferred candidate is SDK-supported Streamable HTTP over TLS. SSE may be considered only if the approved SDK/client compatibility review requires it. Plain HTTP, unauthenticated HTTP, WebSocket, arbitrary TCP protocols, and public exposure are prohibited.

The frozen contract must specify:

- one exact service scheme, host/interface, and port;
- one exact MCP endpoint path and health/readiness behavior, if any;
- an internal source-network/CIDR allowlist owned outside this repository or represented by an explicit deployment variable;
- TLS certificate, private-key, trust-store, ownership, mode, rotation, and revocation responsibilities;
- connection, request-body, response, idle, header, and concurrent-session bounds;
- whether HTTP proxying is prohibited or limited to named internal reverse-proxy paths; and
- whether the service is disabled by default until deployment and network authorization are separately accepted.

The server must bind only to the approved internal interface. It must never bind `0.0.0.0`, a public address, an unreviewed interface, or a dynamically supplied address. A listener/process check must prove that no unexpected address or port is opened.

#### Authentication and authorization contract

Authentication is a server-side boundary and cannot be inferred from an internal network location. The preferred candidate is mutual TLS with a closed trust store and per-client certificate identity. A bearer-token alternative requires an explicit owner decision, fixed secret-file handling, rotation/revocation, constant-time verification, and a prohibition on query-string or log-visible tokens.

Authentication and authorization are separate checks:

1. TLS proves the peer presents a certificate or other approved credential.
2. The server maps the authenticated identity to a fixed allowlisted MCP principal.
3. The authorization policy permits only the approved initial tool/resource set and request bounds.
4. The server passes only registry-declared public arguments to the fixed runner.
5. Caller-provided actor, profile, target, registry, audit, timeout, output, environment, executable, correlation, or path values are rejected.

No anonymous, wildcard, default-allow, network-only, or client-asserted identity is accepted. Authentication failure, authorization failure, missing trust material, expired credentials, and policy ambiguity all fail closed without runner invocation.

The external client is not deployed by this phase. Its identity and registration are represented only as an owner-managed integration prerequisite; no client secret, certificate, token, or configuration is committed to the repository.

#### Service identity and lifecycle contract

The network service is a distinct revised process and service identity. Proposed values require Chunk 0 confirmation:

```text
role: ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp/
service name: ai-ops-assistant-mcp
runtime user/group: aiops_assistant:aiops_assistant
runtime root: /opt/openstack-ai-ops-assistant/mcp
adapter: /opt/openstack-ai-ops-assistant/mcp/aiops_assistant_mcp_server.py
```

The service must run without root privileges, use a fixed working directory, receive a minimal environment, and have no provider/model/SSH/OpenStack credential variables. A service manager may supervise the process, but automatic restart, readiness, and shutdown behavior must be explicit and bounded. Deployment is default-disabled and independently removable; it must not alter the prior runtime or the revised runner deployment.

#### Runner delegation contract

The network adapter invokes the accepted revised runner with fixed argument-vector execution:

```text
python3 <fixed revised runner path> TOOL_NAME [--arg KEY=VALUE ...]
```

It does not execute diagnostics directly, import diagnostic implementations, accept a caller-selected executable, or create a second registry/profile/limit implementation. The runner remains authoritative for target selection, credentials, timeout, output limit, redaction, result envelope, correlation ID, and tool audit.

The network server may record a separate bounded connection/authentication event, but it must not write a duplicate tool-execution audit event. The audit-origin decision must either preserve the runner's current fixed `local_cli` actor or introduce a separately reviewed fixed non-authorizing network invocation classification. A client-supplied identity never enters the runner.

#### Tool and resource contract

The initial exposed tools remain exactly:

- `project_resource_summary`;
- `server_basic_info`; and
- `server_network_info`.

Phase 06 tools remain non-discoverable unless separately approved for network exposure. Schemas are derived from the accepted registry and must use `additionalProperties: false`, exact required fields, patterns, bounds, defaults, and allowlists.

Resources remain embedded reviewed static content addressed by an exact URI allowlist. No network request may select a filesystem path, URL, directory, glob, audit file, credential file, or dynamic command output.

---

### II. Observed Evidence and Assumptions

#### Observed evidence

- The current Phase 07 plan and ADS define local stdio as the only transport and explicitly prohibit listeners.
- The revised PRD prohibits unauthenticated or publicly reachable network MCP; it does not prohibit a separately authenticated internal service.
- The revised runtime placement contract currently records no inbound MCP listener and only an assistant-to-controller Keystone route.
- The foundation creates `/opt/openstack-ai-ops-assistant/mcp` but installs no MCP service, listener, certificate, firewall rule, or client registration.
- The revised runner has a fixed CLI boundary, fixed registry adjacency, fixed authority mappings, bounded execution, result redaction, and runner-owned audit persistence.
- No revised MCP role, service unit, network policy, certificate contract, or MCP test directory currently exists.
- The historical bridge is excluded because it imports the orchestrator and opens a Unix listener; it is not a network-service reuse candidate.

#### Assumptions requiring confirmation

- The internal service will run on the revised assistant host and will be reachable only through an approved management/internal network path.
- Network exposure is separately authorized from package acquisition, artifact deployment, runner execution, audit inspection, and external-client registration.
- The approved MCP SDK supports the selected network transport without importing provider, egress, or unrelated server frameworks.
- The service can use a dedicated certificate/trust-store path without embedding secrets in Git or client configuration.
- The external client can be validated later using a fixture or owner-provided integration environment; this phase does not implement that client.

#### Chunk 0 decisions required

1. Exact wire transport and SDK API: preferred Streamable HTTP over TLS, or an approved alternative.
2. Exact bind interface, port, endpoint path, internal source allowlist, firewall owner, and DNS/service name if used.
3. TLS mode: mTLS preferred, or another approved authentication mechanism; certificate/trust-store owners, paths, modes, rotation, and revocation.
4. Authenticated-principal to MCP authorization mapping and initial tool/resource permissions.
5. Connection, request, response, header, idle, rate, concurrency, and aggregate-byte limits.
6. Service manager, launch identity, restart policy, readiness/liveness behavior, log sink, retention, and shutdown contract.
7. Runner audit-origin decision and server-side authentication/audit event schema.
8. Exact revised role, adapter, service, test, certificate-reference, and operations-contract paths.
9. Network exposure, package acquisition, artifact deployment, runner invocation, audit inspection, rollback, and external-client registration approvals.

---

### III. Required Technical Dependencies and Imports

- Official Python MCP SDK, exact approved version and dependency closure pending Chunk 0.
- Only the SDK network server API required for the selected transport; do not import HTTP proxy, provider, remote-operation, orchestration, SSH, database, or generic file-serving frameworks.
- Python standard library for bounded configuration, JSON/schema validation, subprocess argument-vector execution, redaction, and lifecycle handling where the SDK does not supply those controls.
- A repository-controlled service/deployment contract with strict ownership and modes.
- Host TLS support and an externally managed certificate/trust-store source. No private key, token, or certificate material is committed to Git.
- Accepted revised runner and registry; no copied historical registry or alternate execution map.

---

### IV. Step-by-Step Procedure / Execution Flow

1. Confirm the accepted Phase 04/06 prerequisites, current revision, historical exclusions, and absence of an existing revised MCP service.
2. Freeze the network transport, bind scope, endpoint, TLS/authentication, principal mapping, limits, service identity, audit-origin, and authorization matrix without creating host state.
3. Add or revise the non-activation operations contract and amend the runtime-placement contract to distinguish authenticated internal MCP from prohibited public/unauthenticated exposure.
4. Add a compile-safe network server skeleton that remains disabled, validates fixed configuration, creates no successful capability surface when trust/auth policy is unresolved, and never invokes the runner.
5. Add fixture tests for bind-scope validation, TLS/auth configuration validation, request-size/concurrency bounds, public-bind rejection, no-auth rejection, and no historical imports.
6. Implement one authenticated fixture request for `project_resource_summary` through the fixed runner boundary. Use a fake runner or injected process fixture; do not contact OpenStack or inspect live audits.
7. Validate the accepted runner envelope and map it to the MCP network response without weakening status, redaction, truncation, correlation, or audit semantics.
8. Extend the same path to `server_basic_info` and `server_network_info`; prove exact schema equivalence and no-child behavior for invalid requests.
9. Add static resource discovery/read through the exact embedded catalog. Reject arbitrary paths, URLs, dynamic reads, and protected content.
10. Add rate limiting, idle/session cancellation, timeout cleanup, response bounds, sanitized protocol logging, graceful shutdown, and bounded restart behavior.
11. Add default-disabled Ansible/service deployment metadata with exact ownership, modes, certificate references, firewall/allowlist references, and non-symlink checks. Do not register or configure the external client.
12. Run static and fixture validation, then stop before host deployment, network changes, certificate issuance, external-client registration, live runner execution, audit inspection, or rollback rehearsal.

---

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| --- | --- | --- | --- |
| Transport selection | SDK lacks the approved network transport or imports prohibited dependencies | Reject the transport and expose no service | `network_transport_approval_error` |
| Bind configuration | Wildcard, public, unexpected, or caller-supplied bind address/port | Fail startup and deployment validation | `network_bind_scope_error` |
| TLS setup | Missing, expired, mismatched, world-readable, or untrusted certificate material | Do not listen or accept requests | `tls_configuration_error` |
| Authentication | Anonymous, malformed, expired, revoked, or unknown peer credential | Return generic unauthorized response; invoke no runner | `authentication_failed` |
| Authorization | Authenticated principal lacks fixed MCP permission or policy is ambiguous | Return generic forbidden response; invoke no runner | `authorization_denied` |
| Request bounds | Oversized headers/body, excessive concurrency, rate, or idle duration | Reject or terminate within fixed bounds | `request_limit_error` |
| Schema | Network request differs from accepted registry schema | Reject before child creation | `schema_equivalence_error` |
| Runner | Fixed runner unavailable, malformed, timed out, or returns invalid envelope | Preserve fail-closed adapter error; do not retry | `runner_unavailable` or `runner_protocol_error` |
| Logging | Credentials, tokens, raw payloads, topology, or result data reach logs | Suppress emission and fail the affected operation | `adapter_redaction_error` |
| Listener lifecycle | Orphaned process, unexpected restart loop, or stale socket remains | Stop service and require operator review | `service_lifecycle_error` |
| Network policy | Firewall/allowlist is absent, broader than approved, or changed unexpectedly | Keep service disabled | `network_authorization_pending` |
| External client | Client registration or compatibility is absent | Keep server-side artifact independently disabled/enabled only by owner decision | `external_client_out_of_scope` |
| Rollback | Service removal could affect runner, diagnostics, credentials, audit, or prior runtime | Remove only exact MCP artifacts after process absence checks | `rollback_scope_error` |

---

### VI. Security, Integrity, Idempotency, and Cleanup

- **Internal is not trusted:** every request requires approved cryptographic authentication and fixed authorization; source-network filtering is defense in depth only.
- **No public exposure:** reject wildcard/public binds, unauthenticated listeners, port forwarding, reverse-proxy drift, and unapproved ingress.
- **TLS integrity:** verify certificate identity, trust chain, expiry, key permissions, revocation/rotation behavior, and no insecure verification bypass.
- **Credential isolation:** keep server private keys and client credentials outside Git and outside MCP request payloads. The adapter never forwards TLS identity, bearer tokens, or arbitrary headers to the runner.
- **Single execution boundary:** every tool request traverses the fixed revised runner; network transport cannot create a second diagnostic path.
- **Deny by default:** tools, resources, principals, methods, routes, headers, and origins are exact allowlists. Unknown capability is absent or rejected.
- **Availability bounds:** cap connections, request/response bytes, request duration, idle time, concurrent runner children, and per-principal rate. Never queue unbounded work.
- **Audit minimum disclosure:** record only bounded authentication/authorization and lifecycle metadata needed for operations; the runner remains the sole tool-audit writer unless an explicit fixed-origin revision is accepted.
- **Cleanup:** cancellation and disconnect terminate/reap only the request's runner child. Shutdown leaves no MCP or runner child and does not remove runner, diagnostics, profiles, audits, evidence, or historical runtime.
- **Rollback:** disable ingress/client access first, stop the exact service, verify listener/process absence, then remove only reviewed MCP artifacts and optional SDK environment.

---

### VII. Validation Strategy

Documentation and contract validation must prove that the network extension is authenticated internal-only, does not expose public/wildcard binds, keeps external-client implementation out of scope, delegates to the revised runner, and preserves the local stdio design as a separate mode.

Required local/fixture checks:

1. Exact transport/API imports are present and prohibited provider, bridge, orchestrator, socket, proxy, and generic file-serving paths are absent.
2. Public bind, wildcard bind, missing TLS, anonymous auth, unknown principal, and missing authorization policy fail closed.
3. Request headers/body, response, timeout, idle, rate, concurrency, and aggregate output bounds are enforced.
4. Discovery equals the approved three-tool registry subset; optional Phase 06 tools remain absent.
5. Valid and invalid fixture requests produce exact runner argv or no child, respectively.
6. Runner result envelopes preserve status, error, truncation, timestamp, correlation, redaction, and audit semantics.
7. Resource reads are exact embedded catalog lookups with no filesystem/network fetch.
8. Service startup/shutdown/cancellation leaves no orphan process and no unexpected listener.
9. Deployment metadata is default-disabled, root-owned where required, strict-mode, non-symlinked, and references no committed secrets.
10. Existing runner tests remain unchanged and pass under their separately approved environment.

Validation must not install packages, issue certificates, change firewall rules, start a listener, register an external client, execute live diagnostics, or inspect raw audits without separate authorization and the user-provided Python environment.

---

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the network service in one pass.

#### Chunk 0: Network Boundary Discovery

- **Goal:** Freeze transport, bind, TLS/authentication, authorization, service, limits, audit, and approval contracts without edits to executable files.
- **Files to read:** this ADS; Phase 07 local ADS and plan; PRD; runtime-placement/foundation contracts; tool-runner contracts; SDK metadata; host service/firewall conventions.
- **Commands:** bounded `rtk find`, `rtk rg`, targeted reads, `rtk git status`, and documentation scans. No package install, network access, certificate issuance, listener, runner, or audit operation.
- **Evidence to confirm:** exact network API, bind/port, TLS owner and paths, principal map, limits, service manager, role paths, audit-origin, and approval matrix.
- **Stop condition:** all network-specific decisions are owner-approved or remain explicit blockers.

#### Chunk 1: Non-Activation Network Operations Contract

- **Goal:** Freeze the authenticated internal-only service contract and preserve local stdio as a separate mode.
- **Files to change:** proposed `docs/ai-ops-revised/runtime/mcp-interface-internal-network-operations-contract.md`; `docs/ai-ops-revised/runtime/runtime-placement-contract.md` only for the deferred internal boundary statement.
- **Symbols to add/change:** transport/bind/TLS/auth tables, principal authorization matrix, limits, lifecycle, audit-origin, deployment/rollback, and approval gates.
- **Implementation shape:** Markdown only; no listener, certificate, firewall, package, client registration, or runner execution.
- **Validation:** targeted security/path scans, Markdown review, `rtk git diff --check`, focused diff.
- **Stop condition:** reviewers can determine every allowed network request and every denied path without implementation ambiguity.

#### Chunk 2: Disabled Network Server Skeleton

- **Goal:** Add a syntax-safe server skeleton that cannot activate without complete fixed configuration and never invokes the runner.
- **Files to change:** proposed MCP adapter source and one lifecycle/configuration test file.
- **Symbols to add/change:** fixed service configuration, transport factory, bind validator, TLS/auth configuration validator, disabled startup path, and bounded shutdown.
- **Implementation shape:** approved SDK network API only; no wildcard bind, anonymous mode, client registration, diagnostic imports, or successful tool discovery.
- **Validation:** Python compile, fixture tests, prohibited-import/bind scans, no-listener-by-default checks.
- **Stop condition:** skeleton is fail-closed and default-disabled.

#### Chunk 3: Authenticated First Tool Slice

- **Goal:** Serve one authenticated fixture request for `project_resource_summary` through the fixed runner subprocess.
- **Files to change:** adapter source and focused first-tool network tests.
- **Symbols to add/change:** principal authorization lookup, request schema validation, fixed runner invocation, bounded envelope decoder, and MCP response mapping.
- **Implementation shape:** fake runner/fixture transport only; no live network, OpenStack call, client registration, or audit inspection.
- **Validation:** exact auth decisions, exact argv, no-child-on-denial, envelope/status/redaction tests.
- **Stop condition:** one approved authenticated path works in fixtures; all other tools remain absent.

#### Chunk 4: Three-Tool and Resource Equivalence

- **Goal:** Add the two remaining initial tools and exact static resources using the same policy and runner boundary.
- **Files to change:** adapter source, resource catalog, and focused equivalence/resource tests.
- **Symbols to add/change:** registry projector, three-tool exposure policy, resource catalog loader/list/read, and invalid-request handling.
- **Implementation shape:** no optional Phase 06 exposure; no arbitrary file/network reads; no duplicated execution authority.
- **Validation:** schema fixtures, negative capability, resource canaries, bounds, and runner equivalence tests.
- **Stop condition:** network discovery equals the approved registry subset and resource access is exact/closed.

#### Chunk 5: Service Hardening and Deployment Contract

- **Goal:** Add bounded lifecycle, rate/concurrency limits, sanitized logging, default-disabled service metadata, and rollback checks.
- **Files to change:** adapter source/tests plus proposed MCP role/defaults/tasks/playbook and service contract fixtures.
- **Symbols to add/change:** shutdown/reap helpers, rate/idle limits, deployment metadata, service hardening, ownership/mode checks, and listener validation.
- **Implementation shape:** no certificate issuance, firewall mutation, external-client registration, live runner call, or audit inspection.
- **Validation:** Python/Ansible syntax, static service/listener checks, idempotency fixtures, diff/security review.
- **Stop condition:** artifacts are statically deployable and independently disableable, or a concrete blocker is recorded.

---

### IX. Handoff to `chunked-implementation`

Recommended execution sequence:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, pre-edit-discipline, and post-edit-discipline.

Task:
Extend Phase 07 with the internal authenticated network MCP service described by
07-01-internal-network-mcp-extension-ads.md.

Mode:
Execute Chunk 0 only. Do not edit executable files. Resolve or record the
transport, bind, TLS/authentication, authorization, limits, lifecycle, audit,
and approval decisions, then stop.
```

After Chunk 0 acceptance, execute one chunk at a time and stop after each chunk. External-client implementation, registration, certificate issuance, firewall changes, host deployment, live runner calls, raw audit inspection, and rollback rehearsal remain separately authorized work.

---

### X. Conclusion and Next Steps

Option B is now represented as an internal authenticated service extension rather than an external-client implementation. The next safe action is Chunk 0 discovery and owner decision capture. Until the network contract is frozen, the service must remain absent or disabled, and the original local stdio implementation must not be broadened implicitly.
