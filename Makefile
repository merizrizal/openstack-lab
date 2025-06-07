MAKEFLAGS += --no-print-directory
SHELL := /bin/bash

export MAKE := make

generate-os-client-config:
	@output=$$ROOT_DIR/generated/local_clouds.yml; \
	controller01_ip_addr=`(yq '.controller01.mgmtnet_ip_address' inventories/local/nodes.yml)`; \
	os_keystone_password=`(yq '.os_keystone_password' ansible/deploy_openstack/inventories/local/group_vars/all/common_secret.yml)`; \
	echo "---" > $$output; \
	echo "clouds:" >> $$output; \
	echo "  cicd_lab:" >> $$output; \
	echo "    auth:" >> $$output; \
	echo "      auth_url: http://$$controller01_ip_addr:5000/v3" >> $$output; \
	echo "      username: admin" >> $$output; \
	echo "      password: $$os_keystone_password" >> $$output; \
	echo "      project_name: admin" >> $$output; \
	echo "      user_domain_name: default" >> $$output; \
	echo "      project_domain_name: default" >> $$output; \
	echo "    identity_api_version: 3" >> $$output; \
