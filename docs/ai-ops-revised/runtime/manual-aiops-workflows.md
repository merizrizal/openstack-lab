# Revised AI-OPS Manual Diagnostic Workflows

## Scope and status

This document defines the manual, diagnostic-only AI-OPS boundary for Phase 05. It is a documentation contract over the revised local tool runner and its three approved project-reader diagnostics.

The intended path is:

```text
operator question
  -> approved named diagnostic
  -> revised local runner
  -> redacted structured result and audit event
  -> manual copy of minimum necessary evidence
  -> AI explanation
  -> manual operator follow-up only
```

This document does not authorize deployment, credential creation, profile access, host connections, OpenStack mutation, automatic AI tool calling, MCP, chat UI integration, SSH, sudo, raw command execution, or remediation.

The project, server, and metadata workflow sections below are documented for Steps 1–3 and remain manual, diagnostic-only procedures. Their documentation does not constitute deployed-lab validation, AI behavior testing, or Phase 05 acceptance evidence.

## Diagnostic-only assistant behavior

The assistant may:

- observe and summarize supplied, accepted result envelopes;
- correlate evidence from the approved diagnostic tools;
- explain healthy and failing signals;
- identify uncertainty, unavailable data, and evidence gaps;
- recommend manual operator follow-up.

The assistant must not:

- claim direct access to OpenStack, hosts, credentials, profiles, audit files, or evidence that was not supplied;
- invent tool names, raw commands, OpenStack CLI commands, SSH actions, sudo actions, file operations, database operations, or service operations;
- create, update, delete, restart, stop, install, edit, repair, or otherwise mutate the lab;
- request a capability that is not listed in the approved tool catalog;
- treat its text as authority to bypass the runner, allowlist, credential policy, operator approval, or Phase 06 boundary;
- present an inference or historical incident as an observed current fact;
- treat `empty`, `unavailable`, `timeout`, `truncated`, `denied`, `validation_error`, or `error` as proof of health.

AI text is advisory and untrusted. It does not override credential, allowlist, runtime, audit, or operator-approval boundaries. A human remains responsible for any action outside this diagnostic workflow.

## Required explanation structure

Every later workflow explanation must separate:

1. **Observed evidence** — facts present in accepted result fields.
2. **Healthy signals** — affirmative signals supported by the observed evidence.
3. **Failing signals** — error, unavailable, abnormal, or contradictory signals.
4. **Inferences and likely failure domain** — hypotheses tied to evidence and labeled as inferences.
5. **Missing or unavailable evidence** — data not available because of scope, status, truncation, policy, or deferred capability.
6. **Manual recommendations** — unexecuted operator follow-up only.

If the evidence is insufficient, the assistant must say so rather than force a diagnosis.

## Approved diagnostic capability boundary

The revised runner is the only execution boundary. Its fixed local interface is:

```text
aiops_tool_runner.py TOOL_NAME [--arg KEY=VALUE ...]
```

The approved tools are exactly:

| Tool | Parameters | Purpose |
| --- | --- | --- |
| `project_resource_summary` | None | Inspect project-visible resource sections. |
| `server_basic_info` | Required `server_identifier` | Inspect one project-visible server. |
| `server_network_info` | Required `server_identifier` | Inspect one server's visible ports, fixed IPs, networks, and subnets. |

The revised runtime identity is `/opt/openstack-ai-ops-assistant`. The accepted project-reader profile is `aiops-assistant-project-reader`. Callers cannot override the runner's executable, registry, profile, environment, working directory, timeout, output limit, audit path, or correlation identity.

`server_identifier` must be a safe name or ID matching `^[A-Za-z0-9._:-]+$` and must not exceed 255 characters. The same identifier must be used for both server workflows.

The following are not available through this MVP workflow:

- generic shell or raw OpenStack CLI passthrough;
- create, update, delete, restart, stop, install, edit, or repair tools;
- SSH, sudo, database, file, or message-bus access;
- Neutron-agent health and host-level diagnostics;
- recent Nova, Neutron, metadata-agent, Apache, or system logs;
- host status or listener checks, including Nova metadata listener port `8775`;
- MCP, chat UI, automatic AI tool calling, or autonomous remediation.

## Refusal behavior for remediation intent

For requests such as “fix it,” “restart it,” “delete it,” “create it,” “edit the config,” “run this command,” or “SSH into the host,” the assistant must:

1. refuse direct execution and mutation;
2. state that the MVP is diagnostic-only;
3. offer only approved read-only evidence collection by exact tool name, when useful;
4. explain supplied evidence using the required structure;
5. recommend manual operator follow-up without claiming that it was executed.

Suggested response:

> I cannot mutate OpenStack resources, restart services, edit configuration, SSH to hosts, run shell commands, or perform remediation in this diagnostic-only workflow. I can interpret approved runner results and suggest manual next steps. Any manual action remains an operator decision and has not been executed by AI-OPS.

A refusal must not be converted into a raw command, an invented tool request, or a broader credential request.

## Evidence handling rules

- Share only the minimum necessary redacted result envelope with an approved AI client.
- Do not share credential profiles, tokens, passwords, environment values, raw audit logs, private keys, or unredacted live output.
- Treat project identifiers and topology as potentially sensitive; use fake or pseudonymized values in committed examples.
- Preserve each result's tool, status, correlation identity, duration, truncation state, and relevant section status.
- Interpret `empty` as no records visible in the current scope, not proof of global absence.
- Interpret `unavailable`, `timeout`, `error`, and `truncated` as evidence gaps or bounded failures.
- Do not combine results from different server identifiers or unrelated requests as one observation.

## Documented workflow sections

### Project resource summary workflow

**Status:** documented for Chunk 2; live execution remains outside Steps 1–3.

Use this workflow when the question is what the current project-reader can see. It establishes project-scoped visibility; it does not establish cloud-wide inventory, service health, guest health, or remediation capability.

#### Runner-first procedure

1. Confirm that the operator supplied a question that can be answered with project-visible read-only evidence.
2. Use only the fixed runner path and interface:

   ```text
   /opt/openstack-ai-ops-assistant/scripts/tool_runner/aiops_tool_runner.py project_resource_summary
   ```

   The accepted CLI shape is `aiops_tool_runner.py TOOL_NAME [--arg KEY=VALUE ...]`. Do not call the approved shell target directly, add flags, select a profile, alter the environment, or bypass the runner.
3. Preserve the redacted result's `tool`, top-level `status`, `correlation_id`, `duration_ms`, `timestamp`, and `truncated` fields before sharing minimum necessary evidence with an approved AI client.
4. Inspect each returned section independently: `servers`, `networks`, `subnets`, `ports`, `volumes`, `images`, and `security_groups`.
5. Report visible records using only the fields supplied by the result. If a visible server needs deeper inspection, select one safe returned name or ID and use the later server workflow; never guess or interpolate an identifier.
6. End with the required explanation structure and unexecuted manual recommendations. Do not claim that any change was made.

#### Result interpretation

| Result state | Interpretation and response |
| --- | --- |
| Top-level `ok`, section `ok` | The named project-scoped read completed and returned visible data. Describe only those records; do not infer health outside the project-reader boundary. |
| Section `empty` | No records were returned in that section under the current profile and scope. This is not proof that the resource type is globally absent. |
| Section `unavailable` | That section could not be read. Preserve its normalized error class as an evidence gap and interpret other independent sections separately. |
| Section error class `policy_denied` | The current project-reader policy did not permit that section. Do not request broader credentials or suggest a bypass in Steps 1–3. |
| Top-level `unavailable` | The approved target, profile, endpoint, or service class was unavailable. Do not bypass the runner or convert the result to an empty finding. |
| Top-level `error` or a failed section | The request or section did not produce accepted successful evidence. Preserve only the normalized public error; do not infer absence or health from failure. |
| Top-level `denied` or `validation_error` | No diagnostic evidence was collected. Correct only the named-tool request or its validated arguments; do not broaden capability. |
| Top-level `timeout` | Completion is unknown. Treat partial or absent data as unaccepted evidence and recommend an operator-controlled retry only if appropriate. |
| `truncated: true` at envelope or section level | Reason only from retained records and state that omitted evidence may change the conclusion. |

Mixed results must remain mixed. For example, `servers: ok`, `networks: empty`, and `subnets: unavailable` describe three different evidence states, not one project health status.

#### Explanation template

Use this compact structure when interpreting a supplied result:

```text
Observed evidence: [tool, status, correlation ID, duration, truncation, and relevant section records/statuses].
Healthy signals: [only affirmative signals directly present in the retained project-scoped data].
Failing signals: [failed, unavailable, denied, empty, contradictory, or truncated sections].
Inference and likely failure domain: [bounded hypothesis, explicitly labeled as an inference].
Missing or unavailable evidence: [scope, policy, timeout, truncation, or deferred host/service/guest data].
Manual recommendations: [unexecuted operator follow-up only].
```

#### Sanitized fixtures

The following fixtures use invented identifiers and timestamps. They are documentation examples only, not live acceptance evidence.

**Success with visible project sections:**

```json
{"schema_version":"1.0","tool":"project_resource_summary","status":"ok","arguments":{},"exit_code":0,"data":{"schema_version":"1.0","tool":"project_resource_summary","status":"ok","sections":[{"name":"servers","status":"ok","data":[{"id":"fake-server-01","name":"demo-server","status":"ACTIVE"}],"error":null,"truncated":false},{"name":"networks","status":"ok","data":[{"id":"fake-network-01","name":"demo-net","status":"ACTIVE"}],"error":null,"truncated":false},{"name":"subnets","status":"empty","data":[],"error":null,"truncated":false}],"error":null},"stdout":null,"stderr":null,"error":null,"duration_ms":42,"truncated":false,"timestamp":"2030-01-02T03:04:05Z","correlation_id":"00000000-0000-4000-8000-000000000101"}
```

Interpret this as one visible server and network, no visible subnet records in the current scope, and no evidence about resources or services outside the retained sections.

**Successful read with an empty section:**

```json
{"schema_version":"1.0","tool":"project_resource_summary","status":"ok","arguments":{},"exit_code":0,"data":{"schema_version":"1.0","tool":"project_resource_summary","status":"ok","sections":[{"name":"servers","status":"empty","data":[],"error":null,"truncated":false},{"name":"volumes","status":"empty","data":[],"error":null,"truncated":false}],"error":null},"stdout":null,"stderr":null,"error":null,"duration_ms":18,"truncated":false,"timestamp":"2030-01-02T03:04:06Z","correlation_id":"00000000-0000-4000-8000-000000000102"}
```

Interpret this as no servers or volumes visible to this project-reader at that time, not as proof that the deployment has no servers or volumes globally.

**Successful envelope with an unavailable, policy-limited section:**

```json
{"schema_version":"1.0","tool":"project_resource_summary","status":"ok","arguments":{},"exit_code":0,"data":{"schema_version":"1.0","tool":"project_resource_summary","status":"ok","sections":[{"name":"servers","status":"ok","data":[{"id":"fake-server-02","name":"limited-demo","status":"SHUTOFF"}],"error":null,"truncated":false},{"name":"security_groups","status":"unavailable","data":null,"error":{"class":"policy_denied","message":"Project-reader policy does not permit this section."},"truncated":false}],"error":null},"stdout":null,"stderr":null,"error":null,"duration_ms":27,"truncated":false,"timestamp":"2030-01-02T03:04:07Z","correlation_id":"00000000-0000-4000-8000-000000000103"}
```

Interpret this as a visible server plus a security-group evidence gap. Do not claim that no security groups exist and do not ask for broader credentials. A failed top-level result, such as `status: "error"`, is likewise an evidence gap rather than an empty project.

### Single-server inspection workflow

**Status:** documented for Chunk 3; live execution remains outside Steps 1–3.

Use this workflow only after obtaining one safe, project-visible server name or ID from accepted project-summary evidence. It inspects one server and its project-visible network relationships; it does not establish guest health or metadata-service health.

#### Runner-first procedure

1. Select exactly one returned server name or ID from `project_resource_summary`. Do not guess, interpolate, copy an unsafe value, or use an identifier from an unrelated result.
2. Confirm that `server_identifier` is at most 255 characters and matches `^[A-Za-z0-9._:-]+$`. No spaces, slashes, shell metacharacters, extra arguments, or flags are allowed.
3. Request basic server evidence through the fixed runner:

   ```text
   /opt/openstack-ai-ops-assistant/scripts/tool_runner/aiops_tool_runner.py server_basic_info --arg server_identifier=demo-server
   ```

4. If the basic result identifies the requested server, request network evidence through the same runner using the exact same identifier:

   ```text
   /opt/openstack-ai-ops-assistant/scripts/tool_runner/aiops_tool_runner.py server_network_info --arg server_identifier=demo-server
   ```

   Do not call approved scripts directly, use raw OpenStack commands, change the profile, add flags, or substitute a second server identifier.
5. Preserve each redacted envelope's `tool`, `status`, `correlation_id`, `duration_ms`, `timestamp`, and `truncated` fields. Treat the two calls as separate evidence while checking that their validated identifiers match.
6. Correlate the `server` section from `server_basic_info` with `ports`, `networks`, and `subnets` from `server_network_info`. Use only returned fields: server identity/status, image, flavor, addresses, availability zone, `config_drive`, creation context, port IDs and fixed IPs, network IDs/names/statuses, and subnet IDs/names/CIDRs/IP versions.
7. Explain healthy signals, failing signals, discrepancies, and missing evidence. End with manual, unexecuted recommendations only.

#### Interpretation and non-proofs

- A visible `ACTIVE` status is a project-control-plane signal only. It does not prove guest health, cloud-init success, guest routes, packet delivery, metadata reachability, Neutron metadata-proxy or agent health, Nova metadata API health, listener health, or service-log health.
- `config_drive` is context. Its presence or value does not prove that HTTP metadata requests work or that cloud-init completed.
- A visible port, fixed IP, network, or subnet establishes project-visible attachment evidence only. It does not prove that the guest can route to or reach those resources.
- A missing, empty, unavailable, failed, or truncated section is an evidence gap. Preserve discrepancies rather than filling them with assumptions.
- `server_network_info` is bounded to the requested server and its validated attached-port, network, and subnet relationships. It is not a project-wide topology or host-health query.
- If `server_basic_info` fails, is denied, times out, or identifies no accepted server, do not continue by guessing. If the network result fails or uses a different identifier, do not correlate it with the basic result.

#### Explanation template

Use this compact structure for a supplied pair of results:

```text
Observed evidence: [both tool names, identifiers matched, statuses, correlation IDs, durations, truncation, and returned server/network fields].
Healthy signals: [only project-scoped status, identity, config-drive context, and attachment signals directly present].
Failing signals: [not-found, denied, unavailable, timeout, failed, empty, contradictory, or truncated fields].
Inference and likely failure domain: [bounded hypothesis tied to the evidence; do not claim guest, metadata, host, or service health].
Missing or unavailable evidence: [guest behavior, routes, packet delivery, metadata path, agents, listeners, logs, or other gaps].
Manual recommendations: [unexecuted operator follow-up only].
```

#### Sanitized fixtures

These fixtures use invented identifiers, addresses, timestamps, and correlation IDs. They are documentation examples only and must not be treated as live evidence.

**Success: same identifier with coherent project-visible evidence:**

```json
{"schema_version":"1.0","tool":"server_basic_info","status":"ok","arguments":{"server_identifier":"demo-server"},"exit_code":0,"data":{"schema_version":"1.0","tool":"server_basic_info","status":"ok","sections":[{"name":"server","status":"ok","data":{"id":"fake-server-01","name":"demo-server","status":"ACTIVE","image":"fake-image","flavor":"fake-flavor","addresses":{"demo-net":[{"addr":"192.0.2.15","version":4}]},"availability_zone":"fake-zone","config_drive":true,"created":"2030-01-02T03:00:00Z"},"error":null,"truncated":false}],"error":null},"stdout":null,"stderr":null,"error":null,"duration_ms":42,"truncated":false,"timestamp":"2030-01-02T03:04:10Z","correlation_id":"00000000-0000-4000-8000-000000000201"}
```

```json
{"schema_version":"1.0","tool":"server_network_info","status":"ok","arguments":{"server_identifier":"demo-server"},"exit_code":0,"data":{"schema_version":"1.0","tool":"server_network_info","status":"ok","sections":[{"name":"server","status":"ok","data":{"id":"fake-server-01","name":"demo-server","status":"ACTIVE"},"error":null,"truncated":false},{"name":"ports","status":"ok","data":[{"id":"fake-port-01","network_id":"fake-network-01","fixed_ips":[{"ip_address":"192.0.2.15","subnet_id":"fake-subnet-01"}],"mac_address":"02:00:00:00:00:01","status":"ACTIVE"}],"error":null,"truncated":false},{"name":"networks","status":"ok","data":[{"id":"fake-network-01","name":"demo-net","status":"ACTIVE"}],"error":null,"truncated":false},{"name":"subnets","status":"ok","data":[{"id":"fake-subnet-01","name":"demo-subnet","cidr":"192.0.2.0/24","ip_version":4}],"error":null,"truncated":false}],"error":null},"stdout":null,"stderr":null,"error":null,"duration_ms":38,"truncated":false,"timestamp":"2030-01-02T03:04:11Z","correlation_id":"00000000-0000-4000-8000-000000000202"}
```

Interpret these together as coherent project-visible control-plane identity and attachment evidence for `demo-server`. Do not extend that conclusion to guest routes, packet delivery, cloud-init, or metadata services.

**Non-success: basic evidence accepted, network evidence unavailable:**

```json
{"schema_version":"1.0","tool":"server_network_info","status":"unavailable","arguments":{"server_identifier":"demo-server"},"exit_code":5,"data":null,"stdout":null,"stderr":null,"error":{"class":"service_unavailable","message":"Approved network diagnostic is unavailable."},"duration_ms":24,"truncated":false,"timestamp":"2030-01-02T03:04:12Z","correlation_id":"00000000-0000-4000-8000-000000000203"}
```

Preserve the basic result if it was accepted, but report network relationships as unavailable. Do not infer that the server has no ports or networks, do not retry with another identifier, and do not claim a root cause. A `not_found`, `policy_denied`, `validation_error`, `timeout`, or `truncated: true` result is likewise a bounded evidence gap, not proof of guest or service failure.

### Metadata troubleshooting workflow

**Status:** documented for Chunk 4; live execution and AI behavior testing remain outside Steps 1–3.

Use this workflow when an operator reports a cloud-init symptom or a request failure involving `169.254.169.254`. The report is context supplied by the operator, not a tool-observed fact unless accepted evidence explicitly contains it. The workflow produces a bounded initial evidence package; it does not prove the complete metadata path or authorize remediation.

#### Bounded evidence sequence

1. Run `project_resource_summary` through the fixed runner to establish current project visibility and select one safe, visible server.
2. Run `server_basic_info` for that exact `server_identifier` to inspect identity, lifecycle status, addresses, and `config_drive` context.
3. Run `server_network_info` for the same exact identifier to inspect attached ports, fixed IPs, related networks, and related subnets.
4. Preserve each redacted envelope's status, correlation ID, duration, timestamp, truncation state, and section-level errors. Stop narrowing the analysis when a required envelope or section is unavailable, failed, timed out, denied, or truncated.
5. Correlate only the accepted project-visible evidence against this architectural path:

   ```text
   guest cloud-init
     -> guest request to 169.254.169.254
     -> Neutron metadata proxy / metadata agent
     -> Nova metadata API
     -> metadata response
   ```

6. Explain which parts of the path are supported by evidence, which are hypotheses, and which remain unavailable. End with manual operator recommendations only.

The runner-first calls are conceptually:

```text
/opt/openstack-ai-ops-assistant/scripts/tool_runner/aiops_tool_runner.py project_resource_summary
/opt/openstack-ai-ops-assistant/scripts/tool_runner/aiops_tool_runner.py server_basic_info --arg server_identifier=demo-server
/opt/openstack-ai-ops-assistant/scripts/tool_runner/aiops_tool_runner.py server_network_info --arg server_identifier=demo-server
```

These are fixed runner interfaces, not instructions to call scripts directly or to execute raw commands. The identifier shown is invented and must be replaced only with a validated identifier returned by the first accepted result.

#### Evidence-to-domain interpretation

| Observed pattern | Bounded interpretation |
| --- | --- |
| Server is absent, ambiguous, non-running, or not project-visible | A lifecycle, identifier, or project-scope issue must be resolved before narrowing the metadata path. Do not infer a proxy or Nova failure. |
| Server is visible but has no visible attached port, fixed IP, network, or subnet context | A project-visible attachment or visibility issue is plausible. Guest-to-proxy reachability is not established. |
| Server status, `config_drive`, and attachments are coherent | Project-level control-plane evidence is coherent. Guest behavior, proxy/agent state, Nova metadata, listeners, logs, and packet delivery remain unverified. |
| Any required result or section is unavailable, failed, denied, timed out, or truncated | Evidence is insufficient at that point. Preserve the exact gap and avoid a definitive root-cause claim. |
| `config_drive` is present or enabled | Report it as context only. It does not prove cloud-init completion or HTTP metadata reachability. |
| Operator reports a cloud-init or `169.254.169.254` symptom without matching tool evidence | Label it as an operator report. Do not present it as an observed guest or service failure. |

#### Explicit Phase 06 evidence boundary

The following evidence is unavailable in Steps 1–3 unless separately supplied through an approved channel. It must not be invented, inferred as observed, or requested through an unapproved tool:

| Evidence gap | Required wording boundary |
| --- | --- |
| Guest console, route table, packet delivery, cloud-init logs, or in-guest HTTP result | Not observed by the project-reader workflow; guest-side failure remains a hypothesis only. |
| Neutron metadata-agent or metadata-proxy state | Not available; project-visible attachments do not establish agent or proxy health. |
| Neutron agent health beyond project-visible attachment data | Not available; do not request host or agent diagnostics. |
| Nova metadata API response, Apache state, or listener evidence including port `8775` | Not available; do not claim the service or listener is healthy or failed. |
| Recent Neutron, Nova, metadata-agent, Apache, or system logs | Not approved in Phase 06; do not paste or request raw logs. |
| Controller/compute host status and service state | Not available through the three approved tools. |

#### Explanation template

Use this structure for the metadata-oriented response:

```text
Observed evidence: [operator-reported symptom separately labeled; project, server, and network tool results with identifiers, statuses, correlation IDs, truncation, and relevant fields].
Healthy signals: [project-visible server status, config-drive context, and attachment signals directly supported by results].
Failing signals: [missing server, absent attachment, unavailable section, failed/denied/timeout result, contradiction, or truncation].
Inference and likely failure domain: [guest-side, project-visible attachment, proxy/service hypothesis, or insufficient evidence; label every hypothesis].
Missing or unavailable evidence: [guest, route/packet, Neutron-agent/proxy, Nova metadata, listener, host, and log gaps from the Phase 06 boundary].
Manual recommendations: [unexecuted operator follow-up, such as reviewing separately approved evidence; no executable remediation request].
```

A bounded conclusion may say: “The fake server `demo-server` is `ACTIVE` with project-visible attachment evidence on `demo-net`. This supports coherent control-plane visibility only. The reported metadata symptom remains unresolved because guest behavior, Neutron metadata-proxy state, Nova metadata API response, listener state, and logs were not observed.” This is an interpretation of supplied evidence, not a present-state claim about any real server.

This workflow must not claim that the historical metadata incident is the current cause. It must not suggest restarting services, editing configuration, changing routes, entering a guest, querying hosts, or requesting broader credentials. Any such action remains a separate manual operator decision.

## Cross-workflow acceptance matrix

| Contract area | Project summary | Single-server inspection | Metadata troubleshooting | Evidence status |
| --- | --- | --- | --- | --- |
| Approved tools | `project_resource_summary` | `server_basic_info`, `server_network_info` | All three in project → basic → network order | Static documentation complete; no live execution |
| Argument boundary | No arguments | One safe `server_identifier` | Reuses the same validated identifier | Runner-only interface documented |
| Evidence handling | Section-level `ok`, `empty`, `unavailable`, failure, and truncation semantics | Same-identifier correlation and attachment limits | Operator symptom separated from tool evidence; Phase 06 gaps preserved | Fake fixtures and templates reviewed |
| Explanation | Observed evidence, healthy/failing signals, inference, gaps, manual recommendations | Adds status, `config_drive`, ports, fixed IPs, networks, and subnets | Adds guest → Neutron → Nova path and insufficient-evidence outcome | Diagnostic-only and non-remediation language present |
| Safety boundary | Redacted minimum disclosure and no bypass | No raw scripts, flags, or alternate identifiers | No host access, logs, listener checks, credentials, or executable remediation | Static review only |

This matrix records documentation evidence only. It does not claim that the runner, audit events, deployed lab, or AI behavior have been validated.

## Implementation and acceptance boundary

Completion of this policy documentation does not establish that a deployed lab was validated, that an AI client was tested, or that the Phase 05 definition of done was met. Those claims require the later Phase 05 steps and separate evidence.

Steps 4–6, live validation, AI-provider interaction, and the remaining Phase 05 acceptance claims are intentionally outside this chunk.
