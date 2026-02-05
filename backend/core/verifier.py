"""Verifier module - dual verification with web + self-verify (ReVISE-inspired).

Phase 4 of the v2 pipeline. Fact-checks claims against web sources (Track A)
and through independent re-derivation (Track B), then combines verdicts.

Maintains backward compatibility with v1 check_claims interface.
"""

import asyncio
import logging
from typing import AsyncGenerator, Optional

from services.llm import LLMService
from services.search import SearchService
from models.schemas import VerificationResult, SearchResult
from core.schemas import ClaimToVerify, ClaimVerdict, VerificationResultV2
from core.prompts import (
    WEB_VERIFY_SYSTEM_PROMPT,
    WEB_VERIFY_USER_PROMPT,
    SELF_VERIFY_SYSTEM_PROMPT,
    SELF_VERIFY_USER_PROMPT,
)

logger = logging.getLogger(__name__)

# Web verification tool
WEB_VERIFY_TOOLS = [
    {
        "name": "submit_verdict",
        "description": "Submit the verification verdict for a claim",
        "input_schema": {
            "type": "object",
            "properties": {
                "verdict": {
                    "type": "string",
                    "enum": ["verified", "refuted", "unclear"],
                },
                "explanation": {"type": "string"},
            },
            "required": ["verdict", "explanation"],
        },
    }
]

# Self-verification tool
SELF_VERIFY_TOOLS = [
    {
        "name": "submit_self_verdict",
        "description": "Submit self-verification verdict with independent derivation",
        "input_schema": {
            "type": "object",
            "properties": {
                "derivation": {
                    "type": "string",
                    "description": "Your independent reasoning and derivation",
                },
                "verdict": {
                    "type": "string",
                    "enum": ["verified", "refuted", "unclear"],
                },
            },
            "required": ["derivation", "verdict"],
        },
    }
]

# Fallback web verification prompt
VERIFY_FALLBACK_PROMPT = """You are a fact-checker. Evaluate the given claim based on your knowledge.
NOTE: No web search results are available. Evaluate based on your training data.
Be conservative — lean toward "unclear" unless you are very confident.
You MUST use the submit_verdict tool."""


def _combine_verdicts(
    web_verdict: ClaimVerdict,
    self_verdict: Optional[ClaimVerdict],
) -> tuple[ClaimVerdict, int]:
    """Combine web and self-verification verdicts with confidence.

    Returns (combined_verdict, confidence).
    """
    if self_verdict is None:
        # Self-verify disabled, use web verdict alone
        conf_map = {
            ClaimVerdict.VERIFIED: 65,
            ClaimVerdict.REFUTED: 65,
            ClaimVerdict.UNCLEAR: 30,
        }
        return web_verdict, conf_map.get(web_verdict, 30)

    # Both verdicts available
    if web_verdict == self_verdict:
        # Agreement
        conf_map = {
            ClaimVerdict.VERIFIED: 90,
            ClaimVerdict.REFUTED: 90,
            ClaimVerdict.UNCLEAR: 40,
        }
        return web_verdict, conf_map.get(web_verdict, 40)

    # Disagreement cases
    if web_verdict == ClaimVerdict.VERIFIED and self_verdict == ClaimVerdict.UNCLEAR:
        return ClaimVerdict.VERIFIED, 60
    if web_verdict == ClaimVerdict.REFUTED and self_verdict == ClaimVerdict.UNCLEAR:
        return ClaimVerdict.REFUTED, 60
    if web_verdict == ClaimVerdict.UNCLEAR and self_verdict == ClaimVerdict.VERIFIED:
        return ClaimVerdict.VERIFIED, 45
    if web_verdict == ClaimVerdict.UNCLEAR and self_verdict == ClaimVerdict.REFUTED:
        return ClaimVerdict.REFUTED, 45

    # Direct conflict (verified vs refuted) — mark as unclear
    return ClaimVerdict.UNCLEAR, 25


class Verifier:
    """Fact-checks claims with dual verification: web + self-verify."""

    def __init__(
        self,
        llm: LLMService,
        search: SearchService,
        self_verify_enabled: bool = True,
        self_verify_parallel: bool = True,
    ):
        self.llm = llm
        self.search = search
        self.self_verify_enabled = self_verify_enabled
        self.self_verify_parallel = self_verify_parallel
        self._results: list[VerificationResult] = []
        self._results_v2: list[VerificationResultV2] = []

    def _format_results(self, results: list[SearchResult]) -> str:
        """Format search results for the LLM prompt."""
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"{i}. {r.title}\n   URL: {r.url}\n   {r.snippet}")
        return "\n\n".join(formatted)

    async def _web_verify_claim(self, claim: str) -> dict:
        """Verify a claim against web search results.

        Returns dict with verdict, explanation, source, web_verified.
        """
        search_results = await self.search.query(claim)

        if search_results:
            user_message = WEB_VERIFY_USER_PROMPT.format(
                claim=claim,
                search_results=self._format_results(search_results),
            )

            verdict_data = await self.llm.generate_with_tools(
                system=WEB_VERIFY_SYSTEM_PROMPT,
                user=user_message,
                tools=WEB_VERIFY_TOOLS,
                tool_choice={"type": "tool", "name": "submit_verdict"},
            )

            return {
                "verdict": verdict_data.get("verdict", "unclear") if verdict_data else "unclear",
                "explanation": verdict_data.get("explanation", "Unable to evaluate") if verdict_data else "Unable to evaluate",
                "source": search_results[0].url if search_results else None,
                "source_title": search_results[0].title if search_results else None,
                "web_verified": True,
            }
        else:
            # Fallback: use Claude's knowledge
            user_message = f"Claim: {claim}\n\nEvaluate this claim based on your knowledge.\nUse the submit_verdict tool."

            verdict_data = await self.llm.generate_with_tools(
                system=VERIFY_FALLBACK_PROMPT,
                user=user_message,
                tools=WEB_VERIFY_TOOLS,
                tool_choice={"type": "tool", "name": "submit_verdict"},
            )

            explanation = ""
            if verdict_data:
                explanation = verdict_data.get("explanation", "")
            explanation += " (verified against AI knowledge only, not web sources)"

            return {
                "verdict": verdict_data.get("verdict", "unclear") if verdict_data else "unclear",
                "explanation": explanation,
                "source": None,
                "source_title": None,
                "web_verified": False,
            }

    async def self_verify_claim(self, claim: str) -> dict:
        """Independently re-derive and verify a claim (ReVISE Track B).

        Returns dict with verdict, derivation.
        """
        user_message = SELF_VERIFY_USER_PROMPT.format(claim=claim)

        try:
            result = await self.llm.generate_with_tools(
                system=SELF_VERIFY_SYSTEM_PROMPT,
                user=user_message,
                tools=SELF_VERIFY_TOOLS,
                tool_choice={"type": "tool", "name": "submit_self_verdict"},
            )

            if result:
                return {
                    "verdict": result.get("verdict", "unclear"),
                    "derivation": result.get("derivation", ""),
                }
        except Exception as e:
            logger.warning("Self-verification failed for claim: %s", e)

        return {"verdict": "unclear", "derivation": "Self-verification failed"}

    async def _verify_single_claim(self, claim_obj: ClaimToVerify) -> VerificationResultV2:
        """Verify a single claim with dual tracks."""
        claim_text = claim_obj.claim

        if self.self_verify_enabled and self.self_verify_parallel:
            # Run web and self-verify in parallel
            web_task = self._web_verify_claim(claim_text)
            self_task = self.self_verify_claim(claim_text)
            web_result, self_result = await asyncio.gather(web_task, self_task)
        elif self.self_verify_enabled:
            # Run sequentially
            web_result = await self._web_verify_claim(claim_text)
            self_result = await self.self_verify_claim(claim_text)
        else:
            # Web only
            web_result = await self._web_verify_claim(claim_text)
            self_result = None

        # Parse verdicts
        web_verdict = ClaimVerdict(web_result["verdict"])
        self_verdict = ClaimVerdict(self_result["verdict"]) if self_result else None

        # Combine verdicts
        combined_verdict, combined_confidence = _combine_verdicts(web_verdict, self_verdict)

        return VerificationResultV2(
            claim_id=claim_obj.id,
            claim=claim_text,
            web_verdict=web_verdict,
            web_source=web_result.get("source"),
            web_explanation=web_result["explanation"],
            self_verdict=self_verdict,
            self_derivation=self_result.get("derivation") if self_result else None,
            combined_verdict=combined_verdict,
            combined_confidence=combined_confidence,
            web_verified=web_result["web_verified"],
        )

    async def dual_verify(
        self, claims: list[ClaimToVerify]
    ) -> list[VerificationResultV2]:
        """Verify all claims with dual web + self verification.

        Args:
            claims: List of ClaimToVerify objects from the critique.

        Returns:
            List of VerificationResultV2 with combined verdicts.
        """
        self._results_v2 = []

        if not claims:
            return []

        logger.info("Starting dual verification of %d claims", len(claims))

        # Process claims sequentially to yield results as they complete
        # (parallel per-claim with web+self, but claims processed one at a time
        # so we can stream results to the frontend)
        for claim_obj in claims:
            try:
                result = await self._verify_single_claim(claim_obj)
                self._results_v2.append(result)
                logger.info(
                    "Claim %s: web=%s, self=%s, combined=%s (conf=%d)",
                    claim_obj.id,
                    result.web_verdict.value,
                    result.self_verdict.value if result.self_verdict else "N/A",
                    result.combined_verdict.value,
                    result.combined_confidence,
                )
            except Exception as e:
                logger.error("Failed to verify claim %s: %s", claim_obj.id, e)
                self._results_v2.append(
                    VerificationResultV2(
                        claim_id=claim_obj.id,
                        claim=claim_obj.claim,
                        web_verdict=ClaimVerdict.UNCLEAR,
                        web_source=None,
                        web_explanation=f"Verification failed: {e}",
                        self_verdict=None,
                        self_derivation=None,
                        combined_verdict=ClaimVerdict.UNCLEAR,
                        combined_confidence=0,
                        web_verified=False,
                    )
                )

        return self._results_v2

    def get_results_v2(self) -> list[VerificationResultV2]:
        """Get all v2 verification results from the last run."""
        return self._results_v2.copy()

    # ---- V1 backward compatibility ----

    async def check_claims(
        self, claims: list[str]
    ) -> AsyncGenerator[VerificationResult, None]:
        """V1-compatible: verify each claim and yield results."""
        self._results = []

        for claim in claims:
            web_result = await self._web_verify_claim(claim)

            result = VerificationResult(
                claim=claim,
                verdict=web_result["verdict"],
                source=web_result.get("source"),
                source_title=web_result.get("source_title"),
                explanation=web_result["explanation"],
                web_verified=web_result["web_verified"],
            )

            self._results.append(result)
            yield result

    def get_results(self) -> list[VerificationResult]:
        """Get all v1 verification results from the last run."""
        return self._results.copy()
