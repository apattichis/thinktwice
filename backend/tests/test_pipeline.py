"""Integration tests for the ThinkTwice pipeline orchestrator."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.pipeline import ThinkTwicePipeline
from models.schemas import ThinkRequest, InputMode


@pytest.fixture
def mock_services():
    """Create mock services for the pipeline."""
    from services.llm import LLMService
    from services.search import SearchService
    from services.scraper import ScraperService

    llm = MagicMock(spec=LLMService)
    llm.generate = AsyncMock(return_value="Mock response")
    llm.generate_with_tools = AsyncMock(return_value=None)

    async def mock_stream(*args, **kwargs):
        for token in ["Hello", " ", "world"]:
            yield token
    llm.stream = mock_stream

    search = MagicMock(spec=SearchService)
    search.query = AsyncMock(return_value=None)
    search.close = AsyncMock()

    scraper = MagicMock(spec=ScraperService)

    return llm, search, scraper


@pytest.fixture
def pipeline(mock_services):
    llm, search, scraper = mock_services
    return ThinkTwicePipeline(
        llm=llm, search=search, scraper=scraper,
        max_iterations=2, gate_threshold=85,
    )


def parse_sse_events(event_strings: list[str]) -> list[dict]:
    """Parse SSE event strings into dicts."""
    events = []
    for s in event_strings:
        lines = s.strip().split("\n")
        event = {}
        for line in lines:
            if line.startswith("event: "):
                event["event"] = line[7:]
            elif line.startswith("data: "):
                try:
                    event["data"] = json.loads(line[6:])
                except json.JSONDecodeError:
                    event["data"] = line[6:]
        if event:
            events.append(event)
    return events


class TestPipeline:
    @pytest.mark.asyncio
    async def test_emits_decompose_event(self, pipeline, mock_services):
        """Test that pipeline emits decompose_complete event."""
        llm = mock_services[0]
        # Decompose response
        llm.generate_with_tools.return_value = {
            "main_task": "Answer question",
            "constraints": [
                {"id": "C1", "type": "accuracy", "description": "Be accurate", "priority": "high", "verifiable": True},
            ],
            "implicit_constraints": [],
            "difficulty_estimate": "easy",
        }

        request = ThinkRequest(input="What is 2+2?", mode=InputMode.QUESTION)
        events = []
        async for event in pipeline.execute_pipeline(request):
            events.append(event)

        parsed = parse_sse_events(events)
        event_names = [e["event"] for e in parsed]

        assert "decompose_complete" in event_names

    @pytest.mark.asyncio
    async def test_emits_gate_event(self, pipeline, mock_services):
        """Test that pipeline emits gate_decision event."""
        llm = mock_services[0]

        # Setup sequential tool responses
        responses = [
            # Decompose
            {
                "main_task": "Test",
                "constraints": [{"id": "C1", "type": "accuracy", "description": "Be accurate", "priority": "high", "verifiable": True}],
                "implicit_constraints": [],
                "difficulty_estimate": "easy",
            },
            # Gate (skip path)
            {
                "sub_questions": [{"constraint_id": "C1", "question": "Q?", "answer": "Yes", "passed": True}],
                "gate_decision": "skip",
                "gate_confidence": 95,
                "failing_constraints": [],
            },
            # Trust
            {
                "winner": "refined",
                "reasoning": "Same version",
                "draft_score": 80,
                "refined_score": 80,
                "final_output": "Hello world",
                "blended": False,
            },
        ]
        llm.generate_with_tools.side_effect = responses

        request = ThinkRequest(input="What is 2+2?", mode=InputMode.QUESTION)
        events = []
        async for event in pipeline.execute_pipeline(request):
            events.append(event)

        parsed = parse_sse_events(events)
        event_names = [e["event"] for e in parsed]

        assert "gate_decision" in event_names

    @pytest.mark.asyncio
    async def test_pipeline_complete_has_metrics(self, pipeline, mock_services):
        """Test that pipeline_complete event includes expected metrics."""
        llm = mock_services[0]

        responses = [
            # Decompose
            {
                "main_task": "Test",
                "constraints": [{"id": "C1", "type": "accuracy", "description": "Test", "priority": "high", "verifiable": True}],
                "implicit_constraints": [],
                "difficulty_estimate": "easy",
            },
            # Gate (skip)
            {
                "sub_questions": [{"constraint_id": "C1", "question": "Q?", "answer": "Yes", "passed": True}],
                "gate_decision": "skip",
                "gate_confidence": 95,
                "failing_constraints": [],
            },
            # Trust
            {
                "winner": "refined",
                "reasoning": "Good",
                "draft_score": 80,
                "refined_score": 85,
                "final_output": "Hello world",
                "blended": False,
            },
        ]
        llm.generate_with_tools.side_effect = responses

        request = ThinkRequest(input="Test", mode=InputMode.QUESTION)
        events = []
        async for event in pipeline.execute_pipeline(request):
            events.append(event)

        parsed = parse_sse_events(events)
        complete_event = next(e for e in parsed if e["event"] == "pipeline_complete")

        assert "gate_decision" in complete_event["data"]
        assert "trust_winner" in complete_event["data"]
        assert "constraints_total" in complete_event["data"]
        assert "fast_path" in complete_event["data"]
