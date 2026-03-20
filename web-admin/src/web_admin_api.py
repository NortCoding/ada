"""
A.D.A — Web Admin (UI + API proxy)
- Sirve el frontend estático (React build) desde /frontend/dist
- Proxya llamadas /api/* hacia agent-core y memory_service
- Expone endpoints de FS para explorador de archivos (solo lectura; escritura opcional si ENABLE_AGENT_FS)
"""

import os
import hashlib
import shlex
import subprocess
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="A.D.A Web Admin", version="0.2.0")

AGENT_URL = (os.getenv("AGENT_URL") or "http://agent-core:3001").rstrip("/")
MEMORY_URL = (os.getenv("MEMORY_URL") or "http://memory_service:3005").rstrip("/")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30"))
CHAT_REQUEST_TIMEOUT = float(os.getenv("CHAT_REQUEST_TIMEOUT", "180"))

FILES_ROOT = os.path.abspath((os.getenv("ADA_FILES_ROOT") or "/dockers").strip() or "/dockers")
ENABLE_AGENT_FS = (os.getenv("ENABLE_AGENT_FS") or "0").lower() in ("1", "true", "yes")
UI_RUN_ALLOWLIST = [
    s.strip() for s in (os.getenv("ADA_UI_RUN_ALLOWLIST") or "ls,python3,pytest").split(",") if s.strip()
]
UI_RUN_TIMEOUT = int(os.getenv("ADA_UI_RUN_TIMEOUT", "60"))

FRONTEND_DIST = "/frontend/dist"


def _frontend_exists() -> bool:
    try:
        return os.path.isfile(os.path.join(FRONTEND_DIST, "index.html"))
    except Exception:
        return False


# Static assets (React build)
if os.path.isdir(os.path.join(FRONTEND_DIST, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")


@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.now(timezone.utc).isoformat()}


@app.get("/")
async def index():
    """Serve SPA index if available; otherwise show API status."""
    if _frontend_exists():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
    return {"status": "ok", "detail": "Frontend not built/mounted. Expected /frontend/dist/index.html"}


# -----------------------
# API proxy for frontend
# -----------------------

class ChatBody(BaseModel):
    message: str = ""
    use_ollama: bool = True
    history: Optional[list] = None
    image_base64: Optional[str] = None
    agent_type: Optional[str] = None
    execution_mode: bool = False


@app.post("/api/chat")
async def api_chat(body: ChatBody):
    payload = body.model_dump()
    async with httpx.AsyncClient(timeout=CHAT_REQUEST_TIMEOUT) as client:
        r = await client.post(f"{AGENT_URL}/chat", json=payload)
    if r.status_code >= 400:
        return JSONResponse(status_code=502, content={"status": "error", "response": r.text[:1000]})
    data = r.json() if r.text else {}
    if "status" not in data and "response" in data:
        data["status"] = "done"
    return data


@app.get("/api/agent/health")
async def api_agent_health():
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{AGENT_URL}/health")
    if r.status_code >= 400:
        raise HTTPException(status_code=503, detail="agent-core down")
    return {"status": "ok"}


@app.get("/api/agent/status")
async def api_agent_status():
    """ADA v1: estado mínimo sin depender de endpoints autónomos legacy."""
    return {"status": "ok", "ada_v1": True, "model_hint": "ollama_local"}


@app.get("/api/autonomous/plan")
async def api_autonomous_plan():
    # Legacy desactivado en ADA v1; no exponer planes de negocio/autonomía por defecto.
    return {"status": "disabled_v1", "plan": None, "step_statuses": []}


@app.post("/api/execute_plan")
async def api_execute_plan(body: dict):
    plan = body.get("plan") or body.get("pending_plan")
    if not plan:
        raise HTTPException(status_code=400, detail="Missing 'plan'")
    async with httpx.AsyncClient(timeout=CHAT_REQUEST_TIMEOUT) as client:
        r = await client.post(f"{AGENT_URL}/execute_plan", json={"plan": plan})
    if r.status_code >= 400:
        return {"status": "error", "detail": r.text[:1000], "results": []}
    return r.json()


@app.get("/api/system/monitor")
async def api_system_monitor():
    return {"status": "disabled_v1", "agents": []}


@app.get("/api/agent_market/proposals")
async def api_agent_market_proposals(status: Optional[str] = None):
    return {"status": "disabled_v1", "proposals": []}


@app.post("/api/agent_market/propose")
async def api_agent_market_propose(body: dict):
    raise HTTPException(status_code=410, detail="Agent market desactivado en ADA v1.")


# -----------------------
# File system (Explorer)
# -----------------------

def _safe_join(root: str, rel: str) -> str:
    rel = (rel or ".").strip().lstrip("/")
    if ".." in rel.split("/"):
        raise HTTPException(status_code=400, detail="Invalid path")
    full = os.path.abspath(os.path.join(root, rel)) if rel and rel != "." else os.path.abspath(root)
    root_real = os.path.realpath(root)
    full_real = os.path.realpath(full)
    if full_real != root_real and not full_real.startswith(root_real + os.sep):
        raise HTTPException(status_code=403, detail="Path outside root")
    return full


@app.get("/api/fs/list")
async def api_fs_list(path: str = ""):
    target_dir = _safe_join(FILES_ROOT, path)
    if not os.path.isdir(target_dir):
        raise HTTPException(status_code=404, detail="Not a directory")
    try:
        names = sorted(os.listdir(target_dir))
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e))
    entries = []
    rel = (path or ".").strip().strip("/")
    if rel == ".":
        rel = ""
    for name in names:
        if name.startswith("."):
            continue
        full = os.path.join(target_dir, name)
        is_dir = os.path.isdir(full)
        rel_path = (os.path.join(rel, name).replace("\\", "/") if rel else name)
        entries.append({"name": name, "path": rel_path, "is_dir": is_dir})
    entries.sort(key=lambda e: (not e["is_dir"], e["name"].lower()))
    return {"path": rel or ".", "entries": entries}


@app.get("/api/fs/read")
async def api_fs_read(path: str):
    target = _safe_join(FILES_ROOT, path)
    if not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="Not a file")
    try:
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            return {"path": path, "content": f.read()}
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e))


class FileWriteBody(BaseModel):
    path: str
    content: str = ""


@app.post("/api/fs/write")
async def api_fs_write(body: FileWriteBody, request: Request):
    if not ENABLE_AGENT_FS:
        raise HTTPException(status_code=403, detail="Filesystem write disabled (ENABLE_AGENT_FS=0).")
    target = _safe_join(FILES_ROOT, body.path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    try:
        with open(target, "w", encoding="utf-8") as f:
            f.write(body.content or "")
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok", "path": body.path}


# -----------------------
# Controlled execution for approvals (v2)
# -----------------------

class ApproveExecuteBody(BaseModel):
    action_type: str
    payload: dict = {}


def _sha256_text(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8", errors="replace")).hexdigest()

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_text_file(full_path: str) -> str:
    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def _is_allowed_command(cmd: str) -> bool:
    cmd = (cmd or "").strip()
    if not cmd:
        return False
    head = cmd.split()[0]
    return head in UI_RUN_ALLOWLIST


@app.post("/api/approve/execute")
async def api_approve_execute(body: ApproveExecuteBody):
    """
    Controlled execution endpoint for UI approvals.
    The UI must never execute directly; it must call this endpoint.

    Supported action_type:
    - create_file: { path, content }
    - run_command: { command, cwd? }
    - apply_patch: { path, new_content }
    """
    request_id = str(uuid.uuid4())
    ts = _now_iso()
    action_type = (body.action_type or "").strip().lower()
    payload = body.payload or {}

    if action_type not in ("create_file", "run_command", "apply_patch"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Unsupported action_type",
                "request_id": request_id,
                "ts": ts,
                "action_type": action_type,
                "supported": ["create_file", "run_command", "apply_patch"],
            },
        )

    # 1) CREATE FILE (write through FS root)
    if action_type == "create_file":
        if not ENABLE_AGENT_FS:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Filesystem write disabled",
                    "request_id": request_id,
                    "ts": ts,
                    "action_type": action_type,
                    "hint": "Set ENABLE_AGENT_FS=1 to allow create_file/apply_patch",
                },
            )
        rel_path = (payload.get("path") or "").strip()
        content = payload.get("content") or ""
        if not rel_path:
            raise HTTPException(status_code=400, detail={"error": "Missing path", "request_id": request_id, "ts": ts})

        target = _safe_join(FILES_ROOT, rel_path)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        existed_before = os.path.exists(target)
        before = _read_text_file(target) if existed_before else ""
        sha_before = _sha256_text(before) if existed_before else None
        try:
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
        except OSError as e:
            raise HTTPException(status_code=500, detail={"error": str(e), "request_id": request_id, "ts": ts})

        after = _read_text_file(target)
        size_bytes = os.path.getsize(target) if os.path.exists(target) else 0
        sha = _sha256_text(after)
        preview = after[:300]
        return {
            "status": "ok",
            "request_id": request_id,
            "ts": ts,
            "action_type": "create_file",
            "target": rel_path,
            "success": True,
            "message": "File written",
            "verification": {
                "full_path": target,
                "size_bytes": size_bytes,
                "existed_before": existed_before,
                "sha256_before": sha_before,
                "sha256_after": sha,
                "changed": (sha_before != sha) if existed_before else True,
                "preview": preview,
            },
        }

    # 2) RUN COMMAND (controlled allowlist + timeout)
    if action_type == "run_command":
        command = (payload.get("command") or "").strip()
        cwd_rel = (payload.get("cwd") or "").strip()
        if not command:
            raise HTTPException(status_code=400, detail={"error": "Missing command", "request_id": request_id, "ts": ts})
        if not _is_allowed_command(command):
            head = command.split()[0] if command.split() else ""
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Command not allowed",
                    "request_id": request_id,
                    "ts": ts,
                    "action_type": action_type,
                    "head": head,
                    "allowlist": UI_RUN_ALLOWLIST,
                },
            )

        cwd = _safe_join(FILES_ROOT, cwd_rel) if cwd_rel else FILES_ROOT
        if not os.path.isdir(cwd):
            raise HTTPException(
                status_code=400,
                detail={"error": "cwd is not a directory", "request_id": request_id, "ts": ts, "cwd": cwd},
            )
        started = time.time()
        try:
            args = shlex.split(command)
            proc = subprocess.run(
                args,
                cwd=cwd,
                timeout=UI_RUN_TIMEOUT,
                text=True,
                capture_output=True,
            )
            elapsed_ms = int((time.time() - started) * 1000)
            stdout = (proc.stdout or "")[:8000]
            stderr = (proc.stderr or "")[:8000]
            return {
                "status": "ok",
                "request_id": request_id,
                "ts": ts,
                "action_type": "run_command",
                "target": command,
                "success": proc.returncode == 0,
                "message": "Command executed",
                "verification": {
                    "exit_code": proc.returncode,
                    "duration_ms": elapsed_ms,
                    "cwd": cwd,
                    "argv": args,
                    "allowlist": UI_RUN_ALLOWLIST,
                    "timeout_s": UI_RUN_TIMEOUT,
                    "stdout_truncated": len(proc.stdout or "") > 8000,
                    "stderr_truncated": len(proc.stderr or "") > 8000,
                },
                "output": {"stdout": stdout, "stderr": stderr},
            }
        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=504,
                detail={"error": "Command timed out", "request_id": request_id, "ts": ts, "timeout_s": UI_RUN_TIMEOUT},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail={"error": str(e), "request_id": request_id, "ts": ts})

    # 3) APPLY PATCH (overwrite with new content; diff should be shown by UI before approval)
    rel_path = (payload.get("path") or "").strip()
    new_content = payload.get("new_content")
    if not rel_path:
        raise HTTPException(status_code=400, detail={"error": "Missing path", "request_id": request_id, "ts": ts})
    if new_content is None:
        raise HTTPException(status_code=400, detail={"error": "Missing new_content", "request_id": request_id, "ts": ts})
    if not ENABLE_AGENT_FS:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Filesystem write disabled",
                "request_id": request_id,
                "ts": ts,
                "action_type": action_type,
                "hint": "Set ENABLE_AGENT_FS=1 to allow create_file/apply_patch",
            },
        )

    target = _safe_join(FILES_ROOT, rel_path)
    existed_before = os.path.exists(target)
    before = _read_text_file(target)
    sha_before = _sha256_text(before)
    size_before = len((before or "").encode("utf-8", errors="replace"))

    os.makedirs(os.path.dirname(target), exist_ok=True)
    try:
        with open(target, "w", encoding="utf-8") as f:
            f.write(new_content or "")
    except OSError as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "request_id": request_id, "ts": ts})

    after = _read_text_file(target)
    sha_after = _sha256_text(after)
    size_bytes = os.path.getsize(target) if os.path.exists(target) else 0

    return {
        "status": "ok",
        "request_id": request_id,
        "ts": ts,
        "action_type": "apply_patch",
        "target": rel_path,
        "success": True,
        "message": "Patch applied (overwrite)",
        "verification": {
            "full_path": target,
            "size_bytes": size_bytes,
            "size_bytes_before": size_before,
            "existed_before": existed_before,
            "sha256_before": sha_before,
            "sha256_after": sha_after,
            "changed": sha_before != sha_after,
        },
    }


@app.get("/{path:path}")
async def spa_fallback(path: str):
    """SPA fallback: return index.html for non-API routes. Must be registered LAST."""
    if path.startswith("api/") or path in ("health",):
        raise HTTPException(status_code=404, detail="Not found")
    if _frontend_exists():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
    raise HTTPException(status_code=404, detail="Frontend not available")
