# Brasaland MCP servers

MCP servers live here (not under `services/`).

| Server | Path | Port | Auth |
|--------|------|------|------|
| Company tools (incidents + inventory) | `brasaland_tools/` | `8100` | OAuth via **mcpauth** |

```bash
uv run python -m mcps.brasaland_tools
```

Docs: [`docs/mcp/mcp-oauth-tools.md`](../docs/mcp/mcp-oauth-tools.md)
