#!/usr/bin/env bash
# ADA auto-orchestrator loop every 30 minutes:
# 1) advance next autonomous step
# 2) trigger self_improve
#
# Run:
#   chmod +x scripts/auto-orchestrator.sh
#   ./scripts/auto-orchestrator.sh
#
# Optional env:
#   AGENT_URL=http://localhost:3001 INTERVAL_SECONDS=1800 ./scripts/auto-orchestrator.sh

set -euo pipefail
cd "$(dirname "$0")/.."

AGENT_URL="${AGENT_URL:-http://localhost:3001}"
INTERVAL_SECONDS="${INTERVAL_SECONDS:-1800}"

command -v curl >/dev/null 2>&1 || { echo "❌ curl is required"; exit 1; }

echo "🤖 ADA auto-orchestrator started"
echo "AGENT_URL=${AGENT_URL}"
echo "INTERVAL_SECONDS=${INTERVAL_SECONDS}"

while true; do
  echo "----------------------------------------"
  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Step 1: POST /autonomous/advance_next_step"
  curl -fsS -X POST "${AGENT_URL}/autonomous/advance_next_step" | tee /tmp/ada_advance_next_step.json

  next_step_index="$(python3 - <<'PY'
import json
from pathlib import Path
p = Path("/tmp/ada_advance_next_step.json")
if not p.exists():
    print("")
    raise SystemExit
try:
    data = json.loads(p.read_text())
except Exception:
    print("")
    raise SystemExit
idx = data.get("next_step_index")
print("" if idx is None else idx)
PY
)"

  if [ -n "${next_step_index}" ]; then
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Step 1b: POST /autonomous/execute_step?step_index=${next_step_index}"
    curl -fsS -X POST "${AGENT_URL}/autonomous/execute_step?step_index=${next_step_index}" | tee /tmp/ada_execute_step.json
  else
    echo "ℹ️ No executable next_step_index returned"
  fi

  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Step 2: GET /self_improve?trigger=cron_30m"
  curl -fsS "${AGENT_URL}/self_improve?trigger=cron_30m" | tee /tmp/ada_self_improve_cron.json

  echo "⏱ Sleeping ${INTERVAL_SECONDS}s..."
  sleep "${INTERVAL_SECONDS}"
done
