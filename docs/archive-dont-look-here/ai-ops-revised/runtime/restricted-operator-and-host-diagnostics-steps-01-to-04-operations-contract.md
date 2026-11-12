# Restricted Operator and Host Diagnostics Operations Contract — Steps 1–4

## Status and authority

This is the non-activation operations contract for Phase 06 Steps 1–4. It defines the evidence and administrator decisions required before higher-visibility diagnostics can be implemented or activated.

It does **not** authorize:

- credential, application-profile, key, or account creation;
- policy or role assignment;
- Ansible execution against a host;
- OpenStack authentication or API calls;
- SSH, sudo, collector, or host contact;
- runner registration, deployment, or execution;
- audit inspection or evidence export; or
- mutation-denial, revocation, or rollback operations.

All administrator-owned values, protected inventory, credentials, keys, raw output, identifiers, addresses, and live evidence remain outside Git. A missing, ambiguous, or contradictory input is a blocker; it must not be replaced with a guess or a broader authority.

This contract is subordinate to:

- `docs/ai-ops-revised/runtime/identity-policy-operations-contract.md`;
- `docs/ai-ops-revised/runtime/tool-runner-safety-gateway-steps-01-to-04-operations-contract.md`;
- `docs/ai-ops-revised/runtime/mvp-live-validation-and-rollback-operations-contract.md`;
- `docs/ai-ops-revised/runtime/selective-reuse-manifest.md`; and
- `docs/ai-ops-revised/runtime/source-capability-catalog.md`.

## Fail-closed rule

The decision rule for every gate is:

```text
complete, owner-approved, normalized evidence
  -> continue to the next gate

missing, ambiguous, unsafe, or contradictory evidence
  -> stop, record a blocker class, keep the capability unavailable
```

The following outcomes are not interchangeable:

| Outcome | Meaning | Allowed action |
| --- | --- | --- |
| `policy_denied` | The exact requested read reached the intended service and was refused by policy | May support a narrowly scoped authority review, after owner approval |
| `catalog_missing` | The service/catalog could not be resolved | Keep the capability unavailable; do not broaden authority |
| `connectivity_error` | The intended endpoint could not be reached | Resolve transport separately; do not broaden authority |
| `authentication_error` | Credentials or authentication failed | Resolve the existing identity boundary; do not create broader access automatically |
| `configuration_error` | The request or profile was invalid | Correct configuration; do not interpret as policy insufficiency |
| `unavailable` | The optional capability is absent or not approved | Return the bounded unavailable result |
| `accepted` | The responsible owner reviewed all required evidence and approved the gate | Continue only within the approved scope |

A result is not `accepted` merely because a playbook completed, a file exists, or a plan checkbox is marked complete.

## Decision and evidence register

The administrator must maintain an outcome-only register outside Git. Each row must identify the gate, owner, decision, evidence reference, timestamp, source revision, and unresolved limitations. The register must not contain secrets, profile contents, private keys, tokens, raw command output, resource identifiers, addresses, raw logs, or raw audit records.

The eight required inputs are described below. Each section defines what the administrator must decide, how the evidence is collected in a separately authorized operation, what may be retained, and the fail-closed result.

## 1. Phase 05 live acceptance and evidence ownership

### Decision required

Confirm whether the revised three-tool MVP is accepted as the prerequisite for Phase 06. The acceptance must cover the revised runtime, project-reader profile, runner, result/audit pair, no-mutation comparator, and prior-runtime isolation.

Name the owners for:

- live deployment authorization;
- runner execution authorization;
- protected evidence;
- audit inspection;
- identity and credential rollback; and
- administrator state comparison.

### Required evidence

The responsible operators must produce protected outcome-only evidence showing:

1. the exact source revision and target environment;
2. the limited host and inventory scope;
3. independent acceptance of foundation, project-reader profile, diagnostic toolbox, runner, and Python prerequisites;
4. the three approved tools executed only through the revised runner;
5. result and audit fields agreeing for every request;
6. a valid pre-state and post-state comparison reporting unchanged state;
7. revised-path isolation from the prior runtime; and
8. known limitations, including unavailable host-level evidence.

A documentation-only contract, static test, or default-disabled validation playbook is not live acceptance evidence.

### Retention

Retain only normalized statuses, tool names, correlation identifiers if approved by the evidence owner, durations, truncation flags, path-isolation outcomes, comparator booleans, source revision, and unresolved gates. Keep raw envelopes, identifiers, audit lines, stdout, stderr, and comparator data transient and protected.

### Fail-closed result

If acceptance evidence or an owner is missing, Phase 06 implementation may continue only as non-activating documentation or fixtures. No operator profile, host observer, or live diagnostic may be deployed.

## 2. Project-reader Neutron-agent need proof

### Decision required

Determine whether the existing project-reader can perform the exact Neutron-agent list/read operation needed by `neutron_agent_health`.

The test must distinguish policy insufficiency from transport, catalog, authentication, and configuration failures. It must use the existing project-reader only and a fixed read-only operation. It must not use admin, member, service, environment, or fallback credentials.

### Required evidence

The administrator-owned test record must contain only:

- operation label;
- profile class, not credential content or identity secrets;
- normalized result class;
- intended service/read scope;
- timestamp and source revision; and
- owner decision.

The exact operation must be reviewed before execution. No raw catalog, token, response body, resource payload, host address, stdout, or stderr may be retained.

### Decision rule

- `pass` or approved `empty`: project-reader is sufficient; do not create operator-reader for this capability.
- `policy_denied`: the exact read reached the intended policy boundary and was refused; an operator-reader proposal may proceed to owner review.
- `catalog_missing`, `connectivity_error`, `authentication_error`, or `configuration_error`: the result is inconclusive for broader authority; resolve the existing boundary or leave the capability unavailable.
- Any mutation or unexpected read success: stop immediately and investigate the project-reader boundary.

### Fail-closed result

Until a conclusive `policy_denied` result and explicit owner approval exist, `neutron_agent_health` remains unavailable and no broader profile is created.

## 3. Operator-reader identity lifecycle

### Decisions required

The OpenStack identity owner must approve all of the following:

| Item | Required decision |
| --- | --- |
| Owner | Named team or administrator responsible for creation, monitoring, and revocation |
| Profile name | Exact non-human profile label, distinct from project-reader |
| Identity | Fresh identity/application credential provenance; no historical or human credential reuse |
| Role and scope | Minimum read-only role and exact service/project/domain scope |
| Expiry | Maximum lifetime and replacement window |
| Source | Protected external source location and owner |
| Runtime | Separate protected destination directory and exact allowed filenames |
| Selection | Only the explicitly registered diagnostic may select the profile |
| Rotation | Procedure, owner, overlap policy, and old-profile removal |
| Revocation | Immediate-revocation triggers, operator, verification, and evidence |
| Mutation denial | Disposable create/update/delete targets, expected denial signatures, and postconditions |

The proposed label `aiops-assistant-operator-reader` is only a design proposal until the identity owner approves it.

### Required evidence

Before materialization, retain only normalized decisions and metadata checks:

- fresh-provenance confirmation;
- approved scope and role labels;
- expiry and rotation class;
- source and runtime path classes;
- regular-file, non-symlink, owner, group, and mode results;
- profile-to-tool mapping approval; and
- independent revocation procedure.

Profile contents, credential values, IDs, checksums, tokens, passwords, rendered configuration, and private keys must never enter Git, logs, arguments, environments, or retained evidence.

### Mutation-denial procedure

After separate authorization, the identity owner supplies uniquely named disposable targets. The validation uses fixed requests and records only normalized denial, HTTP authorization signature, and administrator-owned postconditions. It must run create, update, then delete in that order.

Any mutation success is an emergency stop. The identity owner revokes the profile, verifies impact, and performs restoration or cleanup outside the revised runner. The tested credential is never used for cleanup.

### Fail-closed result

If any lifecycle decision is missing, the profile remains absent and `neutron_agent_health` remains unavailable. The runner must never fall back between project-reader, operator-reader, admin, or environment credentials.

## 4. Maintained service-placement inventory and safe host projection

### Decisions required

The lab maintainer must identify the authoritative, maintained source for service placement and approve:

- inventory owner and revision/update process;
- exact role labels, such as controller, compute, storage, or other approved roles;
- service-to-role mapping;
- approved host labels for each future collector;
- freshness and drift procedure;
- source-to-runtime projection method; and
- evidence owner for inventory decisions.

Protected addresses, connection details, variables, credentials, and unrelated inventory values are not required in the revised repository.

### Required safe projection

The runtime projection may contain only reviewed non-secret policy data, for example:

```text
collector name
approved host label
approved inventory role
approved source class
fixed bound class
```

It must not accept caller-supplied hostnames, addresses, DNS names, paths, units, commands, or arbitrary inventory selectors. The projection must be generated or reviewed from the maintained source and must reject stale, duplicate, ambiguous, or unmapped entries.

### Evidence

Retain only:

- source identifier or revision label;
- owner and review timestamp;
- approved role labels;
- approved collector-to-role mappings;
- projection validation result; and
- unresolved placement limitations.

Do not retain protected inventory contents or raw host lists in Git.

### Fail-closed result

If service placement or the safe projection is missing, stale, ambiguous, or ownerless, no observer host may be contacted and no host parameter may be exposed.

## 5. Observer identity, collector, sources, and sudo

### Decisions required

The host-access owner must approve each item independently:

| Item | Required decision |
| --- | --- |
| Account | Fresh, distinctly named non-human observer account |
| Key | Fresh dedicated key, owner, source restriction, rotation, and removal procedure |
| Hosts | Exact inventory-derived role/host scope |
| SSH policy | No forwarding, agent use, PTY, tunneling, interactive shell, or arbitrary original command |
| Forced command | Exact fixed collector entrypoint and argument behavior |
| Collector | Root-owned path, fixed source selectors, bounded time/line/byte output, and redaction behavior |
| Sources | Exact approved logs/status/listener sources; no broad filesystem scan |
| Sudo | Whether unprivileged reads are insufficient; if needed, exact root-owned collector and fixed arguments |
| Rollback | Per-host key disablement, key rotation, sudo removal, and account removal order |

The observer must not reuse the `aiops_assistant` runtime account, OpenStack profiles, operator transport credentials, prior keys, or prior sudo state.

### Required evidence

Before host contact, retain only normalized policy results:

- account/key/policy names and ownership classes;
- approved role and source classes;
- forced-command and SSH restriction validation;
- collector metadata and bounds;
- sudo necessity decision;
- root ownership and non-symlink checks; and
- independent revocation procedure.

No key content, authorized-key line, address, raw command, raw log, environment, or collector payload may be retained in Git or normal output.

### Sudo rule

Sudo is optional and must be avoided when the approved source can be read safely without it. If required, the rule must authorize only the exact root-owned collector with fixed arguments. It must not permit argument substitution, environment changes, path changes, shell execution, editor execution, service control, package operations, or arbitrary file reads.

### Fail-closed result

If the account, key, source restriction, forced command, collector, source allowlist, or sudo decision is unresolved, provisioning stops before account/key/policy mutation and no host is contacted.

## 6. Authorized negative SSH and sudo tests

### Decision required

The host-access owner must authorize a bounded adversarial test plan and identify the protected outcome-only evidence location. Tests must be performed only after positive policy review and only against approved disposable or controlled observer targets.

### Required negative cases

The test plan must verify denial of:

- interactive shell and alternate shell;
- PTY allocation;
- agent, X11, local, and remote forwarding;
- tunnel and port-forward requests;
- arbitrary executable and extra arguments;
- environment-variable injection;
- destination or host-label bypass;
- out-of-policy file and log reads;
- editor and package-manager execution;
- service start, stop, restart, enable, disable, and status control outside the fixed collector;
- unrestricted sudo and alternate sudo arguments; and
- collector output redirection or caller-selected destination.

The test harness must use fixed argument vectors, bounded timeouts, non-interactive mode, no credential logging, and explicit cleanup. It must not open an interactive session accidentally.

### Positive control

The approved fixed collector must return bounded, redacted, structured evidence for an approved role/source case. A positive result does not compensate for any negative-case failure.

### Evidence and stop rules

Retain only test-case labels and normalized pass/fail outcomes. Any unexpected success, secret disclosure, shell access, forwarding, unrestricted sudo, or destination bypass is a critical failure:

1. stop all tests;
2. disable the affected key/account/policy through its owner;
3. preserve only protected incident metadata;
4. investigate independently; and
5. do not claim observer acceptance.

## 7. Frozen Neutron-agent output contract

### Decisions required

The diagnostic owner must approve the exact output schema before implementation. The contract must specify:

- schema version and tool name;
- overall status and unavailable representation;
- agent-record fields;
- allowed host representation or host-label mapping;
- alive and administrative-state fields;
- diagnostically necessary timestamps;
- deterministic ordering;
- maximum record count;
- truncation behavior;
- total output-byte cap;
- command/API timeout;
- secret-like redaction rules and canaries;
- malformed or unexpected field behavior; and
- audit fields and retention.

The public tool accepts no caller-selected profile, endpoint, operation, timeout, output limit, host, selector, or raw OpenStack command.

### Minimum proposed field set

Unless the diagnostic owner approves a narrower schema, the result should contain only:

```text
schema_version
tool
overall status
agents[].agent_type
agents[].host_label_or_redacted_host
agents[].alive
agents[].admin_state_up
agents[].diagnostic_timestamps
truncated
```

The final contract must define exact field names and types. Full topology, configuration, environment, credentials, connection strings, raw response fields, and unnecessary identifiers are prohibited.

### Unavailable classes

The approved unavailable classes must include, at minimum:

- missing or revoked operator profile;
- absent approved policy capability;
- service or catalog unavailability;
- connectivity failure;
- approved optional-capability absence; and
- unsupported deployment state.

The diagnostic must not retry with project-reader or a broader credential when the operator profile is missing or denied.

### Synthetic validation

Before live execution, synthetic fixtures must prove:

- deterministic ordering;
- maximum record enforcement;
- deterministic truncation;
- byte-limit enforcement;
- secret-canary redaction;
- rejection of unexpected fields;
- malformed JSON handling;
- invalid UTF-8 handling; and
- read-only argv/API behavior.

### Fail-closed result

No schema, bound, redaction rule, or unavailable mapping means no registry entry and no executable diagnostic. A valid explicit `unavailable` stub is safer than a success-shaped placeholder.

## 8. Evidence location, retention, and authorization owners

### Decisions required

The evidence owner must approve:

- protected evidence location;
- directory and file ownership/modes;
- retention duration;
- access roles;
- review and disclosure procedure;
- deletion and incident procedure;
- audit owner and audit-inspection authorization; and
- separate authorization for deployment, execution, host contact, credential operations, mutation testing, and revocation.

The repository contracts propose external protected locations, but a proposed path is not an approved location until the owner confirms it.

### Allowed outcome-only record

A retained record may contain only:

- source revision and UTC timestamp;
- non-secret run identifier;
- fixed environment, host-group, and runtime labels;
- capability/tool label;
- normalized status and limitation class;
- bounded validation booleans;
- owner and authorization class; and
- unresolved gates or rollback status.

Do not retain credentials, tokens, private keys, profile content, addresses, protected inventory, raw command arguments, stdout, stderr, raw logs, raw audit lines, resource identifiers, or comparator data.

### Authorization separation

These are separate scopes. Approval of one does not imply approval of another:

1. contract and static fixture work;
2. profile materialization;
3. runner deployment;
4. runner execution;
5. host observer provisioning;
6. host contact and collector execution;
7. audit inspection;
8. mutation-denial testing;
9. credential/key/account revocation; and
10. rollback or cleanup.

### Fail-closed result

Without a named evidence owner, approved location, retention rule, and authorization scope, the operation must not begin and no acceptance claim may be made.

## Required execution sequence

The administrator-owned process must follow this order:

1. Register owners, authorization scopes, and the protected evidence location.
2. Confirm Phase 05 acceptance and its external evidence record.
3. Test the exact Neutron read with project-reader and classify the result.
4. If and only if the result is conclusive `policy_denied`, review whether a separate operator-reader is necessary.
5. Approve the operator-reader lifecycle and mutation-denial procedure, without materializing it yet.
6. Identify the maintained service-placement source and approve a non-secret projection.
7. Approve the observer account, key, forced collector, source allowlist, and sudo decision.
8. Approve the bounded negative SSH/sudo test plan.
9. Freeze the Neutron output schema, bounds, redaction, and unavailable classes.
10. Confirm evidence retention and independent authorization for each later operation.
11. Record all decisions as outcome-only evidence.
12. Stop at the first unresolved or contradictory gate.

No later step may repair an earlier missing decision by broadening authority or reusing a historical path.

## Repository and historical-path boundary

The selective-reuse manifest remains authoritative. No historical Phase 06 script, observer role, inventory, key, account, policy, playbook, or raw evidence is selected by this contract. Historical paths may be reconsidered only through an exact manifest amendment with dependency and security review.

The revised implementation must remain under the revised namespace and must not share credentials, keys, accounts, profiles, audit paths, service paths, or mutable state with the prior runtime.

## Validation and completion criteria

This contract is complete as a documentation artifact when reviewers can identify:

- every required owner and decision;
- the exact evidence needed for each gate;
- the distinction between policy denial and environmental failure;
- the allowed retained data;
- the stop condition for unsafe or missing inputs; and
- the separate authorization scope for each later operation.

Static validation must inspect the focused diff, Markdown structure, prohibited secret-like content, historical-path references, and consistency with the identity, runner, live-validation, and selective-reuse contracts.

Completion of this document does not mean that any administrator input exists, that any profile or observer is provisioned, or that any live validation has passed.
