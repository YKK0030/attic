# Attic — Build TODO

## Working slice
- [x] FastAPI app with `/health`, `/memory`, `/recall`
- [x] SQLite persistence and namespace isolation
- [x] SHA-256 deduplication
- [x] Markdown/text ingestion CLI
- [x] Docker Compose API service
- [x] Qdrant vector storage and Ollama embeddings
- [x] Ollama grounded `/ask` RAG endpoint
- [x] `DELETE /memory/{id}`
- [x] `/surface` cross-source connections
- [x] Static memory web console
- [x] MCP tools: remember, recall, ask
- [x] Agent integration examples
- [x] URL clip and local Whisper CLI adapters
- [x] Configurable Ollama/OpenAI/Claude/Voyage provider adapters
- [x] Notion database pull adapter (env-configured)
- [x] Weekly connection-surfacing scheduler
- [x] PDF parser and end-to-end ingestion pipeline
- [x] CLI namespace/tag/limit options and status command
- [x] Obsidian vault watcher
- [x] Setup script and live smoke tests
- [x] Namespace-aware web console
- [x] Generic Python and JavaScript agent clients
- [x] Universal REST/MCP integration guide

## Remaining verification
- [x] Phase B baseline: hybrid retrieval, filters, citations, context budgets, reindex endpoint
- [x] Phase B offline acceptance test
- [x] Phase A: lifecycle fields, provenance, audit log, update/approve/reject/supersede, export/import
- [x] Provider contract tests without cloud credentials
- [ ] Optional live external-provider test when credentials are configured

## Phase C — Universal integrations
- [x] Version REST routes without breaking existing clients
- [x] OpenAI-compatible memory tool schema and endpoint
- [x] Normalized conversation ingestion
- [x] Replay-safe webhook ingestion
- [x] Five thin framework integration examples
- [x] Add Phase C contract checks to `scripts/regression_test.py`

## Recurring verification
- [ ] Run `python3 scripts/regression_test.py` after every change
- [ ] Run `python3 scripts/smoke_test.py` when API, Qdrant, and Ollama are running
- [ ] Keep the Phase B context payload-length assertion green
- [ ] Keep `python3 scripts/phase_c_test.py` green

## Phase D — Production safety
- [x] Tenant-scoped API keys and SQLite isolation
- [x] Tenant-scoped idempotency and audit records
- [x] Request-size limit and rate limit middleware
- [x] Export/import backup path
- [ ] PostgreSQL storage option
- [ ] Dedicated audit UI
- [ ] CI release and security scanning
