# Restricted Host Diagnostics Runbook

## Purpose

This runbook defines the diagnostic-only host evidence boundary available through the local AI-OPS runner. It covers recent metadata, Nova, and Neutron evidence from reviewed controller and compute aliases only.

The runner is the only public entry point. Operators and AI workflows must not use direct SSH, sudo, shell, file-read, service-control, database, or remediation commands.

## Reviewed Tools

| Tool | Approved hosts | Fixed kind | Windows |
| --- | --- | --- | --- |
| `recent_metadata_errors` | `controller01` | `metadata` | `15m`, `30m`, `1h` |
| `recent_nova_errors` | `controller01`, `compute01`, `compute02` | `nova` | `15m`, `30m`, `1h` |
| `recent_neutron_errors` | `controller01`, `compute01`, `compute02` | `neutron` | `15m`, `30m`, `1h` |

Each request requires `host`; `time_window` defaults to `15m`. Caller-supplied diagnostic kinds, unknown arguments, unapproved aliases, IP substitutions, and non-exact windows are rejected before connector execution.

## Evidence Boundary

The connector uses a dedicated observer identity, pinned host keys, strict host-key verification, no SSH configuration, no agent or password fallback, no TTY, no forwarding, and a fixed remote collector grammar. The collector can inspect only its fixed service, journal, listener, and log-source maps. It returns bounded, redacted JSON sections; an unavailable source is evidence of an unavailable source, not proof that a service is healthy.

Metadata evidence includes the Nova metadata listener category, Neutron metadata-agent categories, and fixed Apache metadata-log categories. Interpret an unavailable listener, Neutron proxy-related evidence, source absence, and no matching recent lines as distinct outcomes. Do not infer remediation from any result.

## Operating Procedure

1. Start with `project_resource_summary`, `server_basic_info`, and `server_network_info` for the same reviewed server context.
2. Select the named host tool whose fixed scope matches the symptom.
3. Submit only the approved alias and exact window through the local runner.
4. Preserve the structured envelope fields: `tool`, `status`, `arguments`, `duration_ms`, `truncated`, `timestamp`, and `request_id`.
5. Correlate the request ID with the runner audit event.
6. Explain observed evidence, unavailable sections, and uncertainty. Recommend manual operator follow-up only.

Never expose raw diagnostic payloads, audit lines, known-host entries, private keys, credentials, tokens, or secret-like log values outside the protected runtime.

## Failure Handling

- `validation_error`: correct the reviewed alias/window/argument; do not retry with an IP address or altered command.
- `timeout`: preserve the envelope and request ID; do not broaden SSH or collector timeouts ad hoc.
- `error`: preserve sanitized metadata and escalate to the operator; do not substitute another identity or host key source.
- `truncated`: treat the result as partial evidence and escalate with its request ID.
- `unavailable` source sections: report the evidence gap without claiming service health.

## Prohibited Actions

Do not restart, reload, start, stop, edit, install, remove, forward ports, allocate a TTY, open a shell, use arbitrary sudo, read arbitrary configuration, query databases, or invoke generic SSH. No host-control capability exists in the registry or connector.

## Rollback

1. Revert the reviewed host-tool registry entries to unavailable and deploy the assistant role.
2. Remove the observer authorized keys, sudoers rule, collector, and observer account through the reviewed observer role.
3. Remove the dedicated observer key, pinned known-host file, and generated policy from `assistant01` only after disabling the tools.
4. Retain only sanitized evidence and audit records according to operator retention policy.

Do not manually edit credential, sudoers, or authorized-key files while attempting rollback.
