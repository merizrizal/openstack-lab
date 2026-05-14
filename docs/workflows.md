# Deployment and Operations Workflows

## 1) Prerequisites

Required baseline:

- Ubuntu host with Libvirt/KVM.
- Vagrant + libvirt provider.
- Ansible and Python deps (`requirements.txt`).
- `yq`, build tools, and custom collection referenced by README.

Environment bootstrap:

1. Source `envrc` from repository root.
   - This exports `ROOT_DIR` and `ANSIBLE_CONFIG`.
   - It also installs the git hook and verifies Python tooling.
2. Build the reusable Ubuntu base box from `vagrant/base_image`.
3. Create `br-provider0` with `make -C vagrant/controller start-provider-network`.
4. Bring up VMs from `inventories/local/nodes.yml` with `make -C vagrant/controller start-vm`.
5. If you plan to use downstream OpenStack-hosted labs, keep `generated/` available because `generate_os_client_config` writes cloud configs there.

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

Notes:

- Default inventory is single-node Ceph through `ceph01` as `ceph_adm`.
- `playbook_setup_common.yml` only matters when `ceph_common` hosts are enabled.
- `playbook_openstack_init.yml` exports the Ceph artifacts later consumed by the OpenStack domain.

### B. OpenStack

Ordered playbooks:

1. `deploy_openstack/playbook_pre_setup.yml`
2. `deploy_openstack/playbook_setup_controller.yml`
3. `deploy_openstack/playbook_setup_compute.yml`
4. `deploy_openstack/playbook_setup_storage.yml`
5. `deploy_openstack/playbook_ceph_integration.yml` when `ceph_enabled: true`
6. Optional: `deploy_openstack/playbook_setup_octavia.yml`

One-shot alternative:

- `deploy_openstack/playbook_deploy.yml`

Notes:

- `ceph_enabled` defaults to `true` in `deploy_openstack/inventories/local/group_vars/all/common.yml`.
- `playbook_pre_setup.yml` already loads `ceph_common_vars` and the `ceph` role when Ceph is enabled, so the Ceph export step must have happened first.
- `playbook_deploy.yml` automatically imports `playbook_ceph_integration.yml` when Ceph is enabled, so a manual staged deployment should include it to match the one-shot path.

### C. OpenStack Bootstrap (tenant resources)

- `bootstrap_openstack/playbook_bootstrap.yml` creates:
  - flavors
  - the uploaded base image in Glance
  - provider and self-service networks
  - router wiring
  - an `openstack_lab` security group with common operational ports

Before running it:

1. Copy a qcow2 image to `controller01` with `make -C vagrant/controller copy-image-to-vm IMAGE_PATH=/path/to/image.qcow2`.
2. By default the copied filename should be `vm_image01.img`, matching `image_name: vm_image01` in `bootstrap_openstack/inventories/local/group_vars/all/common.yml`.

## 3) Stage Validation Checkpoints

These checks are not a substitute for full test automation, but they are useful
after each major stage. Run them from the repository root after `source envrc`
unless noted otherwise.

### A. After Vagrant VM creation

Confirm Ansible can reach the static lab inventory:

```bash
cd ansible
ansible -i deploy_openstack/inventories/local/local.yml all -m ping
ansible -i deploy_ceph/inventories/local/local.yml all -m ping
```

Confirm the provider bridge exists on the host:

```bash
ip addr show br-provider0
```

### B. After Ceph deployment

Check cluster status on the Ceph admin node:

```bash
cd ansible
ansible -i deploy_ceph/inventories/local/local.yml ceph_adm \
  -b -m command -a "ceph -s"
```

Confirm OpenStack integration artifacts exist on the Ansible control machine:

```bash
ls -l /tmp/fetch-ceph.conf \
  /tmp/fetch-ceph.client.glance.keyring \
  /tmp/fetch-ceph.client.cinder.keyring
```

### C. After OpenStack deployment

The OpenStack common role writes admin `OS_*` variables to `/etc/environment`.
Use a shell module so those values are loaded before running OpenStack CLI
checks:

```bash
cd ansible
ansible -i deploy_openstack/inventories/local/local.yml controller \
  -b -m shell -a ". /etc/environment; openstack token issue"

ansible -i deploy_openstack/inventories/local/local.yml controller \
  -b -m shell -a ". /etc/environment; openstack compute service list"

ansible -i deploy_openstack/inventories/local/local.yml controller \
  -b -m shell -a ". /etc/environment; openstack network agent list"

ansible -i deploy_openstack/inventories/local/local.yml controller \
  -b -m shell -a ". /etc/environment; openstack volume service list"
```

### D. After OpenStack bootstrap

Confirm the expected tenant resources exist:

```bash
cd ansible
ansible -i deploy_openstack/inventories/local/local.yml controller \
  -b -m shell -a ". /etc/environment; openstack flavor list"

ansible -i deploy_openstack/inventories/local/local.yml controller \
  -b -m shell -a ". /etc/environment; openstack image list"

ansible -i deploy_openstack/inventories/local/local.yml controller \
  -b -m shell -a ". /etc/environment; openstack network list"

ansible -i deploy_openstack/inventories/local/local.yml controller \
  -b -m shell -a ". /etc/environment; openstack security group rule list openstack_lab"
```

For a stronger smoke test, boot one disposable instance with the `small` flavor
and `vm_image01` image, verify network behavior, then delete it.

### E. After observability deployment

Check the local services on `controller01`:

```bash
cd ansible
ansible -i deploy_prometheus/inventories/local/local.yml controller \
  -b -m shell -a "systemctl is-active prometheus grafana-server prometheus_openstack_exporter prometheus_mariadb_exporter"

ansible -i deploy_opensearch/inventories/local/local.yml controller \
  -b -m shell -a "systemctl is-active opensearch dashboards filebeat logstash"
```

Confirm node exporter is reachable on the repository default port:

```bash
ansible -i deploy_prometheus/inventories/local/local.yml all \
  -b -m shell -a "curl -fsS http://127.0.0.1:9200/metrics >/dev/null"
```

### F. Before downstream CI/CD or Kubernetes playbooks

Confirm the generated clouds config exists and that dynamic inventory can see
the OpenStack-hosted VMs:

```bash
test -f "$ROOT_DIR/generated/local_clouds.yml"
export OS_CLIENT_CONFIG_FILE=$ROOT_DIR/generated/local_clouds.yml

cd ansible
```

For the CI/CD lab after `generate_os_client_config local cicd_lab`:

```bash
ansible-inventory -i cicd_in_openstack/inventories/local/openstack.yml --graph
```

For the Kubernetes lab after `generate_os_client_config local kubernetes_lab`:

```bash
ansible-inventory -i kubernetes_in_openstack/inventories/local/openstack.yml --graph
```

## 4) Optional Stacks

### A. Observability (on base lab nodes)

- `deploy_opensearch` domain:
  - OpenSearch on `controller`
  - OpenSearch Dashboards on `controller`
  - Filebeat and Logstash-related setup on `controller`, `compute`, and `storage`
- `deploy_prometheus` domain:
  - Prometheus, Grafana, OpenStack exporter integration, and OpenSearch datasource setup on `controller`
  - node exporter on `controller`, `compute`, `storage`, and `ceph_adm`

Operational note:

- Node exporter defaults to port `9200`, not `9100`.

### B. CI/CD in OpenStack

1. Run `generate_os_client_config local cicd_lab`.
   - This writes `generated/local_clouds.yml`.
2. Export `OS_CLIENT_CONFIG_FILE=$ROOT_DIR/generated/local_clouds.yml`.
3. Initialize OpenStack VMs with `bootstrap_openstack/playbook_init_cicd_server.yml`.
4. Assign floating IPs if you need direct access from outside the tenant network.
5. Run:
   - `cicd_in_openstack/playbook_pre_setup.yml`
   - `cicd_in_openstack/playbook_setup_gitlab.yml`
   - `cicd_in_openstack/playbook_setup_jenkins.yml`
   - `cicd_in_openstack/playbook_setup_runner.yml`
   - `cicd_in_openstack/playbook_setup_ci_monitor.yml`
   - `cicd_in_openstack/playbook_setup_node_exporter.yml`

Expected VM set:

- `gitlab_vm01`
- `jenkins_vm01`
- `runner_vm01`
- `ci_monitor_vm01`

### C. Kubernetes in OpenStack

1. Run `generate_os_client_config local kubernetes_lab`.
   - This overwrites `generated/local_clouds.yml` with the `kubernetes_lab` cloud entry.
2. Export `OS_CLIENT_CONFIG_FILE=$ROOT_DIR/generated/local_clouds.yml`.
3. Initialize VMs with `bootstrap_openstack/playbook_init_kubernetes.yml`.
4. Assign floating IPs if required for external access.
5. Run:
   - `kubernetes_in_openstack/playbook_pre_setup.yml`
   - `kubernetes_in_openstack/playbook_setup_kubernetes.yml`
   - `kubernetes_in_openstack/playbook_setup_nodes.yml`

Expected VM set:

- `control_plane_vm01`
- `worker_vm01`
- `worker_vm02`

## 5) Day-2 Operations Notes

1. Re-running playbooks:
   - Most tasks are designed for repeat runs, but many shell/command tasks force `changed_when: false`, which weakens drift visibility.
2. Ceph/OpenStack coupling:
   - If Ceph artifacts in `/tmp/fetch-ceph*` are missing, OpenStack Ceph integration path fails.
3. Networking:
   - Nested virtualization external access needs host NAT configuration for provider subnet.
4. Dynamic inventory workloads:
   - CI/CD and Kubernetes domains rely on the OpenStack inventory plugin plus the generated clouds config referenced by `OS_CLIENT_CONFIG_FILE`.
5. Bootstrap security group:
   - `bootstrap_openstack/playbook_bootstrap.yml` opens `22`, `80`, `8080`, `443`, `6443`, `3000`, `9090`, and `9100`, but node exporter defaults to `9200`.

## 6) Practical Runbook Advice

1. Keep a strict order:
   - Vagrant base -> Ceph -> OpenStack -> OpenStack bootstrap -> optional stacks.
2. Validate immediately after each stage:
   - Service health, API endpoint checks, and basic smoke tests (e.g., boot test instance).
3. Persist artifacts:
   - Keep generated cloud configs and exported Ceph files under controlled pathing for repeatability.
4. Treat defaults as lab defaults:
   - Credentials and permissive settings are intentionally simple for learning and should be hardened before shared environments.
