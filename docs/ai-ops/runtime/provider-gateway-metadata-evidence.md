# Provider Gateway Metadata Evidence Runbook

## Scope

This runbook applies only to the local evidence ledger written by
`aiops-provider-gateway` on `assistant01`. The ledger is sensitive metadata,
not a general log, and is not an API, audit stream, or provider acceptance
record by itself.

- Ledger path: `/var/lib/aiops-provider-gateway/gateway-evidence.jsonl`
- Owner: `aiops-provider`
- Directory mode: `0700`
- Ledger mode: `0600`
- Retention: fixed 64 KiB maximum; no automatic deletion or rotation

The ledger must contain only these parsed fields:

- `schema_version`, `timestamp_utc`, `correlation_id`, `model`, and `route`
- `classification_status` and `redaction_counts`
- `outcome`, `upstream_status_class`, and `tls_verified`

## Schema and Route Contract

The parser accepts only these schema/route pairs:

| Schema | Route | Meaning |
| --- | --- | --- |
| `1` | `/v1/responses` | Historical API-key-oriented gateway record; preserve and do not relabel. |
| `2` | `/backend-api/codex/responses` | Current ChatGPT/device-auth gateway record. |

New gateway events use schema 2 only. A mixed ledger is expected during migration;
do not rewrite, delete, truncate, rotate, or migrate historical schema 1 records.
Any unknown schema or mismatched schema/route pair is an evidence-policy failure:
stop review, preserve the ledger in place, and escalate.

It must never retain or display prompts, request or response bodies, headers,
authorization values, provider URLs, account data, exception text, or raw
ledger lines.

## Retrieve Parsed Metadata Only

Use a privileged local terminal on `assistant01`. Do **not** use `cat`,
`less`, `tail`, copy/paste, screenshot, upload, or publish the ledger or any
raw line. Run this reviewed parser exactly; it rejects records with fields
outside the allowlist and prints only approved parsed metadata.

```bash
rtk sudo -u aiops-provider /usr/bin/python3 - /var/lib/aiops-provider-gateway/gateway-evidence.jsonl <<'PY'
import json
import sys
from pathlib import Path

allowed = frozenset({
    "classification_status", "correlation_id", "model", "outcome",
    "redaction_counts", "route", "schema_version", "timestamp_utc",
    "tls_verified", "upstream_status_class",
})
schema_routes = {
    1: "/v1/responses",
    2: "/backend-api/codex/responses",
}

def unique_mapping(pairs):
    event = {}
    for key, value in pairs:
        if key in event:
            raise ValueError("duplicate key")
        event[key] = value
    return event

path = Path(sys.argv[1])
try:
    records = path.read_text(encoding="utf-8").splitlines()
except OSError:
    raise SystemExit("ledger is unavailable") from None
for record in records:
    try:
        event = json.loads(record, object_pairs_hook=unique_mapping)
    except (TypeError, ValueError):
        raise SystemExit("ledger contains an invalid record") from None
    schema = event.get("schema_version") if isinstance(event, dict) else None
    if (
        not isinstance(event, dict)
        or frozenset(event) != allowed
        or isinstance(schema, bool)
        or not isinstance(schema, int)
        or event["route"] != schema_routes.get(schema)
    ):
        raise SystemExit("ledger contains an unapproved schema or route")
    print(json.dumps({key: event[key] for key in sorted(allowed)}, sort_keys=True))
PY
```

Record only the approved fields needed for the reviewed acceptance checklist.
Do not place terminal output, raw records, or derived data in repository
files. If a record is invalid or contains an unexpected field, stop evidence
review, preserve the ledger in place, and escalate through the incident
process.

## Retention and Failure Handling

The gateway fails closed when it cannot create, validate, lock, append, or
sync the ledger, or when the 64 KiB bound is reached. It returns the sanitized
`ERR_GATEWAY_EVIDENCE` response and must not forward a new request upstream.

Do not delete, truncate, rotate, or repair the ledger to restore service.
Stop the gateway and obtain explicit approval before any preservation or
rollback action. Never remove authentication state, runtime-home data, or
unrelated system logs as part of this procedure.

## Rollback

With explicit approval, disable remote selection and stop
`aiops-provider-gateway` if required before reversing a service deployment.
Preserve the ledger in place, including mixed schema 1 and schema 2 records;
rollback must not delete, truncate, relabel, or resume schema 1 provider
traffic. Confirm the loopback listener, direct-egress policy, and service
sandbox remain within the provider-boundary contract after rollback. This
runbook does not approve provider requests, manual authentication, credential
inspection, or remote synthetic acceptance.
