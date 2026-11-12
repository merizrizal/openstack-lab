# Metadata Evidence Contract Resolution Guide

## Purpose

This guide explains how to resolve the Phase 06 Steps 5–7 metadata evidence contract gap before implementing Chunk 3.

The current generated decision record accepts D05–D07 only “as defined in the authoritative contract,” while the tracked contract states that exact metadata sources, bounds, output schema, truncation behavior, and redaction rules remain unconfirmed. Treat D05–D07 as unresolved until concrete, owner-approved values are recorded.

This guide does not authorize implementation, deployment, host contact, authentication, source reads, audit inspection, negative testing, rollback, or live workflow execution.

Authoritative contract:

- `docs/ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-steps-05-to-07-operations-contract.md`

## 1. Resolve D05: source and role matrix

The diagnostic owner, inventory owner, and host-service owner should approve one exact metadata source slice.

| Field | Required decision |
| --- | --- |
| Diagnostic | Exact public diagnostic name, such as `recent_metadata_errors` |
| Source class | One fixed non-generic identifier |
| Permitted roles | Exact inventory role allowlist |
| Service class | Exact metadata service classification |
| Fixed selector | Approved journald unit, file class, or listener-event class |
| Prohibited sources | Configuration dumps, arbitrary logs, recursive scans, commands, and unrelated services |
| Missing source | Explicit `unavailable` mapping |
| Permission failure | Explicit `policy_denied` or `unavailable` mapping |
| Malformed source data | Explicit `error` mapping |

The owner must answer:

1. Where are metadata failure events recorded?
2. On which inventory roles are those events available?
3. Which exact event fields are diagnostically necessary?
4. Which nearby sources are explicitly prohibited?
5. What result applies when the source is absent, empty, stale, or unreadable?

Do not place protected addresses, credentials, raw logs, or inventory contents in the repository.

## 2. Resolve D06: closed bounds

Use finite classes and trusted configuration rather than caller-provided numbers.

| Field | Required decision |
| --- | --- |
| `window_class` | Exact allowlist and default |
| `line_limit_class` | Exact allowlist and default |
| Maximum records | Exact integer |
| Maximum normalized message length | Exact integer |
| Maximum total output bytes | Exact integer |
| Collector timeout | Exact duration |
| Empty source behavior | Explicit `empty` result |
| Limit behavior | Explicit `truncated: true` behavior |

Also define the processing order:

```text
source read bound
  -> record bound
  -> message normalization
  -> host-side redaction
  -> total-byte bound
  -> deterministic truncation
```

Callers must never provide a path, unit, timeout, byte cap, search expression, or numeric limit.

## 3. Resolve D07: output and redaction

Freeze exact field names, types, nullability, status values, and error mappings. The ADS proposes this starting shape:

```text
schema_version
tool
status
sections[]
  name
  status
  data[]
    host_label
    inventory_role
    source_class
    service_class
    observed_at
    severity
    event_class
    redacted_summary
  error
  truncated
error
```

The owner must decide:

- allowed overall and section statuses;
- timestamp format and missing-timestamp behavior;
- deterministic ordering and tie-breakers;
- whether `host_label` is retained;
- exact truncation semantics;
- exact error classes; and
- exact redaction replacements.

Synthetic redaction tests should cover at least:

- passwords;
- tokens and API keys;
- authorization headers;
- private-key blocks;
- credential-bearing URLs; and
- addresses or identifiers prohibited by the minimum-disclosure contract.

A redaction failure or surviving canary must discard the source-derived payload and return a normalized error without data.

## 4. Record a contract addendum

Create an outcome-only addendum for D05–D07 containing:

```text
decision ID
status
owner
source revision
protected evidence reference
exact accepted non-secret values
limitations
implementation authorization: separate
live authorization: separate
```

Then update these repository documents so they agree with the approved values:

- `docs/ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-steps-05-to-07-operations-contract.md`
- `docs/ai-ops-revised/implementation-plan/ads/06-01-restricted-operator-and-host-diagnostics-steps-05-to-07-ads.md`

Do not silently reinterpret or overwrite the existing generated decision record. If the approved values differ from its wording, issue a revised outcome-only decision record with a new source revision/reference.

## 5. Chunk 3 readiness checklist

Chunk 3 may resume only when all of the following are true:

- one exact metadata source class is accepted;
- role/source mapping is explicit;
- all bounds are finite and closed;
- output schema and status values are frozen;
- ordering and truncation are deterministic;
- redaction rules and canaries are frozen;
- missing, empty, denied, malformed, and oversized cases are defined;
- implementation remains synthetic/local only;
- Neutron and Nova remain explicit unavailable stubs; and
- transport, runner, registry, deployment, and host contact remain out of scope.

Until then, the correct behavior is the existing explicit `unavailable` result.
