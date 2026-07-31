# Phase 12 Orchestrator Authentication Egress Evidence

**Date:** 2026-07-28
**Status:** Authentication status established; remote execution remains blocked.

## Scope

This record retains metadata-safe outcomes from the separately approved,
bounded authentication-egress operation for `aiops-orchestrator`. It contains no
approval identifier or expiry, authentication command output, account/device
information, credentials, Codex-home data, provider data, DNS results, or raw
UFW rules.

## Accepted Outcomes

- Permanent disabled orchestrator egress and the independent `assistant` egress
  policy passed check-mode validation before the temporary operation.
- A bounded authentication-only egress interval completed.
- Temporary IPv4 and IPv6 authentication marker blocks were removed
  unconditionally after the interval.
- Permanent disabled orchestrator egress and independent `assistant` egress
  validation passed after cleanup.
- The operator declared the closed authentication category: `authenticated`.

## Operational Observation

The authentication-window playbook validates its expiry as a string. When
passing extra variables from a temporary file, use JSON or quote the ISO-8601
UTC expiry in YAML so it is not coerced to a datetime value before validation.

## Final State

- Temporary authentication egress markers retained: 0.
- Authentication category retained: `authenticated`.
- Remote unit activation: 0.
- Official adapter selection: 0.
- Provider workflows or requests: 0.
- Bridge activation: 0.
- Permanent dedicated-identity denial: restored.
- Regular remote use: disabled.

## Remaining Gate

This authentication result is a prerequisite only. Phase 12 Chunk 7 remains
separately gated: it requires a reviewed live-operation boundary, fresh
one-request authorization, a separate egress approval, exactly one terminal
attempt, cleanup, post-validation, and metadata-only acceptance evidence.
