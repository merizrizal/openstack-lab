# Phase 07 Remote Provider: Decision, Recovery, and Alternatives

**Date:** 2026-07-14  
**Status:** Decision required; remote-provider acceptance is blocked  
**Scope:** Phase 07 remote-model integration only. This document does not change the accepted read-only tool, runner, or local-MCP safety boundaries.

## 1. Executive Summary

Phase 07 has exceeded the original estimate because the work expanded from local stdio MCP integration into a separate remote-provider security and compatibility program.

The core AI-OPS diagnostic boundary is substantially further along than the remote-provider acceptance path:

- The approved tool runner, read-only tools, local MCP adapter, curated resources, prompts, and lifecycle boundaries have local evidence.
- The provider gateway, metadata-only evidence ledger, loopback listener, and `assistant` direct-egress controls have been deployed and locally validated.
- Remote provider acceptance is **not** complete. The active authenticated Codex runtime did not route the bounded synthetic invocation through the reviewed loopback gateway. No gateway evidence event was created, so no provider transmission is evidenced.

The immediate obstacle is not redaction or firewall materialization. A temporary, non-secret Codex profile successfully routed a local synthetic request to a loopback fake Responses API provider when invoked from a Git workspace. The operator-managed authenticated runtime profile did not select that route during the approved real synthetic attempt.

**Recommended decision:** pause further real-provider attempts. Run one bounded, local-only profile-selection recovery slice first. It must prove that the actual authenticated runtime selects the reviewed custom provider by reaching a fake loopback provider from a Git workspace. Only then should manual-auth compatibility and one separately approved real synthetic request be repeated.

## 2. What Changed From the Original Phase 07 Estimate

`docs/ai-ops/implementation-plan/07-mcp-integration.md` estimated Phase 07 at **18–30 focused hours (3–5 engineer-days)**. Its stated scope was a local, stdio-first MCP interface over the existing trusted runner.

The work now includes additional concerns specified by the revised provider and metadata-evidence ADSs:

1. Determining whether Codex exposes a complete final provider-request redaction hook.
2. Replacing the unavailable client-native hook with a custom-provider, loopback gateway architecture.
3. Implementing payload validation, redaction, leak scanning, fixed upstream routing, and streamed-response behavior.
4. Deploying a separate gateway identity with a constrained systemd sandbox and evidence path.
5. Enforcing and proving `assistant` direct-provider-egress denial while preserving required management access.
6. Supporting operator-owned manual authentication without inspecting, storing, or logging credentials.
7. Creating bounded metadata-only evidence and performing a single remote acceptance request.

These are distinct security, integration, and operational-validation workstreams. They were not represented as a small extension of MCP tool exposure in the original estimate.

## 3. Evidence-Based Current State

| Area | State | Evidence / implication |
| --- | --- | --- |
| Read-only AI-OPS tools and runner | Accepted local foundation | The PRD and prior runtime evidence define a deny-by-default diagnostic boundary. |
| Local MCP | Accepted local/stdin-stdout direction | The Phase 07 plan and runtime evidence retain MCP as local stdio, not a network service. |
| Provider gateway deployment | Deployed and locally validated | The gateway is active, loopback-only, and uses a dedicated `aiops-provider` identity. |
| Evidence ledger | Deployed and permission-validated | Ledger directory and file use the reviewed `0700`/`0600` modes; retrieval is metadata-only. |
| Assistant egress controls | Materialization checks passing | IPv4/IPv6 UFW traversal and owner-rule materialization were rechecked before and after acceptance attempts. |
| Custom-provider mechanics | Locally proven with a fake provider | A temporary assistant-owned Git workspace plus explicit non-secret profile generated one `POST /v1/responses` request for `gpt-5.6-terra` to a loopback fake provider. |
| Authenticated runtime routing | Blocked | The real synthetic invocation exited nonzero and generated no gateway ledger event, including after use of a temporary Git workspace. |
| Real provider acceptance | Not accepted | No metadata proves that a request reached the gateway or a provider. No retry should occur without resolving profile selection. |

### Important interpretation

An empty metadata ledger after the real attempt proves only that the gateway did not receive the request. It does **not** prove why the Codex invocation failed. Possible causes include active-profile selection, client configuration compatibility, model selection, authentication state, or another client-side preflight condition. This distinction matters because credentials and operator-managed configuration were intentionally not inspected.

## 4. Why the Spillover Happened

### 4.1 The original client assumption failed

The revised provider-boundary ADS records that Codex does not provide a verified client-native hook for rewriting the complete final provider payload. That invalidated the simplest redaction design and required a new explicit application-layer gateway.

### 4.2 Security requirements created coupled acceptance gates

The remote path must simultaneously prove:

- final request routing through the loopback gateway;
- complete-request redaction before upstream forwarding;
- fixed upstream, TLS verification, and no caller-selected URL;
- direct-provider-egress denial for `assistant`;
- non-interactive service separation for `aiops-provider`;
- manual authentication without credential capture; and
- metadata-only evidence without raw request or response retention.

A failure in any gate prevents a safe remote retry. This is intentional fail-closed behavior, but it increases elapsed engineering time.

### 4.3 The critical integration state is operator-managed

The authenticated Codex profile is intentionally outside repository automation so that credentials and client configuration are not captured. That safety choice removes an easy automation seam for confirming which provider profile is active. The team must therefore use local fake-provider tests and operator attestations rather than inspecting configuration or retrying against the real provider.

### 4.4 Client execution has hidden prerequisites

The temporary fake-provider proof showed that Codex required a Git workspace before it would initiate provider routing. The first remote attempt did not meet this prerequisite. A later attempt used a temporary Git workspace but still did not reach the gateway, proving that workspace preparation alone is insufficient.

## 5. Obstacles and Challenges

| Obstacle | Why it matters | Safe resolution |
| --- | --- | --- |
| Active authenticated profile does not select the gateway | No remote request reaches the redaction/evidence boundary. | Prove the actual runtime profile against a local fake provider before any real request. |
| Credentials and configuration cannot be inspected | Normal debugging by reading client config or tokens is prohibited. | Use operator-owned configuration steps, non-secret profile identifiers, exit-category metadata, and fake-sink hit metadata only. |
| Each real request is a sensitive acceptance event | Blind retries could submit unexpected content or bypass evidence. | Treat every real attempt as separately approved; diagnose only with loopback fake providers until routing is deterministic. |
| Client version/configuration behavior can drift | A documented profile shape may be unsupported or not selected by the installed client version. | Pin the observed client version, verify the profile with a fake provider, and record only route/method/model/count metadata. |
| Gateway acceptance depends on several independent controls | A working client route alone is insufficient. | Keep preflight order: listener -> egress materialization -> profile/fake-provider route -> manual auth -> one remote request -> metadata review. |
| Original estimate mixed product phases | The timebox did not isolate remote-provider compatibility from local MCP integration. | Split the roadmap and track the remote-provider boundary as a separately estimated capability. |

## 6. Recovery Plan for the Current Architecture

The current architecture remains technically viable. The local fake-provider proof demonstrates that Codex `0.144.1` can issue the reviewed Responses API request when given an explicit temporary profile and a Git workspace.

### 6.1 Recovery slice: deterministic authenticated-profile routing

**Goal:** prove that the operator-owned authenticated runtime selects the reviewed custom provider without contacting a real provider.

1. Create a temporary assistant-owned Git workspace and loopback fake Responses API sink.
2. Ask the operator to select the reviewed custom-provider profile explicitly for that invocation. Do not ask for, print, copy, or inspect configuration or credentials.
3. Use the fixed model identifier and disable retries for the local test where the client supports it.
4. Capture only: fake-sink hit count, HTTP method, route, model, stream flag, presence/absence of an authorization header, and client exit category.
5. Require exactly one fake-sink request at `POST /v1/responses`; reject a second request, an unexpected route, or any direct public connection.
6. Remove the temporary profile, workspace, listener, and metadata after recording the sanitized result.

**Stop condition:** if the active authenticated runtime still cannot be proven to use the custom provider locally, keep remote mode disabled. Do not repeat the real acceptance request.

### 6.2 Manual-auth compatibility rerun

After the routing slice passes:

1. Recheck gateway service, listener scope, ledger mode, and egress materialization.
2. The operator confirms only non-sensitive authentication status in the fixed runtime context.
3. Confirm the gateway test path receives the reviewed header behavior without retaining any credential value.
4. Stop if authentication requires configuration changes that cannot be applied without exposing secrets or widening egress.

### 6.3 Final remote acceptance

Only after the preceding gates pass:

1. Obtain a new explicit approval for one request.
2. Run from the proven Git workspace and explicit authenticated custom-provider profile.
3. Submit one minimal synthetic prompt; suppress client and provider output.
4. Use the reviewed parser to inspect allowlisted gateway metadata only.
5. Recheck loopback listener, direct-egress denial, MCP stdio-only behavior, and runner invariants.
6. Record a dated metadata-only evidence note only on success. On failure, disable the custom-provider selection and record a sanitized blocker.

## 7. Alternative Delivery Approaches

### Alternative A: Complete the current Codex custom-provider gateway design

**Description:** retain Codex as the agent client; route it through the existing loopback gateway; use the gateway for full-payload redaction and fixed upstream forwarding.

**Benefits**

- Preserves the existing Codex and local MCP investment.
- Keeps the complete provider request at one explicit redaction boundary.
- Reuses deployed gateway, egress, and evidence controls.
- Best fit if the operator wants an interactive Codex-driven agentic experience.

**Costs and risks**

- Depends on version-specific Codex custom-provider and profile-selection behavior.
- Manual authentication and profile selection remain operator-managed integration points.
- Remote acceptance cannot be accelerated safely with repeated live retries.

**Best next action:** execute the authenticated-profile fake-provider recovery slice in Section 6.1.

### Alternative B: Deliver the local AI-OPS assistant without remote-model automation

**Description:** declare the locally validated tool runner and stdio MCP interface as the current AI-OPS milestone. The operator uses an approved external AI interface manually and supplies only appropriately sanitized diagnostic context; no provider gateway or remote model request is part of the deployment acceptance.

**Benefits**

- Aligns directly with the PRD's staged evolution from manual diagnostics to a local tool-runner assistant and then MCP.
- Avoids provider authentication, external data egress, client custom-provider behavior, and gateway operational complexity.
- Delivers useful read-only diagnostic workflows sooner.

**Costs and risks**

- It is human-in-the-loop AI assistance, not a fully integrated autonomous/agentic model session on `assistant01`.
- The operator must follow a separate data-handling procedure when providing diagnostic context to an external model.
- It does not prove remote gateway redaction or model-driven MCP orchestration.

**Best use:** choose this if operational value from safe diagnostics is more urgent than integrated remote-agent capability.

### Alternative C: Build a purpose-built AI-OPS orchestrator client

**Description:** replace Codex as the remote-provider integration point with a small repository-owned client/orchestrator. It would own the model-provider API interaction, tool loop, allowlisted MCP/runner calls, and explicit redaction boundary.

**Benefits**

- The provider selection and request lifecycle become repository-owned and testable rather than hidden in a client profile.
- A typed configuration contract can make routing, retries, model selection, and evidence deterministic.
- The tool loop can be designed specifically around the existing read-only runner rather than general coding-agent behavior.

**Costs and risks**

- It is a new product component, not a small integration fix.
- It must solve secure operator authentication or a reviewed secret-management design; embedding credentials is unacceptable.
- It needs its own streaming, cancellation, prompt/context, audit, and usability design.

**Best use:** choose this if deterministic operational control is more important than reusing Codex's interactive agent experience.

### Alternative D: Use a local/self-hosted model with the existing MCP boundary

**Description:** run an approved local model runtime outside the OpenStack control plane and connect it to the existing stdio MCP/tool boundary, with no public provider request.

**Benefits**

- Removes external provider authentication and data-egress concerns.
- Keeps tool invocation local and easier to observe.
- Can support an agentic loop if local hardware and model quality are sufficient.

**Costs and risks**

- Requires a model-runtime, hardware-capacity, model-governance, patching, and performance decision.
- May not meet quality, latency, or resource constraints on the current lab infrastructure.
- Still needs strict prompt/tool/output handling; local inference does not remove AI-tool safety risks.

**Best use:** evaluate as a separate prototype if data residency or deterministic offline operation is a priority.

## 8. Comparative Decision Matrix

| Criterion | A. Codex gateway recovery | B. Local MCP/manual AI | C. Purpose-built orchestrator | D. Local model |
| --- | --- | --- | --- | --- |
| Reuses current implementation | High | High | Medium | Medium |
| Near-term delivery | Medium | High | Low | Low to medium |
| Fully integrated agentic experience | High if recovered | Low | High | High if model quality is sufficient |
| External data egress | Controlled external egress | Operator-managed outside runtime | Controlled external egress | None by design |
| Configuration determinism | Medium | High | High | High |
| New engineering scope | Low to medium | Low | High | High |
| Primary uncertainty | Codex profile/auth behavior | Operator workflow adoption | Authentication and client product scope | Capacity, quality, operations |

## 9. Estimated Completion Scenarios

These are **focused engineering-time ranges**, not promises. They exclude waiting for operator decisions, access, account behavior, vendor changes, or unrelated infrastructure incidents.

### Scenario 1: Recover the current Codex gateway design

| Work item | Focused estimate |
| --- | ---: |
| Local authenticated-profile fake-provider proof and sanitized runbook | 4–8 hours |
| Resolve supported profile-selection/configuration procedure with operator | 2–6 hours |
| Manual-auth compatibility rerun and metadata-only verification | 2–4 hours |
| One approved remote acceptance, evidence note, and final rechecks | 2–4 hours |
| Contingency for client-version/profile incompatibility | 8–16 hours |
| **Total** | **18–38 hours (roughly 3–6 focused engineer-days)** |

**Completion condition:** the active authenticated profile deterministically reaches the gateway; exactly one remote synthetic request produces only approved metadata; no direct assistant egress or unexpected listener is observed.

### Scenario 2: Deliver local MCP/manual AI assistance and defer remote integration

| Work item | Focused estimate |
| --- | ---: |
| Re-scope Phase 07 acceptance and document remote-provider deferral | 2–4 hours |
| Re-run/organize existing local MCP evidence and operator runbook | 2–6 hours |
| Review split/cleanup of existing Phase 07 changes | 2–6 hours |
| **Total** | **6–16 hours (roughly 1–2 focused engineer-days)** |

**Completion condition:** operators can use the approved local MCP/tool boundary safely, with remote model integration tracked as a separate milestone.

### Scenario 3: Purpose-built orchestrator

| Work item | Focused estimate |
| --- | ---: |
| Architecture, authentication, and threat-model decision | 1–3 days |
| Minimal typed client, redaction/gateway integration, and tests | 3–6 days |
| Deployment, evidence, and remote acceptance | 2–4 days |
| **Total** | **6–13 focused engineer-days** |

### Scenario 4: Local-model prototype

| Work item | Focused estimate |
| --- | ---: |
| Capacity/model/runtime discovery prototype | 2–5 days |
| MCP/tool-loop integration and safety validation | 3–6 days |
| Operational hardening and acceptance | 2–5 days |
| **Total** | **7–16 focused engineer-days** |

## 10. Recommended Decision Gates

1. **Product decision:** Is a fully integrated remote agent required for the next AI-OPS milestone, or is local MCP/manual AI assistance sufficient?
2. **If remote is required:** approve only the local authenticated-profile fake-provider recovery slice. Do not approve another real request yet.
3. **After a fake-provider pass:** decide whether to continue with the Codex gateway path or invest in a purpose-built client based on the observed profile-selection procedure.
4. **If the fake-provider slice remains blocked:** stop the Codex path, defer remote integration, and choose Alternative B, C, or D rather than widening egress or inspecting credentials.

## 11. Non-Negotiable Safety Constraints

Any selected approach must preserve:

- read-only, allowlisted diagnostic tools; no generic shell, SSH, OpenStack CLI, database, or remediation interface for AI use;
- local stdio MCP unless a separate remote-MCP design is approved;
- no provider credential, token, device code, raw client configuration, prompt, request body, response body, or raw ledger line in Git, Ansible inventory, logs, or evidence;
- loopback-only gateway listener and fixed upstream policy where a gateway is used;
- direct public-provider egress denial for the `assistant` identity outside a separately reviewed authentication procedure;
- explicit approval for each real-provider acceptance request; and
- fail-closed behavior when routing, redaction, evidence, TLS, authentication, or egress validation is uncertain.

## 12. Decision Requested

Choose one of the following:

1. **Recover current architecture:** approve the local authenticated-profile fake-provider recovery slice only.
2. **Deliver local AI-OPS first:** accept local MCP/manual AI assistance as the current milestone and defer remote-provider integration.
3. **Design a purpose-built orchestrator:** start a new architecture and implementation plan for a repository-owned model client.
4. **Prototype local inference:** run a capacity and model-quality prototype before committing to a local-model agent.

Until a decision is made, keep remote-provider mode disabled and do not retry the real request.
