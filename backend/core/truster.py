"""Trust-and-rank comparator (ART-inspired).

Phase 7 of the v2 pipeline. Side-by-side comparison of original draft
vs refined output. Picks the winner or blends the best parts of both.
"""

import logging
from typing import Optional

from services.llm import LLMService
from core.schemas import (
    Constraint,
    VerificationResultV2,
    ClaimVerdict,
    TrustResult,
)
from core.prompts import TRUST_SYSTEM_PROMPT, TRUST_USER_PROMPT

logger = logging.getLogger(__name__)

TRUST_TOOLS = [
    {
        "name": "submit_trust_decision",
        "description": "Submit the trust comparison decision",
        "input_schema": {
            "type": "object",
            "properties": {
                "winner": {
                    "type": "string",
                    "enum": ["draft", "refined", "blended"],
                },
                "reasoning": {
                    "type": "string",
                    "description": "Explanation of why this version was chosen",
                },
                "draft_score": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                },
                "refined_score": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                },
                "final_output": {
                    "type": "string",
                    "description": "The chosen final output text (or blended version)",
                },
                "blended": {
                    "type": "boolean",
                    "description": "Whether the output is a blend of both versions",
                },
                "blend_notes": {
                    "type": "string",
                    "description": "If blended, explain which parts came from where",
                },
            },
            "required": [
                "winner",
                "reasoning",
                "draft_score",
                "refined_score",
                "final_output",
                "blended",
            ],
        },
    }
]


def _format_constraints(constraints: list[Constraint]) -> str:
    """Format constraints for prompt insertion."""
    lines = []
    for c in constraints:
        lines.append(f"[{c.id}] ({c.priority.value.upper()}) {c.description}")
    return "\n".join(lines)


def _format_verifications(verifications: list[VerificationResultV2]) -> str:
    """Format verification results for the prompt."""
    if not verifications:
        return "No verification results available."
    lines = []
    for v in verifications:
        emoji = {"verified": "✅", "refuted": "❌", "unclear": "⚠️"}.get(
            v.combined_verdict.value, "?"
        )
        lines.append(f"{emoji} [{v.claim_id}] {v.combined_verdict.value.upper()}: {v.claim}")
    return "\n".join(lines)


class Truster:
    """Compares draft vs refined output and selects the winner."""

    def __init__(self, llm: LLMService, blend_enabled: bool = True):
        self.llm = llm
        self.blend_enabled = blend_enabled

    async def trust_and_rank(
        self,
        original_draft: str,
        refined_output: str,
        constraints: list[Constraint],
        verifications: list[VerificationResultV2],
    ) -> TrustResult:
        """Compare draft and refined output, select the best.

        Args:
            original_draft: The original draft response.
            refined_output: The refined response after critique/verify/refine loop.
            constraints: Original constraints.
            verifications: Verification results.

        Returns:
            TrustResult with winner, scores, and final output.
        """
        # If draft and refined are identical, skip comparison
        if original_draft.strip() == refined_output.strip():
            logger.info("Draft and refined are identical, using refined")
            return TrustResult(
                winner="refined",
                reasoning="Draft and refined versions are identical",
                draft_score=75,
                refined_score=75,
                final_output=refined_output,
                blended=False,
            )

        user_prompt = TRUST_USER_PROMPT.format(
            constraints=_format_constraints(constraints),
            draft=original_draft,
            refined=refined_output,
            verifications=_format_verifications(verifications),
        )

        logger.info("Running trust-and-rank comparison")

        try:
            result = await self.llm.generate_with_tools(
                system=TRUST_SYSTEM_PROMPT,
                user=user_prompt,
                tools=TRUST_TOOLS,
                tool_choice={"type": "tool", "name": "submit_trust_decision"},
            )

            if result is None:
                logger.warning("Trust comparison returned None, using refined output")
                return TrustResult(
                    winner="refined",
                    reasoning="Trust comparison failed, defaulting to refined version",
                    draft_score=50,
                    refined_score=60,
                    final_output=refined_output,
                    blended=False,
                )

            # If blending is disabled but model chose blend, fall back to higher score
            winner = result.get("winner", "refined")
            blended = result.get("blended", False)

            if blended and not self.blend_enabled:
                draft_score = result.get("draft_score", 50)
                refined_score = result.get("refined_score", 60)
                winner = "refined" if refined_score >= draft_score else "draft"
                blended = False
                final_output = refined_output if winner == "refined" else original_draft
            else:
                final_output = result.get("final_output", refined_output)

            trust_result = TrustResult(
                winner=winner,
                reasoning=result.get("reasoning", ""),
                draft_score=result.get("draft_score", 50),
                refined_score=result.get("refined_score", 60),
                final_output=final_output,
                blended=blended,
                blend_notes=result.get("blend_notes"),
            )

            logger.info(
                "Trust decision: %s (draft=%d, refined=%d, blended=%s)",
                trust_result.winner,
                trust_result.draft_score,
                trust_result.refined_score,
                trust_result.blended,
            )
            return trust_result

        except Exception as e:
            logger.error("Trust comparison failed: %s", e, exc_info=True)
            return TrustResult(
                winner="refined",
                reasoning=f"Trust comparison failed ({e}), defaulting to refined",
                draft_score=50,
                refined_score=60,
                final_output=refined_output,
                blended=False,
            )
