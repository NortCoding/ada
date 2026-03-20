"""
Shell tools for ADA CLI.

Security note:
- The router must ask for confirmation before calling `run_command`.
"""

from __future__ import annotations

import subprocess
from typing import Optional


def run_command(command: str, *, cwd: Optional[str] = None, timeout: Optional[int] = None) -> str:
    """
    Run a shell command and return stdout+stderr as a string.

    We do not raise on non-zero exit; we return output with a returncode hint.
    """
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            timeout=timeout,
            text=True,
            capture_output=True,
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        out = stdout + stderr
        if proc.returncode != 0:
            return f"[returncode={proc.returncode}]\n{out}"
        return out
    except subprocess.TimeoutExpired:
        return "Command timed out."
    except Exception as e:
        return f"Command failed: {e}"

