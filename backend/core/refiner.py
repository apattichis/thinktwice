"""Refiner module - produces final refined answer."""

from services.llm import LLMService
from models.schemas import InputMode, Critique, VerificationResult, RefinedResponse


REFINER_SYSTEM_PROMPT = """You are a careful editor producing the final, refined response.

You have access to:
1. The original user input
2. The initial draft response
3. A critique identifying issues and strengths
4. Verification results for factual claims

Your job is to produce an improved response that:
- Fixes all issues identified in the critique
- Preserves the strengths noted in the critique
- Incorporates the verification results (correct verified info, fix refuted claims, acknowledge unclear claims)
- Maintains a helpful, clear tone
- Cites sources where appropriate

After writing the refined response, also provide:
- A list of specific changes you made
- Your confidence level (0-100) in the refined response's accuracy

Use the submit_refined_response tool to provide your output."""


REFINER_TOOLS = [
    {
        "name": "submit_refined_response",
        "description": "Submit the refined response with metadata",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The refined, improved response",
                },
                "confidence": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Your confidence in the accuracy of this refined response",
                },
                "changes_made": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of specific changes/improvements made from the original draft",
                },
            },
            "required": ["content", "confidence", "changes_made"],
        },
    }
]


class Refiner:
    """Produces final refined response incorporating all feedback."""

    def __init__(self, llm: LLMService):
        self.llm = llm

    def _format_critique(self, critique: Critique) -> str:
        """Format critique for the prompt."""
        lines = ["## Critique"]

        if critique.issues:
            lines.append("\n### Issues Found:")
            for issue in critique.issues:
                severity = issue.severity.upper()
                lines.append(f"- [{severity}] {issue.description}")
                if issue.quote:
                    lines.append(f'  Quote: "{issue.quote}"')

        if critique.strengths:
            lines.append("\n### Strengths (preserve these):")
            for strength in critique.strengths:
                lines.append(f"- {strength}")

        lines.append(f"\n### Initial Confidence: {critique.confidence}%")

        return "\n".join(lines)

    def _format_verifications(self, results: list[VerificationResult]) -> str:
        """Format verification results for the prompt."""
        if not results:
            return "## Verification Results\nNo claims were verified."

        lines = ["## Verification Results"]
        for r in results:
            emoji = {"verified": "✅", "refuted": "❌", "unclear": "⚠️"}.get(
                r.verdict, "?"
            )
            lines.append(f"\n{emoji} **{r.verdict.upper()}**: {r.claim}")
            lines.append(f"   {r.explanation}")
            if r.source:
                lines.append(f"   Source: {r.source}")
            if not r.web_verified:
                lines.append("   ⚠️ Not web-verified (AI knowledge only)")

        return "\n".join(lines)

    async def produce(
        self,
        user_input: str,
        draft: str,
        critique: Critique,
        verification_results: list[VerificationResult],
        mode: InputMode,
    ) -> RefinedResponse:
        """Produce the final refined response."""
        user_message = f"""## Original Input
Mode: {mode.value}
{user_input}

## Initial Draft
{draft}

{self._format_critique(critique)}

{self._format_verifications(verification_results)}

---

Now produce an improved, refined response that addresses all the issues, incorporates the verification results, and preserves the strengths. Use the submit_refined_response tool."""

        result = await self.llm.generate_with_tools(
            system=REFINER_SYSTEM_PROMPT,
            user=user_message,
            tools=REFINER_TOOLS,
            tool_choice={"type": "tool", "name": "submit_refined_response"},
        )

        if result is None:
            # Fallback if tool call fails
            return RefinedResponse(
                content=draft,
                confidence=critique.confidence,
                changes_made=["No refinements could be made"],
            )

        return RefinedResponse(
            content=result.get("content", draft),
            confidence=result.get("confidence", critique.confidence),
            changes_made=result.get("changes_made", []),
        )

    async def stream(
        self,
        user_input: str,
        draft: str,
        critique: Critique,
        verification_results: list[VerificationResult],
        mode: InputMode,
    ):
        """Stream the refined response (for the content only)."""
        # For streaming, we just stream the content without the tool structure
        user_message = f"""## Original Input
Mode: {mode.value}
{user_input}

## Initial Draft
{draft}

{self._format_critique(critique)}

{self._format_verifications(verification_results)}

---

Write an improved, refined response that addresses all the issues, incorporates the verification results, and preserves the strengths."""

        async for token in self.llm.stream(system=REFINER_SYSTEM_PROMPT, user=user_message):
            yield token
