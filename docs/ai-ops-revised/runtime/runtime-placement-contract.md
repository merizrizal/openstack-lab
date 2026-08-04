# Revised AI-OPS Runtime Placement and Namespace Contract

## Status and Authority

This is a Phase 01 planning contract. It records the isolated placement and namespace required before a minimal revised foundation can be implemented. It does not create inventory, provision a VM, configure a route, install software, create credentials, or start a process.

The revised product remains limited to:

```text
reviewed manual diagnostics -> one deny-by-default runner/registry -> local stdio MCP over that runner
```

## Placement Contract

| Concern | Contract |
| --- | --- |
| Placement | A separate VM or equivalent isolated observer host. |
| Host identity | `assistant02`. |
| Historical separation | Must not replace, alter, or share the historical `assistant01` runtime. |
| OpenStack role | Must have no controller, compute, storage, Ceph, database, message-bus, observability, or other control-plane role. |
| Network location | Management-path placement only; tenant-network placement is not required. |
| Initial purpose | Workspace/tooling foundation and later project-level diagnostic support; no diagnostic authority, runner, or MCP process in this slice. |

The final inventory declaration and host existence are Phase 01 Step 4 work. Protected inventory values were deliberately not read while recording this contract.

## Distinct Namespace and Ownership

| Concern | Historical value | Revised contract |
| --- | --- | --- |
| Repository root | `ansible/ai_ops_runtime/` | `ansible/ai_ops_assistant/` |
| Active inventory group | `assistant` | `ai_ops_assistant` |
| Host | `assistant01` | `assistant02` |
| Runtime root | `/opt/openstack-ai-ops` | `/opt/openstack-ai-ops-assistant` |
| Runtime user/group | `assistant` | `aiops_assistant` |
| Project-reader profile | `aiops-project-reader` | `aiops-assistant-project-reader` |
| Audit root | `/opt/openstack-ai-ops/audit` | `/opt/openstack-ai-ops-assistant/audit` |
| MCP registration | Historical registration | Separately named local stdio registration |

The `aiops_assistant` account and group own only revised runtime-managed workspace, approved future diagnostic files, and revised audit locations. Credential material and raw audit evidence remain outside committed source and have separate restrictive-permission requirements.

## Initial Network Boundary

| Direction | Contract | Status |
| --- | --- | --- |
| `assistant02` to `controller01:5000` | Management-path TCP reachability to Keystone only. | Required before Phase 01 Step 4 acceptance. |
| Keystone authentication | No credential installation or authentication in this slice. | Deferred to Phase 02. |
| Additional OpenStack APIs | Require an accepted diagnostic and an explicit route justification. | Denied until justified. |
| Tenant network | No placement or route requirement. | Denied/unneeded. |
| Provider or model egress | No route or policy configuration. | Excluded. |
| Inbound/public MCP | No listener, port, or public exposure. | Excluded. |
| Historical runner/MCP/orchestrator paths | No invocation, route, or registration. | Excluded. |
| Host SSH diagnostics | No route or authorization in the initial foundation. | Deferred to Phase 06. |

The intended first route is:

```text
assistant02 -> management network -> controller01:5000 (Keystone)
```

No network command or host operation is authorized by this document.

## Collision and Isolation Evidence

Repository evidence establishes the following historical identifiers:

- `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml` declares `/opt/openstack-ai-ops` and `aiops-project-reader`.
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/main.yml` constrains the historical runtime to `assistant01` in the `assistant` group.
- Historical MCP, runner, host-observer, provider, and orchestrator paths use the historical runtime root and/or `assistant01`.

The revised identifiers above differ from each observed historical identifier. The revised scaffold exists separately at `ansible/ai_ops_assistant/`; no implementation or inventory diff exists under the protected paths during this contract step.

The following collision checks remain mandatory before implementation acceptance because inventory values were not inspected:

1. Confirm `assistant02` is not assigned any control-plane role and is distinct from `assistant01`.
2. Confirm `ai_ops_assistant` is a unique inventory group and contains only the revised observer host.
3. Confirm the revised runtime root, user/group, credential-profile name, audit root, and local MCP registration do not exist in historical runtime configuration.
4. Confirm no prior or revised listener, service, credential, key, or audit path is reused.

A collision blocks foundation deployment until a new distinct identifier is approved and this contract is updated.

## Step 4 Verification and Rollback

After the host and minimal foundation are explicitly approved, verification must record only redacted evidence that:

1. the revised host identity and inventory group resolve to the intended separate observer host;
2. no control-plane role is present;
3. TCP reachability to `controller01:5000` succeeds from the revised host without installing credentials or starting an MCP listener; and
4. denied routes and excluded capabilities remain absent.

The only rollback for this planning record is to revert this documentation. Once implementation begins, rollback must disconnect or destroy only the revised runtime and remove revised repository-managed state; it must not alter `assistant01`, the historical source, or OpenStack resources.

## Non-Activation Record

This contract introduces no executable automation, inventory mutation, host provisioning, credential, route, firewall, service, listener, diagnostic, runner, MCP, provider, orchestrator, egress, device-auth, wheelhouse, or remote-operation capability.
