"""
ADA v2 — Strategy engine.
Analyzes ideas and generates opportunities. Uses reasoning + memory; safe on failure.
"""
from typing import List, Optional

from ada_core.memory_manager import MemoryManager
from ada_core.reasoning_engine import reason_about


class StrategyEngine:
    """Generate and store strategic ideas from goals. Never crashes."""

    def __init__(self):
        self.memory = MemoryManager()

    def get_active_goals(self) -> List[dict]:
        """Return active goals. Empty list on failure."""
        return self.memory.get_active_goals()

    def think_about_goal(self, goal: dict) -> List[str]:
        """
        For one goal, generate ideas via LLM. Returns list of idea strings (may be empty).
        """
        goal_text = goal.get("goal") or ""
        if not goal_text:
            return []

        prompt = f"""Given this strategic goal: "{goal_text}"

Generate 1 to 3 concrete ideas or next steps to advance this goal. Be brief; one line per idea.
Reply with only the ideas, one per line, no numbering or extra text."""

        response = reason_about(prompt)
        if not response:
            return []

        ideas = []
        for line in response.strip().split("\n"):
            line = line.strip()
            # Strip common prefixes like "1." or "-"
            for prefix in ("1.", "2.", "3.", "-", "*", "•"):
                if line.lower().startswith(prefix):
                    line = line[len(prefix):].strip()
                    break
            if line and len(line) > 5:
                ideas.append(line)
        return ideas[:5]

    def store_ideas(self, goal_id: Optional[int], ideas: List[str], score: float = 0) -> int:
        """Store ideas; return count stored. 0 on failure."""
        if not ideas:
            return 0
        n = 0
        for idea in ideas:
            if self.memory.store_idea(goal_id, idea, score):
                n += 1
        return n
