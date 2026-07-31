# Orchestrator Remote Acceptance Operations

## Current state

The deployed default remains the static `aiops-orchestrator` fake-only service. The
separate `aiops-orchestrator-remote` unit is installed, disabled, stopped, and
conditioned on a private approval artifact. The reviewed operation playbook is
default-false and fails closed without distinct, fresh operation and temporary-egress
approvals. Do not override its default.

The separately approved one-shot acceptance completed and restored the disabled
baseline; see `phase12-one-shot-remote-acceptance-evidence-2026-07-31.md`. No active
authorization exists now. A future separately approved operation requires fresh
approval and local preflight; it must not be improvised by changing inventory values
or starting the unit manually.

## No-provider preflight

Before any future approval is requested, run only the reviewed local validator:

```bash
rtk ansible-playbook -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_validate_phase12_remote_preflight.yml
```

This validates the Phase 11 fake-only deployment first, then verifies that the remote
approval artifact is absent, the remote unit is static, and the permanent orchestrator
egress mode remains `disabled`. Retain only pass/fail categories; do not retain
command output, unit metadata, credentials, Codex-home contents, firewall output, or
provider data.

## Approval and invocation boundary

A future remote operation requires a fresh, operation-specific approval that binds
one reviewed workflow, one model alias, one tool request, one turn, zero retries, and
a bounded expiry. Authentication approval is separate. Expired, reused, malformed, or
broadened approval must stop before egress or unit start.

The future operation must create the approval artifact with restrictive ownership and
remove it unconditionally. It must perform exactly one start of the separate remote
unit and stop on its first terminal category. It must not enable the unit, add a
timer, accept arbitrary arguments, use a custom provider or proxy, inspect Codex-home,
or retain prompt, response, SDK, tool, authentication, or advisory content.

## Timeout, cancellation, and failure

On cancellation, timeout, unsupported SDK behavior, unexpected tool behavior, or
unsafe output classification: do not retry. Stop the remote unit, remove the private
approval and temporary workspace, restore permanent orchestrator denial, and rerun the
no-provider preflight. Record only the closed terminal category and validation outcome.
A supported-runtime failure is a vendor blocker, not authorization for private protocol
debugging, packet capture, gateway fallback, or credential inspection.

## Disablement and authentication expiry

Keep the remote unit disabled and stopped at all times outside one future approved
operation. If the operator reports `authentication_required` or `operator_error`,
restore the disabled baseline and use the separate authentication runbook. The operator
performs any supported login-status action privately; automation records only the
closed category and never captures command output or authentication material.

## Evidence and retention

Persist only approved versions, counts, closed terminal categories, and validator
outcomes in the accepted evidence location. Do not store raw input, result, provider,
SDK, tool, authentication, endpoint, egress, exception, or advisory data in evidence,
logs, tickets, chat, shell history, or handoffs.
