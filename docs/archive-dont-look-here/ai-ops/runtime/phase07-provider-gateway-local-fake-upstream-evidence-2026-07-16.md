# Phase 07 Provider Gateway Local Fake-Upstream Evidence — 2026-07-16

## Scope

This note records the local-only provider-gateway deployment and authenticated
Codex fake-upstream acceptance checks on `assistant01`. It is not provider
acceptance evidence and does not authorize remote mode or a provider request.

## Deployment boundary

The permanent deployment validator confirmed:

- `aiops-provider-gateway` is active and enabled as `aiops-provider`.
- The service retains the reviewed systemd identity, sandbox, IPv4-only address
  family, write scope, and cleared proxy environment.
- The production listener is limited to `127.0.0.1:8765`.
- Gateway artifacts use the reviewed root/group ownership and modes.
- The metadata ledger directory and file retain `0700` and `0600` modes,
  respectively, with `aiops-provider` ownership.

## Local fake-upstream acceptance

A temporary `aiops-provider`-owned loopback gateway used an injected local
transport and `evidence_writer=None`. A temporary assistant-owned Git workspace
ran one authenticated Codex `0.144.1` diagnostic with ephemeral runtime
overrides, no profile file, and retries disabled.

Only the following sanitized metadata was retained:

- two exact `GET /v1/models?client_version=0.144.1` discovery requests;
- one `POST /v1/responses` loopback request;
- exactly one Authorization header and one `ChatGPT-Account-ID` header by
  count only;
- one rebuilt local request to `/backend-api/codex/responses`;
- rebuilt header names only: `Accept`, `Content-Type`, `Authorization`, and
  `ChatGPT-Account-ID`;
- client exit category `1`, retained as local fake-stream metadata rather than
  a provider outcome.

The fake transport could not open an external connection. No provider request,
ledger write, raw request/response body, header value, account value, credential,
prompt, client output, or temporary runtime configuration was retained.

## Cleanup and remaining gates

Temporary runner, listener, workspace, and metadata paths were removed. A
post-check found no listener on the temporary port; the production loopback
listener and deployment validator remained healthy.

Remote mode remains disabled. The direct-`assistant` egress-denial recheck was
not run because no separately approved non-provider synthetic endpoint was
supplied. This note does not claim DNS/TLS remote acceptance or authorization
for any real provider request.

## References

- `docs/ai-ops/runtime/codex-custom-provider-profile-contract.md`
- `docs/ai-ops/runtime/provider-gateway-metadata-evidence.md`
- `docs/ai-ops/implementation-plan/ads/07-03-openai-remote-provider-boundary-ads-revised.md`
