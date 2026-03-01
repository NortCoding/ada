"""
A.D.A — Financial Ledger (F4–F5)
Registra transacciones en ada_finance.transactions. Logging blocking ack: si log falla, no se confirma.
"""
import json
import os
from contextlib import contextmanager
from typing import Any

import psycopg2
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="A.D.A Financial Ledger", version="0.1.0")

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "ada_user")
PG_PASSWORD = os.getenv("PG_PASSWORD", "supersecret")
PG_DB = os.getenv("PG_DB", "ada_main")
LOG_URL = os.getenv("LOG_URL", "http://logging-system:3006/log")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))


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


class Transaction(BaseModel):
    type: str
    amount: float
    description: str = ""


@app.get("/health")
def health():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"DB unreachable: {e}")
    return {"status": "ok", "service": "financial-ledger"}


def _log_event(payload: dict) -> bool:
    try:
        r = requests.post(LOG_URL, json=payload, timeout=REQUEST_TIMEOUT)
        return r.status_code == 200
    except requests.RequestException:
        return False


@app.post("/transaction")
def create_transaction(tx: Transaction):
    """
    Inserta transacción. Solo hace commit tras recibir ack de logging (blocking ack).
    """
    with get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO ada_finance.transactions (type, amount, description)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (tx.type, float(tx.amount), tx.description),
            )
            row = cur.fetchone()
            if not row:
                conn.rollback()
                raise HTTPException(status_code=500, detail="Insert did not return id")
            tx_id = row[0]

            # Logging blocking ack: si falla, no confirmamos
            log_payload = {
                "service_name": "financial-ledger",
                "event_type": "transaction_created",
                "payload": {"id": tx_id, "type": tx.type, "amount": tx.amount, "description": tx.description},
            }
            if not _log_event(log_payload):
                conn.rollback()
                return {"error": "Logging falló, transacción revertida."}

            conn.commit()
            return {"id": tx_id, "status": "ok"}
        except HTTPException:
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            cur.close()


@app.get("/transactions")
def list_transactions(limit: int = 100):
    """Lista últimas transacciones (para web-admin y métricas)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, type, amount, description, created_at
                FROM ada_finance.transactions
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
    return {
        "transactions": [
            {"id": r[0], "type": r[1], "amount": float(r[2]), "description": r[3], "created_at": str(r[4])}
            for r in rows
        ]
    }


@app.get("/balance")
def get_balance():
    """Calcula balance total (ingresos - gastos)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT type, SUM(amount) FROM ada_finance.transactions GROUP BY type")
            rows = cur.fetchall()
    
    data = {r[0]: float(r[1]) for r in rows}
    income = data.get("income", 0.0) + data.get("ingreso", 0.0)
    expense = data.get("expense", 0.0) + data.get("gasto", 0.0)
    return {
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "can_use_paid_tools": income > 0
    }
