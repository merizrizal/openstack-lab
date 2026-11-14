# 07. Local MCP and Approved Client Sessions

**Phase boundary:** PROPOSED.
**Authority:** Roadmap phase, not an approved implementation task contract.
**Source requirements:** [PRD](../prd.md), Solution; Model boundary and interoperability; Session, data lifecycle, and legacy records; Testing Decisions 4, 14–15. FR-010–FR-011, FR-017–FR-019, FR-023–FR-029, FR-032–FR-035, FR-039–FR-041, FR-045–FR-047; NFR-001–NFR-003, NFR-005–NFR-006, NFR-008, NFR-010–NFR-015; AC-004, AC-009, AC-012, AC-014–AC-015, AC-019, AC-022, AC-028–AC-030.
**Decision gaps:** G1 authenticated client context, session-bound independently enforced egress/revocation; G6 independent real Pi and full protocol validation. Existing inference-only Pi approval is not standalone client authorization.

## 07.1 Goal

Expose the trusted Go catalog and curated knowledge through local/stdio MCP without changing policy, and prove a separately approved standalone Pi client can use it within a verified session/egress boundary.

```text
Go CLI reviews scope/targets/capabilities/egress/lifetime -> session approval
  -> independently verified client connection -> local/stdio MCP
  -> same audited Go gateway -> session end -> egress revoked
```

## 07.2 Estimate

```text
7–11 engineer-days
42–66 focused hours
```

## 07.3 Scope

Included:

- Local/stdio MCP mode in the same Go runtime executable, using enabled reviewed tools only.
- Read-only curated resources and diagnostic prompts for metadata, VM boot, network and volume workflows.
- CLI-approved client sessions with one-hour configurable default, identity/context binding, finite budgets and independently enforced client egress.
- Manual/automated/MCP parity and real standalone Pi interoperability, including tools/resources/prompts and teardown.

Excluded:

- HTTP/network-exposed MCP, arbitrary local client trust, reusable session approval across disconnects and generic execution/file tools.
- Native MCP/tool access inside Go-owned Codex/Pi inference sessions; those remain inference-only.
- Installing/updating/authenticating Pi or provisioning firewall/sandbox policies from diagnostic tools.

## 07.4 Assumptions

- [ ] Shared gateway and curated knowledge contracts from Phases 01–06 are verified; only capabilities with required manual validation and readiness evidence can be advertised/enabled.
- [ ] An independently verified local client security context can be bound to a specific approval without exposing reusable credentials in arguments/logs.
- [ ] Operator-managed client environment and egress policy can restrict approved destinations/data classes and reliably revoke access on session end; otherwise standalone evidence delivery fails closed.
- [ ] Pi is separately approved as a real standalone client; its Go inference-adapter approval supplies no session authority.

## 07.5 Ordered Tasks

### Step 1 - Bind every connection to explicit session authority

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Add Go CLI review/approval for cloud/project, permitted targets, capabilities, egress profile and lifetime before connection. Project-wide summaries require explicit project-wide approval.
- [ ] Default sessions to one hour with operator configuration; bind connection and independently checked client security context to approval/policy identity. Unknown/unapproved local processes cannot reuse it.
- [ ] Use the approved authenticated binding mechanism without credentials in command arguments or logs; reject expired, revoked, mismatched, replayed or unverified contexts.
- [ ] Independently verify managed client egress against approved destinations/data classes before evidence delivery. Sanitization, disclosure consent and egress enforcement remain separate obligations.
- [ ] End approval on revocation, expiry, disconnect or runtime shutdown; a reconnect/new session needs fresh approval. Revoke dedicated client environment egress and stop new dispatch/delivery at session end.
- [ ] Apply cancellation attempts and withholding for in-flight authorization changes; report possible prior reads/transmission and never claim client copies or sent data were erased/recalled.

Done when:

- [ ] Context spoof/replay, expiry/disconnect/shutdown, teardown failure and in-flight revocation tests cannot yield new unauthorized evidence or reusable session authority.

### Step 2 - Expose only reviewed tools, resources and prompts

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Add a local/stdio MCP transport in the runtime, with protocol output separated from diagnostics/logging and finite request/message/output/time limits.
- [ ] Discover exactly the enabled reviewed diagnostic subset permitted by session scope; maintain versioned names/schema/result translations and readiness limitations.
- [ ] Route every call through the same Go gateway with application-owned scope/profile, relationship, budget, validation, redaction and audit checks. MCP cannot select implementations or supply credentials/policy.
- [ ] Expose only approved bounded curated resources with stable source/revision/chunk identity and current session visibility; do not expose arbitrary paths, archives, raw protected state or full configurations.
- [ ] Provide diagnostic-only metadata, VM boot, network and volume prompts. Prompt retrieval is not diagnostic/plan authorization and never broadens scope or instructs runnable mutation.
- [ ] Preserve all result states, safe errors, partial project-summary category statuses, truncation/redaction and correlation metadata through documented MCP translations.

Done when:

- [ ] Protocol fixtures exercise discovery, calls, resources and prompts and show no unknown/disabled/out-of-scope capability or resource leakage.

### Step 3 - Prove entry-point policy and lifecycle parity

Estimate: **1–2 engineer-days / 6–12 hours**.

- [ ] Run equivalent manual CLI, automated and MCP requests against the same recording API/host fakes; compare authorized calls, semantic outcomes and sanitized audit/correlation rather than transport formatting alone.
- [ ] Cover unknown tools, extra/invalid arguments, generic commands, selected executable/host/path, profile override, scope/relationship mismatch, timeout/cancellation, output truncation and unavailable capabilities.
- [ ] Inject intent/outcome-audit failure, storage failure, secret canaries and hostile prompts/resources/output; denied execution and withheld payload behavior must match local semantics.
- [ ] Test one-hour session/24-hour plan defaults, current approval/policy invalidation, name-lookup authorization and in-flight result withholding across relevant paths. Session approval cannot reuse an investigation’s expired authority or expand targets.

Done when:

- [ ] Public contract tests demonstrate that transport/client changes do not change authorization, result semantics, data minimization or audit failure behavior.

### Step 4 - Validate real Pi interoperability and operator guidance

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Obtain separate authorization for the actual Pi standalone version/provider/client environment, session scope, outbound categories and egress profile. Validate before connection, not after receiving evidence.
- [ ] Exercise real tools/resources/prompts interoperability over local/stdio transport, including enabled discovery, permitted reads, denied requests, curated citations and diagnostic prompts.
- [ ] Verify independently observed context binding, egress allow/deny and teardown on normal disconnect, expiry, revocation and runtime shutdown; record failures honestly and disable unsafe sessions.
- [ ] Demonstrate inference-only Pi remains tool/MCP-disabled inside Go-owned investigations while standalone approved Pi uses the separate controlled client path.
- [ ] Document session creation/revocation, supported versions, shared registry/policy, unavailable capabilities, client-copy/export responsibilities and the fact that previously received data cannot be recalled.
- [ ] Record real interoperability separately from fake protocol tests; absent safe environment/access blocks AC-019, not an excuse to claim completion from fixtures.

Done when:

- [ ] Authorized real standalone Pi passes tools/resources/prompts and enforced-egress/session checks, with an evidence record tied to tested runtime/client/policy versions.

## 07.6 Phase Definition of Done

- [ ] One Go executable provides local/stdio MCP over manually trusted capabilities and the shared safety boundary.
- [ ] Tools, approved resources and all four diagnostic prompt families have protocol and real Pi evidence.
- [ ] Every session has explicit CLI scope/egress/lifetime approval and independently verified client identity/context; all ending conditions revoke approval and egress.
- [ ] Entry-point parity includes audit/storage faults, secret canaries, revocation races and all result statuses.
- [ ] No network MCP, generic execution, session reuse or Go-inference harness bypass is introduced. Missing independent client/egress proof blocks enablement.

## 07.7 Risks

| Risk | Mitigation |
| --- | --- |
| Local stdio is assumed to authenticate any process | Bind approval to independently verified client security context and reject replay. |
| Client has permitted tool access but unrestricted outbound network | Independently enforce approved egress before evidence delivery and revoke it at end. |
| Disconnect ends logical session but leaves egress active | Treat teardown as a tested operation for disconnect/expiry/shutdown and expose failures. |
| Protocol adapter bypasses safe result handling | Shared dispatch plus cross-entry-point contract/fault tests. |
| Inference-only and standalone Pi roles become conflated | Distinct approvals/environments and explicit positive/negative role tests. |

## 07.8 Proposed Requirement Coverage and Handoff

| Requirement / AC source | Proposed phase responsibility | Existing behavior / deferral | Risk or unapproved decision |
| --- | --- | --- | --- |
| FR-035/047; AC-019/030 | Local MCP, bound one-hour sessions and real Pi tools/resources/prompts | Required Delivery 1 scope, not an optional extension | G1/G6 identity, independent egress and teardown validation. |
| FR-010–FR-011/023–FR-029; AC-004/012/014/015 | Full entry-point gateway/result/audit/privacy parity | Uses existing verified Go contracts, not legacy MCP scripts | No protocol-specific bypass. |
| FR-017–FR-019/032/045; AC-009/028 | Curated resources, safe prompts and disclosed client evidence | No arbitrary-file resources or runnable remediation | Data already delivered cannot be recalled. |
| FR-039–FR-041/046; AC-022/029 | Session events/bounds/readiness and shared manual contract | Final packaging/deployment acceptance in 08 | Required dependencies must fail closed. |

Proposed handoff to Phase 08: protocol/parity results, real Pi interoperability, session/context/egress lifecycle evidence and final enabled capability matrix. Independent scope readiness and a separate approved task contract are still required; this phase file is neither.
