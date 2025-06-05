## OpenStack Provisioning

### This repo is intended for learning OpenStack or deploying an OpenStack Lab.
#### We will install OpenStack to Libvirt KVM, this means any VM instances that is provisioned by OpenStack are running in nested virtualisation.

#### *Currently, it has only been tested on Ubuntu.

**Ansible directory structure**
```
  | - ansible
  |  | - .ansible-lint
  |  | - ansible.cfg
  |  | - bootstrap_openstack
  |  |  | - inventories
  |  |  |  | - local
  |  |  | - playbook_bootstrap.yml
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
5. Run `ansible-playbook -i bootstrap_openstack/inventories/local/local.yml bootstrap_openstack/playbook_bootstrap.yml` to bootstrap the minimum configuration, such as flavors, Glance images, provider or self-service networks, and security rules.

Reach me at meriz.rizal@gmail.com to connect with me or collaboration.
