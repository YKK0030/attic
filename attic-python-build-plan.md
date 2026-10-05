# Attic — Python Build Plan (v2)

> Same product: an open-source agent memory layer that doubles as your personal second brain.
> This version swaps the backend to **Python (FastAPI)** and adds a live TODO tracker so progress is checkable at a glance.

---

## What changed from the Node version

1. **Backend is FastAPI**, not Express — async by default, Pydantic gives you request validation for free (replaces Zod).
2. **SQLModel** (SQLAlchemy + Pydantic in one) instead of Prisma — still SQLite by default, still a one-line swap to Postgres.
3. **Typer** instead of commander.js for the CLI — same command shape, Python-native.
4. **qdrant-client** (official Python SDK) instead of the JS client — identical Qdrant server, no change to infra.
5. Everything else — schema, API contract, dedup logic, timeline shape, free-stack philosophy — carries over unchanged from the Node plan, because none of that was language-specific.

---

## Folder Structure

```
attic/
│
├── apps/
│   ├── api/                         # FastAPI backend
│   │   ├── attic_api/
│   │   │   ├── ingestion/
│   │   │   │   ├── watcher.py       # watchdog file watcher
│   │   │   │   ├── pipeline.py      # parse → chunk → embed → store
│   │   │   │   ├── dedup.py         # SHA-256 hash check, skip if unchanged
│   │   │   │   ├── parsers/
│   │   │   │   │   ├── markdown.py
│   │   │   │   │   ├── pdf.py       # pypdf
│   │   │   │   │   ├── audio.py     # calls whisper.cpp binary via subprocess
│   │   │   │   │   └── url.py       # BeautifulSoup scraper
│   │   │   │   ├── chunker.py       # 512 tokens, 50 overlap, boundary-aware
│   │   │   │   └── embedder.py      # Ollama nomic-embed (swappable via config)
│   │   │   │
│   │   │   ├── storage/
│   │   │   │   ├── vector.py        # qdrant-client wrapper
│   │   │   │   └── db.py            # SQLModel engine + session
│   │   │   │
│   │   │   ├── query/
│   │   │   │   ├── search.py        # ANN search, re-rank, filter by tag/namespace
│   │   │   │   ├── rag.py           # retrieval + LLM call, grounding, no-context guard
│   │   │   │   └── surface.py       # connection finder (cross-source similarity)
│   │   │   │
│   │   │   ├── routes/
│   │   │   │   ├── memory.py        # POST /memory, DELETE /memory/{id}
│   │   │   │   ├── recall.py        # GET /recall
│   │   │   │   ├── ask.py           # GET /ask
│   │   │   │   ├── surface.py       # GET /surface
│   │   │   │   └── health.py        # GET /health
│   │   │   │
│   │   │   ├── jobs/
│   │   │   │   └── connection_surface.py   # APScheduler weekly job
│   │   │   │
│   │   │   ├── middleware/
│   │   │   │   └── auth.py          # API key check (x-attic-key header)
│   │   │   │
│   │   │   ├── models.py            # SQLModel table definitions
│   │   │   ├── config.py            # provider config: ollama vs openai vs claude
│   │   │   └── main.py              # FastAPI app entry
│   │   │
│   │   ├── alembic/                 # migrations
│   │   ├── pyproject.toml
│   │   └── requirements.txt
│   │
│   ├── web/                         # React + Vite frontend (unchanged — talks to FastAPI over REST)
│   │   └── ...                      # same as Node plan, no changes needed
│   │
│   └── cli/                         # Typer CLI
│       ├── attic_cli/
│       │   ├── commands/
│       │   │   ├── search.py        # attic search "query"
│       │   │   ├── ask.py           # attic ask "question"
│       │   │   ├── ingest.py        # attic ingest ./folder OR --voice memo.mp3
│       │   │   ├── forget.py        # attic forget <id>
│       │   │   └── status.py        # attic status
│       │   └── main.py
│       └── pyproject.toml
│
├── packages/
│   └── mcp_server/                  # Phase 4: MCP server (Python SDK)
│       ├── attic_mcp/
│       │   ├── tools/
│       │   │   ├── remember.py      # MCP tool: write a memory
│       │   │   ├── recall.py        # MCP tool: semantic search
│       │   │   └── ask.py           # MCP tool: RAG Q&A
│       │   └── server.py
│       └── pyproject.toml
│
├── docker/
│   ├── docker-compose.yml           # Qdrant + API + Web in one command
│   ├── docker-compose.dev.yml       # dev override with hot reload
│   └── Dockerfile.api
│
├── scripts/
│   ├── setup.sh                     # install Ollama, pull models, run alembic upgrade
│   └── seed.sh                      # ingest a sample folder to test
│
├── docs/
│   ├── agent-integration.md
│   ├── api-reference.md
│   └── mcp-setup.md
│
├── TODO.md                          # <- the live tracker, see below
├── .env.example
├── .gitignore
└── README.md
```

---

## Database Schema (SQLModel)

```python
# apps/api/attic_api/models.py

from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Document(SQLModel, table=True):
    id: str = Field(primary_key=True)             # cuid-style string
    namespace: str = Field(default="default", index=True)
    source: str                                     # file path, URL, "agent:name"
    source_type: str                                 # "file" | "url" | "audio" | "api"
    content_hash: str = Field(index=True)            # SHA-256 of raw content — dedup key
    title: Optional[str] = None
    tags: str = Field(default="[]")                  # JSON array stored as string
    chunk_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    chunks: List["Chunk"] = Relationship(back_populates="document")


class Chunk(SQLModel, table=True):
    id: str = Field(primary_key=True)
    document_id: str = Field(foreign_key="document.id")
    namespace: str = Field(default="default", index=True)
    vector_id: str                                   # Qdrant point ID
    content: str
    chunk_index: int
    token_count: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    document: Document = Relationship(back_populates="chunks")


class Connection(SQLModel, table=True):
    id: str = Field(primary_key=True)
    namespace: str = Field(default="default", index=True)
    chunk_id_a: str
    chunk_id_b: str
    score: float                                     # cosine similarity
    surfaced_at: datetime = Field(default_factory=datetime.utcnow)
    dismissed: bool = False
```

---

## Provider Config (swap with one env var)

```python
# apps/api/attic_api/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    llm_provider: str = "ollama"          # "ollama" | "claude" | "openai"
    embed_provider: str = "ollama"        # "ollama" | "openai" | "voyage"
    whisper_provider: str = "local"       # "local" | "openai"

    ollama_llm_model: str = "llama3.2"
    ollama_embed_model: str = "nomic-embed-text"
    claude_model: str = "claude-haiku-4-5"
    openai_llm_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"

    chunk_size: int = 512
    chunk_overlap: int = 50

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "attic_memories"

    port: int = 4000
    attic_api_key: str = "dev-key"

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## REST API Reference (unchanged contract, now served by FastAPI)

All endpoints accept header `x-attic-key: <your-key>` and optional query param `?namespace=default`.

### `POST /memory`
```json
Request:
{
  "content": "User prefers bullet points over prose.",
  "source": "agent:onboarding",
  "tags": ["user-preference"],
  "namespace": "project-x"
}
Response:
{ "id": "clx...", "chunks": 1, "tags": ["user-preference"] }
```

### `GET /recall?q=query&limit=5&tag=engineering&namespace=default`
```json
[{ "id": "clx...", "content": "...", "source": "notes/system-design.md",
   "score": 0.91, "tags": ["engineering"], "date": "2026-09-01T10:00:00Z" }]
```

### `GET /ask?q=your+question&namespace=default`
```json
{ "answer": "Based on your notes, you prefer...",
  "sources": [{ "source": "notes/prefs.md", "score": 0.88 }],
  "had_context": true }
```

### `GET /surface?since=7d&tag=engineering&namespace=default`
```json
[{ "chunk_a": {...}, "chunk_b": {...}, "score": 0.87,
   "note": "You wrote about this from two different angles, 3 months apart." }]
```

### `DELETE /memory/{id}`
Cascades to all chunks in Qdrant and SQLite.

### `GET /health`
Qdrant connection, Ollama status, total memories, active namespaces.

FastAPI gives you `/docs` (Swagger UI) for free at `http://localhost:4000/docs` — no separate Postman collection needed, though one can still be exported for non-technical agent authors.

---

## Deduplication Logic (unchanged)

```
On every ingest:
1. Compute SHA-256 of raw file content
2. Query: SELECT * FROM document WHERE content_hash = ? AND namespace = ?
3a. Found + hash matches  → skip (file unchanged)
3b. Found + hash differs  → delete old chunks from Qdrant + SQLite, re-ingest
3c. Not found             → ingest fresh
```

---

## Free Stack Summary

| Layer               | Free (default)             | Paid upgrade (one env var) |
|---------------------|-----------------------------|------------------------------|
| Embeddings          | nomic-embed-text (Ollama)  | text-embedding-3-small |
| LLM                 | llama3.2 (Ollama)           | Claude Haiku / GPT-4o-mini |
| Vector DB           | Qdrant (Docker local)      | Qdrant Cloud (free tier) |
| Metadata DB         | SQLite                       | PostgreSQL (swap SQLModel engine URL) |
| Voice transcription | whisper.cpp (local binary) | OpenAI Whisper API |
| Web scraping        | BeautifulSoup                | Playwright (JS-rendered pages) |
| Deployment          | Docker Compose local         | Railway / Fly.io (hobby free tier) |

---

## TODO.md — Live Progress Tracker

Copy this into `TODO.md` at the repo root. Check items off as you go — it's the single source of truth for where the build actually stands, independent of the week numbers below (life happens; the checklist doesn't lie).

```markdown
# Attic — Build TODO

Legend: [ ] not started · [~] in progress · [x] done

## Phase 0 — Foundation
- [ ] uv/poetry workspace set up (apps/api, apps/cli share a root)
- [ ] docker-compose.yml: Qdrant + API service boot together
- [ ] SQLModel schema written (Document, Chunk, Connection) with namespace + content_hash from day one
- [ ] Alembic initialized, first migration applied
- [ ] `ollama pull nomic-embed-text` && `ollama pull llama3.2` done locally
- [ ] config.py provider abstraction skeleton in place
- [ ] Deliverable check: `docker compose up` starts everything, Ollama responds to a test call

## Phase 1 — Ingestion Core
- [ ] Markdown + txt parser
- [ ] PDF parser (pypdf)
- [ ] Chunker (tiktoken, 512/50, boundary-aware — don't cut mid-sentence)
- [ ] Embedder calling Ollama nomic-embed-text
- [ ] Dedup logic: SHA-256 hash check before every ingest
- [ ] Vectors → Qdrant, metadata → SQLite via SQLModel
- [ ] `python -m attic_api.ingestion.pipeline ./folder` works end to end
- [ ] Deliverable check: drop a folder, everything indexed; re-drop same folder, nothing re-processed

## Phase 2 — Search + RAG
- [ ] Semantic search: embed query → Qdrant ANN → top-k with scores
- [ ] RAG: retrieval → prompt build → Ollama llama3.2 → grounded answer
- [ ] No-context guard: score < 0.75 → "nothing relevant found"
- [ ] Tag + namespace filters on search
- [ ] Deliverable check: search and ask both return sane answers on your own test notes

## Phase 3 — CLI (Typer)
- [ ] `attic search "query" [--tag] [--namespace] [--limit]`
- [ ] `attic ask "question" [--namespace]`
- [ ] `attic ingest ./path [--namespace]`
- [ ] `attic ingest --voice memo.mp3` (whisper.cpp via subprocess)
- [ ] `attic forget <id>`
- [ ] `attic status` (total memories, top tags, namespaces)
- [ ] Deliverable check: full CLI installable via `pip install -e .`, all commands work

## Phase 4 — Web UI
- [ ] Vite + React scaffold (unchanged from Node plan — just points at FastAPI base URL)
- [ ] Search page: bar, results with source/score/date, tag filter chips
- [ ] Ask page: conversational thread, sources shown per answer
- [ ] Dashboard: memory count, top topics chart, recently added
- [ ] Namespace selector in nav
- [ ] Connections page: surfaced links + dismiss button
- [ ] Deliverable check: full local web app on localhost:3000

## Phase 5 — Agent REST API
- [ ] FastAPI routes: POST /memory, GET /recall, GET /ask, GET /surface, DELETE /memory/{id}
- [ ] API key middleware (x-attic-key header)
- [ ] Pydantic validation on all request bodies (built in — just define the schemas)
- [ ] Namespace isolation enforced at route level, tested with two namespaces side by side
- [ ] GET /health endpoint
- [ ] Swagger docs verified at /docs
- [ ] Test script: a plain Python script (outside the repo) that writes + recalls memories via HTTP
- [ ] Deliverable check: external script can read/write memories with just `requests`

## Phase 6 — Connection Surfacer
- [ ] APScheduler weekly job registered
- [ ] Cross-source high-similarity pair query against Qdrant
- [ ] Results stored in Connection table, served via GET /surface
- [ ] Shown in web UI Connections page
- [ ] Deliverable check: at least one real surfaced connection from your own notes

## Phase 7 — MCP Server
- [ ] attic_mcp package scaffolded with the Python MCP SDK
- [ ] Tools: remember, recall, ask — each calls the local FastAPI over HTTP
- [ ] Tested natively as a connected tool in Claude Desktop
- [ ] docs/mcp-setup.md written (step by step, Claude + Cursor)
- [ ] Deliverable check: Claude uses Attic as memory in a live demo, zero custom glue code

## Phase 8 — Integrations + Polish
- [ ] Notion sync (pull pages via Notion API, ingest automatically)
- [ ] Obsidian vault watcher (watchdog on vault folder)
- [ ] URL clipper: `attic clip https://...`
- [ ] scripts/setup.sh: one script installs Ollama, pulls models, runs `alembic upgrade head`
- [ ] README.md quick start (3 commands to running)
- [ ] docs/agent-integration.md with Python, Node, and curl examples
- [ ] Deliverable check: a friend clones the repo and is running in under 10 minutes, unassisted
```

---

## What Makes This Different (unchanged from v1)

- Not another note app — it's a memory API. Agents are the primary user.
- Namespace isolation from day one.
- Deduplication built in — re-ingest the same folder endlessly, nothing duplicates.
- Swap providers with one env var — start free, upgrade without rewriting code.
- MCP-native — works with Claude Desktop and Cursor without custom integration.
- Runs entirely locally — no data leaves your machine unless you choose a cloud provider.

---

*Attic · Python edition · open-source agent memory layer · starts free, stays free*
