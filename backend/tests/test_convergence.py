"""Tests for the convergence checker module."""

import pytest
from unittest.mock import AsyncMock

from core.convergence import ConvergenceChecker
from core.schemas import Constraint, ConstraintType, ConstraintPriority, ConvergenceDecision, ConvergenceResult


def _make_constraint(id: str, priority: str = "high") -> Constraint:
    return Constraint(
        id=id, type=ConstraintType.ACCURACY, description=f"Constraint {id}",
        priority=ConstraintPriority(priority), verifiable=True,
    )


@pytest.fixture
def checker(mock_llm):
    return ConvergenceChecker(mock_llm)


class TestConvergenceChecker:
    @pytest.mark.asyncio
    async def test_converged_decision(self, checker, mock_llm):
        """Test convergence when all constraints satisfied."""
        mock_llm.generate_with_tools.return_value = {
            "constraint_checks": [
                {"constraint_id": "C1", "satisfied": True, "confidence": 90},
                {"constraint_id": "C2", "satisfied": True, "confidence": 85},
            ],
            "decision": "converged",
            "overall_confidence": 88,
        }

        constraints = [_make_constraint("C1"), _make_constraint("C2")]
        result = await checker.check_convergence("Refined text", constraints, 1, 3, 80)

        assert result.decision == ConvergenceDecision.CONVERGED
        assert result.satisfied_count == 2
        assert result.confidence == 88

    @pytest.mark.asyncio
    async def test_continue_decision(self, checker, mock_llm):
        """Test continue when constraints unsatisfied."""
        mock_llm.generate_with_tools.return_value = {
            "constraint_checks": [
                {"constraint_id": "C1", "satisfied": False, "confidence": 40},
                {"constraint_id": "C2", "satisfied": True, "confidence": 85},
            ],
            "decision": "continue",
            "overall_confidence": 55,
        }

        constraints = [_make_constraint("C1"), _make_constraint("C2")]
        result = await checker.check_convergence("Refined text", constraints, 1, 3, 80)

        assert result.decision == ConvergenceDecision.CONTINUE
        assert "C1" in result.unsatisfied_constraints

    @pytest.mark.asyncio
    async def test_max_iterations_forced(self, checker, mock_llm):
        """Test max iterations override."""
        mock_llm.generate_with_tools.return_value = {
            "constraint_checks": [
                {"constraint_id": "C1", "satisfied": False, "confidence": 40},
            ],
            "decision": "continue",
            "overall_confidence": 40,
        }

        constraints = [_make_constraint("C1")]
        result = await checker.check_convergence("Refined text", constraints, 3, 3, 80)

        assert result.decision == ConvergenceDecision.MAX_ITERATIONS

    @pytest.mark.asyncio
    async def test_fallback_on_none(self, checker, mock_llm):
        """Test fallback when tool returns None."""
        mock_llm.generate_with_tools.return_value = None

        constraints = [_make_constraint("C1")]
        result = await checker.check_convergence("Text", constraints, 1, 3, 80)

        assert result.decision == ConvergenceDecision.CONVERGED  # Safe fallback exits loop
