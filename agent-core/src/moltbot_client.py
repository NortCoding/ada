import os
import requests
from typing import Any, Dict, Optional

class MoltbotClient:
    """
    Client for Moltbot, integrated as a high-level tool for ADA.
    """
    def __init__(self):
        self.url = os.getenv("MOLTBOT_URL", "http://moltbot:3010/execute")
        self.timeout = int(os.getenv("MOLTBOT_TIMEOUT", "60"))

    def execute_task(self, task_name: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Sends a task to Moltbot for execution."""
        try:
            payload = {
                "task": task_name,
                "details": details
            }
            response = requests.post(self.url, json=payload, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            return {"status": "failed", "error": f"Moltbot returned status {response.status_code}", "detail": response.text}
        except Exception as e:
            return {"status": "error", "error": str(e)}

moltbot = MoltbotClient()
