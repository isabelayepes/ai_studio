#!/usr/bin/env python3
import os
from nanda_adapter import NANDA
from crewai import Agent, Task, Crew
from langchain_anthropic import ChatAnthropic

# import your persona utils from HW1 file in same folder
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
            description=f"{message_text}\n\nFollow the persona and constraints above.",
            expected_output="A concise, helpful reply in the user's voice.",
            agent=you_agent,
        )
        crew = Crew(agents=[you_agent], tasks=[task])
        return str(crew.kickoff())
    return improve

def main():
    nanda = NANDA(create_you_agent_improvement())
    nanda.start_server_api(
        os.getenv("ANTHROPIC_API_KEY"),
        os.getenv("DOMAIN_NAME"),  # e.g., myisabelaagent.duckdns.org
    )

if __name__ == "__main__":
    main()
