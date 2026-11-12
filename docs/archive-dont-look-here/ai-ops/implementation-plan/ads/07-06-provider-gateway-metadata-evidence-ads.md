## Architectural Design Specification: Provider Gateway Metadata-Only Acceptance Evidence

**Source:** `07-03-openai-remote-provider-boundary-ads-revised.md` Chunk 7; provider-gateway evidence gap discovered during Chunk 7 preparation.

**Goal:** Retain bounded, non-secret evidence for one reviewed provider-boundary acceptance request without retaining any request body, response body, authorization value, header value, prompt, or provider output.

---

### I. Overview and Contract

The loopback gateway will emit one local, append-only metadata event per accepted request attempt to a dedicated `aiops-provider`-owned ledger. The ledger is the only runtime evidence source; no HTTP metrics endpoint, access log, or request logging is permitted.

**Event Contract (Conceptual):** UTC timestamp; generated correlation UUID; fixed model identifier; route; classification status; redaction-count mapping; gateway outcome; upstream HTTP status class or sanitized transport failure; TLS-attempt pass/fail; and schema version. It must exclude payloads, payload lengths, header names/values, authorization material, response content, provider URL, account data, and exception text.

The gateway serializes and durably appends the event before returning a final result. If event validation or persistence fails, it returns a fail-closed error and must not forward upstream.

### II. Observed Evidence and Assumptions

- `redaction.py` already produces `redaction_counts`, `classification_status`, and a UUID `correlation_id` in `RedactionResult` and `LeakScanResult`.
- `aiops_provider_gateway.py` currently rebuilds and forwards a request but disables `BaseHTTPRequestHandler` logging, so it emits no acceptance evidence.
- The gateway is deployed as `aiops-provider`; its service root and systemd sandboxing are managed by `ai_client_runtime` provider-gateway tasks and template.
- The accepted gateway policy fixes the loopback listener, Responses route, model, HTTPS upstream, timeout, and response bound.

### III. Required Technical Dependencies and Imports

- Existing Python standard library only: `dataclasses`, `datetime`, `json`, `os`, `pathlib`, `uuid` validation, and locking/atomic-append primitives as confirmed during implementation.
- Existing gateway/redaction modules and provider-gateway Ansible deployment task/template.
- No telemetry SDK, database, HTTP endpoint, provider SDK, credentials, or new network dependency.

### IV. Step-by-Step Procedure / Execution Flow

1. Validate the reviewed request and run redaction/leak scan.
2. Construct a strict metadata event from the redaction result and fixed policy values.
3. Before upstream forwarding, append a `forward_started` metadata event; failure returns `ERR_GATEWAY_EVIDENCE` and performs no remote I/O.
4. After a terminal sanitized outcome, append a matching terminal event using the same correlation UUID.
5. The operator retrieves only the reviewed metadata fields through a privileged local procedure; the runbook never copies raw ledger lines into repository evidence.
6. Enforce bounded retention by a reviewed size limit with no automatic deletion or rotation; overflow fails closed for new remote acceptance requests.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
|---|---|---|---|
| Event construction | Unsupported value or forbidden field | Do not forward | `ERR_GATEWAY_EVIDENCE` (proposed) |
| Ledger write | Missing path, ownership/mode drift, full disk, lock/write failure | Do not forward or return a sanitized failure | `ERR_GATEWAY_EVIDENCE` (proposed) |
| Upstream transport | TLS/connection/non-2xx failure | Append sanitized terminal outcome only | Existing sanitized gateway error |
| Retention | Safe size bound cannot be enforced | Do not forward further acceptance requests | `ERR_GATEWAY_EVIDENCE_RETENTION` (proposed) |
| Evidence review | Unexpected field or raw content found | Disable acceptance path, preserve for incident handling without copying content | `ERR_GATEWAY_EVIDENCE_POLICY` (proposed) |

### VI. Security, Integrity, Idempotency, and Cleanup

- Permit only an allowlisted event schema; reject unknown keys and values exceeding fixed bounds.
- Do not log raw inputs, outputs, headers, authorization, exceptions, URLs, or byte counts.
- Use `0600` ledger permissions under a dedicated gateway evidence directory; the service identity writes, and the approved operator procedure reads metadata only.
- Maintain a bounded ledger and explicit retention behavior. No network listener or query API is introduced.
- A retry may create a new correlation UUID, but each UUID must have at most one started and one terminal event.
- Rollback removes the new ledger artifact only after the gateway service is stopped and after approval; it must not remove authentication state or unrelated logs.

### VII. Validation Strategy

- Unit-test event schema validation, forbidden-field rejection, count/UUID bounds, and deterministic serialization.
- Unit-test fail-closed behavior: a ledger write failure must make `forward_upstream_request` unreachable.
- Unit-test terminal success, non-2xx, and transport-failure metadata paths using injected upstream connections.
- Validate Ansible syntax/lint, service ownership/mode, and systemd sandbox write access.
- Run a local fake-upstream integration test that inspects only parsed metadata fields and asserts no synthetic protected values or authorization marker appears.
- Before remote acceptance, review `git diff --check`, scoped diffs, and sanitized runtime metadata only.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full capability in one pass.

#### Chunk 0: Evidence Contract and Deployment Discovery
- **Goal:** Confirm service sandbox write constraints, safe ledger location, existing test seams, and accepted metadata field bounds.
- **Files to read:** provider gateway source/tests, deployment task, service template, policy, and this ADS.
- **Commands:** scoped searches, static inspection, and metadata-only service inspection.
- **Evidence to confirm:** no existing evidence sink; exact service identity and writable-path contract.
- **Stop condition:** Stop with no source edit if any required field would contain provider data or a safe local write path is absent.

#### Chunk 1: Metadata Event Contract and Pure Tests
- **Goal:** Add a compile-safe immutable event type and strict serializer with no filesystem or gateway wiring.
- **Files to change:** `aiops_provider_gateway.py` and `test_provider_gateway.py`.
- **Symbols to add/change:** conceptual `GatewayEvidenceEvent` and `serialize_gateway_evidence_event`.
- **Implementation shape:** allowlisted values and fixed bounds only; no-op/explicit error behavior is safe because no call site changes yet.
- **Validation:** Python compile and focused provider-gateway tests.
- **Stop condition:** No event can contain payload/header/authorization/provider-output fields.

#### Chunk 2: Fail-Closed Local Ledger Slice
- **Goal:** Add an injected ledger writer that atomically appends only validated event bytes and fails closed.
- **Files to change:** gateway source and focused tests.
- **Symbols to add/change:** conceptual `GatewayEvidenceWriter` protocol and append helper.
- **Implementation shape:** test writer first; production writer remains unwired until deployment contract is confirmed.
- **Validation:** write-failure/no-forward tests and syntax/tests.
- **Stop condition:** A failed write can never invoke the upstream connection factory.

#### Chunk 2.5: Retention Guard
- **Goal:** Bound the append-only ledger without automatic deletion or rotation.
- **Files to change:** gateway source and focused tests.
- **Symbols to add/change:** conceptual maximum-ledger bound and exclusive append lock.
- **Implementation shape:** lock → inspect current size → reject overflow before write → append/fsync; preserve all existing evidence for explicit operator handling.
- **Validation:** exact-bound success, over-bound rejection, symlink rejection, and concurrent append tests.
- **Stop condition:** An overflow, unsafe path, or lock/write failure cannot add an unbounded record or permit a later forwarding call.

#### Chunk 3: Gateway Outcome Wiring
- **Goal:** Wire started and terminal sanitized events to the gateway request lifecycle.
- **Files to change:** gateway source and focused tests.
- **Symbols to add/change:** conceptual event factory and outcome mapping.
- **Implementation shape:** reuse the redaction correlation UUID; preserve existing fail-closed error mapping and no access logging.
- **Validation:** fake-upstream success, non-2xx, transport failure, redaction failure, and header-suppression tests.
- **Stop condition:** Tests prove one bounded metadata lifecycle without raw data retention.

#### Chunk 4: Deployment and Operator Runbook
- **Goal:** Provision the minimal evidence directory/service permissions and document metadata-only retrieval and rollback.
- **Files to change:** provider-gateway Ansible task/template plus one runtime runbook.
- **Symbols to add/change:** conceptual evidence path and service `ReadWritePaths` allowance.
- **Implementation shape:** explicit owner/mode and syntax-validated unit; no listener/API or remote request.
- **Validation:** Ansible syntax/lint, systemd verify, ownership/mode checks, local fake-upstream smoke, and diff review.
- **Stop condition:** The service can write only the reviewed evidence path and the runbook excludes raw data.

#### Chunk 5: One Remote Synthetic Acceptance
- **Goal:** Execute one separately approved minimal synthetic request and record only sanitized evidence.
- **Files to change:** dated evidence note/checklist only after success.
- **Implementation shape:** preflight → one request → metadata review → direct-egress/listener recheck → stop.
- **Validation:** ADS Chunk 7 matrix.
- **Stop condition:** Remote use is accepted with sanitized proof, or the profile/gateway is disabled and the blocker is recorded.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, pre-edit-discipline, safe-python-edit, and post-edit-discipline.

Task:
Execute Chunk 0 only of the Provider Gateway Metadata-Only Acceptance Evidence ADS.

Do not edit source files, invoke Codex, contact a provider, inspect credentials, or create a network listener. Confirm the gateway service sandbox, exact writable-path constraints, and test seams. Stop with a sanitized discovery report.
```

After Chunk 0 is accepted, execute Chunk 1 only and stop after focused compile/test/diff validation.

### X. Conclusion and Next Steps

Chunk 7 acceptance cannot truthfully meet its metadata-only evidence contract until the gateway emits a bounded local event. Execute Chunk 0 discovery next, then implement one compile-safe evidence slice at a time. A remote synthetic request remains prohibited until Chunk 4 is accepted and separately approved.
