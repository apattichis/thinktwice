"""Decomposer module - breaks input into structured constraints (DeCRIM-inspired).

Phase 0 of the ThinkTwice pipeline. Analyzes user input and produces a set of
constraints that a complete response must satisfy.
"""

import logging
from typing import Optional

from services.llm import LLMService
from models.schemas import InputMode
from core.schemas import (
    Constraint,
    ConstraintType,
    ConstraintPriority,
    DecomposeResult,
)
from core.prompts import DECOMPOSE_SYSTEM_PROMPT, DECOMPOSE_MODE_PROMPTS

logger = logging.getLogger(__name__)

DECOMPOSE_TOOLS = [
    {
        "name": "submit_decomposition",
        "description": "Submit the structured decomposition of the user's input into constraints",
        "input_schema": {
            "type": "object",
            "properties": {
                "main_task": {
                    "type": "string",
                    "description": "A one-sentence summary of what the user is asking for",
                },
                "constraints": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Unique ID like C1, C2, C3...",
                            },
                            "type": {
                                "type": "string",
                                "enum": ["content", "reasoning", "accuracy", "format", "tone"],
                            },
                            "description": {"type": "string"},
                            "priority": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                            },
                            "verifiable": {"type": "boolean"},
                        },
                        "required": ["id", "type", "description", "priority", "verifiable"],
                    },
                },
                "implicit_constraints": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Constraints the user didn't state but would expect",
                },
                "difficulty_estimate": {
                    "type": "string",
                    "enum": ["easy", "medium", "hard"],
                },
            },
            "required": ["main_task", "constraints", "implicit_constraints", "difficulty_estimate"],
        },
    }
]


class Decomposer:
    """Decomposes user input into structured constraints."""

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def decompose(
        self,
        input_text: str,
        mode: InputMode,
        scraped_content: Optional[str] = None,
    ) -> DecomposeResult:
        """Decompose input into constraints using Claude tool use.

        Args:
            input_text: The user's original input.
            mode: Input mode (question, claim, url).
            scraped_content: Extracted article content for URL mode.

        Returns:
            DecomposeResult with main_task, constraints, implicit_constraints,
            and difficulty_estimate.
        """
        # Build mode-specific user prompt
        mode_key = mode.value
        template = DECOMPOSE_MODE_PROMPTS.get(mode_key, DECOMPOSE_MODE_PROMPTS["question"])

        format_kwargs = {"input_text": input_text}
        if scraped_content:
            format_kwargs["scraped_content"] = scraped_content

        user_message = template.format(**format_kwargs)

        logger.info("Decomposing input (mode=%s, length=%d)", mode.value, len(input_text))

        try:
            result = await self.llm.generate_with_tools(
                system=DECOMPOSE_SYSTEM_PROMPT,
                user=user_message,
                tools=DECOMPOSE_TOOLS,
                tool_choice={"type": "tool", "name": "submit_decomposition"},
            )

            if result is None:
                logger.warning("Decomposition tool call returned None, using fallback")
                return self._fallback_result(input_text)

            # Parse constraints
            constraints = []
            for c in result.get("constraints", []):
                try:
                    constraints.append(
                        Constraint(
                            id=c["id"],
                            type=ConstraintType(c["type"]),
                            description=c["description"],
                            priority=ConstraintPriority(c["priority"]),
                            verifiable=c.get("verifiable", True),
                        )
                    )
                except (KeyError, ValueError) as e:
                    logger.warning("Skipping malformed constraint: %s", e)
                    continue

            if not constraints:
                logger.warning("No valid constraints parsed, using fallback")
                return self._fallback_result(input_text)

            decompose_result = DecomposeResult(
                main_task=result.get("main_task", input_text[:200]),
                constraints=constraints,
                implicit_constraints=result.get("implicit_constraints", []),
                difficulty_estimate=result.get("difficulty_estimate", "medium"),
            )

            logger.info(
                "Decomposed into %d constraints (difficulty=%s)",
                len(constraints),
                decompose_result.difficulty_estimate,
            )
            return decompose_result

        except Exception as e:
            logger.error("Decomposition failed: %s", e, exc_info=True)
            return self._fallback_result(input_text)

    def _fallback_result(self, input_text: str) -> DecomposeResult:
        """Return a minimal fallback decomposition."""
        return DecomposeResult(
            main_task=input_text[:200],
            constraints=[
                Constraint(
                    id="C1",
                    type=ConstraintType.ACCURACY,
                    description="Respond accurately and completely to the user's input",
                    priority=ConstraintPriority.HIGH,
                    verifiable=True,
                ),
                Constraint(
                    id="C2",
                    type=ConstraintType.CONTENT,
                    description="Address all aspects of the user's query",
                    priority=ConstraintPriority.HIGH,
                    verifiable=True,
                ),
            ],
            implicit_constraints=["Response should be factually accurate"],
            difficulty_estimate="medium",
        )
