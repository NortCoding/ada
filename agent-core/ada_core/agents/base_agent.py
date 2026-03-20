"""
ADA v3 — Base Agent.
Common interface for all specialized agents.
"""
from typing import Any, Dict, List, Optional
from ada_core.skills import SKILL_REGISTRY
from ada_core.reasoning_engine import run_with_skill

class BaseAgent:
    """
    Standard agent class. Encapsulates personality and skill access.
    """
    
    def __init__(self, name: str, role: str, skills: List[str]):
        self.name = name
        self.role = role
        self.skills = skills

    def execute(self, task_description: str, context: Optional[str] = None) -> Dict:
        """
        Main execution loop for the agent.
        """
        # 1. Decide which skill to use
        skill_to_use = self._decide_skill(task_description)
        
        # 2. Execute the skill if found, otherwise use general reasoning
        if skill_to_use and skill_to_use in self.skills:
            result = run_with_skill(skill_to_use, f"Task: {task_description}\nContext: {context}")
        else:
            result = run_with_skill("strategy", f"Task: {task_description}\nContext: {context}")

        return {
            "agent": self.name,
            "skill_used": skill_to_use or "general_reasoning",
            "result": result,
            "status": "completed" if result else "failed"
        }

    def _decide_skill(self, description: str) -> Optional[str]:
        """
        Simple heuristic for skill selection.
        """
        # In a real v3 implementation, this would be an LLM call
        desc = description.lower()
        for skill in self.skills:
            if skill in desc or (skill == "coding" and "code" in desc):
                return skill
        return self.skills[0] if self.skills else None
