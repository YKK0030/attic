# Attic roadmap and decisions

This folder is the public product plan. Each phase records:

- what problem it solves;
- why Attic needs it;
- what existing products or standards influenced the decision;
- what is implemented, deferred, and used as the acceptance gate.

## Product position

Attic is a local-first memory backend for agents, not another all-in-one chat
workspace. It exposes one inspectable memory contract through REST, MCP,
Python, and JavaScript while SQLite remains the source of truth.

## Status

| Phase | Area | Status |
|---|---|---|
| [A](phase-a.md) | Trustworthy core | Implemented |
| [B](phase-b.md) | Retrieval quality | Baseline implemented |
| [C](phase-c.md) | Universal integrations | Baseline implemented |
| [D](phase-d.md) | Production safety | Baseline implemented |
| [E](phase-e.md) | Open-source adoption | Planned |

## Why these phases

The order follows the dependency chain:

```text
trustworthy data → useful retrieval → stable integrations
                 → safe operation → easy adoption
```

Do not build framework adapters on unstable memory semantics, or optimize a
retrieval system that cannot explain where evidence came from.

## Competitor-informed scope

Attic borrows useful patterns without copying complete products:

- Open WebUI and AnythingLLM demonstrate practical knowledge-base and agent
  workflows.
- Khoj demonstrates personal search across notes and sources.
- Zep/Graphiti and Mem0 demonstrate temporal memory, provenance, and optional
  relations.
- Letta demonstrates agent-scoped archival memory.
- LlamaIndex demonstrates hybrid retrieval and measurable evaluation.
- Dify, RAGFlow, and PrivateGPT demonstrate workflow/document integrations and
  private deployment expectations.

Attic’s differentiation is portability, local ownership, lifecycle controls,
and inspectable provenance rather than a competing chat shell.

Detailed links and the source-to-decision map are in [sources.md](sources.md).
