"""Pydantic schemas for the ThinkTwice API."""

from enum import Enum
from typing import Literal

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


class CritiqueIssue(BaseModel):
    """A single issue identified by the critic."""

    description: str
    severity: Literal["low", "medium", "high"]
    quote: str | None = None


class Critique(BaseModel):
    """Structured critique output from the critic step."""

    issues: list[CritiqueIssue]
    strengths: list[str]
    claims_to_verify: list[str]
    confidence: int = Field(ge=0, le=100)


class VerificationResult(BaseModel):
    """Result of verifying a single claim."""

    claim: str
    verdict: Literal["verified", "refuted", "unclear"]
    source: str | None = None
    source_title: str | None = None
    explanation: str
    web_verified: bool = False


class RefinedResponse(BaseModel):
    """Final refined response from the refiner step."""

    content: str
    confidence: int = Field(ge=0, le=100)
    changes_made: list[str]


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


class PipelineMetrics(BaseModel):
    """Final metrics from the pipeline execution."""

    total_duration_ms: int
    confidence_before: int
    confidence_after: int
    issues_found: int
    issues_addressed: int
    claims_checked: int
    claims_verified: int
    claims_refuted: int
    claims_unclear: int
    web_verified: bool


class ExamplePrompt(BaseModel):
    """An example prompt for the UI."""

    text: str
    mode: InputMode


class ExamplesResponse(BaseModel):
    """Response model for the /api/examples endpoint."""

    questions: list[str]
    claims: list[str]
    urls: list[str]
