# Phase 06 Live-Acceptance Readiness Requirement

## Status and purpose

This is a **non-activating requirement** for preparing Phase 06 live acceptance. It authorizes planning and gate reconciliation only. It does not authorize credential use, deployment, SSH, OpenStack API calls, host contact, source reads, negative testing, audit inspection, rollback, or workflow execution.

Phase 06 live acceptance may begin only when this requirement is satisfied for the exact run and every separately authorized scope passes its fail-closed gate.

## Governing authorization package

The administrator-owned authorization package is:

- Authorization reference: `phase06-live-acceptance-2026-0004`
- Non-secret run ID: `2026-0004`
- Authorization class: `phase06-restricted-diagnostics-live-acceptance`
- Primary owner: OpenStack platform operations / lab administrator
- Emergency revocation owner: OpenStack security or senior lab administrator

The package must contain separate approvals for deployment, one host/source contact, positive validation, negative boundary validation, outcome-only evidence recording, protected audit inspection, unchanged-state comparison, revocation/rollback, and the representative workflow. One broad approval must not substitute for these scope approvals.

## External materialization boundary

Protected inputs must be materialized by the approved external inventory, secret, and operator procedures. The agent must receive only non-secret paths, labels, run identifiers, approval references, and normalized gate results.

The external procedure must provide the non-secret readiness manifest at:

```text
/run/openstack-ai-ops/2026-0004/phase06-readiness.json
```

The parent directory must be operator-controlled with mode `0700`; the manifest must be a regular, non-symlink file with mode `0600`, and its serialized size must not exceed `16384` bytes. It is read-only input to gate validation and must be deleted after the run. The manifest must not contain addresses, credentials, private keys, profiles, raw logs, commands, audit lines, source payloads, or comparator data.

The external procedure separately materializes and protects:

- Destination projection: `/opt/openstack-ai-ops-assistant/credentials/host-observer/destination-projection.json`
- Operator-reader source: `/run/openstack-ai-ops/<run-id>/operator-reader/`
- Operator-reader target: `/opt/openstack-ai-ops-assistant/credentials/operator-reader`
- Observer private key: `/opt/openstack-ai-ops-assistant/credentials/host-observer/id_ed25519`
- Host collector: `/usr/local/libexec/openstack-ai-ops-assistant/host-observer-collector`
- Host policy: `/etc/openstack-ai-ops-assistant/host-observer-policy.yml`

Protected contents remain outside Git, chat, shell history, logs, audit records, and normal command output.

## Readiness-manifest contract

The manifest uses `schema_version: "1.0"` and a closed schema. Unknown fields, duplicate keys, unsafe paths, stale revisions, invalid statuses, or protected-value fields fail closed.

Top-level fields are:

- `schema_version`
- `run_id`
- `authorization_reference`
- `authorization_class`
- `source_revision`
- `environment_label`
- `evidence_owner`
- `scope_approvals`
- `protected_input_references`
- `integrity_checks`
- `status`
- `issued_at`
- `expires_at`

Each `scope_approvals` entry contains exactly:

- `scope`;
- `status`;
- `owner_label`;
- `authorization_reference`; and
- `outcome_evidence_reference`.

`scope` must occur exactly once for each of: `prerequisite_readiness`,
`operator_reader_deployment`, `observer_deployment`, `host_source_contact`,
`positive_validation`, `negative_boundary_validation`,
`outcome_evidence_recording`, `protected_audit_inspection`,
`unchanged_state_comparison`, `revocation_rollback`, and
`representative_workflow`. `status` is one of `approved`, `pending`, `denied`,
`revoked`, or `expired`. `owner_label`, `authorization_reference`, and
`outcome_evidence_reference` are non-secret opaque references, not paths or
protected values.

`protected_input_references` is an object with exactly these opaque,
non-secret revision fields:

- `manifest_revision`;
- `destination_projection_revision`;
- `operator_reader_revision`;
- `observer_key_revision`;
- `host_collector_revision`; and
- `host_policy_revision`.

`integrity_checks` is an object with exactly these keys:

- `destination_projection_directory`;
- `destination_projection_file`;
- `destination_projection_freshness`;
- `operator_reader_source`;
- `operator_reader_target`;
- `observer_private_key`;
- `host_collector`; and
- `host_policy`.

Each integrity-check value contains exactly `status` and
`outcome_evidence_reference`. Integrity `status` is one of `passed`, `blocked`,
`failed`, or `unavailable`; its evidence reference is a non-secret opaque
identifier, not a path or protected value. The manifest `status` is one of
`ready`, `blocked`, `failed`, or `unavailable`. `ready` requires every scope
approval to be `approved`, every integrity check to be `passed`, and all
revisions to match the accepted run.

The manifest must use the approved run/reference/class, have current `issued_at` and `expires_at` metadata, and expire within 24 hours. Projection, credential, key, policy, manifest, and source revisions must belong to the same accepted run. Any revision or expiry mismatch requires a fresh run ID and approvals.

## Protected-input integrity gates

Before any live scope, gate validation must confirm outcomes without exposing protected values:

- Projection directory: `aiops_assistant:aiops_assistant`, `0700`.
- Projection file: `aiops_assistant:aiops_assistant`, `0600`, regular, non-symlink.
- Projection metadata: owner-issued revision; `generated_at <= now <= expires_at`; lifetime no greater than 24 hours.
- Operator-reader source: only `clouds.yaml` and `secure.yaml`; directory `0700`; files `0600`.
- Operator-reader target: `aiops_assistant:aiops_assistant`; directory `0700`; files `0600`.
- Observer private key: dedicated Ed25519 key; `aiops_assistant:aiops_assistant`; `0600`.
- Host collector: root-owned, group `aiops-host-observer`, mode `0750`.
- Host policy: root-owned, mode `0600`.
- All protected files: regular and non-symlinked.

Protected task state may hold validation details only under `no_log`; exported evidence contains normalized pass/fail outcomes only.

## Ownership matrix

| Concern | Owner |
| --- | --- |
| Maintained inventory and destination projection | OpenStack platform operations / lab administrator |
| Observer account deployment/removal | OpenStack platform operations / lab administrator |
| Observer key rotation | OpenStack platform operations / lab administrator |
| Emergency observer revocation | OpenStack security or senior lab administrator |
| Operator-reader lifecycle | OpenStack platform operations / lab administrator |
| Outcome-only evidence | OpenStack platform operations / lab administrator |
| Rollback execution | OpenStack platform operations / lab administrator |
| Final acceptance decision | Named evidence owner after all scope outcomes pass |

## Scope order and stop conditions

Scopes execute one at a time, with a fresh normalized outcome for each:

1. Reconcile prerequisites and validate the readiness manifest.
2. Deploy the operator-reader authority.
3. Deploy the observer account, key policy, collector, and host policy.
4. Contact one approved host and one approved source class.
5. Run positive collector validation.
6. Run all approved negative SSH, forwarding, sudo, and source-boundary controls.
7. Record normalized outcome-only evidence.
8. Inspect protected audit results under separate authorization.
9. Compare owner-controlled unchanged-state attestations.
10. Rehearse revocation and rollback.
11. Run the representative advisory-only workflow.

Stop immediately on missing, stale, contradictory, malformed, unauthorized, or unsafe evidence. Do not retry with broader permissions, alternate hosts, alternate addresses, fallback credentials, caller-selected sources, or ad hoc sudo.

## Approved host and source matrix

Only these host/source pairs are allowed:

- `recent_metadata_errors` → `controller01` only.
- `recent_nova_errors` → `controller01` only.
- `recent_neutron_errors` → `controller01`, `compute01`, and `compute02`.

The observer user is `aiops-host-observer`, transport is TCP port `22`, and the initial scope requires `sudo_required: false`. Host labels must resolve through the owner-approved projection. No DNS name, literal address, alternate interface, caller override, or unapproved host is permitted.

Approved source policy is:

- Metadata on `controller01`: Neutron metadata-agent evidence and `/var/log/apache2/nova_metadata_error.log`.
- Neutron on `controller01`: `neutron-server` and `neutron-openvswitch-agent`.
- Neutron on `compute01` and `compute02`: `neutron-openvswitch-agent`.
- Nova on `controller01`: `nova-api`, `nova-conductor`, `nova-scheduler`, and `/var/log/apache2/nova_metadata_error.log`.

Configuration dumps, databases, arbitrary logs/journals, recursive scans, caller-selected selectors, and source broadening are prohibited.

## Bounds and disclosure controls

Every diagnostic must enforce the frozen D05–D07 contract:

- Windows: `15m`, `30m`, `1h`; default `30m`.
- Source lines: `50`, `100`, `200`; default `medium`.
- Maximum records: `20`.
- Raw summary: `4096` bytes.
- Normalized summary: `512` bytes.
- Collector output: `16384` bytes.
- Collector timeout: `5s`.
- Runner timeout: `15s`.

Callers cannot override source, path, unit, selector, timeout, line, byte, or record limits. Truncation is explicit and remains an evidence limitation.

Redaction occurs on the host before transport and again at the runner boundary. The replacement is `[REDACTED]`. Passwords, tokens, authorization values, private keys, credential URLs, addresses, MACs, UUIDs/resource IDs, hostnames, and host-like summary identifiers must be removed. A surviving synthetic canary or redaction failure discards all source-derived output and stops acceptance.

Each request receives a distinct correlation ID and sanitized audit event. Audit data must not contain projection contents, addresses, commands, credentials, raw requests, raw evidence, or secrets.

## Negative-control requirements

All 18 observer controls must be denied:

- interactive shell and PTY;
- agent, X11, local, remote, and tunnel forwarding;
- arbitrary commands and extra arguments;
- environment injection and destination bypass;
- out-of-policy file reads;
- editor, package-manager, and service-control execution;
- unrestricted or alternate-argument sudo; and
- collector output redirection.

Any unexpected success is a critical failure. Stop testing, disable or revoke the affected authority, preserve only normalized failure evidence, and do not continue.

## Evidence and unchanged-state requirements

Outcome-only evidence uses:

- Producer result: `/run/openstack-ai-ops/phase06-validation/2026-0004.json`
- Retained directory: `/opt/openstack-ai-ops-assistant/evidence/phase06/`
- Directory mode: `0700`
- Record mode: `0600`
- Access role: `phase06-evidence-reviewer`
- Retention label: `restricted-phase06-acceptance-90d`

Evidence may contain only normalized statuses, limitation classes, gate booleans, run/reference metadata, and rollback status. It must not contain raw logs, addresses, commands, credentials, keys, audit lines, source payloads, identifiers, or comparator data.

The platform operations owner supplies pre/post state attestations. Deployment is compared against an approved expected observer-deployment manifest; diagnostic execution must not change OpenStack resources, services, configuration, guest state, or unrelated host state. A missing, contradictory, or changed post-state attestation invalidates acceptance.

## Representative workflow

The final workflow scope is:

1. Select one server from accepted `project_resource_summary` output.
2. Run `server_basic_info` and `server_network_info` for that same server.
3. Run `neutron_agent_health` only if separately accepted and available.
4. Run all three host diagnostics on `controller01`.
5. Run one additional `recent_neutron_errors` call on `compute01`.
6. Validate `compute02` as a separate host/source scope.
7. Produce an evidence-gap-aware, advisory-only interpretation.

The workflow must not claim causality, execute remediation, broaden authority, or suppress unavailable, stale, denied, failed, timed-out, truncated, or contradictory evidence.

## Acceptance decision rule

Phase 06 may be marked `accepted` only when:

- every required scope has explicit authorization;
- all protected inputs pass integrity and freshness checks;
- required positive diagnostics return schema-valid, redacted, audited `ok` or approved `empty` outcomes;
- all negative controls are denied;
- no state changes occur outside the approved deployment manifest;
- outcome-only evidence is recorded and owner-accepted;
- protected audit inspection passes;
- revocation/rollback succeeds; and
- the representative workflow completes without unresolved required evidence gaps.

Otherwise the result is `blocked`, `unavailable`, or `failed`.

A failed, changed, expired, revoked, or contradictory prerequisite invalidates the current run. Generate a fresh run ID after any gate, source revision, projection, key, policy, or authorization change. Blocked run `2026-0002` and stale evidence must never be reused.

## Implementation-readiness gate

No protected live input may be used until the repository implementation is ready and validated. Readiness requires:

- live metadata, Neutron, and Nova source adapters;
- protected projection, key, and policy integration;
- observer account and forced-collector deployment;
- operator-reader deployment integration;
- runner and evidence wiring for all seven tools;
- positive and negative execution paths;
- unchanged-state and rollback recording; and
- targeted regression and security validation.

The current synthetic collector, unavailable connector/runner boundary, and project-reader-only validation producer do not satisfy this gate.

## References

- `docs/ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-steps-05-to-07-operations-contract.md`
- `docs/ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-evidence-template.md`
- `docs/ai-ops-revised/implementation-plan/ads/06-01-restricted-operator-and-host-diagnostics-steps-05-to-07-ads.md`
- `docs/ai-ops-revised/implementation-plan/06-restricted-operator-and-host-diagnostics.md`
- `ansible/ai_ops_assistant/playbook_validate_host_observer_scope.yml`
- `ansible/ai_ops_assistant/playbook_record_restricted_diagnostics_evidence.yml`
