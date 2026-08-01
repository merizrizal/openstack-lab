# Phase 13 Provider Gateway Retirement Evidence

**Date:** 2026-07-31
**Status:** Retirement implementation and final read-only live validation complete.

## Scope

This evidence records only the Phase 13 retirement implementation and
metadata-safe outcomes. It contains no ledger content, command output,
provider traffic, authentication material, credentials, endpoints, prompts, or
responses.

## Recorded Outcomes

- The operator-selected disposition is `verified_absent_preexisting` for the
  gateway unit, active root, state directory, ledger, and `aiops-provider`
  identity on the rebuilt `assistant01` host.
- The bounded stop/disable operation previously confirmed the gateway service,
  process, and TCP 8765 listener were absent or closed without creating any
  gateway, ledger, state directory, or identity.
- Normal AI-client setup no longer includes the historical gateway deployment
  task. Independent `assistant_egress` enforcement remains included.
- The retirement playbook now requires fresh, expiry-bounded authorization for
  stop/disable, deployment de-wiring, and unit/root removal; the removal path
  is limited to the fixed unit and active root and rechecks the approved
  absence disposition.
- The retired-state validator is read-only. It checks gateway absence and the
  Phase 12 fake-only, disabled-egress, static/inactive successor baseline
  without starting gateway, bridge, or remote services.
- Historical gateway source, tests, templates, defaults, schemas, and prior
  evidence remain retained and unwired. They are not a rollback invocation or
  provider fallback.

## Static Validation

- Retirement and retired-state validator playbooks passed Ansible syntax
  checks.
- Scoped repository searches found no remaining normal setup include of
  `provider_gateway.yml`.
- The historical restart notifications remain only inside the retained,
  unreachable gateway deployment task.
- Git diff whitespace checks passed.

## Live Validation

The approved inventory inputs were restored and the read-only Phase 13
retired-state validator passed on `assistant01` with `ok=33`, `changed=0`, and
`failed=0`. It confirmed the gateway unit, active root, evidence paths,
identity, process, and TCP 8765 listener remain absent; Phase 12 remote and
bridge units remain static and inactive; ephemeral approval, socket, and
temporary-egress artifacts remain absent; and persistent assistant egress
controls remain active.

No gateway, bridge, or remote unit was started. No provider traffic was
created, no ledger content was inspected, and no assistant or orchestrator
egress control was weakened. Do not run the historical active gateway
validator or restore the historical deployment include.
