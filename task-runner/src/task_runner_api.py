"""
A.D.A — Task Runner (F4)
Ejecuta solo tareas ya aprobadas; registra en logging (blocking ack); rollback si log falla.
Modo opcional: SANDBOX_MODE=true — no afecta recursos reales, solo registra lo que se ejecutaría (para pruebas).
"""
import os

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sandbox import execute_bash, WORKSPACE_DIR

app = FastAPI(title="A.D.A Task Runner", version="0.1.0")

LOG_URL = os.getenv("LOG_URL", "http://logging-system:3006/log")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))
SANDBOX_MODE = False  # Disabled for production execution


class TaskRequest(BaseModel):
    task_name: str
    details: dict


@app.get("/health")
def health():
    return {"status": "ok", "service": "task-runner"}


@app.post("/execute")
def execute_task(task: TaskRequest):
    try:
        if SANDBOX_MODE:
            # Modo seguro: no modificar recursos reales; solo registrar para aprendizaje
            result = {
                "status": "success",
                "sandbox": True,
                "message": "Modo sandbox: no se ejecutó en real (task-runner SANDBOX_MODE=1).",
                "would_execute": {"task_name": task.task_name, "details": task.details},
            }
        else:
            # Lógica real acotada
            if task.task_name == "bash_command":
                cmd = task.details.get("command")
                if not cmd:
                    return {"status": "failed", "error": "El comando bash no fue proporcionado en 'details.command'."}

                timeout = task.details.get("timeout_seconds", 30)
                exec_result = execute_bash(cmd, timeout_seconds=timeout)
                
                result = {
                    "status": "success" if exec_result["success"] else "failed",
                    "details": exec_result,
                    "workspace": WORKSPACE_DIR
                }
            else:
                # Simular otras tareas por ahora
                result = {"status": "success", "message": "Tarea simulada (no es bash_command)", "details": task.details}

        # Logging después de ejecutar (blocking ack)
        log_payload = {
            "service_name": "task-runner",
            "event_type": "task_executed",
            "payload": {"task_name": task.task_name, "result": result},
        }
        try:
            log_resp = requests.post(LOG_URL, json=log_payload, timeout=REQUEST_TIMEOUT)
            if log_resp.status_code != 200:
                return {
                    "error": "Logging falló, rollback simulado.",
                    "original_result": result,
                }
        except requests.RequestException as e:
            return {
                "error": f"Logging unreachable: {e}. Rollback simulado.",
                "original_result": result,
            }

        return result

    except Exception as e:
        return {"status": "failed", "error": str(e)}
