# OpenStack Lab Architecture Summary

## Layers

The repository provisions a learning lab through four main layers:

1. Vagrant and Libvirt create the base virtual machines from inventory.
2. Ansible deploys OpenStack and supporting platform services.
3. OpenStack APIs bootstrap tenant resources and optional CI/CD or Kubernetes workloads.
4. Molecule and repository checks validate inventory contracts and runtime behavior.

## Service Placement

- `controller01` hosts the OpenStack control plane and Apache-served APIs, including Nova compute, Nova metadata, Neutron, Keystone, Cinder, and Placement endpoints.
- `compute01` and `compute02` host Nova and Neutron compute agents.
- `storage01` hosts Cinder volume services.
- `ceph01` is the default Ceph administration and storage node when Ceph is enabled.
- Observability control services are centered on `controller01`, with selected agents and exporters distributed across infrastructure nodes.

The assistant runtime is separate from controller, compute, storage, Ceph, database, message-bus, and observability service roles. Its initial MCP transport is local stdio and does not open a network listener.

## Operational Dependencies

Guest metadata follows the Neutron metadata path to the Nova metadata API on `controller01`. General server or network health does not alone prove that this complete path is healthy.

Ceph-backed OpenStack deployment requires Ceph initialization and exported configuration before OpenStack integration. Optional workload domains depend on generated cloud configuration and dynamic OpenStack inventory.

## Diagnostic Boundary

Architecture context helps identify likely service ownership and failure domains, but it is not live evidence. Use only discovered read-only tools for current state, preserve result status and request IDs, and clearly state evidence gaps. Do not infer credentials, hidden network details, host health, or remediation actions from this summary.
