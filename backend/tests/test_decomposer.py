"""Tests for the constraint decomposer module."""

import pytest
from unittest.mock import AsyncMock

from core.decomposer import Decomposer
from core.schemas import ConstraintType, ConstraintPriority, DecomposeResult


@pytest.fixture
def decomposer(mock_llm):
    return Decomposer(mock_llm)


class TestDecomposer:
    @pytest.mark.asyncio
    async def test_decompose_returns_constraints(self, decomposer, mock_llm):
        """Test that decompose returns structured constraints."""
        mock_llm.generate_with_tools.return_value = {
            "main_task": "Answer a question about physics",
            "constraints": [
                {
                    "id": "C1",
                    "type": "accuracy",
                    "description": "Must be factually correct",
                    "priority": "high",
                    "verifiable": True,
                },
                {
                    "id": "C2",
                    "type": "content",
                    "description": "Must cover the main topic",
                    "priority": "medium",
                    "verifiable": True,
                },
            ],
            "implicit_constraints": ["Should be in English"],
            "difficulty_estimate": "medium",
        }

        result = await decomposer.decompose("What is gravity?")

        assert isinstance(result, DecomposeResult)
        assert len(result.constraints) == 2
        assert result.constraints[0].id == "C1"
        assert result.constraints[0].type == ConstraintType.ACCURACY
        assert result.constraints[0].priority == ConstraintPriority.HIGH
        assert result.main_task == "Answer a question about physics"
        assert result.difficulty_estimate == "medium"

    @pytest.mark.asyncio
    async def test_decompose_fallback_on_none(self, decomposer, mock_llm):
        """Test fallback when tool call returns None."""
        mock_llm.generate_with_tools.return_value = None

        result = await decomposer.decompose("What is gravity?")

        assert isinstance(result, DecomposeResult)
        assert len(result.constraints) >= 1
        assert result.constraints[0].priority == ConstraintPriority.HIGH

    @pytest.mark.asyncio
    async def test_decompose_fallback_on_exception(self, decomposer, mock_llm):
        """Test fallback when API call raises."""
        mock_llm.generate_with_tools.side_effect = Exception("API error")

        result = await decomposer.decompose("What is gravity?")

        assert isinstance(result, DecomposeResult)
        assert len(result.constraints) >= 1

    @pytest.mark.asyncio
    async def test_decompose_skips_malformed_constraints(self, decomposer, mock_llm):
        """Test that malformed constraints are skipped."""
        mock_llm.generate_with_tools.return_value = {
            "main_task": "Test",
            "constraints": [
                {"id": "C1", "type": "accuracy", "description": "Valid", "priority": "high", "verifiable": True},
                {"id": "C2", "type": "invalid_type", "description": "Bad type"},  # Missing required fields
            ],
            "implicit_constraints": [],
            "difficulty_estimate": "easy",
        }

        result = await decomposer.decompose("Test")
        assert len(result.constraints) == 1
        assert result.constraints[0].id == "C1"

    @pytest.mark.asyncio
    async def test_decompose_with_scraped_content(self, decomposer, mock_llm):
        """Test decomposition with scraped content."""
        mock_llm.generate_with_tools.return_value = {
            "main_task": "Analyze article",
            "constraints": [
                {"id": "C1", "type": "content", "description": "Cover main claims", "priority": "high", "verifiable": True},
            ],
            "implicit_constraints": [],
            "difficulty_estimate": "hard",
        }

        result = await decomposer.decompose(
            "https://example.com", scraped_content="Article text here"
        )
        assert result.difficulty_estimate == "hard"
