#!/usr/bin/env python3
"""
Pruebas de funcionamiento del agent-core (health, chat con Gemini, chat con Ollama).
Ejecutar desde la raíz del repo:
  cd agent-core && python -m pytest tests/test_functional.py -v -s
O con servicios en localhost:3001:
  python tests/test_functional.py
"""
import os
import sys

import requests

# Base URL del agent-core (localhost cuando se corre con docker compose)
BASE_URL = os.getenv("AGENT_CORE_URL", "http://localhost:3001")
TIMEOUT = 60  # Chat puede tardar (Gemini ~5-15s, Ollama más)


def test_health():
    """GET /health debe devolver status ok."""
    r = requests.get(f"{BASE_URL}/health", timeout=10)
    assert r.status_code == 200, f"Health: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("status") == "ok" and data.get("service") == "agent-core"
    print("[OK] Health: agent-core responde.")


def test_chat_gemini():
    """POST /chat con use_advanced_brain=true debe usar Gemini si GEMINI_API_KEY está configurada."""
    payload = {
        "message": "Di solo: Hola, soy ADA y estoy usando Gemini.",
        "use_ollama": True,
        "use_advanced_brain": True,
    }
    r = requests.post(f"{BASE_URL}/chat", json=payload, timeout=TIMEOUT)
    assert r.status_code == 200, f"Chat Gemini: {r.status_code} {r.text}"
    data = r.json()
    assert "response" in data, data
    resp_text = (data.get("response") or "").strip()
    assert len(resp_text) > 0, "Respuesta vacía"
    brain = data.get("brain", "")
    if brain == "gemini":
        print("[OK] Chat con cerebro Gemini:", resp_text[:120] + ("..." if len(resp_text) > 120 else ""))
    else:
        print("[OK] Chat respondió (fallback Ollama, brain=%r):" % brain, resp_text[:120] + ("..." if len(resp_text) > 120 else ""))


def test_chat_ollama():
    """POST /chat sin advanced brain usa Ollama (puede fallar si Ollama no está)."""
    payload = {
        "message": "Responde en una sola palabra: OK",
        "use_ollama": True,
        "use_advanced_brain": False,
    }
    r = requests.post(f"{BASE_URL}/chat", json=payload, timeout=TIMEOUT)
    assert r.status_code == 200, f"Chat Ollama: {r.status_code} {r.text}"
    data = r.json()
    assert "response" in data, data
    print("[OK] Chat Ollama: respuesta recibida (status=%s)." % data.get("status", ""))


def run_manual():
    """Ejecutar pruebas manualmente (sin pytest) para diagnóstico."""
    print("Base URL:", BASE_URL)
    try:
        test_health()
    except Exception as e:
        print("[FALLO] Health:", e)
        print("  ¿Está agent-core en marcha? docker compose up -d (o profile extended)")
        return 1
    try:
        test_chat_gemini()
    except Exception as e:
        print("[FALLO] Chat Gemini:", e)
    try:
        test_chat_ollama()
    except Exception as e:
        print("[FALLO] Chat Ollama:", e)
    print("Pruebas manuales terminadas.")
    return 0


if __name__ == "__main__":
    sys.exit(run_manual())
