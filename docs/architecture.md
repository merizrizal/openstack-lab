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
   - OpenStack bootstraps tenant resources and then launches CI/CD/Kubernetes VMs via OpenStack APIs.
4. Validation layer:
   - Molecule validates inventory variable contracts (not functional end-to-end behavior).

## 3) Topology and Node Model

Base nodes (`inventories/local/nodes.yml`):

- `controller01`: OpenStack control-plane services.
- `compute01`, `compute02`: Nova + Neutron compute.
- `storage01`: Cinder-volume (LVM or Ceph backend).
- `ceph01`: Ceph admin and OSD in single-node mode (with optional commented `ceph02`, `ceph03`).

Network model:

- Management network: `192.168.121.0/24`.
- Provider network: `192.168.123.0/24` bridged through `br-provider0`.
- Vagrant helper also uses `192.168.124.0/24` private connectivity for SSH convenience.

## 4) Ansible Domain Structure

Major domains under `ansible/`:

1. `deploy_openstack/`
   - Core OpenStack services (Keystone, Glance, Placement, Nova, Neutron, Horizon, Cinder, optional Octavia).
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
