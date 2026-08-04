# Revised AI-OPS Identity and Policy Operations Contract

## Status and Authority

This contract records the Phase 02 credential, policy, lifecycle, and evidence
boundary approved before any revised identity, credential, profile, or OpenStack
authority exists. It is subordinate to:

- `docs/ai-ops-revised/runtime/foundation-operations-contract.md`
- `docs/ai-ops-revised/runtime/runtime-placement-contract.md`
- `docs/ai-ops-revised/runtime/selective-reuse-manifest.md`
- `docs/ai-ops-revised/implementation-plan/ads/02-00-readonly-identity-and-policy-boundary-ads.md`

It does not authorize credential creation, profile materialization, host
connection, Ansible execution, authentication, OpenStack API calls, policy
changes, or cleanup operations.

## Approved Identity and Lifecycle Matrix

| Concern | Approved contract |
| --- | --- |
| Project | `admin` project only; this is a project label, not administrator authority. |
| Identity domain | `default` |
| Fresh revised identity | `aiops-assistant-project-reader` |
| Assigned role | `reader` only |
| Application-credential label | `reader_platformpass` (non-secret administrative label) |
| Credential provenance | Fresh credential for the revised identity; no historical, human, member, service, or administrator credential may be reused. |
| Credential scope | Restricted to project `admin` and role `reader`. |
| Expiry and rotation | Expires after one month; the OpenStack admin team replaces it before expiry. |
| Revocation owner | OpenStack admin team |
| Immediate-revocation triggers | Any mutation success or suspected credential exposure. |

The OpenStack admin team creates the identity, assigns the role, creates the
restricted application credential, retains non-secret creation/revocation
metadata in its approved operator system, and performs all revocation,
verification, restoration, and cleanup. The revised runtime has no identity or
policy administration authority.

## Transport and Runtime Profile Boundary

The approved Local-Lab SSH Transport Exception applies only to `assistant02` in
the `local` inventory. It must not be copied to another inventory or
environment. All other transport requires host verification and an
operator-approved known-hosts source.

The only revised profile is `aiops-assistant-project-reader`. Its destination
layout is:

```text
/opt/openstack-ai-ops-assistant/credentials/profiles/
  clouds.yaml
  secure.yaml
```

The profile directory is `0700` and every profile file is a regular, non-symlink
file with mode `0600`; all are owned by `aiops_assistant:aiops_assistant`.
Profile content, credential values, IDs, tokens, passwords, private keys,
checksums, and rendered configuration are protected values and must not enter
Git, evidence, command arguments, inherited environments, or output.

## External Secret Source and Transfer

The approved source is a transient controller-local directory:

```text
/run/openstack-ai-ops/<run-id>/
```

The directory is operator-owned with mode `0700`; `clouds.yaml` and
`secure.yaml` are each mode `0600`. The operator materializes fresh credential
content there from an approved external secret system immediately before the
reviewed deployment. Ansible receives only the non-secret source-directory path,
uses `no_log: true` for every secret-observing task, and copies only the two
approved filenames. The transient source is removed after successful
materialization and metadata verification.

`generated/clouds.yaml` may inform an administrator's redacted project and
identity decision record, but it is not an approved deployment source and must
not be read or copied by the agent. No source may be in the repository,
historical runtime, shell arguments, process-visible environment, backups, or
profile-derived evidence.

## Required Read and Unavailable-Authority Matrix

The project-reader validation uses fixed argument-vector operations only. It
retains an operation label and normalized result class, never resource payloads,
identifiers, addresses, stdout, stderr, catalog data, or token output.

| Required operation | Acceptance rule |
| --- | --- |
| Token issuance and project scope | Must be `pass`. |
| Server, network, subnet, port, volume, image, and security-group list/show | Each must be `pass` or an administrator-approved `empty` result. |

The only normalized result classes are `pass`, `empty`, `policy_denied`,
`service_unavailable`, `catalog_missing`, `connectivity_error`,
`authentication_error`, and `configuration_error`. A result other than `pass`
or an approved `empty` blocks the required-read gate; it must not trigger a role
or policy expansion.

Service, hypervisor, Neutron-agent, broader cloud-health, operator-reader,
administrator, member, service, database, message-bus, provider, egress, and
host-diagnostic authority remain unavailable and deferred.

## Mutation-Denial and Emergency Contract

The OpenStack admin team prepares separate, uniquely named disposable security
groups and records their identifiers and baselines only in its approved external
operator system. It owns postcondition verification, restoration, and cleanup.

| Probe | Target | Acceptance |
| --- | --- | --- |
| Create | A unique security-group create request | Conclusive authorization denial; no created probe exists. |
| Update | Disposable security group A description | Conclusive authorization denial; baseline remains unchanged. |
| Delete | Separate disposable security group B | Conclusive authorization denial; target still exists. |

### Controlled Invocation Inputs

The administrator supplies non-secret runtime values through its approved
operator procedure; values and identifiers must not be retained in Git, shell
history, console output, or evidence. For a run ID `<run-id>`, the update target
must be named `aiops-deny-<run-id>-update`, its externally recorded baseline
description must be `ai-ops phase02 baseline <run-id>`, and the separate delete
target must be named `aiops-deny-<run-id>-delete`. The fixed update request sets
the update target description to `ai-ops phase02 update-denial <run-id>`.

The validation play rejects any other target or baseline input before running a
CLI command. It reports normalized results only; the administrator records the
baseline and verifies, out of band, that the update target remains unchanged and
the delete target still exists.

Run probes in create, update, then delete order. A conclusive denial requires a
non-zero CLI result plus the installed client's approved explicit HTTP `403` or
`Forbidden` signature and the administrator-owned postcondition check. A `404`,
malformed input, missing catalog, timeout, connectivity failure, or unrecognized
non-zero result is inconclusive and cannot satisfy a denial check.

On any mutation success, stop immediately. The OpenStack admin team revokes the
credential, verifies impact, and performs restoration or cleanup; the
project-reader credential is never used for cleanup.

## Evidence and Retention

The approved external evidence location is:

```text
/var/lib/openstack-ai-ops-evidence/phase02/<run-id>.md
```

The evidence directory is operator-owned with mode `0700`; each record is mode
`0600`. It is outside Git and the credential directory. A record may contain
only source revision, UTC timestamp, non-secret run identifier, host/group and
profile labels, approved project/domain/role labels, operation label, normalized
result class, denial boolean, administrator postcondition boolean, revocation
status, and unresolved gates.

It must not retain credential values or IDs, tokens, passwords, private keys,
profile content, checksums, command arguments, stdout, stderr, resource payloads,
resource identifiers, addresses, catalog data, or response bodies.

## Lifecycle Rehearsal Status

The approved lifecycle rehearsal is accepted in outcome-only form. The protected
replacement profile deployment and its identical rerun completed with no changes;
the required project-reader authentication and read matrix accepted only `pass`
or approved `empty` results. The prior approved mutation-denial matrix retained
only conclusive denial outcomes and administrator-confirmed postconditions.

The OpenStack administrator confirmed that the superseded credential was revoked
and that a no-log authentication attempt with it failed. No credential value,
identifier, profile content, command argument, or raw output is retained here.
Operator-reader remains unavailable. Transient-source removal and any stale
runtime-local profile removal remain administrator-owned actions and must be
recorded only in approved external outcome-only evidence before operational
closure.

## Historical Reuse and Rollback

The three historical Phase 02 candidate paths are reference-only. Their behavior
may inform review, but no content, variables, generated profile, credential, or
validation implementation may be copied or activated. The revised implementation
must be derived from this contract and independently validated.

Before authority exists, rollback is to remove only agent-created documentation
changes. After a separately approved deployment, rollback stops revised
automation, has the OpenStack admin team revoke the credential, removes only the
revised runtime-local profile through the approved operator procedure, and
retains redacted evidence. It must not alter `assistant01`, historical runtime
paths, protected inventory, or unrelated OpenStack resources.

## Live-Execution Gate

No live Phase 02 action is authorized until a reviewer confirms this contract,
the external secret procedure, disposable targets, client authorization
signature, evidence handling, and the scoped transport exception. Any missing or
ambiguous item fails closed.
