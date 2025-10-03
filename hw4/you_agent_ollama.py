# deps: mcp, kokoro-tts (server side), faster-whisper, soundfile, numpy,
#       spacy(en), crewai, crewai-tools, langchain, pydantic, python-dotenv
# make sure Ollama is running and you pulled a model (e.g. llama3.1:8b-instruct or deepseek-r1)

import os
import re
import json
from typing import List
from pydantic import BaseModel
from crewai import Agent, Task, LLM
from crewai_tools import tool   # <— NEW
from speech_mcp_client import tts, stt  # your MCP speech client

# ------------- LLM via Ollama -------------
# Tip: to minimize <think> blocks, try an instruct model like "ollama/llama3.1:8b-instruct"
LLM_MODEL = os.getenv("OLLAMA_MODEL", "ollama/deepseek-r1")
llm = LLM(model=LLM_MODEL, base_url="http://localhost:11434", temperature=0.3)

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

# ------------- Tools (via crewai-tools) -------------
@tool("synthesize_speech")
def tool_tts(text: str) -> str:
    """Convert English text to speech (Kokoro). Input: plain text. Output (stringified JSON): {"audio_path": "..."}"""
    out = tts(text, voice="af_heart", rate=1.0, save_path="speech/agent_say.wav")
    return json.dumps({"audio_path": out.get("audio_path", "")})

@tool("transcribe_audio")
def tool_stt(path: str) -> str:
    """Transcribe a local audio file (wav/mp3). Output (stringified JSON): {"text": "..."}"""
    out = stt(audio_path=path)
    return json.dumps({"text": out.get("text", "")})

# Make both tools available to the agent
you_agent.tools = [tool_tts, tool_stt]

# ------------- Task: write the paragraph (no tool use) -------------
about_task = Task(
    description=(
        "Explain the user's background in ~3 sentences. "
        "Summarize their strengths, recent projects, and interests. "
        "Reply as a single natural paragraph only."
    ),
    expected_output="One clean paragraph (~3 sentences), no headings.",
    agent=you_agent,
)

# ------------- Task: synthesize speech using the tool -------------
def make_tts_task(paragraph: str) -> Task:
    return Task(
        description=(
            "Synthesize the following paragraph to speech using the 'synthesize_speech' tool. "
            "Return ONLY a JSON object on the last line with the shape: "
            '{"audio_path": "<absolute-or-relative-path>"}\n'
            "Paragraph:\n"
            f"{paragraph}"
        ),
        expected_output='{"audio_path": "..."}',
        agent=you_agent,
        tools=[tool_tts],
    )

# ------------- Cleaner for LLM output -------------
THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
def clean_for_tts(text: str) -> str:
    s = THINK_RE.sub("", text)                         # drop <think>…</think>
    s = re.sub(r"(?im)^\s*(outline|summary|raw|output\s*format)\s*:.*$", "", s)
    s = re.sub(r"```.*?```", "", s, flags=re.DOTALL)   # strip fenced code
    s = re.sub(r"\s+\n", "\n", s).strip()              # tidy whitespace
    return s

def to_text(task_out) -> str:
    """Extract a string from CrewAI TaskOutput across versions."""
    for attr in ("output", "raw_output", "raw", "result", "final_output"):
        v = getattr(task_out, attr, None)
        if isinstance(v, str) and v.strip():
            return v
    return str(task_out)

def extract_json_block(s: str) -> str:
    s = s.strip()
    start = s.find("{")
    end = s.rfind("}")
    return s[start:end+1] if start != -1 and end != -1 and end > start else s

# ------------- Main -------------
if __name__ == "__main__":
    # 1) (Optional) run STT completely separate from TTS/LLM
    wav_path = "samples/isabela.wav"
    if os.path.exists(wav_path):
        stt_res = stt(audio_path=wav_path)  # direct call, not via tool
        transcript = stt_res.get("text", "") or ""
        print("Speech to text:", transcript)

    # 2) Generate the paragraph (no tools)
    about_out = about_task.execute_sync(agent=you_agent)
    about_text = clean_for_tts(to_text(about_out))
    print("\n=== ABOUT (clean) ===\n", about_text)

    # 3) Separate task that *only* synthesizes speech using the tool
    tts_task = make_tts_task(about_text)
    tts_out = tts_task.execute_sync(agent=you_agent)

    # Robustly parse JSON that the model returns
    raw = to_text(tts_out).strip()
    try:
        data = json.loads(extract_json_block(raw))
    except Exception:
        data = {"audio_path": ""}

    audio_path = data.get("audio_path", "").strip()
    print("\nAudio saved to:", audio_path or "(none)")
    if audio_path and os.path.exists(audio_path):
        print("Tip: on macOS you can play it with:\n  afplay", audio_path)
