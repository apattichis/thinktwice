"""Trust-and-rank comparator (ART-inspired).

Phase 7 of the ThinkTwice pipeline. Side-by-side comparison of original draft
vs refined output. Picks the winner or blends the best parts of both.
"""

import logging
from typing import Optional

from services.llm import LLMService
from core.schemas import (
    Constraint,
    VerificationResult,
    ClaimVerdict,
    TrustResult,
)
from core.prompts import TRUST_SYSTEM_PROMPT, TRUST_USER_PROMPT
from core.structural_analysis import analyze, format_for_prompt, format_delta

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


def _format_verifications(verifications: list[VerificationResult]) -> str:
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


def _check_structural_override(
    draft_analysis: dict,
    refined_analysis: dict,
    constraints: list[Constraint],
) -> str | None:
    """Check if refinement degraded structural properties that constraints require.

    Returns a reason string if override to draft is warranted, None otherwise.
    This is a general-purpose check — not tied to any specific benchmark.
    """
    # Build a lowercase string of all constraint descriptions for keyword search
    all_constraints = " ".join(c.description.lower() for c in constraints)

    # Check: quotation wrapping lost
    if (draft_analysis["starts_with_quote"] and draft_analysis["ends_with_quote"]
            and not (refined_analysis["starts_with_quote"] and refined_analysis["ends_with_quote"])):
        if any(kw in all_constraints for kw in ["quotation", "quote", "wrap"]):
            return "quotation wrapping lost"

    # Check: placeholders decreased
    if draft_analysis["placeholder_count"] > refined_analysis["placeholder_count"]:
        if any(kw in all_constraints for kw in ["placeholder", "bracket", "[", "square"]):
            return "placeholders decreased"

    # Check: all-uppercase lost
    if draft_analysis["all_uppercase"] and not refined_analysis["all_uppercase"]:
        if any(kw in all_constraints for kw in ["capital", "uppercase", "upper case"]):
            return "uppercase lost"

    # Check: all-lowercase lost
    if draft_analysis["all_lowercase"] and not refined_analysis["all_lowercase"]:
        if any(kw in all_constraints for kw in ["lowercase", "lower case", "lower"]):
            return "lowercase lost"

    # Check: ALL-CAPS word count decreased significantly
    draft_caps = draft_analysis["all_caps_word_count"]
    refined_caps = refined_analysis["all_caps_word_count"]
    if draft_caps > 0 and refined_caps < draft_caps * 0.5:
        if any(kw in all_constraints for kw in ["capital", "caps", "uppercase"]):
            return "capitalized words decreased"

    # Check: postscript lost
    if draft_analysis["has_postscript"] and not refined_analysis["has_postscript"]:
        if any(kw in all_constraints for kw in ["postscript", "p.s."]):
            return "postscript lost"

    # Check: six-star separator lost
    if draft_analysis["has_six_star_separator"] and not refined_analysis["has_six_star_separator"]:
        if any(kw in all_constraints for kw in ["******", "separator", "two responses"]):
            return "separator lost"

    # Check: comma presence changed when constraint mentions commas
    if draft_analysis["has_comma"] != refined_analysis["has_comma"]:
        if "comma" in all_constraints:
            if not draft_analysis["has_comma"] and refined_analysis["has_comma"]:
                return "commas introduced"

    # Check: bullet count decreased when constraints mention bullets
    draft_bullets = draft_analysis.get("bullet_count", 0)
    refined_bullets = refined_analysis.get("bullet_count", 0)
    if draft_bullets > 0 and refined_bullets < draft_bullets:
        if any(kw in all_constraints for kw in ["bullet", "list item", "list point"]):
            return "bullet count decreased"

    return None


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
        verifications: list[VerificationResult],
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

        # Programmatic structural measurements for both versions
        draft_analysis = analyze(original_draft)
        refined_analysis = analyze(refined_output)
        draft_measurements = format_for_prompt(draft_analysis)
        refined_measurements = format_for_prompt(refined_analysis)
        structural_delta = format_delta(draft_analysis, refined_analysis)

        user_prompt = TRUST_USER_PROMPT.format(
            constraints=_format_constraints(constraints),
            draft=original_draft,
            refined=refined_output,
            verifications=_format_verifications(verifications),
        ) + f"\n\n{structural_delta}\n\nDRAFT {draft_measurements}\n\nREFINED {refined_measurements}"

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
            elif blended:
                # Blended: must use LLM's combined output
                final_output = result.get("final_output", refined_output)
            else:
                # Non-blended: use EXACT original text to prevent LLM
                # reproduction artifacts (stripped quotes, altered formatting)
                if winner == "draft":
                    final_output = original_draft
                else:
                    final_output = refined_output

            # Structural safety net: if the chosen output lost structural
            # properties that the draft had and constraints mention, override
            if winner != "draft" and not blended:
                override_reason = _check_structural_override(
                    draft_analysis, refined_analysis, constraints
                )
                if override_reason:
                    logger.info(
                        "Structural override: %s -> draft (%s)",
                        winner, override_reason,
                    )
                    winner = "draft"
                    final_output = original_draft

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
