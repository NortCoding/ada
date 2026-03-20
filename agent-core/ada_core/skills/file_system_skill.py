"""
ADA v3 — File System Skill.
Explicit file operations for ADA's autonomous workspace.
"""
import os
import shutil
from typing import List, Optional
from ada_core.skills.base_skill import BaseSkill

WORKSPACE_ROOT = "/Volumes/Datos/dockers/ADA/workspace"

class FileSystemSkill(BaseSkill):
    def __init__(self):
        super().__init__()
        self.role = "You are ADA's File System Manager. Your objective is to manage the autonomous workspace storage."

    def write_file(self, folder: str, filename: str, content: str) -> str:
        """Writes a file to a specific workspace folder (downloads, images, code, documents, tasks)."""
        target_dir = os.path.join(WORKSPACE_ROOT, folder)
        if not os.path.exists(target_dir):
            return f"Error: Folder {folder} does not exist in workspace."
        
        filepath = os.path.join(target_dir, filename)
        with open(filepath, "w") as f:
            f.write(content)
        return f"File {filename} written to {folder}."

    def read_file(self, folder: str, filename: str) -> str:
        filepath = os.path.join(WORKSPACE_ROOT, folder, filename)
        if not os.path.exists(filepath):
            return "Error: File not found."
        with open(filepath, "r") as f:
            return f.read()

    def list_files(self, folder: str) -> List[str]:
        target_dir = os.path.join(WORKSPACE_ROOT, folder)
        if not os.path.exists(target_dir):
            return []
        return os.listdir(target_dir)

    def save_image(self, filename: str, content_bytes: bytes) -> str:
        filepath = os.path.join(WORKSPACE_ROOT, "images", filename)
        with open(filepath, "wb") as f:
            f.write(content_bytes)
        return f"Image {filename} saved."
