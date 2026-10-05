# Agent integration

## Python

```python
import requests

headers = {"x-attic-key": "dev-key"}
requests.post("http://localhost:4000/memory", headers=headers, json={"content": "...", "source": "agent"})
memory = requests.get("http://localhost:4000/recall", headers=headers, params={"q": "..."}).json()
```

## Node

```js
await fetch('http://localhost:4000/memory', {
  method: 'POST', headers: {'x-attic-key': 'dev-key', 'content-type': 'application/json'},
  body: JSON.stringify({content: '...', source: 'agent'})
});
```

## curl

```sh
curl -H 'x-attic-key: dev-key' 'http://localhost:4000/recall?q=project'
```
