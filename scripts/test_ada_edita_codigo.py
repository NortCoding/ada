#!/usr/bin/env python3
"""
Prueba: ADA (Ollama vía agent-core) genera código y lo escribe en el workspace.
Requisitos: agent-core en marcha (docker compose up -d agent-core), Ollama en el host.
"""
import os
import re
import sys

try:
    import requests
except ImportError:
    print("Instala requests: pip install requests")
    sys.exit(1)

AGENT_URL = os.getenv("AGENT_URL", "http://localhost:3001")
WORKSPACE_DIR = os.getenv("ADA_WORKSPACE_DIR", os.path.join(os.path.dirname(__file__), "..", "ada_workspace"))


def main():
    print("1. Pidiendo a ADA (Ollama) que genere código Python...")
    r = requests.post(
        f"{AGENT_URL}/chat",
        json={
            "message": "Responde ÚNICAMENTE con un script Python de pocas líneas que imprima 'Hola desde ADA'. Solo código, sin explicación ni markdown.",
            "use_ollama": True,
        },
        timeout=120,
    )
    if r.status_code != 200:
        print(f"Error chat: {r.status_code} {r.text[:300]}")
        return 1
    data = r.json()
    response = (data.get("response") or "").strip()
    if not response:
        print("Respuesta vacía del chat.")
        return 1

    # Extraer código (quitar bloques ```python ... ``` si existen)
    code = response
    if "```" in response:
        match = re.search(r"```(?:python)?\s*\n?(.*?)```", response, re.DOTALL)
        if match:
            code = match.group(1).strip()
    code = code.strip()
    print(f"Código recibido ({len(code)} chars):\n---\n{code[:400]}\n---")

    print("2. Escribiendo archivo vía POST /autonomous/write_file...")
    w = requests.post(
        f"{AGENT_URL}/autonomous/write_file",
        json={"path": "test_ada_hello.py", "content": code},
        timeout=10,
    )
    if w.status_code != 200:
        print(f"Error write_file: {w.status_code} {w.text}")
        return 1
    wr = w.json()
    if wr.get("status") != "ok":
        print("write_file no ok:", wr)
        return 1
    print("Escrito:", wr.get("path"), "->", wr.get("full_path"))

    # Verificar en host (ada_workspace está montado en el host)
    path_host = os.path.join(WORKSPACE_DIR, "test_ada_hello.py")
    if os.path.isfile(path_host):
        print("3. OK: Archivo existe en el host:", path_host)
        with open(path_host, "r", encoding="utf-8") as f:
            content = f.read()
        print("Contenido:\n" + content)
    else:
        print("3. Comprueba en el contenedor que el archivo exista en /workspace/test_ada_hello.py")
        print("   (En el host debería estar en ada_workspace/test_ada_hello.py)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
