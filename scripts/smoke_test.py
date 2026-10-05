import json
import os
import uuid
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = os.getenv("ATTIC_URL", "http://localhost:4000")
KEY = os.getenv("ATTIC_API_KEY", "dev-key")
marker = uuid.uuid4().hex


def call(method, path, body=None):
    request = Request(BASE + path, method=method, headers={"x-attic-key": KEY, "content-type": "application/json"})
    if body is not None:
        request.data = json.dumps(body).encode()
    with urlopen(request, timeout=90) as response:
        return response.status, json.load(response)


status, health = call("GET", "/health")
assert status == 200 and health["ok"]
created = []
for source, content in (("smoke/a", f"Attic stores {marker} in local memory."), ("smoke/b", f"Qdrant retrieves {marker} from semantic notes.")):
    status, result = call("POST", "/memory", {"content": content, "source": source, "tags": ["smoke"]})
    assert status == 200 and result["skipped"] is False
    created.append(result["id"])
status, results = call("GET", "/recall?" + urlencode({"q": marker, "tag": "smoke"}))
assert status == 200 and results
status, answer = call("GET", "/ask?" + urlencode({"q": f"Where is {marker}?"}))
assert status == 200 and answer["had_context"]
status, connections = call("GET", "/surface")
assert status == 200 and isinstance(connections, list)
for memory_id in created:
    status, result = call("DELETE", f"/memory/{memory_id}")
    assert status == 200 and result["deleted"] == memory_id
print("Attic live smoke test: ok")
