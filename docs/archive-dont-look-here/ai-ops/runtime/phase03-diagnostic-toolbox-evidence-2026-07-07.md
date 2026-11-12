# Phase 03 Diagnostic Toolbox Evidence - 2026-07-07

## Source

Runtime evidence was generated on `assistant01` by:

```text
ansible/ai_ops_runtime/playbook_validate_phase03_diagnostic_toolbox.yml
```

Generated runtime evidence path:

```text
/opt/openstack-ai-ops/diagnostics/summaries/phase03-diagnostic-toolbox-evidence-2026-07-07.md
```

This repository note is a redacted summary of the runtime evidence. It intentionally omits credential contents, tokens, private keys, raw profile files, full resource UUIDs, host IDs, user IDs, MAC addresses, and IP addresses.

## Metadata

- Runtime date: `2026-07-07T00:25:32Z`
- Runtime host: `assistant01`
- Workspace root: `/opt/openstack-ai-ops`
- Approved script directory: `/opt/openstack-ai-ops/scripts/approved`
- Default OpenStack profile: `aiops-project-reader`
- Server-specific validation target: `control_plane_vm01`
- Server-specific checks skipped: `false`

## Deployed Toolbox Paths

The runtime evidence confirmed these deployed paths exist with expected ownership and modes:

| Path | Owner | Group | Mode | Result |
| --- | --- | --- | --- | --- |
| `/opt/openstack-ai-ops/scripts/approved` | `assistant` | `assistant` | `0755` | present |
| `/opt/openstack-ai-ops/scripts/approved/README.md` | `assistant` | `assistant` | `0644` | present |
| `/opt/openstack-ai-ops/scripts/approved/lib/aiops_common.sh` | `assistant` | `assistant` | `0644` | present |
| `/opt/openstack-ai-ops/scripts/approved/project_resource_summary.sh` | `assistant` | `assistant` | `0755` | present |
| `/opt/openstack-ai-ops/scripts/approved/server_basic_info.sh` | `assistant` | `assistant` | `0755` | present |
| `/opt/openstack-ai-ops/scripts/approved/server_network_info.sh` | `assistant` | `assistant` | `0755` | present |
| `/opt/openstack-ai-ops/scripts/approved/neutron_agent_health.sh` | `assistant` | `assistant` | `0755` | present |
| `/opt/openstack-ai-ops/.venv/bin/openstack` | `root` | `root` | `0755` | present |
| `/opt/openstack-ai-ops/credentials/profiles/clouds.yaml` | `assistant` | `assistant` | `0600` | present |
| `/opt/openstack-ai-ops/credentials/profiles/secure.yaml` | `assistant` | `assistant` | `0600` | present |

## Shell Syntax Checks

All deployed approved shell scripts passed `bash -n` on `assistant01`:

| Script | Return code |
| --- | ---: |
| `neutron_agent_health.sh` | 0 |
| `server_network_info.sh` | 0 |
| `server_basic_info.sh` | 0 |
| `project_resource_summary.sh` | 0 |
| `lib/aiops_common.sh` | 0 |

## Runtime Diagnostic Results

### `project_resource_summary.sh`

- Return code: `0`
- Evidence shape: sectioned output with JSON payloads.
- Read-only sections observed successfully:
  - servers
  - networks
  - subnets
  - ports
  - volumes
  - images
  - security groups
- Redacted inventory counts observed:
  - servers: 3
  - networks: 3
  - subnets: 2
  - ports: 7
  - volumes: 3
  - images: 1
  - security groups: 3

### `server_basic_info.sh control_plane_vm01`

- Return code: `0`
- Evidence shape: JSON server detail output.
- Redacted facts observed:
  - server name: `control_plane_vm01`
  - status: `ACTIVE`
  - flavor: `medium`
  - image field: booted from volume
  - security group list present
  - attached volume list present
  - config drive field present

### `server_network_info.sh control_plane_vm01`

- Return code: `0`
- Evidence shape: sectioned output with JSON payloads.
- Read-only sections observed successfully:
  - server summary
  - server ports
  - project-visible networks for correlation
  - project-visible subnets for correlation
- Redacted facts observed:
  - target server was active
  - one server port was returned
  - project-visible network and subnet context was returned for correlation

### Unsafe identifier rejection

Both server-specific scripts rejected an unsafe identifier before OpenStack invocation:

| Check | Return code | Result |
| --- | ---: | --- |
| `server_basic_info.sh unsafe;identifier` | 64 | rejected unsafe characters |
| `server_network_info.sh unsafe;identifier` | 64 | rejected unsafe characters |

### `neutron_agent_health.sh`

- Return code: `69`
- Result: unavailable by design.
- Evidence: script returned an unavailable status because the non-default operator-reader profile is deferred.
- Boundary: the script did not fall back to the project-reader profile for operator-level visibility.

## Local Static Safety Validation

Local repository validation also passed after the runtime playbook was added:

```text
rtk bash -n scripts/check_ai_ops_diagnostic_safety.sh
rtk scripts/check_ai_ops_diagnostic_safety.sh
```

Observed result:

```text
aiops safety check passed: 5 shell script(s) scanned under ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved
```

Ansible syntax checks also passed locally using a temporary Python virtual environment under `/tmp`:

```text
ansible-playbook --syntax-check ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml
ansible-playbook --syntax-check ansible/ai_ops_runtime/playbook_validate_phase03_diagnostic_toolbox.yml
```

## Boundary Notes

- No credential file contents, token output, passwords, private keys, raw profile files, or secret material are recorded in this repository evidence note.
- The project-reader diagnostics executed fixed reviewed scripts rather than arbitrary OpenStack command passthrough.
- The current `server_network_info.sh` version intentionally keeps network/subnet correlation simple and does not yet perform per-port network/subnet `show` expansion.
- `neutron_agent_health.sh` remains a fail-closed availability gate until a separate non-default operator-reader profile is created, validated, and documented.
