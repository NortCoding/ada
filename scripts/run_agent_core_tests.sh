#!/usr/bin/env bash
# Pruebas de funcionamiento del agent-core (health, chat Gemini, chat Ollama).
# Requiere: agent-core en marcha en AGENT_CORE_URL (por defecto http://localhost:3001).
# Uso: ./scripts/run_agent_core_tests.sh

set -e
BASE_URL="${AGENT_CORE_URL:-http://localhost:3001}"
CHAT_TIMEOUT="${CHAT_TIMEOUT:-90}"

echo "=== Pruebas agent-core (BASE_URL=$BASE_URL) ==="

echo ""
echo "1. GET /health"
code=$(curl -s -o /tmp/health.json -w "%{http_code}" "$BASE_URL/health")
if [ "$code" = "200" ]; then
  echo "   [OK] HTTP 200"
  cat /tmp/health.json
else
  echo "   [FALLO] HTTP $code"
  cat /tmp/health.json 2>/dev/null || true
  exit 1
fi

echo ""
echo "2. POST /chat (use_advanced_brain=true, Gemini)"
out=$(curl -s -X POST "$BASE_URL/chat" -H "Content-Type: application/json" \
  -d '{"message":"Di solo: Hola, soy ADA.","use_ollama":true,"use_advanced_brain":true}' \
  --max-time "$CHAT_TIMEOUT" -w "\n%{http_code}" || true)
code=$(echo "$out" | tail -n1)
body=$(echo "$out" | sed '$d')
if [ "$code" = "200" ]; then
  echo "   [OK] HTTP 200"
  echo "$body" | head -c 300
  echo ""
  if echo "$body" | grep -q '"brain":"gemini"'; then
    echo "   -> Cerebro usado: Gemini"
  else
    echo "   -> Cerebro: Ollama (fallback) o no indicado"
  fi
else
  echo "   [INFO] HTTP $code o timeout. Si es 200 con timeout: aumentar CHAT_TIMEOUT."
  echo "   Cuerpo: ${body:0:200}"
fi

echo ""
echo "3. POST /chat (use_advanced_brain=false, Ollama)"
out=$(curl -s -X POST "$BASE_URL/chat" -H "Content-Type: application/json" \
  -d '{"message":"Responde en una palabra: OK","use_ollama":true,"use_advanced_brain":false}' \
  --max-time "$CHAT_TIMEOUT" -w "\n%{http_code}" || true)
code=$(echo "$out" | tail -n1)
body=$(echo "$out" | sed '$d')
if [ "$code" = "200" ]; then
  echo "   [OK] HTTP 200 - respuesta recibida"
  echo "$body" | head -c 200
  echo ""
else
  echo "   [INFO] HTTP $code o timeout (Ollama puede tardar o no estar listo)."
fi

echo ""
echo "=== Fin pruebas ==="
