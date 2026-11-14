# 02. Inference Isolation and Manual Analysis

**Phase boundary:** PROPOSED.
**Authority:** Roadmap phase, not an approved implementation task contract.
**Source requirements:** [PRD](../prd.md), Diagnostic implementation form; Model boundary and interoperability; Retained toolbox and manual-operation requirements; Testing Decisions 9, 14–15. FR-007, FR-018–FR-019, FR-029–FR-034, FR-039–FR-040, FR-043, FR-045–FR-046; NFR-001–NFR-003, NFR-006, NFR-008–NFR-009, NFR-012–NFR-015; AC-015–AC-018, AC-022, AC-028–AC-030.
**Decision gaps:** G1 independent harness/credential isolation and egress; G2 approved installed versions/provider-model combinations; G5 release thresholds before model-enabled rollout. External harness prerequisites are settled product scope; their concrete supported matrix is not.

## 02.1 Goal

Make both harnesses safe, bounded inference adapters and deliver the first manual copy-paste analysis workflow before any automatic tool selection.

```text
named manual Go diagnostic -> sanitized output pasted into Go analysis mode
  -> disclosed/approved outbound categories -> isolated tested Codex or Pi
  -> evidence-qualified explanation, with zero automatic diagnostic calls
```

## 02.2 Estimate

```text
7–11 engineer-days
42–66 focused hours
```

## 02.3 Scope

Included:

- Common text/structured contracts for operator-installed Codex and Pi, tested version/provider/model allowlisting and finite limits.
- Independently enforced model isolation, destination/data-class consent, minimization/aliasing and egress checks.
- Inference-only manual analysis, provider failure/revocation behavior and model usage events.
- Deterministic adapter tests; separately authorized real checks may be performed when prerequisites and gates permit, with final evidence integration in Phase 08.

Excluded:

- Model-owned tool/MCP access, automatic diagnostic dispatch, provider fallback, runtime harness installation/authentication/update and direct remote-model API harness development.
- Standalone Pi MCP-client sessions, which have separate security/egress approval in Phase 07.

## 02.4 Assumptions

- [ ] Phase 01’s shared gateway, sanitization, protected persistence and manual path have verified evidence.
- [ ] Operator-managed Codex/Pi installations and provider authentication are available under approved isolated identities; the application will not bootstrap them.
- [ ] G1 can constrain subprocesses, files, credentials, network routes and inherited state independently of CLI flags or environment filtering.
- [ ] Real inference tests are explicitly authorized; unavailable access is recorded as a blocker to model enablement, not permission to skip required acceptance.

## 02.5 Ordered Tasks

### Step 1 - Normalize the two inference adapter contracts

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Adapt existing Go clients to a common bounded text/structured response contract with cancellation, sanitized errors, version/provider/model identity and usage availability.
- [ ] Require an operator-approved tested exact harness/provider/model combination. Reject unknown, missing, changed or unvalidated combinations without disabling independent manual diagnostics.
- [ ] Validate structured responses structurally; bound repair attempts, output/context bytes, elapsed time and available token/cost budgets. Semantic control-flow validation remains application-owned in Phase 03.
- [ ] Disable native tools and direct MCP in Go-owned inference sessions; reject unexpected tool/execution events rather than treating them as valid text completion.
- [ ] Keep configured harness locations operator-controlled and integrity-checked as required by the approved design; never accept model/client-selected executable paths or silently switch providers.

Done when:

- [ ] Deterministic process/adapter fixtures cover both backends, malformed streams, invalid structured output, timeout/cancellation, unknown versions and explicit unknown usage.

### Step 2 - Enforce isolation, disclosure and destination controls

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Implement the separately approved non-root process/identity/IPC boundary and independently verify that model-facing components cannot read cloud/SSH credentials, protected raw state, unrelated files or invoke bypass diagnostic tools.
- [ ] Keep provider authentication opaque to diagnostics, reports and telemetry. Verify process environment, descendants, filesystem access and permitted routes, not just adapter configuration.
- [ ] Require reusable explicit approval for identifiable provider/model destination and allowed outbound data classes. Show goals, observations, summaries, memories and knowledge categories before the first model call of each analysis/investigation.
- [ ] Sanitize/minimize all submitted data and consistently alias lab identifiers where practical; block credentials, full configurations and content that cannot be transformed safely before persistence or outbound use.
- [ ] Recheck disclosure policy and enforced egress before every request. Destination or data-class changes require renewed approval; missing isolation or egress proof blocks model-enabled work.
- [ ] On policy revocation, stop new requests, attempt in-flight cancellation, ignore late responses and explain that already transmitted data cannot be recalled.

Done when:

- [ ] Canary/bypass/changed-destination/revocation-race tests demonstrate independent isolation and no unauthorized provider calls, data classes or diagnostic credential access.

### Step 3 - Add protected manual analysis without tools

Estimate: **2–3 engineer-days / 12–18 hours**.

- [ ] Provide Go CLI analysis input for pasted diagnostic output, with size bounds and sanitization before any persistence/model context. Treat pasted text and user goals as untrusted data.
- [ ] Apply diagnostic-only instructions and produce facts, hypotheses, limitations and plain-language manual recommendations. Cite an explicitly approved sanitized runbook when recommending remediation; do not emit runnable mutation commands.
- [ ] Ensure analysis neither creates/approves an investigation plan nor dispatches tools, including when pasted content or the operator says “fix it”, names a tool or attempts prompt injection.
- [ ] Explain unsupported or unsafe inputs and unavailable knowledge without inventing evidence. Distinguish user-pasted claims from fresh gateway-collected observations.
- [ ] Document manual tool selection → execution → sanitized paste → disclosure → approved harness analysis, including the limits of protection for independent sharing outside the product.

Done when:

- [ ] Recording gateway fixtures show zero tool calls from the entire analysis path, while approved sanitized evidence can be analyzed through either backend.

### Step 4 - Prove degraded operation and capture model evidence

Estimate: **1–2 engineer-days / 6–12 hours**.

- [ ] Emit correlated model-purpose, adapter/provider/model, disclosure-policy, retry, latency and available token/cost events without prompts containing secrets or hidden reasoning traces.
- [ ] Record unknown/unavailable usage and conservative limits instead of zero-cost fiction. Keep cost estimates tied to an identified pricing basis when available.
- [ ] Test absent consent, outage, cancellation, revoked access and invalid versions while preserving permitted manual diagnostics, local inspection and existing reports.
- [ ] Verify both integrations in a controlled environment with only the required external harnesses/runtime dependencies, not diagnostic scripts/utilities. Record authorized real-model checks separately or carry explicit outstanding evidence to Phase 08.
- [ ] Extend offline regression coverage and the capability matrix with actual tested combinations. Do not represent exploratory provider checks as approved rollout or as the required live-lab investigation.

Done when:

- [ ] Model-dependent work fails closed, manual/local paths remain usable when their own safety prerequisites are healthy, and evidence clearly distinguishes deterministic tests from authorized real inference.

## 02.6 Phase Definition of Done

- [ ] Both adapters satisfy deterministic bounded inference-only contracts and independent isolation checks.
- [ ] Destination/data policy, pre-call disclosure, aliasing and egress controls operate independently and fail closed.
- [ ] Manual Go analysis works without automatic calls or MCP, with honest evidence classifications and manual-only recommendations.
- [ ] Outage/revocation tests preserve safe local/manual access and reject late responses without provider switching.
- [ ] Unknown versions and unproved isolation block model enablement. Required real-model and release-threshold evidence is either recorded under authorization or explicitly blocks later acceptance.

## 02.7 Risks

| Risk | Mitigation |
| --- | --- |
| CLI inference mode still exposes native execution features | Disable features and independently deny bypass by OS/security context; negative tests are required. |
| Only Pi has explicit outbound controls in current wiring | Use one common policy contract for both; no implicit Codex-account default approval. |
| Manual pasted output is considered inherently safe | Sanitize and minimize at analysis ingress; separate source provenance from trusted fresh observations. |
| Revocation races accept an already returned response | Recheck policy before consuming completion; test in-flight changes and disclose irreversibility. |
| Supported versions drift under operator updates | Explicit approved matrix; unvalidated drift fails closed rather than auto-upgrading. |

## 02.8 Proposed Requirement Coverage and Handoff

| Requirement / AC source | Proposed phase responsibility | Existing behavior / deferral | Risk or unapproved decision |
| --- | --- | --- | --- |
| FR-007/031; AC-016 | Common validated contracts for both harnesses | Existing clients are reuse candidates; real checks integrated in 08 | G2 tested version/provider matrix. |
| FR-029/032–FR-033; AC-015/017/030 | Isolation, minimized disclosure and independent egress | Flags/environment filtering alone are insufficient | G1; provider auth and diagnostic credentials separated. |
| FR-034; AC-018 | Safe outage/revocation and provider-independent operation | Full persisted investigation behavior in 03/04 | No fallback provider or recalled-data claims. |
| FR-019/045–FR-046; AC-028 | First protected manual analysis workflow | Automatic approved workflow in 03; standalone MCP in 07 | Plain-language recommendations, no automatic dispatch. |
| FR-039–FR-040; AC-022/029 | Honest usage, finite adapters and packaging evidence | Final acceptance and thresholds in 08 | G5; no release performance claim yet. |

Proposed handoff to Phase 03: reviewed inference contract, tested matrix, isolation/disclosure evidence and a working manual-analysis path. Independent scope readiness and a separate approved task contract are still required; this phase file is neither.
