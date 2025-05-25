MAKEFLAGS += --no-print-directory
SHELL := /bin/bash

export MAKE := make

start-provider-network:
	@sudo ip link add name br-provider0 type bridge || true
	@sudo ip addr add 192.168.123.1/24 dev br-provider0 || true
	@sudo ip link set dev br-provider0 up || true

start-vm:
	@$(MAKE) -C ../base_image check-base-image
	@nodes=`(yq '.[] | key' ../../inventories/local/nodes.yml)`; \
	{ \
		for node in $$nodes; do \
			$(MAKE) spin-up-vm VM=$$node; \
		done; \
	}

spin-up-vm:
	@echo "> Spin-up: $$VM"; \
	INITIALIZE=1 vagrant up $$VM; \
	shell_file="/tmp/patch.sh"; \
	$(MAKE) -C ../base_image prepare-ubuntu-vm-network-patch VM=$$VM FILE=$$shell_file || exit $$?; \
	vagrant upload $$shell_file /home/vagrant/ $$VM; \
	vagrant ssh $$VM -c "sudo /home/vagrant/patch.sh"

teardown-vm:
	vagrant halt $(VM)
	vagrant destroy -f $(VM)

teardown-provider-network:
	@sudo ip link del dev br-provider0 type bridge || true

check-available-image:
	@if [ ! -f "$$IMAGE_PATH" ]; then \
		echo "Image: $$IMAGE_PATH is not found."; \
		echo "Need to set IMAGE_PATH=/path/to/image.qcow2."; \
		exit 1; \
	else \
		echo Found $$IMAGE_PATH; \
		echo Copying image; \
	fi;

copy-image-to-vm: check-available-image
	@vagrant upload $$IMAGE_PATH /home/vagrant/ubuntu24.img controller01
