## Architectural Design Specification: Phase 07 ChatGPT Device-Authentication Provider Boundary

**Status:** Revised design after the authenticated upstream-contract mismatch; implementation and provider traffic remain prohibited until the local chunks pass and a provider request receives separate explicit approval.

**Dependency order:** Accepted Codex runtime home and MCP lifecycle -> accepted loopback routing, redaction, gateway, evidence, and `assistant` egress controls -> this ChatGPT/device-auth revision Chunks 0-7 -> separately approved remote acceptance -> Phase 99.

**Supersedes:** The `api.openai.com/v1/responses` authentication and upstream portions of earlier revisions of this ADS. The accepted loopback, payload-redaction, MCP, service-identity, evidence-retention, and direct-`assistant`-egress boundaries remain in force unless this revision explicitly changes them.

**Source:** Phase 07 MCP integration; accepted local gateway/redaction/evidence work; `docs/ai-ops/runtime/phase07-remote-provider-decision-2026-07-14.md`; `docs/ai-ops/runtime/codex-custom-provider-profile-contract.md`; metadata-only provider classification `authentication`; and the reviewed official Codex `rust-v0.144.1` ChatGPT authentication contracts recorded in handoff 53.

**Goal:** Make the existing loopback redaction gateway compatible with the currently authenticated Codex ChatGPT/device-auth runtime by rebuilding requests for one fixed ChatGPT Codex backend endpoint and transiently forwarding only the reviewed authentication-routing headers, without retaining account or credential values or weakening any existing redaction, evidence, MCP, TLS, or egress boundary.

---

### I. Overview and Contract

The selected architecture remains an explicit application-layer gateway:

```text
Codex 0.144.1 as assistant
  -> temporary runtime override with loopback base_url ending in /v1
  -> POST /v1/responses on 127.0.0.1:8765
  -> validate, redact, leak-scan, and rebuild JSON
  -> validate the authentication-routing header set
  -> verified HTTPS POST to chatgpt.com:443/backend-api/codex/responses
  -> stream the bounded response to Codex
```

The current authenticated runtime uses the ChatGPT/device-auth family. It is not compatible with the API-key endpoint. This revision therefore chooses the preferred current-runtime contract:

- **Inbound gateway route:** fixed `POST /v1/responses`; unchanged so the validated Codex runtime override remains stable.
- **Upstream scheme:** fixed `https`.
- **Upstream host:** fixed `chatgpt.com`.
- **Upstream port:** fixed `443`.
- **Upstream route:** fixed `/backend-api/codex/responses`.
- **Provider selection:** the request cannot select or override scheme, host, port, path, proxy, DNS result, or transport.
- **Authentication mode:** exactly one non-empty `Authorization: Bearer <opaque-value>` header.
- **Account routing:** exactly one non-empty `ChatGPT-Account-ID` header.
- **FedRAMP routing:** unsupported in this slice. Any inbound `X-OpenAI-Fedramp` header is rejected, not ignored or forwarded. Support requires a separately reviewed branch and egress/evidence contract.
- **Agent identity:** unsupported in this slice. Any non-Bearer authorization scheme or agent-assertion path fails closed; parsing must not be broadened opportunistically.
- **Alternative API-key design:** deferred. An operator-managed API-key path retaining `api.openai.com/v1/responses` would require a separate authentication source, policy mode, egress contract, tests, and approval. The gateway must not infer the mode from credential shape or retry one endpoint after another.

#### Header Boundary

The inbound HTTP parser is case-insensitive for field names. Validation must operate on all values returned for each protected name, not on a comma-joined or first-value view.

The gateway may construct only these upstream headers:

| Header | Source | Contract |
| --- | --- | --- |
| `Accept` | gateway constant | Exactly `text/event-stream` |
| `Content-Type` | gateway constant | Exactly `application/json` |
| `Authorization` | inbound request | Exactly one valid Bearer value; transient memory only |
| `ChatGPT-Account-ID` | inbound request | Exactly one non-empty bounded value; transient memory only |

`Authorization` and `ChatGPT-Account-ID` values must reject empty values, leading or trailing whitespace ambiguity, control characters, CR/LF, duplicate field lines, and parser-produced multiple values. The implementation may define conservative byte bounds during Chunk 0 after confirming the official client’s emitted shape; absence of a reviewed bound blocks implementation rather than allowing an unbounded value.

Security-relevant singleton headers—`Authorization`, `ChatGPT-Account-ID`, `X-OpenAI-Fedramp`, `Content-Type`, `Content-Length`, `Content-Encoding`, `Transfer-Encoding`, and `Host`—must reject duplicate field lines. `Host`, content length, and connection metadata are rebuilt by the outbound HTTP client. Cookies, forwarding headers, proxy headers, inbound host, user-agent, tracing headers, and every unlisted field are not forwarded. Presence of `X-OpenAI-Fedramp` is an explicit local error even if only one value is present.

No authentication or account-routing value may enter a dataclass representation intended for evidence, logs, exception text, test failure text, process arguments, files, or Git. A short-lived upstream request object may hold the validated values only until the request is completed or aborted.

#### Payload and Response Boundary

The accepted payload path is unchanged:

```text
bounded body -> exact content/encoding checks -> strict JSON parse
-> reviewed model/input shape -> fail-closed redaction -> leak scan
-> new JSON serialization -> fixed upstream request
```

The raw body is never forwarded. Unsupported, malformed, duplicate-key, ambiguous-label, binary, multipart, compressed, image, audio, or file-upload content remains rejected. The model remains exactly `gpt-5.6-terra` until separately revised. A non-success response is classified from status only; response content is not inspected or retained.

#### DNS and Egress Contract

- `assistant` keeps its current deny-by-default public egress policy and reaches only the loopback gateway plus already reviewed management destinations. No ChatGPT exception is added for `assistant`.
- Only `aiops-provider` performs upstream transport. The gateway passes the literal fixed hostname `chatgpt.com` to the verified HTTPS client so certificate and SNI validation use that hostname.
- Name resolution uses only the host’s operator-managed system resolver. The application must not accept a resolver, IP address, URL, proxy, or Host override from the request or environment.
- The service remains restricted to `AF_INET` until an IPv6 path is separately designed and tested. Resolution with no approved IPv4 result fails closed; it must not trigger an IPv6 or alternate-host fallback.
- Network policy for `aiops-provider` may permit only resolver traffic required by the operator-managed host baseline and outbound TCP/443. Application-layer host fixation is mandatory because CDN address drift makes an unreviewed static destination list unsafe to claim as the sole host control.
- Chunk 0 must confirm whether proxy environment variables can influence the current standard-library transport. The deployed service must clear or reject proxy variables and must use a transport that does not honor caller- or environment-selected proxies.
- DNS failure, address-family drift, certificate mismatch, SNI mismatch, redirect, or connection to any caller-selected destination fails closed. HTTP redirects are never followed.

#### Evidence and Migration Contract

The existing metadata-only ledger remains append-only, `aiops-provider` owned, mode `0600`, and bounded to 64 KiB. It must never contain account data, authentication data, header names or values, DNS answers, provider URLs, request/response bodies, prompts, or raw exception text.

Route semantics change and therefore require an evidence schema revision:

| Evidence schema | `route` meaning | Allowed value |
| --- | --- | --- |
| `1` | Historical fixed API-key-oriented upstream attempted by the prior gateway | `/v1/responses` |
| `2` | Fixed ChatGPT/device-auth upstream selected by this revision | `/backend-api/codex/responses` |

Schema 2 keeps the existing field allowlist. It changes only the schema value and route semantics; it does not add an auth mode, account identifier, hostname, or header metadata field. New gateway code writes schema 2 only. Existing schema 1 records are never rewritten, deleted, relabeled, or treated as ChatGPT attempts.

A mixed schema 1/schema 2 ledger is valid when each record satisfies its own schema/route pair and the existing retention bound. The metadata retrieval parser must validate both known pairs and reject unknown versions or pairings. Rollback stops remote mode before restoring old code; it preserves the mixed ledger in place and does not resume schema 1 provider traffic. Ledger deletion, truncation, rotation, or migration requires separate operator approval.

### II. Observed Evidence and Assumptions

#### Observed Evidence

- `aiops_provider_gateway.py` fixes the current upstream to `api.openai.com:443/v1/responses` and accepts only one Bearer authorization value.
- `gateway_policy.json` repeats that fixed API-key-oriented endpoint.
- The current upstream request allowlist is `Accept`, `Content-Type`, and `Authorization`; it does not forward `ChatGPT-Account-ID`.
- Gateway tests prove strict loopback routing, request bounds, redaction, rebuilt JSON, fixed upstream forwarding, SSE bounds, and status-only provider error classification.
- The current evidence event is schema 1 and hard-codes `/v1/responses`; the runbook excludes headers, account data, provider URLs, and raw ledger lines.
- The gateway service runs as `aiops-provider`, permits only `AF_INET`, and writes only its state directory. `assistant` direct public egress remains denied by UID-owner UFW rules.
- Local no-forward acceptance proved exactly one Responses POST reached the redaction boundary and no prohibited marker reached a fake sink.
- The deployed redaction fix passed focused tests and the real provider attempt reached verified TLS, then produced metadata-only HTTP `4xx` category `authentication`.
- Reviewed official Codex `rust-v0.144.1` source uses `https://chatgpt.com/backend-api/codex`, appends `/responses`, and sends `Authorization` plus `ChatGPT-Account-ID` for ChatGPT sessions. It may send `X-OpenAI-Fedramp` for applicable accounts.

#### Assumptions and Open Confirmations for Chunk 0

- The active authenticated runtime emits exactly one Bearer authorization field and exactly one account-routing field on the loopback request.
- The selected account does not require FedRAMP routing or an agent-assertion authorization path.
- The standard-library HTTPS client performs verified SNI/certificate validation for `chatgpt.com`, does not follow redirects, and does not use proxy environment variables in the current call path.
- The selected model is accepted by the ChatGPT backend. This remains unproven and must not be tested remotely until all local gates pass.
- Conservative size bounds for the two transient header values can be selected from official-source constants or synthetic emitted-shape evidence without reading either real value.

If any assumption cannot be confirmed without inspecting credential/account values, stop and request a new design decision.

### III. Required Technical Dependencies and Imports

- Existing Python standard-library gateway, strict JSON parser, redactor, leak scanner, HTTPS client, and injected fake-upstream test seams.
- Existing `ai_client_runtime` deployment role, systemd service, gateway policy, evidence ledger, and focused unit tests.
- Existing `assistant_egress` and validation roles; these remain unchanged unless Chunk 6 proves a separate `aiops-provider` egress change is required.
- Existing runtime documents:
  - `docs/ai-ops/runtime/codex-custom-provider-profile-contract.md`
  - `docs/ai-ops/runtime/provider-gateway-metadata-evidence.md`
  - `docs/ai-ops/runtime/phase07-remote-provider-decision-2026-07-14.md`
- No provider SDK, generic proxy, credential store, telemetry library, TLS interception, browser automation, OpenStack dependency, or new network-facing listener is approved.

**Function Signature Contract (Conceptual):**

```text
validate_chatgpt_auth_headers(all_inbound_header_values)
  -> transient validated Authorization and ChatGPT-Account-ID values
build_upstream_request(redaction_result, fixed_policy, validated_auth_headers)
  -> fixed ChatGPT UpstreamRequest
serialize_gateway_evidence_event(event)
  -> schema-specific metadata bytes
```

The exact Python names and temporary value types must be confirmed in Chunk 0. A stub must fail with a bounded local error; it must never return synthetic success or permit forwarding before both required headers validate.

### IV. Step-by-Step Procedure / Execution Flow

1. Codex runs as `assistant` in the fixed runtime home and uses the accepted ephemeral runtime overrides.
2. Codex discovers the local reviewed model and sends exactly one `POST /v1/responses` to loopback.
3. The gateway validates route, singleton transport headers, content type/encoding, and body bounds.
4. It strictly parses JSON, validates model/input shape, redacts, leak-scans, and serializes a new body.
5. It rejects FedRAMP, non-Bearer, duplicate, missing, malformed, or unbounded authentication-routing headers before evidence or network I/O.
6. It constructs a request containing only the four reviewed outbound headers and fixed ChatGPT endpoint.
7. It appends a schema 2 `forward_started` event without any auth/account/DNS data. Failure prevents network I/O.
8. The verified HTTPS client resolves and connects to `chatgpt.com`, validates SNI/certificate, sends one POST, follows no redirect, and performs no retry.
9. The gateway appends one schema 2 terminal metadata event and streams only a valid bounded SSE success response. Non-success bodies are discarded unread where practical and never retained.
10. The gateway clears transient references after completion or failure and returns a bounded local result.
11. Remote mode remains disabled after local testing. A real request requires fresh explicit approval and all deployment, egress, ledger, and fake-upstream gates to pass immediately beforehand.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| --- | --- | --- | --- |
| Local route | Method/path differs or a second Responses POST occurs | Reject; no upstream request | `ERR_GATEWAY_ROUTE` |
| Header framing | Duplicate protected singleton header | Reject before body forwarding | `ERR_GATEWAY_HEADER_AMBIGUITY` (proposed) |
| Authorization | Missing, empty, malformed, non-Bearer, or multiple values | Reject without retaining value | `ERR_CHATGPT_AUTH` (proposed) |
| Account routing | Missing, empty, malformed, unbounded, or multiple account IDs | Reject without retaining value | `ERR_CHATGPT_ACCOUNT_ROUTE` (proposed) |
| FedRAMP | `X-OpenAI-Fedramp` is present | Reject; require separate design | `ERR_CHATGPT_FEDRAMP_UNSUPPORTED` (proposed) |
| Payload | JSON/schema/redaction/leak-scan gate fails | Preserve existing fail-closed behavior | Existing bounded gateway error |
| Upstream policy | Any caller/environment attempts host, route, proxy, resolver, or transport selection | Reject or clear influence; no network I/O | `ERR_GATEWAY_UPSTREAM_POLICY` |
| DNS | Resolution fails, yields no usable IPv4 result, or drifts family | Do not fall back to another host/family | `ERR_CHATGPT_DNS` (proposed) |
| TLS | Certificate/SNI verification fails | Never disable verification | `ERR_OPENAI_TLS` |
| Redirect | Upstream returns redirect | Do not follow it; record status class only | `ERR_CHATGPT_REDIRECT` (proposed) |
| Provider | Non-success status | Discard body; append status class only | Existing bounded provider failure |
| Evidence | Schema/route pair invalid or append fails | Do not forward, or return sanitized terminal failure | `ERR_GATEWAY_EVIDENCE` |
| Migration | Unknown or mismatched historical evidence record | Stop metadata review; preserve ledger | `ERR_GATEWAY_EVIDENCE_POLICY` |
| Cleanup | Temporary value appears in logs, files, errors, or tests | Disable remote mode and treat as security failure | `ERR_CHATGPT_AUTH_RETENTION` (proposed) |

No failure may fall back to `api.openai.com`, omit account routing, add FedRAMP routing, switch authorization schemes, follow redirects, retry automatically, or permit direct `assistant` egress.

### VI. Security, Integrity, Idempotency, and Cleanup

- **Security:** Authentication and account values are opaque transient secrets/account data. Validate shape only; never inspect meaning, print, persist, compare against fixtures, or include them in errors/evidence.
- **Integrity:** Endpoint constants must agree between Python policy validation, deployed JSON policy, tests, evidence schema, and runbook. Any mismatch prevents service start or forwarding.
- **Header integrity:** Build a new header mapping from the four-field allowlist. Do not mutate or copy the inbound header mapping.
- **Redaction integrity:** Header changes occur only after the existing payload redaction and leak scan. They do not weaken unsupported-content or ambiguity rejection.
- **Network integrity:** Keep loopback listener scope and `assistant` deny rules. Do not grant public ChatGPT access to `assistant` for testing.
- **Idempotency:** No automatic request or stream retries. Each accepted turn has one new correlation UUID and at most one started/terminal pair.
- **Cleanup:** Unconditionally remove temporary workspaces, listeners, fake sinks, runtime overrides, and controller-local metadata. Preserve operator authentication state and the production ledger.
- **Rollback:** Disable runtime selection, stop the gateway if needed, restore the prior package only for local rollback, retain mixed ledger records, and do not resume the known-incompatible API endpoint.

### VII. Validation Strategy

All validation before deployment uses synthetic values and injected/local fake upstreams only.

- **Syntax:** `rtk python3 -m py_compile ansible/ai_ops_runtime/roles/ai_client_runtime/files/provider_gateway/aiops_provider_gateway.py`
- **Focused tests:** `rtk python3 -m unittest tests.ai_ops.test_provider_gateway tests.ai_ops.test_provider_redaction`
- **Policy syntax:** `rtk python3 -m json.tool ansible/ai_ops_runtime/roles/ai_client_runtime/files/provider_gateway/gateway_policy.json >/dev/null`
- **Ansible syntax:** `rtk ansible-playbook --syntax-check -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_setup_ai_client_runtime.yml`
- **Diff checks:** `rtk git diff --check` and scoped `rtk git diff -- <changed-files>`.

Targeted tests must prove:

- one Bearer plus one account ID produces exactly four upstream headers;
- missing, duplicate, empty, whitespace-ambiguous, CR/LF, oversized, non-Bearer, and FedRAMP cases perform zero upstream submissions and zero started-event writes;
- no unlisted inbound header reaches the fake upstream;
- fixed host/port/route and verified HTTPS are used; no redirect or retry occurs;
- schema 1 and schema 2 evidence records remain distinguishable, while invalid pairings fail;
- serialized evidence and all captured logs/errors exclude synthetic auth/account markers;
- existing redaction, request-bound, model, SSE, status-classification, and ledger-retention tests still pass;
- an actual local Codex invocation reaches a local fake sink exactly once at the expected upstream route after gateway rebuilding;
- listener scope, service identity, ledger modes, direct `assistant` egress denial, and required management access remain intact.

No deployment or provider request is permitted on unit-test failure. No real provider request is permitted merely because local tests pass.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass.

#### Chunk 0: Discovery and Integration Confirmation

- **Goal:** Confirm exact official-source header emission, conservative header bounds, current proxy/DNS behavior, test seams, and all policy/evidence call sites without inspecting real values.
- **Files to read:** gateway source/policy/tests, service template, egress roles, evidence runbook, runtime override contract, and reviewed official-source references if a fresh temporary checkout is explicitly approved.
- **Commands:** targeted symbol searches and local synthetic inspection only; no provider request.
- **Evidence to confirm:** Bearer-only current runtime, exactly-one account header expectation, no FedRAMP requirement, no environment-proxy use, and all schema 1 route dependencies.
- **Stop condition:** Stop with no edits if agent assertion, FedRAMP, unbounded headers, proxy influence, or credential inspection would be required.

#### Chunk 1: Transient Header Validation Contract

- **Goal:** Add and test a fail-closed helper for exactly one Bearer value, exactly one account ID, duplicate protected headers, and default FedRAMP rejection without changing forwarding.
- **Files to change:** `aiops_provider_gateway.py`, `test_provider_gateway.py`.
- **Symbols to add/change:** conceptual `validate_chatgpt_auth_headers` and a transient immutable value type.
- **Implementation shape:** The helper returns validated opaque values; all failures return bounded errors. No call site changes and no endpoint change.
- **Validation:** Python compile plus focused helper and no-retention tests.
- **Stop condition:** The new helper is unused by production forwarding and every invalid shape fails without exposing values.

#### Chunk 2: Fixed ChatGPT Upstream Policy

- **Goal:** Atomically replace the fixed API endpoint contract with the fixed ChatGPT endpoint while keeping production forwarding disabled until Chunk 3 wiring.
- **Files to change:** gateway source, `gateway_policy.json`, and focused gateway tests. Three files are justified because code, deployed policy, and executable contract must remain consistent in one compile-safe slice.
- **Symbols to add/change:** fixed host/port/route constants and policy assertions.
- **Implementation shape:** Update constants and request-builder tests; retain the old handler auth call until the next chunk only if a deliberate local fail-closed gate prevents service forwarding. Otherwise combine this chunk with Chunk 3 rather than leave a deployable mismatch.
- **Validation:** Compile, JSON syntax, focused policy/build tests, and no-network gateway tests.
- **Stop condition:** No code path can send a request to either endpoint with an incomplete header contract.

#### Chunk 3: Header-to-Upstream Wiring

- **Goal:** Wire validated transient authentication-routing headers into the rebuilt ChatGPT request.
- **Files to change:** gateway source and focused tests.
- **Symbols to add/change:** `build_upstream_request`, `GatewayRequestHandler.do_POST`, and upstream request tests.
- **Implementation shape:** Extract all protected header values, validate once, construct only the four allowlisted outbound fields, then clear references after request completion.
- **Validation:** Full header matrix, zero-submit assertions, fake HTTPS connection assertions, compile, and focused tests.
- **Stop condition:** Synthetic fake transport receives exactly one sanitized request with no unlisted header; no deployment.

#### Chunk 4: Evidence Schema 2 and Mixed-Ledger Compatibility

- **Goal:** Make the ChatGPT route unambiguous while preserving historical schema 1 records.
- **Files to change:** gateway source and focused tests.
- **Symbols to add/change:** evidence schema/route validation and mixed-record parser test seam.
- **Implementation shape:** New events use schema 2 plus ChatGPT route; known schema 1 remains historical/readable; unknown pairs reject. No header/account fields are added.
- **Validation:** Serialization, mixed-ledger, invalid-pair, retention, and no-sensitive-marker tests.
- **Stop condition:** Existing records need no rewrite and every new event is unambiguously ChatGPT schema 2.

#### Chunk 5: Runtime Evidence Contract and Runbook Migration

- **Goal:** Update operator retrieval, rollback, and status documentation for schema 2 and resolved redaction.
- **Files to change:** `provider-gateway-metadata-evidence.md` and `codex-custom-provider-profile-contract.md`.
- **Symbols to add/change:** documented schema/route pair validation and current acceptance gap.
- **Implementation shape:** Documentation/parser example only; never copy raw ledger data.
- **Validation:** Markdown diff review, command-prefix review, and `rtk git diff --check`.
- **Stop condition:** Operators can distinguish schema versions without viewing raw lines or account/header data.

#### Chunk 6: Deployment and Egress Validation

- **Goal:** Deploy the reviewed gateway under `aiops-provider` and prove DNS/TLS/egress boundaries without provider traffic.
- **Files to change:** only confirmed Ansible task/template/validation files; no `assistant` public-egress exception.
- **Symbols to add/change:** proxy-environment clearing/assertion and any separately justified `aiops-provider` resolver/TCP-443 enforcement checks.
- **Implementation shape:** Syntax first, local fake TLS or injected transport, service restart, listener/identity/ledger checks, direct-`assistant` denial recheck, rollback proof.
- **Validation:** Ansible syntax, first/second-run idempotency, service sandbox, loopback listener, IPv4-only DNS behavior, and egress materialization.
- **Stop condition:** Production gateway is locally ready but remote mode remains disabled and no provider request has occurred.

#### Chunk 7: Codex Local Fake-Upstream Acceptance

- **Goal:** Prove the actual authenticated runtime sends the required headers to loopback and the gateway rebuilds exactly one ChatGPT-path request to a local fake upstream.
- **Files to change:** none; temporary runtime artifacts only.
- **Implementation shape:** Ephemeral runtime overrides, assistant-owned temporary Git workspace, non-production gateway port, fake upstream, `evidence_writer=None`, retries disabled, unconditional cleanup.
- **Validation:** Exactly reviewed model-discovery calls and one Responses POST; required header presence/count only, never values; expected rebuilt path; no public connection; no retained bodies/configuration.
- **Stop condition:** Pass all local gates and write a sanitized handoff, or disable the path and report the blocker. Do not proceed to a real request.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Execute Chunk 0 only of the Phase 07 ChatGPT Device-Authentication Provider Boundary ADS.

Mode:
Do not edit files, inspect authentication/account values, alter egress, deploy, or contact a provider. Confirm official-source header shape, conservative bounds, proxy/DNS behavior, exact code/test/evidence integration points, and whether the active account requires FedRAMP or agent assertion using value-free evidence only. Stop on uncertainty.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Execute Chunk 1 only.
Do not continue to Chunk 2. Add only the transient header validation contract and focused synthetic tests. Do not change the endpoint, wire forwarding, deploy, or make network requests. Run targeted validation and show the scoped diff.
```

### X. Conclusion and Next Steps

The previous gateway successfully proved routing, redaction, rebuilt-request forwarding, verified TLS, and metadata-only classification, but its API-key-oriented endpoint cannot consume the authenticated Codex ChatGPT/device-auth contract. The approved design direction is now one fixed ChatGPT Codex backend with exactly one transient Bearer authorization field and one transient account-routing field. FedRAMP and agent assertion fail closed, and the API-key endpoint is not a fallback.

The next implementation action is Chunk 0 only. No gateway code, egress policy, authentication state, deployment, or provider traffic may change until that discovery confirms the value-free contract and produces a handoff.