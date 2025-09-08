# pip install crewai langchain langchain-community pydantic python-dotenv

import os
from typing import List
from pydantic import BaseModel
from crewai import Agent, Task, LLM

# Make sure `ollama serve` is running and you have the model pulled (e.g., `ollama pull deepseek-r1`)
# Point CrewAI/LiteLLM at your local Ollama
llm = LLM(
    model="ollama/deepseek-r1",           # provider/model together
    base_url="http://localhost:11434",    # Ollama default
    temperature=0.3,
)

# ---- Your persona (edit these) ----------------------------------------------

class Persona(BaseModel):
    name: str = "Isabela's Personal Agent"
    roles: List[str] = ["User's Representative Agent"]
    strengths: List[str] = [
        "Python, Pandas, scikit-learn, PyTorch basics",
        "Linear algrebra, ML fundamentals, and basic statistics",
        "Clean writing; explains with small examples",
    ]
    projects: List[str] = [
        "Rainfall prediction (Python+R), Kaggle X mentorship",
        "Music generation using a transformer (PyTorch, Lakh midi dataset)",
        "Two IBM internships (software dev including creating tools for AI agents, and agentic communication protocol such as ACP, and A2A)",
    ]
    interests: List[str] = [
        "AI alignment & impact",
        "AI architecture & data science",
        "Mindfulness",
        "Running & yoga",
    ]
    communication_style: str = (
        "Clear, concise, friendly. Avoids purple prose. Prefers examples."
    )
    constraints: List[str] = [
        "Cites assumptions if unsure",
        "Avoids overclaiming; prefers simple baseline before fancy methods",
    ]

YOU = Persona()

# ---- Helper to render persona into the agent system prompt ------------------

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
- Mirror {p.name}'s voice and preferences.
- Be explicit about tradeoffs and assumptions.
- Prefer reproducible, minimal examples over hand-wavy claims.
- If code is requested, write clean, runnable snippets with comments.

When asked for opinions or plans, answer as {p.name} would.
If a task is outside scope, propose a safe, concrete next step.
""".strip()

# ---- The Agent that “is you” -----------------------------------------------

you_agent = Agent(
    role="Personal agent",
    goal=(
        "Represent the user in conversations and tasks; draft messages, plans, "
        "and code consistent with their background, skills, and tone."
    ),
    backstory=persona_prompt(YOU),
    llm=llm,
    verbose=False,
)

# ---- Example Tasks (pick/modify what your HW asks for) ----------------------

task_about_me = Task(
    description=(
        "Explain the user's background in 3 sentences"
        "Summarize their strengths, recent projects, and interests. "
    ),
    expected_output=(
        "A short intro paragraph."
    ),
    agent=you_agent,
)

task_cover_note = Task(
    description=(
        "Draft a concise 140–180 word networking note to a hiring manager for a "
        "data science or ML internship. Reflect the user's background and projects. "
        "Keep tone friendly, specific, and refrain from empty superlatives."
    ),
    expected_output="A single paragraph, 140–180 words.",
    agent=you_agent,
)

if __name__ == "__main__":

    # run the first task
    about = task_about_me.execute_sync(agent=you_agent)

    # note  = task_cover_note.execute_sync(agent=you_agent)

    print("\n=== ABOUT ME ===\n")
    print(about)

    # print("\n=== COVER NOTE ===\n")
    # print(note)
