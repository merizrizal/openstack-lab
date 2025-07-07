## OpenStack Provisioning

### This repo is intended for learning OpenStack or deploying an OpenStack Lab.
#### We will install OpenStack to Libvirt KVM, this means any VM instances that is provisioned by OpenStack are running in nested virtualisation.

#### *Currently, it has only been tested on Ubuntu.

**Ansible directory structure**
```
  | - ansible
  |  | - bootstrap_openstack
  |  |  | - inventories
  |  |  |  | - local
  |  |  | - playbook_bootstrap.yml
  |  |  | - playbook_init_cicd_server.yml
  |  |  | - playbook_init_kubernetes.yml
  |  | - cicd_in_openstack
  |  |  | - inventories
  |  |  |  | - local
  |  |  | - playbook_deploy.yml
  |  |  | - playbook_pre_setup.yml
  |  |  | - playbook_setup_gitlab.yml
  |  |  | - playbook_setup_jenkins.yml
  |  |  | - playbook_setup_runner.yml
  |  |  | - roles
  |  |  |  | - gitlab
  |  |  |  | - jenkins
  |  |  |  | - runner
  |  | - deploy_openstack
  |  |  | - inventories
  |  |  |  | - local
  |  |  | - playbook_deploy.yml
  |  |  | - playbook_pre_setup.yml
  |  |  | - playbook_setup_compute.yml
  |  |  | - playbook_setup_controller.yml
  |  |  | - playbook_setup_storage.yml
  |  |  | - roles
  |  |  |  | - cinder
  |  |  |  | - cinder_controller
  |  |  |  | - cinder_storage
  |  |  |  | - common
  |  |  |  | - controller
  |  |  |  | - glance
  |  |  |  | - horizon
  |  |  |  | - keystone
  |  |  |  | - neutron
  |  |  |  | - neutron_compute
  |  |  |  | - neutron_controller
  |  |  |  | - nova
  |  |  |  | - nova_compute
  |  |  |  | - nova_controller
  |  |  |  | - placement
  |  | - kubernetes_in_openstack
  |  |  | - inventories
  |  |  |  | - local
  |  |  | - playbook_pre_setup.yml
  |  |  | - playbook_setup_kubernetes.yml
  |  |  | - playbook_setup_nodes.yml
  |  |  | - roles
  |  |  |  | - kubernetes
  |  |  |  | - nodes
  |  | - shared_resources
  |  |  | - inventories
  |  |  |  | - local
  |  |  | - playbooks
  |  |  |  | - roles
  | - inventories
  |  | - local
  |  |  | - nodes.yml
```

Learning materials sourced from https://docs.openstack.org/install-guide/openstack-services.html

**Pre-requisite - Installed to our Operating System:**
- QEMU + Libvirt: https://documentation.ubuntu.com/server/how-to/virtualisation/libvirt/
- `yq`: https://github.com/mikefarah/yq
- GCC + Make or build-essential package if we are using Ubuntu.
- Vagrant: https://developer.hashicorp.com/vagrant/install
- Vagrant Libvirt: https://vagrant-libvirt.github.io/vagrant-libvirt/installation.html
- Ansible: https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html
- Install Ansible collection - merizrizal.utils: https://github.com/merizrizal/ansible-collections-for-utilities


**Preparation:**
1. Run `source envrc` then navigate to `./vagrant` directory.
2. Build the base image which will be used by Vagrant later.<br>
Run `make -C base_image/ rebuild-base-image-ubuntu`. This will create a new Vagrant box that will be used for our OpenStack VM (controller node, compute and storage node).
3. Run `make -C controller/ start-provider-network` to create a new interface which will be used by Controller, Compute and Storage node.
4. Run `make -C controller/ start-vm` to spin up 4 VMs which are 1 Controller, 2 Computes and 1 Storage node.

**Provision OpenStack:**
1. Run `source envrc` then navigate to `./ansible` directory.
2. Run `ansible-playbook -i deploy_openstack/inventories/local/local.yml deploy_openstack/playbook_pre_setup.yml` to install and configure the pre-requisite packages.
3. Run `ansible-playbook -i deploy_openstack/inventories/local/local.yml deploy_openstack/playbook_setup_controller.yml` to install and configure OpenStack services to Controller node.
4. Run `ansible-playbook -i deploy_openstack/inventories/local/local.yml deploy_openstack/playbook_setup_compute.yml` to install and configure OpenStack services to Compute node.
5. Run `ansible-playbook -i deploy_openstack/inventories/local/local.yml deploy_openstack/playbook_setup_storage.yml` to install and configure OpenStack services to Storage node.

or

Run `ansible-playbook -i deploy_openstack/inventories/local/local.yml deploy_openstack/playbook_deploy.yml` to deploy all at once.

Now our OpenStack Lab should be ready.

**Bootstraping**
1. Prepare the VM image in qcow2 format. This image is going to be uploaded to controller node.
2. Run `export IMAGE_PATH=/path/to/image.qcow2`.
3. Run `make -C vagrant/controller copy-image-to-vm`.
4. Run `source envrc` then navigate to `./ansible` directory.
5. Run `ansible-playbook -i bootstrap_openstack/inventories/local/local.yml bootstrap_openstack/playbook_bootstrap.yml` to bootstrap the minimum. configuration, such as flavors, Glance images, provider or self-service networks, and security rules.

***Note:**

> If your VM instances in OpenStack can't reach internet and if you're in a nested setup and using br-provider0 (custom bridge) with IP 192.168.123.1/24, make sure the host machine (baremetal) is doing NAT for VMs traffic.<br>
Add this on the host:
`sudo iptables -t nat -A POSTROUTING -s 192.168.123.0/24 -o <host-external-interface> -j MASQUERADE`<br>
Replace <host-external-interface> with the actual NIC connected to the internet (e.g., eth0).

<br>

**CI/CD Lab Deployment**

1. Run `source envrc`.
2. Run `generate_os_client_config local cicd_lab` to generate the OpenStack cloud config `generated/local_clouds.yml`.
3. Navigate to `./ansible` directory.
4. Run `ansible-playbook -i bootstrap_openstack/inventories/local/local.yml bootstrap_openstack/playbook_init_cicd_server.yml` to spin-up 3 VMs on top of OpenStack.
5. Run `export OS_CLIENT_CONFIG_FILE=$ROOT_DIR/generated/local_clouds.yml`
6. Run `ansible-playbook -i cicd_in_openstack/inventories/local/openstack.yml cicd_in_openstack/playbook_pre_setup.yml` to install and configure the pre-requisite packages.
7. Run `ansible-playbook -i cicd_in_openstack/inventories/local/openstack.yml cicd_in_openstack/playbook_setup_gitlab.yml` to provision Gitlab server.
8. Run `ansible-playbook -i cicd_in_openstack/inventories/local/openstack.yml cicd_in_openstack/playbook_setup_jenkins.yml` to provision Jenkins server.
9. Run `ansible-playbook -i cicd_in_openstack/inventories/local/openstack.yml cicd_in_openstack/playbook_setup_runner.yml` to provision the Runner VM. we will use this for running the pipeline job from Gitlab CI or Jenkins.

Our CI/CD Lab should be ready.

**Kubernetes Lab Deployment**

1. Run `source envrc`.
2. Run `generate_os_client_config local kubernetes_lab` to generate the OpenStack cloud config `generated/local_clouds.yml`.
3. Navigate to `./ansible` directory.
4. Run `ansible-playbook -i bootstrap_openstack/inventories/local/local.yml bootstrap_openstack/playbook_init_kubernetes.yml` to spin-up 3 VMs on top of OpenStack.
5. Run `export OS_CLIENT_CONFIG_FILE=$ROOT_DIR/generated/local_clouds.yml`
6. Run `ansible-playbook -i kubernetes_in_openstack/inventories/local/openstack.yml kubernetes_in_openstack/playbook_pre_setup.yml` to install and configure the pre-requisite packages.
7. Run `ansible-playbook -i kubernetes_in_openstack/inventories/local/openstack.yml kubernetes_in_openstack/playbook_setup_kubernetes.yml` to install and provision Kubernetes platform to all VMs.
8. Run `ansible-playbook -i kubernetes_in_openstack/inventories/local/openstack.yml kubernetes_in_openstack/playbook_setup_nodes.yml` to provision a Control plane and two Worker nodes.

Our Kubernetes Lab should be ready.

Reach me at meriz.rizal@gmail.com to connect with me or collaboration.
