# Phase B — Retrieval quality

## Need

Vector-only retrieval misses exact identifiers and errors. Agents also need
bounded, cited context instead of opaque prompt stuffing.

## Plan

- Combine SQLite FTS5 keyword candidates and Qdrant dense candidates.
- Fuse rankings with reciprocal rank fusion and over-fetch before filtering.
- Filter by namespace, tags, memory type, agent, user, lifecycle, and time.
- Return source, citation, score, retrieval method, chunk, and status fields.
- Deduplicate results and enforce a hard context character budget.
- Reindex vectors with dry-run support and metadata.

## Status

Baseline implemented. `/v1/recall`, `/v1/context`, and `/v1/reindex` are the
main surfaces. Reranking remains lightweight and optional; a full benchmark
report is still future work.

## Acceptance

```sh
python3 scripts/phase_b_test.py
```

The regression gate verifies hybrid retrieval, filtering, citations, lifecycle
visibility, reindex preview, and that the actual returned context never exceeds
its budget.

## Deferred

Measure Recall@K, MRR, latency, faithfulness, and token cost before adding an
expensive cross-encoder or LLM query rewriting.
