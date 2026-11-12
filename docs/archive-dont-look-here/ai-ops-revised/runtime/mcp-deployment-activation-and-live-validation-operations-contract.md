# Revised AI-OPS MCP Deployment, Activation, and Live-Validation Operations Contract

## Status and authority

This is the Chunk 0 decision and evidence contract for the Phase 07-X01 MCP
deployment/activation extension. It records repository evidence and unresolved
owner decisions before executable implementation. It does **not** authorize
package acquisition, dependency installation, host contact, TLS or credential
handling, firewall mutation, process or listener startup, runner/OpenStack
calls, client registration, audit inspection, disablement, or rollback.

It is subordinate to:

- `docs/ai-ops-revised/implementation-plan/07-x01-mcp-deployment-activation-and-live-validation.md`;
- `docs/ai-ops-revised/implementation-plan/ads/07-x01-mcp-deployment-activation-steps-01-to-05-ads.md`;
- `docs/ai-ops-revised/runtime/mcp-interface-steps-01-to-04-operations-contract.md`;
- `docs/ai-ops-revised/runtime/mcp-interface-steps-05-to-07-operations-contract.md`;
- `docs/ai-ops-revised/runtime/mcp-interface-internal-network-operations-contract.md`;
- `docs/ai-ops-revised/runtime/mvp-live-validation-and-rollback-operations-contract.md`; and
- `docs/ai-ops-revised/runtime/phase06-live-acceptance-readiness-requirement.md`.

The local-stdio and authenticated internal-network modes remain separate
namespaces and lifecycles. Repository defaults remain false.

## Decision status

A value marked **confirmed design input** is copied from an existing operations
contract and is not evidence that host state, approval, or protected material
exists. A value marked **blocked** cannot be supplied by inference or a
placeholder. Any blocked decision required by a later chunk keeps that chunk
stopped.

| Decision | Status | Repository evidence or required owner input |
| --- | --- | --- |
| Target host/group | Confirmed design input | `assistant02` in `ai_ops_assistant`; both MCP playbooks assert the exact host and limit. |
| Mode order | Confirmed design input | Local stdio first; Option B only after local runner equivalence. |
| Local-stdio lifecycle | Confirmed design input | Owner-managed client process; no service, listener, or persistent registration. |
| Option B lifecycle | Confirmed design input | `ai-ops-assistant-mcp` under systemd, initially stopped and disabled. |
| Runtime roots and identities | Confirmed design input | Local stdio `/opt/openstack-ai-ops-assistant/mcp-stdio`; Option B `/opt/openstack-ai-ops-assistant/mcp`; runtime identity `aiops_assistant:aiops_assistant`. |
| Option B network scope | Confirmed design input | `eth0`, `192.168.121.21:8443`, `/mcp`, source `192.168.121.0/24`, TLS 1.3, mandatory mTLS. |
| Option B principal | Confirmed design input | URI SAN `spiffe://openstack-lab/mcp/mcp-internal-reader` maps only to `mcp-internal-reader`. |
| Firewall ownership | Partially confirmed; activation blocked | Vagrant owns marker `ai-ops-assistant-mcp-https-ingress`; the repository does not contain the owning automation path or an accepted marker-evidence interface. |
| Approval reference | Design input; verification blocked | `phase07-internal-mcp-https-mtls-0701` is owner-supplied in the internal-network contract; current approval scope, issuer, expiry, and verification interface are absent. |
| Python executable/version/ABI | Blocked | Inventory does not freeze the approved interpreter. Host inspection is prohibited in Chunk 0; owner must provide non-secret interpreter, version, ABI, platform tag, and wheel compatibility evidence. |
| Dependency source/closure | Blocked | Both `requirements.lock` files are absent. Owner must provide approved source, provenance, license review, complete hashes, closure, wheel-storage/transfer path, and decide whether modes share a closure. |
| Accepted runner revision/readiness | Blocked | Fixed runner path and audit path are documented, but an accepted revision/hash and current readiness evidence for MCP are not recorded. |
| MCP SDK request/lifespan/auth seam | Blocked | `mcp==1.28.1` is the required version and existing factories are documented; exact Streamable HTTP signatures and validated TLS client-certificate access must be confirmed against the approved environment. |
| Local smoke client | Partially confirmed; implementation blocked | Owner-managed client label is `owner-managed-local-stdio-client-v1`; exact implementation/API, support-path location, and outcome-only evidence procedure require owner confirmation. |
| Option B resource catalog | Blocked | Local stdio has six accepted resources; Option B currently exposes three. Owner must approve the exact six-resource set, URI order, and content ownership. |
| Normalized MCP evidence | Partially confirmed; retention blocked | Existing runner and network lifecycle schemas provide conventions. MCP-specific fields, protected destination, retention, deletion owner, and raw-data prohibition require explicit acceptance below. |
| Stop authority/triggers | Partially confirmed; exact triggers blocked | Security or senior lab administrator is the emergency revocation owner and platform operations owns rollback in existing contracts; exact MCP stop authority and automatic disablement triggers remain unconfirmed. |
| Activation control | Blocked | The root-controlled non-secret artifact path, closed schema, ownership, mode, freshness, one-run binding, consumption, and deletion behavior are not yet approved. |
| Protected TLS source | Partially confirmed; materialization blocked | Destination paths and metadata are documented; external CA/platform ownership is documented, but the protected source and Ansible materialization mechanism, `no_log` boundary, and cleanup contract are absent. |

## Authority matrix

Approvals are independent. One approval never authorizes another side effect.
Until the required row is approved and its evidence is current, the operation
remains unavailable.

| Scope | Required authority | Minimum non-secret evidence | Status |
| --- | --- | --- | --- |
| Contract/static review | Phase 07 maintainer/reviewer | Reviewable contract diff and static checks | Permitted for this chunk |
| Python ABI selection | Platform operations / lab administrator | Actual `assistant02` interpreter and compatibility record | Blocked |
| Dependency artifacts | Platform operations / lab administrator | Source, provenance, licenses, hashes, closure, ABI compatibility, protected artifact reference | Blocked |
| Local artifact deployment | Platform operations / lab administrator | Exact target/limit, accepted dependencies, explicit opt-in, rollback owner | Blocked |
| Option B artifact deployment | Platform operations / lab administrator | Exact target/limit, accepted dependencies/TLS inputs, explicit opt-in, rollback owner | Blocked |
| Firewall mutation/evidence | Vagrant/firewall owner | Owning automation result or accepted marker-scoped evidence | Blocked |
| Local smoke process | Owner-managed client operator | Exact client contract, bounded cases, cleanup and evidence procedure | Blocked |
| Runner execution | Diagnostic operator | Accepted runner revision, readiness, protected prerequisites, current run ID | Blocked |
| Live MCP activation | Named activation owner | Current approval, explicit confirmation, current-run preflight, exact target | Blocked |
| Live validation | Diagnostic/operator owner | Approved client, source scope, test identity, runner/evidence approvals | Blocked |
| Audit inspection | Audit owner | Minimum matching-event scope, fixed access path, retention and deletion | Blocked |
| Outcome-only evidence | OpenStack platform operations / lab administrator | Protected destination, schema, retention, deletion owner | Blocked |
| Disablement | Activation owner or delegated platform operator | Separate current authorization and stop criteria | Blocked |
| Rollback | OpenStack platform operations; security escalation for credentials | Exact owned-artifact manifest and replacement/recovery plan | Blocked |
| Emergency revocation | OpenStack security or senior lab administrator | Trigger, revocation procedure, normalized outcome reference | Partially confirmed |

## Frozen non-secret deployment values

These values are accepted as design inputs from the existing contracts. They do
not authorize their materialization or prove that they exist on `assistant02`.

### Local stdio

```text
client label: owner-managed-local-stdio-client-v1
runtime root: /opt/openstack-ai-ops-assistant/mcp-stdio
adapter: /opt/openstack-ai-ops-assistant/mcp-stdio/aiops_assistant_mcp_stdio_server.py
catalog: /opt/openstack-ai-ops-assistant/mcp-stdio/mcp_resource_catalog.json
configuration: /etc/ai-ops-assistant/mcp-stdio/config.json
venv: /opt/openstack-ai-ops-assistant/mcp-stdio/venv
user/group: aiops_assistant:aiops_assistant
transport: stdin/stdout only
required SDK: mcp==1.28.1, no extras
```

The local surface is exactly three tools, six resources, and three prompts. The
adapter stdout is reserved for MCP frames. Client registration is external and
separately approved.

### Authenticated internal-network Option B

```text
service: ai-ops-assistant-mcp
unit: /etc/systemd/system/ai-ops-assistant-mcp.service
runtime root: /opt/openstack-ai-ops-assistant/mcp
adapter: /opt/openstack-ai-ops-assistant/mcp/aiops_assistant_mcp_server.py
catalog: /opt/openstack-ai-ops-assistant/mcp/mcp_resource_catalog.json
configuration: /etc/ai-ops-assistant/mcp/config.json
venv: /opt/openstack-ai-ops-assistant/mcp/venv
user/group: aiops_assistant:aiops_assistant
interface: eth0
address: 192.168.121.21
port: 8443
endpoint: /mcp
source CIDR: 192.168.121.0/24
transport: Streamable HTTP over TLS 1.3
principal: mcp-internal-reader
```

The Option B surface is exactly three tools, six owner-approved resources, and
no prompts. The six-resource catalog is not frozen until the owner resolves the
current three-versus-six discrepancy.

TLS destination metadata is fixed by the existing internal-network contract:
`/etc/ai-ops-assistant/mcp/tls/{server.crt,server.key,client-ca.crt,client-ca.crl}`
owned by `root:aiops_assistant` with mode `0640`, under a directory owned by
`root:aiops_assistant` with mode `0750`. These are destination constraints only;
no TLS material may be generated, copied, or inspected in this chunk.

## Normalized evidence contract

No live evidence is collected by this chunk. When separately authorized, the
MCP evidence record may retain only normalized, non-secret outcome fields:

```text
schema_version
run_id
source_revision
mode
operation
host_label
service_state
listener_state
transport_state
authentication_outcome
authorization_outcome
capability_surface_outcome
tool
status
exit_code
correlation_id
duration_ms
timestamp
truncated
redaction_check
runner_equivalence_check
audit_pair_check
limitation_class
rollback_outcome
```

The exact field types, allowed values, protected destination, retention period,
delete owner, evidence reference format, and whether `host_label` is retained
are **blocked owner decisions**. Until accepted, automation must not create an
MCP evidence file or report live readiness.

The following are always prohibited from retained evidence, protocol output,
normal logs, and task output:

- credentials, private keys, certificates, certificate subjects, tokens, and
  authorization values;
- raw requests, headers, bodies, tool results, prompts, stdout, stderr,
  exceptions, audit lines, and client identity details;
- server identifiers, source addresses, topology payloads, dynamic paths, and
  protected inventory unless a later owner-approved schema explicitly permits a
  non-sensitive label; and
- claims of deployment, activation, listener state, runner equivalence, audit
  correlation, or rollback without current normalized evidence.

Sensitive Ansible tasks must use `no_log`. Failure, absence, staleness, unsafe
metadata, or evidence-policy violation fails closed and retains only a bounded
limitation class.

## Activation-state contract

Activation remains impossible by repository default. No deployment task may
start or enable the service, create a listener, add a firewall rule, or imply
client registration.

A later activation operation must require all of the following, validated for
the same current run:

1. exact target `assistant02` and `--limit assistant02`;
2. accepted runner revision/readiness;
3. accepted dependency closure for the actual host ABI;
4. accepted TLS metadata/material and current CRL;
5. accepted firewall-owner evidence;
6. accepted rollback manifest and stop authority;
7. exact current approval reference and explicit activation confirmation; and
8. a root-controlled, non-secret, default-absent activation artifact.

The activation artifact contract is currently blocked. Its path, closed schema,
owner, mode, freshness, one-run binding, consumption, and deletion behavior
must be supplied before executable activation code is written. A missing or
invalid artifact must produce a deterministic activation denial; it must never
fall back to a source constant or caller-provided path.

The intended state boundary is:

```text
UNREADY
  -> READY_FOR_DISABLED_DEPLOYMENT
  -> LOCAL_DEPLOYED_NO_PROCESS
  -> LOCAL_SMOKE_ACTIVE
  -> LOCAL_DEPLOYED_NO_PROCESS
  -> OPTION_B_DEPLOYED_DISABLED
  -> OPTION_B_ACTIVATION_READY
  -> OPTION_B_ACTIVE
  -> OPTION_B_DEPLOYED_DISABLED
  -> OPTION_B_ABSENT
```

A failed preflight, stale approval, changed revision, missing protected input,
unexpected listener, unsafe ownership/mode, or failed cleanup cannot be reused
as activation evidence for another run.

## Stop and rollback rules

The exact MCP stop authority and automatic trigger set remain blocked. Pending
owner confirmation, the safe default is to stop and escalate on any of:

- target, limit, revision, ABI, dependency, TLS, CRL, principal, source scope,
  firewall, service identity, or activation mismatch;
- an unexpected listener, process, child, route, firewall rule, or shared-path
  mutation;
- authentication, authorization, request-bound, redaction, runner-equivalence,
  evidence, audit-pair, or shutdown failure;
- a secret, raw payload, identifier, address, or protected value reaching an
  unauthorized sink; or
- inability to prove disablement, process/listener absence, or exact rollback
  scope.

No automatic rollback is authorized by this contract. A later rollback must
first revoke or disable client access, remove only the marker-owned firewall
rule through Vagrant ownership, stop and disable only `ai-ops-assistant-mcp`,
verify process/listener/child absence, and remove only exact MCP-owned artifacts.
It must preserve the revised runner, diagnostics, credentials, audit/evidence
paths, local-stdio mode, manual runner workflow, and historical runtime.

## Chunk 0 blockers and next decisions

Chunk 0 is complete only as a documentation boundary; executable chunks remain
blocked until the following owner inputs are recorded:

1. actual approved `assistant02` Python executable/version/ABI/platform tags;
2. shared versus separate local/Option B dependency closures;
3. dependency source, provenance, license, hash, storage, and transfer process;
4. named owners and current approval references for every authority-matrix row;
5. final MCP evidence schema, location, retention, and deletion policy;
6. exact stop authority and disablement/rollback triggers;
7. activation artifact contract;
8. protected TLS source/materialization/cleanup mechanism;
9. Vagrant firewall automation or marker-evidence interface;
10. SDK 1.28.1 request/lifespan/TLS-principal integration seam;
11. local smoke-client API, location, and normalized outcome procedure;
12. accepted runner revision/hash and readiness evidence; and
13. exact Option B six-resource catalog and ownership.

Until these are resolved, the correct outcomes are `contract_blocked`,
`dependency_closure_rejected`, or `activation_denied` as applicable. No
placeholder lock, wheel, TLS input, credential, activation default, live
entrypoint, or resource definition may be added to bypass a blocker.

## Validation performed for this contract

The contract was created after targeted inspection of the extension plan, ADS,
three Phase 07 MCP contracts, the readiness requirement, MCP defaults/tasks,
MCP deployment playbooks, inventory, and existing runner/readiness paths.
Validation for this documentation-only chunk is:

```bash
rtk git diff --check
rtk grep -nE '^##|^###' docs/ai-ops-revised/runtime/mcp-deployment-activation-and-live-validation-operations-contract.md
rtk grep -nE 'assistant02|mcp==1\.28\.1|192\.168\.121\.21|8443|/mcp|ai-ops-assistant-mcp|activation|rollback|no_log' \
  docs/ai-ops-revised/runtime/mcp-deployment-activation-and-live-validation-operations-contract.md
```

These checks do not constitute deployment, host, dependency, TLS, firewall,
listener, runner, audit, or rollback evidence.
