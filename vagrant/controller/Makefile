MAKEFLAGS += --no-print-directory
SHELL := /bin/bash

export MAKE := make

start-vm:
	@$(MAKE) -C ../base_image check-base-image
	@nodes=`(yq '.[] | key' ../../inventories/controller.yml)`; \
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
