"""
ADA v2.5 — Self-improvement engine.
Analiza el sistema ADA: cuellos de botella, servicios innecesarios, mejoras posibles.
Puede proponer cambios en prompts y optimización de arquitectura. Nunca lanza excepciones.
"""
from typing import List, Optional

from ada_core.reasoning_engine import reason_about

SYSTEM_CONTEXT = """
El sistema ADA es un agente autónomo con: ada_core (conversación, razonamiento, memoria, estrategia, scheduler),
memory_service (key-value), postgres (goals, memories, ideas, experiences, opportunities).
Opcional: logging, policy, simulation, task-runner, financial-ledger, n8n (perfil extended).
Ollama en host para LLM. Interfaz web (chat_interface) para conversar.
"""


def analyze_system_bottlenecks() -> str:
    """Detecta cuellos de botella y servicios innecesarios en la arquitectura actual."""
    prompt = SYSTEM_CONTEXT + """

Analiza la arquitectura ADA actual.
Detecta:
- cuellos de botella (qué puede ralentizar o fallar)
- servicios innecesarios para un núcleo mínimo
- mejoras posibles (sin cambiar código, solo recomendaciones)

Responde en texto claro y breve (máximo 15 líneas)."""

    return reason_about(prompt).strip()


def suggest_prompt_improvements(current_prompt: str, issue: str = "") -> str:
    """Sugiere mejoras para un prompt dado. issue: descripción del problema (opcional)."""
    if not current_prompt or not current_prompt.strip():
        return ""
    issue_ctx = f" Problema a mejorar: {issue}." if issue else ""
    prompt = f"""Prompt actual (fragmento):
---
{current_prompt[:1500]}
---
{issue_ctx}

Sugiere 1-3 mejoras concretas para este prompt (más claridad, mejor formato, menos ambigüedad). Breve."""

    return reason_about(prompt).strip()


def analyze_recent_errors(errors_summary: List[str]) -> str:
    """Analiza un resumen de errores recientes y propone correcciones."""
    if not errors_summary:
        return ""
    lines = "\n".join(f"- {e[:200]}" for e in errors_summary[:20])
    prompt = f"""Errores recientes del sistema ADA:

{lines}

Analiza patrones y propón 1-3 acciones para reducir estos errores (configuración, reintentos, simplificación). Breve."""

    return reason_about(prompt).strip()
