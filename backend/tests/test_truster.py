"""Tests for the trust-and-rank module."""

import pytest
from unittest.mock import AsyncMock

from core.truster import Truster
from core.schemas import Constraint, ConstraintType, ConstraintPriority, TrustResult, VerificationResult, ClaimVerdict


def _make_constraint(id: str) -> Constraint:
    return Constraint(
        id=id, type=ConstraintType.ACCURACY, description=f"Constraint {id}",
        priority=ConstraintPriority.HIGH, verifiable=True,
    )


@pytest.fixture
def truster(mock_llm):
    return Truster(mock_llm, blend_enabled=True)


class TestTruster:
    @pytest.mark.asyncio
    async def test_refined_wins(self, truster, mock_llm):
        """Test refined version selected as winner."""
        mock_llm.generate_with_tools.return_value = {
            "winner": "refined",
            "reasoning": "Refined is more accurate",
            "draft_score": 60,
            "refined_score": 85,
            "final_output": "The refined response",
            "blended": False,
        }

        result = await truster.trust_and_rank(
            "Draft text", "Refined text", [_make_constraint("C1")], []
        )

        assert isinstance(result, TrustResult)
        assert result.winner == "refined"
        assert result.draft_score == 60
        assert result.refined_score == 85
        assert result.final_output == "The refined response"

    @pytest.mark.asyncio
    async def test_draft_wins(self, truster, mock_llm):
        """Test draft selected when refinement made things worse."""
        mock_llm.generate_with_tools.return_value = {
            "winner": "draft",
            "reasoning": "Refinement introduced errors",
            "draft_score": 80,
            "refined_score": 55,
            "final_output": "The original draft",
            "blended": False,
        }

        result = await truster.trust_and_rank(
            "Draft text", "Refined text", [_make_constraint("C1")], []
        )

        assert result.winner == "draft"

    @pytest.mark.asyncio
    async def test_identical_versions_skip_comparison(self, truster, mock_llm):
        """Test short-circuit when draft == refined."""
        result = await truster.trust_and_rank(
            "Same text", "Same text", [_make_constraint("C1")], []
        )

        assert result.winner == "refined"
        mock_llm.generate_with_tools.assert_not_called()

    @pytest.mark.asyncio
    async def test_blend_disabled_falls_back(self, mock_llm):
        """Test blend disabled falls back to higher scorer."""
        truster = Truster(mock_llm, blend_enabled=False)
        mock_llm.generate_with_tools.return_value = {
            "winner": "blended",
            "reasoning": "Best of both",
            "draft_score": 70,
            "refined_score": 80,
            "final_output": "Blended text",
            "blended": True,
            "blend_notes": "Mixed parts",
        }

        result = await truster.trust_and_rank(
            "Draft text", "Refined text", [_make_constraint("C1")], []
        )

        # Should fall back to refined since it scored higher
        assert result.winner == "refined"
        assert result.blended == False

    @pytest.mark.asyncio
    async def test_fallback_on_exception(self, truster, mock_llm):
        """Test fallback when API fails."""
        mock_llm.generate_with_tools.side_effect = Exception("API error")

        result = await truster.trust_and_rank(
            "Draft", "Refined", [_make_constraint("C1")], []
        )

        assert result.winner == "refined"
        assert result.final_output == "Refined"
