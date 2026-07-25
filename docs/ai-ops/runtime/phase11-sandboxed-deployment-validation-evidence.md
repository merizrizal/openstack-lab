# Phase 11 Sandboxed Deployment Validation Evidence

## Scope

This record contains metadata-safe Phase 11 acceptance outcomes only. It does not
contain credentials, Codex-home contents, provider data, endpoint tuples, raw
firewall output, probe output, process environment, or runtime evidence contents.

## Accepted Outcomes

- Fake-only deployment validator: passed.
- Artifact integrity and protected ownership/mode boundary: passed.
- On-demand sandbox, listener, process-cleanup, and network-disabled checks: passed.
- Credential and historical-runtime read-denial checks: passed.
- Permanent dedicated-identity disabled egress policy: passed for both address families.
- Independent `assistant` egress policy validation: passed.
- Approved synthetic orchestrator path: passed.
- Independent `assistant` denial against the approved synthetic path: passed.
- Unconditional rollback after success: passed.
- Injected-failure rollback: passed; the intentional operation failure was followed by
  temporary-marker removal and permanent-policy revalidation.

## Control Summary

- Temporary egress markers retained after validation: 0.
- Provider requests: 0.
- Official remote adapter selections: 0.
- Authentication operations performed: 0.
- Permanent dedicated-identity egress modes left enabled: 0.

## Final State

The deployed orchestrator remains fake-only, network-disabled, and on-demand. The
permanent dedicated-identity reject policy and existing `assistant` policy remain
materialized. Phase 12 remains separately gated by its own compatibility and
approval requirements.
