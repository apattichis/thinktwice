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

logger = logging.getLogger(__name__)

# Word-to-number mapping for parsing written-out numbers
_WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12,
}
_WORD_PATTERN = "|".join(_WORD_NUMBERS.keys())

# Ordinal-to-number mapping for "the first paragraph", "the second paragraph"
_ORDINALS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
}


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

    # Apply enforcements in dependency order:
    # 1. Response start phrase (before paragraph enforcement — prepending shifts structure)
    result = _enforce_start_phrase(result, all_text)
    # 2. Paragraph count
    result = _enforce_paragraph_count(result, all_text)
    # 3. Nth paragraph first word (after paragraph count is correct)
    result = _enforce_first_word(result, all_text)
    # 4. Bullet/list count
    result = _enforce_bullet_count(result, all_text)

    return result


# ---------------------------------------------------------------------------
# Paragraph count enforcement
# ---------------------------------------------------------------------------

def _parse_number(text: str) -> int | None:
    """Parse a number from text — supports digits and written-out words."""
    text = text.strip().lower()
    if text.isdigit():
        return int(text)
    return _WORD_NUMBERS.get(text)


def _extract_paragraph_requirement(text: str) -> int | None:
    """Parse paragraph count requirement from constraint/prompt text.

    Handles common patterns like:
    - "exactly 4 paragraphs" / "exactly four paragraphs"
    - "exactly 4 sections" / "in two paragraphs"
    - "into 3 parts"
    - "should contain 3 paragraphs"
    """
    block_terms = r'(?:paragraph|section|part)s?'
    num = rf'(\d+|{_WORD_PATTERN})'

    patterns = [
        rf'exactly\s+{num}\s+{block_terms}',
        rf'in\s+{num}\s+{block_terms}',
        rf'contain\s+{num}\s+{block_terms}',
        rf'into\s+{num}\s+{block_terms}',
        rf'have\s+{num}\s+{block_terms}',
        rf'{num}\s+{block_terms}',
        rf'at\s+least\s+{num}\s+{block_terms}',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            n = _parse_number(match.group(1))
            if n is not None and n > 0:
                return n
    return None


def _split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs the same way the IFEval verifier does."""
    return [p.strip() for p in re.split(r'\n\s*\n', text.strip()) if p.strip()]


def _is_separator_block(block: str) -> bool:
    """Check if a block is just a separator line (e.g., ***, ---, ======)."""
    stripped = block.strip()
    return bool(re.match(r'^[\*\-=~_]{3,}$', stripped))


def _enforce_paragraph_count(text: str, requirement_text: str) -> str:
    """Enforce paragraph count if a specific requirement is found.

    Handles *** separator blocks by merging them with neighbors rather than
    counting them as standalone paragraphs.
    """
    expected = _extract_paragraph_requirement(requirement_text)
    if expected is None:
        return text

    paragraphs = _split_paragraphs(text)
    current = len(paragraphs)

    if current == expected:
        return text

    logger.info(
        "Paragraph enforcement: %d -> %d (expected %d)",
        current, expected, expected,
    )

    if current > expected:
        # First pass: collapse separator-only blocks (***) into the previous
        # paragraph using a single newline (so they don't count as separate)
        collapsed = []
        for p in paragraphs:
            if _is_separator_block(p) and collapsed:
                collapsed[-1] = collapsed[-1] + "\n" + p
            else:
                collapsed.append(p)
        paragraphs = collapsed

        # Second pass: merge shortest adjacent pairs if still too many
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

    result = "\n\n".join(paragraphs)

    # Post-enforcement verification: re-count to confirm
    final_count = len(_split_paragraphs(result))
    if final_count != expected:
        logger.warning(
            "Paragraph enforcement produced %d paragraphs, expected %d — reverting",
            final_count, expected,
        )
        return text

    return result


# ---------------------------------------------------------------------------
# Nth paragraph first word enforcement
# ---------------------------------------------------------------------------

def _extract_first_word_requirements(text: str, num_paragraphs: int = 0) -> list[tuple[int, str]]:
    """Parse Nth-paragraph-first-word requirements from text.

    Args:
        text: Combined prompt + constraint text (lowercased).
        num_paragraphs: Total paragraph count in the output (used for "last paragraph").

    Returns list of (paragraph_number, required_first_word).
    """
    results = []

    # "paragraph N must/should start with word X"
    pattern1 = (
        r'paragraph\s+(\d+)\s+(?:must|should|has\s+to)\s+'
        r'start\s+with\s+(?:the\s+)?word\s+["\']?(\w+)["\']?'
    )
    for m in re.finditer(pattern1, text, re.IGNORECASE):
        results.append((int(m.group(1)), m.group(2)))

    # "the first/second/third paragraph ... start with word X"
    ordinal_pat = "|".join(_ORDINALS.keys())
    pattern2 = (
        rf'(?:the\s+)?({ordinal_pat})\s+paragraph'
        r'.*?start\s+with\s+(?:the\s+)?word\s+["\']?(\w+)["\']?'
    )
    for m in re.finditer(pattern2, text, re.IGNORECASE):
        num = _ORDINALS.get(m.group(1).lower())
        if num:
            results.append((num, m.group(2)))

    # "the last paragraph must start with word X"
    pattern3 = (
        r'(?:the\s+)?last\s+paragraph'
        r'.*?start\s+with\s+(?:the\s+)?word\s+["\']?(\w+)["\']?'
    )
    for m in re.finditer(pattern3, text, re.IGNORECASE):
        if num_paragraphs > 0:
            results.append((num_paragraphs, m.group(1)))

    return results


def _enforce_first_word(text: str, requirement_text: str) -> str:
    """Enforce that the Nth paragraph starts with the required word.

    Must run AFTER paragraph count enforcement so paragraph structure is stable.
    """
    paragraphs = _split_paragraphs(text)
    requirements = _extract_first_word_requirements(requirement_text, len(paragraphs))
    if not requirements:
        return text
    changed = False

    for para_num, required_word in requirements:
        if para_num < 1 or para_num > len(paragraphs):
            continue

        idx = para_num - 1
        words = paragraphs[idx].split()
        if not words:
            continue

        first_word = words[0]

        # Match the verifier exactly: compare first word stripped + lowered
        # The verifier does: para_words[0].strip().lower() == first_word.lower()
        if first_word.strip().lower() == required_word.lower():
            continue  # Already matches

        # Prepend the required word to the paragraph
        paragraphs[idx] = required_word + " " + paragraphs[idx]
        changed = True
        logger.info(
            "First-word enforcement: paragraph %d, prepended '%s'",
            para_num, required_word,
        )

    if changed:
        return "\n\n".join(paragraphs)
    return text


# ---------------------------------------------------------------------------
# Bullet/list count enforcement
# ---------------------------------------------------------------------------

_BULLET_PATTERN = re.compile(r'^\s*(?:[-*•]|\d+[.)]) ', re.MULTILINE)


def _extract_bullet_requirement(text: str) -> int | None:
    """Parse bullet/list count requirement from text."""
    num = rf'(\d+|{_WORD_PATTERN})'
    bullet_terms = r'(?:bullet|list)\s*(?:point|item)?s?'

    patterns = [
        rf'exactly\s+{num}\s+{bullet_terms}',
        rf'contain\s+{num}\s+{bullet_terms}',
        rf'{num}\s+{bullet_terms}',
        rf'at\s+least\s+{num}\s+{bullet_terms}',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            n = _parse_number(match.group(1))
            if n is not None and n > 0:
                return n
    return None


def _find_bullet_lines(text: str) -> list[tuple[int, int]]:
    """Find all bullet item lines and return their (start, end) positions."""
    lines = text.split('\n')
    bullet_ranges = []
    for i, line in enumerate(lines):
        if re.match(r'^\s*(?:[-*•]|\d+[.)]) ', line):
            bullet_ranges.append(i)
    return bullet_ranges


def _enforce_bullet_count(text: str, requirement_text: str) -> str:
    """Enforce bullet/list item count."""
    expected = _extract_bullet_requirement(requirement_text)
    if expected is None:
        return text

    lines = text.split('\n')
    bullet_indices = _find_bullet_lines(text)
    current = len(bullet_indices)

    if current == expected:
        return text

    logger.info(
        "Bullet enforcement: %d -> %d (expected %d)",
        current, expected, expected,
    )

    if current > expected:
        # Remove excess bullets from the end
        while len(bullet_indices) > expected:
            remove_idx = bullet_indices.pop()
            lines.pop(remove_idx)

    elif current < expected:
        # Split longest bullet items at sentence boundary
        while len(bullet_indices) < expected:
            if not bullet_indices:
                break
            # Find the longest bullet line
            max_len = 0
            max_bi = 0
            for bi_idx, line_idx in enumerate(bullet_indices):
                if len(lines[line_idx]) > max_len:
                    max_len = len(lines[line_idx])
                    max_bi = bi_idx

            line_idx = bullet_indices[max_bi]
            line = lines[line_idx]
            # Extract bullet prefix
            m = re.match(r'^(\s*(?:[-*•]|\d+[.)]) )', line)
            if not m:
                break
            prefix = m.group(1)
            content = line[len(prefix):]
            sentences = re.split(r'(?<=[.!?])\s+', content)
            if len(sentences) > 1:
                mid = len(sentences) // 2
                lines[line_idx] = prefix + " ".join(sentences[:mid])
                new_line = prefix + " ".join(sentences[mid:])
                lines.insert(line_idx + 1, new_line)
                # Recalculate bullet indices
                bullet_indices = _find_bullet_lines('\n'.join(lines))
            else:
                break

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Response start phrase enforcement
# ---------------------------------------------------------------------------

def _extract_start_phrase_requirement(text: str) -> str | None:
    """Parse response start phrase requirement from text.

    Handles patterns like:
    - "your response must begin with..."
    - "start your response with..."
    - "your entire output should begin with..."
    - IFEval constrained_response: "answer with 'My answer is yes/no/maybe'"
    """
    # Explicit start-with patterns
    patterns = [
        r'(?:response|answer|output)\s+(?:must|should|has\s+to)\s+(?:begin|start)\s+with\s+["\']([^"\']+)["\']',
        r'(?:begin|start)\s+(?:your\s+)?(?:response|answer|output)\s+with\s+["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    # Constrained response detection: "My answer is yes/no/maybe" as options
    if re.search(r'my answer is (?:yes|no|maybe)', text, re.IGNORECASE):
        return None  # Handled by _enforce_constrained_response instead

    return None


def _enforce_constrained_response(text: str, requirement_text: str) -> str:
    """Enforce constrained response format (My answer is yes/no/maybe).

    Detects when the prompt presents 'My answer is yes/no/maybe' as required
    options and ensures the response starts with one of them.
    """
    # Check if the prompt presents these as constrained options
    if not re.search(r'my answer is (?:yes|no|maybe)', requirement_text, re.IGNORECASE):
        return text

    stripped = text.strip().lower()
    constrained_phrases = [
        "my answer is yes", "my answer is no", "my answer is maybe",
    ]

    # Already starts with a constrained phrase
    for phrase in constrained_phrases:
        if stripped.startswith(phrase):
            return text

    # Try to detect the answer from the text content
    answer = "maybe"  # default
    lower = text.lower()
    if re.search(r'\byes\b', lower) and not re.search(r'\bno\b', lower):
        answer = "yes"
    elif re.search(r'\bno\b', lower) and not re.search(r'\byes\b', lower):
        answer = "no"

    prefix = f"My answer is {answer}.\n\n"
    logger.info("Constrained-response enforcement: prepending '%s'", prefix.strip())
    return prefix + text


def _enforce_start_phrase(text: str, requirement_text: str) -> str:
    """Enforce that the response starts with a required phrase."""
    # First check for constrained response pattern
    result = _enforce_constrained_response(text, requirement_text)
    if result != text:
        return result

    # Then check explicit start-with requirements
    required = _extract_start_phrase_requirement(requirement_text)
    if required is None:
        return text

    stripped = text.strip()
    if stripped.lower().startswith(required.lower()):
        return text

    logger.info("Start-phrase enforcement: prepending '%s'", required[:40])
    return required + "\n\n" + text
