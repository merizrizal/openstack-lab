# Workspace Setup Runbook

Use this runbook on the assistant runtime host to create the Phase 01 workspace layout described in `docs/ai-ops/runtime/README.md`.

This is operator-run setup only. Do not expose these commands as AI-facing tools.

## Prerequisites

- You know the runtime user and group that should own the workspace files.
- You have permission to create `/opt/openstack-ai-ops/` on the runtime host.
- You are **not** placing credentials in the workspace during this step.

## Create the workspace directories

Set the runtime user and group first:

```bash
export RUNTIME_USER=assistant
export RUNTIME_GROUP=assistant
```

Create the directory tree:

```bash
sudo install -d -m 0755 /opt/openstack-ai-ops
sudo install -d -o "$RUNTIME_USER" -g "$RUNTIME_GROUP" -m 0755 \
  /opt/openstack-ai-ops/scripts/approved \
  /opt/openstack-ai-ops/diagnostics/raw \
  /opt/openstack-ai-ops/diagnostics/summaries \
  /opt/openstack-ai-ops/runbooks \
  /opt/openstack-ai-ops/credentials/profiles \
  /opt/openstack-ai-ops/audit \
  /opt/openstack-ai-ops/mcp
```

If the runtime user already owns `/opt/openstack-ai-ops/`, you may omit `sudo` and run the same `install -d` commands directly.

## Verify ownership and permissions

Check the directory metadata:

```bash
stat -c '%U:%G %a %n' \
  /opt/openstack-ai-ops \
  /opt/openstack-ai-ops/scripts/approved \
  /opt/openstack-ai-ops/diagnostics/raw \
  /opt/openstack-ai-ops/diagnostics/summaries \
  /opt/openstack-ai-ops/runbooks \
  /opt/openstack-ai-ops/credentials/profiles \
  /opt/openstack-ai-ops/audit \
  /opt/openstack-ai-ops/mcp
```

Confirm the writable paths are writable by the runtime user:

```bash
test -w /opt/openstack-ai-ops/diagnostics/raw
test -w /opt/openstack-ai-ops/diagnostics/summaries
test -w /opt/openstack-ai-ops/audit
```

## Verify credential storage is empty

This directory must exist but stay empty until Phase 02:

```bash
find /opt/openstack-ai-ops/credentials/profiles -mindepth 1 -maxdepth 1 -print
```

Expected result: no output.

## Optional sanity checks

Confirm the workspace root exists:

```bash
test -d /opt/openstack-ai-ops
```

Confirm the runbook and diagnostics areas are present:

```bash
find /opt/openstack-ai-ops -maxdepth 2 -type d | sort
```

## Stop conditions

Stop and investigate if any of the following are true:

- `/opt/openstack-ai-ops/credentials/profiles/` contains files.
- `diagnostics/raw/`, `diagnostics/summaries/`, or `audit/` are not writable by the runtime user.
- Ownership does not match the intended runtime user and group.
- Any credential material is present during Phase 01.
