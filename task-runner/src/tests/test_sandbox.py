import pytest
import os
import sys

# Ensure sandbox can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sandbox import execute_bash, is_safe_path

TEST_WORKSPACE = os.getenv("WORKSPACE_DIR", "/app/workspace")

def test_within_workspace_valid():
    assert is_safe_path(f"{TEST_WORKSPACE}/foo/bar") is True
    assert is_safe_path(f"{TEST_WORKSPACE}") is True

def test_within_workspace_invalid():
    assert is_safe_path("/tmp/outside") is False
    assert is_safe_path(f"{TEST_WORKSPACE}/../tmp") is False

def test_execute_bash_safe_command():
    result = execute_bash("echo 'hello sandbox'")
    if not result["success"]:
        print(result["stderr"])
    assert result["success"] is True
    assert "hello sandbox" in result["stdout"]
    assert result["exit_code"] == 0

def test_execute_bash_timeout():
    result = execute_bash("sleep 3", timeout_seconds=1)
    assert result["success"] is False
    assert "límite" in result["stderr"] or "Timeout" in result["stderr"]
    assert result["exit_code"] == 124

def test_dangerous_commands_blocked():
    dangerous_commands = [
        "rm -rf /",
        "mkfs",
        "dd ",
        "> /dev/sd"
    ]
    for cmd in dangerous_commands:
        result = execute_bash(cmd)
        assert result["success"] is False
        assert "Error de seguridad" in result["stderr"]
        assert result["exit_code"] == 1
