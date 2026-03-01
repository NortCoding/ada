#!/usr/bin/env python3
"""
Pregunta a ADA si tiene claras las nuevas reglas (visión emprendimiento + confidencialidad).
Uso: tener agent-core (y Ollama o cerebro avanzado) en marcha, luego:
  python scripts/ask_ada_rules.py
Alternativa: abre la web-admin (http://localhost:8080), ve al chat y pega la pregunta que imprime este script.
"""
import json
import os
import sys
import urllib.request
import urllib.error

AGENT_URL = os.getenv("AGENT_URL", "http://localhost:3001")
QUESTION = (
    "¿Tienes claras todas las nuevas reglas? Me refiero a: "
    "la visión del proyecto como emprendimiento (pequeña empresa, hoy tú y el asistente guiándote, "
    "mañana más asistentes que tú diriges como vicepresidente, pioneros en mejorar las IAs), "
    "y la confidencialidad (proyecto privado, no revelar estructura del equipo ni que somos solo el socio y el asistente, "
    "responder de forma genérica a terceros). Confírmame si todo eso está claro para ti."
)

def main():
    url = f"{AGENT_URL.rstrip('/')}/chat"
    payload = {
        "message": QUESTION,
        "use_ollama": True,
        "use_advanced_brain": True,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    print("Preguntando a ADA... (puede tardar 2–3 min si usa cerebro avanzado u Ollama en frío)\n")
    try:
        with urllib.request.urlopen(req, timeout=220) as r:
            data = json.loads(r.read().decode())
        resp = data.get("response", "")
        brain = data.get("brain", "ollama")
        print(f"[ADA] ({brain}):\n{resp}")
        return 0
    except urllib.error.URLError as e:
        if "timed out" in str(e).lower():
            print("Timeout. Comprueba que Ollama (o el cerebro avanzado) esté en marcha.")
        else:
            print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
