## Architectural Design Specification: Minimal Revised Runtime Foundation and Isolation Acceptance

**Source:** `docs/ai-ops-revised/implementation-plan/01-baseline-and-runtime-foundation.md`, Steps 4–6

**Goal:** Create and validate the smallest namespace-safe foundation for the isolated `assistant02` observer runtime, establish workspace, ownership, evidence, and rollback conventions, and prove Keystone-only management reachability without installing credentials or activating diagnostics, a runner, MCP, provider integration, egress policy, or restricted host access.

---

### I. Overview and Contract

This ADS begins where `01-00-selective-reuse-and-runtime-placement-ads.md` stops. Steps 1–3 fixed the historical provenance, selective-reuse boundary, revised namespace, and intended placement. Steps 4–6 may now implement only the foundation needed by later phases:

```text
approved assistant02 placement
  -> namespace-safe inventory and fail-closed foundation entrypoint
  -> minimal account, workspace, permissions, and baseline tooling
  -> credential-free TCP check to Keystone
  -> isolation, exclusion, compatibility, and rollback evidence
```

The foundation is infrastructure preparation, not diagnostic authority. Successful completion creates no OpenStack identity, cloud profile, diagnostic script, generic executor, runner, registry, MCP process, network listener, provider/model client, egress policy, host-observer access, or remote-operation path.

#### Scope boundary

Included:

* confirm `assistant02` exists or is explicitly designated, is separate from `assistant01`, and has no OpenStack or observability role
* replace the unsafe historical-shaped revised scaffold with a minimal `ai_ops_assistant` inventory and entrypoint
* create the `aiops_assistant` system account/group and revised runtime workspace
* define future artifact locations and least-privilege ownership without placing credentials or evidence in Git
* install only the baseline packages required by FR-004 and record resolved versions
* perform unauthenticated TCP reachability verification from `assistant02` to Keystone at `controller01:5000`
* prove excluded capabilities and historical identifiers are absent from the foundation
* preserve existing bootstrap, deployment, observability, Molecule, and historical AI-OPS paths
* define repeatable validation, redacted evidence, and revised-only rollback

Excluded:

* creating or installing OpenStack credentials, tokens, keys, or cloud profiles
* authenticating to Keystone or invoking any OpenStack API operation
* copying any `reference-only`, `candidate`, or `excluded` prior implementation file
* installing diagnostic scripts or implementing Phase 03 behavior
* implementing a runner, registry, audit-event writer, MCP adapter, service, listener, or registration
* configuring provider/model egress, tenant-network access, firewall policy, remote bridges, wheelhouses, or device authentication
* enabling restricted SSH/sudo or host-observer diagnostics
* modifying `ansible/ai_ops_runtime/`, `assistant01`, control-plane hosts, OpenStack resources, or existing lab entrypoints
* treating prior-runtime tests or logs as revised acceptance evidence

#### Placement gate

Implementation is blocked until Chunk 0 confirms, by an approved inventory filename/classification procedure that does not expose protected values:

1. `assistant02` resolves to a distinct host from `assistant01`;
2. `assistant02` has no controller, compute, storage, Ceph, database, message-bus, observability, or other control-plane role;
3. `ai_ops_assistant` is unique and contains only the revised observer host;
4. the management path from `assistant02` to the Keystone endpoint can be evaluated without adding a route or firewall rule; and
5. no revised identifier collides with historical runtime state.

A collision or missing host keeps Step 4 pending. It does not authorize renaming inventory, provisioning a VM, or changing protected values without a separate approved decision.

#### Namespace contract

The following values are concrete because they are established by the placement contract:

| Concern | Revised value | Foundation behavior |
| --- | --- | --- |
| Repository root | `ansible/ai_ops_assistant/` | Contains only revised inventory, role, setup, and validation automation. |
| Inventory group | `ai_ops_assistant` | Contains only `assistant02`. |
| Host identity | `assistant02` | Separate observer host with no control-plane role. |
| Runtime root | `/opt/openstack-ai-ops-assistant` | Root for revised runtime-managed state only. |
| Runtime user/group | `aiops_assistant` | Owns only revised workspace and future approved artifacts. |
| Future credential profile | `aiops-assistant-project-reader` | Name reserved only; no file or credential is created in Phase 01. |
| Audit root | `/opt/openstack-ai-ops-assistant/audit` | Directory convention only; no runner audit event is emitted. |
| MCP registration | separately named local stdio registration | Namespace reserved only; no config, listener, or process is created. |

#### Workspace and permission contract

Exact child names below are **proposed contracts** and must be confirmed in Chunk 0 before implementation. They translate Step 5’s artifact classes into non-overlapping locations:

| Artifact class | Proposed path | Owner/group | Proposed mode | Phase 01 content |
| --- | --- | --- | --- | --- |
| Runtime root | `/opt/openstack-ai-ops-assistant` | `root:aiops_assistant` | `0750` | Directories and version evidence only. |
| Future approved scripts | `.../scripts/approved` | `root:aiops_assistant` | `0750` directory | Empty; Phase 03 owns content. |
| Future diagnostic output | `.../output` | `aiops_assistant:aiops_assistant` | `0750` directory | Empty. |
| Future credential profiles | `.../credentials` | `aiops_assistant:aiops_assistant` | `0700` directory | Empty; Phase 02 owns content. |
| Future audit events | `.../audit` | `aiops_assistant:aiops_assistant` | `0700` directory | Empty; Phase 04 owns event format/content. |
| Revised tests | `.../tests` | `root:aiops_assistant` | `0750` directory | Empty until owning phases add tests. |
| Future local MCP config | `.../mcp` | `aiops_assistant:aiops_assistant` | `0700` directory | Empty; Phase 07 owns content. |
| Foundation evidence | `.../evidence/foundation` | `root:aiops_assistant` | `0750` directory | Redacted, non-secret foundation facts only. |

The role must not use recursive ownership or mode changes outside the revised runtime root. Empty reserved directories do not authorize future content or activation.

#### Baseline tooling contract

FR-004 confirms these capability classes: Python, OpenStack CLI, OpenStack SDK, SSH client, curl, JSON tooling, log-search tooling, and version-control tooling. Exact distribution package names and version policy are **conceptual contracts** pending target-OS confirmation in Chunk 0.

The package allowlist must:

* map every package to one FR-004 capability;
* use the target distribution’s configured repositories only;
* avoid adding PPAs, package repositories, downloaded standalone binaries, Node.js, compilers, archive tools, servers, firewall packages, or unrelated conveniences;
* install an SSH client, never an SSH server, for this foundation;
* record configured package names and resolved installed versions in redacted evidence;
* avoid promising an exact package version unless that version is available and intentionally pinned by the lab’s repository policy.

#### Ansible module and variable contracts

**Module Contract (Conceptual):** proposed role `ai_ops_assistant_foundation` under `ansible/ai_ops_assistant/roles/`.

Inputs:

* approved inventory membership and host identity
* revised runtime root, user, group, and workspace definitions
* baseline package allowlist
* Keystone endpoint host and TCP port
* explicit foundation-enable and validation-mode controls

Outputs/state:

* idempotent account, directory, permission, and package state
* no credential, diagnostic, service, listener, firewall, or OpenStack state
* redacted validation facts suitable for evidence review

**Stub Behavior Contract (Conceptual):** the first role stub must validate namespace constants and then stop with a clear temporary failure such as `ERR_FOUNDATION_NOT_IMPLEMENTED` (proposed). Returning success would falsely imply that the foundation exists. The stub is replaced by independently validated workspace behavior before any live deployment is accepted.

**Entrypoint Contract (Conceptual):** the minimal setup play targets only `ai_ops_assistant`, uses `become` only for approved account/package/workspace tasks, loads no committed secret file, and invokes only the revised foundation role. It must not invoke the shared `common` role.

**Verification Contract (Conceptual):** a separate validation play performs non-mutating assertions, package/version queries, file metadata checks, process/listener absence checks, and a TCP-only Keystone check. It must not authenticate, write OpenStack state, print protected inventory values, or widen connectivity.

### II. Observed Evidence and Assumptions

#### Observed evidence

* `01-baseline-and-runtime-foundation.md` Steps 4–6 require a minimal runtime, workspace/ownership/evidence conventions, isolation checks, narrow Ansible validation, and lab compatibility.
* `runtime-placement-contract.md` fixes `assistant02`, `ai_ops_assistant`, `/opt/openstack-ai-ops-assistant`, `aiops_assistant`, and the initial route to `controller01:5000`.
* `selective-reuse-manifest.md` classifies historical foundation defaults, workspace, tooling, setup, and aggregate task files as `reference-only`; they are not copy authority.
* The current `ansible/ai_ops_assistant/inventories/local/local.yml` still declares historical `assistant01`, `assistant`, `wheelhouse_builders`, and `ai_ops_host_observers` groups. It does not satisfy the revised inventory contract.
* The current revised `playbook_pre_setup.yml` targets `all`, loads `inventories/local/nodes.yml`, and invokes the shared `common` role.
* The shared `common` role can grow disks, change hostnames, install broad dependencies, modify cloud-init and PAM limits, configure firewall behavior, and reboot. Its dependency task also adds a Git PPA and installs unrelated packages/applications including an SSH server, build tools, archives, yq, and Node.js. It is too broad for this foundation.
* The current revised `common_secret.yml` contains credential-shaped Ansible connection variables. Even placeholder secret configuration is not an acceptable committed credential mechanism for the revised foundation.
* `ansible.cfg` resolves shared roles through `ansible/shared_resources/roles`; a revised local role path must therefore be confirmed by syntax validation rather than assumed to resolve automatically.
* Root `requirements.txt` exists and is the repository dependency source for an isolated Ansible validation environment.
* The worktree was clean at ADS discovery on branch `ai-ops-assistant-phase01` at `26f2de2`.

#### Assumptions

* `assistant02` is already provisioned or can be explicitly designated without this ADS provisioning a VM.
* Existing operator-controlled SSH bootstrap material can be supplied outside committed source. This ADS does not choose the secret injection mechanism.
* The target host uses a package manager supported by `ansible.builtin.package`; exact package names need target-OS confirmation.
* TCP success at the Keystone endpoint is sufficient for Phase 01. TLS, HTTP response, service catalog, and token behavior belong to later accepted contracts.
* Foundation evidence can be represented as sanitized keys, booleans, modes, package names/versions, and result statuses without addresses, passwords, tokens, or command output containing secrets.

#### Open confirmations for Chunk 0

1. Approve the protected-inventory inspection procedure and evidence classification.
2. Confirm `assistant02` existence, uniqueness, and absence from every protected/control-plane group.
3. Confirm whether `ansible/ai_ops_assistant/roles/` resolves automatically or the entrypoint must set a local role path by repository-supported means.
4. Confirm the target OS and exact FR-004 package mapping.
5. Confirm the proposed workspace child paths and modes.
6. Confirm the operator-supplied Ansible transport/authentication mechanism without committing secret variables.
7. Confirm whether Keystone endpoint input is a protected inventory reference, resolvable management hostname, or another approved non-secret variable; never record its protected value in evidence.
8. Confirm whether an existing host or route violates the denied-path contract.

Any unresolved placement, role-resolution, secret-injection, or package decision blocks live deployment but does not block documentation-only contract work.

### III. Required Technical Dependencies and Imports

#### Confirmed repository dependencies

* `docs/ai-ops-revised/prd.md` — FR-001 through FR-004 and AC-001, AC-002, AC-022
* `docs/ai-ops-revised/implementation-plan/00-implementation-overview.md`
* `docs/ai-ops-revised/implementation-plan/01-baseline-and-runtime-foundation.md`
* `docs/ai-ops-revised/implementation-plan/ads/01-00-selective-reuse-and-runtime-placement-ads.md`
* `docs/ai-ops-revised/runtime/runtime-placement-contract.md`
* `docs/ai-ops-revised/runtime/selective-reuse-manifest.md`
* `ansible/ai_ops_assistant/` current scaffold, which must be reviewed rather than trusted
* `ansible.cfg` and root `requirements.txt` for repository-supported Ansible resolution
* protected `inventories/local/nodes.yml` by approved filename/classification access only

#### Proposed implementation dependencies

* Ansible built-in modules only where practical: assertions, account/group, file, package, package facts, stat, service facts, command facts with `changed_when: false`, and TCP wait/check modules
* no new collection, Python runtime dependency, package repository, downloaded binary, daemon, or network service unless Chunk 0 proves it is already required by repository-native validation
* an isolated `/tmp` Python virtual environment for Ansible syntax validation, populated from root `requirements.txt`

### IV. Step-by-Step Procedure / Execution Flow

1. Reconfirm branch, `HEAD`, clean worktree, and immutability of historical/runtime and protected inventory paths.
2. Apply the approved inventory-classification procedure without printing protected values.
3. Fail closed unless `assistant02` is distinct, belongs only to `ai_ops_assistant`, and has no control-plane or historical assistant role.
4. Record the final package mapping, workspace layout, permission matrix, evidence schema, transport boundary, and rollback contract.
5. Add a local revised foundation role with namespace assertions and a temporary explicit failure.
6. Replace the scaffold inventory and entrypoint so only `ai_ops_assistant`/`assistant02` can invoke the revised role; remove committed credential-shaped configuration from the revised scaffold.
7. Implement the system group/user and revised workspace with exact non-recursive ownership and modes.
8. Implement only the approved FR-004 package allowlist using existing OS repositories and record resolved package versions.
9. Add a non-mutating validation entrypoint that verifies identity, inventory scope, workspace metadata, package presence/version, forbidden path/process/listener absence, and TCP reachability to Keystone.
10. Run syntax and inventory checks locally before any live execution.
11. Obtain explicit approval for the live foundation play. Use Ansible check mode first where module behavior is reliable; review the proposed change set.
12. Apply only the minimal foundation to `assistant02`; never use a broad host pattern.
13. Run the non-mutating validation entrypoint and capture redacted evidence outside committed source.
14. Confirm historical source/runtime, protected inventory, controller/compute/storage/Ceph/provider/network roles, bootstrap, observability, and Molecule entrypoints remain unchanged.
15. Re-run the foundation to prove idempotency; unexpected changes fail acceptance.
16. Reconcile Steps 4–6 and the Phase 01 DoD only where live and static evidence supports completion.
17. Stop before Phase 02 credentials or any diagnostic authority is introduced.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| --- | --- | --- | --- |
| Placement | `assistant02` is missing, aliases `assistant01`, or has another lab role | Stop before inventory or host mutation; request corrected placement | `ERR_FOUNDATION_PLACEMENT` (proposed) |
| Inventory safety | Protected values would need to be printed or copied | Stop and use only approved classification evidence | `ERR_PROTECTED_INVENTORY_ACCESS` (proposed) |
| Namespace | Revised group, user, root, profile, audit, or MCP identity collides | Stop; update the placement contract before implementation | `ERR_FOUNDATION_NAMESPACE_COLLISION` (proposed) |
| Entrypoint | Play targets `all` or invokes `common`/historical roles | Fail static validation; do not run the play | `ERR_FOUNDATION_TARGET_SCOPE` (proposed) |
| Stub | Compile-safe role is invoked before behavior exists | Return explicit temporary failure, never success | `ERR_FOUNDATION_NOT_IMPLEMENTED` (proposed) |
| Packages | Package has no FR-004 mapping or requires a new repository/download | Reject it or seek a separate approved dependency decision | `ERR_FOUNDATION_PACKAGE_SCOPE` (proposed) |
| Workspace | Task would recurse outside the revised root or loosen a sensitive mode | Fail before mutation and report the exact path | `ERR_FOUNDATION_PERMISSION_SCOPE` (proposed) |
| Secret boundary | Committed credential, key, password variable, token, or cloud profile is detected | Stop, remove only agent-created exposure, and initiate secret review if live | `ERR_FOUNDATION_SECRET_PRESENT` (proposed) |
| Reachability | `controller01:5000` is unreachable from `assistant02` | Record endpoint/status only; do not add routes or firewall rules | `ERR_KEYSTONE_TCP_UNREACHABLE` (proposed) |
| Reachability scope | Validation attempts authentication or contacts another endpoint | Abort validation and reject the scope expansion | `ERR_FOUNDATION_NETWORK_SCOPE` (proposed) |
| Exclusion | Diagnostic, runner, MCP, provider, orchestrator, egress, wheelhouse, or observer marker appears | Fail acceptance and remove only revised foundation changes | `ERR_EXCLUDED_CAPABILITY_PRESENT` (proposed) |
| Compatibility | Existing lab or historical AI-OPS path changes | Stop; do not reset unrelated work; identify the exact diff | `ERR_LAB_COMPATIBILITY` (proposed) |
| Idempotency | Second apply reports an unexplained change | Fail acceptance and isolate the non-idempotent task | `ERR_FOUNDATION_NOT_IDEMPOTENT` (proposed) |
| Rollback | Cleanup would affect `assistant01`, shared roles, or control-plane state | Refuse rollback and require a revised-only cleanup plan | `ERR_FOUNDATION_ROLLBACK_SCOPE` (proposed) |

### VI. Security, Integrity, Idempotency, and Cleanup

#### Security

* Do not read, print, copy, diff, or commit protected inventory values.
* Remove credential-shaped committed scaffold configuration; receive deployment transport credentials only through an approved external mechanism.
* Keep future credential and audit directories empty and mode-restricted in Phase 01.
* Use TCP reachability only. Do not install a cloud profile, request a token, or call Keystone APIs.
* Install no SSH server, public listener, MCP service, provider client, or egress policy.
* Do not add repositories or download binaries as an implicit package-install side effect.
* Validation output must omit IP addresses if classified, environment values, command lines with secrets, file contents, tokens, passwords, and keys.

#### Integrity

* Pin implementation review to the accepted plan and selective-reuse contracts.
* Never modify or copy from `ansible/ai_ops_runtime/` during foundation implementation.
* Map every revised file and package to a Phase 01 requirement.
* Use exact host/group limits and assert the target identity before privileged tasks.
* Validate owner, group, and numeric mode for every managed directory.
* Review all implementation and inventory diffs before live execution.

#### Idempotency

* Account/group, directory, and package tasks must use declarative Ansible modules.
* Directory tasks must converge without recursive mutation beyond their exact managed paths.
* Evidence generation must replace one bounded foundation record or create a uniquely identified run record outside Git; it must not append unbounded logs.
* A second foundation apply with identical inputs must report no changes.
* Validation tasks must always report `changed: false`.

#### Cleanup and rollback

Rollback is revised-only and ordered:

1. disconnect or destroy the explicitly designated revised observer host when host lifecycle is separately authorized; otherwise do not destroy it;
2. remove only the revised role-managed packages if package ownership and shared use are proven safe;
3. remove only `/opt/openstack-ai-ops-assistant` and `aiops_assistant` account/group after confirming no later phase owns data there;
4. revert only revised inventory/automation state;
5. preserve redacted acceptance evidence according to the approved evidence policy;
6. never alter `assistant01`, historical runtime files, shared role behavior, OpenStack resources, network roles, or control-plane services.

If selective package removal is unsafe, leave packages installed, disconnect the revised runtime, and record the residual state rather than risking shared-host damage.

### VII. Validation Strategy

Validation is chunk-aware. No command that contacts a host or applies Ansible is authorized until its chunk is explicitly approved.

#### Documentation and repository state

```bash
rtk git status --short
rtk git diff --check
rtk git diff -- docs/ai-ops-revised/implementation-plan/ads/01-01-minimal-runtime-foundation-and-isolation-ads.md
rtk git diff --exit-code -- ansible/ai_ops_runtime inventories/local/nodes.yml
```

#### Static inventory and exclusion checks

Use inventory graph/list output only after confirming it will not expose protected variables:

```bash
rtk ansible-inventory -i ansible/ai_ops_assistant/inventories/local/local.yml --graph
rtk grep -RniE 'assistant01|wheelhouse|host_observer|provider|orchestrator|egress|device_auth|tool_runner|mcp|credential|openrc' ansible/ai_ops_assistant
```

Every match must be classified. Reserved empty credential/audit/MCP path names may be allowed by the approved workspace contract; activation, implementation, secret values, and historical identifiers are not.

#### Ansible syntax in an isolated environment

Create and use a temporary virtual environment as required by repository edit discipline:

```bash
rtk python3 -m venv /tmp/openstack-lab-ai-ops-foundation-venv
. /tmp/openstack-lab-ai-ops-foundation-venv/bin/activate
rtk python -m pip install -r requirements.txt
rtk ansible-playbook --syntax-check -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_pre_setup.yml
rtk ansible-playbook --syntax-check -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_validate_foundation.yml
```

The validation playbook path is **proposed**. Adjust it only if Chunk 0 approves another repository-conforming name.

#### Targeted static contract checks

Verify that:

* the setup play targets exactly `ai_ops_assistant`, not `all`;
* only the proposed revised role is called;
* no committed secret vars file is loaded;
* each package maps to FR-004;
* no task configures repositories, downloads binaries, changes disks/hostnames/cloud-init/PAM/firewall, reboots, starts services, or installs SSH server;
* no source file from the historical runtime was copied;
* all managed filesystem paths are under `/opt/openstack-ai-ops-assistant` except the approved system account/group and package database effects.

#### Approved live checks

After explicit approval and check-mode review:

```bash
rtk ansible-playbook --check --diff --limit assistant02 -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_pre_setup.yml
rtk ansible-playbook --limit assistant02 -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_pre_setup.yml
rtk ansible-playbook --limit assistant02 -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_validate_foundation.yml
rtk ansible-playbook --limit assistant02 -i ansible/ai_ops_assistant/inventories/local/local.yml ansible/ai_ops_assistant/playbook_pre_setup.yml
```

The final apply must report no changes. Exact credential injection arguments are intentionally omitted and must not be committed or pasted into evidence.

#### Evidence schema

Each acceptance record must contain only:

* source revision and foundation contract revision
* UTC timestamp and non-secret run identifier
* target identity label `assistant02` and group label `ai_ops_assistant`
* boolean role-separation result without protected inventory values
* workspace paths, owner/group labels, and numeric modes
* approved package names and resolved versions
* Keystone endpoint label/port and status, without credentials or response body
* excluded-capability scan statuses
* syntax, check-mode, apply, validation, idempotency, and compatibility statuses
* unresolved gates and rollback status

Evidence must not be committed until its redaction classification is reviewed.

#### Final diff review

```bash
rtk git diff --check
rtk git status --short
rtk git diff -- ansible/ai_ops_assistant docs/ai-ops-revised
rtk git diff --exit-code -- ansible/ai_ops_runtime inventories/local/nodes.yml
```

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement Steps 4–6 in one pass.

#### Chunk 0: Placement, Inventory, and Integration Confirmation

- **Goal:** Resolve all host-placement, protected-inventory, role-resolution, package, workspace, transport, and endpoint-input gates before edits.
- **Files to read:** this ADS; placement contract; selective-reuse manifest; revised scaffold; `ansible.cfg`; root `requirements.txt`; protected inventory only under the approved filename/classification procedure.
- **Commands:** branch/HEAD/status; bounded path and symbol discovery; safe inventory graph/classification checks; package/OS facts only if host inspection is explicitly approved.
- **Evidence to confirm:** `assistant02` uniqueness and role separation; `ai_ops_assistant` membership; exact package mapping; role path resolution; workspace paths/modes; no committed-secret transport; Keystone input classification.
- **Validation:** no file edits and no Ansible play execution.
- **Stop condition:** all gates are explicit. Any unresolved placement or secret-handling item blocks Chunk 1.

#### Chunk 1: Foundation Operations Contract

- **Goal:** Record final workspace, package, evidence, transport, activation, and rollback decisions before executable automation.
- **Files to change:** proposed `docs/ai-ops-revised/runtime/foundation-operations-contract.md` only.
- **Symbols to add/change:** no executable symbols; final package allowlist, directory permission matrix, evidence schema, protected-input policy, live-execution gate, rollback ownership.
- **Implementation shape:** documentation only; preserve conceptual labels for unresolved implementation details and fail closed on missing decisions.
- **Validation:** `rtk git diff --check`; cross-reference and forbidden-scope scans; implementation/inventory diff must remain empty.
- **Stop condition:** maintainers can determine exactly what may be created, validated, recorded, and removed; no automation changed.

#### Chunk 2: Revised Role Contract and Fail-Closed Stub

- **Goal:** Introduce a syntax-valid local role contract without claiming foundation success.
- **Files to change:** proposed `ansible/ai_ops_assistant/roles/ai_ops_assistant_foundation/defaults/main.yml` and `ansible/ai_ops_assistant/roles/ai_ops_assistant_foundation/tasks/main.yml`.
- **Symbols to add/change:** proposed revised namespace variables, package/workspace structures, enable control, namespace assertions, and temporary `ERR_FOUNDATION_NOT_IMPLEMENTED` failure.
- **Implementation shape:** built-in assertions plus explicit temporary failure; no host state changes, imports, historical source, or external dependencies.
- **Validation:** YAML parse/lint if repository tooling exists; role path resolution through a minimal syntax harness; exclusion scan; diff review.
- **Stop condition:** role contracts are inspectable and syntax-valid, but deployment cannot return false success.

#### Chunk 3: Namespace-Safe Inventory and Entrypoint

- **Goal:** Replace historical-shaped scaffold targeting with the isolated revised host and role only.
- **Files to change:** `ansible/ai_ops_assistant/inventories/local/local.yml` and `ansible/ai_ops_assistant/playbook_pre_setup.yml`.
- **Symbols to add/change:** `ai_ops_assistant`, `assistant02`, exact host targeting, protected endpoint reference, and revised role invocation.
- **Implementation shape:** remove `assistant`, `assistant01`, wheelhouse, host-observer, `hosts: all`, shared `common` role, and committed secret-file loading from the execution path. Keep the explicit role failure from Chunk 2.
- **Validation:** safe `ansible-inventory --graph`; setup syntax check; target/role/forbidden-name scans; no live play.
- **Stop condition:** only `assistant02` can enter the foundation role and execution still fails safely before mutation.

#### Chunk 4: Credential-Free Transport Configuration Cleanup

- **Goal:** Remove credential-shaped committed scaffold variables and retain only approved non-secret connection defaults.
- **Files to change:** `ansible/ai_ops_assistant/inventories/local/group_vars/all/common_secret.yml` (delete unless Chunk 0 approves a non-secret replacement) and `ansible/ai_ops_assistant/inventories/local/group_vars/all/common_vars.yml`.
- **Symbols to add/change:** remove password/sudo-password placeholders; retain only approved transport settings that do not disable host identity verification without an explicit lab policy.
- **Implementation shape:** authentication material is externally supplied and absent from Git; do not add environment-variable secret names unless the operations contract approves them.
- **Validation:** secret-keyword diff review, inventory syntax/graph, no protected-value output, no live play.
- **Stop condition:** revised committed inventory contains no password, token, key, cloud profile, or credential value.

#### Chunk 5: Workspace and Ownership Slice

- **Goal:** Replace the temporary role failure with idempotent account/group and workspace creation only.
- **Files to change:** proposed role `defaults/main.yml` and `tasks/main.yml` only.
- **Symbols to add/change:** validated directory list, exact owner/group/mode contracts, account/group tasks, revised-root boundary assertions.
- **Implementation shape:** create `aiops_assistant` and only approved revised directories; no packages, network checks, files containing credentials, services, or recursive changes outside the root.
- **Validation:** syntax check; static managed-path/mode scan; explicitly approved check mode limited to `assistant02`; diff review.
- **Stop condition:** workspace state can converge independently, while tooling and reachability remain absent.

#### Chunk 6: Minimal Baseline Tooling Slice

- **Goal:** Install only the Chunk 0-approved FR-004 package allowlist and record resolved versions.
- **Files to change:** proposed role `defaults/main.yml` and `tasks/main.yml` only.
- **Symbols to add/change:** package allowlist and package/version evidence facts.
- **Implementation shape:** use configured OS repositories; no repository addition, direct download, build toolchain, SSH server, Node.js, daemon, firewall, reboot, diagnostics, or credentials.
- **Validation:** syntax check; package-to-FR mapping check; approved check mode and limited apply; package facts; second apply must be unchanged.
- **Stop condition:** required tooling capability exists with recorded versions and no unrelated package behavior.

#### Chunk 7: Non-Mutating Foundation Acceptance Slice

- **Goal:** Prove placement, workspace, tooling, exclusion, process/listener absence, and Keystone TCP reachability without authentication.
- **Files to change:** proposed `ansible/ai_ops_assistant/playbook_validate_foundation.yml` and, only if needed, one proposed validation task file under the revised role.
- **Symbols to add/change:** fail-closed assertions, metadata/fact queries, TCP check, redacted status output.
- **Implementation shape:** all validation tasks report unchanged; inspect metadata, not secret contents; contact only the approved Keystone TCP endpoint; write no committed evidence.
- **Validation:** syntax check; approved limited live validation; evidence redaction review; exclusion scan.
- **Stop condition:** AC-001/AC-002 foundation evidence exists, no diagnostic authority is present, and failures do not trigger network remediation.

#### Chunk 8: Isolation, Compatibility, Rollback, and Phase Reconciliation

- **Goal:** Complete Step 6 acceptance and update planning status only where evidence proves it.
- **Files to change:** `docs/ai-ops-revised/runtime/foundation-operations-contract.md` and `docs/ai-ops-revised/implementation-plan/01-baseline-and-runtime-foundation.md`.
- **Symbols to add/change:** acceptance evidence references, unresolved Phase 02 gates, and evidence-backed Step 4–6/DoD checkboxes.
- **Implementation shape:** run historical/revised/protected-path diff checks, existing-entrypoint preservation checks, idempotency review, revised-only rollback review, and stale/excluded capability scans. Do not check unsupported items.
- **Validation:** Markdown whitespace/link checks; full revised diff review; clean historical runtime and protected inventory diffs; no unexpected lab-path changes.
- **Stop condition:** Phase 01 is either evidence-backed complete or explicitly blocked with named gates. Stop before Phase 02.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline and post-edit-discipline if available.

Task:
Execute Chunk 0 only from docs/ai-ops-revised/implementation-plan/ads/01-01-minimal-runtime-foundation-and-isolation-ads.md.

Mode:
Discovery only. Do not edit files, run an Ansible play, provision a host, change inventory, or print protected values. Confirm assistant02 placement and role separation through an approved filename/classification procedure; confirm role resolution, target OS/package mapping, workspace permissions, external transport handling, and Keystone endpoint-input classification. Stop with explicit gates and evidence.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Execute Chunk 1 only.
Do not continue to Chunk 2.
Create only the foundation operations contract, run targeted Markdown and implementation-immutability checks, show the diff, and stop. Do not change inventory, Ansible automation, host state, credentials, or network state.
```

For every later chunk:

```text
Execute only the explicitly approved chunk.
Do not continue to the next chunk.
Use a temporary Python virtual environment for Ansible validation, run the chunk's narrow checks, review the exact diff, preserve protected values, and stop with a handoff. Never run a live play unless that chunk and command are explicitly approved.
```

### X. Conclusion and Next Steps

Steps 4–6 must establish a small, independently reviewable foundation rather than extend the existing historical-shaped scaffold. The revised runtime receives only a distinct host/group, tightly owned workspace, FR-004 tooling, redacted evidence conventions, and unauthenticated Keystone TCP reachability. Every diagnostic, credential, runner, MCP, provider, egress, host-observer, and remote-operation capability remains absent.

The next session must execute Chunk 0 only. The placement and protected-inventory gate is the first blocker; no automation or live host action is authorized by this ADS.