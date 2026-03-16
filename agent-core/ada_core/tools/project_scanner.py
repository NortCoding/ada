"""
Project Scanner Tool for ADA.
Scans directories for code files while ignoring heavy or binary folders.
"""
import os
from typing import List

# Directories that should NEVER be scanned to prevent context bloat and slow execution
IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "build", "dist", ".next"}

# File extensions that are valid for ADA to review
TARGET_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".md", ".json", ".html", ".css", ".sh"}

def scan_project(directory: str, max_files: int = 50) -> List[str]:
    """
    Scans a directory recursively for readable code files, 
    ignoring specific heavy/binary folders.
    Returns a list of absolute or relative paths depending on the input directory.
    """
    files_found = []
    
    if not os.path.exists(directory):
        return []

    for root, dirs, filenames in os.walk(directory):
        # Modify dirs list in place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for f in filenames:
            if any(f.endswith(ext) for ext in TARGET_EXTS):
                files_found.append(os.path.join(root, f))
                
                # Stop scanning if we hit the limit to protect the LLM's context window
                if len(files_found) >= max_files:
                    return files_found
                    
    return files_found
