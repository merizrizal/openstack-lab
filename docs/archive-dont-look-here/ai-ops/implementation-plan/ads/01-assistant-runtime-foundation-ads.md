## Architectural Design Specification: AI-OPS Assistant Runtime Foundation

**Source:** `docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md`

**Goal:** Create or designate the isolated assistant runtime for read-only AI-OPS diagnostics, document workspace conventions, verify management reachability, install baseline diagnostic tooling, and preserve the no-privileged-credentials boundary before Phase 02.

---

### I. Overview and Contract

Phase 01 establishes the safe place where later AI-OPS diagnostic tooling will run. It must not introduce read-only credentials, admin credentials, generic AI shell access, diagnostic scripts, a tool runner, MCP, host SSH diagnostics, or remediation automation.

The implementation should move from documentation-only foundation toward an evidence-backed runtime:

```text
runtime placement decision
  -> isolated runtime exists or is designated
  -> management reachability verified
  -> baseline diagnostic tooling installed and version-recorded
  -> workspace directories created
  -> prohibited capabilities documented and absent
  -> Phase 02 can create read-only credentials without ambiguity
```

#### Contracts

**Runtime Boundary Contract (Concrete from plan/docs):**

- The assistant runtime is a separate VM or equivalent isolated host.
- It is not `controller01`, `compute01`, `compute02`, `storage01`, `ceph01`, or another OpenStack control-plane/service node.
- It can reach OpenStack management APIs, especially Keystone on `controller01:5000`.
- It does not require tenant-network access for the first milestone.
- It contains no privileged OpenStack, SSH, database, RabbitMQ, or service credentials in Phase 01.

**Workspace Layout Contract (Concrete from `docs/ai-ops/runtime/README.md`):**

```text
/opt/openstack-ai-ops/
  README.md
  scripts/
    approved/
  diagnostics/
    raw/
    summaries/
  runbooks/
  credentials/
    profiles/
  audit/
  mcp/
```

**Vagrant Runtime Profile Contract (Conceptual, if repository-managed runtime is chosen):**

A proposed `assistant01` inventory entry would follow existing `inventories/local/nodes.yml` shape:

```yaml
assistant01:
  environment: assistant
  mgmtnet_ip_address: <192.168.121.x>
  provider_ip_address: <192.168.123.x>
  hostname: assistant01.local
  memory: <small-runtime-memory-mb>
  cpus: <small-runtime-cpu-count>
  disks: <small-runtime-root-disk-gb>
```

This contract is conceptual until a human confirms that the assistant should be provisioned by this repository rather than manually designated outside Vagrant.

**Function Signature Contract:** not applicable. Phase 01 is infrastructure/documentation/runtime setup. No concrete application functions, classes, or methods exist in the current repository for this phase.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops/implementation-plan/00-implementation-overview.md` places Phase 01 first in the build order: establish assistant runtime and workspace boundaries before credentials, scripts, runner, workflows, host diagnostics, or MCP.
- `docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md` defines Phase 01 scope: runtime placement, management reachability, baseline tooling, workspace conventions, and prohibited runtime capabilities.
- `docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md` currently marks initial runtime foundation notes, expected network path, workspace notes, prohibited capability notes, rollback notes, and workspace-conventions documentation as complete.
- `docs/ai-ops/runtime/README.md` documents default runtime placement as `assistant01` or equivalent isolated host, management API reachability, workspace layout, baseline tooling targets, prohibited capabilities, verification checklist, and rollback.
- `docs/architecture.md` documents existing lab networks:
  - management: `192.168.121.0/24`
  - provider: `192.168.123.0/24`
  - Vagrant private SSH convenience: `192.168.124.0/24`
- `docs/architecture.md` documents OpenStack API placement on `controller01`, including Keystone `5000`, Nova `8774`, Neutron `9696`, Cinder `8776`, and Placement `8778`.
- `inventories/local/nodes.yml` currently defines `controller01`, `compute01`, `compute02`, `storage01`, and `ceph01`; it does not define `assistant01`.
- `vagrant/base.rb` provisions VMs from `inventories/local/nodes.yml`, adds bridged provider networking, adds a derived private network, and loads provision commands from `vagrant/controller/provision.yml` by `environment`.
- `vagrant/controller/provision.yml` currently has entries for `controller` and `compute`, but no `assistant` entry.
- `vagrant/controller/Makefile` starts VMs by iterating `inventories/local/nodes.yml`.

#### Assumptions

- The first useful Phase 01 implementation can be manual or repository-managed; the implementation plan explicitly allows manual setup if full automation is deferred.
- If a repository-managed `assistant01` VM is added to `inventories/local/nodes.yml`, the `vagrant/controller/Makefile` loop may start it with other VMs unless gated by Makefile logic or explicit operator usage.
- The assistant runtime should not be added to OpenStack deployment Ansible groups unless a later phase explicitly designs such integration.
- Baseline tooling installation may be documented first and automated later.
- Actual Keystone/controller reachability cannot be checked from this repository alone; it requires a running lab and an assistant runtime.

### III. Required Technical Dependencies and Imports

#### Documentation dependencies

- `docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md`
- `docs/ai-ops/runtime/README.md`
- `docs/architecture.md`
- `docs/base-knowledge.md` if network/topology wording needs additional context

#### Runtime dependencies

The assistant runtime should eventually provide:

- Python 3
- Python virtual environment support
- package tooling for isolated environments
- OpenStack CLI
- OpenStack SDK
- SSH client for operator access only
- curl or equivalent HTTP client
- JSON parser
- fast text search
- Git client

#### Repository-managed VM dependencies, if selected

- `inventories/local/nodes.yml` for VM profile data
- `vagrant/controller/provision.yml` for environment-specific provisioning command stubs
- `vagrant/base.rb` behavior for networking and host entries
- `vagrant/controller/Makefile` behavior for start/teardown flow
- YAML parser validation, ideally via `yq`
- Ruby syntax validation for touched Vagrant files if any are edited

No source-code imports are required unless a later chunk adds scripts.

### IV. Step-by-Step Procedure / Execution Flow

1. Confirm whether the Phase 01 runtime will be manually designated or repository-managed as `assistant01`.
2. If manual:
   - Record the chosen host/VM, placement reason, and management network path in `docs/ai-ops/runtime/README.md` or a separate runtime evidence note.
   - Do not change Vagrant or Ansible inventories.
3. If repository-managed:
   - Add an `assistant01` profile to `inventories/local/nodes.yml` using a non-conflicting management/provider IP.
   - Add an `assistant` provisioning entry to `vagrant/controller/provision.yml` that remains minimal and does not install credentials.
   - Decide whether Makefile flow should start `assistant01` by default or only through an explicit target.
4. Create the runtime workspace on the actual runtime:
   - `/opt/openstack-ai-ops/scripts/approved/`
   - `/opt/openstack-ai-ops/diagnostics/raw/`
   - `/opt/openstack-ai-ops/diagnostics/summaries/`
   - `/opt/openstack-ai-ops/runbooks/`
   - `/opt/openstack-ai-ops/credentials/profiles/`
   - `/opt/openstack-ai-ops/audit/`
   - `/opt/openstack-ai-ops/mcp/`
5. Ensure writable directories are writable by the runtime user.
6. Ensure `credentials/profiles/` exists but is empty until Phase 02.
7. Install baseline tooling manually or through a minimal bootstrap script/runbook.
8. Record tool versions as runtime evidence.
9. Verify management reachability:
   - Keystone endpoint on management path
   - controller management address
   - no tenant-network requirement for first milestone
10. Confirm prohibited capabilities remain absent.
11. Update `01-assistant-runtime-foundation.md` checkboxes only where evidence exists.
12. Stop before Phase 02 credential creation.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| ----- | ------------ | ------------------- | ----------------------- |
| Placement decision | Runtime is accidentally placed on `controller01` or another service node | Reject placement and keep Step 1 unchecked | Report `ERR_RUNTIME_ON_CONTROL_PLANE` (proposed) with node identity and reason |
| Inventory addition | `assistant01` conflicts with existing IPs or hostnames | Stop before editing or revert the small chunk | Report conflicting field and candidate file |
| Vagrant provisioning | `assistant` environment is missing from `provision.yml` after inventory addition | Add minimal compile-safe provision entry in same chunk as inventory addition | Ruby/YAML validation remains actionable |
| Makefile behavior | `assistant01` starts unintentionally with default lab VMs | Do not modify default start behavior without explicit decision | Report `ERR_UNCONFIRMED_START_POLICY` (proposed) |
| Reachability | Runtime cannot reach Keystone/controller management address | Record failed endpoint and leave reachability checklist unchecked | Runtime remains Phase 01 incomplete |
| Tooling install | OpenStack CLI/SDK missing or broken | Record missing tool/version failure; do not proceed to credentials | Baseline tooling step remains unchecked |
| Credential boundary | Credentials appear in Phase 01 runtime | Stop; remove/revoke credentials before continuing | Report `ERR_CREDENTIALS_CREATED_TOO_EARLY` (proposed) |
| Workspace setup | Credential profile directory contains files before Phase 02 | Stop and inspect/remove unauthorized files | Keep credential-empty checklist unchecked |
| Safety boundary | Generic AI shell/SSH/OpenStack passthrough is introduced | Reject change; revert unsafe path | Report safety violation and affected file/tool |
| Documentation tracking | Checklist is checked without runtime evidence | Revert checkbox or add evidence note | Prevent false Phase 01 completion |

### VI. Security, Integrity, Idempotency, and Cleanup

#### Security

- Do not create OpenStack credentials in Phase 01.
- Do not install admin OpenStack credentials on the assistant runtime.
- Do not install root SSH keys for OpenStack nodes.
- Do not configure unrestricted sudo, database credentials, RabbitMQ credentials, or service credentials.
- Do not expose generic shell, SSH, OpenStack CLI passthrough, file-write, package-install, restart, database, or remediation tools to AI.
- Keep MCP inactive until trusted scripts and the safety gateway exist in later phases.

#### Integrity

- Checkboxes in `01-assistant-runtime-foundation.md` must reflect observed evidence, not intent.
- Runtime evidence should include exact endpoint names, tool versions, and workspace path checks.
- If repository-managed VM support is added, changes must preserve existing controller/compute/storage/Ceph behavior.

#### Idempotency

- Workspace creation should be safe to re-run with existing directories.
- Tool version recording should append dated evidence or replace a clearly labeled current-state section.
- Vagrant inventory changes should be additive and use a unique node name/IP.

#### Cleanup and rollback

- Documentation-only rollback: remove or update the Phase 01 runtime notes and uncheck unsupported checklist items.
- Runtime rollback: disconnect/destroy the assistant runtime and remove `/opt/openstack-ai-ops/` if created.
- Repository-managed VM rollback: remove `assistant01` inventory/provision entries and destroy the VM if it was started.
- If credentials already exist, rollback becomes a Phase 02 credential revocation task.

### VII. Validation Strategy

Validation is chunk-aware. Do not claim Phase 01 complete until the operational checks have evidence.

#### Documentation validation

- Review changed docs:

  ```bash
  rtk git diff -- docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md docs/ai-ops/runtime/README.md docs/ai-ops/implementation-plan/ads/01-assistant-runtime-foundation-ads.md
  ```

- Check whitespace:

  ```bash
  rtk git diff --check
  ```

- Scan for accidental secrets:

  ```bash
  rtk grep -RniE "OS_PASSWORD=|password:|token:|secret:|BEGIN (RSA|OPENSSH|PRIVATE) KEY|admin-openrc" docs/ai-ops
  ```

#### YAML/Vagrant validation, if repository-managed runtime is added

- Parse inventory:

  ```bash
  rtk yq '.' inventories/local/nodes.yml >/dev/null
  ```

- Parse Vagrant provision YAML:

  ```bash
  rtk yq '.' vagrant/controller/provision.yml >/dev/null
  ```

- Check Ruby syntax if `vagrant/base.rb` or `vagrant/controller/Vagrantfile` changes:

  ```bash
  rtk ruby -c vagrant/base.rb
  rtk ruby -c vagrant/controller/Vagrantfile
  ```

#### Runtime validation, executed on or against the assistant runtime

Exact commands may vary by runtime image, but evidence must show:

- runtime identity and hostname
- route or reachability to `controller01`
- Keystone endpoint reachability on `controller01:5000`
- tool versions for Python, OpenStack CLI/SDK environment, SSH client, curl, JSON parser, text search, and Git
- expected workspace directories exist
- `credentials/profiles/` is empty
- no privileged credentials are installed

#### Final review

- Re-check `docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md` so only evidence-backed checkboxes are checked.
- Run `rtk git status --short` and review all changed files before handoff.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass.

#### Chunk 0: Discovery and Integration Confirmation

- **Goal:** Confirm whether Phase 01 should stay manual or add repository-managed `assistant01` support.
- **Files to read:**
  - `docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md`
  - `docs/ai-ops/runtime/README.md`
  - `inventories/local/nodes.yml`
  - `vagrant/base.rb`
  - `vagrant/controller/provision.yml`
  - `vagrant/controller/Makefile`
- **Commands:**
  - `rtk git status --short`
  - `rtk grep -Rni "assistant01\|assistant" docs/ai-ops inventories vagrant 2>/dev/null`
  - `rtk yq '.' inventories/local/nodes.yml >/dev/null`
- **Evidence to confirm:**
  - No existing `assistant01` runtime profile conflicts.
  - Existing Vagrant flow reads `inventories/local/nodes.yml` and provision commands by `environment`.
  - Human decision on manual vs repository-managed runtime is captured.
- **Stop condition:** Report evidence and recommendation. Do not edit files.

#### Chunk 1: Runtime Evidence Note Contract

- **Goal:** Create a repository-backed place to record actual Phase 01 runtime evidence without adding credentials or automation.
- **Files to change:**
  - Proposed: `docs/ai-ops/runtime/evidence-template.md`
- **Symbols to add/change:** Not applicable; documentation contract only.
- **Implementation shape:** Add a template with sections for placement, network reachability, tool versions, workspace checks, credential absence, and prohibited-capability confirmation.
- **Validation:**
  - `rtk git diff -- docs/ai-ops/runtime/evidence-template.md`
  - `rtk git diff --check`
  - secret-like scan under `docs/ai-ops/runtime/`
- **Stop condition:** Evidence template exists and does not claim runtime checks have passed.

#### Chunk 2: Placement Decision Recording

- **Goal:** Record the chosen runtime placement and reason once the human confirms manual or repository-managed runtime.
- **Files to change:**
  - `docs/ai-ops/runtime/README.md`
  - `docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md`
- **Symbols to add/change:** Not applicable; checklist/status updates only.
- **Implementation shape:** Add a dated placement decision section. Check only Step 1 tasks that are supported by evidence.
- **Validation:**
  - `rtk git diff -- docs/ai-ops/runtime/README.md docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md`
  - `rtk git diff --check`
- **Stop condition:** Placement decision is documented, but reachability/tooling/workspace runtime checks remain unchecked unless independently verified.

#### Chunk 3: Optional Repository-Managed `assistant01` Stub

- **Goal:** Add minimal compile-safe Vagrant/inventory support only if repository-managed runtime is selected.
- **Files to change:**
  - `inventories/local/nodes.yml`
  - `vagrant/controller/provision.yml`
- **Symbols to add/change:**
  - Conceptual inventory key: `assistant01`
  - Conceptual provision key: `assistant`
- **Implementation shape:** Add `assistant01` with unique IPs and a small resource footprint. Add a no-credential `assistant` provision entry that only identifies the node or prepares for later manual setup. Do not install OpenStack credentials or AI tools in this chunk.
- **Validation:**
  - `rtk yq '.' inventories/local/nodes.yml >/dev/null`
  - `rtk yq '.' vagrant/controller/provision.yml >/dev/null`
  - `rtk git diff -- inventories/local/nodes.yml vagrant/controller/provision.yml`
- **Stop condition:** Inventory/provision YAML parses and the new VM is not added to OpenStack Ansible deployment groups.

#### Chunk 4: Runtime Workspace Setup Runbook

- **Goal:** Add manual commands/runbook to create `/opt/openstack-ai-ops/` directories safely on the runtime.
- **Files to change:**
  - Proposed: `docs/ai-ops/runtime/workspace-setup.md`
- **Symbols to add/change:** Not applicable; runbook only.
- **Implementation shape:** Document idempotent directory creation, ownership checks, empty credential profile check, and writable diagnostics/audit directories. Commands must be operator-run, not AI-exposed tools.
- **Validation:**
  - `rtk git diff -- docs/ai-ops/runtime/workspace-setup.md`
  - `rtk git diff --check`
  - manual review that no credentials or unsafe AI tool paths are introduced
- **Stop condition:** Runbook is ready for an operator, but no runtime checklist items are checked until executed evidence exists.

#### Chunk 5: Baseline Tooling Setup Runbook

- **Goal:** Document baseline tooling installation and version capture without adding credentials.
- **Files to change:**
  - Proposed: `docs/ai-ops/runtime/tooling-setup.md`
- **Symbols to add/change:** Not applicable; runbook only.
- **Implementation shape:** Include package categories, isolated Python environment target, OpenStack CLI/SDK install target, and version evidence capture. Explicitly state OpenStack commands may fail for missing credentials until Phase 02.
- **Validation:**
  - `rtk git diff -- docs/ai-ops/runtime/tooling-setup.md`
  - `rtk git diff --check`
  - secret-like scan under `docs/ai-ops/runtime/`
- **Stop condition:** Tooling runbook exists; actual installed/version-checked checkbox remains unchecked until evidence is recorded.

#### Chunk 6: Operational Evidence Update

- **Goal:** After the operator runs reachability, workspace, and tooling checks, update the plan checkboxes with evidence-backed status.
- **Files to change:**
  - `docs/ai-ops/runtime/evidence-template.md` or a dated copied evidence note
  - `docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md`
- **Symbols to add/change:** Not applicable; evidence and checklist only.
- **Implementation shape:** Record observed endpoint results, tool versions, directory checks, and credential absence. Check only satisfied tasks and DoD items.
- **Validation:**
  - `rtk git diff -- docs/ai-ops/runtime docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md`
  - `rtk git diff --check`
  - `rtk grep -RniE "OS_PASSWORD=|password:|token:|secret:|BEGIN (RSA|OPENSSH|PRIVATE) KEY|admin-openrc" docs/ai-ops/runtime docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md`
- **Stop condition:** Phase 01 checklist accurately reflects evidence. Stop before Phase 02 credentials.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Implement Phase 01 AI-OPS Assistant Runtime Foundation from docs/ai-ops/implementation-plan/ads/01-assistant-runtime-foundation-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm repository evidence and stop.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Execute Chunk 1 only.
Do not continue to Chunk 2.
After editing, run targeted validation and show git diff.
```

If repository-managed `assistant01` is selected later:

```text
Use the chunked-implementation skill.
Execute Chunk 3 only.
Do not continue to Chunk 4.
After editing, run YAML validation, review the diff, and stop.
```

### X. Conclusion and Next Steps

Phase 01 is partially documented but not operationally complete. The current repository already contains runtime foundation notes and updated checklist status. The next safest step is Chunk 0: confirm whether the assistant runtime should be manually designated or added as a repository-managed `assistant01` VM. After that decision, proceed one chunk at a time, keeping checkboxes evidence-backed and stopping before any Phase 02 credential work.
