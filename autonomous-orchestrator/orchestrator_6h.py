"""
A.D.A — Orquestador autónomo Misión 6h
Aprendizaje completamente autónomo: simula 10-15 propuestas de ingresos, consolida score
y genera plan final pendiente de aprobación humana. No ejecuta task-runner.
"""
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

# Entorno (Docker Compose)
AGENT_URL = os.getenv("AGENT_URL", "http://agent-core:3001").rstrip("/")
MEMORY_URL = os.getenv("MEMORY_URL", "http://memory-db:3005").rstrip("/")
LOG_URL = os.getenv("LOG_URL", "http://logging-system:3006").rstrip("/")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
MISSION_DURATION_HOURS = float(os.getenv("MISSION_DURATION_HOURS", "24"))
CYCLE_MINUTES = int(os.getenv("CYCLE_MINUTES", "20"))
NOTIFY_INTERVAL_HOURS = float(os.getenv("NOTIFY_INTERVAL_HOURS", "2"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))
SPAWN_AGENT_NAME = os.getenv("SPAWN_AGENT_NAME", "ALMA")
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "0.7"))

# Ideas base de propuestas de ingresos digitales (si no hay Ollama o fallo)
DEFAULT_PROPOSALS = [
    {"task_name": "digital_product_ebook", "details": {"description": "Ebook o guía digital sobre automatización/DevOps", "channel": "web"}},
    {"task_name": "api_microservicio", "details": {"description": "API o microservicio de pago por uso", "channel": "web"}},
    {"task_name": "curso_online", "details": {"description": "Curso online sobre infraestructura o desarrollo", "channel": "web"}},
    {"task_name": "consultoria_tecnica", "details": {"description": "Consultoría técnica remota (Docker, cloud)", "channel": "email/telegram"}},
    {"task_name": "bot_telegram_premium", "details": {"description": "Bot de Telegram con funcionalidades premium", "channel": "telegram"}},
    {"task_name": "plantillas_automatizacion", "details": {"description": "Plantillas Docker/CI vendidas en marketplace", "channel": "web"}},
    {"task_name": "monitoreo_saas", "details": {"description": "SaaS de monitoreo ligero para pequeños equipos", "channel": "web"}},
    {"task_name": "newsletter_tecnica", "details": {"description": "Newsletter técnica con sponsors o suscripción", "channel": "email"}},
    {"task_name": "soporte_patronaje", "details": {"description": "GitHub Sponsors / Patreon para proyectos open source", "channel": "web"}},
    {"task_name": "auditoria_seguridad", "details": {"description": "Auditorías de seguridad o revisión de código", "channel": "email"}},
    {"task_name": "webinar_workshop", "details": {"description": "Webinar o workshop en vivo de pago", "channel": "web"}},
    {"task_name": "plugin_herramientas", "details": {"description": "Plugins o extensiones para herramientas populares", "channel": "web"}},
]


def _get(path: str, base: str = MEMORY_URL) -> tuple:
    try:
        r = requests.get(f"{base}{path}", timeout=REQUEST_TIMEOUT)
        return (r.json() if r.text else {}, r.status_code)
    except requests.RequestException as e:
        return ({"error": str(e)}, 500)


def _post(url: str, json_data: dict) -> tuple:
    try:
        r = requests.post(url, json=json_data, timeout=REQUEST_TIMEOUT)
        return (r.json() if r.text else {}, r.status_code)
    except requests.RequestException as e:
        return ({"error": str(e)}, 500)


def _post_params(url: str, params: dict, json_data: dict) -> tuple:
    try:
        r = requests.post(url, params=params, json=json_data, timeout=REQUEST_TIMEOUT)
        return (r.json() if r.text else {}, r.status_code)
    except requests.RequestException as e:
        return ({"error": str(e)}, 500)


def memory_set(key: str, value: dict) -> bool:
    resp, code = _post(f"{MEMORY_URL}/set", {"key": key, "value": value})
    return code == 200


def memory_get(key: str) -> Optional[dict]:
    data, code = _get(f"/get/{key}")
    if code != 200:
        return None
    return data.get("value")


def log_event(service_name: str, event_type: str, payload: dict) -> bool:
    resp, code = _post(f"{LOG_URL}/log", {
        "service_name": service_name,
        "event_type": event_type,
        "payload": payload,
    })
    return code == 200


def propose_no_execute(proposal: dict) -> Optional[dict]:
    """Llama a agent-core /propose con execute=False (solo simulación + policy, sin task-runner)."""
    resp, code = _post_params(
        f"{AGENT_URL}/propose",
        {"execute": False},
        proposal,
    )
    if code != 200:
        return None
    return resp


def send_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        return r.status_code == 200
    except Exception:
        return False


def ensure_mission_context():
    """Inicializa contexto de misión y recursos en memory-db."""
    context = {
        "resources": ["Mac mini", "Ollama", "Docker", "PostgreSQL"],
        "channels": ["Web-Admin", "Telegram", "Signal", "email"],
        "mission_start": datetime.now(timezone.utc).isoformat(),
        "mission_duration_hours": MISSION_DURATION_HOURS,
    }
    memory_set("ada_mission_context", context)
    memory_set("ada_resources", {"list": context["resources"]})
    memory_set("ada_channels", {"list": context["channels"]})
    log_event("autonomous-orchestrator", "ada_mission_started", context)


def compute_evolution_score(proposals: List[dict]) -> dict:
    """Score evolutivo: 35% ROI, 20% estabilidad, 20% precisión, 15% reducción riesgo, 10% eficiencia."""
    if not proposals:
        return {"ROI": 0, "stability": 0, "precision": 0, "risk_reduction": 0, "efficiency": 0, "composite": 0}
    rois = []
    risks = []
    for p in proposals:
        sim = p.get("simulation") or {}
        roi = sim.get("ROI")
        risk = sim.get("risk")
        if roi is not None:
            try:
                rois.append(float(roi))
            except (TypeError, ValueError):
                pass
        if risk is not None:
            if isinstance(risk, str):
                r = risk.strip().lower()
                if r in ("low", "bajo"):
                    risks.append(0.2)
                elif r in ("medium", "med", "medio"):
                    risks.append(0.5)
                elif r in ("high", "alto"):
                    risks.append(0.8)
                else:
                    try:
                        risks.append(float(risk))
                    except (TypeError, ValueError):
                        pass
            else:
                try:
                    risks.append(float(risk))
                except (TypeError, ValueError):
                    pass
    avg_roi = sum(rois) / len(rois) if rois else 0
    avg_risk = sum(risks) / len(risks) if risks else 0.5
    # Estabilidad y precisión simplificadas desde variabilidad
    stability = 1 - (max(rois) - min(rois)) if len(rois) > 1 else 0.8
    precision = 0.8
    risk_reduction = 1 - avg_risk
    efficiency = avg_roi * 0.5 + risk_reduction * 0.5
    composite = 0.35 * avg_roi + 0.20 * stability + 0.20 * precision + 0.15 * risk_reduction + 0.10 * efficiency
    return {
        "ROI": round(avg_roi, 3),
        "stability": round(max(0, min(1, stability)), 3),
        "precision": round(precision, 3),
        "risk_reduction": round(risk_reduction, 3),
        "efficiency": round(max(0, min(1, efficiency)), 3),
        "composite": round(max(0, min(1, composite)), 3),
    }


def run_cycle(proposal_template: dict, index: int) -> Optional[dict]:
    """Ejecuta un ciclo: propuesta → agent-core (sin ejecutar) → guardar y loguear."""
    out = propose_no_execute(proposal_template)
    if not out:
        return None
    proposal = out.get("proposal") or proposal_template
    simulation = out.get("simulation") or {}
    policy = out.get("policy") or {}
    record = {
        "index": index,
        "proposal": proposal,
        "simulation": simulation,
        "policy": policy,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "autonomous_orchestrator_6h",
    }
    # Añadir a lista en memory-db
    data = memory_get("ada_proposals_6h") or {}
    entries = data.get("proposals", []) if isinstance(data, dict) else []
    if not isinstance(entries, list):
        entries = []
    entries.append(record)
    memory_set("ada_proposals_6h", {"proposals": entries})
    log_event("autonomous-orchestrator", "learning_recorded", {"key": f"proposal_6h_{index}", "value": record})
    return record


def notify_progress(cycle: int, total_cycles: int, score: dict, elapsed_hours: float):
    """Escribe progreso en memory-db, logging y opcionalmente Telegram."""
    msg = (
        f"[A.D.A Misión 6h] Progreso a {elapsed_hours:.1f}h — "
        f"Ciclos: {cycle}/{total_cycles}. "
        f"Score compuesto: {score.get('composite', 0):.2f} (ROI: {score.get('ROI', 0):.2f}, riesgo red: {score.get('risk_reduction', 0):.2f})."
    )
    memory_set("ada_progress", {
        "last_update": datetime.now(timezone.utc).isoformat(),
        "cycle": cycle,
        "total_cycles": total_cycles,
        "elapsed_hours": elapsed_hours,
        "score": score,
        "message": msg,
    })
    log_event("autonomous-orchestrator", "ada_progress", {"message": msg, "score": score, "elapsed_hours": elapsed_hours})
    send_telegram(msg)


def build_final_plan(proposals: List[dict], score: dict) -> dict:
    """Construye el plan final a partir de la mejor propuesta por score compuesto."""
    if not proposals:
        return {
            "action": "Ninguna (no hubo propuestas simuladas)",
            "ROI_estimado": 0,
            "riesgo": 0,
            "recursos_requeridos": [],
            "canal_sugerido": "N/A",
            "status": "pendiente_aprobacion_humana",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    # Ordenar por ROI luego por menor riesgo
    def key(p):
        sim = p.get("simulation") or {}
        return (-(sim.get("ROI") or 0), sim.get("risk") or 1)
    best = max(proposals, key=key)
    prop = best.get("proposal") or {}
    sim = best.get("simulation") or {}
    details = prop.get("details") or {}
    return {
        "action": f"{prop.get('task_name', 'unknown')}: {details.get('description', '')[:200]}",
        "task_name": prop.get("task_name"),
        "details": details,
        "ROI_estimado": sim.get("ROI"),
        "riesgo": sim.get("risk"),
        "impact_financial": sim.get("impact_financial"),
        "infra_cost": sim.get("infra_cost"),
        "recursos_requeridos": ["Mac mini", "Ollama", "Docker", "PostgreSQL"],
        "canal_sugerido": details.get("channel", "Web-Admin"),
        "score_evolutivo": score,
        "status": "pendiente_aprobacion_humana",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _trigger_self_improve_and_spawn(score: dict, cycle_index: int) -> dict:
    """Si score < threshold: llama /self_improve y /spawn_agent una vez por ciclo."""
    composite = float((score or {}).get("composite", 0))
    if composite >= SCORE_THRESHOLD:
        return {"triggered": False, "reason": "score_ok", "composite": composite}
    self_resp, self_code = _get("/self_improve?trigger=orchestrator_low_score", base=AGENT_URL)
    spawn_resp, spawn_code = _get(f"/spawn_agent?agent_name={SPAWN_AGENT_NAME}", base=AGENT_URL)
    payload = {
        "triggered": True,
        "cycle": cycle_index,
        "composite": composite,
        "threshold": SCORE_THRESHOLD,
        "self_improve": {"code": self_code, "resp": self_resp},
        "spawn_agent": {"code": spawn_code, "resp": spawn_resp},
    }
    memory_set("ada_last_low_score_actions", payload)
    log_event("autonomous-orchestrator", "low_score_actions_triggered", payload)
    return payload


def main():
    duration_sec = MISSION_DURATION_HOURS * 3600
    cycle_sec = CYCLE_MINUTES * 60
    total_cycles = max(1, int(duration_sec / cycle_sec))
    proposals_to_run = DEFAULT_PROPOSALS[: min(15, max(10, total_cycles))]

    ensure_mission_context()
    last_notify = 0
    start = time.time()

    for i in range(total_cycles):
        elapsed = time.time() - start
        elapsed_hours = elapsed / 3600
        if elapsed >= duration_sec:
            break

        # Una propuesta por ciclo (10–15 distintas en total)
        template = proposals_to_run[i % len(proposals_to_run)]
        run_cycle(template, index=i)

        # Actualizar score evolutivo
        data = memory_get("ada_proposals_6h") or {}
        entries = data.get("proposals", []) if isinstance(data, dict) else []
        score = compute_evolution_score(entries)
        memory_set("evolution_score", score)
        log_event("autonomous-orchestrator", "learning_recorded", {"key": "evolution_score", "value": score})

        # Si el score cae por debajo del umbral: auto-mejora + spawn de agente
        low_score_action = _trigger_self_improve_and_spawn(score, i + 1)

        # Notificación cada NOTIFY_INTERVAL_HOURS
        if elapsed_hours - last_notify >= NOTIFY_INTERVAL_HOURS or last_notify == 0:
            notify_progress(i + 1, total_cycles, score, elapsed_hours)
            if low_score_action.get("triggered"):
                send_telegram(
                    f"[A.D.A] score bajo detectado ({score.get('composite', 0):.2f} < {SCORE_THRESHOLD:.2f}). "
                    f"Se ejecutó /self_improve y /spawn_agent({SPAWN_AGENT_NAME})."
                )
            last_notify = elapsed_hours

        time.sleep(max(1, cycle_sec - (time.time() - start - (i * cycle_sec))))

    # Plan final
    data = memory_get("ada_proposals_6h") or {}
    entries = data.get("proposals", []) if isinstance(data, dict) else []
    score = memory_get("evolution_score") or compute_evolution_score(entries)
    final = build_final_plan(entries, score)
    memory_set("final_plan_6h", final)
    log_event("autonomous-orchestrator", "ada_final_plan", final)
    memory_set("ada_progress", {
        "last_update": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "message": "Misión 6h completada. Plan final guardado en final_plan_6h. Pendiente de aprobación humana.",
        "final_plan_summary": {k: v for k, v in final.items() if k != "details"},
    })
    send_telegram(
        f"[A.D.A] Misión 6h completada. Plan final listo. "
        f"Acción: {final.get('action', '')[:150]}... ROI: {final.get('ROI_estimado')}, Riesgo: {final.get('riesgo')}. "
        f"Revisar en Web-Admin (final_plan_6h)."
    )
    print("Misión autónoma finalizada. Plan en memory-db: final_plan_6h")


if __name__ == "__main__":
    main()
