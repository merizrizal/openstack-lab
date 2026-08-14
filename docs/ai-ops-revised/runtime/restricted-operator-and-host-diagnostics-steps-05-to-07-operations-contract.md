# Restricted Operator and Host Diagnostics Operations Contract — Steps 5–7

## Status and authority

This is the **non-activation** operations contract for Phase 06 Steps 5–7. It records the repository-fixed safety boundary and the owner decisions that must be accepted before any recent-evidence diagnostic is implemented, registered, deployed, contacted, or executed.

This contract remains non-activating. D05–D07 are frozen at source revision `rev-2026-08-0002`; maintained host projection, observer identity and transport policy, deployment, evidence ownership, and live authorizations remain separately gated. Those unresolved gates are blockers, not defaults. Until every relevant activation blocker is accepted, all host diagnostics remain `unavailable` and absent from the runner registry.

This contract does **not** authorize:

- account, credential, key, profile, policy, sudo, or role creation or modification;
- inspection of protected inventory, addresses, connection metadata, credentials, keys, raw output, logs, audits, or evidence;
- SSH, host contact, OpenStack authentication, API calls, source reads, negative tests, or workflow execution;
- connector, runner, registry, deployment, host contact, live validation, or any implementation beyond the separately recorded metadata synthetic slice; or
- Phase 06 live acceptance or Phase 07 exposure.

This contract is subordinate to:

- `docs/ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-steps-01-to-04-operations-contract.md`;
- `docs/ai-ops-revised/runtime/identity-policy-operations-contract.md`;
- `docs/ai-ops-revised/runtime/tool-runner-safety-gateway-steps-01-to-04-operations-contract.md`;
- `docs/ai-ops-revised/runtime/mvp-live-validation-and-rollback-operations-contract.md`;
- `docs/ai-ops-revised/runtime/selective-reuse-manifest.md`; and
- `docs/ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-evidence-template.md`.

## Fail-closed rule

```text
complete, owner-approved, outcome-only evidence for the exact scope
  -> permit only the next separately authorized scope

missing, stale, ambiguous, contradictory, or unapproved evidence
  -> stop, retain the blocker, and keep the capability unavailable
```

No playbook completion, static test, generated template, file presence, or plan checkbox substitutes for owner acceptance. The retained blocked run `2026-0002` is stale after any gate, authorization, or source-revision change and must not be reused.

## Repository-fixed boundary

The following are observed repository constraints, not deployment authorization:

| Boundary | Contract |
| --- | --- |
| Public capability | No generic SSH, sudo, journal, file, service, command, path, unit, or OpenStack passthrough capability may be exposed. |
| Diagnostic intents | `recent_metadata_errors`, `recent_neutron_errors`, and `recent_nova_errors` are the accepted D05 public identifiers and descriptions at `rev-2026-08-0002`; they remain absent from the runner registry until separate registration authorization. |
| Public selectors | A future request may contain only an approved non-secret `host_label`, `window_class`, and `line_limit_class`. It may never contain a destination, address, path, unit, command, source selector, account, key, port, SSH option, sudo option, timeout, or byte cap. |
| Observer files | The fixed candidate collector path is `/usr/local/libexec/openstack-ai-ops-assistant/host-observer-collector`; the fixed candidate policy path is `/etc/openstack-ai-ops-assistant/host-observer-policy.yml`. Their existence, owner, mode, regular-file status, and deployment are unapproved. |
| Authority isolation | Project-reader, operator-reader, and host-observer authority must remain independently revocable. Host diagnostics must receive no `OS_*` environment; API diagnostics must receive no observer state. |
| Historical reuse | Deferred host-diagnostic assets remain unselected under the selective-reuse manifest. No historical implementation may be inspected, copied, or adapted without an exact approved manifest amendment. |
| Default behavior | Missing capability, gate, projection, policy, key metadata, source approval, or authorization produces explicit `unavailable`, never success or fallback. |

## Pending decision register

All entries below require outcome-only, administrator-owned evidence outside Git. The decision record must identify owner, decision, evidence reference, timestamp, source revision, retention label, and limitations. It must not retain protected values.

| ID | Decision required | Required owner-approved outcome | Fail-closed effect while unresolved |
| --- | --- | --- | --- |
| D01 | Steps 1–4 prerequisite acceptance and the Phase 05 gate-label contradiction | Confirm the exact prerequisite disposition and evidence owner | No implementation beyond this contract; Phase 06 remains blocked. |
| D02 | Maintained inventory projection | Confirm source owner, revision/freshness, approved safe labels, role mappings, enablement/disablement, protected runtime location, and drift procedure | No host label is valid and no destination may be resolved. |
| D03 | Host-observer authority model | Review the proposed closed `authority_class` descriptor without overloading `credential_profile`; confirm isolation, lifecycle, and no `OS_*` environment | No host authority descriptor, connector, or registry mapping may exist. |
| D04 | Observer account, key, forced transport, and sudo | Confirm account/key owners, source restriction, rotation/revocation, forced-stdin compatibility, no-forwarding restrictions, collector integrity, and whether sudo is required | No observer provisioning, SSH, collector invocation, or sudo policy. |
| D05 | Three public tool names and role/source matrix | Accepted at `rev-2026-08-0002`: exact names/descriptions, controller role, source classes, service classes, logical selectors, prohibited sources, and source outcomes | No tool registration or live source read. |
| D06 | Inputs and bounds | Accepted at `rev-2026-08-0002`: exact public inputs, defaults, allowlists, request/line/record/message/byte caps, timeouts, empty behavior, and truncation order | No caller-controlled source, path, unit, timeout, or output limit. |
| D07 | Output, unavailable, ordering, truncation, and redaction | Accepted at `rev-2026-08-0002`: exact schema, statuses, error classes/messages, enums, timestamps, ordering, redaction, canaries, serialization, and stubs | No source-derived success until the metadata implementation scope is separately validated. |
| D08 | Evidence, audit, rollback, and negative tests | Confirm evidence location/retention/audit access, unchanged-state comparator, rollback owner/order, and bounded positive/negative test plan | No live validation, audit inspection, revocation rehearsal, or acceptance claim. |
| D09 | Step 7 representative metadata case | Confirm safe pre/post state procedure, case owner, and advisory-only interpretation boundary | No workflow execution or diagnosis claim. |

## Diagnostic and projection contract

The three accepted diagnostic identifiers each select exactly one source class. A caller must never select a source, role, destination, path, unit, command, transport option, or authority. The accepted tool name, source class, source-to-role matrix, and deployment state must be evaluated before any transport construction.

A future projection resolver has this closed behavior:

```text
approved tool name + approved host label + owner-approved projection
  -> fixed private destination descriptor
  | unavailable | denial | integrity error
```

The descriptor is private implementation state. It must not be emitted in a result, audit record, argument list, environment, repository document, fixture, or normal command output. Missing, stale, duplicate, disabled, ownerless, ambiguous, or role-incompatible projection data stops before child-process creation or network contact.

The projection schema, protected location, owner, group, mode, revision, freshness field, and deployment process remain D02 decisions. Synthetic labels may be used only by a later authorized fixture/test chunk.

## Authority and transport contract

The only reviewed direction is a closed host-observer authority descriptor, tentatively named `authority_class`, distinct from the existing OpenStack `credential_profile` model. D03 must accept or replace that design before implementation. Existing profile semantics must not be broadened implicitly.

A future connector may use one fixed argument vector and one bounded structured request on standard input only after D04 acceptance. It must not use a shell, a caller-selected remote command, extra remote arguments, ambient environment values, fallback identities, or caller-selected transport options. Forced-stdin compatibility remains unconfirmed; therefore no protocol, connector, or collector implementation is authorized by this contract.

A future forced collector must reject `SSH_ORIGINAL_COMMAND`, arguments, unknown or duplicate request fields, oversized input, unsupported schemas, unapproved classes, and source-to-role mismatches before a source read. It must not perform configuration reads, recursive scans, service control, package operations, shell evaluation, output redirection, or arbitrary file/journal access.

## Source, bounds, output, and redaction contract

D05–D07 are accepted at source revision `rev-2026-08-0002`. The contract freezes the following non-secret policy while keeping implementation and live activation separately authorized.

### D05 source and role matrix

| Public diagnostic | Source class | Permitted role | Service class | Fixed logical selector |
| --- | --- | --- | --- | --- |
| `recent_metadata_errors` | `metadata_error_events` | `controller` | `metadata` | `metadata_service_errors` |
| `recent_neutron_errors` | `neutron_error_events` | `controller` | `neutron` | `neutron_service_errors` |
| `recent_nova_errors` | `nova_error_events` | `controller` | `nova` | `nova_service_errors` |

The public descriptions are bounded, redacted recent metadata-service, Neutron, and Nova error evidence for an approved host label. The selector is fixed by the tool mapping; callers never provide a source class, path, unit, command, pattern, or destination. Actual protected path/unit mappings remain outside Git.

Prohibited sources are configuration dumps, arbitrary logs or journals, recursive filesystem scans, caller-selected commands/paths/units, unrelated services, raw audit records, credential or key stores, network inventory, and connection metadata. Source outcomes are: missing -> `unavailable/source_missing`; empty -> `empty`; stale -> `unavailable/source_stale`; denied or unreadable -> `denied/source_denied`; malformed -> `error/malformed_source`. A stale or unknown policy/projection freshness class is `source_stale`; events outside the selected window are filtered and do not by themselves make the source stale.

### D06 closed inputs and bounds

The public request contains exactly a required lowercase ASCII `host_label` (non-empty, maximum 64 characters, no leading or trailing hyphen), optional `window_class`, and optional `line_limit_class`. The public request contains no source selector. Unknown fields, duplicate fields, missing fields, invalid UTF-8, invalid types, or invalid classes produce `error/validation_error` at the collector boundary. The maximum request size is 8,192 UTF-8 bytes.

`window_class` has allowlist `[15m, 30m, 1h]`, default `30m`, and durations 900, 1,800, and 3,600 seconds. `line_limit_class` has allowlist `[small, medium, large]`, default `medium`, and source-line bounds 50, 100, and 200. The maximum normalized records is 20; maximum pre-redaction summary is 4,096 UTF-8 bytes; maximum normalized summary is 512 UTF-8 bytes; maximum serialized collector output is 16,384 UTF-8 bytes; collector timeout is 5 seconds; runner timeout is 15 seconds. None is caller-overridable.

The collector captures one UTC collection-start time and accepts timestamps in the inclusive interval `collection_start - window_duration <= observed_at <= collection_start`. Canonical output timestamps are `YYYY-MM-DDTHH:MM:SS.ffffffZ`; missing, invalid, future, or excessive-precision timestamps produce `error/malformed_source` with no source-derived data. Events outside the selected window are excluded; if none remain, the result is `ok` with one `empty` section and no error.

Processing order is: bounded source read -> deterministic ordering -> record cap -> Unicode/message normalization -> host-side redaction and canary scan -> per-message cap -> total-output cap. Source-line, record, message, or output-byte limits set `truncated=true`; known out-of-window filtering alone does not. If the source reader stops at its line bound and reports `source_truncated=true`, `truncated=true` even when the inspected bounded prefix has no in-window events. One request performs one collection attempt and does not retry or broaden sources.

### D07 output and redaction

The collector document has exactly these typed fields: `schema_version` string fixed to `1.0`; `tool` string equal to the public diagnostic name; `status` top-level status enum; `sections` array; and `error` either a `{class: string, message: string}` object or `null`. A section has exactly `name` string, `status` section-status enum, `data` array, `error` either the same fixed error object or `null`, and `truncated` boolean. Each event has exactly string fields `host_label`, `inventory_role`, `source_class`, `service_class`, `severity`, `event_class`, and `redacted_summary`, plus required non-null string `observed_at` in canonical UTC format. No source-specific additions are permitted.

Top-level statuses are `ok`, `error`, `denied`, `timeout`, and `unavailable`; section statuses are `ok`, `empty`, `denied`, `error`, `timeout`, and `unavailable`. Public error classes are `validation_error`, `invocation_denied`, `observer_integrity_error`, `unsupported_deployment_state`, `host_unavailable`, `host_disabled`, `source_role_mismatch`, `source_missing`, `source_stale`, `source_denied`, `malformed_source`, `timeout`, `redaction_failure`, and `approved_optional_capability_absent`. Internal validation details collapse to `validation_error`. Fixed messages are: `validation_error` -> `Collector request is invalid.`; `invocation_denied` -> `Collector invocation is unavailable.`; `observer_integrity_error` -> `Observer metadata is unavailable.`; `unsupported_deployment_state` -> `Observer deployment is unavailable.`; `host_unavailable` -> `Approved host is unavailable.`; `host_disabled` -> `Approved host is disabled.`; `source_role_mismatch` -> `Approved source is unavailable for this host role.`; `source_missing` -> `Approved source is missing.`; `source_stale` -> `Approved source is stale.`; `source_denied` -> `Approved source access is denied.`; `malformed_source` -> `Approved source data is malformed.`; `timeout` -> `Diagnostic exceeded its time limit.`; `redaction_failure` -> `Diagnostic output could not be safely redacted.`; and `approved_optional_capability_absent` -> `Approved optional capability is unavailable.` No message contains source text or protected values.

Severity is `[critical, error, warning, info, unknown]`; unmapped values become `unknown`. Event class is `[request_error, connection_error, timeout, authentication_error, dependency_error, configuration_error, unknown]`; unmapped values become `unknown`. Events are ordered by `observed_at` descending, severity priority `critical > error > warning > info > unknown`, `event_class` ascending, and `source_sequence` ascending. Duplicate events are retained.

The canonical redaction replacement is `[REDACTED]`. Redaction covers passwords/passphrases, tokens/API keys, authorization and bearer values, private-key blocks, credential-bearing URLs, IPv4/IPv6 addresses, MAC addresses, UUIDs/resource identifiers, and hostnames or host-label-like identifiers inside summaries. Only the approved structured `host_label` is retained. Synthetic canaries cover each category, including reserved documentation addresses and `.invalid` credential URLs. A surviving canary or redaction failure discards all source-derived data and returns `error/redaction_failure`.

Summaries require valid UTF-8, NFC normalization, control/newline replacement, whitespace collapse, trimming, and non-empty output before redaction. Per-message truncation retains the largest valid UTF-8 prefix without a marker. Total-byte truncation retains only complete ordered records; no partial JSON is emitted. Serialization is compact UTF-8 JSON with `ensure_ascii=false`, sorted keys, `allow_nan=false`, one trailing newline, and the newline included in the 16,384-byte cap.

For source failures, `sections` is empty and the top-level error is used. For successful or empty results, one fixed section is emitted: `metadata_errors`, `neutron_errors`, or `nova_errors`. Neutron and Nova remain explicit `unavailable/approved_optional_capability_absent` stubs with no source access until separately approved. Correlation and audit fields remain in the outer runner envelope.

## Audit, evidence, and rollback boundary

Each future diagnostic request requires a distinct runner-generated correlation identifier and a sanitized audit event. Audits must not retain projection contents, private transport metadata, raw requests, raw evidence, or secrets. D08 must define the evidence owner, protected location, retention, authorized audit inspection, and normalized retained fields before any operation.

Rollback is independently scoped from registry/deployment disablement and observer account/key/sudo removal. The owner-approved rollback sequence must disable the affected capability without affecting project-reader or operator-reader authority. Any unexpected mutation, shell, forwarding, destination bypass, unrestricted sudo, secret disclosure, or state change is an emergency stop; the responsible owner disables the affected authority and investigates outside that authority.

## Step 7 workflow boundary

The intended advisory-only sequence is:

```text
server_basic_info
  -> server_network_info
  -> neutron_agent_health when separately accepted and available
  -> accepted recent_metadata_errors when separately available
  -> accepted recent_neutron_errors when separately available
  -> accepted recent_nova_errors when separately available
  -> evidence-gap-aware interpretation
```

This is not an aggregate executor and is not authorized to run. Each request retains independent authorization and correlation. Missing, denied, stale, failed, timed-out, truncated, contradictory, or unavailable evidence remains a stated gap. The workflow must not claim causality, restart services, edit configuration, enter a guest, broaden authority, or execute remediation.

## Separate authorization scopes

The following scopes require separate owner authorization and a fresh non-secret run identifier after any changed gate, authorization, or source revision:

1. observer account/key/policy/collector deployment;
2. one approved host and one approved source-class contact;
3. positive collector validation;
4. negative SSH, forwarding, sudo, and source-boundary validation;
5. protected audit/evidence inspection;
6. unchanged-state comparison;
7. authority revocation or rollback rehearsal; and
8. the representative Step 7 workflow case.

Authorization for one scope does not authorize another scope.

## Completion criteria and next action

This contract remains reviewable but **non-activating** while D01–D04 and D08–D09 or any deployment/live gate remain unresolved. D05–D07 are complete at source revision `rev-2026-08-0002`; the next separately authorized implementation is the metadata synthetic slice only. Neutron and Nova remain unavailable and absent from the runner registry. No generated input, protected data, host contact, or live action may be used to manufacture activation completeness.
