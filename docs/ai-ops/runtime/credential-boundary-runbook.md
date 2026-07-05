# AI-OPS Credential Boundary Runbook

This runbook documents the Phase 02 project-reader credential boundary for `assistant01`.

## Current operator decisions

These values must stay aligned with `ansible/bootstrap_openstack/inventories/local/group_vars/all/common.yml`.

- Target project: `admin`
- Target domain: `default`
- Role name: `reader`
- Application credentials: not supported in this lab at present
- Profile shape: `clouds.yaml` + `secure.yaml`
- Phase 02 mode: hybrid
- Default profile name: `aiops-project-reader`
- Rotation expectation: rotate the dedicated credential whenever secret material is reissued, on any suspected exposure, after any role/project scope change, and during the next planned operator credential review; record each rotation in a dated evidence note.

## Purpose

Create or install a dedicated OpenStack diagnostic profile on the assistant runtime, prove read access, and prove mutation denial without placing admin or human credentials on `assistant01`.

## Runtime-local storage

All real credential material must live only here:

```text
/opt/openstack-ai-ops/credentials/profiles/
```

Required protections:

- directory mode: `0700`
- file mode: `0600`
- owner/group: runtime-approved and operator-verified

Do not commit real profile files to git.

## Profile layout

Use two runtime-local files:

- `clouds.yaml` for non-secret profile metadata
- `secure.yaml` for secret auth material

The profile name must be `aiops-project-reader` unless a later operator decision overrides it.

## Validation commands

Set the profile path first:

```bash
export OS_CLIENT_CONFIG_FILE=/opt/openstack-ai-ops/credentials/profiles/clouds.yaml
export OS_CLOUD=aiops-project-reader
```

Then validate authentication and reads with the runtime OpenStack CLI:

```bash
/opt/openstack-ai-ops/.venv/bin/openstack token issue
/opt/openstack-ai-ops/.venv/bin/openstack server list
/opt/openstack-ai-ops/.venv/bin/openstack network list
/opt/openstack-ai-ops/.venv/bin/openstack subnet list
/opt/openstack-ai-ops/.venv/bin/openstack port list
/opt/openstack-ai-ops/.venv/bin/openstack volume list
/opt/openstack-ai-ops/.venv/bin/openstack image list
/opt/openstack-ai-ops/.venv/bin/openstack security group list
```

Record only command outcome and non-secret error class.

## Mutation-denial checks

Use harmless, unique names. The goal is authorization denial, not malformed input.

Examples:

```bash
/opt/openstack-ai-ops/.venv/bin/openstack network create aiops-deny-probe-<timestamp>
/opt/openstack-ai-ops/.venv/bin/openstack security group create aiops-deny-probe-sg-<timestamp>
/opt/openstack-ai-ops/.venv/bin/openstack server create aiops-deny-probe-server-<timestamp> \
  --flavor <small-flavor> --image <test-image> --network <project-network>
```

Expected outcomes:

- `Forbidden`
- `Not authorized`
- policy denial
- equivalent authz failure

Any successful mutation is a blocking safety failure.
This includes "safe" same-value update probes: if a command such as `openstack network set --description <current-description> ...` returns success, treat that as evidence that update authority is broader than intended even if the effective resource state did not change.

## Deferred operator-reader scope

Phase 02 validates only the default project-scoped `aiops-project-reader` profile for project-visible reads and mutation-denial checks.

The following visibility remains deferred to a separate non-default operator-reader profile and was not validated in Phase 02:

- cross-project inventory outside the selected default project scope
- control-plane service, agent, or hypervisor visibility such as `openstack compute service list`, `openstack network agent list`, and `openstack hypervisor list`
- host-level diagnostics or SSH-based observer workflows

Do not widen the default `aiops-project-reader` profile to satisfy these deferred needs.

## Rollback

If the credential must be removed:

1. Revoke or delete the dedicated OpenStack credential/user through operator/admin control.
2. Remove `/opt/openstack-ai-ops/credentials/profiles/clouds.yaml`.
3. Remove `/opt/openstack-ai-ops/credentials/profiles/secure.yaml`.
4. Confirm `openstack --os-cloud aiops-project-reader token issue` no longer succeeds.
5. Record the rollback in a dated evidence note.

## Evidence to capture

Record:

- selected project and domain
- role name
- credential owner and purpose
- profile name and file locations
- read command pass/fail matrix
- mutation-denial matrix
- deferred operator-reader-only commands or visibility classes
- credential rotation expectation and any performed rotation/revocation action

Do not include secrets, tokens, passwords, private keys, or raw unredacted config.
