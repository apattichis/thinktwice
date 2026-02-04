"""Verifier module - fact-checks claims against web sources."""

from typing import AsyncGenerator

from services.llm import LLMService
from services.search import SearchService
from models.schemas import VerificationResult, SearchResult


VERIFY_SYSTEM_PROMPT = """You are a fact-checker. Evaluate whether the given claim is supported by the search results.

Respond with a JSON object containing:
- verdict: "verified" (if search results clearly support the claim), "refuted" (if search results contradict the claim), or "unclear" (if evidence is insufficient or mixed)
- explanation: A brief explanation of your verdict based on the sources

Be rigorous. Only mark as "verified" if the search results explicitly support the claim.
If there's any ambiguity or the results don't directly address the claim, mark as "unclear"."""


VERIFY_FALLBACK_PROMPT = """You are a fact-checker. Evaluate the given claim based on your knowledge.

NOTE: You do not have access to web search results for this claim. Evaluate based on your training data.

Respond with a JSON object containing:
- verdict: "verified" (if you are highly confident the claim is accurate), "refuted" (if you are highly confident the claim is false), or "unclear" (if you are uncertain)
- explanation: A brief explanation of your verdict

Be conservative. Without web sources to verify against, lean toward "unclear" unless you are very confident."""


VERIFY_TOOLS = [
    {
        "name": "submit_verdict",
        "description": "Submit the verification verdict for a claim",
        "input_schema": {
            "type": "object",
            "properties": {
                "verdict": {
                    "type": "string",
                    "enum": ["verified", "refuted", "unclear"],
                    "description": "The verdict for the claim",
                },
                "explanation": {
                    "type": "string",
                    "description": "Brief explanation of the verdict",
                },
            },
            "required": ["verdict", "explanation"],
        },
    }
]


class Verifier:
    """Fact-checks claims against web search results."""

    def __init__(self, llm: LLMService, search: SearchService):
        self.llm = llm
        self.search = search
        self._results: list[VerificationResult] = []

    def _format_results(self, results: list[SearchResult]) -> str:
        """Format search results for the LLM prompt."""
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"{i}. {r.title}\n   URL: {r.url}\n   {r.snippet}")
        return "\n\n".join(formatted)

    async def check_claims(
        self, claims: list[str]
    ) -> AsyncGenerator[VerificationResult, None]:
        """
        Verify each claim and yield results as they complete.

        This is an async generator that yields VerificationResult objects
        as each claim is checked.
        """
        self._results = []

        for claim in claims:
            # Search for the claim
            search_results = await self.search.query(claim)

            if search_results:
                # Evaluate claim against search results
                user_message = f"""Claim: {claim}

Search Results:
{self._format_results(search_results)}

Evaluate whether the search results support, refute, or are unclear about this claim.
Use the submit_verdict tool to provide your verdict."""

                verdict_data = await self.llm.generate_with_tools(
                    system=VERIFY_SYSTEM_PROMPT,
                    user=user_message,
                    tools=VERIFY_TOOLS,
                    tool_choice={"type": "tool", "name": "submit_verdict"},
                )

                if verdict_data:
                    result = VerificationResult(
                        claim=claim,
                        verdict=verdict_data.get("verdict", "unclear"),
                        source=search_results[0].url if search_results else None,
                        source_title=search_results[0].title if search_results else None,
                        explanation=verdict_data.get("explanation", ""),
                        web_verified=True,
                    )
                else:
                    result = VerificationResult(
                        claim=claim,
                        verdict="unclear",
                        source=search_results[0].url if search_results else None,
                        source_title=search_results[0].title if search_results else None,
                        explanation="Unable to evaluate claim",
                        web_verified=True,
                    )

            else:
                # Fallback: use Claude's knowledge
                user_message = f"""Claim: {claim}

Evaluate this claim based on your knowledge (no web search available).
Use the submit_verdict tool to provide your verdict."""

                verdict_data = await self.llm.generate_with_tools(
                    system=VERIFY_FALLBACK_PROMPT,
                    user=user_message,
                    tools=VERIFY_TOOLS,
                    tool_choice={"type": "tool", "name": "submit_verdict"},
                )

                explanation = ""
                if verdict_data:
                    explanation = verdict_data.get("explanation", "")
                explanation += " (verified against AI knowledge only, not web sources)"

                result = VerificationResult(
                    claim=claim,
                    verdict=verdict_data.get("verdict", "unclear") if verdict_data else "unclear",
                    source=None,
                    source_title=None,
                    explanation=explanation,
                    web_verified=False,
                )

            self._results.append(result)
            yield result

    def get_results(self) -> list[VerificationResult]:
        """Get all verification results from the last run."""
        return self._results.copy()
