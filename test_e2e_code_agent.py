import requests
import time
import os
import json

AGENT_CORE_URL = "http://localhost:3001"
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "workspace"))
TEST_FILENAME = "test_ada_e2e.html"
TEST_FILEPATH = os.path.join(WORKSPACE_DIR, TEST_FILENAME)

def run_e2e_test():
    print("==================================================")
    print("🚀 Starting E2E Test for CODE Agent Integration")
    print("==================================================")
    
    # Payload para simular una propuesta generada por el Brain (agent-core)
    # y enviada al pipeline: Simulation -> Policy -> Task Runner (Hands)
    payload = {
        "task_name": "bash_command",
        "details": {
            "command": f"echo '<h1>Hello from ADA Sandbox E2E Test</h1>' > {TEST_FILENAME}",
            "timeout_seconds": 15,
            "description": "Create an HTML file to verify sandbox access."
        }
    }

    print(f"\n[1] Sending 'propose' task to agent-core: {AGENT_CORE_URL}/propose")
    try:
        response = requests.post(f"{AGENT_CORE_URL}/propose", json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        print("\n✅ Task Result Payload:")
        print(json.dumps(data.get("task_result", {}), indent=2))
        
        if data.get("status") != "done":
             print(f"\n❌ Pipeline failed early. Status: {data.get('status')}")
             return
             
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Failed to communicate with agent-core: {e}")
        return

    # Esperar propagación del file system
    time.sleep(1)
    
    print(f"\n[2] Verifying file creation in host workspace: {TEST_FILEPATH}")
    if os.path.exists(TEST_FILEPATH):
        with open(TEST_FILEPATH, "r") as f:
            content = f.read().strip()
            print(f"File contents: {content}")
        
        if "Hello from ADA Sandbox E2E Test" in content:
            print("\n🎉 E2E Test Passed: The agent proposed a command, it cleared policies, and task-runner executed it safely in the workspace!")
            # Cleanup
            os.remove(TEST_FILEPATH)
            print("🧹 Cleanup: Removed test file.")
        else:
            print(f"\n❌ E2E Test Failed: The file exists but contains unexpected content: {content}")
    else:
        print(f"\n❌ E2E Test Failed: The file {TEST_FILENAME} was not found in the workspace.")

if __name__ == "__main__":
    run_e2e_test()
