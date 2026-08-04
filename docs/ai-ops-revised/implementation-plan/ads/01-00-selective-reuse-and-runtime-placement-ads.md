## Architectural Design Specification: Goal-Aligned Prior-Source Catalog and Selective Reuse Boundary

**Source:** `docs/ai-ops-revised/implementation-plan/01-baseline-and-runtime-foundation.md`, Steps 1-3

**Goal:** Preserve the prior AI-OPS implementation as immutable historical evidence, catalog its capabilities at a fixed revision, approve a fail-closed path-level selective-reuse boundary for the diagnostic → runner → local MCP product path, and record revised runtime placement without copying or implementing runtime source.

---

### I. Overview and Contract

The revised product is not a full migration of `ansible/ai_ops_runtime/`. It is a bounded read-only assistant that progresses through three authority-preserving layers:

```text
reviewed manual diagnostics -> one deny-by-default runner/registry -> local stdio MCP over that runner
```

The prior tree is a read-only source catalog. Git provenance preserves it; destination path parity is neither required nor desired. A prior asset may enter the revised namespace only when the phase that owns the capability confirms its current requirement, dependency closure, required isolation changes, and independent validation.

#### Scope boundary

Included in this ADS:

* pinning the prior source revision and tree identity
* inventorying tracked paths by capability without reading protected values
* defining selective-reuse and exclusion dispositions
* identifying initial path-level candidates for later diagnostics, runner, restricted-host, and MCP phases
* explicitly excluding unrelated provider, orchestrator, egress, device-auth, wheelhouse, remote-operation, and retirement capabilities
* recording revised runtime placement and initial Keystone-only management reachability
* defining static checks that fail if later work widens selection without an approved manifest change

Excluded from this ADS:

* copying any implementation file into `ansible/ai_ops_assistant/`
* changing the existing revised scaffold
* provisioning or starting a runtime host
* installing packages or credentials
* activating diagnostics, runner, MCP, host access, provider integration, egress, or remote operation
* running an Ansible playbook against a host
* modifying `ansible/ai_ops_runtime/`

#### Provenance contract

The catalog must record:

* accepted repository revision
* prior runtime tree identity
* tracked source path
* capability classification
* current revised requirement or explicit lack of requirement
* owning implementation phase
* disposition
* known direct dependency or coupling concern
* whether content review is deferred to the owning phase

Historical tests, documents, and evidence remain attached to the prior baseline. They may inform later design but do not prove revised acceptance.

#### Selective-reuse contract

Allowed dispositions are:

| Disposition | Meaning |
| --- | --- |
| `candidate` | Potentially relevant, but not approved to copy or activate. |
| `selected-for-phase` | Approved for path-level review by the named phase; still not approved to activate. |
| `reference-only` | May inform a new implementation but must not be copied as implementation source. |
| `excluded` | Outside the approved product path; must not enter the revised namespace without a new approved requirement and plan change. |

Selection is fail-closed:

* absence from the manifest means `excluded`
* directory-level selection is prohibited unless every tracked descendant is independently classified
* selecting a file requires selecting or replacing its complete import, include, template, resource, and runtime-path dependency closure
* selection never includes protected inventory values, credentials, generated state, caches, logs, raw audit data, or unredacted evidence
* `selected-for-phase` authorizes later review, not immediate copying or execution

#### Goal-aligned capability boundary

Initial candidate boundary:

| Capability | Prior-source evidence | Planned owner | Initial disposition |
| --- | --- | --- | --- |
| Runtime workspace/tooling behavior | Prior assistant runtime defaults/tasks and setup entrypoint | Phase 01 Step 4 | `reference-only`; implement a minimal namespace-safe foundation from current requirements. |
| Three project-level diagnostics and shared helper | `project_resource_summary.sh`, `server_basic_info.sh`, `server_network_info.sh`, `lib/aiops_common.sh` | Phase 03 | `selected-for-phase`; content and dependencies reviewed before reuse. |
| Deny-by-default runner | `aiops_tool_runner.py` | Phase 04 | `selected-for-phase`; revise historical paths and validate only accepted tools. |
| Tool registry | `tool_registry.json` | Phase 04 | `reference-only`; derive a minimal revised registry because the prior registry includes Phase 06 tools and historical paths. |
| Neutron-agent and restricted-host diagnostics | Neutron script, host connector, observer role/templates | Phase 06 | `candidate`; remain absent until broader read-only controls are approved. |
| Local stdio MCP adapter | `aiops_mcp_server.py` | Phase 07 | `selected-for-phase`; dependency and contract review required. |
| MCP resources, policy, and lifecycle behavior | Curated resources, policy template, lifecycle task | Phase 07 | `candidate`; select only after content and dependency review. |
| Historical MCP assistant bridge | `aiops_assistant_bridge.py` and orchestrator imports | none in current path | `excluded`; coupled to historical orchestrator architecture. |

Explicitly excluded capability families:

* `files/orchestrator/`
* `roles/orchestrator_runtime/`
* `roles/orchestrator_egress/`
* `roles/orchestrator_wheelhouse_builder/`
* `roles/orchestrator_wheelhouse_transfer/`
* `roles/ai_client_runtime/` and provider gateway
* `roles/assistant_egress/`
* `roles/assistant_egress_validation/`
* `roles/assistant_device_auth_egress/`
* provider, orchestrator, egress, device-auth, wheelhouse, remote-acceptance, bridge-activation, and provider-retirement playbooks

The host-observer family is not globally selected. Its individual paths remain `candidate` for Phase 06 only and are absent from the Phase 01 foundation.

#### Revised namespace contract

The namespace remains distinct from the historical runtime:

| Concern | Prior | Revised contract |
| --- | --- | --- |
| Repository root | `ansible/ai_ops_runtime/` | `ansible/ai_ops_assistant/` |
| Active inventory group | `assistant` | `ai_ops_assistant` |
| Runtime host | `assistant01` | `assistant02` |
| Runtime root | `/opt/openstack-ai-ops` | `/opt/openstack-ai-ops-assistant` |
| Runtime user/group | `assistant` | `aiops_assistant` |
| Project-reader profile | `aiops-project-reader` | `aiops-assistant-project-reader` |
| Audit root | `/opt/openstack-ai-ops/audit` | `/opt/openstack-ai-ops-assistant/audit` |
| MCP identity | historical registration | separately named local stdio registration |

These values are planning contracts until Phase 01 Step 4 implements and validates the minimal foundation.

#### Runtime placement and network contract

The revised assistant is a separate VM or equivalent host outside the OpenStack control plane and separate from `assistant01`. Initial reachability is management-path access to Keystone at `controller01:5000` only. Later API routes must be justified by accepted diagnostics. Provider/model egress, tenant-network placement, and inbound/public MCP are not part of this slice.

**Function Signature Contract:** not applicable. This ADS creates planning and evidence contracts only; no application function, role, or executable is introduced.

### II. Observed Evidence and Assumptions

#### Observed evidence

* The PRD defines manual diagnostics, then a local safety runner, then MCP as an interface over the same runner.
* The implementation overview states MCP must not become a second execution path.
* The prior runtime contains provider gateway, orchestrator, egress, wheelhouse, device-auth, remote-operation, host-observer, diagnostics, runner, and MCP capabilities in one tree.
* The prior `assistant_runtime/tasks/main.yml` unconditionally includes workspace, scripts, tooling, and MCP lifecycle, so the role is not a minimal foundation boundary.
* The prior `tool_registry.json` includes both initial project tools and later restricted-host tools, and embeds historical runtime/source paths.
* The prior `aiops_assistant_bridge.py` imports `openstack_ai_ops_orchestrator`; it is not required for local stdio MCP.
* The prior `aiops_mcp_server.py` exposes a stdio adapter over the runner and is a plausible Phase 07 path-level candidate.
* `ansible/ai_ops_assistant/` currently contains only the pre-existing scaffold at `HEAD`; copied runtime work has been rolled back.

#### Assumptions

* Git history and a fixed tree identity preserve prior-source traceability without a duplicate destination tree.
* Later phases may choose new implementation over reuse when dependency removal would be riskier than a small focused implementation.
* Existing revised scaffold files require independent Step 4 review; their presence is not evidence that they satisfy this ADS.
* `assistant02` placement and revised namespace values remain approved unless repository evidence reveals a collision.

#### Chunk 0 confirmations

Before any evidence artifact is written, confirm:

1. the accepted source revision and branch
2. `ansible/ai_ops_runtime/` has no worktree diff
3. no copied implementation remains under the revised root
4. the diagnostic → runner → local stdio MCP sequence remains the approved product path
5. complete-tree copy and path-parity acceptance are rejected
6. excluded capability families require an explicit plan/requirement change before reconsideration

Any unresolved item blocks later chunks.

### III. Required Technical Dependencies and Imports

#### Repository dependencies

* `docs/ai-ops-revised/prd.md`
* `docs/ai-ops-revised/implementation-plan/00-implementation-overview.md`
* `docs/ai-ops-revised/implementation-plan/01-baseline-and-runtime-foundation.md`
* `docs/ai-ops-revised/implementation-plan/03-manual-diagnostic-toolbox.md`
* `docs/ai-ops-revised/implementation-plan/04-tool-runner-safety-gateway.md`
* `docs/ai-ops-revised/implementation-plan/06-restricted-operator-and-host-diagnostics.md`
* `docs/ai-ops-revised/implementation-plan/07-mcp-interface.md`
* tracked path names under `ansible/ai_ops_runtime/`
* current `ansible/ai_ops_assistant/` scaffold and `inventories/local/nodes.yml`

#### Tooling dependencies

* Git tree/path inspection at a fixed revision
* bounded path-name filtering with POSIX shell tools
* Markdown and diff hygiene checks
* no Python package, Ansible execution, or network access is required for this ADS

### IV. Step-by-Step Procedure / Execution Flow

1. Reconfirm branch, `HEAD`, worktree state, and prior-source immutability.
2. Record the accepted source revision and prior runtime tree identity.
3. Enumerate only Git-tracked prior paths and classify them by capability family.
4. Map relevant path-level candidates to current PRD requirements and owning phases.
5. Record direct coupling concerns before any selection, including imports, includes, templates, resource files, and historical paths.
6. Create the source capability catalog without copying implementation content.
7. Create the fail-closed selective-reuse manifest with explicit excluded families.
8. Verify the manifest does not select the historical orchestrator bridge or any provider, egress, wheelhouse, device-auth, remote-operation, or retirement path.
9. Record revised placement, namespace, initial Keystone route, and denied/unneeded paths.
10. Run static consistency checks across the PRD, overview, Phase 01, Phase 07, catalog, manifest, and placement contract.
11. Stop before changing `ansible/ai_ops_assistant/`, inventory, host state, credentials, network state, or runtime processes.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| --- | --- | --- | --- |
| Provenance | Source revision moves during cataloging | Stop and regenerate catalog evidence from one accepted revision | `ERR_SOURCE_REVISION_MOVED` (proposed) |
| Prior integrity | Prior runtime has a worktree diff | Stop; do not reset unrelated work | `ERR_PRIOR_SOURCE_CHANGED` (proposed) |
| Classification | A directory is selected without descendant review | Reject selection and classify paths individually | `ERR_SELECTION_TOO_BROAD` (proposed) |
| Dependency review | Selected file imports/includes an excluded capability | Reject or defer it; do not widen selection automatically | `ERR_EXCLUDED_DEPENDENCY` (proposed) |
| Requirement mapping | Candidate has no current PRD requirement or phase owner | Mark it `excluded` or `reference-only` | `ERR_UNOWNED_ASSET` (proposed) |
| Security | Protected or secret-bearing material is selected | Remove it from selection and retain only filename/classification evidence | `ERR_PROTECTED_SOURCE_SELECTED` (proposed) |
| Architecture | MCP selection includes the historical orchestrator bridge | Reject selection; retain local stdio boundary | `ERR_MCP_ORCHESTRATOR_COUPLING` (proposed) |
| Scope | Implementation source is copied during this ADS | Remove only agent-created destination changes and stop | `ERR_PREMATURE_IMPLEMENTATION` (proposed) |
| Placement | Revised host or namespace collides with prior runtime | Leave placement pending and request a distinct value | `ERR_RUNTIME_COLLISION` (proposed) |
| Network | Provider/model egress or public MCP is added | Reject scope expansion | `ERR_NETWORK_SCOPE_EXPANSION` (proposed) |

### VI. Security, Integrity, Idempotency, and Cleanup

#### Security

* Never display or copy prior credential values, tokens, keys, cloud profiles, raw logs, audit events, or unredacted evidence.
* Catalog protected files by path/classification only.
* Do not activate any prior or revised playbook.
* Keep provider credentials, remote-provider protocols, and egress controls outside the revised diagnostic contract.
* Require local stdio MCP; networking requires a separate approved design.

#### Integrity

* Fix repository revision and prior tree identity before classification.
* Treat prior source as immutable.
* Require every selected path to map to a current requirement and phase owner.
* Preserve excluded paths only in the historical source; do not duplicate them for traceability.
* Do not use destination path parity as acceptance evidence.

#### Idempotency

* Re-running path catalog generation at the same revision must produce the same path set.
* Re-running classification must not create destination source.
* Manifest updates replace explicit dispositions rather than append conflicting ones.
* Later selection expansion requires a reviewed manifest change before implementation.

#### Cleanup and rollback

* This ADS changes documentation/evidence only.
* Rollback removes or reverts only the newly created revised catalog, manifest, and placement documents.
* It never modifies or deletes the historical prior source.
* If protected content is exposed, stop and initiate credential-remediation procedures; ordinary document rollback is insufficient.

### VII. Validation Strategy

#### Repository state and prior immutability

```bash
rtk git branch --show-current
rtk git rev-parse HEAD
rtk git status --short
rtk git diff --exit-code -- ansible/ai_ops_runtime
rtk git status --short -- ansible/ai_ops_runtime
```

#### Tracked source catalog

```bash
rtk git ls-tree -r --name-only HEAD -- ansible/ai_ops_runtime
rtk git ls-tree HEAD ansible/ai_ops_runtime
```

Use bounded path-name searches to confirm capability families. Do not inspect protected inventory contents.

#### Selection checks

The catalog/manifest validation must prove:

* no whole-tree or directory wildcard is selected
* every selected path has a requirement and phase owner
* explicit excluded families remain excluded
* the MCP bridge and orchestrator package are not selected
* Phase 03 selection is limited to the shared helper and three initial project diagnostics
* Phase 04 registry is derived minimally rather than copied with later tools/historical paths
* no destination implementation file was created

#### Documentation consistency

Search revised planning documents for stale requirements such as:

```text
complete source-controlled copy
complete traceable source copy
path parity
copy-first
copied MCP implementation
```

Every remaining occurrence must either describe rejected historical policy or be revised.

#### Diff review

```bash
rtk git diff --check
rtk git diff --cached --check
rtk git status --short
rtk git diff -- docs/ai-ops-revised
rtk git diff --exit-code -- ansible/ai_ops_runtime ansible/ai_ops_assistant inventories/local/nodes.yml
```

The final command must show no implementation/inventory changes during this ADS revision and later evidence-only chunks.

### VIII. Thin Vertical Slice Chunk Design

The work must proceed through `chunked-implementation`. No chunk may copy or implement runtime source.

#### Chunk 0: Goal and Repository Decision Confirmation

- **Goal:** Confirm the revised product path, fixed source revision, rollback state, and rejection of complete-tree copying.
- **Files to read:** PRD, overview, Phase 01, Phases 03/04/06/07, prior tracked path names, revised scaffold path names.
- **Commands:** branch/HEAD/status, prior-source diff, tracked-path capability listing.
- **Evidence to confirm:** diagnostic → runner → local stdio MCP path; excluded families; no copied implementation remains.
- **Validation:** documentation notes and repository state only.
- **Stop condition:** decisions are explicit; no repository file is edited.

#### Chunk 1: Source Capability Catalog

- **Goal:** Record fixed provenance and classify prior paths by capability without selecting implementation.
- **Files to change:** proposed `docs/ai-ops-revised/runtime/source-capability-catalog.md`.
- **Symbols to add/change:** capability families, source paths, dependencies/coupling notes, candidate phase owners.
- **Implementation shape:** path-name and requirement evidence only; no protected values or destination source.
- **Validation:** prior-source immutability, catalog path existence against fixed Git revision, Markdown diff check.
- **Stop condition:** every prior tracked path belongs to a capability family; no reuse approval is implied.

#### Chunk 2: Fail-Closed Selective-Reuse Manifest

- **Goal:** Approve only goal-aligned path-level candidates and explicit exclusions.
- **Files to change:** proposed `docs/ai-ops-revised/runtime/selective-reuse-manifest.md`.
- **Symbols to add/change:** disposition vocabulary, selected paths, requirement, phase owner, dependency closure, activation gate.
- **Implementation shape:** select Phase 03/04/07 candidates as described in this ADS; keep Phase 06 deferred; exclude unrelated architecture.
- **Validation:** path-existence check, duplicate/disposition consistency, excluded-family scan, no destination source diff.
- **Stop condition:** absence means excluded, and no whole directory or historical bridge is selected.

#### Chunk 3: Manifest Consistency Gate Design

- **Goal:** Define a repeatable static check for provenance and selection boundaries before Step 4 implementation.
- **Files to change:** proposed documentation-only check contract in the manifest or a separately approved non-mutating script path.
- **Symbols to add/change:** accepted revision, selected-path allowlist, excluded-prefix list, required manifest fields.
- **Implementation shape:** fail closed on unknown paths, broad directories, missing owners, or excluded dependencies; print paths/reasons only.
- **Validation:** test the design with known selected, excluded, and unknown path examples; do not copy source.
- **Stop condition:** later implementation can verify selection without relying on agent memory.

#### Chunk 4: Runtime Placement and Namespace Contract

- **Goal:** Record distinct placement, namespace, ownership, initial Keystone route, and denied paths.
- **Files to change:** proposed `docs/ai-ops-revised/runtime/runtime-placement-contract.md`.
- **Symbols to add/change:** host, addresses, inventory group, runtime root/user/group, profile/audit/MCP names, route boundary.
- **Implementation shape:** evidence and decisions only; no inventory, VM, route, or credential mutation.
- **Validation:** collision search against repository inventory and prior identifiers; Markdown diff check.
- **Stop condition:** placement is explicit and implementation remains untouched.

#### Chunk 5: Steps 1-3 Acceptance Reconciliation

- **Goal:** Reconcile catalog, manifest, gate contract, and placement evidence with Phase 01 checkboxes.
- **Files to change:** Phase 01 plan and evidence documents only where evidence supports completion.
- **Symbols to add/change:** status/checklist evidence links; no executable symbols.
- **Implementation shape:** check only completed evidence tasks; leave Step 4 and later implementation unchecked.
- **Validation:** stale copy-first wording scan, cross-document consistency, prior/revised source diff, final Markdown hygiene.
- **Stop condition:** Steps 1-3 are evidence-backed and work stops before minimal runtime implementation.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline and post-edit-discipline if available.

Task:
Execute Chunk 0 only from docs/ai-ops-revised/implementation-plan/ads/01-00-selective-reuse-and-runtime-placement-ads.md.

Mode:
Single-chunk discovery. Do not edit files. Confirm the fixed source revision, prior-source cleanliness, rollback state, diagnostic -> runner -> local stdio MCP goal, selective-reuse rule, and explicit excluded capability families. Do not copy or implement runtime source. Stop after reporting evidence.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Execute Chunk 1 only.
Do not continue to Chunk 2.
Create only the source capability catalog, run targeted documentation and prior-source-integrity checks, review the diff, and stop. Do not copy implementation source.
```

### X. Conclusion and Next Steps

This ADS replaces complete-tree copying with fixed-revision provenance plus fail-closed, phase-owned, path-level selective reuse. It preserves the useful historical diagnostic, runner, and local stdio MCP evidence while excluding unrelated provider, orchestrator, egress, wheelhouse, device-auth, remote-operation, and bridge architecture.

The next implementation session must execute Chunk 0 only. Runtime source selection, copying, adaptation, provisioning, credentials, diagnostics, runner, and MCP activation remain prohibited until their owning chunks/phases establish the required evidence and validation boundary.
