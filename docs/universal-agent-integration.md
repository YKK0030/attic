# Universal agent integration

Attic is model-independent. Agents connect through REST or MCP. Store original facts and decisions in Attic; keep temporary reasoning in the agent.

## Agent loop

```text
start task → recall relevant context → work → remember durable result
```

Use a separate namespace for each user, project, or tenant. Use `source` to identify the agent, tool, file, or conversation that produced the memory.

## Python

```sh
python3 -m pip install -e packages/attic_client
```

```python
from attic_client import Attic

memory = Attic(namespace="project-alpha")
context = memory.recall("deployment decisions")
answer = memory.ask("What deployment decisions were recorded?")
memory.remember("API runs behind Qdrant and Ollama.", "agent:planner", ["architecture"])
```

## JavaScript

```js
import { Attic } from './packages/attic-js/index.mjs';

const memory = new Attic({ namespace: 'project-alpha' });
const context = await memory.recall('deployment decisions');
await memory.remember('API runs behind Qdrant and Ollama.', 'agent:planner', ['architecture']);
```

## Any HTTP-capable agent

```sh
curl -X POST http://localhost:4000/memory \
  -H 'x-attic-key: dev-key' -H 'content-type: application/json' \
  -d '{"content":"User prefers concise answers.","source":"agent:profile","tags":["preference"],"namespace":"user-1"}'
```

Then retrieve it with `GET /recall?q=concise+answers&namespace=user-1`.

## MCP

Run:

```sh
cd packages/mcp_server
python3 -m pip install -e .
ATTIC_URL=http://localhost:4000 ATTIC_API_KEY=dev-key python3 -m attic_mcp.server
```

Expose the MCP server to any MCP-compatible client. Tools: `remember`, `recall`, `ask`.

## Memory rules

- Remember stable facts, preferences, decisions, and completed work.
- Do not remember secrets, passwords, tokens, or raw private credentials.
- Use source names that can be opened or understood later.
- Recall before answering questions about prior work.
- Ask Attic for grounded answers when source citations matter.
- Write only durable outcomes after a task; avoid saving every intermediate thought.
