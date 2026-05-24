# Quality and Maintainability Assessment

## 1) What Is Strong

1. Clear domain partitioning:
   - OpenStack, Ceph, observability, CI/CD, and Kubernetes are cleanly separated.
2. Reusable shared roles:
   - `shared_resources/playbooks/roles/*` centralizes common host prep, Docker, and telemetry behavior.
3. Practical lab ergonomics:
   - Vagrant + inventories + Makefiles make end-to-end setup approachable.
4. Dual CI footprint:
   - GitHub and GitLab pipelines both enforce linting and molecule variable checks.
5. Inventory contract testing:
   - Molecule snapshot validation guards accidental variable-schema drift.
6. Runtime verification:
   - Molecule `test` runs smoke checks by default and can run the OpenStack
     workload lifecycle against a deployed lab when enabled.

## 2) Testing Posture

Current test scope:

- Linting with `ansible-lint`.
- Molecule `check` variable validation against expected JSON snapshots.
- Molecule `test` runtime smoke verification for deployed lab environments.
- Optional OpenStack end-to-end workload verification with
  `MOLECULE_E2E_VERIFY=true`.

Missing coverage areas:

- Default CI runs the Molecule `check` path, not the Molecule `test` runtime
  path, because it does not deploy a live lab.
- Runtime assertions for network reachability, endpoint availability, and guest
  metadata reachability require a deployed lab and Molecule `test`.
- No workload scenario tests for CI/CD and Kubernetes flows.

Net effect:

- High confidence in inventory-variable shape.
- Moderate/low confidence in runtime system behavior after refactors unless
  Molecule `test` runtime verification is run against a deployed lab.

## 3) Idempotency and Drift Visibility

Observed patterns:

- Frequent use of `shell`/`command`.
- Many tasks force `changed_when: false`.
- Several tasks rely on grep-based existence checks.

Impact:

- Good for avoiding noisy changes in labs.
- Weaker for production-style change auditability and drift detection.

## 4) Security Posture (Lab-Oriented by Default)

Current behavior is explicitly lab-friendly:

- Plaintext credentials in repo inventories.
- SSH strict host checking disabled.
- Broadly permissive defaults for internal services.

For isolated local learning this is acceptable.
For any shared or semi-public environment, this must be hardened.

## 5) Operational Robustness

Strengths:

- Modular playbook composition (`import_playbook`, include roles/tasks).
- Sensible host grouping and staged deploy strategy.

Weak points:

- Multiple hidden couplings (optional Ceph artifacts consumed from `/tmp`, generated cloud config dependencies).
- Some static assumptions that can break portability (hardcoded network, architecture-specific values).

## 6) Maintainability View

The codebase is maintainable for a single-owner or small-team lab project.
Main scaling constraints are:

1. Secret management model.
2. Limited runtime test coverage.
3. Tight coupling to one topology and host assumptions.
4. A few correctness gaps that should be fixed before adding new features.

## 7) Recommended Quality Upgrades

1. Use Molecule smoke verification after deployment:
   - Run Molecule `test` against a live lab inventory.
   - Current OpenStack coverage includes Keystone token issuance, service catalog endpoint reachability, Nova/Neutron/Cinder service status, Apache listener checks for OpenStack APIs, Nova metadata API checks on `8775`, Ceph integration file checks when enabled, Prometheus target health, and OpenSearch health.
   - Current Ceph coverage includes cluster health, OSD status, and orchestrator host registration.
   - Keep smoke tests read-only where possible and fail with targeted messages that identify the failed service or endpoint.
2. Use Molecule end-to-end workload verification after OpenStack bootstrap:
   - Enable with `MOLECULE_E2E_VERIFY=true` via Molecule `test` after image,
     flavor, network, and security group bootstrap resources exist.
   - Current coverage boots one small VM in OpenStack, waits for `ACTIVE`, verifies tenant network attachment, checks the console log for metadata `503` failures, attaches and detaches a small Cinder volume, then deletes all test resources.
   - The workload test uses unique resource names and cleanup blocks so failed runs do not leave stale instances or volumes behind.
3. Adopt secret abstraction:
   - Vault/SOPS with CI secret injection for non-lab environments.
4. Add architecture/port consistency tests:
   - Assert expected listener ports match security group rules and scrape configs.
5. Track idempotency outcomes:
   - Keep `changed_when` truthful where feasible, especially on critical bootstrap tasks.
