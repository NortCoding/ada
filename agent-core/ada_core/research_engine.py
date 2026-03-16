"""
ADA v2.5 — Research engine.
Investiga internamente: analizar metas, proponer estrategias, comparar opciones.
Por ahora solo análisis interno (sin búsqueda web). Nunca lanza excepciones.
"""
from typing import List, Optional

from ada_core.reasoning_engine import reason_about, run_with_skill
from ada_core.tools import search_web, read_webpage


def research_goal(goal: str, context: str = "") -> str:
    """
    Analiza una meta y devuelve análisis/estrategias en texto.
    context: memorias o contexto relacionado (opcional).
    """
    if not goal or not goal.strip():
        return ""

    prompt = f"""Analiza esta meta: "{goal.strip()}"

Propón hasta 5 estrategias realistas considerando:
- el proyecto ADA (agente autónomo, IA local, Mac M1)
- habilidades técnicas disponibles (código, Ollama, automatización)
- recursos actuales (tiempo, sin gastar dinero innecesario)

Sé conciso. Responde en texto claro, una estrategia por línea o párrafo corto."""

    if context:
        prompt = f"Contexto previo:\n{context[:1500]}\n\n" + prompt

    return reason_about(prompt).strip()


def compare_options(question: str, options: List[str]) -> str:
    """Compara opciones (tecnologías, herramientas) y devuelve análisis."""
    if not question or not options:
        return ""
    opts_text = "\n".join(f"- {o}" for o in options[:10])
    prompt = f"{question}\n\nOpciones:\n{opts_text}\n\nCompara brevemente y recomienda."
    return reason_about(prompt).strip()


def evaluate_tools(tool_names: List[str], for_goal: str = "") -> str:
    """Evalúa herramientas para un objetivo. Análisis interno."""
    if not tool_names:
        return ""
    tools = "\n".join(f"- {t}" for t in tool_names[:15])
    goal_ctx = f" para: {for_goal}" if for_goal else ""
    prompt = f"Evalúa estas herramientas{goal_ctx}:\n{tools}\n\nIndica cuáles son más útiles y por qué (breve)."
    return reason_about(prompt).strip()


def web_research_topic(query: str, max_results: int = 3, max_pages_to_read: int = 2) -> List[dict]:
    """
    Realiza una investigación en internet sobre un tema específico.
    Busca, descarga páginas web verdaderas, usa Ollama para resumirlas, y
    devuelve las fuentes.
    """
    if not query or not query.strip():
        return []

    # 1. Buscar en DuckDuckGo
    results = search_web(query, max_results=max_results)
    if not results or "error" in results[0]:
        return [{"error": results[0].get("error", "Unknown search error")}] if results else []

    knowledge = []
    pages_read = 0

    # 2. Leer y resumir
    for r in results:
        if pages_read >= max_pages_to_read:
            break
            
        url = r.get("url")
        if not url:
            continue

        raw_content = read_webpage(url)
        if raw_content.startswith("Error"):
            continue

        # 3. Resumir contenido usando el cerebro local (Skill Investigador Web)
        prompt = (
            f"Please summarize the key points of the following web page content "
            f"contextualized for this subject: '{query}'.\n\nCONTENT:\n{raw_content}"
        )
        summary = run_with_skill("web_research", prompt)

        if summary:
            knowledge.append({
                "source_url": url,
                "title": r.get("title", "Unknown Title"),
                "summary": summary
            })
            pages_read += 1

    return knowledge

