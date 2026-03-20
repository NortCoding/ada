"""
Tools initialization mapping for ADA.
"""

from ada_core.tools.web_search import search_web
from ada_core.tools.web_reader import read_webpage
from ada_core.tools.code_reader import read_code_file
from ada_core.tools.project_scanner import scan_project
from ada_core.tools.file_ops import make_dir, write_file

__all__ = ["search_web", "read_webpage", "read_code_file", "scan_project", "make_dir", "write_file"]
