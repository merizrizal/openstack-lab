MAKEFLAGS += --no-print-directory
SHELL := /bin/bash

export MAKE := make

start-vm:
	vagrant up

stop-vm:
	vagrant halt

teardown-vm: stop-vm
	vagrant destroy -f

rebuild-base-image:
	@if [ -z "$$BASE_IMAGE_NAME" ]; then \
		echo ">>>>> BASE_IMAGE_NAME need to be provided <<<<<"; \
		echo "BASE_IMAGE_NAME=this_name"; \
		exit 1; \
	fi;
	@$(MAKE) teardown-vm start-vm
	@sleep 5
	@if [[ "$$BASE_IMAGE_NAME" == "ubuntu_24" ]]; then \
		vagrant ssh $$BASE_IMAGE_NAME -c "sudo sed -i 's/^FallbackDNS=.*/FallbackDNS=8.8.8.8/g' /etc/systemd/resolved.conf"; \
		vagrant ssh $$BASE_IMAGE_NAME -c "sudo sed -i 's/^DNSSEC=.*/DNSSEC=8.8.8.8/g' /etc/systemd/resolved.conf"; \
		vagrant ssh $$BASE_IMAGE_NAME -c "sudo systemctl restart systemd-resolved"; \
		vagrant upload ./netplan-config.cfg /home/vagrant/network-config.cfg $$BASE_IMAGE_NAME; \
		vagrant ssh $$BASE_IMAGE_NAME -c "sudo cp /home/vagrant/network-config.cfg /etc/cloud/cloud.cfg.d/99-network-config.cfg"; \
		vagrant ssh $$BASE_IMAGE_NAME -c "sudo cloud-init clean"; \
	fi
	@sleep 5 && vagrant halt; \
	image_name=base_image_$(BASE_IMAGE_NAME); \
	image_path=`(virsh domblklist --domain $$image_name | awk '/vda/{print $$2}')`; \
	echo Found base image path: $$image_path; \
	sudo qemu-img create -f qcow2 -b $$image_path -F qcow2 $$image_name.qcow2; \
	current_user=`(id -u -n)`; \
	sudo chown $$current_user:$$current_user $$image_name.qcow2; \
	image_size=`(qemu-img info --output=json $$image_name.qcow2 | jq -r '."virtual-size"' | awk '{print $$1}')`; \
	echo Image size = $$image_size; \
	image_size_h=`(qemu-img info --output=json $$image_name.qcow2 | jq -r '."virtual-size"' | awk '{s=int($$1)/(1024^3); print (s == int(s)) ? s : int(s)+1 }')`; \
	echo Human readable image size = $$image_size_h GB; \
	box_name=$(BASE_IMAGE_NAME)_base; \
	sudo ./create_box.sh $$image_name.qcow2 $$box_name.box Vagrantfile.add $$image_size_h; \
	sudo chown $$current_user:$$current_user $$box_name.box; \
	vagrant box add $$box_name.box --force --name $$box_name; \
	rm $$box_name.box; rm $$image_name.qcow2;

rebuild-base-image-ubuntu:
	@$(MAKE) rebuild-base-image BASE_IMAGE_NAME=ubuntu_24
	@$(MAKE) teardown-vm BASE_IMAGE_NAME=ubuntu_24

check-base-image:
	@image=`(vagrant box list | grep ubuntu_24_base)`; \
	if [ -z "$$image" ]; then \
		echo ">>>>> Base image is not found. Run make rebuild-base-image <<<<<"; \
		exit 1; \
	else \
		echo Found $$image; \
	fi;

prepare-ubuntu-vm-network-patch:
	@echo "Patching VM network $$VM"
	@shell_file=$$FILE; \
	echo "#!/bin/bash" > $$shell_file; \
	echo "" >> $$shell_file; \
	echo "mv /etc/netplan/50-vagrant.yaml /tmp/" >> $$shell_file; \
	echo "rm /etc/netplan/*" >> $$shell_file; \
	echo "mv /tmp/50-vagrant.yaml /etc/netplan/" >> $$shell_file; \
	echo "cp /etc/netplan/50-vagrant.yaml /etc/netplan/51-vagrant.yaml" >> $$shell_file; \
	echo "sed -i 's/eth1:/eth0:/g' /etc/netplan/51-vagrant.yaml" >> $$shell_file; \
	echo "sed -i 's/.123./.121./g' /etc/netplan/51-vagrant.yaml" >> $$shell_file; \
	echo "" >> $$shell_file; \
	echo "echo '      nameservers:' | tee --append /etc/netplan/51-vagrant.yaml" >> $$shell_file; \
	echo "echo '        addresses: [8.8.8.8, 1.1.1.1]' | tee --append /etc/netplan/51-vagrant.yaml" >> $$shell_file; \
	echo "echo '      routes:' | tee --append /etc/netplan/51-vagrant.yaml" >> $$shell_file; \
	echo "echo '      - to: 0.0.0.0/0' | tee --append /etc/netplan/51-vagrant.yaml" >> $$shell_file; \
	echo "echo '        via: 192.168.124.1' | tee --append /etc/netplan/51-vagrant.yaml" >> $$shell_file; \
	echo "netplan apply" >> $$shell_file; \
	chmod +x $$shell_file;