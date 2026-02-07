"""Convergence checker - iterative loop control (ReVISE-inspired).

Phase 6 of the ThinkTwice pipeline. Lightweight constraint re-check to determine
whether the refinement loop should continue or has converged.
"""

import logging

from services.llm import LLMService
from core.schemas import (
    Constraint,
    ConstraintPriority,
    ConvergenceDecision,
    ConvergenceResult,
)
from core.prompts import CONVERGENCE_SYSTEM_PROMPT, CONVERGENCE_USER_PROMPT
from core.structural_analysis import analyze, format_for_prompt

logger = logging.getLogger(__name__)

CONVERGENCE_TOOLS = [
    {
        "name": "submit_convergence",
        "description": "Submit convergence evaluation",
        "input_schema": {
            "type": "object",
            "properties": {
                "constraint_checks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "constraint_id": {"type": "string"},
                            "satisfied": {"type": "boolean"},
                            "confidence": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": ["constraint_id", "satisfied", "confidence"],
                    },
                },
                "decision": {
                    "type": "string",
                    "enum": ["converged", "continue", "max_iterations_reached"],
                },
                "overall_confidence": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                },
            },
            "required": ["constraint_checks", "decision", "overall_confidence"],
        },
    }
]


def _format_constraints(constraints: list[Constraint]) -> str:
    """Format constraints for prompt insertion."""
    lines = []
    for c in constraints:
        lines.append(
            f"[{c.id}] ({c.priority.value.upper()}) {c.description}"
        )
    return "\n".join(lines)


class ConvergenceChecker:
    """Lightweight constraint re-check for loop control."""

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def check_convergence(
        self,
        refined: str,
        constraints: list[Constraint],
        iteration: int,
        max_iterations: int,
        threshold: int,
    ) -> ConvergenceResult:
        """Check whether the refined response has converged.

        Args:
            refined: The current refined response.
            constraints: Original constraints to check against.
            iteration: Current iteration number.
            max_iterations: Maximum allowed iterations.
            threshold: Confidence threshold for convergence.

        Returns:
            ConvergenceResult with decision and details.
        """
        # Force max iterations check
        if iteration >= max_iterations:
            logger.info("Max iterations reached (%d/%d)", iteration, max_iterations)
            # Still run the check to get counts, but override decision
            force_max = True
        else:
            force_max = False

        # Programmatic structural measurements (LLMs can't count reliably)
        structural_measurements = format_for_prompt(analyze(refined))

        system_prompt = CONVERGENCE_SYSTEM_PROMPT.format(
            threshold=threshold,
            iteration=iteration,
            max_iterations=max_iterations,
        )

        user_prompt = CONVERGENCE_USER_PROMPT.format(
            constraints=_format_constraints(constraints),
            refined=refined,
            iteration=iteration,
            max_iterations=max_iterations,
        ) + f"\n\n{structural_measurements}"

        logger.info(
            "Checking convergence (iteration=%d/%d, threshold=%d)",
            iteration,
            max_iterations,
            threshold,
        )

        try:
            result = await self.llm.generate_with_tools(
                system=system_prompt,
                user=user_prompt,
                tools=CONVERGENCE_TOOLS,
                tool_choice={"type": "tool", "name": "submit_convergence"},
            )

            if result is None:
                logger.warning("Convergence check returned None, exiting loop")
                return ConvergenceResult(
                    decision=ConvergenceDecision.CONVERGED,
                    satisfied_count=0,
                    total_count=len(constraints),
                    confidence=0,
                    unsatisfied_constraints=[],
                )

            # Parse checks
            checks = result.get("constraint_checks", [])
            satisfied = [c for c in checks if c.get("satisfied", False)]
            unsatisfied = [
                c["constraint_id"] for c in checks if not c.get("satisfied", False)
            ]
            overall_confidence = result.get("overall_confidence", 0)

            # Determine decision
            if force_max:
                decision = ConvergenceDecision.MAX_ITERATIONS
            else:
                raw_decision = result.get("decision", "continue")
                try:
                    decision = ConvergenceDecision(raw_decision)
                except ValueError:
                    decision = ConvergenceDecision.CONTINUE

                # Override: check our own thresholds
                high_priority_ids = {
                    c.id for c in constraints if c.priority == ConstraintPriority.HIGH
                }
                high_unsatisfied = [uid for uid in unsatisfied if uid in high_priority_ids]

                if not high_unsatisfied and overall_confidence >= threshold:
                    decision = ConvergenceDecision.CONVERGED
                elif high_unsatisfied:
                    decision = ConvergenceDecision.CONTINUE

            convergence_result = ConvergenceResult(
                decision=decision,
                satisfied_count=len(satisfied),
                total_count=len(checks),
                confidence=overall_confidence,
                unsatisfied_constraints=unsatisfied,
            )

            logger.info(
                "Convergence: %s (%d/%d satisfied, confidence=%d)",
                decision.value,
                len(satisfied),
                len(checks),
                overall_confidence,
            )
            return convergence_result

        except Exception as e:
            logger.error("Convergence check failed: %s", e, exc_info=True)
            return ConvergenceResult(
                decision=ConvergenceDecision.CONVERGED,
                satisfied_count=0,
                total_count=len(constraints),
                confidence=0,
                unsatisfied_constraints=[],
            )
