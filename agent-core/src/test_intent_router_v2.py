import sys
import os

sys.path.append(os.path.abspath("/Volumes/Datos/dockers/ADA/agent-core"))

from ada_core.conversation_engine import ConversationEngine

def main():
    engine = ConversationEngine()
    
    # Test 4: List Skills
    print("\n--- Test 4: List Skills Command ---")
    response4 = engine.respond("/skills")
    print(response4)
    
    # Test 5: Generic Skill (Strategy)
    print("\n--- Test 5: Generic Skill (Strategy) ---")
    response5 = engine.respond("/skill strategy how can we scale ADA's infrastructure?")
    print(response5)

if __name__ == "__main__":
    main()
