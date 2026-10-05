# Phase D — Production safety

## Need

Shared development keys and namespace filtering are insufficient when multiple
users or agents share a service. Access must be authorized, bounded, and
auditable.

## Plan

- Map API keys to tenant IDs and enforce tenant ownership in storage/search.
- Audit authenticated reads as well as memory mutations.
- Limit request size and request rate.
- Preserve export/import as the first backup/restore path.
- Add PostgreSQL, audit UI, CI, release automation, and security scanning as
  the deployment matures.

## Status

Baseline implemented:

- `ATTIC_TENANT_KEYS` provides per-tenant API keys.
- SQLite and vector searches are tenant-scoped.
- Content and webhook idempotency are tenant-scoped.
- Requests and mutations are written to the audit log.
- Request size and fixed-window rate limits are configurable.
- Existing export/import provides a portable backup path.

See [security contract](../phase-d-security.md) for configuration and rollback
notes.

## Acceptance

```sh
python3 scripts/phase_d_test.py
```

Two tenants can store identical content and event IDs without reading each
other’s memories or audit records.

## Remaining

PostgreSQL storage, a dedicated audit UI, and CI/release/security automation
are intentionally separate follow-up work.
