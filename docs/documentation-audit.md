# Documentation Audit

This note captures documentation mismatches found while reconciling `docs/` with the repository implementation.

## Corrected in This Docs Refresh

1. Reconciled docs with the Gazpacho / 2026.1 implementation.
   - The docs now call out `cloud-archive:gazpacho` as the current OpenStack package source.
   - Nova metadata API placement on Apache port `8775` is now documented in the base knowledge, architecture, workflow, and troubleshooting docs.
   - README Horizon examples now use the current lab admin password value, `platformpass`.

2. Added troubleshooting coverage for the metadata `503` issue found after the Gazpacho upgrade.
   - `docs/troubleshooting/01-openstack-instance-metadata-503.md` records the investigation path, root cause, fix, and validation commands.
   - `docs/README.md` now includes `docs/troubleshooting/` in the reading map.

3. Added a base-knowledge guide for new operators and contributors.
   - `docs/base-knowledge.md` now explains the project mental model, node roles, network model, OpenStack service responsibilities, Ceph artifact lifecycle, inventory boundaries, and common edit points.
   - Earlier docs were accurate but assumed the reader already understood how Vagrant, Ansible, Ceph, OpenStack, and downstream labs fit together.

4. Added concrete stage validation checkpoints to the workflow guide.
   - `docs/workflows.md` now includes checks after Vagrant, Ceph, OpenStack, OpenStack bootstrap, observability, and dynamic-inventory lab setup.
   - This closes the previous gap where validation advice was mostly conceptual.

5. `envrc` does more than export variables.
   - It sets `ROOT_DIR` and `ANSIBLE_CONFIG`, installs the git hook from `githooks/`, checks for Python 3.11-3.14, verifies `pip` and `venv`, and exposes `generate_os_client_config`.
   - Earlier docs treated it mostly as a plain environment-loader step.

6. The base lab topology is more specific than the earlier summaries implied.
   - Default lab nodes are `controller01`, `compute01`, `compute02`, `storage01`, and `ceph01`.
   - `ceph02` and `ceph03` exist only as commented inventory examples.
   - Storage and Ceph nodes attach additional raw disks for Cinder and OSD use.

7. Observability placement is split across two Ansible domains.
   - `deploy_opensearch` installs OpenSearch and Dashboards on `controller` and Filebeat on `controller`, `compute`, and `storage`.
   - `deploy_prometheus` installs Prometheus, Grafana, OpenStack exporter integration, and OpenSearch datasource wiring on `controller`, plus node exporter on `controller`, `compute`, `storage`, and `ceph_adm`.
   - Earlier docs described the stack at a higher level without clearly stating where each component lands.

8. Step-by-step OpenStack deployment needs a separate Ceph integration step when Ceph is enabled.
   - `playbook_pre_setup.yml` already consumes Ceph artifacts through the `ceph` role.
   - `playbook_deploy.yml` also imports `playbook_ceph_integration.yml` when `ceph_enabled: true`.
   - A manual staged deployment therefore needs that extra integration playbook to match the one-shot path.

9. OpenStack bootstrap is also the prerequisite for downstream dynamic-inventory labs.
   - `bootstrap_openstack/playbook_bootstrap.yml` creates flavors, image, provider/self-service networks, router, and a security group.
   - The CI/CD and Kubernetes labs then rely on `generate_os_client_config`, OpenStack server creation playbooks, and the OpenStack inventory plugin.
   - Earlier docs mentioned these areas, but not their operational dependency chain tightly enough.

## Still True After Review

1. Ceph remains enabled by default for the OpenStack domain.
2. Node exporter still defaults to port `9200`.
3. CI only validates inventory-variable contracts through Molecule, not full runtime behavior.
4. OpenStack and Ceph local inventories now use `ansible_sys_user`, while several bootstrap/downstream domains still use the `vagrant` account.

## Remaining Documentation Opportunities

1. Add screenshots or sample command output for successful lab validation checkpoints.
2. Extend the troubleshooting catalog with more common failures, symptoms, likely causes, and first commands to run.
3. Add a secrets-hardening guide that shows how to replace lab defaults with Ansible Vault or SOPS.
