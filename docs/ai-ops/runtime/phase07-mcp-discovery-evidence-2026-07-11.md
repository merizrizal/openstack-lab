# Phase 07 MCP Discovery Record

Repository record for Phase 07 MCP Integration discovery on 2026-07-11. This is a design and compatibility record, not runtime deployment evidence.

## Scope and Evidence Policy

- Completed scope: Chunk 0 discovery only; no Phase 07 MCP artifact, dependency, policy, service, listener, client configuration, or runtime deployment was created.
- Repository evidence was taken from the Phase 07 ADS and plan, the deployed-role defaults/tasks, the reviewed runner and registry, the restricted-host runbook, and an isolated local SDK probe.
- The probe used temporary files and a temporary virtual environment only; both were removed after validation.
- This record retains API names, package/protocol versions, and sanitized probe outcomes only. It contains no credentials, keys, client-profile contents, raw audit records, or diagnostic payloads.

## Confirmed Decisions

- The selected SDK is `mcp==1.28.1`. Its published metadata supports Python `>=3.10`; the prior assistant-runtime deployment log identifies the managed virtual environment as Python 3.12.
- The selected protocol transport is one local stdio process per AI-client session. It must not bind HTTP, SSE, WebSocket, or any other network listener.
- The isolated stdio probe negotiated MCP protocol revision `2025-11-25` and returned both text and `structuredContent` in a successful `CallToolResult`.
- The adapter should use the low-level `mcp.server.lowlevel.Server` API. It supports tool, resource, and prompt registration through `list_tools`, `call_tool`, `list_resources`, `read_resource`, `list_prompts`, and `get_prompt` handlers.
- Tool calls must register with `validate_input=False`. The probe confirmed an argument that violates an advertised identifier pattern reaches the handler, preserving the required path to runner-owned string validation and audit correlation.
- The existing runner remains the only diagnostic executor and audit boundary. The adapter must launch its CLI as a fixed subprocess and must not call scripts or runner functions directly.
- MCP-originated calls require fixed audit-origin metadata. Current runner CLI parsing has no `--client-id` or `--transport` options, so the next implementation slice must add compatible fixed-origin support before tool execution is exposed.
- Initial discovery remains limited to `project_resource_summary`, `server_basic_info`, and `server_network_info`. Restricted-host tools remain disabled by default; no opt-in was approved by this discovery record.
- SDK cancellation support exists, but the adapter must use cancellable child-process management and safely terminate a dispatched runner process when an MCP request is cancelled.

## Open Constraints and Blockers

- No AI client or local client configuration is selected in the repository. The exact client launch syntax and proof that it runs as `assistant` remain runtime validation work.
- No remote `assistant01` inspection ran because Ansible tooling is unavailable in this workspace. The SDK installation and stdio probe were local compatibility evidence, not deployed-runtime proof.
- The runner limits each stdout and stderr stream to 131072 bytes, but accepted string arguments have no reviewed maximum length and are echoed into result envelopes. A finite MCP frame/result bound cannot be proven until a reviewed argument-length and envelope-size bound exists.
- Do not expose argument-bearing MCP tools until that bound is decided and covered by validation. No Phase 07 completion checkbox may be updated from this record.

## Validation Performed

- Installed `mcp==1.28.1` into an isolated temporary virtual environment and inspected its package metadata and low-level server API.
- Compiled throwaway stdio probe client/server scripts in that environment.
- Ran a local stdio client/server handshake, tool discovery, structured-result call, and invalid-pattern argument pass-through probe.
- Confirmed the probe reported protocol revision `2025-11-25`, one advertised tool, `isError: false`, and the invalid string received by the handler.

## Next Step

After review of the unresolved frame-bound decision, execute Chunk 1 only: add backward-compatible fixed MCP audit-origin metadata to the existing runner. Do not add an MCP server, client configuration, network transport, or executable MCP tool in that slice.
