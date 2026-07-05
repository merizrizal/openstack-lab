# AI-OPS Approved Diagnostic Scripts Safety Policy

This directory is the repository source for reviewed AI-OPS diagnostic scripts that may be installed to:

```text
/opt/openstack-ai-ops/scripts/approved/
```

Scripts in this directory must remain diagnostic-only, read-only, narrow, and manually reviewable. They are not a generic shell, SSH, sudo, OpenStack CLI, file-write, database, service-control, or remediation interface.

## Default credential profile

Unless a script is explicitly classified otherwise, it must use the Phase 02 project-reader profile:

```text
OS_CLIENT_CONFIG_FILE=/opt/openstack-ai-ops/credentials/profiles/clouds.yaml
OS_CLOUD=aiops-project-reader
```

Do not use admin, member, service, database, RabbitMQ, SSH, or operator-reader credentials as the default. Operator-reader diagnostics must stay separate and unavailable until a non-default operator-reader profile has been explicitly created, validated, and documented.

## Read-only scope

Approved scripts may perform fixed OpenStack API read operations such as `list` and `show` for project-visible resources where policy allows.

Scripts must not expose arbitrary command execution or user-selected OpenStack subcommands. User input may select only narrow resource identifiers accepted by a reviewed script.

## Forbidden operations

Scripts in this directory must not contain or invoke operations that mutate the lab or broaden access, including:

- OpenStack create, update, delete, set, unset, add, remove, reboot, rebuild, evacuate, migrate, resize, shelve, unshelve, pause, unpause, suspend, resume, lock, unlock, rescue, unrescue, start, stop, restart, or service control operations
- package installation or upgrade commands
- service restart, reload, enable, disable, or repair commands
- unrestricted `sudo`
- generic shell execution, command passthrough, `eval`, or user-controlled subcommands
- raw SSH command forwarding
- database, RabbitMQ, or service-credential access
- file writes, append redirection, in-place edits, or config mutation
- printing, copying, or transforming credential files or secret material

If a diagnostic need appears to require any forbidden operation, stop and document it as a manual operator task outside this toolbox.

## Input validation rules

Every script that accepts input must validate it before invoking OpenStack or any other command.

MVP object identifiers and names should use a conservative safe character set, such as letters, digits, dot, underscore, colon, and hyphen. Scripts must reject empty values and shell metacharacters such as whitespace, quotes, semicolons, pipes, ampersands, redirects, dollar expansion, backticks, parentheses, braces, brackets, glob characters, and path separators unless a later reviewed policy explicitly permits them.

Validation failures must fail closed with a clear error message and non-zero exit code.

## Output rules

Prefer OpenStack JSON output, for example fixed commands using `-f json`, or clear bounded sections when multiple reads are combined.

Outputs must be scoped to the requested diagnostic and should avoid excessive data volume. Scripts must not print tokens, passwords, private keys, unredacted profile files, or secret-like configuration values.

If a section is unavailable because of policy, missing service, or permission denial, report that section as unavailable instead of escalating credentials.

## Review and static-check expectations

Before a script is trusted:

1. Review the script for fixed read-only command paths and narrow parameters.
2. Run shell syntax validation with `bash -n`.
3. Run the repository-local AI-OPS safety check once available.
4. Review any static-check false positives manually before approving.
5. Validate manually on `assistant01` with the default project-reader profile and record only redacted/non-secret evidence.

Static checks are a guardrail, not a substitute for human review. Any script change that weakens this policy must be treated as a safety-sensitive design change, not a routine implementation edit.
