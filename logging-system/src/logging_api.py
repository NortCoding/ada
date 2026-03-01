"""
A.D.A — Logging System
Blocking acknowledgement: si este servicio falla, el llamador debe cancelar la acción.
"""
import json
import os
from contextlib import contextmanager
from typing import Optional

import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="A.D.A Logging System", version="0.1.0")

# Config desde entorno (por defecto para Docker Compose)
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "ada_user")
PG_PASSWORD = os.getenv("PG_PASSWORD", "supersecret")
PG_DB = os.getenv("PG_DB", "ada_main")


@contextmanager
def get_conn():
    """Conexión por petición para evitar condiciones de carrera (blocking ack confiable)."""
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


class Event(BaseModel):
    service_name: str
    event_type: str
    payload: dict


@app.get("/health")
def health():
    """Comprobación de que el servicio y la BD están disponibles."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"DB unreachable: {e}")
    return {"status": "ok", "service": "logging-system"}


@app.get("/events")
def get_events(limit: int = 50, event_type: Optional[str] = None, service_name: Optional[str] = None):
    """Lista eventos recientes (para dashboard y auditoría)."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                if event_type or service_name:
                    conditions = []
                    params = []
                    if event_type:
                        conditions.append("event_type = %s")
                        params.append(event_type)
                    if service_name:
                        conditions.append("service_name = %s")
                        params.append(service_name)
                    params.append(min(limit, 200))
                    cur.execute(
                        """
                        SELECT id, service_name, event_type, payload, created_at
                        FROM ada_logs.events
                        WHERE """ + " AND ".join(conditions) + """
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        params,
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, service_name, event_type, payload, created_at
                        FROM ada_logs.events
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (min(limit, 200),),
                    )
                rows = cur.fetchall()
        return {
            "events": [
                {
                    "id": r[0],
                    "service_name": r[1],
                    "event_type": r[2],
                    "payload": r[3],
                    "created_at": str(r[4]),
                }
                for r in rows
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/log")
def log_event(event: Event):
    """
    Registra un evento en ada_logs.events.
    Blocking ack: solo devuelve 200 + event_id tras escribir en PostgreSQL.
    Si falla, el llamador debe abortar/cancelar la acción.
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ada_logs.events (service_name, event_type, payload)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (event.service_name, event.event_type, json.dumps(event.payload)),
                )
                row = cur.fetchone()
                if not row:
                    conn.rollback()
                    raise HTTPException(status_code=500, detail="Insert did not return id")
                event_id = row[0]
            conn.commit()
        return {"status": "ok", "event_id": event_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
