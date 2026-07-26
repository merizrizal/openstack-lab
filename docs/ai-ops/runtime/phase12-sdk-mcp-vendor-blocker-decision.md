# Phase 12 SDK and MCP Vendor-Blocker Decision

## Status

**Decision:** remote acceptance remains blocked.

**Closed category:** `VENDOR_BLOCKED / MCP_INTERCEPTION_UNSUPPORTED`.

This record documents local no-provider contract discovery only. It does not record
SDK events, provider data, credentials, Codex-home contents, endpoint data, firewall
output, prompts, responses, tool output, or authentication output.

## Evidence

The reviewed pinned SDK exposes `CodexConfig`, `AsyncCodex`, `AsyncThread.turn()`,
`AsyncTurnHandle.stream()`, and `AsyncTurnHandle.interrupt()` through its public
Python surface. Public Codex configuration documentation and
`docs/ai-ops/runtime/mcp-integration.md` establish the fixed local stdio MCP
command/arguments, working directory, enabled-tool, startup, and timeout contract.
The remaining proof is narrower: the repository-owned proxy/bridge must validate and
redact every result before Codex consumes it; the public SDK has no callback for that
pre-consumption interception.

The public async turn stream emits notification objects with payloads. The repository
adapter intentionally rejects payload-bearing events and currently models a different
mock-only stream shape. Enabling it would weaken the reviewed metadata-only boundary.

The repository contains a tested Unix bridge and credential-free proxy, but no
assistant-owned bridge executor/service deployment. The existing assistant MCP server
owns the credential-bearing runner through stdio and is not a bridge executor.

## Decision

Do not:

- enable `OFFICIAL_ADAPTER_ENABLED`;
- enable or start `aiops-orchestrator-remote`;
- create a service-readable approval artifact;
- deploy an assistant bridge socket or executor;
- change egress, authenticate, resolve DNS, construct a live SDK client, or contact a
  provider;
- use generic SDK overrides, custom process arguments, a proxy, gateway fallback, or
  private-protocol inspection to bypass the missing contract.

The existing fake-only service and permanent egress denial remain the accepted
baseline.

## Reopening criteria

A new reviewed design may reopen this work only after all of the following are proven
without provider contact:

1. The documented fixed stdio MCP configuration is rendered to launch exactly one
   repository-owned local boundary without caller-selectable routing or overrides.
2. A metadata-only reducer can consume the documented lifecycle without retaining or
   exposing payload content.
3. An assistant-owned bridge executor maps only the reviewed tool request to the
   existing credential-bearing runner and redacts results before the orchestrator can
   receive them.
4. Socket ownership, mode, peer-UID verification, service lifecycle, timeout, and
   cleanup are defined and tested.
5. A root-controlled one-shot approval artifact has an atomic consume/remove contract
   that does not grant broad write access to the orchestrator identity.
6. A separately approved temporary egress and rollback design exists.

Until then, classify the remote path as a vendor blocker. Do not treat this decision
as an authentication, egress, retry, upgrade, or provider-request approval.
