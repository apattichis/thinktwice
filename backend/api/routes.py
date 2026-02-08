"""API routes for the ThinkTwice backend."""

import anthropic
from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse

from config import get_settings
from models.schemas import ThinkRequest, ExamplesResponse
from services import LLMService
from core import ThinkTwicePipeline


router = APIRouter()


def _resolve_api_key(request: Request, x_api_key: str | None) -> str:
    """Get API key from header, fall back to server config, or raise 401."""
    if x_api_key:
        return x_api_key
    settings = request.app.state.settings
    if settings.anthropic_api_key:
        return settings.anthropic_api_key
    raise HTTPException(status_code=401, detail="API key required. Provide X-API-Key header.")


def _build_pipeline(
    request: Request, api_key: str
) -> tuple[ThinkTwicePipeline, LLMService | None]:
    """Return (pipeline, per_request_llm_or_None).

    Reuses the singleton pipeline when the key matches the server config.
    Otherwise creates a per-request LLMService + pipeline (GC'd after request).
    """
    settings = request.app.state.settings
    if settings.anthropic_api_key and api_key == settings.anthropic_api_key and request.app.state.pipeline:
        return request.app.state.pipeline, None

    # Per-request pipeline
    llm = LLMService(
        api_key=api_key,
        model=settings.model_name,
        max_tokens=settings.max_tokens,
        timeout=settings.timeout,
    )
    pipeline = ThinkTwicePipeline(
        llm=llm,
        search=request.app.state.search,
        scraper=request.app.state.scraper,
        gate_threshold=settings.gate_threshold,
        gate_min_pass_rate=settings.gate_min_pass_rate,
        max_iterations=settings.max_iterations,
        convergence_threshold=settings.convergence_threshold,
        self_verify_enabled=settings.self_verify_enabled,
        self_verify_parallel=settings.self_verify_parallel,
        trust_blend_enabled=settings.trust_blend_enabled,
    )
    return pipeline, llm


@router.post("/think")
async def think(
    request: Request,
    body: ThinkRequest,
    max_iterations: int | None = Query(None, ge=1, le=10, description="Max refinement iterations"),
    gate_threshold: int | None = Query(None, ge=0, le=100, description="Gate confidence threshold"),
    x_api_key: str | None = Header(None),
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
    api_key = _resolve_api_key(request, x_api_key)
    pipeline, per_request_llm = _build_pipeline(request, api_key)

    async def event_generator():
        try:
            async for event in pipeline.execute(
                body,
                max_iterations=max_iterations,
                gate_threshold=gate_threshold,
            ):
                yield event
        finally:
            if per_request_llm:
                await per_request_llm.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/think/single-shot")
async def think_single_shot(
    request: Request,
    body: ThinkRequest,
    x_api_key: str | None = Header(None),
):
    """Run a single LLM call without the pipeline for comparison."""
    api_key = _resolve_api_key(request, x_api_key)
    pipeline, per_request_llm = _build_pipeline(request, api_key)

    try:
        response = await pipeline.single_shot(body)
        return JSONResponse({"response": response})
    finally:
        if per_request_llm:
            await per_request_llm.close()


@router.post("/validate-key")
async def validate_key(x_api_key: str | None = Header(None)):
    """Validate an Anthropic API key with a minimal API call."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="No API key provided.")

    try:
        client = anthropic.AsyncAnthropic(api_key=x_api_key)
        await client.messages.create(
            model=get_settings().model_name,
            max_tokens=1,
            messages=[{"role": "user", "content": "hi"}],
        )
        await client.close()
        return {"valid": True}
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid API key.")
    except Exception:
        raise HTTPException(status_code=502, detail="Key validation failed. Please try again.")


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
