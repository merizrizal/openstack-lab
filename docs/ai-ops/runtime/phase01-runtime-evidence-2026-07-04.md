# Phase 01 Runtime Evidence - 2026-07-04

## Metadata

- Runtime host: `assistant01`
- Inventory source: `inventories/local/nodes.yml`
- Automation source: `ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml`
- Runtime evidence file: `/opt/openstack-ai-ops/diagnostics/summaries/phase01-runtime-evidence-2026-07-04.md`
- Playbook result: `assistant01 : ok=18 changed=7 unreachable=0 failed=0`

## Placement and Reachability

- `assistant01` was running under Vagrant/libvirt.
- Management IP `192.168.121.20`, provider IP `192.168.123.20`, and Vagrant private IP `192.168.124.20` responded to ping from the operator host.
- From `assistant01`, `controller01.local` resolved to `192.168.121.5`.
- From `assistant01`, ping to controller management address `192.168.121.5` succeeded with `0% packet loss`.
- From `assistant01`, `curl http://192.168.121.5:5000/v3/` returned HTTP `200`.
- Tenant-network access was not required for these Phase 01 checks.

## Workspace Evidence

Runtime evidence reported these paths present:

- `/opt/openstack-ai-ops`
- `/opt/openstack-ai-ops/scripts/approved`
- `/opt/openstack-ai-ops/diagnostics/raw`
- `/opt/openstack-ai-ops/diagnostics/summaries`
- `/opt/openstack-ai-ops/runbooks`
- `/opt/openstack-ai-ops/credentials/profiles`
- `/opt/openstack-ai-ops/audit`
- `/opt/openstack-ai-ops/mcp`

Writable-path check as runtime user `assistant` returned `writable` for:

- `/opt/openstack-ai-ops/diagnostics/raw`
- `/opt/openstack-ai-ops/diagnostics/summaries`
- `/opt/openstack-ai-ops/audit`

`/opt/openstack-ai-ops/credentials/profiles` entry count was `0`.

## Baseline Tool Versions

Captured on `assistant01`:

- Python 3: `Python 3.12.3`
- Virtualenv Python: `Python 3.12.3`
- Virtualenv pip: `pip 24.0`
- OpenStack CLI: `openstack 10.1.0`
- OpenStack SDK: `4.17.0`
- SSH client: `OpenSSH_9.6p1 Ubuntu-3ubuntu13.16`
- curl: `curl 8.5.0`
- JSON parser: `jq-1.7`
- Fast text search: `ripgrep 14.1.0`
- Git: `git version 2.43.0`

OpenStack CLI behavior without credentials was checked with `/opt/openstack-ai-ops/.venv/bin/openstack server list`; it failed with `Missing value auth-url required for auth plugin password`, confirming the client exists and auth is not configured.

## Credential Absence Checks

- The playbook reported: `OpenStack auth configured by this playbook: no`.
- `credentials/profiles` contained `0` entries.
- Runtime environment scan for `OS_` variables returned no output.
- Constrained workspace scan excluding `.venv` found no OpenStack credential files, private-key files, or cloud secret patterns.
- Package-internal fixture/certificate files inside `.venv` were observed during a broad filename scan and were not operator-created credential profiles.

## Notes

- The runtime bootstrap used key-based operator SSH for the Ansible run; no SSH private keys were copied into the AI-OPS runtime workspace.
- MCP remains inactive for Phase 01.
- No Phase 02 OpenStack credentials were created.
