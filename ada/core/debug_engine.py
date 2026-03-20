"""
Debug engine for ADA CLI.

Goal: parse an error string, extract:
- file path
- line number

Then:
- read the file (real FS)
- print error + snippet
- return structured info
"""

from __future__ import annotations

import re
import difflib
from typing import Any, Dict, Optional

import os

from ada.tools.file_tools import read_file


def _extract_file_and_line(error_text: str) -> tuple[Optional[str], Optional[int]]:
    """
    Try extracting:
    - file path after 'File <path>' or 'file <path>'
    - line number after 'line <n>'
    """
    text = error_text or ""

    # Examples:
    # "File test.py line 10 NameError: ..."
    # "file /tmp/x.py line 2 ..."
    file_patterns = [
        r"[Ff]ile\s+(?P<path>[^\\s].*?)\s+[Ll]ine\s+(?P<line>\d+)",
        r"[Ff]ile\s+(?P<path>.+?)\s+[Ll]ine\s+(?P<line>\d+)",
    ]
    for pat in file_patterns:
        m = re.search(pat, text)
        if m:
            path = (m.group("path") or "").strip().strip("\"'`")
            line_s = m.group("line")
            try:
                line = int(line_s)
            except (TypeError, ValueError):
                line = None
            if path:
                return path, line

    # Fallback: line number only
    m_line = re.search(r"[Ll]ine\s+(?P<line>\d+)", text)
    line = None
    if m_line:
        try:
            line = int(m_line.group("line"))
        except (TypeError, ValueError):
            line = None
    return None, line


def _make_snippet(content: str, line_number: int, *, context_lines: int = 3) -> str:
    """
    Build a snippet around a 1-based line_number.
    """
    lines = content.splitlines()
    if line_number < 1:
        return content[:4000]

    start_idx = max(0, line_number - 1 - context_lines)
    end_idx = min(len(lines), line_number - 1 + context_lines + 1)
    snippet_lines = []
    for i in range(start_idx, end_idx):
        snippet_lines.append(f"{i+1}: {lines[i]}")
    return "\n".join(snippet_lines)


def show_diff(original: str, modified: str) -> str:
    """
    Print (and return) a unified diff, without applying any changes.
    """
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)

    diff = "".join(
        difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile="original",
            tofile="modified",
        )
    )
    if diff.strip():
        print("\n=== DIFF (unified) ===\n")
        print(diff)
    else:
        print("\n=== DIFF (unified) ===\nNo changes detected.")
    return diff


def apply_fix(path: str, new_content: str) -> dict:
    """
    Overwrite file using `write_file()` and confirm bytes written.
    """
    from ada.tools.file_tools import write_file

    res = write_file(path, new_content)
    print(f"Write success: {res['full_path']}")
    return res


def _extract_name_from_nameerror(error_text: str) -> Optional[str]:
    text = error_text or ""
    m1 = re.search(r"NameError:\s*(?P<name>\w+)\s+is not defined", text)
    if m1:
        return m1.group("name")
    m2 = re.search(r"NameError:\s*name\s+'(?P<name>\w+)'\s+is not defined", text)
    if m2:
        return m2.group("name")
    return None


def _heuristic_fix_nameerror(error_text: str, file_content: str) -> Optional[str]:
    """
    Minimal deterministic fixes (Phase 1 -> Phase 2):
    - NameError: x is not defined => insert `x = 0` at top if not present.
    """
    name = _extract_name_from_nameerror(error_text)
    if not name:
        return None

    # If already defined, don't touch.
    if re.search(rf"^\s*{re.escape(name)}\s*=", file_content, flags=re.MULTILINE):
        return None

    assignment = f"{name} = 0\n"

    # Prefer inserting after shebang/encoding/comments header when present.
    lines = file_content.splitlines(keepends=True)
    idx = 0
    # Keep initial shebang / encoding / blank lines / comments.
    while idx < len(lines):
        stripped = lines[idx].strip()
        if idx == 0 and lines[idx].startswith("#!"):
            idx += 1
            continue
        if re.match(r"^#.*coding[:=]\s*[-\w.]+", stripped):
            idx += 1
            continue
        if stripped.startswith("#") or stripped == "":
            idx += 1
            continue
        break

    new_content = "".join(lines[:idx]) + assignment + "".join(lines[idx:])
    return new_content


def _extract_first_code_block(text: str) -> Optional[str]:
    """
    Extract first fenced code block from a model response.
    """
    if not text:
        return None
    m = re.search(r"```(?:python)?\s*\n(?P<code>.*?\n)```", text, flags=re.DOTALL)
    if m:
        return m.group("code").strip("\n")
    return None

def analyze_error(error_text: str) -> Dict[str, Any]:
    """
    Steps:
    1) Extract file path + line number
    2) If file exists:
       - read file
       - print error + snippet
    3) Return structured info
    """
    file_path, line_number = _extract_file_and_line(error_text)

    print("== ADA DEBUG ENGINE: analyze_error ==")
    print("Error text:")
    print(error_text.strip() if error_text else "")
    print(f"Extracted file_path: {file_path}")
    print(f"Extracted line_number: {line_number}")

    if not file_path:
        return {
            "file_path": None,
            "line_number": line_number,
            "exists": False,
            "snippet": "",
            "content_length": 0,
        }

    base_path = os.getcwd()
    full_path = os.path.join(base_path, file_path)

    content = read_file(file_path)
    if not os.path.exists(full_path) or not os.path.isfile(full_path) or content == "":
        print(f"File not found: {full_path}")
        return {
            "file_path": file_path,
            "line_number": line_number,
            "exists": False,
            "snippet": "",
            "content_length": 0,
        }

    content_length = len(content)
    snippet = ""
    if line_number is not None:
        snippet = _make_snippet(content, line_number)
    else:
        snippet = content[:4000]

    print("\nFile snippet:")
    print(snippet)

    return {
        "file_path": file_path,
        "line_number": line_number,
        "exists": True,
        "snippet": snippet,
        "content_length": content_length,
        "content": content,
    }


def suggest_fix(error_text: str, file_content: str) -> str:
    """
    Proposed fix (IA).

    This step tries to use Ollama if available. If Ollama is not running,
    we fall back to a placeholder suggestion.

    NOTE: This function does not write/modify any files.
    """
    import json
    import urllib.request

    # 1) Deterministic heuristic first (fast + reliable for early stages).
    heuristic = _heuristic_fix_nameerror(error_text, file_content)
    if heuristic:
        return heuristic

    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    base_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")

    prompt = (
        "Fix this error in the given file. "
        "Return the corrected full file content as plain text. "
        "Do not include markdown fences.\n\n"
        f"Error:\n{error_text}\n\n"
        f"File content:\n{file_content}\n"
    )

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

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
        if not response_text.strip():
            raise RuntimeError("Empty ollama response")
        extracted = _extract_first_code_block(response_text)
        if extracted:
            return extracted.strip()
        return response_text.strip()
    except Exception:
        # Keep going with a minimal placeholder suggestion.
        return (
            "/* Proposed fix (placeholder) */\n"
            "// Ollama not available (or failed). No automatic write.\n"
        )

