# OpenStack Lab Provisioning

## Overview

This repository is intended for **learning OpenStack** and **deploying a full OpenStack lab environment**.

The lab is deployed on **Libvirt/KVM**, meaning all OpenStack instances run under **nested virtualization**.

> **Status**
>
> * Tested on **Ubuntu only**
> * Intended for lab, learning, and experimentation purposes

Learning materials are primarily sourced from the official OpenStack documentation:
[https://docs.openstack.org/install-guide/openstack-services.html](https://docs.openstack.org/install-guide/openstack-services.html)

---

## Architecture Summary

* Host OS: Ubuntu
* Hypervisor: Libvirt + KVM
* VM provisioning: Vagrant
* Configuration management: Ansible
* Storage backend: Ceph
* Observability: OpenSearch, Prometheus, Grafana stack
* Optional workloads:

  * CI/CD Lab (GitLab, Jenkins, Runner, Prometheus)
  * Kubernetes Lab (kubeadm-based)

---

## Prerequisites (Host Machine)

Ensure the following tools are installed on your host OS:

* **QEMU + Libvirt**
  [https://documentation.ubuntu.com/server/how-to/virtualisation/libvirt/](https://documentation.ubuntu.com/server/how-to/virtualisation/libvirt/)

* **yq**
  [https://github.com/mikefarah/yq](https://github.com/mikefarah/yq)

* **Build tools**
  `gcc`, `make`, or `build-essential` (Ubuntu)

* **Vagrant**
  [https://developer.hashicorp.com/vagrant/install](https://developer.hashicorp.com/vagrant/install)

* **Vagrant Libvirt provider**
  [https://vagrant-libvirt.github.io/vagrant-libvirt/installation.html](https://vagrant-libvirt.github.io/vagrant-libvirt/installation.html)

* **Ansible**
  [https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html)

* **Custom Ansible collection**
  [https://github.com/merizrizal/ansible-collections-for-utilities](https://github.com/merizrizal/ansible-collections-for-utilities)

---

## Environment Preparation

1. Load environment variables:

   ```bash
   source envrc
   ```

2. Navigate to the Vagrant directory:

   ```bash
   cd vagrant
   ```

3. Build the base Ubuntu image:

   ```bash
   make -C base_image/ rebuild-base-image-ubuntu
   ```

   This creates a reusable Vagrant box for:

   * Controller node
   * Compute nodes
   * Storage node
   * Ceph node

4. Create the provider network:

   ```bash
   make -C controller/ start-provider-network
   ```

5. Start the OpenStack VMs:

   ```bash
   make -C controller/ start-vm
   ```

   This provisions:

   * 1 Controller node
   * 2 Compute nodes
   * 1 Storage node
   * 1 Ceph node

---

## Ceph Provisioning

All Ceph provisioning is done using Ansible.

1. Load environment variables and navigate to Ansible:

   ```bash
   source envrc
   cd ansible
   ```

2. Run the playbooks in sequence:

   * Pre-requisites:

     ```bash
     ansible-playbook -i deploy_ceph/inventories/local/local.yml \
       deploy_ceph/playbook_pre_setup.yml
     ```

   * Deploy Ceph ADM:

     ```bash
     ansible-playbook -i deploy_ceph/inventories/local/local.yml \
       deploy_ceph/playbook_setup_adm.yml
     ```

   * Install Ceph common packages:

     ```bash
     ansible-playbook -i deploy_ceph/inventories/local/local.yml \
       deploy_ceph/playbook_setup_common.yml
     ```

   * Apply OSDs:

     ```bash
     ansible-playbook -i deploy_ceph/inventories/local/local.yml \
       deploy_ceph/playbook_apply_osd.yml
     ```

   * Integrate Ceph with OpenStack (Cinder & Nova):

     ```bash
     ansible-playbook -i deploy_ceph/inventories/local/local.yml \
       deploy_ceph/playbook_openstack_init.yml
     ```

### One-step Ceph deployment

Alternatively, deploy everything at once:

```bash
ansible-playbook -i deploy_ceph/inventories/local/local.yml \
  deploy_ceph/playbook_deploy.yml
```

---

## OpenStack Provisioning

1. Load environment variables and navigate to Ansible:

   ```bash
   source envrc
   cd ansible
   ```

2. Run the playbooks in sequence:

   * Pre-requisites:

     ```bash
     ansible-playbook -i deploy_openstack/inventories/local/local.yml \
       deploy_openstack/playbook_pre_setup.yml
     ```

   * Controller node:

     ```bash
     ansible-playbook -i deploy_openstack/inventories/local/local.yml \
       deploy_openstack/playbook_setup_controller.yml
     ```

   * Compute nodes:

     ```bash
     ansible-playbook -i deploy_openstack/inventories/local/local.yml \
       deploy_openstack/playbook_setup_compute.yml
     ```

   * Storage node:

     ```bash
     ansible-playbook -i deploy_openstack/inventories/local/local.yml \
       deploy_openstack/playbook_setup_storage.yml
     ```

### One-step OpenStack deployment

```bash
ansible-playbook -i deploy_openstack/inventories/local/local.yml \
  deploy_openstack/playbook_deploy.yml
```

At this point, your **OpenStack Lab should be operational**.

---

## Observability Stack (OpenSearch, Prometheus, Grafana)

1. Load environment variables and navigate to Ansible:

   ```bash
   source envrc
   cd ansible
   ```

2. Deploy OpenSearch components individually:

   * OpenSearch:

     ```bash
     ansible-playbook -i deploy_opensearch/inventories/local/local.yml \
       deploy_opensearch/playbook_setup_opensearch.yml
     ```

   * OpenSearch Dashboards:

     ```bash
     ansible-playbook -i deploy_opensearch/inventories/local/local.yml \
       deploy_opensearch/playbook_setup_opensearch_dashboard.yml
     ```

   * Logstash and Filebeat:

     ```bash
     ansible-playbook -i deploy_opensearch/inventories/local/local.yml \
       deploy_opensearch/playbook_setup_filebeat.yml
     ```

3. Deploy Prometheus and Grafana components individually:

   * Prometheus and Grafana:

     ```bash
     ansible-playbook -i deploy_prometheus/inventories/local/local.yml \
       deploy_prometheus/playbook_setup_prometheus.yml
     ```

   * Prometheus node exporter:

     ```bash
     ansible-playbook -i deploy_prometheus/inventories/local/local.yml \
       deploy_prometheus/playbook_setup_node_exporter.yml

### One-step deployment

```bash
ansible-playbook -i deploy_opensearch/inventories/local/local.yml \
  deploy_opensearch/playbook_deploy.yml

ansible-playbook -i deploy_prometheus/inventories/local/local.yml \
  deploy_prometheus/playbook_deploy.yml
```

---

## OpenStack Bootstrap

This step initializes basic OpenStack resources.

1. Prepare a VM image in **qcow2** format.

2. Export the image path:

   ```bash
   export IMAGE_PATH=/path/to/image.qcow2
   ```

3. Copy the image to the Controller VM:

   ```bash
   make -C vagrant/controller copy-image-to-vm
   ```

4. Bootstrap OpenStack:

   ```bash
   source envrc
   cd ansible
   ansible-playbook -i bootstrap_openstack/inventories/local/local.yml \
     bootstrap_openstack/playbook_bootstrap.yml
   ```

This configures:

* Flavors
* Glance images
* Provider / self-service networks
* Security groups

---

## Networking Note (Nested Virtualization)

If OpenStack instances cannot access the internet and you are using:

* Custom bridge: `br-provider0`
* Subnet: `192.168.123.0/24`

Ensure NAT is configured on the **bare-metal host**:

```bash
sudo iptables -t nat -A POSTROUTING \
  -s 192.168.123.0/24 \
  -o <host-external-interface> \
  -j MASQUERADE
```

To auto-detect the external interface:

```bash
$(ip route get 1.1.1.1 | awk '{print $5}')
```

---

## CI/CD Lab Deployment

This deploys GitLab, Jenkins, Runner, and Prometheus on OpenStack.

1. Load environment variables:

   ```bash
   source envrc
   ```

2. Generate OpenStack client config:

   ```bash
   generate_os_client_config local cicd_lab
   ```

3. Bootstrap CI/CD VMs:

   ```bash
   cd ansible
   ansible-playbook -i bootstrap_openstack/inventories/local/local.yml \
     bootstrap_openstack/playbook_init_cicd_server.yml
   ```

4. Assign floating IPs via Horizon:

   * URL: OpenStack Dashboard
   * User: `admin`
   * Password: `vagrant`

5. Export cloud config:

   ```bash
   export OS_CLIENT_CONFIG_FILE=$ROOT_DIR/generated/local_clouds.yml
   ```

6. Provision services:

   * Pre-setup:

     ```bash
     ansible-playbook -i cicd_in_openstack/inventories/local/openstack.yml \
       cicd_in_openstack/playbook_pre_setup.yml
     ```
   * GitLab:

     ```bash
     ansible-playbook -i cicd_in_openstack/inventories/local/openstack.yml \
       cicd_in_openstack/playbook_setup_gitlab.yml
     ```
   * Jenkins:

     ```bash
     ansible-playbook -i cicd_in_openstack/inventories/local/openstack.yml \
       cicd_in_openstack/playbook_setup_jenkins.yml
     ```
   * Runner:

     ```bash
     ansible-playbook -i cicd_in_openstack/inventories/local/openstack.yml \
       cicd_in_openstack/playbook_setup_runner.yml
     ```
   * Prometheus:

     ```bash
     ansible-playbook -i cicd_in_openstack/inventories/local/openstack.yml \
       cicd_in_openstack/playbook_setup_ci_monitor.yml
     ```
   * Node Exporter:

     ```bash
     ansible-playbook -i cicd_in_openstack/inventories/local/openstack.yml \
       cicd_in_openstack/playbook_setup_node_exporter.yml
     ```

---

## Kubernetes Lab Deployment

This provisions a **kubeadm-based Kubernetes cluster** on OpenStack.

1. Load environment variables:

   ```bash
   source envrc
   ```

2. Generate OpenStack client config:

   ```bash
   generate_os_client_config local kubernetes_lab
   ```

3. Bootstrap Kubernetes VMs:

   ```bash
   cd ansible
   ansible-playbook -i bootstrap_openstack/inventories/local/local.yml \
     bootstrap_openstack/playbook_init_kubernetes.yml
   ```

4. Assign floating IPs via Horizon.

   * URL: OpenStack Dashboard
   * User: `admin`
   * Password: `vagrant`

5. Export cloud config:

   ```bash
   export OS_CLIENT_CONFIG_FILE=$ROOT_DIR/generated/local_clouds.yml
   ```

6. Provision Kubernetes:

   * Pre-setup:

     ```bash
     ansible-playbook -i kubernetes_in_openstack/inventories/local/openstack.yml \
       kubernetes_in_openstack/playbook_pre_setup.yml
     ```
   * Install Kubernetes:

     ```bash
     ansible-playbook -i kubernetes_in_openstack/inventories/local/openstack.yml \
       kubernetes_in_openstack/playbook_setup_kubernetes.yml
     ```
   * Configure nodes:

     ```bash
     ansible-playbook -i kubernetes_in_openstack/inventories/local/openstack.yml \
       kubernetes_in_openstack/playbook_setup_nodes.yml
     ```

---

## Contact

For collaboration, questions, or discussions:

**Email:** [meriz.rizal@gmail.com](mailto:meriz.rizal@gmail.com)

