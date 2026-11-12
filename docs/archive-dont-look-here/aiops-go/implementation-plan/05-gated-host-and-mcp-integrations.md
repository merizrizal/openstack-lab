# 05. Gated Host and MCP Integrations

## 05.1 Goal

Enable optional higher-visibility evidence and local interoperability without granting new ambient authority or duplicating policy.

```text
independent capability approval -> validated host/profile or MCP adapter -> existing boundary -> equivalent evidence/audit
```

## 05.2 Estimate

Total: **4-7 engineer-days / 24-42 focused hours**.

The two steps are independent enablement tracks. MCP may expose project-only tools without enabling hosts; host diagnostics may be used locally without MCP.

## 05.3 Scope

Included: separately validated operator-reader and restricted SSH-observer tools, Neutron health, bounded Nova/Neutron/metadata evidence, local/stdio MCP tools/resources/prompts and parity tests. Primary requirements: FR-022, FR-025–FR-026, FR-035; continued FR-010/FR-018/FR-027–FR-029. Evidence: AC-012–AC-013, AC-019; deployed checks finalized in Phase 07.

Excluded: admin credentials, root SSH, generic remote commands/paths, sudo in the initial host scope, forwarding, full configuration dumps, network MCP transport, arbitrary URI/file access and specialist agents. The existing Option B network MCP implementation and historical runtime are not modified or activated.

## 05.4 Assumptions

- [ ] Phases 01-04 supply the authoritative boundary, curated knowledge contracts and qualified domain reports.
- [ ] Operator approves higher-visibility profiles and host aliases independently within the accepted host contracts below. Missing or stale approval means disabled, never an implicit prerequisite for the core MVP.
- [ ] Retain the accepted local-stdio MCP client, SDK and interface below unless an applicable replacement is approved and its governing contracts amended; a maintainer selection alone cannot change them.
- [ ] Provisioning and live host/client checks are operator-controlled and separately authorized; source fixtures do not establish deployed restriction.

Dependency: Phases 01-04, including [Phase 01 contract reconciliation](01-safety-boundary-and-manual-slice.md#constraint-reconciliation-and-authority) and [Phase 03 recovery](03-durable-state-and-knowledge.md). Phase 06 can proceed without this phase when both integration tracks remain disabled.

### Retained contracts, readiness and amendment gates

This is a draft phase plan, not implementation or deployment authorization. Before an executable task contract, identify the approved PRD revision and approval evidence, accepted Phase 01–04 revisions, applicable contract amendments and prerequisite verification. The [overview](00-implementation-overview.md) records no approval of the current PRD. A commit or prior draft review is not approval.

- **Host authority:** Inherit the revised [host Steps 1–4](../../ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-steps-01-to-04-operations-contract.md), [Steps 5–7](../../ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-steps-05-to-07-operations-contract.md), and [readiness](../../ai-ops-revised/runtime/phase06-live-acceptance-readiness-requirement.md) contracts, including accepted amendments. Before broader operator-reader authority, the exact project-reader Neutron read must prove `policy_denied` and the owner must approve need and lifecycle; a successful or approved-empty read needs no broader profile, and transport, catalog, authentication or configuration failure is not proof of need. Preserve independent project-reader, operator-reader and host-observer authority, expiry, rotation and revocation. The accepted initial host scope requires `sudo_required: false`; unreadable sources return bounded denial/unavailability, never sudo fallback. Preserve the exact D05 host/role/source matrix and fixed Neutron operation, not general service reads.
- **Host evidence and privacy:** The Steps 5–7 contract's D05–D07 fixes public inputs/defaults, source mapping, output schemas, windows, ordering, normalization, duplicate-event retention, limits, redaction and failure behavior. Apply it exactly, including host-side minimization, redaction and canary rejection **before SSH output**, followed by runner-side redaction; malformed data or failed redaction withholds all source-derived payload. The revised [host ADS §VI](../../ai-ops-revised/implementation-plan/ads/06-02-phase06-completion-and-phase05-prerequisite-closure-ads.md) reinforces both disclosure boundaries. Keep the closed collector boundary enforceable even by direct use of the observer key, not merely by front-end validation.
- **MCP retained interface:** Inherit [local MCP Steps 1–4](../../ai-ops-revised/runtime/mcp-interface-steps-01-to-04-operations-contract.md), [Steps 5–7](../../ai-ops-revised/runtime/mcp-interface-steps-05-to-07-operations-contract.md), and their applicable accepted amendments: local stdio on `assistant02`, `owner-managed-local-stdio-client-v1`, `mcp==1.28.1` with verified hash-locked offline artifact, separate local namespace and lifecycle, and exactly `project_resource_summary`, `server_basic_info`, `server_network_info`. The six fixed resources and three ordered prompts `project_summary`, `server_inspection`, `metadata_diagnosis` remain as specified in those contracts; omit any prompt whose required tool is absent, and keep standalone network/volume prompts and Phase 06 tools absent even if host tools are independently enabled. Prompts are non-executable. The adapter delegates to the revised runner, with one child, no queue/retry, fixed `local_cli` audit actor and no client identity forwarded. Registry projection must satisfy the accepted bounded projector/equivalence contract, not dynamically import the runner.
- **Version and replacement:** The retained runner has the closed six-status result envelope and one runner-generated terminal audit event per invoked request; the adapter writes no duplicate audit. The PRD's cancellation distinction, additional host/listener facts, and any expanded MCP subset or audit intent/events are target requirements, not permission to extend these closed contracts. Cancellation must clean up without silently adding a result status. Any incompatible result/audit version, client/SDK, namespace, tool/resource/prompt exposure, host/source mapping, listener operation, broader service read or sudo grant requires a scoped Level 2 decision, approved governing contract amendment and versioned migration/rollback before enablement. Until then, affected behavior remains unavailable or explicitly limited, not reported as meeting the incompatible requirement.
- **Current readiness and selective reuse:** The host contract records a historically accepted run, not current deployment readiness. Confirm current owner-approved normalized revision, readiness and lifecycle evidence for the exact scope; otherwise keep affected capabilities disabled. Follow the [selective-reuse manifest](../../ai-ops-revised/runtime/selective-reuse-manifest.md): historical host assets remain unselected and cannot be inspected, copied or adapted without the exact approved amendment. Selection is not activation. Live access, credential operations, deployment and acceptance each require separate authorization.

Compliant fixture design, helper organization and adapter mechanics are Level 0/1; changing a product, security, privilege, exposure or audit boundary is Level 2. Where reconciliation remains unresolved, continue only non-activating work that does not prejudge the decision.

## 05.5 Ordered Tasks

### Step 1 - Prove restricted higher-visibility diagnostics

Estimate: **2-4 days / 12-24 hours**.

- [ ] Review only eligible revised observer assets under the selective-reuse manifest; record approved host-role aliases, exact fixed operations and source mappings, protected projection and independent profile bindings. Discovered host relationships never automatically authorize access.
- [ ] Prove project-reader insufficiency and obtain the operator-reader lifecycle decision as specified above before creating broader authority; use only the exact approved Neutron-agent operation. Disable unavailable profiles rather than selecting admin or another profile after failure. Keep provisioning credentials outside the diagnostic runtime.
- [ ] Specify pinned host keys, restricted observer keys and forced entry point with no interactive shell, forwarding, root login or sudo. Test direct-key/collector rejection of original commands, arguments, forwarding, shell escapes, wildcard abuse, unauthorized sources and caller-selected destination/path/user/key; reject cross-authority environments (`OS_*` for hosts and observer state for API tools).
- [ ] Register Neutron agent health and recent Nova/Neutron/metadata evidence only within the accepted D05 mappings and applicable activation gates. Retain explicit unavailable stubs where required by those contracts. The Nova port-8775 listener observation and any additional service facts remain unavailable until a separate scoped amendment approves a fixed operation; do not expose generic process/configuration inspection.
- [ ] Bound host/service/window combinations, elapsed time, remote scan volume, line/byte output and concurrent work before reading unlimited logs. Handle rotations, unsupported layouts, unreachable hosts and permission denial explicitly.
- [ ] Enforce frozen D05–D07 processing and host-side redaction/canary rejection before transport, then runner redaction before results, persistence or model use. Withhold all source-derived payload on malformed source or redaction failure; never leak raw errors.
- [ ] Test exact inputs/defaults and limits, malformed/duplicate fields, projection uniqueness/freshness and role mapping, NFC normalization, duplicate-event retention, deterministic ordering/truncation and all-or-nothing withholding. Add alias/operation/window negatives, direct SSH/collector restrictions, cross-authority isolation, missing prerequisites, floods, cancellation and canaries in offline fixtures.
- [ ] Feed permitted observations into Phase 04 metadata cases; use synthetic fixtures to show that healthy agent lists do not prove Nova listener availability, and that missing listener or host evidence produces an explicit gap and partial result. Do not imply the unapproved listener operation exists or induce a real outage.
- [ ] Prepare independent enable/disable, key rotation/revocation and deployed restriction procedures for Phase 07. A failed deployment must remove partial permissive authority; rollback removes only exact owned artifacts and preserves independent authorities. Keep tools disabled until their applicable deployed acceptance passes.

Done when:

- [ ] AC-013 has bounded host-contract fixtures, and the enabled/disabled capability matrix identifies every remaining deployed prerequisite; project-reader operation works with all higher-visibility tools disabled.

### Step 2 - Expose the same contracts through local MCP

Estimate: **2-3 days / 12-18 hours**.

- [ ] Adapt the eligible revised local MCP service only within the retained interface above; prove the fixed read-only projector's equivalence to the authoritative registry and fail closed on mismatch. Do not expose higher-visibility tools merely because they are enabled locally.
- [ ] Preserve application-owned cloud/project/target authorization outside tool arguments, without accepting client initialization metadata, names, principals, actor or correlation IDs as authority or forwarding them to runner/audit. Route calls through the same boundary; if the retained runner cannot enforce the needed application scope, block the integration pending an approved reconciliation.
- [ ] Preserve the six runner statuses and fixed envelope; do not synthesize `cancelled` or additional audit events. Enforce the accepted request, deadline, output and one-child concurrency limits, no queue/retry, and EOF/cancellation termination and reaping. Reserve stdout for protocol frames and sanitize bounded stderr.
- [ ] Expose exactly the six fixed curated resource identities and three approved prompts with their closed schemas, ordering, rendering, limits and evidence-gap instructions. Reject arbitrary URIs, traversal, symlink escape and secret-bearing resources. Any expanded resource, citation or prompt behavior requires the applicable approved amendment.
- [ ] Keep prompt/resource content untrusted; it cannot grant tools, host access, provider authorization or new scope. A client's possible remote inference is a separate Phase 02 disclosure decision, not MCP permission.
- [ ] Run local/MCP parity for valid and invalid calls, client-identity spoofing, scope/profile override, generic executable requests, canaries, audit failure, timeout/cancel and unavailable profiles. Assert the applicable version, one terminal audit per invoked request and no adapter duplicate; require durable terminal audit before successful publication. Audit failure withholds payload/raw errors, blocks further dispatch and never retries. Exercise Phase 03 cross-sink recovery: preserve committed evidence/audits, no false success or automatic replay, and visible incomplete/uncertain state; do not claim external reads or separate sinks are one transaction or delete audit to simulate rollback.
- [ ] Verify exact tool/resource/prompt discovery, deterministic pure list/read/get operations with no tool dispatch, audit or persistent side effects, malformed requests, one-child/no-queue concurrency, EOF/cancellation cleanup and no listener with an offline harness. Run retained runner and local MCP regression suites in their documented environments; verify independent client shutdown and exact-owned-artifact rollback without affecting shared or Option B assets.
- [ ] Prepare an explicitly approved client smoke test for Phase 07; protocol validation does not require real inference. Any network transport request requires a separate authenticated-transport/network design before enablement.

Done when:

- [ ] AC-019 and MCP portions of AC-012 prove the retained interface's policy/result equivalence; disabling MCP preserves manual/local workflows, and Phase 06 tools remain absent from MCP even when independently enabled locally. Record unmet PRD parity/status requirements as limitations pending an approved amendment; do not claim the affected acceptance criterion passed.

## 05.6 Phase Definition of Done

- [ ] Each integration is either independently accepted or explicitly optional-disabled with reasons and enablement prerequisites.
- [ ] All enabled adapters preserve scope, bounds, host-to-runtime privacy, audit cardinality, recovery and unavailable-capability semantics; any incompatible requirement has an approved versioned amendment, migration and rollback or remains explicitly unavailable.
- [ ] No extra infrastructure authority, arbitrary file access or network-facing service is introduced.
- [ ] Deployed restriction/client evidence is assigned to Phase 07 and never inferred from fixture success.

## 05.7 Risks

| Risk | Mitigation |
| --- | --- |
| Direct observer-key use bypasses front-end validation | Enforce the forced, closed collector without sudo and negative-test the remote boundary. |
| Logs contain credentials despite read-only access | Minimize collection, redact before all consumers and withhold unsafe content. |
| MCP becomes a parallel permissive runner | Registry-derived discovery and entry-point parity tests. |
| Optional hosts accidentally block core release | Independent tracks and explicit missing-evidence reports. |
| MCP client forwards context remotely | Require separate client disclosure review and model authorization. |
