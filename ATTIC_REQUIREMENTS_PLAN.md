# Attic — Product Requirements and Build Plan

Date: 2026-10-05  
Status: prototype review → production-ready open-source memory layer

## 1. Product decision

Attic should not compete as another all-in-one chat workspace.

**Positioning:**

> Attic is a local-first, open-source memory operating system for AI agents.

Attic stores durable facts, conversations, documents, decisions, and preferences. Any model, agent, framework, or UI can use the same memory through REST, MCP, Python, or JavaScript.

## 2. Research summary

Competitors already cover broad assistant experiences:

- [AnythingLLM](https://docs.anythingllm.com/features/all-features) provides workspaces, RAG, agents, APIs, memories, model routing, and private deployment.
- [Open WebUI](https://docs.openwebui.com/features/) provides chat, uploads, hybrid search, reranking, knowledge bases, tools, agents, automations, permissions, and multiple model providers.
- [Khoj](https://github.com/khoj-ai/khoj) provides personal AI over documents and web sources, custom agents, automations, and many interfaces.
- [Letta](https://www.letta.com/) focuses on stateful agents, tools, and persistent memory managed by the agent runtime.
- [Zep](https://help.getzep.com/v3/overview) focuses on temporal context graphs, context assembly, governance, and agent memory.
- [Mem0](https://docs.mem0.ai/) provides persistent memory across sessions, tools, and runs with SDKs, integrations, compression, and observability.
- [LlamaIndex](https://developers.llamaindex.ai/python/framework/) is a framework for data ingestion, RAG, agents, tools, evaluation, and structured extraction.
- [Dify](https://docs.dify.ai/en/home) targets AI applications, knowledge bases, workflows, and agent building.
- RAGFlow and PrivateGPT compete mainly on document understanding and private document Q&A.

### Strategic conclusion

Do not copy their complete UIs. Make Attic the portable memory backend that these tools and agents can call.

## 3. Current Attic review

### Existing strengths

- FastAPI REST API
- SQLite source of truth
- Qdrant vector index
- Ollama local embeddings and RAG
- MCP server
- Python and JavaScript clients
- Namespace and tag support
- SHA-256 deduplication
- Markdown, text, PDF, URL, voice, Notion, and Obsidian paths
- Docker Compose deployment
- Basic web console
- Smoke tests and provider contract tests

### Current weaknesses

| Area | Current state | Required fix |
|---|---|---|
| Memory model | Document text + vector | Add facts, events, conversations, entities, validity, confidence |
| Time | Created/updated timestamps | Add valid-from, valid-until, supersedes, temporal queries |
| Provenance | Source string | Add source URI, agent, user, tool, evidence, approval state |
| Security | One shared API key | Add users, agents, scopes, tenant isolation, rotation |
| Retrieval | Vector search with lexical fallback | Add hybrid search, reranking, deduped results, evaluation |
| RAG | Basic prompt | Add citations, context budget, untrusted-context boundaries |
| Ingestion | Several adapters | Add resumable jobs, progress, retries, source change tracking |
| UI | Basic search/ask console | Add upload, memory review, edit, approve, forget, audit, namespace management |
| Connections | O(n²) lexical scan | Use Qdrant nearest-neighbor pairs or a graph index |
| Database | SQLite implementation + SQLModel artifacts | Make migrations authoritative and add PostgreSQL option |
| Testing | Smoke/unit checks | Add retrieval benchmark, security tests, load tests, CI |
| Operations | Local Compose | Add backup, restore, metrics, structured logs, health dependencies |

## 4. Non-negotiable requirements

### R1 — Portable API

Any agent must be able to:

```text
remember(content, source, metadata)
recall(query, filters)
ask(question, context_policy)
update(memory)
forget(memory)
export(scope)
```

Support REST, MCP, Python, and JavaScript. Keep API responses versioned and backwards-compatible.

### R2 — Durable memory lifecycle

Every memory needs:

```text
id
tenant_id
namespace
memory_type
content
source
source_uri
agent_id
user_id
created_at
valid_from
valid_until
confidence
status: active | pending | superseded | rejected
supersedes_id
content_hash
```

Memory writes must support idempotency and safe deletion.

### R3 — Trust and provenance

Every retrieved result must expose:

- memory ID
- source
- timestamp
- namespace
- score
- retrieval method
- evidence or chunk location
- approval state

Retrieved memory is untrusted evidence. It must never become a system instruction, permission, credential, or tool authorization.

### R4 — Retrieval quality

Implement in order:

1. Exact/keyword search
2. Vector search
3. Hybrid score fusion
4. Metadata filtering
5. Reranking
6. Result deduplication
7. Context budget enforcement
8. Citation generation

Measure Recall@K, MRR, answer faithfulness, latency, token cost, and no-context precision.

### R5 — Local-first deployment

Default stack remains:

```text
SQLite or PostgreSQL
Qdrant
Ollama
Docker Compose
```

Cloud LLMs and vector stores remain optional. Export must work without the original provider.

### R6 — Security

Required before public release:

- Replace default `dev-key` in production.
- Per-agent and per-user credentials.
- Namespace authorization, not only namespace filtering.
- Request size limits.
- Rate limits.
- Secret redaction.
- Audit logs for every read/write/delete.
- Prompt-injection tests against stored memory.
- Backup encryption guidance.

## 5. Product scope

### Build now

- Temporal memory and fact supersession
- Upload/review UI
- Hybrid retrieval and reranking
- Citations and provenance
- Multi-agent namespaces and scopes
- Conversation ingestion
- Backup/export/import
- Retrieval evaluation suite
- OpenAI-compatible memory tool endpoint
- Framework adapters for LangChain, LlamaIndex, CrewAI, Letta, Dify, and Open WebUI

### Defer

- General-purpose chat platform
- Image generation
- Code execution sandbox
- Mobile app
- WhatsApp client
- Workflow marketplace
- Hosted billing platform
- Large connector marketplace

## 6. Execution phases

### Phase A — Trustworthy core

- Finalize schema and migrations
- Add temporal fields and memory types
- Add provenance and audit tables
- Add update/supersede/approve/reject APIs
- Add export/import

Acceptance: a user can inspect why a memory exists, change it, invalidate it, and restore it.

Status: implemented in the SQLite runtime/API. Acceptance check: `python3 scripts/phase_a_test.py`.

### Phase B — Retrieval quality

- Add hybrid retrieval
- Add reranking
- Add result deduplication
- Add citations
- Add benchmark fixtures
- Add context/token budgets

Acceptance: benchmark report shows Recall@5, MRR, answer faithfulness, latency, and token usage.

Research and detailed implementation scope: [PHASE_B_RESEARCH.md](PHASE_B_RESEARCH.md).

Status: implemented baseline hybrid retrieval, filters, citations, context budgets, reindex endpoint, and offline acceptance check: `python3 scripts/phase_b_test.py`.

### Phase C — Universal integrations

- Version REST API
- Add OpenAI-compatible tool schema
- Add framework adapters
- Add conversation adapters
- Add webhook ingestion
- Add integration examples for major agent runtimes

Acceptance: five different agent frameworks can remember and recall through Attic without custom database code.

### Phase D — Production safety

- Authentication and authorization
- Per-tenant isolation
- Rate limits
- Audit UI
- Backup/restore
- PostgreSQL option
- CI, release automation, security scanning

Acceptance: two tenants cannot read each other’s memory; every access is auditable.

Status: baseline implemented with tenant-scoped API keys, SQLite ownership,
request/mutation audit records, request-size limits, rate limiting, and
export/import backup flow. PostgreSQL, audit UI, and CI release/security
automation remain follow-up infrastructure work. Check: `python3 scripts/phase_d_test.py`.

### Phase E — Open-source adoption

- Apache-2.0 or MIT license decision
- Contributor guide
- Good-first-issue backlog
- Docker quickstart under ten minutes
- Public API documentation
- Architecture decision records
- Compatibility and migration policy

Acceptance: a new developer can install, ingest, query, test, and contribute without maintainer help.

## 7. Dependency graph

```text
Schema + auth
    ├──> provenance + audit
    ├──> temporal memory
    └──> multi-tenant API

Ingestion normalization
    └──> hybrid retrieval + reranking
              └──> citations + RAG evaluation

Stable API
    ├──> SDKs
    ├──> MCP
    └──> framework adapters

All core features
    └──> UI, backups, CI, public release
```

## 8. Definition of “perfect enough”

Attic is ready for serious public competition when it can answer yes to all:

- Can any agent connect in under ten minutes?
- Can users see exactly why an answer was produced?
- Can incorrect memory be corrected or removed safely?
- Can facts become invalid without deleting history?
- Can two users or agents never cross memory boundaries?
- Can the system run fully offline?
- Can memory export to a portable format?
- Can retrieval quality be measured instead of guessed?
- Can the same memory work across multiple models and frameworks?
- Can a maintainer upgrade storage or models without data loss?

## 9. Recommended identity

> Attic is the open-source, local-first memory layer for agents: portable across models, inspectable by humans, grounded in source evidence, and safe to evolve over time.

That is the defensible wedge. Do not compete on the number of chat features. Compete on memory quality, portability, provenance, temporal correctness, and developer trust.
