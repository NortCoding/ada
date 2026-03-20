"""
Progress logger for ADA CLI.

It appends events to `ada/memory/progress.md`.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict


def _progress_path() -> str:
    base_path = os.getcwd()
    return os.path.join(base_path, "ada", "memory", "progress.md")


def log_progress(task: str, result: str) -> Dict[str, Any]:
    """
    Append a progress record to `ada/memory/progress.md`.
    """
    path = _progress_path()
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    now = datetime.utcnow().isoformat() + "Z"
    entry = f"- [{now}] {task}\n  - result: {result}\n"

    # Ensure file exists.
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("# ADA PROGRESS LOG\n\n")

    with open(path, "a", encoding="utf-8") as f:
        f.write(entry)

    return {"path": path, "task": task, "result": result}

