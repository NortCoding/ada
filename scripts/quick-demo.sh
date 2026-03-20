#!/usr/bin/env bash
# Quick ADA Demo: Full stack up + Ollama pull + self-improve checks
# Run: chmod +x scripts/quick-demo.sh && ./scripts/quick-demo.sh

set -euo pipefail
cd "$(dirname "$0")/.."

AGENT_URL="${AGENT_URL:-http://localhost:3001}"
OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2}"

echo "🚀 Starting ADA Full Demo..."

# 1) Validate required local tools
command -v docker >/dev/null 2>&1 || { echo "❌ docker is required"; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "❌ curl is required"; exit 1; }

# 2) Setup Ollama model (existing helper) + explicit pull best-effort
echo "1) Ollama setup helper..."
./scripts/setup_ollama_model.sh || echo "⚠️ setup_ollama_model.sh returned non-zero, continuing"

if command -v ollama >/dev/null 2>&1; then
  echo "2) Pulling Ollama model: ${OLLAMA_MODEL}"
  ollama pull "${OLLAMA_MODEL}" || echo "⚠️ ollama pull failed, continuing with existing model"
else
  echo "⚠️ ollama CLI not found in host PATH; assuming model/server already available"
fi

# 3) Bring up full ADA stack needed for autonomy/self-improve
echo "3) Docker Compose up (full autonomy stack)..."
docker compose up -d \
  postgres \
  memory_service \
  agent-core \
  chat_interface \
  logging-system \
  task-runner \
  web-search \
  autonomous-orchestrator

# 4) Wait and show service status
echo "4) Waiting services to warm up..."
sleep 12
docker compose ps

# 5) Smoke tests for endpoints
echo "5) Testing /health..."
curl -fsS "${AGENT_URL}/health" >/dev/null
echo "✅ /health OK"

echo "6) Testing /web_search..."
curl -fsS "${AGENT_URL}/web_search?query=autonomous+llm+self+improve" >/tmp/ada_web_search_response.json
echo "✅ /web_search OK (saved /tmp/ada_web_search_response.json)"

echo "7) Testing /self_improve..."
curl -fsS "${AGENT_URL}/self_improve?trigger=quick_demo" >/tmp/ada_self_improve_response.json
echo "✅ /self_improve OK (saved /tmp/ada_self_improve_response.json)"

# 6) Optional ALMA health check (if already running)
echo "8) Optional ALMA health check..."
if curl -fsS "http://localhost:3011/health" >/dev/null 2>&1; then
  echo "✅ ALMA /health OK"
else
  echo "ℹ️ ALMA not ready/available yet (this can be normal before first successful spawn)"
fi

# 7) Open Chat UI
echo "9) Opening Chat UI: http://localhost:8080"
open http://localhost:8080 || xdg-open http://localhost:8080 || echo "Manually open http://localhost:8080"

echo "✅ ADA full demo ready."
echo "Inspect logs with: docker compose logs -f autonomous-orchestrator agent-core task-runner"
