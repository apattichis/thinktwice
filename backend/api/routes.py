"""API routes for the ThinkTwice backend."""

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse

from models.schemas import ThinkRequest, ExamplesResponse


router = APIRouter()


@router.post("/think")
async def think(
    request: Request,
    body: ThinkRequest,
    max_iterations: int | None = Query(None, ge=1, le=10, description="Max refinement iterations"),
    gate_threshold: int | None = Query(None, ge=0, le=100, description="Gate confidence threshold"),
):
    """
    Main endpoint - runs the ThinkTwice pipeline and streams SSE events.

    Events:
    - step_start: A step is beginning
    - step_stream: Token streaming for draft/refine steps
    - step_complete: A step has completed
    - decompose_complete: Constraint decomposition results
    - gate_decision: Gate evaluation with sub-questions and decision
    - constraint_verdict: Per-constraint evaluation (streamed)
    - verify_claim: A claim verification result
    - self_verify_claim: Self-verification result for a claim
    - iteration_start: Refinement loop iteration beginning
    - iteration_complete: Refinement loop iteration with convergence result
    - trust_decision: Trust comparison result with scores
    - pipeline_complete: Final metrics
    """
    pipeline = request.app.state.pipeline

    async def event_generator():
        async for event in pipeline.execute(
            body,
            max_iterations=max_iterations,
            gate_threshold=gate_threshold,
        ):
            yield event

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/think/single-shot")
async def think_single_shot(request: Request, body: ThinkRequest):
    """Run a single LLM call without the pipeline for comparison."""
    pipeline = request.app.state.pipeline
    response = await pipeline.single_shot(body)
    return JSONResponse({"response": response})


@router.get("/examples")
async def get_examples():
    """Return curated example prompts."""
    return ExamplesResponse(
        examples=[
            "Is intermittent fasting safe for people with diabetes?",
            "Humans only use 10% of their brain",
            "What causes the northern lights and how far south can they be seen?",
            "The Great Wall of China is visible from space",
        ],
    )
