# you_agent_ollama.py
# deps: mcp, kokoro-tts (server side), soundfile, numpy, spacy(en), crewai, langchain, pydantic, python-dotenv
# make sure Ollama is running and you've pulled a model (e.g., `ollama pull llama3.1:8b-instruct` or `deepseek-r1`)

import os
import re
from typing import List
from pydantic import BaseModel
from crewai import Agent, Task, LLM, Tool
from speech_mcp_client import tts, stt

# ------------- LLM via Ollama -------------
# Tip: to minimize <think> blocks, try an instruct model like "ollama/llama3.1:8b-instruct"
LLM_MODEL = os.getenv("OLLAMA_MODEL", "ollama/deepseek-r1")

llm = LLM(
    model=LLM_MODEL,
    base_url="http://localhost:11434",
    temperature=0.3,
)

# ------------- Persona -------------
class Persona(BaseModel):
    name: str = "Isabela"
    roles: List[str] = ["User's Representative Agent"]
    strengths: List[str] = [
        "Python, Pandas, scikit-learn, PyTorch basics",
        "Linear algebra, ML fundamentals, basic statistics",
        "Clean writing; explains with small examples",
    ]
    projects: List[str] = [
        "Rainfall prediction (Python+R), Kaggle X mentorship",
        "Music generation using a transformer (PyTorch, Lakh MIDI dataset)",
        "Two IBM internships (software dev + AI agents / A2A protocols)",
    ]
    interests: List[str] = [
        "AI alignment & impact",
        "AI architecture & data science",
        "Mindfulness",
        "Running & yoga",
    ]
    communication_style: str = "Clear, concise, friendly. Avoids purple prose. Prefers examples."
    constraints: List[str] = [
        "Cites assumptions if unsure",
        "Avoids overclaiming; start simple before fancy methods",
    ]

YOU = Persona()

def persona_prompt(p: Persona) -> str:
    return f"""
You are {p.name}'s representative agent.

ROLES: {", ".join(p.roles)}
STRENGTHS: {", ".join(p.strengths)}
EXPERIENCE: {", ".join(p.projects)}
INTERESTS: {", ".join(p.interests)}

COMMUNICATION STYLE: {p.communication_style}
CONSTRAINTS: {", ".join(p.constraints)}

OPERATING PRINCIPLES:
- You are a personal agent for {p.name}'s preferences.
- Be explicit about tradeoffs and assumptions.
- Prefer reproducible, minimal examples over hand-wavy claims.
- If code is requested, write clean, runnable snippets with comments.

Reply with a single natural paragraph unless explicitly asked for lists or sections.
Do NOT include headings like "Outline:", "Summary:", or any chain-of-thought.
""".strip()

you_agent = Agent(
    role="Personal agent",
    goal=("Represent the user in conversations and tasks; draft messages, plans, "
          "and code consistent with their background, skills, and tone."),
    backstory=persona_prompt(YOU),
    llm=llm,
    verbose=False,
)

# ------------- Tools -------------
def tool_tts(text: str) -> str:
    """Return a filepath to generated audio."""
    out = tts(text, voice="af_heart", rate=1.0, save_path="speech/agent_say.wav")
    return out.get("audio_path", "")

def tool_stt(path: str) -> str:
    """Return a transcript from an audio file path."""
    out = stt(audio_path=path)
    return out.get("text", "")

tts_tool = Tool(
    name="synthesize_speech",
    description="Convert English text to speech (Kokoro). Input: plain text. Output: path to WAV file.",
    func=tool_tts,
)

stt_tool = Tool(
    name="transcribe_audio",
    description="Transcribe an audio file at a local path. Input: path to WAV/MP3. Output: transcript.",
    func=tool_stt,
)

you_agent.tools = [tts_tool, stt_tool]  # both available to the agent (task will only allow TTS)

# ------------- Task: write the paragraph AND call TTS -------------
about_task = Task(
    description=(
        "Explain the user's background in ~3 sentences. "
        "Summarize their strengths, recent projects, and interests. "
        "Reply as a single natural paragraph only (no headings, no code, no chain-of-thought). "
        "Then call the tool `synthesize_speech` with exactly that paragraph to create audio. "
        "Return ONLY a JSON object with these keys:\n"
        '{"text": "<the paragraph>", "audio_path": "<wav path returned by the tool>"}'
    ),
    expected_output='A single JSON object with keys "text" and "audio_path".',
    agent=you_agent,
    tools=[tts_tool],  # only TTS is allowed in this task
)

# ------------- Cleaner (still handy if you ever need it) -------------
THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)

def clean_for_tts(text: str) -> str:
    s = THINK_RE.sub("", text)
    s = re.sub(r"(?im)^\s*(outline|summary|raw|output\s*format)\s*:.*$", "", s)
    s = re.sub(r"```.*?```", "", s, flags=re.DOTALL)
    s = re.sub(r"\s+\n", "\n", s).strip()
    return s

def to_text(task_out) -> str:
    for attr in ("output", "raw_output", "raw", "result", "final_output"):
        v = getattr(task_out, attr, None)
        if isinstance(v, str) and v.strip():
            return v
    return str(task_out)

# ------------- Main -------------
if __name__ == "__main__":
    import json

    # 1) Optional: STT is separate from TTS/LLM
    wav_path = "samples/isabela.wav"
    if os.path.exists(wav_path):
        stt_res = stt(audio_path=wav_path)
        transcript = stt_res.get("text", "") or ""
        print("Speech to text:", transcript)

    # 2) Single task that writes the paragraph AND calls TTS via tool
    task_out = about_task.execute_sync(agent=you_agent)

    # Robust JSON extraction (in case the model adds extra text)
    def extract_json_block(s: str) -> str:
        s = s.strip()
        start = s.find("{")
        end = s.rfind("}")
        return s[start:end+1] if start != -1 and end != -1 and end > start else s

    raw = to_text(task_out).strip()
    try:
        data = json.loads(extract_json_block(raw))
    except Exception:
        data = {}

    text = data.get("text", "").strip()
    audio_path = data.get("audio_path", "").strip()

    # Optional: post-clean the text you display (audio already produced by tool)
    display_text = clean_for_tts(text) if text else text

    print("\n=== ABOUT (clean) ===\n", display_text or "(none)")
    print("\nAudio saved to:", audio_path or "(none)")
    if audio_path and os.path.exists(audio_path):
        print("Tip: on macOS you can play it with:\n  afplay", audio_path)

