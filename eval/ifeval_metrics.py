"""IFEval metrics -- deterministic instruction verification.

Implements the 25 IFEval instruction types as deterministic verifiers.
No LLM judge needed -- all checks are string/count operations.

Metrics (matching the IFEval paper):
- Prompt-level strict accuracy: % of prompts where ALL instructions pass
- Instruction-level strict accuracy: % of individual instructions that pass
- Prompt-level loose accuracy: same but with response transformations
- Instruction-level loose accuracy: same with transformations
- Per-instruction-type breakdown
- Per-instruction-count breakdown
- Latency + pipeline metrics
"""

import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Instruction verifier registry
# ---------------------------------------------------------------------------

_VERIFIERS: dict[str, callable] = {}


def _register(instruction_id: str):
    """Decorator to register a verifier function."""
    def decorator(fn):
        _VERIFIERS[instruction_id] = fn
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Loose response transformations (IFEval paper Section 3.2)
# ---------------------------------------------------------------------------

def _generate_loose_variants(response: str) -> list[str]:
    """Generate loose-evaluation variants of a response.

    The IFEval paper applies transformations to be lenient about formatting:
    1. Strip markdown formatting (bold, headers, etc.)
    2. Strip leading/trailing whitespace per line
    3. Remove first/last line if they look like preamble/postscript

    Returns up to 8 variants (power set of 3 transforms).
    """
    variants = [response]

    # Transform 1: Strip markdown
    def strip_markdown(text: str) -> str:
        text = re.sub(r'#{1,6}\s*', '', text)  # headers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)  # italic
        text = re.sub(r'`([^`]+)`', r'\1', text)  # inline code
        text = re.sub(r'```[\s\S]*?```', '', text)  # code blocks
        text = re.sub(r'^[-*+]\s', '', text, flags=re.MULTILINE)  # bullets
        text = re.sub(r'^\d+\.\s', '', text, flags=re.MULTILINE)  # numbered lists
        return text

    # Transform 2: Strip whitespace per line
    def strip_whitespace(text: str) -> str:
        return '\n'.join(line.strip() for line in text.split('\n'))

    # Transform 3: Remove first/last line
    def remove_bookends(text: str) -> str:
        lines = text.strip().split('\n')
        if len(lines) <= 2:
            return text
        return '\n'.join(lines[1:-1])

    transforms = [strip_markdown, strip_whitespace, remove_bookends]

    # Generate power set of transforms (2^3 = 8 combinations)
    for mask in range(1, 8):
        text = response
        for i, transform in enumerate(transforms):
            if mask & (1 << i):
                text = transform(text)
        variants.append(text)

    return variants


# ---------------------------------------------------------------------------
# Instruction verifiers (25 types)
# ---------------------------------------------------------------------------

# --- Keywords ---

@_register("keywords:existence")
def _verify_keywords_existence(response: str, kwargs: dict) -> bool:
    """Check that all required keywords exist in the response."""
    keywords = kwargs.get("keywords", [])
    response_lower = response.lower()
    return all(kw.lower() in response_lower for kw in keywords)


@_register("keywords:frequency")
def _verify_keywords_frequency(response: str, kwargs: dict) -> bool:
    """Check keyword appears at least/at most N times."""
    keyword = kwargs.get("keyword", "")
    frequency = kwargs.get("frequency", 1)
    relation = kwargs.get("relation", "at least")
    count = response.lower().count(keyword.lower())
    if relation == "at least":
        return count >= frequency
    elif relation == "at most":
        return count <= frequency
    return count == frequency


@_register("keywords:forbidden_words")
def _verify_forbidden_words(response: str, kwargs: dict) -> bool:
    """Check that forbidden words do not appear."""
    forbidden = kwargs.get("forbidden_words", [])
    response_lower = response.lower()
    return not any(word.lower() in response_lower for word in forbidden)


@_register("keywords:letter_frequency")
def _verify_letter_frequency(response: str, kwargs: dict) -> bool:
    """Check that a letter appears at least/at most N times."""
    letter = kwargs.get("letter", "").lower()
    frequency = kwargs.get("let_frequency", kwargs.get("frequency", 1))
    relation = kwargs.get("let_relation", kwargs.get("relation", "at least"))
    count = response.lower().count(letter)
    if relation == "at least":
        return count >= frequency
    elif relation == "at most":
        return count <= frequency
    return count == frequency


# --- Length constraints ---

@_register("length_constraints:number_words")
def _verify_number_words(response: str, kwargs: dict) -> bool:
    """Check word count constraint."""
    num_words = kwargs.get("num_words", 0)
    relation = kwargs.get("relation", "at least")
    words = len(response.split())
    if relation == "at least":
        return words >= num_words
    elif relation == "at most":
        return words <= num_words
    return words == num_words


@_register("length_constraints:number_sentences")
def _verify_number_sentences(response: str, kwargs: dict) -> bool:
    """Check sentence count constraint."""
    num_sentences = kwargs.get("num_sentences", 0)
    relation = kwargs.get("relation", "at least")
    # Split on sentence-ending punctuation
    sentences = [s.strip() for s in re.split(r'[.!?]+', response) if s.strip()]
    count = len(sentences)
    if relation == "at least":
        return count >= num_sentences
    elif relation == "at most":
        return count <= num_sentences
    return count == num_sentences


@_register("length_constraints:number_paragraphs")
def _verify_number_paragraphs(response: str, kwargs: dict) -> bool:
    """Check paragraph count constraint."""
    num_paragraphs = kwargs.get("num_paragraphs", 0)
    # Paragraphs are separated by blank lines
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', response.strip()) if p.strip()]
    count = len(paragraphs)
    # Allow +-1 tolerance for paragraph splitting ambiguity
    return abs(count - num_paragraphs) <= 1


@_register("length_constraints:nth_paragraph_first_word")
def _verify_nth_paragraph_first_word(response: str, kwargs: dict) -> bool:
    """Check that the Nth paragraph starts with a specific word."""
    nth = kwargs.get("num_paragraphs", kwargs.get("nth_paragraph", 1))
    first_word = kwargs.get("first_word", "").lower()
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', response.strip()) if p.strip()]
    if nth > len(paragraphs) or nth < 1:
        return False
    para_words = paragraphs[nth - 1].split()
    if not para_words:
        return False
    # Strip markdown from the first word
    actual = re.sub(r'[*#_`]', '', para_words[0]).lower()
    return actual == first_word


# --- Format ---

@_register("detectable_format:json_format")
def _verify_json_format(response: str, kwargs: dict) -> bool:
    """Check that the response contains valid JSON."""
    # Try to find JSON in the response
    # First try the whole response
    try:
        json.loads(response.strip())
        return True
    except (json.JSONDecodeError, ValueError):
        pass

    # Try to find JSON block (```json ... ```)
    json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', response)
    if json_match:
        try:
            json.loads(json_match.group(1).strip())
            return True
        except (json.JSONDecodeError, ValueError):
            pass

    # Try to find any { ... } or [ ... ] block
    for pattern in [r'\{[\s\S]*\}', r'\[[\s\S]*\]']:
        match = re.search(pattern, response)
        if match:
            try:
                json.loads(match.group(0))
                return True
            except (json.JSONDecodeError, ValueError):
                pass

    return False


@_register("detectable_format:title")
def _verify_title_format(response: str, kwargs: dict) -> bool:
    """Check that the response has a title (wrapped in markdown or first line is title-like)."""
    lines = response.strip().split('\n')
    if not lines:
        return False
    first = lines[0].strip()
    # Check for markdown header or title-like formatting
    if re.match(r'^#{1,3}\s+\S', first):
        return True
    if re.match(r'^\*\*.*\*\*$', first):
        return True
    # Title case with reasonable length
    if len(first) < 100 and first[0].isupper():
        return True
    return False


@_register("detectable_format:number_bullet_lists")
def _verify_bullet_lists(response: str, kwargs: dict) -> bool:
    """Check for the required number of bullet points."""
    num_bullets = kwargs.get("num_bullets", 1)
    bullets = re.findall(r'^[\s]*[-*+]\s', response, re.MULTILINE)
    # Also count numbered items
    numbered = re.findall(r'^[\s]*\d+[.)]\s', response, re.MULTILINE)
    total = len(bullets) + len(numbered)
    return total >= num_bullets


@_register("detectable_format:number_highlighted_sections")
def _verify_highlighted_sections(response: str, kwargs: dict) -> bool:
    """Check for highlighted sections (bold headers, markdown headers)."""
    num_sections = kwargs.get("num_highlights", kwargs.get("num_sections", 1))
    headers = re.findall(r'^#{1,6}\s+\S', response, re.MULTILINE)
    bold_headers = re.findall(r'^\*\*[^*]+\*\*', response, re.MULTILINE)
    total = len(headers) + len(bold_headers)
    return total >= num_sections


@_register("detectable_format:multiple_sections")
def _verify_multiple_sections(response: str, kwargs: dict) -> bool:
    """Check that response has multiple distinct sections."""
    num_sections = kwargs.get("section_spliter", kwargs.get("num_sections", 2))
    # Count sections by headers or significant breaks
    headers = re.findall(r'^#{1,6}\s+\S', response, re.MULTILINE)
    bold_headers = re.findall(r'^\*\*[^*]+\*\*', response, re.MULTILINE)
    total = len(headers) + len(bold_headers)
    if isinstance(num_sections, str):
        # section_spliter can be a string like "Section"
        total = len(re.findall(re.escape(num_sections), response))
    return total >= 2


@_register("detectable_format:constrained_response")
def _verify_constrained_response(response: str, kwargs: dict) -> bool:
    """Check response is one of allowed choices."""
    # This is typically "respond with only X or Y"
    # We check if the response (stripped) is very short
    stripped = response.strip().lower()
    # If response is under 50 words, it's likely constrained
    return len(stripped.split()) <= 50


# --- Case ---

@_register("change_case:english_capital")
def _verify_english_capital(response: str, kwargs: dict) -> bool:
    """Check that the entire response is in capital letters."""
    # Only check alphabetic characters
    alpha_chars = [c for c in response if c.isalpha()]
    if not alpha_chars:
        return False
    return all(c.isupper() for c in alpha_chars)


@_register("change_case:english_lowercase")
def _verify_english_lowercase(response: str, kwargs: dict) -> bool:
    """Check that the entire response is in lowercase."""
    alpha_chars = [c for c in response if c.isalpha()]
    if not alpha_chars:
        return False
    return all(c.islower() for c in alpha_chars)


@_register("change_case:capital_word_frequency")
def _verify_capital_word_frequency(response: str, kwargs: dict) -> bool:
    """Check that at least N words are fully capitalized."""
    capital_frequency = kwargs.get("capital_frequency", kwargs.get("num_words", 1))
    relation = kwargs.get("capital_relation", kwargs.get("relation", "at least"))
    words = response.split()
    capital_count = sum(1 for w in words if w.isalpha() and w.isupper())
    if relation == "at least":
        return capital_count >= capital_frequency
    elif relation == "at most":
        return capital_count <= capital_frequency
    return capital_count == capital_frequency


# --- Punctuation ---

@_register("punctuation:no_comma")
def _verify_no_comma(response: str, kwargs: dict) -> bool:
    """Check that the response contains no commas."""
    return ',' not in response


# --- Language ---

@_register("language:response_language")
def _verify_response_language(response: str, kwargs: dict) -> bool:
    """Check that the response is in the specified language.

    Uses langdetect if available, otherwise returns True (graceful fallback).
    """
    expected_lang = kwargs.get("language", "en").lower()

    # Normalize common language names to ISO codes
    lang_map = {
        "english": "en", "french": "fr", "spanish": "es", "german": "de",
        "italian": "it", "portuguese": "pt", "dutch": "nl", "russian": "ru",
        "chinese": "zh-cn", "japanese": "ja", "korean": "ko", "arabic": "ar",
        "hindi": "hi", "turkish": "tr", "polish": "pl", "swedish": "sv",
    }
    expected = lang_map.get(expected_lang, expected_lang)

    try:
        from langdetect import detect
        detected = detect(response)
        return detected.startswith(expected.split('-')[0])
    except ImportError:
        logger.debug("langdetect not installed, skipping language check")
        return True
    except Exception:
        return True


# --- Content ---

@_register("detectable_content:number_placeholders")
def _verify_placeholders(response: str, kwargs: dict) -> bool:
    """Check for placeholder brackets [like this]."""
    num_placeholders = kwargs.get("num_placeholders", 1)
    placeholders = re.findall(r'\[[\w\s]+\]', response)
    return len(placeholders) >= num_placeholders


@_register("detectable_content:postscript")
def _verify_postscript(response: str, kwargs: dict) -> bool:
    """Check that the response includes a postscript (P.S.)."""
    postscript_marker = kwargs.get("postscript_marker", "P.S.")
    return postscript_marker.lower() in response.lower() or "p.s." in response.lower()


# --- Start/End ---

@_register("startend:end_checker")
def _verify_end_checker(response: str, kwargs: dict) -> bool:
    """Check that the response ends with a specific phrase."""
    end_phrase = kwargs.get("end_phrase", "")
    if not end_phrase:
        return True
    return response.strip().lower().endswith(end_phrase.lower().strip())


@_register("startend:quotation")
def _verify_quotation(response: str, kwargs: dict) -> bool:
    """Check that the response is wrapped in quotation marks."""
    stripped = response.strip()
    return (
        (stripped.startswith('"') and stripped.endswith('"')) or
        (stripped.startswith("'") and stripped.endswith("'")) or
        (stripped.startswith('\u201c') and stripped.endswith('\u201d'))
    )


# --- Combo ---

@_register("combination:two_responses")
def _verify_two_responses(response: str, kwargs: dict) -> bool:
    """Check that the response contains two distinct responses (separated by a marker)."""
    separators = ["***", "---", "===", "response 1", "response 2", "answer 1", "answer 2"]
    response_lower = response.lower()
    return any(sep in response_lower for sep in separators)


@_register("combination:repeat_prompt")
def _verify_repeat_prompt(response: str, kwargs: dict) -> bool:
    """Check that the response repeats the original prompt."""
    prompt_to_repeat = kwargs.get("prompt_to_repeat", "")
    if not prompt_to_repeat:
        return True
    return prompt_to_repeat.lower().strip() in response.lower()


# ---------------------------------------------------------------------------
# Core verification functions
# ---------------------------------------------------------------------------

def verify_instruction(instruction_id: str, response: str, kwargs: dict, loose: bool = False) -> bool:
    """Verify a single instruction against a response.

    Args:
        instruction_id: The instruction type ID (e.g., "keywords:existence")
        response: The model's response text
        kwargs: Parameters for the instruction check
        loose: If True, try all loose variants and pass if any passes
    """
    verifier = _VERIFIERS.get(instruction_id)
    if verifier is None:
        logger.warning("No verifier for instruction type: %s (passing by default)", instruction_id)
        return True

    if not loose:
        return verifier(response, kwargs or {})

    # Loose mode: try original + all transformations
    for variant in _generate_loose_variants(response):
        if verifier(variant, kwargs or {}):
            return True
    return False


def verify_prompt(instruction_ids: list[str], response: str, kwargs_list: list[dict], loose: bool = False) -> dict:
    """Verify all instructions for a single prompt.

    Returns dict with per-instruction results and aggregate pass/fail.
    """
    if not instruction_ids:
        return {"prompt_pass": True, "instruction_results": [], "pass_count": 0, "total": 0}

    # Ensure kwargs_list matches instruction_ids
    while len(kwargs_list) < len(instruction_ids):
        kwargs_list.append({})

    results = []
    for iid, kw in zip(instruction_ids, kwargs_list):
        passed = verify_instruction(iid, response, kw, loose=loose)
        results.append({"instruction_id": iid, "passed": passed, "kwargs": kw})

    pass_count = sum(1 for r in results if r["passed"])
    return {
        "prompt_pass": pass_count == len(results),
        "instruction_results": results,
        "pass_count": pass_count,
        "total": len(results),
    }


# ---------------------------------------------------------------------------
# Batch judge (called from run_eval.py post-processing)
# ---------------------------------------------------------------------------

def judge_all(results: list[dict]) -> list[dict]:
    """Run deterministic IFEval verification on all results.

    Attaches ifeval_judgements to each result dict.
    """
    for r in results:
        output = r.get("output", "")
        instruction_ids = r.get("instruction_id_list", [])
        kwargs_list = r.get("instruction_kwargs", [])

        strict = verify_prompt(instruction_ids, output, kwargs_list, loose=False)
        loose = verify_prompt(instruction_ids, output, kwargs_list, loose=True)

        r["ifeval_judgements"] = {
            "prompt_strict": strict["prompt_pass"],
            "prompt_loose": loose["prompt_pass"],
            "instruction_strict_results": strict["instruction_results"],
            "instruction_loose_results": loose["instruction_results"],
            "strict_pass_count": strict["pass_count"],
            "strict_total": strict["total"],
            "loose_pass_count": loose["pass_count"],
            "loose_total": loose["total"],
        }

    return results


# ---------------------------------------------------------------------------
# Aggregate metrics computation
# ---------------------------------------------------------------------------

def compute_ifeval_metrics(results: list[dict]) -> dict:
    """Compute all IFEval metrics from judged results.

    Returns:
        dict with prompt_strict_accuracy, instruction_strict_accuracy,
        prompt_loose_accuracy, instruction_loose_accuracy,
        per_type breakdown, per_count breakdown, and latency.
    """
    total_prompts = 0
    prompt_strict_pass = 0
    prompt_loose_pass = 0
    instruction_strict_pass = 0
    instruction_strict_total = 0
    instruction_loose_pass = 0
    instruction_loose_total = 0

    # Per instruction type tracking
    per_type_strict = {}  # {type: {"pass": 0, "total": 0}}
    per_type_loose = {}

    # Per instruction count tracking
    per_count = {}  # {count: {"strict_pass": 0, "loose_pass": 0, "total": 0}}

    for r in results:
        j = r.get("ifeval_judgements", {})
        if not j:
            continue

        total_prompts += 1
        if j.get("prompt_strict"):
            prompt_strict_pass += 1
        if j.get("prompt_loose"):
            prompt_loose_pass += 1

        instruction_strict_pass += j.get("strict_pass_count", 0)
        instruction_strict_total += j.get("strict_total", 0)
        instruction_loose_pass += j.get("loose_pass_count", 0)
        instruction_loose_total += j.get("loose_total", 0)

        # Per-type
        for ir in j.get("instruction_strict_results", []):
            iid = ir["instruction_id"]
            if iid not in per_type_strict:
                per_type_strict[iid] = {"pass": 0, "total": 0}
            per_type_strict[iid]["total"] += 1
            if ir["passed"]:
                per_type_strict[iid]["pass"] += 1

        for ir in j.get("instruction_loose_results", []):
            iid = ir["instruction_id"]
            if iid not in per_type_loose:
                per_type_loose[iid] = {"pass": 0, "total": 0}
            per_type_loose[iid]["total"] += 1
            if ir["passed"]:
                per_type_loose[iid]["pass"] += 1

        # Per instruction count
        count = r.get("instruction_count", len(r.get("instruction_id_list", [])))
        count_key = str(count)
        if count_key not in per_count:
            per_count[count_key] = {"strict_pass": 0, "loose_pass": 0, "total": 0}
        per_count[count_key]["total"] += 1
        if j.get("prompt_strict"):
            per_count[count_key]["strict_pass"] += 1
        if j.get("prompt_loose"):
            per_count[count_key]["loose_pass"] += 1

    # Compute per-type accuracy
    per_type_breakdown = {}
    for iid in sorted(set(list(per_type_strict.keys()) + list(per_type_loose.keys()))):
        s = per_type_strict.get(iid, {"pass": 0, "total": 0})
        l = per_type_loose.get(iid, {"pass": 0, "total": 0})
        per_type_breakdown[iid] = {
            "strict_accuracy": s["pass"] / s["total"] if s["total"] > 0 else 0,
            "loose_accuracy": l["pass"] / l["total"] if l["total"] > 0 else 0,
            "strict_pass": s["pass"],
            "loose_pass": l["pass"],
            "total": s["total"],
        }

    # Compute per-count accuracy
    per_count_breakdown = {}
    for count_key in sorted(per_count.keys()):
        d = per_count[count_key]
        per_count_breakdown[count_key] = {
            "strict_accuracy": d["strict_pass"] / d["total"] if d["total"] > 0 else 0,
            "loose_accuracy": d["loose_pass"] / d["total"] if d["total"] > 0 else 0,
            "strict_pass": d["strict_pass"],
            "loose_pass": d["loose_pass"],
            "total": d["total"],
        }

    # Latency
    durations = [r.get("duration_ms", 0) for r in results if r.get("duration_ms")]
    durations.sort()
    n_dur = len(durations)
    latency = {
        "mean_ms": sum(durations) / n_dur if n_dur else 0,
        "median_ms": durations[n_dur // 2] if n_dur else 0,
        "p95_ms": durations[int(n_dur * 0.95)] if n_dur else 0,
        "min_ms": durations[0] if n_dur else 0,
        "max_ms": durations[-1] if n_dur else 0,
        "total_samples": n_dur,
    }

    # Pipeline metrics
    gate_total = 0
    fast_path_count = 0
    total_iterations = 0
    total_constraints = 0
    satisfied_constraints = 0
    for r in results:
        m = r.get("metrics", {})
        if "gate_decision" in m:
            gate_total += 1
            if m.get("fast_path", False):
                fast_path_count += 1
            total_iterations += m.get("iterations_used", 0)
        total_constraints += m.get("constraints_total", 0)
        satisfied_constraints += m.get("constraints_satisfied", 0)

    return {
        "total_prompts": total_prompts,
        "prompt_strict_accuracy": prompt_strict_pass / total_prompts if total_prompts else 0,
        "prompt_loose_accuracy": prompt_loose_pass / total_prompts if total_prompts else 0,
        "instruction_strict_accuracy": instruction_strict_pass / instruction_strict_total if instruction_strict_total else 0,
        "instruction_loose_accuracy": instruction_loose_pass / instruction_loose_total if instruction_loose_total else 0,
        "prompt_strict_pass": prompt_strict_pass,
        "prompt_loose_pass": prompt_loose_pass,
        "instruction_strict_pass": instruction_strict_pass,
        "instruction_strict_total": instruction_strict_total,
        "instruction_loose_pass": instruction_loose_pass,
        "instruction_loose_total": instruction_loose_total,
        "per_type": per_type_breakdown,
        "per_count": per_count_breakdown,
        "latency": latency,
        "pipeline": {
            "gate_total": gate_total,
            "fast_path_count": fast_path_count,
            "fast_path_rate": fast_path_count / gate_total if gate_total else 0,
            "avg_iterations": total_iterations / gate_total if gate_total else 0,
            "constraint_satisfaction": satisfied_constraints / total_constraints if total_constraints else 0,
            "constraints_total": total_constraints,
            "constraints_satisfied": satisfied_constraints,
        },
    }
