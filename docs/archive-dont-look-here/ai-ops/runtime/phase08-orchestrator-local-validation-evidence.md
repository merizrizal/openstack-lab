# Phase 08 Orchestrator Local Validation Evidence

**Date:** 2026-07-21  
**Status:** Local fake-backed acceptance passed; remote execution remains blocked.

## Scope

The repository-owned orchestrator package was validated only with its injected
`FakeCodexAdapter`. No Codex app-server, authentication flow, credential path,
listener, DNS lookup, provider connection, MCP server, deployment role, or
egress policy was invoked or changed.

## Accepted local checks

The package validation environment is
`/tmp/openstack-ai-ops-orchestrator-venv`, populated from the approved
hash-locked requirements.

```text
python -m ruff format --check ansible/ai_ops_runtime/files/orchestrator
python -m ruff check ansible/ai_ops_runtime/files/orchestrator
python -m mypy ansible/ai_ops_runtime/files/orchestrator/src ansible/ai_ops_runtime/files/orchestrator/tests
python -m py_compile <orchestrator source and test files>
python -m pytest -q ansible/ai_ops_runtime/files/orchestrator/tests
```

Acceptance coverage proves closed request/state/event contracts; fake success,
cancellation, deadline, excessive-event, malformed-event, turn-limit,
output-limit, cleanup, fixed error classification, and metadata evidence
failure behavior. Static assertions prove the fake adapter has no SDK, network,
process, credential-runtime, or filesystem-runtime imports, and the official
adapter remains disabled without runtime or authentication calls.

## Remaining gates

The official adapter remains disabled. It must not be enabled until all of the
following are separately approved and implemented:

1. MCP tool-result redaction before model submission.
2. Dedicated deployment identity and opaque Codex runtime-home controls.
3. Supported operator authentication without repository credential access.
4. Bounded DNS/HTTPS egress policy and a separately approved remote acceptance.

No local validation result authorizes API-key fallback, provider-gateway reuse,
private-protocol inspection, remote provider access, or remediation.
