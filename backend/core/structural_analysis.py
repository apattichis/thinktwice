"""Structural analysis of text responses.

Provides programmatic measurements of structural properties that LLMs
cannot reliably count themselves. These measurements are injected into
pipeline prompts (gate, critique, refiner, convergence) so the LLM
has accurate data to work with.

This is a general-purpose module — not specific to any benchmark.
"""

import re


def analyze(text: str) -> dict:
    """Compute structural measurements of a text response.

    Returns a dict with all measurable structural properties.
    """
    if not text or not text.strip():
        return {"paragraph_count": 0, "word_count": 0, "sentence_count": 0}

    stripped = text.strip()

    # Paragraph count (double-newline separated)
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', stripped) if p.strip()]

    # Word count
    words = stripped.split()

    # Sentence count (split on sentence-ending punctuation)
    sentences = [s.strip() for s in re.split(r'[.!?]+', stripped) if s.strip()]

    # Bullet/list items
    bullets = re.findall(r'^[\s]*[-*+]\s', stripped, re.MULTILINE)
    numbered = re.findall(r'^[\s]*\d+[.)]\s', stripped, re.MULTILINE)

    # Square bracket placeholders
    placeholders = re.findall(r'\[[\w\s]+\]', stripped)

    # Highlighted sections (*text* or **text**)
    highlights = re.findall(r'\*{1,2}[^*\n]+\*{1,2}', stripped)

    # Quotation wrapping
    starts_with_quote = stripped[0] in '"\'\u201c' if stripped else False
    ends_with_quote = stripped[-1] in '"\'\u201d' if stripped else False

    # Case analysis (only alphabetic chars)
    alpha_chars = [c for c in stripped if c.isalpha()]
    all_upper = all(c.isupper() for c in alpha_chars) if alpha_chars else False
    all_lower = all(c.islower() for c in alpha_chars) if alpha_chars else False

    # All-caps words
    all_caps_words = sum(1 for w in words if w.isalpha() and w.isupper())

    # First/last line
    lines = stripped.split('\n')
    first_line = lines[0].strip() if lines else ""
    last_line = lines[-1].strip() if lines else ""

    # First word of each paragraph
    para_first_words = []
    for p in paragraphs:
        p_words = p.split()
        if p_words:
            para_first_words.append(p_words[0])

    # Letter frequency (compact: only non-zero)
    letter_freq = {}
    for c in stripped.lower():
        if c.isalpha():
            letter_freq[c] = letter_freq.get(c, 0) + 1

    # Section headers (## or ### style)
    section_headers = re.findall(r'^#{1,6}\s+.+', stripped, re.MULTILINE)

    # Contains specific markers
    has_postscript = "p.s." in stripped.lower() or "p.p.s." in stripped.lower()
    has_six_stars = "******" in stripped
    has_json = bool(re.search(r'[\{\[][\s\S]*[\}\]]', stripped))
    has_comma = ',' in stripped

    return {
        "paragraph_count": len(paragraphs),
        "word_count": len(words),
        "sentence_count": len(sentences),
        "bullet_count": len(bullets) + len(numbered),
        "placeholder_count": len(placeholders),
        "placeholders": placeholders[:5],  # first 5 for display
        "highlight_count": len(highlights),
        "starts_with_quote": starts_with_quote,
        "ends_with_quote": ends_with_quote,
        "all_uppercase": all_upper,
        "all_lowercase": all_lower,
        "all_caps_word_count": all_caps_words,
        "first_line_preview": first_line[:80],
        "last_line_preview": last_line[:80],
        "paragraph_first_words": para_first_words,
        "has_postscript": has_postscript,
        "has_six_star_separator": has_six_stars,
        "has_json": has_json,
        "has_comma": has_comma,
        "letter_frequencies": letter_freq,
        "section_header_count": len(section_headers),
    }


def format_for_prompt(analysis: dict) -> str:
    """Format structural analysis for injection into LLM prompts."""
    lines = [
        "STRUCTURAL MEASUREMENTS (programmatic, exact):",
        f"  Paragraphs: {analysis['paragraph_count']}",
        f"  Words: {analysis['word_count']}",
        f"  Sentences: {analysis['sentence_count']}",
        f"  Bullet/list items: {analysis['bullet_count']}",
        f"  Square-bracket placeholders: {analysis['placeholder_count']}",
    ]
    if analysis.get("placeholders"):
        lines.append(f"    Found: {', '.join(analysis['placeholders'])}")
    lines.extend([
        f"  Highlighted sections (*text*): {analysis['highlight_count']}",
        f"  Starts with quotation mark: {'Yes' if analysis['starts_with_quote'] else 'No'}",
        f"  Ends with quotation mark: {'Yes' if analysis['ends_with_quote'] else 'No'}",
        f"  All uppercase: {'Yes' if analysis['all_uppercase'] else 'No'}",
        f"  All lowercase: {'Yes' if analysis['all_lowercase'] else 'No'}",
        f"  ALL-CAPS words: {analysis['all_caps_word_count']}",
        f"  Has postscript (P.S.): {'Yes' if analysis['has_postscript'] else 'No'}",
        f"  Has ****** separator: {'Yes' if analysis['has_six_star_separator'] else 'No'}",
        f"  Contains JSON: {'Yes' if analysis['has_json'] else 'No'}",
        f"  Contains commas: {'Yes' if analysis['has_comma'] else 'No'}",
        f"  First line: \"{analysis['first_line_preview']}\"",
        f"  Last line: \"{analysis['last_line_preview']}\"",
    ])
    if analysis.get("paragraph_first_words"):
        for i, word in enumerate(analysis["paragraph_first_words"][:5], 1):
            lines.append(f"  Paragraph {i} first word: \"{word}\"")
    if analysis.get("section_header_count", 0) > 0:
        lines.append(f"  Section headers (## style): {analysis['section_header_count']}")
    if analysis.get("letter_frequencies"):
        freq = analysis["letter_frequencies"]
        freq_str = ", ".join(f"{k}={v}" for k, v in sorted(freq.items()))
        lines.append(f"  Letter frequencies: {freq_str}")

    return "\n".join(lines)


def format_delta(draft_analysis: dict, refined_analysis: dict) -> str:
    """Format structural differences between draft and refined for the Trust step.

    Highlights ONLY properties that changed, making degradation immediately visible.
    """
    checks = [
        ("Paragraphs", "paragraph_count"),
        ("Words", "word_count"),
        ("Sentences", "sentence_count"),
        ("Bullet/list items", "bullet_count"),
        ("Square-bracket placeholders", "placeholder_count"),
        ("Highlighted sections", "highlight_count"),
        ("ALL-CAPS words", "all_caps_word_count"),
        ("Section headers", "section_header_count"),
    ]
    bool_checks = [
        ("Starts with quotation mark", "starts_with_quote"),
        ("Ends with quotation mark", "ends_with_quote"),
        ("All uppercase", "all_uppercase"),
        ("All lowercase", "all_lowercase"),
        ("Has postscript (P.S.)", "has_postscript"),
        ("Has ****** separator", "has_six_star_separator"),
        ("Contains commas", "has_comma"),
    ]

    changes = []
    for label, key in checks:
        d_val = draft_analysis.get(key, 0)
        r_val = refined_analysis.get(key, 0)
        if d_val != r_val:
            direction = "INCREASED" if r_val > d_val else "DECREASED"
            changes.append(f"  {label}: {d_val} -> {r_val} ({direction})")

    for label, key in bool_checks:
        d_val = draft_analysis.get(key, False)
        r_val = refined_analysis.get(key, False)
        if d_val != r_val:
            d_str = "Yes" if d_val else "No"
            r_str = "Yes" if r_val else "No"
            changes.append(f"  {label}: {d_str} -> {r_str} (CHANGED)")

    if not changes:
        return "STRUCTURAL DELTA: No structural changes detected."

    return "STRUCTURAL DELTA (draft -> refined):\n" + "\n".join(changes)
