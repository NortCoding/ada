"""
Small filesystem tools for ADA CLI.

Keep it simple and deterministic:
- list_files(path="."): prints all files under `path`
- count_files(path="."): returns total number of files
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator


def _iter_files(root: str | os.PathLike[str]) -> Iterator[Path]:
    """
    Internal iterator of regular files under `root`.
    Uses `os.walk` for simplicity.
    """
    root_path = Path(root).resolve()
    skip_dir_names = {".git", "__pycache__", "node_modules", ".venv", "dist"}

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Avoid descending into noisy directories.
        dirnames[:] = [d for d in dirnames if d not in skip_dir_names and not d.startswith(".")]

        for name in filenames:
            p = Path(dirpath) / name
            if p.is_file():
                yield p


def list_files(path: str | os.PathLike[str] = ".") -> None:
    """
    List files under `path` and print them (one per line).
    """
    root_path = Path(path).resolve()
    for p in _iter_files(root_path):
        try:
            rel = p.relative_to(root_path).as_posix()
        except ValueError:
            rel = p.as_posix()
        print(rel)


def count_files(path: str | os.PathLike[str] = ".") -> int:
    """
    Return the total number of files under `path`.
    """
    return sum(1 for _ in _iter_files(path))


def write_file(path: str, content: str) -> dict:
    """
    Write/overwrite a file (creates directories if needed).

    Uses BASE_PATH = os.getcwd() to avoid ambiguous relative paths.
    Returns:
      - path (as provided)
      - full_path (absolute)
      - size_bytes
      - success_message
    """
    base_path = os.getcwd()
    # Join to keep behavior deterministic and avoid host-relative confusion.
    full_path = os.path.join(base_path, path)

    parent_dir = os.path.dirname(full_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

    size_bytes = os.path.getsize(full_path)
    return {
        "path": path,
        "full_path": full_path,
        "size_bytes": size_bytes,
        "success_message": f"Written {path} ({size_bytes} bytes)",
    }


def read_file(path: str) -> str:
    """
    Read a file as string (relative to BASE_PATH=os.getcwd()).

    If file does not exist, returns "".
    """
    base_path = os.getcwd()
    full_path = os.path.join(base_path, path)

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        return ""

    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()

