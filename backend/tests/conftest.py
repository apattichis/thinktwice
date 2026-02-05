"""Shared test fixtures for ThinkTwice tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from services.llm import LLMService
from services.search import SearchService


@pytest.fixture
def mock_llm():
    """Create a mock LLMService."""
    llm = MagicMock(spec=LLMService)
    llm.generate = AsyncMock(return_value="Mock response")
    llm.generate_with_tools = AsyncMock(return_value=None)
    llm.stream = AsyncMock()
    return llm


@pytest.fixture
def mock_search():
    """Create a mock SearchService."""
    search = MagicMock(spec=SearchService)
    search.query = AsyncMock(return_value=None)
    search.close = AsyncMock()
    return search
