# Phase 07 MCP Integration Evidence Snapshot

Repository record for successful local MCP deployment and runtime validation on 2026-07-12.

## Validation Context

- Runtime host: `assistant01`
- Deployment playbook: `ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml`
- Validation playbook: `ansible/ai_ops_runtime/playbook_validate_phase07_mcp_integration.yml`
- Scope: the sole `assistant` inventory host, with a reviewed project-visible server identifier.
- Evidence policy: paths, modes, package version, capability names, structured statuses, and audit-origin metadata only. No credentials, profile content, raw diagnostic payloads, raw audit lines, prompts, or resource bodies are recorded.

## Deployment and Repeatability

- The first setup run completed with `ok=89`, `changed=58`, `unreachable=0`, and `failed=0`.
- The repeat setup run completed with `ok=70`, `changed=1`, `unreachable=0`, and `failed=0`.
- On the repeat run, the MCP directories, adapter, policy, curated resources, and pinned SDK were unchanged. The one change was the shared `common` role restarting Chrony; the broad setup playbook is therefore not fully idempotent, while the MCP deployment slice is.

## MCP Boundary Confirmation

- The deployed adapter, policy, curated-resource directory, runner, and registry passed type, owner, group, mode, and non-symlink assertions.
- The runtime virtual environment reported the reviewed `mcp==1.28.1` package.
- Discovery returned exactly the three reviewed low-risk project tools, three fixed curated resources, and three diagnostic prompts. Tool schemas were closed.
- The deployed policy exposed only the low-risk project scope. Restricted-host tools remained excluded.
- The temporary local stdio client completed successful low-risk project and server calls. An invalid identifier produced `validation_error`; an unknown generic tool was rejected.
- Every checked MCP-originated call correlated to sanitized runner audit metadata with fixed local-client and stdio origin values.
- The stdio session created no additional listening socket. The adapter process was absent after client disconnect.

## Content and Safety Confirmation

- Curated resources were nonempty and passed the validation secret-pattern check.
- Prompts passed diagnostic-only and manual-next-step assertions.
- No network service, remote transport, generic execution capability, restricted-host default exposure, remediation action, or client configuration was introduced by this validation.

## Remaining Operational Notes

- An operator must configure and later disable an approved local AI client entry separately; no client-specific configuration is stored in this repository.
- Before any rollback that removes artifacts, disable the client MCP command first. The current role has no dedicated artifact-removal toggle.
- The shared Chrony restart on every broad setup rerun is outside the MCP role and should be addressed separately if full-playbook idempotency is required.
