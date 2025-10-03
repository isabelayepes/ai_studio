# HW4 — Voice Interaction via MCP (STT + TTS) + CrewAI + Ollama

This project adds speech-to-text and text-to-speech to an MCP server and wires it into a small CrewAI “personal agent” running on a local LLM via Ollama.

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
