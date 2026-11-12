## Architectural Design Specification: Restricted Host Diagnostics

**Source:** `docs/ai-ops/implementation-plan/06-restricted-host-diagnostics.md` (Phase 06, Steps 1-6)

**Goal:** Add opt-in, audited metadata, Nova, and Neutron host diagnostics through a dedicated observer identity, forced-command SSH, a narrowly allowlisted sudo collector, explicit host/time-window validation, and the existing local tool-runner safety gateway—without exposing generic SSH, sudo, shell, file access, service control, or remediation.

---

### I. Overview and Contract

Phase 06 extends the proven project-scoped API diagnostic path with a higher-risk host-evidence path:

```text
operator or future AI client
  -> existing local tool runner
  -> explicit tool, host, and time-window validation
  -> fixed assistant-side SSH connector
  -> dedicated observer key and forced command
  -> root-owned host collector allowed by one narrow sudo rule
  -> bounded, redacted log/status evidence
  -> existing result envelope and audit event
```

The local runner remains the public safety gateway. Phase 06 must not add a public generic SSH, sudo, shell, file-read, service-control, or command-passthrough tool. SSH is an internal implementation detail of three named diagnostics only.

#### Public Tool Contract (Conceptual)

Proposed public names:

- `recent_metadata_errors`
- `recent_nova_errors`
- `recent_neutron_errors`

Each tool accepts:

- `host` — required and validated against an explicit per-tool list, never only a regex;
- `time_window` — optional with a proposed default of `15m`, validated against an exact bounded set.

Proposed initial bounded values are `15m`, `30m`, and `1h`. The list is an assumption to confirm in Chunk 0. Arbitrary durations, negative values, absolute timestamps, whitespace, path separators, and shell metacharacters must fail before execution.

Proposed initial host matrix, derived from observed inventory and service placement:

| Tool | Initial allowed hosts | Reason |
|---|---|---|
| `recent_metadata_errors` | `controller01` | The repository installs Nova metadata WSGI, Neutron metadata agent, Apache metadata logs, and port `8775` on the controller path. |
| `recent_nova_errors` | `controller01`, `compute01`, `compute02` | Nova controller services run on `controller01`; `nova-compute` runs on both compute nodes. |
| `recent_neutron_errors` | `controller01`, `compute01`, `compute02` | Neutron controller services run on `controller01`; Neutron agent roles run on both compute nodes. |

`storage01` is part of the observer model but has no Phase 06 Nova/Neutron/metadata tool assignment, so least privilege keeps it unprovisioned by default. `ceph01` is excluded because the OpenStack inventory does not include it and `ceph_enabled` is currently false. Either host class requires a later reviewed tool and explicit opt-in.

#### Tool Registry Contract (Concrete Extension Point; Proposed Fields)

The concrete registry is:

```text
ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/tool_registry.json
```

Existing entries already declare risk level, availability, timeout, output limit, mutation guarantee, and ordered arguments. Its advertised validation types include `allowed_host_list` and `bounded_time_window`, but the concrete runner currently implements only `required_string` and `safe_identifier_pattern`.

Proposed host-tool entries must declare:

- `risk_level: "high_readonly_restricted_host_scope"`;
- `credential_profile: "restricted-ssh-observer"`;
- `available: false` until observer provisioning and denial validation succeed;
- one fixed diagnostic kind controlled by reviewed registry data, not caller input;
- per-tool host `allowed_values`;
- exact time-window `allowed_values` and default;
- a short timeout and output-size limit;
- `mutation_guarantee: "forced_command_restricted_sudo_readonly_bounded"`.

A proposed `fixed_arguments` registry field may prepend the non-user-selectable diagnostic kind (`metadata`, `nova`, or `neutron`) to the connector argv. Chunk 0 must confirm this approach. It must be rejected if registry data is malformed and must never accept caller overrides.

#### Existing Runner Function Contracts (Concrete)

The current runner provides these confirmed integration points in `aiops_tool_runner.py`:

```text
load_registry(path) -> dict
validate_argument_value(argument_definition, value, supported_validation_types) -> str
validate_request(registry, tool_name, raw_args) -> (requested_tool, validated_args)
build_command_argv(requested_tool, validated_args) -> list[str]
run_tool(registry, requested_tool, validated_args) -> execution-result dict
build_result_envelope(...) -> dict
build_audit_event(envelope) -> dict
write_audit_event(path, event) -> None
main(argv) -> process exit code
```

**Function Signature Contract (Conceptual):** validator helpers may be introduced as:

```text
validate_allowed_host(argument_definition, value) -> str
validate_bounded_time_window(argument_definition, value) -> str
validate_fixed_arguments(requested_tool) -> list[str]
```

Inputs are reviewed registry definitions and caller values; outputs are unchanged validated strings or fixed argv values. Initial stubs must raise a clear `ValueError` rather than return success. That is safe because host tools are not registered yet and avoids silently accepting an unimplemented boundary.

`build_command_argv` should remain argv-only and `shell=False`; its proposed order is:

```text
[script_target, *fixed_arguments, *validated_user_arguments]
```

#### Assistant-Side Connector Contract (Conceptual)

Proposed source path:

```text
ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/host_diagnostics/aiops_host_diagnostic_connector.py
```

Proposed runtime path:

```text
/opt/openstack-ai-ops/scripts/host_diagnostics/aiops_host_diagnostic_connector.py
```

**Function Signature Contract (Conceptual):** the connector may expose:

```text
load_host_policy(path) -> mapping
validate_connector_request(kind, host_alias, time_window, policy) -> resolved target
build_ssh_argv(resolved_target, kind, time_window, key_path, known_hosts_path) -> list[str]
run_connector(argv, timeout_seconds) -> process result
main(argv) -> process exit code
```

The connector receives only the registry-controlled diagnostic kind and runner-validated host/window. It resolves the alias from a root-managed local policy, then invokes `/usr/bin/ssh` using an argv list, `BatchMode=yes`, `IdentitiesOnly=yes`, strict host-key verification, a dedicated private key, no TTY, and no forwarding. It must not use `shell=True`, `os.system`, an SSH config wildcard, caller-provided addresses, or caller-provided remote commands.

The exact host-policy source path is **proposed** and must be confirmed in Chunk 0. A generated root-managed JSON mapping is preferred over assuming local DNS resolution.

#### Restricted Observer SSH Contract (Conceptual)

Proposed observer identity: `aiops-observer`.

Required controls:

- dedicated keypair used only for Phase 06 host diagnostics;
- private key stored on `assistant01`, owned by `assistant`, mode `0600`;
- observer account password locked;
- no membership in privileged service or administrator groups;
- authorized-key options that force one root-owned dispatcher/collector entrypoint and apply `restrict`;
- no PTY, agent forwarding, port forwarding, X11 forwarding, user rc, or interactive command;
- pinned host keys in a dedicated `known_hosts` file;
- one reviewed `NOPASSWD` sudo command for the root-owned collector entrypoint only;
- no `ALL`, shell, editor, package manager, service-control, database, arbitrary `journalctl`, arbitrary `cat`, or arbitrary `tail` sudo rule.

The observer may possess a normal shell only if OpenSSH requires it to execute the forced command. The forced-command key restriction must reject an empty `SSH_ORIGINAL_COMMAND`, interactive login, and every command shape except the exact diagnostic kind/window grammar.

#### Host Collector Contract (Conceptual)

Proposed role and source path:

```text
ansible/ai_ops_runtime/roles/host_observer/
ansible/ai_ops_runtime/roles/host_observer/files/aiops_host_diagnostic.py
```

Proposed installed path:

```text
/usr/local/sbin/aiops-host-diagnostic
```

**Function Signature Contract (Conceptual):** the collector may expose:

```text
parse_forced_command(original_command) -> (kind, time_window)
validate_kind_and_window(kind, time_window) -> validated request
build_fixed_journal_argv(unit, window, line_limit) -> list[str]
collect_fixed_log_tail(path, line_limit) -> section
collect_service_state(unit) -> section
redact_line(text) -> text
bound_payload(payload, byte_limit) -> payload
main(argv, environ) -> process exit code
```

The same root-owned executable may serve as the forced-command dispatcher and, after validation, invoke itself through `sudo -n` in an internal collection mode. If this shape is rejected in Chunk 0, dispatcher and collector must be separate root-owned programs; no shell parser may be introduced.

Collector behavior:

- diagnostic kind is an exact enum: `metadata`, `nova`, or `neutron`;
- time window is an exact enum, mapped internally to fixed `journalctl --since` values;
- service units, log roots, port checks, and match terms are code-owned fixed sets;
- file fallback uses fixed paths/globs and bounded tail reads, never a caller path;
- metadata evidence includes relevant Neutron metadata-agent and Apache/Nova metadata logs, fixed error terms, and listener evidence restricted to port `8775`;
- Nova evidence includes role-applicable fixed Nova units and `/var/log/nova/*.log`;
- Neutron evidence includes role-applicable fixed Neutron units and `/var/log/neutron/*.log`;
- output is structured JSON or clearly sectioned JSON-compatible data;
- every source section reports `ok`, `partial`, `unavailable`, or `error`;
- missing files/units are evidence states, not reasons to broaden access;
- secret-like key/value content is redacted before output;
- per-section lines and total bytes are bounded before SSH returns data.

A successfully evaluated request with missing evidence may exit `0` and report `partial` or `unavailable` inside the host payload, preserving the existing runner envelope contract. Transport, forced-command validation, sudo denial, malformed output, or collector execution failures return non-zero.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `docs/ai-ops/implementation-plan/06-restricted-host-diagnostics.md` requires restricted observer SSH, reviewed read-only sudo commands, bounded metadata/Nova/Neutron tools, host/time validation, audit, denial tests, and metadata workflow validation.
- `docs/ai-ops/implementation-plan/00-implementation-overview.md` classifies host diagnostics as stricter than API diagnostics and prohibits generic SSH, sudo, shell, restart, file mutation, database access, and remediation.
- `docs/ai-ops/prd.md` FR-015 through FR-031 require bounded read-only log diagnostics through the existing allowlist, argv execution, limits, result envelopes, and audit. AC-008 and AC-010 preserve bounded logs and prohibit generic host-control capability.
- `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py` uses `subprocess.run(argv, shell=False)`, applies per-tool timeout/output limits, emits stable envelopes, and audits all terminal states.
- The same runner advertises `allowed_host_list` and `bounded_time_window` via the registry but currently falls through to `ValueError` for those types.
- `tests/ai_ops/test_tool_runner.py` uses Python stdlib `unittest` and temporary registries/scripts to verify denial, validation, argv execution, timeout, truncation, audit, and secret-like argument sanitization.
- `ansible/ai_ops_runtime/inventories/local/local.yml` currently contains only `assistant01`; it does not yet expose host-diagnostic target groups.
- `ansible/deploy_openstack/inventories/local/local.yml` defines `controller01`, `compute01`, `compute02`, and `storage01` by current role names.
- `inventories/local/nodes.yml` defines those nodes plus optional `ceph01` and confirms `assistant01` is separate on the management network.
- `ansible/deploy_openstack/playbook_setup_controller.yml` installs `nova_controller` and `neutron_controller` on the controller; `playbook_setup_compute.yml` installs `nova_compute` and `neutron_compute` on compute nodes.
- `ansible/deploy_openstack/roles/nova_controller/files/metadata_api.conf` defines Nova metadata WSGI on `8775` and logs to `/var/log/apache2/nova_metadata_error.log` and `/var/log/apache2/nova_metadata_access.log`.
- `docs/troubleshooting/01-openstack-instance-metadata-503.md` records useful evidence from `neutron-metadata-agent`, `/var/log/neutron/neutron-metadata-agent.log`, Apache/Nova metadata listener `8775`, and connection/proxy error terms.
- `ansible/deploy_opensearch/roles/filebeat/templates/filebeat.yml.j2` confirms OpenStack logs under `/var/log/nova/*.log` and `/var/log/neutron/*.log`.
- `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/workspace.yml` creates the local `assistant` system user with `/usr/sbin/nologin`; Phase 06 connector execution must therefore be validated explicitly under the actual runtime identity.
- `scripts/check_ai_ops_diagnostic_safety.sh` intentionally rejects shell scripts containing any raw `ssh` or `sudo`. A Python fixed connector plus dedicated tests is preferred over weakening that existing guardrail.
- Current branch during ADS creation is `ai-ops/06-restricted-host-diagnostics`, and the working tree was clean before this document was created.

#### Assumptions

- The initial host slice should provision only `controller01`, `compute01`, and `compute02`; storage and Ceph remain opt-in extensions with no public tool in this phase.
- Exact windows `15m`, `30m`, and `1h`, with `15m` default, are safe initial values but require Chunk 0 confirmation.
- A Python stdlib collector/connector is acceptable and preferable because it preserves argv execution and supports focused unit tests without adding packages.
- The existing trusted Ansible control path can generate/distribute the observer public key and collect host public keys for a dedicated pinned `known_hosts` file.
- Provisioning mutations are operator-run Ansible administration, not AI-facing diagnostic operations. Runtime tools remain read-only.
- Runtime evidence and audit logs stay outside Git; only sanitized summaries are committed.

#### Open confirmations for Chunk 0

- Confirm the accepted time-window set and output/line limits.
- Confirm whether controller-only metadata evidence is sufficient for the first slice or compute metadata agents must also be included.
- Confirm the generated host-policy format and whether aliases resolve through policy mapping, DNS, or managed `/etc/hosts` entries.
- Confirm forced-command single-executable versus separate dispatcher/collector implementation.
- Confirm the exact sudoers command specification with `visudo -cf` on the target distribution.
- Confirm `assistant` can execute the connector despite its nologin shell when launched directly by the runner/Ansible.
- Confirm log formats and journal unit names on the deployed Gazpacho lab before finalizing filters.

### III. Required Technical Dependencies and Imports

#### Existing concrete dependencies

- `assistant01` and `/opt/openstack-ai-ops` runtime workspace.
- Python 3 and OpenSSH client already listed by `assistant_runtime` defaults.
- Existing runner, registry, audit JSONL path, result envelope, and `unittest` test seam.
- Existing Ansible inventories and `inventories/local/nodes.yml` role/address variables.
- OpenStack host `systemd-journald`, service logs, and Apache metadata logs where installed.

#### Proposed Python standard-library imports

- `argparse`, `json`, `os`, `re`, `shlex`, `subprocess`, `sys`;
- `collections.deque` for bounded file tails;
- `datetime`/`time` for timestamps and durations;
- `pathlib` for fixed path handling;
- `typing` for explicit contracts.

`shlex` may tokenize only `SSH_ORIGINAL_COMMAND`; resulting tokens must match an exact grammar and must never be passed to a shell.

#### Proposed configuration and runtime artifacts

All paths below are conceptual until Chunk 0 confirms them:

- observer role: `ansible/ai_ops_runtime/roles/host_observer/`;
- observer setup: `ansible/ai_ops_runtime/playbook_setup_phase06_host_observer.yml`;
- collector: `/usr/local/sbin/aiops-host-diagnostic`, root-owned `0755`;
- sudoers policy: `/etc/sudoers.d/aiops-host-observer`, root-owned `0440`;
- private key: `/opt/openstack-ai-ops/credentials/ssh/observer_ed25519`, `assistant:assistant`, `0600`;
- pinned host keys: `/opt/openstack-ai-ops/credentials/ssh/known_hosts`, `assistant:assistant`, `0600`;
- assistant connector and host policy: `/opt/openstack-ai-ops/scripts/host_diagnostics/`;
- runtime runbook: `docs/ai-ops/runtime/restricted-host-diagnostics.md`;
- runtime validation: `ansible/ai_ops_runtime/playbook_validate_phase06_restricted_host_diagnostics.yml`.

No new pip package, MCP server, remote API, root SSH key, admin OpenStack credential, database credential, service credential, or remediation dependency is required.

### IV. Step-by-Step Procedure / Execution Flow

1. Confirm the target matrix, exact windows, service units, log paths, line limits, byte limits, and SSH host-key source.
2. Extend runner validation fail-closed.
   - Implement exact `allowed_host_list` and `bounded_time_window` semantics.
   - Add reviewed fixed argv support only if needed for diagnostic kind selection.
   - Test unknown hosts, unsafe durations, metacharacters, malformed registry values, and caller attempts to override fixed arguments.
3. Add and unit-test the host collector contract.
   - Reject interactive/empty/or malformed forced commands.
   - Map kind/window to fixed units, paths, terms, and argv.
   - Bound and redact output before emission.
   - Represent missing evidence as section status.
4. Provision the observer boundary through Ansible.
   - Generate a dedicated keypair on `assistant01` without exposing the private key.
   - Create a locked, unprivileged observer account on selected nodes.
   - Install the root-owned collector and forced-command authorized key.
   - Install one narrow sudoers entry and validate it with `visudo` before activation.
   - Pin selected host keys for the connector.
5. Prove negative access before enabling tools.
   - Interactive SSH, TTY, forwarding, arbitrary commands, shells, direct `sudo`, `sudo -l` breadth, service restart, file mutation, and config reads must fail.
   - The three approved collector forms must succeed where role-applicable.
6. Add the assistant connector.
   - Resolve only reviewed aliases.
   - Use the dedicated identity and pinned host keys.
   - Execute fixed SSH argv with no shell and no caller-selected remote command.
7. Register host tools initially unavailable.
   - Add high-risk entries with exact hosts/windows, limits, fixed diagnostic kinds, and explicit unavailable reason.
   - Deploy the connector/policy via the existing assistant role.
8. Enable each tool only after its observer path and denial tests pass.
   - Metadata first on `controller01`.
   - Nova next on controller and compute nodes.
   - Neutron next on controller and compute nodes.
9. Validate through the local runner.
   - Confirm envelope fields, host/window argument preservation, output bounds, payload redaction, timeout behavior, and audit events.
   - Confirm rejected host/window/metacharacter requests are audited and no SSH process starts.
10. Run the metadata incident workflow.
    - Use the existing project/server/network tools first.
    - Add `recent_metadata_errors` on the approved controller.
    - Distinguish listener failure, Neutron metadata proxy error, source unavailable, and no matching evidence.
    - Confirm no remediation path exists.
11. Commit only sanitized evidence, then update Phase 06 checkboxes for behavior actually proven.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
|---|---|---|---|
| Registry load | Host list, time list, or fixed arguments are absent/malformed | Fail closed before execution and audit the validation failure | `validation_error`; no connector process |
| Request validation | Host is syntactically safe but not explicitly allowlisted | Reject exact value; do not resolve or connect | `validation_error`; audited host argument |
| Request validation | Window is unsupported or contains metacharacters | Reject exact value | `validation_error`; no SSH |
| Tool availability | Observer boundary is not validated | Keep registry entry unavailable | `unavailable`; audited reason |
| Host policy | Alias is missing or maps to an unexpected role/tool | Connector rejects the request | Non-zero connector result; runner `error` |
| SSH identity | Private key missing, unreadable, or wrong mode | Fail without fallback identity | Runner `error`; no alternate credentials |
| Host identity | Pinned host key mismatches | Strict host-key verification aborts | Runner `error`; operator investigates rotation/MITM |
| SSH boundary | Interactive login or arbitrary command requested | Forced command rejects it | Access denied; denial evidence recorded by validation |
| Sudo boundary | Collector command does not match reviewed rule | `sudo -n` fails; no password prompt | Runner `error`; no broader sudo fallback |
| Collector validation | Kind/window is malformed after transport | Reject before journal/file access | Structured collector validation error |
| Service placement | Unit or log does not exist on selected role | Emit `unavailable` section; do not search arbitrary paths | Valid bounded payload with evidence gap |
| Log read | Permission/read error occurs | Emit bounded `error` section and continue other fixed sources | `partial` payload |
| Log content | Secret-like assignment/header appears | Redact value before buffering/output | Redacted payload; redaction count/marker |
| Output volume | Section or total exceeds limits | Stop collection/truncate deterministically and mark it | Payload and/or runner `truncated=true` |
| Timeout | SSH or collector exceeds runner timeout | Runner terminates connector | `timeout`, `exit_code: null`, audited |
| Audit write | Audit event cannot be written | Existing runner converts outcome to error | `error`; diagnostic not represented as successful |
| Runtime validation | Approved diagnostics work but denial tests fail | Keep tools unavailable and stop phase | Blocking security failure |
| Metadata workflow | No host evidence matches | Report `no matching evidence` rather than healthy service | Manual follow-up; no remediation |

### VI. Security, Integrity, Idempotency, and Cleanup

- **Security:** The observer key is dedicated, non-root, restricted by key options, pinned host keys, and one forced command. The sudo rule names one root-owned collector and never grants `ALL` or generic binaries.
- **Defense in depth:** Runner allowlists, exact values, connector policy, forced-command parsing, sudoers, collector enums, fixed source maps, output bounds, and audit each enforce the boundary independently.
- **No shell construction:** Runner, connector, dispatcher, and collector use argv execution only. No `shell=True`, `os.system`, `eval`, user-controlled glob, command substitution, or string-interpolated remote command is permitted.
- **No host control:** Runtime diagnostics cannot restart/reload/start/stop services, edit files, install packages, open databases, inspect arbitrary configs, forward ports, allocate a TTY, or execute arbitrary programs.
- **Credential integrity:** Private keys are never committed, logged, returned, embedded in evidence, or copied to target hosts. Public keys and fingerprints may be recorded only where operationally necessary.
- **Host integrity:** The collector is root-owned and not writable by `aiops-observer`. Sudoers and authorized-key files are root-owned with restrictive modes.
- **Output integrity:** Each payload identifies requested alias, observed hostname/role where safe, diagnostic kind, requested window, source statuses, truncation, and timestamp so evidence cannot silently mix hosts or windows.
- **Redaction:** Redact values associated with password, token, secret, credential, authorization, API key, private key, and metadata proxy shared-secret patterns. Do not read full configuration files.
- **Idempotency:** Ansible user, directory, key, collector, authorized-key, sudoers, host-policy, and known-host tasks must converge without rotating keys or duplicating entries unless explicit rotation is requested.
- **Cleanup/rollback:** Set host tools unavailable, remove observer authorized keys and sudoers entries, remove the observer account/collector from selected nodes, remove the dedicated private key/known-hosts/policy from `assistant01`, and retain sanitized audit/evidence according to operator policy.
- **Opt-in:** Adding a new host, service, path, unit, time window, or tool requires registry, host policy, collector map, tests, and runtime denial validation; inventory presence alone does not grant access.

### VII. Validation Strategy

#### Static and Unit Validation

Use a temporary virtual environment for Python validation if the chunk modifies Python:

```bash
rtk python3 -m venv /tmp/openstack-lab-phase06-venv
. /tmp/openstack-lab-phase06-venv/bin/activate
rtk python -m py_compile \
  ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py \
  ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/host_diagnostics/aiops_host_diagnostic_connector.py \
  ansible/ai_ops_runtime/roles/host_observer/files/aiops_host_diagnostic.py \
  tests/ai_ops/test_tool_runner.py \
  tests/ai_ops/test_host_diagnostics.py
rtk python -m unittest discover -s tests -p 'test_tool_runner.py'
rtk python -m unittest discover -s tests -p 'test_host_diagnostics.py'
```

Registry and symbol checks:

```bash
rtk python3 -m json.tool ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/tool_registry.json >/dev/null
rtk grep -Rni "allowed_host_list\|bounded_time_window\|fixed_arguments" \
  ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner tests/ai_ops
rtk grep -Rni "recent_metadata_errors\|recent_nova_errors\|recent_neutron_errors" \
  ansible/ai_ops_runtime docs/ai-ops/runtime tests/ai_ops
```

Safety review:

```bash
rtk grep -RniE "shell=True|os\.system|eval\(|exec\(|StrictHostKeyChecking=no|NOPASSWD:[[:space:]]*ALL|ALL[[:space:]]*=.*ALL" \
  ansible/ai_ops_runtime/roles/host_observer \
  ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/host_diagnostics \
  ansible/ai_ops_runtime/playbook_setup_phase06_host_observer.yml
rtk scripts/check_ai_ops_diagnostic_safety.sh
```

The safety grep requires manual review of any match; absence is not proof of safety.

#### Ansible Validation

```bash
rtk ansible-playbook --syntax-check \
  -i ansible/ai_ops_runtime/inventories/local/local.yml \
  ansible/ai_ops_runtime/playbook_setup_phase06_host_observer.yml
rtk ansible-playbook --syntax-check \
  -i ansible/ai_ops_runtime/inventories/local/local.yml \
  ansible/ai_ops_runtime/playbook_validate_phase06_restricted_host_diagnostics.yml
```

The provisioning playbook must validate candidate sudoers content with `visudo -cf` before installing it. Runtime validation must verify owner/mode, forced-command authorized-key options, private-key mode, and pinned host entries without printing key material.

#### Negative Runtime Validation

From `assistant01`, prove all of the following fail:

- interactive observer SSH and TTY allocation;
- port, agent, X11, and tunnel forwarding;
- empty or arbitrary remote command;
- `sh`, `bash`, editor, package manager, database client, raw `journalctl`, arbitrary `cat`/`tail`, config read, and service-control requests;
- unrestricted `sudo`, password escalation, and any sudo command other than the collector;
- runner calls with unknown hosts, IP substitutions, unsupported windows, unknown arguments, and shell metacharacters.

Then prove approved metadata/Nova/Neutron calls work only for their role-appropriate hosts and exact windows, produce bounded/redacted payloads, and generate one audit event per request.

#### Metadata Workflow Smoke Check

Run existing project/server tools plus `recent_metadata_errors` against `controller01`. Confirm the combined evidence can distinguish:

- Nova metadata listener `8775` unavailable;
- Neutron metadata-agent proxy/connectivity errors;
- source/log/unit unavailable;
- no matching recent evidence.

No restart, edit, repair, or remediation command may exist in the registry or connector.

#### Final Review

```bash
rtk git status --short
rtk git diff --stat
rtk git diff -- \
  docs/ai-ops/implementation-plan/06-restricted-host-diagnostics.md \
  docs/ai-ops/implementation-plan/ads/06-restricted-host-diagnostics-ads.md \
  docs/ai-ops/runtime \
  ansible/ai_ops_runtime \
  tests/ai_ops
```

Review for private keys, tokens, passwords, shared secrets, raw audit logs, overly broad hosts/commands, disabled host-key checking, mutation commands, and unrelated refactors.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass. Every chunk must run post-edit verification, review its scoped diff, record risk, and create a handoff when another chunk remains.

#### Chunk 0: Discovery and Integration Confirmation

- **Goal:** Resolve all open security and runtime contracts before editing.
- **Files to read:**
  - `docs/ai-ops/implementation-plan/06-restricted-host-diagnostics.md`
  - `docs/ai-ops/prd.md`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/tool_registry.json`
  - `ansible/ai_ops_runtime/inventories/local/local.yml`
  - `ansible/deploy_openstack/inventories/local/local.yml`
  - relevant deployed service/log evidence on selected nodes
- **Commands:**
  - `rtk git status --short --branch`
  - `rtk git grep -n -E "allowed_host_list|bounded_time_window|metadata-agent|nova_metadata_error|8775" -- ansible docs tests`
  - read-only Ansible facts/commands needed to confirm units, files, modes, host keys, and runtime identity behavior
- **Evidence to confirm:** exact host matrix, windows, units, paths, limits, key lifecycle, alias resolution, forced-command design, sudoers syntax, and connector execution identity.
- **Stop condition:** no edits; decisions and blockers are written in the Chunk 0 handoff.

#### Chunk 1: Runner Contracts and Fail-Closed Stubs

- **Goal:** Introduce explicit contracts for host/time validators and fixed registry arguments without enabling any host tool.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py`
  - `tests/ai_ops/test_tool_runner.py`
- **Symbols to add/change:** conceptual validator helpers and fixed-argument validation seam; focused tests.
- **Implementation shape:** Add minimal helpers that initially raise clear `ValueError` for unimplemented or malformed host-specific contracts. Keep existing tools/tests unchanged and host tools absent.
- **Validation:** Python compile, existing `test_tool_runner.py`, new fail-closed tests, and scoped diff review.
- **Stop condition:** existing runner is green; unsupported host contracts cannot return success; no SSH or host tool is reachable.

#### Chunk 2: Exact Host/Window Validation and Fixed Argv

- **Goal:** Implement and test exact list validation plus registry-controlled diagnostic-kind argv.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py`
  - `tests/ai_ops/test_tool_runner.py`
- **Symbols to add/change:** `validate_argument_value`, conceptual host/window helpers, `build_command_argv`, registry validation tests.
- **Implementation shape:** Accept only string lists of exact values, reject empty/duplicate/malformed values, validate defaults, prepend only reviewed fixed arguments, and reject caller overrides. Do not register host tools yet.
- **Validation:** targeted unit tests for valid hosts/windows, unknown safe hosts, metacharacters, malformed registry lists, fixed-argument order, and argv-only execution.
- **Stop condition:** runner boundary is fully tested but still has no Phase 06 registry entries.

#### Chunk 3: Bounded Host Collector

- **Goal:** Add one root-owned collector implementation with no provisioning or caller wiring.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/host_observer/files/aiops_host_diagnostic.py` (proposed new file)
  - `tests/ai_ops/test_host_diagnostics.py` (proposed new file)
- **Symbols to add/change:** forced-command parser, kind/window validator, fixed source maps, journal argv builder, bounded file reader, redactor, payload bounder, CLI entrypoint.
- **Implementation shape:** Use dependency-injected or temporary fixtures for unit tests; initial real source maps are role-aware fixed constants. Missing sources become structured statuses. No Ansible role calls the collector yet.
- **Validation:** Python compile; focused collector tests for grammar rejection, fixed argv, bounds, redaction, unavailable sections, and no shell use.
- **Stop condition:** collector behavior is locally testable and fail-closed but not installed anywhere.

#### Chunk 4: Observer Provisioning Vertical Slice

- **Goal:** Provision the dedicated key, selected observer accounts, forced command, root-owned collector, sudoers rule, and pinned host keys as one reviewable infrastructure boundary.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/host_observer/defaults/main.yml` (proposed)
  - `ansible/ai_ops_runtime/roles/host_observer/tasks/main.yml` (proposed)
  - `ansible/ai_ops_runtime/inventories/local/local.yml`
  - `ansible/ai_ops_runtime/playbook_setup_phase06_host_observer.yml` (proposed)
- **Symbols to add/change:** observer variables, exact target group, idempotent user/key/file/sudoers tasks, assistant key/known-host tasks, playbook wiring.
- **Implementation shape:** Four files are justified because inventory selection, role defaults, role tasks, and executable playbook are independently reviewable parts of one deployable access slice. Validate sudoers before installation and keep tools unavailable.
- **Validation:** Ansible syntax check, `--check` where safe, targeted deployment, second-run idempotency, owner/mode checks, and negative SSH/sudo tests.
- **Stop condition:** approved collector forms work manually through the forced command; every generic access/escalation attempt fails; registry remains unchanged.

#### Chunk 5: Fixed Assistant Connector

- **Goal:** Add a locally testable connector that can reach only policy-mapped observer targets.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/host_diagnostics/aiops_host_diagnostic_connector.py` (proposed)
  - `tests/ai_ops/test_host_diagnostics.py`
- **Symbols to add/change:** policy loader, request revalidation, SSH argv builder, subprocess wrapper, CLI entrypoint, connector tests.
- **Implementation shape:** Start with an explicit temporary error if policy/key/known-host inputs are absent. Then implement strict argv construction and mocked subprocess tests. Do not deploy or register it yet.
- **Validation:** Python compile; connector tests for alias mismatch, kind/window mismatch, exact SSH options, no shell, timeout/error propagation, and no fallback key.
- **Stop condition:** connector contract is green locally and cannot construct caller-selected remote commands.

#### Chunk 6: Deploy and Register One Metadata Tool

- **Goal:** Complete the first end-to-end thin slice for `recent_metadata_errors` on `controller01` only.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/tasks/scripts.yml`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/tool_registry.json`
  - proposed host-policy template/file under the assistant role
- **Symbols to add/change:** connector/policy installation tasks and one high-risk registry entry.
- **Implementation shape:** Three files are required to connect implementation, deployment, and reviewed policy. Register metadata as unavailable first, deploy, run denial checks, then set `available: true` only after the observer boundary passes. Nova/Neutron remain absent.
- **Validation:** JSON syntax, Ansible syntax, runner unit regression, runtime valid/invalid metadata calls, output/redaction bounds, and audit correlation.
- **Stop condition:** one metadata host diagnostic works through the runner; unknown hosts/windows/commands fail and audit; no Nova/Neutron tool exists yet.

#### Chunk 7: Nova and Neutron Tool Slices

- **Goal:** Extend the proven connector/collector path to role-aware Nova and Neutron evidence.
- **Files to change:**
  - `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/tool_registry.json`
  - `tests/ai_ops/test_host_diagnostics.py`
- **Symbols to add/change:** two high-risk registry entries and role/host matrix regression tests; collector source maps only if Chunk 0 evidence requires corrections.
- **Implementation shape:** Add one tool at a time in the same chunk session: Nova tests/validation first, then Neutron. If collector changes are required, stop and split them into a separate corrective chunk rather than exceeding scope.
- **Validation:** JSON syntax, Python tests, per-role allowed/denied matrix, unavailable-source behavior, output limits, redaction, and audit events.
- **Stop condition:** all three host tools work only on approved role hosts and exact windows; no host-control primitive exists.

#### Chunk 8: Runtime Validation, Runbook, Evidence, and Phase Status

- **Goal:** Prove the complete phase and record sanitized operational guidance/evidence before checking Phase 06 complete.
- **Files to change:**
  - `ansible/ai_ops_runtime/playbook_validate_phase06_restricted_host_diagnostics.yml` (proposed)
  - `docs/ai-ops/runtime/restricted-host-diagnostics.md` (proposed)
  - `docs/ai-ops/runtime/phase06-restricted-host-diagnostics-evidence-<date>.md` (after successful runtime execution)
  - `docs/ai-ops/implementation-plan/06-restricted-host-diagnostics.md` (validated checkboxes only)
- **Symbols to add/change:** validation tasks, operator boundary/rollback guidance, sanitized evidence, accurate checklist state.
- **Implementation shape:** Implement playbook and runbook first; syntax-check and run validation; create evidence and update status only after success. Four files are justified because executable validation, operator guidance, immutable evidence, and plan status have distinct responsibilities.
- **Validation:** Ansible syntax and runtime checks, complete positive/negative matrix, metadata incident workflow, secret scan, final scoped diff, and manual security review.
- **Stop condition:** Phase 06 definition of done has sanitized proof; failures remain unchecked and documented; Phase 07 MCP work has not started.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.
Activate rtk-command-prefix for shell commands.

Task:
Implement Phase 06 Restricted Host Diagnostics from docs/ai-ops/implementation-plan/06-restricted-host-diagnostics.md using docs/ai-ops/implementation-plan/ads/06-restricted-host-diagnostics-ads.md.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm the host matrix, windows, service/log paths, SSH key lifecycle, forced-command design, sudoers command, alias resolution, and runtime identity behavior. Write a handoff and stop.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Use the Phase 06 ADS and latest handoff.
Execute Chunk 1 only.
Do not continue to Chunk 2.
After editing, run targeted validation, review git diff, assess risk, write the Chunk 1-to-2 handoff, and stop.
```

For subsequent chunks:

```text
Use the chunked-implementation skill.
Resume from the latest Phase 06 handoff.
Execute exactly the next approved chunk only.
Do not implement later tools or enable unavailable registry entries early.
Run the chunk-specific validation, review the scoped diff, assess security risk, write the next handoff, and stop.
```

### X. Conclusion and Next Steps

Phase 06 should add host evidence as a narrow extension of the existing safety gateway, not as a new command surface. The preferred design combines exact runner validation, a fixed Python SSH connector, forced-command key restrictions, one root-owned collector, one narrow sudo rule, role-aware source maps, bounded/redacted output, strict host-key verification, and existing envelope/audit behavior.

The immediate next step is Chunk 0 only. Implementation must not begin until the proposed windows, target matrix, key/known-host lifecycle, forced-command parsing, sudoers syntax, deployed service/log names, and `assistant` runtime execution behavior are confirmed in the actual lab.
