"""
A.D.A — Policy Engine (F2)
Responde: ¿aprobado según políticas actuales?
Reglas en PostgreSQL (ada_policies). Soporta modo "feedback supervisado" con condiciones ROI/riesgo.
"""
import os
from contextlib import contextmanager
from typing import Any, Optional

import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="A.D.A Policy Engine", version="0.1.0")

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


class PolicyRequest(BaseModel):
    service_name: str
    action_type: str
    payload: dict
    simulation: Optional[dict] = None  # ROI, risk, impact_financial, infra_cost para reglas condicionadas


def _eval_safe_metrics_rule(config: dict, simulation: dict) -> bool:
    """True si simulation cumple roi_min y risk_max del config (aprobación simulada segura)."""
    if not config or not simulation:
        return False
    roi_min = config.get("roi_min")
    risk_max = config.get("risk_max")
    if roi_min is None and risk_max is None:
        return False
    
    # Normalizar a minúsculas
    roi = simulation.get("roi") or simulation.get("ROI")
    risk = simulation.get("risk") or simulation.get("RISK")
    
    if roi is not None and roi_min is not None and float(roi) < float(roi_min):
        return False
    if risk is not None and risk_max is not None and float(risk) > float(risk_max):
        return False
    return True


@app.get("/health")
def health():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"DB unreachable: {e}")
    return {"status": "ok", "service": "policy-engine"}


@app.post("/approve")
def check_policy(req: PolicyRequest):
    """
    Consulta reglas activas. Si hay regla con condition (roi_min, risk_max) y simulation cumple,
    aprueba como "aprobación simulada" (modo feedback supervisado). Si no, aprueba si existe
    regla activa para action_type (o action_type = '*').
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT action_type, config FROM ada_policies.rules
                    WHERE active = true
                    AND (action_type = %s OR action_type = '*')
                    """,
                    (req.action_type,),
                )
                rows = cur.fetchall()
        simulation = req.simulation or {}
        for action_type, config in rows:
            config = config or {}
            is_sim = config.get("simulated_approval")
            eval_result = _eval_safe_metrics_rule(config, simulation)
            if is_sim and eval_result:
                return {
                    "approved": True,
                    "reason": "Aprobación simulada (modo feedback supervisado): ROI y riesgo en rango seguro.",
                    "simulated_approval": True,
                    "rule_notes": config.get("notes", ""),
                }
        approved = len(rows) > 0
        return {
            "approved": approved,
            "reason": "Regla activa encontrada" if approved else "No hay regla activa",
            "simulated_approval": True,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
