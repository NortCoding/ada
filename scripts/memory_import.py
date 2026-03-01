#!/usr/bin/env python3
"""Importa memoria desde un JSON exportado por memory-db (GET /export). Uso: memory_import.py <MEMORY_URL> <file.json>"""
import json
import sys
import urllib.request

def main():
    if len(sys.argv) < 3:
        print("Uso: memory_import.py <MEMORY_URL> <file.json>", file=sys.stderr)
        sys.exit(1)
    base_url = sys.argv[1].rstrip("/")
    path = sys.argv[2]
    with open(path) as f:
        data = json.load(f)
    entries = data.get("entries") or []
    count = 0
    for e in entries:
        key = e.get("key")
        value = e.get("value")
        if key is None:
            continue
        if value is None:
            value = {}
        body = json.dumps({"key": key, "value": value}).encode("utf-8")
        req = urllib.request.Request(
            base_url + "/set",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status == 200:
                    count += 1
        except Exception as err:
            print(f"Error escribiendo key={key!r}: {err}", file=sys.stderr)
    print(f"[OK] Importadas {count} claves.")

if __name__ == "__main__":
    main()
