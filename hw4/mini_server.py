# mini_server.py
from mcp.server.fastmcp import FastMCP
import sys, traceback, os

app = FastMCP("mini")

@app.tool()
def ping(payload: dict) -> dict:
    return {"pong": True}

if __name__ == "__main__":
    print("mini_server: starting", file=sys.stderr, flush=True)
    try:
        app.run(transport="stdio")  # speak JSON-RPC on stdin/stdout
    except Exception:
        print("mini_server: crashed:\n" + traceback.format_exc(), file=sys.stderr, flush=True)
        os._exit(1)
