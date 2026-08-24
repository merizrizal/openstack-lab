# Restricted Operator and Host Diagnostics Operations Contract — Steps 5–7

## Status and authority

This contract records the repository-fixed safety boundary for Phase 06 Steps
5–7 and the fail-closed rules for any future run. The pre-activation language
below remains the default for new or separately scoped operations.

The exact Phase 06 run `2026-0004` is owner-accepted at source revision
`2026-0004-src-rev`. Its outcome-only record was written, reviewed by
`openstack-platform-operations-lab-admin`, and accepted at
`2026-08-24T14:55:34Z` with no limitations.
The protected evidence reference is `2026-0004-evidence-prtct-ref`.
The accepted run does not broaden the contract, reuse stale run `2026-0002`, or
authorize capabilities outside its recorded scopes.

This contract does **not** authorize:

- account, credential, key, profile, policy, sudo, or role creation or modification;
- inspection of protected inventory, addresses, connection metadata, credentials, keys, raw output, logs, audits, or evidence;
- SSH, host contact, OpenStack authentication, API calls, source reads, negative tests, or workflow execution;
- live connector invocation, runner activation, deployment, host contact, live validation, or any protected-input operation; static contract reconciliation and synthetic tests remain non-activating; or
- Phase 06 live acceptance or Phase 07 exposure for any run not covered by a current owner-accepted outcome record.

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
| Diagnostic intents | `recent_metadata_errors`, `recent_neutron_errors`, and `recent_nova_errors` are the accepted D05 public identifiers and descriptions at `rev-2026-08-0002`; static registry entries remain unavailable for any run without the required protected runtime gates and live authorization. |
| Public selectors | A future request may contain only an approved non-secret `host_label`, `window_class`, and `line_limit_class`. It may never contain a destination, address, path, unit, command, source selector, account, key, port, SSH option, sudo option, timeout, or byte cap. |
| Observer files | The fixed candidate collector path is `/usr/local/libexec/openstack-ai-ops-assistant/host-observer-collector`; the fixed candidate policy path is `/etc/openstack-ai-ops-assistant/host-observer-policy.yml`. Their existence, owner, mode, regular-file status, and deployment are unapproved. |
| Authority isolation | Project-reader, operator-reader, and host-observer authority must remain independently revocable. Host diagnostics must receive no `OS_*` environment; API diagnostics must receive no observer state. |
| Historical reuse | Deferred host-diagnostic assets remain unselected under the selective-reuse manifest. No historical implementation may be inspected, copied, or adapted without an exact approved manifest amendment. |
| Default behavior | Missing capability, gate, projection, policy, key metadata, source approval, or authorization produces explicit `unavailable`, never success or fallback. |

## Decision register and accepted-run status

The entries below define the required outcome-only decisions and their
fail-closed effects for future runs. For the exact run `2026-0004`, the named
evidence owner accepted the complete scope package and final outcome; no D01–D09
or live-campaign gate remained unresolved.

| ID | Decision required | Required owner-approved outcome | Fail-closed effect while unresolved |
| --- | --- | --- | --- |
| D01 | Steps 1–4 prerequisite acceptance and the Phase 05 gate-label contradiction | Confirm the exact prerequisite disposition and evidence owner | No implementation beyond this contract; Phase 06 remains blocked. |
| D02 | Maintained inventory projection | Confirm source owner, revision/freshness, approved safe labels, role mappings, enablement/disablement, protected runtime location, and drift procedure | No host label is valid and no destination may be resolved. |
| D03 | Host-observer authority model | Review the proposed closed `authority_class` descriptor without overloading `credential_profile`; confirm isolation, lifecycle, and no `OS_*` environment | No live host authority use, connector invocation, or registry activation. |
| D04 | Observer account, key, forced transport, and sudo | Confirm account/key owners, source restriction, rotation/revocation, forced-stdin compatibility, no-forwarding restrictions, collector integrity, and whether sudo is required | No observer provisioning, SSH, collector invocation, or sudo policy. |
| D05 | Three public tool names and role/source matrix | Accepted at `rev-2026-08-0002`: exact names/descriptions, controller/compute role matrix, source classes, service classes, logical selectors, prohibited sources, and source outcomes | No live source read or activation. |
| D06 | Inputs and bounds | Accepted at `rev-2026-08-0002`: exact public inputs, defaults, allowlists, request/line/record/message/byte caps, timeouts, empty behavior, and truncation order | No caller-controlled source, path, unit, timeout, or output limit. |
| D07 | Output, unavailable, ordering, truncation, and redaction | Accepted at `rev-2026-08-0002`: exact schema, statuses, error classes/messages, enums, timestamps, ordering, redaction, canaries, serialization, and stubs | No source-derived success until the metadata implementation scope is separately validated. |
| D08 | Evidence, audit, rollback, and negative tests | Confirm evidence location/retention/audit access, unchanged-state comparator, rollback owner/order, and bounded positive/negative test plan | No live validation, audit inspection, revocation rehearsal, or acceptance claim. |
| D09 | Step 7 representative metadata case | Confirm safe pre/post state procedure, case owner, and advisory-only interpretation boundary | No workflow execution or diagnosis claim. |

## Confirmed safety decisions

The following safety decisions remain authoritative for the accepted run and
future runs. They do not broaden the accepted scopes or replace a fresh
owner-approved package when a new run changes authorization, revisions, inputs,
or targets:

- The canonical observer runtime username is `aiops-host-observer`. Connector,
  collector, policy, inventory, deployment, and test references must use this
  username consistently; `aiops-observer` is not an accepted alternate.
- Destination projection and collector metadata are separate schemas. The
  connector-only destination projection may contain the protected transport
  descriptor (`address`, `port`, and canonical observer `user`). Collector
  metadata may contain only non-secret host labels, inventory roles, source
  classes, enablement, and approved policy/bound metadata; it must never contain
  or emit a destination, address, connection metadata, key path, or transport
  credential.
- The connector resolves the private destination projection and sends only the
  closed diagnostic request to the forced collector. The collector does not
  resolve destinations and must not validate or receive connector transport
  fields.
- The protected destination projection is located at
  `/opt/openstack-ai-ops-assistant/credentials/host-observer/destination-projection.json`.
  Its parent directory is `aiops_assistant:aiops_assistant` with mode `0700`; the
  projection file is `aiops_assistant:aiops_assistant` with mode `0600`. The file
  is owner-generated or owner-installed, remains outside Git, and is never printed,
  audited, or exposed to callers.
- The destination projection carries an immutable owner-issued `revision`,
  `generated_at`, and `expires_at`, all validated as protected metadata. The
  projection is accepted only when `generated_at` is not future-dated,
  `expires_at` is later than `generated_at`, and the current time is no later than
  `expires_at`. Missing, malformed, future-dated, or expired metadata returns
  `unavailable/stale_projection`; callers cannot provide or override these fields.
  The maximum projection lifetime is 24 hours.
- The maintained OpenStack service-placement inventory is the source of truth.
  `OpenStack platform operations / lab administrator` owns both the source and
  the generated projection unless an explicit delegation is recorded. The
  generator must derive only approved host labels and destinations, reject
  missing, duplicate, ambiguous, disabled, or role-incompatible entries, and
  keep all addresses and connection metadata outside Git.
- The initial per-tool host mapping is:
  `recent_metadata_errors` -> `controller01` only;
  `recent_nova_errors` -> `controller01` only; and
  `recent_neutron_errors` -> `controller01`, `compute01`, and `compute02`.
  The corresponding permitted inventory roles are `controller` for metadata and
  Nova, and `controller` or `compute` for Neutron. No other host labels are
  accepted without a new reviewed mapping.
- The `controller01` destination is derived from the maintained inventory’s
  `controller01.mgmtnet_ip_address`, materialized only as a canonical protected
  IP in the destination projection, and contacted on TCP port 22 as
  `aiops-host-observer`. DNS names, alternate interfaces, caller overrides, and
  literal addresses in Git or normal output are prohibited.
- The observer key is a fresh, dedicated Ed25519 key generated or imported under
  `OpenStack platform operations / lab administrator` control, never copied from
  another runtime. Its private key is installed on `assistant02` at
  `/opt/openstack-ai-ops-assistant/credentials/host-observer/id_ed25519` with
  ownership `aiops_assistant:aiops_assistant` and mode `0600`. Only the public key
  is installed on approved observer hosts. Its authorized-key entry forces the
  collector and disables agent forwarding, X11 forwarding, TCP forwarding, PTY,
  and interactive shells.
- The observer authorized-key entry is restricted to the exact protected `/32`
  source address of `assistant02`’s management/observer interface. Broad subnets,
  hostnames, wildcards, and unrestricted sources are prohibited. If multiple
  stable egress addresses are unavoidable, each must be an explicitly approved
  `/32`; any source-address change requires key-policy and projection review plus
  a fresh acceptance run.
- The key rotation owner is `OpenStack platform operations / lab administrator`.
  The revocation owner is `OpenStack security or senior lab administrator`.
  Rotation must create and validate a replacement before retiring the old key;
  revocation must independently disable the observer key, account, and policy
  without affecting project-reader or operator-reader authority. Emergency
  revocation invalidates the current projection and requires fresh acceptance.
- The initial live scope requires no sudo: `sudo_required: false`. The collector
  runs as `aiops-host-observer`; unreadable approved sources return a bounded
  `denied` or `unavailable` result. No fallback sudo, ad hoc arguments, or broad
  privilege grant is permitted. Any later fixed collector-only sudo proposal
  requires a separate decision and fresh negative testing.
- `recent_metadata_errors` is approved only for `controller01` with the
  `controller` role and the fixed `metadata_service_errors` selector. Its
  reviewed sources are Neutron metadata-agent service evidence and
  `/var/log/apache2/nova_metadata_error.log`. No other journal, log path,
  configuration source, or caller-selected selector is permitted.
- `recent_neutron_errors` is approved with the fixed `neutron_service_errors`
  selector. On `controller01` it may read only `neutron-server` and
  `neutron-openvswitch-agent` error evidence. On `compute01` and `compute02` it
  may read only `neutron-openvswitch-agent` error evidence. Missing or unreadable
  units produce bounded unavailable/denied evidence, with no sudo fallback.
- `recent_nova_errors` is approved only for `controller01` with the `controller`
  role and the fixed `nova_service_errors` selector. Its reviewed sources are
  `nova-api`, `nova-conductor`, `nova-scheduler`, and
  `/var/log/apache2/nova_metadata_error.log`. No Nova source is approved on
  compute hosts in the initial scope; configuration, database, arbitrary Apache
  logs, caller-selected units, and caller-selected paths remain prohibited.
- The operator-reader profile source is a transient external-secret materialized
  directory at `/run/openstack-ai-ops/<run-id>/operator-reader/`. The source
  directory is operator-owned with mode `0700`; only `clouds.yaml` and
  `secure.yaml` are accepted, each with mode `0600`. The target profile remains
  `/opt/openstack-ai-ops-assistant/credentials/operator-reader`, owned by
  `aiops_assistant:aiops_assistant` with directory mode `0700` and file mode
  `0600`. The transient source is deleted after successful materialization and
  metadata verification; its contents never enter Git, logs, audits, or output.
- The operator-reader identity/scope and rotation owner is `OpenStack platform
  operations / lab administrator`. The revocation owner is `OpenStack security
  or senior lab administrator`. Operator-reader credentials have a maximum
  lifetime of 24 hours. Rotation creates and validates a replacement before
  retirement; revocation independently removes the operator profile/credential.
  Expiry or revocation invalidates associated acceptance evidence, and
  mutation-denial evidence must be refreshed after every credential revision.
- The approved live run uses authorization reference
  `phase06-live-acceptance-2026-0004` and non-secret run ID `2026-0004`, with
  authorization class `phase06-restricted-diagnostics-live-acceptance`. This
  reference covers only the explicitly approved Phase 06 scopes; it does not
  authorize Phase 07, unrelated hosts, broader credentials, or remediation.
- Outcome-only evidence is owned by `OpenStack platform operations / lab
  administrator` and stored under
  `/opt/openstack-ai-ops-assistant/evidence/phase06/`, with the normalized
  producer result at `/run/openstack-ai-ops/phase06-validation/2026-0004.json`.
  The evidence directory is `aiops_assistant:aiops_assistant`, mode `0700`; each
  record is mode `0600`; the access role is `phase06-evidence-reviewer`; and the
  retention label is `restricted-phase06-acceptance-90d`. Only normalized
  outcome fields may be retained. Raw logs, addresses, commands, credentials,
  audit lines, source payloads, and comparator data are excluded.
- The representative live metadata case is approved to select one server at
  runtime from accepted `project_resource_summary` evidence, then run
  `server_basic_info`, `server_network_info`, `neutron_agent_health`, and all
  three host diagnostics on `controller01`. One additional
  `recent_neutron_errors` call on `compute01` exercises the compute-role mapping;
  `compute02` is validated separately as its own host/source scope. The case is
  read-only, retains only normalized outcome evidence, requires unchanged-state
  confirmation, and produces advisory-only interpretation.

These decisions narrow D02/D04 but do not resolve their remaining lifecycle,
source-policy, or live-authorization gates.

## Diagnostic and projection contract

The three accepted diagnostic identifiers each select exactly one source class. A caller must never select a source, role, destination, path, unit, command, transport option, or authority. The accepted tool name, source class, source-to-role matrix, and deployment state must be evaluated before any transport construction.

A projection resolver has this closed behavior:

```text
approved tool name + approved host label + owner-approved projection
  -> fixed private destination descriptor
  | unavailable | denial | integrity error
```

The descriptor is private implementation state. It must not be emitted in a result, audit record, argument list, environment, repository document, fixture, or normal command output. Missing, stale, duplicate, disabled, ownerless, ambiguous, or role-incompatible projection data stops before child-process creation or network contact.

The separation between the connector-only destination projection and collector
metadata is confirmed. The destination projection is an owner-issued JSON
projection at `/opt/openstack-ai-ops-assistant/credentials/host-observer/destination-projection.json`
with an `aiops_assistant:aiops_assistant` `0700` parent directory and `0600`
regular file. It contains `projection_type: host_observer_destination`, immutable
`revision`, `generated_at`, `expires_at`, and protected transport entries. The
collector metadata schema contains `projection_type: host_observer_metadata` and
non-transport entries only. Synthetic labels may be used only in fixtures/tests;
protected values remain outside Git and are never emitted.

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
| `recent_neutron_errors` | `neutron_error_events` | `controller`, `compute` | `neutron` | `neutron_service_errors` |
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

## Live-acceptance readiness prerequisite

`docs/ai-ops-revised/runtime/phase06-live-acceptance-readiness-requirement.md`
is the non-activating prerequisite for the exact acceptance run. It defines two
ordered local gates that retain only normalized outcomes:

1. A campaign authorization gate validates the Phase 05 prerequisite, owner
   approvals, current references/timestamps, deployment-source integrity
   references, and rollback ownership before operator-reader or observer
   deployment. It does not create a readiness manifest or authorize host contact.
2. A runtime readiness gate runs after both authorities are deployed and checks
   all 8 deployed-state integrity outcomes. Only a successful runtime gate may
   materialize or consume the closed `status: ready` manifest before host/source
   contact.

The manifest must not expose protected values, and either gate fails closed
rather than authorizing an adjacent scope. The approved requirement fixes the
manifest top-level fields, exact `scope_approvals` entries and scope/status
enums, plus closed `protected_input_references` and `integrity_checks` schemas.
A validator must reject unknown, duplicate, missing, or protected-value fields
and fail closed rather than infer a value or broaden a scope.

## Completion criteria and next action

The exact Phase 06 run `2026-0004` is complete and owner-accepted at source
revision `2026-0004-src-rev`. The normalized evidence record reports accepted
outcomes for all seven tools, 11 scopes, 18 negative controls, seven audit
pairs, attestations, unchanged-state comparison, rollback, and the
representative workflow, with no unresolved gates.

The accepted run permits Phase 06 plan and operations-contract reconciliation
and Phase 07 planning. It does not authorize MCP implementation or exposure by
itself; Phase 07 must establish and validate its own local, runner-boundary,
non-network contract before implementation.
