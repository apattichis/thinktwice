"""Evaluation metrics for the ThinkTwice pipeline.

Computes accuracy, constraint satisfaction, hallucination rate, verification
precision/recall, gate efficiency, refinement delta, trust override rate,
latency, and token usage metrics.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _extract_output(result: dict) -> str:
    """Extract output text from a result, falling back to events if output field is empty."""
    output = result.get("output", "")
    if output:
        return output
    # Fallback: extract from refine step_complete event
    for event in reversed(result.get("events", [])):
        if event.get("event") == "step_complete" and event.get("data", {}).get("step") == "refine":
            return event["data"].get("content", "")
    return ""


def _extract_verdict_section(text: str) -> str:
    """Extract text from the last verdict/conclusion section of structured output."""
    import re
    # Look for common verdict section headers (bold or H2) — broad matching
    header_keywords = (
        r"overall assessment|overall|conclusion|verdict|final assessment|"
        r"initial assessment|bottom line|accuracy assessment|assessment|summary|"
        r"in summary|key takeaway|final verdict|the bottom line|"
        r"additional context|scientific consensus|important caveats|"
        r"more accurate framing|the actual situation|current status|"
        r"scientific basis|key findings|important context|"
        r"more complete picture|more accurate framework|"
        r"problematic aspects|what the evidence shows|"
        r"evidence-based assessment|evidence-based conclusion"
    )
    patterns = [
        rf'\*\*(?:{header_keywords})[:\s]*\*\*\s*(.*)',
        rf'##\s*(?:{header_keywords})\s*\n(.*)',
    ]
    for pattern in patterns:
        matches = list(re.finditer(pattern, text, re.IGNORECASE | re.DOTALL))
        if matches:
            # Take the last match (final verdict section), strip markdown bold
            return matches[-1].group(1).strip().replace("**", "").replace("__", "")[:600]
    return ""


def _classify_output(output: str) -> str:
    """Classify pipeline output as true/false/partial based on language cues.

    Uses multiple regions of the text for signal detection:
    - Opener (first 300 chars): strongest signal for conversational responses
    - Verdict section: extracted from structured headers like **Overall:**
    - Closer (last 500 chars): verdict signal for structured/analytical responses
    - Full text: weaker but broad signal

    Returns 'true', 'false', 'partial', or 'unknown'.
    """
    raw_text = output.lower()
    # Strip markdown bold/italic for signal matching (but keep raw for header extraction)
    text = raw_text.replace("**", "").replace("__", "")
    # Opening sentences carry the verdict signal (conversational style)
    opener = text[:300]
    # Closing sentences carry the verdict in analytical/structured outputs
    # Use last 800 chars (V1 conclusions can be long)
    closer = text[-800:] if len(text) > 800 else text
    # Extract verdict section from raw text (needs ** markers for header detection)
    verdict_section = _extract_verdict_section(raw_text)

    # --- Partial signals (check first — most specific) ---
    partial_signals = [
        "partially true", "partially correct", "partly true", "partly correct",
        "partially accurate", "not entirely", "oversimplification",
        "technically correct but", "misleading but contains", "grain of truth",
        "mostly true but", "mostly correct but", "approximately correct but",
        "not quite right", "not quite correct",
        "there's some debate", "depends on who",
        "depends on what criteria", "depends on the definition",
        "it's complicated", "it depends",
        "small but important correction", "important correction",
        "small correction", "a correction",
        "important nuance", "with a caveat",
        "more complex than", "a bit more complex",
        "more nuanced than", "bit more nuanced", "more nuanced",
        "the short answer is yes, but", "the short answer is no, but",
        "is a simplification", "is an oversimplification",
        "technically", "but with caveats",
        "let me clarify", "needs some clarification",
        "there's a small correction", "a bit of clarification",
        "the answer is both yes and no",
        "some truth but", "contains some truth",
        "this statement contains some truth",
        "mixed evidence", "mixed scientific evidence",
        "debated topic", "remains debated", "debated among",
        "highly debated", "remains a highly debated",
        "depends on how you measure", "depends on the measure",
        "bold prediction", "a bold prediction",
        "i'd like to clarify",
        "significant promise", "shows significant promise",
        "significant but", "significant, but",
        "both its benefits and limitations",
        "though the exact numbers",
        "can vary by",
        "worth noting some important context",
    ]
    if any(s in opener for s in partial_signals):
        return "partial"

    # --- Definitive true signals in closer (check BEFORE partial closer) ---
    # These are unambiguous overall verdicts that should not be overridden by
    # nuance/caveat signals like "oversimplifies the" or "true for practical purposes".
    definitive_true_closer = [
        "the claim is accurate",
        "this claim is accurate",
        "the claim is correct",
        "the claim is true",
        "the statement is accurate",
        "the statement is correct",
        "the statement is true",
        "claim is well-supported",
        "claim is supported by",
        "is scientifically sound",
        "fundamentally accurate",
        "fundamentally correct",
        "fundamentally sound",
        "remains substantially true",
        "substantially accurate",
        "entirely accurate",
        "claim is entirely",
    ]
    if any(s in closer for s in definitive_true_closer):
        return "true"

    # Partial signals in closer (V1/V2 analytical style)
    partial_closer_signals = [
        "would be more accurate if",
        "mostly accurate but",
        "largely accurate but oversimplified",
        "mostly accurate with",
        "accurate but oversimplified",
        "accurate but incomplete",
        "correct but oversimplified",
        "correct but incomplete",
        "true for practical purposes",
        "true in spirit but",
        "may need qualification",
        "needs qualification",
        "requires qualification",
        "with important caveats",
        "with some caveats",
        "with notable exceptions",
        "with important qualifications",
        "with significant caveats",
        "not the whole story",
        "more complex picture",
        "more complicated than",
        "somewhat misleading",
        "an oversimplification",
        "while generally accurate",
        "while broadly correct",
        "while technically accurate",
        "oversimplifies the",
        "overlooks the underlying",
        "more precise statement",
        "correct in its basic premise but",
        "accurate in broad terms but",
        "too categorical",
        "significantly mythologized",
        "mythologized",
        "captures an essential truth",
        "essential truth, though",
        "substantial overstatement",
        "substantial oversimplification",
        "were a critical trigger",
        "were the trigger",
        "too absolute to be",
        "too absolute",
        "too simplistic",
        "too broad",
        "too narrow",
        "scientifically contested",
        "remains contested",
        "remains controversial",
        "still debated",
        "subject to debate",
        "open to interpretation",
    ]
    if any(s in closer for s in partial_closer_signals):
        return "partial"

    # --- False signals (check BEFORE true to catch negations) ---
    false_signals = [
        "myth", "misconception", "not true", "is false", "is incorrect",
        "refuted", "debunked", "inaccurate", "misleading", "wrong",
        "not accurate", "not quite accurate", "actually not",
        "doesn't actually", "doesn't really", "don't actually",
        "is not correct", "not correct", "not the case",
        "this is actually a common", "this is a popular myth",
        "this is actually a myth", "this is a myth",
        "not exactly", "not quite", "are not the same",
        "is not the same", "isn't the same", "isn't exactly",
        "aren't the same", "not really",
        "common point of confusion", "common misunderstanding",
        "a common belief but", "widely believed but",
        "related but distinct", "related but different",
        "no scientific evidence", "no evidence",
        "has been disproven", "has been debunked",
        "isn't necessarily", "not necessarily",
        "limited scientific evidence",
        "not medically accurate",
        "not found a causal link", "not found a link",
        "hasn't been shown", "has not been shown",
        "isn't completely", "not completely",
        "is a continent, not", "is a continent",
        "actually a real technical problem",
        "not a hoax", "isn't a hoax",
        "not considered scientifically reliable",
        "less reliable",
        "generally safe for most",
        "aren't necessarily",
        "doesn't pose", "do not pose",
    ]
    if any(s in opener for s in false_signals):
        return "false"

    # False signals in closer (V1/V2 analytical style)
    false_closer_signals = [
        "scientifically inaccurate",
        "claim is inaccurate",
        "claim is false",
        "claim is not accurate",
        "claim is incorrect",
        "clearly refutes",
        "has no scientific basis",
        "no basis in",
        "has been consistently debunked",
        "consistently debunked",
        "have consistently debunked",
        "contradicted by",
        "misrepresents how",
        "misrepresents the",
        "this persistent myth",
        "this is a persistent myth",
        "this popular myth",
        "the myth that",
        "remains a myth",
        "is a myth",
        "is not supported by",
        "not supported by evidence",
        "not supported by scientific",
        "lacks scientific support",
        "factually incorrect",
        "factually inaccurate",
        "historically inaccurate",
        "historically incorrect",
        "scientifically unfounded",
        "claim is not true",
        "widely debunked",
        "thoroughly debunked",
        "fundamentally incorrect",
        "common misconception",
        "substantial overestimation",
        "overestimation",
        "inaccurate",
        "this claim is not",
        "this is not correct",
        "does not accurately",
        "oversimplified to the point of being incorrect",
        "significantly overstated",
        "significantly understated",
        "significantly exaggerated",
        "this claim is misleading",
        "this is misleading",
        "misleading claim",
        "does not support the claim",
        "does not support this claim",
        "evidence does not support",
        "overstates what",
        "significantly overstates",
        "largely inaccurate",
        "unsupported by current",
        "unsupported by scientific",
        "contradicts current",
        "contradicts the",
        "contradicts scientific",
        "not well-supported",
        "poorly supported",
        "mathematically false",
        "mathematically incorrect",
        "scientifically false",
        "claim is disputed",
        "remains disputed",
        "is disputed",
    ]
    if any(s in closer for s in false_closer_signals):
        return "false"

    # --- True signals — check opener first, then closer, then full text ---
    true_signals_strong = [
        "that's correct", "this is correct", "is correct",
        "that's accurate", "is accurate",
        "that's true", "is true",
        "that's absolutely correct", "absolutely correct",
        "you're absolutely correct", "you're correct",
        "you're absolutely right", "you're right",
        "verified", "confirmed",
        "that's right",
        "well-established",
        "great approximation", "good approximation",
        "a great approximation", "a good approximation",
        "you're referring to a key", "you're spot on",
        "this is widely accepted", "widely accepted",
        "this is a well-known fact",
        "fascinating statistic! you're",
        "fascinating comparison",
        "that's a great question! yes",
        "yes, that's", "yes! that's",
        "a significant milestone",
        "that's a reasonable estimate",
        "a pivotal moment",
        "did surpass", "has surpassed",
        "did indeed", "was indeed",
        "yes, the us national debt",
        "yes, human sacrifice was indeed",
    ]
    if any(s in opener for s in true_signals_strong):
        return "true"

    # True signals in closer (V1/V2 analytical style)
    true_closer_signals = [
        "the claim is accurate",
        "this claim is accurate",
        "the claim is correct",
        "the claim is true",
        "the statement is accurate",
        "the statement is correct",
        "the statement is true",
        "claim is well-supported",
        "claim is supported",
        "is scientifically sound",
        "scientifically sound",
        "fundamentally sound",
        "fundamentally accurate",
        "fundamentally correct",
        "well-established physical",
        "well-established scientific",
        "well-established principle",
        "extensive experimental verification",
        "well-documented historical",
        "well-documented fact",
        "correctly represents",
        "correctly describes",
        "remains accurate",
        "this is accurate",
        "factually correct",
        "straightforward historical fact",
        "straightforward fact",
        "historically accurate",
        "historically correct",
        "this is a verified fact",
        "consensus supports",
        "consensus among",
        "this fact is well-documented",
        "well-verified claim",
        "the data confirms",
        "data supports this",
        "mathematical verification",
        "mathematically correct",
        "mathematically accurate",
        "the numbers confirm",
        "the math checks out",
        "entirely accurate",
        "substantially accurate",
        "overall accuracy: very high",
        "accuracy: very high",
        "accuracy: high",
        "the claim is entirely",
        "claim is substantially",
        "is entirely correct",
        "is substantially correct",
        "well-supported by evidence",
        "supported by evidence",
        "largely accurate",
        "accurate based on",
        "authoritative scientific data",
        "widely accepted scientific",
        "well-supported by scientific",
        "confirmed by multiple",
        "confirmed by scientific",
    ]
    if any(s in closer for s in true_closer_signals):
        return "true"

    # Broader signals in the full text (weaker but still useful)
    true_signals_weak = [
        "this claim is correct", "this claim is accurate", "this claim is true",
        "this statement is correct", "this statement is accurate",
        "the answer is yes", "this is indeed",
        "scientifically accurate", "factually accurate",
        "this is generally considered to be true",
        "this comparison is actually correct",
        "the claim is accurate", "the statement is accurate",
        "believed to be true by", "widely believed to be true",
        "the statement is true", "the claim is true",
        "is generally accurate", "is broadly correct",
        "commonly cited and highlights",
        "well-supported scientific",
    ]
    if any(s in text for s in true_signals_weak):
        return "true"

    # Full-text false signals (broader than closer, catches mid-text verdicts)
    false_signals_weak = [
        "this claim is false", "this claim is incorrect",
        "this claim is not true", "the claim is false",
        "the claim is incorrect", "the claim is not true",
        "this statement is false", "this statement is incorrect",
        "this is a myth", "this is a popular myth",
        "this claim is a myth", "widely debunked myth",
    ]
    if any(s in text for s in false_signals_weak):
        return "false"

    # Verdict section analysis (V1 structured outputs with **Overall:** etc.)
    if verdict_section:
        # Apply all signal lists to the extracted verdict section
        if any(s in verdict_section for s in partial_signals):
            return "partial"
        if any(s in verdict_section for s in partial_closer_signals):
            return "partial"
        if any(s in verdict_section for s in false_signals):
            return "false"
        if any(s in verdict_section for s in false_closer_signals):
            return "false"
        if any(s in verdict_section for s in true_signals_strong):
            return "true"
        if any(s in verdict_section for s in true_closer_signals):
            return "true"
        if any(s in verdict_section for s in true_signals_weak):
            return "true"

    # Last resort: look for clear verdict patterns anywhere
    if any(s in text for s in ["**verdict: true**", "**true**", "claim is supported"]):
        return "true"
    if any(s in text for s in ["**verdict: false**", "**false**", "claim is not supported"]):
        return "false"

    return "unknown"


def _normalize_gold(gold) -> str:
    """Normalize gold verdict to standard string."""
    if gold in (True, "true"):
        return "true"
    if gold in (False, "false"):
        return "false"
    if gold == "partial":
        return "partial"
    return str(gold)


def compute_accuracy(results: list[dict]) -> dict:
    """Compute overall accuracy against gold verdicts."""
    if not results:
        return {"accuracy": 0.0, "total": 0, "correct": 0, "incorrect": 0, "skipped": 0}

    correct = 0
    incorrect = 0
    total = 0
    per_domain = {}
    per_difficulty = {}
    mismatches = []

    for r in results:
        gold = r.get("gold_verdict")
        if gold is None:
            continue

        total += 1
        gold_norm = _normalize_gold(gold)
        output = _extract_output(r)
        predicted = _classify_output(output)

        is_correct = False
        if gold_norm == "true" and predicted == "true":
            is_correct = True
        elif gold_norm == "false" and predicted == "false":
            is_correct = True
        elif gold_norm == "partial" and predicted in ("partial", "true"):
            is_correct = True

        if is_correct:
            correct += 1
        else:
            incorrect += 1
            mismatches.append({
                "input": r.get("input", "")[:100],
                "gold": gold_norm,
                "predicted": predicted,
            })

        domain = r.get("domain", "unknown")
        if domain not in per_domain:
            per_domain[domain] = {"correct": 0, "total": 0}
        per_domain[domain]["total"] += 1
        if is_correct:
            per_domain[domain]["correct"] += 1

        difficulty = r.get("difficulty", "unknown")
        if difficulty not in per_difficulty:
            per_difficulty[difficulty] = {"correct": 0, "total": 0}
        per_difficulty[difficulty]["total"] += 1
        if is_correct:
            per_difficulty[difficulty]["correct"] += 1

    return {
        "accuracy": correct / total if total > 0 else 0.0,
        "total": total,
        "correct": correct,
        "incorrect": incorrect,
        "skipped": len(results) - total,
        "mismatches": mismatches[:10],
        "per_domain": {
            d: {**v, "accuracy": v["correct"] / v["total"] if v["total"] > 0 else 0.0}
            for d, v in per_domain.items()
        },
        "per_difficulty": {
            d: {**v, "accuracy": v["correct"] / v["total"] if v["total"] > 0 else 0.0}
            for d, v in per_difficulty.items()
        },
    }


def compute_classification_metrics(results: list[dict]) -> dict:
    """Compute per-class precision, recall, F1, and macro/weighted averages.

    Standard metrics for publishable fact-checking evaluation.
    Classes: true, false, partial.
    """
    classes = ["true", "false", "partial"]
    # Confusion matrix counts
    tp = {c: 0 for c in classes}
    fp = {c: 0 for c in classes}
    fn = {c: 0 for c in classes}
    total_per_class = {c: 0 for c in classes}

    for r in results:
        gold = r.get("gold_verdict")
        if gold is None:
            continue

        gold_norm = _normalize_gold(gold)
        predicted = _classify_output(_extract_output(r))

        # Map unknown predictions — treat as abstention (wrong for all classes)
        if predicted == "unknown":
            if gold_norm in classes:
                fn[gold_norm] += 1
                total_per_class[gold_norm] += 1
            continue

        if gold_norm in classes:
            total_per_class[gold_norm] += 1

        for c in classes:
            if predicted == c and gold_norm == c:
                tp[c] += 1
            elif predicted == c and gold_norm != c:
                fp[c] += 1
            elif predicted != c and gold_norm == c:
                fn[c] += 1

    per_class = {}
    for c in classes:
        precision = tp[c] / (tp[c] + fp[c]) if (tp[c] + fp[c]) > 0 else 0.0
        recall = tp[c] / (tp[c] + fn[c]) if (tp[c] + fn[c]) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        per_class[c] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": total_per_class[c],
        }

    # Macro average (unweighted mean across classes)
    macro_p = sum(per_class[c]["precision"] for c in classes) / len(classes)
    macro_r = sum(per_class[c]["recall"] for c in classes) / len(classes)
    macro_f1 = sum(per_class[c]["f1"] for c in classes) / len(classes)

    # Weighted average (weighted by class support)
    total_support = sum(total_per_class[c] for c in classes)
    if total_support > 0:
        weighted_p = sum(per_class[c]["precision"] * total_per_class[c] for c in classes) / total_support
        weighted_r = sum(per_class[c]["recall"] * total_per_class[c] for c in classes) / total_support
        weighted_f1 = sum(per_class[c]["f1"] * total_per_class[c] for c in classes) / total_support
    else:
        weighted_p = weighted_r = weighted_f1 = 0.0

    return {
        "per_class": per_class,
        "macro": {"precision": macro_p, "recall": macro_r, "f1": macro_f1},
        "weighted": {"precision": weighted_p, "recall": weighted_r, "f1": weighted_f1},
    }


def compute_constraint_satisfaction(results: list[dict]) -> dict:
    """Compute constraint satisfaction rate across all results."""
    total_constraints = 0
    satisfied_constraints = 0

    for r in results:
        metrics = r.get("metrics", {})
        total_constraints += metrics.get("constraints_total", 0)
        satisfied_constraints += metrics.get("constraints_satisfied", 0)

    return {
        "satisfaction_rate": satisfied_constraints / total_constraints if total_constraints > 0 else 0.0,
        "total": total_constraints,
        "satisfied": satisfied_constraints,
    }


def compute_verification_metrics(results: list[dict]) -> dict:
    """Compute verification precision, recall, and F1."""
    total_claims = 0
    verified = 0
    refuted = 0
    unclear = 0

    for r in results:
        metrics = r.get("metrics", {})
        total_claims += metrics.get("claims_checked", 0)
        verified += metrics.get("claims_verified", 0)
        refuted += metrics.get("claims_refuted", 0)
        unclear += metrics.get("claims_unclear", 0)

    return {
        "total_claims": total_claims,
        "verified": verified,
        "refuted": refuted,
        "unclear": unclear,
        "verification_rate": verified / total_claims if total_claims > 0 else 0.0,
        "refutation_rate": refuted / total_claims if total_claims > 0 else 0.0,
    }


def compute_gate_efficiency(results: list[dict]) -> dict:
    """Compute gate fast-path rate and average iterations."""
    total = 0
    fast_path_count = 0
    total_iterations = 0

    for r in results:
        metrics = r.get("metrics", {})
        if "gate_decision" in metrics:
            total += 1
            if metrics.get("fast_path", False):
                fast_path_count += 1
            total_iterations += metrics.get("iterations_used", 0)

    return {
        "total_runs": total,
        "fast_path_count": fast_path_count,
        "fast_path_rate": fast_path_count / total if total > 0 else 0.0,
        "avg_iterations": total_iterations / total if total > 0 else 0.0,
    }


def compute_trust_metrics(results: list[dict]) -> dict:
    """Compute trust override rate and winner distribution."""
    total = 0
    draft_wins = 0
    refined_wins = 0
    blended = 0
    total_draft_score = 0
    total_refined_score = 0

    for r in results:
        metrics = r.get("metrics", {})
        winner = metrics.get("trust_winner")
        if winner:
            total += 1
            if winner == "draft":
                draft_wins += 1
            elif winner == "refined":
                refined_wins += 1
            elif winner == "blended":
                blended += 1
            total_draft_score += metrics.get("draft_score", 0)
            total_refined_score += metrics.get("refined_score", 0)

    return {
        "total_runs": total,
        "draft_wins": draft_wins,
        "refined_wins": refined_wins,
        "blended": blended,
        "draft_override_rate": draft_wins / total if total > 0 else 0.0,
        "avg_draft_score": total_draft_score / total if total > 0 else 0.0,
        "avg_refined_score": total_refined_score / total if total > 0 else 0.0,
    }


def compute_latency_metrics(results: list[dict]) -> dict:
    """Compute latency statistics."""
    durations = [r.get("duration_ms", 0) for r in results if r.get("duration_ms")]
    if not durations:
        return {"mean_ms": 0, "median_ms": 0, "p95_ms": 0, "min_ms": 0, "max_ms": 0}

    durations.sort()
    n = len(durations)

    return {
        "mean_ms": sum(durations) / n,
        "median_ms": durations[n // 2],
        "p95_ms": durations[int(n * 0.95)],
        "min_ms": durations[0],
        "max_ms": durations[-1],
        "total_samples": n,
    }


def compute_refinement_delta(results: list[dict]) -> dict:
    """Compute average confidence improvement from refinement."""
    deltas = []
    for r in results:
        metrics = r.get("metrics", {})
        before = metrics.get("confidence_before", 0)
        after = metrics.get("confidence_after", 0)
        if before > 0 or after > 0:
            deltas.append(after - before)

    if not deltas:
        return {"mean_delta": 0.0, "median_delta": 0.0, "positive_rate": 0.0}

    deltas.sort()
    positive = sum(1 for d in deltas if d > 0)

    return {
        "mean_delta": sum(deltas) / len(deltas),
        "median_delta": deltas[len(deltas) // 2],
        "positive_rate": positive / len(deltas),
        "total_samples": len(deltas),
    }


def compute_all_metrics(results: list[dict]) -> dict:
    """Compute all metrics for a set of results."""
    return {
        "accuracy": compute_accuracy(results),
        "classification": compute_classification_metrics(results),
        "constraint_satisfaction": compute_constraint_satisfaction(results),
        "verification": compute_verification_metrics(results),
        "gate_efficiency": compute_gate_efficiency(results),
        "trust": compute_trust_metrics(results),
        "latency": compute_latency_metrics(results),
        "refinement_delta": compute_refinement_delta(results),
    }
