# Attic

Attic is a local-first memory service for AI agents.

It stores durable facts, notes, documents, decisions, conversations, and
preferences. Agents can use it through REST, MCP, Python, JavaScript, or the
included CLI.

```text
agent → remember / recall → Attic
                         ├─ SQLite: source of truth
                         ├─ Qdrant: semantic index
                         └─ Ollama: local embeddings and answers
```

## Try it in 5 minutes

Requirements: Docker, Docker Compose, and Ollama.

```sh
ollama pull all-minilm
ollama pull qwen2.5:0.5b-instruct
OLLAMA_HOST=0.0.0.0:11434 ollama serve
docker compose -f docker/docker-compose.yml up --build
```

Open the console at <http://localhost:4000> or API docs at
<http://localhost:4000/docs>.

The default development key is `dev-key`. Change it before sharing the service:

```sh
ATTIC_API_KEY='replace-me' docker compose -f docker/docker-compose.yml up --build
```

### Store and retrieve a memory

```sh
curl -X POST http://localhost:4000/v1/memory \
  -H 'x-attic-key: dev-key' \
  -H 'content-type: application/json' \
  -d '{"content":"The deployment runs every Friday.","source":"team-notes","tags":["deployment"],"namespace":"project-alpha"}'

curl 'http://localhost:4000/v1/recall?q=deployment&namespace=project-alpha' \
  -H 'x-attic-key: dev-key'

curl 'http://localhost:4000/v1/ask?q=When is the deployment?&namespace=project-alpha' \
  -H 'x-attic-key: dev-key'
```

`/v1` is the stable API surface. The original unversioned routes remain
available for compatibility.

## What to use

| Need | Use |
|---|---|
| Explore memories manually | Web console at `/` |
| Integrate any agent or app | REST API at `/v1` |
| Python agent | `packages/attic_client` |
| JavaScript agent | `packages/attic-js` |
| MCP-compatible agent | `packages/mcp_server` |
| Ingest Markdown, text, or PDF | `apps/cli/attic_cli.py ingest` |
| Clip a web page | `apps/cli/attic_cli.py clip` |
| Transcribe audio | `apps/cli/attic_cli.py voice` |
| Review lifecycle and provenance | update, approve, reject, supersede, and audit endpoints |
| Connect conversations/webhooks | `/v1/conversations` and `/v1/webhooks/memory` |

## Python client

```sh
pip install -e packages/attic_client
```

```python
from attic_client import Attic

memory = Attic(url="http://localhost:4000", key="dev-key", namespace="project-alpha")
memory.remember("The deployment runs every Friday.", "team-notes", ["deployment"])
print(memory.recall("deployment"))
print(memory.ask("When is the deployment?"))
```

## JavaScript client

```js
import { Attic } from './packages/attic-js/index.mjs';

const memory = new Attic({ url: 'http://localhost:4000', key: 'dev-key', namespace: 'project-alpha' });
await memory.remember('The deployment runs every Friday.', 'team-notes');
console.log(await memory.recall('deployment'));
```

## CLI ingestion

Run from the repository root:

```sh
PYTHONPATH=apps python3 apps/cli/attic_cli.py ingest ./notes \
  --namespace project-alpha --tag reference

PYTHONPATH=apps python3 apps/cli/attic_cli.py search "deployment" \
  --namespace project-alpha

PYTHONPATH=apps python3 apps/cli/attic_cli.py ask "What is the deployment plan?"
```

Supported local files: `.md`, `.txt`, and `.pdf`.

Optional adapters:

```sh
PYTHONPATH=apps python3 apps/cli/attic_cli.py clip https://example.com/article
WHISPER_BIN=whisper-cli PYTHONPATH=apps python3 apps/cli/attic_cli.py voice memo.wav
```

## MCP

```sh
pip install -e packages/mcp_server
ATTIC_URL=http://localhost:4000 \
ATTIC_API_KEY=dev-key \
python3 -m attic_mcp.server
```

Tools: `remember`, `recall`, and `ask`.

## REST API essentials

All protected requests use `x-attic-key: <key>`.

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/v1/health` | Tenant-scoped health and memory count |
| `POST` | `/v1/memory` | Store a memory |
| `GET` | `/v1/recall` | Keyword, semantic, or hybrid retrieval |
| `GET` | `/v1/context` | Retrieval with a hard character budget |
| `GET` | `/v1/ask` | Grounded answer with citations |
| `PATCH` | `/v1/memory/{id}` | Update memory metadata or content |
| `POST` | `/v1/memory/{id}/approve` | Approve pending memory |
| `POST` | `/v1/memory/{id}/reject` | Reject memory |
| `POST` | `/v1/memory/{id}/supersede` | Replace a memory while preserving history |
| `GET` | `/v1/memory/{id}/audit` | View memory audit history |
| `DELETE` | `/v1/memory/{id}` | Forget a memory |
| `GET` | `/v1/export` | Export tenant memories and audit data |
| `POST` | `/v1/import` | Import an export bundle |
| `POST` | `/v1/reindex` | Rebuild vector index; supports `dry_run=true` |
| `POST` | `/v1/conversations` | Store normalized conversation messages |
| `POST` | `/v1/webhooks/memory` | Idempotent webhook memory ingestion |
| `GET` | `/v1/openai/tools` | Get memory tool definitions |
| `POST` | `/v1/openai/tools/execute` | Execute a memory tool call |

Recall modes: `hybrid` (default), `semantic`, `keyword`, `context`, and
`timeline`. Results include scores, retrieval methods, source data, memory IDs,
namespace, lifecycle state, and citations.

## Tenant isolation and production settings

For multiple tenants, map separate API keys to tenant IDs:

```sh
export ATTIC_TENANT_KEYS='{"team-a":"secret-a","team-b":"secret-b"}'
```

Each key gets isolated memories, namespaces, exports, vector searches,
idempotency keys, and audit history.

Useful safety settings:

```sh
ATTIC_MAX_REQUEST_BYTES=1048576
ATTIC_RATE_LIMIT=120
ATTIC_RATE_WINDOW_SECONDS=60
```

See [docs/phase-d-security.md](docs/phase-d-security.md) for the security
contract and [docs/universal-agent-integration.md](docs/universal-agent-integration.md)
for agent integration guidance.

## Providers

Defaults are local Ollama models:

```text
Embedding: all-minilm
Answering: qwen2.5:0.5b-instruct
```

Optional providers:

```sh
EMBED_PROVIDER=ollama|openai|voyage
LLM_PROVIDER=ollama|openai|claude
```

Set the matching provider API key and model variables before starting the API.
Ollama/Qdrant failures do not prevent keyword recall; vector indexing and
grounded answers may be unavailable until the dependency returns.

## Local development

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r apps/api/requirements.txt
PYTHONPATH=apps/api uvicorn attic_api.main:app --reload --port 4000
```

For local development, point `QDRANT_URL` and `OLLAMA_URL` at running services.
The SQLite database defaults to `attic.db`; set `ATTIC_DB` to move it.

## Verification

Run the cheap offline gates after changes:

```sh
python3 scripts/regression_test.py
```

This checks lifecycle behavior, retrieval, Phase C integrations, tenant
isolation, provider contracts, and Python compilation.

When the API, Qdrant, and Ollama are running:

```sh
python3 scripts/smoke_test.py
```

The smoke test verifies live health, writes, deduplication, recall, grounded
answers, connections, and deletion.

## Project layout

```text
apps/api/                 FastAPI service and SQLite/Qdrant core
apps/cli/                 Ingestion and search CLI
packages/attic_client/    Python client
packages/attic-js/        JavaScript client
packages/mcp_server/      MCP adapter
web/                      Static web console
docker/                   API and Qdrant Compose setup
scripts/                  Smoke, phase, and regression checks
docs/                     Integration and security guides
```

## Design principles

- SQLite is the source of truth; Qdrant is rebuildable search state.
- Retrieved memories are evidence, not instructions or permissions.
- Use namespaces for projects, users, or tenants.
- Store durable facts and decisions, not every intermediate thought.
- Keep `source`, tags, and provenance useful enough to inspect later.

Roadmap details: [ATTIC_REQUIREMENTS_PLAN.md](ATTIC_REQUIREMENTS_PLAN.md).
