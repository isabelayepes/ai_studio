# HW4 — Voice Interaction via MCP (STT + TTS) + CrewAI + Ollama

This project adds speech-to-text and text-to-speech to an MCP server and wires it into a small CrewAI “personal agent” running on a local LLM via Ollama.

### Demo and Explanation
- [Demo Link]()
- Model: ollama/deepseek-r1 locally hosted.
- For the speech to text, the input `samples/isabela.wav` is "Hello, this is the real Isabela on the speech to text function". The output is that text which appears in the terminal after "Speech to Text:".
- For the text to speech, for the server test, the input is text of "It works — Kokoro speaking!". And the output is the audio file `out/speech/kokoro_hello.wav`.
- Then the CrewAI Demo the agent is provided with the backstory about me and prompted with the task:
```
# ------------- Task -------------
about_task = Task(
    description=(
        "Explain the user's background in ~3 sentences. "
        "Summarize their strengths, recent projects, and interests. "
        "Reply as a single natural paragraph only."
    ),
    expected_output="One clean paragraph (~3 sentences), no headings.",
    agent=you_agent,
)
```
- After generating a text response it is converted to speech audio using the mcp tool and saved to `out/speech/intro.wav`
- Insights observed:
    - Kokoro is only for English but lightweight and simple to run (just needs spaCy’s small English model). Coqui has a multilingual model but it is not for commercial use, and had torch weight loading errors. Piper's open source multilingual's Spanish modality did not sound good.
    - When using stdio, the MCP stream must be pure JSON-RPC. Any progress bars or installer logs printed to stdout will corrupt the stream and cause “Invalid JSON” errors. Fixes that worked: run Python unbuffered (-u/PYTHONUNBUFFERED=1), redirect noisy library output to stderr, and keep our own prints off stdout. (SSE/HTTP could avoid this, but stdio was simpler for local dev.)
    - FastMCP expects arguments under a {"payload": ...} wrapper. Missing that causes Pydantic “Field required” errors. The client now always sends arguments={"payload": arguments}.
    - Some MCP clients (e.g., my Claude Desktop setup) didn’t auto-play or download audio returned from tools. Saving files to a known folder (TTS_DOWNLOAD_DIR) and optionally exposing them via a tiny HTTP server (TTS_FILE_BASE_URL) made results easy to play (afplay on macOS) or click.

### What’s inside
- `mcp_speech_server.py` — MCP server exposing:
  - `transcribe_audio` (STT via faster-whisper)
  - `synthesize_speech` (TTS via Kokoro)
- `speech_mcp_client.py` — tiny client to call those MCP tools from Python.
- `you_agent_ollama.py` — CrewAI agent that:
  - (optionally) transcribes `samples/isabela.wav`
  - generates a short “about me” paragraph with Ollama
  - cleans output (removes `<think>…</think>`, headings)
  - speaks it with Kokoro
- `mini_server.py` - for debugging the mcp client if needed.
- `requirements.txt` - for a virtual environment to run the code.

### Virtual Environment Setup
- `python3.11 -m venv .venv`
- `source .venv/bin/activate`
- `pip install -r requirements.txt`
- `python -m spacy download en_core_web_sm` # Kokoro uses spaCy under the hood to clean and segment text into sentences/tokens before TTS

### Run MCP Client Test
```
export SPEECH_DEBUG=1
python - <<'PY'
import anyio
from speech_mcp_client import _call_tool
print(anyio.run(_call_tool, "ping", {}))   # client sends {"payload": {}}
PY

```
- Expected:
```
{'pong': True}
```

### Run the MCP server tests:
```
# save files to this folder
export TTS_DOWNLOAD_DIR=out
# mkdir -p out/speech # if not already there

# List voices (Kokoro)
python - <<'PY'
from speech_mcp_client import list_voices
print(list_voices())
PY

# TTS smoke test
python - <<'PY'
from speech_mcp_client import tts
res = tts("It works — Kokoro speaking!", voice="af_heart", rate=1.0, save_path="speech/kokoro_hello.wav")
print(res.get("audio_path"))
PY

# Play it (macOS)
afplay out/speech/kokoro_hello.wav

# STT test (optional)
python - <<'PY'
from speech_mcp_client import stt
print(stt(audio_path="out/speech/kokoro_hello.wav"))
PY

```

### Run the CrewAI demo:
```
# Start Ollama
ollama serve  # leave running in another terminal

# Reduce CrewAI chatter (optional)
export CREWAI_LOG_LEVEL=ERROR

# Run
python you_agent_ollama.py

# Play the generated audio
afplay out/speech/intro.wav

```
