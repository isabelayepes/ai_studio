Followed instructions here: https://modelcontextprotocol.io/docs/develop/build-server
Smithery yaml file follows format here: https://smithery.ai/docs/build/project-config/smithery-yaml#smithery-yaml 

Terminal commands I used to run the server:
`curl -LsSf https://astral.sh/uv/install.sh | sh`
`source $HOME/.local/bin/env`
`uv init weather`
`cd weather`
`uv venv`
`source .venv/bin/activate`
`uv add "mcp[cli]" httpx`
`uv pip install fastmcp`
`uv run weather.py`

Then you can ensure the Claude Desktop's Local MCP Servers' config json in settings>developer has:

```
{
  "mcpServers": {
    "weather": {
      "command": "/Users/isabelayepes/.local/bin/uv",
      "args": [
        "--directory",
        "[absolute-path]/ai_studio/hw3/weather/src",
        "run",
        "weather.py"
      ]
    }
  }
}
```

For smithery.ai deployment, I needed to move weather.py into a src folder.