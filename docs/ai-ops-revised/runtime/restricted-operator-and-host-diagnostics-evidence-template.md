# Restricted Operator and Host Diagnostics Outcome-Only Evidence

This template records only normalized evidence for the restricted-operator and host-diagnostics gates. It is not an authorization to deploy, execute, contact hosts, inspect protected audit data, or revoke credentials.

The corresponding administrator-approved record must be stored outside Git at an approved protected location. Do not replace any field with credentials, private keys, addresses, raw commands, stdout, stderr, raw logs, resource identifiers, or comparator data.

## Metadata

- Source revision:
- UTC timestamp:
- Non-secret run ID:
- Environment label:
- Host-group label:
- Runtime label:
- Evidence owner:
- Authorization class:
- Retention policy label:
- Access-role label:

## Normalized outcome

- Overall status: `accepted` | `unavailable` | `blocked` | `failed`
- Limitation class:
- Rollback status: `not_required` | `pending` | `complete` | `failed`
- Unresolved gate labels:

## Bounded validation booleans

- Phase 05 acceptance confirmed:
- Neutron read classified:
- Operator-reader reviewed:
- Observer policy reviewed:
- Negative test plan approved:
- Output schema frozen:
- Redaction check completed:

## Retention boundary

Only the fields above may be retained. Raw task results and protected inputs must remain transient and must not appear in Ansible output or repository files.
