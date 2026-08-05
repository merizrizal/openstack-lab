# Revised AI-OPS Manual Diagnostic Toolbox Operations Contract

## Status and Authority

This is the approved Phase 03 Chunk 1 documentation contract. It is subordinate to:

- `docs/ai-ops-revised/implementation-plan/ads/03-00-manual-diagnostic-toolbox-ads.md`
- `docs/ai-ops-revised/implementation-plan/03-manual-diagnostic-toolbox.md`
- `docs/ai-ops-revised/runtime/foundation-operations-contract.md`
- `docs/ai-ops-revised/runtime/identity-policy-operations-contract.md`
- `docs/ai-ops-revised/runtime/selective-reuse-manifest.md`

It defines the contract for later implementation. It does not create scripts, deploy files, connect to a host, read profile content, authenticate, call OpenStack, alter cloud state, or authorize a runner, MCP, host diagnostic, or remediation capability.

## Approved Runtime Boundary

| Concern | Approved value |
| --- | --- |
| Revised host/group | `assistant02` / `ai_ops_assistant` only |
| Runtime user/group | `aiops_assistant:aiops_assistant` |
| Runtime root | `/opt/openstack-ai-ops-assistant` |
| Profile | `aiops-assistant-project-reader` only |
| Profile configuration path | `/opt/openstack-ai-ops-assistant/credentials/profiles/clouds.yaml` |
| OpenStack CLI | `/usr/bin/openstack` from `python3-openstackclient` |
| JSON processor | `/usr/local/bin/jq`, version `1.8.2` |
| Evidence root | `/var/lib/openstack-ai-ops-evidence/phase03/` |

The only profile selection is the named project-reader profile. Implementations must not read, print, checksum, copy, transform, or validate profile content; use another profile; use a caller-selected executable; or use a `PATH` fallback for the OpenStack CLI.

## Diagnostic Invocation Contract

| Tool | Arguments | Fixed read-only operations | Required sections |
| --- | --- | --- | --- |
| `project_resource_summary` | none | fixed project-reader lists for servers, networks, subnets, ports, volumes, images, and security groups | `servers`, `networks`, `subnets`, `ports`, `volumes`, `images`, `security_groups` |
| `server_basic_info` | exactly one server name or ID | fixed `server show` for the validated identifier | `server` |
| `server_network_info` | exactly one server name or ID | fixed server, attached-port, and permitted related network/subnet reads | `server`, `ports`, `networks`, `subnets` |

Every invocation uses an argument array owned by the implementation. User input may occupy only the validated server-identifier position. Flags, subcommands, extra arguments, profile names, executable paths, output paths, and field selectors are rejected before an external process runs.

A server identifier is non-empty, at most 255 bytes, and contains only ASCII letters, digits, dot, underscore, colon, and hyphen. Empty, extra, whitespace, control/non-ASCII, shell-metacharacter, quoted, expansion, glob, path-separator, traversal, and overlong values are invalid.

## Relationship-Expansion Boundary

`server_network_info` may traverse only:

```text
requested server -> attached ports -> validated derived network/subnet IDs -> permitted related detail
```

It must establish the requested server first, query only that server's attached ports, and revalidate each derived identifier before a related lookup. It must not list or emit unrelated project ports, networks, or subnets; access Neutron-agent or host data; or substitute a project-wide topology dump for unavailable related detail.

## Selected Fields and Bounds

Every stdout result is one JSON document. The implementation selects only these fields after JSON validation and recursive secret-key redaction.

| Section | Allowed fields |
| --- | --- |
| Project-summary servers | `id`, `name`, `status` |
| Networks | `id`, `name`, `status` |
| Subnets | `id`, `name`, `network_id`, `cidr`, `ip_version` |
| Ports | `id`, `device_id`, `network_id`, `status` |
| Volumes | `id`, `name`, `status`, `size` |
| Images | `id`, `name`, `status` |
| Security groups | `id`, `name`, `status` |
| Basic server | `id`, `name`, `status`, `image`, `flavor`, `addresses`, `availability_zone`, `config_drive`, `created` |
| Server-network ports | `id`, `network_id`, `fixed_ips`, `mac_address`, `status` |
| Related networks | `id`, `name`, `status` |
| Related subnets | `id`, `name`, `cidr`, `ip_version` |

Limits are public behavior:

- at most 50 records per list section;
- at most 512 characters in a sanitized error message; and
- at most 1 MiB for the complete JSON document.

Omitted records set the affected section's `truncated` field to `true`. A value exceeding a bound must be deterministically truncated or rejected as `execution_error`; it must not produce invalid JSON or unbounded output.

## Output, Status, and Error Contract

All diagnostics use schema version `1.0` and write exactly this top-level shape to stdout:

```json
{
  "schema_version": "1.0",
  "tool": "server_basic_info",
  "status": "ok",
  "sections": [
    {
      "name": "server",
      "status": "ok",
      "data": {},
      "error": null,
      "truncated": false
    }
  ],
  "error": null
}
```

Top-level `status` is exactly `ok`, `partial`, or `error`. Section `status` is exactly `ok`, `empty`, or `unavailable`. A successful read with no records is `empty`; a blocked, missing, malformed, or failed read is never represented as a successful empty result.

Recognized normalized error classes are:

| Condition | Normalized class |
| --- | --- |
| Rejected local argument | `invalid_input` |
| Requested server absent | `not_found` |
| Server name resolves to more than one result | `ambiguous` |
| HTTP 403 or `Forbidden` | `policy_denied` |
| HTTP 503 or service unavailable | `service_unavailable` |
| Missing endpoint or service catalog | `catalog_missing` |
| DNS, timeout, refused, or unreachable endpoint | `connectivity_error` |
| HTTP 401, `Unauthorized`, or credential rejection | `authentication_error` |
| Missing fixed executable, inaccessible profile, or invalid client configuration | `configuration_error` |
| Malformed JSON or every unrecognized failure | `execution_error` |

Only recognized signatures receive a specific mapping. Unknown failures fail closed as `execution_error`; they are not treated as `empty`, `not_found`, or `policy_denied`. Error objects contain only their normalized `class` and a bounded sanitized `message`. They contain no command arguments, profile data, token, stack trace, catalog, raw response, or raw stderr.

For an aggregate diagnostic, an independent unavailable section produces top-level `partial` and does not prevent other independent fixed reads. Authentication or configuration failure may stop subsequent reads and produces top-level `error`.

## Exit-Code Contract

| Exit code | Meaning |
| --- | --- |
| `0` | All requested sections completed with top-level `ok`. |
| `2` | `invalid_input`; no external process was started. |
| `3` | Top-level `partial`; one or more sections are unavailable. |
| `4` | Top-level `error`, including not-found, ambiguous, authentication, configuration, or execution failure. |

## Redaction and Evidence

Secret-like keys are recursively replaced by a fixed redaction marker before output. The match set includes case-insensitive variants of `password`, `secret`, `token`, `credential`, `private key`, and `authorization`. Redaction is a safety requirement, not a reason to suppress unrelated safe fields.

External outcome-only evidence uses:

```text
/var/lib/openstack-ai-ops-evidence/phase03/<run-id>.md
```

The directory is operator-owned with mode `0700`; each record is mode `0600`; it is outside Git and the credential directory. A record may contain only source revision, UTC timestamp, non-secret run identifier, host/group/profile labels, tool name, normalized outcome, JSON-shape/bounds/redaction results, idempotency result, unchanged-cloud-state confirmation, and unresolved gates.

Evidence must not contain credentials, credential IDs, tokens, passwords, private keys, profile content, checksums, command arguments, stdout, stderr, resource identifiers, addresses, resource payloads, catalog data, or response bodies.

## Historical Reuse Decision

The manifest-pinned source tree is `3abc4bcf3fa4caf1c6d89f8d25865e2c0aef8e07`. The exact allowlist remains unchanged; selection is review authority only, not copying or execution authority.

| Historical selected path | Decision | Revised dependency/replacement |
| --- | --- | --- |
| `lib/aiops_common.sh` | Adapt into a newly authored revised helper; do not copy or execute historical code. | Revised root, fixed profile/CLI contract, strict validation, JSON envelope, redaction, and bounds. |
| `project_resource_summary.sh` | Adapt behavior only into a new revised diagnostic. | Revised helper; seven fixed list sections; selected fields and bounds in this contract. |
| `server_basic_info.sh` | Adapt behavior only into a new revised diagnostic. | Revised helper; exactly one validated identifier and fixed server-show operation. |
| `server_network_info.sh` | Implement new; historical project-wide correlation is not permitted. | Revised helper; requested-server-only relationship boundary in this contract. |

No README, validator/playbook, Neutron-agent tool, registry, runner, MCP resource, bridge, provider, orchestrator, egress, device-auth, wheelhouse, remote-operation, or retirement path is selected. No manifest change is required because its four-path allowlist and stated dependency closures already match these decisions.

## Validation, Rollback, and Non-Activation

Before executable implementation, reviewers must verify this document's approved paths, tool names, fields, limits, status/error/exit tables, evidence exclusions, and historical allowlist against the ADS and manifest. Static checks must reject historical runtime/profile identifiers and credential-content reads.

Rollback of this chunk is limited to reverting this documentation and the related ADS correction. It must not alter `ansible/ai_ops_runtime/`, protected inventory, Phase 02 identity material, `assistant02`, profiles, OpenStack resources, or retained external evidence.

This contract introduces no executable files, deployment role, validation playbook, host connection, Ansible execution, profile access, OpenStack call, runner registration, MCP resource, or cloud-state authority.
