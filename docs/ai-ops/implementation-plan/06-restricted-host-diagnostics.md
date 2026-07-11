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

- [x] MVP OpenStack API diagnostics are working through the local runner.
- [x] The restricted observer account is provisioned on reviewed lab nodes.
- [x] Host-level diagnostics are classified as higher risk and remain explicitly allowlisted.
- [x] Initial diagnostics cover controller metadata plus reviewed controller/compute Nova and Neutron evidence.

## 06.5 Ordered Tasks

### Step 1 - Design Observer SSH Policy

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [x] Identified reviewed controller and compute targets for host diagnostics.
- [x] Defined explicit per-tool host allowlists using current node role names.
- [x] Defined the observer user purpose and forced-command login restrictions.
- [x] Defined the single read-only collector command allowed through sudo.
- [x] Defined and tested prohibited shells, editors, package managers, service control, file mutation, database clients, and arbitrary command forwarding.

Done when:

- [x] A reviewer can tell exactly what host access the assistant runtime should and should not have.

### Step 2 - Provision Restricted Observer Access

Estimate:

```text
0.75-1.25 engineer-days
4.5-7.5 hours
```

Tasks:

- [x] Created the observer user on selected nodes using a repeatable process.
- [x] Installed dedicated public-key access for the assistant runtime.
- [x] Configured sudo for only the reviewed read-only collector command.
- [x] Disabled password-based escalation for the observer user.
- [x] Verified unrestricted sudo, interactive shell escalation, service control, TTY, and forwarding attempts fail.

Done when:

- [x] The assistant runtime can run approved read-only host checks and cannot escalate to unrestricted host control.

### Step 3 - Implement Bounded Metadata Log Diagnostics

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [x] Added a recent metadata errors tool with an exact host allowlist and bounded time window.
- [x] Collected fixed Nova metadata API evidence categories where present.
- [x] Collected fixed Neutron metadata-agent evidence categories where present.
- [x] Collected fixed journal evidence for metadata, proxy, timeout, bad gateway, and `169.254.169.254` terms.
- [x] Limited lines and output size before returning to the runner.
- [x] Redacted secret-like values.

Done when:

- [x] Metadata troubleshooting includes recent host-level evidence without granting generic SSH.

### Step 4 - Implement Bounded Nova and Neutron Error Diagnostics

Estimate:

```text
0.5-1 engineer-days
3-6 hours
```

Tasks:

- [x] Added a recent Nova errors tool for approved hosts and bounded time windows.
- [x] Added a recent Neutron errors tool for approved hosts and bounded time windows.
- [x] Kept each tool focused on logs and status only.
- [x] Returned structured, bounded, sectioned output.
- [x] Verified that missing log files or services produce unavailable/error statuses instead of failing unsafely.

Done when:

- [x] Operators can gather recent Nova and Neutron evidence without raw SSH commands.

### Step 5 - Extend Tool Registry and Tests

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [x] Registered host/log tools with higher risk classification.
- [x] Required host arguments to match explicit host allowlists, not only a regex.
- [x] Required time-window arguments to match accepted bounded forms.
- [x] Added tests that unsafe hosts, unsafe time windows, and shell metacharacters are rejected.
- [x] Validated that host tool calls produce audit events.

Done when:

- [x] Host diagnostics are available only through the same safety gateway as OpenStack API tools.

### Step 6 - Validate Metadata Incident Workflow With Host Evidence

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [x] Ran server basic and network tools for a representative server.
- [x] Ran recent metadata errors against the approved controller.
- [x] Verified the output retains Nova listener, Neutron metadata, Nova metadata-log, and unavailable-evidence categories.
- [x] Confirmed no remediation command is available or executed.

Done when:

- [x] The metadata troubleshooting workflow produces stronger evidence while remaining diagnostic-only.

## 06.6 Phase Definition of Done

This phase is done when:

- [x] Restricted observer SSH access exists for selected nodes.
- [x] Sudo rules allow only reviewed read-only diagnostics.
- [x] Root SSH, unrestricted sudo, and service control attempts fail.
- [x] Metadata, Nova, and Neutron recent-error tools are available through the runner.
- [x] Host inputs and time windows are validated.
- [x] Log outputs are bounded and redacted.
- [x] All host tool calls are audited.

## 06.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| SSH access becomes too broad | Use explicit host allowlists and narrow sudo command rules; test denied escalation. |
| Log tools leak secrets | Bound output, redact secret-like fields, and avoid full config dumps. |
| Host diagnostics are treated as safe as API diagnostics | Classify them higher risk and keep them opt-in. |
| Service placement changes break scripts | Use role-aware documentation and unavailable statuses rather than assumptions that fail unsafely. |