from __future__ import annotations
import os, sys, json, anyio
from typing import Any, Dict

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.session import ClientSession

# Launch command (unbuffered)
MCP_SPEECH_CMD  = os.getenv("MCP_SPEECH_CMD", sys.executable)
MCP_SPEECH_ARGS = os.getenv("MCP_SPEECH_ARGS", "-u mcp_speech_server.py").split()
MCP_SPEECH_CWD  = os.getenv("MCP_SPEECH_CWD", os.getcwd())
SPEECH_DEBUG    = os.getenv("SPEECH_DEBUG") == "1"

async def _call_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    params = StdioServerParameters(
        command=MCP_SPEECH_CMD,
        args=MCP_SPEECH_ARGS,
        cwd=MCP_SPEECH_CWD,
        env=env,
    )
    if SPEECH_DEBUG:
        print("[client] launching:", MCP_SPEECH_CMD, MCP_SPEECH_ARGS, "cwd=", MCP_SPEECH_CWD)

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(
            read_stream=read_stream,
            write_stream=write_stream,
            client_info={"name": "you-agent", "version": "0.1.0"},
        ) as session:
            with anyio.fail_after(60):
                if SPEECH_DEBUG:
                    print("[client] initialize() …")
                await session.initialize()

            with anyio.fail_after(120):
                if SPEECH_DEBUG:
                    print(f"[client] call_tool({tool_name}) … args={arguments}")
                # FastMCP tool signature expects {"payload": {...}}
                result = await session.call_tool(tool_name, arguments={"payload": arguments})

    # Extract first JSON result
    for part in result.content:
        t = getattr(part, "type", None)
        if t == "json":
            return getattr(part, "data", {}) or {}
        if t == "text":
            try:
                return json.loads(part.text)
            except Exception:
                return {"text": part.text}
    return {}

# Convenience wrappers
def tts(text: str, *, voice: str | None = None, rate: float | None = None,
        save_path: str | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"text": text}
    if voice is not None: payload["voice"] = voice
    if rate is not None: payload["rate"] = rate
    if save_path is not None: payload["save_path"] = save_path
    return anyio.run(_call_tool, "synthesize_speech", payload)

def stt(*, audio_path: str | None = None, audio_b64: str | None = None,
        language: str | None = None) -> Dict[str, Any]:
    if not audio_path and not audio_b64:
        raise ValueError("Provide audio_path or audio_b64")
    payload: Dict[str, Any] = {}
    if audio_path: payload["audio_path"] = audio_path
    if audio_b64: payload["audio_b64"] = audio_b64
    if language: payload["language"] = language
    return anyio.run(_call_tool, "transcribe_audio", payload)

def list_voices() -> Dict[str, Any]:
    return anyio.run(_call_tool, "list_voices", {})
