#!/usr/bin/env python3
# Submission-ready: CrewAI-style persona + Anthropic via LangChain, parsed to str.
# Env needed: ANTHROPIC_API_KEY, DOMAIN_NAME
# Certs in CWD: ./fullchain.pem ./privkey.pem

import os
from nanda_adapter import NANDA
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Reuse your HW1 persona
from you_agent_ollama import Persona, persona_prompt

def create_you_agent_improvement():
    YOU = Persona()

    # Anthropic LLM (Haiku) via LangChain
    llm = ChatAnthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-haiku-20240307",
        temperature=0.3,
    )

    # System prompt pins your persona
    system_prompt = (
        persona_prompt(YOU)
        + "\n\nIMPORTANT:\n"
        + f"- Speak as \"{YOU.name}\" in first person.\n"
        + "- Do NOT say you are Claude or an AI assistant.\n"
        + "- Be concise and specific.\n"
    )

    # Build once; StrOutputParser guarantees a plain string
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{message}")
    ])
    chain = prompt | llm | StrOutputParser()

    def improve(message_text: str) -> str:
        try:
            text = chain.invoke({"message": message_text})
            return text.strip() if isinstance(text, str) else str(text)
        except Exception as e:
            # Always return a string so the adapter never sends non-text
            return f"Sorry—error: {type(e).__name__}: {e}"

    return improve

def main():
    NANDA(create_you_agent_improvement()).start_server_api(
        os.getenv("ANTHROPIC_API_KEY"),
        os.getenv("DOMAIN_NAME"),
    )

if __name__ == "__main__":
    main()

