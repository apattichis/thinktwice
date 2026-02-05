"""Side-by-side comparison of v1 vs v2 pipeline results.

Computes per-sample differences, statistical significance, and
generates comparison examples.
"""

import json
import logging
import math
from pathlib import Path
from typing import Optional

from eval.metrics import compute_all_metrics

logger = logging.getLogger(__name__)


def load_results(path: str) -> list[dict]:
    """Load results from a JSON file."""
    with open(path) as f:
        data = json.load(f)
    return data.get("results", data) if isinstance(data, dict) else data


def compare_v1_v2(
    v1_results: list[dict],
    v2_results: list[dict],
) -> dict:
    """Compare v1 and v2 results side-by-side.

    Returns comparison metrics and example diffs.
    """
    v1_metrics = compute_all_metrics(v1_results)
    v2_metrics = compute_all_metrics(v2_results)

    # Per-sample comparison (match by input)
    v1_by_input = {r["input"]: r for r in v1_results}
    v2_by_input = {r["input"]: r for r in v2_results}
    common_inputs = set(v1_by_input.keys()) & set(v2_by_input.keys())

    paired_diffs = []
    for inp in common_inputs:
        r1 = v1_by_input[inp]
        r2 = v2_by_input[inp]

        m1 = r1.get("metrics", {})
        m2 = r2.get("metrics", {})

        diff = {
            "input": inp[:100],
            "v1_confidence": m1.get("confidence_after", 0),
            "v2_confidence": m2.get("confidence_after", 0),
            "v1_duration_ms": r1.get("duration_ms", 0),
            "v2_duration_ms": r2.get("duration_ms", 0),
            "v2_iterations": m2.get("iterations_used", 0),
            "v2_gate_decision": m2.get("gate_decision", ""),
            "v2_trust_winner": m2.get("trust_winner", ""),
        }
        diff["confidence_delta"] = diff["v2_confidence"] - diff["v1_confidence"]
        diff["duration_delta_ms"] = diff["v2_duration_ms"] - diff["v1_duration_ms"]
        paired_diffs.append(diff)

    # Statistical significance (paired t-test approximation)
    confidence_deltas = [d["confidence_delta"] for d in paired_diffs]
    sig_result = _paired_t_test(confidence_deltas) if confidence_deltas else None

    # Find best/worst/interesting examples
    sorted_by_improvement = sorted(paired_diffs, key=lambda d: d["confidence_delta"], reverse=True)
    examples = {
        "best_improvement": sorted_by_improvement[:3] if sorted_by_improvement else [],
        "worst_regression": sorted_by_improvement[-3:] if sorted_by_improvement else [],
        "fast_path_examples": [d for d in paired_diffs if d["v2_gate_decision"] == "skip"][:3],
        "draft_wins": [d for d in paired_diffs if d["v2_trust_winner"] == "draft"][:3],
    }

    return {
        "v1_metrics": v1_metrics,
        "v2_metrics": v2_metrics,
        "paired_comparison": {
            "total_paired": len(paired_diffs),
            "mean_confidence_delta": sum(confidence_deltas) / len(confidence_deltas) if confidence_deltas else 0,
            "mean_duration_delta_ms": sum(d["duration_delta_ms"] for d in paired_diffs) / len(paired_diffs) if paired_diffs else 0,
            "v2_improved_count": sum(1 for d in confidence_deltas if d > 0),
            "v2_same_count": sum(1 for d in confidence_deltas if d == 0),
            "v2_regressed_count": sum(1 for d in confidence_deltas if d < 0),
        },
        "statistical_significance": sig_result,
        "examples": examples,
    }


def _paired_t_test(deltas: list[float]) -> dict:
    """Compute paired t-test for confidence deltas."""
    n = len(deltas)
    if n < 2:
        return {"significant": False, "reason": "Not enough samples"}

    mean = sum(deltas) / n
    variance = sum((d - mean) ** 2 for d in deltas) / (n - 1)
    std_err = math.sqrt(variance / n) if variance > 0 else 0

    if std_err == 0:
        return {"significant": False, "t_stat": 0, "p_approx": 1.0, "mean_delta": mean}

    t_stat = mean / std_err
    # Approximate p-value using normal distribution for large n
    p_approx = 2 * (1 - _normal_cdf(abs(t_stat)))

    return {
        "significant": p_approx < 0.05,
        "t_stat": round(t_stat, 4),
        "p_approx": round(p_approx, 6),
        "mean_delta": round(mean, 2),
        "std_err": round(std_err, 4),
        "n": n,
    }


def _normal_cdf(x: float) -> float:
    """Approximate standard normal CDF."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))
