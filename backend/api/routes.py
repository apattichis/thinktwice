"""API routes for the ThinkTwice backend."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from models.schemas import ThinkRequest, ExamplesResponse


router = APIRouter()


@router.post("/think")
async def think(request: Request, body: ThinkRequest):
    """
    Main endpoint - runs the ThinkTwice pipeline and streams SSE events.

    Events:
    - step_start: A step is beginning
    - step_stream: Token streaming for draft/refine steps
    - step_complete: A step has completed
    - verify_claim: A claim verification result
    - pipeline_complete: Final metrics
    """
    pipeline = request.app.state.pipeline

    async def event_generator():
        async for event in pipeline.execute(body):
            yield event

    return EventSourceResponse(event_generator())


@router.post("/think/single-shot")
async def think_single_shot(request: Request, body: ThinkRequest):
    """Run a single LLM call without the pipeline for comparison."""
    pipeline = request.app.state.pipeline
    response = await pipeline.single_shot(body)
    return JSONResponse({"response": response})


@router.get("/examples")
async def get_examples():
    """Return curated example prompts organized by mode."""
    return ExamplesResponse(
        questions=[
            "Is intermittent fasting safe for people with diabetes?",
            "Explain how mRNA vaccines work. Are there long-term risks?",
            "What causes the northern lights and how far south can they be seen?",
            "How does blockchain technology actually work?",
            "What are the real environmental impacts of electric vehicles?",
        ],
        claims=[
            "Humans only use 10% of their brain",
            "The Great Wall of China is visible from space",
            "Coffee stunts your growth",
            "Napoleon Bonaparte was unusually short",
            "Goldfish have a 3-second memory",
        ],
        urls=[],  # Users provide their own URLs
    )
