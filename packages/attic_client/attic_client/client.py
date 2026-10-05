import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class Attic:
    def __init__(self, url: str = "http://localhost:4000", key: str = "dev-key", namespace: str = "default"):
        self.url, self.key, self.namespace = url.rstrip("/"), key, namespace

    def _call(self, method: str, path: str, body: dict | None = None):
        request = Request(self.url + path, method=method, headers={"x-attic-key": self.key, "content-type": "application/json"})
        if body is not None:
            request.data = json.dumps(body).encode()
        with urlopen(request, timeout=90) as response:
            return json.load(response)

    def remember(self, content: str, source: str, tags: list[str] | None = None, namespace: str | None = None):
        return self._call("POST", "/memory", {"content": content, "source": source, "tags": tags or [], "namespace": namespace or self.namespace})

    def recall(self, query: str, limit: int = 5, tag: str | None = None, namespace: str | None = None):
        params = {"q": query, "limit": limit, "namespace": namespace or self.namespace}
        if tag:
            params["tag"] = tag
        return self._call("GET", "/recall?" + urlencode(params))

    def ask(self, question: str, namespace: str | None = None):
        return self._call("GET", "/ask?" + urlencode({"q": question, "namespace": namespace or self.namespace}))

    def forget(self, memory_id: str):
        return self._call("DELETE", f"/memory/{memory_id}")
