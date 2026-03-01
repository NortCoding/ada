#!/usr/bin/env bash
# Aplica los recursos de hardware que ADA solicitó (desde memory).
# Uso: ./scripts/apply_ada_resources.sh
# Luego: docker compose --env-file ada_resources.env up -d (o incluir ada_resources.env en el proyecto)

set -e
cd "$(dirname "$0")/.."
API="${API:-http://localhost:8080}"

echo "Obteniendo recursos solicitados por ADA desde $API..."
resp=$(curl -s "${API}/api/autonomous/resources" || true)
if ! echo "$resp" | grep -q '"requested"'; then
  echo "No se pudo conectar a la API o no hay recursos solicitados. Crea ada_resources.env manualmente si hace falta."
  exit 1
fi

# Extraer requested (valores entre comillas); escribir ada_resources.env
# Formato JSON: "requested": { "OLLAMA_NUM_THREADS": 8, ... }
out="ada_resources.env"
echo "# Generado por apply_ada_resources.sh - recursos que ADA pidió para crecer" > "$out"
echo "$resp" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    r = d.get('requested') or {}
    for k, v in r.items():
        if k == 'reason' or v is None: continue
        print(f'{k}={v}', file=sys.stdout)
except Exception as e:
    sys.exit(1)
" >> "$out" 2>/dev/null || true

if [ ! -s "$out" ] || [ "$(wc -l < "$out")" -le 1 ]; then
  echo "# Sin recursos nuevos; valores por defecto (ajustados para estabilidad)" >> "$out"
  echo "OLLAMA_NUM_THREADS=6" >> "$out"
  echo "OLLAMA_NUM_CTX=4096" >> "$out"
  echo "OLLAMA_NUM_PREDICT=768" >> "$out"
  echo "OLLAMA_CHAT_TIMEOUT=120" >> "$out"
  echo "OLLAMA_DEFAULT_KEEPALIVE=300" >> "$out"
fi

echo "Escrito $out"
echo ""
echo "Para aplicar (Ollama y agent-core usarán estos valores al reiniciar):"
echo "  docker compose --env-file ada_resources.env up -d"
echo "O añade en tu .env las variables que quieras y reinicia: docker compose up -d"
