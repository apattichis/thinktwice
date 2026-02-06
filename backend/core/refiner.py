"""Refiner module - selective/surgical refinement (ART + DeCRIM).

Phase 5 of the v2 pipeline. Makes targeted changes based on per-constraint
evaluations and claim verifications. Preserves strengths, fixes violations,
acknowledges limitations.

Maintains backward compatibility with v1 produce/stream interface.
"""

import logging
from typing import Optional

from services.llm import LLMService
from models.schemas import InputMode, Critique, VerificationResult, RefinedResponse
from core.schemas import (
    Constraint,
    ConstraintEvaluation,
    ConstraintVerdict,
    CritiqueResult,
    VerificationResultV2,
    ClaimVerdict,
    ChangeRecord,
    RefineResult,
)
from core.prompts import SELECTIVE_REFINE_SYSTEM_PROMPT, SELECTIVE_REFINE_USER_PROMPT

logger = logging.getLogger(__name__)

# V1 refine tools (kept for backward compatibility)
REFINER_TOOLS_V1 = [
    {
        "name": "submit_refined_response",
        "description": "Submit the refined response with metadata",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
                "changes_made": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["content", "confidence", "changes_made"],
        },
    }
]

# V2 selective refine tools
REFINER_TOOLS_V2 = [
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

REFINER_V1_SYSTEM_PROMPT = """You are a careful editor producing the final, refined response.

You have access to:
1. The original user input
2. The initial draft response
3. A critique identifying issues and strengths
4. Verification results for factual claims

Your job is to produce an improved response that:
- Fixes all issues identified in the critique
- Preserves the strengths noted in the critique
- Incorporates the verification results
- Maintains a helpful, clear tone

Use the submit_refined_response tool to provide your output."""


def _build_preserve_fix_acknowledge(
    critique: CritiqueResult,
    verifications: list[VerificationResultV2],
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
                f"- [Claim {v.claim_id}] REFUTED: '{v.claim}' — {v.web_explanation}"
            )

    # ACKNOWLEDGE: unclear claims
    ack_lines = []
    for v in verifications:
        if v.combined_verdict == ClaimVerdict.UNCLEAR:
            ack_lines.append(
                f"- [Claim {v.claim_id}] UNCLEAR: '{v.claim}' — cannot be confirmed"
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


def _format_verifications_v2(verifications: list[VerificationResultV2]) -> str:
    """Format v2 verification results for the prompt."""
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
        lines.append(f"  Web: {v.web_verdict.value} — {v.web_explanation}")
        if v.self_verdict:
            lines.append(f"  Self: {v.self_verdict.value} — {v.self_derivation or ''}")
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
        verifications: list[VerificationResultV2],
        constraints: list[Constraint],
    ) -> RefineResult:
        """V2 selective refinement.

        Makes targeted changes based on per-constraint evaluations and
        claim verifications. Preserves strengths, fixes violations.

        Args:
            draft: Current draft to refine.
            critique: Per-constraint critique result.
            verifications: Dual verification results.
            constraints: Original constraints.

        Returns:
            RefineResult with refined response and change records.
        """
        strengths, fixes, acknowledge = _build_preserve_fix_acknowledge(
            critique, verifications
        )

        system_prompt = SELECTIVE_REFINE_SYSTEM_PROMPT.format(
            strengths=strengths,
            fixes=fixes,
            acknowledge=acknowledge,
        )

        user_prompt = SELECTIVE_REFINE_USER_PROMPT.format(
            draft=draft,
            constraint_evaluations=_format_constraint_evaluations(
                critique.constraint_evaluations
            ),
            verification_results=_format_verifications_v2(verifications),
            constraints=_format_constraints(constraints),
        )

        logger.info("Running selective refinement")

        try:
            result = await self.llm.generate_with_tools(
                system=system_prompt,
                user=user_prompt,
                tools=REFINER_TOOLS_V2,
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

    # ---- V1 backward compatibility ----

    def _format_critique(self, critique: Critique) -> str:
        """Format v1 critique for the prompt."""
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
        """Format v1 verification results for the prompt."""
        if not results:
            return "## Verification Results\nNo claims were verified."
        lines = ["## Verification Results"]
        for r in results:
            emoji = {"verified": "✅", "refuted": "❌", "unclear": "⚠️"}.get(r.verdict, "?")
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
        """V1-compatible: produce refined response."""
        user_message = f"""## Original Input
Mode: {mode.value}
{user_input}

## Initial Draft
{draft}

{self._format_critique(critique)}

{self._format_verifications(verification_results)}

---

Now produce an improved, refined response. Use the submit_refined_response tool."""

        result = await self.llm.generate_with_tools(
            system=REFINER_V1_SYSTEM_PROMPT,
            user=user_message,
            tools=REFINER_TOOLS_V1,
            tool_choice={"type": "tool", "name": "submit_refined_response"},
        )

        if result is None:
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
        """V1-compatible: stream the refined response."""
        user_message = f"""## Original Input
Mode: {mode.value}
{user_input}

## Initial Draft
{draft}

{self._format_critique(critique)}

{self._format_verifications(verification_results)}

---

Write an improved, refined response."""

        async for token in self.llm.stream(system=REFINER_V1_SYSTEM_PROMPT, user=user_message):
            yield token
