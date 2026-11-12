# 01. Baseline and Runtime Foundation

## 01.1 Goal

Preserve the prior AI-OPS implementation unchanged, classify it as a source catalog, define a fail-closed selective-reuse boundary, and establish only the minimal isolated runtime foundation required for the revised diagnostic → runner → local MCP product path.

Target outcome:

```text
prior source pinned and cataloged -> required capabilities mapped -> unrelated source excluded -> minimal revised runtime and reachability verified
```

## 01.2 Estimate

Total estimate:

```text
2-3.5 engineer-days
12-21 focused hours
```

## 01.3 Scope

Included:

* Inventory the prior AI-OPS automation, diagnostics, runner, MCP, tests, runbooks, and runtime evidence by path and capability.
* Record source provenance and map candidate assets to current revised requirements.
* Create a selective-reuse manifest whose default decision is exclusion.
* Explicitly exclude prior provider, orchestrator, egress, device-auth, wheelhouse, remote-operation, and unrelated host-observer paths from the revised foundation.
* Create minimal namespace-safe inventory, runtime setup, workspace, and tooling automation without copying the prior runtime tree wholesale.
* Decide or confirm revised assistant-runtime placement outside the control plane.
* Establish management endpoint reachability and least-network-access expectations.
* Define configuration ownership, evidence capture, and foundation rollback.

Excluded:

* Creating a complete copy or maintaining path parity with `ansible/ai_ops_runtime/`.
* Copying a whole prior role, playbook family, package, or test suite before its dependency closure and current requirement are reviewed.
* Creating or installing OpenStack credentials.
* Copying live credentials, tokens, private keys, raw audit logs, secret-bearing runtime state, generated artifacts, or unredacted evidence.
* Implementing or activating diagnostics, the runner, MCP, provider gateways, model orchestration, egress, remote bridges, or restricted host access.
* Modifying the prior AI-OPS source tree or deployed runtime in place.
* Local LLM deployment.

## 01.4 Assumptions

- [ ] The prior AI-OPS source and deployed runtime are read-only historical baselines during revised implementation.
- [ ] Git revision and path-level provenance are sufficient to preserve historical traceability; duplicate source-tree parity is not required.
- [ ] A prior asset enters the revised namespace only when an owning phase maps it to a current requirement, reviews its dependency closure, and defines independent acceptance checks.
- [ ] Absence from the selective-reuse manifest means excluded.
- [ ] Runtime secrets and operational state are created fresh rather than copied.
- [ ] The revised runtime is a separate VM or equivalent observer host, not a controller, compute, storage, Ceph, database, message-bus, observability node, or prior assistant runtime.
- [ ] Management-network reachability is sufficient for initial API diagnostics; tenant-network placement is not required.
- [ ] The runtime is initially a connector/tool host and does not need an LLM, runner, or MCP process in this phase.

## 01.5 Ordered Tasks

### Step 1 - Pin and Catalog the Prior AI-OPS Source

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [x] Record the accepted prior source revision and prior runtime tree identity. ([catalog](../runtime/source-capability-catalog.md#fixed-provenance))
- [x] Inventory tracked prior paths by capability without traversing caches or reading protected runtime material. ([catalog](../runtime/source-capability-catalog.md#capability-catalog))
- [x] Map each candidate asset to a revised PRD requirement, owning phase, direct dependencies, and security boundary. ([catalog](../runtime/source-capability-catalog.md#capability-catalog))
- [x] Record incompatibilities such as historical host names, runtime paths, credential assumptions, provider integration, duplicated execution boundaries, or remote operation. ([catalog](../runtime/source-capability-catalog.md#capability-catalog))
- [x] Keep prior tests, runbooks, and evidence attached to the historical baseline; do not treat them as revised acceptance. ([catalog](../runtime/source-capability-catalog.md#fixed-provenance))

Done when:

- [x] Maintainers can trace every considered prior asset to a fixed revision and capability without copying it. ([catalog](../runtime/source-capability-catalog.md#coverage-reconciliation))

### Step 2 - Approve the Selective-Reuse and Exclusion Manifest

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [x] Create a manifest with `candidate`, `selected-for-phase`, `reference-only`, and `excluded` dispositions. ([manifest](../runtime/selective-reuse-manifest.md#disposition-vocabulary))
- [x] Require every `selected-for-phase` entry to name its current requirement, destination concept, dependency closure, required modifications, validation owner, and activation gate. ([manifest](../runtime/selective-reuse-manifest.md#selected-exact-paths))
- [x] Record the initial Phase 03 candidates as the shared shell helper and the three project-level diagnostic scripts only. ([manifest](../runtime/selective-reuse-manifest.md#selected-exact-paths))
- [x] Record the Phase 04 runner and registry as review candidates; require a revised minimal registry containing only accepted tools and revised paths. ([manifest](../runtime/selective-reuse-manifest.md#reference-only-paths))
- [x] Record the Phase 07 local stdio MCP server, curated resources, policy template, and lifecycle behavior as review candidates; explicitly exclude the historical orchestrator-dependent bridge. ([manifest](../runtime/selective-reuse-manifest.md#deferred-candidates))
- [x] Defer Neutron-agent and restricted-host assets to Phase 06 rather than importing them into the foundation. ([manifest](../runtime/selective-reuse-manifest.md#deferred-candidates))
- [x] Explicitly exclude AI-client/provider gateway, orchestrator package/runtime, assistant/orchestrator/device-auth egress, wheelhouse build/transfer, remote acceptance, provider retirement, and their dedicated validation playbooks. ([manifest](../runtime/selective-reuse-manifest.md#explicit-exclusions))
- [x] Exclude protected inventory values, generated state, caches, logs, raw audit data, credentials, and secret-bearing material regardless of source tracking. ([manifest](../runtime/selective-reuse-manifest.md#authority-and-default))
- [x] Verify no destination source is created during manifest approval. ([manifest](../runtime/selective-reuse-manifest.md#non-activation-record))

Done when:

- [x] The approved manifest is fail-closed, goal-aligned, and contains no whole-tree copy or path-parity requirement. ([manifest](../runtime/selective-reuse-manifest.md#manifest-consistency-requirements))

### Step 3 - Decide Revised Runtime Placement and Network Contract

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Record whether the assistant runs on the lab hypervisor, another routed machine, or another isolated placement. ([placement contract](../runtime/runtime-placement-contract.md#placement-contract))
- [ ] Confirm the chosen host has no OpenStack control-plane role and does not replace the historical assistant runtime. (Deferred to Step 4 inventory and host validation; protected inventory values were not read.)
- [x] Define the initial reachable endpoint set, beginning with Keystone and adding endpoints only when a later accepted diagnostic requires them. ([placement contract](../runtime/runtime-placement-contract.md#initial-network-boundary))
- [x] Document denied or unnecessary network paths, including tenant-network access, provider/model egress, and inbound public service exposure. ([placement contract](../runtime/runtime-placement-contract.md#initial-network-boundary))
- [x] Record the expected management-network route and endpoint verification method. ([placement contract](../runtime/runtime-placement-contract.md#step-4-verification-and-rollback))

Done when:

- [x] Runtime placement and first-milestone network reachability are explicit and independently reviewable. ([placement contract](../runtime/runtime-placement-contract.md#step-4-verification-and-rollback))

### Step 4 - Create the Minimal Revised Runtime Foundation

Estimate:

```text
0.5-1 engineer-days
3-6 hours
```

Tasks:

- [ ] Create or designate a revised assistant host with a distinct inventory group, host identity, runtime root, user/group, profile name, audit root, and future MCP registration namespace.
- [ ] Build minimal revised inventory and runtime setup automation from current requirements; use prior foundation files only as behavioral references, not whole-file copy authority.
- [ ] Keep diagnostics, credentials, runner, MCP, provider, orchestrator, egress, wheelhouse, and host-observer activation absent from the foundation entrypoint.
- [ ] Install only baseline packages justified for workspace management and later project-level diagnostics.
- [ ] Pin or record versions needed for repeatability.
- [ ] Verify Keystone reachability without installing credentials or starting an MCP listener/process.
- [ ] Ensure the runtime contains no admin credentials, root node keys, database credentials, RabbitMQ credentials, provider credentials, or unrestricted service credentials.

Done when:

- [ ] The isolated runtime has a minimal workspace/tooling foundation and management path but no diagnostic authority or protocol automation.

### Step 5 - Establish Workspace, Ownership, and Evidence Conventions

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Create distinct revised locations for future approved scripts, diagnostic output, credential profiles, audit events, tests, and local MCP configuration.
- [ ] Define minimal read/write permissions for each location.
- [ ] Keep credential and raw audit locations outside committed source material.
- [ ] Define a redacted evidence format for endpoint checks, tool versions, permissions, reuse decisions, and acceptance results.
- [ ] Document rollback by disconnecting or destroying the revised runtime and removing only revised repository-managed state.

Done when:

- [ ] A maintainer can identify where each artifact belongs, who may modify it, and what may be committed.

### Step 6 - Verify Isolation, Exclusions, and Lab Compatibility

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Verify every revised foundation file maps to a Phase 01 requirement and is not an unexplained prior-tree copy.
- [ ] Verify excluded prior capability names and dependency imports are absent from the revised runtime foundation.
- [x] Run narrow inventory and syntax validation for the minimal revised setup entrypoint. (Revised inventory graph and isolated Ansible syntax checks passed; no host connection occurred.)
- [ ] Confirm the prior AI-OPS source tree and deployed runtime remain unchanged and independently operable.
- [ ] Confirm controller, compute, storage, Ceph, provider, tenant, and management network roles remain unchanged.
- [ ] Confirm existing bootstrap, observability, and Molecule entrypoints are not replaced.
- [ ] Capture unresolved placement, namespace, endpoint, or package decisions as explicit gates for Phase 02.

Done when:

- [ ] The foundation fits beside the lab architecture, contains no excluded capability, and provides no executable diagnostic, runner, or MCP path.

## 01.6 Phase Definition of Done

This phase is done when:

- [ ] Prior AI-OPS source has fixed provenance and a requirement-to-capability catalog.
- [ ] A fail-closed selective-reuse manifest exists; complete-tree copying and path parity are explicitly rejected.
- [ ] Provider, orchestrator, egress, device-auth, wheelhouse, remote-operation, and unrelated host-observer assets are explicitly excluded from the current product path.
- [ ] No implementation asset is reused before its owning phase reviews dependencies and defines validation.
- [ ] Minimal revised repository/runtime identifiers are distinct from the prior implementation.
- [ ] No live secret, key, raw audit log, generated state, or secret-bearing material was copied.
- [ ] A separate revised assistant runtime exists or is explicitly designated and does not replace the prior runtime.
- [ ] Keystone management reachability is verified without diagnostic authority.
- [ ] Workspace permissions and evidence conventions are recorded.
- [ ] No diagnostic, generic execution, runner, MCP, provider, orchestrator, egress, or remote-operation capability is active.
- [ ] Existing OpenStack Lab deployment and validation paths remain intact.

## 01.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Historical code is mistaken for current requirements | Require requirement, phase owner, dependency closure, and validation fields for every selected asset. |
| Selective reuse omits a necessary helper | Discover dependency closure before selection and add it explicitly rather than widening to a directory copy. |
| A small selected file imports excluded architecture | Scan imports, paths, service names, and call sites; reject or refactor the candidate within its owning phase. |
| Revised foundation silently recreates the prior monolith | Require a minimal entrypoint and absence checks for diagnostics, runner, MCP, provider, orchestrator, egress, wheelhouse, and observer activation. |
| Revised paths or services collide with the prior runtime | Use distinct repository, automation, runtime, user, credential, audit, and MCP identifiers; validate coexistence. |
| Secret-bearing state is copied accidentally | Use path-level allowlisting and explicitly prohibit protected inventory, credentials, keys, logs, caches, and generated state. |
| Runtime is placed too close to privileged services | Require explicit node-role and network-path review before credentials are installed. |
| Existing AI/provider integration expands scope | Exclude it from the manifest and require a new approved requirement before reconsideration. |
| Endpoint access is broader than required | Start with Keystone and justify every later route from an accepted diagnostic. |
