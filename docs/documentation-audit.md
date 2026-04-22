# Documentation Audit

This note captures documentation mismatches found while reconciling `docs/` with the repository implementation.

## Corrected in This Docs Refresh

1. `envrc` does more than export variables.
   - It sets `ROOT_DIR` and `ANSIBLE_CONFIG`, installs the git hook from `githooks/`, checks for Python 3.11-3.14, verifies `pip` and `venv`, and exposes `generate_os_client_config`.
   - Earlier docs treated it mostly as a plain environment-loader step.

2. The base lab topology is more specific than the earlier summaries implied.
   - Default lab nodes are `controller01`, `compute01`, `compute02`, `storage01`, and `ceph01`.
   - `ceph02` and `ceph03` exist only as commented inventory examples.
   - Storage and Ceph nodes attach additional raw disks for Cinder and OSD use.

3. Observability placement is split across two Ansible domains.
   - `deploy_opensearch` installs OpenSearch and Dashboards on `controller` and Filebeat on `controller`, `compute`, and `storage`.
   - `deploy_prometheus` installs Prometheus, Grafana, OpenStack exporter integration, and OpenSearch datasource wiring on `controller`, plus node exporter on `controller`, `compute`, `storage`, and `ceph_adm`.
   - Earlier docs described the stack at a higher level without clearly stating where each component lands.

4. Step-by-step OpenStack deployment needs a separate Ceph integration step when Ceph is enabled.
   - `playbook_pre_setup.yml` already consumes Ceph artifacts through the `ceph` role.
   - `playbook_deploy.yml` also imports `playbook_ceph_integration.yml` when `ceph_enabled: true`.
   - A manual staged deployment therefore needs that extra integration playbook to match the one-shot path.

5. OpenStack bootstrap is also the prerequisite for downstream dynamic-inventory labs.
   - `bootstrap_openstack/playbook_bootstrap.yml` creates flavors, image, provider/self-service networks, router, and a security group.
   - The CI/CD and Kubernetes labs then rely on `generate_os_client_config`, OpenStack server creation playbooks, and the OpenStack inventory plugin.
   - Earlier docs mentioned these areas, but not their operational dependency chain tightly enough.

## Still True After Review

1. Ceph remains enabled by default for the OpenStack domain.
2. Node exporter still defaults to port `9200`.
3. CI only validates inventory-variable contracts through Molecule, not full runtime behavior.

## Remaining Documentation Opportunities

1. Add a dedicated operator runbook for common validation commands after each stage.
2. Add a small reference table mapping playbooks to hosts and major services.
3. Add a bootstrap note explaining the expected location and lifecycle of `/tmp/fetch-ceph*` artifacts.
