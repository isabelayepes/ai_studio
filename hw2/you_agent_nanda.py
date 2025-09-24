#!/usr/bin/env python3
import os, json
from nanda_adapter import NANDA
from crewai import Agent, Task, Crew
from langchain_anthropic import ChatAnthropic

from you_agent_ollama import Persona, persona_prompt

def create_you_agent_improvement():
    llm = ChatAnthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-haiku-20240307",
        temperature=0.3,
    )

    YOU = Persona()
    you_agent = Agent(
        role="Personal agent",
        goal=("Represent the user in conversations and tasks; draft messages, plans, "
              "and code consistent with their background, skills, and tone."),
        backstory=persona_prompt(YOU),
        llm=llm,
        verbose=False,
    )

    def improve(message_text: str) -> str:
        task = Task(
            description=(
                f"{message_text}\n\n"
                f"- Speak in the first person as \"{YOU.name}\".\n"
                "- Do NOT say you are Claude or an AI assistant.\n"
                "- Follow the persona, strengths, interests, and constraints above.\n"
                "- Keep it concise and specific."
            ),
            expected_output="A concise, helpful reply in the user's voice.",
            agent=you_agent,
        )
        result = Crew(agents=[you_agent], tasks=[task]).kickoff()

        # ---- normalize to plain text ----
        if isinstance(result, str):
            return result

        # common CrewAI attrs
        for attr in ("final_output", "output", "raw"):
            try:
                val = getattr(result, attr)
                if isinstance(val, str) and val.strip():
                    return val
            except Exception:
                pass

        # dict-ish?
        try:
            if isinstance(result, dict):
                # prefer common keys
                for k in ("final_output", "output", "text", "response"):
                    if k in result and isinstance(result[k], str) and result[k].strip():
                        return result[k]
                return json.dumps(result, ensure_ascii=False)
        except Exception:
            pass

        # fallback: stringify anything else
        try:
            return str(result)
        except Exception:
            return "Sorry—produced a non-text result; please try again."

    return improve

def main():
    nanda = NANDA(create_you_agent_improvement())
    nanda.start_server_api(os.getenv("ANTHROPIC_API_KEY"), os.getenv("DOMAIN_NAME"))

if __name__ == "__main__":
    main()
