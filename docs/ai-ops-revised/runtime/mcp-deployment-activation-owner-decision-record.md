# MCP Deployment and Activation Owner-Decision Record

## Status and scope

This record captures the non-secret decisions supplied during the owner grilling
session following handoff `200-phase08-mcp-deployment-activation-chunk0-contract-created-handoff.md`.
It is subordinate to
`mcp-deployment-activation-and-live-validation-operations-contract.md`.

This record does not prove that the referenced approvals, protected artifacts,
wheelhouse, readiness manifest, or host state exist. It does not authorize host
contact, package acquisition, dependency installation, TLS handling, firewall
mutation, process/listener startup, runner calls, audit inspection, or rollback.

## Decision record

### D01 — Approved Python runtime

```text
executable: /usr/bin/python3
implementation: CPython
version: 3.12.3
ABI: cpython-312
architecture: x86_64
sysconfig platform: linux-x86_64
GLIBC: 2.39
```

The supplied runtime evidence did not include a `packaging.tags` wheel-platform
result. The approved offline builder must therefore record and verify the exact
wheel compatibility tags before publication. The repository's existing
wheelhouse convention uses `manylinux_2_17_x86_64`; that convention is not, by
itself, acceptance evidence for this MCP closure.

### D02 — Dependency closure strategy

Local stdio and Option B will use one identical approved dependency closure,
installed into separate dedicated virtual environments. The closure remains
specific to CPython 3.12 on x86_64 and must contain exactly the approved
`mcp==1.28.1` transitive dependency set without extras.

### D03 — Offline build, publication, and transfer

Dependency generation will occur in a separate approved immutable offline build
environment. `builder01` will verify and publish the reviewed seed; later
playbooks may install only the already-closed artifact set and must not resolve
or download dependencies.

```text
seed root:             /tmp/openstack-ai-ops-wheelhouse-seed-inbox/mcp
builder publication:   /var/lib/openstack-ai-ops/wheelhouse-artifacts/mcp
transfer root:         /tmp/openstack-ai-ops-wheelhouse-transfer/mcp
assistant publication: /var/lib/openstack-ai-ops/wheelhouse/mcp
lock generator:        pip-tools 7.6.1
approval_id:           builder-2026-0001
approval_expiry_utc:   2026-09-04T03:52:20Z
```

The publication must include `requirements.lock`, the complete wheel set, and a
non-secret manifest containing package names, exact versions, filenames,
SHA-256 hashes, compatibility tags, license identifiers, provenance references,
generator environment digest, approval ID, and expiry. `manifest.sha256` must
cover the published artifact set. The actual immutable build-image identity,
generator environment digest, source seed contents, lock, wheels, and manifest
remain to be supplied and verified.

### D04 — Owners and scope approvals

The following owner labels were supplied:

| Scope | Owner |
| --- | --- |
| Dependency closure and deployment | `openstack-platform-operations-lab-admin` |
| Smoke client, runner invocation, evidence retention, audit inspection | `openstack-platform-operations-lab-admin` |
| TLS/CA/CRL and firewall | `openstack-platform-operations-lab-security-admin` |
| Activation, disablement, rollback, emergency revocation | `openstack-platform-operations-lab-operator` |

The same owner assignments across multiple scopes are an accepted operating
decision but create a separation-of-duties risk. The following scope-specific
approval references and common expiry were supplied:

```text
host_access:        2026-0004-builder-host-access-ref
test_client:        2026-0004-builder-test-client-ref
runner_invocation:  2026-0004-builder-runner-invocation-ref
evidence_retention: 2026-0004-builder-evidence-retention-ref
audit_inspection:   2026-0004-builder-audit-inspection-ref
activation:         2026-0004-builder-activation-ref
disablement:        2026-0004-builder-disablement-ref
rollback:           2026-0004-builder-rollback-ref
expiry_utc:         2026-09-03T03:52:20Z
```

These are owner-supplied references recorded for later verification; this
repository has not verified their issuer, scope, validity, or protected
approval records.

### D05 — Runner revision and readiness

```text
runner_revision:             2026-0004-builder-runner-revision-ref
readiness_manifest_reference: 2026-0004-builder-readiness-manifest-ref
readiness_status:            ready
readiness_run_id:            2026-0004
readiness_expiry_utc:        2026-09-03T03:52:20Z
```

The repository's tracked readiness fixture remains blocked by default. The
supplied `ready` status is an owner assertion requiring protected-manifest
verification during a separately authorized operation.

## Resulting implementation boundary

The owner decisions are recorded sufficiently to define the Chunk 1 acceptance
contract. Full closure acceptance remains blocked until the approved immutable
build environment, exact wheel compatibility tags, complete hash-pinned lock,
wheel inventory, provenance/license manifest, and protected approval evidence
are available.

The next safe implementation action is Chunk 1 in rejection-only/static mode:
missing or malformed closure inputs must fail closed, and no deployment default,
host operation, package download, TLS input, process, listener, or runner call
may be added to bypass the remaining evidence gap.

## Security and operational notes

- No credentials, private keys, certificates, raw payloads, audit lines, or
  protected manifest contents are recorded here.
- The existing MCP repository defaults remain disabled.
- Approval for dependency publication does not authorize live activation.
- The approval expiries must be checked against the operation timestamp before
  any future side effect.
- This record must not be treated as host deployment or live-validation evidence.
