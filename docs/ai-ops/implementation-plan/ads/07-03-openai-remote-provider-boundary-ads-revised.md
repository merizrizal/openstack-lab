## Architectural Design Specification: Phase 07 OpenAI Remote Provider via Reviewed Redaction Gateway

**Status:** Revised downstream architecture after the client-native redaction blocker.

**Dependency order:** Phase 07 MCP integration -> `07-01-codex-runtime-home-ads-revised.md` Chunks 0-5 -> `07-02-extended-mcp-client-lifecycle-ads-revised.md` Chunks 0-4 -> this ADS Revised Chunks 0-7 -> Phase 99.

**Supersedes:** `07-openai-remote-provider-boundary-ads.md` where that document requires a Codex-native full-payload rewrite hook.

**Source:** Phase 07 MCP integration, accepted Codex runtime-home/local-MCP evidence, accepted MCP deployment-lifecycle evidence, the failed client-native redaction discovery, and the operator-approved OpenAI data-egress policy.

**Goal:** Permit the operator-managed OpenAI model `gpt-5.6-terra` only through a reviewed local application-layer gateway that receives the complete Codex Responses API request, redacts approved sensitive fields before any remote transmission, and preserves the existing local MCP stdio and trusted-runner boundaries.

---

### I. Overview and Contract

`assistant01` retains one local Codex runtime under the non-interactive `assistant` account. The local MCP adapter remains a stdio child process and continues to delegate every diagnostic action to the existing trusted runner. MCP is not made network-facing and remains unrelated to remote-provider authentication.

This ADS begins only after both prerequisite handoff gates are accepted: the runtime-home ADS has proven fixed-home Codex and local MCP behavior, and the lifecycle ADS has restored the exact reviewed MCP deployment after guarded remove/reinstall validation. The Codex MCP entry must be disabled at the start of Revised Chunk 0, and remote mode must still be inactive.

Chunk 0 established that the installed Codex client has no verified client-native hook that can rewrite the complete final provider-bound payload. Official Codex hook behavior is narrower:

- `UserPromptSubmit` receives the current prompt and can block it, but it does not provide a supported replacement-prompt field;
- `PreToolUse` can rewrite supported tool inputs, including MCP arguments, but this occurs before execution and is not a provider-request boundary;
- `PostToolUse` receives MCP results, but replacement of MCP tool output is not supported in the reviewed behavior;
- lifecycle hooks do not expose one supported object representing the complete final request after history, instructions, compaction, and tool results are assembled.

Therefore Codex hooks may be used as defense-in-depth blocking controls, but they are not the mandatory redaction boundary.

Codex supports a custom model-provider definition with a fixed `base_url`, OpenAI authentication reuse, and the Responses API wire format. The revised design uses that supported provider boundary to route Codex to a reviewed loopback-only gateway.

```text
operator
  -> local Codex runtime as assistant
  -> local MCP stdio process when tools are needed
  -> trusted aiops_tool_runner.py
  -> approved read-only OpenStack diagnostics

Codex final Responses API request
  -> explicit custom provider base_url
  -> loopback-only AI-OPS redaction gateway
  -> parse and validate complete request
  -> redact and revalidate
  -> rebuild a new outbound request
  -> HTTPS with normal TLS verification
  -> fixed OpenAI upstream endpoint
```

The gateway is an explicit application-layer provider endpoint, not a transparent proxy, TLS interception layer, shell wrapper, generic forwarding proxy, or MCP transport. It accepts only the reviewed Responses API route from the local Codex process and forwards only to one fixed upstream provider endpoint.

#### Approved Remote-Provider Policy

- Provider: OpenAI.
- Model identifier: `gpt-5.6-terra`, treated as operator-provided until runtime acceptance proves the selected account and client accept it.
- Authentication: manual operator login in the Codex runtime context. No provider credential may enter Git, Ansible inventory, MCP configuration, evidence, audit events, command-line arguments, or logs.
- Local provider routing: Codex uses a dedicated custom provider ID whose `base_url` points only to the loopback gateway.
- Upstream transport: HTTPS only with normal system certificate validation.
- Upstream destination: fixed by gateway configuration and never caller-selected. The operator's unrestricted-HTTPS exception remains documented as residual network risk, but application code must still reject an arbitrary upstream URL.
- Retention: provider retention is allowed.
- Training: provider training on submitted content is not approved and must be verified by the operator at account or workspace level.
- Data policy: values associated with `username`, `group`, and secret-like field names must be replaced before remote transmission. Other reviewed diagnostic fields may be submitted.
- Remote mode: disabled by default and enabled only after every local synthetic acceptance test passes.

#### Full-Payload Redaction Boundary

The gateway receives the final JSON request body that Codex intends to send using the Responses API. Every accepted request must pass this sequence:

```text
raw inbound request bytes
  -> bounded read
  -> exact route/method/content-type validation
  -> JSON parse
  -> reviewed request-shape validation
  -> redact_remote_payload(parsed_request)
  -> post-redaction leak scan
  -> construct new outbound JSON from redacted result
  -> send to fixed HTTPS upstream
```

The raw inbound body must never be forwarded. The outbound request must be newly serialized from the redacted object.

A failure at any stage returns a bounded local error and causes no upstream request.

#### Redaction Scope Contract

The enforceable meaning of the policy is:

1. JSON object values whose normalized field names match `username`, `group`, or reviewed aliases are replaced with a fixed marker.
2. Values whose field names are secret-like, including `password`, `passwd`, `secret`, `token`, `api_key`, `private_key`, `credential`, and reviewed aliases, are removed or replaced according to policy.
3. Values discovered in sensitive structured fields are added to an in-memory sensitive-value set and replaced wherever the exact value appears elsewhere in string content in the same request.
4. Canonical text forms such as `username=value`, `username: value`, `group=value`, and JSON embedded in text are redacted when the parser can classify them deterministically.
5. A reserved sensitive label in an unsupported or ambiguous text form causes fail-closed rejection rather than best-effort transmission.
6. Binary, image, audio, file-upload, compressed, multipart, or otherwise unsupported provider input is rejected until separately designed and reviewed.

This boundary guarantees syntactic redaction of reviewed fields and exact-value propagation within the request. It does not claim semantic recognition of an unlabeled identity hidden in arbitrary natural language. Operators and upstream diagnostic producers must represent protected values using the reviewed structured fields or canonical labeled forms. If policy requires discovery of arbitrary unlabeled personal identifiers, remote mode remains disabled until a separate data-classification design is approved.

#### Function Contracts

```text
parse_provider_request(raw_body, headers, path, method) -> ParsedProviderRequest
validate_provider_request_shape(payload, schema_version) -> ValidatedProviderRequest
redact_remote_payload(payload) -> RedactionResult
scan_redacted_payload(result) -> LeakScanResult
build_upstream_request(result, fixed_config) -> UpstreamRequest
forward_responses_request(request) -> streamed provider response
```

`RedactionResult` contains only:

- the redacted payload;
- counts by redaction category;
- classification status;
- request schema version;
- a generated local correlation ID.

It must not contain, log, persist, or return the original values.

### II. Observed Evidence and Assumptions

#### Observed Evidence

- The existing Codex runtime is fixed at `/opt/nodejs/bin/codex`, version `0.144.1`, with runtime home `/opt/openstack-ai-ops/codex-home`.
- Existing runtime evidence proves fixed-home version/help execution but does not prove remote provider use.
- The MCP server returns trusted-runner envelopes in MCP text and structured content; that is not an end-to-end remote-provider redaction boundary.
- The trusted runner sanitizes selected audit arguments but does not sanitize complete provider requests.
- Official Codex hook behavior permits blocking a submitted prompt and rewriting selected pre-tool inputs, but does not provide a verified full final provider-request rewrite seam.
- Official Codex hook behavior does not support replacing MCP tool output through `PostToolUse` in the reviewed behavior.
- Official Codex configuration supports custom model providers with a `base_url`, optional OpenAI authentication reuse, the Responses API wire format, request retry controls, stream retry controls, and WebSocket capability declaration.
- The reviewed MCP surface remains the three low-risk API diagnostics; restricted-host tools remain disabled by default.

#### Assumptions Requiring Local Confirmation

- Codex `0.144.1` honors a custom provider `base_url` for every model request in the selected mode.
- `requires_openai_auth=true` can reuse the operator's manual OpenAI authentication while sending the request to the custom provider endpoint.
- The selected Codex mode can operate through Responses API HTTPS/SSE without WebSockets.
- Request and stream retry counts can be set to zero for acceptance testing.
- The actual request body produced by Codex can be fully parsed as bounded JSON without content encoding or multipart data.
- The selected model identifier is accepted after manual authentication.
- The gateway can run under a separate non-interactive service identity while Codex and MCP remain under `assistant`.

### III. Required Technical Dependencies and Proposed Artifacts

#### Existing Dependencies

- Accepted `07-01-codex-runtime-home-ads-revised.md` runtime-home and local-MCP evidence.
- Accepted `07-02-extended-mcp-client-lifecycle-ads-revised.md` remove/restore evidence with MCP restored and the client entry disabled.
- Fixed Codex runtime and runtime home.
- Restored local stdio MCP adapter.
- Existing runner registry, runner, result envelope, timeout, redaction, and audit path.
- Manual operator authentication, used only in the later authentication chunk.
- Python runtime already used by the AI-OPS deployment.

#### Proposed Runtime Components

- A loopback-only HTTP server capable of bounded JSON request handling and SSE response streaming.
- A reviewed HTTP client using system TLS validation.
- No generic proxy framework, browser automation, packet interception, TLS man-in-the-middle certificate, shell command execution, OpenStack SDK, SSH library, database client, or file-browser capability belongs in the gateway.

Exact dependency choice and version must be pinned after the local payload-shape probe. Standard-library HTTP components are acceptable only if cancellation, streaming, header controls, and request bounds can be proven clearly; otherwise use one narrowly scoped pinned HTTP library.

#### Proposed Repository Artifacts

```text
ansible/ai_ops_runtime/roles/ai_client_runtime/files/provider_gateway/aiops_provider_gateway.py
ansible/ai_ops_runtime/roles/ai_client_runtime/files/provider_gateway/redaction.py
ansible/ai_ops_runtime/roles/ai_client_runtime/templates/provider_gateway/gateway_policy.json.j2
ansible/ai_ops_runtime/roles/ai_client_runtime/templates/provider_gateway/aiops-provider-gateway.service.j2
tests/ai_ops/test_provider_redaction.py
tests/ai_ops/test_provider_gateway.py
ansible/ai_ops_runtime/playbook_validate_phase07_provider_gateway.yml
docs/ai-ops/runtime/openai-provider-gateway.md
```

Proposed runtime paths:

```text
/opt/openstack-ai-ops/provider-gateway/aiops_provider_gateway.py
/opt/openstack-ai-ops/provider-gateway/redaction.py
/opt/openstack-ai-ops/provider-gateway/gateway_policy.json
/opt/openstack-ai-ops/provider-gateway/venv/
```

Proposed identities:

```text
assistant
  - runs Codex
  - runs local MCP adapter and trusted runner
  - accesses approved OpenStack management endpoints
  - may connect to the gateway loopback port
  - must not connect directly to public provider endpoints

aiops-provider
  - runs only the redaction gateway
  - has no OpenStack credentials
  - has no sudo
  - may connect outbound using HTTPS
  - receives provider authorization only in process memory
```

### IV. Step-by-Step Execution Flow

1. The operator starts Codex as `assistant` using the fixed runtime home.
2. Codex loads a reviewed non-secret custom provider definition whose base URL is the loopback gateway. The provider configuration disables WebSockets and automatic retries for initial acceptance.
3. When diagnostics are needed, Codex calls the existing local MCP server over stdio. MCP delegates to the trusted runner exactly as before.
4. Codex assembles its complete provider request, including current prompt, instructions, client-maintained context, tool calls, and MCP tool results.
5. Codex submits the Responses API request to the loopback gateway rather than directly to OpenAI.
6. The gateway accepts only the configured local interface, exact route, exact method, allowed content type, and bounded body size.
7. The gateway authenticates the local caller using the reviewed local control selected during implementation, such as UID-scoped firewall policy and an optional runtime-local header secret. It never treats the provider bearer token as sufficient local authorization by itself.
8. The gateway parses the complete JSON payload and validates it against the reviewed Codex request-shape contract.
9. The gateway redacts structured sensitive fields, propagates discovered sensitive values across string content, handles canonical text forms, and rejects ambiguous sensitive-label forms.
10. The gateway scans the redacted payload for original synthetic markers, unredacted reserved fields, secret-like keys, unsupported content, and schema drift.
11. The gateway checks that the requested model is exactly the reviewed model and that no caller-selected upstream URL or transport exists.
12. The gateway creates a new outbound request from the redacted object, forwards only the minimum required headers, and sends it to the fixed OpenAI HTTPS endpoint with normal TLS verification.
13. The gateway streams the provider response back to Codex without recording response bodies. It emits only bounded non-sensitive lifecycle metadata.
14. Codex presents the answer to the operator. Local MCP and runner audit correlation remain unchanged.
15. On any gateway, redaction, TLS, schema, authentication, or evidence failure, the request is not sent and remote mode remains disabled.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Required Action | Result |
|---|---|---|---|
| Client configuration | Codex bypasses the custom provider or contacts OpenAI directly | Block direct public egress for `assistant`; disable remote mode | `ERR_PROVIDER_BYPASS` |
| Local listener | Gateway binds a non-loopback interface | Fail service startup | `ERR_GATEWAY_BIND_SCOPE` |
| Local authorization | Caller is not the reviewed local client identity | Reject without parsing or forwarding | `ERR_GATEWAY_LOCAL_AUTH` |
| Route | Method or path differs from the reviewed Responses API route | Return local not-found/method error | `ERR_GATEWAY_ROUTE` |
| Request bounds | Body exceeds the reviewed maximum | Stop reading, reject, send nothing upstream | `ERR_GATEWAY_REQUEST_SIZE` |
| Encoding | Compressed, multipart, binary, file, image, or audio input is received | Reject until separately reviewed | `ERR_GATEWAY_UNSUPPORTED_CONTENT` |
| JSON parsing | Request is malformed or contains duplicate-key ambiguity | Reject and do not log the body | `ERR_GATEWAY_JSON` |
| Schema validation | Request shape differs from the reviewed Codex schema | Fail closed; require a new compatibility review | `ERR_GATEWAY_SCHEMA_DRIFT` |
| Redaction | Sensitive value cannot be classified safely | Reject without upstream transmission | `ERR_OPENAI_REDACTION_UNCLASSIFIED` |
| Redaction | Synthetic marker remains after redaction | Reject and disable acceptance configuration | `ERR_OPENAI_REDACTION_LEAK` |
| Model policy | Model differs from `gpt-5.6-terra` | Reject rather than rewriting silently | `ERR_OPENAI_MODEL_SELECTION` |
| Upstream policy | Caller attempts to select host, URL, proxy, or transport | Reject; upstream is fixed | `ERR_GATEWAY_UPSTREAM_POLICY` |
| Authentication | Provider token is absent or invalid | Return bounded authentication failure; never log token | `ERR_OPENAI_AUTH_MANUAL` |
| TLS | Certificate validation or HTTPS connection fails | Stop; never disable verification | `ERR_OPENAI_TLS` |
| Provider response | Stream is malformed, oversized, or stalls | Terminate only the gateway-owned upstream request and return bounded error | `ERR_OPENAI_RESPONSE` |
| Evidence | Raw payload, header, token, prompt, response, or configuration is retained | Delete unsafe evidence and repeat with metadata-only recording | `ERR_OPENAI_EVIDENCE_SANITIZATION` |

No failure may fall back to direct Codex-to-provider access, a different model, a generic proxy, an unredacted retry, or a URL-mode MCP server.

### VI. Security, Integrity, Idempotency, and Cleanup

#### Security Boundary

- MCP remains local stdio and is not changed into HTTP, SSE, WebSocket, or URL mode.
- The provider gateway is a separate explicit loopback Responses API boundary. It must not expose MCP tools, OpenStack operations, shell execution, file access, or remediation.
- Codex hooks are optional defense-in-depth controls. They may block obvious secrets in user prompts or deny unsafe tools, but successful hook execution is not evidence of full-payload redaction.
- Direct provider egress by the `assistant` identity must be denied. The `assistant` identity retains only loopback access, required OpenStack management destinations, package/runtime destinations explicitly needed by policy, and no general public provider route.
- The `aiops-provider` identity has no OpenStack credentials or management-plane role.
- The upstream host and path are fixed by reviewed configuration. Request data may never choose them.
- The gateway forwards only required authentication and protocol headers. It removes cookies, proxy headers, inbound host, forwarding headers, connection headers, content length, and unreviewed tracing headers before constructing the upstream request.
- Provider bearer material is memory-only and must be redacted from exception messages, process inspection evidence, access logs, and tests.
- Gateway access logs must be disabled or metadata-only. Request and response bodies are never logged.
- The gateway must not persist conversation state. Codex remains the owner of local conversation state.

#### Redaction Integrity

- Matching is case-insensitive after deterministic field-name normalization.
- The original sensitive values exist only in the parsed inbound object and ephemeral in-memory sensitive-value set for the duration of one request.
- The redactor returns a new object rather than mutating and later reusing the raw parsed object.
- Duplicate JSON keys are rejected because parser overwrite semantics could bypass field policy.
- Post-redaction serialization is scanned again before network transmission.
- Tests must use unique synthetic markers and prove that no marker reaches the fake upstream sink.
- Redaction counts may be logged; source values may not.

#### Idempotency and Retries

- Local validation and gateway deployment must converge without changing OpenStack resources.
- Codex request and stream retries are set to zero during acceptance. Any later retry policy requires a separate review because each retry is a new provider submission.
- The gateway performs no automatic retry in the initial release.
- Every accepted submission receives a fresh correlation ID. Correlation metadata must not include prompt or diagnostic content.

#### Cleanup and Rollback

- Disable the Codex custom-provider selection first.
- Stop and disable the gateway service.
- Restore the remote-disabled Codex profile; do not switch to direct OpenAI as fallback.
- Remove temporary synthetic fixtures and fake upstream sinks.
- Preserve the local MCP adapter, trusted runner, registry, OpenStack credentials, audit records, and Codex runtime home.
- Do not delete operator-managed authentication state unless the operator explicitly requests logout or credential revocation.

### VII. Validation Strategy

#### Static Validation

```bash
rtk python3 -m py_compile <provider-gateway-python-files>
rtk python3 -m unittest tests.ai_ops.test_provider_redaction tests.ai_ops.test_provider_gateway
rtk python3 -m json.tool <rendered-gateway-policy>
rtk ansible-playbook --syntax-check -i ansible/ai_ops_runtime/inventories/local/local.yml <phase07-provider-playbook>
rtk git diff --check
```

#### Redaction Unit Tests

Test at minimum:

- nested `username` and `group` fields;
- case and separator aliases such as `user_name` and `group-name` only when explicitly approved;
- arrays containing sensitive objects;
- exact sensitive values repeated in unrelated string fields;
- canonical `key=value` and `key: value` text forms;
- JSON embedded in string content;
- empty, null, numeric, boolean, and collection values under protected keys;
- secret-like keys;
- duplicate JSON keys;
- malformed JSON;
- ambiguous sensitive-label text;
- payloads containing unsupported file, image, audio, or binary representations;
- proof that a non-sensitive marker remains intact;
- proof that redaction metadata contains counts but no original values.

#### Local End-to-End Acceptance

Use a fake local upstream before any OpenAI access:

```text
Codex synthetic prompt and synthetic MCP result
  -> loopback redaction gateway
  -> fake upstream capture sink
```

The fake sink must assert:

- zero prohibited synthetic markers;
- the approved non-sensitive marker remains;
- the model field is the reviewed value;
- only reviewed headers arrive;
- no unexpected route or second request occurs;
- retries are zero;
- no WebSocket connection is attempted.

Synthetic requests should place unique markers in:

- current operator prompt;
- prior conversation context;
- system/developer context where controllable;
- nested MCP structured content;
- MCP text content;
- tool arguments;
- tool results;
- compacted or resumed context if the client supports those flows.

#### Process and Network Validation

- Prove the gateway listens only on loopback.
- Prove MCP still uses stdio and creates no listener.
- Prove `assistant` cannot connect directly to the public provider endpoint.
- Prove `assistant` can still reach required OpenStack management endpoints.
- Prove `aiops-provider` has no OpenStack credentials and cannot invoke the trusted runner through an alternate path.
- Prove the gateway uses normal TLS verification and a fixed upstream URL.
- Inspect logs and evidence for forbidden payloads, credentials, authorization headers, and raw response data.

#### Remote Acceptance

Only after local acceptance passes:

- the operator authenticates manually;
- the reviewed custom provider is selected runtime-locally;
- one minimal synthetic request is sent;
- only metadata is retained: provider, model, timestamp, correlation ID, redaction counts, TLS result, listener result, and pass/fail status;
- no raw prompt, response, provider token, client configuration, MCP payload, or audit line is retained.

### VIII. Thin Vertical Slice Chunk Design

Implementation must proceed one chunk at a time. Each chunk ends with targeted validation, scoped diff review, risk assessment, and an explicit stop.

#### Revised Chunk 0: Custom-Provider and Payload-Shape Confirmation

- **Prerequisites:** Accepted runtime-home/local-MCP evidence; accepted lifecycle remove/restore evidence; exact MCP deployment restored; runtime-local MCP entry disabled; remote mode inactive.
- **Goal:** Prove that installed Codex `0.144.1` can route all model requests to a custom Responses API base URL and characterize the exact synthetic request shape without contacting OpenAI.
- **Actions:** Use a temporary loopback fake provider, a synthetic prompt, dummy local authentication, retry counts of zero, and no MCP production data. Do not alter the accepted MCP lifecycle contract or runtime-home role.
- **Confirm:** `base_url`, `wire_api=responses`, `requires_openai_auth` behavior, request path, method, headers, JSON shape, SSE expectations, cancellation, retry behavior, WebSocket behavior, and direct-egress controls.
- **Files changed:** none in the repository; temporary fixtures only.
- **Stop condition:** Either the full request reaches the fake provider through one deterministic route, or remote mode remains disabled and this architecture is blocked.

#### Chunk 1: Redaction Contract and Pure Unit Tests

- **Goal:** Implement the standalone fail-closed redaction engine with no listener and no network code.
- **Files:** `redaction.py` and `test_provider_redaction.py` only.
- **Implementation:** New-object transformation, normalized protected keys, exact-value propagation, canonical text parsing, duplicate-key protection support, ambiguity rejection, no logging.
- **Validation:** Focused compile and unit tests.
- **Stop condition:** No prohibited synthetic marker survives; unsupported or ambiguous content is rejected.

#### Chunk 2: Fail-Closed Gateway Stub

- **Goal:** Add a loopback-only provider endpoint that validates local route, method, content type, request bounds, and JSON but never forwards upstream.
- **Files:** gateway entrypoint, gateway tests, and minimal policy fixture.
- **Implementation:** Exact route only, bounded body, no access logging, explicit unavailable response after validation, fixed identity.
- **Validation:** Bind-scope, route, size, encoding, malformed JSON, cancellation, and no-forward tests.
- **Stop condition:** The service accepts only the reviewed local request shape and cannot perform remote I/O.

#### Chunk 3: Redaction-to-Fake-Upstream Slice

- **Goal:** Connect the validated gateway request to the redactor and a fixed fake upstream transport.
- **Implementation:** Parse, validate, redact, scan, rebuild, send to test sink. Do not use OpenAI or real credentials.
- **Validation:** Full marker matrix, header stripping, fixed route, fixed upstream, zero retries, no raw logging, streaming response behavior.
- **Stop condition:** The fake upstream receives only sanitized payloads for all accepted cases.

#### Chunk 4: Codex-to-Gateway Local Integration

- **Goal:** Configure a temporary synthetic Codex custom provider and prove an actual Codex session flows through the gateway to the fake upstream.
- **Implementation:** Runtime-local temporary profile only; no committed credential or permanent provider selection.
- **Validation:** Current prompt, history, MCP synthetic result, compaction/resume where supported, cancellation, one request per turn, and no direct public egress.
- **Stop condition:** Every observed Codex provider request uses the gateway and passes redaction or fails closed.

#### Chunk 5: Identity, Service, and Egress Controls

- **Goal:** Deploy the gateway under `aiops-provider`, bind only to loopback, and enforce that `assistant` cannot bypass it.
- **Files:** Ansible defaults/tasks/templates and gateway policy.
- **Implementation:** Separate service identity, minimal modes, fixed upstream, UID-aware network policy, required OpenStack management exceptions for `assistant`, no provider credential in automation.
- **Validation:** Ansible syntax, first/second-run idempotency, process ownership, listener scope, direct-egress denial, OpenStack access preservation, rollback.
- **Stop condition:** Bypass is technically blocked and local MCP remains unchanged.

#### Chunk 6: Manual Authentication Compatibility

- **Goal:** Confirm manual OpenAI authentication can be reused through the reviewed custom provider without exposing credentials.
- **Actions:** Operator-owned login only; inspect only non-sensitive status. Never print, copy, or capture tokens.
- **Validation:** Authentication success/failure behavior, gateway header suppression, no credential in logs/process arguments/evidence, exact model acceptance.
- **Stop condition:** Authentication reaches the fixed upstream only through the gateway, or remote mode remains disabled.

#### Chunk 7: Remote Synthetic Acceptance and Evidence

- **Goal:** Send one minimal synthetic request through the complete boundary and create sanitized evidence.
- **Validation:** Redaction counts, provider/model status, TLS verification, no listener beyond loopback gateway, no direct Codex egress, unchanged MCP stdio and runner behavior.
- **Files:** validation playbook, operator runbook, dated metadata-only evidence, and phase checklist updates only after success.
- **Stop condition:** Remote use is accepted with sanitized proof, or the custom provider and gateway are disabled with the blocker recorded.

### IX. Handoff to `chunked-implementation`

Use this prompt for the next agent:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Execute Revised Chunk 0 of the Phase 07 OpenAI Remote Provider via Reviewed Redaction Gateway ADS.

Mode:
Execute Chunk 0 only. Treat the accepted runtime-home/local-MCP evidence and accepted MCP lifecycle remove/restore evidence as prerequisites. Confirm the exact MCP deployment is restored and the runtime-local MCP entry is disabled. Do not edit repository files, alter lifecycle tasks, contact OpenAI, log in, use a real provider credential, or enable permanent remote mode.

Create a temporary loopback fake Responses API provider and a temporary Codex custom-provider profile using synthetic data only. Confirm whether installed Codex 0.144.1 routes the complete request to the configured base_url, and record the exact method, route, bounded JSON shape, SSE expectations, retry behavior, WebSocket behavior, cancellation behavior, and whether direct public egress can be blocked while the custom provider remains usable.

Do not proceed to the redactor. If the complete request cannot be captured at the explicit custom-provider boundary, report the blocker and stop.
```

After Revised Chunk 0 is accepted:

```text
Resume from the accepted Revised Chunk 0 handoff.
Execute Revised Chunk 1 only: the pure redaction module and focused synthetic tests.
Do not add a listener, gateway forwarding, Codex configuration, authentication, or network traffic.
Run targeted validation, review the scoped diff, assess residual risk, write the next handoff, and stop.
```

### X. Conclusion and Next Steps

The previous ADS correctly blocked implementation because Codex does not provide a verified client-native hook for rewriting the complete final provider-bound payload. This revised architecture starts only after the Codex runtime-home and MCP lifecycle ADSs are accepted, then removes the unsupported hook dependency while retaining Codex as the local client.

The mandatory security boundary becomes an explicit loopback Responses API gateway configured as a custom Codex provider. This gateway receives the final assembled request, validates and redacts the entire supported payload, rebuilds a new outbound request, and forwards only to a fixed OpenAI HTTPS endpoint. Codex hooks remain useful for early blocking but are not trusted as the redaction mechanism.

The next action is Revised Chunk 0 only: prove the custom-provider request seam and payload shape locally with synthetic data and a fake provider. No redactor, gateway deployment, provider login, or remote request should be implemented until that seam is confirmed.
