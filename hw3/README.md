# Commands used
- Download `uv`: `curl -LsSf https://astral.sh/uv/install.sh | sh`
```
# Create a new directory for our project
uv init weather
cd weather

# Create virtual environment and activate it
uv venv
source .venv/bin/activate

# Install dependencies
uv add "mcp[cli]" httpx
uv pip install fastmcp

# Create our server file
touch weather.py
```
Followed: http://modelcontextprotocol.io/docs/develop/build-server

