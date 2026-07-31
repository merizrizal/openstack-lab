# Orchestrator SDK Runtime Upgrade and Rollback

## Scope

This procedure applies to the root-owned, hash-locked orchestrator runtime only. It
does not authorize authentication, remote egress, remote unit start, a provider
request, custom routing, API-key use, or Codex-home inspection.

## Upgrade gate

1. Keep `aiops-orchestrator-remote` disabled and stopped; preserve the fake-only
   service as the default.
2. Review the proposed lock-file and wheelhouse change independently. Do not accept an
   unpinned package, a missing hash, or an unreviewed public API change.
3. Rebuild and publish the reviewed offline wheelhouse through the existing controlled
   procedure; do not download dependencies from a target host.
4. Deploy only after the fake-only deployment validator, local mocked adapter tests,
   local MCP safety tests, and evidence-boundary checks pass.
5. Run the reviewed no-provider preflight. A package, sandbox, listener, protected-path,
   egress, or fake-workflow failure rejects the upgrade.

The remote acceptance path remains unavailable after an upgrade. A later remote
attempt requires a new end-to-end review, local preflight, separate authentication
authorization where applicable, and a new one-request approval.

## Required local validation

Use a temporary environment and retain only pass/fail outcomes:

```bash
rtk python3 -m venv /tmp/openstack-ai-ops-orchestrator-upgrade-venv
rtk /tmp/openstack-ai-ops-orchestrator-upgrade-venv/bin/python -m pip install --require-hashes -r ansible/ai_ops_runtime/files/orchestrator/requirements.lock
rtk /tmp/openstack-ai-ops-orchestrator-upgrade-venv/bin/python -m pytest -q ansible/ai_ops_runtime/files/orchestrator/tests
rtk ansible-playbook -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_validate_phase12_remote_preflight.yml
```

Do not copy test, package-manager, runtime, or authentication output into repository
artifacts, logs, tickets, chat, or handoffs.

## Rollback

If any gate fails, or accepted public SDK behavior changes:

1. Keep the remote unit disabled and stopped; do not retry the failed path.
2. Restore the last accepted hash-locked requirements file and approved offline
   wheelhouse publication.
3. Redeploy the prior root-owned venv, sources, fake-only service, and permanent
   orchestrator egress denial through the reviewed deployment roles.
4. Remove only a temporary approval/workspace artifact created by a future approved
   operation. Never delete, list, parse, hash, copy, or otherwise inspect Codex-home.
5. Rerun the fake-only deployment and no-provider preflight validators.
6. Record the closed rejection category and validator outcomes. Treat unsupported
   SDK/runtime behavior as a vendor blocker until a new reviewed version is accepted.

Rollback never enables the remote unit, widens egress, enables a provider gateway, or
converts a failed attempt into a second request.
