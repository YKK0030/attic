# Attic Phase B — Retrieval Quality Research

Date: 2026-10-05  
Status: research complete; implementation scope defined

## Goal

Make retrieval reliable enough for an agent to use Attic as evidence:

```text
query -> normalize -> keyword + vector candidates -> fuse -> rerank
      -> filter lifecycle/security -> dedupe -> pack context -> cite
```

Phase B is not a new chat UI. It is a portable retrieval service for REST,
MCP, Python, JavaScript, and future framework adapters.

## What competitors do well

| Product | Useful retrieval capability | Attic response |
|---|---|---|
| Open WebUI | BM25 + vector + cross-encoder reranking; exact grep; focused vs full-context modes; agentic knowledge tools; citations; reindexing | Implement hybrid retrieval, exact match, bounded context, citations, and explicit reindex metadata |
| AnythingLLM | Workspace-scoped RAG, document uploads, agent/tool workflows, private deployment | Treat namespace as a first-class retrieval scope; expose stable tool/API contracts |
| Khoj | Personal notes/document/web search, custom agents, multiple interfaces | Optimize for portable memory and provenance, not another assistant shell |
| Zep/Graphiti | Temporal graph, invalidated facts, entity/edge expansion, BM25 + semantic search, context blocks with character budgets | Add optional lightweight relations and time-aware filtering; keep raw evidence authoritative |
| Mem0 | Memory extraction, vector retrieval, optional graph relations, reranking | Add memory types and optional relations without making an LLM mandatory for every write |
| Letta | Agent-scoped archival search, tags, date filters, shared archives, editable memory | Support agent/user scope, temporal filters, tags, and shared namespaces |
| LlamaIndex | Hybrid mode, metadata filters, reciprocal-rank fusion, retrieval evaluation | Use RRF first; add a small benchmark with Recall@K/MRR |
| RAGFlow | Document parsing/chunking and citation-oriented RAG | Preserve chunk/source offsets and make ingestion/reindexing observable |
| Dify | Knowledge bases, retrieval settings, reranking, workflow/agent integration | Keep retrieval independently callable by any workflow or agent |
| PrivateGPT | Local/private document Q&A | Keep Ollama/Qdrant/SQLite defaults and make cloud providers optional |

Sources: [Open WebUI knowledge](https://docs.openwebui.com/features/workspace/knowledge/),
[Open WebUI RAG](https://docs.openwebui.com/features/chat-conversations/rag/),
[Zep Graphiti](https://help.getzep.com/graphiti/getting-started/overview),
[Zep search](https://help.getzep.com/searching-the-graph),
[Mem0 graph memory](https://docs.mem0.ai/open-source/features/graph-memory),
[Letta archival memory](https://docs.letta.com/api/resources/agents),
[LlamaIndex hybrid retrieval](https://docs.llamaindex.ai/en/v0.10.17/optimizing/basic_strategies/basic_strategies.html).

## Phase B requirements

### B1. Retrieval contract

`recall` returns, for every hit:

```json
{
  "id": "memory-id",
  "content": "evidence",
  "source": "file.md",
  "source_uri": "file:///...",
  "namespace": "default",
  "score": 0.81,
  "retrieval": ["vector", "keyword", "rerank"],
  "chunk_index": 0,
  "citation": {"source": "file.md", "memory_id": "memory-id"},
  "status": "active"
}
```

Backward compatibility: existing fields remain; new fields are additive.

### B2. Hybrid candidate retrieval

- Keyword: SQLite FTS5 when available; lexical fallback otherwise.
- Dense: Qdrant top `candidate_k`.
- Fusion: Reciprocal Rank Fusion, configurable `keyword_weight` and `vector_weight`.
- Filters before final ranking: namespace, tag, memory type, agent, user, status, validity window.
- Candidate over-fetch: retrieve `max(limit * 4, 20)` before deduplication.

### B3. Reranking

Provider order:

1. Optional local reranker configured by environment.
2. Lightweight lexical/metadata reranker when no model is available.
3. Never fail recall because a reranker is unavailable.

Do not use the chat LLM as a reranker by default: it costs more, adds latency,
and makes retrieval less deterministic.

### B4. Dedupe and diversity

- Collapse duplicate chunks from the same memory.
- Prefer the best-scoring chunk, retain source/chunk metadata.
- Optional per-source cap to prevent one document monopolizing context.
- Add MMR only after baseline hybrid + RRF is measured.

### B5. Context assembly

Add `GET /context` or equivalent client method:

```text
context(query, max_tokens, max_chars, limit, filters)
```

Rules:

- hard character/token budget;
- stable ordering;
- source labels and citations;
- explicit “untrusted evidence” wrapper for the LLM;
- return raw hits and the packed context for inspection;
- no-context result when evidence is below threshold.

### B6. Query modes

Implement only the useful modes:

- `semantic`: vector retrieval;
- `keyword`: exact identifiers/errors/names;
- `hybrid`: default;
- `context`: hybrid + rerank + budget packing;
- `timeline`: valid/created time filters.

Defer autonomous query rewriting until the benchmark proves it helps. It adds
LLM cost and can distort exact queries.

### B7. Reindexing

Store index metadata: embedding provider/model/dimension, chunk size/overlap,
schema version, and indexed timestamp. Add:

- `POST /reindex` with namespace and dry-run options;
- collection/model mismatch detection;
- resumable per-memory reindexing;
- no silent mixing of incompatible embedding dimensions.

### B8. Evaluation

Create a small versioned fixture containing:

- paraphrase questions;
- exact identifier questions;
- conflicting/superseded facts;
- namespace isolation cases;
- temporal questions;
- no-answer questions;
- duplicate and multi-source evidence.

Report:

- Recall@1/5/10;
- MRR;
- citation/source accuracy;
- no-context precision;
- p50/p95 latency;
- embedding/reranker/LLM token cost;
- failure reason and fallback path.

Minimum gate before calling Phase B complete:

- hybrid beats vector-only on the fixture;
- superseded/rejected memories never appear in active recall;
- exact identifiers are found;
- context never exceeds its budget;
- every answer source maps to a returned memory.

## Deliberate non-goals

- No mandatory graph database. SQLite relations plus Qdrant are enough for the first release.
- No full-context default for large documents.
- No LLM query rewriting in the first implementation.
- No expensive cross-encoder download in the base Docker image.
- No competitor-specific UI cloning.

## Implementation order

1. Normalize retrieval result/citation schema.
2. Add SQLite FTS5 keyword index with fallback.
3. Add Qdrant over-fetch and RRF fusion.
4. Add filters and lifecycle-aware visibility before ranking.
5. Add dedupe and source diversity.
6. Add bounded `/context` assembly.
7. Add reindex metadata/endpoints.
8. Add benchmark fixtures and report.
9. Add optional reranker adapter.

## Attic differentiation

Attic should win on portability and trust:

- one memory API for any agent/model/framework;
- local-first operation with inspectable SQLite/Qdrant data;
- every result carries provenance and lifecycle state;
- correction, supersession, export, and audit are first-class;
- predictable context budgets instead of opaque prompt stuffing;
- no required hosted platform or vendor-specific model.
