# Metadata Troubleshooting Context

## Symptom and Request Path

A guest metadata failure can appear as cloud-init receiving an HTTP 503 from `169.254.169.254`. In this lab, the conceptual request path is guest cloud-init, Neutron metadata proxy or agent, Nova metadata API, then the instance metadata response.

A prior lab incident showed that healthy general Nova and Neutron service state did not prove metadata-path health. The failure domain was the Nova metadata endpoint behind the proxy path. This history is context only; do not assume a new incident has the same cause.

## Safe Evidence Order

1. Use `project_resource_summary` to confirm project-visible inventory and locate the target server.
2. Use `server_basic_info` with the exact reviewed `server_identifier`.
3. Use `server_network_info` with the same identifier.
4. Separate confirmed server and attachment evidence from metadata-path evidence that these tools cannot observe.

A visible active server, expected ports, fixed IPs, or config-drive clues do not prove that guest metadata is healthy. Missing or partial network evidence may indicate an attachment issue, a project-scope mismatch, or a permission boundary.

## Interpretation

Preserve the status, request ID, and truncation state for every result. Report `validation_error`, `timeout`, `unavailable`, and `truncated` states without broadening access or guessing. Explain healthy signals, failing signals, the likely failure domain, evidence gaps, and manual operator follow-up.

Restricted-host diagnostics are not part of the initial MCP surface. If API evidence cannot localize the metadata path, state that listener, proxy-log, and service-log evidence remains unavailable through the exposed tools. Do not provide host commands, raw logs, secret-bearing configuration, remediation steps, or claims that a fix was executed.
