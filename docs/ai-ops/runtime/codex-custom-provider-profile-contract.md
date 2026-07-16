# Codex 0.144.1 Custom-Provider Profile Contract

## Status

**Locally route-validated runtime-override contract — not accepted for remote use.**
The official Codex 0.144.1 runtime-override form reached the no-forward loopback
gateway, and the nested-input redaction ambiguity has been resolved and deployed.
The reviewed gateway source now rebuilds the authenticated ChatGPT/device-auth
request for the fixed ChatGPT Codex backend with transient account routing and
schema 2 metadata-only evidence. These local source and injected-transport checks
do not authorize deployment or a provider request. Remote provider mode remains
disabled pending the remaining revised provider-boundary ADS chunks and a separately
approved provider request.

## Scope and boundaries

- Client: `/opt/nodejs/bin/codex`, version `0.144.1`, run only as `assistant` with
  `HOME=/opt/openstack-ai-ops/codex-home`.
- Selection: pass the dedicated provider definition and selected provider through
  Codex `-c` runtime overrides for the one diagnostic invocation.
- Model: `gpt-5.6-terra` only.
- Base URL: an explicitly chosen loopback diagnostic URL only. It is never a public
  provider URL and is deleted after the diagnostic.
- Authentication: `requires_openai_auth = true` reuses the operator-managed login.
  The profile contains no token, device code, account data, environment secret, or
  credential reference.
- Transport: Responses API over HTTP/SSE for the loopback diagnostic. WebSockets and
  automatic request/stream retries are disabled.
- No profile file is created or existing operator-managed profile overwritten.

## Route-validated runtime override shape

Use these non-secret runtime overrides only for the temporary loopback diagnostic.
They are not provider credentials.

```text
-c 'model_providers.aiops_loopback={ name = "AI-OPS loopback diagnostic", base_url = "http://127.0.0.1:<diagnostic-port>/v1", wire_api = "responses", requires_openai_auth = true, request_max_retries = 0, stream_max_retries = 0, supports_websockets = false }'
-c 'model_provider="aiops_loopback"'
-c 'model="gpt-5.6-terra"'
```

## Validation contract

Before a synthetic invocation:

1. Verify `rtk codex --version` returns `0.144.1` in the fixed runtime home.
2. Verify `rtk codex login status` succeeds without printing its output.
3. Use the exact non-secret runtime overrides above; do not create or overwrite a
   profile file.
4. Start a temporary `aiops-provider`-owned loopback gateway on a port other than
   `8765`, with `fake_upstream_sink` and `evidence_writer=None`.
5. Use an assistant-owned temporary Git workspace and `rtk codex exec --ephemeral`.
   Do not use the unsupported `--ask-for-approval never` option.
6. Permit exactly one synthetic invocation. Retain only client exit category,
   request method/route, gateway HTTP status/code, redaction category, and the
   fixed ambiguity metadata when applicable.
7. Require the reviewed model-discovery route followed by exactly one
   `POST /v1/responses`. Any other result fails closed.
8. Remove the workspace, runner, listener, metadata, and local temporary files in
   an unconditional cleanup path.

## Known acceptance gap

The runtime override shape is grounded in the Phase 07 provider-boundary ADS, the
official `rust-v0.144.1` source proxy example, and metadata-only loopback runs. The
redaction ambiguity is resolved: local no-forward acceptance reached the reviewed
model-discovery routes and exactly one `POST /v1/responses`, and the deployed gateway
later reached verified upstream TLS with redacted metadata.

Remote acceptance remains blocked pending deployment and egress validation plus the
local fake-upstream acceptance gate. The reviewed source fixes the upstream to
`chatgpt.com/backend-api/codex/responses`, forwards only the transient allowlisted
Bearer and `ChatGPT-Account-ID` headers, and writes schema 2 metadata-only evidence;
it has not been deployed or used for a provider request. Do not change this
runtime-override shape, inspect authentication or account values, or retry a real
provider request without fresh explicit approval.

## References

- `docs/ai-ops/implementation-plan/ads/07-03-openai-remote-provider-boundary-ads-revised.md`
- `docs/ai-ops/runtime/phase07-remote-provider-decision-2026-07-14.md`
- `docs/ai-ops/runtime/provider-gateway-metadata-evidence.md`
