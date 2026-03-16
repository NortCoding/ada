"""
ADA v2.5 — Opportunity engine.
Evalúa ideas con métricas: impacto, facilidad, velocidad, riesgo.
Fórmula: score = (impact * 0.4) + (ease * 0.3) + (speed * 0.3) - (risk * 0.2)
Permite priorizar ideas. Nunca lanza excepciones.
"""
from typing import List, Optional, Tuple

from ada_core.reasoning_engine import reason_about

# Pesos: score = (impact * 0.4) + (ease * 0.3) + (speed * 0.3). risk se guarda aparte.
W_IMPACT = 0.4
W_EASE = 0.3
W_SPEED = 0.3


def score_opportunity(impact: float, ease: float, speed: float, risk: float = 0) -> float:
    """
    Fórmula: score = (impact*0.4) + (ease*0.3) + (speed*0.3).
    risk no entra en el score; se almacena para referencia.
    Valores típicos 0-10. Devuelve redondeado 2 decimales.
    """
    s = (impact * W_IMPACT) + (ease * W_EASE) + (speed * W_SPEED)
    return round(max(0.0, min(10.0, s)), 2)


def evaluate_idea_with_llm(idea: str, goal: Optional[str] = None) -> Tuple[float, float, float, float]:
    """
    Pide al LLM que evalúe idea en impact, ease, speed, risk (0-10).
    Devuelve (impact, ease, speed, risk). En fallo devuelve (5,5,5,5).
    """
    goal_ctx = f" Meta: {goal}." if goal else ""
    prompt = f"""Evalúa esta idea (solo números 0-10, uno por línea):{goal_ctx}

Idea: {idea[:500]}

Responde exactamente 4 líneas:
impacto (0-10)
facilidad (0-10)
velocidad (0-10)
riesgo (0-10)"""

    out = reason_about(prompt)
    if not out:
        return (5.0, 5.0, 5.0, 5.0)

    values = []
    for line in out.strip().split("\n")[:4]:
        line = line.strip()
        for prefix in ("impacto", "facilidad", "velocidad", "riesgo", "impact", "ease", "speed", "risk", "-", "1.", "2.", "3.", "4."):
            if line.lower().startswith(prefix):
                line = line[len(prefix):].strip()
                break
        try:
            n = float(line.replace(",", ".").split()[0] if line.split() else "5")
            values.append(max(0, min(10, n)))
        except (ValueError, IndexError):
            values.append(5.0)

    while len(values) < 4:
        values.append(5.0)
    return (values[0], values[1], values[2], values[3])


def evaluate_and_score_idea(idea: str, goal_id: Optional[int] = None, goal_text: Optional[str] = None) -> dict:
    """
    Evalúa una idea con LLM y calcula score. Devuelve dict con idea, score, impact, ease, speed, risk.
    """
    impact, ease, speed, risk = evaluate_idea_with_llm(idea, goal_text)
    score = score_opportunity(impact, ease, speed, risk)
    return {
        "idea": idea,
        "score": score,
        "impact": round(impact, 2),
        "ease": round(ease, 2),
        "speed": round(speed, 2),
        "risk": round(risk, 2),
        "goal_id": goal_id,
    }
