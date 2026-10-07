import hmac
import json
import os
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from mcp.server.fastmcp import FastMCP
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings

BASE = os.getenv("ATTIC_URL", "http://localhost:4000")
KEY = os.getenv("ATTIC_API_KEY", "dev-key")
MCP_KEY = os.getenv("ATTIC_MCP_API_KEY", "")
MCP_PUBLIC_URL = os.getenv("ATTIC_MCP_PUBLIC_URL", "http://localhost:4100")
NAMESPACE = os.getenv("ATTIC_NAMESPACE", "aria:personal")
TRANSPORT = os.getenv("ATTIC_MCP_TRANSPORT", "streamable-http")
HOST = os.getenv("ATTIC_MCP_HOST", "127.0.0.1")
PORT = int(os.getenv("ATTIC_MCP_PORT", "4100"))
PATH = os.getenv("ATTIC_MCP_PATH", "/mcp")


class _TokenVerifier:
    async def verify_token(self, token: str) -> AccessToken | None:
        if not MCP_KEY or not hmac.compare_digest(token, MCP_KEY):
            return None
        return AccessToken(token=token, client_id="aria", scopes=["memory"], resource=MCP_PUBLIC_URL)


auth = {}
if MCP_KEY:
    auth = {
        "token_verifier": _TokenVerifier(),
        "auth": AuthSettings(
            issuer_url=MCP_PUBLIC_URL,
            resource_server_url=MCP_PUBLIC_URL,
            validate_token_resource=True,
        ),
    }
mcp = FastMCP("attic", **auth)


def call(method: str, path: str, payload: dict | None = None):
    request = Request(BASE + path, method=method, headers={"x-attic-key": KEY, "content-type": "application/json"})
    if payload:
        request.data = json.dumps(payload).encode()
    with urlopen(request, timeout=10) as response:
        return json.load(response)


@mcp.tool()
def remember(content: str, source: str, tags: list[str] | None = None) -> str:
    """Store a memory in Attic."""
    return json.dumps(call("POST", "/v1/memory", {
        "content": content,
        "source": source,
        "tags": tags or [],
        "namespace": NAMESPACE,
    }))


@mcp.tool()
def recall(query: str, limit: int = 5) -> str:
    """Search Attic memories semantically."""
    return json.dumps(call("GET", "/v1/recall?" + urlencode({
        "q": query,
        "limit": limit,
        "namespace": NAMESPACE,
    })))


@mcp.tool()
def ask(question: str) -> str:
    """Ask a grounded question over Attic memories."""
    return json.dumps(call("GET", "/v1/ask?" + urlencode({"q": question, "namespace": NAMESPACE})))


@mcp.tool()
def forget(memory_id: str) -> str:
    """Delete one memory from Attic."""
    encoded_id = quote(memory_id, safe="")
    memory = call("GET", f"/v1/memory/{encoded_id}")
    if memory.get("namespace") != NAMESPACE:
        return json.dumps({"error": "memory not found"})
    return json.dumps(call("DELETE", f"/v1/memory/{encoded_id}"))


@mcp.tool()
def health() -> str:
    """Check Attic health."""
    return json.dumps(call("GET", "/v1/health"))


def main():
    if TRANSPORT == "stdio":
        mcp.run(transport="stdio")
        return
    if not MCP_KEY:
        raise RuntimeError("ATTIC_MCP_API_KEY is required for HTTP transport")
    mcp.settings.host = HOST
    mcp.settings.port = PORT
    mcp.settings.streamable_http_path = PATH
    mcp.run(transport=TRANSPORT)


if __name__ == "__main__":
    main()
