# 03. Manual Diagnostic Toolbox

## 03.1 Goal

Deliver a small, inspectable, manually runnable toolbox for project inventory, server state, and server networking, with stable output contracts and static read-only safety checks.

Target outcome:

```text
reviewed safety contract -> three narrow diagnostics -> validated structured output -> manual deployed-lab evidence -> no mutation primitives
```

## 03.2 Estimate

Total estimate:

```text
2.5-4 engineer-days
15-24 focused hours
```

## 03.3 Scope

Included:

* Define diagnostic implementation and output conventions.
* Start from copied project-resource, server-basic, and server-network tools where available, preserving unchanged behavior that already satisfies the revised contract.
* Modify only the revised copies where the gap map identifies a required contract or isolation change.
* Validate user-supplied identifiers.
* Prefer JSON OpenStack output and stable sectioned envelopes.
* Add static forbidden-operation, syntax, parameter, and output-shape tests.
* Validate tools manually with project-reader credentials.

Excluded:

* Generic OpenStack, shell, SSH, sudo, or file access.
* Neutron-agent and host-log diagnostics.
* Tool-runner automation.
* MCP integration.
* Full SDK migration when simple reviewed scripts meet the contract.

## 03.4 Assumptions

- [ ] The fresh revised project-reader profile and its tested read matrix are available.
- [ ] Copied diagnostic implementations are located only in the revised namespace; the prior scripts remain unchanged.
- [ ] Shell scripts are acceptable for simple learning-oriented tools when they remain inspectable and testable.
- [ ] Python/OpenStack SDK may be used where it materially improves structured behavior without enlarging authority.
- [ ] Server names and IDs can use a deliberately narrow validation pattern.

## 03.5 Ordered Tasks

### Step 1 - Define Toolbox Contracts and Safety Rules

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Compare each copied diagnostic with the revised contract and record whether no code change is needed or which exact gap requires modification.
- [ ] Define revised diagnostic names, intent, credential profile, parameters, output shape, expected errors, and mutation guarantee without colliding with prior runtime registrations.
- [ ] Ban create, update, delete, start, stop, restart, install, edit, redirect-write, eval, generic shell, generic SSH, unrestricted sudo, database access, and raw OpenStack passthrough.
- [ ] Require strict input validation before every external invocation.
- [ ] Require bounded output and explicit unavailable behavior for unsupported policy or services.
- [ ] Define redaction rules for secret-like keys and prohibit full secret-bearing configuration output.

Done when:

- [ ] Reviewers can assess a diagnostic against one documented safety and output contract.

### Step 2 - Add Shared Validation and Output Helpers

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Add reusable validation for server names/IDs and other MVP identifiers.
- [ ] Reject empty values, shell metacharacters, control characters, path traversal, and overlong input.
- [ ] Add common project-reader profile selection without exposing secret values.
- [ ] Add consistent status, error, and exit-code conventions for manual execution.
- [ ] Add JSON or section helpers that preserve raw service errors without confusing them with successful empty results.

Done when:

- [ ] New diagnostics share tested validation and output behavior rather than duplicating command construction.

### Step 3 - Implement Project Resource Summary

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] List project-visible servers, networks, subnets, ports, volumes, images, and security groups using read-only operations.
- [ ] Emit JSON for each supported resource class or a stable sectioned aggregate.
- [ ] Report policy-blocked or unavailable sections explicitly without failing open.
- [ ] Keep output concise through selected fields or documented limits where resource counts are large.
- [ ] Capture a redacted representative result and verify no credential material is present.

Done when:

- [ ] An operator can answer “what exists in this project?” with one reviewed diagnostic.

### Step 4 - Implement Server Basic Information

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [ ] Accept exactly one validated server name or ID.
- [ ] Return status, image, flavor, addresses, availability zone, config-drive state, and other safe boot context available from the API.
- [ ] Preserve distinct not-found, ambiguous-name, permission-denied, endpoint, and authentication outcomes.
- [ ] Verify success for a representative server and rejection for malformed input.
- [ ] Verify the implementation cannot append arbitrary OpenStack arguments.

Done when:

- [ ] An operator can inspect one server’s basic state without raw CLI access.

### Step 5 - Implement Server Network Information

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Accept the same validated server identifier contract.
- [ ] Return attached ports, fixed IPs, network IDs, subnet context, and relevant port metadata through read-only operations.
- [ ] Resolve related network/subnet information only where policy permits and report unavailable detail explicitly.
- [ ] Keep the data useful for metadata-path diagnosis without exposing unrelated project data.
- [ ] Verify expected behavior for a server with multiple ports and for not-found input.

Done when:

- [ ] An operator can identify the server’s network attachment path and metadata-relevant context.

### Step 6 - Add Static and Behavioral Safety Tests

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Scan diagnostic implementations for forbidden mutation and generic-execution patterns.
- [ ] Run language-appropriate syntax and lint checks.
- [ ] Test empty, malformed, overlong, metacharacter, and path-like parameters.
- [ ] Test successful output shape, service error preservation, and unavailable sections with controlled fixtures.
- [ ] Test that only the project-reader profile is selected for initial tools.
- [ ] Document any static-check false-positive review process without allowing blanket suppression.

Done when:

- [ ] The initial toolbox passes automated safety, syntax, input, and output-contract checks.

### Step 7 - Validate Manual Use Against the Lab

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Run all three diagnostics from the assistant runtime against representative project state.
- [ ] Verify no resource state changes before and after execution.
- [ ] Confirm outputs are concise, parseable, and useful to both an operator and an AI assistant.
- [ ] Record policy/version-specific unavailable fields and accepted limitations.
- [ ] Retain only redacted evidence and remove raw output when it is no longer needed.

Done when:

- [ ] The three diagnostics are trusted manually before any wrapper or MCP integration.

## 03.6 Phase Definition of Done

This phase is done when:

- [ ] Project resource summary, server basic info, and server network info exist and run manually.
- [ ] Every tool validates inputs and uses project-reader by default.
- [ ] Outputs are structured, bounded, and distinguish findings from execution failures.
- [ ] Static checks find no mutation or generic execution capability.
- [ ] Automated tests cover unsafe inputs and output contracts.
- [ ] Deployed-lab evidence confirms useful reads and unchanged cloud state.

## 03.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Simple scripts become unsafe command builders | Centralize strict validation and prohibit pass-through arguments. |
| CLI JSON varies by OpenStack release | Preserve raw structured fields, test deployed behavior, and use SDK code only where needed. |
| Output leaks excessive topology or secrets | Scope fields, bound output, redact secret-like values, and retain only reviewed samples. |
| Copied historical scripts differ from revised contracts | Modify only the revised copies for documented gaps and rerun all revised tests; never patch the prior scripts in place. |
| Copied tools accidentally call prior runtime paths or profiles | Test revised implementation roots, profile names, and runtime paths explicitly. |
| Project policy blocks useful expansion | Report unavailable data and defer broader scope to Phase 06. |
