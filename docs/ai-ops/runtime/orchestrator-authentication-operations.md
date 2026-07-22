# Orchestrator Codex Authentication Operations

## Scope and boundary

This runbook applies only to the `aiops-orchestrator` system identity and its fixed
Codex home, `/var/lib/aiops-orchestrator/codex-home`. It supports the pinned,
repository-reviewed Codex runtime artifact and does not enable remote orchestration.
The deployed orchestrator remains fake-only and network-disabled unless a separate,
current approval authorizes a bounded authentication egress operation.

The operator alone performs authentication. Do not place authentication output in
Ansible, inventory, evidence, logs, tickets, chat, shell history, or handoffs. In
particular, do not share device codes, browser addresses, account details, tokens,
refresh data, status text, or logout output. Repository automation must not list,
read, copy, hash, parse, or delete Codex-home contents.

## Prerequisites

1. Confirm the permanent `disabled` orchestrator egress policy is materialized.
2. Obtain a fresh, separately approved temporary authentication egress window. A
   synthetic-validation approval does not authorize sign-in.
3. Confirm the root-owned pinned runtime artifact is deployed. Resolve its bundled
   executable without accessing Codex-home contents:

   ```bash
   CODEX_BIN="$(/opt/openstack-ai-ops/orchestrator/venv/bin/python -c "import codex_cli_bin; from pathlib import Path; print(Path(codex_cli_bin.__file__).parent / 'bin' / 'codex')")"
   ```

4. As the operator, confirm only the executable version. Do not retain its output:

   ```bash
   /usr/sbin/runuser -u aiops-orchestrator -- /usr/bin/env -i HOME=/var/lib/aiops-orchestrator/codex-home PATH=/usr/bin:/bin "$CODEX_BIN" --version
   ```

## Operator-owned sign-in

During the approved temporary window, invoke only the supported interactive command
under the dedicated identity and fixed home:

```bash
/usr/sbin/runuser -u aiops-orchestrator -- /usr/bin/env -i HOME=/var/lib/aiops-orchestrator/codex-home PATH=/usr/bin:/bin "$CODEX_BIN" login
```

Complete any interactive step privately. Do not automate browser interaction, device
codes, or output capture. On success or failure, close the temporary egress window
unconditionally and restore the permanent `disabled` policy.

## Status and recovery

Use status only as a private operator action, under the same identity and home:

```bash
/usr/sbin/runuser -u aiops-orchestrator -- /usr/bin/env -i HOME=/var/lib/aiops-orchestrator/codex-home PATH=/usr/bin:/bin "$CODEX_BIN" login status
```

Record only one closed operator outcome outside the terminal: `authenticated`,
`authentication_required`, or `operator_error`. Do not record the command output,
account identifier, expiry, or any credential-related detail.

If authentication is required or the supported runtime reports an error, leave remote
selection disabled. Request a new approval for another bounded operator action; do
not inspect, repair, export, or replace credential files and do not use an API key or
proxy fallback.

## Logout and disablement

To end the managed session, the operator may use the supported command privately:

```bash
/usr/sbin/runuser -u aiops-orchestrator -- /usr/bin/env -i HOME=/var/lib/aiops-orchestrator/codex-home PATH=/usr/bin:/bin "$CODEX_BIN" logout
```

Do not delete Codex-home or its contents. After logout, ensure temporary egress is
absent and the permanent dedicated-identity reject remains active. Logout does not
authorize real adapter selection, provider access, firewall broadening, or any Phase
12 operation.
