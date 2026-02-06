"""Tests for the refiner module."""

import pytest
from unittest.mock import AsyncMock

from core.refiner import Refiner
from core.schemas import (
    Constraint, ConstraintType, ConstraintPriority,
    ConstraintEvaluation, ConstraintVerdict, ClaimToVerify,
    CritiqueResult, VerificationResult, ClaimVerdict,
    ChangeRecord, RefineResult,
)


def _make_constraint(id: str) -> Constraint:
    return Constraint(
        id=id, type=ConstraintType.ACCURACY, description=f"Constraint {id}",
        priority=ConstraintPriority.HIGH, verifiable=True,
    )


def _make_critique_result() -> CritiqueResult:
    return CritiqueResult(
        constraint_evaluations=[
            ConstraintEvaluation(constraint_id="C1", verdict=ConstraintVerdict.SATISFIED, confidence=90),
            ConstraintEvaluation(constraint_id="C2", verdict=ConstraintVerdict.VIOLATED, confidence=80, feedback="Missing detail"),
        ],
        claims_to_verify=[
            ClaimToVerify(id="V1", claim="Test claim", source_constraint="C1", source_quote="..."),
        ],
        overall_confidence=65,
        strengths_to_preserve=["Clear structure"],
    )


def _make_verification() -> VerificationResult:
    return VerificationResult(
        claim_id="V1", claim="Test claim",
        web_verdict=ClaimVerdict.VERIFIED, web_source="https://example.com",
        web_explanation="Confirmed", self_verdict=ClaimVerdict.VERIFIED,
        self_derivation="Independent confirmation",
        combined_verdict=ClaimVerdict.VERIFIED, combined_confidence=90,
        web_verified=True,
    )


@pytest.fixture
def refiner(mock_llm):
    return Refiner(mock_llm)


class TestRefiner:
    @pytest.mark.asyncio
    async def test_selective_refine_returns_result(self, refiner, mock_llm):
        """Test selective refinement returns structured result."""
        mock_llm.generate_with_tools.return_value = {
            "refined_response": "Improved response text",
            "changes_made": [
                {"target_id": "C2", "change": "Added missing detail", "type": "content_addition"},
            ],
            "confidence_after": 85,
        }

        constraints = [_make_constraint("C1"), _make_constraint("C2")]
        result = await refiner.selective_refine(
            "Draft text", _make_critique_result(), [_make_verification()], constraints
        )

        assert isinstance(result, RefineResult)
        assert result.refined_response == "Improved response text"
        assert len(result.changes_made) == 1
        assert result.changes_made[0].target_id == "C2"
        assert result.confidence_after == 85

    @pytest.mark.asyncio
    async def test_selective_refine_fallback(self, refiner, mock_llm):
        """Test fallback when tool returns None."""
        mock_llm.generate_with_tools.return_value = None

        constraints = [_make_constraint("C1")]
        result = await refiner.selective_refine(
            "Draft text", _make_critique_result(), [], constraints
        )

        assert result.refined_response == "Draft text"
        assert len(result.changes_made) == 0
