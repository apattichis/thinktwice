"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from api.routes import router
from services import LLMService, SearchService, ScraperService
from core import ThinkTwicePipeline


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager - initialize and cleanup resources."""
    settings = get_settings()

    # Initialize services
    llm_service = LLMService(
        api_key=settings.anthropic_api_key,
        model=settings.model_name,
        max_tokens=settings.max_tokens,
        timeout=settings.timeout,
    )
    search_service = SearchService(
        brave_key=settings.brave_search_api_key,
        tavily_key=settings.tavily_api_key,
    )
    scraper_service = ScraperService()

    # Initialize pipeline with v2 settings
    pipeline = ThinkTwicePipeline(
        llm=llm_service,
        search=search_service,
        scraper=scraper_service,
        gate_threshold=settings.gate_threshold,
        gate_min_pass_rate=settings.gate_min_pass_rate,
        max_iterations=settings.max_iterations,
        convergence_threshold=settings.convergence_threshold,
        self_verify_enabled=settings.self_verify_enabled,
        self_verify_parallel=settings.self_verify_parallel,
        trust_blend_enabled=settings.trust_blend_enabled,
    )

    # Store in app state
    app.state.llm = llm_service
    app.state.search = search_service
    app.state.scraper = scraper_service
    app.state.pipeline = pipeline
    app.state.settings = settings

    yield

    # Cleanup
    await llm_service.close()
    await search_service.close()


app = FastAPI(
    title="ThinkTwice API",
    description="AI reasoning pipeline that drafts, critiques, verifies, and refines answers",
    version="2.0.0",
    lifespan=lifespan,
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/api/health")
async def health_check() -> dict:
    """Health check endpoint."""
    settings = get_settings()
    return {
        "status": "healthy",
        "search_enabled": settings.has_search,
        "search_provider": (
            "brave" if settings.brave_search_api_key
            else "tavily" if settings.tavily_api_key
            else None
        ),
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
