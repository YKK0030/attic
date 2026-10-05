import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("attic")
BASE = os.getenv("ATTIC_URL", "http://localhost:4000")
KEY = os.getenv("ATTIC_API_KEY", "dev-key")


def call(method: str, path: str, payload: dict | None = None):
    request = Request(BASE + path, method=method, headers={"x-attic-key": KEY, "content-type": "application/json"})
    if payload:
        request.data = json.dumps(payload).encode()
    with urlopen(request, timeout=60) as response:
        return json.load(response)


@mcp.tool()
def remember(content: str, source: str, tags: list[str] | None = None, namespace: str = "default") -> str:
    """Store a memory in Attic."""
    return json.dumps(call("POST", "/memory", {"content": content, "source": source, "tags": tags or [], "namespace": namespace}))


@mcp.tool()
def recall(query: str, limit: int = 5, namespace: str = "default") -> str:
    """Search Attic memories semantically."""
    return json.dumps(call("GET", "/recall?" + urlencode({"q": query, "limit": limit, "namespace": namespace})))


@mcp.tool()
def ask(question: str, namespace: str = "default") -> str:
    """Ask a grounded question over Attic memories."""
    return json.dumps(call("GET", "/ask?" + urlencode({"q": question, "namespace": namespace})))


if __name__ == "__main__":
    mcp.run()


def main():
    mcp.run()
