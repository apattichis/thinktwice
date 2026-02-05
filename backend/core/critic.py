"""Critic module - per-constraint evaluation (DeCRIM-inspired).

Phase 3 of the v2 pipeline. Evaluates a draft against each constraint,
identifies violations, and extracts verifiable claims.

Also maintains backward compatibility with v1 critique interface.
"""

import logging
from typing import Optional

from services.llm import LLMService
from models.schemas import InputMode, Critique, CritiqueIssue
from core.schemas import (
    Constraint,
    ConstraintEvaluation,
    ConstraintVerdict,
    ClaimToVerify,
    CritiqueResult,
)
from core.prompts import CRITIQUE_SYSTEM_PROMPT, CRITIQUE_USER_PROMPT

logger = logging.getLogger(__name__)

# V1 critique tools (kept for backward compatibility)
CRITIC_TOOLS_V1 = [
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
                    "description": "Specific factual claims that should be checked",
                },
                "confidence": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                },
            },
            "required": ["issues", "strengths", "claims_to_verify", "confidence"],
        },
    }
]

# V2 critique tools with per-constraint evaluation
CRITIC_TOOLS_V2 = [
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

CRITIC_V1_SYSTEM_PROMPT = """You are a rigorous, adversarial critic. Your job is to find EVERYTHING wrong
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
checkable statements — not vague topics.

Be thorough. Be harsh. The next step will verify your claims against real sources.
You MUST use the submit_critique tool to provide your analysis."""


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

    async def analyze(
        self, user_input: str, draft: str, mode: InputMode
    ) -> Critique:
        """V1-compatible critique interface.

        Returns the v1 Critique model for backward compatibility.
        """
        user_message = f"""Original input: {user_input}

Mode: {mode.value}

Draft response to critique:
{draft}

Analyze this draft thoroughly and use the submit_critique tool to provide your structured critique."""

        result = await self.llm.generate_with_tools(
            system=CRITIC_V1_SYSTEM_PROMPT,
            user=user_message,
            tools=CRITIC_TOOLS_V1,
            tool_choice={"type": "tool", "name": "submit_critique"},
        )

        if result is None:
            return Critique(
                issues=[],
                strengths=["Draft appears reasonable"],
                claims_to_verify=[],
                confidence=50,
            )

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

    async def critique(
        self,
        draft: str,
        constraints: list[Constraint],
        failing_constraints: list[str],
        input_text: str = "",
        mode: str = "question",
    ) -> CritiqueResult:
        """V2 per-constraint critique.

        Args:
            draft: The draft response to evaluate.
            constraints: List of constraints to evaluate against.
            failing_constraints: Constraint IDs that failed the gate check.
            input_text: Original user input.
            mode: Input mode string.

        Returns:
            CritiqueResult with per-constraint evaluations and claims to verify.
        """
        failing_str = ", ".join(failing_constraints) if failing_constraints else "None"

        system_prompt = CRITIQUE_SYSTEM_PROMPT.format(
            failing_constraints=failing_str,
        )

        user_prompt = CRITIQUE_USER_PROMPT.format(
            constraints=_format_constraints(constraints),
            draft=draft,
            input_text=input_text,
            mode=mode,
        )

        logger.info(
            "Running v2 critique on %d constraints (%d failing)",
            len(constraints),
            len(failing_constraints),
        )

        try:
            result = await self.llm.generate_with_tools(
                system=system_prompt,
                user=user_prompt,
                tools=CRITIC_TOOLS_V2,
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
                except (KeyError, ValueError) as e:
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
                except (KeyError, ValueError) as e:
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
                    feedback="Unable to evaluate — critique step failed",
                )
                for c in constraints
            ],
            claims_to_verify=[],
            overall_confidence=30,
            strengths_to_preserve=[],
        )
