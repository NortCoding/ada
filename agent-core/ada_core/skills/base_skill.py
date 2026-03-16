"""
Base definition for ADA's reusable cognitive skills.
"""

class BaseSkill:
    """
    Defines a cognitive persona for ADA.
    Contains the role description, key responsibilities, and reasoning style guidelines.
    """
    def __init__(self):
        self.role = "General AI Assistant"
        self.responsibilities = [
            "Provide helpful and accurate information.",
            "Follow user instructions safely."
        ]
        self.reasoning_style = [
            "Be concise and direct.",
            "Acknowledge limitations."
        ]

    def get_system_prompt(self) -> str:
        """Constructs the system prompt to be injected into the reasoning engine."""
        resp_list = "\n".join(f"- {r}" for r in self.responsibilities)
        style_list = "\n".join(f"- {s}" for s in self.reasoning_style)

        return (
            f"ROLE:\n{self.role}\n\n"
            f"RESPONSIBILITIES:\n{resp_list}\n\n"
            f"REASONING STYLE:\n{style_list}"
        )
