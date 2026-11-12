# Phase 07 Codex Runtime Invocation Evidence

Sanitized record of the approved fixed-argv Codex and reversible local-stdio MCP acceptance validation on 2026-07-12.

## Scope and Evidence Policy

- Runtime host: `assistant01`.
- Scope: fixed-argv Codex version/help checks plus a reversible local-stdio MCP entry acceptance test.
- Validation used the reviewed non-interactive `assistant` identity, fixed runtime-home boundary, approved executable, and the reviewed `openstack-ai-ops` adapter command documented in `mcp-integration.md`.
- The validation retained only pass/fail metadata. It did not retain raw client output, listener snapshots, runtime-home contents, environment values, client configuration, credentials, prompts/history, provider data, OpenStack profile data, tool payloads, or audit records.

## Observed Results

- The approved Codex executable reported version `0.144.1` through the fixed runtime-home invocation.
- Version and help invocations succeeded without alias or configuration warnings.
- Version-specific help confirmed the supported command-and-arguments stdio contract for MCP addition and the named-entry remove operation.
- The reviewed entry was initially absent; two add/remove cycles succeeded, and the entry was absent after the second removal.
- No listener delta or surviving adapter process was observed across the fixed-argv and entry-acceptance validation.
- The repository validator passed the exact three-tool, three-resource, three-prompt discovery contract, closed schemas, default restricted-host denial, low-risk/negative-case envelopes, audit correlation, and stdio disconnect cleanup.
- The validation made no repository change and did not log in, configure a provider, inject credentials, or invoke a model.

## Remaining Boundary

- Persisting, changing, or enabling an MCP entry requires separate explicit approval and reviewed fixed name/executable/arguments.
- URL mode, remote MCP transport, `mcp --env`, provider authentication, and remote-model use remain prohibited pending separate acceptance.
- The runtime-home contents remain operator-managed and were not inspected or copied.
