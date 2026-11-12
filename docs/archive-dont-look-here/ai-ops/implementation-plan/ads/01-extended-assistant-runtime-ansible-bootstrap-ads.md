## Architectural Design Specification: Phase 01 Extended — Assistant Runtime Ansible Bootstrap

**Source:** Phase 01 side-quest derived from `docs/ai-ops/implementation-plan/ads/01-assistant-runtime-foundation-ads.md`, `docs/ai-ops/runtime/README.md`, and the repository-managed `assistant01` decision.

**Goal:** Add a narrow, idempotent Ansible bootstrap path for the repository-managed `assistant01` runtime so Phase 01 can create the workspace, install baseline tooling, capture evidence, and still avoid OpenStack credentials, generic AI tool execution, and remediation automation.

---

### I. Overview and Contract

This extended Phase 01 side-quest turns the documented runtime setup into operator-run Ansible automation for `assistant01`.

The side-quest does **not** replace the core Phase 01 safety boundary. It only automates repeatable setup steps that are already documented in:

- `docs/ai-ops/runtime/workspace-setup.md`
- `docs/ai-ops/runtime/tooling-setup.md`
- `docs/ai-ops/runtime/evidence-template.md`

Expected flow:

```text
assistant01 inventory profile exists
  -> operator starts assistant01
  -> Ansible targets only assistant01 / assistant group
  -> workspace directories are created idempotently
  -> baseline packages and isolated Python tooling are installed
  -> no credentials are installed
  -> evidence is captured
  -> Phase 01 checkboxes are updated only after evidence exists
```

**Runtime Boundary Contract (Concrete):**

- Target host is `assistant01` from `inventories/local/nodes.yml`.
- Target group should be `assistant` in a dedicated AI-OPS Ansible inventory.
- The playbook must not target `controller`, `compute`, `storage`, `ceph_adm`, or other OpenStack service groups.
- The playbook must not install OpenStack credentials, SSH private keys, database credentials, RabbitMQ credentials, service configuration secrets, MCP servers, generic shell tools for AI, or remediation tools.
- OpenStack CLI/SDK may be installed, but they remain unauthenticated until Phase 02.

**Ansible Layout Contract (Proposed):**

Follow existing repository convention of domain-specific Ansible directories:

```text
ansible/ai_ops_runtime/
  inventories/local/local.yml
  playbook_setup_assistant_runtime.yml
  roles/assistant_runtime/
    defaults/main.yml
    tasks/main.yml
    tasks/workspace.yml
    tasks/tooling.yml
    tasks/evidence.yml
```

The exact role/task split can be adjusted during implementation, but the target must remain scoped to `assistant01` only.

**Function Signature Contract:** not applicable. This side-quest is Ansible/YAML automation, not application code.

**Playbook Contract (Conceptual):**

```yaml
- name: Setup AI-OPS assistant runtime
  hosts: assistant
  become: true
  vars_files:
    - "{{ root_dir ~ '/inventories/' ~ target_env ~ '/nodes.yml' }}"
  roles:
    - role: assistant_runtime
```

The playbook should be syntax-valid before tasks become fully functional.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops/runtime/README.md` defines the runtime placement, workspace layout, baseline tooling target, prohibited runtime capabilities, verification checklist, and rollback behavior.
- `docs/ai-ops/runtime/workspace-setup.md` documents the required `/opt/openstack-ai-ops/` directory layout and checks.
- `docs/ai-ops/runtime/tooling-setup.md` documents baseline host packages, virtual environment setup, OpenStack CLI/SDK install, version capture, and expected missing-credential behavior.
- `docs/ai-ops/runtime/evidence-template.md` defines the evidence fields needed before Phase 01 can be marked complete.
- `inventories/local/nodes.yml` now contains `assistant01` with:
  - `environment: assistant`
  - `mgmtnet_ip_address: 192.168.121.20`
  - `provider_ip_address: 192.168.123.20`
  - `hostname: assistant01.local`
  - `memory: 4096`
  - `cpus: 2`
  - `disks: 25`
- `vagrant/controller/provision.yml` now contains a minimal `assistant` provision block that only echoes a message.
- `ansible.cfg` sets repository-level role paths and callback behavior.
- Existing Ansible areas are grouped by capability, for example `ansible/deploy_openstack/`, `ansible/deploy_prometheus/`, and `ansible/bootstrap_openstack/`.
- Existing inventories use `lab.children.<group>.hosts.<host>.ansible_host` and load node variables from `inventories/<target_env>/nodes.yml` through playbook `vars_files`.
- `vagrant/controller/Makefile` currently starts VMs by iterating `inventories/local/nodes.yml` and stops at Ceph nodes unless `WITH_CEPH` is set. Because `assistant01` is after `ceph01`, it is not reached by the default loop.

#### Assumptions

- The operator will start `assistant01` explicitly before running the AI-OPS runtime Ansible playbook.
- The first automation target is Ubuntu/Debian-like because current tooling examples use `apt-get`; implementation should either guard for supported OS families or make package lists configurable.
- The Ansible controller can SSH to `assistant01` over the management or Vagrant private path after the VM is started.
- `assistant01` should remain outside OpenStack deployment Ansible groups.
- Actual reachability and installed tool versions require a running VM; repository syntax checks alone are not Phase 01 completion evidence.

### III. Required Technical Dependencies and Imports

#### Repository dependencies

- `inventories/local/nodes.yml`
- proposed `ansible/ai_ops_runtime/inventories/local/local.yml`
- proposed `ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml`
- proposed `ansible/ai_ops_runtime/roles/assistant_runtime/`
- `docs/ai-ops/runtime/workspace-setup.md`
- `docs/ai-ops/runtime/tooling-setup.md`
- `docs/ai-ops/runtime/evidence-template.md`
- `docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md`

#### Runtime package dependencies

Target package categories from the runtime docs:

- Python 3 runtime
- Python virtual environment support
- Python package tooling
- SSH client
- curl or equivalent HTTP client
- JSON parser
- fast text search tool
- Git client

#### Python environment dependencies

Installed into `/opt/openstack-ai-ops/.venv`:

- `openstackclient`
- `openstacksdk`

#### Ansible module dependencies

Use built-in Ansible modules where possible:

- `ansible.builtin.file`
- `ansible.builtin.package` or distro-specific package module if needed
- `ansible.builtin.pip`
- `ansible.builtin.command` for version checks where no module exists
- `ansible.builtin.copy` or `ansible.builtin.template` for runtime evidence notes
- `ansible.builtin.assert` for safety checks

### IV. Step-by-Step Procedure / Execution Flow

1. Confirm `assistant01` is the selected repository-managed runtime.
2. Confirm `assistant01` can be started explicitly and is not part of OpenStack service groups.
3. Add a dedicated AI-OPS Ansible inventory that targets only the `assistant` group.
4. Add a syntax-valid playbook and role skeleton.
5. Add workspace directory tasks matching `docs/ai-ops/runtime/workspace-setup.md`:
   - `/opt/openstack-ai-ops/`
   - `scripts/approved/`
   - `diagnostics/raw/`
   - `diagnostics/summaries/`
   - `runbooks/`
   - `credentials/profiles/`
   - `audit/`
   - `mcp/`
6. Add package installation tasks for baseline host tools.
7. Add virtual environment and Python package tasks for OpenStack CLI/SDK.
8. Add verification tasks that capture versions and credential-absence status.
9. Write a dated runtime evidence note, either on the runtime host or into a repository evidence file after operator review.
10. Update Phase 01 checklist items only after evidence exists.
11. Stop before Phase 02 credential creation.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| ----- | ------------ | ------------------- | ----------------------- |
| Target selection | Playbook targets controller/compute/storage/Ceph groups | Stop and restrict inventory to `assistant` only | `ERR_AI_OPS_TARGET_SCOPE` (proposed) |
| VM state | `assistant01` is not started or not reachable over SSH | Stop before configuration; report start/connect command needed | `ERR_ASSISTANT_UNREACHABLE` (proposed) |
| Inventory | `assistant01` IP conflicts or does not resolve | Stop and report conflicting field | `ERR_ASSISTANT_INVENTORY_CONFLICT` (proposed) |
| Workspace | Directory creation fails or wrong owner is set | Leave evidence unchecked and report path/owner | `ERR_RUNTIME_WORKSPACE` (proposed) |
| Credentials | Any credential files exist in `credentials/profiles/` during Phase 01 | Stop, report unsafe state, do not continue tooling evidence | `ERR_CREDENTIALS_CREATED_TOO_EARLY` (proposed) |
| Package install | OS package names do not match runtime OS | Make package list configurable or fail with OS family details | `ERR_RUNTIME_PACKAGE_INSTALL` (proposed) |
| Python tooling | OpenStack CLI/SDK fail to install in venv | Stop before evidence update and report pip output | `ERR_OPENSTACK_TOOLING_INSTALL` (proposed) |
| Version capture | Tool exists but version command fails | Record failed command; leave relevant checklist unchecked | `ERR_RUNTIME_VERSION_CAPTURE` (proposed) |
| OpenStack command behavior | OpenStack CLI fails because binary missing rather than auth absent | Stop; tooling install is incomplete | `ERR_OPENSTACK_CLIENT_MISSING` (proposed) |
| Safety boundary | Generic AI shell/SSH/OpenStack passthrough is introduced | Reject/revert unsafe task | `ERR_AI_TOOL_BOUNDARY` (proposed) |
| Documentation tracking | Checkboxes are marked without runtime evidence | Revert checkbox update or add evidence note | `ERR_UNSUPPORTED_CHECKBOX` (proposed) |

### VI. Security, Integrity, Idempotency, and Cleanup

#### Security

- Do not create or copy OpenStack credentials in this side-quest.
- Do not create SSH keys for OpenStack nodes.
- Do not install database, RabbitMQ, Keystone, Nova, Neutron, Cinder, Glance, Ceph, OpenSearch, Prometheus, or Grafana service credentials.
- Do not expose generic shell execution, SSH execution, OpenStack CLI passthrough, file-write, package-install, service-restart, database, or remediation tools to AI.
- Keep MCP inactive; `mcp/` is a placeholder directory only.
- Keep OpenStack CLI/SDK unauthenticated until Phase 02.

#### Integrity

- Ansible inventory must target only `assistant01` / `assistant`.
- Evidence capture must distinguish between installed-tool evidence and operational reachability evidence.
- Phase 01 checklist updates must be evidence-backed.
- `credentials/profiles/` must exist but remain empty until Phase 02.

#### Idempotency

- Directory creation must use idempotent Ansible modules.
- Package installation must be re-runnable.
- Virtual environment setup must be re-runnable.
- Evidence output should be dated or clearly replace a current-state file.
- Re-running the playbook must not install credentials or overwrite operator-created evidence unexpectedly.

#### Cleanup and rollback

- Remove proposed `ansible/ai_ops_runtime/` files if the side-quest is abandoned.
- Destroy or disconnect `assistant01` if runtime creation needs rollback.
- Remove `/opt/openstack-ai-ops/` from `assistant01` if the runtime is discarded.
- If credentials are accidentally created, rollback becomes a Phase 02 credential revocation/security cleanup task.

### VII. Validation Strategy

Validation is chunk-aware and must not claim Phase 01 completion until runtime evidence exists.

#### Static validation

- Check YAML syntax:

  ```bash
  rtk yq '.' ansible/ai_ops_runtime/inventories/local/local.yml >/dev/null
  rtk yq '.' ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml >/dev/null
  ```

- Run Ansible syntax check:

  ```bash
  rtk ansible-playbook --syntax-check -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml -e root_dir="$PWD" -e target_env=local
  ```

- Review changed files:

  ```bash
  rtk git diff -- ansible/ai_ops_runtime docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md docs/ai-ops/runtime
  rtk git diff --check
  ```

#### Runtime smoke validation

After `assistant01` is started and reachable:

```bash
rtk ansible-playbook -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml -e root_dir="$PWD" -e target_env=local
```

Expected evidence after a successful run:

- workspace directories exist
- writable diagnostic/audit directories are writable by the runtime user
- `credentials/profiles/` exists and is empty
- baseline package/tool versions are captured
- OpenStack CLI/SDK are installed but unauthenticated
- no privileged credentials are installed

#### Secret and safety scan

Use a strict scan over the new runtime automation and docs:

```bash
rtk grep -RniE 'AKIA[0-9A-Z]{16}|BEGIN (RSA|EC|OPENSSH) PRIVATE KEY|ghp_[A-Za-z0-9]{36}|xox[baprs]-|aws_secret_access_key|client_secret|-----BEGIN PRIVATE KEY-----|OS_PASSWORD=|admin-openrc' ansible/ai_ops_runtime docs/ai-ops/runtime 2>/dev/null || true
```

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass.

#### Chunk 0: Discovery and Integration Confirmation
- **Goal:** Confirm the existing Ansible conventions, `assistant01` inventory state, and exact start/targeting policy.
- **Files to read:**
  - `inventories/local/nodes.yml`
  - `vagrant/controller/Makefile`
  - `vagrant/controller/provision.yml`
  - `ansible.cfg`
  - representative existing playbooks/inventories under `ansible/`
  - `docs/ai-ops/runtime/workspace-setup.md`
  - `docs/ai-ops/runtime/tooling-setup.md`
- **Commands:**
  - `rtk git status --short`
  - `rtk grep -Rni "assistant01\|environment: assistant" inventories vagrant ansible docs/ai-ops 2>/dev/null`
  - `rtk yq '.' inventories/local/nodes.yml >/dev/null`
- **Evidence to confirm:**
  - `assistant01` exists and uses non-conflicting IPs.
  - Existing Ansible layout supports a dedicated `ansible/ai_ops_runtime/` area.
  - No existing playbook already bootstraps the assistant runtime.
  - The desired policy is explicit operator start of `assistant01`, not default OpenStack deployment group membership.
- **Stop condition:** Report evidence and proposed file layout. Do not edit files.

#### Chunk 1: Ansible Inventory and Playbook Skeleton
- **Goal:** Add a syntax-valid, no-op or minimal-safe Ansible entrypoint that targets only `assistant01`.
- **Files to change:**
  - `ansible/ai_ops_runtime/inventories/local/local.yml`
  - `ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml`
  - optional minimal role file under `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/main.yml`
- **Symbols to add/change:** Not applicable; YAML/playbook contracts only.
- **Implementation shape:** Create `assistant` group with `assistant01` host and a playbook that includes an `assistant_runtime` role. The role may start with a safe `debug` or `assert` task proving target scope.
- **Validation:**
  - `rtk yq '.' ansible/ai_ops_runtime/inventories/local/local.yml >/dev/null`
  - `rtk yq '.' ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml >/dev/null`
  - `rtk ansible-playbook --syntax-check -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml -e root_dir="$PWD" -e target_env=local`
  - `rtk git diff -- ansible/ai_ops_runtime`
- **Stop condition:** Syntax-valid playbook exists and targets only `assistant` / `assistant01`; no workspace/tooling changes yet.

#### Chunk 2: Workspace Directory Automation
- **Goal:** Implement idempotent workspace creation matching `workspace-setup.md`.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/workspace.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/main.yml`
- **Symbols to add/change:** Proposed vars: `ai_ops_runtime_root`, `ai_ops_runtime_user`, `ai_ops_runtime_group`, `ai_ops_runtime_directories`.
- **Implementation shape:** Use `ansible.builtin.file` to create `/opt/openstack-ai-ops/` and child directories. Include an assertion or check that `credentials/profiles/` is empty after creation.
- **Validation:**
  - `rtk ansible-playbook --syntax-check -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml -e root_dir="$PWD" -e target_env=local`
  - `rtk grep -Rni "credentials/profiles" ansible/ai_ops_runtime`
  - `rtk git diff -- ansible/ai_ops_runtime`
- **Stop condition:** Workspace tasks are idempotent and do not create credentials.

#### Chunk 3: Baseline Host Package Installation
- **Goal:** Install baseline host tools without configuring credentials.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/tooling.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/main.yml`
- **Symbols to add/change:** Proposed vars: `ai_ops_runtime_packages`.
- **Implementation shape:** Use `ansible.builtin.package` or guarded distro-specific package tasks for Python, venv support, pip, SSH client, curl, jq, ripgrep, and git.
- **Validation:**
  - `rtk ansible-playbook --syntax-check -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml -e root_dir="$PWD" -e target_env=local`
  - `rtk grep -RniE "OS_PASSWORD|admin-openrc|private key" ansible/ai_ops_runtime 2>/dev/null || true`
  - `rtk git diff -- ansible/ai_ops_runtime`
- **Stop condition:** Package install tasks are syntax-valid, idempotent, and credential-free.

#### Chunk 4: Isolated Python OpenStack Tooling
- **Goal:** Create the AI-OPS virtual environment and install OpenStack CLI/SDK without credentials.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/tooling.yml`
- **Symbols to add/change:** Proposed vars: `ai_ops_runtime_venv_path`, `ai_ops_runtime_python_packages`.
- **Implementation shape:** Use `ansible.builtin.pip` with a virtualenv at `/opt/openstack-ai-ops/.venv` to install `openstackclient` and `openstacksdk`.
- **Validation:**
  - `rtk ansible-playbook --syntax-check -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml -e root_dir="$PWD" -e target_env=local`
  - `rtk grep -RniE "openstackclient|openstacksdk|\.venv" ansible/ai_ops_runtime`
  - `rtk git diff -- ansible/ai_ops_runtime`
- **Stop condition:** Python tooling tasks are syntax-valid and do not configure OpenStack auth.

#### Chunk 5: Runtime Evidence Capture Tasks
- **Goal:** Capture workspace, credential-absence, and tool-version evidence after the playbook runs.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/evidence.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/main.yml`
  - optional template under `ansible/ai_ops_runtime/roles/assistant_runtime/templates/`
- **Symbols to add/change:** Proposed vars: `ai_ops_runtime_evidence_path`.
- **Implementation shape:** Use read-only commands to collect versions and workspace checks. Write a dated evidence note under `/opt/openstack-ai-ops/diagnostics/summaries/` or another explicitly configured evidence path. Do not mark repository checkboxes from Ansible directly.
- **Validation:**
  - `rtk ansible-playbook --syntax-check -i ansible/ai_ops_runtime/inventories/local/local.yml ansible/ai_ops_runtime/playbook_setup_assistant_runtime.yml -e root_dir="$PWD" -e target_env=local`
  - `rtk grep -RniE "password:|token:|secret:|OS_PASSWORD=|admin-openrc" ansible/ai_ops_runtime 2>/dev/null || true`
  - `rtk git diff -- ansible/ai_ops_runtime`
- **Stop condition:** Evidence capture tasks exist and remain read-only with respect to OpenStack authority.

#### Chunk 6: Operator Run and Repository Evidence Update
- **Goal:** Run the playbook against a real `assistant01`, review output, and update Phase 01 evidence/checklists only where supported.
- **Files to change:**
  - `docs/ai-ops/runtime/` dated evidence note or copied evidence output
  - `docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md`
- **Symbols to add/change:** Not applicable; evidence/checklist docs only.
- **Implementation shape:** Execute the playbook, capture output, verify runtime facts, then update only evidence-backed checkboxes.
- **Validation:**
  - `rtk git diff -- docs/ai-ops/runtime docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md`
  - `rtk git diff --check`
  - `rtk grep -RniE "OS_PASSWORD=|password:|token:|secret:|BEGIN (RSA|OPENSSH|PRIVATE) KEY|admin-openrc" docs/ai-ops/runtime docs/ai-ops/implementation-plan/01-assistant-runtime-foundation.md 2>/dev/null || true`
- **Stop condition:** Runtime evidence exists, Phase 01 checklist is accurate, and Phase 02 credentials have not been introduced.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Implement Phase 01 Extended — Assistant Runtime Ansible Bootstrap from docs/ai-ops/implementation-plan/ads/01-extended-assistant-runtime-ansible-bootstrap-ads.md.

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

For the final evidence update:

```text
Use the chunked-implementation skill.
Execute Chunk 6 only.
Do not continue to Phase 02.
Update checkboxes only with evidence from a real assistant01 run.
```

### X. Conclusion and Next Steps

This side-quest is a reasonable Phase 01 extension because the project now has a repository-managed `assistant01` target and runtime setup is documented. It should remain separate from the core Phase 01 ADS because it introduces Ansible automation, idempotency concerns, and a runtime execution path.

Next recommended action: execute Chunk 0 from this ADS to confirm the proposed `ansible/ai_ops_runtime/` structure and target policy before adding playbook files.
