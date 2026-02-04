"""Critic module - self-critiques the draft using structured output."""

from services.llm import LLMService
from models.schemas import InputMode, Critique, CritiqueIssue


CRITIC_SYSTEM_PROMPT = """You are a rigorous, adversarial critic. Your job is to find EVERYTHING wrong
with the draft response before it reaches the user.

Analyze for:
- Factual errors or unsupported claims
- Logical fallacies or reasoning gaps
- Missing important nuance or context
- Overconfident statements presented as fact
- Potential hallucinations (specific numbers, dates, names that could be fabricated)
- Bias or one-sidedness

Also identify what the draft got RIGHT — the strengths that should be preserved.

Extract SPECIFIC factual claims that can be independently verified. These should be concrete,
checkable statements — not vague topics. For example:
  ✅ "The Treaty of Versailles was signed in 1919"
  ❌ "Something about World War I treaties"

Be thorough. Be harsh. The next step will verify your claims against real sources.
You MUST use the submit_critique tool to provide your analysis."""


CRITIC_TOOLS = [
    {
        "name": "submit_critique",
        "description": "Submit a structured critique of the draft response",
        "input_schema": {
            "type": "object",
            "properties": {
                "issues": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "severity": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                            },
                            "quote": {
                                "type": "string",
                                "description": "The specific part of the draft this refers to",
                            },
                        },
                        "required": ["description", "severity"],
                    },
                },
                "strengths": {"type": "array", "items": {"type": "string"}},
                "claims_to_verify": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific factual claims that should be checked against external sources. Extract exact claims, not vague topics.",
                },
                "confidence": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "How confident you are in the draft's overall accuracy",
                },
            },
            "required": ["issues", "strengths", "claims_to_verify", "confidence"],
        },
    }
]


class Critic:
    """Analyzes draft response and produces structured critique."""

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def analyze(
        self, user_input: str, draft: str, mode: InputMode
    ) -> Critique:
        """Analyze the draft and return structured critique."""
        user_message = f"""Original input: {user_input}

Mode: {mode.value}

Draft response to critique:
{draft}

Analyze this draft thoroughly and use the submit_critique tool to provide your structured critique."""

        result = await self.llm.generate_with_tools(
            system=CRITIC_SYSTEM_PROMPT,
            user=user_message,
            tools=CRITIC_TOOLS,
            tool_choice={"type": "tool", "name": "submit_critique"},
        )

        if result is None:
            # Fallback if tool call fails
            return Critique(
                issues=[],
                strengths=["Draft appears reasonable"],
                claims_to_verify=[],
                confidence=50,
            )

        # Parse the tool response into our model
        issues = [
            CritiqueIssue(
                description=i.get("description", ""),
                severity=i.get("severity", "medium"),
                quote=i.get("quote"),
            )
            for i in result.get("issues", [])
        ]

        return Critique(
            issues=issues,
            strengths=result.get("strengths", []),
            claims_to_verify=result.get("claims_to_verify", []),
            confidence=result.get("confidence", 50),
        )
