# Weather MCP Server (Python · FastMCP · Streamable HTTP)

[![smithery badge](https://smithery.ai/badge/@isabelayepes/weather)](https://smithery.ai/server/@isabelayepes/weather)

> **Credit:** Adapted from the official MCP “Build a server” tutorial:  
> https://modelcontextprotocol.io/docs/develop/build-server  
> Adapted to support both Smithery cloud deployment and local deployment (i.e. Claude Desktop)  

A minimal MCP server exposing two tools backed by the US National Weather Service (NWS):

- `get_forecast(latitude, longitude)` – short-term forecast for a location  
- `get_alerts(state)` – active alerts for a US state (2-letter code, e.g. `IL`)  
> NWS supports US locations only.

---

## Live (hosted on Smithery)

- **Endpoint:** `https://server.smithery.ai/@isabelayepes/weather/mcp`  
- **Auth header:** `Authorization: Bearer <smithery_api_key>`  
  (Opening the URL in a browser without the header shows `invalid_token` — expected.)

**Quick curl check (replace token):**
```bash
curl -N -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --data '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"local","version":"1.0.0"}}}' \
  https://server.smithery.ai/@isabelayepes/weather/mcp
```

---

## Local development

Requires Python ≥ 3.11 and [uv](https://github.com/astral-sh/uv).

```bash
uv venv && source .venv/bin/activate
uv sync

# STDIO mode (for Claude Desktop)
uv run python src/weather.py

# HTTP mode (simulate hosted env)
MCP_TRANSPORT=http PORT=8000 uv run python src/weather.py
```

### Claude Desktop config (macOS example)

`~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "weather": {
      "command": "/Users/isabelayepes/.local/bin/uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/weather",
        "run",
        "python",
        "src/weather.py"
      ]
    }
  }
}
```

---

## Deployment (Smithery)

This repo uses **runtime: container** with `Dockerfile` + `smithery.yaml`.  
The server builds an ASGI app via `mcp.streamable_http_app()` and serves it with **uvicorn**, adding **CORS** so browser clients can call `/mcp`.

> Note: In `mcp==1.15.0`, `FastMCP.run()` does **not** accept `host/port` for HTTP, so we run uvicorn directly.

---

## Project structure

```
hw3/weather/
├─ src/
│  └─ weather.py
├─ pyproject.toml        # deps: mcp[cli], httpx, starlette, uvicorn
├─ uv.lock
├─ Dockerfile
└─ smithery.yaml
```

---

## Links

- Hosted server page: https://smithery.ai/server/@isabelayepes/weather  
- Repo: https://github.com/isabelayepes/ai_studio/tree/main/hw3  
- Tutorial (source code basis): https://modelcontextprotocol.io/docs/develop/build-server
