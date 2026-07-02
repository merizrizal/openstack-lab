# 01. Assistant Runtime Foundation

## 01.1 Goal

Create or designate the isolated runtime where AI-OPS diagnostic tooling will live, and define the workspace conventions before credentials or automation are added.

Target outcome:

```text
separate assistant runtime -> management reachability verified -> diagnostic workspace prepared -> no privileged credentials installed
```

Status note:

- [x] Initial runtime foundation notes created at `docs/ai-ops/runtime/README.md`.
- [ ] Actual assistant runtime creation/designation, reachability verification, tool installation, and runtime-local workspace creation remain pending.

## 01.2 Estimate

Total estimate:

```text
1-2 engineer-days
6-12 focused hours
```

## 01.3 Scope

Included:

* Choose initial placement for the assistant runtime.
* Confirm management-network or routed access to OpenStack API endpoints.
* Install baseline diagnostic tooling.
* Create workspace conventions for scripts, diagnostics, runbooks, audit output, and credentials.
* Document what the runtime must not contain.

Excluded:

* Creating OpenStack credentials.
* Implementing diagnostic scripts.
* Implementing the tool runner or MCP server.
* Configuring restricted SSH/sudo on OpenStack nodes.
* Running a local LLM.

## 01.4 Assumptions

- [ ] The first runtime is a separate VM or equivalent isolated host, not a controller, compute, storage, or Ceph node.
- [ ] The runtime can reach the lab management network or route to required management endpoints.
- [ ] The first implementation uses the runtime as a tool host, not as a local model host.
- [ ] The operator can perform manual setup for the first iteration if full Ansible automation is deferred.

## 01.5 Ordered Tasks

### Step 1 - Decide Runtime Placement

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Decide whether the assistant runtime runs outside OpenStack on the lab hypervisor, inside OpenStack as a tenant VM, or on another routed machine.
- [x] Record the chosen placement and reason in AI-OPS notes.
- [ ] Confirm the runtime is not part of the OpenStack control plane and does not host Keystone, Nova, Neutron, Glance, Cinder, Ceph, OpenSearch, Prometheus, or Grafana services.
- [x] Record expected network path to Keystone and other future management endpoints.

Done when:

- [ ] A human can point to the assistant runtime and explain why it is close enough to observe but isolated from control-plane authority.

### Step 2 - Verify Network Reachability

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Verify the runtime can resolve or reach the Keystone endpoint on the management path.
- [ ] Verify the runtime can reach the controller management address.
- [ ] Verify the runtime does not require tenant-network access for the first milestone.
- [ ] Record which endpoints are reachable and which are intentionally deferred.

Done when:

- [ ] Keystone reachability succeeds from the runtime without using floating-IP paths unless explicitly chosen.

### Step 3 - Install Baseline Diagnostic Tooling

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Install Python runtime, virtual environment support, package tooling, SSH client, curl, JSON tooling, fast text search, and version-control tooling.
- [ ] Install OpenStack CLI and OpenStack SDK in an isolated Python environment.
- [ ] Verify tool versions and record them in runtime notes.
- [ ] Confirm OpenStack commands fail only because credentials are not configured yet, not because client tooling is missing.

Done when:

- [ ] The runtime can display tool versions for Python, OpenStack CLI, OpenStack SDK environment, SSH client, curl, JSON parser, and text-search tool.

### Step 4 - Create Workspace Conventions

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Create a workspace with separate areas for approved scripts, diagnostic outputs, runbooks, credential profiles, audit logs, and future MCP code.
- [x] Add a short workspace README explaining the boundary between scripts, diagnostics, credentials, runbooks, and audit logs.
- [ ] Ensure credential storage locations are present but empty until Phase 02.
- [ ] Ensure diagnostic output and audit directories are writable by the runtime user.

Done when:

- [ ] A new contributor can inspect the workspace and identify where scripts, outputs, credentials, runbooks, and audit logs belong.

### Step 5 - Document Prohibited Runtime Capabilities

Estimate:

```text
0.25 engineer-days
1.5 hours
```

Tasks:

- [x] Document that the runtime must not contain admin OpenStack credentials.
- [x] Document that the runtime must not contain root SSH to OpenStack nodes.
- [x] Document that the runtime must not contain database, RabbitMQ, or unrestricted service credentials.
- [x] Document that the runtime must not expose generic shell execution to AI.
- [x] Document rollback behavior for this phase: remove the runtime or disconnect it from management access.

Done when:

- [x] The runtime notes include a clear “not allowed here” section matching the PRD safety boundary.

## 01.6 Phase Definition of Done

This phase is done when:

- [ ] A separate assistant runtime exists or is designated.
- [ ] Keystone/controller management reachability is verified.
- [ ] Baseline diagnostic tooling is installed and version-checked.
- [x] Workspace conventions are documented.
- [ ] No privileged OpenStack, SSH, database, or message-bus credentials are installed.
- [ ] The implementation can proceed to credential setup without ambiguity.

## 01.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Runtime is placed too close to the control plane | Require explicit confirmation that it is not a controller, compute, storage, or Ceph node. |
| Runtime cannot reach management endpoints | Prefer management-network placement or explicit routing before adding credentials. |
| Manual setup drifts from documentation | Record tool versions, network assumptions, and workspace structure immediately. |
| Local LLM requirements distract from MVP | Keep model hosting out of scope; use runtime as a tool host first. |
