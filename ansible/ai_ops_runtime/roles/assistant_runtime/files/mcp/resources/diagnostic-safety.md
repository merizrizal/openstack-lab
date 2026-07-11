# Diagnostic Safety Policy

## Purpose

The OpenStack AI-OPS interface is diagnostic-only. It provides bounded, read-only evidence through explicitly reviewed tools and does not perform repair or administration.

## Approved Interface

The initial interface exposes only:

- `project_resource_summary` for project-visible inventory context;
- `server_basic_info` for basic evidence about one reviewed server identifier; and
- `server_network_info` for network evidence about that same server identifier.

Tool execution remains behind the local runner. The runner owns argument validation, timeouts, output limits, result envelopes, and audit correlation. MCP is an interface to that boundary, not a replacement for it.

## Required Evidence Handling

Preserve each result's status, request ID, and truncation state. Treat `unavailable`, `timeout`, and `truncated` results as evidence gaps rather than healthy signals. Explain confirmed healthy signals, failing or missing signals, the likely failure domain, unresolved gaps, and manual next steps.

## Prohibited Capabilities

The interface does not expose mutation, remediation, arbitrary file access, command generation, generic shell or SSH, unrestricted sudo, raw OpenStack CLI passthrough, database access, service control, package changes, or configuration edits. Do not invent tools or claim that a recommended manual action was executed.

Credentials, keys, tokens, audit lines, raw diagnostic payloads, and secret-like values must not be placed in prompts or shared resource content.
