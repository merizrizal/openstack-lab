# Architecture Study

## 1) Repository Intent

This repository is a lab platform to provision and operate:

- Core OpenStack (controller, compute, storage).
- Ceph storage backend integration.
- Observability stack (OpenSearch, Prometheus, Grafana).
- Optional OpenStack-hosted CI/CD lab (GitLab, Jenkins, runner, telemetry).
- Optional OpenStack-hosted Kubernetes lab (kubeadm-based).

Primary entrypoint is `README.md` with Vagrant-first VM creation and Ansible-first service deployment.

## 2) High-Level Layers

1. Infrastructure layer:
   - Vagrant + Libvirt/KVM creates local lab VMs from `inventories/local/nodes.yml`.
2. Platform layer:
   - Ansible roles deploy OpenStack and supporting services on those VMs.
3. Workload layer:
   - OpenStack bootstraps tenant resources and then launches CI/CD and Kubernetes VMs via OpenStack APIs.
4. Validation layer:
   - Molecule validates inventory variable contracts, not full functional end-to-end behavior.

There is also a shell bootstrap layer in `envrc`:

- exports `ROOT_DIR` and `ANSIBLE_CONFIG`
- installs the repository git hook
- verifies Python, `pip`, and `venv`
- defines `generate_os_client_config`

## 3) Topology and Node Model

Base nodes (`inventories/local/nodes.yml`):

- `controller01`: OpenStack control-plane services.
- `compute01`, `compute02`: Nova + Neutron compute.
- `storage01`: Cinder-volume node, with an additional `vdb` data disk.
- `ceph01`: Ceph admin and OSD in single-node mode, with an additional `vdb` OSD disk.
- `ceph02`, `ceph03`: present only as commented inventory examples for a larger Ceph layout.

Default VM sizing is encoded in inventory, not inferred elsewhere:

- `controller01`: 16 GiB RAM, 4 vCPU, 50 GiB root disk
- `compute01`: 16 GiB RAM, 10 vCPU, 25 GiB root disk
- `compute02`: 12 GiB RAM, 6 vCPU, 25 GiB root disk
- `storage01`: 4 GiB RAM, 4 vCPU, 25 GiB root disk + 200 GiB data disk
- `ceph01`: 9 GiB RAM, 2 vCPU, 25 GiB root disk + 300 GiB data disk

Network model:

- Management network: `192.168.121.0/24`.
- Provider network: `192.168.123.0/24` bridged through `br-provider0`.
- Vagrant also creates a `192.168.124.0/24` private network for SSH convenience.

## 4) Ansible Domain Structure

Major domains under `ansible/`:

1. `deploy_openstack/`
   - Core OpenStack Gazpacho / 2026.1 services (Keystone, Glance, Placement, Nova, Neutron, Horizon, Cinder, optional Octavia).
2. `deploy_ceph/`
   - Ceph bootstrap via `cephadm`, host enrollment, OSD setup, and OpenStack key material export.
3. `deploy_opensearch/`
   - OpenSearch + Dashboards + Logstash/Filebeat.
4. `deploy_prometheus/`
   - Prometheus + Grafana + exporters + OpenSearch Grafana datasource.
5. `bootstrap_openstack/`
   - Tenant bootstrap: flavors/images/networks/security groups and workload VM creation.
6. `cicd_in_openstack/`
   - Dynamic inventory from OpenStack cloud config, then GitLab/Jenkins/runner/monitor setup.
7. `kubernetes_in_openstack/`
   - Dynamic inventory from OpenStack cloud config, then kubeadm cluster bring-up.
8. `shared_resources/playbooks/roles/`
   - Reusable `common`, `docker`, `telemetry`, and `ceph_common_vars`.

Inventory boundaries are explicit and matter operationally:

- `deploy_openstack`: `controller`, `compute`, `storage`
- `deploy_ceph`: `ceph_adm` and optionally `ceph_common`
- `deploy_prometheus`: `controller`, `compute`, `storage`, `ceph_adm`
- `deploy_opensearch`: `controller`, `compute`, `storage`
- `bootstrap_openstack`: `controller`
- `cicd_in_openstack` and `kubernetes_in_openstack`: dynamic inventory via `openstack.cloud.openstack`

## 5) Deployment Graph (Logical)

Recommended dependency order implemented in playbooks:

1. Build base image + spin VMs with Vagrant.
2. Deploy Ceph (`deploy_ceph/*`) and export keyrings/config.
3. Deploy OpenStack (`deploy_openstack/*`) with Ceph integration.
4. Bootstrap OpenStack resources (`bootstrap_openstack/playbook_bootstrap.yml`).
5. Deploy optional stacks:
   - Observability (`deploy_opensearch`, `deploy_prometheus`).
   - CI/CD VMs + services.
   - Kubernetes VMs + services.

Important hidden coupling:

- OpenStack pre-setup enables Ceph path by default (`ceph_enabled: true`) and copies Ceph config from `/tmp/fetch-ceph.conf`.
- That file is produced by Ceph-side fetch tasks, so Ceph initialization effectively precedes OpenStack in default mode.
- Step-by-step OpenStack deployment also needs `playbook_ceph_integration.yml` if Ceph remains enabled, because the one-shot deploy imports it conditionally.
- Guest metadata depends on both Neutron metadata agent and Nova metadata API. In the current Gazpacho implementation, Nova metadata is exposed through Apache on `controller01:8775` using `/usr/bin/nova-metadata-wsgi`.
- CI/CD and Kubernetes domains depend on generated clouds config files under `generated/` and on the OpenStack inventory plugin grouping hosts as expected.

Operational placement of major services is:

- OpenStack control-plane services on `controller01`
- Apache-served OpenStack APIs on `controller01`, including Keystone `5000`, Nova compute `8774`, Nova metadata `8775`, Cinder `8776`, Placement `8778`, and Neutron `9696`
- Nova/Neutron agents on `compute01` and `compute02`
- Cinder-volume on `storage01`
- Ceph admin and OSD on `ceph01` in the default topology
- OpenSearch, Dashboards, Prometheus, and Grafana on `controller01`
- Filebeat on `controller01`, `compute01`, `compute02`, and `storage01`
- Node exporter on `controller01`, `compute01`, `compute02`, `storage01`, and `ceph01`

## 6) CI and Validation Architecture

Two pipeline definitions:

- GitHub Actions: lint + molecule on Python 3.11/3.12.
- GitLab CI: similar stages and matrix.

Local quality gate:

- `githooks/pre-commit` runs `ansible-lint --fix` on staged YAML changes.

Validation behavior:

- Molecule verifies inventory variable snapshots against checked-in expected JSON, not service reachability or runtime correctness.

## 7) Engineering Perspective

The architecture is practical for a learning lab:

- Clear separation by domain and host roles.
- Reusable shared roles reduce repetition.
- OpenStack bootstrap for downstream labs is a strong design decision.

The repository is strong as an automation playground and reference implementation.
For production-like reliability, the largest gaps are secret hygiene, stronger runtime tests, and tighter consistency controls between related domains.
