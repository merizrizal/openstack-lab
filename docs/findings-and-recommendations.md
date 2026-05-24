# Findings and Recommendations

This report prioritizes concrete issues found during repository study.

Severity model:

- `Critical`: security or correctness issue with immediate high impact.
- `High`: likely to break flows or create significant operational pain.
- `Medium`: correctness/consistency risk, not always immediate failure.
- `Low`: documentation/usability/maintainability gaps.

## Critical Findings

1. Plaintext credentials and tokens are committed in inventories.
   - Evidence:
     - `ansible/cicd_in_openstack/inventories/local/group_vars/all/common_secret.yml:7`
     - `ansible/deploy_openstack/inventories/local/group_vars/all/common_secret.yml:6`
     - `ansible/deploy_opensearch/inventories/local/group_vars/all/common_secret.yml:10`
   - Impact:
     - Credential leakage risk, accidental reuse risk, and low barrier for lateral movement in shared environments.
   - Recommendation:
     - Move secrets to Ansible Vault or SOPS and inject via CI/runtime secret stores.

2. Kubernetes worker join token is generated on workers, not control plane.
   - Evidence:
     - `ansible/kubernetes_in_openstack/roles/nodes/tasks/workers.yml:26`
   - Impact:
     - `kubeadm token create` commonly requires control-plane admin context; this can break worker join.
   - Recommendation:
     - Generate join command once on control plane (delegate/run_once), then distribute to workers.

## High Findings

1. Port mismatch between node exporter default and OpenStack bootstrap security group.
   - Evidence:
     - Node exporter default: `ansible/shared_resources/playbooks/roles/telemetry/defaults/main.yml:14` (`9200`)
     - Security group opens: `ansible/bootstrap_openstack/playbook_bootstrap.yml:142` (`9100`)
   - Impact:
     - CI/CD node-exporter scraping from monitor VMs can fail due to blocked port.
   - Recommendation:
     - Standardize on one port and enforce alignment check in CI.

2. Vagrant provisioning logic applies host/provision loops to every machine.
   - Evidence:
     - `vagrant/base.rb:112`
     - `vagrant/base.rb:125`
   - Impact:
     - Repeated and incorrect provisioning commands per machine; possible duplicated `/etc/hosts` entries and wrong role-specific bootstrap commands.
   - Recommendation:
     - Scope provisioning to current machine host context, not full inventory loops.

3. OpenStack pre-setup depends on Ceph artifacts in `/tmp` while Ceph is enabled by default.
   - Evidence:
     - Default enable: `ansible/deploy_openstack/inventories/local/group_vars/all/common.yml:12`
     - Ceph role in pre-setup: `ansible/deploy_openstack/playbook_pre_setup.yml:13`
     - Artifact path default: `ansible/shared_resources/playbooks/roles/ceph_common_vars/defaults/main.yml:5`
     - Artifact consumption: `ansible/deploy_openstack/roles/ceph/tasks/main.yml:8`
   - Impact:
     - OpenStack pre-setup can fail if Ceph export phase was not run previously.
   - Recommendation:
     - Add explicit preflight checks and clearer failure messaging; optionally disable Ceph by default.

4. Kubernetes containerd config is hardcoded to `linux/amd64`.
   - Evidence:
     - `ansible/kubernetes_in_openstack/roles/kubernetes/files/containerd.config.toml:199`
   - Impact:
     - Conflicts with declared architecture abstraction and reduces ARM portability.
   - Recommendation:
     - Template this value from architecture mapping.

## Medium Findings

1. Dynamic inventory host-group assumption may be fragile in CI/CD and Kubernetes pre-setup.
   - Evidence:
     - `ansible/cicd_in_openstack/playbook_pre_setup.yml:3` (`hosts: cicd_lab`)
     - `ansible/kubernetes_in_openstack/playbook_pre_setup.yml:3` (`hosts: kubernetes_lab`)
     - OpenStack plugin inventory file has cloud selection but no explicit keyed groups:
       `ansible/cicd_in_openstack/inventories/local/openstack.yml:2`
   - Impact:
     - Depending on plugin behavior, group resolution can be brittle.
   - Recommendation:
     - Add explicit `keyed_groups` or use deterministic host patterns.

2. Jenkins template declares `runner_vm02` but inventory defines only one runner.
   - Evidence:
     - `ansible/cicd_in_openstack/roles/jenkins/templates/jenkins.yml.j2:15`
     - `ansible/shared_resources/inventories/local/cicd.yml:8`
   - Impact:
     - Potential dead agent definition, confusion, and unnecessary operational noise.
   - Recommendation:
     - Parameterize node list from inventory instead of hardcoding.

3. Custom callback plugin is required by default ansible config.
   - Evidence:
     - `ansible.cfg:5`
     - README lists external collection dependency: `README.md:69`
   - Impact:
     - Fresh setups fail if collection is missing.
   - Recommendation:
     - Provide automated collection bootstrap (`ansible-galaxy` requirements file) and fallback callback behavior.

## Low Findings

1. Documentation previously under-described repo-critical operator behavior.
   - Evidence:
     - `envrc:1`
     - `ansible/deploy_prometheus/playbook_setup_prometheus.yml:2`
     - `ansible/deploy_opensearch/playbook_setup_filebeat.yml:2`
     - `ansible/deploy_openstack/playbook_deploy.yml:26`
   - Impact:
     - Operators can miss `envrc` side effects, the actual placement of observability services, and the fact that staged OpenStack deployment should include Ceph integration when Ceph is enabled.
   - Recommendation:
     - Keep `docs/` tied to implementation details and update workflow docs whenever playbook composition or inventory scope changes.

2. Molecule separates variable validation from runtime behavior checks.
   - Evidence:
     - `molecule/config.yml:28`
     - `molecule/vars_validation.yml:2`
     - `molecule/verify.yml:2`
     - `molecule/openstack/tasks/smoke_verify.yml:1`
     - `molecule/openstack/tasks/e2e_workload_verify.yml:1`
     - `molecule/ceph/tasks/smoke_verify.yml:1`
   - Impact:
     - Regressions in service behavior may pass the default Molecule `check` path unless Molecule `test` is run against a deployed lab.
   - Recommendation:
     - Run Molecule `test` against deployed lab runners when smoke runtime validation is required.
     - Run OpenStack end-to-end workload verification with `MOLECULE_E2E_VERIFY=true` through Molecule `test` after bootstrap resources exist.
     - Keep the smoke task fast and mostly read-only so it can run before the deeper workload test; use the OpenStack scenario for API and integration checks and the Ceph scenario for cluster health checks.

## Prioritized Remediation Roadmap

1. Immediate (day 0-2):
   - Remove plaintext sensitive values from repo and rotate exposed tokens/passwords.
   - Fix Kubernetes worker join-token generation flow.
   - Align node-exporter port and security group rules.
2. Short term (week 1):
   - Refactor Vagrant provisioning loops to host-scoped logic.
   - Add Ceph/OpenStack preflight checks and explicit dependency guardrails.
   - Keep operator-facing docs synchronized with playbook composition and inventory scope.
3. Medium term (week 2-4):
   - Run Molecule `test` smoke checks on deployed lab runners where available.
   - Template architecture-specific values (`amd64` hardcoding).
   - Move static Jenkins node definitions to data-driven inventory templates.

## Overall Point of View

The project is a good learning and experimentation platform with practical modular automation.
Its biggest risks are not architectural complexity, but operational hygiene and consistency controls.
If the prioritized fixes above are completed, the repository can become a strong reference-grade lab automation baseline.
