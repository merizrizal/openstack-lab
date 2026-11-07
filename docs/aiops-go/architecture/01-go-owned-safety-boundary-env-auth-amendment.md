# Delivery 1 — Go Authentication Environment Amendment

**Status:** Owner-approved Go environment-auth decision; specification candidate committed for independent review. Independent review and fresh preflight remain required before implementation; this document grants no code authorization.

**Scope:** The Go-owned Delivery 1 diagnostic path only. This amendment changes the Go authentication-input source and supersedes only the credential-source clauses identified below. It does not amend the legacy/revised Python runtime contracts.

**Repository base:** `16cfe0ede231df7b90b4f93961a7b6eff16512a1`, branch `aiops-go-phase01`; worktree was clean when this amendment was prepared.

**Amends:** [Go-owned ADR](01-go-owned-safety-boundary-adr.md), committed blob `58e8c4e2c9c2c92fb341a3b8693a49a09671efb9`; [Go-owned task](../tasks/01-go-owned-safety-boundary-task.md), committed blob `ab3dda9b0dfaa4b8e00b389a8485a0b5d1621e8f835039d1291af951ab639dbb`; and the sole [Delivery 1 ladder](../delivery/01-safety-boundary-and-manual-slice-delivery.md), committed blob `711a26dc1a5242b0c9e254fee4028b4d2aa065838d006a40fc1ecb7dcd6dd7cb`. The accepted originals and prior approval record remain unchanged. Owner approval and commitment of this candidate are recorded in the U4 approval record; independent review and fresh preflight remain required.

## 1. Decision provenance

`U4` is the user's decision in this conversation:

- “For aiops in Go language, I prefer to use environment variable only. I approved for the architecture changes.”
- In confirmation of the bounded interpretation—process environment supplied by a trusted launcher, OpenStack authentication inputs only, no Go `.env` loader, and preservation of the dedicated reader identity, fixed-project verification, and no fallback—the user replied: “Yes, I confirm that.”

This approves the Go-specific environment-authentication design for Delivery 1 and authorizes commitment of this documentation candidate. It does not authorize implementation, `.env` value inspection or loading, credential provisioning, wider privileges, changes to the PRD, or changes to legacy runtimes. No timestamp, signature, or external transcript is inferred.

## 2. Approved decision and narrow boundary

For the new Go manual diagnostic path, OpenStack authentication inputs come only from the Go process environment as supplied by a trusted operator-controlled launcher. Go does not itself search for or load `.env`, and it must not obtain authentication credentials or fall back to them from `clouds.yaml`, `secure.yaml`, or another profile. It does not invoke the root Makefile to obtain environment values. Any separate trusted noncredential policy/configuration source remains governed by the parent ADR/task; U4 neither authorizes a new source nor permits credentials from that source.

Environment inputs are authentication material, not authorization policy. Preserve the approved identity and scope: the fresh `aiops-assistant-project-reader` credential, project label `admin` (not administrator authority), domain `default`, reader-only access, expiry, and OpenStack admin-team rotation/revocation ownership. The authenticated principal and project must be checked against trusted application policy before any resource read. The environment cannot expand tool, target, project-wide, budget, audit-path, or approval authority. Authentication, identity, project, or policy failure has no stronger-credential fallback.

This is a narrow Go-specific exception to profile-based credential loading. The existing revised/Python identity and profile contracts remain unchanged for their own runtimes. This amendment neither authorizes reading nor changing their protected profile files.

## 3. Required engineering constraints

1. Read only a closed, documented set of process variables needed for project-scoped authentication. The observed Gophercloud v2.14.0 helper `openstack.AuthOptionsFromEnv` also reads alternate identity/authentication inputs, including `OS_USERID`, `OS_PASSCODE`, application-credential variables, `OS_SYSTEM_SCOPE`, and deprecated `OS_TENANT_ID`/`OS_TENANT_NAME`. It does not read an `OS_TOKEN` variable; token-based auth is nevertheless outside this contract and must not be introduced. A future implementation may use the helper only if it proves the listed alternatives cannot influence authentication; otherwise it must construct the required options from an explicit allowlist. Unsupported or conflicting selectors fail closed before authentication.
2. The accepted authentication source is the process environment—not a Go dotenv loader or credential profile. Do not read, log, copy, print, or embed local `.env` values. The existing development example is not evidence of the dedicated reader identity and must not be used as a production diagnostic credential source. Any separate noncredential policy/configuration source must satisfy the parent ADR/task and must not supply or override authentication inputs.
3. Authentication endpoint and project-scope inputs must match the approved deployment identity/project. Verify the authenticated project identity before resource requests. Service endpoints, region/interface selection, targets, policy, budgets, capability definitions, audit paths, and approval state are not ambient environment overrides or public request inputs; they remain under the approved trusted configuration/owner boundary.
4. Environment variables must not cause credentials to be sent through proxy settings, redirects, or unapproved endpoint origins. Retain collection-time response-byte bounds and destination validation for authentication and service requests.
5. Credential values never appear in arguments, logs, errors, results, audit, reports, fixtures, or model input. No model or child process receives OpenStack authentication variables. Existing Go Codex/Pi environment filtering is a relevant observed seam, not acceptance evidence; add regression tests that prove the invariant.
6. Do not change identity, role, project, expiry, rotation, audit retention, legacy profile layout, or deployment authority as part of this source change. Live effective-policy acceptance remains separately gated.

For the current Gophercloud API, candidate allowlist fields are the password/project-scoped inputs (`OS_AUTH_URL`, `OS_USERNAME`, `OS_PASSWORD`, one project selector, and the domain selector required by that project form). Exact field mapping and rejection behavior must be verified against the pinned SDK and fixed identity contract before implementation. This candidate allowlist is not permission to accept alternate auth modes or to use environment values as policy.

## 4. Architectural consequences and alternatives

The approved preference removes the existing YAML profile as a Go authentication-credential source; it does not decide how any separate trusted noncredential policy is represented. No dotenv/auth-profile parser or new credential-file layout is proposed. If an existing policy source cannot be used without also loading credentials or adding an unapproved parser/source, stop and raise the specific feasibility decision rather than inventing one. The trusted launch environment is part of the Go authentication boundary. Same-user process inspection and accidental child inheritance are material risks; the no-model manual command, strict child-environment filtering, least-privileged credential, and explicit live acceptance remain necessary controls. Environment sourcing does not prove that a credential is read-only.

Level 1 implementation latitude remains between using the pinned SDK helper behind strict checks and constructing explicit Gophercloud authentication options from the allowed fields. Either choice must prove closed inputs, fixed identity/project, zero authentication for pre-auth rejected/disabled requests, zero resource reads for post-auth identity/scope mismatch, no credential-file fallback, and no secret propagation. A new dotenv/auth-profile parser dependency, credential broker, privilege change, or broader environment-derived policy is outside this decision and requires a separate decision.

## 5. Cross-document fidelity and requirements

| Decision | ADR/task locations | Governing requirements and evidence |
| --- | --- | --- |
| U4: Go process environment is the sole authentication-input source; no Go `.env` loader | This amendment §§2–3; [task amendment](../tasks/01-go-owned-safety-boundary-env-auth-amendment.md) §§2–5 | FR-022/023/041, NFR-002/014; synthetic process-environment fixtures, no Go dotenv or credential-profile auth/fallback |
| Preserve dedicated reader, fixed expected project, no fallback or privilege expansion | This amendment §§2–3; task amendment §§2–6 | FR-009/010/022/028, NFR-001/002/005/006; zero auth on pre-auth denial, zero resource calls on authenticated project mismatch, live policy gate remains deferred |
| No credential disclosure to model/child or any sink | This amendment §3; task amendment §§4–6 | FR-029/033, NFR-001/012, AC-014/015/017; canaries at result/audit/error/model-child boundaries |
| No change to legacy profile/runtime contracts | This amendment §§2–4; task amendment §§1/5/7 | FR-024/035, NFR-010, AC-012/019/024; legacy consumers remain untouched and incompatible Go evidence is rejected |

The Go PRD continues to govern read-only behavior, dedicated project-reader use, least privilege, denial, auditing, and credential isolation. U4 changes the Go credential transport only; it does not revise those product outcomes or authorize admin credentials.

## 6. Approval and implementation gate

The user explicitly approved the environment-auth direction and requested commitment of this candidate. The approval is recorded in [the U4 approval record](../delivery/02-go-environment-auth-approval-record.md); the prior approval record remains unchanged. A separate fresh agent session must independently review this amendment, the task amendment, original ADR/task, current Go PRD, revised sole ladder, and relevant legacy contracts. Until that review and fresh implementation preflight pass, no code may rely on this amendment. Any material review-driven change requires affected review and renewed exact-candidate approval/commit.

**End of draft Go authentication environment amendment.**
