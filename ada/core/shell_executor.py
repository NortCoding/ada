"""
Minimal shell execution helper for ADA CLI.

We keep it intentionally small and safe:
- capture stdout/stderr
- never throw on non-zero exit code (callers can decide)
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ShellResult:
    command: str
    returncode: int
    stdout: str
    stderr: str


def run_shell_command(command: str, *, cwd: Optional[str] = None) -> ShellResult:
    proc = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    return ShellResult(
        command=command,
        returncode=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
    )

