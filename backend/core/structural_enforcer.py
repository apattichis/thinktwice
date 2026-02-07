"""Structural enforcement - programmatic post-processing for structural constraints.

Addresses a fundamental LLM limitation: models cannot reliably count or enforce
exact structural properties like paragraph counts. This module parses structural
requirements from constraint descriptions and applies deterministic fixes.

This is a general-purpose module -- any prompt with structural requirements
(paragraph counts, case requirements, etc.) benefits from this enforcement.
"""

import logging
import re

from core.schemas import Constraint
from core.structural_analysis import analyze

logger = logging.getLogger(__name__)


def enforce(text: str, constraints: list[Constraint], original_prompt: str) -> str:
    """Apply programmatic structural enforcement based on constraints.

    Parses constraint descriptions and the original prompt for structural
    requirements, then applies safe deterministic fixes.

    Args:
        text: The pipeline's final output text.
        constraints: Decomposed constraints from the pipeline.
        original_prompt: The user's original input prompt.

    Returns:
        The text with structural fixes applied, or the original text if
        no fixes were needed or safe to apply.
    """
    result = text

    # Combine constraint descriptions + original prompt for requirement parsing
    all_text = original_prompt.lower() + " " + " ".join(
        c.description.lower() for c in constraints
    )

    # Paragraph count enforcement
    result = _enforce_paragraph_count(result, all_text)

    return result


def _extract_paragraph_requirement(text: str) -> int | None:
    """Parse paragraph count requirement from constraint/prompt text.

    Handles common patterns like:
    - "exactly 4 paragraphs"
    - "should contain 3 paragraphs"
    - "reply in 5 paragraphs"
    - "with exactly 2 paragraphs"
    """
    # Match "exactly N paragraphs" or "N paragraphs" (with word boundary)
    patterns = [
        r'exactly\s+(\d+)\s+paragraph',
        r'contain\s+(\d+)\s+paragraph',
        r'(\d+)\s+paragraph',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def _enforce_paragraph_count(text: str, requirement_text: str) -> str:
    """Enforce paragraph count if a specific requirement is found.

    Merges adjacent short paragraphs (if too many) or splits long
    paragraphs at sentence boundaries (if too few).
    """
    expected = _extract_paragraph_requirement(requirement_text)
    if expected is None:
        return text

    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text.strip()) if p.strip()]
    current = len(paragraphs)

    if current == expected:
        return text

    logger.info(
        "Paragraph enforcement: %d -> %d (expected %d)",
        current, expected, expected,
    )

    if current > expected:
        # Merge shortest adjacent paragraph pairs until count matches
        while len(paragraphs) > expected:
            min_combined = float('inf')
            min_idx = 0
            for i in range(len(paragraphs) - 1):
                combined = len(paragraphs[i]) + len(paragraphs[i + 1])
                if combined < min_combined:
                    min_combined = combined
                    min_idx = i
            paragraphs[min_idx] = paragraphs[min_idx] + " " + paragraphs[min_idx + 1]
            paragraphs.pop(min_idx + 1)

    elif current < expected:
        # Split longest paragraphs at sentence boundaries
        while len(paragraphs) < expected:
            max_len = 0
            max_idx = 0
            for i, p in enumerate(paragraphs):
                if len(p) > max_len:
                    max_len = len(p)
                    max_idx = i
            # Split at sentence boundary
            sentences = re.split(r'(?<=[.!?])\s+', paragraphs[max_idx])
            if len(sentences) > 1:
                mid = len(sentences) // 2
                paragraphs[max_idx] = " ".join(sentences[:mid])
                paragraphs.insert(max_idx + 1, " ".join(sentences[mid:]))
            else:
                logger.warning(
                    "Cannot split paragraph further (no sentence boundary)"
                )
                break

    return "\n\n".join(paragraphs)
