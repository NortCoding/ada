import sys
import os
import json

# Ensure the module can find ada_core
sys.path.append(os.path.abspath("/Volumes/Datos/dockers/ADA/agent-core"))

from ada_core.reasoning_engine import review_single_file, review_project

def create_buggy_file():
    path = "/tmp/buggy_example.py"
    with open(path, "w") as f:
        f.write("def add_numbers(a, b):\n    return a - b\n\nprint(add_numbers(5, 3))\n")
    return path

def main():
    print("Testing Code Review System...")
    buggy_file = create_buggy_file()
    
    print(f"\n--- Testing Single File Review on {buggy_file} ---")
    result = review_single_file(buggy_file)
    print(f"File: {result.get('file')}")
    print(f"Analysis:\n{result.get('analysis')}\n")
    
    os.remove(buggy_file)

if __name__ == "__main__":
    main()
