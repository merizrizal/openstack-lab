# Secure Diagnostic Acceptance Operations Contract

## Purpose

This contract defines the approved local boundary for Phase 03 server-specific diagnostic acceptance. It supersedes any acceptance design that passes a server identifier to Ansible or the OpenStack CLI.

## Fixed Paths and Principals

| Item | Contract |
| --- | --- |
| Acceptance host | `assistant02` only |
| Runtime identity | `aiops_assistant:aiops_assistant` |
| Consumer | `/opt/openstack-ai-ops-assistant/scripts/approved/secure_diagnostic_acceptance_consumer` |
| Runtime record directory | `/run/openstack-ai-ops/secure-diagnostic-acceptance` |
| Record ownership and mode | `aiops_assistant:aiops_assistant`, `0600` |
| Record directory ownership and mode | `aiops_assistant:aiops_assistant`, `0700` |
| Operator access | externally administered fixed sudo rule for the consumer only |

The consumer is root-owned, non-symlinked, mode `0750`, and executable by the runtime group. No generic shell, login shell, arbitrary interpreter, alternate executable, profile override, or additional argument is permitted.

## Invocation Boundary

The approved operator executes the fixed consumer through an externally administered `sudo -u aiops_assistant` rule from an approved interactive terminal. The command accepts exactly one non-secret run identifier matching `^[a-z0-9][a-z0-9-]{0,47}$`; `20026-0001` is an approved example.

The consumer requires a controlling `/dev/tty`, disables echo while collecting exactly one server identifier, validates the identifier, and restores terminal state on every exit path. The terminal session has no keystroke recording or identifier-retaining audit trail.

The server identifier must never enter Git, inventory, defaults, extra-vars, process arguments, environment variables, shell history, callback output, Ansible task state, evidence, or the runtime record.

## Consumer Authority

The consumer uses the installed OpenStack SDK in process as `aiops_assistant`. It may perform only the reviewed read operations needed for the existing server-basic and server-network outcome contracts. It must not spawn the OpenStack CLI, shell, generic executor, SSH client, sudo, or a listener.

Raw SDK responses and the server identifier remain in process memory only. The consumer normalizes and validates output before writing a record, unlinks incomplete records on failure, and exits after one invocation.

## Outcome Record

For one run identifier, the consumer writes at most one atomically-created JSON record. It may contain only:

- schema version and UTC timestamp;
- non-secret run identifier;
- fixed host and transport labels;
- fixed tool names;
- normalized outcome/status values;
- JSON-shape, bounds, and redaction booleans; and
- an explicit unresolved-gate value.

It must not contain identifiers, addresses, command text or arguments, stdout, stderr, SDK or cloud payloads, profile data, credentials, or comparator data.

## Acceptance Sequence

1. An administrator records a boolean-only pre-state attestation for the run identifier.
2. The acceptance playbook runs only the non-identifier project-summary diagnostic under its existing controls.
3. The operator invokes the local consumer from the approved terminal.
4. The acceptance playbook verifies only the outcome record's path, ownership, mode, schema, run identifier, and allowed fields.
5. An administrator records a boolean-only post-state attestation; acceptance fails unless `unchanged` is true.

The sudo rule, operator identity, terminal-audit configuration, and administrator comparator remain externally owned and are not stored or configured in this repository.

## Failure Handling

| Condition | Required action |
| --- | --- |
| No controlling TTY, invalid run identifier, or invalid server identifier | Stop without cloud access or record creation. |
| Consumer path/owner/mode or sudo rule is not approved | Stop before identifier collection. |
| SDK, profile, or read operation failure | Write no raw data; optionally write only an allowed normalized failure record. |
| Unsafe, malformed, oversized, or non-redacted response | Delete partial record and stop. |
| Missing/invalid outcome record or failed post-state attestation | Fail acceptance; administrator investigates externally. |

## Validation Requirements

Before live use, static checks must verify the fixed path, owner/mode, no CLI or subprocess execution, TTY-only input, run-identifier validation, atomic `0600` outcome records, field allowlist, and absence of identifier-bearing persistence. A live invocation remains separately approved.
