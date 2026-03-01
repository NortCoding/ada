#!/bin/bash
# Pruebas del chat de ADA (sin Telegram: API directa a agent-core).
# Para probar el bot en Telegram: levanta el chat-bridge y escribe a @ADA_SocioBot.
set -e
AGENT_URL="${AGENT_URL:-http://localhost:3001}"
echo "=== Prueba 1: mensaje corto ==="
curl -s -X POST "$AGENT_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Responde en una frase: ¿estás operativo?", "use_ollama": true}' \
  --max-time 90 | python3 -c "
import sys, json
d = json.load(sys.stdin)
r = d.get('response', '')
s = d.get('status', '')
print('Status:', s)
print('Respuesta:', r[:400] + ('...' if len(r) > 400 else ''))
print('OK' if s == 'done' and r else 'FALLO')
sys.exit(0 if s == 'done' and r else 1)
"
echo ""
echo "=== Prueba 2: otro mensaje ==="
curl -s -X POST "$AGENT_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Qué plan tienes para generar ingresos? Responde en dos líneas.", "use_ollama": true}' \
  --max-time 120 | python3 -c "
import sys, json
d = json.load(sys.stdin)
r = d.get('response', '')
s = d.get('status', '')
print('Status:', s)
print('Respuesta:', r[:500] + ('...' if len(r) > 500 else ''))
print('OK' if s == 'done' and r else 'FALLO')
sys.exit(0 if s == 'done' and r else 1)
"
echo ""
echo "Chat API OK. Para probar por Telegram: docker compose --profile extended --profile telegram up -d chat-bridge && escribe a @ADA_SocioBot"
