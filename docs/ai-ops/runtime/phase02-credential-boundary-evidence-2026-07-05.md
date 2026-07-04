# Phase 02 Credential Boundary Evidence - 2026-07-05

## Metadata

- Runtime host: `assistant01`
- Inventory source: `inventories/local/nodes.yml`
- Validation automation: `ansible/ai_ops_runtime/playbook_validate_phase02_readonly_credential_boundary.yml`
- Validation log: `ansible/log/ai_ops_runtime/playbook_validate_phase02_readonly_credential_boundary-2026-07-05-00-43-09-745553.log`
- Profile name: `aiops-project-reader`
- Profile shape: `clouds.yaml` + `secure.yaml`
- Target project: default project
- Target domain: default domain
- Role name: `aiops-readonly`
- Application credentials: not supported in this lab at present
- Phase 02 mode: hybrid

## Credential Storage Evidence

Validated on `assistant01`:

- `/opt/openstack-ai-ops/credentials/profiles` exists
- directory mode: `0700`
- owner/group: `assistant:assistant`
- `/opt/openstack-ai-ops/credentials/profiles/clouds.yaml` exists
- `clouds.yaml` mode: `0600`
- `/opt/openstack-ai-ops/credentials/profiles/secure.yaml` exists
- `secure.yaml` mode: `0600`

## Authentication Evidence

- `openstack token issue` succeeded
- token issue return code: `0`

## Read Validation Evidence

All listed commands returned `rc=0`.

| Command | Result |
| --- | --- |
| `openstack server list -f json` | `[]` |
| `openstack network list -f json` | `private`, `provider` |
| `openstack subnet list -f json` | `private-subnet`, `provider-subnet` |
| `openstack port list -f json` | 4 ports returned |
| `openstack volume list -f json` | `[]` |
| `openstack image list -f json` | `vm_image01` |
| `openstack security group list -f json` | `openstack_lab`, `default` |

## Notes

- The runtime-local profile was copied into `/opt/openstack-ai-ops/credentials/profiles/` from the staged `generated/` source.
- This evidence confirms the assistant runtime can authenticate and perform project-visible read checks with the dedicated project-reader profile.
- Mutation-denial checks are deferred to the next phase chunk.
- No secrets, tokens, passwords, private keys, or raw profile content are included here.
