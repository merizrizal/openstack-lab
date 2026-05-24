MAKEFLAGS += --no-print-directory
SHELL := /bin/bash

export MAKE := make

validate-ceph:
	@$(MAKE) start-validate-ceph TARGET_ENV=local

validate-openstack:
	@$(MAKE) start-validate-openstack TARGET_ENV=local

start-validate-%:
	@mkdir -p molecule/log/$*
	@mkdir -p molecule/$*/results/$$TARGET_ENV/expected
	@date=`(date "+%Y_%m_%d_%H_%M_%N")`; \
	SCENARIO=$* LOG_FILE=$$TARGET_ENV-$$date molecule -c molecule/config.yml check -s $* --report --command-borders
	@rm -rf molecule/$*/results/$$TARGET_ENV/actual

test-ceph:
	@$(MAKE) start-test-ceph TARGET_ENV=local

test-openstack:
	@$(MAKE) start-test-openstack TARGET_ENV=local

start-test-%:
	@mkdir -p molecule/log/$*
	@date=`(date "+%Y_%m_%d_%H_%M_%N")`; \
	SCENARIO=$* LOG_FILE=$$TARGET_ENV-$$date molecule -c molecule/config.yml test -s $* --report --command-borders