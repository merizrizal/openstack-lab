## Architectural Design Specification: Temporary Approval-Gated Device-Authentication Egress

**Source:** Phase 07 manual-authentication blocker in `45-phase07-gateway-forwarding-egress-role-refactor-to-manual-auth-handoff.md`; `07-openai-remote-provider-boundary-ads-revised.md` Chunk 6; `07-provider-gateway-egress-enforcement-revision-ads.md`.

**Goal:** Let the operator perform one manual device-authentication flow in the fixed `assistant` runtime context through a separately approved, temporary, least-privilege egress exception, then remove it and prove the permanent direct-egress deny policy is restored. This ADS does not authorize a remote request or Chunk 7.

---

### I. Overview and Contract

The exception is a short-lived firewall rule owned by a proposed sibling role, `assistant_device_auth_egress`. It is distinct from the permanent `assistant_egress` role and must be inserted before the permanent owner reject. It permits only operator-reviewed device-auth IPv4/IPv6 destinations, reviewed resolver destinations when required, and TCP/443. It is not a general Internet, provider API, proxy, or gateway exception.

**Configuration Contract (Conceptual):** An operator supplies a reviewed, non-secret approval object for one run: approval identifier, UTC expiry, exact destination IP addresses/CIDRs per family, optional resolver IPs and port 53 protocol, and the fixed user `assistant`. Hostnames, URLs, authorization codes, tokens, account identifiers, and provider responses are not configuration values and must never be captured.

**State transition:** permanent egress deny active -> preflight and explicit approval -> temporary device-auth allow rules active -> operator-owned login pause -> expiry or explicit rollback -> temporary markers removed and permanent owner reject materially verified. Any uncertain state fails closed and leaves remote mode disabled.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `assistant_egress` installs allow rules followed by an owner `REJECT` for `assistant` in `ufw-before-output` and `ufw6-before-output`.
- `assistant_egress_validation` already proves UFW activity, UFW chain traversal, numeric UID resolution, rule ordering/materialization, and marker-only rollback.
- `playbook_validate_phase07_provider_gateway_egress.yml` requires explicit approval flags and uses an `always` rollback block.
- The gateway accepts only loopback `POST /v1/responses`; it cannot relay device authorization. The provider-boundary ADS requires direct provider egress by `assistant` to remain denied outside this approved compatibility flow.

#### Assumptions

- The operator separately owns an active UFW baseline already accepted for the permanent egress role.
- The actual device-auth endpoints, address records, resolver requirements, protocol, and a safe maximum window are not yet repository evidence. Chunk 0 must establish and approve them without performing login, retaining codes, or collecting credentials.
- UFW rule placement can be proven such that the temporary allow marker precedes the permanent `AI-OPS assistant egress policy` marker and its final reject rule.

#### Open confirmations for Chunk 0

- Exact device-auth-only endpoints and resolved IPv4/IPv6 addresses/CIDRs; whether DNS is necessary; and a bounded expiry policy.
- Whether the client’s device flow needs any endpoint beyond the approved set. If so, stop for a new ADS decision.
- Exact Ansible integration point, handler ownership, and a validation playbook that guarantees rollback on controller interruption as far as Ansible execution permits.

### III. Required Technical Dependencies and Imports

- Existing roles: `assistant_egress`, `assistant_egress_validation`, and `ai_client_runtime`.
- Existing UFW ownership and validation mechanisms: `blockinfile`, restore-test validation, `Reload UFW`, `meta: flush_handlers`, active `iptables`/`ip6tables` inspection.
- Proposed role artifacts (subject to Chunk 0): `roles/assistant_device_auth_egress/tasks/main.yml`, IPv4/IPv6 templates, and an expiry/rollback validation task or focused Phase 07 playbook.
- No new Python, client, OpenAI, browser, proxy, credential store, or secret-management dependency is authorized.

### IV. Step-by-Step Procedure / Execution Flow

1. The operator approves a single use by supplying a non-secret approval ID, UTC expiry, and exact reviewed network tuples; the playbook requires an affirmative apply flag.
2. Read-only preflight confirms target `assistant01`, permanent egress materialization, UFW active state, numeric assistant UID, current UTC time before expiry, strict schema, no broad CIDR, and no destination overlap with management or loopback allowances.
3. The role renders and restore-tests separate temporary IPv4/IPv6 marker blocks. It permits only approved device-auth/resolver tuples and is inserted before the permanent marker/reject.
4. Reload once and assert active rules show each temporary allow before the permanent owner reject; verify no unrelated owner allow is added.
5. Pause with an explicit operator instruction. The operator runs the device login interactively as `assistant`; automation neither launches, observes, copies, nor logs it. Sanitized result is only operator-declared success/failure.
6. On expiry, operator-declared completion, or any validation failure, remove only temporary markers, reload, and prove their runtime absence while the permanent reject is still materialized.
7. Run metadata-only direct-egress denial against a separately approved non-provider synthetic endpoint. Do not contact OpenAI during validation. Remote mode and Chunk 7 remain disabled.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
|---|---|---|---|
| Approval | Apply flag, approval ID, expiry, or tuple schema missing | Do not write rules | `ERR_DEVICE_AUTH_APPROVAL` (proposed) |
| Preflight | Expired, too-long, broad, loopback, management-overlapping, hostname, or unrecognized tuple | Do not write rules | `ERR_DEVICE_AUTH_SCOPE` (proposed) |
| Preflight | Permanent egress reject/UFW traversal absent | Stop; do not create exception | `ERR_DEVICE_AUTH_BASELINE` (proposed) |
| Apply | Candidate parser or reload fails | Remove temporary markers if written; prove state | `ERR_DEVICE_AUTH_APPLY` (proposed) |
| Materialization | Allow is absent, after reject, or extra owner allow exists | Roll back temporary block | `ERR_DEVICE_AUTH_NOT_MATERIALIZED` (proposed) |
| Operator pause | Login fails, expires, is cancelled, or needs another endpoint | Roll back; do not broaden rules | `ERR_OPENAI_AUTH_MANUAL` |
| Cleanup | Expiry reached or rollback proof fails | Keep remote mode disabled; report marker/ruleset metadata only | `ERR_DEVICE_AUTH_ROLLBACK` (proposed) |

### VI. Security, Integrity, Idempotency, and Cleanup

- **Security:** No automated login, browser control, device-code handling, token access, credential inspection, TLS weakening, proxying, or gateway bypass. Use exact numeric destination tuples; do not implement hostname-based broad allowances. IPv4 and IPv6 default to deny if no separately reviewed tuple is supplied.
- **Integrity:** Treat every approval object as untrusted until schema and fixed-boundary assertions pass. Bound expiry against a proposed maximum decided in Chunk 0; reject future/invalid timestamps and use target-host UTC only.
- **Idempotency:** A valid active approval may converge to one marker block per family. Reapplication must not extend expiry, replace the approval ID, or broaden tuples. A new window requires a new explicit approval.
- **Cleanup:** The rollback path removes only the temporary marker blocks, reloads only when UFW remains active, and proves temporary owner allows/markers are absent while permanent policy remains. The operator must manually cancel any exposed device code; none is recorded.

### VII. Validation Strategy

- **Static/syntax:** `rtk ansible-playbook --syntax-check -i ansible/ai_ops_runtime/inventories/local/local.yml <proposed-device-auth-playbook>` and `rtk ansible-lint <changed-role-or-playbook-files>`.
- **Template validation:** retain IPv4 and IPv6 restore-test validation before each UFW write.
- **Read-only checks:** UFW status, OUTPUT traversal, permanent marker/reject ordering, target UTC, approval schema, resolved UID, and rendered tuple count; retain metadata only.
- **Behavior:** first apply, active ruleset ordering, explicit operator pause (no captured login data), expiry/explicit rollback, second-run non-extension, and post-rollback synthetic denial.
- **Review:** `rtk git diff --check`, `rtk git diff -- <changed-files>`, and verify no logs, variables, fixtures, or docs contain code, URL, token, account, or raw provider output.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full capability in one pass.

#### Chunk 0: Endpoint, Expiry, and Integration Discovery
- **Goal:** Establish the reviewed non-secret tuple set, resolver need, expiry bound, baseline rule insertion point, and safe operator procedure.
- **Files to read:** existing ADSs; `assistant_egress` templates/tasks; validation tasks; current UFW metadata; client documentation/status only as permitted by the operator.
- **Commands:** metadata-only ruleset/UFW probes and scoped repository searches. No login, provider request, or firewall write.
- **Evidence to confirm:** exact tuples, required protocols, active permanent reject, and marker ordering mechanism.
- **Stop condition:** Stop with no edits if any endpoint or resolver requirement remains unreviewed or cannot be narrowed to numeric tuples.

#### Chunk 1: Approval Contract and Compile-Safe Role Stub
- **Goal:** Add a disabled-by-default role/playbook contract that validates approval shape and fails before writes.
- **Files to change:** proposed role `defaults/main.yml` and `tasks/main.yml`, plus at most one focused validation playbook after Chunk 0 confirms integration.
- **Symbols to add/change:** conceptual `ai_ops_device_auth_egress` approval mapping and proposed errors above.
- **Implementation shape:** strict allowlisted keys, `enabled: false` default, target/UTC/expiry/tuple assertions; no template rendering or UFW change yet.
- **Validation:** Ansible syntax/lint and invalid/expired approval runs proving no temporary marker exists.
- **Stop condition:** All invalid input fails closed with no firewall change.

#### Chunk 2: One-Family Temporary Rule and Materialization Slice
- **Goal:** Implement IPv4 temporary allow insertion before the permanent reject and deterministic marker-only removal.
- **Files to change:** proposed IPv4 template and role task file; reuse existing handler only after its ownership is confirmed.
- **Symbols to add/change:** conceptual IPv4 temporary marker and post-reload ordering assertion.
- **Implementation shape:** restore-test, exact approved TCP/443 tuples only, one reload, active-rule ordering assertion, `always` rollback path.
- **Validation:** approved synthetic non-provider tuple in a controlled test; marker/ruleset proof before and after rollback.
- **Stop condition:** Roll back immediately if placement, tuple count, or permanent reject proof differs.

#### Chunk 3: IPv6 and Resolver Parity Slice
- **Goal:** Add only Chunk-0-approved IPv6 and resolver rules with equivalent ordering and removal guarantees.
- **Files to change:** proposed IPv6 template and the same focused role/validation file.
- **Symbols to add/change:** conceptual family-specific allow tuple validation.
- **Implementation shape:** no IPv6/resolver rule is emitted when absent from approval; protocols and ports are explicit.
- **Validation:** parser checks, active ordering, tuple count, rollback, and permanent deny proof for both families.
- **Stop condition:** Any asymmetric or broader family behavior removes all temporary markers and stops.

#### Chunk 4: Operator Pause, Expiry, and Final Rollback Validation
- **Goal:** Exercise the approved temporary window without automation observing authentication; prove expiry/completion rollback and restored deny state.
- **Files to change:** one focused validation playbook/runbook after exact paths are confirmed.
- **Symbols to add/change:** conceptual operator pause gate and expiry/rollback metadata assertions.
- **Implementation shape:** apply -> verify -> operator-owned pause -> explicit completion or expiry -> `always` rollback -> post-rollback synthetic denial. No remote synthetic request.
- **Validation:** first run, second-run non-extension, explicit rollback, expiry path where safely testable, and sanitized evidence review.
- **Stop condition:** Do not advance to Chunk 7 unless temporary markers are absent and permanent direct-egress denial is materially proven.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline and diagnose if needed.

Task:
Execute Chunk 0 of the Temporary Approval-Gated Device-Authentication Egress ADS.

Mode:
Read-only discovery only. Do not edit files, change UFW, start device login, contact OpenAI, inspect credentials, or capture codes/URLs. Establish exact reviewed numeric destination tuples, resolver requirements, expiry bound, permanent-rule ordering, and rollback integration. Stop if any requirement cannot be narrowed.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, pre-edit-discipline, safe-python-edit, and post-edit-discipline.

Task:
Execute Chunk 1 only of the Temporary Approval-Gated Device-Authentication Egress ADS.

Add only the disabled-by-default approval contract and fail-closed preflight. Do not render firewall rules, permit egress, run login, or continue to Chunk 2. Run targeted validation, review the diff, and stop.
```

### X. Conclusion and Next Steps

This design preserves the permanent direct-egress deny boundary while allowing an operator-owned device-auth compatibility window only when its endpoint scope, approval, expiry, and rollback are independently proven. It intentionally does not determine provider endpoints or authorize any remote request. The next action is Chunk 0 read-only discovery and approval of its exact numeric tuple/expiry findings.
