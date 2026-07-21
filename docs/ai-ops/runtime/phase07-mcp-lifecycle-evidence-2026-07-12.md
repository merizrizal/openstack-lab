# Phase 07 MCP Lifecycle Evidence

Sanitized record of approved live MCP artifact removal and restoration validation on `assistant01` on 2026-07-12.

## Scope and Evidence Policy

- Scope: disable the approved local client entry; remove only the reviewed MCP artifacts; validate preservation and the manual runner; restore artifacts; rerun MCP validation.
- Evidence retains only task outcomes, counts, and reviewed contract results. It excludes runtime-home contents, client configuration, credentials, profiles, prompts, raw tool output, audit records, listener snapshots, and environment values.
- SDK removal was not requested; the pinned MCP SDK remained installed.

## Observed Lifecycle Results

- The fixed-argv removal of the approved local client entry succeeded. The exact adapter process was absent before artifact removal.
- The first confirmed `absent` apply completed with `ok=18`, `changed=4`, and `failed=0`. Exact process, managed-entry/type, and preserved-path metadata assertions passed before and after removal.
- The repeat confirmed `absent` apply completed with `ok=14`, `changed=0`, and `failed=0`.
- A sanitized `assistant`-account manual-runner smoke passed its structured `project_resource_summary` safety contract after artifact removal.
- The first dedicated `present` apply completed with `ok=8`, `changed=4`, and `failed=0`; the repeat completed with `ok=8`, `changed=0`, and `failed=0`.
- The Phase 07 MCP integration validator passed after restoration, including the no-bytecode adapter syntax check, reviewed MCP artifact assertions, local stdio discovery/call boundary, no listener delta, and adapter exit after disconnect.
- A final exact-adapter-process assertion passed after validation. The temporary validator does not alter the disabled Codex MCP entry.
- Targeted runner and MCP Python regressions passed: 58 tests.

## Current Boundary

- The reviewed MCP deployment is restored on `assistant01`; the local client entry remains disabled.
- MCP remains local stdio only. No MCP listener, remote MCP transport, provider configuration, credentials, login, or model invocation was introduced.
- The manual runner, registry, credentials, diagnostics, audit path, and Codex runtime-home metadata remained preserved; runtime-home contents were not inspected.
- Phase 99 and remote-provider work have not begun.
