## OpenStack Provisioning

### This repo is intended for learning OpenStack or deploying an OpenStack Lab.
#### We well install OpenStack to Libvirt KVM, this means any VM instances that is provisioned by OpenStack are running in nested virtualisation.

**Pre-requisite - Installed to our Operating System:**
- QEMU + Libvirt: https://documentation.ubuntu.com/server/how-to/virtualisation/libvirt/
- `yq`: https://github.com/mikef
- GCC + Make or build-essential package if we are using Ubuntu.
- Vagrant: https://developer.hashicorp.com/vagrant/install
- Vagrant Libvirt: https://vagrant-libvirt.github.io/vagrant-libvirt/installation.html


**Preparation:**
1. Navigate to `./vagrant` directory.
2. Build the base image which will be is used by Vagrant later.<br>
Run `make -C base_image/ rebuild-base-image`. This will create a new Vagrant box that will be used for our OpenStack VM (controller node and compute node).
3. Run `make -C controller/ start-provider-network` to create a new interface which will be used by Controller and Compute node.
4. Run `make -C controller/ start-vm` to spin up 2 VMs which are Controller and Compute node.

**Provision OpenStack:**
1. Navigate to `./ansible` directory.
2. Run `ansible-playbook -i inventory_local.yml playbook_pre_setup.yml` to install and configure the pre-requisite packages.
3. Run `ansible-playbook -i inventory_local.yml playbook_setup_controller.yml` to install and configure OpenStack services to Controller node.
4. Run `ansible-playbook -i inventory_local.yml playbook_setup_compute.yml` to install and configure OpenStack services to Compute node.

Now our OpenStack Lab should be ready.

**Known Issues:**
- Once we provisioned a VM by doing `openstack create server`. There will be no IP address configured. Somehow, the OpenStack DHCP service does not work as expected. So we need to configure the IP address manually on the VM.
- Also we need to configure this on our bare-metal `sudo iptables -t nat -A POSTROUTING -s 192.168.123.0/24 -o <our-physical-interface> -j MASQUERADE` to allow the VM to be connected to the internet.

Reach me at meriz.rizal@gmail.com to connect with me