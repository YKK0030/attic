# MCP setup

Install the adapter:

```sh
cd packages/mcp_server
python3 -m pip install -e .
```

Run it while Attic is available at `http://localhost:4000`:

```sh
ATTIC_URL=http://localhost:4000 ATTIC_API_KEY=dev-key python3 -m attic_mcp.server
```

The server exposes `remember`, `recall`, and `ask`.

For Claude Desktop, point the command at the installed Python executable and set `ATTIC_URL` and `ATTIC_API_KEY` in its MCP server environment.
