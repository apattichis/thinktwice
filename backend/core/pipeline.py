"""Pipeline orchestrator - runs the ThinkTwice self-correcting pipeline.

The pipeline implements:
  Phase 0: Decompose -> Phase 1: Draft -> Phase 2: Gate ->
  [Phase 3: Critique -> Phase 4: Verify -> Phase 5: Refine -> Phase 6: Converge]xN ->
  Phase 7: Trust & Rank
"""

import json
import logging
import time
from typing import AsyncGenerator, Optional

from models.schemas import ThinkRequest, InputMode
from services.llm import LLMService
from services.search import SearchService
from services.scraper import ScraperService
from core.drafter import Drafter
from core.critic import Critic
from core.verifier import Verifier
from core.refiner import Refiner
from core.decomposer import Decomposer
from core.gatekeeper import Gatekeeper
from core.convergence import ConvergenceChecker
from core.truster import Truster
from core.schemas import ConvergenceDecision

logger = logging.getLogger(__name__)


class ThinkTwicePipeline:
    """Orchestrates the ThinkTwice reasoning pipeline."""

    def __init__(
        self,
        llm: LLMService,
        search: SearchService,
        scraper: ScraperService,
        gate_threshold: int = 85,
        gate_min_pass_rate: float = 1.0,
        max_iterations: int = 3,
        convergence_threshold: int = 80,
        self_verify_enabled: bool = True,
        self_verify_parallel: bool = True,
        trust_blend_enabled: bool = True,
    ):
        self.drafter = Drafter(llm)
        self.critic = Critic(llm)
        self.verifier = Verifier(
            llm, search,
            self_verify_enabled=self_verify_enabled,
            self_verify_parallel=self_verify_parallel,
        )
        self.refiner = Refiner(llm)
        self.scraper = scraper
        self.search = search

        self.decomposer = Decomposer(llm)
        self.gatekeeper = Gatekeeper(llm, gate_threshold, gate_min_pass_rate)
        self.convergence = ConvergenceChecker(llm)
        self.truster = Truster(llm, blend_enabled=trust_blend_enabled)

        # Config
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold

    def _sse(self, event: str, data: dict) -> str:
        """Format data as an SSE event string."""
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    # ------------------------------------------------------------------
    # ThinkTwice Pipeline
    # ------------------------------------------------------------------
    async def execute_pipeline(
        self,
        request: ThinkRequest,
        max_iterations: Optional[int] = None,
        gate_threshold: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """Execute the ThinkTwice self-correcting pipeline.

        Yields SSE events for each phase of the pipeline.
        """
        pipeline_start = time.monotonic()
        phase_durations: dict[str, float] = {}
        user_input = request.input
        scraped_content: Optional[str] = None
        max_iter = max_iterations or self.max_iterations

        # Pre-process: URL extraction
        if request.mode == InputMode.URL:
            try:
                yield self._sse("step_start", {
                    "step": "extract",
                    "status": "running",
                    "label": "Extracting article content...",
                })
                scraped_content = await self.scraper.extract(request.input)
                user_input = f"Analyze and fact-check this article:\n\n{scraped_content}"
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

        # Phase 0: Decompose
        decompose_start = time.monotonic()
        yield self._sse("step_start", {
            "step": "decompose",
            "status": "running",
            "label": "Analyzing constraints...",
        })

        try:
            decompose_result = await self.decomposer.decompose(
                request.input, request.mode, scraped_content
            )
        except Exception as e:
            logger.error("Decompose failed, using fallback: %s", e)
            decompose_result = self.decomposer._fallback_result(request.input)

        decompose_duration = int((time.monotonic() - decompose_start) * 1000)
        phase_durations["decompose"] = decompose_duration

        yield self._sse("decompose_complete", {
            "step": "decompose",
            "status": "complete",
            "duration_ms": decompose_duration,
            "main_task": decompose_result.main_task,
            "constraints": [c.model_dump() for c in decompose_result.constraints],
            "implicit_constraints": decompose_result.implicit_constraints,
            "difficulty_estimate": decompose_result.difficulty_estimate,
        })

        # Phase 1: Draft (streaming)
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
        phase_durations["draft"] = draft_duration

        yield self._sse("step_complete", {
            "step": "draft",
            "status": "complete",
            "duration_ms": draft_duration,
            "content": draft_content,
        })

        # Phase 2: Ask & Gate
        gate_start = time.monotonic()
        yield self._sse("step_start", {
            "step": "gate",
            "status": "running",
            "label": "Evaluating draft quality...",
        })

        try:
            gate_result = await self.gatekeeper.gate(
                draft_content, decompose_result.constraints, request.mode.value
            )
        except Exception as e:
            logger.error("Gate failed, defaulting to refine: %s", e)
            gate_result = self.gatekeeper._fallback_result(decompose_result.constraints)

        gate_duration = int((time.monotonic() - gate_start) * 1000)
        phase_durations["gate"] = gate_duration

        yield self._sse("gate_decision", {
            "step": "gate",
            "status": "complete",
            "duration_ms": gate_duration,
            "gate_decision": gate_result.gate_decision,
            "gate_confidence": gate_result.gate_confidence,
            "failing_constraints": gate_result.failing_constraints,
            "sub_questions": [sq.model_dump() for sq in gate_result.sub_questions],
        })

        current_draft = draft_content
        all_verifications = []
        iteration = 0
        fast_path = gate_result.gate_decision == "skip"

        if fast_path:
            # Fast path -- skip refinement loop
            yield self._sse("step_complete", {
                "step": "gate",
                "fast_path": True,
            })
            logger.info("Gate: fast path -- skipping refinement loop")
        else:
            # Refinement loop
            while True:
                iteration += 1
                yield self._sse("iteration_start", {
                    "iteration": iteration,
                    "max_iterations": max_iter,
                })

                # Phase 3: Constraint-Critique
                critique_start = time.monotonic()
                yield self._sse("step_start", {
                    "step": "critique",
                    "status": "running",
                    "label": f"Critiquing (iteration {iteration})...",
                })

                try:
                    critique_result = await self.critic.critique(
                        current_draft,
                        decompose_result.constraints,
                        gate_result.failing_constraints,
                        input_text=request.input,
                        mode=request.mode.value,
                    )
                except Exception as e:
                    logger.error("Critique failed: %s", e)
                    critique_result = self.critic._fallback_critique(decompose_result.constraints)

                critique_duration = int((time.monotonic() - critique_start) * 1000)
                phase_durations[f"critique_{iteration}"] = critique_duration

                # Stream per-constraint verdicts
                for ev in critique_result.constraint_evaluations:
                    yield self._sse("constraint_verdict", ev.model_dump())

                yield self._sse("step_complete", {
                    "step": "critique",
                    "status": "complete",
                    "duration_ms": critique_duration,
                    "content": critique_result.model_dump(),
                })

                # Phase 4: Dual Verify
                verify_start = time.monotonic()
                claims_count = len(critique_result.claims_to_verify)
                yield self._sse("step_start", {
                    "step": "verify",
                    "status": "running",
                    "label": f"Verifying {claims_count} claims...",
                })

                try:
                    verifications = await self.verifier.dual_verify(
                        critique_result.claims_to_verify
                    )
                except Exception as e:
                    logger.error("Verification failed: %s", e)
                    verifications = []

                for v in verifications:
                    yield self._sse("verify_claim", v.model_dump())
                    if v.self_verdict:
                        yield self._sse("self_verify_claim", {
                            "claim_id": v.claim_id,
                            "self_verdict": v.self_verdict.value,
                            "self_derivation": v.self_derivation,
                        })

                all_verifications = verifications
                verify_duration = int((time.monotonic() - verify_start) * 1000)
                phase_durations[f"verify_{iteration}"] = verify_duration

                verified = sum(1 for v in verifications if v.combined_verdict.value == "verified")
                refuted = sum(1 for v in verifications if v.combined_verdict.value == "refuted")
                unclear = sum(1 for v in verifications if v.combined_verdict.value == "unclear")

                yield self._sse("step_complete", {
                    "step": "verify",
                    "status": "complete",
                    "duration_ms": verify_duration,
                    "verified": verified,
                    "refuted": refuted,
                    "unclear": unclear,
                })

                # Phase 5: Selective Refine
                refine_start = time.monotonic()
                yield self._sse("step_start", {
                    "step": "refine",
                    "status": "running",
                    "label": f"Refining (iteration {iteration})...",
                })

                try:
                    refine_result = await self.refiner.selective_refine(
                        current_draft,
                        critique_result,
                        verifications,
                        decompose_result.constraints,
                    )
                except Exception as e:
                    logger.error("Refinement failed: %s", e)
                    from core.schemas import RefineResult
                    refine_result = RefineResult(
                        refined_response=current_draft,
                        changes_made=[],
                        confidence_after=critique_result.overall_confidence,
                    )

                refine_duration = int((time.monotonic() - refine_start) * 1000)
                phase_durations[f"refine_{iteration}"] = refine_duration

                yield self._sse("step_complete", {
                    "step": "refine",
                    "status": "complete",
                    "duration_ms": refine_duration,
                    "content": refine_result.refined_response,
                    "confidence": refine_result.confidence_after,
                    "changes_made": [ch.model_dump() for ch in refine_result.changes_made],
                })

                # Phase 6: Convergence Check
                try:
                    convergence_result = await self.convergence.check_convergence(
                        refine_result.refined_response,
                        decompose_result.constraints,
                        iteration,
                        max_iter,
                        self.convergence_threshold,
                    )
                except Exception as e:
                    logger.error("Convergence check failed: %s", e)
                    convergence_result = None

                yield self._sse("iteration_complete", {
                    "iteration": iteration,
                    "convergence": convergence_result.model_dump() if convergence_result else {
                        "decision": "converged",
                        "satisfied_count": 0,
                        "total_count": len(decompose_result.constraints),
                        "confidence": 0,
                        "unsatisfied_constraints": [],
                    },
                })

                current_draft = refine_result.refined_response

                if convergence_result is None or convergence_result.decision != ConvergenceDecision.CONTINUE:
                    break

        # Phase 7: Trust & Rank
        trust_start = time.monotonic()
        yield self._sse("step_start", {
            "step": "trust",
            "status": "running",
            "label": "Comparing versions...",
        })

        try:
            trust_result = await self.truster.trust_and_rank(
                draft_content,
                current_draft,
                decompose_result.constraints,
                all_verifications,
            )
        except Exception as e:
            logger.error("Trust comparison failed: %s", e)
            from core.schemas import TrustResult
            trust_result = TrustResult(
                winner="refined",
                reasoning=f"Trust comparison failed ({e}), using refined",
                draft_score=50,
                refined_score=60,
                final_output=current_draft,
                blended=False,
            )

        trust_duration = int((time.monotonic() - trust_start) * 1000)
        phase_durations["trust"] = trust_duration

        yield self._sse("trust_decision", {
            "step": "trust",
            "status": "complete",
            "duration_ms": trust_duration,
            "winner": trust_result.winner,
            "reasoning": trust_result.reasoning,
            "draft_score": trust_result.draft_score,
            "refined_score": trust_result.refined_score,
            "blended": trust_result.blended,
            "blend_notes": trust_result.blend_notes,
        })

        # Final metrics
        total_duration = int((time.monotonic() - pipeline_start) * 1000)

        verified_total = sum(1 for v in all_verifications if v.combined_verdict.value == "verified")
        refuted_total = sum(1 for v in all_verifications if v.combined_verdict.value == "refuted")
        unclear_total = sum(1 for v in all_verifications if v.combined_verdict.value == "unclear")

        # Compute constraint satisfaction from the last critique if available
        constraints_satisfied = 0
        if not fast_path and iteration > 0:
            constraints_satisfied = sum(
                1 for ev in critique_result.constraint_evaluations
                if ev.verdict.value == "satisfied"
            )

        yield self._sse("pipeline_complete", {
            "final_output": trust_result.final_output,
            "total_duration_ms": total_duration,
            "confidence_before": gate_result.gate_confidence,
            "confidence_after": trust_result.refined_score,
            "gate_decision": gate_result.gate_decision,
            "fast_path": fast_path,
            "iterations_used": iteration,
            "trust_winner": trust_result.winner,
            "constraints_total": len(decompose_result.constraints),
            "constraints_satisfied": constraints_satisfied,
            "claims_checked": len(all_verifications),
            "claims_verified": verified_total,
            "claims_refuted": refuted_total,
            "claims_unclear": unclear_total,
            "phase_durations": phase_durations,
            "web_verified": all(v.web_verified for v in all_verifications) if all_verifications else True,
            "draft_score": trust_result.draft_score,
            "refined_score": trust_result.refined_score,
        })

    # ------------------------------------------------------------------
    # Default execute (routes to ThinkTwice pipeline)
    # ------------------------------------------------------------------
    async def execute(
        self,
        request: ThinkRequest,
        max_iterations: Optional[int] = None,
        gate_threshold: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """Execute the ThinkTwice pipeline.

        Args:
            request: The think request.
            max_iterations: Override max iterations.
            gate_threshold: Override gate threshold.
        """
        async for event in self.execute_pipeline(request, max_iterations, gate_threshold):
            yield event

    async def single_shot(self, request: ThinkRequest) -> str:
        """Run a single-shot response without the pipeline for comparison."""
        user_input = request.input

        if request.mode == InputMode.URL:
            try:
                extracted = await self.scraper.extract(request.input)
                user_input = f"Analyze this article:\n\n{extracted}"
            except ValueError:
                return "Error: Could not extract content from URL"

        return await self.drafter.llm.generate(
            system="You are a helpful assistant. Answer the user's question or analyze their input thoroughly.",
            user=user_input,
        )
