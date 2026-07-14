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

It must never retain or display prompts, request or response bodies, headers,
authorization values, provider URLs, account data, exception text, or raw
ledger lines.

## Retrieve Parsed Metadata Only

Use a privileged local terminal on `assistant01`. Do **not** use `cat`,
`less`, `tail`, copy/paste, screenshot, upload, or publish the ledger or any
raw line. Run this reviewed parser exactly; it rejects records with fields
outside the allowlist and prints only approved parsed metadata.

```bash
sudo -u aiops-provider /usr/bin/python3 - /var/lib/aiops-provider-gateway/gateway-evidence.jsonl <<'PY'
import json
import sys
from pathlib import Path

allowed = frozenset({
    "classification_status", "correlation_id", "model", "outcome",
    "redaction_counts", "route", "schema_version", "timestamp_utc",
    "tls_verified", "upstream_status_class",
})
path = Path(sys.argv[1])
try:
    records = path.read_text(encoding="utf-8").splitlines()
except OSError:
    raise SystemExit("ledger is unavailable") from None
for record in records:
    try:
        event = json.loads(record)
    except (TypeError, ValueError):
        raise SystemExit("ledger contains an invalid record") from None
    if not isinstance(event, dict) or frozenset(event) != allowed:
        raise SystemExit("ledger contains an unapproved record")
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

With explicit approval, stop `aiops-provider-gateway` before removing the
ledger artifact or reversing the service-unit deployment. Confirm the
loopback listener, direct-egress policy, and service sandbox remain within
the provider-boundary contract after rollback. This runbook does not approve
provider requests, manual authentication, credential inspection, or remote
synthetic acceptance.
