# AI-OPS Assistant Runtime Foundation

This document records the Phase 01 runtime boundary for the read-only AI-OPS assistant.

Phase 01 does not install OpenStack credentials, expose AI-controlled shell access, or add remediation automation. It only establishes where the assistant tooling will live and how the workspace should be organized.

## Placement Decision

Recorded on 2026-07-02:

- Phase 01 uses a manually designated assistant runtime outside the OpenStack control plane.
- Preferred host class: a small VM on the lab hypervisor or another routed management host.
- Management path: the `192.168.121.0/24` management network to `controller01` APIs.
- `assistant01` remains optional for later repository-managed automation and is not required for Phase 01.

## Runtime Placement

Reference placement for the first implementation:

```text
assistant01 separate VM or equivalent isolated host
  -> reachable to OpenStack management APIs
  -> not a controller, compute, storage, Ceph, database, message-bus, or observability service node
  -> no privileged OpenStack, SSH, database, RabbitMQ, or service credentials installed
```

Recommended lab placement:

- Run the assistant runtime outside the OpenStack control plane.
- Prefer a small VM on the lab hypervisor or another routed management host.
- Attach or route it to the management path that can reach `controller01` OpenStack APIs.
- Do not place it on `controller01`, `compute01`, `compute02`, `storage01`, or `ceph01`.
- Do not make tenant-network access a Phase 01 requirement.

The existing lab network model is:

| Network | CIDR | Phase 01 use |
| ------- | ---- | ------------ |
| Management | `192.168.121.0/24` | Required for Keystone/controller API reachability. |
| Provider | `192.168.123.0/24` | Not required for the first AI-OPS milestone. |
| Vagrant private SSH convenience | `192.168.124.0/24` | Optional operator access path only, not an AI tool boundary. |

Expected first management endpoints:

| Endpoint | Expected location | Purpose |
| -------- | ----------------- | ------- |
| Keystone | `controller01:5000` | Identity API reachability check. |
| Nova API | `controller01:8774` | Future server diagnostics. |
| Neutron API | `controller01:9696` | Future network diagnostics. |
| Cinder API | `controller01:8776` | Future volume diagnostics. |
| Placement API | `controller01:8778` | Future scheduler/resource diagnostics. |

## Workspace Layout

Create this workspace on the assistant runtime:

```text
/opt/openstack-ai-ops/
  README.md
  scripts/
    approved/
  diagnostics/
    raw/
    summaries/
  runbooks/
  credentials/
    profiles/
  audit/
  mcp/
```

Directory intent:

| Path | Purpose | Phase 01 rule |
| ---- | ------- | ------------- |
| `scripts/approved/` | Reviewed read-only diagnostic scripts. | May exist empty until Phase 03. |
| `diagnostics/raw/` | Raw command/script output captured by the operator or tool runner. | Writable by runtime user. |
| `diagnostics/summaries/` | Human/AI-readable summaries derived from raw results. | Writable by runtime user. |
| `runbooks/` | Manual diagnostic workflow notes. | Documentation only in Phase 01. |
| `credentials/profiles/` | Future dedicated read-only credential profiles. | Must remain empty until Phase 02. |
| `audit/` | Future tool-runner audit events. | Writable by runtime user; may be empty until Phase 04. |
| `mcp/` | Future MCP server/interface code. | Must remain inactive until trusted scripts and runner exist. |

## Baseline Tooling Target

Phase 01 runtime tooling should support later diagnostics but should not add authority.

Target tools:

- Python 3 runtime
- Python virtual environment support
- package tooling for an isolated virtual environment
- OpenStack CLI
- OpenStack SDK
- SSH client for operator access only
- curl or equivalent HTTP client
- JSON parser
- fast text search
- Git client

Version evidence should be recorded in the runtime-local `README.md` or a dated note under `diagnostics/summaries/` after the runtime exists.

## Prohibited Runtime Capabilities

The assistant runtime must not contain or expose:

- admin OpenStack credentials
- root SSH keys for OpenStack nodes
- unrestricted sudo for OpenStack nodes
- database credentials
- RabbitMQ credentials
- service configuration secrets
- generic shell execution as an AI tool
- generic SSH execution as an AI tool
- generic OpenStack CLI passthrough as an AI tool
- file-write, package-install, service-restart, database, or remediation tools for AI use

Operators may administer the runtime manually. AI-facing tools must remain deny-by-default and explicitly allowlisted in later phases.

## Phase 01 Verification Checklist

Record the actual evidence before checking Phase 01 complete:

- [ ] Runtime exists or is explicitly designated.
- [ ] Runtime is not an OpenStack controller, compute, storage, Ceph, database, message-bus, or observability service node.
- [ ] Runtime can resolve or reach the Keystone endpoint on the management path.
- [ ] Runtime can reach the controller management address.
- [ ] Runtime does not require tenant-network access for the first milestone.
- [ ] Baseline tool versions are recorded.
- [ ] Workspace directories exist and are writable by the runtime user where required.
- [ ] `credentials/profiles/` exists but contains no credentials until Phase 02.
- [ ] No privileged OpenStack, SSH, database, RabbitMQ, or service credentials are installed.

## Rollback

Phase 01 rollback is intentionally simple:

1. Disconnect the assistant runtime from the management path, or destroy the VM/host.
2. Remove `/opt/openstack-ai-ops/` from the runtime if it was created.
3. Confirm no AI-OPS credentials were created in Phase 01.

If credentials already exist, treat rollback as a Phase 02 credential revocation task instead.
