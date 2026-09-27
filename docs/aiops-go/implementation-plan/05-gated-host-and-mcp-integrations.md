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

Excluded: admin credentials, root SSH, generic remote commands/paths, unrestricted sudo, forwarding, full configuration dumps, network MCP transport, arbitrary URI/file access and specialist agents.

## 05.4 Assumptions

- [ ] Phases 01-04 supply the authoritative boundary, curated knowledge contracts and qualified domain reports.
- [ ] Operator approves higher-visibility profiles and host aliases independently. Missing approval means disabled, never an implicit prerequisite for the core MVP.
- [ ] Maintainer selects the retained MCP implementation, first client and supported protocol/SDK version before compatibility testing. Initial transport is local stdio.
- [ ] Provisioning and live host/client checks are operator-controlled and separately authorized; source fixtures do not establish deployed restriction.

Dependency: Phases 01-04. Phase 06 can proceed without this phase when both integration tracks remain disabled.

## 05.5 Ordered Tasks

### Step 1 - Prove restricted higher-visibility diagnostics

Estimate: **2-4 days / 12-24 hours**.

- [ ] Review existing observer deployment/helpers and record approved host-role aliases, fixed operations, service/log mappings, endpoints and independent operator/SSH profile bindings. Discovered host relationships never automatically authorize access.
- [ ] Configure pinned host keys, restricted observer keys/forced entry points, no interactive shell/forwarding/root login, and exact sudo operation/argument rules only where needed. Test shell escapes, wildcard abuse and caller-selected destination/path/user/key rejection.
- [ ] Validate operator-reader only for approved service/Neutron-agent reads; disable unavailable profiles rather than selecting admin or the other profile after failure. Keep provisioning credentials outside the diagnostic runtime.
- [ ] Register reviewed Neutron agent health, recent Nova/Neutron/metadata logs and narrowly necessary metadata listener/service facts. Do not expose generic process/configuration inspection; the Nova port-8775 observation must be a fixed reviewed operation if supported.
- [ ] Bound host/service/window combinations, elapsed time, remote scan volume, line/byte output and concurrent work before reading unlimited logs. Handle rotations, unsupported layouts, unreachable hosts and permission denial explicitly.
- [ ] Apply the shared structured result, scope, audit and redaction contracts before local persistence or model use; withhold sensitive configurations and sanitize free-text secrets.
- [ ] Test all alias/operation/window positives and negatives, missing prerequisites, floods, cancellation, redaction and host/profile escape with offline fixtures.
- [ ] Feed permitted observations into Phase 04 metadata cases; demonstrate healthy agent lists plus missing Nova listener evidence and missing-host partial results without inducing a real outage.
- [ ] Prepare independent enable/disable, key rotation/revocation and deployed restriction procedures for Phase 07. Keep tools disabled until their applicable deployed acceptance passes.

Done when:

- [ ] AC-013 has bounded host-contract fixtures, and the enabled/disabled capability matrix identifies every remaining deployed prerequisite; project-reader operation works with all higher-visibility tools disabled.

### Step 2 - Expose the same contracts through local MCP

Estimate: **2-3 days / 12-18 hours**.

- [ ] Adapt the selected existing MCP service where practical; derive discovery/schema/availability from the authoritative registry. Expose exactly the approved enabled subset without a second policy implementation.
- [ ] Bind session/client identity and permitted cloud/project/targets outside tool arguments. Route every call through the same validation, authorization, profile, bounds, redaction, audit and result pipeline as local execution.
- [ ] Map protocol errors and all result statuses without hiding denied/unavailable/cancelled distinctions. Bound request size/concurrency and propagate cancellation; reserve stdout for stdio messages and send sanitized operational logs separately.
- [ ] Expose only fixed curated resource identities and reviewed diagnostic prompts for boot, metadata/network and attachments. Preserve revision/chunk citations and limitations; reject traversal, symlink escape, arbitrary URIs and secret-bearing resources.
- [ ] Keep prompt/resource content untrusted; it cannot grant tools, host access, provider authorization or new scope. A client's possible remote inference is a separate Phase 02 disclosure decision, not MCP permission.
- [ ] Run local/MCP parity for valid and invalid calls, scope/profile override, generic executable requests, secret canaries, audit failure, timeout/cancel, unavailable profiles and optional host tools when enabled.
- [ ] Verify exact discovery, resource/prompt behavior and no unintended listening port with an offline client harness; document supported client versions and independent shutdown/revocation.
- [ ] Prepare an explicitly approved client smoke test for Phase 07; protocol validation does not require real inference. Any network transport request requires a separate authenticated-transport/network design before enablement.

Done when:

- [ ] AC-019 and MCP portions of AC-012 prove policy/result equivalence; disabling MCP preserves manual/local workflows, and host tools are absent unless independently enabled.

## 05.6 Phase Definition of Done

- [ ] Each integration is either independently accepted or explicitly optional-disabled with reasons and enablement prerequisites.
- [ ] All enabled adapters preserve scope, bounds, privacy, audit and unavailable-capability semantics.
- [ ] No extra infrastructure authority, arbitrary file access or network-facing service is introduced.
- [ ] Deployed restriction/client evidence is assigned to Phase 07 and never inferred from fixture success.

## 05.7 Risks

| Risk | Mitigation |
| --- | --- |
| Restricted sudo helper permits escape | Review exact remote commands/arguments and negative-test the remote boundary. |
| Logs contain credentials despite read-only access | Minimize collection, redact before all consumers and withhold unsafe content. |
| MCP becomes a parallel permissive runner | Registry-derived discovery and entry-point parity tests. |
| Optional hosts accidentally block core release | Independent tracks and explicit missing-evidence reports. |
| MCP client forwards context remotely | Require separate client disclosure review and model authorization. |
