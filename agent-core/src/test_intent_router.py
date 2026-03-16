import sys
import os

sys.path.append(os.path.abspath("/Volumes/Datos/dockers/ADA/agent-core"))

from ada_core.conversation_engine import ConversationEngine

def main():
    engine = ConversationEngine()
    
    # Test 1: Normal chat
    print("--- Test 1: Normal Chat ---")
    response1 = engine.respond("Hello ADA, what are you?")
    print(response1)
    
    # Test 2: Web Search
    print("\n--- Test 2: Web Search Command ---")
    response2 = engine.respond("/search Open source AI agents 2024")
    print(response2)
    
    # Test 3: Code Review (Using a temp buggy file)
    print("\n--- Test 3: Code Review Command ---")
    
    path = "/tmp/test_router_bug.py"
    with open(path, "w") as f:
        f.write("def div(a,b):\n    return a*b\n")
        
    response3 = engine.respond(f"/review {path}")
    print(response3)
    
    os.remove(path)

if __name__ == "__main__":
    main()
