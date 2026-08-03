# 01. Baseline and Runtime Foundation

## 01.1 Goal

Preserve the prior AI-OPS implementation unchanged, create a traceable and isolated revised copy, modify only the copied foundation where the revised PRD requires it, and establish the revised runtime, network path, tooling, and workspace.

Target outcome:

```text
prior baseline inventoried -> isolated revised copy created -> required deltas applied only to copy -> revised runtime and reachability verified
```

## 01.2 Estimate

Total estimate:

```text
2-3.5 engineer-days
12-21 focused hours
```

## 01.3 Scope

Included:

* Inventory the prior AI-OPS automation, diagnostics, tests, runbooks, and runtime evidence.
* Record source provenance and map required differences to the revised PRD.
* Create a complete source-controlled copy of the prior AI-OPS runtime implementation under a revised namespace before making changes.
* Assign distinct repository and runtime identifiers so the revised copy cannot collide with the prior implementation.
* Decide or confirm revised assistant-runtime placement outside the control plane.
* Establish management endpoint reachability and least-network-access expectations.
* Install or adjust baseline diagnostic tooling only where the revised gap map requires it.
* Define configuration ownership, evidence capture, and foundation rollback.

Excluded:

* Creating or installing OpenStack credentials.
* Copying live credentials, tokens, private keys, raw audit logs, secret-bearing runtime state, or unredacted evidence.
* Modifying the prior AI-OPS source tree or deployed runtime in place.
* Accepting copied tools without revised validation.
* Implementing new diagnostic behavior, the runner, or MCP.
* Restricted SSH/sudo access to OpenStack nodes.
* Local LLM deployment.

## 01.4 Assumptions

- [ ] The prior AI-OPS source and deployed runtime are treated as read-only historical baselines during revised implementation.
- [ ] The complete source-controlled prior AI-OPS runtime implementation is copied into a distinct revised namespace before any modification.
- [ ] A copied component remains unchanged when the gap map shows that it already satisfies the revised PRD.
- [ ] Runtime secrets and operational state are created fresh rather than copied.
- [ ] The revised runtime is a separate VM or equivalent observer host, not a controller, compute, storage, Ceph, database, message-bus, observability node, or the prior assistant runtime.
- [ ] Management-network reachability is sufficient for the initial API diagnostics; tenant-network placement is not required.
- [ ] The runtime is initially a connector/tool host and need not run an LLM.
- [ ] Manual provisioning is acceptable only when the resulting state and repeatable follow-up are documented.

## 01.5 Ordered Tasks

### Step 1 - Baseline the Prior AI-OPS Assets

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [ ] Inventory prior AI-OPS provisioning, scripts, runner, MCP, tests, runbooks, credential guidance, and evidence without reading secret-bearing runtime material.
- [ ] Record the source revision or commit, copy date, selected source areas, and responsible maintainer.
- [ ] Map each asset to revised functional, non-functional, testing, and acceptance requirements.
- [ ] Classify each copied asset as unchanged, modify for a documented gap, keep disabled, or retain for traceability but exclude from revised activation.
- [ ] Record incompatibilities, especially generic execution paths, model/provider-specific behavior, duplicated safety boundaries, or undocumented credential dependencies.
- [ ] Define how historical evidence will remain attached to the prior baseline without being treated as current acceptance evidence.

Done when:

- [ ] Maintainers have a provenance record and gap matrix that identify what will be copied unchanged, modified only in the revised copy, disabled, or excluded.

### Step 2 - Create the Isolated Revised Copy

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Copy the complete source-controlled prior AI-OPS runtime implementation into a distinct revised namespace before editing it.
- [ ] Copy or reconnect its associated source-controlled tests, configuration templates, and documentation so the revised copy has an independently executable validation path.
- [ ] Preserve history or record source-to-copy traceability so later reviewers can distinguish inherited behavior from revised changes.
- [ ] Assign distinct repository directories, Ansible role/playbook/inventory identifiers, package/module names, runtime installation paths, service/unit names, runtime users, credential-profile names, SSH key names, audit locations, and MCP client registration names where applicable.
- [ ] Do not copy live credentials, tokens, private keys, raw logs, raw audit events, runtime caches, generated secret material, or unredacted evidence.
- [ ] Add a copy manifest that records source provenance and identifies copied components that are unchanged, modified, disabled, or excluded from revised activation.
- [ ] Verify the copy operation produced no changes inside the prior source tree.

Done when:

- [ ] A complete traceable source copy of the prior runtime implementation exists in the revised namespace, has an independent validation path, contains no copied secret-bearing runtime state, and can be changed without modifying or colliding with the prior implementation.

### Step 3 - Decide Revised Runtime Placement and Network Contract

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Record whether the assistant runs on the lab hypervisor, another routed machine, or another isolated placement.
- [ ] Confirm the chosen host has no OpenStack control-plane role.
- [ ] Define the initial reachable endpoint set, beginning with Keystone and adding Nova, Neutron, Cinder, Glance, or selected observability endpoints only as required.
- [ ] Document denied or unnecessary network paths, including tenant-network access and inbound public service exposure.
- [ ] Record the expected management-network route and endpoint verification method.

Done when:

- [ ] Runtime placement and first-milestone network reachability are explicit and independently reviewable.

### Step 4 - Provision the Revised Runtime Baseline

Estimate:

```text
0.5-1 engineer-days
3-6 hours
```

Tasks:

- [ ] Create or designate a revised assistant runtime that is distinct from the prior assistant runtime, using the copied automation as the starting point.
- [ ] Modify copied provisioning only for documented revised gaps or namespace isolation.
- [ ] Install or preserve Python, virtual-environment support, OpenStack CLI, OpenStack SDK, SSH client, curl, JSON tools, log-search tools, and Git as required by the revised baseline.
- [ ] Pin or record versions needed for repeatable diagnostics.
- [ ] Verify Keystone and selected endpoint TCP/HTTP reachability without installing credentials.
- [ ] Ensure the runtime does not contain admin OpenStack credentials, root node keys, database credentials, RabbitMQ credentials, or unrestricted service credentials.

Done when:

- [ ] The isolated runtime has the required tools and network path but no diagnostic authority yet.

### Step 5 - Establish Revised Workspace, Ownership, and Evidence Conventions

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Create revised locations for approved implementations, diagnostic output, runbooks, credential profiles, audit events, tests, and future MCP configuration that cannot overlap the prior runtime’s locations.
- [ ] Define distinct revised runtime users and minimal read/write permissions for each location.
- [ ] Keep credential and raw audit locations outside committed source material.
- [ ] Define a redacted evidence format for endpoint checks, tool versions, permissions, and acceptance results.
- [ ] Document foundation rollback by disconnecting or destroying the runtime and removing repository-managed state.

Done when:

- [ ] A maintainer can identify where each artifact belongs, who may modify it, and what may be committed.

### Step 6 - Verify Isolation and Existing Lab Compatibility

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Compare the revised copy with its recorded source baseline and confirm every difference maps to namespace isolation or a documented revised-PRD gap.
- [ ] Run the narrow existing inventory/configuration validation relevant to copied provisioning changes.
- [ ] Confirm the prior AI-OPS source tree and deployed runtime remain unchanged and independently operable.
- [ ] Confirm controller, compute, storage, Ceph, provider, tenant, and management network roles remain unchanged.
- [ ] Confirm existing bootstrap, observability, and Molecule entry points are not replaced by the revised AI-OPS copy.
- [ ] Capture unresolved endpoint, placement, copy, or automation decisions as explicit gates for the next phase.

Done when:

- [ ] The foundation fits beside the lab architecture without changing existing control-plane or deployment workflows.

## 01.6 Phase Definition of Done

This phase is done when:

- [ ] Prior AI-OPS assets have recorded provenance and a revised-PRD copy/change classification.
- [ ] A complete traceable source copy of the prior AI-OPS runtime implementation exists and the prior source tree remains unchanged.
- [ ] Revised repository/runtime identifiers are distinct from the prior implementation.
- [ ] No live secret, key, raw audit log, or secret-bearing runtime state was copied.
- [ ] A separate revised assistant runtime exists or is explicitly designated, and it does not replace the prior runtime.
- [ ] Keystone and selected management endpoint reachability are verified.
- [ ] Baseline diagnostic tooling and workspace permissions are recorded.
- [ ] No privileged credential or generic AI-facing execution capability is present.
- [ ] Existing OpenStack Lab deployment and validation paths remain intact.

## 01.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Historical completion evidence hides revised gaps | Require a provenance and requirement-to-asset matrix, then rerun revised acceptance checks against the copy. |
| Copy-first creates silent drift between two implementations | Record source provenance, maintain a copy manifest, and require every revised difference to map to isolation or a PRD gap. |
| Revised paths or services collide with the prior runtime | Use distinct names for repository, automation, runtime, service, user, credential, key, audit, and MCP identifiers; test coexistence. |
| Secret-bearing runtime state is copied accidentally | Copy source-controlled assets only and explicitly exclude credentials, keys, logs, caches, and unredacted evidence. |
| Runtime is placed too close to privileged services | Require explicit node-role and network-path review before credentials are installed. |
| Manual setup drifts | Record versions and ownership, then add repeatable automation where stable. |
| Existing AI/provider integration expands scope | Classify model integration separately and keep the revised runtime diagnostic-only. |
| Endpoint access is broader than required | Start with Keystone and explicitly justify every additional route. |
