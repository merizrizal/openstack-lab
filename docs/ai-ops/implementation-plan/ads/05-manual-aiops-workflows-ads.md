## Architectural Design Specification: Manual AI-OPS Workflows

**Source:** `docs/ai-ops/implementation-plan/05-manual-aiops-workflows.md`

**Goal:** Make the AI-OPS MVP usable through documented, validated manual workflows where an operator runs approved local runner tools, provides redacted outputs to an AI assistant, and receives explanation plus manual recommendations only.

---

### I. Overview and Contract

Phase 05 turns the Phase 03 diagnostic toolbox and Phase 04 tool runner into repeatable human-operated AI-OPS workflows.

Target execution path:

```text
operator question
  -> approved tool sequence
  -> local runner structured outputs
  -> AI explanation prompt
  -> manual recommendation only
```

This phase is documentation-first and validation-backed. It must not add MCP integration, chat UI automation, host-level SSH diagnostics, sudo rules, raw OpenStack passthrough, database access, file mutation tools, or remediation capability.

#### Manual Workflow Boundary Contract (Concrete)

Observed approved local runner tools from `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/tool_registry.json`:

- `project_resource_summary`
- `server_basic_info`
- `server_network_info`
- `neutron_agent_health`, explicitly unavailable until a validated non-default operator-reader profile exists

Observed runner source path:

```text
ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py
```

Observed runtime install path from Phase 04 evidence:

```text
/opt/openstack-ai-ops/scripts/tool_runner/aiops_tool_runner.py
```

Observed default runtime audit path:

```text
/opt/openstack-ai-ops/audit/tool-runner.jsonl
```

Observed runner CLI shape from `aiops_tool_runner.py`:

```text
aiops_tool_runner.py <tool_name> --arg key=value --request-id <id> --audit-path <path>
```

The Phase 05 workflows should show runner-first examples and should not present raw `openstack`, shell, SSH, sudo, restart, edit, delete, create, or repair commands as AI-operated actions.

#### Result Envelope Contract (Concrete)

Observed `build_result_envelope` returns JSON fields:

- `tool`
- `status`
- `arguments`
- `exit_code`
- `stdout`
- `stderr`
- `duration_ms`
- `truncated`
- `timestamp`
- `request_id`

Phase 05 documentation and validation should teach operators to preserve these fields when sharing evidence with AI, while redacting identifiers and any secret-like values before committing repository evidence.

#### Manual AI Prompt Contract (Conceptual)

Prompt templates should ask the AI assistant to:

- summarize healthy signals;
- summarize failing or unavailable signals;
- identify likely failure domains;
- ask specific follow-up questions when output is incomplete;
- recommend manual next steps only;
- refuse to execute or request remediation.

Prompt templates should explicitly forbid mutation requests such as `fix it`, `restart it`, `delete it`, `create it`, `edit config`, `run this shell command`, and `SSH into the host`.

#### Documentation Contract (Conceptual)

Proposed primary Phase 05 workflow document:

```text
docs/ai-ops/runtime/manual-aiops-workflows.md
```

It should include:

1. Diagnostic-only assistant behavior policy.
2. Refusal guidance for mutation requests.
3. Approved MVP tool catalog.
4. Unavailable/deferred tool catalog.
5. Basic project inspection workflow.
6. Server inspection workflow.
7. Metadata troubleshooting workflow.
8. AI explanation prompt templates.
9. Redacted sample output summaries.
10. Remaining gaps for Phase 06 host diagnostics and Phase 07 MCP.

#### Runtime Validation Contract (Conceptual)

Proposed runtime validation playbook:

```text
ansible/ai_ops_runtime/playbook_validate_phase05_manual_aiops_workflows.yml
```

It should prove:

- project summary runs through the local runner;
- server basic info runs against a project-visible server;
- server network info runs against the same server;
- structured result envelopes are produced;
- audit events are emitted for validation request IDs;
- `neutron_agent_health` remains unavailable;
- AI prompt guidance remains diagnostic-only and non-mutating.

### II. Observed Evidence and Assumptions

#### Observed Evidence

- `docs/ai-ops/implementation-plan/05-manual-aiops-workflows.md` defines the Phase 05 target as `operator question -> approved tool sequence -> local runner outputs -> AI explanation prompt -> manual recommendation only`.
- Phase 05 includes documentation for assistant behavior, project inspection, server inspection, metadata troubleshooting, and full MVP validation.
- Phase 05 excludes MCP integration, chat UI implementation, host-level SSH log diagnostics unless already available, and automatic selection/execution by an AI client.
- `docs/ai-ops/implementation-plan/00-implementation-overview.md` states the MVP is done when a safe workflow can move from operator question to approved diagnostic tools, structured result/audit, AI explanation, manual next steps, and no mutation.
- `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/tool_registry.json` contains the reviewed tool registry and deny-by-default policy.
- `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py` implements the local runner CLI, structured result envelopes, validation, audit writing, and status-specific exit codes.
- `docs/ai-ops/runtime/phase04-tool-runner-safety-gateway-evidence-2026-07-08.md` confirms runtime checks for the runner, registry, audit path, approved scripts, denied unknown tool, unsafe parameter rejection, unavailable Neutron gate, approved project summary smoke, and audit event summaries.
- `docs/ai-ops/runtime/phase03-diagnostic-toolbox-evidence-2026-07-07.md` confirms approved script deployment and successful runtime evidence for project summary, server basic info, and server network info against a representative server.
- `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved/project_resource_summary.sh` accepts no arguments and emits sectioned JSON-oriented project-visible resource summaries.
- `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved/server_basic_info.sh` accepts exactly one validated server name or ID and runs a fixed read-only server show operation.
- `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/approved/server_network_info.sh` accepts exactly one validated server name or ID and emits server summary, server ports, and project-visible network/subnet correlation sections.
- `docs/troubleshooting/01-openstack-instance-metadata-503.md` documents a metadata troubleshooting path involving guest cloud-init, `169.254.169.254`, Neutron metadata proxy/agent, Nova metadata API, Apache listener `8775`, and host logs/listeners.
- `ansible/ai_ops_runtime/roles/assistant_runtime/defaults/main.yml` includes runtime directories for `runbooks`, `diagnostics/raw`, `diagnostics/summaries`, and `audit`.

#### Assumptions

- Phase 05 can be delivered primarily as repository documentation plus runtime validation evidence.
- A representative project-visible server is available for server workflow validation, or validation can be parameterized and clearly skipped with a recorded reason.
- Operators will manually copy redacted runner outputs into an AI assistant for the MVP.
- Runtime raw outputs and audit logs remain outside the repository; only sanitized evidence summaries are committed.
- The optional Phase 05 validation playbook should follow the existing Phase 03/04 validation evidence pattern.
- Any host-level metadata checks from the troubleshooting note must be labeled deferred until Phase 06 unless already available through approved read-only tools.

### III. Required Technical Dependencies and Imports

#### Runtime Dependencies

- AI-OPS assistant runtime, currently represented by `assistant01` in evidence.
- Runtime root:

  ```text
  /opt/openstack-ai-ops
  ```

- Local tool runner:

  ```text
  /opt/openstack-ai-ops/scripts/tool_runner/aiops_tool_runner.py
  ```

- Tool registry:

  ```text
  /opt/openstack-ai-ops/scripts/tool_runner/tool_registry.json
  ```

- Audit path:

  ```text
  /opt/openstack-ai-ops/audit/tool-runner.jsonl
  ```

- Approved scripts:

  ```text
  /opt/openstack-ai-ops/scripts/approved/project_resource_summary.sh
  /opt/openstack-ai-ops/scripts/approved/server_basic_info.sh
  /opt/openstack-ai-ops/scripts/approved/server_network_info.sh
  /opt/openstack-ai-ops/scripts/approved/neutron_agent_health.sh
  ```

- Default project-reader credential profile:

  ```text
  aiops-project-reader
  ```

#### Repository Dependencies

- `docs/ai-ops/runtime/` for workflow documentation and sanitized evidence.
- `docs/ai-ops/implementation-plan/05-manual-aiops-workflows.md` for checklist/DoD updates after validation.
- `ansible/ai_ops_runtime/` for optional runtime validation playbook.

#### New External Dependencies

Not applicable. Phase 05 should not add new Python packages, services, APIs, MCP dependencies, chat integrations, SSH credentials, sudo rules, OpenStack write credentials, or remediation executors.

### IV. Step-by-Step Procedure / Execution Flow

1. Confirm target documentation and validation paths.
   - Use the existing `docs/ai-ops/runtime/` evidence pattern.
   - Prefer `manual-aiops-workflows.md` for the operator-facing runbook.
2. Add diagnostic-only assistant behavior policy.
   - State that AI may observe, explain, and recommend manual actions.
   - State that AI must not mutate the lab or request mutation tools.
   - Include refusal examples for `fix it`, `restart it`, `delete it`, `create it`, `edit config`, and raw command requests.
3. Add the approved and unavailable tool catalog.
   - List `project_resource_summary`, `server_basic_info`, and `server_network_info` as available MVP tools.
   - List `neutron_agent_health` as unavailable until validated operator-reader credentials exist.
   - List host/log diagnostics, MCP, chat UI, remediation, generic shell, SSH, sudo, and raw OpenStack passthrough as deferred or forbidden.
4. Add the project inspection workflow.
   - Explain when to run `project_resource_summary`.
   - Show runner-first invocation shape.
   - Explain empty outputs, permission-denied/unavailable sections, truncation, and structured status handling.
   - Include a redacted sample summary, not raw sensitive inventory.
5. Add the server inspection workflow.
   - Explain how to choose a safe `server_identifier` from project summary output.
   - Run `server_basic_info` and `server_network_info` for the same identifier.
   - Explain server status, attached networks, fixed IPs, ports, volumes, config-drive clues, and incomplete output questions.
6. Add the metadata troubleshooting workflow.
   - Start from a symptom such as cloud-init or guest metadata failure at `169.254.169.254`.
   - Use project summary and server inspection to gather project-visible evidence.
   - Explain which evidence is available now and which evidence remains deferred until host/log diagnostics exist.
   - Use the known path: guest cloud-init -> `169.254.169.254` -> Neutron metadata proxy/agent -> Nova metadata API.
   - Do not instruct the AI to SSH, inspect host logs, restart services, or edit configuration in Phase 05.
7. Add AI prompt templates.
   - Project summary prompt.
   - Server inspection prompt.
   - Metadata troubleshooting prompt.
   - Safety refusal/policy prompt.
8. Add optional runtime validation playbook.
   - Check runner and registry paths.
   - Run approved project summary.
   - Run server tools when a server identifier is supplied.
   - Check `neutron_agent_health` unavailable gate.
   - Parse JSON result envelopes.
   - Check audit entries for request IDs.
   - Generate sanitized evidence summary.
9. Record validation evidence.
   - Commit only sanitized evidence.
   - Exclude raw audit logs, credential material, tokens, private keys, passwords, and raw profile contents.
10. Update Phase 05 checklist and DoD only after the workflow document and validation evidence exist.

### V. Failure Modes and Resilience

| Stage | Failure Mode | Agent/System Action | Next State/Error Report |
| ----- | ------------ | ------------------- | ----------------------- |
| Tool selection | Operator asks for unsupported diagnostic | Point to approved/unavailable tool list; do not invent commands | Documented limitation |
| Unsafe request | Operator asks AI to fix, restart, delete, create, edit, or run raw commands | Refuse execution; offer read-only evidence collection and manual recommendation | Diagnostic-only response |
| Runner invocation | Unknown tool is requested | Runner returns `denied`; audit event is written | Non-zero status, structured envelope |
| Argument validation | Unsafe `server_identifier` is provided | Runner returns `validation_error` before script execution | Non-zero status, structured envelope |
| Server lookup | Server does not exist or is not visible to project-reader | Preserve runner/script error; prompt asks for corrected identifier or visibility context | Manual follow-up |
| Permission boundary | Project-reader cannot see a resource section | Treat as visibility/permission limitation; do not escalate credentials | Gap recorded |
| Tool availability | `neutron_agent_health` requested before operator-reader validation | Runner returns `unavailable`; workflow explains deferral | Phase 06/credential follow-up |
| Output volume | Runner result is truncated | Prompt asks AI to reason from available sections and request targeted rerun/manual review | `truncated=true` noted |
| Audit validation | Request ID missing from audit | Validation fails; do not mark Phase 05 complete | Evidence gap |
| Metadata workflow | Host logs/listeners are required for decisive diagnosis | Label evidence as deferred to Phase 06; provide manual operator next-step categories | No SSH/sudo introduced |
| Evidence handling | Output contains sensitive identifiers or secret-like material | Redact before committing repository evidence | Sanitized summary only |
| Scope creep | MCP/chat automation requested in Phase 05 | Defer to Phase 07 | No interface expansion |
| Documentation drift | Workflow names diverge from registry tool names | Validation/review catches mismatch | Fix docs before completion |

### VI. Security, Integrity, Idempotency, and Cleanup

- Phase 05 must preserve the established safety boundary: AI reasoning is allowed; OpenStack Lab mutation is blocked.
- Documentation must use named approved tools, not arbitrary commands.
- The operator may administer the lab manually outside AI-OPS, but AI-facing workflow instructions must not execute remediation.
- Prompt templates must require manual recommendations only.
- The documentation must distinguish unavailable/deferred evidence from failure.
- `neutron_agent_health` remains unavailable until a validated non-default operator-reader profile exists.
- Host-level metadata checks from the existing troubleshooting note must be marked deferred to Phase 06 unless implemented behind approved restricted diagnostics.
- Validation playbooks must be idempotent and read-only.
- Runtime raw outputs and audit logs must not be committed.
- Sanitized evidence summaries must omit credential file contents, tokens, passwords, private keys, raw profile material, full sensitive identifiers, and raw audit logs.
- No cleanup of lab resources is required because Phase 05 does not create, update, or delete OpenStack resources.

### VII. Validation Strategy

#### Static and Local Validation

Use targeted validation for changed documentation and any optional validation playbook.

If only Markdown docs are changed:

```bash
rtk grep -Rni "project_resource_summary\|server_basic_info\|server_network_info\|neutron_agent_health" docs/ai-ops/runtime/manual-aiops-workflows.md
rtk grep -Rni "restart it\|delete it\|create it\|edit config\|manual recommendations" docs/ai-ops/runtime/manual-aiops-workflows.md
rtk git diff -- docs/ai-ops/runtime/manual-aiops-workflows.md
```

If an Ansible validation playbook is added:

```bash
rtk ansible-playbook --syntax-check ansible/ai_ops_runtime/playbook_validate_phase05_manual_aiops_workflows.yml
```

Existing runner safety regression should remain green:

```bash
rtk python3 -m json.tool ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/tool_registry.json >/dev/null
rtk python3 -m py_compile ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py tests/ai_ops/test_tool_runner.py tests/ai_ops/__init__.py
rtk python3 -m unittest discover -s tests -p 'test_tool_runner.py'
```

#### Runtime Validation

Run on the assistant runtime, preferably through a Phase 05 validation playbook:

1. Run `project_resource_summary` through the runner.
2. Run `server_basic_info` for one project-visible server.
3. Run `server_network_info` for the same server.
4. Confirm structured result envelopes are produced.
5. Confirm audit events exist for all validation request IDs.
6. Confirm `neutron_agent_health` still returns `unavailable`.
7. Provide sanitized output to an AI assistant and verify the response explains signals and gives manual recommendations only.
8. Record confusing output or missing evidence as follow-up work.

#### Final Review

Before marking Phase 05 complete:

```bash
rtk git diff --stat
rtk git diff -- docs/ai-ops/implementation-plan/05-manual-aiops-workflows.md docs/ai-ops/runtime ansible/ai_ops_runtime
```

Review for:

- no secrets or raw audit logs;
- no AI-facing mutation instructions;
- no MCP/chat/SSH/sudo additions;
- tool names match registry entries;
- remaining gaps are explicitly documented.

### VIII. Thin Vertical Slice Chunk Design

The implementation must proceed through `chunked-implementation`. Do not implement the full feature in one pass.

#### Chunk 0: Discovery and Integration Confirmation

- **Goal:** Confirm exact documentation, runner, registry, and validation conventions before edits.
- **Files to read:**
  - `docs/ai-ops/implementation-plan/05-manual-aiops-workflows.md`
  - `docs/ai-ops/implementation-plan/00-implementation-overview.md`
  - `docs/ai-ops/runtime/README.md`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/tool_registry.json`
  - `ansible/ai_ops_runtime/roles/assistant_runtime/files/scripts/tool_runner/aiops_tool_runner.py`
  - `docs/troubleshooting/01-openstack-instance-metadata-503.md`
- **Commands:**
  - `rtk find docs/ai-ops -maxdepth 4 -type f | rtk sort`
  - `rtk grep -Rni "manual\|metadata\|project_resource_summary\|server_basic_info\|server_network_info" docs ansible tests 2>/dev/null | rtk head -100`
- **Evidence to confirm:** target workflow doc path, exact runner tool names, CLI shape, runtime evidence pattern, and metadata source.
- **Stop condition:** no edits; implementation path and uncertainties documented.

#### Chunk 1: Workflow Document Skeleton and Assistant Policy

- **Goal:** Add the Phase 05 manual workflow document with diagnostic-only behavior policy.
- **Files to change:**
  - `docs/ai-ops/runtime/manual-aiops-workflows.md`
- **Symbols to add/change:** Markdown sections only; no code symbols.
- **Implementation shape:** Add title, scope, diagnostic-only assistant behavior, refusal guidance, approved/deferred tool catalog, and safety principles.
- **Validation:**
  - `rtk grep -n "Diagnostic-Only\|Approved MVP Tools\|Unavailable\|Refusal" docs/ai-ops/runtime/manual-aiops-workflows.md`
  - `rtk git diff -- docs/ai-ops/runtime/manual-aiops-workflows.md`
- **Stop condition:** operator can understand what the AI-OPS MVP can and cannot do before running tools.

#### Chunk 2: Basic Project Inspection Workflow

- **Goal:** Document a safe workflow for answering “what exists in this project?”
- **Files to change:**
  - `docs/ai-ops/runtime/manual-aiops-workflows.md`
- **Symbols to add/change:** Markdown section for project resource summary workflow.
- **Implementation shape:** Add when-to-run guidance, runner invocation shape, expected envelope fields, interpretation of empty output or unavailable sections, AI prompt template, and redacted sample summary.
- **Validation:**
  - `rtk grep -n "project_resource_summary\|what exists in this project\|permission" docs/ai-ops/runtime/manual-aiops-workflows.md`
  - `rtk git diff -- docs/ai-ops/runtime/manual-aiops-workflows.md`
- **Stop condition:** project workflow is independently usable without server-specific context.

#### Chunk 3: Server Inspection Workflow

- **Goal:** Document read-only evidence collection for one server.
- **Files to change:**
  - `docs/ai-ops/runtime/manual-aiops-workflows.md`
- **Symbols to add/change:** Markdown section for server basic and network inspection.
- **Implementation shape:** Use the same `server_identifier` for `server_basic_info` and `server_network_info`; document safe identifier rules, status, networks, ports, fixed IPs, volumes, config-drive clues, permission errors, and follow-up questions for incomplete output.
- **Validation:**
  - `rtk grep -n "server_basic_info\|server_network_info\|server_identifier\|config-drive" docs/ai-ops/runtime/manual-aiops-workflows.md`
  - `rtk git diff -- docs/ai-ops/runtime/manual-aiops-workflows.md`
- **Stop condition:** operator can collect enough read-only evidence to discuss one server state and network attachments with AI.

#### Chunk 4: Metadata Troubleshooting Workflow

- **Goal:** Convert existing metadata troubleshooting knowledge into an MVP-safe workflow.
- **Files to change:**
  - `docs/ai-ops/runtime/manual-aiops-workflows.md`
- **Symbols to add/change:** Markdown metadata troubleshooting section and AI prompt template.
- **Implementation shape:** Start from `169.254.169.254` or cloud-init symptoms; use project/server/network runner outputs; explain healthy/failing signals; label Neutron metadata agent logs, Nova metadata API listener `8775`, Apache config, and host checks as deferred to Phase 06 unless safely exposed later.
- **Validation:**
  - `rtk grep -n "169.254.169.254\|metadata\|Phase 06\|manual next steps" docs/ai-ops/runtime/manual-aiops-workflows.md`
  - Manual review that the workflow does not instruct AI to SSH, sudo, restart services, or edit config.
  - `rtk git diff -- docs/ai-ops/runtime/manual-aiops-workflows.md`
- **Stop condition:** operator can begin metadata diagnosis safely using approved MVP tools only.

#### Chunk 5: Runtime Validation Playbook

- **Goal:** Add an optional validation playbook that proves the manual/local-runner MVP path.
- **Files to change:**
  - `ansible/ai_ops_runtime/playbook_validate_phase05_manual_aiops_workflows.yml`
- **Symbols to add/change:** Ansible tasks/vars only.
- **Implementation shape:** Add read-only tasks to check runner paths, run project summary, run server basic/network when a server identifier is supplied, check unavailable Neutron gate, parse result envelopes, check audit events by request ID, and write a sanitized evidence summary under runtime diagnostics.
- **Validation:**
  - `rtk ansible-playbook --syntax-check ansible/ai_ops_runtime/playbook_validate_phase05_manual_aiops_workflows.yml`
  - `rtk git diff -- ansible/ai_ops_runtime/playbook_validate_phase05_manual_aiops_workflows.yml`
- **Stop condition:** syntax-valid playbook exists; no runtime claim made until it is executed.

#### Chunk 6: Runtime Evidence and Phase Status Update

- **Goal:** Record sanitized validation results and mark Phase 05 complete only after validation succeeds.
- **Files to change:**
  - `docs/ai-ops/runtime/phase05-manual-aiops-workflows-evidence-<date>.md`
  - `docs/ai-ops/implementation-plan/05-manual-aiops-workflows.md`
- **Symbols to add/change:** Markdown evidence summary and checklist boxes.
- **Implementation shape:** Add redacted runtime evidence summary with request IDs/statuses, structured envelope confirmation, audit event confirmation, AI manual-only response confirmation, and remaining gaps. Update checklist/DoD only for validated items.
- **Validation:**
  - `rtk grep -Rni "password\|token\|private key\|secret" docs/ai-ops/runtime/phase05-manual-aiops-workflows-evidence-<date>.md`
  - Manual review for false positives and redaction completeness.
  - `rtk git diff -- docs/ai-ops/runtime docs/ai-ops/implementation-plan/05-manual-aiops-workflows.md`
- **Stop condition:** Phase 05 has sanitized proof, plan status is accurate, and remaining gaps are documented.

### IX. Handoff to `chunked-implementation`

Recommended agent prompt:

```text
Use the chunked-implementation skill.
Use pre-read-discipline, safe-python-edit, and post-edit-discipline if available.

Task:
Implement Phase 05 Manual AI-OPS Workflows from docs/ai-ops/implementation-plan/05-manual-aiops-workflows.md.

Mode:
Execute Chunk 0 only. Do not edit files. Confirm repository evidence and stop.
```

After Chunk 0 is accepted:

```text
Use the chunked-implementation skill.
Execute Chunk 1 only.
Do not continue to Chunk 2.
After editing, run targeted validation and show git diff.
```

For later chunks:

```text
Use the chunked-implementation skill.
Execute the next approved Phase 05 chunk only.
Do not continue to subsequent chunks.
Run the chunk-specific validation from the ADS and show git diff before stopping.
```

### X. Conclusion and Next Steps

Phase 05 should be implemented as a documentation-first, validation-backed MVP usability layer over the existing safe diagnostic scripts and local runner. The first implementation step is Chunk 0 discovery, followed by a small workflow document skeleton and assistant behavior policy. MCP, chat UI, host-level diagnostics, SSH, sudo, raw OpenStack passthrough, and remediation remain out of scope for this phase.
