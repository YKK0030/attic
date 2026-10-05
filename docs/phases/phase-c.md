# Phase C — Universal integrations

## Need

Attic is useful only if agent runtimes can call it without writing database
code or coupling to one model provider.

## Plan

- Version the REST API while preserving existing routes.
- Expose OpenAI-compatible memory tool definitions and execution.
- Normalize conversation ingestion.
- Add replay-safe webhook ingestion.
- Provide thin examples for common agent runtimes.

## Status

Baseline implemented:

- `/v1` routes mirror the legacy API.
- `/v1/openai/tools` and `/v1/openai/tools/execute` expose memory tools.
- `/v1/conversations` stores message-level provenance.
- `/v1/webhooks/memory` uses tenant-scoped idempotency keys.
- Examples cover LangChain, LlamaIndex, CrewAI, Letta, and Dify/HTTP.

See [integration examples](../phase-c-integrations.md).

## Acceptance

```sh
python3 scripts/phase_c_test.py
```

Existing REST, Python, JavaScript, and MCP clients remain compatible while new
integration paths preserve citations, namespace, and lifecycle metadata.
