"""
ADA v3 — Goal generation engine.
Generates derived goals from parent goals and ideas. Wraps and extends decision_engine logic.
Never crashes; returns 0 or empty list on failure.
"""
from typing import List, Optional

from ada_core.memory_manager import MemoryManager
from ada_core.decision_engine import generate_derived_goals as _generate_derived_goals


def generate_derived_goals(
    parent_goal: dict,
    ideas: List[str],
    memory: Optional[MemoryManager] = None,
) -> int:
    """
    Generate new sub-goals from a parent goal and its ideas. Stores in derived_goals table.
    Example: parent "generate income", idea "sell automation bots" -> derived "build prototype automation bot".
    Returns count of goals stored. 0 on failure.
    """
    try:
        return _generate_derived_goals(parent_goal, ideas, memory)
    except Exception:
        return 0


def get_active_derived_goals(
    parent_goal_id: Optional[int] = None,
    memory: Optional[MemoryManager] = None,
) -> List[dict]:
    """Return active derived goals, optionally for one parent. Empty list on failure."""
    mem = memory or MemoryManager()
    try:
        return mem.get_derived_goals(parent_goal_id=parent_goal_id, status="active")
    except Exception:
        return []
