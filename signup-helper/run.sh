#!/usr/bin/env bash
# Ejecuta el registro asistido con el venv (Playwright instalado). Uso: ./run.sh gumroad
cd "$(dirname "$0")/.."
SCRIPT_DIR="$(dirname "$0")"
if [ -d "$SCRIPT_DIR/venv" ]; then
  "$SCRIPT_DIR/venv/bin/python3" "$SCRIPT_DIR/register.py" "$@"
else
  python3 "$SCRIPT_DIR/register.py" "$@"
fi
