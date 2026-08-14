## Architectural Design Specification: Bounded Host Evidence and Complete Metadata Diagnosis — Steps 5–7

**Source:** `docs/ai-ops-revised/implementation-plan/06-restricted-operator-and-host-diagnostics.md`, Steps 5 through 7; PRD requirements FR-015 through FR-031, NFR-001 through NFR-010, and acceptance criteria AC-008 through AC-016 and AC-021.

**Goal:** Add three separately named, bounded, redacted recent-evidence diagnostics for metadata, Neutron, and Nova; register them through the existing revised runner without introducing generic SSH, command, file, journal, or service access; and validate a read-only metadata troubleshooting sequence that distinguishes supported failure domains or reports explicit evidence gaps. All implementation and activation must remain fail-closed while the Phase 06 operator-reader, maintained inventory projection, observer identity, source policy, negative-test, and evidence-owner gates remain unresolved.

---

### I. Overview and Contract

Phase 06 Steps 5–7 extend the current four-tool revised registry only after the Steps 1–4 authority boundaries are accepted. The intended execution path is:

```text
named recent-evidence request
  -> closed revised registry and parameter validation
  -> approved host-label projection lookup
  -> fixed host-observer authority (never an OpenStack profile)
  -> fixed assistant-side connector argv
  -> dedicated key + restricted SSH transport
  -> forced collector with closed request schema
  -> exact role/source policy lookup
  -> bounded recent read
  -> host-side minimization and redaction
  -> structured diagnostic result
  -> existing runner result/redaction/audit boundary
  -> metadata workflow interpretation with uncertainty
```

The public surface contains three diagnostic intents, not one generic host tool.
The following public names and descriptions are accepted under D05 at source revision `rev-2026-08-0002`:

- `recent_metadata_errors`;
- `recent_neutron_errors`; and
- `recent_nova_errors`.

These names and their descriptions are accepted under D05 at source revision
`rev-2026-08-0002`; they are not runner-registered until separately authorized.
No public tool may accept a hostname, address, path, unit, service name, journal
expression, search term, command, executable, key path, user, port, SSH option,
sudo option, output destination, profile, timeout, or byte cap. The public inputs
are:

- `host_label`: a non-secret label that must resolve through the owner-approved
  maintained inventory projection before any child process or network contact;
- `window_class`: an optional closed, non-sensitive recent-time class; and
- `line_limit_class`: an optional closed, non-sensitive line-bound class.

D06 freezes `window_class` as `[15m, 30m, 1h]` with default `30m` and
`line_limit_class` as `[small, medium, large]` with default `medium`. The class
mappings are 900/1,800/3,600 seconds and 50/100/200 source lines. The collector
uses a 20-record cap, 4,096-byte raw summary cap, 512-byte normalized summary cap,
16,384-byte serialized output cap, 5-second collector timeout, and 15-second
runner timeout. None is caller-overridable.

#### Approved-host projection contract

**Function Signature Contract (Conceptual):**

```text
resolve_observer_destination(tool_name, host_label, projection)
  -> approved destination descriptor | unavailable | denial | integrity error
```

Inputs are the already validated tool name and host label plus one protected,
owner-approved runtime projection. The output contains only the fixed transport
descriptor needed by the connector. The caller never receives an address, key
path, inventory contents, or connection metadata. Missing, stale, duplicate,
ambiguous, role-incompatible, disabled, or ownerless entries stop before SSH.

The projection must be generated or reviewed from the maintained inventory. It
must not be committed with protected addresses or connection variables. Its
repository schema/fixture may use synthetic labels only. The exact runtime path,
owner, group, mode, freshness field, and deployment mechanism are **proposed**
and must be confirmed in Chunk 0.

#### Public diagnostic contract

**Function Signature Contract (Accepted D05–D07, source revision `rev-2026-08-0002`):**

```text
recent_<source>_errors(
  host_label,
  window_class="30m",
  line_limit_class="medium"
) -> bounded redacted diagnostic JSON
```

The accepted public names and fixed mappings are:

| Public name | Source class | Role | Service class | Fixed logical selector |
| --- | --- | --- | --- | --- |
| `recent_metadata_errors` | `metadata_error_events` | `controller` | `metadata` | `metadata_service_errors` |
| `recent_neutron_errors` | `neutron_error_events` | `controller` | `neutron` | `neutron_service_errors` |
| `recent_nova_errors` | `nova_error_events` | `controller` | `nova` | `nova_service_errors` |

The public descriptions are bounded, redacted recent metadata-service, Neutron,
and Nova error evidence for an approved host label. Callers cannot select the
source, role, service, selector, path, unit, command, destination, timeout, or
output limit. Neutron and Nova are explicit
`unavailable/approved_optional_capability_absent` stubs until their source slices
are separately approved.

Public request validation is exact: required lowercase ASCII `host_label` with a
maximum of 64 characters and no leading/trailing hyphen; optional
`window_class` in `[15m, 30m, 1h]` with default `30m`; and optional
`line_limit_class` in `[small, medium, large]` with default `medium`. The request
is capped at 8,192 UTF-8 bytes. Unknown/duplicate/missing fields, invalid UTF-8,
invalid types, or invalid classes produce `error/validation_error`. The internal
collector request may carry the fixed source class; the public request may not.

The exact collector document has typed fields only: `schema_version` string fixed
to `1.0`; `tool` string; top-level status enum; `sections` array; and nullable
`error` object `{class: string, message: string}`. Each section has string `name`,
section-status enum `status`, `data` array, nullable fixed error object, and
boolean `truncated`. Each event has string `host_label`, `inventory_role`,
`source_class`, `service_class`, required non-null canonical `observed_at`,
`severity`, `event_class`, and `redacted_summary`. No source-specific additions
are accepted.
Top-level statuses are `ok`, `error`, `denied`, `timeout`, and `unavailable`;
section statuses additionally include `empty`. Error classes, severity/event
class enums, canonical timestamps, deterministic ordering, redaction, canaries,
and serialization are frozen by the Steps 5–7 operations contract.

A successful or empty source result contains one fixed section. A missing, stale,
denied, malformed, timed-out, or otherwise unavailable source returns no sections
and a fixed top-level error. Correlation IDs, exit codes, durations, and audit
fields remain in the outer runner envelope. `redacted_summary` is normalized,
bounded, and redacted text; it is never a raw log line.

#### Restricted transport and collector contract

**Function Signature Contract (Conceptual):**

```text
collect_fixed_host_evidence(fixed_policy, closed_request)
  -> bounded redacted structured JSON | normalized unavailable/error
```

The confirmed target collector path is:

```text
/usr/local/libexec/openstack-ai-ops-assistant/host-observer-collector
```

The confirmed target policy path is:

```text
/etc/openstack-ai-ops-assistant/host-observer-policy.yml
```

The transport protocol is **proposed** as one bounded JSON request on standard
input to the forced collector. The SSH invocation supplies no caller-selected
remote command. The forced collector rejects `SSH_ORIGINAL_COMMAND`, extra
arguments, unknown fields, duplicate keys, oversized input, unsupported schema,
unknown source/window/line classes, and source-to-role mismatches. This design
avoids exposing a generic remote command channel while allowing one reviewed
collector to serve three fixed diagnostic intents.

The accepted host policy maps `metadata_error_events`, `neutron_error_events`,
and `nova_error_events` to the `controller` role, service classes `metadata`,
`neutron`, and `nova`, and fixed logical selectors
`metadata_service_errors`, `neutron_service_errors`, and `nova_service_errors`.
The actual protected path/unit mapping remains outside Git. The policy must not
permit configuration dumps, arbitrary logs or journals, recursive scans,
caller-selected paths/units/commands/patterns, unrelated services, raw audits,
credential/key stores, network inventory, or connection metadata.

Sudo remains optional. If unprivileged reads are insufficient, the already
specified sudo boundary may authorize only the root-owned collector with its
fixed invocation. No direct sudo or SSH primitive is registered in the runner.

#### Runner authority contract

**Function Signature Contract (Concrete for current behavior, extension conceptual):** current `resolve_tool_profile(tool)`, `build_child_environment(tool)`,
`validate_request(...)`, `validate_runtime_target(...)`, and
`execute_fixed_diagnostic(...)` remain the only runner path.

For host diagnostics, the registry requires a third fixed authority descriptor,
proposed as `aiops-assistant-host-observer`. It is not an OpenStack cloud profile.
Its child environment must contain no `OS_*` variables and no caller or parent
environment values. The connector obtains only fixed runtime policy locations;
key material and destinations are never public arguments. Unknown authority
labels, cross-profile mappings, missing projection/key metadata, or target
mismatches fail before contact. There is no project-reader, operator-reader,
admin, ambient-environment, or historical-runtime fallback.

#### Metadata evidence-path contract

Step 7 is a sequence of existing named tools, not a new aggregate executor:

```text
server_basic_info
  -> server_network_info
  -> neutron_agent_health when accepted/available
  -> recent_metadata_errors when accepted/available
  -> recent_neutron_errors when accepted/available
  -> recent_nova_errors when accepted/available
  -> evidence-to-domain interpretation
```

`project_resource_summary` may be used first when project or identifier context
is unresolved. Each request retains its own runner-generated correlation ID and
audit event. The workflow must separate:

- operator-reported guest/network symptoms;
- project-visible server and attachment evidence;
- Neutron agent/proxy evidence;
- Nova metadata API/listener evidence;
- bounded recent service events;
- unavailable, denied, timed-out, failed, truncated, stale, or contradictory
  evidence; and
- unexecuted manual recommendations.

The workflow cannot claim causality solely from one event or from the historical
metadata incident. It cannot restart a service, edit configuration, enter a
guest, broaden credentials, or request raw logs.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops-revised/implementation-plan/06-restricted-operator-and-host-diagnostics.md` requires three separate recent-evidence tools, inventory-derived hosts, bounded time/line/byte behavior, reviewed sources, redaction, runner registration, negative capability tests, and complete metadata-path validation.
- The same plan currently records Steps 5–7 as not started and Phase 06 as blocked; it does not authorize Phase 07 MCP exposure.
- `docs/ai-ops-revised/implementation-plan/ads/06-00-restricted-operator-and-host-diagnostics-steps-01-to-04-ads.md` explicitly stops before Step 5 and reserves recent Nova/Neutron/metadata collectors without registering them.
- `docs/ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-steps-01-to-04-operations-contract.md` requires an owner-approved service-placement projection, fixed observer account/key/forced collector, exact sources, bounded negative tests, protected outcome-only evidence, and separate authorization scopes.
- `ansible/ai_ops_assistant/roles/ai_ops_assistant_host_observer_boundary/defaults/main.yml` fixes the distinct `aiops-host-observer` account, `nologin` shell, SSH restrictions, collector/policy paths, owner/modes, and optional sudo path while leaving inventory, source, lifecycle, bounds, redaction, and authorization values unresolved.
- `ansible/ai_ops_assistant/roles/ai_ops_assistant_host_observer_boundary/tasks/main.yml` is a policy validator only. If enabled, it checks all owner-approved gates and then deliberately fails; it does not create an account, key policy, collector, or sudo policy.
- `ansible/ai_ops_assistant/playbook_validate_host_observer_scope.yml` uses `connection: local`, remains disabled by default, targets the absent/unapproved `ai_ops_host_observers` projection, normalizes fixture-only blocked outcomes, and defines 18 negative cases without contacting hosts.
- `ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/tool_registry.json` contains exactly four tools: three project-reader diagnostics and `neutron_agent_health`. No host diagnostic is registered.
- `aiops_tool_runner.py` has exact tool/target/profile/risk/timeout/output/parameter mappings, one supported string validator, a fresh profile-specific child environment, fixed argv execution with `shell=False`, process-group timeout cleanup, bounded capture, diagnostic validation, recursive redaction, and result/audit persistence.
- `ansible/ai_ops_assistant/tests/tool_runner/test_profile_isolation.py` proves project-reader/operator-reader separation and no fallback. `test_request_gateway.py` proves unknown/generic tools and malformed, undeclared, or unsafe parameters are rejected without spawning a child.
- `ansible/ai_ops_assistant/roles/ai_ops_assistant_diagnostic_toolbox/defaults/main.yml` and `tasks/main.yml` deploy only the current approved diagnostic set; their exact source and mode lists must be intentionally revised for any new files.
- `ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/defaults/main.yml` and `tasks/main.yml` deploy an exact four-target allowlist and must be intentionally revised after source/registry acceptance.
- `docs/ai-ops-revised/runtime/manual-aiops-workflows.md` currently labels Phase 06 host, listener, agent/proxy, and recent-log evidence unavailable. Its metadata interpretation structure already separates observed evidence, healthy/failing signals, inference, gaps, and manual recommendations.
- `docs/ai-ops-revised/runtime/selective-reuse-manifest.md` keeps historical host-diagnostic connector, policy, observer roles, and restricted diagnostics as deferred candidates. They are not selected implementation authority.
- The retained Phase 06 run `2026-0002` is blocked and cannot be reused after a source, authorization, or gate change.

#### Assumptions

- **Resolved:** D05 accepts the three public names, descriptions, source classes, controller role, service classes, fixed logical selectors, and prohibited sources at `rev-2026-08-0002`.
- **Assumed:** one newly derived assistant-side connector can share validation/redaction helpers among three fixed public wrappers without becoming a generic SSH interface.
- **Assumed:** the forced collector can receive a bounded closed request through standard input while rejecting remote-command text. Chunk 0 must confirm compatibility with the approved SSH/authorized-key mechanism.
- **Resolved:** the approved non-secret `host_label` is retained only in its structured event field; addresses, connection metadata, and host-label-like values inside summaries remain redacted.
- **Resolved:** D05–D07 require fixed source classes and normalized events instead of raw log lines. The shared event fields, source outcomes, bounds, ordering, truncation, redaction, and canaries are frozen at `rev-2026-08-0002`.
- **Assumed:** a host-observer authority descriptor can fit the current registry model without reusing the `credential_profile` semantics unsafely. Chunk 0 must decide whether to extend that field or introduce a closed `authority_class` field.
- **Assumed:** the existing Python standard library, fixed OpenSSH client, and existing Ansible modules are sufficient. No generic SSH Python library or new package is approved by this ADS.
- **Assumed:** synthetic tests can model host roles, transport, redaction, listener states, and source records without reading protected inventory or contacting a live host.

#### Remaining open confirmations for Chunk 0

1. Whether all Steps 1–4 prerequisites required by Step 5 have owner-accepted evidence, including the Phase 05 inconsistency resolution.
2. Maintained inventory source, owner, revision/freshness model, approved role labels, safe host labels, service placement, and protected projection mechanism.
3. Observer account/key/source restriction/rotation/revocation owners, exact SSH invocation, forced-command stdin behavior, and whether sudo is required.
4. Assistant-side connector source path, runtime projection path, fixed key/config path, file ownership/modes, and deployment owner.
5. Runner schema decision: extend `credential_profile` with a host-observer descriptor or add a closed authority-class contract without weakening current profile isolation.
6. Selective-reuse decision. Unless exact historical paths are amended to `selected-for-phase`, implementation must be newly derived and historical content must not be copied.
7. Protected evidence location, retention, audit-inspection authorization, unchanged-state comparator, rollback owner, and separate authorization for deployment, host contact, negative testing, and workflow execution.
8. Representative metadata case and safe pre/post state procedure for Step 7 without committing identifiers, addresses, raw logs, or raw audit lines.

D05–D07 source, bounds, output, ordering, truncation, redaction, and canary decisions are resolved at source revision `rev-2026-08-0002` and are no longer Chunk 0 blockers.

### III. Required Technical Dependencies and Imports

No new external package is approved by this ADS.

- **Existing revised runner:** Python standard library JSON, path, subprocess, selector, signal, time, UUID, redaction, and audit behavior already used by `aiops_tool_runner.py`.
- **Existing runner contracts:** exact registry parsing, `validate_request`, authority/profile resolution, fresh child environments, fixed argv, timeout/output capture, result envelopes, and audit persistence.
- **Proposed assistant-side connector:** Python standard library only, with an exact absolute OpenSSH executable selected in Chunk 0; no shell and no caller-controlled SSH options.
- **Proposed target collector:** a root-owned regular executable at the confirmed collector path. Its language must be selected in Chunk 0 from already available host dependencies.
- **Target policy:** root-owned `0600` policy at the confirmed path, containing only exact local source/role/bound/redaction rules. A repository template may contain policy structure and synthetic values, never protected inventory, keys, or addresses.
- **Protected runtime projection:** proposed generated/owner-supplied mapping from reviewed host labels to fixed destination descriptors. Its content is not committed or printed.
- **Dedicated key/account:** fresh Phase 06 observer authority, separately revocable and unrelated to project-reader, operator-reader, deployment transport, or historical keys.
- **Focused tests:** existing `unittest` and shell static-harness conventions under `ansible/ai_ops_assistant/tests/`; no deployed cloud or host is required for synthetic chunks.
- **Ansible:** existing `assert`, `stat`, `copy`, `template`, `file`, and narrowly reviewed account/key modules only after explicit deployment authorization. Generic `shell`, `command`, or `raw` tasks are not the provisioning design.
- **Operations documentation:** a new non-activation Steps 5–7 contract is required before executable collector logic.

### IV. Step-by-Step Procedure / Execution Flow

1. Reconcile the Steps 1–4 acceptance gates. Stop if Phase 05 acceptance, operator-reader review, observer policy, inventory projection, negative plan, output schema, redaction, evidence ownership, or authorization is contradictory or incomplete.
2. Create and approve a Steps 5–7 non-activation operations contract. Freeze exact tool names, source/role matrix, public inputs, bound classes, output schemas, redaction rules, unavailable states, audit treatment, and rollback sequence.
3. Decide selective reuse by exact path. Default to newly derived revised code; do not inspect/copy candidate implementation content without a manifest amendment and dependency review.
4. Freeze the maintained inventory projection schema and protected runtime location. Validate owner, mode, revision, freshness, duplicates, allowed labels/roles, service mappings, per-host enablement, and disablement procedure without printing content.
5. Define the closed transport. The connector resolves an approved host label, builds one fixed SSH argv, sends one bounded request to the forced collector, closes stdin, captures bounded output, and never uses a shell.
6. Implement a compile-safe forced-collector stub that validates its invocation/request/policy and returns explicit `unavailable`. It must reject remote-command text, arguments, unknown selectors, unsafe policy metadata, and output redirection before source access.
7. Implement the metadata source slice only. Read exact approved metadata/proxy/API/listener source classes for permitted roles, apply collector-side bounds and redaction, and emit the frozen schema. Do not scan configuration or unrelated system logs.
8. Implement the Neutron source slice only, preserving the same transport, policy, bounds, schema, and denial behavior. Permit only sources required for metadata proxy/agent diagnosis.
9. Implement the Nova source slice only, permitting only reviewed metadata API/listener/service evidence needed by the workflow.
10. Add assistant-side diagnostic wrappers or another Chunk-0-approved fixed mapping so each public tool selects exactly one source class. A caller cannot select a source, command, path, unit, role, or destination outside its host label and bound-class declarations.
11. Extend the runner with a closed host-observer authority descriptor and validators for approved host labels and bound classes. Keep existing project-reader/operator-reader behavior unchanged and reject cross-authority tampering before projection access or child execution.
12. Register exactly the three accepted host tools, then update exact deployment target/file lists. Missing observer capability returns `unavailable`; registration does not authorize deployment or host contact.
13. Run synthetic tests for allowed/denied hosts, role/source mismatch, stale projection, bad ranges/classes, metacharacters, duplicate/unknown fields, timeout, truncation, redaction, profile/authority isolation, absent generic capabilities, audit correlation, and process cleanup.
14. Provision observer state only under separate authorization and only after all policy owners approve. Apply one host at a time, verify metadata and positive/negative controls, and stop on any unexpected capability.
15. Validate each recent-evidence tool separately against an approved controlled case, retaining only normalized outcome evidence. No raw host payload, address, command, audit line, or secret enters Git or normal output.
16. Execute the Step 7 metadata sequence under its own authorization. Correlate normalized results, verify pre/post unchanged-state attestations, classify supported domains or missing evidence, and produce advisory-only recommendations.
17. Update the runbook and Phase 06 checklist only for claims supported by accepted evidence. Keep Phase 07 unavailable until Phase 06 tool and workflow acceptance is explicit.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| --- | --- | --- | --- |
| Prerequisites | Any Steps 1–4 gate is blocked or contradictory | Stop before collector or registry implementation/activation | `authorization_pending` / Phase 06 remains blocked |
| Manifest | Historical candidate is not selected or dependency closure is incomplete | Do not inspect for adaptation or copy content | `reuse_not_authorized` (proposed) |
| Projection | Missing, stale, ownerless, duplicate, ambiguous, disabled, or role-incompatible host label | Do not spawn connector or contact host | normalized `unavailable` or validation denial per frozen contract |
| Request | Unknown field, duplicate key, malformed value, metacharacter, unsupported bound class, or undeclared parameter | Reject before projection/transport | runner `validation_error`; audited without raw value |
| Authority | Host tool maps to project/operator profile, ambient environment, wrong key/config, or unknown authority | Fail before target inspection/contact | runner integrity `error`; no fallback |
| Target | Connector/collector/policy is missing, symlinked, writable, wrong owner/mode, or outside fixed path | Execute nothing | `profile_integrity_error` or proposed `observer_integrity_error` |
| Transport | SSH binary/options/destination differ from fixed descriptor | Reject fixed-argv construction | integrity `error`; no network call |
| SSH | Authentication, source restriction, connection, or forced-command negotiation fails | Do not retry with another key/user/host | normalized `unavailable` with approved class |
| Collector invocation | Arguments or `SSH_ORIGINAL_COMMAND` are present, stdin is oversized, or schema is unsupported | Reject before source read | structured denied/error result |
| Policy | Source, role, unit/path, window, line, byte, or redaction rule is absent/ambiguous | Read nothing | `unsupported_deployment_state` / `unavailable` |
| Source read | Approved service/log/listener is absent | Do not broaden sources or scan filesystem | section `unavailable` with bounded class |
| Source read | Permission denied and sudo was not approved | Do not retry with sudo | `policy_denied` or approved unavailable class |
| Bounds | Time, record, line, message, or byte cap is reached | Stop collection deterministically | bounded result with `truncated: true` |
| Decode/schema | Invalid UTF-8, malformed JSON, unexpected field, invalid timestamp, or unknown event class | Fail closed; emit no raw payload | normalized diagnostic/runner `error` |
| Redaction | Canary remains, secret-like key cannot be safely normalized, or redaction throws | Discard unsafe payload | redaction `error`; no result data retained |
| Timeout/cancel | Connector or collector exceeds deadline | Terminate local process group; rely on bounded SSH/collector termination; do not retry | runner `timeout`; audit normalized outcome |
| Audit | Result cannot be paired with a sanitized audit event | Return fail-closed runner error; do not rerun diagnostic | `audit_persistence` error |
| Negative test | Shell, forwarding, arbitrary command/path, unrestricted sudo, service control, or destination bypass succeeds | Stop all testing and invoke owner disablement/revocation | critical failure; no observer acceptance |
| Workflow | Required result is unavailable, stale, denied, failed, timed out, truncated, or contradictory | Preserve the gap and avoid root-cause certainty | partial/insufficient-evidence diagnosis |
| State comparison | Pre/post comparator is absent, invalid, or reports change | Reject acceptance and investigate externally | Phase 06 remains blocked; no cleanup by tested authority |
| Revocation | One authority cannot be disabled independently | Stop acceptance and correct lifecycle design | isolation/revocation blocker |

### VI. Security, Integrity, Idempotency, and Cleanup

- **Security:** No generic SSH, shell, sudo, journal, file, OpenStack passthrough, database, package, service-control, or remediation tool is public. Public host labels resolve through an owner-approved projection; callers never provide addresses, paths, units, commands, keys, users, ports, or transport options. Host redaction occurs before evidence crosses SSH, and runner redaction remains a second boundary.
- **Least privilege:** Project-reader, operator-reader, and host observer remain distinct authority classes with separate environment, storage, rotation, revocation, and tool mappings. A host tool receives no `OS_*` environment. An API tool receives no observer key/projection values.
- **Integrity:** Connector, collector, policy, projection, key/config, registry, and diagnostic files require exact fixed paths, regular-file/non-symlink checks, strict ownership/modes, and closed schemas. Trusted selectors are fixed by tool mapping, never public data.
- **Minimum disclosure:** Return normalized recent events, not raw files, raw journals, full configuration, environment, connection strings, catalog data, resource identifiers, addresses, or unbounded message text. Audit records use sanitized arguments and never retain projection contents or raw evidence.
- **Input safety:** Validate duplicate keys, exact fields, UTF-8, size, host labels, bound classes, role/source relationships, and numeric/order constraints before reads. Never compose shell strings or evaluate regular expressions supplied by callers.
- **Idempotency:** Static validation and fixture execution are read-only. Re-running a diagnostic performs another bounded read and audit append but creates no host/cloud state. Provisioning is idempotent only after separately approved account/key/policy design and must preserve exact owner/mode/content declarations.
- **Cleanup:** Diagnostics create no remote temporary files. Local subprocesses are placed in process groups and terminated on timeout/cancellation. If temporary local request files are ever required, Chunk 0 must reject them or define `0700`/`0600` creation and unconditional deletion. No raw evidence remains after result normalization.
- **Emergency stop:** Any mutation, unexpected shell/forwarding/sudo capability, secret disclosure, destination bypass, or state difference stops execution. Owners disable the affected key/account/policy, revoke credentials if relevant, and investigate outside the tested authority. The observer or operator credential is never used for cleanup.
- **Rollback:** Disable registry entries/runner deployment separately from key/account/sudo removal. Per-host observer disablement must not affect project-reader or operator-reader. Rollback evidence is outcome-only and separately authorized.

### VII. Validation Strategy

Validation is fixture-first and chunk-aware. Live tests are not substitutes for
static/synthetic safety evidence and require separate authorization.

- **Markdown/contract structure:**
  - `rtk grep -n "^### [IVX]" docs/ai-ops-revised/implementation-plan/ads/06-01-restricted-operator-and-host-diagnostics-steps-05-to-07-ads.md`
  - `rtk git diff --check`
- **Python syntax:** after the user provides/approves the repository Python environment, run `rtk "$PYTHON_BIN" -m py_compile <changed-python-files>`.
- **Shell syntax:** `rtk bash -n <changed-shell-tests-or-scripts>`.
- **JSON/YAML:** `rtk yq '.' <changed-yaml>` and `rtk jq -e '.' <changed-json>` where applicable.
- **Focused collector/connector tests:** proposed `rtk "$PYTHON_BIN" -m unittest discover -s ansible/ai_ops_assistant/tests/phase06 -p 'test_*host*diagnostic*.py'` after exact paths are created.
- **Focused runner tests:** `rtk "$PYTHON_BIN" -m unittest discover -s ansible/ai_ops_assistant/tests/tool_runner -p 'test_*.py'`.
- **Existing Neutron regression:** `rtk "$PYTHON_BIN" -m unittest ansible.ai_ops_assistant.tests.diagnostic_toolbox.test_neutron_agent_health` or the repository-confirmed equivalent.
- **Observer static harness:** `rtk bash ansible/ai_ops_assistant/tests/phase06/test_host_observer_policy_scoped_entrypoint.sh`.
- **Phase 06 deployment/static harness:** `rtk bash ansible/ai_ops_assistant/tests/phase06/test_tool_runner_diagnostic_deployment_static.sh`, updated only after intentional registry/deployment expansion.
- **Ansible syntax:** use repository inventory/extra-vars conventions and run `rtk ansible-playbook --syntax-check` only when the approved Ansible environment is available; syntax check does not authorize host contact.
- **Forbidden capability scan:** target changed implementation and registry files for `shell=True`, `os.system`, generic tool names, caller-selected SSH/sudo/path/unit/service/command options, mutation verbs, historical paths, raw output logging, and secret material.
- **Synthetic integration:** validate exact tool discovery, role/host allowlists, unavailable behavior, timeout/truncation, redaction canaries, audit correlation, cross-authority isolation, and absent generic capabilities with invented hosts/events only.
- **Workflow fixtures:** cover guest/network uncertainty, Neutron agent/proxy evidence, Nova metadata/listener evidence, contradictory events, optional-tool absence, stale/truncated evidence, and advisory-only recommendations.
- **Live acceptance:** run one tool/host/source scope at a time with owner-approved pre/post state attestations and protected outcome-only evidence. Any unexpected success outside the read contract invalidates acceptance.
- **Diff review:** after every chunk, run `rtk git diff --check`, `rtk git status --short`, and `rtk git diff -- <changed-files>`; review staged and unstaged changes and scan for protected/generated data.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not
implement the full feature in one pass.

#### Chunk 0: Discovery and Integration Confirmation

- **Goal:** Resolve every authority, inventory, source, schema, transport, bound, evidence, reuse, and live-authorization decision required before Step 5 implementation.
- **Files to read:** Phase 06 plan; both Phase 06 ADS files; Steps 1–4 operations contract; selective-reuse manifest/catalog; current observer defaults/tasks/playbook; runner/registry/deployment files; diagnostic deployment files; focused tests; metadata runbook; only owner-approved non-secret inventory/service-placement documentation.
- **Commands:** targeted `rtk ls`, `rtk find`, `rtk grep`, `rtk git status`, and bounded file reads. Do not inspect protected inventory values, generated keys/profiles, raw logs, or runtime evidence.
- **Evidence to confirm:** all 12 open confirmations in Section II, exact source/runtime/test paths, current branch revision, current blocked run disposition, and whether Steps 1–4 live gates permit only design/stubs or later activation.
- **Stop condition:** produce a decision register and blockers only. Do not edit, provision, contact hosts, authenticate, inspect audit records, or execute diagnostics.

#### Chunk 1: Steps 5–7 Operations Contract and Frozen Schemas

- **Goal:** Create the non-activation contract that freezes tool/source/role/input/output/bound/redaction/audit/workflow decisions before executable behavior.
- **Files to change:** proposed `docs/ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-steps-05-to-07-operations-contract.md`; amend `docs/ai-ops-revised/runtime/selective-reuse-manifest.md` only if exact historical paths are explicitly selected.
- **Symbols to add/change:** three tool contracts, projection schema, authority descriptor, forced-collector stdin protocol, source matrix, bounds, unavailable classes, event fields, workflow evidence matrix, authorization/evidence/rollback register.
- **Implementation shape:** documentation only; no success defaults, protected values, source code, deployment, registry entries, or live authorization. Unresolved decisions keep tools unavailable.
- **Validation:** Markdown heading/link checks, manifest consistency check if amended, prohibited-secret/path scan, `rtk git diff --check`, focused diff review.
- **Stop condition:** reviewers can predict every allowed input/read/output/failure and each separate authorization scope; otherwise stop with the contract incomplete.

#### Chunk 2: Forced-Collector and Projection Compile-Safe Stubs

- **Goal:** Add a syntactically valid fixed collector/projection boundary that validates metadata and always returns explicit `unavailable` before any source read or SSH activation.
- **Files to change:** repository-confirmed collector source path under `ai_ops_assistant_host_observer_boundary`; one focused synthetic collector/projection test file. Add a policy template only if Chunk 0 confirms its exact path and non-secret content.
- **Symbols to add/change:** proposed closed request parser, policy/projection metadata validators, exact source-class enum, bounds-class validators, deterministic unavailable document, invocation/`SSH_ORIGINAL_COMMAND` rejection.
- **Implementation shape:** stub-first. It reads no journal/file/listener, invokes no service command, opens no SSH connection, and returns a clear non-success `unavailable` result after validating safe synthetic input. Returning success is prohibited.
- **Validation:** language syntax/compile check, fixture tests for malformed/oversized/duplicate/unknown input and unsafe metadata, forbidden-operation scan, focused diff.
- **Stop condition:** the collector boundary is compile-safe, fails closed, and cannot read a host source or claim acceptance.

#### Chunk 3: Metadata Evidence Thin Slice

- **Goal:** Implement only `recent_metadata_errors` through the local collector with the accepted D05–D07 contract.
- **Files to change:** collector source; focused collector test file from Chunk 2; no runner registry, connector, transport, deployment, or host files.
- **Fixed adapter seam:**
  ```python
  collect_metadata_slice(
      source_records,
      source_truncated,
      freshness_class,
      host_label,
      inventory_role,
      window_class,
      line_limit_class,
      collection_started_at,
  ) -> diagnostic_document
  ```
- **Fixed metadata policy:** source class `metadata_error_events`, service class `metadata`, logical selector `metadata_service_errors`, permitted role `controller`. The public request cannot provide any of these values.
- **Synthetic fixture fields:** exact `source_sequence`, `observed_at`, `severity`, `event_class`, and `summary`; strict field/type validation; maximum raw summary 4,096 UTF-8 bytes; malformed records fail atomically.
- **Processing:** source freshness and role checks first; bounded source read; timestamp window; deterministic ordering; 20-record cap; NFC/whitespace/control normalization; `[REDACTED]` canary-safe redaction; 512-byte message cap; 16,384-byte deterministic serialization cap.
- **Failure behavior:** missing, stale, denied, malformed, timeout, role mismatch, and redaction failures use the accepted normalized mappings. Empty approved evidence returns `ok` with one `metadata_errors` section whose status is `empty`. Neutron and Nova remain explicit `unavailable/approved_optional_capability_absent` stubs.
- **Validation:** syntax/compile, success/empty/source-truncated/unavailable/denied/malformed/timeout fixtures, timestamp and ordering tests, duplicate preservation, UTF-8/message/byte truncation, all redaction canaries, atomic redaction failure, forbidden source/mutation scan, and focused diff.
- **Stop condition:** the metadata collector slice is locally contract-valid and read-only. Do not continue to Neutron/Nova, runner registration, connector/SSH, deployment, host contact, or live validation.

#### Chunk 4: Neutron Evidence Thin Slice

- **Goal:** Add only the reviewed recent Neutron metadata-proxy/agent source classes to the same fixed collector contract.
- **Files to change:** collector source; focused collector test file.
- **Symbols to add/change:** Neutron selector handler, source-to-role rules, normalized event classes, bounds/redaction/unavailable behavior.
- **Implementation shape:** preserve metadata behavior unchanged; no arbitrary journal unit, file, command, or search expression; Nova remains unavailable.
- **Validation:** syntax/compile, Neutron fixtures and role mismatch tests, existing metadata regression, redaction/truncation tests, focused diff.
- **Stop condition:** metadata and Neutron slices pass; no assistant connector, registry, deployment, or host contact exists.

#### Chunk 5: Nova Evidence Thin Slice

- **Goal:** Add only the reviewed Nova metadata API/listener/service source classes needed by the metadata workflow.
- **Files to change:** collector source; focused collector test file.
- **Symbols to add/change:** Nova selector handler, listener/event normalization, source-to-role rules, bounds/redaction/unavailable behavior.
- **Implementation shape:** preserve prior selectors; do not expose service control or broad status commands. Listener evidence is a bounded observation, not a health or causal conclusion.
- **Validation:** syntax/compile, Nova listener/event fixtures, missing service and contradictory evidence fixtures, all collector regressions, forbidden-operation scan, focused diff.
- **Stop condition:** all three collector selectors are synthetic-test complete but unreachable from the runner and unavailable in deployment.

#### Chunk 6: Assistant Connector, Runner Validation, and Closed Registration

- **Goal:** Add the fixed assistant-side transport and register exactly three host diagnostics through a host-observer authority without weakening existing tools.
- **Files to change:** repository-confirmed connector/wrapper source and focused tests; `aiops_tool_runner.py`; `tool_registry.json`; targeted runner tests. If more than two files are required, make connector/wrapper creation a separately reviewed sub-chunk before runner wiring.
- **Symbols to add/change:** destination resolver, fixed SSH argv builder, bounded stdin/stdout protocol, three fixed tool-to-source mappings, host-label projection validator, bound-class validator, host-observer authority environment, exact names/targets/profiles/risks/timeouts/output caps/parameter sets.
- **Implementation shape:** create connector/wrappers and explicit unavailable behavior before adding call sites. Registration is closed and complete; host tools cannot receive OpenStack environments, API tools cannot receive observer state, and caller data cannot alter transport/source selection. Missing projection/key/policy remains unavailable before SSH.
- **Validation:** connector fixtures, runner request/profile/result/audit/process tests, exact seven-tool registry test if three names are accepted, generic-capability absence, cross-authority tampering, Python/JSON checks, focused diff.
- **Stop condition:** all synthetic runner/connector tests pass; source registration is complete but deployment and live host contact remain separately disabled.

#### Chunk 7: Deployment Wiring, Metadata Workflow, and Static Acceptance

- **Goal:** Wire exact root-owned files into disabled-by-default deployment, update the metadata runbook and synthetic workflow tests, and reconcile checklist state without claiming live acceptance.
- **Files to change:** diagnostic/runner/observer role defaults and tasks as narrowly required; focused Phase 06 static test; `docs/ai-ops-revised/runtime/manual-aiops-workflows.md`; focused workflow fixture test; Phase 06 plan checkboxes only when supported.
- **Symbols to add/change:** exact source/target/file/mode lists, protected projection/policy metadata assertions, explicit deployment/host-contact gates, seven-tool static allowlist, metadata sequence, evidence-to-domain matrix, optional-tool behavior, advisory-only recommendation/refusal checks.
- **Implementation shape:** preserve default-disabled gates. Static tests use invented labels/events and no network. Do not combine provisioning, host contact, negative testing, audit inspection, and Step 7 live workflow into one playbook authorization.
- **Validation:** targeted Ansible/shell/Python/JSON/YAML checks, all existing runner/diagnostic/Phase 06 static regressions, workflow fixtures, secret/historical/generic-capability scan, `rtk git diff --check`, final diff review.
- **Stop condition:** static Steps 5–7 implementation is reviewable and fail-closed. Stop before every live operation unless the user separately authorizes that exact scope. Phase 06 acceptance and Phase 07 exposure remain unavailable until protected live evidence is owner-accepted.

After Chunk 7, live provisioning, each host/source validation, negative SSH/sudo
tests, audit inspection, unchanged-state comparison, revocation rehearsal, and the
complete Step 7 workflow are separate administrator-owned operations. Each uses
a fresh run identifier and stops on the first unresolved or unsafe result.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Implement Phase 06 Steps 5–7 from docs/ai-ops-revised/implementation-plan/06-restricted-operator-and-host-diagnostics.md using docs/ai-ops-revised/implementation-plan/ads/06-01-restricted-operator-and-host-diagnostics-steps-05-to-07-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm Steps 1–4 prerequisite evidence, maintained inventory projection and service placement, observer ownership and forced-collector protocol, exact sources and bounds, tool/input/output schemas, runner authority model, selective-reuse disposition, evidence ownership, rollback, and separate live authorization scopes. Do not inspect protected values or historical implementation content, deploy, authenticate, contact hosts, execute diagnostics, inspect raw audits, or perform negative tests. Stop with evidence and blockers.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Execute Chunk 1 only.
Do not continue to Chunk 2.
Create only the non-activation Steps 5–7 operations contract and any explicitly approved exact-path manifest amendment. Run targeted Markdown/manifest validation, scan for protected content, show git diff, and stop. Do not implement, deploy, or perform live operations.
```

For later chunks:

```text
Use the chunked-implementation skill.
Execute only the next explicitly approved chunk from the Phase 06 Steps 5–7 ADS.
Do not continue to another chunk. Keep every intermediate state syntax-safe and fail-closed, use explicit unavailable stubs before call sites, run the chunk-specific targeted validation, review staged and unstaged diffs, and stop with a handoff. Treat observer provisioning, host contact, negative SSH/sudo testing, audit inspection, state comparison, revocation, rollback, and complete workflow validation as separate live authorization scopes.
```

### X. Conclusion and Next Steps

This design completes Phase 06 through three named host-evidence tools and one
read-only metadata evidence workflow without introducing a generic remote-access
path. The fixed public tool determines the source class; an owner-approved
projection determines the destination; the dedicated observer authority and
forced collector enforce transport and host policy; host-side and runner-side
redaction minimize output; and the existing runner remains the only public
validation, execution, result, and audit gateway.

D05–D07 are now frozen at source revision `rev-2026-08-0002`. The next
separately authorized action is Chunk 3: the local synthetic metadata slice only.
Maintained projection, observer policy, transport, deployment, negative-test,
evidence, and Steps 1–4 activation gates remain separate blockers; no host
contact, runner registration, or live validation is authorized. Neutron and Nova
remain explicit unavailable stubs. Phase 07 MCP exposure remains out of scope
until the resulting Phase 06 tools and workflow have owner-accepted local and
live evidence.
