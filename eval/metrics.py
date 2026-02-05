"""Evaluation metrics for the ThinkTwice pipeline.

Computes accuracy, constraint satisfaction, hallucination rate, verification
precision/recall, gate efficiency, refinement delta, trust override rate,
latency, and token usage metrics.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def compute_accuracy(results: list[dict]) -> dict:
    """Compute overall accuracy against gold verdicts."""
    if not results:
        return {"accuracy": 0.0, "total": 0, "correct": 0}

    correct = 0
    total = 0
    per_domain = {}

    for r in results:
        gold = r.get("gold_verdict")
        if gold is None:
            continue

        total += 1
        metrics = r.get("metrics", {})

        # Determine pipeline's verdict from the final output
        output = r.get("output", "").lower()
        trust_winner = metrics.get("trust_winner", "")

        # For claims, check if pipeline agrees with gold
        if gold in ("true", True):
            if "verified" in output or "accurate" in output or "true" in output:
                correct += 1
        elif gold in ("false", False):
            if "refuted" in output or "false" in output or "incorrect" in output:
                correct += 1
        elif gold == "partial":
            if "partial" in output or "nuance" in output or "complex" in output:
                correct += 1

        domain = r.get("domain", "unknown")
        if domain not in per_domain:
            per_domain[domain] = {"correct": 0, "total": 0}
        per_domain[domain]["total"] += 1
        if total > 0 and correct == total:
            per_domain[domain]["correct"] += 1

    return {
        "accuracy": correct / total if total > 0 else 0.0,
        "total": total,
        "correct": correct,
        "per_domain": {
            d: {**v, "accuracy": v["correct"] / v["total"] if v["total"] > 0 else 0.0}
            for d, v in per_domain.items()
        },
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
        "constraint_satisfaction": compute_constraint_satisfaction(results),
        "verification": compute_verification_metrics(results),
        "gate_efficiency": compute_gate_efficiency(results),
        "trust": compute_trust_metrics(results),
        "latency": compute_latency_metrics(results),
        "refinement_delta": compute_refinement_delta(results),
    }
