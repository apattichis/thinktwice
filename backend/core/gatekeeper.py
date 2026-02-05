"""Gatekeeper module - ask-and-gate mechanism (ART-inspired).

Phase 2 of the v2 pipeline. Generates diagnostic sub-questions per constraint,
evaluates the draft against them, and decides whether refinement is needed.
"""

import logging
from typing import Optional

from services.llm import LLMService
from core.schemas import Constraint, ConstraintPriority, SubQuestion, GateResult
from core.prompts import GATE_SYSTEM_PROMPT, GATE_USER_PROMPT

logger = logging.getLogger(__name__)

GATE_TOOLS = [
    {
        "name": "submit_gate_result",
        "description": "Submit the gate evaluation with sub-questions and decision",
        "input_schema": {
            "type": "object",
            "properties": {
                "sub_questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "constraint_id": {"type": "string"},
                            "question": {
                                "type": "string",
                                "description": "A diagnostic question that tests whether the draft satisfies this constraint",
                            },
                            "answer": {
                                "type": "string",
                                "description": "The answer based on examining the draft",
                            },
                            "passed": {
                                "type": "boolean",
                                "description": "Whether the draft passes this check",
                            },
                        },
                        "required": ["constraint_id", "question", "answer", "passed"],
                    },
                },
                "gate_decision": {
                    "type": "string",
                    "enum": ["skip", "refine"],
                    "description": "Whether to skip refinement or proceed with it",
                },
                "gate_confidence": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Overall confidence in the draft quality",
                },
                "failing_constraints": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "IDs of constraints that failed the gate check",
                },
            },
            "required": ["sub_questions", "gate_decision", "gate_confidence", "failing_constraints"],
        },
    }
]


def _format_constraints(constraints: list[Constraint]) -> str:
    """Format constraints for prompt insertion."""
    lines = []
    for c in constraints:
        lines.append(
            f"[{c.id}] ({c.priority.value.upper()}) [{c.type.value}] {c.description}"
            f" {'(verifiable)' if c.verifiable else '(subjective)'}"
        )
    return "\n".join(lines)


class Gatekeeper:
    """Evaluates draft quality and decides whether refinement is needed."""

    def __init__(self, llm: LLMService, gate_threshold: int = 85, gate_min_pass_rate: float = 1.0):
        self.llm = llm
        self.gate_threshold = gate_threshold
        self.gate_min_pass_rate = gate_min_pass_rate

    async def gate(
        self,
        draft: str,
        constraints: list[Constraint],
        mode: str,
    ) -> GateResult:
        """Evaluate the draft against constraints and decide on refinement.

        Args:
            draft: The draft response to evaluate.
            constraints: List of constraints to check against.
            mode: Input mode (question, claim, url).

        Returns:
            GateResult with sub-questions, decision, confidence, and failing constraints.
        """
        # Only evaluate high and medium priority constraints
        eval_constraints = [
            c for c in constraints if c.priority in (ConstraintPriority.HIGH, ConstraintPriority.MEDIUM)
        ]

        if not eval_constraints:
            eval_constraints = constraints

        system_prompt = GATE_SYSTEM_PROMPT.format(
            gate_threshold=self.gate_threshold,
            gate_min_pass_pct=int(self.gate_min_pass_rate * 100),
        )

        user_prompt = GATE_USER_PROMPT.format(
            constraints=_format_constraints(eval_constraints),
            draft=draft,
        )

        logger.info(
            "Running gate check on %d constraints (threshold=%d, min_pass=%.0f%%)",
            len(eval_constraints),
            self.gate_threshold,
            self.gate_min_pass_rate * 100,
        )

        try:
            result = await self.llm.generate_with_tools(
                system=system_prompt,
                user=user_prompt,
                tools=GATE_TOOLS,
                tool_choice={"type": "tool", "name": "submit_gate_result"},
            )

            if result is None:
                logger.warning("Gate tool call returned None, defaulting to 'refine'")
                return self._fallback_result(constraints)

            # Parse sub-questions
            sub_questions = []
            for sq in result.get("sub_questions", []):
                try:
                    sub_questions.append(
                        SubQuestion(
                            constraint_id=sq["constraint_id"],
                            question=sq["question"],
                            answer=sq["answer"],
                            passed=sq["passed"],
                        )
                    )
                except (KeyError, ValueError) as e:
                    logger.warning("Skipping malformed sub-question: %s", e)

            # Validate gate decision against our thresholds
            raw_decision = result.get("gate_decision", "refine")
            raw_confidence = result.get("gate_confidence", 0)
            failing = result.get("failing_constraints", [])

            # Enforce our own gate logic
            if sub_questions:
                passed_count = sum(1 for sq in sub_questions if sq.passed)
                total_count = len(sub_questions)
                pass_rate = passed_count / total_count if total_count > 0 else 0

                high_priority_ids = {c.id for c in constraints if c.priority == ConstraintPriority.HIGH}
                high_failed = any(
                    sq.constraint_id in high_priority_ids and not sq.passed
                    for sq in sub_questions
                )

                # Override decision if thresholds not met
                if high_failed or pass_rate < self.gate_min_pass_rate or raw_confidence < self.gate_threshold:
                    raw_decision = "refine"

                # Rebuild failing constraints from sub-questions
                if not failing:
                    failing = [sq.constraint_id for sq in sub_questions if not sq.passed]

            gate_result = GateResult(
                sub_questions=sub_questions,
                gate_decision=raw_decision,
                gate_confidence=raw_confidence,
                failing_constraints=failing,
            )

            logger.info(
                "Gate decision: %s (confidence=%d, failing=%d)",
                gate_result.gate_decision,
                gate_result.gate_confidence,
                len(gate_result.failing_constraints),
            )
            return gate_result

        except Exception as e:
            logger.error("Gate check failed: %s", e, exc_info=True)
            return self._fallback_result(constraints)

    def _fallback_result(self, constraints: list[Constraint]) -> GateResult:
        """Return a fallback result that triggers refinement."""
        return GateResult(
            sub_questions=[],
            gate_decision="refine",
            gate_confidence=0,
            failing_constraints=[c.id for c in constraints],
        )
