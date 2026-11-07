# Delivery 1 — Go Authentication Environment Task Amendment

**Status:** Owner-approved Go authentication-source candidate; exact fingerprints and commit state are recorded in the U4 approval record. Independent fresh-session review and fresh preflight remain required before implementation; no code authorization is granted.

**Base:** `16cfe0ede231df7b90b4f93961a7b6eff16512a1`, branch `aiops-go-phase01`; worktree was clean when prepared.

**Amends:** [Go-owned task](01-go-owned-safety-boundary-task.md), committed blob `ab3dda9b0dfaa4b8e00b389a8485a0b5d1621e8f835039d1291af951ab639dbb`; as constrained by [Go-owned ADR](../architecture/01-go-owned-safety-boundary-adr.md), committed blob `58e8c4e2c9c2c92fb341a3b8693a49a09671efb9`; and the sole [Delivery 1 ladder](../delivery/01-safety-boundary-and-manual-slice-delivery.md), committed blob `711a26dc1a5242b0c9e254fee4028b4d2aa065838d006a40fc1ecb7dcd6dd7cb`.

## 1. Purpose and authority

This amendment records user decision `U4` for the Go-only authentication source: “For aiops in Go language, I prefer to use environment variable only. I approved for the architecture changes.” The user confirmed the bounded interpretation—trusted launcher process environment, authentication inputs only, no Go `.env` loader, and preservation of the dedicated reader/fixed-project/no-fallback constraints—with: “Yes, I confirm that.”

Apply this amendment only to the new Go manual diagnostic path. Keep the original accepted ADR, task, PRD, identity/policy contract, legacy runtimes, and prior approval record unchanged. The updated ladder is owner-approved for commitment; independent fresh-session review and preflight remain required. This authorization does not permit implementation, credential provisioning, `.env` access, live-cloud actions, deployment, or changes to existing identities/roles.

## 2. Required authentication boundary

- OpenStack authentication inputs for the Go manual diagnostic process come only from its process environment, provided by a trusted operator-controlled launcher.
- Go must not itself locate/read/load `.env` or use `clouds.yaml`, `secure.yaml`, or another profile as an authentication source or fallback. Do not invoke the root Makefile for credential loading or add a dotenv/auth-profile parser dependency. Any separate trusted noncredential policy/configuration source remains governed by the parent ADR/task; U4 does not authorize changing that source or loading credentials from it.
- Allow only the password-based, project-scoped inputs required by the pinned Gophercloud version and the approved identity contract. Candidate names to verify are `OS_AUTH_URL`, `OS_USERNAME`, `OS_PASSWORD`, exactly one of `OS_PROJECT_ID`/`OS_PROJECT_NAME`, and the required domain selector `OS_DOMAIN_ID`/`OS_DOMAIN_NAME`. Reject missing, conflicting, or unsupported authentication modes before making network requests. Values must not appear in source, tests, documentation, process arguments, or output.
- The observed pinned Gophercloud v2.14.0 `AuthOptionsFromEnv` helper reads additional inputs (`OS_USERID`, `OS_PASSCODE`, application-credential variables, `OS_SYSTEM_SCOPE`, and deprecated `OS_TENANT_ID`/`OS_TENANT_NAME`). It does not read `OS_TOKEN`; token-based auth is still outside this contract and must not be introduced. The implementation must either reject unsupported inputs before they can affect the helper or avoid it and map only the reviewed allowlist. Verify the exact mapping against the pinned SDK and identity contract.
- The environment is not an authorization policy source. Authenticate only as the dedicated `aiops-assistant-project-reader`; retain project label `admin`, domain `default`, the expected project identity, reader-only role, expiry, and admin-team rotation/revocation. Verify the authenticated project before any resource read. A missing/mismatched identity, project, or policy fails closed without a fallback credential.
- Authentication endpoint and project scope must match the approved deployment context. `OS_REGION_NAME`, `OS_INTERFACE`, proxy variables, CLI cloud/config selectors, request data, or model output cannot choose service endpoints, region, targets, tools, budget, audit path, or approval state. Preserve fixed service-endpoint, TLS, destination, redirect, proxy, response-size, and audit controls from the parent task/ADR.
- Never forward OpenStack variables or secrets to Codex, Pi, another model, or child processes. Do not expose them through logs, errors, tool results, audit, reports, or fixtures. Add canary tests for existing Codex/Pi child-environment boundaries.
- The existing revised/Python profile-based contracts continue to apply to those runtimes and are not changed by this Go-only amendment.

## 3. Bounded implementation and verification obligations

After this owner-approved candidate is independently reviewed and a named implementation chunk is separately authorized, update the existing Delivery 1 chunks—not a second ladder—to include:

1. A closed-environment-input validator tied to the pinned SDK; exact-one project/domain selectors; endpoint and identity/project consistency; unsupported-mode rejection before auth; and no dotenv/profile-credential auth fallback.
2. Assert zero authentication for pre-auth policy denials, disabled routes, and missing/conflicting/malformed/unsupported environment selectors. If authentication returns a principal/project that fails trusted identity/scope checks, assert zero subsequent service-resource calls. Do not claim offline fixtures prove the cloud-side role; effective reader permissions remain a separately authorized live/admin-verification gate. Cover system-scope, unsupported token variables/auth modes, application-credential, passcode, user-ID, tenant-alias, proxy, and endpoint-selector cases as applicable to the closed contract.
3. Positive tests with synthetic credentials and local/fake transports only. Never use real credential values or call the live cloud during offline verification. Assert the principal/project check occurs before resource requests and that secret canaries are absent from outputs, logs, errors, audit, and model/child environments.
4. Regression tests proving the Go authentication path does not load `.env` or YAML/profile credentials and that authentication environment variables are not passed to model processes. Any separate noncredential policy/configuration loading must remain within the parent contract. Keep live verification of effective reader permissions in the already-defined separately authorized acceptance gate; offline tests do not prove cloud-side role policy.
5. Documentation of accepted variable names, trusted-launcher ownership, expected identity/project, rotation/revocation responsibility, and safe operator setup without secret values. Do not add actual values, secret hashes, or an alternate protected-file layout.

Retain all other parent-task tests and acceptance obligations, including disabled-by-default behavior, fail-closed startup, no Python/backend/legacy fallback, fixed endpoint/destination controls, read-only operations, audited outcomes, bounded responses, and manual-only execution.

## 4. Scope exclusions

This amendment does not authorize: admin/elevated/service-account credentials; changing the project or domain; accepting system-wide or application-credential/token auth; using environment values to select authorization policy, resources, service endpoints, regions, proxy, budgets, or audit paths; a Go dotenv loader or use of profile files as an authentication source/fallback; modifying `.env` or `.env.example`; inspecting `.env` values; provisioning or rotating credentials; editing Python/Ansible/legacy contracts; activating MCP, agent loops, deployment, or live cloud access; adding dependencies/infrastructure; or starting any implementation chunk.

## 5. Requirement traceability

| Requirement family | Preserved behavior / added verification |
| --- | --- |
| FR-009/010/022; NFR-001/002/005/006 | Dedicated reader identity and fixed project remain mandatory; reject missing/wrong principal/project/privilege; no fallback; live effective-policy gate remains required. |
| FR-023/028; NFR-002/014 | Only allowlisted process variables supply auth inputs; reject unsupported modes; no dotenv/profile-credential auth source; zero auth on pre-auth rejection and zero resource reads on post-auth identity/scope mismatch. |
| FR-029/033; NFR-001/012; AC-014/015/017 | Secret canaries never appear in outputs, audit, errors, reports, model input, or child environment. |
| FR-024/035; NFR-010; AC-012/019/024 | No legacy profile/runtime changes; Go refuses to rely on incompatible legacy execution evidence. |
| FR-041 and existing live acceptance criteria | Offline tests use synthetic inputs and fake transports; real effective permissions remain a separately gated live acceptance obligation. |

## 6. Decision authority

**Authorized implementation discretion after exact-candidate commitment, independent review, fresh preflight, and separate named-chunk authorization:** choose explicit Gophercloud option construction versus a rigorously constrained pinned helper; test seams and internal package organization; precise validation/error types, provided errors contain no credential values and outcomes fail closed.

**Requires a new human decision:** changing the dedicated identity, project/domain, role or privilege; accepting a different authentication mode or environment source; using a dotenv/profile file as an authentication source/fallback; deriving authorization policy or service destinations from ambient environment; weakening child-process isolation, audit, TLS, destination, or read-only controls; adding external dependencies/infrastructure; modifying the PRD or legacy contracts; provisioning/using live credentials; or expanding beyond Delivery 1.

## 7. Completion gate

This amendment is documentation only and creates no implementation authorization. The user explicitly approved the current environment-auth direction and requested this candidate be committed; the exact decision and source fingerprints are recorded in [the U4 approval record](../delivery/02-go-environment-auth-approval-record.md). A separate fresh agent session must independently review the committed amendment pair and sole ladder. If that review requests material changes, do not edit or approve them in the reviewer session; obtain affected authoring/review/approval and commit the revised exact candidate. Then perform fresh preflight against the reviewed committed sources. Until review and preflight pass and implementation is separately authorized, stop before code.

**End of draft Go authentication environment task amendment.**
