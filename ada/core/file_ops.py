"""
Minimal file operations for ADA CLI.

This is intentionally small: create files and perform a tiny, deterministic "fix".
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import datetime


@dataclass(frozen=True)
class CreateFileResult:
    path: str
    created: bool


def create_file(path: str, content: str | None = None) -> CreateFileResult:
    p = Path(path)
    if content is None:
        content = f"Created by ADA CLI at {datetime.datetime.utcnow().isoformat()}Z\n"

    # Ensure parent folder exists.
    if p.parent != Path("."):
        p.parent.mkdir(parents=True, exist_ok=True)

    if p.exists():
        return CreateFileResult(path=p.as_posix(), created=False)

    p.write_text(content, encoding="utf-8")
    return CreateFileResult(path=p.as_posix(), created=True)


def fix_error(error_path: str = "error.txt") -> str:
    """
    Deterministic example "fix":
    - Ensure `error.txt` exists with a line containing `ERROR:`
    - Replace the first occurrence of `ERROR:` with `FIXED:`
    """
    p = Path(error_path)
    if not p.exists():
        p.write_text("ERROR: example\n", encoding="utf-8")

    text = p.read_text(encoding="utf-8")
    if "ERROR:" in text:
        new_text = text.replace("ERROR:", "FIXED:", 1)
    else:
        new_text = "FIXED: example\n" + text

    p.write_text(new_text, encoding="utf-8")
    return p.as_posix()

