"""
A.D.A — Memory DB (F4–F5)
Estado, contexto e historial en ada_memory.context (key / value JSONB).
"""
import json
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional

import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="A.D.A Memory DB", version="0.1.0")

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "ada_user")
PG_PASSWORD = os.getenv("PG_PASSWORD", "supersecret")
PG_DB = os.getenv("PG_DB", "ada_main")


@contextmanager
def get_conn():
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        dbname=PG_DB,
    )
    try:
        yield conn
    finally:
        conn.close()


class MemoryRecord(BaseModel):
    key: str
    value: Optional[Any] = None  # None para "borrar" la key (limpiar plan, etc.)


@app.get("/health")
def health():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"DB unreachable: {e}")
    return {"status": "ok", "service": "memory-db"}


@app.post("/set")
def set_memory(record: MemoryRecord):
    """Upsert: key → value (JSONB)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            try:
                # value None → jsonb NULL en DB (para limpiar plan, oferta, etc.)
                cur.execute(
                    """
                    INSERT INTO ada_memory.context (key, value)
                    VALUES (%s, %s::jsonb)
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
                    """,
                    (record.key, json.dumps(record.value) if record.value is not None else None),
                )
                conn.commit()
                return {"status": "ok"}
            except Exception as e:
                conn.rollback()
                raise HTTPException(status_code=500, detail=str(e))


@app.get("/get/{key}")
def get_memory(key: str):
    """Devuelve value para la key o null si no existe."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM ada_memory.context WHERE key = %s", (key,))
            row = cur.fetchone()
    if row is None:
        return {"value": None}
    val = row[0]
    return {"value": val if isinstance(val, dict) else val}


@app.get("/get_many")
def get_many(keys: str = ""):
    """Devuelve varias claves en una sola petición. keys=first_plan,weekly_plan,requested_hardware_resources."""
    if not keys.strip():
        return {}
    key_list = [k.strip() for k in keys.split(",") if k.strip()]
    if not key_list:
        return {}
    with get_conn() as conn:
        with conn.cursor() as cur:
            placeholders = ",".join("%s" for _ in key_list)
            cur.execute(
                f"SELECT key, value FROM ada_memory.context WHERE key IN ({placeholders})",
                key_list,
            )
            rows = cur.fetchall()
    return {r[0]: r[1] if isinstance(r[1], dict) else r[1] for r in rows}


@app.get("/keys")
def list_keys(prefix: str = ""):
    """Lista keys (opcional filtro por prefix) para web-admin."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            if prefix:
                cur.execute(
                    "SELECT key FROM ada_memory.context WHERE key LIKE %s ORDER BY key",
                    (prefix + "%",),
                )
            else:
                cur.execute("SELECT key FROM ada_memory.context ORDER BY key")
            rows = cur.fetchall()
    return {"keys": [r[0] for r in rows]}


@app.get("/export")
def export_all():
    """Exporta todas las claves y valores como un único JSON. Útil para backup o scripts de export a archivos."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT key, value, updated_at FROM ada_memory.context ORDER BY key")
            rows = cur.fetchall()
    out = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "entries": [{"key": r[0], "value": r[1], "updated_at": r[2].isoformat() if hasattr(r[2], "isoformat") else str(r[2])} for r in rows],
    }
    return out
