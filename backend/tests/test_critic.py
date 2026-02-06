"""Tests for the critic module."""

import pytest
from unittest.mock import AsyncMock

from core.critic import Critic
from core.schemas import (
    Constraint, ConstraintType, ConstraintPriority,
    ConstraintEvaluation, ConstraintVerdict, ClaimToVerify, CritiqueResult,
)


def _make_constraint(id: str, priority: str = "high") -> Constraint:
    return Constraint(
        id=id, type=ConstraintType.ACCURACY, description=f"Constraint {id}",
        priority=ConstraintPriority(priority), verifiable=True,
    )


@pytest.fixture
def critic(mock_llm):
    return Critic(mock_llm)


class TestCritic:
    @pytest.mark.asyncio
    async def test_critique_returns_evaluations(self, critic, mock_llm):
        """Test per-constraint evaluation."""
        mock_llm.generate_with_tools.return_value = {
            "constraint_evaluations": [
                {"constraint_id": "C1", "verdict": "satisfied", "confidence": 90, "feedback": "Good"},
                {"constraint_id": "C2", "verdict": "violated", "confidence": 80, "feedback": "Missing info"},
            ],
            "claims_to_verify": [
                {"id": "V1", "claim": "Water boils at 100C", "source_constraint": "C1", "source_quote": "..."},
            ],
            "overall_confidence": 65,
            "strengths_to_preserve": ["Clear explanation"],
        }

        constraints = [_make_constraint("C1"), _make_constraint("C2")]
        result = await critic.critique("Draft", constraints, ["C2"], "input", "question")

        assert isinstance(result, CritiqueResult)
        assert len(result.constraint_evaluations) == 2
        assert result.constraint_evaluations[0].verdict == ConstraintVerdict.SATISFIED
        assert result.constraint_evaluations[1].verdict == ConstraintVerdict.VIOLATED
        assert len(result.claims_to_verify) == 1
        assert result.claims_to_verify[0].id == "V1"
        assert result.overall_confidence == 65

    @pytest.mark.asyncio
    async def test_critique_fallback_on_none(self, critic, mock_llm):
        """Test fallback when tool returns None."""
        mock_llm.generate_with_tools.return_value = None

        constraints = [_make_constraint("C1")]
        result = await critic.critique("Draft", constraints, [], "input", "question")

        assert isinstance(result, CritiqueResult)
        assert len(result.constraint_evaluations) == 1
        assert result.constraint_evaluations[0].verdict == ConstraintVerdict.PARTIALLY_SATISFIED
