"""
A.D.A — Simulation Engine (F3)
Calcula ROI, riesgo, impacto financiero y costo de infra antes de aprobar.
"""
import random

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="A.D.A Simulation Engine", version="0.1.0")


class SimulationRequest(BaseModel):
    proposal: dict


@app.get("/health")
def health():
    return {"status": "ok", "service": "simulation-engine"}


@app.post("/simulate")
def simulate(req: SimulationRequest):
    """
    Simulación de prueba mejorada: 
    - Acciones de aprendizaje/técnicas locales -> bajo riesgo, alto ROI.
    - Acciones desconocidas -> random.
    """
    task_name = req.proposal.get("task_name", "").lower()
    desc = str(req.proposal.get("details", {}).get("description", "")).lower()
    full_text = task_name + " " + desc
    
    learning_keywords = ["aprendizaje", "learn", "insight", "scan", "analiza", "memoria", "infra", "network", "red"]
    
    is_low_risk = any(k in full_text for k in learning_keywords)
    
    if is_low_risk:
        return {
            "roi": round(random.uniform(0.6, 0.9), 2),
            "risk": round(random.uniform(0.05, 0.15), 2),
            "impact_financial": 0.0,
            "infra_cost": 0.0,
        }
    
    return {
        "roi": round(random.uniform(0.1, 0.5), 2),
        "risk": round(random.uniform(0.3, 0.8), 2),
        "impact_financial": round(random.uniform(1000, 5000), 2),
        "infra_cost": round(random.uniform(50, 500), 2),
    }
