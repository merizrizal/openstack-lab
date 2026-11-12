## Architectural Design Specification: MCP Deployment, Activation, and Live-Validation Foundation

**Source:** `docs/ai-ops-revised/implementation-plan/07-x01-mcp-deployment-activation-and-live-validation.md`, Steps 1–5

**Goal:** Close the non-live implementation gap between the accepted Phase 07 static/fixture MCP artifacts and separately authorized operations on `assistant02`: freeze authority and evidence contracts, accept reproducible offline SDK closures, add guarded local-stdio deployment and smoke-test seams, complete the fixture-testable Option B application startup path, and separate disabled deployment from activation, validation, disablement, and rollback automation.

---

### I. Overview and Contract

This ADS covers implementation-plan Steps 1–5 only. It prepares the repository for the later local/static acceptance in Step 6 and for separately authorized operational Steps 7–10. It does not itself authorize package acquisition, protected artifact handling, host contact, process or listener startup, firewall mutation, live runner/OpenStack calls, audit inspection, disablement, or rollback.

The implementation preserves two independent modes:

```text
approved owner decisions and dependency closure
  -> local-stdio dedicated environment and artifacts
  -> bounded client-owned smoke harness
  -> Option B fixture-testable authenticated application
  -> disabled Option B environment, artifacts, TLS metadata, and unit
  -> current-run preflight
  -> separate activation / validation / disablement / rollback entrypoints
```

#### Mode boundary

| Concern | Local stdio baseline | Authenticated internal-network Option B |
| --- | --- | --- |
| Lifecycle owner | Owner-managed client | systemd |
| Runtime root | `/opt/openstack-ai-ops-assistant/mcp-stdio` | `/opt/openstack-ai-ops-assistant/mcp` |
| Transport | Process stdin/stdout only | Streamable HTTP over TLS 1.3 |
| Listener | Forbidden | Exactly `192.168.121.21:8443` after separate activation |
| MCP surface | Three tools, six resources, three prompts | Target: three tools, six resources, no prompts; current source has three resources |
| Principal | No client identity forwarded | Exact URI SAN maps to `mcp-internal-reader` |
| Audit authority | Existing runner only | Existing runner only |
| Deployment effect | Artifacts and dedicated venv; no service | Artifacts, dedicated venv, TLS inputs, and disabled unit |
| Activation | Client-owned bounded process | Separate approval-bearing operation |

Local stdio already has a six-entry accepted catalog. The extension plan also requires six Option B resources, but current Option B source/catalog contains three. Chunk 0 must confirm whether Option B adopts the same six reviewed resources or another exact six-entry set; implementation must not guess the missing entries. Option B must not gain prompts through this extension.

#### Authority and state-transition contract

Repository defaults remain false. Ordinary deployment must never imply activation.

```text
UNREADY
  -- approved decisions + complete offline closure --> READY_FOR_DISABLED_DEPLOYMENT
  -- local artifact deployment --------------------> LOCAL_DEPLOYED_NO_PROCESS
  -- bounded client-owned launch ------------------> LOCAL_SMOKE_ACTIVE
  -- client closes stdin / cleanup ----------------> LOCAL_DEPLOYED_NO_PROCESS
  -- Option B disabled deployment -----------------> OPTION_B_DEPLOYED_DISABLED
  -- current-run preflight + separate approval ----> OPTION_B_ACTIVATION_READY
  -- separate activation entrypoint ---------------> OPTION_B_ACTIVE
  -- separate disablement -------------------------> OPTION_B_DEPLOYED_DISABLED
  -- separately authorized exact rollback --------> OPTION_B_ABSENT
```

Any missing, stale, unsafe, unexpected, symlinked, incorrectly owned, hash-mismatched, or unauthorized prerequisite keeps the operation at its prior non-active state. A failed preflight cannot be reused as activation evidence for a later run.

#### Existing concrete Python contracts

**Function Signature Contract (Concrete):** observed in the local-stdio adapter.

```python
async def run_server(
    configuration: AdapterConfiguration,
    lifecycle: ChildProcessRegistry | None = None,
    *,
    fixed_registry_path: Path = REGISTRY_PATH,
) -> None
```

The smoke harness must launch the deployed adapter executable rather than import this function as an alternate execution path. The contract is relevant because EOF, cancellation, and final cleanup already converge through `ChildProcessRegistry.cleanup()`.

**Function Signature Contract (Concrete):** observed in the local-stdio adapter.

```python
def main(configuration_path: Path = CONFIG_PATH) -> int
```

The deployed process reserves stdout for MCP protocol frames and emits only bounded error classes on stderr.

**Function Signature Contract (Concrete):** observed in the Option B adapter.

```python
def create_application(
    config: NetworkMCPConfig,
    *,
    enabled: bool = DEFAULT_ENABLED,
    explicit_activation: bool = DEFAULT_EXPLICIT_ACTIVATION,
) -> NetworkMCPApplication
```

The current implementation validates both booleans and then still raises `NetworkMCPDisabledError("network MCP authentication is not activated")`. Step 4 replaces only that unconditional final rejection after all startup/authentication prerequisites can be injected and fixture-tested.

**Function Signature Contract (Concrete):** observed in the Option B adapter.

```python
def build_tls_context(config: NetworkMCPConfig) -> ssl.SSLContext
def build_uvicorn_config(
    application: Starlette,
    config: NetworkMCPConfig,
    tls_context: ssl.SSLContext,
) -> uvicorn.Config
def main(arguments: Sequence[str] | None = None) -> int
```

`main()` currently validates configuration and exits without constructing or running Uvicorn. Its eventual active path must construct the accepted application, verify bind ownership and activation evidence, run one Uvicorn worker, and preserve deterministic non-zero exits for disabled or rejected startup.

#### Proposed contracts requiring Chunk 0 confirmation

**Function Signature Contract (Conceptual):** offline closure validation.

```text
validate_offline_dependency_closure(lock_path, wheel_directory, expected_python_abi)
  -> normalized closure result or fail-closed dependency error
```

Inputs are fixed operator-controlled paths, not request data. Success means every exact hash-pinned lock requirement resolves from the approved offline set with no missing or extra wheel and no network fallback. The temporary implementation must return an explicit failure until owner-approved lock and wheel inputs exist; it must never report success for an absent closure.

**Function Signature Contract (Conceptual):** local smoke orchestration.

```text
run_local_stdio_smoke(adapter_argv, normalized_case_set, deadline)
  -> normalized outcomes only
```

The harness owns one child, communicates only through MCP stdin/stdout, closes stdin, reaps the adapter and any runner child, and retains no raw result, identifier, credential, audit, or protected payload. Exact language, path, and test interface are Chunk 0/Chunk 3 decisions.

**Function Signature Contract (Conceptual):** activation evidence loading.

```text
load_current_activation_evidence(fixed_root_controlled_path)
  -> validated non-secret approval/preflight state or fail-closed activation error
```

The exact artifact path, schema, ownership, mode, freshness, one-run binding, and deletion behavior are deliberately unresolved in the extension plan. Returning success without a current artifact would incorrectly authorize activation, so the initial stub must raise a clear activation-disabled error.

**Function Signature Contract (Conceptual):** Option B request authentication seam.

```text
extract_authenticated_principal(validated_tls_scope)
  -> "mcp-internal-reader" or authentication/authorization denial
```

It may trust only TLS state established by the server process, never headers or request-body identity. The exact Starlette/Uvicorn TLS-scope integration must be confirmed against MCP SDK `1.28.1` before coding.

#### Automation contract

`playbook_deploy_mcp_stdio.yml` and `playbook_deploy_mcp.yml` remain deployment-only and default-disabled. Proposed separate entrypoints are:

- `playbook_preflight_mcp.yml` (proposed);
- `playbook_activate_mcp.yml` (proposed);
- `playbook_validate_mcp.yml` (proposed);
- `playbook_disable_mcp.yml` (proposed); and
- `playbook_rollback_mcp.yml` (proposed).

Names are conceptual until Chunk 0 confirms repository naming and ownership. Each entrypoint must target only `ai_ops_assistant`/`assistant02`, require `--limit assistant02`, expose check mode where safe, and perform exactly one lifecycle purpose. Deployment cannot include or trigger activation tasks.

### II. Observed Evidence and Assumptions

#### Observed evidence

- `07-x01-mcp-deployment-activation-and-live-validation.md` explicitly orders local stdio before Option B and separates deployment, activation, validation, disablement, and rollback.
- `ansible/ai_ops_assistant/inventories/local/local.yml` contains `assistant02` under `ai_ops_assistant`; it does not freeze a Python interpreter or ABI.
- `playbook_deploy_mcp_stdio.yml` and `playbook_deploy_mcp.yml` assert `assistant02`, `ai_ops_assistant`, and exact `ansible_limit == 'assistant02'`, then pass false enablement/activation variables.
- Both MCP role defaults pin `mcp==1.28.1` and identify an external approved offline artifact as the dependency source.
- Both expected `requirements.lock` files are absent. The local-stdio static test treats this absence as a deployment blocker rather than fabricating a lock.
- The local-stdio role currently copies source/configuration/`requirements.in` and the required lock when enabled; it does not create or validate the dedicated venv.
- The Option B role currently copies adapter/catalog/configuration, installs a hardened unit, and enforces stopped/disabled state; it does not create the venv or materialize TLS files.
- The Option B unit already uses fixed interpreter/adapter paths, one service identity, minimal environment, `TimeoutStopSec=10s`, `KillMode=mixed`, and the reviewed hardening directives.
- `aiops_assistant_mcp_server.py` already contains fixed configuration validation, TLS-context construction, principal checks, request/response limits, runner invocation/result mapping, low-level server factories, a session-manager factory, and a `NetworkMCPApplication` container.
- `create_application()` still rejects activation after both booleans are true; `main()` does not construct or run a listener.
- Existing `tests/mcp/` fixtures validate configuration, default-disabled startup, three-tool/resource exposure, exact runner argv, result equivalence, limits, sanitized lifecycle events, and hardening without a listener.
- The local-stdio catalog contains six resource URIs. The Option B catalog and `REVIEWED_RESOURCE_METADATA` contain three, while extension-plan Step 4 requires a six-resource Option B allowlist; the exact target set needs reconciliation before implementation.
- Existing `tests/mcp_stdio/` fixtures validate protocol-only lifecycle, tool/resource/prompt behavior, cancellation cleanup, safety integration, and default-disabled artifact deployment.
- No MCP activation, validation, disablement, or rollback playbooks exist at the observed paths.
- The firewall marker exists only in the MCP defaults/tasks and documentation found during discovery; no repository owning automation for that marker was found in the bounded search.
- `mcp-interface-internal-network-operations-contract.md` states Python 3.14 for its future lock, while the extension plan requires recording the actual approved `assistant02` interpreter/ABI before lock generation. This is an unresolved confirmation, not deployed evidence.

#### Assumptions

- The extension plan is authoritative where it strengthens prior non-activation contracts, but it does not silently resolve the Python ABI or activation-control details.
- Approved wheel artifacts remain outside Git unless the repository owner explicitly defines a reviewed artifact-storage mechanism. The ADS does not assume wheels should be committed.
- A complete lock may be committed only after provenance, license, transitive closure, ABI compatibility, and hashes are independently accepted.
- Existing MCP adapters remain the only protocol-to-runner implementations; smoke and lifecycle automation must not create a second runner path.
- Existing normalized-evidence automation can inform conventions, but MCP evidence fields, location, retention, and deletion remain a separate owner decision.
- The Vagrant/firewall owner must either provide an owning automation path or independently verified marker evidence. MCP lifecycle code must not invent ad hoc firewall commands.

#### Open confirmations for Chunk 0

1. Exact approved Python executable, version, ABI tag, platform tag, and wheel compatibility for `assistant02`.
2. Whether local stdio and Option B use identical approved closures or separately generated lock/wheel sets.
3. Approved lock-generation environment, internal index/offline source, provenance record, license review, and wheel-storage/transfer path.
4. Exact owners and current approval references for dependency handling, TLS/CRL, firewall, host access, test client, runner calls, normalized audit evidence, activation, disablement, and rollback.
5. Exact MCP normalized evidence schema, protected location, retention label, deletion owner, and raw-data prohibitions.
6. Exact stop authority and automatic rollback/disablement triggers.
7. Exact non-secret root-controlled activation artifact path, schema, mode, freshness, and current-run preflight binding.
8. Exact protected source and Ansible mechanism for TLS materialization, including `no_log` boundaries and cleanup.
9. Exact Vagrant-owned firewall automation path or accepted marker-evidence interface.
10. MCP SDK `1.28.1` Streamable HTTP request/lifespan signatures and the supported way to obtain authenticated client-certificate state without trusting headers.
11. Exact local smoke-client implementation/API and whether it belongs in a test/support path or a protected operator entrypoint.
12. Which accepted runner revision/hash and readiness evidence preflight must verify.
13. Whether Option B must adopt the local-stdio six-resource set or another owner-reviewed six-resource catalog, including exact URI order and content ownership.

Any unresolved item needed by a chunk is a stop condition for that chunk.

### III. Required Technical Dependencies and Imports

#### Existing runtime dependencies

- Official Python MCP SDK exactly `mcp==1.28.1`, no extras.
- Existing transitive MCP runtime packages, including the observed Starlette and Uvicorn imports for Option B; exact versions come only from the approved complete lock.
- Python standard-library facilities already used for `asyncio`, `contextlib`, `ssl`, `subprocess`, bounded process cleanup, JSON, paths, and timing.
- Existing fixed tool runner and registry under `ansible/ai_ops_assistant/roles/ai_ops_assistant_tool_runner/`.
- systemd on `assistant02` for Option B only.
- Externally managed server certificate/key, closed client CA bundle, current CRL, and bounded test-client identity for later operational steps.

#### Build/deployment dependencies

- An approved lock generator such as pip-tools with hash generation and stripped extras, run outside runtime deployment.
- An approved network-disabled installer capable of requiring hashes and resolving only the approved offline wheel set.
- Ansible modules already used by the roles (`assert`, `stat`, `file`, `copy`, `template`, and `systemd_service`). Additional modules must be justified and available in the project environment.
- `systemd-analyze verify` remains the service-unit validation contract on target deployment.
- Vagrant/firewall owner integration or accepted normalized marker evidence; no direct MCP-owned firewall command is assumed.

#### Forbidden dependencies and paths

- Public package-index access or runtime downloads.
- Historical orchestrator/provider/bridge dependencies or runtime paths.
- Generic shell, SSH, sudo, database, file-browser, package-control, service-control, remediation, or OpenStack passthrough packages.
- Caller-provided executable, environment, registry, profile, audit, timeout, output, credential, bind, TLS, or activation overrides.
- Client private keys on `assistant02`, in Git, ordinary evidence, chat, or automation output.

### IV. Step-by-Step Procedure / Execution Flow

#### Step 1 — freeze authority and evidence

1. Record each side effect, owner, approval reference, target, and expiration/current-run rule.
2. Freeze mode order: local stdio first; Option B only after runner equivalence is preserved.
3. Record the actual host Python version/ABI and reconcile prior Python 3.14 wording.
4. Freeze runtime paths, user/group, Option B bind/interface/port/CIDR/endpoint/principal, and accepted runner revision.
5. Define normalized evidence fields, protected location, retention, deletion, and `no_log` scope.
6. Define stop authority and disablement/rollback triggers.
7. Freeze a root-controlled, non-secret, default-absent activation artifact. Source constants and repository defaults remain false.
8. Publish the resulting operations contract before executable work.

#### Step 2 — close offline dependency supply chain

1. Generate complete per-ABI lock files from only the owner-approved source.
2. Reject unpinned, unhashed, editable, URL, VCS, extra, unexpected, or prohibited capability dependencies.
3. Verify package licenses, provenance, wheel hashes, tags, and complete transitive resolution.
4. Compare lock requirements and wheel inventory exactly; missing and extra artifacts both fail.
5. Prove installation into a temporary dedicated venv with network access disabled and hash enforcement enabled.
6. Verify installed distributions/versions against the accepted lock and confirm `mcp==1.28.1` API imports.
7. Define deterministic host venv creation/replacement: build a new candidate, validate it, atomically select it only when safe, and remove failed candidates.
8. Keep deployment disabled if any closure or ownership check fails.

#### Step 3 — guarded local-stdio deployment and smoke seam

1. Require explicit run-scoped deployment approval while preserving false role and playbook defaults.
2. Validate lock/wheel inputs before writing runtime state.
3. Materialize the dedicated venv, adapter, catalog, configuration, requirement, and lock with fixed ownership/modes and no symlinks.
4. Verify hashes and installed SDK/version/API without starting the adapter.
5. Launch one adapter as `aiops_assistant` through a non-registering client harness; reserve stdout for MCP.
6. Run the exact bounded discovery, prompt/resource, positive tool, invalid argument, negative capability, cancellation, timeout, and cleanup matrix.
7. Compare one local runner and MCP request using normalized fields only and verify one runner-owned audit event under separately approved evidence inspection.
8. Close stdin, reap all children, remove transient client inputs, and verify no adapter/listener remains.

Steps 7–8 above are later operational execution in plan Step 7. Steps 1–4 and fixture-safe harness construction are within this ADS; no live run is authorized here.

#### Step 4 — complete Option B startup path

1. Load and validate the fixed configuration, activation state, bind ownership, runner prerequisites, TLS metadata/material, and CRL before application construction.
2. Build TLS 1.3 `CERT_REQUIRED` context from fixed protected paths and closed trust/CRL sources.
3. After the resource decision is frozen, reconcile the current three-entry Option B catalog to the exact approved six-resource target and construct the three-tool/six-resource low-level server with no prompts.
4. Construct the stateful Streamable HTTP session manager and Starlette lifespan.
5. Mount exactly `/mcp`; admit only approved Host, absent Origin, methods, content type, source CIDR, and authenticated principal.
6. Enforce request, response, rate, burst, session, deadline, and one-runner-child limits before runner creation.
7. Build one-worker Uvicorn configuration on the exact address/port with no proxy-header trust.
8. On shutdown, stop admission, cancel sessions, terminate/reap runner children, exit within the systemd deadline, and emit only normalized lifecycle events.
9. Exercise application construction, request denial, accepted request, cancellation, and shutdown only through injected fixtures; do not open a real listener.

#### Step 5 — separate lifecycle automation

1. Keep both existing deployment playbooks unable to activate.
2. Add a current-run preflight that checks exact host/limit, runner revision/readiness, closure integrity, TLS metadata and CRL freshness, address ownership, absent port, firewall evidence, stopped/disabled service, and rollback readiness.
3. Materialize TLS inputs only from the approved protected source with `no_log` and metadata-only output.
4. Consume only owner-controlled Vagrant firewall automation or independently verified marker evidence.
5. Add a separate activation entrypoint requiring exact current approval, explicit confirmation, current-run preflight evidence, and `assistant02` scope.
6. Render activation state through the confirmed root-controlled non-secret artifact, then start/enable only `ai-ops-assistant-mcp`.
7. Add a separate validation entrypoint reporting only normalized process/unit/listener/policy outcomes.
8. Add a separate disablement entrypoint that removes access in the documented order and proves process/listener absence.
9. Add a separately authorized exact-artifact rollback entrypoint with path/ownership guards and shared-runtime preservation.
10. Add static tests proving operation separation, default-false behavior, target scope, check-mode safety, and rollback preservation.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| --- | --- | --- | --- |
| Decision freeze | Owner, approval, evidence, stop authority, or activation control is ambiguous | Do not generate operational artifacts or code around guessed values | `contract_blocked` (proposed); prior state preserved |
| ABI freeze | Actual host interpreter/ABI conflicts with prior Python 3.14 text | Stop lock generation and reconcile contract | `python_abi_mismatch` (proposed) |
| Lock validation | Missing, stale, duplicate, unhashed, unpinned, URL/VCS/editable, extra, or prohibited dependency | Reject closure; do not create/select venv | `dependency_closure_rejected` (proposed) |
| Offline resolution | A lock entry has no approved matching wheel, an extra wheel exists, or installer requests network | Abort and remove temporary candidate environment | `offline_artifact_mismatch` (proposed) |
| Venv creation | Partial creation, wrong owner/mode, symlink, wrong SDK/API, or installed-set drift | Never select candidate; clean only owned candidate path | `runtime_environment_rejected` (proposed) |
| Local deployment | Explicit run approval, exact target/limit, or dependency inputs are absent | Existing playbook remains no-op/fail-closed | normalized deployment blocker |
| Local smoke | Protocol output is contaminated, discovery drifts, timeout/cancel fails, or child survives | Close stdin, terminate/reap owned process group, retain normalized failure only | `local_smoke_failed` (proposed) |
| Runner equivalence | Status, bounds, redaction, correlation, duration, timestamp, truncation, or audit count drifts | Reject local readiness; do not proceed to Option B | `runner_equivalence_failed` (proposed) |
| Option B startup | Activation artifact absent/stale, defaults false, or preflight not bound to current run | Do not construct/run Uvicorn | existing `NetworkMCPDisabledError` or normalized activation denial |
| Bind preflight | Interface lacks exact address, port is occupied, or alternate/wildcard listener exists | Do not bind; if active, stop service and escalate | `network_bind_scope_error` |
| TLS/CRL | Missing/unsafe material, invalid chain/EKU/SAN, stale CRL, wrong owner/mode, or symlink | Do not construct active application or bind | `tls_configuration_error` |
| Authentication | Missing, invalid, revoked, or unknown certificate identity | Deny before MCP handling and runner creation | generic TLS failure or `403`; no sensitive detail |
| HTTP admission | Wrong source, Host, Origin, method, content type, size, rate, session, or concurrency | Return fixed bounded denial; do not queue/retry/spawn | `403`, `413`, `429`, or `431` as contracted |
| Runner execution | Runner unavailable, malformed, timed out, or cancelled | Preserve existing bounded MCP result; terminate/reap; never retry | accepted runner status/error semantics |
| Activation | Approval, confirmation, preflight, target, or service identity mismatch | Keep stopped/disabled; remove unconsumed activation state if contracted | `activation_denied` (proposed) |
| Validation | Raw certificate, identity, payload, topology, credential, or audit data would be emitted | Suppress output and fail validation | `evidence_policy_violation` (proposed) |
| Disablement | Access removal or stop cannot be proven | Stop further operation, deny new activation, escalate to stop authority | `disablement_incomplete` (proposed) |
| Rollback | Path ownership is unclear or target intersects runner/diagnostics/credentials/audit/evidence/local stdio/historical runtime | Abort removal and preserve shared state | `rollback_scope_error` (proposed) |
| Shutdown | Sessions or runner children survive the 10-second deadline | systemd may kill after deadline; mark lifecycle failure and require review | `shutdown_timeout` / orphan blocker |

### VI. Security, Integrity, Idempotency, and Cleanup

- **Security:** Default-disabled values remain source-controlled false. Activation requires separate current approval, explicit confirmation, current-run preflight, fixed target, and root-controlled non-secret state. TLS secrets and client credentials never enter Git or ordinary output. mTLS identity comes only from validated TLS state. No request reaches the runner before all transport, authentication, authorization, and bounds checks pass.
- **Least authority:** Both modes expose only their accepted surfaces and fixed runner argv. No helper may add shell execution, retries, generic passthrough, caller-selected paths, service control, or remediation capability.
- **Integrity:** Locks require exact versions and hashes; wheel inventory and installed distributions must match. Source/configuration/catalog/unit/TLS metadata require regular non-symlink files, fixed ownership/modes, and accepted hashes. Activation binds to accepted deployment and preflight revisions.
- **Evidence:** Retain normalized outcomes only. Prohibit raw tool results, prompts, identifiers, credentials, certificates, private keys, certificate subjects, source addresses, request headers/bodies, raw exceptions, raw audits, and unapproved topology. Sensitive Ansible operations use `no_log`; no secret appears in diffs.
- **Idempotency:** Re-running disabled deployment converges without activation. Re-running activation succeeds only for the same current accepted state and never broadens scope. Validation is read-only. Disablement is safe when already stopped/disabled. Rollback removes only exact owned artifacts and reports already-absent state without touching shared paths.
- **Atomicity:** Build dependency environments as candidates and select only after full validation. Do not mutate a currently accepted environment in place when a failed upgrade could leave mixed distributions.
- **Cleanup:** Remove failed candidate venvs, transient smoke-client input, activation evidence according to its one-run contract, and temporary protected material copies. Always close stdin, cancel sessions, terminate/reap owned children, and verify listener/process absence after failure or disablement.
- **Coexistence:** Local stdio and Option B use separate paths and lifecycle controls. Option B rollback preserves local stdio. Both preserve the runner, diagnostics, credentials, audit/evidence paths, and historical runtime.
- **Firewall:** Only the Vagrant owner may mutate the marker-scoped rule. If owning automation is not found and approved, consume verified marker evidence and stop before activation; never substitute ad hoc host commands.

### VII. Validation Strategy

Validation is chunk-aware and non-live through this ADS. Use the user-approved Python environment for Python compilation/tests; do not fall back to system Python. Step 6 and operational Steps 7–10 remain separate gates.

#### Documentation and artifact checks

```bash
rtk git status --short
rtk git diff --check
rtk grep -nE '^### (I|II|III|IV|V|VI|VII|VIII|IX|X)\.' \
  docs/ai-ops-revised/implementation-plan/ads/07-x01-mcp-deployment-activation-steps-01-to-05-ads.md
rtk grep -RniE 'enabled: true|0\.0\.0\.0|FastMCP|shell=True|verify=False' \
  ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp \
  ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio
```

#### Dependency closure checks

Exact commands depend on the owner-approved lock tooling and offline source. Validation must prove:

- lock syntax and complete hashes;
- no editable/URL/VCS/extra/prohibited dependency;
- exact lock-to-wheel inventory and wheel hash/tag compatibility;
- network-disabled, hash-required installation into a temporary venv;
- installed distribution equality and `mcp==1.28.1` API signatures; and
- no runtime package acquisition in Ansible tasks.

No placeholder lock or fabricated wheel may be created to make these checks pass.

#### Python validation

```bash
rtk <approved-python-venv>/bin/python -m py_compile \
  ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp_stdio/files/mcp_stdio/aiops_assistant_mcp_stdio_server.py \
  ansible/ai_ops_assistant/roles/ai_ops_assistant_mcp/files/mcp/aiops_assistant_mcp_server.py
rtk <approved-python-venv>/bin/python -m unittest discover \
  -s ansible/ai_ops_assistant/tests/mcp_stdio -p 'test_*.py'
rtk <approved-python-venv>/bin/python -m unittest discover \
  -s ansible/ai_ops_assistant/tests/mcp -p 'test_*.py'
```

Targeted additions must cover offline closure rejection, venv integrity, local smoke protocol/lifecycle behavior, Option B application construction, no-runner denial, TLS/auth fixtures, graceful shutdown, and normalized lifecycle output. Fixture tests must patch/inject transports and runners and prove no real listener, OpenStack access, package acquisition, firewall mutation, host contact, or raw audit inspection occurs.

#### Deployment/static validation

```bash
rtk bash -n ansible/ai_ops_assistant/tests/mcp_stdio/test_deployment_static.sh
rtk env PYTHON_BIN=<approved-python-venv>/bin/python \
  ansible/ai_ops_assistant/tests/mcp_stdio/test_deployment_static.sh
rtk ansible-playbook --syntax-check \
  -i ansible/ai_ops_assistant/inventories/local/local.yml \
  ansible/ai_ops_assistant/<changed-mcp-playbook>.yml \
  --limit assistant02
```

Run Ansible syntax/check mode only when the tool is available and the command cannot contact a host. Every lifecycle playbook must have static assertions for exact target, one operation, false defaults, absent broad host patterns, protected output, and shared-path preservation.

#### Symbol, path, and contract checks

- Confirm existing or modified `create_application`, `build_tls_context`, `build_uvicorn_config`, `main`, `run_server`, and child cleanup symbols with targeted search and tests.
- Confirm both approved lock paths exist only after owner-supplied closure acceptance.
- Confirm every proposed lifecycle playbook includes only its intended task path and cannot import deployment as implicit activation.
- Confirm service name, unit path, runtime roots, bind address/port, endpoint, source CIDR, principal URI, and firewall marker remain exact.
- Confirm rollback manifests contain no shared runner, diagnostic, credential, audit, evidence, local-stdio, or historical-runtime paths.

#### Final review

```bash
rtk git diff --stat
rtk git diff -- docs/ai-ops-revised ansible/ai_ops_assistant
rtk git diff --check
```

Review staged and unstaged changes separately. Scan diffs for secrets, private keys, certificates, tokens, passwords, raw payloads/audits, public bind, TLS verification bypass, ad hoc firewall commands, package downloads, shell execution, broad host scope, and unsupported live-completion claims.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement Steps 1–5 in one pass. This ladder refines extension-plan Chunks 0–4 so each compile-safe session has a narrower stop point.

#### Chunk 0: Decision, Authority, and Evidence Contract

- **Goal:** Freeze Step 1 decisions and reconcile the actual host ABI, activation control, protected inputs, evidence policy, firewall owner interface, stop authority, and rollback ownership before executable changes.
- **Files to read:** extension plan; this ADS; all three Phase 07 MCP operations contracts; both MCP defaults/tasks/playbooks; inventory; accepted runner/readiness contracts; existing normalized-evidence and rollback entrypoints; approved SDK metadata.
- **Commands:** bounded `rtk git status`, `rtk find`, `rtk grep`, targeted reads, and approved interpreter metadata inspection. No package generation/install, host contact, TLS handling, firewall action, process start, runner call, audit inspection, or rollback.
- **Evidence to confirm:** all thirteen open confirmations in Section II and exact operations-contract destination.
- **Files to change:** proposed `docs/ai-ops-revised/runtime/mcp-deployment-activation-and-live-validation-operations-contract.md`; extension plan only if an owner-approved decision must be reconciled.
- **Symbols to add/change:** documentation decision register, authorization matrix, normalized evidence schema, activation-state contract, stop rules, and exact ownership/removal manifests; no executable symbols.
- **Implementation shape:** documentation only; retain unresolved fields as blockers rather than placeholders accepted by automation.
- **Validation:** Markdown heading/fence/link scans, terminology/path checks, focused diff, `rtk git diff --check`.
- **Stop condition:** reviewers can identify who authorizes every side effect, the exact accepted ABI and target, what evidence may be retained, and why deployment remains unable to activate. Otherwise stop with blockers.

#### Chunk 1: Approved Offline Dependency Closure and Fail-Closed Acceptance

- **Goal:** Implement Step 2 acceptance around owner-supplied locks/wheels without enabling either deployment mode.
- **Files to change:** both mode-specific `requirements.lock` files only when supplied and approved; proposed focused dependency-closure validator/test artifacts in `ansible/ai_ops_assistant/tests/`; operations contract only for evidence-backed reconciliation.
- **Symbols to add/change:** conceptual closure parser/inventory validator, prohibited-dependency policy, ABI/tag/hash checks, normalized result type, and temporary-venv verification seam.
- **Implementation shape:** write failing/rejection fixtures first; validator accepts injected temporary lock/wheel inventories. Do not embed wheel binaries, protected source locations, credentials, or network fallback. If approved locks/wheels are unavailable, complete only rejection/static fixtures and report the closure blocker.
- **Validation:** validator syntax/tests; lock policy scans; network-disabled temporary install only with separately approved local artifacts; API signature checks using the approved environment; focused diff.
- **Stop condition:** both modes have independently accepted reproducible closures for the frozen ABI, or the chunk stops fail-closed with no fabricated artifacts and no deployment changes.

#### Chunk 2: Local-stdio Dedicated Venv and Guarded Deployment

- **Goal:** Extend Step 3 deployment so explicit run-scoped enablement can materialize and verify the approved local venv/artifacts while never creating a service, listener, registration, or process.
- **Files to change:** `roles/ai_ops_assistant_mcp_stdio/defaults/main.yml`; `roles/ai_ops_assistant_mcp_stdio/tasks/main.yml`; `tests/mcp_stdio/test_deployment_static.sh` (three files are required because the existing role contract and its acceptance live separately).
- **Symbols to add/change:** fixed offline wheel input metadata, lock/wheel/ABI validation tasks, deterministic candidate-venv lifecycle, installed-set/hash checks, explicit approval variables, and artifact/venv ownership assertions.
- **Implementation shape:** defaults stay false/unconfirmed. Create and validate called task logic before adding enabled call sites. Build no service; run no adapter. Failure removes only the owned candidate environment and leaves existing accepted state untouched.
- **Validation:** `bash -n`; static deployment test with approved `PYTHON_BIN`; Ansible syntax/check-mode validation if available; role scans forbidding service/listener/firewall/client/runner/audit/network package actions; focused diff.
- **Stop condition:** an enabled, explicitly approved role can converge the local dedicated environment from accepted offline inputs, while default execution remains non-activating. Do not contact `assistant02`.

#### Chunk 3: Non-Registering Local-stdio Smoke Harness

- **Goal:** Add the fixture-safe Step 3 smoke seam that owns one adapter process and emits normalized outcomes only.
- **Files to change:** proposed smoke harness under `ansible/ai_ops_assistant/tests/mcp_stdio/` or an owner-approved operator-support path; one focused harness test module.
- **Symbols to add/change:** conceptual child lifecycle wrapper, initialize/discovery/request/cancel cases, protocol-only stdout parser, normalized outcome model, deadline handling, stdin-close, and process-group cleanup.
- **Implementation shape:** start with an injected fake adapter subprocess. Do not register a client, connect to a listener, call OpenStack, inspect raw audits, or retain raw results. The future host command path remains separately gated.
- **Validation:** Python compile and focused tests for exact discovery, invalid/generic/remediation denials, timeout/cancellation/EOF, stdout contamination, normalized evidence fields, and no surviving child; full local-stdio suite; focused diff.
- **Stop condition:** the harness proves bounded client ownership and cleanup against fixtures. No live adapter or runner is launched.

#### Chunk 4: Option B Application Construction and Fixture Startup/Shutdown

- **Goal:** Replace the unconditional Step 4 `create_application()` rejection with a complete but still fail-closed application-construction path exercised only through injected fixtures.
- **Files to change:** `roles/ai_ops_assistant_mcp/files/mcp/aiops_assistant_mcp_server.py`; `roles/ai_ops_assistant_mcp/files/mcp/mcp_resource_catalog.json`; `tests/mcp/test_aiops_assistant_mcp_server.py`; `tests/mcp/test_aiops_assistant_mcp_equivalence.py`. Four tightly coupled files are required because the plan's six-resource target differs from the current three-entry Option B catalog and both source metadata and fixture equivalence must change together.
- **Symbols to add/change:** `create_application`, `REVIEWED_RESOURCE_METADATA`, Starlette `/mcp` route/lifespan wiring, authenticated principal extraction seam, activation-evidence validator, admission middleware/handler, and deterministic lifecycle errors. Existing `NetworkMCPApplication` remains the return container unless SDK confirmation requires a reviewed change.
- **Implementation shape:** first freeze and test the exact Option B six-resource catalog, then define dependency-injection seams before active call sites. A temporary absent activation-evidence loader must raise, not return success. Fixture construction may inject validated TLS/principal state; production code must reject header-asserted identity. Do not modify `main()` to run Uvicorn in this chunk.
- **Validation:** Python compile; focused application construction, exact route/method, Host/Origin/source/principal denial, no-runner-on-denial, three-tool/six-resource/no-prompt, lifespan, cancellation, and shutdown tests; confirm no socket bind; focused diff.
- **Stop condition:** authenticated application behavior is fixture-testable and unauthorized requests cannot reach the runner; executable startup remains disabled because `main()` is unchanged.

#### Chunk 5: Disabled Option B Environment, TLS Inputs, Unit, and Current-Run Preflight

- **Goal:** Complete the non-activating half of Step 5: deterministic Option B venv/artifact/TLS/unit deployment plus current-run readiness checks, leaving the service stopped and disabled.
- **Files to change:** Option B role defaults/tasks and focused static deployment tests; proposed preflight task file/entrypoint if confirmed in Chunk 0.
- **Symbols to add/change:** offline closure inputs, protected TLS source descriptors, `no_log` materialization, certificate/CRL metadata checks, accepted runner revision, bind ownership/port-absence checks, firewall-marker evidence, rollback-readiness manifest, and current-run preflight result.
- **Implementation shape:** preserve `playbook_deploy_mcp.yml` as deployment-only. TLS inputs come only from the approved protected source. Firewall work delegates to owner automation or validates evidence; no ad hoc command. Install unit stopped/disabled and never create activation state.
- **Validation:** YAML/Ansible syntax and safe check mode if available; static tests for exact target/limit, closure and TLS failures, no listener/start/enable, `no_log`, service hardening, firewall ownership, normalized preflight, and idempotent disabled deployment; focused diff.
- **Stop condition:** Option B artifacts can be prepared and assessed without activation. No host deployment, TLS handling, firewall mutation, or listener occurs in this implementation session.

#### Chunk 6: Explicit Option B Activation and Normalized Validation Entrypoints

- **Goal:** Add the narrowly separate activation and validation operations from Step 5 and complete the production `main()` path without executing it.
- **Files to change:** Option B adapter plus proposed activation/validation playbooks/task files and their focused static tests. Because the plan mandates separate entrypoints, multiple small files are required; implement activation first, validate, then add read-only validation in the same reviewed chunk only if compile-safe.
- **Symbols to add/change:** `main()` active path, current-run activation-state loader, Uvicorn server construction/run seam, activation approval/confirmation checks, exact service start/enable action, and normalized post-start validation fields.
- **Implementation shape:** repository defaults remain false. Activation requires current preflight and exact approval and touches only `ai-ops-assistant-mcp`. Validation reads unit/PID/user/group/listener/hardening state without exposing protected values. Tests inject the server and systemd outcomes; no listener or service starts locally.
- **Validation:** Python compile; focused `main()` disabled/rejected/injected-success/shutdown tests; YAML/Ansible syntax; static operation-separation and no-secret checks; full Option B fixture suite; focused diff.
- **Stop condition:** source and automation can express a separately gated exact activation and normalized validation, but no playbook is run against a host and no server binds.

#### Chunk 7: Disablement, Exact Rollback, and Lifecycle Separation Acceptance

- **Goal:** Complete Step 5 with separately authorized disablement and rollback entrypoints and prove shared-runtime preservation.
- **Files to change:** proposed disablement/rollback playbooks/task files; one focused lifecycle static test; operations contract only for evidence-backed corrections.
- **Symbols to add/change:** ordered access-removal/service-stop checks, exact owned-artifact manifest, independent rollback approval, check-mode guards, already-absent idempotency, post-operation process/listener assertions, and normalized outcomes.
- **Implementation shape:** disablement and rollback are separate. Rollback rejects path drift/symlinks/ownership ambiguity and cannot remove runner, diagnostics, credentials, audit/evidence, local stdio, Option B-independent firewall state, or historical runtime. No operational execution occurs.
- **Validation:** YAML/Ansible syntax and non-contact check mode where possible; static negative tests for deployment-to-activation coupling, broadened service/firewall scope, shared-path removal, raw evidence, and absent authorization; all MCP static/fixture suites; aggregate diff/security review.
- **Stop condition:** all five lifecycle operations are distinct, fail-closed, scoped, and statically evidenced. Stop before plan Step 6 acceptance or any `assistant02` contact.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, pre-edit-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Implement Steps 1–5 of docs/ai-ops-revised/implementation-plan/07-x01-mcp-deployment-activation-and-live-validation.md using docs/ai-ops-revised/implementation-plan/ads/07-x01-mcp-deployment-activation-steps-01-to-05-ads.md.

Mode:
Execute Chunk 0 only. Confirm and record the authority matrix, actual assistant02 Python version/ABI, dependency source and ownership, normalized evidence contract, stop authority, activation-state contract, protected TLS source, Vagrant firewall-owner interface, MCP SDK authentication/lifespan seam, smoke-client ownership, and accepted runner revision. Do not modify executable files. Do not generate or install packages, contact a host, handle certificates or credentials, mutate firewall state, start a process/listener, register a client, call a runner/OpenStack, inspect raw audits, disable services, or execute rollback. Stop with evidence and blockers.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Execute Chunk 1 only.
Do not continue to Chunk 2.
Accept only owner-supplied dependency closure inputs and implement fail-closed static/fixture validation. Do not fabricate requirements.lock or wheel artifacts, use public package indexes, modify deployment enablement, contact assistant02, start MCP, or perform any live operation. Run targeted validation, show staged and unstaged diffs, and stop.
```

For every later chunk, obtain explicit approval for that chunk only. Chunks 0–7 are repository implementation/static-fixture work; they do not authorize extension-plan operational Chunks 6–9 or Steps 7–10.

### X. Conclusion and Next Steps

Steps 1–5 should convert the current artifact-only Phase 07 state into a reviewable, default-disabled deployment and lifecycle foundation without claiming any host or live evidence. The first safe action is Chunk 0: resolve the actual Python ABI and freeze authority, evidence, activation, TLS, firewall, and rollback contracts. The missing approved dependency closures remain a hard stop for enabled deployment, and the absent firewall-owner automation remains a hard stop for Option B activation unless an approved evidence interface is supplied.
