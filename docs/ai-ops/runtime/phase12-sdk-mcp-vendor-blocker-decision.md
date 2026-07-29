# Phase 12 SDK and MCP Live MVP Policy Decision

## Status

**Decision:** the former vendor blocker is superseded for the fixed live Codex
MVP by an explicit bounded in-memory payload-reduction policy.

**Prior closed category:** `VENDOR_BLOCKED / MCP_INTERCEPTION_UNSUPPORTED`.

This record documents the reviewed policy change only. It contains no SDK events,
provider data, credentials, Codex-home contents, endpoint data, firewall output,
prompts, responses, tool output, or authentication output. It does not authorize a
live request, authentication action, egress change, or remote-unit activation.

## Evidence

The offline review of pinned `openai-codex==0.144.4` confirmed the public
`CodexConfig`, `AsyncCodex`, `AsyncThread.turn()`, `AsyncTurnHandle.stream()`, and
`AsyncTurnHandle.interrupt()` surface. Public `Notification` objects contain both
`method` and `payload`; no payload-free lifecycle or pre-consumption metadata callback
was found.

The fixed local stdio MCP command, working directory, enabled tool, startup, and
timeout contracts remain valid. The repository-owned proxy/bridge validates and
redacts each OpenStack tool result before Codex consumes it. The separate official
adapter must then treat SDK notifications as tainted process-memory objects and reduce
only reviewed public shapes to repository-owned metadata and sanitized advisory text.

The repository contains a tested Unix bridge, credential-free proxy, and an
assistant-owned bridge executor/service deployment. The units are static, disabled,
and stopped; the separately gated activation playbook uses a fake runner only. The
existing assistant MCP server still owns the credential-bearing runner through stdio;
the bridge executor delegates only through that reviewed runner contract.

## Decision

The MVP may implement the pinned official SDK behind the repository-owned model
adapter contract under these conditions:

- raw notification payloads exist only as tainted values in the one-shot adapter
  process and reducer call stack;
- exact public method/payload types, turn identity, order, count, and byte bounds are
  checked before repository output is produced;
- only sanitized `AdapterEvent` metadata and bounded `AdapterResult.advisory_text`
  cross the adapter boundary;
- raw payloads never enter logs, exceptions, evidence, presenters, callbacks, test
  snapshots, or persistent files;
- the fixed MCP proxy/bridge redacts OpenStack tool results before Codex receives
  them;
- orchestration depends on a provider-neutral structural adapter contract so Codex
  can later be replaced without changing tool or evidence boundaries.

Python memory zeroization is not claimed. Exposure is minimized with immediate
reduction, bounded values, dropped references, disabled raw logging, exact cleanup,
and termination of the one-shot process.

## Remaining gates

This policy decision authorizes offline implementation under
`12-01-phase12-gated-remote-boundary-ads.md`; it does not authorize a live operation.
Before one provider request:

1. The provider-neutral contract, tainted reducer, pinned lifecycle wiring, one-shot
   entrypoint, and offline end-to-end simulation must pass their reviewed chunks.
2. `OFFICIAL_ADAPTER_ENABLED` and ordinary remote execution must remain disabled by
   default; no unconditional global enablement is permitted.
3. A fresh one-request approval and separate temporary-egress approval must be
   obtained and consumed through the reviewed operation boundary.
4. Exactly one attempt, no retry, bounded ephemeral presentation, unconditional
   cleanup, baseline restoration, and metadata-only evidence are required.

Do not use generic SDK overrides, private-protocol inspection, provider gateways,
API-key fallback, copied credentials, or recurring remote operation. Any failed
validation or cleanup blocks the live request and preserves the fake-only baseline.
