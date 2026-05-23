# OpenStack Lab Documentation Pack

This directory contains a repository-backed technical study of the OpenStack lab.
It is intended to describe what the code currently does, not just the intended design.

## Documents

Recommended reading order:

1. `docs/base-knowledge.md`
   - Base concepts, node roles, network model, repository map, variable boundaries, and validation mindset for this lab.
2. `docs/architecture.md`
   - System architecture, node roles, network model, inventory boundaries, and dependency graph.
3. `docs/workflows.md`
   - End-to-end deployment and operational runbooks for OpenStack, Ceph, observability, CI/CD lab, and Kubernetes lab.
4. `docs/quality-assessment.md`
   - Automation quality, idempotency patterns, CI/testing posture, and maintainability review.
5. `docs/findings-and-recommendations.md`
   - Prioritized findings, risks, and practical remediation roadmap.
6. `docs/documentation-audit.md`
   - Documentation discrepancies found while reconciling `docs/` with the current repo implementation.
7. `docs/troubleshooting/`
   - Incident-style troubleshooting notes for known operational failures and their validated fixes.

## Scope

The analysis covers:

- Repository structure and orchestration model (`vagrant/`, `ansible/`, `molecule/`, CI files).
- Host inventories, group vars, shared roles, and service-level configuration behavior.
- Operational risks, security posture, and consistency gaps.
- Lab fundamentals for new contributors and operators who need to understand how the pieces fit before running playbooks.
- Troubleshooting records for failures observed while upgrading or operating the lab.
