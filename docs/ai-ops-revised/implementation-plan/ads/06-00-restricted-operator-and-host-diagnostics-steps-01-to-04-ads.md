## Architectural Design Specification: Restricted Operator Authority, Host Observation, and Neutron Agent Health — Steps 1–4

**Source:** `docs/ai-ops-revised/implementation-plan/06-restricted-operator-and-host-diagnostics.md`, Steps 1 through 4; PRD requirements FR-014 through FR-021, FR-022 through FR-031, NFR-001 through NFR-007, and acceptance criteria AC-008 through AC-016.

**Goal:** Define and implement, through separately authorized chunks, a fail-closed higher-visibility boundary that (1) maps every proposed diagnostic to its least authority, (2) introduces an independently revocable operator-reader profile only when project-reader evidence is insufficient, (3) provisions fixed-purpose host observation without generic SSH, shell, sudo, forwarding, service control, or arbitrary file access, and (4) exposes one named `neutron_agent_health` API diagnostic through the revised runner with explicit profile selection, bounded redacted output, and safe `unavailable` behavior.

---

### I. Overview and Contract

Phase 06 Steps 1–4 extend the accepted project-scoped diagnostic path without making broader authority the default:

```text
named diagnostic request
  -> complete revised registry validation
  -> exact tool and parameter validation
  -> explicit authority selection (never fallback)
  -> fixed target and minimal per-tool child environment
  -> bounded read-only collection
  -> structured validation and redaction
  -> result envelope and sanitized audit event
  -> no mutation or alternate execution path
```

Host observation is a separate authority plane:

```text
approved inventory role and host label
  -> fixed destination allowlist
  -> dedicated revised observer key/account
  -> source restriction + no forwarding + no interactive shell
  -> one fixed collector or exact argument-free command set
  -> exact minimal sudo rule where unavoidable
  -> bounded redacted evidence
  -> no caller-selected command, path, unit, file, or destination
```

The two planes must be independently removable:

- revoking operator-reader must not disable project-reader or require host-observer changes;
- removing one host observer account/key/sudo policy must not expose or alter OpenStack credentials;
- disabling the revised runner must not be represented as credential or observer revocation;
- no profile, key, account, policy, inventory group, or evidence from `ansible/ai_ops_runtime/` may be copied into the revised runtime.

#### Step 1 higher-visibility access matrix

**Document Contract (Conceptual):** a new non-activation operations contract should be created at a repository-confirmed Phase 06 runtime-contract path, proposed as:

```text
docs/ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-steps-01-to-04-operations-contract.md
```

It must contain a closed matrix for every Steps 1–4 capability and reserve later Step 5 collectors without enabling them:

| Capability | Required authority | Fixed scope | Public parameters | Bounds | Data sensitivity | Required handling |
| --- | --- | --- | --- | --- | --- | --- |
| Existing project diagnostics | `aiops-assistant-project-reader` | project-visible resources | existing declarations only | existing runner limits | tenant/resource context | preserve accepted Phase 03/04 behavior |
| `neutron_agent_health` | proposed `aiops-assistant-operator-reader`, only after empirical need and read-only proof | Neutron agent list only | none in Step 4 | proposed short timeout and conservative byte cap, confirmed in Chunk 0/contract review | infrastructure host/type/state/timestamps | minimize fields, redact, audit, return `unavailable` when absent |
| Restricted host observation foundation | dedicated revised observer key/account | exact inventory-derived host labels and roles | no public command/path/unit argument in Steps 1–4 | fixed collector-side time/line/byte limits | host/service/log context | forced command, no shell/forwarding, pre-return redaction |
| Recent Nova/Neutron/metadata collectors | deferred to Step 5 | reserved reviewed roles/sources only | not registered in Steps 1–4 | to be frozen before Step 5 | potentially secret/tenant bearing | remain unavailable and unregistered |

Every matrix row must declare: exact tool name, implementation class, credential/profile class, permitted host roles, host source of truth, input schema, timeout, output cap, source allowlist, returned fields, redaction behavior, audit treatment, unavailable conditions, revocation owner, and rejection rationale. A proposed diagnostic without a narrow inspectable operation must be rejected rather than granted broader access.

#### Step 2 operator-reader boundary

Operator-reader is optional. Project-reader remains the default and must be tested first for the required Neutron agent list operation. A separate profile may be created only after an evidence owner accepts a normalized `policy_denied` or equivalent approved insufficient-visibility result. Missing service/catalog/connectivity is not proof that broader authority is needed.

**Profile Contract (Conceptual):**

```text
profile label: aiops-assistant-operator-reader (proposed)
provenance: fresh revised identity/application credential
scope: minimum policy-approved read scope for the named agent/service view
storage: separate protected source and runtime profile boundary
selection: only a registry-mapped named tool
fallback: prohibited in both directions
revocation: independent from project-reader and host observer
```

Exact identity name, role assignment, scope, source layout, runtime files, and expiry are administrator decisions that Chunk 0 must confirm. The existing `ai_ops_assistant_identity_boundary` role cannot simply be reused with variable overrides: its current assertions fix `aiops-assistant-project-reader`, one profile directory, and exactly `clouds.yaml` plus `secure.yaml`. Implementation must add a separately reviewed role/path or deliberately refactor the identity boundary only after tests prove that profile isolation remains closed and compile-safe.

**Profile Selection Contract (Conceptual):**

```text
resolve_tool_profile(tool) -> one fixed approved profile descriptor or fail closed
build_child_environment(tool) -> fresh minimal environment for exactly that descriptor
```

Inputs are a fully validated trusted registry entry, never caller data. Output is a new environment containing only fixed process variables and one exact `OS_CLIENT_CONFIG_FILE`/`OS_CLOUD` pair. Unknown profile labels, missing protected files, unsafe metadata, or mismatches return a normalized non-executing `unavailable` or integrity error as defined by the operations contract. There is no temporary success stub: until profile resolution is implemented, `neutron_agent_health` must remain absent from the executable registry or return an explicit fail-closed error before target execution.

Representative create, update, and delete denials must be repeated at operator scope using administrator-owned disposable targets and postconditions. Any mutation success triggers immediate stop and operator-reader revocation. The revised runtime never performs cleanup with the credential under test.

#### Step 3 restricted host-observer boundary

Host observation must not reuse the `aiops_assistant` runtime account, operator transport credentials, project/operator OpenStack profiles, or prior-runtime observer state. It requires:

- a fresh, distinctly named, non-human observer account on only approved target hosts;
- fresh dedicated key material with an approved source restriction;
- exact destination hosts derived from maintained inventory roles, never caller-supplied names or addresses;
- disabled agent/X11/TCP forwarding, tunneling, PTY, interactive shell, and arbitrary command execution;
- a forced command or exact fixed collector with no caller-selected executable, path, service, unit, pattern, or output destination;
- passwordless sudo only when the collector cannot safely read an approved source unprivileged, and then only for the exact root-owned collector with fixed arguments;
- root-owned, non-writable policy/collector files with regular-file and non-symlink checks;
- collector-side time, line, byte, source, and host-role bounds, plus secret-like redaction before evidence crosses the SSH boundary;
- independent per-host disablement, key rotation, sudo removal, account removal, and source-side key removal procedures.

**Host Allowlist Contract (Conceptual):**

```text
resolve_observer_destination(tool, requested_host_label, maintained_inventory)
  -> exact approved destination descriptor or denial
```

Steps 1–4 do not yet expose a public host parameter or host log tool through the runner. The contract is defined now so Step 5 cannot introduce arbitrary destinations. The current revised inventory contains only `assistant02` in `ai_ops_assistant`; it is not evidence of an approved target-host set. Chunk 0 must identify the maintained inventory and role labels without committing protected addresses or values. A dedicated Phase 06 inventory projection or generated allowlist may be proposed only after its provenance, ownership, and redacted representation are reviewed.

**Fixed Collector Contract (Conceptual):**

```text
restricted_host_collector(fixed_policy) -> bounded redacted structured evidence
```

The collector accepts no free-form command. If narrow enumerated selectors are later necessary, each value must be fixed by the root-owned policy and validated before any read. A compile-safe provisioning stub must fail explicitly while the inventory projection, forced-command form, exact sources, or sudo policy is unresolved; a no-op success could falsely claim observer safety.

Step 3 acceptance requires both positive and negative proof: approved bounded evidence is readable, while interactive shell, PTY, forwarding, arbitrary command, unrestricted sudo, extra arguments, out-of-policy file read, editor, package manager, service-control, and destination-bypass attempts fail. Live adversarial checks require separate authorization and protected outcome-only evidence.

#### Step 4 Neutron-agent health tool

**Tool Contract (Conceptual):**

```text
neutron_agent_health() -> Phase 03-compatible structured diagnostic JSON
```

- **Inputs:** no public parameters in Step 4; profile, executable, timeout, output cap, environment, registry, endpoint, and scope are trusted configuration only.
- **Operation:** one fixed Neutron agent list/read path using the validated operator-reader profile. No raw OpenStack passthrough and no update/delete/enable/disable action.
- **Output:** schema version, tool name, overall status, and one agents section containing only agent type, minimized inventory-approved host label or redacted host representation, alive indicator, administrative-state indicator, and diagnostically necessary timestamps. Exact field names must be fixed by the operations contract and fixtures before implementation.
- **Bounds:** short fixed runner timeout, conservative output byte cap, and a fixed maximum agent-record count or deterministic truncation rule. Exact values are proposed during Chunk 1 and must not be caller-overridable.
- **Unavailable:** missing/unmaterialized operator profile, absent policy capability, catalog/service unavailability, or an administrator-approved optional-capability absence returns normalized `unavailable`; it never retries with project-reader, admin, environment credentials, or a raw command.
- **Safety:** unexpected fields, malformed JSON, unsafe host/detail content, unsupported status, profile mismatch, or redaction failure fails closed.

The runner must continue to enforce a complete closed registry. Adding this tool requires an intentional registry contract revision rather than merely adding a JSON entry, because the current implementation hardcodes exactly three names, three targets, one project-reader profile, one risk class, one parameter shape, and one child environment.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops-revised/implementation-plan/06-restricted-operator-and-host-diagnostics.md` requires separate operator/observer authority, exact inventory-derived hosts, restricted host access, `neutron_agent_health`, safe `unavailable`, and denial of generic control paths.
- `docs/ai-ops-revised/runtime/identity-policy-operations-contract.md` establishes project-reader as the only current revised profile and explicitly defers operator-reader, Neutron-agent, and host authority.
- `ansible/ai_ops_assistant/roles/ai_ops_assistant_identity_boundary/defaults/main.yml` and `tasks/main.yml` fix one `aiops-assistant-project-reader` profile and exactly two protected files; profile source and destination tasks use `no_log` and reject symlinks/weak metadata.
- `ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/files/scripts/tool_runner/aiops_tool_runner.py` fixes `TOOL_NAMES`, `TOOL_TARGETS`, `PROJECT_READER_PROFILE`, `CHILD_ENVIRONMENT`, one supported validator, exact tool count, and project-reader-only profile validation.
- The runner executes fixed argv with `shell=False`, a fresh child environment, process-group timeout cleanup, bounded combined output, diagnostic JSON validation, recursive redaction, deterministic envelopes, and fail-closed audit persistence.
- `tool_registry.json`, runner defaults, and runner deployment tasks contain exactly three project tools and their fixed revised paths. Phase 06 cannot be enabled by a registry-only edit.
- `ansible/ai_ops_assistant/inventories/local/local.yml` contains only `assistant02` under `ai_ops_assistant`. No revised host-observer group or approved host allowlist is present.
- `docs/ai-ops-revised/runtime/selective-reuse-manifest.md` classifies historical Neutron-agent and host-observer assets as `candidate`, not `selected-for-phase`; no current copy/adaptation authority exists.
- `docs/ai-ops-revised/runtime/source-capability-catalog.md` identifies the historical candidate family but states that separate operator-reader, restricted SSH/sudo, host policy, and output/redaction review are prerequisites.
- `docs/ai-ops-revised/runtime/mvp-live-validation-and-rollback-operations-contract.md` preserves the runner as the only executable boundary and treats deployment, execution, audit inspection, and credential rollback as independent authorization scopes.
- FR-014 and FR-015 require Neutron-agent and restricted-host diagnostics only when safe optional authority exists; NFR-006 requires missing optional authority to remain a useful `unavailable` state.

#### Assumptions

- **Assumed:** the operator-reader profile label will be `aiops-assistant-operator-reader`. The identity owner must confirm the exact label, role, scope, expiry, and policy behavior.
- **Assumed:** a dedicated Phase 06 operator-profile role/path is safer than parameterizing the existing exact project-reader role. Chunk 0 must compare these approaches against repository conventions.
- **Assumed:** host observer provisioning will be owned by a new revised role rather than the foundation role, because the foundation contract explicitly excludes observer behavior.
- **Assumed:** the maintained host-role inventory is available to authorized operators outside the revised `local.yml`; its exact path and safe projection are not yet confirmed.
- **Assumed:** `neutron_agent_health` needs no public argument. If the installed OpenStack client requires additional scope input, that input must be trusted fixed configuration or the design must return to review.
- **Assumed:** the existing Phase 03 structured diagnostic schema can be retained. Exact Neutron-agent output fields and maximum-record behavior require fixture confirmation.
- **Assumed:** historical candidate behavior may be inspected only after the selective-reuse manifest is amended to `selected-for-phase`; implementation content is newly derived unless that approval explicitly permits adaptation.

#### Open confirmations for Chunk 0

1. Whether the accepted Phase 05 runner/API evidence satisfies the Phase 06 prerequisite on the current branch.
2. Which Neutron agent list operation project-reader can and cannot perform, using normalized evidence only.
3. Operator-reader identity owner, exact scope/role, profile label, protected source/runtime layout, rotation, expiry, revocation, and mutation-denial procedure.
4. Maintained inventory owner, exact role labels, service placement, approved target hosts, and safe non-secret host-label projection.
5. Observer account label, source restriction, key ownership, forced-command mechanism, exact collector path, approved sources, and whether sudo is necessary.
6. Exact negative SSH/sudo tests and a safe test harness that cannot open an interactive session accidentally.
7. Neutron-agent output schema, record cap, timestamps, host-field minimization, timeout, byte cap, redaction canaries, and unavailable classes.
8. Whether the selective-reuse manifest will select any exact historical candidate path or require all-new revised implementation.
9. External evidence owner/location, retention, outcome-only schema, and separate authorization for deployment or live validation.

### III. Required Technical Dependencies and Imports

No new external package is approved by this ADS. Implementation should use the repository’s existing Ansible/Python/shell/runtime dependencies unless Chunk 0 proves a narrowly required dependency and the operations contract is revised first.

- Existing revised runner: Python standard library modules already used for JSON, subprocess, selectors, signals, paths, redaction, and audit persistence.
- Existing OpenStack tooling: installed `python3-openstackclient`/`python3-openstacksdk`; the exact fixed read implementation must follow the current diagnostic-toolbox convention selected during implementation.
- Existing Ansible modules: `assert`, `stat`, `file`, `copy`, and other fixed non-shell modules where practical.
- Proposed operator profile materialization role/playbook: repository-local, disabled by default, protected with `no_log`, regular-file checks, strict owner/mode checks, and an explicit `assistant02` limit.
- Proposed host-observer role/playbook: repository-local, independently opt-in, exact host-role scope, root-owned fixed policy/collector, restrictive authorized-key/SSH configuration, and exact sudo policy only if required.
- Proposed test groups: operator identity/profile static tests, restricted host-observer policy tests, Neutron diagnostic fixtures, and revised runner profile-isolation/request/execution/result/audit tests.
- Maintained inventory/service-placement source: required but not yet confirmed; protected values must not enter Git or test output.
- No MCP, provider SDK, generic SSH library, generic executor, database client, message-bus client, service manager API, package operation, or remediation dependency is permitted.

### IV. Step-by-Step Procedure / Execution Flow

1. Confirm repository state, accepted Phase 05 prerequisites, and current source/manifest revisions without touching live systems.
2. Freeze the Steps 1–4 non-activation operations contract and higher-visibility matrix. Reject any capability lacking an exact authority, source, bound, output, redaction, audit, unavailable, and revocation contract.
3. Test project-reader suitability for the exact Neutron-agent read through a separately authorized, normalized validation. Do not interpret connectivity/catalog failure as policy insufficiency.
4. If project-reader is sufficient, keep operator-reader absent and explicitly map the named tool to the least profile proved adequate. If it is insufficient, obtain identity-owner approval for a fresh, narrowly scoped operator-reader.
5. Implement operator-profile materialization as a separate disabled-by-default slice. Validate source/destination metadata without exposing profile content, then test independent rotation/revocation and representative mutation denial under separate live authorization.
6. Refactor the runner from one global child environment to an exact trusted tool-to-profile mapping. Preserve a fresh environment and deny unknown labels. Existing tools must remain project-reader-only; no caller can choose a profile.
7. Establish the maintained inventory projection for observer destinations. The projection contains only reviewed non-secret labels/roles needed by approved tools, not arbitrary hostnames/addresses supplied at request time.
8. Add a dedicated disabled-by-default observer role with fresh key/account/policy state on only approved hosts. Use forced command/non-interactive behavior, disable forwarding and PTY, and avoid sudo when possible.
9. If sudo is unavoidable, grant only the exact root-owned collector with fixed arguments. Ensure neither environment manipulation nor argument injection can select another command, source, path, unit, or output destination.
10. Validate positive bounded collection and all negative shell/SSH/sudo/file/service/package/forwarding paths. Record outcome classes only outside Git; any unexpected success stops validation and triggers host-by-host disablement.
11. Add a newly derived `neutron_agent_health` diagnostic and fixtures. Perform one fixed read; emit only the approved minimized schema; enforce record/output bounds and safe unavailable classes; never mutate an agent.
12. Extend the runner’s closed constants/schema/profile resolver/target mapping and registry with exactly the approved fourth tool. Validate profile isolation before target inspection/execution and preserve all Phase 04 result/audit guarantees.
13. Run fixture/static validation first. Live operator API validation requires separate approval, configured optional credentials, unchanged-state attestations, and protected outcome-only evidence.
14. Stop after Step 4 acceptance or an explicit blocker. Do not register Nova, Neutron, or metadata host tools; those belong to Steps 5–6.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| --- | --- | --- | --- |
| Prerequisite | Phase 05 API/runner acceptance is missing or ambiguous | Stop before Phase 06 implementation or live work | unresolved prerequisite gate |
| Matrix | A proposed diagnostic lacks a narrow inspectable least-privilege path | Reject the row; do not broaden authority | capability remains absent/unavailable |
| Manifest | Historical candidate remains unselected or provenance changed | Do not inspect for adaptation or copy content | manifest-review blocker |
| Need proof | Project-reader result is connectivity/catalog/configuration failure | Do not create operator-reader based on that result | normalized inconclusive/unavailable outcome |
| Operator identity | Scope, role, expiry, owner, or revocation is unconfirmed | Do not materialize profile | unresolved authority gate |
| Profile source | Missing, symlinked, weak-mode, unexpected, or historical source file | Abort under `no_log`; copy nothing | profile integrity blocker |
| Profile resolution | Tool/profile mapping is unknown, mismatched, or caller influenced | Reject before target inspection/execution | `target_integrity_error` or proposed `profile_integrity_error` |
| Optional profile | Approved operator profile is absent or revoked | Do not fall back to project-reader/admin/environment | `unavailable` |
| Mutation proof | Create/update/delete unexpectedly succeeds | Stop immediately; identity owner revokes and investigates | acceptance failed; emergency revocation |
| Inventory | Maintained role/host projection is missing, stale, ambiguous, or includes arbitrary input | Provision/connect to no host | inventory authority blocker |
| Observer key/account | Key is reused, unrestricted, weakly owned, or not independently revocable | Reject provisioning or disable affected host | observer integrity failure |
| SSH restriction | Shell, PTY, forwarding, tunneling, or arbitrary command succeeds | Stop; remove/disable key and account per host | critical acceptance failure |
| Sudo policy | Extra arguments, environment, path substitution, or another command succeeds | Remove sudo policy; stop all observer validation | critical acceptance failure |
| Collector source | Requested role/source is absent or unsupported | Do not scan broadly or select another file/unit | bounded section `unavailable` |
| Collector output | Time/line/byte/record limit reached | Stop collection, mark truncation, retain only bounded sanitized data | valid truncated/partial evidence, never health proof |
| Redaction | Secret canary or unsafe field survives, or redaction fails | Emit no raw/partial payload; stop retention | `redaction_error`; incident review if disclosed |
| Neutron policy | Agent list is denied under approved optional profile | Do not escalate or retry with broader profile | `unavailable`/`policy_denied` limitation |
| Neutron output | Malformed JSON, unexpected fields/status, or unsafe host detail | Reject payload before accepted result | `output_decode_error` or validation error |
| Runner timeout | Diagnostic exceeds fixed deadline | Terminate process group and do not retry automatically | `timeout` with truncation metadata as applicable |
| Audit | Sanitized event cannot be safely persisted | Fail closed; do not report diagnostic success | `audit_integrity_error`/`audit_write_error` |
| Prior-runtime isolation | Historical path, key, profile, role, inventory, or service is touched | Stop and investigate; no automatic cleanup | coexistence acceptance failure |
| Revocation | Removing one authority affects another unexpectedly | Stop removal sequence and restore only through owning administrator | independence test failed |
| Live authorization | Deployment, host contact, API call, audit inspection, or revocation lacks explicit approval | Perform no live action | authorization blocker |

### VI. Security, Integrity, Idempotency, and Cleanup

- **Security:** project-reader remains the default. Operator-reader and host observer are optional, separately named, separately stored, separately mapped, and independently revocable. No generic SSH, shell, sudo, OpenStack CLI, forwarding, file, database, message-bus, service-control, package, editor, or remediation capability is exposed.
- **Credential isolation:** each tool receives a newly built minimal environment for exactly one trusted profile. Parent `OS_*`, SSH, proxy, user-site, and caller-selected variables are not inherited. A registry label alone is not authority; the runner validates it against a closed in-code mapping and protected path metadata.
- **Host isolation:** destinations come from maintained inventory policy, not public arguments or DNS/address text. A key is restricted by source and purpose; forwarding and PTY are disabled; forced command ignores/rejects original commands. Policy and collector files are root-owned, regular, non-symlinked, and not writable by the observer.
- **Data minimization:** Neutron-agent output includes only approved diagnostic fields. Host evidence uses only reviewed sources and bounded recent data. Full configuration, environment, command line, credentials, connection strings, and raw log dumps are prohibited.
- **Integrity:** closed registry fields, exact tool/target/profile mappings, root-owned deployed files, duplicate-key rejection, safe argv, no shell, strict JSON schema, recursive redaction, and result/audit correlation remain mandatory.
- **Idempotency:** repeated profile/observer/diagnostic/runner role applies must report no changes after the accepted first apply. Diagnostic calls are read-only and not automatically retried. Provisioning reruns must not append duplicate keys, sudo rules, or SSH directives.
- **Cleanup:** failed profile materialization leaves no partial permissive profile. Failed observer provisioning removes only newly created revised key/account/policy state when explicitly authorized and ownership is proven. Temporary controller sources are removed by their owner. Raw outputs and canaries are discarded after approved transient review.
- **Revocation:** operator profile revocation, source profile removal, runner disablement, observer source-key removal, per-host authorized-key disablement, sudo-policy removal, and observer-account removal are separate ordered actions. Never alter project-reader, `assistant02` foundation state, prior runtime, or unrelated host access as collateral cleanup.
- **Evidence:** Git retains contracts, fixtures with synthetic values, and normalized checklist state only. Credentials, keys, profile content, identifiers, addresses, host lists, raw logs, raw audit lines, command arguments, and operational evidence remain protected and external.

### VII. Validation Strategy

Validation is chunk-aware and local/fixture-driven unless a later chunk has separate explicit authorization. Commands below are implementation guidance; they do not authorize live execution.

#### Documentation and static contract

- Locate required headings, authority matrix, profile isolation, host denials, failure modes, validation, and rollback with targeted `rtk grep`.
- Verify Markdown fences and tables manually or with existing repository tooling.
- Run `rtk git diff --check` and focused `rtk git diff -- <changed-files>`.
- Scan for real credential/profile content, private keys, tokens, addresses, raw evidence, historical runtime paths, and unsupported completion claims.

#### Ansible/YAML

- Run repository-approved `yamllint` and `ansible-lint` only against changed Phase 06 roles/playbooks/tests.
- Run `ansible-playbook --syntax-check` with the known repository environment after the user confirms the Python virtual environment.
- Statically assert default-disabled flags, exact role/host/limit gates, `no_log` on protected material, fixed file allowlists, strict owner/modes, no symlink following, no `hosts: all`, and no prior-runtime role/path.
- Do not run check/apply or contact hosts during static chunks.

#### Python and shell

- Run `python3 -m py_compile` for changed Python only after the user confirms the Python virtual environment required by repository discipline.
- Run focused `unittest` files for runner/profile/host-policy/Neutron fixtures; do not default to a broad suite.
- Run `bash -n` and the existing diagnostic safety harness for any changed shell diagnostic.
- Search changed executable files for `shell=True`, `os.system`, generic `ssh`/`sudo`, raw OpenStack passthrough, mutation verbs, arbitrary file reads, output redirects, caller-selected environments/paths, and historical roots.

#### Required targeted behavior tests

1. Existing three tools remain byte/schema/behavior compatible and project-reader mapped.
2. Registry corruption, unknown tools/profiles/targets/fields, duplicate keys, and undeclared parameters fail before execution.
3. `neutron_agent_health` selects only the approved operator profile and receives no inherited project/operator/admin credential from another context.
4. Missing/revoked operator profile returns `unavailable` and never falls back.
5. Fixed Neutron read argv/SDK operation contains no mutation and accepts no public passthrough parameter.
6. Synthetic agent fixtures produce only approved fields, deterministic ordering, bounded record count, truncation, and redaction.
7. Timeouts, invalid UTF-8/JSON/schema, secret canaries, audit failure, and target integrity failures preserve Phase 04 fail-closed behavior.
8. Observer policy fixtures reject arbitrary hosts, commands, paths, units, arguments, metacharacters, environment changes, PTY, and forwarding before connection/collector execution.
9. Provisioning tests prove fresh distinct key/account/policy names, exact host-role projection, fixed file metadata, default-disabled behavior, and idempotent list/rule management.
10. Negative static scans prove no generic SSH/sudo/journal/file/service/OpenStack tool enters the public registry.

#### Separately authorized live validation

Live validation is not authorized by this ADS. If later approved, use distinct chunks and protected outcome-only evidence for:

- exact project-reader need proof;
- operator-reader read success and mutation denials;
- profile rotation/revocation and cross-profile isolation;
- observer positive collector access and adversarial shell/PTY/forwarding/sudo/file/service denials;
- per-host disablement and independent authority revocation;
- one `neutron_agent_health` runner result/audit pair plus unchanged-state attestation.

Any unexpected success, disclosure, state difference, or prior-runtime touch stops the run. No automatic retry or broad workaround is allowed.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass.

#### Chunk 0: Discovery and Integration Confirmation

- **Goal:** Confirm Phase 05 prerequisites, manifest disposition, operator identity decisions, maintained inventory/service placement, observer restriction mechanism, Neutron output contract, evidence ownership, and authorization boundaries.
- **Files to read:** Phase 06 plan; this ADS; Phase 02/04/05 operations contracts; selective-reuse manifest/catalog; revised identity, diagnostic, runner, inventory, playbook, and focused test files; only approved maintained-inventory documentation needed to resolve non-secret labels.
- **Commands:** bounded `rtk git status`, `rtk find`, `rtk grep`, and targeted reads. Do not inspect protected inventory values, historical credential/key content, raw evidence, or live hosts.
- **Evidence to confirm:** all nine open confirmations in Section II, exact proposed file paths, whether any historical path becomes selected, and per-chunk validation commands/environment.
- **Stop condition:** no edits and no live actions. Produce a decision/blocker report; unresolved authority, inventory, or forced-command details block Chunk 1 approval.

#### Chunk 1: Steps 1–4 Non-Activation Operations Contract

- **Goal:** Freeze the reviewed higher-visibility matrix and authority/failure/revocation contracts before executable work.
- **Files to change:** proposed `docs/ai-ops-revised/runtime/restricted-operator-and-host-diagnostics-steps-01-to-04-operations-contract.md`; if approved, the exact selective-reuse manifest entries only.
- **Symbols to add/change:** closed access matrix, normalized need-proof classes, profile descriptor, host-role projection, forced-collector policy, Neutron output schema/bounds, evidence allowlist/denylist, authorization matrix, and rollback sequence.
- **Implementation shape:** Markdown only; unresolved values remain explicit blockers. Manifest changes select exact paths only and do not authorize copying, deployment, or execution.
- **Validation:** targeted heading/security scans, manifest consistency check, balanced Markdown, `rtk git diff --check`, staged/unstaged focused diff.
- **Stop condition:** reviewers can predict allowed inputs, outputs, data, failures, authority, and revocation; no capability has been activated.

#### Chunk 2: Separate Operator Profile Contract and Fail-Closed Stub

- **Goal:** Add a disabled-by-default, compile/syntax-safe operator-profile materialization boundary without altering project-reader behavior.
- **Files to change:** one repository-confirmed operator identity role defaults file and its task file; if repository convention requires a playbook, split the call site into the next chunk rather than exceeding the slice.
- **Symbols to add/change:** proposed operator profile constants, protected source/destination metadata assertions, explicit enable gate, regular-file/non-symlink checks, exact file allowlist, `no_log`, and temporary explicit failure while identity-owner inputs are absent.
- **Implementation shape:** newly derived revised path; no credential generation or profile content. Safe stub fails when enabled without all approved external inputs and otherwise changes nothing.
- **Validation:** focused YAML lint/syntax, static `no_log`/mode/path/default-false checks, project-reader regression checks, forbidden historical/profile-content scan, focused diff.
- **Stop condition:** role is locally valid and cannot materialize, broaden, or report success with missing authority inputs; no deployment occurred.

#### Chunk 3: Operator Profile Deployment and Validation Harness

- **Goal:** Add exact `assistant02`-limited entrypoint and fixture/static validation for profile separation, read-only proof inputs, and independent lifecycle outcomes.
- **Files to change:** one proposed deployment/validation playbook and one focused static test file.
- **Symbols to add/change:** exact host/group/limit assertions, ambient credential denial, explicit opt-in, normalized need-proof gate, mutation-denial outcome interface, independent revocation/rotation outcome fields, and no-log handling.
- **Implementation shape:** fail closed before live tasks unless all operator-owned inputs/authorizations are present. No generic OpenStack command parameter or cleanup authority.
- **Validation:** focused test, Ansible lint/syntax, fixed-profile/path scan, mutation-verb containment review, `rtk git diff --check`, focused diff. Do not deploy or authenticate.
- **Stop condition:** static harness cannot fall back, leak profiles, or claim read-only acceptance from inconclusive outcomes.

#### Chunk 4: Restricted Observer Policy and Provisioning Stub

- **Goal:** Encode one disabled-by-default observer policy path with exact inventory roles, key/account separation, forced command, forwarding/PTY denial, and fixed collector metadata.
- **Files to change:** one repository-confirmed observer role defaults/policy file and its task file.
- **Symbols to add/change:** proposed observer account/key labels, allowed role labels, root-owned collector/policy paths, SSH restrictions, exact optional sudo rule, per-host enable gate, and explicit unresolved-policy failure.
- **Implementation shape:** no public runner tool. Prefer declarative Ansible modules/templates over generic commands. Until inventory and exact collector/sudo policy are confirmed, enabled execution fails before account/key/policy mutation.
- **Validation:** focused YAML/template lint, static exact-host/role/default-false checks, SSH restriction and sudo-argument scans, forbidden generic-command/path/service patterns, focused diff.
- **Stop condition:** the role is syntax-safe and cannot provision arbitrary hosts, reusable keys, shells, forwarding, or broad sudo; no host contact occurred.

#### Chunk 5: Observer Negative-Test Harness and Scoped Entrypoint

- **Goal:** Add fixture/static proof for the observer policy and a separately gated host-scoped entrypoint without exposing a generic SSH runner.
- **Files to change:** one focused observer policy test file and one scoped provisioning/validation playbook.
- **Symbols to add/change:** inventory-projection assertions; positive fixed-collector case; negative shell, PTY, forwarding, arbitrary-command, extra-argument, environment, sudo, file, editor, package, service, and destination cases; per-host disablement contract.
- **Implementation shape:** fixture/static tests run locally. Any future live adversarial tasks remain behind explicit authorization variables and `no_log`; default execution stops before connection.
- **Validation:** focused test, Ansible lint/syntax, no generic `ssh`/shell task scan, no `hosts: all`, exact limit/role checks, `rtk git diff --check`, focused diff.
- **Stop condition:** local tests prove policy construction is deny-by-default; observer access is not deployed or live-tested.

#### Chunk 6: Neutron Agent Diagnostic Thin Slice

- **Goal:** Add the fixed read-only `neutron_agent_health` diagnostic and synthetic contract tests without registering or deploying it.
- **Files to change:** proposed revised diagnostic source file and one focused fixture/static test file.
- **Symbols to add/change:** `neutron_agent_health` structured output, fixed read operation, field minimization, deterministic ordering, record/output bounds, unavailable mapping, and secret-like redaction tests.
- **Implementation shape:** no public arguments; no raw passthrough; no mutation verbs; no inherited profile selection inside the script. A missing approved profile/service returns the frozen unavailable shape. If full implementation cannot be safe in this chunk, use a valid executable stub that returns explicit `unavailable`, never success.
- **Validation:** `bash -n` or Python compile as applicable, focused fixture tests, diagnostic safety scan, schema/redaction/truncation tests, focused diff.
- **Stop condition:** the unregistered diagnostic is locally contract-valid and read-only; runner behavior and live OpenStack remain unchanged.

#### Chunk 7: Runner Profile Isolation and Fourth-Tool Registration

- **Goal:** Extend the closed runner for one explicit operator-profile tool while preserving the three existing project-reader tools and all Phase 04 guarantees.
- **Files to change:** `aiops_tool_runner.py` and `tool_registry.json`; deployment allowlist changes should be a separate small follow-up if required by repository validation.
- **Symbols to add/change:** proposed `OPERATOR_READER_PROFILE`, closed profile descriptors, `neutron_agent_health` name/target/risk contract, per-tool `build_child_environment(tool)`, exact tool count/set, no-parameter rule, and explicit profile unavailable/integrity handling.
- **Implementation shape:** define profile resolver before wiring execution. Existing tools map only to project-reader; Neutron maps only to operator-reader. Unknown/missing profiles fail before target execution. Registry defaults do not imply fallback.
- **Validation:** focused runner request/execution/result/audit/profile-isolation tests, existing three-tool regression tests updated only for intentional four-tool contract, Python compile, JSON parse, forbidden override scan, focused diff.
- **Stop condition:** all focused tests pass; the source registry exposes exactly four reviewed tools and no host/generic capability; no deployment occurred.

#### Chunk 8: Deployment Allowlist, Static Acceptance, and Evidence-Backed Reconciliation

- **Goal:** Complete local deployment metadata wiring and static Steps 1–4 acceptance, then stop before any live operation unless separately authorized.
- **Files to change:** runner/diagnostic role defaults and tasks as narrowly required; one focused static integration test; Phase 06 plan checkboxes only when supported by reviewed evidence.
- **Symbols to add/change:** exact fourth target/file allowlists, root ownership/modes, default-disabled deployment gates, profile isolation assertions, prohibited-capability scan, and outcome-only acceptance fields.
- **Implementation shape:** no host tools are registered. Static completion does not check live profile, observer, mutation-denial, or Neutron success items. Live claims remain unchecked until separate authorized chunks produce owner-accepted evidence.
- **Validation:** targeted Ansible/Python/shell/JSON checks, focused regression suites, `rtk git diff --check`, staged and unstaged diff review, secret/path/capability scan.
- **Stop condition:** static implementation is complete and reviewable, or a concrete blocker is recorded. Do not proceed to deployment, API calls, observer provisioning, adversarial SSH tests, audit inspection, or Step 5.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Implement Phase 06 Steps 1–4 from docs/ai-ops-revised/implementation-plan/06-restricted-operator-and-host-diagnostics.md using docs/ai-ops-revised/implementation-plan/ads/06-00-restricted-operator-and-host-diagnostics-steps-01-to-04-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm current repository state, Phase 05 acceptance prerequisites, selective-reuse disposition, operator-reader ownership/scope/profile lifecycle, maintained inventory and service-placement source, observer account/key/forced-command/sudo policy, Neutron-agent output bounds, evidence ownership, and separate authorization gates. Do not inspect protected values, deploy, authenticate, contact hosts, execute the runner, inspect raw audits, create credentials/keys/accounts, or perform live validation. Stop with evidence and blockers.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Execute Chunk 1 only.
Do not continue to Chunk 2.
Create only the non-activation Steps 1–4 operations contract and any explicitly approved exact-path selective-reuse manifest amendment. Run targeted Markdown/manifest validation, review staged and unstaged diffs, and stop. Do not implement or perform live operations.
```

For later implementation chunks:

```text
Use the chunked-implementation skill.
Execute only the next explicitly approved chunk from the Phase 06 Steps 1–4 ADS.
Do not continue to another chunk. Preserve compile/syntax-safe fail-closed behavior, run the chunk-specific targeted validation, review staged and unstaged diffs, and stop with a handoff. Treat profile materialization, OpenStack authentication/API calls, mutation-denial probes, observer provisioning, SSH/sudo adversarial checks, audit inspection, and revocation as separate live authorization scopes.
```

### X. Conclusion and Next Steps

This design adds higher visibility as two optional authority planes rather than broadening the project-reader default. It requires an empirical need before operator-reader creation, exact per-tool profile selection with a fresh child environment, inventory-derived host destinations, a fixed-purpose observer collector with shell/forwarding/sudo escape denials, and one bounded `neutron_agent_health` tool that remains unavailable safely when its optional profile or policy is absent.

The next action is Chunk 0 discovery and decision confirmation only. Current repository evidence intentionally blocks implementation assumptions: the existing identity role is project-reader-specific, the runner is hardcoded to three project-reader tools, no revised observer inventory exists, historical Phase 06 assets remain unselected candidates, and exact operator/observer ownership and Neutron output bounds are not yet frozen. These are fail-closed design gates, not permission to reuse historical authority or introduce generic access.
