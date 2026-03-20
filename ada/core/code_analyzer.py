"""
Basic file analyzer for ADA.

Features:
- Scan current directory
- List files
- Print summary:
  - number of files
  - file types
"""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path
from typing import Iterable


def _iter_files(root: Path) -> Iterable[Path]:
    # Keep output manageable by skipping directories that are usually huge/noisy.
    skip_dir_names = {".git", "__pycache__", "node_modules", ".venv", ".venv", "dist"}

    for dirpath, dirnames, filenames in os.walk(root):
        # Modify dirnames in-place to control os.walk recursion.
        dirnames[:] = [d for d in dirnames if d not in skip_dir_names and not d.startswith(".")]

        for name in filenames:
            p = Path(dirpath) / name
            # Only count regular files.
            if p.is_file():
                yield p


def analyze_current_directory(root: str | os.PathLike[str] = ".") -> None:
    root_path = Path(root).resolve()
    files = list(_iter_files(root_path))

    # List files (relative to root).
    for p in files:
        try:
            rel = p.relative_to(root_path).as_posix()
        except ValueError:
            rel = str(p)
        print(rel)

    # Summarize file types by extension.
    ext_counter: Counter[str] = Counter()
    for p in files:
        ext = p.suffix.lower() or "<no_ext>"
        ext_counter[ext] += 1

    print("\nSummary:")
    print(f"Number of files: {len(files)}")
    print("File types:")
    for ext, count in sorted(ext_counter.items(), key=lambda x: (-x[1], x[0])):
        print(f"- {ext}: {count}")


def summarize_current_directory(root: str | os.PathLike[str] = ".") -> dict:
    """
    Returns a machine-readable summary for the CLI cycle test.
    """
    root_path = Path(root).resolve()
    files = list(_iter_files(root_path))

    ext_counter: Counter[str] = Counter()
    for p in files:
        ext = p.suffix.lower() or "<no_ext>"
        ext_counter[ext] += 1

    return {
        "root": str(root_path),
        "number_of_files": len(files),
        "file_types": {ext: count for ext, count in ext_counter.most_common()},
    }


def analyze_project(path: str | os.PathLike[str] = ".") -> None:
    """
    Project analysis for ADA CLI.

    Prints:
    - total files
    - file types (extensions)
    """
    from ada.tools.file_tools import _iter_files, count_files

    total = count_files(path)

    types: set[str] = set()
    for p in _iter_files(path):
        ext = p.suffix.lower() or "<no_ext>"
        types.add(ext)

    types_sorted = sorted(types)
    types_str = ", ".join(types_sorted)

    print("Project Analysis:")
    print(f"- Total files: {total}")
    print(f"- Types: {types_str}")

