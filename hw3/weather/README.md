Followed instructions here https://modelcontextprotocol.io/docs/develop/build-server :

`curl -LsSf https://astral.sh/uv/install.sh | sh`
`source $HOME/.local/bin/env`
`uv init weather`
`cd weather`
`uv venv`
`source .venv/bin/activate`
`uv add "mcp[cli]" httpx`
`uv pip install fastmcp`
`uv run weather.py`