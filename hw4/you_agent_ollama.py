# you_agent_ollama.py
# deps: mcp, kokoro-tts (server side), soundfile, numpy, spacy(en), crewai, langchain, pydantic, python-dotenv
# make sure Ollama is running and you've pulled a model (e.g., `ollama pull llama3.1:8b-instruct` or `deepseek-r1`)

import os
import re
from typing import List
from pydantic import BaseModel
from crewai import Agent, Task, LLM
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

# ------------- Task (no transcript) -------------
about_task = Task(
    description=(
        "Explain the user's background in ~3 sentences. "
        "Summarize their strengths, recent projects, and interests. "
        "Reply as a single natural paragraph only."
    ),
    expected_output="One clean paragraph (~3 sentences), no headings.",
    agent=you_agent,
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

# ------------- Main -------------
if __name__ == "__main__":
    # 1) Optional: speech-to-text first
    wav_path = "samples/isabela.wav"
    if os.path.exists(wav_path):
        stt_res = stt(audio_path=wav_path)
        result = stt_res.get("text", "") or ""
        print("Speech to text:", result)

    # 2) Run the “about me” task
    about_out = about_task.execute_sync(agent=you_agent)
    about_text = clean_for_tts(to_text(about_out))
    print("\n=== ABOUT (clean) ===\n", about_text)

    # 3) TTS with Kokoro (voice id: af_heart)
    res = tts(
        about_text,
        voice="af_heart",          # Kokoro voice id
        rate=1.0,
        save_path="speech/intro.wav"
    )
    print("\nAudio saved to:", res.get("audio_path"))
    if res.get("audio_path") and os.path.exists(res["audio_path"]):
        print("Tip: on macOS you can play it with:\n  afplay", res["audio_path"])
