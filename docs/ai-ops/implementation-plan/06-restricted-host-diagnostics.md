# 06. Restricted Host Diagnostics

## 06.1 Goal

Add host-level log and service-status diagnostics only after restricted SSH and sudo boundaries are designed, implemented, and validated.

Target outcome:

```text
observer SSH user -> restricted read-only sudo rules -> bounded log scripts -> runner allowlist -> audited host diagnostics
```

## 06.2 Estimate

Total estimate:

```text
2-4 engineer-days
12-24 focused hours
```

## 06.3 Scope

Included:

* Design a restricted observer user model for controller, compute, storage, and optional Ceph nodes.
* Define read-only sudo command allowlist for logs and status checks.
* Add bounded Nova, Neutron, and metadata log diagnostics.
* Add host allowlists and time-window validation.
* Extend the tool runner with host/log tools.
* Validate that host diagnostics cannot become host control.

Excluded:

* Root SSH.
* Unrestricted sudo.
* Arbitrary SSH command execution.
* Service restarts or config edits.
* Full OpenSearch/Prometheus integration.
* MCP exposure until tools are validated locally.

## 06.4 Assumptions

- [ ] MVP OpenStack API diagnostics are already working through the local runner.
- [ ] The operator can provision a restricted observer account on selected lab nodes.
- [ ] Host-level diagnostics are higher risk and must remain opt-in.
- [ ] Initial host diagnostics focus on controller metadata, Nova, and Neutron evidence.

## 06.5 Ordered Tasks

### Step 1 - Design Observer SSH Policy

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [ ] Identify which lab nodes are valid targets for host diagnostics.
- [ ] Define an explicit host allowlist using current node role names.
- [ ] Define the observer user purpose and login restrictions.
- [ ] Define which read-only commands may run with sudo and why.
- [ ] Define prohibited commands: shells, editors, package managers, service control, file mutation, database clients, and arbitrary command forwarding.

Done when:

- [ ] A reviewer can tell exactly what host access the assistant runtime should and should not have.

### Step 2 - Provision Restricted Observer Access

Estimate:

```text
0.75-1.25 engineer-days
4.5-7.5 hours
```

Tasks:

- [ ] Create the observer user on selected nodes using a repeatable process.
- [ ] Install public-key access for the assistant runtime.
- [ ] Configure sudo rules for only reviewed read-only log/status commands.
- [ ] Disable password-based escalation for the observer user.
- [ ] Verify that unrestricted sudo, interactive shell escalation, and service restart attempts fail.

Done when:

- [ ] The assistant runtime can run approved read-only host checks and cannot escalate to unrestricted host control.

### Step 3 - Implement Bounded Metadata Log Diagnostics

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Add a recent metadata errors tool that accepts only an allowed host and bounded time window.
- [ ] Collect Nova metadata API logs where present.
- [ ] Collect Neutron metadata-agent logs where present.
- [ ] Collect relevant system journal lines matching metadata, proxy, timeout, bad gateway, and `169.254.169.254` terms.
- [ ] Limit lines and output size before returning to the runner.
- [ ] Redact secret-like values.

Done when:

- [ ] Metadata troubleshooting can include recent host-level evidence without granting generic SSH.

### Step 4 - Implement Bounded Nova and Neutron Error Diagnostics

Estimate:

```text
0.5-1 engineer-days
3-6 hours
```

Tasks:

- [ ] Add a recent Nova errors tool for approved hosts and bounded time windows.
- [ ] Add a recent Neutron errors tool for approved hosts and bounded time windows.
- [ ] Keep each tool focused on logs/status only.
- [ ] Return structured or clearly sectioned output.
- [ ] Verify that missing log files or services produce unavailable/error statuses instead of failing unsafely.

Done when:

- [ ] Operators can gather recent Nova and Neutron evidence without raw SSH commands.

### Step 5 - Extend Tool Registry and Tests

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [ ] Register host/log tools with higher risk classification.
- [ ] Require host arguments to match the explicit host allowlist, not just a regex.
- [ ] Require time-window arguments to match accepted bounded forms.
- [ ] Add tests that unsafe hosts, unsafe time windows, and shell metacharacters are rejected.
- [ ] Add tests that host tools produce audit events.

Done when:

- [ ] Host diagnostics are available only through the same safety gateway as OpenStack API tools.

### Step 6 - Validate Metadata Incident Workflow With Host Evidence

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Run server basic and network tools for a representative server.
- [ ] Run recent metadata errors against the approved controller or network node.
- [ ] Verify the output can distinguish unavailable Nova metadata listener, Neutron metadata errors, and missing evidence.
- [ ] Confirm no remediation command is available or executed.

Done when:

- [ ] The metadata troubleshooting workflow produces stronger evidence while remaining diagnostic-only.

## 06.6 Phase Definition of Done

This phase is done when:

- [ ] Restricted observer SSH access exists for selected nodes.
- [ ] Sudo rules allow only reviewed read-only diagnostics.
- [ ] Root SSH, unrestricted sudo, and service control attempts fail.
- [ ] Metadata, Nova, and Neutron recent-error tools are available through the runner.
- [ ] Host inputs and time windows are validated.
- [ ] Log outputs are bounded and redacted.
- [ ] All host tool calls are audited.

## 06.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| SSH access becomes too broad | Use explicit host allowlists and narrow sudo command rules; test denied escalation. |
| Log tools leak secrets | Bound output, redact secret-like fields, and avoid full config dumps. |
| Host diagnostics are treated as safe as API diagnostics | Classify them higher risk and keep them opt-in. |
| Service placement changes break scripts | Use role-aware documentation and unavailable statuses rather than assumptions that fail unsafely. |