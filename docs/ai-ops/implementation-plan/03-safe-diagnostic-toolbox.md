# 03. Safe Diagnostic Toolbox

## 03.1 Goal

Create the first reviewed set of read-only diagnostic scripts that can collect useful OpenStack facts without exposing arbitrary command execution.

Target outcome:

```text
credential matrix -> reviewed read-only scripts -> manual execution -> structured outputs -> no mutation commands present
```

## 03.2 Estimate

Total estimate:

```text
2-3 engineer-days
12-18 focused hours
```

## 03.3 Scope

Included:

* Create the initial OpenStack API diagnostic scripts.
* Add shared safety helpers for input validation and common output formatting.
* Prefer JSON output from OpenStack APIs.
* Add manual validation notes for each script.
* Add static safety checks for obviously dangerous commands.

Excluded:

* Generic command execution.
* SSH-based log diagnostics.
* Operator-reader tools unless the safe credential is already available.
* MCP integration.
* Full Python SDK rewrite.

## 03.4 Assumptions

- [ ] Project-reader credentials are configured and validated.
- [ ] The assistant runtime has OpenStack CLI, JSON tooling, and shell support.
- [ ] Initial scripts can be simple shell scripts because inspectability is valuable for the first version.
- [ ] Server identifiers and names can be constrained to a safe character set for MVP tooling.

## 03.5 Ordered Tasks

### Step 1 - Define Script Safety Rules

Estimate:

```text
0.25 engineer-days
1.5 hours
```

Tasks:

- [ ] Write a diagnostic toolbox README that states read-only commands only.
- [ ] List forbidden operations: create, update, delete, restart, stop, start, install, edit, write redirection, unrestricted sudo, generic shell, database mutation, and raw command passthrough.
- [ ] Require every script to validate inputs.
- [ ] Require every script to use project-reader credentials by default unless explicitly classified otherwise.
- [ ] Require outputs to be bounded and structured where practical.

Done when:

- [ ] The script directory has a documented safety policy that can be reviewed before any script is trusted.

### Step 2 - Add Common Script Helpers

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [ ] Add a reusable helper for validating OpenStack object identifiers.
- [ ] Add a reusable helper for emitting section headers or JSON envelopes.
- [ ] Add a reusable helper for selecting the default project-reader cloud profile.
- [ ] Add a reusable helper for consistent error messages and exit codes.
- [ ] Add comments explaining why helpers reject shell metacharacters.

Done when:

- [ ] New scripts can share validation and output conventions without duplicating risky patterns.

### Step 3 - Implement Project Resource Summary

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Add a script that lists project-visible servers in JSON.
- [ ] Add network, subnet, port, volume, image, and security group list sections where policy allows.
- [ ] Ensure the script uses the project-reader profile by default.
- [ ] Ensure the script performs no create, update, delete, or service operations.
- [ ] Manually run the script and save a redacted sample output.

Done when:

- [ ] The operator can run one command to see the basic project inventory without changing the cloud.

### Step 4 - Implement Server Basic Info

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Add a script that accepts one server name or ID.
- [ ] Reject empty input and unsafe characters.
- [ ] Return server details in JSON.
- [ ] Preserve OpenStack error output for not-found or permission-denied cases.
- [ ] Manually verify success against an existing server and failure against an invalid identifier.

Done when:

- [ ] The operator can inspect one server’s state, image, flavor, network attachments, and config-drive-related fields through a read-only call.

### Step 5 - Implement Server Network Info

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Add a script that accepts one server name or ID.
- [ ] Return the server summary in JSON.
- [ ] Return port list for the server in JSON.
- [ ] Where practical, expand port, subnet, and network details using read-only show operations.
- [ ] Keep the first version simple if policy or CLI output makes expansion unreliable.
- [ ] Manually verify output helps identify fixed IPs, networks, and ports for metadata troubleshooting.

Done when:

- [ ] The operator can gather server network attachment evidence without using arbitrary OpenStack commands.

### Step 6 - Add Optional Neutron Agent Health Tool Gate

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Add the Neutron agent health script only if an operator-reader profile exists and has been validated.
- [ ] If the profile does not exist, add a documented placeholder that marks the tool unavailable.
- [ ] Classify the tool as higher-visibility than project-reader diagnostics.
- [ ] Ensure the tool lists agents only and performs no service operations.

Done when:

- [ ] The toolbox either has a safe Neutron agent health script or a clear deferred status.

### Step 7 - Add Static Safety Checks

Estimate:

```text
0.5 engineer-days
3 hours
```

Tasks:

- [ ] Add a repository-local check that scans AI-OPS scripts for forbidden command patterns.
- [ ] Include patterns for OpenStack mutation verbs, service restarts, package installation, file mutation, unrestricted sudo, shell eval, and raw SSH command forwarding.
- [ ] Run shell syntax checks on all scripts.
- [ ] Document known false positives and how to review them.

Done when:

- [ ] A maintainer can run a quick check that flags obviously unsafe script changes before trusting them.

## 03.6 Phase Definition of Done

This phase is done when:

- [ ] Initial project-resource, server-basic, and server-network scripts exist.
- [ ] Scripts use read-only OpenStack API operations.
- [ ] Scripts validate inputs and reject unsafe characters.
- [ ] Scripts use JSON or clear sectioned output.
- [ ] Scripts can be run manually from the assistant runtime.
- [ ] Static safety checks and shell syntax checks pass.
- [ ] No generic command execution script exists.

## 03.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Shell scripts grow unsafe over time | Add static checks, shared helpers, and review rules before adding more scripts. |
| CLI JSON differs across OpenStack versions | Keep scripts simple and preserve raw JSON output first; move complex parsing to later SDK tools. |
| Project-reader policy blocks expected read calls | Record unavailable sections and avoid escalating credentials by default. |
| Scripts leak too much data | Keep outputs scoped to requested diagnostics and redact secret-like config if config inspection is ever added. |