"""
Task planner for ADA CLI.

For now:
- tries LLM via Ollama if available
- falls back to deterministic suggestions when LLM is not reachable

It must NOT execute tasks automatically.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any, Dict, List


def _llm_suggest_tasks(roadmap_text: str, current_state: str) -> List[str] | None:
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    base_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")

    prompt = (
        "You are ADA task planner.\n"
        "Return exactly 3 to 5 tasks aligned with current phase.\n"
        "Tasks must be simple, executable, and focused on real CLI tool improvements.\n"
        "Output format: JSON with key `tasks` as an array of strings.\n\n"
        f"ROADMAP:\n{roadmap_text}\n\n"
        f"CURRENT_STATE:\n{current_state}\n"
    )

    payload: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}

    try:
        req = urllib.request.Request(
            url=f"{base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        response_text = data.get("response") or ""

        m = re.search(r"\{.*\}", response_text, flags=re.DOTALL)
        if not m:
            return None
        obj = json.loads(m.group(0))
        tasks = obj.get("tasks")
        if isinstance(tasks, list) and all(isinstance(t, str) for t in tasks):
            cleaned = [t.strip() for t in tasks if t.strip()]
            if 3 <= len(cleaned) <= 5:
                return cleaned
        return None
    except Exception:
        return None


def _fallback_tasks(current_state: str) -> List[str]:
    # Deterministic "good next steps" for our current FASE 1->2 transition.
    base = [
        "Implement file read debug loop for `fix error <...>` (already started) and ensure stable diff display.",
        "Add test automation for CLI commands (analyze/list/create/fix/run) so fixes are verifiable.",
        "Create `git_tools.py` (status/diff/add/commit) and add a guarded command like `git status`.",
        "Create `ada/memory/progress.md` logger to record executed/proposed tasks.",
    ]

    # If run commands exist, propose next: `run tests` integration.
    if "run " in current_state or "run_command" in current_state:
        base.insert(1, "Add `run tests` wrapper and ensure timeouts + safe output capture.")

    # Return 3-5 tasks.
    return base[:5]


def suggest_tasks(roadmap_text: str, current_state: str) -> List[str]:
    llm_tasks = _llm_suggest_tasks(roadmap_text, current_state)
    if llm_tasks:
        return llm_tasks
    return _fallback_tasks(current_state)

