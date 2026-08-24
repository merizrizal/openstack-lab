# Phase 06 Steps 5–7 Owner Decision Request — Outcome-Only Template

Use this template to request administrator-owned decisions for the restricted host-observer diagnostics. It records only non-secret outcomes and references. It does **not** authorize implementation, deployment, host contact, authentication, source reads, audit inspection, negative testing, rollback, or Phase 06/Phase 07 acceptance.

Store the completed administrator record outside Git at an approved protected location. Do not put credentials, private keys, authorized-key lines, addresses, hostnames, inventory contents, destination descriptors, connection metadata, raw commands, raw stdout/stderr, raw logs, raw audits, resource identifiers, or comparator data in this template or its completed record.

A blank, `unconfirmed`, `blocked`, `rejected`, or contradictory response leaves the affected capability unavailable. Approval for one decision or authorization scope does not approve another.

The authoritative decision register and fail-closed rules are in `docs/ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-steps-05-to-07-operations-contract.md`.

## Request metadata

- Request ID:
- Requested UTC date:
- Source revision:
- Requesting role/team:
- Decision owner role/team:
- Evidence owner role/team:
- Protected evidence reference:
- Retention policy label:
- Environment label:
- Non-secret run ID: leave blank until a separately authorized operation is planned.

## Response convention

For each decision, record only:

- Status: `unconfirmed` | `accepted` | `blocked` | `rejected`;
- Owner role/team;
- Outcome-only decision summary;
- Protected evidence reference;
- Source revision and UTC review timestamp; and
- Limitations, follow-up, or blocker label.

Do not mark a decision `accepted` based only on documentation, static tests, generated templates, or file existence. Owner acceptance must cover the exact scope requested.

## D01 — Steps 1–4 prerequisite and Phase 05 disposition

**Requested decision:** Confirm the owner-accepted prerequisite disposition for Steps 1–4, including resolution or explicit blocking status of the Phase 05 gate-label contradiction.

- Status: `unconfirmed`
- Owner role/team:
- Outcome-only prerequisite disposition:
- Protected evidence reference:
- Source revision and UTC review timestamp:
- Limitations or blocker label:

**If not accepted:** Phase 06 remains blocked; no implementation beyond non-activation documentation is permitted.

## D02 — Maintained inventory projection

**Requested decision:** Confirm the maintained projection's owner, source revision/freshness process, approved safe label and role classes, service mappings, enablement/disablement decision process, protected runtime location class, and drift handling.

- Status: `unconfirmed`
- Owner role/team:
- Outcome-only approved role/label classes:
- Projection freshness and drift outcome:
- Protected projection-location reference:
- Protected evidence reference:
- Source revision and UTC review timestamp:
- Limitations or blocker label:

**Do not include:** hostnames, addresses, inventory entries, destination descriptors, connection variables, or protected projection content.

**If not accepted:** no host label is valid; no destination resolution or host contact is permitted.

## D03 — Host-observer authority model

**Requested decision:** Approve, reject, or replace the closed host-observer `authority_class` direction while preserving project-reader and operator-reader isolation and excluding `OS_*` environment variables from host diagnostics.

- Status: `unconfirmed`
- Owner role/team:
- Outcome-only authority-model decision:
- Isolation and independent-revocation outcome:
- Protected evidence reference:
- Source revision and UTC review timestamp:
- Limitations or blocker label:

**If not accepted:** no host authority descriptor, connector, or host-tool registry mapping is permitted.

## D04 — Observer identity, forced transport, and sudo

**Requested decision:** Confirm observer lifecycle ownership, source restriction, rotation/revocation, forced-command behavior, bounded standard-input compatibility, forwarding restrictions, collector integrity requirements, and whether sudo is not required or separately accepted.

- Status: `unconfirmed`
- Owner role/team:
- Outcome-only identity and lifecycle decision:
- Outcome-only forced-transport compatibility decision:
- Sudo decision: `unconfirmed` | `not_required` | `accepted`
- Protected evidence reference:
- Source revision and UTC review timestamp:
- Limitations or blocker label:

**Do not include:** account credentials, key content, authorized-key lines, SSH arguments, destinations, or sudo rule contents.

**If not accepted:** no observer provisioning, SSH, collector invocation, or sudo policy is permitted.

## D05 — Tool names and source-to-role matrix

**Requested decision:** Freeze the three diagnostic names/descriptions, permitted role classes, source classes, and explicit prohibited sources for metadata, Neutron, and Nova evidence.

- Status: `unconfirmed`
- Owner role/team:
- Accepted tool-name outcome:
- Accepted role/source-class outcome:
- Prohibited-source outcome:
- Protected evidence reference:
- Source revision and UTC review timestamp:
- Limitations or blocker label:

**Do not include:** raw log paths, journal units, listener endpoints, configuration locations, or source contents.

**If not accepted:** no source read or tool registration is permitted.

## D06 — Inputs and bounds

**Requested decision:** Freeze the closed public input classes, defaults, validation rules, timeout, record, line, message, and total-byte bounds.

- Status: `unconfirmed`
- Owner role/team:
- Outcome-only input-class decision:
- Outcome-only bounds/defaults decision:
- Protected evidence reference:
- Source revision and UTC review timestamp:
- Limitations or blocker label:

**If not accepted:** no request schema is valid; callers cannot select a host, source, timeout, or output limit.

## D07 — Output, unavailable states, ordering, truncation, and redaction

**Requested decision:** Freeze normalized output fields/types, unavailable and error classes, deterministic ordering/truncation behavior, redaction rules, and redaction-canary acceptance criteria.

- Status: `unconfirmed`
- Owner role/team:
- Outcome-only output-schema decision:
- Outcome-only unavailable/truncation decision:
- Outcome-only redaction/canary decision:
- Protected evidence reference:
- Source revision and UTC review timestamp:
- Limitations or blocker label:

**Do not include:** sample raw evidence, raw log lines, secrets, identifiers, addresses, or audit records.

**If not accepted:** only an explicit non-success unavailable/authorization-pending state with no source-derived data is permitted.

## D08 — Evidence, audit, rollback, and negative-test scope

**Requested decision:** Confirm protected evidence location/retention, audit-inspection authority, unchanged-state comparator owner, rollback ownership/order, and bounded positive/negative test authorization requirements.

- Status: `unconfirmed`
- Owner role/team:
- Outcome-only evidence/retention decision:
- Outcome-only audit and comparator decision:
- Outcome-only rollback decision:
- Outcome-only positive/negative test-plan decision:
- Protected evidence reference:
- Source revision and UTC review timestamp:
- Limitations or blocker label:

**If not accepted:** no live validation, audit inspection, state comparison, negative test, revocation rehearsal, rollback rehearsal, or acceptance claim is permitted.

## D09 — Representative Step 7 metadata workflow case

**Requested decision:** Confirm a safe representative case, its owner, pre/post unchanged-state procedure, evidence-gap handling, and advisory-only interpretation boundary.

- Status: `unconfirmed`
- Owner role/team:
- Outcome-only representative-case decision:
- Outcome-only unchanged-state and evidence-gap decision:
- Protected evidence reference:
- Source revision and UTC review timestamp:
- Limitations or blocker label:

**If not accepted:** the Step 7 workflow cannot execute and cannot make a diagnosis claim.

## Authorization-scope acknowledgement

The following remain separate authorizations even when D01–D09 are accepted:

- observer account/key/policy/collector deployment;
- one approved host and source-class contact;
- positive collector validation;
- negative SSH, forwarding, sudo, and source-boundary validation;
- protected audit/evidence inspection;
- unchanged-state comparison;
- authority revocation or rollback rehearsal; and
- the representative Step 7 workflow case.

- Acknowledged by owner role/team:
- UTC timestamp:
- Limitations or blocker label:

## Final review outcome

- Overall decision status: `unconfirmed` | `accepted` | `blocked` | `rejected`
- Decisions accepted:
- Decisions remaining unavailable:
- Next separately authorized scope, if any:
- Protected evidence reference:
- Source revision and UTC timestamp:

Completing this template does not change repository defaults, generated inputs, playbook gates, registry entries, or live authorization state.
