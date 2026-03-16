import sys
import os

# Ensure the module can find ada_core
sys.path.append(os.path.abspath("/Volumes/Datos/dockers/ADA/agent-core"))

from ada_core.research_engine import web_research_topic

def main():
    print("Testing Web Research Tool...")
    query = "latest advancements in local LLM models 2024."
    print(f"Query: {query}\n")
    
    results = web_research_topic(query, max_results=3, max_pages_to_read=1)
    
    print("\n--- RESULTS ---\n")
    for r in results:
        print(f"Title: {r.get('title')}")
        print(f"Source: {r.get('source_url')}")
        print(f"Summary:\n{r.get('summary')}\n")

if __name__ == "__main__":
    main()
