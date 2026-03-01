#!/usr/bin/env bash
# Exporta o importa la memoria de ADA (memory-db) desde/hacia archivos JSON.
# Uso:
#   ./scripts/memory_export_import.sh export   [directorio]   → exporta a directorio (default: memory_backup)
#   ./scripts/memory_export_import.sh import   <archivo.json> → importa desde archivo (restaura memoria)
# Requiere: memory-db en marcha (docker compose --profile extended). MEMORY_URL por defecto: http://localhost:3005

set -e
cd "$(dirname "$0")/.."
MEMORY_URL="${MEMORY_URL:-http://localhost:3005}"
BACKUP_DIR="${1:-memory_backup}"

export_memory() {
  local dir="$1"
  echo "Exportando memoria desde $MEMORY_URL a $dir ..."
  mkdir -p "$dir"
  local file="$dir/memory_export_$(date +%Y%m%d_%H%M%S).json"
  if ! curl -s -f "$MEMORY_URL/export" -o "$file"; then
    echo "Error: no se pudo conectar a memory-db en $MEMORY_URL. ¿Está levantado? (docker compose --profile extended up -d)"
    exit 1
  fi
  echo "[OK] Exportado en $file"
  cp "$file" "$dir/memory_export_latest.json"
  echo "[OK] Copia como $dir/memory_export_latest.json"
}

import_memory() {
  local file="$1"
  if [ -z "$file" ] || [ ! -f "$file" ]; then
    echo "Uso: $0 import <archivo.json>"
    exit 1
  fi
  echo "Importando memoria desde $file a $MEMORY_URL ..."
  python3 "$(dirname "$0")/memory_import.py" "$MEMORY_URL" "$file"
}

case "${1:-}" in
  export)
    export_memory "$BACKUP_DIR"
    ;;
  import)
    import_memory "$2"
    ;;
  *)
    echo "Uso: $0 export [directorio]  |  $0 import <archivo.json>"
    echo "  export: vuelca la memoria de memory-db a JSON (default: memory_backup/)."
    echo "  import: restaura la memoria desde un JSON exportado."
    exit 1
    ;;
esac
