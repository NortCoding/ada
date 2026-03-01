"""
A.D.A — Bot puente Telegram (chat remoto con Ollama).
Recibe mensajes → agent-core /chat (Ollama) → responde con la opinión de ADA.
Si ADA devuelve una propuesta pendiente de aprobación, muestra botones /approve, /reject.
Registra decisiones en logging-system y memory-db (human_decisions).
También puede enviar mensajes externos a uno o varios chats (TELEGRAM_CHAT_ID / POST /send).
"""
import json
import logging
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

AGENT_URL = os.getenv("AGENT_URL", "http://agent-core:3001").rstrip("/")
LOG_URL = os.getenv("LOG_URL", "http://logging-system:3006").rstrip("/")
MEMORY_URL = os.getenv("MEMORY_URL", "http://memory-db:3005").rstrip("/")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
# Chat(s) a los que enviar mensajes externos (ej. notificaciones). Uno o varios separados por coma.
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
TELEGRAM_CHAT_IDS: List[str] = [c.strip() for c in TELEGRAM_CHAT_ID.split(",") if c.strip()]
REQUEST_TIMEOUT = 30.0
# Chat con Ollama puede tardar bastante
CHAT_TIMEOUT = float(os.getenv("TELEGRAM_CHAT_TIMEOUT", "180"))
SEND_API_PORT = int(os.getenv("TELEGRAM_SEND_PORT", "8081"))

# Pendientes por chat_id: { "proposal": {...}, "simulation": {...}, "policy": {...}, "id": "chat_001" }
pending: Dict[int, dict] = {}
_pending_id = 0


def _next_pending_id() -> str:
    global _pending_id
    _pending_id += 1
    return f"chat_task_{_pending_id:03d}"


async def _post(path: str, json_data: dict, base_url: Optional[str] = None, timeout: Optional[float] = None) -> Tuple[Optional[dict], int]:
    url = (base_url or AGENT_URL) + path
    t = timeout if timeout is not None else REQUEST_TIMEOUT
    async with httpx.AsyncClient(timeout=t) as client:
        try:
            r = await client.post(url, json=json_data)
            return (r.json() if r.text else None, r.status_code)
        except httpx.TimeoutException:
            logger.warning("Timeout en %s", path)
            return ({"error": "Tiempo de espera agotado. ADA (Ollama) tarda mucho; intenta de nuevo."}, 504)
        except Exception as e:
            logger.exception(e)
            return ({"error": str(e)}, 500)


async def _get(path: str) -> Tuple[Optional[dict], int]:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            r = await client.get(f"{MEMORY_URL}{path}")
            return (r.json() if r.text else None, r.status_code)
        except Exception as e:
            logger.exception(e)
            return (None, 500)


def send_telegram_outbound(text: str, chat_ids: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Envía un mensaje a uno o varios chats de Telegram (mensaje externo a otro número/usuario).
    chat_ids: si no se pasa, usa TELEGRAM_CHAT_IDS (env TELEGRAM_CHAT_ID, o varios separados por coma).
    Para enviar a otro número: esa persona debe haber iniciado el bot al menos una vez; luego obtén su chat_id
    (p. ej. con @userinfobot o revisando getUpdates de la API de Telegram) y úsalo en TELEGRAM_CHAT_ID o en POST /send.
    """
    if not TELEGRAM_BOT_TOKEN:
        return False, "TELEGRAM_BOT_TOKEN no configurado"
    ids = chat_ids or TELEGRAM_CHAT_IDS
    if not ids:
        return False, "Ningún TELEGRAM_CHAT_ID configurado. Define TELEGRAM_CHAT_ID (o varios separados por coma)."
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    sent = 0
    for cid in ids:
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.post(url, json={"chat_id": cid, "text": text[:4096], "parse_mode": "HTML"})
            if r.status_code == 200:
                sent += 1
            else:
                logger.warning("Telegram send to %s: %s %s", cid, r.status_code, r.text[:200])
        except Exception as e:
            logger.warning("Telegram send to %s: %s", cid, e)
    if sent == 0:
        return False, "No se pudo enviar a ningún chat (revisa que hayan iniciado el bot y que TELEGRAM_CHAT_ID sea correcto)."
    return True, f"Enviado a {sent} chat(s)."


async def _register_human_decision(
    proposal: dict, decision: str, reason: Optional[str] = None, comment: Optional[str] = None
) -> None:
    """Append human decision to memory-db human_decisions for A.D.A learning."""
    entry = {
        "proposal": proposal,
        "decision": decision,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "telegram",
    }
    if reason:
        entry["reason"] = reason
    if comment:
        entry["comment"] = comment
    get_r, get_code = await _get("/get/human_decisions")
    data = (get_r.get("value") or {}) if get_code == 200 and get_r else {}
    entries = data.get("entries", []) if isinstance(data, dict) else []
    if not isinstance(entries, list):
        entries = []
    entries.append(entry)
    await _post("/set", {"key": "human_decisions", "value": {"entries": entries}}, base_url=MEMORY_URL)


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    user_id = update.effective_chat.id if update.effective_chat else 0
    message = update.message.text.strip()
    if not message:
        await update.message.reply_text("Escribe un mensaje para A.D.A.")
        return

    await update.message.reply_text("ADA (Ollama) está pensando…")
    data, code = await _post("/chat", {"message": message, "use_ollama": True}, timeout=CHAT_TIMEOUT)

    if code != 200 or not data:
        err = data.get("error") or data.get("detail") if isinstance(data, dict) else str(data)
        await update.message.reply_text(f"❌ Error: {err}")
        return

    # Respuesta de Ollama (agent-core /chat devuelve response + status; opcionalmente proposal si pending_approval)
    response_text = (data.get("response") or "").strip()
    status = data.get("task_result", {}).get("status") or data.get("status", "")
    proposal = data.get("proposal") or (data.get("full") or {}).get("proposal") or {}

    # 1) Siempre enviar la respuesta de ADA (Ollama) si existe
    if response_text:
        # Telegram limita mensajes largos; enviar en bloques si hace falta
        if len(response_text) > 4000:
            for i in range(0, len(response_text), 4000):
                await update.message.reply_text(response_text[i : i + 4000])
        else:
            await update.message.reply_text(response_text)

    # 2) Si hay propuesta pendiente de aprobación, mostrar botones
    if status == "pending_approval" and proposal:
        task_name = proposal.get("task_name") or "tarea"
        details = proposal.get("details") or {}
        pending[user_id] = {
            "id": _next_pending_id(),
            "proposal": {"task_name": task_name, "details": details},
        }
        text = f"📋 *Propuesta pendiente:* {task_name}\nPuedes usar: /approve · /reject · /comment \"tu comentario\""
        keyboard = [
            [
                InlineKeyboardButton("✅ Aprobar", callback_data="approve"),
                InlineKeyboardButton("❌ Rechazar", callback_data="reject"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()
    user_id = update.effective_user.id if update.effective_user else 0
    data = pending.get(user_id)

    if query.data == "approve":
        if not data:
            await query.edit_message_text("No hay propuesta pendiente.")
            return
        prop = data["proposal"]
        out, code = await _post("/execute_approved", prop)
        if code == 200 and out and out.get("status") == "ok":
            await _register_human_decision(prop, "approved")
            await query.edit_message_text(f"✅ Ejecución aprobada y registrada.\n{json.dumps(out.get('task_result', {}), indent=2)}")
        else:
            await query.edit_message_text(f"Error al ejecutar: {out}")
        pending.pop(user_id, None)

    elif query.data == "reject":
        if data:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                await client.post(
                    f"{LOG_URL}/log",
                    json={
                        "service_name": "telegram-bot",
                        "event_type": "human_rejected",
                        "payload": {"proposal": data["proposal"], "source": "telegram"},
                    },
                )
            await _register_human_decision(data["proposal"], "rejected", reason="human_rejected")
        await query.edit_message_text("❌ Propuesta rechazada (registrado en log y memory-db).")
        pending.pop(user_id, None)

    elif query.data == "resimulate":
        if not data:
            await query.edit_message_text("No hay propuesta pendiente.")
            return
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            r = await client.post(f"{AGENT_URL}/propose", params={"execute": False}, json=data["proposal"])
        out, code = (r.json() if r.text else None, r.status_code)
        if code == 200 and out:
            sim = out.get("simulation") or {}
            await query.edit_message_text(
                f"🔄 Re-simulación — ROI: {sim.get('ROI')}, Riesgo: {sim.get('risk')}, Impacto: {sim.get('impact_financial')}"
            )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "Hola. Soy el puente con A.D.A (Agente Digital Autónomo).\n\n"
            "• Escribe cualquier mensaje y A.D.A te responderá con su opinión (cerebro Ollama en tu servidor).\n"
            "• Si ADA devuelve una propuesta que requiera tu aprobación, verás botones o podrás usar:\n"
            "  /approve — ejecutar propuesta pendiente\n"
            "  /reject — rechazar\n"
            "  /comment \"texto\" — comentario para aprendizaje de ADA."
        )


async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /approve [id]: aprueba la propuesta pendiente (o la indicada por id)."""
    if not update.message:
        return
    user_id = update.effective_chat.id if update.effective_chat else 0
    data = pending.get(user_id)
    if not data:
        await update.message.reply_text("No hay propuesta pendiente. Envía un mensaje para obtener una propuesta.")
        return
    prop = data["proposal"]
    out, code = await _post("/execute_approved", prop)
    if code == 200 and out and out.get("status") == "ok":
        await _register_human_decision(prop, "approved")
        await update.message.reply_text(f"✅ Ejecución aprobada y registrada (task-runner).")
    else:
        await update.message.reply_text(f"Error al ejecutar: {out}")
    pending.pop(user_id, None)


async def cmd_reject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /reject [id]: rechaza la propuesta pendiente."""
    if not update.message:
        return
    user_id = update.effective_chat.id if update.effective_chat else 0
    data = pending.get(user_id)
    if not data:
        await update.message.reply_text("No hay propuesta pendiente.")
        return
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        await client.post(
            f"{LOG_URL}/log",
            json={
                "service_name": "telegram-bot",
                "event_type": "human_rejected",
                "payload": {"proposal": data["proposal"], "source": "telegram", "command": "/reject"},
            },
        )
    await _register_human_decision(data["proposal"], "rejected", reason="human_rejected")
    await update.message.reply_text("❌ Propuesta rechazada (registrado en log y memory-db).")
    pending.pop(user_id, None)


async def cmd_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /comment \"Prefiero menor riesgo\": registra comentario en memory-db (opcionalmente asociado a propuesta pendiente)."""
    if not update.message or not update.message.text:
        return
    user_id = update.effective_chat.id if update.effective_chat else 0
    text = (update.message.text or "").strip()
    # Quitar el comando y dejar el comentario
    if text.startswith("/comment"):
        text = text[len("/comment"):].strip().strip('"')
    if not text:
        await update.message.reply_text('Uso: /comment "Prefiero menor riesgo en próximas propuestas"')
        return
    data = pending.get(user_id)
    proposal = data["proposal"] if data else {"task_name": "none", "details": {"description": "comentario sin propuesta"}}
    entry = {
        "proposal": proposal,
        "decision": "comment",
        "comment": text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "telegram",
    }
    get_r, get_code = await _get("/get/human_decisions")
    data_mem = (get_r.get("value") or {}) if get_code == 200 and get_r else {}
    entries = data_mem.get("entries", []) if isinstance(data_mem, dict) else []
    if not isinstance(entries, list):
        entries = []
    entries.append(entry)
    await _post("/set", {"key": "human_decisions", "value": {"entries": entries}}, base_url=MEMORY_URL)
    await update.message.reply_text(f"📝 Comentario registrado para A.D.A: «{text[:100]}»")


# --- API HTTP para enviar mensajes externos a Telegram ---
def _run_send_api() -> None:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    send_app = FastAPI(title="ADA Telegram Send", docs_url=None)

    class SendBody(BaseModel):
        text: str
        chat_id: Optional[str] = None  # opcional: si no se pasa, se usa TELEGRAM_CHAT_ID(s)

    @send_app.post("/send")
    def api_send(body: SendBody):
        """Envía un mensaje a Telegram. Por defecto a TELEGRAM_CHAT_ID; si body.chat_id está definido, a ese chat."""
        ids = [body.chat_id] if body.chat_id else None
        ok, msg = send_telegram_outbound(body.text, chat_ids=ids)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"ok": True, "detail": msg}

    uvicorn.run(send_app, host="0.0.0.0", port=SEND_API_PORT, log_level="warning")


def main() -> None:
    t = threading.Thread(target=_run_send_api, daemon=True)
    t.start()
    logger.info("API de envío externo en http://0.0.0.0:%s/send (POST body: {\"text\": \"...\", \"chat_id\": \"opcional\"})", SEND_API_PORT)
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN no definido. Bot no iniciado.")
        return
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", cmd_approve))
    app.add_handler(CommandHandler("reject", cmd_reject))
    app.add_handler(CommandHandler("comment", cmd_comment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
