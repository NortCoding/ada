#!/usr/bin/env bash
# Deja Ollama listo para ADA: comprueba que Ollama esté en marcha y descarga el modelo por defecto (local y gratuito).
# Uso: ./scripts/setup_ollama_model.sh
# Ejecutar en el host (Mac/Linux), no dentro de Docker.

set -e
cd "$(dirname "$0")/.."

# Modelo por defecto que usa ADA (local, gratuito)
if [ -f ada_resources.env ]; then
  MODEL=$(grep -E '^OLLAMA_MODEL=' ada_resources.env 2>/dev/null | cut -d= -f2)
fi
if [ -z "$MODEL" ] && [ -f .env ]; then
  MODEL=$(grep -E '^OLLAMA_MODEL=' .env 2>/dev/null | cut -d= -f2)
fi
MODEL="${MODEL:-llama3.2}"

echo "=== Ollama para ADA (local y gratuito) ==="
echo "Modelo a instalar: $MODEL"
echo ""

# Comprobar que Ollama está en marcha
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:11434/api/tags 2>/dev/null | grep -q 200; then
  echo "Ollama no responde en http://localhost:11434"
  echo "Inicia Ollama en esta máquina: ejecuta 'ollama serve' en otra terminal o abre la app Ollama."
  exit 1
fi
echo "[OK] Ollama está en marcha."

# Ver si el modelo ya está
if ollama list 2>/dev/null | grep -qE "^$MODEL\s|$MODEL:"; then
  echo "[OK] El modelo '$MODEL' ya está instalado. Listo para ADA."
  ollama list
  exit 0
fi

# Descargar el modelo
echo "Descargando modelo '$MODEL' (puede tardar varios minutos la primera vez)..."
if ollama pull "$MODEL"; then
  echo ""
  echo "[OK] Modelo '$MODEL' instalado. Ollama queda listo para ADA (uso local y gratuito)."
  ollama list
else
  echo "Error al descargar. Comprueba conexión e intenta de nuevo: ollama pull $MODEL"
  exit 1
fi
