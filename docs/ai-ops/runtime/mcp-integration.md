# Local MCP Integration Runbook

## Purpose

This runbook defines safe enablement, validation, disablement, and rollback for the OpenStack AI-OPS MCP interface on `assistant01`. The interface exposes reviewed read-only diagnostics through one local stdio child process per AI-client session.

MCP is an interface layer, not a new safety boundary. Every tool call delegates to the existing local runner, which retains registry validation, fixed credentials, timeout and output bounds, structured envelopes, and audit ownership.

## Reviewed Boundary

The default deployed policy exposes exactly these low-risk tools:

- `project_resource_summary`
- `server_basic_info`
- `server_network_info`

It also exposes three fixed curated resources and three diagnostic-only prompts. Restricted-host tools remain disabled by default. Generic command execution, arbitrary file reads, remediation, services, listeners, HTTP, SSE, WebSocket, and remote MCP transport are not part of this phase.

The fixed launch command is:

```text
/opt/openstack-ai-ops/.venv/bin/python /opt/openstack-ai-ops/mcp/aiops_mcp_server.py
```

The process must run as `assistant`. Do not run it as root, wrap it in a shell command, substitute caller-controlled paths, or grant it additional credentials.

## Preconditions

Before enabling a client, confirm:

1. The assistant runtime role has deployed the MCP adapter, policy, resources, and pinned `mcp==1.28.1` package.
2. The adapter and its directories are owned by `assistant:assistant`; directories and the adapter use `0755`, while policy and resources use `0644`.
3. `/opt/openstack-ai-ops/scripts/tool_runner/aiops_tool_runner.py` and its reviewed registry remain available.
4. The local read-only OpenStack profile is valid for the approved project scope.
5. The policy exposes only the expected low-risk tools and `low_readonly_project_scope`.
6. No restricted-host exposure has been separately enabled.

Do not run the broad assistant setup playbook casually. It includes common host management and credential-profile tasks in addition to MCP deployment. Review its task boundary and obtain explicit approval before changing `assistant01`.

## Enable an AI Client

Configure the selected AI client to launch the fixed command directly over stdio as the `assistant` account. Use a command-and-arguments form rather than a shell string:

```json
{
  "command": "/opt/openstack-ai-ops/.venv/bin/python",
  "args": [
    "/opt/openstack-ai-ops/mcp/aiops_mcp_server.py"
  ]
}
```

Apply this configuration only in the local client context on `assistant01`. Do not commit client-specific configuration, credentials, environment dumps, prompt history, or diagnostic payloads to this repository.

A client session starts one adapter child process. Closing or disabling that client entry must end the adapter process. There is no MCP service to start, enable, expose, or restart.

## Runtime Validation

Run the repository validation playbook only after the MCP artifacts are deployed and a project-visible server identifier has been reviewed:

```bash
rtk ansible-playbook \
  -i ansible/ai_ops_runtime/inventories/local/local.yml \
  ansible/ai_ops_runtime/playbook_validate_phase07_mcp_integration.yml \
  -e ai_ops_mcp_validation_server_identifier=control_plane_vm01
```

The playbook performs these checks without retaining raw payloads or audit lines:

- deployed path type, ownership, group, mode, and symlink state;
- Python, JSON, and pinned SDK checks;
- exact tool, resource, and prompt discovery;
- closed input schemas and default restricted-host denial;
- curated resource and diagnostic-prompt assertions;
- successful low-risk calls and invalid/unknown negative cases;
- structured result and request-ID preservation;
- fixed `client_id=local-mcp-client` and `transport=stdio` audit correlation;
- no newly created network listener;
- adapter exit after the stdio client disconnects.

The temporary validation client is removed after execution. Treat any missing artifact, unexpected exposure, failed negative case, uncorrelated request ID, new listener, or surviving adapter process as a failed validation. Do not broaden policy or bypass the runner to make validation pass.

## Operating Procedure

1. Discover tools, resources, and prompts before making a call.
2. Confirm the discovered tool is in the reviewed policy.
3. Call low-risk project diagnostics first.
4. Preserve `tool`, `status`, `arguments`, `duration_ms`, `truncated`, `timestamp`, and `request_id` from each structured envelope.
5. Correlate the request ID with sanitized runner audit metadata.
6. Treat `validation_error`, `timeout`, `unavailable`, `error`, and `truncated` as explicit outcomes or evidence gaps.
7. Explain evidence and uncertainty; recommend manual operator follow-up only.

Never record raw diagnostic output, raw audit events, cloud-profile contents, credentials, keys, tokens, passwords, prompt history, or secret-bearing configuration in repository evidence.

## Failure Handling

- **Adapter cannot start:** disable the client entry and verify the fixed files/package; do not fall back to another interpreter or path.
- **Discovery differs:** disable the client entry and inspect the deployed policy/registry drift; do not accept extra tools.
- **Invalid call succeeds:** stop using MCP and preserve only sanitized request metadata for review.
- **Call lacks an audit event:** stop using MCP; the runner audit boundary is not proven.
- **Listener appears:** terminate the client session and treat this as a security failure.
- **Adapter survives disconnect:** terminate only the adapter-owned process and investigate client lifecycle handling.
- **Result is unavailable, timed out, errored, or truncated:** retain status and request ID, report the evidence gap, and do not retry automatically.

## Disable

1. Remove or disable the local AI-client MCP command entry.
2. Close the client session and its stdio streams.
3. Confirm no adapter process remains.
4. Confirm no network listener was introduced.
5. Leave the manual runner, read-only credential profile, and audit records intact.

Disabling the client entry is the normal rollback because deployed MCP files are inert without a local stdio client launching them. It does not modify OpenStack resources or services.

## Repository-Managed Rollback

If inert files must also be removed:

1. Disable the client entry first and confirm the adapter has exited.
2. Prepare and review an Ansible change that removes only the MCP adapter, policy, curated resources, empty MCP directories, and optional MCP SDK dependency.
3. Preserve the manual runner, registry, approved scripts, credential profile, diagnostics, and audit records.
4. Syntax-check and review the removal change before obtaining approval to apply it to `assistant01`.
5. Validate that manual runner diagnostics still work after removal.

The current assistant role installs MCP artifacts but does not provide a dedicated removal toggle. Do not manually delete files or run the broad setup playbook as an improvised rollback. Full artifact removal requires a separately reviewed repository-managed change.

Rollback must never revoke unrelated read-only credentials, alter observer access, restart OpenStack services, mutate lab resources, delete audit history, or begin remote MCP exposure.
