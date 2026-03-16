"""
ADA v2 Autonomous — Decision engine.
Selects best opportunities, creates action plans, triggers derived goals and experience evaluation.
Never crashes; returns empty list or None on failure.
"""
import os
from typing import List, Optional

from ada_core.reasoning_engine import reason_about
from ada_core.memory_manager import MemoryManager

# Score 0-10 scale: 0.75 threshold = 7.5 (top 75%)
SCORE_THRESHOLD = float(os.getenv("ADA_OPPORTUNITY_SCORE_THRESHOLD", "7.5"))
TOP_N_OPPORTUNITIES = int(os.getenv("ADA_TOP_OPPORTUNITIES", "3"))


def select_best_opportunities(
    memory: Optional[MemoryManager] = None,
    score_threshold: Optional[float] = None,
    top_n: Optional[int] = None,
) -> List[dict]:
    """
    Select opportunities where score >= threshold, sort by score desc, take top N.
    Returns list of opportunity dicts (id, idea, score, goal_id, ...). Empty list on failure.
    """
    mem = memory or MemoryManager()
    threshold = score_threshold if score_threshold is not None else SCORE_THRESHOLD
    n = top_n if top_n is not None else TOP_N_OPPORTUNITIES
    try:
        all_opps = mem.get_opportunities(status="pending", limit=100)
        filtered = [o for o in all_opps if (o.get("score") or 0) >= threshold]
        filtered.sort(key=lambda x: -(x.get("score") or 0))
        return filtered[:n]
    except Exception:
        return []


def create_action_plan(opportunity: dict) -> str:
    """
    Generate a concrete action plan for an opportunity using reasoning_engine.
    opportunity: dict with idea, score, goal_id, etc.
    Returns plan text or empty string on failure.
    """
    idea = opportunity.get("idea") or ""
    goal_id = opportunity.get("goal_id")
    if not idea:
        return ""

    prompt = f"""Given this opportunity: "{idea[:500]}"

Create a short action plan (3 to 5 concrete steps) to execute it.
Consider: project ADA, local tools (Ollama, code, scripts), no heavy infrastructure.
Reply with only the steps, one per line, brief and actionable."""

    return reason_about(prompt).strip()


def generate_derived_goals(parent_goal: dict, ideas: List[str], memory: Optional[MemoryManager] = None) -> int:
    """
    From a parent goal and list of ideas, generate derived goals (e.g. "build prototype X").
    Uses LLM to suggest 1-3 derived goals; stores them and returns count stored.
    """
    mem = memory or MemoryManager()
    parent_id = parent_goal.get("id")
    goal_text = parent_goal.get("goal") or ""
    if not goal_text or not ideas:
        return 0

    ideas_preview = "\n".join(f"- {i[:200]}" for i in ideas[:5])
    prompt = f"""Parent goal: "{goal_text}"

Ideas from this goal:
{ideas_preview}

Generate 1 to 3 new concrete sub-goals (derived goals) that would help achieve the parent goal.
Example: if parent is "generate income" and idea is "sell automation bots", derived goal could be "build prototype automation bot".
Reply with only the derived goals, one per line, no numbering."""

    out = reason_about(prompt)
    if not out:
        return 0

    count = 0
    for line in out.strip().split("\n"):
        line = line.strip()
        for prefix in ("1.", "2.", "3.", "-", "*", "•"):
            if line.lower().startswith(prefix):
                line = line[len(prefix):].strip()
                break
        if line and len(line) > 10:
            if mem.add_derived_goal(parent_id, line):
                count += 1
    return count


def evaluate_experience(result_text: str) -> str:
    """
    Analyze an experience result and extract lessons learned. Returns learning text or empty.
    """
    if not result_text or not result_text.strip():
        return ""
    prompt = f"""Analyze this experience result and extract lessons learned. Be concise (2-4 sentences).

Result:
{result_text[:1500]}

Lessons learned:"""
    return reason_about(prompt).strip()
