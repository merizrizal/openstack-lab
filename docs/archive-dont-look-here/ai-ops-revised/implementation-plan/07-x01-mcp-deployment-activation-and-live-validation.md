# 07-X01. MCP Deployment, Activation, and Live Validation

## 07-X01.1 Relationship to Phase 07

This plan extends [`07-mcp-interface.md`](07-mcp-interface.md). It closes the operational gap between the accepted Phase 07 source/static/fixture boundary and an explicitly authorized MCP deployment on `assistant02`.

The extension preserves two distinct modes:

1. **Local stdio baseline:** an owner-managed client launches one adapter process on `assistant02`; there is no service or listener.
2. **Authenticated internal-network Option B:** a systemd-managed MCP service binds only to `192.168.121.21:8443` and accepts approved mTLS clients from `192.168.121.0/24`.

Local stdio is deployed and smoke-tested first. Option B may proceed only after local runner equivalence is preserved and its separate SDK, TLS, authentication, firewall, activation, and rollback gates pass.

This plan is not deployment authority. Package acquisition, host contact, credential or certificate handling, firewall changes, process startup, live runner/OpenStack calls, audit inspection, and rollback each require their documented approval.

Authoritative contracts:

- [`07-mcp-interface.md`](07-mcp-interface.md)
- [`ads/07-00-mcp-interface-steps-01-to-04-ads.md`](ads/07-00-mcp-interface-steps-01-to-04-ads.md)
- [`ads/07-01-internal-network-mcp-extension-ads.md`](ads/07-01-internal-network-mcp-extension-ads.md)
- [`ads/07-02-mcp-interface-steps-05-to-07-ads.md`](ads/07-02-mcp-interface-steps-05-to-07-ads.md)
- [`../runtime/mcp-interface-steps-01-to-04-operations-contract.md`](../runtime/mcp-interface-steps-01-to-04-operations-contract.md)
- [`../runtime/mcp-interface-steps-05-to-07-operations-contract.md`](../runtime/mcp-interface-steps-05-to-07-operations-contract.md)
- [`../runtime/mcp-interface-internal-network-operations-contract.md`](../runtime/mcp-interface-internal-network-operations-contract.md)

## 07-X01.2 Goal

Deploy the revised MCP artifacts to `assistant02`, prove the local-stdio baseline through a client-owned process, then safely activate and validate the authenticated internal-network MCP service without adding authority or weakening the revised runner boundary.

Target outcome:

```text
approved dependency and security prerequisites
  -> local-stdio artifacts deployed to assistant02
  -> client-owned local MCP process passes bounded smoke tests
  -> Option B artifacts and service unit deployed disabled
  -> TLS, source scope, firewall, ownership, and no-listener preflight pass
  -> separately approved activation starts one hardened service
  -> authenticated client discovers and calls only approved diagnostics
  -> result, redaction, audit-correlation, cancellation, and negative-capability checks pass
  -> disablement and rollback preserve the manual/local runner workflow
```

## 07-X01.3 Estimate

Total estimate:

```text
6-9 engineer-days
36-54 focused hours
```

The estimate excludes waiting for dependency provenance approval, offline artifacts, certificates, client credentials, firewall-owner action, host access, or operational authorization.

## 07-X01.4 Current Baseline

Observed repository state at plan creation:

- Phase 07 source, fixture tests, static acceptance, and default-disabled deployment metadata exist.
- `playbook_deploy_mcp_stdio.yml` and `playbook_deploy_mcp.yml` are restricted to `ai_ops_assistant`/`assistant02` and currently pass disabled role variables.
- The local-stdio role can materialize reviewed artifacts when enabled, but it does not currently materialize a complete approved SDK environment or register/start a client.
- The Option B role can materialize source/configuration and a disabled systemd unit, but it deliberately leaves the service stopped and disabled.
- Option B `create_application()` still rejects activation, and `main()` does not construct or run the listener.
- The required hash-locked `requirements.lock` files and approved offline dependency closure are absent for both modes.
- No repository evidence proves MCP artifacts, dependency environments, TLS material, firewall state, client registration, service activation, live MCP calls, or rollback on `assistant02`.

These facts are implementation inputs, not accepted deployment evidence.

## 07-X01.5 Scope

Included:

* Close the official MCP SDK `1.28.1` dependency supply chain for the actual `assistant02` Python runtime.
* Preserve default-disabled behavior while adding explicit, auditable deployment and activation gates.
* Materialize and verify the dedicated local-stdio environment and artifacts on `assistant02`.
* Run bounded local-stdio protocol, discovery, resource, prompt, and tool-call smoke tests without permanent external-client registration.
* Complete the Option B application startup path, mTLS authentication, principal mapping, request limits, session lifecycle, and listener startup.
* Materialize externally issued TLS/CA/CRL inputs through a protected owner-controlled path without storing secrets in Git.
* Apply or verify the exact Vagrant-owned marker-scoped firewall rule.
* Deploy Option B artifacts and the systemd unit in a stopped/disabled state before activation.
* Activate only through a separate approval-bearing operation after all preflight checks pass.
* Validate authenticated positive workflows, unauthenticated/unauthorized denial, schema equivalence, result semantics, audit correlation, cancellation, process health, and listener scope.
* Prove disablement, rollback, idempotent redeployment, and preservation of the manual/local runner workflow.
* Reconcile Phase 07 documentation only from retained normalized evidence.

Excluded:

* Public, wildcard, unauthenticated, plaintext, IPv6, NAT-forwarded, or internet-facing MCP exposure.
* Generic shell, SSH, sudo, OpenStack passthrough, file, database, package, service-control, or remediation capabilities.
* Provider/model integration, external AI-client implementation, or permanent external-client registration.
* Generating a CA, server key, client key, or credentials in this repository or ordinary automation logs.
* Runtime downloads from public package indexes.
* Reuse of the historical MCP bridge, orchestrator, provider gateway, egress stack, client registration, or runtime paths.
* Activation before the accepted runner, diagnostics, identity profile, dependency closure, TLS material, firewall scope, and rollback path are verified.
* Raw audit export or secret-bearing evidence retention.

## 07-X01.6 Assumptions and Entry Gates

- [ ] The exact target remains `assistant02` in `ai_ops_assistant`, with `--limit assistant02` required for every host operation.
- [ ] The revised runner, initial three diagnostics, identity profile, audit path, and manual workflow are deployed and accepted at the revisions used by MCP.
- [ ] The owner confirms local stdio first and Option B second as the activation order.
- [ ] The approved Python interpreter and host Python ABI are recorded before generating dependency locks.
- [ ] Complete hash-pinned dependency locks and approved offline wheels exist for each deployed MCP environment.
- [ ] Dependency license, provenance, hashes, transitive closure, and offline source are independently approved.
- [ ] The local smoke-test client owner and outcome-only evidence procedure are approved.
- [ ] The externally managed CA provides the server certificate/key, client CA bundle, current CRL, and one bounded test-client identity through protected channels.
- [ ] The Option B approval reference and owner authorization are current for dependency handling, TLS materialization, firewall change, deployment, activation, live validation, evidence inspection, disablement, and rollback.
- [ ] The Vagrant/firewall owner confirms the exact marker-scoped rule and removal procedure.
- [ ] The test client originates only from the approved source range and validates the server identity without disabling certificate checks.
- [ ] A rollback owner and stop authority are present during activation and live testing.

Any unchecked prerequisite that is required by the current step is a stop condition, not permission to bypass the gate.

## 07-X01.7 Ordered Tasks

### Step 1 - Freeze Deployment Mode, Authority, and Evidence Contract

Estimate:

```text
0.5 engineer-days
3 focused hours
```

Tasks:

- [ ] Confirm the primary live target is Option B and that local stdio is the prerequisite baseline, not a long-running service.
- [ ] Record exact owners and approval references for dependency artifacts, TLS/CRL material, Vagrant firewall state, `assistant02`, test-client credentials, live runner calls, normalized audit evidence, and rollback.
- [ ] Freeze the approved Python version/ABI, MCP SDK version, runtime paths, service identity, bind address/port, source CIDR, endpoint, and principal URI.
- [ ] Define allowed evidence fields, protected evidence location, retention, deletion, and prohibition on raw payload/credential capture.
- [ ] Define stop authority and rollback initiation criteria before any live operation.
- [ ] Decide the exact non-secret activation control consumed by the adapter and systemd unit; preserve false defaults and prohibit source-level always-on constants.

Done when:

- [ ] Reviewers can identify who may authorize each side effect, what exact target is affected, what evidence may be retained, and how activation remains fail-closed by default.

### Step 2 - Close the MCP SDK and Runtime Supply Chain

Estimate:

```text
0.75-1.25 engineer-days
4.5-7.5 focused hours
```

Tasks:

- [ ] Generate complete `mcp==1.28.1` transitive locks for the approved `assistant02` Python ABI from an approved internal index or offline wheel source.
- [ ] Require exact versions and hashes for every transitive package; reject editable, URL, VCS, unpinned, unhashed, extra, or historical-orchestrator dependencies.
- [ ] Acquire or build the approved offline wheel closure outside runtime deployment and record normalized provenance/hash evidence.
- [ ] Verify all lock entries resolve from the approved offline artifact set with network access disabled.
- [ ] Scan package names and dependency paths for excluded provider, model, SSH, database, orchestration, and generic-execution capabilities.
- [ ] Define deterministic dedicated venv creation, ownership, modes, upgrade, integrity validation, and exact removal behavior for local stdio and Option B.
- [ ] Add fail-closed acceptance for missing, extra, stale, unsafe, symlinked, incorrectly owned, or hash-mismatched dependency inputs.

Done when:

- [ ] Both MCP modes can create reproducible dedicated environments from approved offline artifacts without contacting a public package source.

### Step 3 - Add Guarded Local-stdio Deployment and Smoke Validation

Estimate:

```text
0.75-1.25 engineer-days
4.5-7.5 focused hours
```

Tasks:

- [ ] Keep local-stdio role defaults disabled and require an explicit run-scoped deployment approval rather than committing always-enabled defaults.
- [ ] Extend the role to materialize and verify the dedicated venv from the approved lock/wheel closure without starting a service or listener.
- [ ] Verify exact artifact paths, regular-file/non-symlink status, root-controlled ownership, group-readable modes, hashes, and configuration.
- [ ] Add a non-registering smoke-test harness that launches the adapter as `aiops_assistant`, reserves stdout for MCP protocol, closes stdin cleanly, and reaps the process.
- [ ] Validate initialization, exact three-tool discovery, six resources, three prompts, valid project summary, same-identifier server inspection, invalid arguments, absent generic/remediation capabilities, cancellation, timeout, and process cleanup.
- [ ] Verify one equivalent local runner request and MCP request preserve status, bounded data/error fields, exit semantics, duration, timestamp, truncation, correlation ID, redaction, and one runner-owned audit event.
- [ ] Retain only normalized outcomes and immediately remove transient client inputs.

Done when:

- [ ] A client-owned local-stdio process works on `assistant02` without a listener, persistent registration, broader authority, orphan process, or duplicate audit path.

### Step 4 - Complete the Option B Authenticated Server Startup Path

Estimate:

```text
1-1.5 engineer-days
6-9 focused hours
```

Tasks:

- [ ] Replace the current unconditional activation rejection with a guarded application-construction path that requires both enabled state and explicit activation evidence.
- [ ] Wire the accepted low-level MCP server, Streamable HTTP transport/session manager, Starlette lifespan, fixed `/mcp` route, and one Uvicorn worker.
- [ ] Build TLS 1.3 server context from fixed protected paths; require client certificates, the closed client CA, and current CRL validation.
- [ ] Map only `spiffe://openstack-lab/mcp/mcp-internal-reader` to the fixed `mcp-internal-reader` principal after successful certificate validation.
- [ ] Enforce exact interface/address/port, source CIDR, Host, Origin, method, body/response bounds, rate, burst, session, request deadline, and concurrency limits before runner invocation.
- [ ] Preserve the exact three-tool and six-resource allowlists; keep prompts absent from Option B unless separately approved.
- [ ] Preserve fixed runner argv, one child maximum, no shell, no request retry, one runner-owned audit event, bounded/sanitized network events, and no raw exception or payload logging.
- [ ] Implement graceful shutdown that stops accepting requests, cancels/reaps children, closes sessions, and exits within the systemd deadline.
- [ ] Keep startup fail-closed for absent activation evidence, unsafe TLS/CRL, wrong bind state, schema drift, missing runner prerequisites, or unknown principal policy.

Done when:

- [ ] Local tests can construct and run the authenticated application against injected fixtures while proving no unauthorized request can reach the runner.

### Step 5 - Add Separate Deployment, Activation, Validation, and Disablement Automation

Estimate:

```text
1-1.5 engineer-days
6-9 focused hours
```

Tasks:

- [ ] Preserve `playbook_deploy_mcp.yml` as an artifact/venv/unit deployment that leaves the service stopped and disabled.
- [ ] Add preflight checks for exact target/limit, accepted runner revisions, dependency hashes, protected TLS file metadata, CRL freshness, interface/address ownership, port absence, firewall evidence, service state, and rollback readiness.
- [ ] Materialize TLS inputs only from the approved protected source; never print, copy to ordinary evidence, or retain client private keys.
- [ ] Integrate the exact Vagrant-owned firewall marker through its owning automation or consume independently verified marker evidence; do not add ad hoc host firewall commands.
- [ ] Add a separate activation entrypoint requiring exact approval reference, explicit activation confirmation, successful current-run preflight, and `assistant02` scope.
- [ ] Render activation state through a root-controlled non-secret unit/drop-in or equivalent fixed contract while keeping repository defaults false.
- [ ] Start and enable only `ai-ops-assistant-mcp`; verify the exact PID/user/group, unit hardening, bind address, port, and absence of alternate listeners.
- [ ] Add a validation entrypoint that reports normalized state without exposing certificates, client identity details, tool payloads, credentials, raw audits, or topology beyond the approved contract.
- [ ] Add separate disablement and exact-artifact rollback entrypoints with independent authorization, check mode, ownership guards, and shared-runtime preservation.
- [ ] Add static tests proving deployment cannot activate, activation cannot broaden scope, and rollback cannot remove runner, diagnostic, credential, audit, evidence, local-stdio, or historical-runtime artifacts.

Done when:

- [ ] Deployment, activation, validation, disablement, and rollback are distinct fail-closed operations with exact scope, approval, evidence, and idempotency contracts.

### Step 6 - Pass Local and Non-Activating Acceptance

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 focused hours
```

Tasks:

- [ ] Run Python compilation and focused local-stdio/Option B unit and fixture suites in the approved Python environment.
- [ ] Run static negative-capability, secret-canary, dependency-closure, service-hardening, deployment-scope, and rollback-scope tests.
- [ ] Run YAML, shell, JSON, Ansible syntax, and check-mode validation for every changed deployment/activation artifact.
- [ ] Prove tests do not open a real listener, contact OpenStack, use live credentials, inspect raw audits, mutate firewall state, or contact `assistant02` unless separately authorized.
- [ ] Reconcile source, tests, service unit, playbooks, ADS, operations contracts, and this plan before any host deployment.

Representative non-live validation shape:

```bash
rtk <approved-python-venv>/bin/python -m unittest discover \
  -s ansible/ai_ops_assistant/tests/mcp_stdio -p 'test_*.py'
rtk <approved-python-venv>/bin/python -m unittest discover \
  -s ansible/ai_ops_assistant/tests/mcp -p 'test_*.py'
rtk ansible-playbook --syntax-check \
  -i ansible/ai_ops_assistant/inventories/local/local.yml \
  ansible/ai_ops_assistant/<mcp-playbook>.yml \
  --limit assistant02
rtk git diff --check
```

Done when:

- [ ] All local/static checks pass and reviewers confirm the next operation is a bounded deployment, not an implicit activation.

### Step 7 - Deploy and Validate Local Stdio on `assistant02`

Estimate:

```text
0.5 engineer-days
3 focused hours
```

Tasks:

- [ ] Obtain separate authorization for SSH/Ansible contact, offline artifact handling, local artifact deployment, process smoke testing, runner calls, and normalized evidence.
- [ ] Run approved preflight/check mode with the repository inventory and exact `--limit assistant02`.
- [ ] Deploy the local-stdio venv and artifacts with explicit run-scoped enablement.
- [ ] Verify artifact hashes, ownership/modes, Python/SDK version, runner prerequisites, no listener, and no persistent adapter process before testing.
- [ ] Run the bounded client-owned smoke matrix from Step 3.
- [ ] Close the client session and prove adapter/runner child absence, no listener, manual runner availability, and no unrelated changes.
- [ ] Repeat the deployment to prove idempotency and retain only normalized outcome evidence.

Done when:

- [ ] Local stdio is demonstrably usable on `assistant02` and remains independently disableable without changing lab state.

### Step 8 - Deploy Disabled Option B Artifacts and Run Activation Preflight

Estimate:

```text
0.5 engineer-days
3 focused hours
```

Tasks:

- [ ] Obtain separate authorization for protected TLS materialization, firewall-owner action, artifact deployment, and host validation.
- [ ] Apply or verify the exact marker-scoped Vagrant rule only after dependency and TLS gates pass.
- [ ] Deploy the Option B venv, adapter, catalog, configuration, TLS inputs, and systemd unit with the service stopped and disabled.
- [ ] Verify hashes, ownership/modes, no symlinks, systemd hardening, fixed configuration, certificate purpose/identity/validity, CRL freshness, interface ownership, and exact firewall scope.
- [ ] Prove no process or listener exists on port `8443` before activation.
- [ ] Repeat disabled deployment to prove idempotency and record a normalized activation-readiness result.

Done when:

- [ ] All Option B artifacts and prerequisites are verified on `assistant02`, while the service remains stopped, disabled, and unreachable.

### Step 9 - Activate and Run Bounded Live MCP Acceptance

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 focused hours
```

Tasks:

- [ ] Reconfirm the current-run activation approval, rollback owner, exact client source, current CRL, no unexpected listener, and accepted deployed revisions.
- [ ] Activate only `ai-ops-assistant-mcp` through the guarded activation entrypoint.
- [ ] Verify one process runs as `aiops_assistant`, one listener binds only to `192.168.121.21:8443`, the service is hardened, and no wildcard/IPv6/alternate listener exists.
- [ ] Prove plaintext, missing-certificate, invalid-certificate, revoked-certificate, unknown-principal, wrong-source, wrong-Host/Origin/method, oversized, rate-limited, unknown-tool, invalid-argument, and generic/remediation requests fail before runner execution.
- [ ] From the approved mTLS client, validate initialization, exact tool/resource discovery, one project summary, and one same-identifier server basic/network workflow.
- [ ] Compare live MCP results with equivalent accepted runner results for status, bounds, redaction, timestamp, duration, truncation, correlation, and audit behavior.
- [ ] Validate cancellation, timeout, disconnect, service restart, and graceful stop without orphan sessions or runner children.
- [ ] Retain only normalized outcomes; do not capture raw tool payloads, credentials, certificates, private keys, or raw audits.

Done when:

- [ ] The authenticated internal MCP endpoint is reachable only through the approved path and exposes exactly the accepted read-only capability with equivalent runner safety semantics.

### Step 10 - Prove Disablement, Rollback, Recovery, and Documentation Closure

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 focused hours
```

Tasks:

- [ ] Disable client access, remove the marker-owned firewall ingress, then stop and disable the Option B service in the documented order.
- [ ] Verify no listener, MCP process, runner child, orphan session, or restart loop remains.
- [ ] Verify local stdio and the manual/local runner remain available unless an accepted safety issue explicitly requires their disablement.
- [ ] Under separate rollback authorization, remove only Option B artifacts, dedicated venv, unit/drop-in, configuration, and protected server-side TLS artifacts owned by this deployment.
- [ ] Preserve shared runner, diagnostics, credentials, audit/evidence paths, local-stdio artifacts, Option B-independent firewall state, and historical runtime.
- [ ] Re-deploy disabled Option B artifacts to prove deterministic recovery, then leave the final enabled/disabled state explicitly owner-decided and recorded.
- [ ] Reconcile Phase 07 assumptions, Step 7, Phase Definition of Done, execution-order documentation, and runtime contracts strictly from accepted evidence.
- [ ] Record unresolved external-client registration or long-term operations gaps without converting test-client evidence into production-client acceptance.

Done when:

- [ ] Disablement and rollback are independently evidenced, shared workflows remain safe, and every Phase 07 completion claim matches observed deployed behavior.

## 07-X01.8 Recommended Implementation Ladder

Use compile-safe chunks and stop after each chunk for review:

1. **Chunk 0 — Decision and dependency gate:** freeze approvals, Python ABI, lock/wheel source, activation control, evidence, and rollback ownership.
2. **Chunk 1 — Offline runtime closure:** add locks, artifact validation, deterministic venv behavior, and fail-closed tests.
3. **Chunk 2 — Local-stdio deployment seam:** add guarded venv/artifact deployment and a non-registering smoke harness.
4. **Chunk 3 — Option B application activation seam:** complete authenticated application construction and fixture-driven startup/shutdown behavior.
5. **Chunk 4 — Deployment lifecycle automation:** separate disabled deployment, activation, validation, disablement, and rollback entrypoints.
6. **Chunk 5 — Local/static acceptance:** run all non-live checks and reconcile contracts.
7. **Chunk 6 — Authorized local-stdio deployment:** deploy and smoke-test only the local baseline on `assistant02`.
8. **Chunk 7 — Authorized disabled Option B deployment:** materialize prerequisites and prove activation readiness without a listener.
9. **Chunk 8 — Authorized activation and live acceptance:** activate, test the bounded matrix, then disable.
10. **Chunk 9 — Rollback/recovery and closure:** prove rollback, restore the owner-selected final state, and reconcile documentation.

Chunks 6-9 are operational chunks and require explicit authorization immediately before execution. Completion of an earlier chunk does not authorize the next one.

## 07-X01.9 Phase Definition of Done

This extension is done when:

- [ ] Approved hash-locked offline MCP dependency closures are reproducible for the deployed Python runtime.
- [ ] Local stdio is deployed and passes bounded client-owned live validation on `assistant02` without a listener or persistent registration.
- [ ] Option B artifacts, dedicated venv, TLS inputs, configuration, and unit deploy idempotently in a stopped/disabled state.
- [ ] Option B activation requires separate current approval and cannot result from ordinary deployment or repository defaults.
- [ ] The service binds only to `192.168.121.21:8443`, accepts only approved mTLS/source/principal requests, and has no public, wildcard, plaintext, or unauthenticated path.
- [ ] Discovery exposes exactly the approved tools/resources for each mode and no generic or remediation capability.
- [ ] Live calls preserve runner validation, limits, result, redaction, correlation, and audit semantics without a second execution or audit path.
- [ ] Negative, timeout, cancellation, disconnect, restart, and shutdown checks leave no orphan process or widened authority.
- [ ] Deployment, activation, validation, disablement, rollback, and recovery are separately gated, observable, idempotent where applicable, and independently evidenced.
- [ ] Disablement and rollback preserve the accepted manual/local runner and unrelated revised/historical runtime state.
- [ ] Phase 07 checkboxes and operations contracts are reconciled only from accepted normalized evidence.

## 07-X01.10 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Changing defaults to true makes deployment an implicit activation | Keep repository defaults false; use a separate approval-bearing activation operation and root-controlled runtime activation state. |
| Missing or incompatible SDK closure causes unsafe runtime package acquisition | Require complete hashes, approved offline wheels, ABI matching, and network-disabled installation tests before host deployment. |
| The current Option B skeleton is mistaken for an activatable server | Require application startup/authentication completion and fixture acceptance before any service start. |
| TLS material or client keys leak through Git, chat, Ansible output, or evidence | Use protected owner-controlled inputs, `no_log` where required, metadata-only checks, and prohibit client private-key retention on `assistant02`. |
| Listener binds publicly, to the wrong interface, or over plaintext | Assert exact interface/address/port, TLS 1.3, mTLS, source CIDR, no wildcard/IPv6, and inspect listeners immediately after activation. |
| Firewall automation changes unrelated policy | Use only the Vagrant-owned marker-scoped rule with independent pre/post evidence and exact marker removal. |
| MCP authentication succeeds but authorization or runner boundaries drift | Map one fixed certificate URI, preserve exact tool/resource allowlists, delegate to fixed runner argv, and run equivalence/negative tests. |
| Activation produces duplicate audits or sensitive network logs | Keep the runner as sole tool-audit writer and constrain network events to normalized bounded fields. |
| Cancellation, restart, or failure leaves runner children or sessions | Enforce one child, process-group reaping, bounded shutdown, systemd checks, and post-test process/listener absence. |
| Rollback removes shared runner, credentials, audit, or historical runtime | Use exact ownership manifests, independent rollback approval, path guards, and shared-state preservation tests. |
| Test-client success is overstated as production external-client readiness | Label evidence as bounded test-client acceptance; keep permanent external-client implementation/registration separately owned. |
| Live testing changes OpenStack or host state | Expose only accepted read-only diagnostics, run explicit negative-capability checks, and stop on any unexpected mutation. |
