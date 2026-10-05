# Phase D security contract

## Tenant keys

Set an explicit key-to-tenant map in deployment configuration:

```sh
ATTIC_TENANT_KEYS='{"team-a":"secret-a","team-b":"secret-b"}'
```

Each key can read, write, export, and delete only its tenant’s memories. The
legacy single `ATTIC_API_KEY` remains the default-tenant fallback when the map
is not configured.

## Runtime controls

- `ATTIC_MAX_REQUEST_BYTES` defaults to 1 MiB.
- `ATTIC_RATE_LIMIT` defaults to 120 requests.
- `ATTIC_RATE_WINDOW_SECONDS` defaults to 60 seconds.
- Authenticated requests are written to `audit_log`; memory mutations retain
  their detailed audit entries.
- SQLite stores tenant ownership and uses tenant-scoped content and
  idempotency uniqueness.

## Verification and rollback

Run `python3 scripts/regression_test.py`. The Phase D gate proves two tenants
can store identical content and event IDs without seeing each other’s memory
or audit history.

Rollback is configuration-safe: remove `ATTIC_TENANT_KEYS` to return to the
legacy default tenant. The tenant column and audit records are additive and
must remain in the database.

Not included in this slice: PostgreSQL storage, a separate audit UI, and CI
provider wiring. Export/import remains the current backup/restore path.
