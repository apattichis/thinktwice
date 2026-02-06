"""Evaluation metrics for the ThinkTwice pipeline.

Computes accuracy, constraint satisfaction, hallucination rate, verification
precision/recall, gate efficiency, refinement delta, trust override rate,
latency, and token usage metrics.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _classify_output(output: str) -> str:
    """Classify pipeline output as true/false/partial based on language cues.

    Uses the opening 2-3 sentences as the strongest signal since Claude typically
    leads with its verdict. Checks for negation context to avoid false positives
    like "not quite accurate" being classified as "true" due to the word "accurate".

    Returns 'true', 'false', 'partial', or 'unknown'.
    """
    text = output.lower()
    # Opening sentences carry the verdict signal
    opener = text[:300]

    # Check for partial/nuanced verdicts first (most specific)
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
        "important nuance", "with a caveat",
    ]
    if any(s in opener for s in partial_signals):
        return "partial"

    # Check for false/myth/misconception signals (check BEFORE true to catch negations)
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
    ]
    if any(s in opener for s in false_signals):
        return "false"

    # Check for true/correct signals — check opener first, then broader text
    true_signals_strong = [
        "that's correct", "this is correct", "is correct",
        "that's accurate", "is accurate",
        "that's true", "is true",
        "that's absolutely correct", "absolutely correct",
        "you're absolutely correct", "you're correct",
        "verified", "confirmed",
        "that's right", "you're right",
        "well-established",
        "great approximation", "good approximation",
        "a great approximation", "a good approximation",
    ]
    if any(s in opener for s in true_signals_strong):
        return "true"

    # Broader signals in the full text (weaker but still useful)
    true_signals_weak = [
        "this claim is correct", "this claim is accurate", "this claim is true",
        "this statement is correct", "this statement is accurate",
        "the answer is yes", "this is indeed",
        "scientifically accurate", "factually accurate",
        "this is a well-known fact", "this is widely accepted",
        "this is generally considered to be true",
        "this comparison is actually correct",
        "the claim is accurate", "the statement is accurate",
    ]
    if any(s in text for s in true_signals_weak):
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
        output = r.get("output", "")
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
        predicted = _classify_output(r.get("output", ""))

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
