# Phase C integration examples

All examples use the stable Python client or REST contract; none needs direct
database access.

## LangChain

```python
from attic_client import Attic
memory = Attic(namespace="langchain-agent")
memory.remember("The deploy job runs nightly.", "langchain", ["decision"])
docs = memory.recall("deploy schedule")
```

## LlamaIndex

```python
from attic_client import Attic
memory = Attic(namespace="llamaindex-agent")
memory.remember("Use Qdrant for vectors.", "llamaindex", ["architecture"])
hits = memory.recall("vector store")
```

## CrewAI

```python
from attic_client import Attic
memory = Attic(namespace="crewai-task")
memory.remember("The research task is complete.", "crewai", ["result"])
context = memory.recall("research result")
```

## Letta

```python
from attic_client import Attic
memory = Attic(namespace="letta-agent")
memory.remember("User prefers concise answers.", "letta", ["preference"])
context = memory.recall("answer style")
```

## Dify / any HTTP agent

```sh
curl -X POST http://localhost:4000/v1/memory \
  -H 'x-attic-key: dev-key' -H 'content-type: application/json' \
  -d '{"content":"Release is Friday","source":"dify","namespace":"dify-app"}'
curl 'http://localhost:4000/v1/recall?q=release&namespace=dify-app' \
  -H 'x-attic-key: dev-key'
```

Conversation ingestion uses `POST /v1/conversations`. Webhook ingestion uses
`POST /v1/webhooks/memory` with a unique `event_id`; replaying an event is
safe and returns the existing memory as skipped.

OpenAI-compatible clients can fetch `GET /v1/openai/tools` and execute the
returned function calls through `POST /v1/openai/tools/execute`.
