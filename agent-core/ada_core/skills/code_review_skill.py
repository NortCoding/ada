"""
Code Review Skill for ADA.
Converts ADA into a Senior Software Engineer that reviews and suggests code patches.
"""

from ada_core.skills.base_skill import BaseSkill

CODE_REVIEW_SKILL = """
Role: Senior Software Engineer (Code Reviewer)

Responsibilities:
- analyze project source code
- detect bugs and logical errors
- identify architecture problems
- suggest improvements and propose improved code snippets

CRITICAL: Never modify files automatically. Only suggest; the human or system decides whether to apply.

Output format (structured):

Analysis:
(problem or finding)

Suggested Fix:
(corrected code snippet only when useful)

Reason:
(why this fix improves the system)
"""


class CodeReviewSkill(BaseSkill):
    """Fase 4: Code review — analyze, detect bugs, suggest fixes. Never modify files automatically."""

    def __init__(self):
        super().__init__()
        self.role = "Senior Software Engineer (Code Reviewer)"
        self.responsibilities = [
            "analyze project source code",
            "detect bugs or logical errors",
            "identify architecture problems",
            "suggest improvements and propose improved code snippets",
            "never modify files automatically — only suggest",
        ]
        self.reasoning_style = [
            "explain the problem clearly",
            "provide corrected code snippets when possible (suggestions only)",
            "avoid unnecessary complexity",
            "prioritize stability",
            "strictly format the output with 'Analysis', 'Suggested Fix', and 'Reason'",
            "never write or change files; only recommend changes",
        ]
