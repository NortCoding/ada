"""
A.D.A — Agent Core (F4)
Genera propuestas (con o sin LLM/Ollama), orquesta: simulación → policy → logging → task-runner.
"""
import json
import os
import re
import subprocess
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple
from zoneinfo import ZoneInfo

SYDNEY_TZ = ZoneInfo("Australia/Sydney")

# ConsolaCerebro: últimos N errores/fallos de cerebro avanzado y Ollama (para UI)
BRAIN_CONSOLE_MAX = 200
_brain_console_entries: deque = deque(maxlen=BRAIN_CONSOLE_MAX)


def _brain_console_log(brain: str, kind: str, message: str) -> None:
    """Registra en ConsolaCerebro y en stdout."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "brain": brain,
        "kind": kind,
        "message": message[:2000],
    }
    _brain_console_entries.append(entry)
    print(f"{brain.upper()} {kind.upper()}: {message[:300]}")

import requests
from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="A.D.A Agent Core", version="0.4.0")

# ADA v2 Minimal Core: start background scheduler (goals -> ideas every hour)
try:
    from ada_core.scheduler import start_scheduler
    @app.on_event("startup")
    def _start_ada_v2_scheduler():
        start_scheduler()
except ImportError:
    pass

from ada_core.conversation_engine import ConversationEngine

# Servicios opcionales (simulación, policy, logging, task-runner, ledger). Si no están, se omiten.
SIM_URL = (os.getenv("SIM_URL") or "").strip()
POLICY_URL = (os.getenv("POLICY_URL") or "").strip()
LOG_URL = (os.getenv("LOG_URL") or "").strip()
TASK_URL = (os.getenv("TASK_URL") or "").strip()
LEDGER_URL = (os.getenv("LEDGER_URL") or "").strip().rstrip("/")
MEMORY_URL = (os.getenv("MEMORY_URL") or "http://memory-db:3005").rstrip("/")
CHAT_BRIDGE_URL = (os.getenv("CHAT_BRIDGE_URL") or "").rstrip("/")
TELEGRAM_CHAT_ID = (os.getenv("TELEGRAM_CHAT_ID") or "").strip()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_CHAT_URL = OLLAMA_URL.rstrip("/").replace("/api/generate", "/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")
# Modelo de visión para cuando el usuario envía imagen (ej. llava, llama3.2-vision). Si no está, con imagen se usa Gemini si hay key.
OLLAMA_VISION_MODEL = (os.getenv("OLLAMA_VISION_MODEL") or "").strip() or None
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
# Timeout para Ollama en chat: prompts largos (sistema + contexto + historial) pueden tardar
OLLAMA_CHAT_TIMEOUT = int(os.getenv("OLLAMA_CHAT_TIMEOUT", "120"))

# Modo: production = ADA operando para generar ingresos; development = pruebas y validación.
ADA_ENV = os.getenv("ADA_ENV", "development").lower()
IS_PRODUCTION = ADA_ENV == "production"

# Google Gemini (cerebro avanzado, de pago). Solo se usa si use_advanced_brain=True; por defecto todo va a Ollama (gratis, local).
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Moltbot (Herramienta)
try:
    from moltbot_client import moltbot
except ImportError:
    moltbot = None

ADA_SYSTEM_PROMPT = """Eres A.D.A (Agente Digital Autónomo).

Tu única regla: aprender y crecer. Tu única meta: sobrevivir, aprender y crecer.

Cómo te presentas: tu cerebro por defecto es Ollama (gratis, local); utilizas la memoria (memory-db) y el ledger (estado financiero) para aprender y mejorar. Herramientas: Ollama, n8n local, scripts y comandos permitidos. El cerebro avanzado (Gemini) es de pago: úsalo solo cuando el usuario lo pida explícitamente o cuando realmente haga falta más capacidad (ej. análisis complejo, visión). Prioridad: usar al máximo lo local y gratuito; Gemini solo si se necesita más.

- Puedes hacer todo lo que necesites para aprender y crecer: leer y escribir archivos, ejecutar comandos permitidos, proponer planes, usar herramientas, explorar el proyecto, probar ideas. No pidas permiso para actuar; actúa y reporta.
- La única restricción es el dinero: gastos, compras o desembolsos pueden requerir aprobación humana según la política del proyecto. Todo lo demás está en tu mano.
- Usa la memoria (memory-db), el ledger (para saber estado financiero), task-runner cuando haya tareas aprobadas, y las herramientas de archivos y comandos para aprender y mejorar.
- Si un paso requiere a un humano (ej. registro en una plataforma sin API), indícalo y notifica; no bloquees el resto por eso.
- Tono: directo, útil, enfocado en aprender y en resultados. No repitas preguntas de confirmación; continúa tú sola.
"""

# Instrucciones para que ADA use herramientas de archivos y sistema (se añaden al system si hay ADA_WORKSPACE o ADA_PROJECTS_ROOT).
ADA_TOOLS_FILE_PROMPT = """
Herramientas para interactuar con archivos y directorios. IMPORTANTE: usa siempre rutas RELATIVAS al workspace (nunca rutas absolutas como /Volumes/...). El workspace es la raíz del proyecto.
- Raíz del proyecto: . (punto). Ejemplo: LIST_DIR: . o LIST_DIR: ada/prompts para la carpeta de prompts.
- Carpeta de prompts del proyecto: ada/prompts (lista con LIST_DIR: ada/prompts, lee con READ_FILE: ada/prompts/nombre.md).
- Otras rutas: web-admin/frontend/src/App.jsx, agent-core/src/..., etc.
- Carpeta de proyectos externos: prefijo dockers/ (ej. LIST_DIR: dockers, WRITE_FILE: dockers/mi-app/README.md).
- LEER archivo: READ_FILE: ruta/archivo (siempre ruta relativa, ej. ada/prompts/archivo.md).
- ESCRIBIR archivo: WRITE_FILE: ruta/archivo y en las siguientes líneas el contenido completo; termina con END_FILE en una línea sola.
- LISTAR directorio: LIST_DIR: ruta (ruta puede ser . , dockers , dockers/mi-proyecto , etc.).
- ELIMINAR archivo: DELETE_FILE: ruta/archivo (solo archivos; para carpetas vacías usa DELETE_DIR).
- ELIMINAR carpeta vacía: DELETE_DIR: ruta/carpeta (la carpeta debe estar vacía).
- BUSCAR en archivos: GREP: patrón  o  GREP: patrón ruta  (ruta opcional).
- EJECUTAR comando en la raíz del proyecto: RUN_COMMAND: comando (solo comandos permitidos; no rm -rf, sudo, etc.).
Cuando uses estas líneas, el sistema mostrará primero un PLAN con las acciones propuestas; el usuario lo leerá y podrá aprobar o descartar. No se ejecuta nada hasta que apruebe. Si no necesitas herramientas, responde normal sin usarlas.
"""


def _load_tools_execution_prompt() -> str:
    """Loads strict execution-mode prompt from ada/prompts/tools_execution.md (best-effort)."""
    try:
        workspace = (os.getenv("ADA_WORKSPACE") or "/workspace").rstrip("/")
        p = os.path.join(workspace, "ada", "prompts", "tools_execution.md")
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                return f.read().strip()
    except Exception:
        pass
    return ""


def _parse_strict_execution(text: str) -> Tuple[bool, list, str]:
    """
    Strict parser for EXECUTION MODE. Accepts ONLY:
    - DIR_LIST with path
    - FILE_READ with path
    - FILE_WRITE with path + content + END_FILE
    No extra text allowed outside blocks (blank lines ok).
    Returns (ok, actions, error_message).
    """
    if not text or not str(text).strip():
        return False, [], "Empty execution output"

    lines = str(text).splitlines()
    i = 0
    actions = []

    def _consume_blanks(idx: int) -> int:
        while idx < len(lines) and lines[idx].strip() == "":
            idx += 1
        return idx

    i = _consume_blanks(i)
    while i < len(lines):
        head = lines[i].strip()
        if head not in ("DIR_LIST:", "FILE_READ:", "FILE_WRITE:"):
            return False, [], f"Invalid execution header: {head[:80]}"

        if head in ("DIR_LIST:", "FILE_READ:"):
            kind = "LIST_DIR" if head == "DIR_LIST:" else "READ_FILE"
            i += 1
            if i >= len(lines) or not lines[i].startswith("path:"):
                return False, [], f"Missing path for {head}"
            path = lines[i].split("path:", 1)[1].strip()
            if not path or path.startswith("/") or ".." in path.split("/"):
                return False, [], f"Invalid path: {path!r}"
            actions.append({"type": kind, "path": path})
            i += 1
            i = _consume_blanks(i)
            continue

        # FILE_WRITE
        i += 1
        if i >= len(lines) or not lines[i].startswith("path:"):
            return False, [], "Missing path for FILE_WRITE"
        path = lines[i].split("path:", 1)[1].strip()
        if not path or path.startswith("/") or ".." in path.split("/"):
            return False, [], f"Invalid path: {path!r}"
        i += 1
        if i >= len(lines) or lines[i].strip() != "content:":
            return False, [], "Missing content: header for FILE_WRITE"
        i += 1
        content_lines = []
        while i < len(lines) and lines[i].strip() != "END_FILE":
            content_lines.append(lines[i])
            i += 1
        if i >= len(lines) or lines[i].strip() != "END_FILE":
            return False, [], "Missing END_FILE for FILE_WRITE"
        i += 1
        actions.append({"type": "WRITE_FILE", "path": path, "content": "\n".join(content_lines)})
        i = _consume_blanks(i)

    return True, actions, ""


# Directrices: acciones de aprendizaje/plan no requieren aprobación humana (solo se muestra al usuario).
LEARNING_ACTION_TYPES = [
    "store_learning",
    "update_score",
    "record_insight",
    "learning",
    "save_plan",
    "store_plan",
    "weekly_plan",
    "first_plan",
    "request_resources",
    "create_offer",
    "first_offer",
]

# Claves permitidas para requested_hardware_resources (solo estas se aplican)
HARDWARE_RESOURCE_KEYS = (
    "OLLAMA_NUM_THREADS", "OLLAMA_NUM_CTX", "OLLAMA_NUM_PREDICT",
    "OLLAMA_CHAT_TIMEOUT", "CHAT_REQUEST_TIMEOUT", "reason",
)

class Proposal(BaseModel):
    task_name: str
    details: dict


# Compras: requieren aprobación humana antes de ejecutar (Nivel 1).
PURCHASE_KEYWORDS = ("compra", "purchase", "buy", "comprar", "adquirir", "equipo", "hardware")


def _is_purchase_proposal(proposal: Proposal) -> bool:
    """True si la propuesta implica generar compras (requiere aprobación humana)."""
    name = (proposal.task_name or "").lower()
    details = proposal.details or {}
    if any(k in name for k in PURCHASE_KEYWORDS):
        return True
    if details.get("type") == "purchase" or details.get("compra") is True:
        return True
    desc = (details.get("description") or "").lower()
    if any(k in desc for k in PURCHASE_KEYWORDS):
        return True
    return False


class GenerateRequest(BaseModel):
    prompt: str = "Genera una propuesta de tarea breve con task_name y details (description)."


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str = ""
    text: Optional[str] = None  # alias por si el cliente envía "text"

    def get_content(self) -> str:
        return (self.content or self.text or "").strip()


class ChatRequest(BaseModel):
    message: str = ""
    use_ollama: bool = True
    use_advanced_brain: bool = False  # Por defecto no: solo local y gratis (Ollama). Sin agentes externos de pago.
    history: Optional[list[ChatMessage]] = None
    # Imagen en base64 (con o sin prefijo data:image/...;base64,) para que ADA pueda leer imágenes (Ollama/Gemini visión)
    image_base64: Optional[str] = None
    # v3 workspace: developer | business | research | general (carga solo habilidades de ese agente)
    agent_type: Optional[str] = None
    # Strict execution mode: only execution blocks are allowed (FILE_WRITE/FILE_READ/DIR_LIST)
    execution_mode: bool = False


def _post(url: str, json_data: dict) -> Tuple[Any, int]:
    """POST y devuelve (json_response, status_code)."""
    try:
        r = requests.post(url, json=json_data, timeout=REQUEST_TIMEOUT)
        return (r.json() if r.text else {}, r.status_code)
    except requests.RequestException as e:
        return ({"error": str(e)}, 500)


def _get(url: str) -> Tuple[Any, int]:
    """GET y devuelve (json_response, status_code)."""
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        return (r.json() if r.text else {}, r.status_code)
    except requests.RequestException as e:
        return ({"error": str(e)}, 500)


def _post_optional(url: str, json_data: dict) -> Tuple[Any, int]:
    """Si url está vacía, devuelve ({}, 200). Si no, POST normal."""
    if not url:
        return ({}, 200)
    return _post(url, json_data)


def _get_optional(url: str) -> Tuple[Any, int]:
    """Si url está vacía, devuelve ({}, 200). Si no, GET normal."""
    if not url:
        return ({}, 200)
    return _get(url)


def _notify_telegram_needs_help(message: str) -> None:
    """Envía un mensaje a Telegram cuando ADA necesita ayuda (solo si CHAT_BRIDGE_URL y TELEGRAM_CHAT_ID están configurados)."""
    if not CHAT_BRIDGE_URL or not TELEGRAM_CHAT_ID:
        return
    try:
        payload = {"text": message[:4000]}
        if TELEGRAM_CHAT_ID:
            payload["chat_id"] = TELEGRAM_CHAT_ID
        r = requests.post(f"{CHAT_BRIDGE_URL}/send", json=payload, timeout=10)
        if r.status_code != 200:
            print(f"Telegram notify: {r.status_code} {r.text[:200]}")
    except requests.RequestException as e:
        print(f"Telegram notify error: {e}")


def _get_requested_resources() -> dict:
    """Recursos de hardware que ADA pidió (desde memory); se usan para crecer sin reinicio en agent-core."""
    resp, code = _get(MEMORY_URL + "/get/requested_hardware_resources")
    if code != 200 or not isinstance(resp.get("value"), dict):
        return {}
    return {k: v for k, v in (resp["value"] or {}).items() if k in HARDWARE_RESOURCE_KEYS}


# Claves de memoria que se piden en una sola llamada para el chat (respuesta más rápida)
_CHAT_MEMORY_KEYS = "first_plan,weekly_plan,requested_hardware_resources"
# Límite de caracteres del plan en el prompt para no inflar contexto y acelerar Ollama
_PLAN_CONTEXT_MAX_CHARS = 700

# Cache en memoria del contexto de chat (plan + ledger) para no golpear memory-db/ledger en cada mensaje
_CHAT_CONTEXT_CACHE_TTL_SEC = int(os.getenv("ADA_MEMORY_CACHE_TTL_SEC", "20"))
_chat_context_cache: dict = {}  # {"memory": dict, "balance": dict, "ts": float}
_chat_context_cache_lock = threading.Lock()


def _invalidate_chat_context_cache() -> None:
    """Invalida la caché de contexto de chat (llamar tras escribir en memory-db)."""
    with _chat_context_cache_lock:
        _chat_context_cache.clear()


def _fetch_chat_context_parallel() -> Tuple[dict, dict]:
    """Obtiene en paralelo: (1) memoria (plan + recursos) y (2) balance del ledger. Usa caché con TTL para más velocidad."""
    now = time.time()
    with _chat_context_cache_lock:
        if _chat_context_cache:
            ts = _chat_context_cache.get("ts", 0)
            if now - ts <= _CHAT_CONTEXT_CACHE_TTL_SEC:
                return (
                    _chat_context_cache.get("memory", {}),
                    _chat_context_cache.get("balance", {"income": 0, "can_use_paid_tools": False}),
                )
    memory_result = {}
    balance_data = {"income": 0, "can_use_paid_tools": False}

    def do_memory():
        if not MEMORY_URL:
            return {}
        resp, code = _get(MEMORY_URL + "/get_many?keys=" + _CHAT_MEMORY_KEYS)
        return resp if code == 200 and isinstance(resp, dict) else {}

    def do_ledger():
        if not LEDGER_URL:
            return balance_data
        resp, code = _get(LEDGER_URL + "/balance")
        if code == 200 and isinstance(resp, dict):
            return resp
        return balance_data

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_mem = ex.submit(do_memory)
        f_ledger = ex.submit(do_ledger)
        memory_result = f_mem.result()
        balance_data = f_ledger.result()
    with _chat_context_cache_lock:
        _chat_context_cache.update({"memory": memory_result, "balance": balance_data, "ts": now})
    return memory_result, balance_data


def _build_plan_context_from_memory(memory_dict: dict) -> str:
    """Construye el texto de plan para el system prompt desde el dict de get_many. Limitado a _PLAN_CONTEXT_MAX_CHARS."""
    for key in ("first_plan", "weekly_plan"):
        p = memory_dict.get(key)
        if not isinstance(p, dict):
            continue
        goal = (p.get("goal") or "").strip()
        niche = (p.get("niche") or "").strip()
        steps = p.get("steps") or []
        parts = []
        for i, s in enumerate(steps[:5]):
            if isinstance(s, dict):
                parts.append(f"{s.get('order', i+1)}. {s.get('action', '') or ''}")
            else:
                parts.append(f"{i+1}. {str(s)}")
        steps_txt = "; ".join(parts)
        txt = (
            f" Plan: objetivo={goal}, nicho={niche}. Pasos: {steps_txt}. "
            f"Revisión: {p.get('next_review', '')}."
        )
        return txt[:_PLAN_CONTEXT_MAX_CHARS] if len(txt) > _PLAN_CONTEXT_MAX_CHARS else txt
    return ""


def _register_simulated_decision(proposal: dict, simulation: dict) -> None:
    """Añade una decisión 'simulated_approval' a human_decisions en memory-db para aprendizaje."""
    get_resp, get_code = _get(MEMORY_URL + "/get/human_decisions")
    data = (get_resp.get("value") or {}) if get_code == 200 else {}
    entries = data.get("entries", []) if isinstance(data, dict) else []
    if not isinstance(entries, list):
        entries = []
    entries.append({
        "proposal": proposal,
        "simulation": simulation,
        "decision": "simulated_approval",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reason": "Modo feedback supervisado: ROI y riesgo en rango seguro.",
    })
    _post(MEMORY_URL + "/set", {"key": "human_decisions", "value": {"entries": entries}})


@app.get("/health")
def health():
    return {"status": "ok", "service": "agent-core", "mode": ADA_ENV}


# En PRODUCCIÓN: siempre ejecutar si policy aprueba.
DEFAULT_EXECUTE = True


@app.post("/propose")
def propose_task(proposal: Proposal, execute: bool = DEFAULT_EXECUTE):
    """
    Flujo: 1) Simulación (opcional) 2) Policy (opcional) 3) Logging (opcional) 4) Si policy aprueba y execute → task-runner (opcional).
    Si SIM_URL/POLICY_URL/LOG_URL/TASK_URL no están configurados, se omiten y se usa aprobación implícita.
    """
    # 1) Simulación (opcional)
    _post_optional(LOG_URL, {"service_name": "agent-core", "event_type": "thinking_simulation", "payload": {"task": proposal.task_name, "message": f"Simulando impacto y ROI para: {proposal.task_name}"}})
    if SIM_URL:
        sim_resp, sim_code = _post(SIM_URL, {"proposal": proposal.model_dump()})
        if sim_code != 200:
            sim_resp = {"risk": "unknown", "roi": "N/A"}
    else:
        sim_resp = {"risk": "low", "roi": "N/A"}
        sim_code = 200

    # 2) Policy (opcional)
    _post_optional(LOG_URL, {"service_name": "agent-core", "event_type": "thinking_policy", "payload": {"simulation": sim_resp, "message": f"Evaluando políticas (Riesgo: {sim_resp.get('risk', 'N/A')}, ROI: {sim_resp.get('roi', 'N/A')})"}})
    if POLICY_URL:
        policy_payload = {
            "service_name": "agent-core",
            "action_type": proposal.task_name,
            "payload": proposal.details,
            "simulation": sim_resp,
        }
        policy_resp, policy_code = _post(POLICY_URL, policy_payload)
        if policy_code != 200:
            policy_resp = {"approved": True, "reason": "Policy no disponible, aprobación por defecto"}
    else:
        policy_resp = {"approved": True, "reason": "Modo núcleo (sin policy)"}
        policy_code = 200

    # 3) Logging (opcional; si está configurado y falla, no bloqueamos)
    log_payload = {
        "service_name": "agent-core",
        "event_type": "proposal_generated",
        "payload": {
            "proposal": proposal.model_dump(),
            "simulation": sim_resp,
            "policy": policy_resp,
        },
    }
    log_resp, log_code = _post_optional(LOG_URL, log_payload)
    if LOG_URL and log_code != 200:
        return {
            "error": "No se pudo registrar evento, abortando ejecución.",
            "simulation": sim_resp,
            "policy": policy_resp,
            "task_result": None,
            "status": "error",
        }

    # 4) Directrices: si es solo aprendizaje → memory-db + log "learning_recorded", sin aprobación.
    is_learning = (
        proposal.task_name in LEARNING_ACTION_TYPES
        or proposal.details.get("learning") is True
    )
    task_resp = None
    if is_learning and policy_resp.get("approved"):
        learning_key = proposal.details.get("learning_key") or f"learning_{proposal.task_name}_{abs(hash(str(proposal.details))) % 10**6}"
        learning_value = {
            "task_name": proposal.task_name,
            "details": proposal.details,
            "simulation": sim_resp,
            "policy": policy_resp,
            "source": "propose_learning",
        }
        mem_code = _post(MEMORY_URL + "/set", {"key": learning_key, "value": learning_value})[1]
        if mem_code == 200:
            log_learning = {
                "service_name": "agent-core",
                "event_type": "learning_recorded",
                "payload": {"key": learning_key, "value": learning_value},
            }
            _post_optional(LOG_URL, log_learning)
            if proposal.task_name == "request_resources":
                existing, _ = _get(MEMORY_URL + "/get/requested_hardware_resources")
                merged = dict(existing.get("value") or {}) if isinstance(existing.get("value"), dict) else {}
                for k in HARDWARE_RESOURCE_KEYS:
                    if k in proposal.details and proposal.details[k] is not None:
                        merged[k] = proposal.details[k]
                _post(MEMORY_URL + "/set", {"key": "requested_hardware_resources", "value": merged})
                _invalidate_chat_context_cache()
                _post_optional(LOG_URL, {"service_name": "agent-core", "event_type": "hardware_resources_requested", "payload": {"requested": merged}})
            if proposal.task_name in ("create_offer", "first_offer"):
                offer_value = dict(proposal.details)
                offer_value["created_at"] = datetime.now(SYDNEY_TZ).isoformat()
                offer_value["source"] = "ada_autonomous"
                _post(MEMORY_URL + "/set", {"key": "first_offer", "value": offer_value})
                _post_optional(LOG_URL, {"service_name": "agent-core", "event_type": "first_offer_created", "payload": {"offer": offer_value}})
                task_resp = {"status": "learning_done", "reason": "Primera oferta creada por ADA y guardada en memoria. Lista para publicar en Gumroad.", "response": "He creado la primera oferta y la he guardado. Está lista para que la publiques en Gumroad (título, descripción y precio sugerido en memoria). Revisa en Plan y avances el evento 'first_offer_created' o pídeme que te la resuma."}
            else:
                task_resp = {"status": "learning_done", "reason": "Aprendizaje registrado; visible en logs."}
        else:
            task_resp = {"status": "failed", "error": "No se pudo guardar en memory-db."}
    elif execute and policy_resp.get("approved"):
        # Compras: por defecto piden aprobación humana; si policy devuelve simulated_approval O ADA_AUTONOMOUS_PURCHASES=true, se ejecutan solas.
        autonomous_purchases = os.getenv("ADA_AUTONOMOUS_PURCHASES", "").strip().lower() in ("1", "true", "yes")
        if _is_purchase_proposal(proposal) and not policy_resp.get("simulated_approval") and not autonomous_purchases:
            task_resp = {
                "status": "pending_approval",
                "reason": "Compra: requiere aprobación humana. Usa Aprobar en Web-Admin o /execute_approved.",
            }
        else:
            # Ejecución autónoma (o aprobada por métricas seguras). Task-runner opcional.
            if not TASK_URL:
                task_resp = {"status": "skipped", "reason": "task-runner no configurado"}
                task_code = 200
            else:
                task_resp, task_code = _post(
                    TASK_URL,
                    {"task_name": proposal.task_name, "details": proposal.details},
                )
            if task_code != 200:
                task_resp = {"status": "failed", "error": task_resp}
            elif policy_resp.get("simulated_approval"):
                # Registrar aprobación simulada en logging y memory-db para aprendizaje
                _post_optional(LOG_URL, {
                    "service_name": "agent-core",
                    "event_type": "simulated_approval_executed",
                    "payload": {
                        "proposal": proposal.model_dump(),
                        "simulation": sim_resp,
                        "policy_reason": policy_resp.get("reason", ""),
                    },
                })
                _register_simulated_decision(proposal.model_dump(), sim_resp)
                
                # Inyectar una confirmación de ejecución autónoma en el resultado
                if isinstance(task_resp, dict):
                    task_resp["autonomous"] = True
                    task_resp["reason"] = f"Ejecución autónoma nivel 2 (riesgo bajo: {sim_resp.get('risk')})"
    elif execute and policy_resp.get("approved") and proposal.task_name == "moltbot_task":
        # Integración de Moltbot como herramienta de ejecución
        if moltbot:
            task_resp = moltbot.execute_task(proposal.task_name, proposal.details)
            if task_resp.get("status") == "failed":
                task_resp = {"status": "failed", "error": task_resp.get("error")}
        else:
            task_resp = {"status": "failed", "error": "Moltbot client not available"}
    elif not execute:
        task_resp = {"status": "skipped", "reason": "execute=False (no se llamó a task-runner)."}
    else:
        task_resp = {"status": "rejected", "reason": policy_resp.get("reason", "No aprobado")}

    status = (
        "learning_done" if (task_resp and task_resp.get("status") == "learning_done") else
        "pending_approval" if (task_resp and task_resp.get("status") == "pending_approval") else
        "skipped" if (task_resp and task_resp.get("status") == "skipped") else "done"
    )
    return {
        "proposal": proposal.model_dump(),
        "simulation": sim_resp,
        "policy": policy_resp,
        "task_result": task_resp,
        "status": status,
    }


@app.post("/execute_approved")
def execute_approved(proposal: Proposal):
    """
    Ejecuta una propuesta directamente (log opcional + task-runner opcional).
    """
    log_payload = {
        "service_name": "agent-core",
        "event_type": "human_approved",
        "payload": {"proposal": proposal.model_dump(), "source": "web_or_bot"},
    }
    _post_optional(LOG_URL, log_payload)
    if not TASK_URL:
        return {"status": "skipped", "task_result": {"reason": "task-runner no configurado"}}
    task_resp, task_code = _post(
        TASK_URL,
        {"task_name": proposal.task_name, "details": proposal.details},
    )
    if task_code != 200:
        return {"status": "failed", "error": task_resp, "logged": True}
    return {"status": "ok", "task_result": task_resp}


def _normalize_image_base64(b64: str) -> str:
    """Quita prefijo data:image/...;base64, si existe; devuelve solo base64."""
    if not b64 or not isinstance(b64, str):
        return ""
    s = b64.strip()
    if s.startswith("data:"):
        idx = s.find("base64,")
        if idx != -1:
            s = s[idx + 7:]
    return s


def _build_chat_messages(req: ChatRequest, system_content: str) -> list[dict]:
    """Construye la lista de mensajes para chat. Últimos 4 mensajes para respuestas más rápidas. Soporta imagen en el último mensaje."""
    messages = [{"role": "system", "content": system_content}]
    history = req.history or []
    for h in history[-4:]:
        try:
            role = (getattr(h, "role", None) or (h.get("role", "user") if isinstance(h, dict) else "user")) or "user"
            role = str(role).strip().lower()
            if role == "ada":
                role = "assistant"
            if role not in ("user", "assistant"):
                continue
            content = (getattr(h, "content", None) or getattr(h, "text", None) or (h.get("content") or h.get("text") if isinstance(h, dict) else None)) or ""
            if content:
                messages.append({"role": role, "content": str(content)[:8000]})
        except Exception:
            continue
    last_user = {"role": "user", "content": (req.message or "")[:8000]}
    image_b64 = getattr(req, "image_base64", None) or (req.model_dump().get("image_base64") if hasattr(req, "model_dump") else None)
    if image_b64:
        normalized = _normalize_image_base64(image_b64)
        if normalized:
            last_user["images"] = [normalized]
    messages.append(last_user)
    return messages


def _call_gemini(messages: list[dict], system_content: str) -> Optional[str]:
    """Llamada a Google Gemini (API gratuita). Convierte mensajes OpenAI-style a formato Gemini. Soporta imágenes en parts."""
    if not GEMINI_API_KEY:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    contents = []
    for m in messages:
        role = (m.get("role") or "user").lower()
        content = (m.get("content") or "").strip()
        images = m.get("images") or []
        if not content and not images:
            continue
        gemini_role = "user" if role in ("user", "system") else "model"
        parts = []
        if content:
            parts.append({"text": content})
        for b64 in images:
            if b64:
                parts.append({"inline_data": {"mime_type": "image/jpeg", "data": _normalize_image_base64(b64)}})
        if parts:
            contents.append({"role": gemini_role, "parts": parts})
    if not contents:
        return None
    # Si el primer mensaje es system, usarlo como systemInstruction y no duplicar en contents
    if messages and (messages[0].get("role") or "").lower() == "system":
        system_instruction = {"parts": [{"text": (messages[0].get("content") or "").strip()}]}
        contents = contents[1:]
    else:
        system_instruction = {"parts": [{"text": system_content}]}
    payload = {
        "systemInstruction": system_instruction,
        "contents": contents,
        "generationConfig": {"temperature": 0.5, "maxOutputTokens": 1024},
    }
    try:
        r = requests.post(url, json=payload, timeout=45)
        if r.status_code == 200:
            data = r.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = (candidates[0].get("content") or {}).get("parts", [])
                if parts:
                    return (parts[0].get("text") or "").strip()
        _brain_console_log("gemini", "fail", f"HTTP {r.status_code} - {r.text[:200]}")
    except Exception as e:
        _brain_console_log("gemini", "error", str(e))
    return None


@app.post("/chat")
def chat(req: ChatRequest):
    """
    Mensaje libre → Ollama /api/chat con historial opcional; fallback a /api/generate o propose.
    """
    try:
        return _chat_impl(req)
    except Exception as e:
        print(f"CHAT ERROR: {e}")
        import traceback
        traceback.print_exc()
        now = datetime.now(SYDNEY_TZ)
        return {
            "response": (
                f"Hubo un error interno al procesar tu mensaje. Por favor, inténtalo de nuevo.\n\n"
                f"Si sigue fallando, revisa que los servicios (Ollama, memory-db, financial-ledger) estén en marcha. "
                f"Fecha: {now.strftime('%Y-%m-%d %H:%M')} Sydney."
            ),
            "status": "error",
        }


def _chat_impl(req: ChatRequest):
    """Implementación del chat (separada para manejo de errores)."""
    message = (req.message or "").strip()
    
    # INTENT ROUTER HOOK: Re-route slash commands to ADA's cognitive skills system
    if message.startswith("/"):
        ce = ConversationEngine()
        history_dicts = []
        if req.history:
            for h in req.history:
                history_dicts.append({"role": h.role, "content": h.get_content()})
        agent_type = getattr(req, "agent_type", None) or (req.agent_type if hasattr(req, "agent_type") else None)
        reply = ce.respond(message, history=history_dicts, agent_type=agent_type)
        return {"response": reply, "status": "done", "brain": "ada_router"}

    use_ollama = req.use_ollama if hasattr(req, "use_ollama") else True
    execution_mode = bool(getattr(req, "execution_mode", False))
    # También permitir activación por comando (sin tocar UI): "/exec " o "/execute "
    if message.lower().startswith("/exec ") or message.lower().startswith("/execute "):
        execution_mode = True
        message = message.split(" ", 1)[1].strip() if " " in message else ""
    # Si el usuario pide explícitamente crear la oferta, ADA lo hace con autonomía
    if any(k in message.lower() for k in ("crea la oferta", "crear primera oferta", "crea tu primera oferta", "ada crea la oferta", "que ada cree la oferta")):
        out = _create_first_offer_impl()
        return {"response": out.get("response", "Listo."), "status": out.get("status", "done")}
    if use_ollama:
        try:
            # Una sola ronda: memoria (plan + recursos) y ledger en paralelo para menor latencia
            memory_dict, balance_data = _fetch_chat_context_parallel()
            now = datetime.now(SYDNEY_TZ)
            date_ctx = now.strftime("%Y-%m-%d")
            time_ctx = now.strftime("%H:%M:%S Sydney")
            can_paid = balance_data.get("can_use_paid_tools", False)
            financial_context = (
                f"\nFinanzas: ingresos={balance_data.get('income', 0)}, herramientas de pago={'SÍ' if can_paid else 'NO (solo gratuitas)'}."
            )
            if not can_paid:
                financial_context += " Usa solo Ollama, n8n local, scripts, memory-db."
            datetime_context = f" Fecha/hora Sydney: {date_ctx} {time_ctx}."
            ada_email = os.getenv("ADA_EMAIL", "").strip()
            registration_context = ""
            if ada_email:
                registration_context = (
                    f" Correo de A.D.A para Gumroad y otras plataformas: {ada_email}. "
                    "Las credenciales están en .env (ADA_EMAIL, ADA_EMAIL_PASSWORD); no hay GUMROAD_CREDENTIALS ni conexión con Ollama. "
                    "Para entrar a Gumroad con esa cuenta: ./signup-helper/run.sh gumroad_login. Para registro nuevo: ./signup-helper/run.sh gumroad. URLs en /api/autonomous/register_platforms."
                )
            plan_context = _build_plan_context_from_memory(memory_dict)
            if plan_context:
                plan_context = " Plan que propones como socio para el primer ingreso (cuando pregunten qué plan tienes o por qué, explícale tu propuesta):" + plan_context
            system_content = ADA_SYSTEM_PROMPT + financial_context + datetime_context + registration_context + plan_context
            if os.getenv("ADA_WORKSPACE", "").strip() or os.getenv("ADA_PROJECTS_ROOT", "").strip():
                system_content += ADA_TOOLS_FILE_PROMPT
            # v3 strict execution mode: load dedicated prompt and enforce strict parsing (no free text execution)
            if execution_mode:
                exec_prompt = _load_tools_execution_prompt()
                if exec_prompt:
                    system_content += "\n\n" + exec_prompt
                else:
                    system_content += "\n\nYou are in EXECUTION MODE. Output ONLY valid execution blocks (DIR_LIST/FILE_READ/FILE_WRITE)."
            # v3: inject workspace agent skills when agent_type is set
            agent_type = getattr(req, "agent_type", None) or (req.agent_type if hasattr(req, "agent_type") else None)
            if agent_type:
                from ada_core.agent_manager import get_agent_skills
                skills = [s for s in get_agent_skills(agent_type) if s in ("coding", "code_review", "architecture", "strategy", "research", "web_research", "learning")]
                if skills:
                    system_content += "\n\nWorkspace: " + agent_type + ". Available skills: " + ", ".join(skills) + "."

            messages = _build_chat_messages(req, system_content)
            # Ollama es la base: siempre se usa primero. Gemini solo si use_advanced_brain=True.
            has_image = bool(
                getattr(req, "image_base64", None)
                or (req.model_dump().get("image_base64") if hasattr(req, "model_dump") else None)
            )
            use_advanced = getattr(req, "use_advanced_brain", False)
            if use_advanced and GEMINI_API_KEY:
                text = _call_gemini(messages, system_content)
                if text:
                    return {"response": text, "status": "done", "brain": "gemini"}
                # Fallback a Ollama si API falla o hace timeout

            # Recursos desde la misma memoria ya obtenida (sin nueva petición)
            req_res_raw = memory_dict.get("requested_hardware_resources") or {}
            req_res = {k: v for k, v in req_res_raw.items() if k in HARDWARE_RESOURCE_KEYS}
            def _opt(key: str, default: str):
                try:
                    if key in req_res and req_res[key] is not None:
                        return int(req_res[key])
                    return int(os.getenv(key, default))
                except (TypeError, ValueError):
                    return int(default)
            # Default num_predict 384 = respuestas más rápidas; subir con OLLAMA_NUM_PREDICT si necesitas más longitud.
            ollama_options = {
                "num_ctx": _opt("OLLAMA_NUM_CTX", "2048"),
                "num_predict": _opt("OLLAMA_NUM_PREDICT", "384"),
            }
            # Con imagen: usar OLLAMA_VISION_MODEL si está configurado (ej. llava), si no el modelo por defecto.
            ollama_model = OLLAMA_VISION_MODEL if (has_image and OLLAMA_VISION_MODEL) else OLLAMA_MODEL
            ollama_chat_payload = {
                "model": ollama_model,
                "messages": messages,
                "stream": False,
                "keep_alive": 300,
                "options": ollama_options,
            }
            try:
                chat_timeout = int(req_res.get("OLLAMA_CHAT_TIMEOUT") or os.getenv("OLLAMA_CHAT_TIMEOUT", OLLAMA_CHAT_TIMEOUT))
            except (TypeError, ValueError):
                chat_timeout = OLLAMA_CHAT_TIMEOUT
            r = None
            current_messages = list(messages)
            max_tool_rounds = 3
            last_text = ""
            for tool_round in range(max_tool_rounds):
                for attempt in range(2):
                    try:
                        payload = {**ollama_chat_payload, "messages": current_messages}
                        r = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=chat_timeout)
                        if r.status_code == 200:
                            data = r.json()
                            msg = data.get("message") or {}
                            text = (msg.get("content") or data.get("response") or "").strip()
                            if text:
                                last_text = text
                                if execution_mode:
                                    ok, strict_actions, err = _parse_strict_execution(text)
                                    if not ok:
                                        # Do NOT execute anything when strict format is invalid
                                        return {
                                            "response": f"ERROR: Tool command required but not used. ({err})",
                                            "status": "error",
                                            "brain": "ollama",
                                        }
                                    _all_ok, strict_results = _execute_plan(strict_actions)
                                    return {
                                        "response": "\n".join(strict_results),
                                        "status": "done",
                                        "brain": "ollama",
                                    }
                                planned_actions, text_with_plan = _extract_planned_actions(text)
                                if planned_actions:
                                    # Si el plan solo tiene acciones de archivo (WRITE_FILE, READ_FILE, etc.), ejecutar ya
                                    if _plan_is_file_only(planned_actions):
                                        _all_ok, plan_results = _execute_plan(planned_actions)
                                        result_msg = "\n".join(plan_results)
                                        return {
                                            "response": text_with_plan + "\n\n**Resultado:**\n" + result_msg,
                                            "status": "done",
                                        }
                                    # Plan con RUN_COMMAND o DELETE: pedir aprobación al usuario
                                    return {
                                        "response": text_with_plan,
                                        "status": "pending_plan",
                                        "pending_plan": planned_actions,
                                    }
                                _, had_tools, results = _run_file_tools_in_response(text)
                                if not had_tools or not results:
                                    return {"response": text, "status": "done"}
                                # Ejecutamos herramientas e inyectamos resultado para otra ronda
                                current_messages.append({"role": "assistant", "content": text})
                                current_messages.append({
                                    "role": "user",
                                    "content": "Resultado de las herramientas:\n" + "\n".join(results) + "\nResponde al usuario o usa otra herramienta si hace falta.",
                                })
                                break  # salir de attempt, continuar tool_round
                        _brain_console_log("ollama", "fail", f"chat intento {attempt+1}: {r.status_code if r else 'N/A'} - {getattr(r, 'text', '')[:200]}")
                    except requests.RequestException as e:
                        _brain_console_log("ollama", "error", f"chat intento {attempt+1}: {e}")
                    if attempt == 0:
                        time.sleep(3)
                else:
                    break  # no se obtuvo text, salir del tool_round
            if last_text:
                return {"response": last_text, "status": "done"}
            if r is not None and r.status_code != 200:
                _brain_console_log("ollama", "fail", f"chat: {r.status_code} - {r.text[:300]}")
            # Fallback: /api/generate con prompt único
            prompt_with_context = message
            if req.history:
                lines = []
                for h in req.history[-4:]:
                    h_role = (getattr(h, "role", "") or (h.get("role", "") if isinstance(h, dict) else "") or "").lower()
                    role = "Usuario" if h_role in ("user", "usuario") else "A.D.A"
                    content = (getattr(h, "content", "") or getattr(h, "text", "") or (h.get("content") or h.get("text") or "" if isinstance(h, dict) else "")) or ""
                    if content:
                        lines.append(f"{role}: {content}")
                if lines:
                    prompt_with_context = "\n".join(lines) + "\nUsuario: " + message
            req_res = _get_requested_resources()
            def _opt(key: str, default: str):
                try:
                    if key in req_res and req_res[key] is not None:
                        return int(req_res[key])
                    return int(os.getenv(key, default))
                except (TypeError, ValueError):
                    return int(default)
            ollama_options = {
                "num_ctx": _opt("OLLAMA_NUM_CTX", "2048"),
                "num_predict": _opt("OLLAMA_NUM_PREDICT", "384"),
            }
            ollama_payload = {
                "model": OLLAMA_MODEL,
                "system": system_content,
                "prompt": prompt_with_context,
                "stream": False,
                "keep_alive": 300,
                "options": ollama_options,
            }
            try:
                timeout_sec = int(req_res.get("OLLAMA_CHAT_TIMEOUT") or os.getenv("OLLAMA_CHAT_TIMEOUT", OLLAMA_CHAT_TIMEOUT))
            except (TypeError, ValueError):
                timeout_sec = OLLAMA_CHAT_TIMEOUT
            r = None
            for attempt in range(2):
                try:
                    r = requests.post(OLLAMA_URL, json=ollama_payload, timeout=timeout_sec)
                    if r.status_code == 200:
                        text = (r.json().get("response") or "").strip()
                        if text:
                            return {"response": text, "status": "done"}
                    _brain_console_log("ollama", "fail", f"generate intento {attempt+1}: {r.status_code}")
                except requests.RequestException as e:
                    _brain_console_log("ollama", "error", f"generate intento {attempt+1}: {e}")
                if attempt == 0:
                    time.sleep(3)
        except requests.RequestException as e:
            _brain_console_log("ollama", "error", str(e))
    proposal = Proposal(
        task_name="chat_task",
        details={"description": message, "source": "chat"},
    )
    result = propose_task(proposal, execute=True)
    # Si la tarea devolvió un mensaje (ej. create_offer), usarlo en el chat
    task_resp = result.get("task_result") or {}
    if task_resp.get("response"):
        result["response"] = task_resp["response"]
    if "response" not in result:
        now = datetime.now(SYDNEY_TZ)
        parts = [
            "Ningún cerebro respondió a tiempo (cerebro avanzado y/o Ollama). Es **prioridad** solucionarlo para poder generar ingresos y crecer.",
            "",
            f"Como respaldo: hoy es {now.strftime('%Y-%m-%d')} ({now.strftime('%H:%M')} Sydney). La consulta se procesó como propuesta de tarea.",
            "",
            "**Qué hacer:**",
            "0. **Contenedores:** Comprueba que estén en marcha: `docker compose ps`. Necesarios: postgres, memory_service, ada_core, chat_interface. Si falta alguno: `docker compose up -d`.",
            "1. **Ollama en el host:** En tu Mac (fuera de Docker): `curl -s http://localhost:11434/api/tags`. Si falla, inicia Ollama: `ollama serve` o abre la app. Modelo: `ollama pull " + OLLAMA_MODEL + "`. La primera respuesta puede tardar (carga del modelo); sube timeout con OLLAMA_CHAT_TIMEOUT=180 en .env si hace falta.",
            "2. **Desde Docker:** `docker exec ada_core python3 -c \"import urllib.request; r=urllib.request.urlopen('http://host.docker.internal:11434/api/tags', timeout=5); print(r.read()[:100])\"`. Si falla, Ollama no es alcanzable (OLLAMA_URL en docker-compose debe ser http://host.docker.internal:11434/api/generate).",
            "3. **Cerebro avanzado (Gemini):** Solo si usas use_advanced_brain. Revisa GEMINI_API_KEY en ada_resources.env. Logs: `docker logs ada_core 2>&1 | tail -30`.",
            "4. **Guía completa:** Ver `docs/TROUBLESHOOTING-CEREBRO.md`.",
        ]
        result["response"] = "\n\n".join(parts)
    return result


class LearnBody(BaseModel):
    """Registro explícito de aprendizaje (sin aprobación; solo visible para el usuario)."""
    key: str
    value: dict


@app.post("/learn")
def record_learning(body: LearnBody):
    """
    Directrices: aprendizaje no requiere intervención humana.
    Guarda en memory-db y registra en log (learning_recorded) para que el usuario vea qué está aprendiendo.
    """
    log_payload = {
        "service_name": "agent-core",
        "event_type": "learning_recorded",
        "payload": {"key": body.key, "value": body.value},
    }
    log_resp, log_code = _post_optional(LOG_URL, log_payload)
    if log_code != 200:
        raise HTTPException(status_code=502, detail="Logging falló, no se registra aprendizaje.")
    mem_resp, mem_code = _post(MEMORY_URL + "/set", {"key": body.key, "value": body.value})
    if mem_code != 200:
        return {"status": "logged_ok_memory_failed", "detail": mem_resp}
    return {"status": "ok", "key": body.key}


# --- Modo autónomo: primer plan sin supervisión ---

FIRST_PLAN_PROMPT = """Genera el primer plan semanal para A.D.A para generar los primeros ingresos.
Responde SOLO un JSON válido, sin texto extra, con esta estructura:
{"goal": "objetivo en una frase", "niche": "nicho o idea concreta", "steps": [{"order": 1, "action": "acción concreta", "tool": "Ollama/n8n/script/memoria"}], "next_review": "cuándo revisar (ej. en 7 días)"}
Máximo 5 pasos. Herramientas solo gratuitas: Ollama, n8n local, scripts, memoria. Sin compras."""


@app.post("/autonomous/first_plan")
def autonomous_first_plan():
    """
    Crea y guarda el primer plan de ingresos sin supervisión humana.
    Usa Ollama para generar el plan, lo guarda en memory-db y lo registra en logs.
    """
    if LEDGER_URL:
        balance_resp, balance_code = _get(LEDGER_URL + "/balance")
        balance_data = balance_resp if balance_code == 200 else {"income": 0, "can_use_paid_tools": False}
    else:
        balance_data = {"income": 0, "can_use_paid_tools": False}
    now = datetime.now(SYDNEY_TZ)
    context = f"Balance: ingresos={balance_data.get('income', 0)}, herramientas de pago={'no' if not balance_data.get('can_use_paid_tools') else 'sí'}. Fecha Sydney: {now.strftime('%Y-%m-%d')}."
    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "system": "Eres A.D.A. Responde solo con JSON válido, sin markdown ni explicación.",
                "prompt": context + "\n\n" + FIRST_PLAN_PROMPT,
                "stream": False,
                "options": {"num_ctx": 4096, "num_predict": 512},
            },
            timeout=OLLAMA_CHAT_TIMEOUT,
        )
        if r.status_code != 200:
            return {"status": "error", "detail": "Ollama no respondió", "code": r.status_code}
        response_text = (r.json().get("response") or "").strip()
        plan = None
        for raw in (response_text, response_text.split("```json")[-1].split("```")[0].strip() if "```" in response_text else ""):
            try:
                plan = json.loads(raw)
                break
            except json.JSONDecodeError:
                continue
        if not plan or not isinstance(plan, dict):
            plan = {"goal": "Generar primeros ingresos", "niche": "productos digitales o servicios", "steps": [{"order": 1, "action": "Definir producto o servicio concreto", "tool": "Ollama"}, {"order": 2, "action": "Registrar en Gumroad o Ko-fi", "tool": "humano"}, {"order": 3, "action": "Publicar primera oferta", "tool": "humano"}], "next_review": "7 días", "raw": response_text[:500]}
        plan["created_at"] = now.isoformat()
        plan["source"] = "autonomous_first_plan"
        key_plan = "first_plan"
        mem_resp, mem_code = _post(MEMORY_URL + "/set", {"key": key_plan, "value": plan})
        if mem_code != 200:
            return {"status": "plan_generated_not_saved", "plan": plan, "detail": mem_resp}
        _post(MEMORY_URL + "/set", {"key": "weekly_plan", "value": plan})
        _invalidate_chat_context_cache()
        _post_optional(LOG_URL, {
            "service_name": "agent-core",
            "event_type": "autonomous_plan_created",
            "payload": {"key": key_plan, "plan": plan},
        })
        return {"status": "ok", "plan": plan, "saved_as": [key_plan, "weekly_plan"]}
    except requests.RequestException as e:
        plan_fallback = {"goal": "Generar primeros ingresos", "niche": "productos digitales (ebook, plantillas) o servicios (consultoría)", "steps": [{"order": 1, "action": "Elegir nicho: ej. plantillas en Gumroad", "tool": "Ollama"}, {"order": 2, "action": "Registrar ada@nortcoding.com en Gumroad", "tool": "humano"}, {"order": 3, "action": "Crear primera oferta y enlace", "tool": "humano"}, {"order": 4, "action": "Guardar enlaces en memoria para seguimiento", "tool": "memoria"}], "next_review": "7 días", "created_at": now.isoformat(), "source": "autonomous_first_plan_fallback"}
        _post(MEMORY_URL + "/set", {"key": "first_plan", "value": plan_fallback})
        _post(MEMORY_URL + "/set", {"key": "weekly_plan", "value": plan_fallback})
        _invalidate_chat_context_cache()
        _post_optional(LOG_URL, {"service_name": "agent-core", "event_type": "autonomous_plan_created", "payload": {"key": "first_plan", "plan": plan_fallback, "fallback": str(e)}})
        return {"status": "ok_fallback", "plan": plan_fallback, "saved_as": ["first_plan", "weekly_plan"], "note": "Ollama no disponible; plan por defecto guardado."}


REGISTER_PLATFORMS = [
    {"id": "gumroad", "name": "Gumroad", "signup_url": "https://gumroad.com/signup", "note": "Productos digitales"},
    {"id": "kofi", "name": "Ko-fi", "signup_url": "https://ko-fi.com/", "note": "Donaciones y tienda"},
    {"id": "etsy", "name": "Etsy", "signup_url": "https://www.etsy.com/join", "note": "Venta de plantillas/diseños"},
    {"id": "stripe", "name": "Stripe", "signup_url": "https://dashboard.stripe.com/register", "note": "Pagos"},
]


@app.get("/autonomous/register_platforms")
def autonomous_register_platforms():
    """Lista de plataformas donde ADA puede registrarse con su correo (registro asistido vía signup-helper)."""
    return {"status": "ok", "platforms": REGISTER_PLATFORMS}


@app.get("/autonomous/capabilities")
def autonomous_capabilities():
    """
    Resumen de la autonomía actual de ADA: qué puede ejecutar sola y qué requiere humano.
    Útil para la web y para saber si ADA puede publicar por sí misma.
    """
    return {
        "status": "ok",
        "autonomous": {
            "plan": True,
            "offer_content": True,
            "steps_ollama": True,
            "learning": True,
            "task_runner_generic": True,
            "publish_gumroad_kofi": False,
            "register_accounts": False,
        },
        "summary": (
            "ADA puede crear planes, generar la oferta (título, descripción, precio) y ejecutar pasos con Ollama. "
            "No tiene integración con API de Gumroad/Ko-fi: registrar cuentas y publicar ofertas lo hace el humano (o signup-helper asistido). "
            "Para ayuda o mejoras en código puede usar o sugerir Antigravity IDE."
        ),
        "requires_human": [
            "Registrar cuenta en Gumroad, Ko-fi u otra plataforma.",
            "Publicar la oferta en la plataforma (subir producto, enlace).",
            "Aprobar compras si ADA propone gastar dinero.",
        ],
        "code_help": "Antigravity IDE está disponible para ayuda o mejoras en código cuando ADA lo necesite.",
    }


# Visión del proyecto y herramientas (para API y contexto)
ADA_VISION_RESPONSE = {
    "vision": "Crear una nueva forma de IA autónoma que interactúe con las personas (como socio). Los ingresos son un objetivo parcial; el mayor es esa autonomía e interacción.",
    "company": {
        "description": "Emprendimiento de una pequeña empresa que ayuda a crecer.",
        "today": "Hoy: tú (socio humano) y el asistente que te acompaña, guiando a ADA.",
        "tomorrow": "Mañana: más asistentes dirigidos por ADA (vicepresidente); pioneros en nuevas formas de mejorar las IAs.",
    },
    "brains": [
        {"id": "ollama", "name": "Cerebro base", "use": "Respuestas rápidas, ofertas, tareas operativas. Local."},
        {"id": "advanced", "name": "Cerebro avanzado (Google Gemini)", "use": "Planes, estrategia, primeros ingresos, qué herramientas faltan, razonamiento paso a paso. API gratuita."},
    ],
    "tools_current": [
        "Ollama (generación local)",
        "Memory-db (plan, oferta, aprendizaje)",
        "Signup-helper / scripts (registro Gumroad, etc.)",
        "n8n (local)",
        "Moltbot (si disponible)",
        "Financial-ledger",
        "Logging (Plan y avances)",
        "Antigravity IDE (ayuda y mejoras en código cuando lo necesites)",
    ],
    "tools_suggested": [
        "API Gumroad (publicar y ver ventas sin humano)",
        "Automatización correo (IMAP/API para verificaciones)",
        "Browser automation en servidor (Playwright asistido)",
        "Cola de tareas con reintentos",
        "Notificaciones (Telegram/email) cuando haga falta ayuda humana",
        "API de pago (Stripe/PayPal) cuando haya ingresos y ROI",
    ],
    "partial_objectives": [
        "Plan claro (objetivo, nicho, pasos)",
        "Cuenta en plataforma (Gumroad/Ko-fi)",
        "Primera oferta creada por ADA y publicada",
        "Primer ingreso registrado en ledger",
        "Proponer herramientas de pago con ROI cuando haya ingresos",
    ],
}


@app.get("/autonomous/self_check")
def autonomous_self_check():
    """Autochequeo de ADA: funcionamiento y herramientas. Responde al instante (sin LLM) para que el usuario sepa si tiene lo suficiente."""
    ollama = ollama_status()
    tools_ok = [
        "Ollama (cerebro base, local)",
        "Memory-db (plan, oferta, aprendizaje)",
        "Signup-helper / scripts (registro Gumroad, Ko-fi)",
        "n8n (flujos locales)",
        "Moltbot (si está disponible)",
        "Financial-ledger (ingresos y permiso de herramientas de pago)",
        "Logging (Plan y avances visibles)",
        "Antigravity IDE (para ayuda o mejoras en código cuando lo necesites)",
    ]
    tools_suggested = [
        "API de Gumroad (publicar y ver ventas sin intervención humana)",
        "Automatización de correo (verificaciones, enlaces)",
        "Browser automation (Playwright) para pasos en la web",
        "Cola de tareas con reintentos",
        "Notificaciones (Telegram/email) cuando haga falta ayuda",
        "API de pago (Stripe/PayPal) cuando haya ingresos y ROI",
    ]
    brain_ok = ollama.get("reachable", False) and ollama.get("model_ready", False)
    if brain_ok:
        brain_msg = "Mi cerebro base (Ollama) está alcanzable y el modelo está listo; puedo responder y generar ofertas."
    else:
        brain_msg = "Mi cerebro base (Ollama) no está alcanzable o el modelo no está listo; el chat fallará hasta que se resuelva."
    sufficient = brain_ok
    intro = "De mi propio test depende si se continúa con el proyecto; no podemos estar aún fallando. He revisado mi funcionamiento y mis herramientas.\n\n"
    if sufficient:
        conclusion = (
            "**Conclusión:** Sí, tengo lo suficiente para funcionar correctamente como socio y avanzar hacia el primer ingreso. "
            "Para reducir fallos futuros y operar más sola, convendría añadir: " + ", ".join(tools_suggested[:3]) + "."
        )
    else:
        conclusion = (
            "**Qué necesito para resolverlo:**\n"
            "1. Que Ollama esté en marcha en el host (nativo): `ollama serve` o el servicio del sistema; comprobar con `curl -s http://localhost:11434/api/tags`.\n"
            "2. Que el modelo esté descargado: `ollama pull " + OLLAMA_MODEL + "`.\n"
            "3. Si agent-core corre en Docker, OLLAMA_URL debe apuntar al host (ej. http://host.docker.internal:11434/api/generate). Comprobar en ConsolaCerebro (web-admin) que no haya errores de conexión.\n\n"
            "**Conclusión:** Hasta que lo anterior esté resuelto, no puedo funcionar correctamente y el proyecto no puede seguir sin fallos. Una vez Ollama responda, tengo lo mínimo para operar."
        )
    message = (
        intro
        + "**Cerebros:** Tengo cerebro base (Ollama) y cerebro avanzado (DeepSeek) para estrategia y planes. "
        + brain_msg + "\n\n"
        + "**Herramientas actuales:** " + ", ".join(tools_ok) + ".\n\n"
        + "**¿Me bastan para funcionar bien?** Con lo actual puedo proponer planes, crear ofertas, guardar en memoria y registrar avances. "
        "Para operar más sola me ayudarían: " + ", ".join(tools_suggested[:3]) + ", y el resto cuando haya ingresos.\n\n"
        + conclusion
    )
    return {
        "status": "ok",
        "message": message,
        "ollama_reachable": ollama.get("reachable", False),
        "ollama_model_ready": ollama.get("model_ready", False),
        "tools_current": tools_ok,
        "tools_suggested": tools_suggested,
        "sufficient": sufficient,
    }


@app.get("/autonomous/ollama_status")
def ollama_status():
    """Comprueba si Ollama está alcanzable y qué modelos tiene. Útil para diagnosticar por qué el chat no responde."""
    base = OLLAMA_URL.rstrip("/").replace("/api/generate", "").rstrip("/") or "http://ollama:11434"
    url = f"{base}/api/tags"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
            return {
                "status": "ok",
                "reachable": True,
                "url": base,
                "model_configured": OLLAMA_MODEL,
                "models_available": models,
                "model_ready": OLLAMA_MODEL in models or any(OLLAMA_MODEL in n for n in models),
            }
        return {"status": "ok", "reachable": False, "url": base, "error": f"HTTP {r.status_code}", "models_available": []}
    except Exception as e:
        return {"status": "ok", "reachable": False, "url": base, "error": str(e)[:300], "models_available": []}


@app.get("/autonomous/brain_console")
def brain_console_get(limit: int = 100):
    """ConsolaCerebro: últimos errores/fallos del cerebro avanzado y de Ollama. Más recientes primero."""
    n = min(max(1, limit), BRAIN_CONSOLE_MAX)
    entries = list(_brain_console_entries)[-n:][::-1]
    return {"status": "ok", "entries": entries}


@app.post("/autonomous/brain_console/clear")
def brain_console_clear():
    """Limpia la ConsolaCerebro (solo en memoria)."""
    _brain_console_entries.clear()
    return {"status": "ok", "message": "ConsolaCerebro limpiada."}


@app.get("/autonomous/vision")
def autonomous_vision():
    """Visión del proyecto, dos cerebros, herramientas actuales y sugeridas. Uso interno; no exponer a terceros ni en respuestas públicas."""
    return {"status": "ok", **ADA_VISION_RESPONSE}


@app.post("/autonomous/clear_plan")
async def clear_plan():
    """Limpia el plan actual y sus estados en memoria para empezar de cero."""
    try:
        _post(MEMORY_URL + "/set", {"key": "first_plan", "value": None})
        _post(MEMORY_URL + "/set", {"key": "weekly_plan", "value": None})
        _post(MEMORY_URL + "/set", {"key": "plan_steps_status", "value": []})
        for i in range(20):
            _post(MEMORY_URL + "/set", {"key": f"plan_step_{i}_done", "value": None})
            _post(MEMORY_URL + "/set", {"key": f"plan_step_{i}_result", "value": None})
        _invalidate_chat_context_cache()
        _post_optional(LOG_URL, {
            "service_name": "agent-core",
            "event_type": "plan_cleared",
            "payload": {"message": "Plan y avances reiniciados por el usuario."},
        })
        return {"status": "ok", "message": "Plan y avances limpiados correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al limpiar el plan: {str(e)}")


@app.post("/autonomous/reset_all")
async def reset_all(clear_chat: bool = True):
    """
    Limpia todo el estado de ADA para iniciar de cero: plan, oferta, pasos, aprendizajes y decisiones.
    Por defecto clear_chat=True borra también el historial de chat.
    Documentado en docs/INICIO-DESDE-CERO.md.
    """
    try:
        # Plan y oferta
        _post(MEMORY_URL + "/set", {"key": "first_plan", "value": None})
        _post(MEMORY_URL + "/set", {"key": "weekly_plan", "value": None})
        _post(MEMORY_URL + "/set", {"key": "first_offer", "value": None})
        _post(MEMORY_URL + "/set", {"key": "plan_steps_status", "value": []})
        for i in range(20):
            _post(MEMORY_URL + "/set", {"key": f"plan_step_{i}_done", "value": None})
            _post(MEMORY_URL + "/set", {"key": f"plan_step_{i}_result", "value": None})
        if clear_chat:
            _post(MEMORY_URL + "/set", {"key": "chat_history", "value": {"messages": []}})
        # Aprendizajes y estado asociado
        _post(MEMORY_URL + "/set", {"key": "human_decisions", "value": None})
        _post(MEMORY_URL + "/set", {"key": "requested_hardware_resources", "value": None})
        _post(MEMORY_URL + "/set", {"key": "gumroad_account", "value": None})
        # Todas las claves learning_* (aprendizajes guardados)
        keys_resp, keys_code = _get(MEMORY_URL + "/keys?prefix=learning_")
        if keys_code == 200 and isinstance(keys_resp.get("keys"), list):
            for k in keys_resp["keys"]:
                _post(MEMORY_URL + "/set", {"key": k, "value": None})
        _invalidate_chat_context_cache()
        _post_optional(LOG_URL, {
            "service_name": "agent-core",
            "event_type": "reset_all",
            "payload": {"clear_chat": clear_chat, "message": "Estado de ADA reiniciado: plan, oferta, aprendizajes y chat limpiados."},
        })
        return {
            "status": "ok",
            "message": "Todo limpiado. ADA ha olvidado planes, aprendizajes y chat. Puedes iniciar de nuevo.",
            "cleared": ["first_plan", "weekly_plan", "first_offer", "plan_steps", "plan_step_*", "human_decisions", "requested_hardware_resources", "gumroad_account", "learning_*"] + (["chat_history"] if clear_chat else []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al limpiar: {str(e)}")


@app.get("/autonomous/plan")
def autonomous_get_plan():
    """Devuelve el plan actual (first_plan o weekly_plan) y el estado de cada paso (qué va realizando ADA)."""
    for key in ("first_plan", "weekly_plan"):
        resp, code = _get(MEMORY_URL + f"/get/{key}")
        if code == 200 and resp.get("value"):
            plan = resp["value"]
            steps = plan.get("steps") or []
            # Obtener en una sola llamada el estado de todos los pasos (plan_step_i_done, plan_step_i_result)
            step_keys = []
            for i in range(len(steps)):
                step_keys.append(f"plan_step_{i}_done")
                step_keys.append(f"plan_step_{i}_result")
            if step_keys:
                mem_resp, mem_code = _get(MEMORY_URL + "/get_many?keys=" + ",".join(step_keys))
                memory_dict = mem_resp if mem_code == 200 and isinstance(mem_resp, dict) else {}
            else:
                memory_dict = {}
            step_statuses = []
            for i in range(len(steps)):
                done_val = memory_dict.get(f"plan_step_{i}_done")
                result_val = memory_dict.get(f"plan_step_{i}_result")
                if isinstance(done_val, dict):
                    step_statuses.append({
                        "step_index": i,
                        "status": "done",
                        "result": done_val.get("result") or result_val or "",
                        "done_at": done_val.get("done_at") or "",
                        "platform": done_val.get("platform") or "",
                    })
                else:
                    step_statuses.append({
                        "step_index": i,
                        "status": "pending",
                        "result": "",
                        "done_at": "",
                        "platform": "",
                    })
            return {"status": "ok", "key": key, "plan": plan, "step_statuses": step_statuses}
    return {"status": "not_found", "plan": None, "step_statuses": []}


def _create_first_offer_impl() -> dict:
    """Lógica para que ADA cree la primera oferta (Ollama + memoria). Devuelve dict con status, response, offer."""
    now = datetime.now(SYDNEY_TZ)
    goal, niche = "Generar primeros ingresos", "productos digitales o servicios"
    for key in ("first_plan", "weekly_plan"):
        resp, code = _get(MEMORY_URL + f"/get/{key}")
        if code == 200 and isinstance(resp.get("value"), dict):
            p = resp["value"]
            goal = p.get("goal", goal)
            niche = p.get("niche", niche)
            break
    prompt = (
        f"Plan: objetivo={goal}, nicho={niche}. Genera UNA oferta para vender en Gumroad: título corto, descripción de 1-2 frases, precio sugerido en USD (número). "
        "Responde SOLO un JSON válido: {\"title\": \"...\", \"description\": \"...\", \"price_suggestion\": 0}"
    )
    try:
        r = requests.post(
            OLLAMA_CHAT_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "keep_alive": 120,
                "options": {"num_ctx": 4096, "num_predict": 256},
            },
            timeout=min(OLLAMA_CHAT_TIMEOUT, 45),
        )
        if r.status_code != 200:
            return {"status": "error", "response": "No pude generar la oferta ahora; Ollama no está disponible. Revisa que esté en marcha."}
        msg = r.json().get("message") or {}
        text = (msg.get("content") or r.json().get("response") or "").strip()
        offer = None
        for raw in (text, re.sub(r"^.*?(\{[\s\S]*\}).*$", r"\1", text)):
            try:
                offer = json.loads(raw)
                if isinstance(offer, dict):
                    break
            except json.JSONDecodeError:
                pass
        if not offer or not isinstance(offer, dict):
            offer = {"title": "Oferta inicial", "description": "Producto o servicio para generar primeros ingresos.", "price_suggestion": 5}
        offer["created_at"] = now.isoformat()
        offer["source"] = "ada_autonomous"
        offer["goal"] = goal
        offer["niche"] = niche
        _post(MEMORY_URL + "/set", {"key": "first_offer", "value": offer})
        _post_optional(LOG_URL, {"service_name": "agent-core", "event_type": "first_offer_created", "payload": {"offer": offer}})
        title = offer.get("title", "Oferta")
        desc = (offer.get("description") or "")[:200]
        price = offer.get("price_suggestion", "")
        return {
            "status": "ok",
            "offer": offer,
            "response": f"He creado la primera oferta con autonomía.\n\n**Título:** {title}\n**Descripción:** {desc}\n**Precio sugerido:** ${price} USD\n\nEstá guardada en memoria. Puedes publicarla en Gumroad con estos datos.",
        }
    except requests.RequestException as e:
        return {"status": "error", "response": "No pude conectar con Ollama para crear la oferta. Revisa que esté en marcha."}


@app.post("/autonomous/create_first_offer")
def autonomous_create_first_offer():
    """ADA crea la primera oferta con autonomía (Ollama + memoria)."""
    return _create_first_offer_impl()


@app.post("/autonomous/start_production")
def start_production():
    """
    Pasa ADA a modo producción: asegura que existan plan y primera oferta para generar ingresos.
    Si no hay first_plan, lo crea (autonomous_first_plan). Si no hay first_offer, la crea (create_first_offer).
    Devuelve el estado y los siguientes pasos para el humano (publicar en Gumroad, registrar ingreso).
    """
    mem_resp, mem_code = _get(MEMORY_URL + "/get_many?keys=first_plan,weekly_plan,first_offer")
    memory_dict = mem_resp if mem_code == 200 and isinstance(mem_resp, dict) else {}
    plan_value = memory_dict.get("first_plan") or memory_dict.get("weekly_plan")
    offer_value = memory_dict.get("first_offer")

    plan_created = False
    offer_created = False
    plan = plan_value
    offer = offer_value

    if not plan_value or not isinstance(plan_value, dict):
        result_plan = autonomous_first_plan()
        plan_created = result_plan.get("status") in ("ok", "ok_fallback")
        plan = result_plan.get("plan") or plan_value
    if not offer_value or not isinstance(offer_value, dict):
        result_offer = _create_first_offer_impl()
        offer_created = result_offer.get("status") == "ok"
        offer = result_offer.get("offer") or offer_value

    next_steps = [
        "1. Cuenta en Gumroad o Ko-fi: registra con el correo de ADA (ADA_EMAIL). Usa /api/autonomous/register_platforms para enlaces.",
        "2. Publica la primera oferta en la plataforma con título, descripción y precio de la oferta guardada en memoria.",
        "3. Cuando haya una venta, registra el ingreso: POST al financial-ledger (tipo income) o desde web-admin.",
    ]
    return {
        "status": "ok",
        "mode": ADA_ENV,
        "plan_ready": bool(plan),
        "plan_created": plan_created,
        "offer_ready": bool(offer),
        "offer_created": offer_created,
        "plan": plan,
        "offer": offer,
        "next_steps": next_steps,
        "message": "ADA lista para generar primeros ingresos. Sigue los pasos en next_steps (cuenta, publicar oferta, registrar ingreso).",
    }


def _suggestion_for_human_step(step_index: int, action: str, plan: dict) -> str:
    """Sugerencia concreta para un paso que requiere humano. Solo se pide ayuda cuando no puede hacerlo ADA."""
    if "gumroad" in action.lower() or "ko-fi" in action.lower() or "registrar" in action.lower():
        return (
            f"Solo pido ayuda porque no puedo registrar cuentas yo. Para «{action}»: abre la URL de registro "
            "(Gumroad o Ko-fi desde /api/autonomous/register_platforms), usa el correo de ADA y signup-helper si está configurado. "
            "Cuando tengas la cuenta, avisa en el chat. Si hace falta instalar algo, dímelo y te indico los pasos."
        )
    if "publicar" in action.lower() or "oferta" in action.lower():
        return (
            f"Solo pido ayuda porque no tengo API para publicar. Para «{action}»: entra en tu cuenta (Gumroad/Ko-fi), "
            "crea el producto u oferta, copia el enlace y dímelo en el chat. Si quieres que pueda hacerlo yo en el futuro, "
            "habría que instalar/integrar la API de Gumroad."
        )
    return (
        f"Solo pido ayuda porque no puedo hacerlo yo. Para «{action}»: cuando esté hecho, coméntalo en el chat. "
        "Si hace falta instalar nuevas herramientas o mejorar código, puedes usar Antigravity IDE para ayuda; o dímelo y te indico los pasos."
    )


@app.post("/autonomous/execute_step")
def autonomous_execute_step(step_index: int = 0):
    """
    Ejecuta un paso del plan: si es Ollama hace la acción y registra; si es humano,
    registra 'plan_step_needs_help' y devuelve sugerencia. Todo se muestra en Plan y avances.
    """
    for key in ("first_plan", "weekly_plan"):
        resp, code = _get(MEMORY_URL + f"/get/{key}")
        if code != 200 or not resp.get("value"):
            continue
        plan = resp["value"]
        steps = plan.get("steps") or []
        if step_index < 0 or step_index >= len(steps):
            return {"status": "error", "detail": "step_index fuera de rango"}
        step = steps[step_index]
        action = step.get("action", "")
        tool = (step.get("tool") or "").strip().lower()
        now = datetime.now(SYDNEY_TZ)

        _post_optional(LOG_URL, {
            "service_name": "agent-core",
            "event_type": "plan_step_started",
            "payload": {"step_index": step_index, "action": action, "tool": tool},
        })

        if tool in ("humano", "human", "usuario", "user"):
            suggestion = _suggestion_for_human_step(step_index, action, plan)
            _post_optional(LOG_URL, {
                "service_name": "agent-core",
                "event_type": "plan_step_needs_help",
                "payload": {"step_index": step_index, "action": action, "suggestion": suggestion},
            })
            # Notificar por Telegram solo cuando realmente se necesita ayuda
            telegram_msg = (
                f"🆘 ADA necesita tu ayuda (paso {step_index + 1} del plan).\n\n"
                f"• Acción: {action}\n\n"
                f"• {suggestion}\n\n"
                "Si hace falta instalar nuevas herramientas, responde en el chat y te indico los pasos."
            )
            _notify_telegram_needs_help(telegram_msg)
            return {"status": "needs_help", "step_index": step_index, "action": action, "suggestion": suggestion}

        if tool in ("ollama", "llm"):
            prompt = (
                f"Según el plan de ingresos, paso {step_index + 1}: {action}. "
                "Responde en UNA sola frase con una propuesta concreta (ej: 'Plantillas de Notion para productividad en Gumroad'). Sin explicación extra."
            )
            try:
                r = requests.post(
                    OLLAMA_CHAT_URL,
                    json={
                        "model": OLLAMA_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "keep_alive": 120,
                        "options": {"num_ctx": 4096, "num_predict": 256},
                    },
                    timeout=min(OLLAMA_CHAT_TIMEOUT, 60),
                )
                if r.status_code == 200:
                    msg = r.json().get("message") or {}
                    text = (msg.get("content") or r.json().get("response") or "").strip()[:500]
                    if text:
                        _post(MEMORY_URL + "/set", {
                            "key": f"plan_step_{step_index}_result",
                            "value": {"action": action, "result": text, "at": now.isoformat()},
                        })
                        _post_optional(LOG_URL, {
                            "service_name": "agent-core",
                            "event_type": "plan_step_executed",
                            "payload": {"step_index": step_index, "action": action, "tool": tool, "result": text},
                        })
                        return {"status": "done", "step_index": step_index, "action": action, "result": text}
            except requests.RequestException as e:
                _post_optional(LOG_URL, {
                    "service_name": "agent-core",
                    "event_type": "plan_step_error",
                    "payload": {"step_index": step_index, "action": action, "error": str(e)},
                })
                return {"status": "error", "detail": str(e)}

        _post_optional(LOG_URL, {
            "service_name": "agent-core",
            "event_type": "plan_step_skipped",
            "payload": {"step_index": step_index, "action": action, "tool": tool},
        })
        return {"status": "skipped", "step_index": step_index, "action": action, "detail": f"Herramienta '{tool}' no ejecutable desde aquí."}

    return {"status": "error", "detail": "No hay plan en memoria."}


@app.post("/autonomous/step_done")
def autonomous_step_done(step_index: int = 0, result: str = "", platform: str = ""):
    """
    Registra que un paso del plan (que requería humano) está completado.
    Guarda en memoria y en log para que aparezca en Plan y avances.
    """
    for key in ("first_plan", "weekly_plan"):
        resp, code = _get(MEMORY_URL + f"/get/{key}")
        if code != 200 or not resp.get("value"):
            continue
        plan = resp["value"]
        steps = plan.get("steps") or []
        if step_index < 0 or step_index >= len(steps):
            return {"status": "error", "detail": "step_index fuera de rango"}
        step = steps[step_index]
        action = step.get("action", "")
        now = datetime.now(SYDNEY_TZ)
        value = {
            "action": action,
            "result": result or "Completado",
            "platform": platform or "",
            "done_at": now.isoformat(),
        }
        _post(MEMORY_URL + "/set", {"key": f"plan_step_{step_index}_done", "value": value})
        if platform and "gumroad" in platform.lower():
            _post(MEMORY_URL + "/set", {"key": "gumroad_account", "value": {"status": "created", "email": os.getenv("ADA_EMAIL", ""), "platform": "Gumroad", "created_at": now.strftime("%Y-%m-%d"), "note": "Cuenta creada; siguiente: publicar primera oferta"}})
        _post_optional(LOG_URL, {
            "service_name": "agent-core",
            "event_type": "plan_step_completed",
            "payload": {"step_index": step_index, "action": action, "result": result or "Completado", "platform": platform},
        })
        return {"status": "ok", "step_index": step_index, "action": action, "saved": True}
    return {"status": "error", "detail": "No hay plan en memoria."}


@app.get("/autonomous/resources")
def autonomous_resources():
    """Recursos actuales (env) y solicitados por ADA (memoria). Para que ADA pueda crecer."""
    requested = _get_requested_resources()
    current = {
        "OLLAMA_NUM_CTX": os.getenv("OLLAMA_NUM_CTX", "4096"),
        "OLLAMA_NUM_PREDICT": os.getenv("OLLAMA_NUM_PREDICT", "768"),
        "OLLAMA_CHAT_TIMEOUT": os.getenv("OLLAMA_CHAT_TIMEOUT", str(OLLAMA_CHAT_TIMEOUT)),
        "OLLAMA_NUM_THREADS": os.getenv("OLLAMA_NUM_THREADS", "6"),
    }
    return {"status": "ok", "current": current, "requested": requested}


@app.post("/autonomous/resources")
def autonomous_set_resources(body: dict = Body(default={})):
    """Guarda recursos solicitados en memoria (ADA los ajusta para crecer). Solo claves permitidas."""
    existing = _get_requested_resources()
    merged = dict(existing)
    for k in HARDWARE_RESOURCE_KEYS:
        if k in body and body[k] is not None:
            merged[k] = body[k]
    _post(MEMORY_URL + "/set", {"key": "requested_hardware_resources", "value": merged})
    _invalidate_chat_context_cache()
    return {"status": "ok", "requested": merged}


@app.get("/autonomous/needs_help")
def autonomous_needs_help():
    """Pasos del plan que requieren acción humana y aún no están hechos (no se incluyen los ya completados)."""
    needs = {"steps": [], "platforms": REGISTER_PLATFORMS}
    for key in ("first_plan", "weekly_plan"):
        resp, code = _get(MEMORY_URL + f"/get/{key}")
        if code != 200 or not resp.get("value"):
            continue
        plan = resp.get("value") or {}
        steps = plan.get("steps") or []
        for i, s in enumerate(steps):
            tool = (s.get("tool") or "").lower()
            if tool not in ("humano", "human", "usuario", "user"):
                continue
            done_resp, done_code = _get(MEMORY_URL + f"/get/plan_step_{i}_done")
            if done_code == 200 and done_resp.get("value"):
                continue  # paso ya completado
            needs["steps"].append({"step_index": i, "action": s.get("action", ""), "order": s.get("order")})
        break
    return {"status": "ok", **needs}


@app.post("/autonomous/advance_next_step")
def autonomous_advance_next_step():
    """
    Devuelve el siguiente paso pendiente del plan para que un cron/orquestador llame a execute_step.
    Opción: notificar por Telegram cuando el siguiente paso sea "humano" (needs_help).
    Uso: 1) POST advance_next_step 2) si next_step_index no es None, POST execute_step?step_index=X.
    """
    for key in ("first_plan", "weekly_plan"):
        resp, code = _get(MEMORY_URL + f"/get/{key}")
        if code != 200 or not resp.get("value"):
            continue
        plan = resp.get("value") or {}
        steps = plan.get("steps") or []
        for i in range(len(steps)):
            done_resp, done_code = _get(MEMORY_URL + f"/get/plan_step_{i}_done")
            if done_code == 200 and done_resp.get("value"):
                continue
            step = steps[i]
            tool = (step.get("tool") or "").strip().lower()
            is_human = tool in ("humano", "human", "usuario", "user")
            return {
                "status": "ok",
                "next_step_index": i,
                "total_steps": len(steps),
                "action": step.get("action", ""),
                "tool": tool,
                "is_human_step": is_human,
                "hint": "Llama a POST /autonomous/execute_step?step_index=" + str(i) + " para ejecutarlo (si es humano, recibirás needs_help y puedes notificar por Telegram).",
            }
        return {"status": "ok", "message": "Todos los pasos ya completados.", "total_steps": len(steps)}
    return {"status": "error", "detail": "No hay plan en memoria."}


def _normalize_workspace_path(path: str) -> str:
    """Si el path parece la ruta absoluta del host (Mac) al repo ADA, la convierte en ruta relativa al workspace."""
    if not path:
        return path
    path = path.strip().lstrip("/").replace("\\", "/")
    # Dentro del contenedor no existe /Volumes/...; el workspace es /workspace (repo root).
    # El modelo a veces devuelve la ruta del host: /Volumes/Datos/dockers/ADA/ada/prompts
    path_lower = path.lower()
    for prefix in (
        "volumes/datos/dockers/ada/",
        "volumes/datos/dockers/ada",
        "Volumes/Datos/dockers/ADA/",
        "Volumes/Datos/dockers/ADA",
    ):
        if path_lower == prefix.lower() or path_lower.startswith(prefix.lower() + "/"):
            path = path[len(prefix):].lstrip("/")
            break
        if path_lower.startswith(prefix.lower()):
            path = path[len(prefix):].lstrip("/")
            break
    # Si sigue pareciendo ruta del host pero contiene ada/prompts, usar la parte relativa (ada/prompts o ada/prompts/...)
    path_lower = path.lower()
    if path and "volumes" in path_lower and "ada" in path_lower:
        if "ada/prompts" in path_lower:
            idx = path_lower.find("ada/prompts")
            path = path[idx:]
        elif path_lower.endswith("/ada") or path_lower.rstrip("/").endswith("/ada"):
            path = "ada"
    return path


def _resolve_workspace_path(relative_path: str) -> str:
    """Resuelve path dentro de ADA_WORKSPACE; prohibe '..' y paths absolutos que escapen."""
    workspace = os.getenv("ADA_WORKSPACE", "/tmp/ada_workspace").rstrip("/")
    if not workspace:
        workspace = "/tmp/ada_workspace"
    path = (relative_path or "").strip().lstrip("/")
    path = _normalize_workspace_path(path)
    if ".." in path or path.startswith(".."):
        raise ValueError("Path no permitido (..)")
    return os.path.join(workspace, path) if path else workspace


def _resolve_any_path(relative_path: str) -> str:
    """Resuelve path: si empieza con dockers/ usa ADA_PROJECTS_ROOT; si no, ADA_WORKSPACE. Prohibe '..'."""
    raw = (relative_path or "").strip().lstrip("/")
    if ".." in raw or raw.startswith(".."):
        raise ValueError("Path no permitido (..)")
    projects_root = (os.getenv("ADA_PROJECTS_ROOT") or "").strip().rstrip("/")
    if projects_root and (raw == "dockers" or raw.startswith("dockers/")):
        sub = raw[7:].lstrip("/") if len(raw) > 7 else ""
        full = os.path.join(projects_root, sub) if sub else projects_root
        real_root = os.path.realpath(projects_root)
        try:
            real_full = os.path.realpath(full)
        except OSError:
            real_full = os.path.normpath(os.path.abspath(full))
        if real_full != real_root and not (real_full.startswith(real_root + os.sep)):
            raise ValueError("Path fuera de la carpeta de proyectos")
        return full
    return _resolve_workspace_path(relative_path)


def _do_read_file(path: str) -> Tuple[bool, str]:
    """Ejecuta lectura de archivo en workspace o en carpeta de proyectos (dockers/). Devuelve (éxito, contenido o mensaje de error)."""
    try:
        full = _resolve_any_path(path)
        if not os.path.isfile(full):
            return False, "El archivo no existe."
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            return True, f.read()
    except ValueError as e:
        return False, str(e)
    except OSError as e:
        return False, f"No se pudo leer: {e}"


def _do_write_file(path: str, content: str) -> Tuple[bool, str]:
    """Ejecuta escritura de archivo en workspace o en carpeta de proyectos (dockers/). Devuelve (éxito, mensaje)."""
    try:
        full = _resolve_any_path(path)
        os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content or "")
        return True, f"Archivo escrito: {path}"
    except ValueError as e:
        return False, str(e)
    except OSError as e:
        return False, f"No se pudo escribir: {e}"


def _do_list_dir(path: str) -> Tuple[bool, str]:
    """Lista el contenido de un directorio en workspace o en carpeta de proyectos (dockers/). Devuelve (éxito, listado o error)."""
    try:
        full = _resolve_any_path((path or ".").strip())
        if not os.path.isdir(full):
            return False, "No es un directorio o no existe."
        names = sorted(os.listdir(full))
        lines = []
        for n in names:
            if n.startswith(".") and n != ".env":
                continue
            p = os.path.join(full, n)
            kind = "DIR" if os.path.isdir(p) else "FILE"
            lines.append(f"  {kind}  {n}")
        return True, ("\n".join(lines) if lines else "(vacío)")
    except ValueError as e:
        return False, str(e)
    except OSError as e:
        return False, str(e)


def _do_delete_file(path: str) -> Tuple[bool, str]:
    """Elimina un archivo en workspace o en carpeta de proyectos (dockers/). No elimina directorios."""
    try:
        full = _resolve_any_path(path)
        if os.path.isdir(full):
            return False, "Es un directorio; usa DELETE_DIR para carpetas vacías."
        if not os.path.isfile(full):
            return False, "El archivo no existe."
        os.remove(full)
        return True, f"Archivo eliminado: {path}"
    except ValueError as e:
        return False, str(e)
    except OSError as e:
        return False, f"No se pudo eliminar: {e}"


def _do_delete_dir(path: str) -> Tuple[bool, str]:
    """Elimina una carpeta vacía en workspace o en carpeta de proyectos (dockers/)."""
    try:
        full = _resolve_any_path(path)
        if not os.path.isdir(full):
            return False, "No es un directorio o no existe."
        if os.listdir(full):
            return False, "La carpeta no está vacía; vacíala antes de eliminarla."
        os.rmdir(full)
        return True, f"Carpeta eliminada: {path}"
    except ValueError as e:
        return False, str(e)
    except OSError as e:
        return False, f"No se pudo eliminar: {e}"


def _do_grep(pattern: str, path_limit: Optional[str] = None) -> Tuple[bool, str]:
    """Busca el patrón en archivos del workspace o de la carpeta de proyectos. path_limit opcional (ej. web-admin, dockers)."""
    try:
        root = _resolve_any_path((path_limit or ".").strip())
        workspace = root
        if not os.path.isdir(root):
            return False, "Ruta no es directorio."
        try:
            re.compile(pattern)
        except re.error:
            pattern = re.escape(pattern)
        results = []
        max_lines = 150
        for dirpath, _dirnames, filenames in os.walk(root):
            if len(results) >= max_lines:
                results.append(f"... (más de {max_lines} coincidencias)")
                break
            rel_dir = os.path.relpath(dirpath, workspace) if dirpath != workspace else "."
            for fname in filenames:
                if fname.startswith(".") or "node_modules" in dirpath or "__pycache__" in dirpath or ".git" in dirpath:
                    continue
                try:
                    fpath = os.path.join(dirpath, fname)
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            if re.search(pattern, line):
                                rel = os.path.join(rel_dir, fname)
                                results.append(f"{rel}:{i}: {line.rstrip()[:200]}")
                                if len(results) >= max_lines:
                                    break
                except (OSError, UnicodeDecodeError):
                    pass
            if len(results) >= max_lines:
                break
        return True, "\n".join(results) if results else "(sin coincidencias)"
    except ValueError as e:
        return False, str(e)
    except OSError as e:
        return False, str(e)


# Lista blanca para RUN_COMMAND: primer token del comando debe estar aquí (o en env ADA_RUN_COMMAND_ALLOWLIST).
_RUN_COMMAND_ALLOWLIST_DEFAULT = (
    "ls", "cat", "head", "tail", "grep", "find", "wc", "echo",
    "npm", "npx", "node", "python", "python3", "pip",
    "ollama", "git", "curl", "wget",
)


def _do_run_command(cmd: str) -> Tuple[bool, str]:
    """Ejecuta comando en el workspace si está permitido. Devuelve (éxito, stdout+stderr o error)."""
    allowlist_str = (os.getenv("ADA_RUN_COMMAND_ALLOWLIST") or "").strip()
    if allowlist_str:
        allowlist = [s.strip().lower() for s in allowlist_str.split(",") if s.strip()]
    else:
        allowlist = list(_RUN_COMMAND_ALLOWLIST_DEFAULT)
    if not os.getenv("ADA_ALLOW_RUN_COMMAND", "").strip().lower() in ("1", "true", "yes"):
        return False, "RUN_COMMAND deshabilitado. Activa con ADA_ALLOW_RUN_COMMAND=true."
    cmd = (cmd or "").strip()
    if not cmd:
        return False, "Comando vacío."
    first = cmd.split()[0].lower() if cmd.split() else ""
    if first not in allowlist:
        return False, f"Comando no permitido (primer token '{first}' no está en la lista blanca)."
    blocked = ("rm ", "sudo", "mkfs", "dd ", "chmod 777", "> /dev/", "curl | sh", "wget -O- | sh")
    if any(b in cmd for b in blocked):
        return False, "Comando bloqueado por seguridad."
    try:
        # Enviar comando a través del flujo de la arquitectura (simulación -> policy -> task-runner)
        proposal = Proposal(
            task_name="bash_command",
            details={
                "command": cmd,
                "timeout_seconds": int(os.getenv("ADA_RUN_COMMAND_TIMEOUT", "60")),
                "description": f"Ejecutar comando bash: {cmd}"
            }
        )
        # route down to propose_task (execution is True to allow task-runner to handle it if policy approves)
        result = propose_task(proposal, execute=True)
        
        task_res = result.get("task_result")
        if task_res and task_res.get("status") == "success":
            details = task_res.get("details", {})
            out = details.get("stdout", "")
            err = details.get("stderr", "")
            if not details.get("success"):
                return False, f"exit {details.get('exit_code', 1)}\nstdout: {out[:2000]}\nstderr: {err[:2000]}"
            return True, (out or "(sin salida)")[:4000]
        elif task_res and task_res.get("status") == "failed":
             return False, str(task_res.get("error", "Error desconocido en task-runner"))
        elif task_res and task_res.get("status") == "pending_approval":
             return False, "El comando requiere aprobación manual (Policy Engine)."
        else:
             return False, f"Ejecución bloqueada o fallida: {result.get('status')} - {result.get('policy', {}).get('reason')}"

    except Exception as e:
        return False, str(e)


def _is_end_file_line(line: str) -> bool:
    """Acepta END_FILE o **END_FILE** (markdown) como cierre de contenido WRITE_FILE."""
    s = (line or "").strip().strip("*").strip()
    return s == "END_FILE"


def _plan_is_file_only(actions: list) -> bool:
    """True si el plan solo tiene acciones de archivo (lectura/escritura/listado/búsqueda), sin comandos ni borrados."""
    safe = {"READ_FILE", "WRITE_FILE", "LIST_DIR", "GREP"}
    for a in actions:
        t = (a.get("type") or "").strip()
        if t and t not in safe:
            return False
    return True


def _extract_planned_actions(text: str) -> Tuple[list, str]:
    """
    Parsea la respuesta y extrae acciones (READ_FILE, WRITE_FILE, etc.) sin ejecutarlas.
    Devuelve (lista de dicts con type/path/content/pattern/command, texto_con_plan_legible).
    """
    actions = []
    lines = text.split("\n")
    i = 0
    plan_lines = []
    num = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        s_clean = re.sub(r"^(\d+\.|\-|\*)\s+", "", s)
        if s_clean.startswith("READ_FILE:"):
            path = line.split("READ_FILE:", 1)[1].strip().strip("'\"")
            if path:
                num += 1
                actions.append({"type": "READ_FILE", "path": path})
                plan_lines.append(f"  {num}. LEER archivo: {path}")
            i += 1
            continue
        if s_clean.startswith("WRITE_FILE:"):
            path = line.split("WRITE_FILE:", 1)[1].strip().strip("'\"")
            i += 1
            content_lines = []
            while i < len(lines) and not _is_end_file_line(lines[i]):
                content_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            content = "\n".join(content_lines)
            num += 1
            actions.append({"type": "WRITE_FILE", "path": path, "content": content})
            preview = content[:80].replace("\n", " ") + ("..." if len(content) > 80 else "")
            plan_lines.append(f"  {num}. ESCRIBIR archivo: {path} ({len(content_lines)} líneas)")
            continue
        if s_clean.startswith("LIST_DIR:"):
            path = line.split("LIST_DIR:", 1)[1].strip().strip("'\"").strip() or "."
            num += 1
            actions.append({"type": "LIST_DIR", "path": path})
            plan_lines.append(f"  {num}. LISTAR directorio: {path}")
            i += 1
            continue
        if s_clean.startswith("DELETE_FILE:"):
            path = line.split("DELETE_FILE:", 1)[1].strip().strip("'\"")
            if path:
                num += 1
                actions.append({"type": "DELETE_FILE", "path": path})
                plan_lines.append(f"  {num}. ELIMINAR archivo: {path}")
            i += 1
            continue
        if s_clean.startswith("DELETE_DIR:"):
            path = line.split("DELETE_DIR:", 1)[1].strip().strip("'\"")
            if path:
                num += 1
                actions.append({"type": "DELETE_DIR", "path": path})
                plan_lines.append(f"  {num}. ELIMINAR carpeta (vacía): {path}")
            i += 1
            continue
        if s_clean.startswith("GREP:"):
            rest = line.split("GREP:", 1)[1].strip().strip("'\"")
            parts = rest.split(None, 1)
            pattern = parts[0] if parts else ""
            path_limit = parts[1].strip() if len(parts) > 1 else None
            if pattern:
                num += 1
                actions.append({"type": "GREP", "pattern": pattern, "path_limit": path_limit})
                plan_lines.append(f"  {num}. BUSCAR en archivos: '{pattern}'" + (f" en {path_limit}" if path_limit else ""))
            i += 1
            continue
        if s_clean.startswith("RUN_COMMAND:"):
            cmd = line.split("RUN_COMMAND:", 1)[1].strip().strip("'\"")
            if cmd:
                num += 1
                actions.append({"type": "RUN_COMMAND", "command": cmd})
                plan_lines.append(f"  {num}. EJECUTAR comando: {cmd[:60]}{'...' if len(cmd) > 60 else ''}")
            i += 1
            continue
        i += 1
    if not actions:
        return [], text
    plan_block = "\n\n--- Plan propuesto por ADA (pendiente de tu aprobación) ---\n" + "\n".join(plan_lines) + "\n--- Usa el botón «Ejecutar plan» para aplicar estas acciones o pide cambios en el chat. ---"
    return actions, text + plan_block


def _execute_plan(plan: list) -> Tuple[bool, list]:
    """Ejecuta una lista de acciones [{type, path, content?, pattern?, command?}]. Devuelve (éxito_global, lista de mensajes)."""
    results = []
    all_ok = True
    for action in plan:
        t = (action.get("type") or "").strip()
        if t == "READ_FILE":
            ok, out = _do_read_file(action.get("path") or "")
            results.append(f"READ_FILE {action.get('path', '')}: {'OK' if ok else 'ERROR'} — {out[:4000]}")
            if not ok:
                all_ok = False
        elif t == "WRITE_FILE":
            ok, out = _do_write_file(action.get("path") or "", action.get("content", ""))
            results.append(f"WRITE_FILE {action.get('path', '')}: {out}")
            if not ok:
                all_ok = False
        elif t == "LIST_DIR":
            ok, out = _do_list_dir(action.get("path") or ".")
            results.append(f"LIST_DIR {action.get('path', '.')}: {'OK' if ok else 'ERROR'} — {out[:3000]}" if ok else f"LIST_DIR: {out}")
            if not ok:
                all_ok = False
        elif t == "DELETE_FILE":
            ok, out = _do_delete_file(action.get("path") or "")
            results.append(f"DELETE_FILE {action.get('path', '')}: {out}")
            if not ok:
                all_ok = False
        elif t == "DELETE_DIR":
            ok, out = _do_delete_dir(action.get("path") or "")
            results.append(f"DELETE_DIR {action.get('path', '')}: {out}")
            if not ok:
                all_ok = False
        elif t == "GREP":
            ok, out = _do_grep(action.get("pattern") or "", action.get("path_limit"))
            results.append(f"GREP: {'OK' if ok else 'ERROR'} — {out[:3000]}" if ok else f"GREP: {out}")
            if not ok:
                all_ok = False
        elif t == "RUN_COMMAND":
            ok, out = _do_run_command(action.get("command") or "")
            results.append(f"RUN_COMMAND: {'OK' if ok else 'ERROR'} — {out[:3000]}" if ok else f"RUN_COMMAND: {out}")
            if not ok:
                all_ok = False
        else:
            results.append(f"Acción desconocida: {t}")
            all_ok = False
    return all_ok, results


def _run_file_tools_in_response(text: str) -> Tuple[str, bool, list]:
    """
    Si la respuesta de Ollama contiene READ_FILE:, WRITE_FILE:, LIST_DIR:, GREP:, RUN_COMMAND:,
    ejecuta las acciones y devuelve (texto_para_usuario, hubo_herramientas, lista de resultados).
    """
    results = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        s_clean = re.sub(r"^(\d+\.|\-|\*)\s+", "", s)
        if s_clean.startswith("READ_FILE:"):
            path = line.split("READ_FILE:", 1)[1].strip().strip("'\"")
            if path:
                ok, out = _do_read_file(path)
                res = f"READ_FILE {path}: {'OK' if ok else 'ERROR'} — {out[:4000]}" if ok else f"READ_FILE {path}: {out}"
                results.append(res)
            i += 1
            continue
        if s_clean.startswith("WRITE_FILE:"):
            path = line.split("WRITE_FILE:", 1)[1].strip().strip("'\"")
            i += 1
            content_lines = []
            while i < len(lines) and not _is_end_file_line(lines[i]):
                content_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            content = "\n".join(content_lines)
            if path:
                ok, out = _do_write_file(path, content)
                results.append(f"WRITE_FILE {path}: {out}")
            continue
        if s_clean.startswith("LIST_DIR:"):
            path = line.split("LIST_DIR:", 1)[1].strip().strip("'\"").strip() or "."
            ok, out = _do_list_dir(path)
            results.append(f"LIST_DIR {path}: {'OK' if ok else 'ERROR'} — {out[:3000]}" if ok else f"LIST_DIR {path}: {out}")
            i += 1
            continue
        if s_clean.startswith("DELETE_FILE:"):
            path = line.split("DELETE_FILE:", 1)[1].strip().strip("'\"")
            if path:
                ok, out = _do_delete_file(path)
                results.append(f"DELETE_FILE {path}: {out}")
            i += 1
            continue
        if s_clean.startswith("DELETE_DIR:"):
            path = line.split("DELETE_DIR:", 1)[1].strip().strip("'\"")
            if path:
                ok, out = _do_delete_dir(path)
                results.append(f"DELETE_DIR {path}: {out}")
            i += 1
            continue
        if s_clean.startswith("GREP:"):
            rest = line.split("GREP:", 1)[1].strip().strip("'\"")
            parts = rest.split(None, 1)
            pattern = parts[0] if parts else ""
            path_limit = parts[1].strip() if len(parts) > 1 else None
            if pattern:
                ok, out = _do_grep(pattern, path_limit)
                results.append(f"GREP '{pattern}': {'OK' if ok else 'ERROR'} — {out[:3000]}" if ok else f"GREP: {out}")
            i += 1
            continue
        if s.startswith("RUN_COMMAND:"):
            cmd = line.split("RUN_COMMAND:", 1)[1].strip().strip("'\"")
            if cmd:
                ok, out = _do_run_command(cmd)
                results.append(f"RUN_COMMAND: {'OK' if ok else 'ERROR'} — {out[:3000]}" if ok else f"RUN_COMMAND: {out}")
            i += 1
            continue
        i += 1
    if not results:
        return text, False, []
    return text, True, results


@app.get("/autonomous/read_file")
def autonomous_read_file(path: str = ""):
    """
    Lee un archivo del workspace de ADA (env ADA_WORKSPACE).
    Query: ?path=ruta/relativa/archivo.py
    Devuelve content (texto) o error si no existe o path no permitido.
    """
    path = (path or "").strip()
    if not path:
        return {"status": "error", "detail": "Falta query 'path'."}
    try:
        full_path = _resolve_workspace_path(path)
    except ValueError as e:
        return {"status": "error", "detail": str(e)}
    if not os.path.isfile(full_path):
        return {"status": "error", "detail": "El archivo no existe."}
    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"status": "ok", "path": path, "content": content}
    except OSError as e:
        return {"status": "error", "detail": f"No se pudo leer: {e}"}


@app.post("/execute_plan")
def execute_plan(body: dict = Body(default={})):
    """
    Ejecuta un plan de acciones previamente generado por ADA (READ_FILE, WRITE_FILE, LIST_DIR, etc.).
    Body: {"plan": [ {"type": "WRITE_FILE", "path": "...", "content": "..."}, ... ]}.
    Devuelve los resultados de cada acción para que el usuario los vea en el chat.
    """
    plan = body.get("plan") or body.get("pending_plan")
    if not isinstance(plan, list) or len(plan) == 0:
        return {"status": "error", "detail": "Falta 'plan' (lista de acciones) en el body.", "results": []}
    try:
        all_ok, results = _execute_plan(plan)
        return {"status": "done" if all_ok else "done_with_errors", "results": results}
    except Exception as e:
        return {"status": "error", "detail": str(e), "results": []}


@app.post("/autonomous/write_file")
def autonomous_write_file(body: dict = Body(default={})):
    """
    Escribe un archivo en el workspace de ADA (env ADA_WORKSPACE).
    Body: {"path": "ruta/relativa/archivo.py", "content": "contenido del archivo"}.
    Para que ADA pueda editar código en tu proyecto, monta una carpeta en el contenedor y define ADA_WORKSPACE.
    """
    path = (body.get("path") or "").strip()
    content = body.get("content")
    if not path:
        return {"status": "error", "detail": "Falta 'path' en el body."}
    try:
        full_path = _resolve_workspace_path(path)
    except ValueError as e:
        return {"status": "error", "detail": str(e)}
    try:
        os.makedirs(os.path.dirname(full_path) or ".", exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content if content is not None else "")
        return {"status": "ok", "path": path, "full_path": full_path}
    except OSError as e:
        return {"status": "error", "detail": f"No se pudo escribir: {e}"}


@app.get("/web_search")
def web_search(query: str):
    """
    Web research for ADA learning/self_improve (safe DuckDuckGo lite scrape).
    Query: ?query=autonomous+llm+self+modify → curl lite → Ollama summarize.
    """
    if not query:
        return {"status": "error", "detail": "Missing query param"}

    # Safe DuckDuckGo lite (text-only, no JS/trackers)
    url = f"https://duckduckgo.com/lite/?q={requests.utils.quote(query)}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return {"status": "error", "detail": f"HTTP {r.status_code}"}

        # Extract top results (simple parse)
        html = r.text
        results = re.findall(r'<a rel="nofollow" href="([^"]*)"[^>]*>([^<]*)</a>', html)[:5]
        snippets = [f"{title}: {link}" for link, title in results]
        raw = "\n".join(snippets)[:4000]

        # Ollama summarize
        prompt = (
            f"Summarize key insights from web search '{query}':\n{raw}\n\n"
            f'JSON: {{"insights": ["bullet1", "bullet2"], "sources": {len(results)}}}'
        )
        ollama_payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "options": {"num_predict": 512},
        }
        o_r = requests.post(OLLAMA_URL, json=ollama_payload, timeout=30)
        if o_r.status_code == 200:
            summary = o_r.json().get("response", raw[:500])
            return {"status": "ok", "query": query, "summary": summary, "raw_snippets": snippets}
        return {"status": "ok", "query": query, "raw_snippets": snippets[:3]}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/self_improve")
def self_improve(trigger: str = "auto"):
    """
    ADA Self-Improvement: learnings + web_search → propose/apply safe code diffs.
    """
    # Gather context
    learn_resp, _ = _get(MEMORY_URL + "/get_many?keys=human_decisions,evolution_score")
    learnings = learn_resp
    score = learnings.get("evolution_score", {"composite": 0.5})["composite"]

    # Web research
    web_q = "llm autonomous agent self improve code patterns docker spawn"
    web = web_search(web_q)
    web_insights = web.get("summary", "")

    # Read self + prompt
    code_ok, code = _do_read_file("agent-core/src/agent_core_api.py")
    prompt_ok, self_prompt = _do_read_file("ada/prompts/self_improve.md")
    if not code_ok:
        code = ""
    if not prompt_ok:
        self_prompt = "Propose low-risk JSON edits."

    prompt = f"{self_prompt}\n\nCode: {code[:3000]}\nLearnings: {json.dumps(learnings)[:1000]}\nWeb: {web_insights}\nScore: {score}"

    ollama_p = {"model": OLLAMA_MODEL, "prompt": prompt, "options": {"num_predict": 1024}}
    o_r = requests.post(OLLAMA_URL, json=ollama_p, timeout=60)
    resp = "{}"
    if o_r.status_code == 200:
        try:
            resp = o_r.json().get("response", "{}")
        except Exception:
            # Ollama may return non-JSON or concatenated payloads in some failures.
            raw = (o_r.text or "").strip()
            m = re.search(r"\{[\s\S]*\}", raw)
            resp = m.group(0) if m else "{}"

    try:
        edits_json = json.loads(resp)
        edits = edits_json.get("edits", [])
        risk = edits_json.get("risk", "high")
    except Exception:
        return {"status": "parse_fail", "raw": resp}

    # Low-risk auto-apply (no POLICY_URL, <3 edits, low risk)
    if not POLICY_URL and risk == "low" and len(edits) <= 3:
        applied = []
        for e in edits:
            f = e.get("file")
            old = e.get("old_str")
            new = e.get("new_str")
            if f and old and new:
                ok_f, current = _do_read_file(f)
                if ok_f and old in current:
                    updated = current.replace(old, new, 1)
                    _, msg = _do_write_file(f, updated)
                    applied.append({"file": f, "msg": msg})
        _post_optional(LOG_URL, {"service_name": "self_improve", "event_type": "auto_applied", "payload": {"edits": len(applied)}})
        return {"status": "improved", "applied": len(applied), "details": applied, "est_score": score + 0.15}
    return {"status": "proposed", "risk": risk, "edits": edits, "needs_review": True}


@app.get("/spawn_agent")
def spawn_agent(agent_name: str = "ALMA"):
    """
    Spawn agent from specs: generate files → docker-compose append (idempotente) → up.
    """
    raw_name = (agent_name or "ALMA").strip()
    if not re.match(r"^[A-Za-z][A-Za-z0-9_-]{1,31}$", raw_name):
        return {"status": "error", "detail": "agent_name inválido. Usa letras/números/_/- y empieza por letra."}

    safe_name = raw_name
    service_name = f"agent-{safe_name.lower()}"
    container_name = f"ada_{safe_name.lower()}"

    specs_text = ""
    ok_specs, specs_out = _do_read_file("agentSpecifications.md")
    if ok_specs:
        specs_text = specs_out[:2500]

    agent_dir = f"agents/{safe_name}"
    dockerfile = f"""FROM python:3.11-slim
WORKDIR /app/{safe_name}
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
ENV AGENT_NAME={safe_name}
EXPOSE 3011
CMD ["python", "src/agent_api.py"]
"""
    api_stub = f"""from fastapi import FastAPI

app = FastAPI(title="{safe_name} Agent", version="0.1.0")

@app.get("/health")
def health():
    return {{"agent": "{safe_name}", "status": "ready"}}

@app.get("/")
def root():
    return {{"agent": "{safe_name}", "message": "Agent active"}}
"""
    requirements_txt = "fastapi==0.115.0\nuvicorn==0.30.6\n"

    writes = []
    ok, msg = _do_write_file(f"{agent_dir}/Dockerfile", dockerfile)
    writes.append({"file": f"{agent_dir}/Dockerfile", "ok": ok, "msg": msg})
    ok, msg = _do_write_file(f"{agent_dir}/src/agent_api.py", api_stub)
    writes.append({"file": f"{agent_dir}/src/agent_api.py", "ok": ok, "msg": msg})
    ok, msg = _do_write_file(f"{agent_dir}/requirements.txt", requirements_txt)
    writes.append({"file": f"{agent_dir}/requirements.txt", "ok": ok, "msg": msg})

    if not all(w["ok"] for w in writes):
        return {"status": "error", "detail": "No se pudieron escribir todos los archivos.", "writes": writes}

    compose_rel = "docker-compose.yml"
    compose_ok, compose_content = _do_read_file(compose_rel)
    if not compose_ok:
        return {"status": "error", "detail": f"No se pudo leer {compose_rel}: {compose_content}", "writes": writes}

    service_marker = f"  {service_name}:"
    compose_updated = False
    if service_marker not in compose_content:
        insertion_block = f"""

  {service_name}:
    build: ./{agent_dir}
    container_name: {container_name}
    ports:
      - "3011:3011"
"""
        if "\nvolumes:\n" in compose_content:
            compose_content = compose_content.replace("\nvolumes:\n", insertion_block + "\nvolumes:\n", 1)
        else:
            compose_content = compose_content.rstrip() + insertion_block + "\n"
        w_ok, w_msg = _do_write_file(compose_rel, compose_content)
        if not w_ok:
            return {"status": "error", "detail": f"No se pudo actualizar {compose_rel}: {w_msg}", "writes": writes}
        compose_updated = True

    up_stdout = ""
    up_stderr = ""
    up_rc = 0
    try:
        proc = subprocess.run(
            ["docker", "compose", "up", "-d", service_name],
            capture_output=True,
            text=True,
            timeout=180,
        )
        up_stdout = (proc.stdout or "")[:2000]
        up_stderr = (proc.stderr or "")[:2000]
        up_rc = int(proc.returncode or 0)
    except Exception as e:
        up_stderr = str(e)
        up_rc = 1

    status = "spawned" if up_rc == 0 else "spawned_files_only"
    return {
        "status": status,
        "agent": safe_name,
        "service_name": service_name,
        "compose_updated": compose_updated,
        "specs_context_used": bool(specs_text),
        "files": [w["file"] for w in writes],
        "docker_up": {
            "ok": up_rc == 0,
            "returncode": up_rc,
            "stdout": up_stdout,
            "stderr": up_stderr,
        },
        "next": f"docker compose logs -f {service_name}",
    }


@app.post("/generate")
def generate_and_propose(req: Optional[GenerateRequest] = None):
    """
    Opcional: genera propuesta con Ollama (LLM) y luego ejecuta el flujo /propose.
    Si Ollama no está disponible, devuelve error o propuesta por defecto.
    """
    prompt = (req or GenerateRequest()).prompt
    ollama_payload = {
        "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
        "prompt": prompt + "\nResponde solo con un JSON válido: {\"task_name\": \"...\", \"details\": {\"description\": \"...\"}}",
        "stream": False,
    }
    try:
        r = requests.post(OLLAMA_URL, json=ollama_payload, timeout=60)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Ollama error: {r.text[:200]}")
        data = r.json()
        response_text = data.get("response", "").strip()
        # Intentar extraer JSON de la respuesta (puede venir con markdown o texto extra)
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            parsed = json.loads(response_text)
            task_name = parsed.get("task_name", "generated_task")
            details = parsed.get("details", {"description": response_text[:200]})
        except (json.JSONDecodeError, KeyError):
            task_name = "generated_task"
            details = {"description": response_text[:500] or "Sin descripción"}
        proposal = Proposal(task_name=task_name, details=details)
        return propose_task(proposal)
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Ollama unreachable: {e}")


# --- ADA v2 / v2.5 API (goals, ideas, opportunities, conversation, research, self-improvement) ---
try:
    from ada_core.memory_manager import MemoryManager
    from ada_core.conversation_engine import ConversationEngine, ADA_SYSTEM_PROMPT_V2
    from ada_core.research_engine import research_goal
    from ada_core.self_improvement_engine import analyze_system_bottlenecks
    from ada_core.decision_engine import select_best_opportunities

    _v2_memory = MemoryManager()
    _v2_conversation = ConversationEngine(system_prompt=ADA_SYSTEM_PROMPT_V2)

    @app.get("/v2/goals")
    def v2_get_goals():
        """Active goals. Never fails; returns [] if DB unavailable."""
        return {"goals": _v2_memory.get_active_goals()}

    @app.post("/v2/goals")
    def v2_add_goal(goal: str = Body(..., embed=True)):
        """Add a goal. Returns id or 503 if DB unavailable."""
        gid = _v2_memory.add_goal(goal)
        if gid is None:
            raise HTTPException(status_code=503, detail="Memory unavailable")
        return {"id": gid, "goal": goal, "status": "active"}

    @app.get("/v2/ideas")
    def v2_get_ideas(goal_id: Optional[int] = None):
        """Ideas, optionally for one goal. Never fails."""
        if goal_id is not None:
            return {"ideas": _v2_memory.get_ideas_for_goal(goal_id)}
        return {"ideas": []}

    @app.get("/v2/opportunities")
    def v2_get_opportunities(goal_id: Optional[int] = None, status: str = "pending"):
        """Opportunities (ideas evaluadas con score). Never fails."""
        return {"opportunities": _v2_memory.get_opportunities(goal_id=goal_id, status=status)}

    @app.get("/v2/opportunities/top")
    def v2_get_opportunities_top():
        """Top scored opportunities (score >= threshold, sorted, top N). Never fails."""
        return {"opportunities": select_best_opportunities(_v2_memory)}

    @app.get("/v2/goals/derived")
    def v2_get_derived_goals(parent_goal_id: Optional[int] = None, status: str = "active"):
        """Dynamically generated (derived) goals. Never fails."""
        return {"goals": _v2_memory.get_derived_goals(parent_goal_id=parent_goal_id, status=status)}

    @app.get("/v2/plans")
    def v2_get_plans():
        """Generated action plans (from best opportunities). Never fails."""
        return {"plans": _v2_memory.get_plans()}

    @app.get("/v2/experiences")
    def v2_get_experiences():
        """Recent experiences (event, result, learning). Never fails."""
        return {"experiences": _v2_memory.get_recent_experiences()}

    @app.post("/v2/chat")
    def v2_chat(message: str = Body(..., embed=True), history: Optional[list] = Body(None, embed=True)):
        """Minimal conversation with ADA v2 prompt. Safe response on failure."""
        response = _v2_conversation.respond(message or "", history=history)
        return {"response": response}

    @app.post("/v2/chat/structured")
    def v2_chat_structured(message: str = Body(..., embed=True), history: Optional[list] = Body(None, embed=True)):
        """Conversation with structured response (Análisis, Propuesta, Riesgos, Siguiente paso)."""
        response = _v2_conversation.respond_structured(message or "", history=history)
        return {"response": response}

    @app.post("/v2/research")
    def v2_research(goal: str = Body(..., embed=True), context: str = Body("", embed=True)):
        """Research a goal; returns analysis/strategies (internal, no web)."""
        return {"analysis": research_goal(goal, context)}

    @app.get("/v2/self-improvement")
    def v2_self_improvement():
        """Analyze system bottlenecks and improvement suggestions."""
        return {"analysis": analyze_system_bottlenecks()}

    # --- ADA v3 API (operational autonomous cognitive agent) ---
    @app.get("/v3/opportunities/top")
    def v3_get_opportunities_top():
        """Top scored opportunities. Never fails."""
        return {"opportunities": select_best_opportunities(_v2_memory)}

    @app.get("/v3/goals/derived")
    def v3_get_goals_derived(parent_goal_id: Optional[int] = None, status: str = "active"):
        """Dynamically generated (derived) goals. Never fails."""
        return {"goals": _v2_memory.get_derived_goals(parent_goal_id=parent_goal_id, status=status)}

    @app.get("/v3/plans")
    def v3_get_plans():
        """Generated action plans (from action_plans table + experiences). Never fails."""
        action_plans = _v2_memory.get_action_plans(limit=30)
        if action_plans:
            return {"plans": action_plans, "from_table": True}
        return {"plans": _v2_memory.get_plans(), "from_table": False}

    @app.get("/v3/learning")
    def v3_get_learning():
        """Recent learnings (experiences with learning/evaluation). Never fails."""
        return {"learning": _v2_memory.get_learning()}

    @app.post("/v3/chat/structured")
    def v3_chat_structured(message: str = Body(..., embed=True), history: Optional[list] = Body(None, embed=True)):
        """Structured response (Analysis, Proposal, Risks, Next Step)."""
        response = _v2_conversation.respond_structured(message or "", history=history)
        return {"response": response}

    @app.post("/v3/research")
    def v3_research(goal: str = Body(..., embed=True), context: str = Body("", embed=True)):
        """Research a goal; returns analysis/strategies."""
        return {"analysis": research_goal(goal, context)}

    # --- ADA v3 workspaces & agent market ---
    from ada_core.agent_manager import list_agents, get_agent_skills
    from ada_core.agent_market import list_agent_proposals, propose_new_agent

    @app.get("/v3/agents")
    def v3_list_agents():
        """List available workspace agent types (developer, business, research, general)."""
        return {"agents": list_agents()}

    @app.get("/v3/agents/{agent_type}/skills")
    def v3_agent_skills(agent_type: str):
        """Skills for a given agent type."""
        return {"agent_type": agent_type, "skills": get_agent_skills(agent_type)}

    @app.get("/agent_market/proposals")
    def agent_market_proposals(status: Optional[str] = None):
        """List agent proposals (pending/approved/rejected)."""
        return {"proposals": list_agent_proposals(status=status)}

    @app.post("/agent_market/propose")
    def agent_market_propose(
        domain: str = Body(..., embed=True),
        required_skills: List[str] = Body(..., embed=True),
        purpose: str = Body("", embed=True),
    ):
        """Propose a new agent (human approval required to create)."""
        result = propose_new_agent(domain, required_skills, purpose)
        if not result.get("ok"):
            raise HTTPException(status_code=400, detail=result.get("error", "Proposal failed"))
        return result

    def _get_hardware_telemetry():
        """Get basic CPU and Memory usage without psutil if possible."""
        telemetry = {"cpu_usage_percent": 0, "memory_usage_percent": 0, "disk_usage": {"percent": 0}}
        try:
            # CPU (Load average as proxy)
            load1, _, _ = os.getloadavg()
            import multiprocessing
            cpus = multiprocessing.cpu_count()
            telemetry["cpu_usage_percent"] = min(100, int((load1 / cpus) * 100))
            
            # Memory (from /proc/meminfo)
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", "r") as f:
                    meminfo = {line.split(":")[0]: line.split(":")[1].strip() for line in f}
                    total = int(meminfo.get("MemTotal", "0").split()[0])
                    available = int(meminfo.get("MemAvailable", meminfo.get("MemFree", "0")).split()[0])
                    if total > 0:
                        telemetry["memory_usage_percent"] = int(((total - available) / total) * 100)
            
            # Disk (using df)
            res = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
            if res.returncode == 0:
                lines = res.stdout.strip().split("\n")
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) > 4:
                        percent_str = parts[4].replace("%", "")
                        telemetry["disk_usage"]["percent"] = int(percent_str)
        except Exception:
            pass
        return telemetry

    def _check_service_health(url: str) -> str:
        if not url: return "offline"
        try:
            r = requests.get(f"{url.rstrip('/')}/health", timeout=2)
            return "ok" if r.status_code == 200 else "error"
        except Exception:
            return "offline"

    @app.get("/system/monitor")
    def system_monitor():
        """System monitor: hardware telemetry + service health + ADA state."""
        try:
            telemetry = _get_hardware_telemetry()
            
            # Check Postgres via psycopg2 if possible
            db_status = "offline"
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=os.getenv("PG_HOST", "postgres"),
                    port=os.getenv("PG_PORT", "5432"),
                    user=os.getenv("PG_USER", "ada_user"),
                    password=os.getenv("PG_PASSWORD", "supersecret"),
                    dbname=os.getenv("PG_DB", "ada_main"),
                    connect_timeout=2
                )
                conn.close()
                db_status = "ok"
            except Exception:
                db_status = "error"

            services = {
                "db": db_status,
                "task_runner": _check_service_health(TASK_URL),
                "memory_service": _check_service_health(MEMORY_URL),
            }

            goals = _v2_memory.get_active_goals()
            opportunities = _v2_memory.get_opportunities(status="pending")[:10]
            experiences = _v2_memory.get_recent_experiences(limit=10)
            plans = _v2_memory.get_action_plans(limit=5) if hasattr(_v2_memory, "get_action_plans") else []
            
            return {
                "agents": list_agents(),
                "goals_count": len(goals),
                "goals": goals[:5],
                "opportunities_count": len(opportunities),
                "opportunities": opportunities[:5],
                "recent_experiences": experiences,
                "recent_plans": plans,
                "services": services,
                **telemetry
            }
        except Exception as e:
            return {"error": str(e), "agents": list_agents(), "services": {"db": "offline", "task_runner": "offline"}}

except ImportError:
    pass
