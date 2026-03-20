"""
Exports for the ADA Core Skills package.
"""
from ada_core.skills.architecture_skill import ArchitectureSkill
from ada_core.skills.coding_skill import CodingSkill
from ada_core.skills.learning_skill import LearningSkill
from ada_core.skills.research_skill import ResearchSkill
from ada_core.skills.strategy_skill import StrategySkill
from ada_core.skills.web_research_skill import WebResearchSkill
from ada_core.skills.code_review_skill import CodeReviewSkill

from ada_core.skills.web_automation_skill import WebAutomationSkill
from ada_core.skills.file_system_skill import FileSystemSkill

SKILL_REGISTRY = {
    "architecture": ArchitectureSkill,
    "research": ResearchSkill,
    "strategy": StrategySkill,
    "coding": CodingSkill,
    "learning": LearningSkill,
    "web_research": WebResearchSkill,
    "code_review": CodeReviewSkill,
    "web_automation": WebAutomationSkill,
    "file_system": FileSystemSkill,
}

def get_skill_system_prompt(skill_name: str) -> str:
    """Retrieves the formatted system prompt for a given skill name."""
    skill_class = SKILL_REGISTRY.get(skill_name.lower())
    if not skill_class:
        return ""
    
    skill_instance = skill_class()
    return skill_instance.get_system_prompt()
