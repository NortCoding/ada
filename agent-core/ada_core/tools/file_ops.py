"""
File Operations Tool for ADA.
Allows ADA to create directories and write files safely.
"""
import os
import logging

def make_dir(path: str) -> str:
    """Creates a directory at the given path."""
    try:
        # Prevent escaping the allowed dockers zone if needed, 
        # but for now we trust the volume maps.
        os.makedirs(path, exist_ok=True)
        return f"Directory created or already exists: {path}"
    except Exception as e:
        return f"Error creating directory {path}: {str(e)}"

def write_file(path: str, content: str) -> str:
    """Writes content to a file at the given path."""
    try:
        # Ensure the parent directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File written successfully: {path}"
    except Exception as e:
        return f"Error writing file {path}: {str(e)}"
