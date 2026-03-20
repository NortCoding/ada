"""
Roadmap engine for ADA CLI.

No complicated parsing:
- load_roadmap() returns the roadmap text
- get_current_phase() extracts current phase using simple regex
- get_current_goals() returns current objectives section as raw lines
"""

from __future__ import annotations

import os
import re
from typing import List


def load_roadmap() -> str:
    """
    Read `ada/ROADMAP.md` from BASE_PATH=os.getcwd().
    """
    base_path = os.getcwd()
    roadmap_path = os.path.join(base_path, "ada", "ROADMAP.md")

    try:
        with open(roadmap_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def get_current_phase(roadmap_text: str) -> str:
    """
    Extract a phase like "FASE 1" using a simple regex.
    """
    text = roadmap_text or ""
    m = re.search(r"FASE\s*([0-9]+)", text, flags=re.IGNORECASE)
    if not m:
        return "FASE desconocida"
    return f"FASE {m.group(1)}"


def get_current_goals(roadmap_text: str) -> List[str]:
    """
    Return raw objective lines under "OBJETIVOS ACTUALES".
    """
    text = roadmap_text or ""
    lines = text.splitlines()

    start = None
    end = None
    for i, line in enumerate(lines):
        if "OBJETIVOS ACTUALES" in line:
            start = i
        if start is not None and i > start and "OBJETIVOS FUTUROS" in line:
            end = i
            break

    if start is None:
        return []
    if end is None:
        end = len(lines)

    goals: List[str] = []
    for line in lines[start:end]:
        stripped = line.strip()
        # Skip horizontal rules or empty separators.
        if not stripped or set(stripped) == {"-"}:
            continue
        # Keep bullet-like and numbered lines.
        if stripped.startswith(tuple("1234567890")) and "." in stripped:
            goals.append(stripped)
        elif stripped.startswith("-") and stripped:
            goals.append(stripped)

    return goals

