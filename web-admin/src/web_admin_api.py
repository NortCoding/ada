"""
A.D.A — Web Admin (F5)
Backend: proxy a agent-core, memory-db, financial-ledger. Dashboard humano–agente.
"""
import os
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from fastapi import Body, FastAPI, HTTPException
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import subprocess
import shlex

app = FastAPI(title="A.D.A Web Admin", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENT_URL = os.getenv("AGENT_URL", "http://agent-core:3001").rstrip("/")
MEMORY_URL = os.getenv("MEMORY_URL", "http://memory-db:3005").rstrip("/")
LEDGER_URL = (os.getenv("LEDGER_URL") or "").strip().rstrip("/")
LOG_URL = (os.getenv("LOG_URL") or "").strip().rstrip("/")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30"))
# Chat puede tardar más (agent-core espera a Ollama hasta OLLAMA_CHAT_TIMEOUT)
CHAT_REQUEST_TIMEOUT = float(os.getenv("CHAT_REQUEST_TIMEOUT", "180"))

# In-memory flag to represent human-initiated "connected" state in the web-admin UI.
# This is only for UI convenience; real connectivity is validated via /agent/health pings.
AGENT_CONNECTED = False


# --- Proxy API (para el frontend y para pruebas) ---

class ProposalBody(BaseModel):
    task_name: str
    details: dict


class ApproveBody(BaseModel):
    task_name: str
    details: dict
    comment: Optional[str] = None


class RejectBody(BaseModel):
    proposal: dict
    reason: str = "human_rejected"
    comment: Optional[str] = None


class MemorySetBody(BaseModel):
    key: str
    value: dict


class TransactionBody(BaseModel):
    type: str
    amount: float
    description: str = ""


class ChatMessageBody(BaseModel):
    role: str = "user"
    content: str = ""
    text: Optional[str] = None  # el frontend a veces envía text


class ChatBody(BaseModel):
    message: str = ""
    use_ollama: bool = True
    history: Optional[list[ChatMessageBody]] = None
    image_base64: Optional[str] = None  # Imagen en base64 para que ADA pueda leer (vision)


class ChatHistoryItem(BaseModel):
    role: str
    text: str
    brain: Optional[str] = None


class ChatHistoryBody(BaseModel):
    history: list[ChatHistoryItem]


class LearnBody(BaseModel):
    key: str
    value: dict


class FileWriteBody(BaseModel):
    path: str
    content: str
    commit: bool = False
    commit_message: Optional[str] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok", "service": "web-admin"}


@app.post("/api/propose")
async def api_propose(body: ProposalBody):
    """Proxy a agent-core POST /propose."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(f"{AGENT_URL}/propose", json=body.model_dump())
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.get("/api/memory/get/{key}")
async def api_memory_get(key: str):
    """Proxy a memory-db GET /get/{key}."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{MEMORY_URL}/get/{key}")
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.post("/api/memory/set")
async def api_memory_set(body: MemorySetBody):
    """Proxy a memory-db POST /set."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(f"{MEMORY_URL}/set", json=body.model_dump())
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.get("/api/memory/keys")
async def api_memory_keys(prefix: str = ""):
    """Proxy a memory-db GET /keys."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{MEMORY_URL}/keys", params={"prefix": prefix})
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.post("/api/ledger/transaction")
async def api_ledger_transaction(body: TransactionBody):
    """Proxy a financial-ledger POST /transaction. 503 si ledger no está configurado."""
    if not LEDGER_URL:
        raise HTTPException(status_code=503, detail="financial-ledger no configurado")
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(f"{LEDGER_URL}/transaction", json=body.model_dump())
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.get("/api/ledger/transactions")
async def api_ledger_transactions(limit: int = 100):
    """Proxy a financial-ledger GET /transactions. Lista vacía si no está configurado."""
    if not LEDGER_URL:
        return {"transactions": []}
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{LEDGER_URL}/transactions", params={"limit": limit})
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.get("/api/balance")
async def api_balance():
    """Proxy a financial-ledger GET /balance. Si no está configurado o no está disponible, devuelve ceros."""
    default = {"income": 0, "expense": 0, "balance": 0, "can_use_paid_tools": False}
    if not LEDGER_URL:
        return default
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            r = await client.get(f"{LEDGER_URL}/balance")
        if r.status_code >= 400:
            return default
        return r.json()
    except Exception:
        return default


@app.get("/api/agent/health")
async def api_agent_health():
    """Estado de agent-core."""
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            r = await client.get(f"{AGENT_URL}/health")
            return {"agent-core": r.json() if r.status_code == 200 else {"error": r.text}}
        except Exception as e:
            return {"agent-core": {"error": str(e)}}


# --- Chat y supervisión (MVP interfaz + bot) ---

@app.get("/api/chat/history")
async def api_chat_history():
    """Historial de conversación persistido (memory-db) para no perder contexto del plan."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{MEMORY_URL}/get/chat_history")
    if r.status_code >= 400:
        return {"messages": []}
    data = r.json()
    val = data.get("value") or {}
    messages = val.get("messages") if isinstance(val, dict) else []
    return {"messages": messages if isinstance(messages, list) else []}


@app.post("/api/chat/history")
async def api_chat_history_save(body: ChatHistoryBody):
    """Guarda el historial de chat para no borrarlo al recargar."""
    payload = {"key": "chat_history", "value": {"messages": [{"role": h.role, "text": h.text, "brain": h.brain} for h in body.history]}}
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(f"{MEMORY_URL}/set", json=payload)
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return {"status": "ok", "saved": len(body.history)}


@app.post("/api/chat")
async def api_chat(body: ChatBody):
    """Envía mensaje a A.D.A. Usa el chat clásico /chat (herramientas de archivos, plan antes de ejecutar, visión con imagen)."""
    try:
        message = getattr(body, "message", "") or ""
        history = getattr(body, "history", None)
        history_payload = [{"role": getattr(h, "role", "user"), "content": getattr(h, "content", "") or getattr(h, "text", "")} for h in history] if history else None
        image_base64 = getattr(body, "image_base64", None)

        payload = {"message": message, "use_ollama": getattr(body, "use_ollama", True), "history": history_payload}
        if image_base64:
            payload["image_base64"] = image_base64
        async with httpx.AsyncClient(timeout=CHAT_REQUEST_TIMEOUT) as client:
            r = await client.post(f"{AGENT_URL}/chat", json=payload)

        if r.status_code == 200:
            data = r.json()
            if "response" in data and "status" not in data:
                data.setdefault("status", "done")
            return data
        try:
            data = r.json()
            msg = data.get("response") or data.get("detail") or r.text[:500]
        except Exception:
            msg = r.text[:500] if r.text else "Error en el servidor"
        return {"response": f"**No pude conectar con ADA.** {msg}\n\nRevisa que Ollama (en el host) y agent-core estén en marcha.", "status": "error"}
    except httpx.TimeoutException:
        return {"response": "**Tiempo de espera agotado.** ADA (Ollama) tarda demasiado. Vuelve a intentar o revisa que Ollama esté activo.", "status": "error"}
    except httpx.ConnectError:
        return {"response": "**No se pudo conectar a ADA.** Revisa que agent-core esté en marcha: `docker compose up -d ada_core`.", "status": "error"}
    except Exception as e:
        return {"response": f"**Error al enviar el mensaje.** {str(e)[:300]}\n\nSi sigue fallando, revisa los logs: `docker logs ada_core`.", "status": "error"}


@app.post("/api/execute_plan")
async def api_execute_plan(body: dict):
    """Ejecuta un plan de acciones devuelto por ADA (cuando status es pending_plan). Body: { \"plan\": [...] }."""
    plan = body.get("plan") or body.get("pending_plan")
    if not plan:
        raise HTTPException(status_code=400, detail="Falta 'plan' en el body.")
    async with httpx.AsyncClient(timeout=CHAT_REQUEST_TIMEOUT) as client:
        r = await client.post(f"{AGENT_URL}/execute_plan", json={"plan": plan})
    if r.status_code >= 400:
        return {"status": "error", "detail": r.text[:500], "results": []}
    return r.json()


# --- Proxies ADA v2/v3 (herramientas: objetivos, investigación, auto-mejora, oportunidades, planes, aprendizaje) ---
class AdaGoalBody(BaseModel):
    goal: str


class AdaResearchBody(BaseModel):
    goal: str
    context: str = ""


@app.get("/api/ada/v2/goals")
async def api_ada_v2_goals():
    """Lista objetivos activos de ADA (v2)."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{AGENT_URL}/v2/goals")
    if r.status_code >= 400:
        return {"goals": []}
    return r.json()


@app.post("/api/ada/v2/goals")
async def api_ada_v2_add_goal(body: AdaGoalBody):
    """Añade un objetivo para que ADA lo trabaje en segundo plano (v2)."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(f"{AGENT_URL}/v2/goals", json={"goal": body.goal})
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.get("/api/ada/v2/self-improvement")
async def api_ada_v2_self_improvement():
    """Análisis de cuellos de botella y sugerencias de mejora del sistema (v2)."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{AGENT_URL}/v2/self-improvement")
    if r.status_code >= 400:
        return {"analysis": "No disponible (revisa que agent-core esté en marcha)."}
    return r.json()


@app.post("/api/ada/v2/research")
async def api_ada_v2_research(body: AdaResearchBody):
    """Investiga un objetivo: análisis y estrategias (v2)."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(f"{AGENT_URL}/v2/research", json={"goal": body.goal, "context": body.context})
    if r.status_code >= 400:
        return {"analysis": r.text[:2000] if r.text else "Error en investigación."}
    return r.json()


@app.get("/api/ada/v3/opportunities/top")
async def api_ada_v3_opportunities_top():
    """Oportunidades mejor puntuadas (v3)."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{AGENT_URL}/v3/opportunities/top")
    if r.status_code >= 400:
        return {"opportunities": []}
    return r.json()


@app.get("/api/ada/v3/plans")
async def api_ada_v3_plans():
    """Planes de acción generados por ADA (v3)."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{AGENT_URL}/v3/plans")
    if r.status_code >= 400:
        return {"plans": [], "from_table": False}
    return r.json()


@app.get("/api/ada/v3/learning")
async def api_ada_v3_learning():
    """Aprendizajes recientes (experiencias evaluadas) (v3)."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{AGENT_URL}/v3/learning")
    if r.status_code >= 400:
        return {"learning": []}
    return r.json()


@app.post("/api/ada/v3/research")
async def api_ada_v3_research(body: AdaResearchBody):
    """Investiga un objetivo (v3)."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(f"{AGENT_URL}/v3/research", json={"goal": body.goal, "context": body.context})
    if r.status_code >= 400:
        return {"analysis": r.text[:2000] if r.text else "Error en investigación."}
    return r.json()


async def _register_human_decision(
    proposal: dict, decision: str, reason: Optional[str] = None, comment: Optional[str] = None
):
    """Registra decisión humana en memory-db (human_decisions) para aprendizaje de A.D.A."""
    entry = {
        "proposal": proposal,
        "decision": decision,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if reason:
        entry["reason"] = reason
    if comment:
        entry["comment"] = comment
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        get_r = await client.get(f"{MEMORY_URL}/get/human_decisions")
        data = (get_r.json().get("value") or {}) if get_r.status_code == 200 else {}
        list_val = data.get("entries", []) if isinstance(data, dict) else []
        if not isinstance(list_val, list):
            list_val = []
        list_val.append(entry)
        await client.post(f"{MEMORY_URL}/set", json={"key": "human_decisions", "value": {"entries": list_val}})


@app.post("/api/approve")
async def api_approve(body: ApproveBody):
    """Aprobación humana → agent-core /execute_approved (log + task-runner). Registra en memory-db con comentario opcional."""
    payload = {"task_name": body.task_name, "details": body.details}
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(f"{AGENT_URL}/execute_approved", json=payload)
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    await _register_human_decision(payload, "approved", comment=body.comment)
    return r.json()


@app.post("/api/reject")
async def api_reject(body: RejectBody):
    """Rechazo humano: registrar en logging (si está) y en memory-db (human_decisions). Comentario opcional."""
    payload = {"proposal": body.proposal, "reason": body.reason}
    if body.comment:
        payload["comment"] = body.comment
    log_res = None
    if LOG_URL:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            r = await client.post(
                LOG_URL + "/log",
                json={
                    "service_name": "web-admin",
                    "event_type": "human_rejected",
                    "payload": payload,
                },
            )
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        log_res = r.json()
    await _register_human_decision(
        body.proposal, "rejected", reason=body.reason, comment=body.comment
    )
    return log_res if log_res is not None else {"status": "ok"}


@app.post("/api/learn")
async def api_learn(body: LearnBody):
    """Registro de aprendizaje (sin aprobación; visible en «Lo que A.D.A está aprendiendo»)."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(f"{AGENT_URL}/learn", json=body.model_dump())
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.post("/api/resimulate")
async def api_resimulate(body: ProposalBody):
    """Re-simular: agent-core /propose con execute=false."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(
            f"{AGENT_URL}/propose",
            params={"execute": False},
            json=body.model_dump(),
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.get("/api/events")
async def api_events(limit: int = 50, event_type: Optional[str] = None, service_name: Optional[str] = None):
    """Eventos recientes (logs) desde logging-system. Si no está configurado o no disponible, lista vacía."""
    if not LOG_URL:
        return {"events": []}
    params: dict = {"limit": limit}
    if event_type:
        params["event_type"] = event_type
    if service_name:
        params["service_name"] = service_name
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            r = await client.get(f"{LOG_URL}/events", params=params)
        if r.status_code >= 400:
            return {"events": []}
        return r.json()
    except Exception:
        return {"events": []}


@app.get("/api/score")
async def api_score():
    """Score evolutivo desde memory-db (key evolution_score)."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{MEMORY_URL}/get/evolution_score")
    if r.status_code >= 400:
        return {"value": None}
    data = r.json()
    return {"value": data.get("value")}


@app.post("/api/autonomous/first_plan")
async def api_autonomous_first_plan():
    """Crea el primer plan de ingresos sin supervisión (agent-core + Ollama + memory)."""
    async with httpx.AsyncClient(timeout=CHAT_REQUEST_TIMEOUT) as client:
        r = await client.post(f"{AGENT_URL}/autonomous/first_plan")
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.get("/api/autonomous/register_platforms")
async def api_autonomous_register_platforms():
    """Plataformas donde ADA puede registrarse (correo ada@...); registro asistido con signup-helper."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{AGENT_URL}/autonomous/register_platforms")
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.get("/api/autonomous/vision")
async def api_autonomous_vision():
    """Visión del proyecto, dos cerebros, herramientas actuales y sugeridas, objetivos parciales."""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            r = await client.get(f"{AGENT_URL}/autonomous/vision")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"status": "ok", "vision": "", "brains": [], "tools_current": [], "tools_suggested": [], "partial_objectives": []}


@app.get("/api/autonomous/self_check")
async def api_autonomous_self_check():
    """Autochequeo de ADA: funcionamiento y herramientas (respuesta al instante, sin LLM)."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{AGENT_URL}/autonomous/self_check")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"status": "ok", "message": "No se pudo obtener el autochequeo.", "sufficient": False}


@app.get("/api/autonomous/ollama_status")
async def api_ollama_status():
    """Estado de Ollama (alcanzable, modelos disponibles)."""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(f"{AGENT_URL}/autonomous/ollama_status")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"status": "ok", "reachable": False, "error": "No se pudo comprobar", "models_available": []}


@app.get("/api/autonomous/brain_console")
async def api_brain_console_get(limit: int = 100):
    """ConsolaCerebro: últimos errores del cerebro avanzado y de Ollama."""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            r = await client.get(f"{AGENT_URL}/autonomous/brain_console", params={"limit": limit})
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"status": "ok", "entries": []}


@app.post("/api/autonomous/brain_console/clear")
async def api_brain_console_clear():
    """Limpia la ConsolaCerebro."""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            r = await client.post(f"{AGENT_URL}/autonomous/brain_console/clear")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"status": "ok"}


@app.get("/api/autonomous/resources")
async def api_autonomous_resources():
    """Recursos actuales y solicitados por ADA (para crecer)."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{AGENT_URL}/autonomous/resources")
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.post("/api/autonomous/resources")
async def api_autonomous_set_resources(body: dict = Body(default={})):
    """Guarda recursos que ADA pide (OLLAMA_NUM_CTX, etc.)."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(f"{AGENT_URL}/autonomous/resources", json=body or {})
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.get("/api/autonomous/needs_help")
async def api_autonomous_needs_help():
    """Pasos que requieren tu ayuda + plataformas de registro (para mostrar en el panel)."""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            r = await client.get(f"{AGENT_URL}/autonomous/needs_help")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"steps": [], "platforms": []}


@app.post("/api/autonomous/execute_step")
async def api_autonomous_execute_step(step_index: int = 0):
    """Ejecuta un paso del plan (Ollama o registra 'necesito tu ayuda'). Se muestra en Plan y avances."""
    async with httpx.AsyncClient(timeout=CHAT_REQUEST_TIMEOUT) as client:
        r = await client.post(f"{AGENT_URL}/autonomous/execute_step", params={"step_index": step_index})
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.post("/api/autonomous/create_first_offer")
async def api_autonomous_create_first_offer():
    """ADA crea la primera oferta con autonomía (Ollama + memoria)."""
    async with httpx.AsyncClient(timeout=CHAT_REQUEST_TIMEOUT) as client:
        r = await client.post(f"{AGENT_URL}/autonomous/create_first_offer")
    if r.status_code >= 400:
        return {"status": "error", "response": r.text[:500] or "Error al crear la oferta."}
    return r.json()


@app.post("/api/autonomous/step_done")
async def api_autonomous_step_done(step_index: int = 0, result: str = "", platform: str = ""):
    """Registra que un paso humano del plan está completado (ej. cuenta Gumroad creada)."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(
            f"{AGENT_URL}/autonomous/step_done",
            params={"step_index": step_index, "result": result, "platform": platform},
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.post("/api/autonomous/clear_plan")
async def api_clear_plan():
    """Proxy a agent-core /autonomous/clear_plan."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(f"{AGENT_URL}/autonomous/clear_plan")
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.post("/api/autonomous/reset_all")
async def api_reset_all(clear_chat: bool = False):
    """Proxy a agent-core /autonomous/reset_all. Limpia plan, oferta, pasos; opcionalmente chat. Ver docs/INICIO-DESDE-CERO.md."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(f"{AGENT_URL}/autonomous/reset_all", params={"clear_chat": clear_chat})
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.get("/api/autonomous/plan")
async def api_autonomous_plan():
    """Obtiene el plan actual (first_plan / weekly_plan) desde agent-core."""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            r = await client.get(f"{AGENT_URL}/autonomous/plan")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"status": "ok", "plan": None, "key": None, "step_statuses": []}


# --- Panel agente: /api/agent/* (objetivos ajustados al sistema actual) ---

@app.get("/api/agent/status")
async def api_agent_status():
    """
    Estado agregado del agente: objetivo global, estado, progreso %, plan, paso en ejecución, próximas acciones.
    Persistencia: plan y pasos en memory-db; logs en logging-system.
    """
    status = {
        "goal": None,
        "state": "idle",
        "progress_percent": 0,
        "plan": None,
        "step_statuses": [],
        "step_in_execution": None,
        "next_actions": [],
        "mode": "development",
        "capabilities": {},
    }
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            r_health = await client.get(f"{AGENT_URL}/health")
            if r_health.status_code == 200:
                h = r_health.json()
                status["mode"] = h.get("mode", "development")
            r_plan = await client.get(f"{AGENT_URL}/autonomous/plan")
            if r_plan.status_code == 200:
                data = r_plan.json()
                plan = data.get("plan")
                step_statuses = data.get("step_statuses") or []
                status["plan"] = plan
                status["step_statuses"] = step_statuses
                if plan:
                    status["goal"] = plan.get("goal")
                    steps = plan.get("steps") or []
                    done = sum(1 for s in step_statuses if (s or {}).get("status") == "done")
                    status["progress_percent"] = round(100 * done / len(steps)) if steps else 0
                    status["next_actions"] = [
                        (s.get("action") or str(s)) for i, s in enumerate(steps)
                        if (step_statuses[i] or {}).get("status") != "done"
                    ][:5]
            r_cap = await client.get(f"{AGENT_URL}/autonomous/capabilities")
            if r_cap.status_code == 200:
                status["capabilities"] = r_cap.json()
            if LOG_URL:
                r_events = await client.get(f"{LOG_URL}/events", params={"limit": 20, "service_name": "agent-core"})
                if r_events.status_code == 200:
                    events = (r_events.json() or {}).get("events") or []
                    for ev in reversed(events):
                        if (ev.get("event_type") or "").startswith("plan_step_started"):
                            p = ev.get("payload") or {}
                            status["step_in_execution"] = p.get("step_index")
                            status["state"] = "executing"
                            break
                        if (ev.get("event_type") or "").startswith("plan_step_needs_help"):
                            status["state"] = "needs_human"
                            break
            if status["plan"] and status["state"] == "idle" and status["progress_percent"] < 100:
                status["state"] = "ready"
        except Exception:
            pass
    return {"status": "ok", **status}


@app.post("/api/agent/connect")
async def api_agent_connect(connect: bool = True):
    """Conectar o desconectar la indicación de conexión a agent-core.

    - Si `connect=true`, hace un ping a `agent-core /health` y marca `AGENT_CONNECTED`.
    - Si `connect=false`, marca `AGENT_CONNECTED = False`.
    Esto no crea conexiones persistentes en el servidor; solo facilita control desde la UI.
    """
    global AGENT_CONNECTED
    if connect:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{AGENT_URL}/health")
            ok = r.status_code == 200
            AGENT_CONNECTED = ok
            try:
                data = r.json() if ok else {"text": r.text}
            except Exception:
                data = {"text": r.text}
            return {"connected": ok, "agent": data}
        except Exception as e:
            AGENT_CONNECTED = False
            return {"connected": False, "error": str(e)}
    else:
        AGENT_CONNECTED = False
        return {"connected": False}


@app.get("/api/agent/connect")
async def api_agent_connect_get():
    """Devuelve el estado actual del indicador de conexión (no garantiza reachability)."""
    return {"connected": AGENT_CONNECTED}


@app.post("/api/agent/update")
async def api_agent_update(body: dict = Body(default={})):
    """Opcional: el agente puede enviar estado; por ahora se acepta y se persiste en memory si viene key/value."""
    if body.get("key") and body.get("value") is not None:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            r = await client.post(f"{MEMORY_URL}/set", json={"key": body["key"], "value": body["value"]})
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
    return {"status": "ok"}


@app.post("/api/agent/complete-step")
async def api_agent_complete_step(step_index: int = 0, result: str = "", platform: str = ""):
    """Marcar paso como completado (proxy a autonomous/step_done)."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(
            f"{AGENT_URL}/autonomous/step_done",
            params={"step_index": step_index, "result": result, "platform": platform},
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.get("/api/agent/credentials")
async def api_agent_credentials_get(platform: Optional[str] = None):
    """Obtener metadata de credenciales por plataforma (no se almacenan secretos)."""
    if platform:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            r = await client.get(f"{MEMORY_URL}/get/credentials_{platform}")
        if r.status_code == 200:
            data = r.json()
            return {"status": "ok", "platform": platform, "configured": bool((data.get("value") or {}).get("configured"))}
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{MEMORY_URL}/keys")
    keys = (r.json() or {}).get("keys") or [] if r.status_code == 200 else []
    cred_keys = [k for k in keys if k.startswith("credentials_")]
    return {"status": "ok", "platforms": [k.replace("credentials_", "") for k in cred_keys]}


class CredentialsBody(BaseModel):
    platform: str
    configured: bool = True
    note: str = ""


@app.post("/api/agent/credentials")
async def api_agent_credentials_post(body: CredentialsBody):
    """Indicar que las credenciales para una plataforma están configuradas (metadata; secretos en .env)."""
    key = f"credentials_{body.platform.strip().lower()}"
    value = {"configured": body.configured, "note": body.note or "Ver .env", "updated_at": datetime.now(timezone.utc).isoformat()}
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(f"{MEMORY_URL}/set", json={"key": key, "value": value})
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return {"status": "ok", "platform": body.platform}


def _is_within_repo(root: str, target: str) -> bool:
    try:
        root_p = os.path.realpath(root)
        targ_p = os.path.realpath(target)
        return os.path.commonpath([root_p]) == os.path.commonpath([root_p, targ_p])
    except Exception:
        return False


def _get_repo_root() -> str:
    """Raíz para el explorador de archivos. Si ADA_FILES_ROOT está definido (ej. /dockers en Docker), se usa esa ruta."""
    files_root = (os.getenv("ADA_FILES_ROOT") or "").strip()
    if files_root:
        return os.path.abspath(files_root)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


@app.get("/api/fs/list")
async def api_fs_list(path: str = ""):
    """Lista el contenido de un directorio. path relativo a la raíz (ADA_FILES_ROOT o repo)."""
    repo_root = _get_repo_root()
    rel = (path or ".").strip().strip("/")
    if rel == ".":
        rel = ""
    target_dir = os.path.normpath(os.path.join(repo_root, rel) if rel else repo_root)
    if not os.path.isdir(target_dir):
        raise HTTPException(status_code=404, detail="Not a directory")
    if not _is_within_repo(repo_root, target_dir):
        raise HTTPException(status_code=403, detail="Path outside repository")
    try:
        names = sorted(os.listdir(target_dir))
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e))
    entries = []
    for name in names:
        if name.startswith(".") and name not in (".cursor", ".env", ".git"):
            continue
        full = os.path.join(target_dir, name)
        try:
            is_dir = os.path.isdir(full)
        except OSError:
            continue
        rel_path = os.path.join(rel, name).replace("\\", "/") if rel else name
        entries.append({"name": name, "path": rel_path, "is_dir": is_dir})
    # Carpetas primero, luego archivos
    entries.sort(key=lambda e: (not e["is_dir"], e["name"].lower()))
    return {"path": rel or ".", "entries": entries}


@app.post("/api/fs/write")
async def api_fs_write(body: FileWriteBody, request: Request):
    """Permite escribir archivos dentro del workspace del proyecto.

    Seguridad:
    - Requiere que la variable de entorno `ENABLE_AGENT_FS` esté exactamente en '1' o 'true'.
    - Valida que la ruta esté dentro del repo (no traversal fuera).
    - Opcional: hace commit local si `commit=true`.
    """
    enabled = os.getenv("ENABLE_AGENT_FS", "0").lower() in ("1", "true", "yes")
    if not enabled:
        raise HTTPException(status_code=403, detail="Agent filesystem operations are disabled on this server.")

    repo_root = _get_repo_root()
    target_path = os.path.abspath(os.path.join(repo_root, body.path))

    if not _is_within_repo(repo_root, target_path):
        raise HTTPException(status_code=400, detail="Invalid path: outside of repository root")

    # Ensure directory exists
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(body.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")

    # Log the write operation to logging-system (best-effort, solo si está configurado)
    if LOG_URL:
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                await client.post(
                    LOG_URL + "/log",
                    json={
                        "service_name": "web-admin",
                        "event_type": "fs_write",
                        "payload": {"path": body.path, "actor": "agent", "remote_addr": request.client.host if request.client else None},
                    },
                )
        except Exception:
            pass

    result = {"status": "ok", "path": body.path}

    # Commits and any push to remote are disabled by default. To allow local git commits
    # set environment variable ENABLE_AGENT_GIT_COMMIT to '1' or 'true'. This prevents
    # accidental pushes to GitHub if the server is exposed.
    git_commit_enabled = os.getenv("ENABLE_AGENT_GIT_COMMIT", "0").lower() in ("1", "true", "yes")
    if body.commit:
        if not git_commit_enabled:
            result["committed"] = False
            result["commit_error"] = "Commits are disabled on this server (ENABLE_AGENT_GIT_COMMIT is not set)."
        else:
            # Make a git commit (local). Use provided author metadata if present.
            try:
                subprocess.run(["git", "add", body.path], cwd=repo_root, check=True)
                msg = body.commit_message or f"Agent update: {body.path}"
                env = os.environ.copy()
                if body.author_name:
                    env["GIT_AUTHOR_NAME"] = body.author_name
                if body.author_email:
                    env["GIT_AUTHOR_EMAIL"] = body.author_email
                subprocess.run(["git", "commit", "-m", msg], cwd=repo_root, check=True, env=env)
                result["committed"] = True
            except subprocess.CalledProcessError as e:
                result["committed"] = False
                result["commit_error"] = str(e)

    return result


@app.get("/api/agent/plan-history")
async def api_agent_plan_history(limit: int = 20):
    """Planes anteriores a partir de eventos (autonomous_plan_created, plan_cleared). Lista vacía si logging no está."""
    if not LOG_URL:
        return {"status": "ok", "history": []}
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{LOG_URL}/events", params={"limit": limit * 2, "service_name": "agent-core"})
    if r.status_code != 200:
        return {"status": "ok", "history": []}
    events = (r.json() or {}).get("events") or []
    history = []
    for ev in events:
        t = ev.get("event_type") or ""
        if t == "autonomous_plan_created":
            p = ev.get("payload") or {}
            plan = p.get("plan")
            if plan:
                history.append({"created_at": ev.get("created_at"), "event": t, "plan": plan})
        elif t == "plan_cleared":
            history.append({"created_at": ev.get("created_at"), "event": t, "plan": None})
    return {"status": "ok", "history": history[:limit]}


# --- Dashboard mínimo (HTML + JS) — fallback si no hay frontend build ---

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>A.D.A — Web Admin (FALLBACK)</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; margin: 1rem; max-width: 900px; }
    h1 { color: #1a1a2e; }
    section { margin: 1.5rem 0; padding: 1rem; border: 1px solid #eee; border-radius: 8px; }
    button { padding: 0.5rem 1rem; margin: 0.25rem; cursor: pointer; }
    input, textarea { padding: 0.4rem; margin: 0.25rem; width: 100%; max-width: 400px; }
    pre { background: #f5f5f5; padding: 1rem; overflow: auto; font-size: 0.85rem; }
    .ok { color: #0a0; }
    .err { color: #c00; }
  </style>
</head>
<body>
  <h1>A.D.A — Web Admin</h1>
  <p>Dashboard humano–agente. Score evolutivo y métricas (MVP).</p>

  <section>
    <h2>Propuesta (agent-core)</h2>
    <input id="taskName" placeholder="task_name" value="test_mvp">
    <input id="taskDetails" placeholder="details (JSON)" value='{"description":"Prueba desde web-admin"}'>
    <button onclick="propose()">Enviar propuesta</button>
    <pre id="proposeOut">—</pre>
  </section>

  <section>
    <h2>Memoria (memory-db)</h2>
    <input id="memKey" placeholder="key" value="proposal_001">
    <input id="memValue" placeholder="value (JSON)" value='{"ROI":0.8,"risk":0.1,"efficiency":0.9}'>
    <button onclick="memorySet()">Guardar</button>
    <button onclick="memoryGet()">Leer</button>
    <pre id="memoryOut">—</pre>
  </section>

  <section>
    <h2>Ledger (financial-ledger)</h2>
    <input id="txType" placeholder="type" value="income">
    <input id="txAmount" placeholder="amount" type="number" value="1000">
    <input id="txDesc" placeholder="description" value="Test revenue">
    <button onclick="ledgerTx()">Crear transacción</button>
    <button onclick="ledgerList()">Listar transacciones</button>
    <pre id="ledgerOut">—</pre>
  </section>

  <section>
    <h2>Estado servicios</h2>
    <button onclick="checkHealth()">Comprobar health</button>
    <pre id="healthOut">—</pre>
  </section>

  <script>
    const api = path => fetch(path, { headers: { 'Content-Type': 'application/json' } });
    const apiPost = (path, body) => fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

    async function propose() {
      const out = document.getElementById('proposeOut');
      try {
        const body = { task_name: document.getElementById('taskName').value, details: JSON.parse(document.getElementById('taskDetails').value || '{}') };
        const r = await apiPost('/api/propose', body);
        const j = await r.json();
        out.textContent = JSON.stringify(j, null, 2);
        out.className = r.ok ? 'ok' : 'err';
      } catch (e) { out.textContent = e.message; out.className = 'err'; }
    }
    async function memorySet() {
      const out = document.getElementById('memoryOut');
      try {
        const body = { key: document.getElementById('memKey').value, value: JSON.parse(document.getElementById('memValue').value || '{}') };
        const r = await apiPost('/api/memory/set', body);
        out.textContent = JSON.stringify(await r.json(), null, 2);
        out.className = r.ok ? 'ok' : 'err';
      } catch (e) { out.textContent = e.message; out.className = 'err'; }
    }
    async function memoryGet() {
      const out = document.getElementById('memoryOut');
      try {
        const key = document.getElementById('memKey').value;
        const r = await api('/api/memory/get/' + encodeURIComponent(key));
        out.textContent = JSON.stringify(await r.json(), null, 2);
        out.className = r.ok ? 'ok' : 'err';
      } catch (e) { out.textContent = e.message; out.className = 'err'; }
    }
    async function ledgerTx() {
      const out = document.getElementById('ledgerOut');
      try {
        const body = { type: document.getElementById('txType').value, amount: +document.getElementById('txAmount').value, description: document.getElementById('txDesc').value };
        const r = await apiPost('/api/ledger/transaction', body);
        out.textContent = JSON.stringify(await r.json(), null, 2);
        out.className = r.ok ? 'ok' : 'err';
      } catch (e) { out.textContent = e.message; out.className = 'err'; }
    }
    async function ledgerList() {
      const out = document.getElementById('ledgerOut');
      try {
        const r = await api('/api/ledger/transactions?limit=50');
        out.textContent = JSON.stringify(await r.json(), null, 2);
        out.className = r.ok ? 'ok' : 'err';
      } catch (e) { out.textContent = e.message; out.className = 'err'; }
    }
    async function checkHealth() {
      const out = document.getElementById('healthOut');
      try {
        const r = await api('/api/agent/health');
        out.textContent = JSON.stringify(await r.json(), null, 2);
      } catch (e) { out.textContent = e.message; out.className = 'err'; }
    }
  </script>
</body>
</html>
"""


STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")


@app.get("/")
def index():
    """Sirve React build si existe, sino dashboard HTML mínimo."""
    if os.path.isdir(STATIC_DIR) and os.path.isfile(os.path.join(STATIC_DIR, "index.html")):
        return FileResponse(
            os.path.join(STATIC_DIR, "index.html"),
            headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
        )
    return HTMLResponse(DASHBOARD_HTML)


if os.path.isdir(STATIC_DIR):
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
