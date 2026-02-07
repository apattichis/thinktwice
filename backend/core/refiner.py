"""Refiner module - selective/surgical refinement (ART + DeCRIM).

Phase 5 of the ThinkTwice pipeline. Makes targeted changes based on per-constraint
evaluations and claim verifications. Preserves strengths, fixes violations,
acknowledges limitations.
"""

import logging

from services.llm import LLMService
from core.schemas import (
    Constraint,
    ConstraintEvaluation,
    ConstraintVerdict,
    CritiqueResult,
    VerificationResult,
    ClaimVerdict,
    ChangeRecord,
    RefineResult,
)
from core.prompts import (
    SELECTIVE_REFINE_SYSTEM_PROMPT,
    SELECTIVE_REFINE_USER_PROMPT,
    SELECTIVE_REFINE_VERDICT_SECTION,
    SELECTIVE_REFINE_NO_VERDICT_SECTION,
)
from core.structural_analysis import analyze, format_for_prompt

logger = logging.getLogger(__name__)

# Selective refine tools
REFINER_TOOLS = [
    {
        "name": "submit_refinement",
        "description": "Submit the surgically refined response with change records",
        "input_schema": {
            "type": "object",
            "properties": {
                "refined_response": {
                    "type": "string",
                    "description": "The refined response text",
                },
                "changes_made": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "target_id": {
                                "type": "string",
                                "description": "The constraint_id or claim_id this change addresses",
                            },
                            "change": {
                                "type": "string",
                                "description": "Description of what was changed",
                            },
                            "type": {
                                "type": "string",
                                "enum": [
                                    "content_addition",
                                    "factual_correction",
                                    "language_softening",
                                    "removal",
                                    "restructure",
                                    "source_addition",
                                ],
                            },
                        },
                        "required": ["target_id", "change", "type"],
                    },
                },
                "confidence_after": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                },
            },
            "required": ["refined_response", "changes_made", "confidence_after"],
        },
    }
]


def _build_preserve_fix_acknowledge(
    critique: CritiqueResult,
    verifications: list[VerificationResult],
) -> tuple[str, str, str]:
    """Build PRESERVE/FIX/ACKNOWLEDGE sections from critique + verifications."""
    # PRESERVE: strengths + satisfied constraints
    preserve_lines = []
    for s in critique.strengths_to_preserve:
        preserve_lines.append(f"- {s}")
    for ev in critique.constraint_evaluations:
        if ev.verdict == ConstraintVerdict.SATISFIED:
            preserve_lines.append(f"- Constraint {ev.constraint_id} is already satisfied")

    # FIX: violated constraints + refuted claims
    fix_lines = []
    for ev in critique.constraint_evaluations:
        if ev.verdict == ConstraintVerdict.VIOLATED:
            fix_lines.append(
                f"- [{ev.constraint_id}] VIOLATED: {ev.feedback or 'No details'}"
            )
        elif ev.verdict == ConstraintVerdict.PARTIALLY_SATISFIED:
            fix_lines.append(
                f"- [{ev.constraint_id}] PARTIAL: {ev.feedback or 'Needs improvement'}"
            )
    for v in verifications:
        if v.combined_verdict == ClaimVerdict.REFUTED:
            fix_lines.append(
                f"- [Claim {v.claim_id}] REFUTED: '{v.claim}' -- {v.web_explanation}"
            )

    # ACKNOWLEDGE: unclear claims
    ack_lines = []
    for v in verifications:
        if v.combined_verdict == ClaimVerdict.UNCLEAR:
            ack_lines.append(
                f"- [Claim {v.claim_id}] UNCLEAR: '{v.claim}' -- cannot be confirmed"
            )

    return (
        "\n".join(preserve_lines) or "None identified",
        "\n".join(fix_lines) or "No fixes needed",
        "\n".join(ack_lines) or "None",
    )


def _format_constraints(constraints: list[Constraint]) -> str:
    """Format constraints for prompt insertion."""
    lines = []
    for c in constraints:
        lines.append(f"[{c.id}] ({c.priority.value.upper()}) {c.description}")
    return "\n".join(lines)


def _format_constraint_evaluations(evaluations: list[ConstraintEvaluation]) -> str:
    """Format constraint evaluations for the prompt."""
    lines = []
    for ev in evaluations:
        lines.append(
            f"[{ev.constraint_id}] {ev.verdict.value.upper()} (confidence: {ev.confidence}%)"
        )
        if ev.feedback:
            lines.append(f"  Feedback: {ev.feedback}")
        if ev.evidence_quote:
            lines.append(f'  Evidence: "{ev.evidence_quote}"')
    return "\n".join(lines)


def _format_verifications(verifications: list[VerificationResult]) -> str:
    """Format verification results for the prompt."""
    if not verifications:
        return "No claims were verified."
    verified = sum(1 for v in verifications if v.combined_verdict.value == "verified")
    refuted = sum(1 for v in verifications if v.combined_verdict.value == "refuted")
    unclear = sum(1 for v in verifications if v.combined_verdict.value == "unclear")
    lines = [f"SUMMARY: {verified} verified, {refuted} refuted, {unclear} unclear out of {len(verifications)} claims\n"]
    for v in verifications:
        emoji = {"verified": "✅", "refuted": "❌", "unclear": "⚠️"}.get(
            v.combined_verdict.value, "?"
        )
        lines.append(f"{emoji} [{v.claim_id}] {v.combined_verdict.value.upper()}: {v.claim}")
        lines.append(f"  Web: {v.web_verdict.value} -- {v.web_explanation}")
        if v.self_verdict:
            lines.append(f"  Self: {v.self_verdict.value} -- {v.self_derivation or ''}")
        lines.append(f"  Combined confidence: {v.combined_confidence}%")
    return "\n".join(lines)


class Refiner:
    """Produces refined responses through selective/surgical editing."""

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def selective_refine(
        self,
        draft: str,
        critique: CritiqueResult,
        verifications: list[VerificationResult],
        constraints: list[Constraint],
        mode: str = "claim",
    ) -> RefineResult:
        """Selective refinement.

        Makes targeted changes based on per-constraint evaluations and
        claim verifications. Preserves strengths, fixes violations.

        Args:
            draft: Current draft to refine.
            critique: Per-constraint critique result.
            verifications: Dual verification results.
            constraints: Original constraints.
            mode: Input mode (claim/question/url) — controls verdict section.

        Returns:
            RefineResult with refined response and change records.
        """
        strengths, fixes, acknowledge = _build_preserve_fix_acknowledge(
            critique, verifications
        )

        # Only include verdict instructions for claim mode
        verdict_section = SELECTIVE_REFINE_VERDICT_SECTION if mode == "claim" else SELECTIVE_REFINE_NO_VERDICT_SECTION

        system_prompt = SELECTIVE_REFINE_SYSTEM_PROMPT.format(
            strengths=strengths,
            fixes=fixes,
            acknowledge=acknowledge,
            verdict_section=verdict_section,
        )

        # Programmatic structural measurements (LLMs can't count reliably)
        structural_measurements = format_for_prompt(analyze(draft))

        user_prompt = SELECTIVE_REFINE_USER_PROMPT.format(
            draft=draft,
            constraint_evaluations=_format_constraint_evaluations(
                critique.constraint_evaluations
            ),
            verification_results=_format_verifications(verifications),
            constraints=_format_constraints(constraints),
        ) + f"\n\n{structural_measurements}"

        logger.info("Running selective refinement")

        try:
            result = await self.llm.generate_with_tools(
                system=system_prompt,
                user=user_prompt,
                tools=REFINER_TOOLS,
                tool_choice={"type": "tool", "name": "submit_refinement"},
            )

            if result is None:
                logger.warning("Refinement tool call returned None, using draft as-is")
                return RefineResult(
                    refined_response=draft,
                    changes_made=[],
                    confidence_after=critique.overall_confidence,
                )

            changes = []
            for ch in result.get("changes_made", []):
                try:
                    changes.append(
                        ChangeRecord(
                            target_id=ch.get("target_id", "unknown"),
                            change=ch.get("change", ""),
                            type=ch.get("type", "content_addition"),
                        )
                    )
                except (KeyError, ValueError) as e:
                    logger.warning("Skipping malformed change record: %s", e)

            refine_result = RefineResult(
                refined_response=result.get("refined_response", draft),
                changes_made=changes,
                confidence_after=result.get("confidence_after", critique.overall_confidence),
            )

            logger.info(
                "Refinement complete: %d changes, confidence=%d",
                len(changes),
                refine_result.confidence_after,
            )
            return refine_result

        except Exception as e:
            logger.error("Refinement failed: %s", e, exc_info=True)
            return RefineResult(
                refined_response=draft,
                changes_made=[],
                confidence_after=critique.overall_confidence,
            )
