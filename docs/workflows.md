# Deployment and Operations Workflows

## 1) Prerequisites

Required baseline:

- Ubuntu host with Libvirt/KVM.
- Vagrant + libvirt provider.
- Ansible and Python deps (`requirements.txt`).
- `yq`, build tools, and custom collection referenced by README.

Environment bootstrap:

1. Source `envrc` from repository root.
2. Build base image (`vagrant/base_image`).
3. Create `br-provider0` bridge (`vagrant/controller/Makefile`).
4. Bring up VMs from `inventories/local/nodes.yml`.

## 2) Core Lab Provisioning Sequence

### A. Ceph

Ordered playbooks:

1. `deploy_ceph/playbook_pre_setup.yml`
2. `deploy_ceph/playbook_setup_adm.yml`
3. `deploy_ceph/playbook_setup_common.yml` (when multi-node Ceph)
4. `deploy_ceph/playbook_apply_osd.yml`
5. `deploy_ceph/playbook_openstack_init.yml`

One-shot alternative:

- `deploy_ceph/playbook_deploy.yml`

### B. OpenStack

Ordered playbooks:

1. `deploy_openstack/playbook_pre_setup.yml`
2. `deploy_openstack/playbook_setup_controller.yml`
3. `deploy_openstack/playbook_setup_compute.yml`
4. `deploy_openstack/playbook_setup_storage.yml`
5. (Optional by default setting) `deploy_openstack/playbook_ceph_integration.yml`

One-shot alternative:

- `deploy_openstack/playbook_deploy.yml`

### C. OpenStack Bootstrap (tenant resources)

- `bootstrap_openstack/playbook_bootstrap.yml` creates flavors, image, networks/router, and base security group.

## 3) Optional Stacks

### A. Observability (on base lab nodes)

- OpenSearch: `deploy_opensearch/playbook_setup_opensearch.yml`
- Dashboards: `deploy_opensearch/playbook_setup_opensearch_dashboard.yml`
- Logstash/Filebeat: `deploy_opensearch/playbook_setup_filebeat.yml`
- Prometheus/Grafana/exporters: `deploy_prometheus/playbook_setup_prometheus.yml`
- Node exporter: `deploy_prometheus/playbook_setup_node_exporter.yml`

### B. CI/CD in OpenStack

1. Generate cloud config via `generate_os_client_config local cicd_lab`.
2. Initialize OpenStack VMs with `bootstrap_openstack/playbook_init_cicd_server.yml`.
3. Assign floating IPs.
4. Set `OS_CLIENT_CONFIG_FILE`.
5. Run:
   - `cicd_in_openstack/playbook_pre_setup.yml`
   - `cicd_in_openstack/playbook_setup_gitlab.yml`
   - `cicd_in_openstack/playbook_setup_jenkins.yml`
   - `cicd_in_openstack/playbook_setup_runner.yml`
   - `cicd_in_openstack/playbook_setup_ci_monitor.yml`
   - `cicd_in_openstack/playbook_setup_node_exporter.yml`

### C. Kubernetes in OpenStack

1. Generate cloud config via `generate_os_client_config local kubernetes_lab`.
2. Initialize VMs with `bootstrap_openstack/playbook_init_kubernetes.yml`.
3. Assign floating IPs.
4. Set `OS_CLIENT_CONFIG_FILE`.
5. Run:
   - `kubernetes_in_openstack/playbook_pre_setup.yml`
   - `kubernetes_in_openstack/playbook_setup_kubernetes.yml`
   - `kubernetes_in_openstack/playbook_setup_nodes.yml`

## 4) Day-2 Operations Notes

1. Re-running playbooks:
   - Most tasks are designed for repeat runs, but many shell/command tasks force `changed_when: false`, which weakens drift visibility.
2. Ceph/OpenStack coupling:
   - If Ceph artifacts in `/tmp/fetch-ceph*` are missing, OpenStack Ceph integration path fails.
3. Networking:
   - Nested virtualization external access needs host NAT configuration for provider subnet.
4. Dynamic inventory workloads:
   - CI/CD and Kubernetes domains rely on OpenStack cloud inventory plugin and generated clouds config.

## 5) Practical Runbook Advice

1. Keep a strict order:
   - Vagrant base -> Ceph -> OpenStack -> OpenStack bootstrap -> optional stacks.
2. Validate immediately after each stage:
   - Service health, API endpoint checks, and basic smoke tests (e.g., boot test instance).
3. Persist artifacts:
   - Keep generated cloud configs and exported Ceph files under controlled pathing for repeatability.
4. Treat defaults as lab defaults:
   - Credentials and permissive settings are intentionally simple for learning and should be hardened before shared environments.
