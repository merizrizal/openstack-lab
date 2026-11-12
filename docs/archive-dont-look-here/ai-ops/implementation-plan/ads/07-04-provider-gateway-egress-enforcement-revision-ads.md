## Architectural Design Specification: Provider Gateway Egress Enforcement Revision

**Source:** `docs/ai-ops/implementation-plan/ads/07-03-openai-remote-provider-boundary-ads-revised.md`, Chunk 5; Phase 07 UFW diagnosis on 2026-07-12.

**Goal:** Revise the disabled assistant egress-policy design so it fails closed before modifying UFW files when UFW is not globally enabled, and so a future approved application proves that UFW materialized the UID-owner rules in the active packet-filter path.

---

### I. Overview and Contract

This is a design-only revision. It does not authorize enabling UFW, editing UFW files, reloading UFW, or applying egress enforcement.

The egress policy remains a UFW-managed policy for `assistant` only. It must allow only the reviewed loopback and OpenStack-management exceptions, then reject all other IPv4 and IPv6 output owned by `assistant`. The provider gateway remains loopback-only and is not a firewall-management component.

**Precondition contract (proposed):** Before any managed block is inserted, the target host must prove all of the following through read-only checks:

1. the target is `assistant01`;
2. `/etc/ufw/ufw.conf` declares UFW enabled;
3. `ufw status verbose` reports active;
4. the active IPv4 and IPv6 OUTPUT paths traverse the applicable UFW before-output chains; and
5. the active backend accepts the rendered IPv4 and IPv6 candidates.

A failed precondition is a fail-closed deployment error: no block insertion, no reload, and no change to UFW's global enabled state.

**Materialization contract (proposed):** After an explicitly approved UFW reload, the play must prove from the active runtime rulesets—not only from candidate files—that both OUTPUT paths traverse the UFW chains and that the final UID-owner reject rule for `assistant` is present in each chain.

### II. Observed Evidence and Assumptions

#### Observed evidence

- The accepted provider-boundary ADS requires direct egress by `assistant` to be denied while retaining reviewed management access (`07-03-openai-remote-provider-boundary-ads-revised.md`, Security Boundary and Chunk 5).
- `tasks/assistant_egress.yml` presently asserts the static policy boundary and validates candidate files with `iptables-restore --test` and `ip6tables-restore --test`, then inserts managed blocks before `COMMIT`.
- The IPv4 and IPv6 templates target `ufw-before-output` and `ufw6-before-output`, respectively.
- `tasks/main.yml` does not include `assistant_egress.yml`; the policy is disabled and unwired.
- On `assistant01` during diagnosis, UFW 0.36.2 reported inactive and `/etc/ufw/ufw.conf` contained `ENABLED=no`. `iptables` and `ip6tables` used the `nf_tables` frontend; the live IPv4 and IPv6 OUTPUT policies were ACCEPT with no UFW traversal rules loaded.
- UFW's installed frontend returns `Firewall not enabled (skipping reload)` for `reload` when its backend is disabled. Candidate parser validation therefore cannot prove runtime materialization.
- The managed markers were absent from both UFW rule files after the earlier rollback.

#### Assumptions requiring confirmation

- An operator who owns the host's baseline firewall may choose to enable and adopt UFW in a separately reviewed operation. This design does not make that choice automatically.
- Once UFW is externally enabled, its active IPv4 and IPv6 rulesets will contain the expected before-output traversal. This must be proven in a read-only discovery chunk before any policy block is applied.
- The installed iptables-nft compatibility frontend can display the owner-match rules in a stable enough form for assertion. The implementation must resolve the `assistant` UID and assert the observed form rather than assume a username rendering.

### III. Required Technical Dependencies and Imports

- Existing Ansible role: `ansible/ai_ops_runtime/roles/ai_client_runtime`.
- Existing policy task and templates:
  - `tasks/assistant_egress.yml`
  - `templates/provider_gateway/aiops-assistant-egress-ipv4.rules.j2`
  - `templates/provider_gateway/aiops-assistant-egress-ipv6.rules.j2`
- Existing UFW commands on `assistant01`: `ufw`, `iptables`, `ip6tables`, `iptables-restore`, and `ip6tables-restore`.
- Proposed Ansible mechanisms: `ansible.builtin.command`, `ansible.builtin.assert`, `ansible.builtin.blockinfile`, a dedicated UFW reload handler, and `meta: flush_handlers`.

No new provider credentials, transport configuration, cloud configuration, general egress exception, standalone nftables rule, or standalone iptables rule is permitted.

### IV. Step-by-Step Procedure / Execution Flow

1. **Separate UFW ownership decision.** If UFW is disabled, stop with a bounded precondition failure. Do not run `ufw enable` from the egress role. An operator-owned baseline-firewall change must be separately reviewed and rolled back independently.
2. **Read-only preflight.** Register metadata-only results for UFW enabled state, `ufw status verbose`, the IPv4 and IPv6 OUTPUT traversal, the `assistant` numeric UID, and the selected iptables frontend. Mark all probes `changed_when: false`.
3. **Assert before write.** Assert the target, fixed policy contract, UFW enabled state, active status, and expected traversal before either `blockinfile` task executes. If any assertion fails, stop before modifying `/etc/ufw/before.rules` or `/etc/ufw/before6.rules`.
4. **Render and validate candidates.** Retain the existing restore-test validation for both candidate files. This is a syntax gate only, not evidence that policy is active.
5. **Apply managed blocks.** Only with `ai_ops_assistant_egress.enabled: true`, a passing preflight, and an approved UFW-enabled baseline, insert the exact IPv4 and IPv6 blocks.
6. **Reload once through UFW.** A dedicated, notified UFW reload handler must run only if a managed block changed. Flush the handler before runtime assertions.
7. **Prove materialization.** Re-run the metadata-only active-ruleset probes. Assert: UFW remains active; IPv4 OUTPUT traverses `ufw-before-output`; IPv6 OUTPUT traverses `ufw6-before-output`; each respective chain contains the final reject rule for the resolved `assistant` UID; and the reject occurs after the policy's narrow allow rules.
8. **Run approved synthetic connectivity checks.** As `assistant`, check loopback and reviewed management destinations still work. Check denial only against an operator-approved synthetic, non-provider, non-allowlisted endpoint with no credentials or payload. Retain pass/fail metadata only.
9. **Rollback on failed materialization or connectivity.** Remove only the managed markers, reload UFW only when it remains globally active, then prove the managed rules are absent. Do not disable UFW or alter operator-owned rules.

### V. Failure Modes and Resilience

| Stage | Failure mode | Agent/system action | Next state / error report |
|---|---|---|---|
| Preflight | UFW disabled or inactive | Fail before file writes; never enable UFW implicitly | `ERR_ASSISTANT_EGRESS_UFW_INACTIVE` (proposed) |
| Preflight | OUTPUT does not traverse expected UFW chain | Fail before file writes; capture chain names and backend metadata only | `ERR_ASSISTANT_EGRESS_CHAIN_PATH` (proposed) |
| Candidate validation | Restore-test rejects rendered rule syntax | Do not update the target file | `ERR_ASSISTANT_EGRESS_CANDIDATE` (proposed) |
| Reload | UFW reload reports inactive/skipped or fails | Do not claim enforcement; retain bounded status text | `ERR_ASSISTANT_EGRESS_RELOAD` (proposed) |
| Materialization | Rules are absent, unordered, or missing from either family | Roll back only managed blocks and re-check absence | `ERR_ASSISTANT_EGRESS_NOT_MATERIALIZED` (proposed) |
| Connectivity | Management access is blocked | Roll back only managed blocks; preserve global UFW state | `ERR_ASSISTANT_EGRESS_MANAGEMENT_ACCESS` (proposed) |
| Connectivity | Synthetic non-allowlisted connection succeeds | Roll back only managed blocks; remote mode remains disabled | `ERR_ASSISTANT_EGRESS_BYPASS` (proposed) |

### VI. Security, Integrity, Idempotency, and Cleanup

- Preserve UFW as the sole owner of its runtime rules. Do not add direct nftables or iptables runtime rules.
- Do not auto-enable, disable, reset, or otherwise adopt the operator-managed global UFW baseline.
- Do not inspect or emit credentials, cloud configuration, headers, prompts, provider data, or payloads. All probes must be metadata-only.
- Keep the policy disabled and unreferenced from `tasks/main.yml` until the revised design is accepted and its implementation chunks pass.
- Use the existing fixed-boundary assertions; any new configuration key requires an explicit contract revision and an allowlist assertion.
- A second run after successful application must report no managed-block change and must still pass runtime-materialization checks.
- Rollback removes only the marker-delimited blocks. It must never remove unrelated UFW rules or disable UFW.

### VII. Validation Strategy

#### Static validation

```bash
rtk ansible-playbook --syntax-check -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_setup_ai_client_runtime.yml
rtk ansible-lint ansible/ai_ops_runtime/roles/ai_client_runtime/tasks/assistant_egress.yml
rtk git diff --check
```

#### Read-only runtime preflight

- Confirm `ufw status verbose` is active and `/etc/ufw/ufw.conf` is enabled.
- Record `iptables -V`, `ip6tables -V`, and the active OUTPUT chain definitions.
- Assert expected UFW traversal separately for IPv4 and IPv6.
- Stop before any firewall change if the current state remains inactive. The diagnosis already establishes this stop condition on `assistant01`.

#### Approved application validation

- Render both templates and retain restore-test validation.
- After a single UFW handler reload, inspect active chains/rulesets and assert all materialization predicates.
- Run first application, second-run idempotency, management-access preservation, synthetic denial, and marker-only rollback checks.
- Review `git diff` and retain only sanitized metadata.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass.

#### Chunk 0: UFW Baseline and Traversal Discovery
- **Goal:** Confirm an operator-approved UFW-enabled baseline and actual IPv4/IPv6 chain traversal without changing the host.
- **Files to read:** existing ADS, `tasks/assistant_egress.yml`, both templates, and active UFW metadata.
- **Commands:** metadata-only UFW status, configuration, backend, OUTPUT, and chain probes.
- **Evidence to confirm:** UFW is active; both output paths traverse the anticipated chains; owner-match display form is known.
- **Stop condition:** Stop with no edits if UFW remains inactive or traversal differs. This is the current state.

#### Chunk 1: Fail-Closed UFW Preflight Contract
- **Goal:** Add read-only, no-change preflight probes and assertions before the first UFW file write.
- **Files to change:** `tasks/assistant_egress.yml` and, if needed, one new focused preflight task file.
- **Symbols to add/change:** proposed UFW enabled-state, active-status, traversal, and resolved-UID assertions.
- **Implementation shape:** Register command output with `changed_when: false`; fail before `blockinfile` when the baseline is inactive or unrecognized.
- **Validation:** Ansible syntax/lint plus an inactive-UFW run proving no marker block is written.
- **Stop condition:** A disabled baseline deterministically fails without changing `/etc/ufw`.

#### Chunk 2: Reload and Runtime-Materialization Verification
- **Goal:** Make a changed managed block trigger exactly one UFW reload and prove both runtime rule families contain ordered owner rules.
- **Files to change:** `tasks/assistant_egress.yml` and `handlers/main.yml`.
- **Symbols to add/change:** proposed `reload ufw` handler notification and post-reload assertion tasks.
- **Implementation shape:** Notify only on block changes, flush the handler, then inspect loaded OUTPUT paths and owner rules using the resolved UID.
- **Validation:** Candidate syntax validation; handler idempotency; active-ruleset assertion after an operator-approved application.
- **Stop condition:** Stop and roll back marker blocks if any materialization assertion fails.

#### Chunk 3: Synthetic Enforcement and Rollback Validation
- **Goal:** Prove narrow management allowances, non-provider synthetic denial, second-run idempotency, and marker-only rollback.
- **Files to change:** one proposed dedicated Phase 07 validation playbook or an existing approved validation playbook after its exact integration point is confirmed.
- **Symbols to add/change:** conceptual metadata-only checks for allowed management connectivity, denied synthetic connectivity, and post-rollback rule absence.
- **Implementation shape:** Never submit provider data or credentials; record only pass/fail, backend, and chain metadata.
- **Validation:** First run, second run, denial, management preservation, rollback, and final ruleset checks.
- **Stop condition:** Direct egress remains unclaimed unless the deny test and post-reload materialization assertions both pass.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline and diagnose.

Task:
Execute Chunk 0 of the Provider Gateway Egress Enforcement Revision ADS.

Mode:
Execute Chunk 0 only. Do not edit files or change firewall state.
Confirm UFW enabled state, active backend, and IPv4/IPv6 output-chain traversal using metadata-only probes. Stop if UFW is inactive or the path differs.
```

After an operator-approved UFW baseline exists and Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, pre-edit-discipline, safe-python-edit, and post-edit-discipline.

Task:
Execute Chunk 1 only from the Provider Gateway Egress Enforcement Revision ADS.

Do not continue to Chunk 2. Add only fail-closed read-only preflight assertions, run targeted validation, review the diff, and stop.
```

### X. Conclusion and Next Steps

The current UFW-disabled state is a hard stop, not a condition the egress role may repair automatically. The next required decision is whether the operator will separately establish and own an active UFW baseline on `assistant01`. Only after that decision and a fresh read-only traversal confirmation may Chunk 1 be implemented. Remote provider mode and direct-egress compliance remain unaccepted until the full materialization and synthetic-denial validation succeeds.
