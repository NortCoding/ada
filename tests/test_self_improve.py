import os
import time
from pathlib import Path

import requests

AGENT_URL = os.getenv("AGENT_URL", "http://localhost:3001").rstrip("/")
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))


def _wait_for(url: str, timeout_sec: int = 180) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(3)
    return False


def test_agent_core_health():
    assert _wait_for(f"{AGENT_URL}/health", timeout_sec=180), "agent-core /health not ready"


def test_web_search_and_self_improve():
    r = requests.get(
        f"{AGENT_URL}/web_search",
        params={"query": "autonomous llm self improve safe code diffs"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"/web_search failed: {r.status_code} {r.text}"
    data = r.json()
    assert isinstance(data, dict)
    assert "query" in data
    assert "summary" in data or "results" in data

    r2 = requests.get(
        f"{AGENT_URL}/self_improve",
        params={"trigger": "pytest_e2e"},
        timeout=TIMEOUT,
    )
    assert r2.status_code == 200, f"/self_improve failed: {r2.status_code} {r2.text}"
    data2 = r2.json()
    assert isinstance(data2, dict)
    assert data2.get("status") in {"improved", "no_change", "blocked", "error"}


def test_spawn_alma_and_health():
    r = requests.get(
        f"{AGENT_URL}/spawn_agent",
        params={"agent_name": "ALMA"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"/spawn_agent failed: {r.status_code} {r.text}"
    payload = r.json()
    assert isinstance(payload, dict)
    assert payload.get("status") in {"spawned", "exists", "ok", "created"}

    alma_dir = Path("agents/ALMA")
    assert alma_dir.exists(), "agents/ALMA folder does not exist after spawn"

    dockerfile = alma_dir / "Dockerfile"
    api_file = alma_dir / "src" / "agent_api.py"
    assert dockerfile.exists(), "ALMA Dockerfile missing"
    assert api_file.exists(), "ALMA API file missing"

    # ALMA service may take extra time to be fully available
    _wait_for("http://localhost:3011/health", timeout_sec=180)
