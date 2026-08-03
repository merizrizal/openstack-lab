# Revised AI-OPS Foundation Operations Contract

## Status and Authority

This contract implements the documentation decision of Phase 01 Steps 4–6. It is subordinate to:

- `docs/ai-ops-revised/runtime/runtime-placement-contract.md`
- `docs/ai-ops-revised/runtime/selective-reuse-manifest.md`
- `docs/ai-ops-revised/implementation-plan/ads/01-01-minimal-runtime-foundation-and-isolation-ads.md`

It authorizes design and later narrowly scoped foundation automation only. It does not authorize a host connection, Ansible play execution, credential creation, Keystone authentication, network change, diagnostic, runner, MCP process, listener, provider integration, egress policy, or restricted host access.

## Current Implementation Reconciliation

Repository-only validation has confirmed the revised inventory graph, role and
entrypoint syntax, package-to-capability mapping, and validation-play syntax.
The validation play records only redacted facts and reports unchanged state by
contract. This is static implementation evidence, not foundation acceptance
or host-state evidence.

The following gates remain open and block live foundation acceptance:

1. remove the SSH host-verification bypass from the revised transport settings
   and obtain an operator-approved known-hosts source;
2. review and resolve the staged root-inventory diff under the protected-input
   policy before live execution;
3. obtain explicit approval for limited check mode, then apply, non-mutating
   validation, and a second idempotency apply, each limited to `assistant02`;
4. capture the resulting redacted evidence outside committed source.

## Approved Placement and Namespace

| Concern | Approved value |
| --- | --- |
| Revised host | `assistant02` |
| Inventory group | `ai_ops_assistant` only |
| Host profile | Same CPU, memory, and disk specification as `assistant01` |
| Management address | `192.168.121.21` |
| Provider address | `192.168.123.21` |
| Runtime root | `/opt/openstack-ai-ops-assistant` |
| Runtime user/group | `aiops_assistant` |
| Future project-reader profile name | `aiops-assistant-project-reader` |
| Audit root | `/opt/openstack-ai-ops-assistant/audit` |
| Initial Keystone endpoint | `http://192.168.121.5:5000/v3` |

The endpoint was copied only from the `auth_url` field in ignored generated cloud configuration. It is a non-secret routing input. No generated credential field may be read, copied, committed, or used by the Phase 01 foundation.

`assistant02` must remain in the sole revised inventory group. Wheelhouse/builder and host-observer groups are not part of the revised inventory or foundation entrypoint.

## Runtime Workspace and Ownership

The foundation role may create only the following paths. Every task must assert that the target path is below the revised runtime root before mutation. It must not use recursive ownership or mode changes outside these exact paths.

| Path | Owner/group | Mode | Phase 01 state | Owner phase for content |
| --- | --- | --- | --- | --- |
| `/opt/openstack-ai-ops-assistant` | `root:aiops_assistant` | `0750` | Directory only | Phase 01 |
| `scripts/approved` | `root:aiops_assistant` | `0750` | Empty | Phase 03 |
| `output` | `aiops_assistant:aiops_assistant` | `0750` | Empty | Phase 03 |
| `credentials` | `aiops_assistant:aiops_assistant` | `0700` | Empty | Phase 02 |
| `audit` | `aiops_assistant:aiops_assistant` | `0700` | Empty | Phase 04 |
| `tests` | `root:aiops_assistant` | `0750` | Empty | Owning phase |
| `mcp` | `aiops_assistant:aiops_assistant` | `0700` | Empty | Phase 07 |
| `evidence/foundation` | `root:aiops_assistant` | `0750` | Empty until reviewed evidence is recorded | Phase 01 |

The `aiops_assistant` system account has no privileged shell, sudo grant, SSH key, cloud profile, credential, or service ownership in this phase. Creation of the account/group and these empty directories is permitted only after the revised role’s fail-closed contract has passed syntax validation.

## Baseline Ubuntu Package Allowlist

The base-node documentation identifies Ubuntu as the lab VM operating system. The foundation may use the configured Ubuntu repositories only and may install exactly this allowlist after package availability is verified in check mode:

| Package | FR-004 capability | Reason |
| --- | --- | --- |
| `python3` | Python | Runtime for later reviewed diagnostics. |
| `python3-venv` | Python | Isolated environment support for later reviewed tooling. |
| `python3-openstackclient` | OpenStack CLI | Required by later manual diagnostics; no profile is configured now. |
| `python3-openstacksdk` | OpenStack SDK | Required by later reviewed diagnostics. |
| `openssh-client` | SSH client | Future restricted client use only; no SSH server is installed. |
| `curl` | HTTP/TCP tooling | Endpoint troubleshooting support; no HTTP request is run in this phase. |
| `jq` | JSON tooling | Later structured diagnostic output review. |
| `ripgrep` | Log-search tooling | Later bounded local evidence review. |
| `git` | Version-control tooling | Revised workspace provenance. |

The role must record the resolved installed versions as redacted evidence. Version recording does not pin an unavailable package version. A change to the allowlist, package repository, PPA, direct download, standalone binary, compiler/toolchain, archive utility, Node.js, server, firewall package, daemon, or service requires a new approved contract revision.

## External Transport and Protected Inputs

All Ansible transport authentication is external to committed repository files. The revised inventory may contain non-secret connection defaults only.

- Do not commit passwords, private keys, tokens, sudo passwords, OpenRC files, cloud profiles, or generated cloud configuration.
- Do not load `common_secret.yml` or any committed credential-shaped vars file from the revised setup entrypoint.
- Supply the approved operator identity, private-key reference, and any vault/secret mechanism at execution time through an operator-controlled path.
- Do not disable SSH host identity verification. The approved operator transport must provide an appropriate known-hosts source.
- Do not create an `aiops_assistant` SSH key in this phase.
- The endpoint input is the scoped non-secret variable `ai_ops_assistant_keystone_endpoint`; it may be used only for the Phase 01 TCP check.

### Local-Lab Transport Placeholder Exception

The local inventory may retain `ansible/ai_ops_assistant/inventories/local/group_vars/all/common_secret.yml` only for the existing local-lab `ansible_user`, `ansible_password`, and `ansible_sudo_pass` placeholder variables. This exception is limited to the `local` inventory and `assistant02`; it does not authorize generated values, OpenStack/cloud credentials, tokens, private keys, OpenRC files, cloud profiles, non-local inventories, or a `vars_files` reference to the file. The placeholders must not be printed in evidence or command output, and the local transport still requires an operator-approved known-hosts source with SSH host identity verification enabled. Replacing a placeholder with actual credential material requires a further approved contract amendment.

## Activation and Live-Execution Gate

Before any live foundation apply, all conditions must be true:

1. The revised role resolves through the repository-supported Ansible role path and passes syntax validation.
2. The entrypoint targets exactly `ai_ops_assistant`; `--limit assistant02` is mandatory for check mode, apply, and validation.
3. The entrypoint does not target `all`, invoke `common` or any historical role, load committed secret vars other than the Local-Lab Transport Placeholder Exception, or contain diagnostic, credential, runner, MCP, provider, orchestrator, egress, wheelhouse, or observer behavior.
4. The package allowlist is available from configured Ubuntu repositories without adding a repository or downloading an artifact.
5. The external transport procedure and known-hosts source are approved by the operator.
6. The host is verified distinct from `assistant01` and absent from all controller, compute, storage, Ceph, database, message-bus, observability, and other control-plane groups.
7. Check mode reports only proposed revised account, workspace, and package changes.
8. A reviewer approves the check-mode diff before the first apply.

The first apply creates only the approved account/group, workspace, and package state. It must not contact Keystone. Keystone TCP verification is a separate non-mutating validation action after the foundation apply is accepted.

## Evidence and Redaction

Foundation acceptance evidence is recorded outside committed source and contains only:

- source and contract revision;
- UTC timestamp and non-secret run identifier;
- host label `assistant02` and group label `ai_ops_assistant`;
- boolean host-separation result;
- workspace paths, owner/group labels, and numeric modes;
- approved package names and resolved versions;
- endpoint label/port and TCP status only;
- syntax, check-mode, apply, idempotency, exclusion-scan, and compatibility statuses;
- unresolved gates and rollback status.

Evidence must not contain an address unless the evidence classification explicitly permits it, command output containing protected values, tokens, passwords, private keys, cloud profile contents, raw audit events, or response bodies.

## Validation and Idempotency

The foundation role and entrypoints must be validated in this order:

1. YAML parsing and `ansible-inventory --graph` without host contact.
2. Ansible syntax validation in an isolated `/tmp` virtual environment populated from root `requirements.txt`.
3. Static scans for forbidden roles, secret vars, excluded capability names, unmanaged paths, and prohibited package/repository/service behavior.
4. Explicitly approved `--check --diff --limit assistant02` execution.
5. Explicitly approved first apply limited to `assistant02`.
6. Non-mutating foundation validation, including TCP connectivity only to `192.168.121.5:5000` with no authentication.
7. A second limited apply that reports no changes.
8. Historical runtime, protected inventory, existing bootstrap, observability, and Molecule diff/entrypoint preservation checks.

Any failed assertion, unexpected target, unapproved package, secret exposure, extra endpoint, or unexplained second-apply change fails closed. It does not authorize a workaround such as route, firewall, repository, credential, or inventory modification.

## Revised-Only Rollback

Rollback order is:

1. stop future revised automation before it is introduced;
2. disconnect or destroy only `assistant02` when separately authorized;
3. remove only proven role-managed packages, workspace paths, and the `aiops_assistant` account/group;
4. revert only revised inventory and automation changes;
5. retain reviewed redacted acceptance evidence according to the evidence policy.

Never modify `assistant01`, `ansible/ai_ops_runtime/`, shared roles, OpenStack resources, network roles, control-plane services, or existing deployment/validation entrypoints. If package removal could affect shared host behavior, retain the packages and disconnect the revised runtime instead.

## Explicit Deferrals

The following remain deferred and absent: OpenStack credentials and authentication (Phase 02); diagnostic scripts (Phase 03); runner/registry and audit-event content (Phase 04); host-observer/SSH diagnostics (Phase 06); local stdio MCP configuration and process (Phase 07); and all provider, orchestrator, egress, wheelhouse, device-auth, bridge, remote-operation, and remediation behavior.
