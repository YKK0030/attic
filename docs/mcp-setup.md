# MCP setup

Install the adapter:

```sh
cd packages/mcp_server
python3 -m pip install -e .
```

Run it while Attic is available at `http://localhost:4000`:

```sh
ATTIC_URL=http://localhost:4000 \
ATTIC_API_KEY=dev-key \
ATTIC_MCP_API_KEY=replace-me \
ATTIC_MCP_PUBLIC_URL=http://localhost:4100 \
ATTIC_NAMESPACE=aria:personal \
python3 -m attic_mcp.server
```

The server exposes `remember`, `recall`, `ask`, `forget`, and `health` over
Streamable HTTP. HTTP transport requires the bearer `ATTIC_MCP_API_KEY`; the
server uses the separate `ATTIC_API_KEY` for its backend connection. Every
memory tool is limited to `ATTIC_NAMESPACE`.

For Claude Desktop, point the command at the installed Python executable and set `ATTIC_URL` and `ATTIC_API_KEY` in its MCP server environment.
