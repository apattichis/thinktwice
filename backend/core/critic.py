"""Critic module - per-constraint evaluation (DeCRIM-inspired).

Phase 3 of the ThinkTwice pipeline. Evaluates a draft against each constraint,
identifies violations, and extracts verifiable claims.
"""

import logging
from typing import Optional

from services.llm import LLMService
from core.schemas import (
    Constraint,
    ConstraintEvaluation,
    ConstraintVerdict,
    ClaimToVerify,
    CritiqueResult,
)
from core.prompts import CRITIQUE_SYSTEM_PROMPT, CRITIQUE_USER_PROMPT
from core.structural_analysis import analyze, format_for_prompt

logger = logging.getLogger(__name__)

# Critique tools with per-constraint evaluation
CRITIC_TOOLS = [
    {
        "name": "submit_critique",
        "description": "Submit per-constraint evaluation and extracted claims",
        "input_schema": {
            "type": "object",
            "properties": {
                "constraint_evaluations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "constraint_id": {"type": "string"},
                            "verdict": {
                                "type": "string",
                                "enum": ["satisfied", "partially_satisfied", "violated"],
                            },
                            "confidence": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "feedback": {"type": "string"},
                            "evidence_quote": {
                                "type": "string",
                                "description": "Exact text from the draft supporting this verdict",
                            },
                        },
                        "required": ["constraint_id", "verdict", "confidence"],
                    },
                },
                "claims_to_verify": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "V1, V2, V3..."},
                            "claim": {"type": "string"},
                            "source_constraint": {"type": "string"},
                            "source_quote": {"type": "string"},
                        },
                        "required": ["id", "claim", "source_constraint", "source_quote"],
                    },
                },
                "overall_confidence": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                },
                "strengths_to_preserve": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": [
                "constraint_evaluations",
                "claims_to_verify",
                "overall_confidence",
                "strengths_to_preserve",
            ],
        },
    }
]


def _format_constraints(constraints: list[Constraint]) -> str:
    """Format constraints for prompt insertion."""
    lines = []
    for c in constraints:
        lines.append(
            f"[{c.id}] ({c.priority.value.upper()}) [{c.type.value}] {c.description}"
        )
    return "\n".join(lines)


class Critic:
    """Analyzes draft response with per-constraint evaluation."""

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def critique(
        self,
        draft: str,
        constraints: list[Constraint],
        failing_constraints: list[str],
        input_text: str = "",
    ) -> CritiqueResult:
        """Per-constraint critique.

        Args:
            draft: The draft response to evaluate.
            constraints: List of constraints to evaluate against.
            failing_constraints: Constraint IDs that failed the gate check.
            input_text: Original user input.

        Returns:
            CritiqueResult with per-constraint evaluations and claims to verify.
        """
        failing_str = ", ".join(failing_constraints) if failing_constraints else "None"

        # Programmatic structural measurements (LLMs can't count reliably)
        structural_measurements = format_for_prompt(analyze(draft))

        system_prompt = CRITIQUE_SYSTEM_PROMPT.format(
            failing_constraints=failing_str,
        )

        user_prompt = CRITIQUE_USER_PROMPT.format(
            constraints=_format_constraints(constraints),
            draft=draft,
            input_text=input_text,
        ) + f"\n\n{structural_measurements}"

        logger.info(
            "Running critique on %d constraints (%d failing)",
            len(constraints),
            len(failing_constraints),
        )

        try:
            result = await self.llm.generate_with_tools(
                system=system_prompt,
                user=user_prompt,
                tools=CRITIC_TOOLS,
                tool_choice={"type": "tool", "name": "submit_critique"},
            )

            if result is None:
                logger.warning("Critique tool call returned None, using fallback")
                return self._fallback_critique(constraints)

            # Parse constraint evaluations
            evaluations = []
            for ev in result.get("constraint_evaluations", []):
                try:
                    evaluations.append(
                        ConstraintEvaluation(
                            constraint_id=ev["constraint_id"],
                            verdict=ConstraintVerdict(ev["verdict"]),
                            confidence=ev.get("confidence", 50),
                            feedback=ev.get("feedback"),
                            evidence_quote=ev.get("evidence_quote"),
                        )
                    )
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning("Skipping malformed evaluation: %s", e)

            # Parse claims to verify
            claims = []
            for cl in result.get("claims_to_verify", []):
                try:
                    claims.append(
                        ClaimToVerify(
                            id=cl["id"],
                            claim=cl["claim"],
                            source_constraint=cl.get("source_constraint", ""),
                            source_quote=cl.get("source_quote", ""),
                        )
                    )
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning("Skipping malformed claim: %s", e)

            critique_result = CritiqueResult(
                constraint_evaluations=evaluations,
                claims_to_verify=claims,
                overall_confidence=result.get("overall_confidence", 50),
                strengths_to_preserve=result.get("strengths_to_preserve", []),
            )

            logger.info(
                "Critique complete: %d evaluations, %d claims, confidence=%d",
                len(evaluations),
                len(claims),
                critique_result.overall_confidence,
            )
            return critique_result

        except Exception as e:
            logger.error("Critique failed: %s", e, exc_info=True)
            return self._fallback_critique(constraints)

    def _fallback_critique(self, constraints: list[Constraint]) -> CritiqueResult:
        """Return a fallback critique that passes everything with low confidence."""
        return CritiqueResult(
            constraint_evaluations=[
                ConstraintEvaluation(
                    constraint_id=c.id,
                    verdict=ConstraintVerdict.PARTIALLY_SATISFIED,
                    confidence=30,
                    feedback="Unable to evaluate -- critique step failed",
                )
                for c in constraints
            ],
            claims_to_verify=[],
            overall_confidence=30,
            strengths_to_preserve=[],
        )
