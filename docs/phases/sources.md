# Sources and decision map

These sources informed the roadmap. They are references for design decisions,
not claims that Attic implements every feature of the linked products.

| Source | Observed pattern | Attic decision |
|---|---|---|
| [Open WebUI knowledge](https://docs.openwebui.com/features/workspace/knowledge/) | Knowledge bases, citations, and retrieval controls | Keep citations and bounded retrieval in the backend |
| [Open WebUI RAG](https://docs.openwebui.com/features/chat-conversations/rag/) | Hybrid/vector retrieval and focused context | Support keyword, vector, hybrid, and context modes |
| [AnythingLLM](https://docs.anythingllm.com/features/all-features) | Workspace-scoped RAG and private deployment | Make namespace a first-class scope; stay UI-independent |
| [Khoj](https://github.com/khoj-ai/khoj) | Personal notes, web sources, and custom agents | Prioritize portable memory and provenance |
| [Zep Graphiti](https://help.getzep.com/graphiti/getting-started/overview) | Temporal graph memory and invalidated facts | Add validity windows and supersession before a graph database |
| [Zep search](https://help.getzep.com/searching-the-graph) | Hybrid search and context blocks | Use hybrid retrieval and inspectable context budgets |
| [Mem0 graph memory](https://docs.mem0.ai/open-source/features/graph-memory) | Extracted memories and optional relations | Keep relations optional; raw evidence remains authoritative |
| [Letta agents](https://docs.letta.com/api/resources/agents) | Agent-scoped archival memory and filters | Support agent/user scope and temporal filters |
| [LlamaIndex hybrid retrieval](https://docs.llamaindex.ai/en/v0.10.17/optimizing/basic_strategies/basic_strategies.html) | Hybrid mode, RRF, and retrieval evaluation | Use RRF first and add a small benchmark |
| [Dify](https://docs.dify.ai/en/home) | Knowledge bases and workflow/agent integration | Keep retrieval callable by any workflow |
| [RAGFlow](https://ragflow.io/) | Document parsing and citation-oriented RAG | Preserve source and chunk provenance |
| [PrivateGPT](https://github.com/zylon-ai/private-gpt) | Local/private document Q&A | Keep local providers and cloud options optional |

## Product decisions

1. Do not clone a broad chat workspace; Attic is the memory backend.
2. Keep SQLite authoritative and Qdrant rebuildable.
3. Prefer deterministic retrieval and explicit provenance over default LLM
   rewriting.
4. Add graph relations only after baseline retrieval proves the need.
5. Keep framework adapters thin and contract-based.
