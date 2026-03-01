#!/usr/bin/env python3
"""
Envía un mensaje de prueba a un usuario de Telegram.
Uso:
  TELEGRAM_BOT_TOKEN=tu_token TELEGRAM_CHAT_ID=123456789 python send_test_to_telegram.py
  TELEGRAM_BOT_TOKEN=tu_token TELEGRAM_CHAT_ID=123456789 python send_test_to_telegram.py "Texto opcional"
  python send_test_to_telegram.py --get-updates   # lista chat_id de quienes han escrito al bot (para obtener el de @poncho220)
"""
import os
import sys
import json

try:
    import httpx
except ImportError:
    print("Instala httpx: pip install httpx")
    sys.exit(1)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def get_updates():
    """Muestra los últimos chats que han escrito al bot (para obtener el chat_id de @poncho220)."""
    if not TELEGRAM_BOT_TOKEN:
        print("Define TELEGRAM_BOT_TOKEN")
        return
    r = httpx.get(f"{BASE}/getUpdates", timeout=10)
    data = r.json()
    if not data.get("ok"):
        print("Error:", data)
        return
    for u in data.get("result", [])[-20:]:
        msg = u.get("message") or u.get("edited_message") or {}
        chat = msg.get("chat", {})
        cid = chat.get("id")
        username = (chat.get("username") or "").strip() or "(sin username)"
        first = (chat.get("first_name") or "").strip()
        print(f"  chat_id={cid}  username=@{username}  name={first}")
    if not data.get("result"):
        print("Nadie ha escrito al bot aún. Pide a @poncho220 que abra tu bot y envíe /start; luego vuelve a ejecutar con --get-updates.")


def send_test(text: str):
    """Envía el mensaje de prueba al TELEGRAM_CHAT_ID."""
    if not TELEGRAM_BOT_TOKEN:
        print("Define TELEGRAM_BOT_TOKEN (token de @BotFather)")
        sys.exit(1)
    if not TELEGRAM_CHAT_ID:
        print("Define TELEGRAM_CHAT_ID (número). Para obtenerlo: ejecuta con --get-updates después de que @poncho220 envíe /start a tu bot.")
        sys.exit(1)
    body = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    r = httpx.post(f"{BASE}/sendMessage", json=body, timeout=10)
    out = r.json()
    if out.get("ok"):
        print("Enviado correctamente a chat_id", TELEGRAM_CHAT_ID)
    else:
        print("Error:", out.get("description", out))
        if "chat not found" in str(out.get("description", "")).lower() or "user not found" in str(out.get("description", "")).lower():
            print("  → Ese usuario debe haber iniciado tu bot (enviar /start) antes de poder recibir mensajes.")


if __name__ == "__main__":
    if "--get-updates" in sys.argv:
        get_updates()
        sys.exit(0)
    text = " ".join(a for a in sys.argv[1:] if not a.startswith("--")) or "Hola, este es un mensaje de prueba desde ADA."
    send_test(text)
