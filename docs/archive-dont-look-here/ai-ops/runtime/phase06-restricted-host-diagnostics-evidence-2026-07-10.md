# Restricted Host Diagnostics Evidence Snapshot

Repository record for successful restricted host diagnostic validation on 2026-07-10.

## Validation Context

- Runtime host: `assistant01`
- Validation playbook: `ansible/ai_ops_runtime/playbook_validate_phase06_restricted_host_diagnostics.yml`
- Scope: reviewed controller and compute observer aliases only
- Evidence policy: status, ownership, mode, envelope, and audit metadata only; no raw diagnostic payloads, keys, known-host entries, credentials, or raw audit records are retained here.

## Boundary Confirmation

- Assistant connector, policy path, observer key, known-host file, runner, and registry passed expected type/owner/group/mode checks.
- Target collector, sudoers policy, and forced-command authorized-key files passed expected type/owner/group/mode checks on every reviewed observer target.
- `visudo -cf` accepted the deployed restricted sudoers policy on every reviewed observer target.
- Approved direct connector forms succeeded for metadata on the controller and Nova/Neutron on the approved controller and compute aliases.
- Direct shell, TTY, and forwarding attempts through the observer identity were denied.

## Runner and Audit Confirmation

- All seven approved host-tool requests returned successful structured runner envelopes for the reviewed `15m` window.
- Invalid host, invalid time window, and caller-supplied diagnostic-kind requests returned `validation_error` before execution.
- Every approved and rejected runner validation request produced a correlated audit event.
- Metadata payload validation retained the fixed listener, Neutron metadata-agent, and Nova metadata-log evidence categories while remaining bounded and redacted.

## Metadata Workflow Confirmation

The validation ran `project_resource_summary`, `server_basic_info`, `server_network_info`, and `recent_metadata_errors` through the local runner. The evidence boundary can distinguish listener, Neutron metadata, Nova metadata-log, unavailable-source, and no-matching-evidence categories without granting remediation or generic host access.

## Sanitization Review

- No private key, known-host content, credential, token, password, shared secret, raw diagnostic payload, or raw audit line is recorded in this repository evidence.
- No restart, configuration edit, package mutation, shell, generic SSH, generic sudo, database access, or remediation capability was added.
- The validated tools remain limited to the reviewed aliases, fixed diagnostic kinds, and exact time windows.

## Remaining Operational Notes

Future service-placement changes require a reviewed registry, policy, collector-map, test, and runtime-validation update. Operators must treat unavailable or truncated sections as evidence gaps rather than proof of health.
