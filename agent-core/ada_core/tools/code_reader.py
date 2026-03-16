"""
Code Reader Tool for ADA.
Safely extracts text from source code files.
"""
import os
from typing import Optional

def read_code_file(path: str) -> Optional[str]:
    """
    Reads a source code file safely.
    Returns the file content as a string, or None if it fails/doesn't exist.
    """
    if not os.path.exists(path):
        return None
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {path}: {str(e)}"
