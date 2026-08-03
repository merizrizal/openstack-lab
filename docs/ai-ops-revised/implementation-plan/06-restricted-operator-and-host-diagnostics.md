# 06. Restricted Operator and Host Diagnostics

## 06.1 Goal

Add higher-visibility Neutron-agent, Nova, Neutron, and metadata diagnostics through separately scoped credentials and tightly restricted host access without turning observation into host control.

Target outcome:

```text
separate operator/observer authority -> allowlisted service and log collectors -> bounded redacted evidence -> runner enforcement -> stronger metadata diagnosis
```

## 06.2 Estimate

Total estimate:

```text
3-5 engineer-days
18-30 focused hours
```

## 06.3 Scope

Included:

* Validate a separate operator-reader profile when required.
* Design and provision a restricted host observer identity.
* Define exact host and command allowlists with minimal sudo.
* Implement Neutron-agent health and recent Nova, Neutron, and metadata diagnostics.
* Bound time windows, lines, bytes, hosts, and service/log sources.
* Redact secret-like values and register tools through the revised runner.
* Validate metadata failure-domain evidence end to end.

Excluded:

* Root SSH, interactive shell, unrestricted sudo, arbitrary SSH commands, or port forwarding.
* Service restart, configuration edit, package operations, or database/message-bus access.
* Full OpenSearch, Prometheus, or Grafana integration.
* MCP exposure until local higher-risk tools pass all tests.

## 06.4 Assumptions

- [ ] Revised MVP API diagnostics and the revised runner are accepted before broader visibility is introduced.
- [ ] Operator credentials, observer identities, SSH keys, host policies, and audit locations are created fresh for the revised runtime and are not copied from or shared with the prior runtime.
- [ ] Operator-reader and SSH observer authority can be revoked independently of project-reader.
- [ ] Node roles and service placement are discoverable from the lab’s maintained inventory and architecture.
- [ ] Missing broader credentials or host access is a supported `unavailable` state.

## 06.5 Ordered Tasks

### Step 1 - Define the Higher-Visibility Access Matrix

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [ ] Map Neutron-agent, service-health, hypervisor, metadata, Nova, and Neutron evidence to the least authority that can read it.
- [ ] Separate API operator-reader needs from host SSH/log needs.
- [ ] Classify each proposed tool by credential profile, host role, sensitivity, timeout, output limit, and expected redaction.
- [ ] Define exact allowed hosts from maintained inventory rather than arbitrary addresses or names.
- [ ] Reject any diagnostic whose least-privilege command cannot be made narrow and inspectable.

Done when:

- [ ] Every proposed higher-risk tool has a reviewed authority and data-access contract.

### Step 2 - Validate a Separate Operator-Reader Profile

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Create the separate operator-reader identity/profile only if project-reader cannot supply required agent/service views.
- [ ] Protect and rotate it independently from the project-reader profile.
- [ ] Verify only the intended read operations succeed.
- [ ] Repeat representative mutation-denial tests at the broader scope.
- [ ] Prevent runner fallback from project-reader to operator-reader unless a registered tool explicitly declares it.

Done when:

- [ ] Operator-level API visibility is available only to named tools and remains empirically read-only.

### Step 3 - Design and Provision Restricted Host Observation

Estimate:

```text
0.75-1.25 engineer-days
4.5-7.5 hours
```

Tasks:

- [ ] Define a dedicated observer user on only the controller/compute/storage/Ceph nodes required by approved tools.
- [ ] Use dedicated key material, explicit source restrictions, disabled forwarding, and non-interactive or forced-command behavior.
- [ ] Define an exact read-only collector or minimal command set for recent logs and status evidence.
- [ ] Configure passwordless sudo only for that exact collector or command set and prohibit arbitrary arguments.
- [ ] Verify interactive shells, unrestricted sudo, file reads outside allowed sources, editors, package managers, service control, and command forwarding fail.
- [ ] Document key rotation, account removal, sudo rollback, and host-by-host disablement.

Done when:

- [ ] Approved host evidence is readable while host control and arbitrary command execution are denied.

### Step 4 - Implement Neutron Agent Health

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Add a named tool that lists Neutron agents through the validated operator-reader profile.
- [ ] Return agent type, host, alive/admin-state indicators, and timestamps needed for diagnosis while minimizing extra topology detail.
- [ ] Use no service enable/disable, agent update/delete, or raw OpenStack passthrough operation.
- [ ] Return `unavailable` when the profile or policy capability is absent.
- [ ] Test profile selection, structured output, and denied unsafe parameters.

Done when:

- [ ] Operators can identify unhealthy Neutron agents without exposing a mutation path.

### Step 5 - Implement Bounded Recent Error Diagnostics

Estimate:

```text
0.75-1.25 engineer-days
4.5-7.5 hours
```

Tasks:

- [ ] Add separate named tools for recent Nova, Neutron, and metadata evidence.
- [ ] Restrict host parameters to exact inventory-derived allowlists.
- [ ] Restrict time windows and line/byte limits to declared bounded ranges with conservative defaults.
- [ ] Query only reviewed service units, log sources, listener/status evidence, and metadata-path terms.
- [ ] Avoid full configuration files and redact known password, token, secret, key, connection-string, and authorization fields.
- [ ] Return unavailable sections for missing services/logs rather than broadening access or scanning the host.

Done when:

- [ ] Recent service evidence is concise, redacted, role-aware, and unavailable safely when unsupported.

### Step 6 - Register and Test Higher-Risk Tools

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Add tools to the revised registry with higher risk classifications and explicit revised credential profiles.
- [ ] Test invalid hosts, time windows, ranges, metacharacters, and undeclared parameters are denied before SSH/API execution.
- [ ] Test timeouts, truncation, redaction, unavailable capability, and audit events.
- [ ] Test that no generic SSH, sudo, journal, file, service, or OpenStack tool appears in the registry.
- [ ] Verify tool-runner child environments do not expose one profile’s secrets to another tool.

Done when:

- [ ] Higher-risk diagnostics receive exactly the same revised gateway protections as MVP tools plus profile/host isolation and no dependency on prior-runtime credentials or keys.

### Step 7 - Validate the Complete Metadata Evidence Path

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [ ] Combine server state, server network, Neutron-agent, recent metadata, recent Neutron, and recent Nova evidence for a representative case.
- [ ] Verify the evidence can separate guest/network symptoms, Neutron proxy/agent failures, Nova metadata API/listener failures, and missing evidence.
- [ ] Validate optional-tool absence produces a useful partial diagnosis.
- [ ] Confirm every operation is audited and no service, file, or resource state changes.
- [ ] Update the runbook with manual recommendations and explicit uncertainty.

Done when:

- [ ] The documented metadata incident class can be localized with read-only evidence and no remediation execution.

## 06.6 Phase Definition of Done

This phase is done when:

- [ ] Broader API and host authority are separate from project-reader and independently revocable.
- [ ] Neutron-agent, Nova, Neutron, and metadata diagnostics are narrow, bounded, and redacted.
- [ ] Hosts and time windows use strict allowlists/ranges.
- [ ] Root SSH, interactive shell, forwarding, unrestricted sudo, service control, and arbitrary file access fail.
- [ ] Higher-risk revised tools use the revised runner, result, and audit contracts.
- [ ] Metadata workflow evidence can distinguish major failure domains or clearly report missing evidence.

## 06.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Sudo rule permits argument-based escape | Prefer one fixed collector/forced command and test adversarial argument cases. |
| Operator-reader becomes default | Require explicit per-tool profile mapping and no fallback. |
| Logs leak credentials or tenant data | Minimize sources, bound output, redact before return, and test secret canaries. |
| Service placement changes | Resolve from maintained role inventory and return unavailable when expected sources move. |
| SSH expands network reach | Restrict source, destination host allowlists, forwarding, and key purpose. |
| Revised observer access shares prior keys or sudo state | Generate fresh revised keys and independently named policies; test independent revocation and coexistence. |
