# Base Knowledge Guide

This guide explains the project from first principles. Use it before the deeper
architecture and workflow documents when you need the mental model for how the
lab fits together.

## 1) Project Mental Model

This repository builds a complete local OpenStack learning environment in three
main layers:

1. Local virtualization:
   - Vagrant creates Ubuntu virtual machines on Libvirt/KVM.
   - `inventories/local/nodes.yml` is the source of truth for VM names, IPs,
     memory, CPU, disk size, and node purpose.
2. Infrastructure services:
   - Ansible installs Ceph and OpenStack services on the Vagrant VMs.
   - Ceph provides the default storage backend for OpenStack image, compute,
     and volume workflows.
3. OpenStack-hosted labs:
   - After OpenStack works, Ansible can create tenant VMs inside OpenStack for
     CI/CD and Kubernetes labs.
   - These downstream labs use OpenStack APIs and dynamic inventory instead of
     static Vagrant inventory.

The most important dependency chain is:

```text
host tools -> Vagrant VMs -> Ceph -> OpenStack -> OpenStack bootstrap -> optional labs
```

## 2) Default Node Roles

The default local topology contains five VMs:

| Node | Role | Main responsibility |
| --- | --- | --- |
| `controller01` | OpenStack controller | Keystone, Glance, Placement, Nova API/scheduler, Neutron controller services, Horizon, Cinder API/scheduler, observability services |
| `compute01` | OpenStack compute | Nova compute and Neutron compute agent |
| `compute02` | OpenStack compute | Second Nova/Neutron compute host |
| `storage01` | OpenStack block storage | Cinder volume service with an additional data disk |
| `ceph01` | Ceph admin and OSD | Single-node Ceph deployment and exported OpenStack storage credentials |

`ceph02` and `ceph03` are present only as commented examples for a larger Ceph
cluster. The default inventory is a single-node Ceph lab.

## 3) Network Model

The lab uses three practical network views:

| Network | Default CIDR | Purpose |
| --- | --- | --- |
| Management | `192.168.121.0/24` | Ansible SSH, OpenStack service endpoints, node-to-node management traffic |
| Provider | `192.168.123.0/24` | External/provider network exposed through host bridge `br-provider0` |
| Vagrant private | `192.168.124.0/24` | Vagrant SSH convenience network after the VM network patch |

OpenStack bootstrap creates:

- a provider network named `provider`
- a self-service tenant network named `private`
- a router named `router`
- a security group named `openstack_lab`

Nested virtualization means the outer host still matters. If OpenStack tenant
instances cannot reach the internet, check host-side NAT for `192.168.123.0/24`
through the host external interface.

## 4) OpenStack Services in This Lab

The OpenStack domain is split by host role:

| Service | What it does | Where this repo deploys it |
| --- | --- | --- |
| Keystone | Identity, tokens, service catalog | `controller01` |
| Glance | VM image catalog and image storage integration | `controller01` |
| Placement | Resource tracking for Nova scheduling | `controller01` |
| Nova controller services | Compute API, metadata API, scheduler, conductor, cell discovery | `controller01` |
| Nova compute | Hypervisor-side VM lifecycle | `compute01`, `compute02` |
| Neutron controller services | Networking API, RPC server, L3/DHCP/metadata/ML2 configuration | `controller01` |
| Neutron compute agent | Open vSwitch and local network plumbing | `compute01`, `compute02` |
| Horizon | Web dashboard | `controller01` |
| Cinder controller services | Block storage API and scheduler | `controller01` |
| Cinder volume | Volume backend service | `storage01` |
| Octavia | Load balancer service | Optional playbook |

OpenStack packages are configured through the Ubuntu Cloud Archive repository
value in `ansible/deploy_openstack/inventories/local/group_vars/all/common.yml`.
The current implementation uses `cloud-archive:gazpacho` for OpenStack Gazpacho /
2026.1.

On Gazpacho, several OpenStack APIs are served through Apache WSGI. Nova
metadata is separate from the Nova compute API:

| API | Default port | Implementation detail |
| --- | --- | --- |
| Nova compute API | `8774` | Apache site from the `nova-api` package |
| Nova metadata API | `8775` | Repository-managed Apache site for `/usr/bin/nova-metadata-wsgi` |
| Neutron API | `9696` | Apache site from the `neutron-server` package plus `neutron-rpc-server` |

Guest cloud-init metadata calls follow this path:

```text
guest 169.254.169.254 -> Neutron metadata agent -> Nova metadata API on controller01:8775
```

## 5) Ceph Integration Model

Ceph is enabled by default for OpenStack with:

```yaml
ceph_enabled: true
```

The Ceph deployment prepares OpenStack-facing artifacts and fetches them to the
machine running Ansible. The OpenStack playbooks later consume those files from
`/tmp`:

| Artifact | Default local path | Consumer |
| --- | --- | --- |
| Ceph config | `/tmp/fetch-ceph.conf` | OpenStack Ceph role |
| Glance keyring | `/tmp/fetch-ceph.client.glance.keyring` | Glance Ceph backend |
| Cinder keyring | `/tmp/fetch-ceph.client.cinder.keyring` | Cinder and Nova integration |
| Ceph public key | `/tmp/fetch-ceph.pub` | Multi-node Ceph host enrollment |

Because of this coupling, default OpenStack deployment expects Ceph deployment
and `deploy_ceph/playbook_openstack_init.yml` to run first. If you do not want
Ceph, set `ceph_enabled: false` before running OpenStack playbooks.

## 6) Inventory and Variable Boundaries

The repository has two inventory styles:

1. Static local inventories:
   - Used for Vagrant-created lab nodes.
   - Main source: `inventories/local/nodes.yml`.
   - Ansible domains read this file through `vars_files`.
2. Dynamic OpenStack inventories:
   - Used after the base OpenStack cloud exists.
   - CI/CD and Kubernetes labs use `openstack.cloud.openstack`.
   - `OS_CLIENT_CONFIG_FILE` must point to `generated/local_clouds.yml`.
   - `generate_os_client_config` rewrites `generated/local_clouds.yml`, so
     regenerate it for the lab cloud name you are about to operate.

When changing node names, IP addresses, or topology, update both the inventory
and any group variables that reference specific hosts. This project currently
has several host-specific assumptions such as `controller01`, `compute01`, and
`ceph01`.

## 7) Environment Helpers

Use the helper files intentionally:

| File | Intended use |
| --- | --- |
| `envrc` | Interactive local use. Sets `ROOT_DIR`, sets `ANSIBLE_CONFIG`, installs git hooks, checks Python tooling, and defines `generate_os_client_config`. |
| `circ` | CI-oriented environment setup. Sets only `ROOT_DIR` and `ANSIBLE_CONFIG`. |
| `ansible.cfg` | Defines role paths, callback plugin behavior, SSH retries, and collection paths. |
| `requirements.txt` | Python package baseline for Ansible, linting, OpenStack SDK, and related modules. |

The custom callback plugin from `merizrizal.utils` is enabled in `ansible.cfg`.
Fresh machines need that collection installed before normal playbook output will
work as configured.

The default OpenStack and Ceph inventories use the base-image-created
`ansible_sys_user` account. Some downstream or bootstrap domains still use the
`vagrant` account where their inventories have not been migrated.

## 8) Repository Map

| Path | Purpose |
| --- | --- |
| `inventories/local/nodes.yml` | Base VM topology and sizing |
| `vagrant/base_image/` | Build reusable Ubuntu and AlmaLinux Vagrant boxes |
| `vagrant/controller/` | Create bridge network, start lab VMs, copy images to controller |
| `ansible/deploy_ceph/` | Deploy Ceph and export OpenStack integration artifacts |
| `ansible/deploy_openstack/` | Deploy core OpenStack services |
| `ansible/bootstrap_openstack/` | Create flavors, image, networks, router, security group, and downstream lab VMs |
| `ansible/deploy_opensearch/` | Deploy OpenSearch, Dashboards, Filebeat, and Logstash pieces |
| `ansible/deploy_prometheus/` | Deploy Prometheus, Grafana, exporters, and Grafana datasources |
| `ansible/cicd_in_openstack/` | Configure GitLab, Jenkins, runner, and CI monitor inside OpenStack VMs |
| `ansible/kubernetes_in_openstack/` | Configure a kubeadm Kubernetes cluster inside OpenStack VMs |
| `ansible/shared_resources/` | Shared roles and downstream lab VM definitions |
| `molecule/` | Molecule variable validation, smoke verification, and end-to-end verification scenarios |
| `docs/` | Architecture, workflows, quality notes, findings, and this base guide |

## 9) Editing Guide for Common Changes

| Change | Start here | Also check |
| --- | --- | --- |
| Add or resize a base VM | `inventories/local/nodes.yml` | Vagrant provider resources, Ansible host groups |
| Change management/provider IPs | `inventories/local/nodes.yml` | Bootstrap network CIDRs, host NAT rules, `provider_interface` |
| Disable Ceph | OpenStack `common.yml` | Cinder/Glance/Nova storage expectations |
| Add a Ceph node | `inventories/local/nodes.yml`, `deploy_ceph/inventories/local/local.yml` | `ceph_common` group, OSD disk names |
| Add an OpenStack service | `ansible/deploy_openstack/roles/` | controller/compute/storage playbook placement and endpoints |
| Change downstream lab VMs | `ansible/shared_resources/inventories/local/*.yml` | bootstrap init playbooks and dynamic inventory groups |
| Change exporter ports | `telemetry/defaults/main.yml` | Prometheus scrape config and OpenStack security group rules |
| Replace lab credentials | `common_secret.yml` files | Ansible Vault/SOPS strategy and generated clouds config |

## 10) Validation Mindset

Molecule has two validation paths in this repository:

- `molecule check` validates inventory variable shape through
  `molecule/vars_validation.yml`. The Makefile exposes this as
  `make validate-openstack` and `make validate-ceph`.
- `molecule test` runs runtime verification through `molecule/verify.yml`.
  The Makefile exposes this as `make test-openstack` and
  `make test-ceph`. Smoke checks run by default in this path when the
  scenario has `smoke_verify.yml`; OpenStack end-to-end workload verification is
  opt-in with `MOLECULE_E2E_VERIFY=true`.

The default CI-oriented validation path still does not deploy the lab by itself,
so treat smoke and end-to-end checks as deployed-lab verification.

After each major stage, validate the running system:

- Ceph: `ceph -s` should be healthy enough for the lab.
- OpenStack identity: `openstack token issue` should return a token.
- OpenStack services: `openstack compute service list`,
  `openstack network agent list`, and `openstack volume service list` should
  show expected services as up.
- OpenStack metadata: `curl -sS -i http://127.0.0.1:8775/openstack` on
  `controller01` should return a Nova metadata response rather than connection
  refused.
- OpenStack tenant path: boot a small test instance, attach network, confirm
  metadata/network reachability, then delete it.
- Observability: Prometheus targets should be up, Grafana should load, and
  OpenSearch health should be acceptable for the lab.
- Downstream labs: dynamic inventory should list the expected OpenStack VMs
  before service playbooks are run.

Treat committed credentials, permissive SSH settings, and broad security group
rules as lab defaults only. They are useful for learning, but they are not a
safe baseline for shared or public environments.
