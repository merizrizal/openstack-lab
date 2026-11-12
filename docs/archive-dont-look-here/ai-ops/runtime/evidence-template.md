# Phase 01 Runtime Evidence Note

Use this template to record actual evidence for the AI-OPS assistant runtime.

Do not mark Phase 01 complete unless each item is backed by observed evidence.

## Metadata

- Date:
- Runtime name / host:
- Operator:
- Evidence source (command, screenshot, note, log):

## Placement

- Runtime location:
- Why this placement was chosen:
- Control-plane separation confirmed:
- Not on controller / compute / storage / Ceph / database / message-bus / observability node:

## Network Reachability

- Management path used:
- Keystone endpoint reachability:
- Controller management address reachability:
- Tenant-network access required for first milestone:
- Deferred endpoints, if any:

## Baseline Tool Versions

- Python:
- Python virtual environment support:
- OpenStack CLI:
- OpenStack SDK:
- SSH client:
- curl or equivalent:
- JSON parser:
- Fast text search tool:
- Git:

## Workspace Checks

- Workspace root:
- Workspace directories present:
- Writable by runtime user where required:
- `credentials/profiles/` exists:
- `credentials/profiles/` is empty:
- `diagnostics/raw/` writable:
- `diagnostics/summaries/` writable:
- `audit/` writable or intentionally empty:

## Credential Absence

- No privileged OpenStack credentials installed:
- No root SSH keys for OpenStack nodes installed:
- No database credentials installed:
- No RabbitMQ credentials installed:
- No service configuration secrets installed:

## Prohibited-Capability Confirmation

- No generic shell execution exposed to AI:
- No generic SSH execution exposed to AI:
- No generic OpenStack CLI passthrough exposed to AI:
- No file-write / package-install / service-restart / remediation tools exposed to AI:

## Notes

- Observed issues:
- Follow-up actions:
- Link to related runtime README or dated summary:
