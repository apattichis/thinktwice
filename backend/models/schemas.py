"""Pydantic schemas for the ThinkTwice API."""

from enum import Enum

from pydantic import BaseModel, Field


class InputMode(str, Enum):
    """Input modes for the ThinkTwice pipeline."""

    QUESTION = "question"
    CLAIM = "claim"
    URL = "url"


class ThinkRequest(BaseModel):
    """Request model for the /api/think endpoint."""

    input: str = Field(..., min_length=1, max_length=5000)
    mode: InputMode = InputMode.QUESTION
    run_single_shot: bool = False


class SearchResult(BaseModel):
    """A single search result from web search."""

    title: str
    url: str
    snippet: str


class StepStatus(str, Enum):
    """Status of a pipeline step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"


class ExamplePrompt(BaseModel):
    """An example prompt for the UI."""

    text: str
    mode: InputMode


class ExamplesResponse(BaseModel):
    """Response model for the /api/examples endpoint."""

    questions: list[str]
    claims: list[str]
    urls: list[str]
