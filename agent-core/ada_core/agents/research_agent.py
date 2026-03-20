"""
ADA v3 — Research Agent.
Specialist in finding information and summarizing knowledge.
"""
from typing import List, Optional
from ada_core.agents.base_agent import BaseAgent

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="research",
            role="Specialist in information retrieval, web research, and summarizing complex data.",
            skills=["web_research", "learning"]
        )

    def execute(self, task_description: str, context: Optional[str] = None) -> dict:
        return super().execute(task_description, context)
