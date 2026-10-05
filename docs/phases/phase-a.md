# Phase A — Trustworthy core

## Need

Agents need durable memory that can be inspected, corrected, invalidated, and
exported. A vector hit without lifecycle or provenance is not trustworthy
evidence.

## Plan

- Store facts, documents, conversations, events, and preferences with memory
  types.
- Track valid time, confidence, source URI, agent, user, status, and
  supersession.
- Support update, approve, reject, supersede, forget, audit, export, and
  import operations.
- Keep writes idempotent through content hashes.

## Status

Implemented in the SQLite runtime and REST API. The source of truth is
`apps/api/attic_api/db.py`; lifecycle behavior is in `core.py`.

## Acceptance

```sh
python3 scripts/phase_a_test.py
```

A user can inspect why a memory exists, change it, invalidate it, supersede it,
and export/import it.
