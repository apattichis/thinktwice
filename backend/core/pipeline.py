"""Pipeline orchestrator - runs all 4 steps and yields SSE events."""

import json
import time
from typing import AsyncGenerator

from models.schemas import ThinkRequest, InputMode
from services.llm import LLMService
from services.search import SearchService
from services.scraper import ScraperService
from core.drafter import Drafter
from core.critic import Critic
from core.verifier import Verifier
from core.refiner import Refiner


class ThinkTwicePipeline:
    """Orchestrates the 4-step reasoning pipeline."""

    def __init__(
        self,
        llm: LLMService,
        search: SearchService,
        scraper: ScraperService,
    ):
        self.drafter = Drafter(llm)
        self.critic = Critic(llm)
        self.verifier = Verifier(llm, search)
        self.refiner = Refiner(llm)
        self.scraper = scraper
        self.search = search

    def _sse(self, event: str, data: dict) -> str:
        """Format data as an SSE event string."""
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    async def execute(self, request: ThinkRequest) -> AsyncGenerator[str, None]:
        """
        Execute the full pipeline and yield SSE events.

        Events emitted:
        - step_start: When a step begins
        - step_stream: Token-by-token streaming (for draft/refine)
        - step_complete: When a step finishes
        - verify_claim: For each claim verification result
        - pipeline_complete: Final metrics
        """
        start = time.monotonic()
        user_input = request.input

        # Pre-process: if URL mode, extract content first
        if request.mode == InputMode.URL:
            try:
                yield self._sse("step_start", {
                    "step": "extract",
                    "status": "running",
                    "label": "Extracting article content...",
                })
                extracted = await self.scraper.extract(request.input)
                user_input = f"Analyze and fact-check this article:\n\n{extracted}"
                yield self._sse("step_complete", {
                    "step": "extract",
                    "status": "complete",
                    "label": "Content extracted",
                })
            except ValueError as e:
                yield self._sse("step_complete", {
                    "step": "extract",
                    "status": "error",
                    "error": str(e),
                })
                return

        # Step 1: Draft
        draft_start = time.monotonic()
        yield self._sse("step_start", {
            "step": "draft",
            "status": "running",
            "label": "Drafting initial response...",
        })

        draft_content = ""
        async for token in self.drafter.stream(user_input, request.mode):
            draft_content += token
            yield self._sse("step_stream", {"step": "draft", "token": token})

        draft_duration = int((time.monotonic() - draft_start) * 1000)
        yield self._sse("step_complete", {
            "step": "draft",
            "status": "complete",
            "duration_ms": draft_duration,
            "content": draft_content,
        })

        # Step 2: Critique
        critique_start = time.monotonic()
        yield self._sse("step_start", {
            "step": "critique",
            "status": "running",
            "label": "Self-critiquing...",
        })

        critique = await self.critic.analyze(user_input, draft_content, request.mode)
        critique_duration = int((time.monotonic() - critique_start) * 1000)

        yield self._sse("step_complete", {
            "step": "critique",
            "status": "complete",
            "duration_ms": critique_duration,
            "content": critique.model_dump(),
        })

        # Step 3: Verify
        verify_start = time.monotonic()
        claims_count = len(critique.claims_to_verify)
        yield self._sse("step_start", {
            "step": "verify",
            "status": "running",
            "label": f"Fact-checking {claims_count} claims...",
        })

        verified_count = 0
        refuted_count = 0
        unclear_count = 0
        web_verified = True

        async for result in self.verifier.check_claims(critique.claims_to_verify):
            yield self._sse("verify_claim", result.model_dump())
            if result.verdict == "verified":
                verified_count += 1
            elif result.verdict == "refuted":
                refuted_count += 1
            else:
                unclear_count += 1
            if not result.web_verified:
                web_verified = False

        verify_duration = int((time.monotonic() - verify_start) * 1000)
        verification_results = self.verifier.get_results()

        yield self._sse("step_complete", {
            "step": "verify",
            "status": "complete",
            "duration_ms": verify_duration,
            "verified": verified_count,
            "refuted": refuted_count,
            "unclear": unclear_count,
            "web_verified": web_verified,
        })

        # Step 4: Refine
        refine_start = time.monotonic()
        yield self._sse("step_start", {
            "step": "refine",
            "status": "running",
            "label": "Refining with corrections...",
        })

        refined = await self.refiner.produce(
            user_input,
            draft_content,
            critique,
            verification_results,
            request.mode,
        )
        refine_duration = int((time.monotonic() - refine_start) * 1000)

        yield self._sse("step_complete", {
            "step": "refine",
            "status": "complete",
            "duration_ms": refine_duration,
            "content": refined.content,
            "confidence": refined.confidence,
            "changes_made": refined.changes_made,
        })

        # Final metrics
        total_duration = int((time.monotonic() - start) * 1000)
        yield self._sse("pipeline_complete", {
            "total_duration_ms": total_duration,
            "confidence_before": critique.confidence,
            "confidence_after": refined.confidence,
            "issues_found": len(critique.issues),
            "issues_addressed": len(refined.changes_made),
            "claims_checked": claims_count,
            "claims_verified": verified_count,
            "claims_refuted": refuted_count,
            "claims_unclear": unclear_count,
            "web_verified": web_verified,
        })

    async def single_shot(self, request: ThinkRequest) -> str:
        """Run a single-shot response without the pipeline for comparison."""
        user_input = request.input

        # Pre-process URL if needed
        if request.mode == InputMode.URL:
            try:
                extracted = await self.scraper.extract(request.input)
                user_input = f"Analyze this article:\n\n{extracted}"
            except ValueError:
                return "Error: Could not extract content from URL"

        # Use the drafter for a single response
        return await self.drafter.llm.generate(
            system="You are a helpful assistant. Answer the user's question or analyze their input thoroughly.",
            user=user_input,
        )
