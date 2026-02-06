"""Tests for the verifier module with dual verification."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from core.verifier import Verifier, _combine_verdicts
from core.schemas import ClaimToVerify, ClaimVerdict, VerificationResult
from models.schemas import SearchResult


def _make_claim(id: str, claim: str) -> ClaimToVerify:
    return ClaimToVerify(id=id, claim=claim, source_constraint="C1", source_quote="...")


@pytest.fixture
def verifier(mock_llm, mock_search):
    return Verifier(mock_llm, mock_search, self_verify_enabled=True, self_verify_parallel=True)


class TestCombineVerdicts:
    def test_both_verified(self):
        verdict, conf = _combine_verdicts(ClaimVerdict.VERIFIED, ClaimVerdict.VERIFIED)
        assert verdict == ClaimVerdict.VERIFIED
        assert conf == 90

    def test_both_refuted(self):
        verdict, conf = _combine_verdicts(ClaimVerdict.REFUTED, ClaimVerdict.REFUTED)
        assert verdict == ClaimVerdict.REFUTED
        assert conf == 90

    def test_conflict_verified_refuted(self):
        verdict, conf = _combine_verdicts(ClaimVerdict.VERIFIED, ClaimVerdict.REFUTED)
        assert verdict == ClaimVerdict.UNCLEAR
        assert conf == 25

    def test_web_verified_self_unclear(self):
        verdict, conf = _combine_verdicts(ClaimVerdict.VERIFIED, ClaimVerdict.UNCLEAR)
        assert verdict == ClaimVerdict.VERIFIED
        assert conf == 60

    def test_no_self_verify(self):
        verdict, conf = _combine_verdicts(ClaimVerdict.VERIFIED, None)
        assert verdict == ClaimVerdict.VERIFIED
        assert conf == 65


class TestVerifier:
    @pytest.mark.asyncio
    async def test_dual_verify_returns_results(self, verifier, mock_llm, mock_search):
        """Test dual verification with web + self."""
        mock_search.query.return_value = [
            SearchResult(title="Source", url="https://example.com", snippet="Water boils at 100C"),
        ]
        # First call: web verify, second call: self verify
        mock_llm.generate_with_tools.side_effect = [
            {"verdict": "verified", "explanation": "Confirmed by source"},
            {"derivation": "Water boils at 100C at sea level", "verdict": "verified"},
        ]

        claims = [_make_claim("V1", "Water boils at 100C")]
        results = await verifier.dual_verify(claims)

        assert len(results) == 1
        assert results[0].claim_id == "V1"
        assert results[0].web_verdict == ClaimVerdict.VERIFIED
        assert results[0].self_verdict == ClaimVerdict.VERIFIED
        assert results[0].combined_verdict == ClaimVerdict.VERIFIED
        assert results[0].combined_confidence == 90

    @pytest.mark.asyncio
    async def test_dual_verify_handles_no_search(self, verifier, mock_llm, mock_search):
        """Test fallback when no search results."""
        mock_search.query.return_value = None
        mock_llm.generate_with_tools.side_effect = [
            {"verdict": "unclear", "explanation": "No web sources"},
            {"derivation": "Known fact", "verdict": "verified"},
        ]

        claims = [_make_claim("V1", "Some claim")]
        results = await verifier.dual_verify(claims)

        assert len(results) == 1
        assert results[0].web_verified == False
        assert results[0].self_verdict == ClaimVerdict.VERIFIED

    @pytest.mark.asyncio
    async def test_dual_verify_empty_claims(self, verifier):
        """Test with empty claims list."""
        results = await verifier.dual_verify([])
        assert results == []

    @pytest.mark.asyncio
    async def test_dual_verify_handles_error(self, verifier, mock_llm, mock_search):
        """Test graceful handling when verification fails."""
        mock_search.query.side_effect = Exception("Search error")
        mock_llm.generate_with_tools.side_effect = Exception("API error")

        claims = [_make_claim("V1", "Some claim")]
        results = await verifier.dual_verify(claims)

        assert len(results) == 1
        assert results[0].combined_verdict == ClaimVerdict.UNCLEAR
