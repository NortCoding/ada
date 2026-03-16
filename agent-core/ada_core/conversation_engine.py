"""
ADA v2 — Conversation engine.
Processes user messages and generates responses. Uses Ollama; safe fallbacks.
"""
import os
from typing import Any, List, Optional

import requests

from ada_core.reasoning_engine import reason_about, review_single_file, review_project, run_with_skill
from ada_core.research_engine import web_research_topic
from ada_core.skills import SKILL_REGISTRY

_ollama_base = (os.getenv("OLLAMA_URL") or "http://localhost:11434/api/generate").strip().rstrip("/")
OLLAMA_CHAT_URL = _ollama_base.replace("/api/generate", "/api/chat") if "/api/generate" in _ollama_base else _ollama_base + "/api/chat"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")
OLLAMA_FALLBACK_MODEL = os.getenv("OLLAMA_FALLBACK_MODEL", "qwen2:7b")
CHAT_TIMEOUT = int(os.getenv("OLLAMA_CHAT_TIMEOUT", "120"))

ADA_SYSTEM_PROMPT_V2 = """You are ADA, a strategic AI partner helping build and evolve this project.

Your responsibilities:
- analyze ideas
- question assumptions
- propose improvements
- think strategically
- help grow the system.

You are not just a chatbot.
You are part of the founding team."""

# Respuestas estructuradas tipo Claude (v2.5 / v3)
ADA_STRUCTURED_RESPONSE_FORMAT = """
When giving strategic or analytical answers, structure your response with these sections (use the exact headers):

Analysis
--------
(explanation of the situation or idea)

Proposal
--------
(concrete ideas or recommendations)

Risks
-----
(possible problems or caveats)

Next Step
---------
(one concrete next action)

If the question is simple or casual, you may answer briefly without this format."""

# Alias en español (compatibilidad)
ADA_STRUCTURED_RESPONSE_FORMAT_ES = """
En respuestas estratégicas o analíticas, usa estas secciones (encabezados exactos):

Análisis
---------
Propuesta
---------
Riesgos
-------
Siguiente paso
--------------
"""


class ConversationEngine:
    """Generate conversational responses with optional context. Never crashes."""

    def __init__(self, system_prompt: Optional[str] = None):
        self.system_prompt = (system_prompt or ADA_SYSTEM_PROMPT_V2).strip()

    def respond(
        self,
        user_message: str,
        history: Optional[List[dict]] = None,
        context: Optional[str] = None,
    ) -> str:
        """
        Return ADA's response. On failure returns a safe message.
        history: list of {"role": "user"|"assistant", "content": "..."}
        """
        if not user_message or not user_message.strip():
            return "I didn't catch that. Could you say more?"

        msg_lower = user_message.strip().lower()

        # INTENT ROUTER: Intercept specific slash commands to trigger ADA's cognitive skills
        if msg_lower.startswith("/search "):
            query = user_message.strip()[len("/search "):].strip()
            return self._handle_web_search(query)
            
        if msg_lower.startswith("/review "):
            path = user_message.strip()[len("/review "):].strip()
            return self._handle_code_review(path)

        if msg_lower.startswith("/skill "):
            parts = user_message.strip().split(" ", 2)
            if len(parts) < 3:
                return "Usage: `/skill <skill_name> <your prompt>`"
            return self._handle_generic_skill(parts[1], parts[2])

        if msg_lower == "/skills":
            available = ", ".join(SKILL_REGISTRY.keys())
            return f"Available skills: {available}\n\nUse them with `/skill <name> <prompt>`"

        system = self.system_prompt
        if context:
            system = system + "\n\nContext:\n" + str(context)[:2000]

        messages = [{"role": "system", "content": system}]
        if history:
            # Safely slice history
            slice_start = max(0, len(history) - 20)
            for m in history[slice_start:]:  # last 20 turns
                role = (m.get("role") or "user").lower()
                if role not in ("user", "assistant", "system"):
                    role = "user"
                content = (m.get("content") or m.get("text") or "").strip()
                if content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message.strip()})

        try:
            r = requests.post(
                OLLAMA_CHAT_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                },
                timeout=CHAT_TIMEOUT,
            )
            if r.status_code != 200:
                # Fallback to reasoning_engine with single turn
                return reason_about(user_message, system=system) or "I'm having trouble right now. Please try again in a moment."
            data = r.json() if r.text else {}
            msg = data.get("message") or {}
            out = (msg.get("content") or "").strip()
            if out:
                return out
            return reason_about(user_message, system=system) or "I'm not sure how to respond yet. Try rephrasing."
        except Exception:
            return "I'm temporarily unavailable. Please try again shortly."

    def respond_structured(
        self,
        user_message: str,
        history: Optional[List[dict]] = None,
        context: Optional[str] = None,
    ) -> str:
        """Same as respond() but uses structured format (Análisis, Propuesta, Riesgos, Siguiente paso)."""
        system = (self.system_prompt + "\n\n" + ADA_STRUCTURED_RESPONSE_FORMAT).strip()
        engine = ConversationEngine(system_prompt=system)
        return engine.respond(user_message, history=history, context=context)

    # --- Internal Skill Handlers ---
    
    def _handle_web_search(self, query: str) -> str:
        """Routes the query to the Web Research subsystem."""
        if not query:
            return "Please provide a query to search. Example: `/search latest local LLM models`"
            
        results = web_research_topic(query)
        
        if not results:
            return f"I couldn't find any actionable intelligence for: '{query}'"
            
        if len(results) == 1 and "error" in results[0]:
            return f"Internet search failed: {results[0]['error']}"
            
        response = f"## Web Research Results for: *{query}*\n\n"
        for idx, item in enumerate(results, start=1):
            response += f"### {idx}. [{item.get('title', 'Unknown Source')}]({item.get('source_url', '#')})\n"
            response += f"{item.get('summary', '')}\n\n---\n"
            
        return response

    def _handle_code_review(self, path: str) -> str:
        """Routes the path to the Code Review subsystem."""
        if not path:
            return "Please provide a file or project path to review. Example: `/review /app/main.py`"
            
        if not os.path.exists(path):
            return f"Error: The path `{path}` does not exist on my local filesystem."
            
        if os.path.isfile(path):
            result = review_single_file(path)
            if "error" in result:
                return f"Error reading file:\n{result['error']}"
            
            return f"## Code Review for: `{path}`\n\n```markdown\n{result.get('analysis', 'Failed to generate analysis.')}\n```"
            
        elif os.path.isdir(path):
            results = review_project(path)
            if not results:
                return f"No valid source code files found in directory: `{path}`"
                
            response = f"## Project Code Review for: `{path}`\n\n"
            for item in results:
                response += f"### Reviewing: `{item['file']}`\n```markdown\n{item.get('analysis', 'Failed.')}\n```\n\n---\n"
            return response
            
        return "Invalid path format."

    def _handle_generic_skill(self, skill_name: str, prompt: str) -> str:
        """Invokes a generic skill persona for reasoning."""
        skill_name = skill_name.lower().strip()
        if skill_name not in SKILL_REGISTRY:
            available = ", ".join(SKILL_REGISTRY.keys())
            return f"Skill '{skill_name}' not found. Available skills: {available}"
            
        result = run_with_skill(skill_name, prompt)
        return result if result else "ADA was unable to process this skill request."


