"""
ADA v3 — Planning Engine.
Breaks down high-level goals into executable tasks.
"""
from typing import Any, Dict, List, Optional
from ada_core.memory_manager import MemoryManager
from ada_core.reasoning_engine import reason_about

class PlanningEngine:
    """
    Takes an Opportunity or a Goal and produces a structured list of tasks.
    """
    
    def __init__(self):
        self.memory = MemoryManager()

    def create_plan(self, goal: str, context: Optional[str] = None) -> List[Dict]:
        """
        Uses reasoning to decompose a goal into steps.
        """
        prompt = (
            f"GOAL: {goal}\n"
            f"CONTEXT: {context or 'No additional context'}\n\n"
            "Analyze this goal and break it down into a maximum of 5 distinct, actionable tasks. "
            "For each task, provide a clear description and identify which agent type should handle it "
            "(developer, research, business, or automation).\n\n"
            "Return the plan in exactly this format for each step:\n"
            "Task: <description>\n"
            "Agent: <type>\n"
        )
        
        raw_plan = reason_about(prompt)
        tasks = self._parse_plan(raw_plan)
        
        # Store the plan in memory
        if tasks:
            self.memory.add_experience(
                event=f"action_plan_v3:{goal[:100]}",
                result=raw_plan,
                learning="Goal decomposed into specialized tasks."
            )
            
        return tasks

    def _parse_plan(self, raw_text: str) -> List[Dict]:
        """
        Parses the text output from the LLM into a structured list of tasks.
        """
        if not raw_text:
            return []
            
        tasks = []
        current_task = {}
        
        for line in raw_text.split("\n"):
            line = line.strip()
            if line.startswith("Task:"):
                if current_task:
                    tasks.append(current_task)
                current_task = {"description": line[len("Task:"):].strip()}
            elif line.startswith("Agent:"):
                if current_task:
                    current_task["agent"] = line[len("Agent:"):].strip().lower()
        
        if current_task:
            tasks.append(current_task)
            
        return tasks
