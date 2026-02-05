"""Tests for the gatekeeper module."""

import pytest
from unittest.mock import AsyncMock

from core.gatekeeper import Gatekeeper
from core.schemas import Constraint, ConstraintType, ConstraintPriority, GateResult


def _make_constraint(id: str, priority: str = "high") -> Constraint:
    return Constraint(
        id=id,
        type=ConstraintType.ACCURACY,
        description=f"Constraint {id}",
        priority=ConstraintPriority(priority),
        verifiable=True,
    )


@pytest.fixture
def gatekeeper(mock_llm):
    return Gatekeeper(mock_llm, gate_threshold=85, gate_min_pass_rate=1.0)


class TestGatekeeper:
    @pytest.mark.asyncio
    async def test_gate_skip_decision(self, gatekeeper, mock_llm):
        """Test that gate returns skip when all constraints pass."""
        mock_llm.generate_with_tools.return_value = {
            "sub_questions": [
                {"constraint_id": "C1", "question": "Is it accurate?", "answer": "Yes", "passed": True},
                {"constraint_id": "C2", "question": "Is it complete?", "answer": "Yes", "passed": True},
            ],
            "gate_decision": "skip",
            "gate_confidence": 90,
            "failing_constraints": [],
        }

        constraints = [_make_constraint("C1"), _make_constraint("C2")]
        result = await gatekeeper.gate("Draft text", constraints, "question")

        assert isinstance(result, GateResult)
        assert result.gate_decision == "skip"
        assert result.gate_confidence == 90
        assert len(result.failing_constraints) == 0

    @pytest.mark.asyncio
    async def test_gate_refine_decision(self, gatekeeper, mock_llm):
        """Test that gate returns refine when constraints fail."""
        mock_llm.generate_with_tools.return_value = {
            "sub_questions": [
                {"constraint_id": "C1", "question": "Is it accurate?", "answer": "No", "passed": False},
                {"constraint_id": "C2", "question": "Is it complete?", "answer": "Yes", "passed": True},
            ],
            "gate_decision": "refine",
            "gate_confidence": 60,
            "failing_constraints": ["C1"],
        }

        constraints = [_make_constraint("C1"), _make_constraint("C2")]
        result = await gatekeeper.gate("Draft text", constraints, "question")

        assert result.gate_decision == "refine"
        assert "C1" in result.failing_constraints

    @pytest.mark.asyncio
    async def test_gate_overrides_skip_when_high_priority_fails(self, gatekeeper, mock_llm):
        """Test server-side override when high-priority constraint fails."""
        mock_llm.generate_with_tools.return_value = {
            "sub_questions": [
                {"constraint_id": "C1", "question": "Is it accurate?", "answer": "No", "passed": False},
            ],
            "gate_decision": "skip",  # LLM says skip but C1 (high) failed
            "gate_confidence": 90,
            "failing_constraints": [],
        }

        constraints = [_make_constraint("C1", "high")]
        result = await gatekeeper.gate("Draft text", constraints, "question")

        # Server should override to refine
        assert result.gate_decision == "refine"

    @pytest.mark.asyncio
    async def test_gate_fallback_on_none(self, gatekeeper, mock_llm):
        """Test fallback when tool call returns None."""
        mock_llm.generate_with_tools.return_value = None

        constraints = [_make_constraint("C1")]
        result = await gatekeeper.gate("Draft text", constraints, "question")

        assert result.gate_decision == "refine"
        assert "C1" in result.failing_constraints

    @pytest.mark.asyncio
    async def test_gate_fallback_on_exception(self, gatekeeper, mock_llm):
        """Test fallback when API call raises."""
        mock_llm.generate_with_tools.side_effect = Exception("API error")

        constraints = [_make_constraint("C1")]
        result = await gatekeeper.gate("Draft text", constraints, "question")

        assert result.gate_decision == "refine"
