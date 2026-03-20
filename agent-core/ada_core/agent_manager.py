"""
ADA v3 — Agent Manager.
Defines specialized agents and the skills they can use.
"""
from typing import List

# Agent type -> list of skill names (must exist in SKILL_REGISTRY)
AGENTS = {
    "developer": [
        "coding",
        "code_review",
        "architecture",
    ],
    "business": [
        "strategy",
        "research",
        "opportunity_engine",  # used as capability, not a skill class
    ],
    "research": [
        "web_research",
        "learning",
    ],
    "general": [
        "strategy",
        "research",
    ],
}


def get_agent_skills(agent_type: str) -> List[str]:
    """
    Returns the list of skill names for the given agent type.
    Unknown types return the "general" agent skills.
    """
    agent_type = (agent_type or "general").strip().lower()
    return list(AGENTS.get(agent_type, AGENTS["general"]))


def list_agents() -> List[str]:
    """Returns the list of available agent type identifiers."""
    return list(AGENTS.keys())
