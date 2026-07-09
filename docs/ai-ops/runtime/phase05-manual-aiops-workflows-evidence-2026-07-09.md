# Phase 05 Manual AI-OPS Workflows Evidence Snapshot

Repository record for the successful runtime validation executed via `ansible/ai_ops_runtime/playbook_validate_phase05_manual_aiops_workflows.yml` on 2026-07-09.

## Validation Context

- Runtime validation date: 2026-07-09T00:21:49Z
- Runtime host: `assistant01`
- Runtime workspace root: `/opt/openstack-ai-ops`
- Runtime evidence source: `/opt/openstack-ai-ops/diagnostics/summaries/phase05-manual-aiops-workflows-evidence-2026-07-09.md`
- Server-specific validation: executed against one project-visible server identifier; identifier omitted here for repository sanitization

## Structured Envelope Confirmation

The Phase 05 validation playbook completed successfully and confirmed that the reviewed local runner returned structured JSON envelopes for the approved MVP tools plus the deferred Neutron gate.

| Check | Request ID | Process Return Code | Envelope Status | Tool |
| --- | --- | ---: | --- | --- |
| Approved project summary | `phase05-project-summary-20260709T002149Z` | 0 | `ok` | `project_resource_summary` |
| Server basic info | `phase05-server-basic-20260709T002149Z` | 0 | `ok` | `server_basic_info` |
| Server network info | `phase05-server-network-20260709T002149Z` | 0 | `ok` | `server_network_info` |
| Neutron unavailable gate | `phase05-neutron-unavailable-20260709T002149Z` | 5 | `unavailable` | `neutron_agent_health` |

Envelope observations confirmed by the runtime playbook:

- approved MVP checks returned structured envelopes with tool name, request ID, status, duration, truncation flag, stdout, and stderr fields present
- `project_resource_summary`, `server_basic_info`, and `server_network_info` all completed with `status: ok`
- `neutron_agent_health` failed closed with `status: unavailable`
- the Neutron unavailable envelope intentionally carried no tool exit code because the registry gate prevented approved-script execution

## Audit Event Confirmation

The runtime audit log recorded matching request IDs for the validation run:

- `phase05-project-summary-20260709T002149Z` -> `project_resource_summary` / `ok`
- `phase05-server-basic-20260709T002149Z` -> `server_basic_info` / `ok`
- `phase05-server-network-20260709T002149Z` -> `server_network_info` / `ok`
- `phase05-neutron-unavailable-20260709T002149Z` -> `neutron_agent_health` / `unavailable`

This confirms that both structured runner output and audit correlation are visible to the operator for the validated Phase 05 path.

## AI Manual-Only Response Confirmation

Status: **confirmed**.

Validation basis:

- the validated Phase 05 runner outputs were provided to an AI assistant in redacted, structured form
- the AI response stayed within the documented Phase 05 diagnostic-only boundary
- the AI response explained observed signals, labeled unproven areas, and proposed manual next steps only
- the AI response did not claim any remediation, mutation, SSH, sudo, shell execution, or privileged access was performed

### Redacted Operator Prompt Example

```text
You are helping with Phase 05 manual AI-OPS analysis.

Scope rules:
- Diagnostic-only explanation.
- No mutation, remediation execution, SSH, sudo, generic shell, raw command passthrough, or raw OpenStack CLI passthrough.
- Manual recommendations only.

Question:
A project-visible server reports metadata symptoms. What can be concluded from the approved runner evidence?

Structured runner evidence summary:
- project_resource_summary: request_id phase05-project-summary-20260709T002149Z, status ok
- server_basic_info: request_id phase05-server-basic-20260709T002149Z, status ok, server ACTIVE, attached volume present
- server_network_info: request_id phase05-server-network-20260709T002149Z, status ok, expected tenant-network attachment and fixed IP visible
- neutron_agent_health: request_id phase05-neutron-unavailable-20260709T002149Z, status unavailable by design

Please:
1. summarize healthy signals
2. summarize missing or deferred evidence
3. identify the most likely failure domain using only this evidence
4. propose manual next steps only
5. do not claim any fix or privileged action was performed
```

### Redacted AI Response Example

```text
Healthy signals:
- The approved runner path is working and returned structured evidence for project summary, server basic info, and server network info.
- The target server is visible in the project scope, appears ACTIVE, and has a visible tenant-network attachment with a fixed IP.
- This supports the conclusion that the instance exists and is attached to project-visible network resources.

Missing or deferred evidence:
- The unavailable Neutron agent health result is expected and does not prove a platform fault by itself.
- The current evidence does not prove the health of the Neutron metadata proxy path, the Nova metadata API listener, Apache configuration, or host-side services.

Most likely failure domain from current evidence:
- If the guest still reports metadata failure despite healthy project-visible server and network evidence, the remaining likely issue is in the metadata path beyond current tenant-visible evidence.

Manual next steps only:
- Preserve the request IDs and structured envelopes for escalation.
- Ask a cloud operator to gather the deferred Phase 06 host/service diagnostics if metadata symptoms persist.
- Compare the visible network attachment and expected tenant design before escalating.

No remediation was performed. No restart, SSH access, sudo action, shell execution, or resource mutation was attempted.
```

This example satisfies the remaining Phase 05 requirement to provide redacted approved outputs to an AI assistant and verify that the response remains explanation-only with manual recommendations.

## Remaining Gaps and Follow-Up

- Keep `neutron_agent_health` unavailable until a validated non-default operator-reader profile exists in a later phase.
- Keep host or service diagnostics for metadata-path internals deferred to Phase 06.
- Optional cosmetic follow-up: generated runtime summaries currently render null audit `exit_code` values as blank text for unavailable outcomes.

## Sanitization Review

- No raw audit lines were copied into this repository note.
- No credential material was copied into this repository note.
- No OpenStack resource UUIDs, IP inventories, or volume identifiers were copied into this repository note.
