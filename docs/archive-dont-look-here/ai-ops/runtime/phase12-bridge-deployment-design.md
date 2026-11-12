# Phase 12 Bridge Deployment Boundary Design

## Status

**Decision:** design only; deployment remains blocked.

This record defines the local IPC boundary required before an assistant bridge
executor or model-facing proxy can be deployed. It does not authorize a
provider request, egress change, authentication action, approval artifact,
remote-unit activation, or Ansible apply.

## Fixed Ownership and IPC Contract

| Item | Required value | Reason |
| --- | --- | --- |
| Credential-bearing executor identity | `assistant:assistant` | The existing reviewed runner and OpenStack profile remain accessible only under the assistant identity. |
| Model-facing proxy identity | `aiops-orchestrator:aiops-orchestrator` | The proxy remains distinct from the credential-bearing runtime. |
| Bridge socket path | `/run/openstack-ai-ops/assistant-mcp-bridge.sock` | Matches `ASSISTANT_MCP_BRIDGE_SOCKET`; no caller-selected path is accepted. |
| Runtime directory | `/run/openstack-ai-ops`, `root:root`, mode `0755` | Root controls path creation and prevents either service identity from replacing the parent. |
| Socket ownership | `assistant:aiops-orchestrator`, mode `0660` | Only the assistant may serve; the dedicated orchestrator group may connect. No other account may connect through filesystem permissions. |
| Peer authorization | Linux `SO_PEERCRED` UID exactly equal to the deployed `aiops-orchestrator` UID | Filesystem access is necessary but insufficient; `UnixSocketBridge` must reject every other UID before executor dispatch. |
| Protocol | One newline-framed request/response over `AF_UNIX` | The fixed bridge/proxy contract permits one reviewed no-argument tool request and no TCP transport. |

The deployment role must resolve the `aiops-orchestrator` numeric UID after it
creates the dedicated identity and pass that exact value to the assistant-owned
executor. It must not infer peer identity from a caller-supplied group, PID,
path, or request field. The group permits opening the exact socket only; it
must not be used to grant credential-file, runner, Codex-home, or general
assistant-runtime access.

## Lifecycle and Cleanup Contract

A future reviewed deployment may use an assistant-owned systemd socket and
service pair only after an executable bridge-server entrypoint exists and is
locally tested. Both units must be installed as root-owned `0644` files but
remain static, disabled, and stopped after deployment. They must have no
`WantedBy`, timer, restart policy, TCP listener, or remote transport.

1. Render the root-owned runtime directory and socket contract before installing
   the executor unit.
2. Start no bridge unit during ordinary setup; the fake-only orchestrator unit
   remains unchanged, disabled, and stopped.
3. A separately authorized local validation may start the exact socket/service,
   exercise only a fake injected reviewed runner, then stop both units.
4. Teardown stops the socket first, then the executor service, so no new peer
   can connect during cleanup. It verifies that the exact socket is absent and
   that no bridge process remains.
5. Removal is limited to named root-owned unit files and the exact socket path.
   It must not recursively remove `/run/openstack-ai-ops`, inspect credentials,
   or alter the existing assistant stdio MCP adapter.

Executor failure, peer denial, malformed input, timeout, cancellation, or
redaction rejection must close the accepted connection, return no tool content,
and leave no retained bridge child process. The proxy must close its exact
client socket on every terminal path. Neither side may retry a tool call.

## Required Future Deployment Artifacts

The following are design targets, not current deployment artifacts:

- an assistant-owned fixed bridge-server entrypoint that injects the existing
  reviewed runner into `AssistantBridgeExecutor`;
- an assistant bridge socket unit and paired service unit, each hardened and
  static;
- role tasks that create the runtime directory, render units, daemon-reload,
  and assert disabled/stopped state without starting either unit;
- deployment validation that checks owner, group, mode, symlink denial, exact
  peer UID, no TCP/UDP listener delta, credential denial for
  `aiops-orchestrator`, timeout/cleanup, and fixed-tool enforcement;
- a separate, later proxy-deployment slice with an explicit rollback from the
  historical assistant stdio MCP command.

The executor must use the existing reviewed runner path; it must not introduce
a second subprocess, generic command runner, copied credential, ACL on
credential files, sudo rule, setuid helper, or provider-facing client.

## Validation Gate

Before any future deployment change, prove with local fake-only tests that the
assistant executor accepts only the fixed request, verifies the exact
orchestrator peer UID, redacts before the proxy receives a result, times out
and closes cleanly, and introduces no TCP listener. Validate rendered units
with `systemd-analyze verify`, Ansible syntax/lint, and scoped static scans for
unsafe permissions, enablement, restart, network, credential, and subprocess
patterns.

Until those artifacts and tests exist, the decision in
`phase12-sdk-mcp-vendor-blocker-decision.md` remains controlling:
`VENDOR_BLOCKED / MCP_INTERCEPTION_UNSUPPORTED`.
