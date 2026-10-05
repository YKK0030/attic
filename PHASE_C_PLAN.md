# Attic Phase C — Universal Integrations

Status: core endpoints implemented; live/framework validation remains. Phase A/B
remain regression gates for every Phase C change.

## Goal

Let agent runtimes use Attic through stable contracts without writing database
integration code.

## Current baseline

- REST API: implemented, currently unversioned (`/memory`, `/recall`, `/ask`).
- Python client: implemented.
- JavaScript client: implemented.
- MCP server: implemented with `remember`, `recall`, and `ask`.
- Conversation ingestion, webhooks, and an OpenAI-compatible tool schema:
  implemented under `/v1`.
- Five thin integration examples: documented in `docs/phase-c-integrations.md`.

## Delivery order

1. ~~Version the REST contract (`/v1`) while preserving existing routes.~~
2. ~~Add an OpenAI-compatible memory tool definition and handler.~~
3. ~~Add conversation ingestion with one normalized message format.~~
4. ~~Add API-key-protected webhook ingestion with replay-safe IDs.~~
5. ~~Add thin examples for five agent runtimes, reusing the clients.~~

Avoid separate storage or business logic per framework; adapters should call
the stable REST/MCP/client contracts.

## Acceptance

- Five agent runtimes can remember and recall without custom database code.
- Existing unversioned routes and Python/JavaScript/MCP clients keep working.
- Conversation and webhook writes are idempotent and preserve source metadata.
- Tool responses include memory IDs, citations, namespace, and lifecycle state.
- Offline and live verification commands below pass.

## Repeatable verification

Run from the repository root:

```sh
python3 scripts/regression_test.py
```

This runs Phase A, Phase B (including the actual context string budget),
provider contracts, and Python compilation. When the local service is running,
also run:

```sh
python3 scripts/smoke_test.py
```

The live test is environment-dependent and may require Ollama, Qdrant, and the
API deployment.
