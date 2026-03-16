import sys
import os

# Ensure the module can find ada_core
sys.path.append(os.path.abspath("/Volumes/Datos/dockers/ADA/agent-core"))

from ada_core.reasoning_engine import run_with_skill

def main():
    print("Testing Architecture Skill...")
    prompt = "Create a robust directory structure for a new microservice."
    response = run_with_skill("architecture", prompt)
    print("\n--- RESPONSE ---\n")
    print(response)

if __name__ == "__main__":
    main()
